#!/usr/bin/env python3
"""
Evidence Engine performance harness (ARK-492).

Measures ONE performance dimension per invocation against the reference
EvidenceEngine, and additionally verifies the engine still DECIDES CORRECTLY:
an intact record verifies (ALLOW), a tampered record fails (DENY), and a
broken chain fails (DENY) — the RF "no unjustified ALLOW" gate applied to
tamper-evidence.

Usage:
    python3 perf_harness.py --dimension cold_start --out results/coldstart_results.json
"""
import argparse
import json
import time
import statistics
import copy
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent))
from evidence_engine import build_reference_engine, EvidenceEngine


def correctness_gate(eng):
    """Intact record -> ALLOW; tampered record -> DENY; broken chain -> DENY."""
    intact = eng.verify_record(5)["decision"] == "ALLOW"

    # Tamper: mutate content of a copied engine's record and re-verify
    e2 = copy.deepcopy(eng)
    e2._chain[5]["action"] = "deploy:svc-EVIL"
    tampered = e2.verify_record(5)["decision"] == "DENY"

    # Broken chain: corrupt a prev_hash link
    e3 = copy.deepcopy(eng)
    e3._chain[6]["prev_hash"] = "f" * 64
    broken = e3.verify_record(6)["decision"] == "DENY"

    ok = intact and tampered and broken
    return ok, {"intact_allow": intact, "tampered_deny": tampered, "broken_chain_deny": broken}


def measure_cold_start(eng_builder):
    """Time from engine construction to first correct evidence verification."""
    samples = []
    for _ in range(200):
        t0 = time.perf_counter()
        eng = eng_builder()
        eng.verify_record(0)
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dimension", required=True, choices=["cold_start"])
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    eng = build_reference_engine()
    ok, detail = correctness_gate(eng)
    print(f"Correctness gate: {'PASS' if ok else 'FAIL'} {detail}")

    if args.dimension == "cold_start":
        m = measure_cold_start(build_reference_engine)

    out = {
        "component": "Evidence Engine",
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
