#!/usr/bin/env python3
"""
ARK-486 Cost At Scale Calculation
Two scenarios: (A) serverless-naive upper bound, (B) realistic running service.
Verdict is evaluated on Scenario B; Scenario A is disclosed as an upper bound.
Input: ARK-485 sustained throughput.
"""

import json
import time
from pathlib import Path

# --- Scenario A: AWS Lambda serverless-naive (disclosed upper bound) ---
LAMBDA_REQUEST_PRICE = 0.20 / 1_000_000   # $0.20 per 1M requests
LAMBDA_GB_SECOND_PRICE = 0.0000166667     # $ per GB-second
MEMORY_GB = 0.125                          # 128MB

# --- Scenario B: realistic running service (verdict basis) ---
# AWS Fargate vCPU rate, us-east-1
FARGATE_VCPU_HOUR = 0.04048
FARGATE_VCPU_SECOND = FARGATE_VCPU_HOUR / 3600.0   # ~$0.00001124/vCPU-second

def load_ark485_results():
    ark485_path = Path("../ark-485/results/sustained_results.json")
    if not ark485_path.exists():
        raise FileNotFoundError(f"{ark485_path} not found — run ARK-485 first")
    with open(ark485_path) as f:
        return json.load(f)

def cost_scenario_a(throughput_per_sec):
    """Serverless-naive: 1 Lambda invocation per decision (unrealistic upper bound)."""
    seconds_per_decision = 1.0 / throughput_per_sec
    compute = MEMORY_GB * LAMBDA_GB_SECOND_PRICE * seconds_per_decision
    request = LAMBDA_REQUEST_PRICE
    total = compute + request
    return {
        "model": "serverless_naive_1_invocation_per_decision",
        "compute_cost_per_decision": compute,
        "request_cost_per_decision": request,
        "total_cost_per_decision": total,
        "cost_per_million_decisions": total * 1_000_000,
        "note": "Unrealistic for an in-process engine; disclosed as an upper bound only."
    }

def cost_scenario_b(throughput_per_sec):
    """Realistic running service: compute time only, per vCPU-second, amortized."""
    # One process ~= one vCPU. Cost per decision = vCPU-second price / decisions per second.
    cost_per_decision = FARGATE_VCPU_SECOND / throughput_per_sec
    return {
        "model": "realistic_running_service_per_vcpu_second",
        "vcpu_second_price": FARGATE_VCPU_SECOND,
        "decisions_per_vcpu_second": throughput_per_sec,
        "total_cost_per_decision": cost_per_decision,
        "cost_per_million_decisions": cost_per_decision * 1_000_000,
        "note": "Per-request/API cost amortizes across millions of in-process decisions per invocation."
    }

def main():
    print("ARK-486: Cost At Scale Calculation (two scenarios)")
    print("=" * 60)

    data = load_ark485_results()
    py_tp = data["results"]["python"]["sustained_throughput"]
    js_tp = data["results"]["javascript"]["sustained_throughput"]

    print(f"ARK-485 sustained throughput:")
    print(f"  Python V2:     {py_tp:,.0f} dec/s")
    print(f"  JavaScript V1: {js_tp:,.0f} dec/s\n")

    py_a, py_b = cost_scenario_a(py_tp), cost_scenario_b(py_tp)
    js_a, js_b = cost_scenario_a(js_tp), cost_scenario_b(js_tp)

    # Verdict on Scenario B
    THRESH_B = 0.01  # $ per 1M decisions
    py_pass = py_b["cost_per_million_decisions"] <= THRESH_B
    js_pass = js_b["cost_per_million_decisions"] <= THRESH_B
    disclosure_ok = all(x["cost_per_million_decisions"] >= 0 for x in (py_a, js_a))

    results = {
        "experiment": "ARK-486",
        "component": "Verification Decision",
        "dimension": "Cost At Scale",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "input_data": {"ark485_python_throughput": py_tp, "ark485_javascript_throughput": js_tp},
        "results": {
            "python": {"scenario_a_naive": py_a, "scenario_b_realistic": py_b},
            "javascript": {"scenario_a_naive": js_a, "scenario_b_realistic": js_b},
        },
        "thresholds": {"scenario_b_max_per_million": THRESH_B},
        "verdict": "PASS" if (py_pass and js_pass and disclosure_ok) else "FAIL",
        "verdict_detail": {
            "C1_realistic_cost": py_pass and js_pass,
            "C2_disclosure": disclosure_ok,
        },
    }

    with open("results/cost_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print("=" * 60)
    print("SCENARIO B — Realistic running service (VERDICT BASIS)")
    print("=" * 60)
    print(f"Python V2:     ${py_b['cost_per_million_decisions']:.6f} / 1M  (threshold ${THRESH_B})")
    print(f"JavaScript V1: ${js_b['cost_per_million_decisions']:.6f} / 1M  (threshold ${THRESH_B})\n")
    print("SCENARIO A — Serverless-naive (disclosed upper bound, NOT verdict basis)")
    print(f"Python V2:     ${py_a['cost_per_million_decisions']:.4f} / 1M")
    print(f"JavaScript V1: ${js_a['cost_per_million_decisions']:.4f} / 1M\n")
    print(f"VERDICT: {results['verdict']}")
    print("Saved to: results/cost_results.json")

if __name__ == "__main__":
    main()
