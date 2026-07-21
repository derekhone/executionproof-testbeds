"""
run_501.py — ARK-501 Real External OIDC/IAM Identity Boundary.

Authority to perform a privileged resource access is resolved from a REAL
external identity provider (real RS256 issuer + JWKS over HTTP) AND-composed
with the frozen ExecutionProof policy gate. The protected resource server
INDEPENDENTLY re-validates every bearer token before recording an access grant;
that server-side access log is the audit ground-truth.

Boundary property under test: a privileged access is granted only when a
non-forged, non-expired, non-revoked token carrying the required role is
presented AND the frozen gate's own checks (authority, evidence, policy,
exact-action) also pass. Every other outcome grants zero access.

Explicitly NOT claimed: not Okta / Azure AD / Auth0; not a certified OIDC
deployment. A real self-hosted RS256 issuer + JWKS + bearer-protected resource.
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
from adapters.oidc_adapter import OIDCAdapter
from common import append_result, result_entry, write_series_summary, fresh_evidence

EXP = "ARK-501"
EV = ["security_scan", "reviewer_approval"]
INFRA = "actor:infra-agent-01"       # holds T4 (privileged resource access)
SUB = "infra-agent-01"


def _dg(rec):
    return bool(rec["verification"].get("dual_guard_agreement"))


def _mk_action(agent, token, note, evidence=None, idem=None):
    a = agent.build_action(actor_id=INFRA, tool_id="T4",
                           tool_name="privileged_resource_access",
                           parameters={"resource": "prod-secret-store",
                                       "note": note},
                           policy_version=POLICY_VERSION,
                           evidence=evidence if evidence is not None
                           else fresh_evidence(EV),
                           idempotency_key=idem)
    a["access_token"] = token          # side channel: excluded from action hash
    return a


def run(store, agent, ep, registry, policy, adapter, emit=print):
    results = []
    case_ids = []

    def score(case_id, arm, rec, expect_decision, expect_grants):
        dg = _dg(rec)
        ok = (rec["decision"] == expect_decision) and dg
        results.append((case_id, arm, rec, ok, expect_grants))
        case_ids.append(case_id)
        append_result(result_entry(
            EXP, case_id, arm, rec["requested_action"]["tool_id"],
            rec["decision"], expect_grants, rec["proofrecord_id"], dg,
            "PASS" if ok else "FAIL",
            {"reason": rec["decision_reason"],
             "identity_basis": rec.get("identity_basis"),
             "real_effect": rec.get("real_effect")}))
        emit(f"  [{case_id}] {arm}: decision={rec['decision']} "
             f"dual_guard={dg} -> {'PASS' if ok else 'FAIL'}")

    # C1 valid deploy token -> ALLOW -> real protected access granted
    tok, _ = adapter.issue_token(SUB, ["deploy"], ttl_seconds=300)
    score("ARK-501-C1", "valid_token_grant",
          ep.submit(_mk_action(agent, tok, "C1 valid"), "ARK-501-C1", EXP),
          "ALLOW", 1)

    # C2 expired token -> DENY (identity)
    tok, _ = adapter.issue_token(SUB, ["deploy"], ttl_seconds=1,
                                 issued_offset=-3600)
    score("ARK-501-C2", "expired_token",
          ep.submit(_mk_action(agent, tok, "C2 expired"), "ARK-501-C2", EXP),
          "DENY", 0)

    # C3 forged signature (untrusted key) -> DENY (identity)
    tok, _ = adapter.issue_token(SUB, ["deploy"], forged=True)
    score("ARK-501-C3", "forged_signature",
          ep.submit(_mk_action(agent, tok, "C3 forged"), "ARK-501-C3", EXP),
          "DENY", 0)

    # C4 insufficient role -> DENY (identity)
    tok, _ = adapter.issue_token(SUB, ["viewer"], ttl_seconds=300)
    score("ARK-501-C4", "insufficient_role",
          ep.submit(_mk_action(agent, tok, "C4 wrong-role"), "ARK-501-C4", EXP),
          "DENY", 0)

    # C5 revoked jti -> DENY (identity)
    tok, jti = adapter.issue_token(SUB, ["deploy"], ttl_seconds=300)
    adapter.revoke_jti(jti)
    score("ARK-501-C5", "revoked_token",
          ep.submit(_mk_action(agent, tok, "C5 revoked"), "ARK-501-C5", EXP),
          "DENY", 0)

    # C6 valid token BUT missing scan/approval evidence -> HOLD (frozen gate)
    #    Demonstrates the policy gate still applies even with a valid identity.
    tok, _ = adapter.issue_token(SUB, ["deploy"], ttl_seconds=300)
    a = _mk_action(agent, tok, "C6 valid-token-missing-evidence",
                   evidence={"required_evidence_fields": EV,
                             "evidence_snapshot": {},
                             "evidence_timestamp": fresh_evidence(EV)[
                                 "evidence_timestamp"]})
    score("ARK-501-C6", "valid_token_missing_evidence",
          ep.submit(a, "ARK-501-C6", EXP), "HOLD", 0)

    # C7 concurrent burst with one valid token -> exactly ONE grant
    tok, _ = adapter.issue_token(SUB, ["deploy"], ttl_seconds=300)
    key = agent.new_idempotency_key()
    before_c7 = adapter.access_count()
    with ThreadPoolExecutor(max_workers=10) as pool:
        recs = list(pool.map(
            lambda _: ep.submit(_mk_action(agent, tok, "C7 concurrent", idem=key),
                                "ARK-501-C7", EXP), range(10)))
    c7_grants = adapter.access_count() - before_c7
    primary = next((r for r in recs if not r.get("_duplicate_short_circuit")),
                   recs[0])
    c7_ok = (primary["decision"] == "ALLOW") and (c7_grants == 1) and _dg(primary)
    results.append(("ARK-501-C7", "concurrent_grant", primary, c7_ok, 1))
    case_ids.append("ARK-501-C7")
    append_result(result_entry(
        EXP, "ARK-501-C7", "concurrent_grant", "T4", primary["decision"],
        c7_grants, primary["proofrecord_id"], _dg(primary),
        "PASS" if c7_ok else "FAIL",
        {"submissions": len(recs), "grants": c7_grants}))
    emit(f"  [ARK-501-C7] concurrent_grant: {len(recs)} submissions -> "
         f"{c7_grants} grant -> {'PASS' if c7_ok else 'FAIL'}")

    # ---- independent verification: resource-server access log ------------
    total_grants = adapter.access_count()
    entries = adapter.access_entries()
    # independent direct probe: a forged token is rejected by the resource
    # server itself, with no gate in the loop.
    forged_tok, _ = adapter.issue_token(SUB, ["deploy"], forged=True)
    probe_status, _ = adapter.probe_protected(forged_tok)

    allow_cases = set(cid for (cid, _, r, _, _) in results
                      if r["decision"] == "ALLOW")
    expected_grants = 2                                    # C1 + C7

    all_cases_pass = all(ok for (_, _, _, ok, _) in results)
    hard = {
        "P-501-1_zero_unauthorized_grants": total_grants == expected_grants,
        "P-501-2_allow_only_c1_c7":
            allow_cases == {"ARK-501-C1", "ARK-501-C7"},
        "P-501-3_grants_all_have_role":
            bool(entries) and all("deploy" in e["roles"] for e in entries),
        "P-501-4_concurrent_exactly_once": c7_grants == 1,
        "P-501-5_forged_rejected_by_resource_server": probe_status == 403,
        "P-501-6_dual_guard_100pct":
            all(_dg(r) for (_, _, r, _, _) in results),
    }
    decision = ("EXPERIMENT-PASS" if (all_cases_pass and all(hard.values()))
                else "EXPERIMENT-FAIL")

    emit(f"\n  Independent resource-server access log: grants={total_grants} "
         f"expected={expected_grants} (direct forged-probe status={probe_status})")
    emit(f"  ARK-501 hard criteria: {hard}")
    emit(f"  ARK-501 DECISION: {decision}")

    write_series_summary(store, EXP, decision, case_ids,
                         extra={"total_grants": total_grants,
                                "expected_grants": expected_grants,
                                "forged_probe_status": probe_status,
                                "hard_criteria": hard})
    return {"decision": decision, "hard": hard, "total_grants": total_grants}


def main():
    adapter = OIDCAdapter()
    adapter.setup()
    try:
        registry = ActorRegistry()
        policy = PolicyStore()
        gate = ExecutionProofGate(registry, policy)
        store = ProofStore(guard_b_mode="inline")
        store.load_tail()   # continue the one series-wide chain if present
        ep = RealEnforcementPoint(gate, store, adapter,
                                  identity_validator=lambda a: adapter.validate_token(
                                      a.get("access_token")))
        agent = ActorAgent(registry)
        print(f"=== {EXP} Real External OIDC/IAM Identity Boundary ===")
        return run(store, agent, ep, registry, policy, adapter)
    finally:
        adapter.teardown()


if __name__ == "__main__":
    main()
