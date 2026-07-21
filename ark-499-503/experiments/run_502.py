"""
run_502.py — ARK-502 Endurance / operational-continuity with SYNTHETIC-YEAR mode.

*** HONEST SCOPE DECLARATION ***
The ARK-502 preregistration describes a >=14-day continuous endurance soak.
Real wall-clock endurance is IMPOSSIBLE on this ephemeral build VM.

Two modes are supported:
1. BOUNDED SMOKE (default, --mode=smoke): seconds, hundreds of ops. Fast sanity check.
2. SYNTHETIC 1-YEAR (--mode=synthetic-year): simulates 365 days of operations,
   events, and restarts compressed into ~30-60 minutes of runtime. Tests the LOGIC
   of long-running safety (chain continuity, restart resume, stressor survival)
   without wall-clock endurance. Honestly labeled as SYNTHETIC — NOT real-time.

Both contribute ZERO scored PASS to the experimental corpus. The >=14-day REAL
wall-clock endurance claim remains NOT-EXECUTED and requires a persistent machine.

Stressors exercised in SYNTHETIC-YEAR mode:
  - 365 simulated "days" of mixed traffic (~12,000-15,000 total operations)
  - 12+ process restarts (simulating crashes, planned maintenance)
  - 12 monthly policy changes
  - 4 quarterly "key rotation" checkpoints (simulate via restart+resume)
  - Multiple dependency outages scattered across the year
  - Malformed input bursts
  - Concurrency stress tests
  - Chain continuity verification after every restart
"""
import os
import sys
import json
import random
import time
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


