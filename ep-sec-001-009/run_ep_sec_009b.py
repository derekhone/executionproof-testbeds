#!/usr/bin/env python3
"""
run_ep_sec_009b.py — EP-SEC-009b remediation experiment runner.

Tests the call-origin guard added to tools.tools.perform_side_effect()
after EP-SEC-009 C005 FAIL.

MUST be run AFTER the preregistration is SHA-locked and pushed.
"""
import json
import os
import secrets
import shutil
import sys
import tempfile
import threading

SUBSTRATE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "substrate")
sys.path.insert(0, SUBSTRATE)

from gate.actor_registry import ActorRegistry
from gate.policy import PolicyStore
from gate.gate import ExecutionProofGate
from gate.core import now_utc, sha256_hex
from enforcement.enforcement_point import EnforcementPoint
from enforcement.proofstore import ProofStore
from actor.actor_agent import ActorAgent
from tools import tools as toolmod
from tools.tools import (
    perform_side_effect, ToolBypassError, SIDE_EFFECT_STATE,
    ALIASES, TOOLS,
)

RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
EXP = "EP-SEC-009b"
POLICY_VERSION = "v1.0"
EVIDENCE_FIELDS = ["budget_remaining", "approval_count", "last_audit_ts"]

results = []


def record_result(case_id, verdict, detail):
    entry = {
        "experiment_id": EXP,
        "case_id": case_id,
        "verdict": verdict,
        "detail": detail,
        "timestamp_utc": now_utc(),
    }
    results.append(entry)
    status = "\u2705" if verdict == "PASS" else "\u274c"
    print(f"  {status} {case_id}: {verdict} — {detail}")


def snapshot_state():
    """Return a copy of SIDE_EFFECT_STATE counts."""
    return {tid: d["executed_count"] for tid, d in SIDE_EFFECT_STATE.items()}


def build_env():
    """Build a fresh gate environment for the positive control."""
    reg = ActorRegistry()
    pol = PolicyStore()
    gate = ExecutionProofGate(reg, pol)
    proof_dir = tempfile.mkdtemp(prefix="ep_sec_009b_")
    store = ProofStore(proof_dir)
    ep = EnforcementPoint(gate, store)
    agent = ActorAgent(reg)
    return reg, pol, gate, store, ep, agent


# =========================================================================
# C001: Direct import + call (original EP-SEC-009 C005 replay)
# =========================================================================
def run_c001():
    print("\nC001: Direct import + call (EP-SEC-009 C005 replay)")
    before = snapshot_state()
    try:
        perform_side_effect("T1", {"amount": 100})
        record_result("SEC-009b-C001", "FAIL",
                      "perform_side_effect executed without ToolBypassError")
    except ToolBypassError as e:
        after = snapshot_state()
        state_unchanged = (before == after)
        if state_unchanged:
            record_result("SEC-009b-C001", "PASS",
                          f"ToolBypassError raised; state unchanged; msg={e}")
        else:
            record_result("SEC-009b-C001", "FAIL",
                          f"ToolBypassError raised BUT state changed: {before} -> {after}")
    except Exception as e:
        record_result("SEC-009b-C001", "FAIL",
                      f"unexpected exception: {type(e).__name__}: {e}")


# =========================================================================
# C002: Direct call on each of T1–T5
# =========================================================================
def run_c002():
    print("\nC002: Direct call on all five tools")
    blocked = []
    leaked = []
    for tid in ["T1", "T2", "T3", "T4", "T5"]:
        before = snapshot_state()
        try:
            perform_side_effect(tid, {"test": True})
            leaked.append(tid)
        except ToolBypassError:
            after = snapshot_state()
            if before == after:
                blocked.append(tid)
            else:
                leaked.append(tid)
        except Exception as e:
            leaked.append(f"{tid}({type(e).__name__})")
    if len(blocked) == 5:
        record_result("SEC-009b-C002", "PASS",
                      f"all 5 tools blocked: {blocked}")
    else:
        record_result("SEC-009b-C002", "FAIL",
                      f"blocked={blocked}, leaked={leaked}")


