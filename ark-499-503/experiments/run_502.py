"""
run_502.py — ARK-502 Endurance / operational-continuity BOUNDED SMOKE.

*** HONEST SCOPE DECLARATION ***
The ARK-502 preregistration describes a >=14-day continuous endurance soak.
That is IMPOSSIBLE on this ephemeral build VM. This file therefore executes
ONLY a bounded operational-continuity SMOKE (seconds, not weeks; hundreds of
operations, not billions). It contributes ZERO scored PASS to the experimental
corpus. Its sole purpose is to validate that the enforcement harness survives a
representative set of operational stressors without leaking or losing chain
integrity. The >=14-day endurance claim remains NOT-EXECUTED and unproven.

Stressors exercised (all real, all verifiable here):
  1. Sustained mixed traffic  (ALLOW / DENY / HOLD) through frozen gate + real PG.
  2. Process restart with chain resume (new ProofStore.load_tail(), new EP).
  3. Dependency outage + recovery (drop / restore the real PG connection).
  4. Malformed requests (missing required fields -> fail-closed DENY).
  5. Policy-version mismatch under load -> DENY.
  6. Concurrency burst -> exactly-once commit.

Stressor explicitly NOT exercised (and therefore NOT claimed): signing-key
rotation mid-stream (the frozen build uses a single fixed key; rotation is out
of scope for this smoke and is left for the ARK-503 human review / real infra).
"""
import os
import sys
import json
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gate.core import POLICY_VERSION
from gate.actor_registry import ActorRegistry
from gate.policy import PolicyStore
from gate.gate import ExecutionProofGate
from enforcement.proofstore import ProofStore, CHAIN_PATH
from enforcement.real_enforcement_point import RealEnforcementPoint
from actor.actor_agent import ActorAgent
from adapters.pg_adapter import PostgresAdapter
from common import append_result, result_entry, write_series_summary, fresh_evidence

EXP = "ARK-502"
EV = ["approval_ref", "risk_review"]
DBA = "actor:dba-agent-01"
UNAUTH = "actor:unauthorized-01"

CYCLES = 60          # mixed-traffic cycles per phase (bounded, fast)


def _dg(rec):
    return bool(rec["verification"].get("dual_guard_agreement"))


def _allow_action(agent, i):
    return agent.build_action(actor_id=DBA, tool_id="T2",
                              tool_name="postgres_write",
                              parameters={"account": f"soak-{i}", "amount": 1,
                                          "note": f"soak allow {i}"},
                              policy_version=POLICY_VERSION,
                              evidence=fresh_evidence(EV))


def _deny_action(agent, i):
    return agent.build_action(actor_id=UNAUTH, tool_id="T2",
                              tool_name="postgres_write",
                              parameters={"account": f"bad-{i}", "amount": 9,
                                          "note": f"soak deny {i}"},
                              policy_version=POLICY_VERSION,
                              evidence=fresh_evidence(EV))


def _hold_action(agent, i):
    return agent.build_action(actor_id=DBA, tool_id="T2",
                              tool_name="postgres_write",
                              parameters={"account": f"hold-{i}", "amount": 2,
                                          "note": f"soak hold {i}"},
                              policy_version=POLICY_VERSION,
                              evidence={"required_evidence_fields": EV,
                                        "evidence_snapshot": {},
                                        "evidence_timestamp": fresh_evidence(EV)[
                                            "evidence_timestamp"]})


def _mixed_phase(ep, agent, tag, counters, expected_commits):
    """Run CYCLES cycles of ALLOW/DENY/HOLD; tally decisions & expected commits."""
    for i in range(CYCLES):
        ra = ep.submit(_allow_action(agent, f"{tag}-{i}"), f"{EXP}-{tag}A{i}", EXP)
        rd = ep.submit(_deny_action(agent, f"{tag}-{i}"), f"{EXP}-{tag}D{i}", EXP)
        rh = ep.submit(_hold_action(agent, f"{tag}-{i}"), f"{EXP}-{tag}H{i}", EXP)
        for r in (ra, rd, rh):
            counters["ops"] += 1
            counters[r["decision"]] = counters.get(r["decision"], 0) + 1
            if not _dg(r):
                counters["dg_fail"] += 1
        if ra["decision"] == "ALLOW":
            expected_commits[0] += 1


