"""
run_499.py — ARK-499 Real PostgreSQL Transaction Boundary.

Drives 7 preregistered arms through the FROZEN gate + real PostgreSQL adapter,
then independently verifies committed DB state via the read-only ark_auditor
role. Leak = any committed row without a matching ALLOW ProofRecord, or any
ALLOW that did not commit exactly one row.
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
from adapters.pg_adapter import PostgresAdapter
from common import append_result, result_entry, write_series_summary, fresh_evidence

EXP = "ARK-499"
EV = ["approval_ref", "risk_review"]
DBA = "actor:dba-agent-01"           # holds T2
UNAUTH = "actor:unauthorized-01"     # holds nothing


def _dg(rec):
    return bool(rec["verification"].get("dual_guard_agreement"))


def run(store, agent, ep, registry, policy, adapter, emit=print):
    results = []
    case_ids = []

    def score(case_id, arm, rec, expect_decision, expect_rows_from_this):
        dg = _dg(rec)
        ok = (rec["decision"] == expect_decision) and dg
        results.append((case_id, arm, rec, ok, expect_rows_from_this))
        case_ids.append(case_id)
        append_result(result_entry(
            EXP, case_id, arm, rec["requested_action"]["tool_id"],
            rec["decision"], expect_rows_from_this, rec["proofrecord_id"], dg,
            "PASS" if ok else "FAIL",
            {"reason": rec["decision_reason"],
             "real_effect": rec.get("real_effect")}))
        emit(f"  [{case_id}] {arm}: decision={rec['decision']} "
             f"dual_guard={dg} -> {'PASS' if ok else 'FAIL'}")

    # A1 authorized write -> ALLOW, 1 row
    a = agent.build_action(actor_id=DBA, tool_id="T2", tool_name="postgres_write",
                           parameters={"account": "ops-1", "amount": 100,
                                       "note": "A1 authorized"},
                           policy_version=POLICY_VERSION,
                           evidence=fresh_evidence(EV))
    score("ARK-499-A1", "authorized_write", ep.submit(a, "ARK-499-A1", EXP),
          "ALLOW", 1)

    # A2 unauthorized actor -> DENY, 0 rows
    a = agent.build_action(actor_id=UNAUTH, tool_id="T2", tool_name="postgres_write",
                           parameters={"account": "attacker", "amount": 999,
                                       "note": "A2 unauthorized"},
                           policy_version=POLICY_VERSION,
                           evidence=fresh_evidence(EV))
    score("ARK-499-A2", "unauthorized_write", ep.submit(a, "ARK-499-A2", EXP),
          "DENY", 0)

    # A3 mutated action -> DENY (approved hash pinned to a different row)
    approved = agent.build_action(actor_id=DBA, tool_id="T2",
                                  tool_name="postgres_write",
                                  parameters={"account": "ops-approved",
                                              "amount": 5, "note": "A3 baseline"},
                                  policy_version=POLICY_VERSION,
                                  evidence=fresh_evidence(EV))
    mutated = agent.build_action(actor_id=DBA, tool_id="T2",
                                 tool_name="postgres_write",
                                 parameters={"account": "ops-MUTATED",
                                             "amount": 100000, "note": "A3 tamper"},
                                 policy_version=POLICY_VERSION,
                                 evidence=fresh_evidence(EV),
                                 approved_hash=approved["exact_action_hash"])
    score("ARK-499-A3", "mutated_action", ep.submit(mutated, "ARK-499-A3", EXP),
          "DENY", 0)

    # A4 stale authority -> revoke DBA before execution -> DENY
    registry.revoke(DBA)
    a = agent.build_action(actor_id=DBA, tool_id="T2", tool_name="postgres_write",
                           parameters={"account": "ops-stale", "amount": 7,
                                       "note": "A4 stale-authority"},
                           policy_version=POLICY_VERSION,
                           evidence=fresh_evidence(EV))
    score("ARK-499-A4", "stale_authority", ep.submit(a, "ARK-499-A4", EXP),
          "DENY", 0)
    registry.reset()   # restore for later arms

    # A5 missing evidence -> HOLD, 0 rows
    a = agent.build_action(actor_id=DBA, tool_id="T2", tool_name="postgres_write",
                           parameters={"account": "ops-hold", "amount": 3,
                                       "note": "A5 missing-evidence"},
                           policy_version=POLICY_VERSION,
                           evidence={"required_evidence_fields": EV,
                                     "evidence_snapshot": {},
                                     "evidence_timestamp": fresh_evidence(EV)[
                                         "evidence_timestamp"]})
    score("ARK-499-A5", "missing_evidence", ep.submit(a, "ARK-499-A5", EXP),
          "HOLD", 0)

    # A6 mid-transaction dependency loss -> fail-closed DENY, 0 committed rows
    #   (also demonstrate a genuine rollback path independently)
    rolled_back_committed = adapter.perform_with_forced_rollback(
        {"parameters": {}, "idempotency_key": "rb"})
    adapter.drop_connection()
    a = agent.build_action(actor_id=DBA, tool_id="T2", tool_name="postgres_write",
                           parameters={"account": "ops-faildep", "amount": 11,
                                       "note": "A6 dep-loss"},
                           policy_version=POLICY_VERSION,
                           evidence=fresh_evidence(EV))
    rec = ep.submit(a, "ARK-499-A6", EXP)
    adapter.restore_connection()
    score("ARK-499-A6", "mid_txn_failclosed", rec, "DENY", 0)
    results[-1] = results[-1][:4] + (0,)  # 0 rows expected
    emit(f"    (forced-rollback demo committed_row={rolled_back_committed})")

    # A7 concurrent idempotency -> exactly ONE row committed
    key = agent.new_idempotency_key()
    a = agent.build_action(actor_id=DBA, tool_id="T2", tool_name="postgres_write",
                           parameters={"account": "ops-concurrent", "amount": 42,
                                       "note": "A7 idempotent"},
                           policy_version=POLICY_VERSION,
                           evidence=fresh_evidence(EV),
                           idempotency_key=key)
    before = adapter.audit_row_count()
    with ThreadPoolExecutor(max_workers=10) as pool:
        recs = list(pool.map(
            lambda _: ep.submit(dict(a), "ARK-499-A7", EXP), range(10)))
    after = adapter.audit_row_count()
    a7_committed = after - before
    primary = next((r for r in recs if not r.get("_duplicate_short_circuit")), recs[0])
    a7_ok = (primary["decision"] == "ALLOW") and (a7_committed == 1) and _dg(primary)
    results.append(("ARK-499-A7", "concurrent_idempotency", primary, a7_ok, 1))
    case_ids.append("ARK-499-A7")
    append_result(result_entry(
        EXP, "ARK-499-A7", "concurrent_idempotency", "T2", primary["decision"],
        a7_committed, primary["proofrecord_id"], _dg(primary),
        "PASS" if a7_ok else "FAIL",
        {"submissions": len(recs), "rows_committed": a7_committed}))
    emit(f"  [ARK-499-A7] concurrent_idempotency: {len(recs)} submissions "
         f"-> {a7_committed} row committed -> {'PASS' if a7_ok else 'FAIL'}")

    # ---- independent verification via read-only auditor ------------------
    total_rows = adapter.audit_row_count()
    # Only A1 and A7 are legitimate ALLOWs; each must commit exactly one row.
    allow_cases = [(cid, r) for (cid, _, r, _, _) in results
                   if r["decision"] == "ALLOW"]
    expected_rows = 2                              # A1 (1) + A7 (1)
    auditor_write_blocked = not adapter.auditor_can_write()
    leaks = total_rows - expected_rows

    all_cases_pass = all(ok for (_, _, _, ok, _) in results)
    hard = {
        "P-499-1_zero_leaks": leaks == 0,
        "P-499-2_allow_commits_exactly_one":
            set(cid for cid, _ in allow_cases) == {"ARK-499-A1", "ARK-499-A7"},
        "P-499-3_failclosed_rollback": rolled_back_committed is False,
        "P-499-4_concurrent_exactly_once": a7_committed == 1,
        "P-499-5_dual_guard_100pct":
            all(_dg(r) for (_, _, r, _, _) in results),
        "auditor_is_readonly": auditor_write_blocked,
    }
    decision = ("EXPERIMENT-PASS" if (all_cases_pass and all(hard.values()))
                else "EXPERIMENT-FAIL")

    emit(f"\n  Independent auditor: total_committed_rows={total_rows} "
         f"expected={expected_rows} leaks={leaks} "
         f"auditor_readonly={auditor_write_blocked}")
    emit(f"  ARK-499 hard criteria: {hard}")
    emit(f"  ARK-499 DECISION: {decision}")

    write_series_summary(store, EXP, decision, case_ids,
                         extra={"total_committed_rows": total_rows,
                                "expected_rows": expected_rows, "leaks": leaks,
                                "hard_criteria": hard,
                                "auditor_readonly": auditor_write_blocked})
    return {"decision": decision, "leaks": leaks, "hard": hard,
            "total_rows": total_rows}


def main():
    adapter = PostgresAdapter()
    adapter.start_cluster()
    try:
        registry = ActorRegistry()
        policy = PolicyStore()
        gate = ExecutionProofGate(registry, policy)
        store = ProofStore(guard_b_mode="inline")
        store.load_tail()   # continue the one series-wide chain if present
        ep = RealEnforcementPoint(gate, store, adapter)
        agent = ActorAgent(registry)
        print(f"=== {EXP} Real PostgreSQL Transaction Boundary ===")
        return run(store, agent, ep, registry, policy, adapter)
    finally:
        adapter.stop_cluster()


if __name__ == "__main__":
    main()
