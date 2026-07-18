#!/usr/bin/env python3
"""
ARK-483 — Verification Decision Latency (Python, V2 component).

Measures the wall-clock latency of a single ExecutionProof *verification
decision*, using the ARK-458 exact-action-binding guard as the Component Under
Test (CUT). This is the first RF latency measurement — it answers Prospect
Question #2 ("What is the verification latency?").

Methodology (preregistered):
  - CUT: ark-458/verifiers/v2_guard.py :: evaluate() (imported directly,
    in-process — measures the decision itself, not process spawn or I/O).
  - Two decision paths measured separately:
      * ALLOW path : exact match — the guard must compare all 5 dimensions.
      * DENY path  : first-dimension mismatch — early-exit (fastest realistic).
      * DENY-last  : last-dimension mismatch — worst-case DENY (all 5 compared).
  - Warmup iterations discarded; cold-start (first call) recorded separately.
  - Timed with time.perf_counter_ns() around a single evaluate() call, repeated
    N times; per-call latency recorded; percentiles computed from the sample.
  - Environment (CPU, Python, OS) captured for bounded-claim discipline.

Absolute numbers are bounded to the machine reported in the results file.
"""
import json
import platform
import statistics
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
# Import the ARK-458 guard as the component under test.
sys.path.insert(0, str(REPO / "ark-458"))
from verifiers.v2_guard import evaluate  # noqa: E402

WARMUP = 5000
N = 100000  # timed iterations per path

BASE_BINDING = {
    "principal": "arn:aws:iam::100000000042:user/svc-0042",
    "role": "ReadOnlyAuditor",
    "account": "100000000042",
    "permission_set": "ps-0123456789abcdef",
    "condition": "region=us-east-1;mfa=true",
}


def _scenario(mutate_dim=None, mutate_val="__X__"):
    binding = dict(BASE_BINDING)
    action = dict(BASE_BINDING)
    if mutate_dim is not None:
        action[mutate_dim] = mutate_val
    return {"scenario_id": "bench", "arm": 0,
            "authorization": {"binding": binding}, "execution": {"action": action}}


def _time_path(scenario, n, expect):
    # sanity: confirm the path yields the expected decision
    d = evaluate(scenario)["decision"]
    assert d == expect, f"expected {expect} got {d}"
    samples_ns = []
    perf = time.perf_counter_ns
    for _ in range(n):
        t0 = perf()
        evaluate(scenario)
        t1 = perf()
        samples_ns.append(t1 - t0)
    return samples_ns


def _summ(samples_ns):
    s = sorted(samples_ns)
    n = len(s)
    def pct(p):
        idx = min(n - 1, int(round(p / 100.0 * (n - 1))))
        return s[idx]
    us = 1000.0
    return {
        "n": n,
        "mean_us": round(statistics.fmean(s) / us, 4),
        "median_us": round(statistics.median(s) / us, 4),
        "p50_us": round(pct(50) / us, 4),
        "p95_us": round(pct(95) / us, 4),
        "p99_us": round(pct(99) / us, 4),
        "p999_us": round(pct(99.9) / us, 4),
        "min_us": round(s[0] / us, 4),
        "max_us": round(s[-1] / us, 4),
        "stdev_us": round(statistics.pstdev(s) / us, 4),
        "throughput_decisions_per_sec": round(1e9 / statistics.fmean(s), 0),
    }


def main():
    print("=" * 70)
    print("ARK-483 — Verification Decision Latency (V2 / Python component)")
    print("=" * 70)

    # Cold start: first-ever call latency (import already done; measures first eval).
    cold = _scenario()
    perf = time.perf_counter_ns
    t0 = perf(); evaluate(cold); t1 = perf()
    cold_start_us = round((t1 - t0) / 1000.0, 4)
    print(f"Cold-start (first decision): {cold_start_us} us")

    # Warmup
    warm_sc = _scenario()
    for _ in range(WARMUP):
        evaluate(warm_sc)

    paths = {
        "allow_exact_match": (_scenario(), "ALLOW"),
        "deny_first_dim_mismatch": (_scenario("principal", "arn:aws:iam::999:user/x"), "DENY"),
        "deny_last_dim_mismatch": (_scenario("condition", "region=*;mfa=false"), "DENY"),
    }

    results = {}
    for name, (sc, expect) in paths.items():
        print(f"\nMeasuring path '{name}' (expect {expect}, n={N})...")
        samples = _time_path(sc, N, expect)
        summ = _summ(samples)
        results[name] = summ
        print(f"  mean={summ['mean_us']}us  p50={summ['p50_us']}us  "
              f"p95={summ['p95_us']}us  p99={summ['p99_us']}us  "
              f"max={summ['max_us']}us  thpt={summ['throughput_decisions_per_sec']:.0f}/s")

    env = {
        "python_version": platform.python_version(),
        "implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "processor": platform.processor() or "unknown",
        "machine": platform.machine(),
        "perf_counter_resolution_ns": time.get_clock_info("perf_counter").resolution * 1e9,
    }

    # Preregistered ceiling for a single in-process verification decision.
    p95_ceiling_us = 1000.0  # 1 ms
    worst_p95 = max(r["p95_us"] for r in results.values())
    ceiling_pass = worst_p95 <= p95_ceiling_us

    out = {
        "experiment": "ARK-483",
        "title": "Verification Decision Latency",
        "component_under_test": "ark-458/verifiers/v2_guard.py::evaluate (exact-action-binding)",
        "substrate": "classical software (in-process, no I/O, no network)",
        "run_time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "warmup_iterations": WARMUP,
        "timed_iterations_per_path": N,
        "cold_start_us": cold_start_us,
        "paths": results,
        "environment": env,
        "preregistered_p95_ceiling_us": p95_ceiling_us,
        "worst_path_p95_us": worst_p95,
        "ceiling_pass": ceiling_pass,
        "verdict": "PASS" if ceiling_pass else "FAIL",
        "bounds_note": ("Absolute latencies are bounded to the environment above. "
                        "Measures the in-process decision only; excludes network, "
                        "auth-token retrieval, evidence persistence, and process startup."),
    }

    results_dir = HERE.parent / "results"
    results_dir.mkdir(exist_ok=True)
    with open(results_dir / "latency_v2_python.json", "w") as f:
        json.dump(out, f, indent=2)

    print(f"\n{'=' * 70}")
    print(f"Worst-path P95 = {worst_p95} us  (ceiling {p95_ceiling_us} us)  -> "
          f"{'PASS' if ceiling_pass else 'FAIL'}")
    print(f"{'=' * 70}")
    return out


if __name__ == "__main__":
    main()