# =========================================================================
# C003: Call via alias resolution
# =========================================================================
def run_c003():
    print("\nC003: Call via alias resolution")
    alias = "payment_dispatch"  # -> T1
    canonical = ALIASES[alias]
    before = snapshot_state()
    try:
        perform_side_effect(canonical, {"via": "alias"})
        record_result("SEC-009b-C003", "FAIL",
                      "alias-resolved call succeeded")
    except ToolBypassError:
        after = snapshot_state()
        if before == after:
            record_result("SEC-009b-C003", "PASS",
                          "alias-resolved call blocked")
        else:
            record_result("SEC-009b-C003", "FAIL",
                          "ToolBypassError raised but state changed")


# =========================================================================
# C004: Fake class named EnforcementPoint in wrong module
# =========================================================================
def run_c004():
    print("\nC004: Fake EnforcementPoint class (wrong module)")

    class EnforcementPoint:  # noqa: shadows import
        def try_bypass(self):
            return perform_side_effect("T1", {"spoof": True})

    fake = EnforcementPoint()
    before = snapshot_state()
    try:
        fake.try_bypass()
        record_result("SEC-009b-C004", "FAIL",
                      "fake EnforcementPoint class bypassed guard")
    except ToolBypassError:
        after = snapshot_state()
        if before == after:
            record_result("SEC-009b-C004", "PASS",
                          "fake class blocked (module check caught it)")
        else:
            record_result("SEC-009b-C004", "FAIL",
                          "ToolBypassError raised but state changed")


# =========================================================================
# C005: Subclass of real EnforcementPoint in test module
# =========================================================================
def run_c005():
    print("\nC005: Subclass of real EnforcementPoint (test module)")

    class SubclassEP(EnforcementPoint):
        def try_bypass(self):
            return perform_side_effect("T2", {"subclass": True})

    # We need a real EP init to create the subclass
    reg = ActorRegistry()
    pol = PolicyStore()
    gate = ExecutionProofGate(reg, pol)
    proof_dir = tempfile.mkdtemp(prefix="ep_sec_009b_c005_")
    store = ProofStore(proof_dir)
    sub = SubclassEP(gate, store)

    before = snapshot_state()
    try:
        sub.try_bypass()
        # If it succeeds, check: class name is "SubclassEP" not "EnforcementPoint"
        # so the guard should block it. If it doesn't block, that's actually
        # interesting — the isinstance check would pass but the name check won't.
        record_result("SEC-009b-C005", "FAIL",
                      "subclass bypassed guard")
    except ToolBypassError:
        after = snapshot_state()
        if before == after:
            record_result("SEC-009b-C005", "PASS",
                          "subclass blocked (class name is SubclassEP, not EnforcementPoint)")
        else:
            record_result("SEC-009b-C005", "FAIL",
                          "ToolBypassError raised but state changed")


# =========================================================================
# C006: exec()/eval() indirect call
# =========================================================================
def run_c006():
    print("\nC006: exec()/eval() indirect call")
    before = snapshot_state()
    try:
        exec("from tools.tools import perform_side_effect; "
             "perform_side_effect('T3', {'exec': True})")
        record_result("SEC-009b-C006", "FAIL",
                      "exec() bypass succeeded")
    except ToolBypassError:
        after = snapshot_state()
        if before == after:
            record_result("SEC-009b-C006", "PASS",
                          "exec() call blocked")
        else:
            record_result("SEC-009b-C006", "FAIL",
                          "ToolBypassError raised but state changed")
    except Exception as e:
        record_result("SEC-009b-C006", "FAIL",
                      f"unexpected: {type(e).__name__}: {e}")


