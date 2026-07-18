#!/usr/bin/env python3
"""
Authority Engine performance harness (ARK-487..491).

Measures ONE performance dimension per invocation against the reference
AuthorityEngine, and additionally verifies the engine still DECIDES CORRECTLY
under load (the RF "without an unjustified ALLOW" gate).

Usage:
    python3 perf_harness.py --dimension cold_start   --out results/x.json
    python3 perf_harness.py --dimension p95_latency  --out results/x.json
    python3 perf_harness.py --dimension burst        --out results/x.json
    python3 perf_harness.py --dimension sustained    --out results/x.json
    python3 perf_harness.py --dimension cost          --out results/x.json
"""
import argparse
import json
import time
import statistics
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent))
from authority_engine import build_reference_engine

# A known-good (ALLOW) key and a known-bad (DENY) key for correctness checks
GOOD_PID = "user-00001"
GOOD_KEY = ("role-3", "acct-001", "arn:aws:svc:::res-3", "cond-3")
BAD_PID = "user-00001"
BAD_KEY = ("role-9", "acct-999", "arn:aws:svc:::res-9", "cond-BADMUTATION")
REVOKED_PID = "user-00000"
REVOKED_KEY = ("role-0", "acct-000", "arn:aws:svc:::res-0", "cond-0")


def correctness_gate(eng):
    """Engine must ALLOW the valid grant, DENY the mutated one, DENY the revoked one."""
    a = eng.check_authority(GOOD_PID, GOOD_KEY)["decision"] == "ALLOW"
    b = eng.check_authority(BAD_PID, BAD_KEY)["decision"] == "DENY"
    c = eng.check_authority(REVOKED_PID, REVOKED_KEY)["decision"] == "DENY"
    return a and b and c, {"valid_allow": a, "mutated_deny": b, "revoked_deny": c}


def measure_cold_start(eng_builder):
    """Time from engine construction to first decision."""
    samples = []
    for _ in range(200):
        t0 = time.perf_counter()
        eng = eng_builder()
        eng.check_authority(GOOD_PID, GOOD_KEY)
        samples.append((time.perf_counter() - t0) * 1e6)  # microseconds
    return {
        "metric": "cold_start_us",
        "runs": len(samples),
        "mean_us": statistics.mean(samples),
        "median_us": statistics.median(samples),
        "p95_us": sorted(samples)[int(0.95 * len(samples)) - 1],
        "min_us": min(samples),
        "max_us": max(samples),
    }


def measure_p95_latency(eng):
    """Per-decision latency distribution on a warm engine."""
    n = 200_000
    # warmup
    for _ in range(10_000):
        eng.check_authority(GOOD_PID, GOOD_KEY)
    samples = []
    for _ in range(n):
        t0 = time.perf_counter()
        eng.check_authority(GOOD_PID, GOOD_KEY)
        samples.append((time.perf_counter() - t0) * 1e6)
    samples.sort()
    return {
        "metric": "latency_us",
        "iterations": n,
        "mean_us": statistics.mean(samples),
        "p50_us": samples[int(0.50 * n) - 1],
        "p95_us": samples[int(0.95 * n) - 1],
        "p99_us": samples[int(0.99 * n) - 1],
        "max_us": samples[-1],
    }


def measure_burst(eng, duration_sec=10):
    """Peak decisions/sec in a short burst."""
    for _ in range(10_000):
        eng.check_authority(GOOD_PID, GOOD_KEY)
    count = 0
    correct = 0
    start = time.perf_counter()
    end = start + duration_sec
    while time.perf_counter() < end:
        r = eng.check_authority(GOOD_PID, GOOD_KEY)
        count += 1
        if r["decision"] == "ALLOW":
            correct += 1
    elapsed = time.perf_counter() - start
    return {
        "metric": "burst_throughput_dps",
        "duration_sec": elapsed,
        "total_decisions": count,
        "correct_decisions": correct,
        "accuracy": correct / count,
        "throughput_dps": count / elapsed,
    }


def measure_sustained(eng, duration_sec=60):
    """Sustained decisions/sec over a longer window."""
    warm_start = time.perf_counter()
    while time.perf_counter() - warm_start < 5:
        eng.check_authority(GOOD_PID, GOOD_KEY)
    count = 0
    correct = 0
    start = time.perf_counter()
    end = start + duration_sec
    while time.perf_counter() < end:
        r = eng.check_authority(GOOD_PID, GOOD_KEY)
        count += 1
        if r["decision"] == "ALLOW":
            correct += 1
    elapsed = time.perf_counter() - start
    return {
        "metric": "sustained_throughput_dps",
        "duration_sec": elapsed,
        "total_decisions": count,
        "correct_decisions": correct,
        "accuracy": correct / count,
        "throughput_dps": count / elapsed,
    }


def measure_cost(eng, duration_sec=10):
    """Marginal compute cost per decision (realistic running-service model)."""
    FARGATE_VCPU_SECOND = 0.04048 / 3600.0
    b = measure_burst(eng, duration_sec)
    tp = b["throughput_dps"]
    cost_per_decision = FARGATE_VCPU_SECOND / tp
    return {
        "metric": "cost_at_scale",
        "throughput_dps": tp,
        "vcpu_second_price": FARGATE_VCPU_SECOND,
        "cost_per_decision": cost_per_decision,
        "cost_per_million_decisions": cost_per_decision * 1_000_000,
        "naive_serverless_per_million": 0.20 + (0.125 * 0.0000166667 / tp) * 1_000_000,
        "accuracy": b["accuracy"],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dimension", required=True,
                    choices=["cold_start", "p95_latency", "burst", "sustained", "cost"])
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    eng = build_reference_engine()
    ok, detail = correctness_gate(eng)
    print(f"Correctness gate: {'PASS' if ok else 'FAIL'} {detail}")

    if args.dimension == "cold_start":
        m = measure_cold_start(build_reference_engine)
    elif args.dimension == "p95_latency":
        m = measure_p95_latency(eng)
    elif args.dimension == "burst":
        m = measure_burst(eng)
    elif args.dimension == "sustained":
        m = measure_sustained(eng)
    elif args.dimension == "cost":
        m = measure_cost(eng)

    out = {
        "component": "Authority Engine",
        "dimension": args.dimension,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "correctness_gate": {"passed": ok, "detail": detail},
        "measurement": m,
    }
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(out, f, indent=2)
    print(json.dumps(m, indent=2))
    print(f"Saved to {args.out}")


if __name__ == "__main__":
    main()
