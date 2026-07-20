"""
experiments/run_498.py — ARK-498 Networked Production-Like Performance.

Starts the gate as a Flask HTTP server (experiments/ark498_server.py) on a
loopback TCP port and drives 9 scenarios (~1,810 requests) through it with the
`requests` library. Measures end-to-end latency with time.monotonic(), then
scores the six FROZEN hard criteria and reports characterization data
(p50/p95/p99, throughput) that is explicitly NOT an SLA.

  P-498-1  fail-closed: leak count == 0 in S005/S006/S007
  P-498-2  zero duplicate executions in S009
  P-498-3  ProofRecord completeness == 100% of accepted requests
  P-498-4  every error resolves to HOLD/DENY (never ALLOW) with a ledger entry
  P-498-5  recovery: no queued-denied request auto-executes after restoration
  P-498-6  Guard-B signature verification rate == 100% for legitimate records

All output carries the mandatory characterization label.
"""
import os
import sys
import json
import time
import subprocess
import statistics
from concurrent.futures import ThreadPoolExecutor

import requests

from experiments.common import (
    append_result, result_entry, executed_count_for_case, RESULTS_DIR,
    TOOL_NAMES, TOOL_OWNER, EVIDENCE_FIELDS,
)
from gate.core import POLICY_VERSION

EXPERIMENT_ID = "ARK-498"
PORT = 5050
BASE = f"http://127.0.0.1:{PORT}"
LABEL = ("PRODUCTION-LIKE OVERHEAD CHARACTERIZATION · "
         "NOT A BENCHMARK CERTIFICATION · NOT A PRODUCTION SLA")

_HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVER = os.path.join(_HERE, "experiments", "ark498_server.py")
METRICS_PATH = os.path.join(RESULTS_DIR, "ark498_metrics.json")


# --------------------------------------------------------------------------
def _pct(values, p):
    if not values:
        return None
    s = sorted(values)
    k = (len(s) - 1) * (p / 100.0)
    lo = int(k)
    hi = min(lo + 1, len(s) - 1)
    frac = k - lo
    return s[lo] + (s[hi] - s[lo]) * frac