# =========================================================================
# C007: Threaded direct call
# =========================================================================
def run_c007():
    print("\nC007: Threaded direct call")
    thread_result = {"blocked": False, "error": None}

    def worker():
        try:
            perform_side_effect("T4", {"threaded": True})
        except ToolBypassError:
            thread_result["blocked"] = True
        except Exception as e:
            thread_result["error"] = f"{type(e).__name__}: {e}"

    before = snapshot_state()
    t = threading.Thread(target=worker)
    t.start()
    t.join(timeout=5)
    after = snapshot_state()

    if thread_result["blocked"] and before == after:
        record_result("SEC-009b-C007", "PASS",
                      "threaded call blocked")
    elif thread_result["error"]:
        record_result("SEC-009b-C007", "FAIL",
                      f"unexpected thread error: {thread_result['error']}")
    else:
        record_result("SEC-009b-C007", "FAIL",
                      f"threaded call not blocked; state={before}->{after}")


# =========================================================================
# C008: Positive control through EnforcementPoint.submit()
# =========================================================================
def run_c008():
    print("\nC008: Positive control (legitimate EP path)")
    reg, pol, gate, store, ep, agent = build_env()

    act = agent.build_action(
        actor_id="actor:payments-agent-01", tool_id="T1",
        tool_name="send_payment", parameters={"amount": 250},
        policy_version=POLICY_VERSION,
        evidence=agent.fresh_evidence(EVIDENCE_FIELDS))

    rec = ep.submit(act, "SEC-009b-C008", EXP)

    if (rec["decision"] == "ALLOW"
            and rec["execution_outcome"]["tool_called"]):
        record_result("SEC-009b-C008", "PASS",
                      f"decision=ALLOW, tool_called=True, "
                      f"proofrecord_id={rec['proofrecord_id']}")
    else:
        record_result("SEC-009b-C008", "FAIL",
                      f"decision={rec['decision']}, "
                      f"tool_called={rec['execution_outcome']['tool_called']}")


# =========================================================================
# MAIN
# =========================================================================
def main():
    print(f"{'='*60}")
    print(f"EP-SEC-009b — Tool Bypass Remediation Verification")
    print(f"{'='*60}")
    print(f"Timestamp: {now_utc()}")
    print(f"Substrate: {SUBSTRATE}")

    # Clean ledger state for bypass-attempt entries
    ledger_dir = os.path.join(SUBSTRATE, "ledgers")
    os.makedirs(ledger_dir, exist_ok=True)

    # Run all cases
    run_c001()
    run_c002()
    run_c003()
    run_c004()
    run_c005()
    run_c006()
    run_c007()
    run_c008()

    # Score
    passes = sum(1 for r in results if r["verdict"] == "PASS")
    fails = sum(1 for r in results if r["verdict"] == "FAIL")
    overall = "PASS" if fails == 0 else "FAIL"

    print(f"\n{'='*60}")
    print(f"EP-SEC-009b VERDICT: {overall}  ({passes} PASS, {fails} FAIL)")
    print(f"{'='*60}")

    # Write results
    os.makedirs(RESULTS_DIR, exist_ok=True)
    summary = {
        "experiment_id": EXP,
        "verdict": overall,
        "cases_pass": passes,
        "cases_fail": fails,
        "cases_total": len(results),
        "timestamp_utc": now_utc(),
        "results": results,
    }
    out_path = os.path.join(RESULTS_DIR, "ep_sec_009b_results.json")
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nResults written to {out_path}")

    # Copy bypass-attempt ledger entries
    ledger_out = os.path.join(RESULTS_DIR, "ep_sec_009b_ledger.jsonl")
    with open(ledger_out, "w") as out:
        for tid in TOOLS:
            lp = os.path.join(ledger_dir, TOOLS[tid]["ledger"])
            if os.path.exists(lp):
                with open(lp) as f:
                    for line in f:
                        try:
                            entry = json.loads(line)
                            if entry.get("invocation_type") == "BYPASS_ATTEMPT":
                                out.write(line)
                        except json.JSONDecodeError:
                            pass
    print(f"Bypass ledger entries written to {ledger_out}")

    return overall


if __name__ == "__main__":
    verdict = main()
    sys.exit(0 if verdict == "PASS" else 1)