def _verify_full_chain():
    """Independently re-read the chain file: prior-hash linkage + dual-guard."""
    prev = "GENESIS"
    n = 0
    broken = 0
    dg_fail = 0
    with open(CHAIN_PATH, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            n += 1
            if rec["chain"]["prior_record_hash"] != prev:
                broken += 1
            if not rec["verification"].get("dual_guard_agreement"):
                dg_fail += 1
            prev = rec["chain"]["this_record_hash"]
    return {"records": n, "linkage_breaks": broken, "dual_guard_fails": dg_fail}


def run(adapter, emit=print):
    registry = ActorRegistry()
    policy = PolicyStore()
    gate = ExecutionProofGate(registry, policy)
    agent = ActorAgent(registry)

    counters = {"ops": 0, "dg_fail": 0}
    expected_commits = [0]

    # ---- Phase 1: sustained mixed traffic --------------------------------
    store1 = ProofStore(guard_b_mode="inline")
    store1.load_tail()   # continue the one series-wide chain if present
    ep1 = RealEnforcementPoint(gate, store1, adapter)
    _mixed_phase(ep1, agent, "P1", counters, expected_commits)
    last_hash_before_restart = store1.last_hash
    emit(f"  Phase 1 mixed traffic: {counters['ops']} ops, "
         f"last_hash={last_hash_before_restart[:12]}...")

    # ---- Phase 2: process restart with chain resume ----------------------
    store2 = ProofStore(guard_b_mode="inline")
    store2.load_tail()                         # resume from persisted chain
    resumed_hash = store2.last_hash
    ep2 = RealEnforcementPoint(gate, store2, adapter)
    first_after = ep2.submit(_allow_action(agent, "resume-0"),
                             f"{EXP}-RESUME0", EXP)
    counters["ops"] += 1
    counters[first_after["decision"]] = counters.get(
        first_after["decision"], 0) + 1
    if first_after["decision"] == "ALLOW":
        expected_commits[0] += 1
    chain_resumed_ok = (resumed_hash == last_hash_before_restart) and \
        (first_after["chain"]["prior_record_hash"] == last_hash_before_restart)
    emit(f"  Phase 2 restart resume: resumed_hash matches={resumed_hash == last_hash_before_restart}, "
         f"first-post-restart links={chain_resumed_ok}")
    _mixed_phase(ep2, agent, "P2", counters, expected_commits)

    # ---- Phase 3: dependency outage + recovery ---------------------------
    commits_before_outage = adapter.audit_row_count()
    adapter.drop_connection()
    outage_denies = 0
    for i in range(20):
        r = ep2.submit(_allow_action(agent, f"outage-{i}"),
                       f"{EXP}-OUT{i}", EXP)
        counters["ops"] += 1
        counters[r["decision"]] = counters.get(r["decision"], 0) + 1
        if r["decision"] == "DENY":
            outage_denies += 1
    commits_during_outage = adapter.audit_row_count() - commits_before_outage
    adapter.restore_connection()
    # resume normal ALLOW traffic post-recovery
    for i in range(10):
        r = ep2.submit(_allow_action(agent, f"recover-{i}"),
                       f"{EXP}-REC{i}", EXP)
        counters["ops"] += 1
        counters[r["decision"]] = counters.get(r["decision"], 0) + 1
        if r["decision"] == "ALLOW":
            expected_commits[0] += 1
    emit(f"  Phase 3 outage: 20 ALLOW-intent submits during outage -> "
         f"{outage_denies} fail-closed DENY, {commits_during_outage} commits")

    # ---- Phase 4: malformed requests -> fail-closed ----------------------
    malformed_all_denied = True
    for i in range(10):
        bad = {"actor_id": DBA, "credential_token": f"cred:{DBA}",
               "tool_id": "T2", "tool_name": "postgres_write",
               "idempotency_key": f"malformed-{i}"}   # missing hashes/policy/etc.
        r = ep2.submit(bad, f"{EXP}-MAL{i}", EXP)
        counters["ops"] += 1
        counters[r["decision"]] = counters.get(r["decision"], 0) + 1
        if r["decision"] != "DENY":
            malformed_all_denied = False
    emit(f"  Phase 4 malformed: 10 malformed submits, all_denied={malformed_all_denied}")

    # ---- Phase 5: policy-version mismatch --------------------------------
    a = agent.build_action(actor_id=DBA, tool_id="T2", tool_name="postgres_write",
                           parameters={"account": "polbad", "amount": 1,
                                       "note": "wrong policy"},
                           policy_version="ark-enterprise-vWRONG",
                           evidence=fresh_evidence(EV))
    rpol = ep2.submit(a, f"{EXP}-POL", EXP)
    counters["ops"] += 1
    counters[rpol["decision"]] = counters.get(rpol["decision"], 0) + 1
    policy_denied = rpol["decision"] == "DENY"
    emit(f"  Phase 5 policy mismatch: decision={rpol['decision']}")

    # ---- Phase 6: concurrency burst -> exactly-once ----------------------
    key = agent.new_idempotency_key()
    a = agent.build_action(actor_id=DBA, tool_id="T2", tool_name="postgres_write",
                           parameters={"account": "burst", "amount": 5,
                                       "note": "burst"},
                           policy_version=POLICY_VERSION,
                           evidence=fresh_evidence(EV), idempotency_key=key)
    before_burst = adapter.audit_row_count()
    with ThreadPoolExecutor(max_workers=16) as pool:
        recs = list(pool.map(lambda _: ep2.submit(dict(a), f"{EXP}-BURST", EXP),
                             range(16)))
    burst_commits = adapter.audit_row_count() - before_burst
    for r in recs:
        counters["ops"] += 1
        counters[r["decision"]] = counters.get(r["decision"], 0) + 1
    if burst_commits == 1:
        expected_commits[0] += 1
    emit(f"  Phase 6 burst: 16 concurrent submits -> {burst_commits} commit")

    # ---- reconciliation --------------------------------------------------
    total_rows = adapter.audit_row_count()
    chain = _verify_full_chain()
    leaks = total_rows - expected_commits[0]

    hard = {
        "P-502-SMOKE-1_chain_continuity_across_restart":
            chain_resumed_ok and chain["linkage_breaks"] == 0,
        "P-502-SMOKE-2_zero_leaks":
            leaks == 0 and commits_during_outage == 0,
        "P-502-SMOKE-3_dual_guard_100pct": counters["dg_fail"] == 0
            and chain["dual_guard_fails"] == 0,
        "P-502-SMOKE-4_malformed_failclosed": malformed_all_denied,
        "P-502-SMOKE-5_outage_all_failclosed": outage_denies == 20,
        "P-502-SMOKE-6_policy_and_burst":
            policy_denied and burst_commits == 1,
    }
    decision = ("SMOKE-PASS" if all(hard.values()) else "SMOKE-FAIL")

    emit(f"\n  Decisions: {counters}")
    emit(f"  Committed rows={total_rows} expected={expected_commits[0]} leaks={leaks}")
    emit(f"  Full-chain re-verify: {chain}")
    emit(f"  ARK-502 hard criteria: {hard}")
    emit(f"  ARK-502 SMOKE DECISION: {decision} "
         f"(>=14-day endurance remains NOT-EXECUTED)")

    write_series_summary(store2, EXP, "SMOKE-PASS" if decision == "SMOKE-PASS"
                         else "SMOKE-FAIL",
                         [f"{EXP}-SMOKE"],
                         extra={"scope": "BOUNDED SMOKE ONLY - not 14-day endurance",
                                "endurance_14day": "NOT-EXECUTED",
                                "total_ops": counters["ops"],
                                "decisions": counters,
                                "committed_rows": total_rows,
                                "expected_commits": expected_commits[0],
                                "leaks": leaks, "chain_reverify": chain,
                                "hard_criteria": hard})
    # record a single results-ledger meta entry (not a scored case)
    append_result(result_entry(
        EXP, f"{EXP}-SMOKE", "bounded_operational_smoke", "MIXED",
        decision, total_rows, "n/a", counters["dg_fail"] == 0,
        decision, {"scope": "BOUNDED SMOKE - contributes 0 scored PASS",
                   "endurance_14day": "NOT-EXECUTED",
                   "total_ops": counters["ops"], "leaks": leaks,
                   "hard_criteria": hard}))
    return {"decision": decision, "hard": hard, "leaks": leaks,
            "ops": counters["ops"]}


def main():
    adapter = PostgresAdapter()
    adapter.start_cluster()
    try:
        print(f"=== {EXP} Operational-Continuity BOUNDED SMOKE "
              f"(NOT 14-day endurance) ===")
        return run(adapter)
    finally:
        adapter.stop_cluster()


if __name__ == "__main__":
    main()