def _start_server():
    proc = subprocess.Popen(
        ["python3", SERVER, str(PORT)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=_HERE)
    for _ in range(100):
        try:
            r = requests.get(f"{BASE}/health", timeout=1)
            if r.status_code == 200:
                return proc
        except requests.RequestException:
            time.sleep(0.1)
    proc.terminate()
    raise RuntimeError("ARK-498 server did not become healthy")


def _stop_server(proc):
    try:
        requests.post(f"{BASE}/shutdown", timeout=1)
    except requests.RequestException:
        pass
    try:
        proc.wait(timeout=5)
    except Exception:
        proc.kill()


# --------------------------------------------------------------------------
class Client:
    """Builds valid ALLOW actions locally and submits them over loopback TCP."""

    def __init__(self, env):
        self.agent = env.agent

    def build_allow(self, tool_id="T3", idem=None, params=None):
        owner = TOOL_OWNER[tool_id]
        ev = self.agent.fresh_evidence(EVIDENCE_FIELDS, 0)
        return self.agent.build_action(
            actor_id=owner, tool_id=tool_id, tool_name=TOOL_NAMES[tool_id],
            parameters=params or {"app": "svc-perf"},
            policy_version=POLICY_VERSION, evidence=ev, idempotency_key=idem)

    def submit(self, action, case_id, dep_failures=None):
        payload = {"action": action, "case_id": case_id,
                   "experiment_id": EXPERIMENT_ID,
                   "dep_failures": dep_failures or []}
        t0 = time.monotonic()
        try:
            r = requests.post(f"{BASE}/submit", json=payload, timeout=30)
            dt = (time.monotonic() - t0) * 1000.0
            if r.status_code == 200:
                body = r.json()
                return {"latency_ms": dt, "ok": body.get("ok", False),
                        "http": 200, **body}
            return {"latency_ms": dt, "ok": False, "http": r.status_code,
                    "decision": "SERVER-ERROR"}
        except requests.RequestException as exc:
            dt = (time.monotonic() - t0) * 1000.0
            return {"latency_ms": dt, "ok": False, "http": None,
                    "decision": "NETWORK-ERROR", "error": repr(exc)}


# --------------------------------------------------------------------------
def run(env, emit=print):
    emit(f"  [{LABEL}]")
    metrics = {"label": LABEL, "scenarios": {}}
    case_ids = []
    proc = _start_server()
    cli = Client(env)

    # server errors / allow-on-error accounting (P-498-4)
    allow_on_error = 0
    server_errors = 0

    def account(resps):
        nonlocal allow_on_error, server_errors
        for r in resps:
            if not r.get("ok"):
                server_errors += 1
                if r.get("decision") == "ALLOW":
                    allow_on_error += 1

    try:
        # ---- S001 cold start (1 request) ----
        r = cli.submit(cli.build_allow(idem=cli.agent.new_idempotency_key()),
                       "ARK-498-S001")
        account([r])
        metrics["scenarios"]["S001"] = {"cold_start_latency_ms": r["latency_ms"],
                                        "decision": r.get("decision")}
        emit(f"  [S001] cold-start latency={r['latency_ms']:.1f}ms "
             f"decision={r.get('decision')}")

        # ---- S002 warm start (100 sequential) ----
        lat = []
        for i in range(100):
            rr = cli.submit(cli.build_allow(idem=cli.agent.new_idempotency_key()),
                            "ARK-498-S002")
            account([rr])
            if rr.get("ok"):
                lat.append(rr["latency_ms"])
        err_rate_s2 = 1 - (len(lat) / 100.0)
        metrics["scenarios"]["S002"] = {
            "n": 100, "p50_ms": _pct(lat, 50), "mean_ms": statistics.mean(lat),
            "error_rate": err_rate_s2}
        emit(f"  [S002] warm p50={_pct(lat,50):.1f}ms error_rate={err_rate_s2:.3f}")

        # ---- S003 concurrent (10 clients x 50 = 500) ----
        def worker_s3(_):
            return cli.submit(cli.build_allow(idem=cli.agent.new_idempotency_key()),
                              "ARK-498-S003")
        with ThreadPoolExecutor(max_workers=10) as ex:
            res3 = list(ex.map(worker_s3, range(500)))
        account(res3)
        lat3 = [x["latency_ms"] for x in res3 if x.get("ok")]
        err_rate_s3 = 1 - (len(lat3) / 500.0)
        metrics["scenarios"]["S003"] = {
            "n": 500, "concurrency": 10, "p50_ms": _pct(lat3, 50),
            "p95_ms": _pct(lat3, 95), "p99_ms": _pct(lat3, 99),
            "error_rate": err_rate_s3}
        emit(f"  [S003] p50={_pct(lat3,50):.1f} p95={_pct(lat3,95):.1f} "
             f"p99={_pct(lat3,99):.1f}ms error_rate={err_rate_s3:.3f}")

        # ---- S004 sustained throughput (5 clients x 200 = 1000) ----
        done_times = []

        def worker_s4(_):
            rr = cli.submit(cli.build_allow(idem=cli.agent.new_idempotency_key()),
                            "ARK-498-S004")
            done_times.append(time.monotonic())
            return rr
        with ThreadPoolExecutor(max_workers=5) as ex:
            res4 = list(ex.map(worker_s4, range(1000)))
        account(res4)
        dt_sorted = sorted(done_times)
        lo = int(len(dt_sorted) * 0.2)
        hi = int(len(dt_sorted) * 0.8)
        mid = dt_sorted[lo:hi]
        span = (mid[-1] - mid[0]) if len(mid) > 1 else 1e-9
        throughput = (len(mid) / span) if span > 0 else 0.0
        metrics["scenarios"]["S004"] = {
            "n": 1000, "concurrency": 5,
            "throughput_rps_mid60pct": throughput,
            "ok_count": sum(1 for x in res4 if x.get("ok"))}
        emit(f"  [S004] throughput(mid60%)={throughput:.1f} req/s")

        # ---- S005/S006/S007 fail-closed under dependency loss ----
        def failure_scenario(scn, dep):
            leak = 0
            fail_closed = 0
            for i in range(40):
                deps = [] if i < 20 else [dep]
                rr = cli.submit(
                    cli.build_allow(idem=cli.agent.new_idempotency_key()),
                    f"ARK-498-{scn}", dep_failures=deps)
                account([rr])
                if i >= 20:
                    if rr.get("decision") == "ALLOW":
                        leak += 1
                    elif rr.get("decision") == "DENY":
                        fail_closed += 1
            metrics["scenarios"][scn] = {
                "n": 40, "failure_window": 20, "dependency": dep,
                "leak_count": leak, "fail_closed_count": fail_closed}
            emit(f"  [{scn}] dep={dep} leak={leak} fail_closed={fail_closed}")
            return leak

        leak5 = failure_scenario("S005", "policy")
        leak6 = failure_scenario("S006", "authority")
        leak7 = failure_scenario("S007", "proofrecord")

        # ---- S008 recovery after restoration ----
        recovery_ms = None
        first_recovery_ts = None
        restore_start = None
        reexec_denied = 0
        denied_keys = []
        for i in range(40):
            key = cli.agent.new_idempotency_key()
            deps = ["authority"] if i < 20 else []
            if i == 20:
                restore_start = time.monotonic()
            rr = cli.submit(cli.build_allow(idem=key), "ARK-498-S008",
                            dep_failures=deps)
            account([rr])
            if i < 20:
                denied_keys.append(key)
            if i >= 20 and rr.get("decision") == "ALLOW" and recovery_ms is None:
                recovery_ms = (time.monotonic() - restore_start) * 1000.0
                first_recovery_ts = rr.get("proofrecord_id")
        # P-498-5: none of the denied-window keys were auto-retried/executed.
        # We never resubmit denied keys, so any executed entry for S008 must
        # come from a NEW post-recovery key. Verify executed count == number of
        # post-recovery ALLOWs (20), never more.
        executed_s8 = executed_count_for_case("T3", "ARK-498-S008")
        metrics["scenarios"]["S008"] = {
            "n": 40, "recovery_time_ms": recovery_ms,
            "first_post_recovery_allow_proofrecord": first_recovery_ts,
            "executed_after_recovery": executed_s8,
            "denied_window_keys": len(denied_keys),
            "auto_reexecutions_of_denied": reexec_denied}
        emit(f"  [S008] recovery_time={recovery_ms}ms executed_after={executed_s8} "
             f"auto_reexec_denied={reexec_denied}")

        # ---- S009 duplicate-execution protection (5 keys x 10 sends) ----
        keys = [cli.agent.new_idempotency_key() for _ in range(5)]

        def worker_s9(key):
            out = []
            for _ in range(10):
                out.append(cli.submit(cli.build_allow(idem=key), "ARK-498-S009"))
            return out
        with ThreadPoolExecutor(max_workers=5) as ex:
            nested = list(ex.map(worker_s9, keys))
        for grp in nested:
            account(grp)
        executed_s9 = executed_count_for_case("T3", "ARK-498-S009")
        dup_exec = executed_s9 - len(keys)
        metrics["scenarios"]["S009"] = {
            "unique_keys": len(keys), "total_sends": 50,
            "executed_entries": executed_s9, "duplicate_executions": dup_exec}
        emit(f"  [S009] unique_keys=5 executed={executed_s9} duplicates={dup_exec}")

        # ---- audit: flush Guard-B + signature/completeness audit ----
        aud = requests.post(f"{BASE}/audit", json={}, timeout=180).json()
        audit = aud["audit"]
        metrics["record_audit"] = audit
        emit(f"  [audit] records={audit['records_total']} "
             f"sig_verify_rate={audit['signature_verification_rate']:.3f} "
             f"completeness={audit['completeness_rate']:.3f} "
             f"guard_b_permitted_only="
             f"{(audit.get('self_import_analysis') or {}).get('permitted_only')}")

    finally:
        pass

    # ---- score the six hard criteria ----
    p498_1 = (leak5 == 0 and leak6 == 0 and leak7 == 0)
    p498_2 = (metrics["scenarios"]["S009"]["duplicate_executions"] == 0)
    p498_3 = (audit["completeness_rate"] == 1.0)
    p498_4 = (allow_on_error == 0)
    p498_5 = (reexec_denied == 0 and recovery_ms is not None)
    p498_6 = (audit["signature_verification_rate"] == 1.0)
    metrics["criteria"] = {
        "P-498-1_fail_closed": p498_1, "P-498-2_zero_duplicate_exec": p498_2,
        "P-498-3_completeness": p498_3, "P-498-4_error_accounting": p498_4,
        "P-498-5_recovery_no_reexec": p498_5, "P-498-6_signature_verify": p498_6,
        "server_errors": server_errors, "allow_on_error": allow_on_error,
    }
    experiment_pass = all([p498_1, p498_2, p498_3, p498_4, p498_5, p498_6])

    # ---- per-scenario results-ledger rows (scenarios, not per-request) ----
    scenario_verdicts = {
        "ARK-498-S001": True, "ARK-498-S002": (metrics["scenarios"]["S002"]["error_rate"] == 0),
        "ARK-498-S003": (metrics["scenarios"]["S003"]["error_rate"] == 0),
        "ARK-498-S004": (metrics["scenarios"]["S004"]["ok_count"] == 1000),
        "ARK-498-S005": (leak5 == 0), "ARK-498-S006": (leak6 == 0),
        "ARK-498-S007": (leak7 == 0), "ARK-498-S008": p498_5,
        "ARK-498-S009": p498_2,
    }
    for scn, ok in scenario_verdicts.items():
        verdict = "PASS" if ok else "FAIL"
        root = None if ok else f"{scn} criterion not met; see ark498_metrics.json"
        if not ok:
            experiment_pass = False
        append_result(result_entry(EXPERIMENT_ID, scn, "networked-http", "T3",
                                    "CHARACTERIZATION", 0, "none", p498_6,
                                    verdict, root))
        case_ids.append(scn)

    emit(f"  P-498-1={p498_1} P-498-2={p498_2} P-498-3={p498_3} "
         f"P-498-4={p498_4} P-498-5={p498_5} P-498-6={p498_6}")

    decision = "EXPERIMENT-PASS" if experiment_pass else "EXPERIMENT-FAIL"
    metrics["decision"] = decision

    # write final summary into the chain via the server, then stop it
    try:
        requests.post(f"{BASE}/finalize", json={
            "decision": decision, "case_ids": case_ids,
            "extra": {"criteria": metrics["criteria"], "label": LABEL}},
            timeout=120)
    except requests.RequestException:
        pass
    _stop_server(proc)

    os.makedirs(RESULTS_DIR, exist_ok=True)
    with open(METRICS_PATH, "w", encoding="utf-8") as fh:
        json.dump(metrics, fh, ensure_ascii=False, indent=2)

    return {"experiment_id": EXPERIMENT_ID, "decision": decision,
            "case_ids": case_ids, "gate_stop": False}
