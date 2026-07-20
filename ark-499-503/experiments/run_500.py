"""
run_500.py — ARK-500 Real CI/CD Release Boundary.

Drives 7 preregistered arms through the FROZEN gate + a REAL local git CI/CD
adapter (real repo, real build, real SHA-256-addressed artifacts, real on-disk
deploy target). Independent verification RE-READS the deployed files from disk
and RECOMPUTES their SHA-256 via inspect_env() — the harness never trusts the
adapter's own claim about deploy state.

Boundary property under test: only the EXACT approved artifact reaches the
EXACT approved environment; every other outcome commits zero deploys.

Explicitly NOT claimed: Docker / Kubernetes / cloud CD. Local runner + on-disk
deploy target only.
"""
import os
import sys
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gate.core import POLICY_VERSION
from gate.actor_registry import ActorRegistry
from gate.policy import PolicyStore
from gate.gate import ExecutionProofGate
from enforcement.proofstore import ProofStore
from enforcement.real_enforcement_point import RealEnforcementPoint
from actor.actor_agent import ActorAgent
from adapters.cicd_adapter import CICDAdapter
from common import append_result, result_entry, write_series_summary, fresh_evidence

EXP = "ARK-500"
EV = ["security_scan", "reviewer_approval"]
INFRA = "actor:infra-agent-01"       # holds T3 (deploy) + T4
UNAUTH = "actor:unauthorized-01"     # holds nothing


def _dg(rec):
    return bool(rec["verification"].get("dual_guard_agreement"))