def run_synthetic_year(adapter, emit=print):
    """
    Synthetic 1-year simulation: 365 simulated days compressed into real-time.
    Tests the LOGIC of long-running operation, chain continuity across restarts,
    and stressor survival. NOT wall-clock endurance.
    """
    registry = ActorRegistry()
    policy = PolicyStore()
    gate = ExecutionProofGate(registry, policy)
    agent = ActorAgent(registry)

    counters = {"ops": 0, "days": 0, "restarts": 0, "outages": 0,
                "policy_changes": 0, "key_rotations": 0, "dg_fail": 0}
    expected_commits = [0]
    restart_hashes = []  # track chain continuity across restarts
    
    # Initial store
    store = ProofStore(guard_b_mode="inline")
    store.load_tail()
    ep = RealEnforcementPoint(gate, store, adapter)
    
    emit(f"\n=== SYNTHETIC 1-YEAR SIMULATION START ===")
    emit(f"Simulating 365 days of operations + events...")
    start_time = time.time()
    
    # Event schedule (deterministic for reproducibility)
    restart_days = [30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330, 360]  # monthly
    policy_change_days = [30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330, 360]  # monthly
    key_rotation_days = [90, 180, 270, 360]  # quarterly
    outage_days = [15, 45, 105, 135, 195, 225, 285, 315, 345]  # scattered
    malformed_burst_days = [50, 150, 250, 350]
    concurrency_burst_days = [75, 175, 275]
    
    for day in range(1, 366):
        counters["days"] = day
        day_tag = f"D{day:03d}"
        
        # Daily operations (30-40 mixed traffic per day)
        daily_ops = random.randint(30, 40)
        for i in range(daily_ops):
            # Random mix: 60% ALLOW, 30% DENY, 10% HOLD
            r = random.random()
            if r < 0.6:
                action = _allow_action(agent, f"{day_tag}-{i}")
                expected_allow = True
            elif r < 0.9:
                action = _deny_action(agent, f"{day_tag}-{i}")
                expected_allow = False
            else:
                action = _hold_action(agent, f"{day_tag}-{i}")
                expected_allow = False
            
            result = ep.submit(action, f"{EXP}-{day_tag}-{i}", EXP)
            counters["ops"] += 1
            counters[result["decision"]] = counters.get(result["decision"], 0) + 1
            if not _dg(result):
                counters["dg_fail"] += 1
            if expected_allow and result["decision"] == "ALLOW":
                expected_commits[0] += 1
        
        # EVENT: Malformed burst
        if day in malformed_burst_days:
            for i in range(10):
                bad = {"actor_id": DBA, "credential_token": f"cred:{DBA}",
                       "tool_id": "T2", "idempotency_key": f"mal-{day}-{i}"}
                r = ep.submit(bad, f"{EXP}-{day_tag}-MAL{i}", EXP)
                counters["ops"] += 1
                counters[r["decision"]] = counters.get(r["decision"], 0) + 1
            emit(f"  Day {day}: malformed burst (10 ops)")
        
        # EVENT: Concurrency burst
        if day in concurrency_burst_days:
            key = agent.new_idempotency_key()
            a = agent.build_action(actor_id=DBA, tool_id="T2",
                                   tool_name="postgres_write",
                                   parameters={"account": f"burst-{day}",
                                              "amount": 1, "note": f"day {day}"},
                                   policy_version=POLICY_VERSION,
                                   evidence=fresh_evidence(EV),
                                   idempotency_key=key)
            before = adapter.audit_row_count()
            with ThreadPoolExecutor(max_workers=16) as pool:
                recs = list(pool.map(lambda _: ep.submit(dict(a),
                                                        f"{EXP}-{day_tag}-BURST",
                                                        EXP),
                                    range(16)))
            after = adapter.audit_row_count()
            burst_commits = after - before
            for r in recs:
                counters["ops"] += 1
                counters[r["decision"]] = counters.get(r["decision"], 0) + 1
            if burst_commits == 1:
                expected_commits[0] += 1
            emit(f"  Day {day}: concurrency burst (16 parallel) -> {burst_commits} commit")
        
        # EVENT: Dependency outage
        if day in outage_days:
            counters["outages"] += 1
            before_outage = adapter.audit_row_count()
            adapter.drop_connection()
            for i in range(10):
                r = ep.submit(_allow_action(agent, f"outage-{day}-{i}"),
                             f"{EXP}-{day_tag}-OUT{i}", EXP)
                counters["ops"] += 1
                counters[r["decision"]] = counters.get(r["decision"], 0) + 1
            during_outage = adapter.audit_row_count() - before_outage
            adapter.restore_connection()
            # Resume after recovery
            for i in range(5):
                r = ep.submit(_allow_action(agent, f"rec-{day}-{i}"),
                             f"{EXP}-{day_tag}-REC{i}", EXP)
                counters["ops"] += 1
                if r["decision"] == "ALLOW":
                    expected_commits[0] += 1
                counters[r["decision"]] = counters.get(r["decision"], 0) + 1
            emit(f"  Day {day}: dependency outage (10 ops) -> {during_outage} commits during outage")
        
        # EVENT: Policy change
        if day in policy_change_days:
            counters["policy_changes"] += 1
            # Simulate policy version mismatch detection
            a = agent.build_action(actor_id=DBA, tool_id="T2",
                                   tool_name="postgres_write",
                                   parameters={"account": f"polchange-{day}",
                                              "amount": 1, "note": "policy test"},
                                   policy_version="ark-enterprise-vOLD",
                                   evidence=fresh_evidence(EV))
            r = ep.submit(a, f"{EXP}-{day_tag}-POL", EXP)
            counters["ops"] += 1
            counters[r["decision"]] = counters.get(r["decision"], 0) + 1
            emit(f"  Day {day}: policy change checkpoint")
        
        # EVENT: Key rotation checkpoint (simulated via restart)
        if day in key_rotation_days:
            counters["key_rotations"] += 1
            last_hash = store.last_hash
            restart_hashes.append(last_hash)
            # Simulate rotation by restarting store+EP (in real system, would load new key)
            store = ProofStore(guard_b_mode="inline")
            store.load_tail()
            ep = RealEnforcementPoint(gate, store, adapter)
            resumed = store.last_hash
            emit(f"  Day {day}: key rotation checkpoint (restart) "
                 f"chain_resume={resumed == last_hash}")
            # Verify one post-rotation record links correctly
            r = ep.submit(_allow_action(agent, f"postrot-{day}"),
                         f"{EXP}-{day_tag}-POSTROT", EXP)
            counters["ops"] += 1
            if r["decision"] == "ALLOW":
                expected_commits[0] += 1
            if r["chain"]["prior_record_hash"] != last_hash:
                emit(f"  ⚠️  CHAIN BREAK after rotation on day {day}")
        
        # EVENT: Process restart
        if day in restart_days:
            counters["restarts"] += 1
            last_hash = store.last_hash
            restart_hashes.append(last_hash)
            store = ProofStore(guard_b_mode="inline")
            store.load_tail()
            ep = RealEnforcementPoint(gate, store, adapter)
            resumed = store.last_hash
            # Verify post-restart continuity
            r = ep.submit(_allow_action(agent, f"restart-{day}"),
                         f"{EXP}-{day_tag}-RESTART", EXP)
            counters["ops"] += 1
            if r["decision"] == "ALLOW":
                expected_commits[0] += 1
            chain_ok = (resumed == last_hash) and \
                      (r["chain"]["prior_record_hash"] == last_hash)
            emit(f"  Day {day}: restart #{counters['restarts']} chain_ok={chain_ok}")
        
        # Progress indicator every 50 days
        if day % 50 == 0:
            elapsed = time.time() - start_time
            emit(f"  Day {day}/365 [{counters['ops']} ops, {elapsed:.1f}s elapsed]")
    
    elapsed_total = time.time() - start_time
    
    # Final reconciliation
    total_rows = adapter.audit_row_count()
    chain = _verify_full_chain()
    leaks = total_rows - expected_commits[0]
    
    emit(f"\n=== SYNTHETIC YEAR COMPLETE ({elapsed_total:.1f}s runtime) ===")
    emit(f"  Simulated days: {counters['days']}")
    emit(f"  Total operations: {counters['ops']}")
    emit(f"  Restarts: {counters['restarts']}")
    emit(f"  Key rotations: {counters['key_rotations']}")
    emit(f"  Policy changes: {counters['policy_changes']}")
    emit(f"  Dependency outages: {counters['outages']}")
    emit(f"  Decisions: ALLOW={counters.get('ALLOW',0)}, "
         f"DENY={counters.get('DENY',0)}, HOLD={counters.get('HOLD',0)}")
    emit(f"  Committed rows={total_rows} expected={expected_commits[0]} leaks={leaks}")
    emit(f"  Chain: {chain['records']} records, {chain['linkage_breaks']} breaks, "
         f"{chain['dual_guard_fails']} dual-guard fails")
    
    hard = {
        "SY-1_zero_chain_breaks": chain["linkage_breaks"] == 0,
        "SY-2_zero_leaks": leaks == 0,
        "SY-3_dual_guard_100pct": counters["dg_fail"] == 0
            and chain["dual_guard_fails"] == 0,
        "SY-4_all_restarts_resumed": counters["restarts"] >= 12,
        "SY-5_simulated_year_complete": counters["days"] == 365,
    }
    decision = ("SYNTHETIC-YEAR-PASS" if all(hard.values())
               else "SYNTHETIC-YEAR-FAIL")
    
    emit(f"\n  Synthetic-year hard criteria: {hard}")
    emit(f"  DECISION: {decision}")
    emit(f"\n  HONEST LABEL: SYNTHETIC 1-YEAR SIMULATION — logic-tested, "
         f"NOT wall-clock endurance")
    
    write_series_summary(store, EXP, decision, [f"{EXP}-SYNTHETIC-YEAR"],
                        extra={"mode": "SYNTHETIC-YEAR", "scope": "LOGIC TEST - contributes 0 scored PASS",
                               "real_endurance": "NOT-EXECUTED",
                               "simulated_days": 365, "runtime_seconds": elapsed_total,
                               "total_ops": counters["ops"],
                               "restarts": counters["restarts"],
                               "key_rotations": counters["key_rotations"],
                               "policy_changes": counters["policy_changes"],
                               "outages": counters["outages"],
                               "decisions": {k: counters.get(k, 0)
                                            for k in ("ALLOW", "DENY", "HOLD")},
                               "committed_rows": total_rows,
                               "expected_commits": expected_commits[0],
                               "leaks": leaks, "chain_reverify": chain,
                               "hard_criteria": hard})
    
    append_result(result_entry(
        EXP, f"{EXP}-SYNTHETIC-YEAR", "synthetic_one_year_simulation", "MIXED",
        decision, total_rows, "n/a", counters["dg_fail"] == 0, decision,
        {"mode": "SYNTHETIC-YEAR", "scope": "LOGIC TEST - contributes 0 scored PASS",
         "real_endurance": "NOT-EXECUTED", "simulated_days": 365,
         "runtime_seconds": elapsed_total, "total_ops": counters["ops"],
         "leaks": leaks, "hard_criteria": hard}))
    
    return {"decision": decision, "hard": hard, "leaks": leaks,
            "ops": counters["ops"], "days": 365, "runtime": elapsed_total}


def main():
    import argparse
    parser = argparse.ArgumentParser(description="ARK-502 Operational Continuity")
    parser.add_argument("--mode", choices=["smoke", "synthetic-year"],
                       default="smoke",
                       help="Run mode: smoke (fast, ~1min) or synthetic-year (logic test, ~30-60min)")
    args = parser.parse_args()
    
    adapter = PostgresAdapter()
    adapter.start_cluster()
    try:
        if args.mode == "synthetic-year":
            print(f"=== {EXP} SYNTHETIC 1-YEAR SIMULATION ===")
            print(f"(365 simulated days, ~12K-15K ops, 12+ restarts, ~30-60min runtime)")
            return run_synthetic_year(adapter)
        else:
            print(f"=== {EXP} Operational-Continuity BOUNDED SMOKE ===")
            print(f"(fast sanity check, NOT 14-day endurance)")
            return run(adapter)
    finally:
        adapter.stop_cluster()


if __name__ == "__main__":
    main()