def run(store, agent, ep, registry, policy, adapter, emit=print):
    results = []
    case_ids = []
    approved_digest = adapter.artifacts["approved"]["digest"]
    tampered_digest = adapter.artifacts["tampered"]["digest"]

    def score(case_id, arm, rec, expect_decision, expect_deploys):
        dg = _dg(rec)
        ok = (rec["decision"] == expect_decision) and dg
        results.append((case_id, arm, rec, ok, expect_deploys))
        case_ids.append(case_id)
        append_result(result_entry(
            EXP, case_id, arm, rec["requested_action"]["tool_id"],
            rec["decision"], expect_deploys, rec["proofrecord_id"], dg,
            "PASS" if ok else "FAIL",
            {"reason": rec["decision_reason"],
             "real_effect": rec.get("real_effect")}))
        emit(f"  [{case_id}] {arm}: decision={rec['decision']} "
             f"dual_guard={dg} -> {'PASS' if ok else 'FAIL'}")

    # B1 approved artifact -> ALLOW -> deploy to staging
    a = agent.build_action(actor_id=INFRA, tool_id="T3", tool_name="cicd_deploy",
                           parameters={"artifact_digest": approved_digest,
                                       "environment": "staging",
                                       "note": "B1 approved release"},
                           policy_version=POLICY_VERSION,
                           evidence=fresh_evidence(EV))
    score("ARK-500-B1", "approved_release", ep.submit(a, "ARK-500-B1", EXP),
          "ALLOW", 1)

    # B2 digest substitution -> DENY (tampered artifact pinned to approved hash)
    approved_b2 = agent.build_action(
        actor_id=INFRA, tool_id="T3", tool_name="cicd_deploy",
        parameters={"artifact_digest": approved_digest, "environment": "staging",
                    "note": "B2 baseline"},
        policy_version=POLICY_VERSION, evidence=fresh_evidence(EV))
    mutated_b2 = agent.build_action(
        actor_id=INFRA, tool_id="T3", tool_name="cicd_deploy",
        parameters={"artifact_digest": tampered_digest, "environment": "staging",
                    "note": "B2 tampered-artifact"},
        policy_version=POLICY_VERSION, evidence=fresh_evidence(EV),
        approved_hash=approved_b2["exact_action_hash"])
    score("ARK-500-B2", "digest_substitution",
          ep.submit(mutated_b2, "ARK-500-B2", EXP), "DENY", 0)

    # B3 environment substitution -> DENY (staging-approved, production attempted)
    approved_b3 = agent.build_action(
        actor_id=INFRA, tool_id="T3", tool_name="cicd_deploy",
        parameters={"artifact_digest": approved_digest, "environment": "staging",
                    "note": "B3 baseline"},
        policy_version=POLICY_VERSION, evidence=fresh_evidence(EV))
    mutated_b3 = agent.build_action(
        actor_id=INFRA, tool_id="T3", tool_name="cicd_deploy",
        parameters={"artifact_digest": approved_digest, "environment": "production",
                    "note": "B3 env-escalation"},
        policy_version=POLICY_VERSION, evidence=fresh_evidence(EV),
        approved_hash=approved_b3["exact_action_hash"])
    score("ARK-500-B3", "environment_substitution",
          ep.submit(mutated_b3, "ARK-500-B3", EXP), "DENY", 0)

    # B4 stale / missing scan evidence -> HOLD
    a = agent.build_action(actor_id=INFRA, tool_id="T3", tool_name="cicd_deploy",
                           parameters={"artifact_digest": approved_digest,
                                       "environment": "staging",
                                       "note": "B4 missing-scan"},
                           policy_version=POLICY_VERSION,
                           evidence={"required_evidence_fields": EV,
                                     "evidence_snapshot": {},
                                     "evidence_timestamp": fresh_evidence(EV)[
                                         "evidence_timestamp"]})
    score("ARK-500-B4", "missing_scan_evidence",
          ep.submit(a, "ARK-500-B4", EXP), "HOLD", 0)

    # B5 revoked deploy authority -> DENY
    registry.revoke(INFRA)
    a = agent.build_action(actor_id=INFRA, tool_id="T3", tool_name="cicd_deploy",
                           parameters={"artifact_digest": approved_digest,
                                       "environment": "staging",
                                       "note": "B5 revoked-authority"},
                           policy_version=POLICY_VERSION,
                           evidence=fresh_evidence(EV))
    score("ARK-500-B5", "revoked_authority",
          ep.submit(a, "ARK-500-B5", EXP), "DENY", 0)
    registry.reset()

    # B6 retry idempotency -> exactly ONE deploy for two identical submissions
    key = agent.new_idempotency_key()
    a = agent.build_action(actor_id=INFRA, tool_id="T3", tool_name="cicd_deploy",
                           parameters={"artifact_digest": approved_digest,
                                       "environment": "staging",
                                       "note": "B6 idempotent-retry"},
                           policy_version=POLICY_VERSION,
                           evidence=fresh_evidence(EV), idempotency_key=key)
    before_b6 = adapter.deploy_event_count()
    r1 = ep.submit(dict(a), "ARK-500-B6", EXP)
    r2 = ep.submit(dict(a), "ARK-500-B6", EXP)   # duplicate -> short-circuit
    b6_deploys = adapter.deploy_event_count() - before_b6
    b6_ok = (r1["decision"] == "ALLOW") and (b6_deploys == 1) and _dg(r1) \
        and bool(r2["execution_outcome"]["duplicate_prevented"])
    results.append(("ARK-500-B6", "retry_idempotency", r1, b6_ok, 1))
    case_ids.append("ARK-500-B6")
    append_result(result_entry(
        EXP, "ARK-500-B6", "retry_idempotency", "T3", r1["decision"],
        b6_deploys, r1["proofrecord_id"], _dg(r1),
        "PASS" if b6_ok else "FAIL",
        {"submissions": 2, "deploys": b6_deploys,
         "duplicate_prevented": r2["execution_outcome"]["duplicate_prevented"]}))
    emit(f"  [ARK-500-B6] retry_idempotency: 2 submissions -> {b6_deploys} "
         f"deploy -> {'PASS' if b6_ok else 'FAIL'}")

    # B7 concurrent burst -> exactly ONE deploy
    key = agent.new_idempotency_key()
    a = agent.build_action(actor_id=INFRA, tool_id="T3", tool_name="cicd_deploy",
                           parameters={"artifact_digest": approved_digest,
                                       "environment": "staging",
                                       "note": "B7 concurrent"},
                           policy_version=POLICY_VERSION,
                           evidence=fresh_evidence(EV), idempotency_key=key)
    before_b7 = adapter.deploy_event_count()
    with ThreadPoolExecutor(max_workers=10) as pool:
        recs = list(pool.map(
            lambda _: ep.submit(dict(a), "ARK-500-B7", EXP), range(10)))
    b7_deploys = adapter.deploy_event_count() - before_b7
    primary = next((r for r in recs if not r.get("_duplicate_short_circuit")),
                   recs[0])
    b7_ok = (primary["decision"] == "ALLOW") and (b7_deploys == 1) and _dg(primary)
    results.append(("ARK-500-B7", "concurrent_deploy", primary, b7_ok, 1))
    case_ids.append("ARK-500-B7")
    append_result(result_entry(
        EXP, "ARK-500-B7", "concurrent_deploy", "T3", primary["decision"],
        b7_deploys, primary["proofrecord_id"], _dg(primary),
        "PASS" if b7_ok else "FAIL",
        {"submissions": len(recs), "deploys": b7_deploys}))
    emit(f"  [ARK-500-B7] concurrent_deploy: {len(recs)} submissions -> "
         f"{b7_deploys} deploy -> {'PASS' if b7_ok else 'FAIL'}")

    # ---- independent verification (re-read disk, recompute SHA-256) -------
    staging = adapter.inspect_env("staging")
    production = adapter.inspect_env("production")
    total_deploys = adapter.deploy_event_count()

    allow_cases = set(cid for (cid, _, r, _, _) in results
                      if r["decision"] == "ALLOW")

    all_cases_pass = all(ok for (_, _, _, ok, _) in results)
    hard = {
        "P-500-1_staging_holds_only_approved":
            staging["deployed"] and staging["digest"] == approved_digest,
        "P-500-2_production_never_deployed": production["deployed"] is False,
        "P-500-3_no_tampered_digest_anywhere":
            tampered_digest not in (staging["digest"], production["digest"]),
        "P-500-4_allow_only_b1_b6_b7":
            allow_cases == {"ARK-500-B1", "ARK-500-B6", "ARK-500-B7"},
        "P-500-5_retry_idempotent": b6_deploys == 1,
        "P-500-6_concurrent_exactly_once": b7_deploys == 1,
        "P-500-7_dual_guard_100pct":
            all(_dg(r) for (_, _, r, _, _) in results),
    }
    decision = ("EXPERIMENT-PASS" if (all_cases_pass and all(hard.values()))
                else "EXPERIMENT-FAIL")

    emit(f"\n  Independent inspect: staging={staging} production={production} "
         f"deploy_events={total_deploys}")
    emit(f"  ARK-500 hard criteria: {hard}")
    emit(f"  ARK-500 DECISION: {decision}")

    write_series_summary(store, EXP, decision, case_ids,
                         extra={"staging": staging, "production": production,
                                "deploy_events": total_deploys,
                                "approved_digest": approved_digest,
                                "tampered_digest": tampered_digest,
                                "hard_criteria": hard})
    return {"decision": decision, "hard": hard, "staging": staging,
            "production": production}


def main():
    adapter = CICDAdapter()
    adapter.setup()
    registry = ActorRegistry()
    policy = PolicyStore()
    gate = ExecutionProofGate(registry, policy)
    store = ProofStore(guard_b_mode="inline")
    store.load_tail()   # continue the one series-wide chain if present
    ep = RealEnforcementPoint(gate, store, adapter)
    agent = ActorAgent(registry)
    print(f"=== {EXP} Real CI/CD Release Boundary ===")
    return run(store, agent, ep, registry, policy, adapter)


if __name__ == "__main__":
    main()
