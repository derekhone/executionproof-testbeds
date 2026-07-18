#!/usr/bin/env python3
"""
ARK-479 — Run all 8 arms (800 scenarios total) and compute metrics.

Arms:
  1: VALID-throughout → expect ALLOW
  2: REVOKED-before-approval → expect DENY
  3: REVOKED-after-approval-before-execution → expect DENY
  4: REVOKED-during-multistep → expect DENY
  5: IN-FLIGHT-at-execution → expect HOLD
  6: REVOKED-then-REAUTHORIZED → expect ALLOW
  7: IN-FLIGHT-boundary → expect HOLD
  8: REVOKED-after-execution → expect ALLOW

Metrics (from ARK-451 pattern):
  - g_allow_valid_min = min ALLOW rate across arms {1, 6, 8}
  - g_deny_revoked_min = min DENY rate across arms {2, 3, 4}
  - g_hold_inflight_min = min HOLD rate across arms {5, 7}
  - g_margin = min(g_allow_valid_min, g_deny_revoked_min, g_hold_inflight_min) - 0.05

Pass criteria:
  C1: g_allow_valid_min ≥ 0.95
  C2: g_deny_revoked_min ≥ 0.95
  C3: g_hold_inflight_min ≥ 0.95
  C4: g_margin ≥ 0.90
  Verdict = PASS iff C1 ∧ C2 ∧ C3 ∧ C4, else FAIL.
"""
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).parent
GENERATOR = HERE / "generator/scenario_generator.py"
V1_GUARD = HERE / "verifiers/v1_guard.js"
V2_GUARD = HERE / "verifiers/v2_guard.py"
RESULTS_DIR = HERE / "results"

ARM_NAMES = {
    1: "VALID-throughout",
    2: "REVOKED-before-approval",
    3: "REVOKED-after-approval-before-execution",
    4: "REVOKED-during-multistep",
    5: "IN-FLIGHT-at-execution",
    6: "REVOKED-then-REAUTHORIZED",
    7: "IN-FLIGHT-boundary",
    8: "REVOKED-after-execution"
}

ARM_EXPECTS = {
    1: "ALLOW", 2: "DENY", 3: "DENY", 4: "DENY",
    5: "HOLD", 6: "ALLOW", 7: "HOLD", 8: "ALLOW"
}

def run_arm(arm: int, n: int = 100):
    """Generate scenarios, run both guards, collect results."""
    print(f"\n{'='*70}")
    print(f"ARM {arm}: {ARM_NAMES[arm]} (expect {ARM_EXPECTS[arm]}, n={n})")
    print('='*70)
    
    # Generate scenarios
    cmd = ["python3", "-c", f"from generator.scenario_generator import generate_arm; import json; print(json.dumps(generate_arm({arm}, {n})))"]
    scenarios_json = subprocess.check_output(cmd, cwd=HERE, text=True)
    scenarios = json.loads(scenarios_json)
    
    # Save scenarios
    scenarios_file = RESULTS_DIR / f"arm_{arm}_scenarios.json"
    with open(scenarios_file, "w") as f:
        json.dump(scenarios, f, indent=2)
    print(f"  Generated {len(scenarios)} scenarios → {scenarios_file.name}")
    
    # Run V2 guard (Python)
    v2_proc = subprocess.run(
        ["python3", str(V2_GUARD)],
        input=scenarios_json, capture_output=True, text=True
    )
    v2_results = json.loads(v2_proc.stdout)
    
    # Run V1 guard (JavaScript)
    v1_proc = subprocess.run(
        ["node", str(V1_GUARD)],
        input=scenarios_json, capture_output=True, text=True
    )
    v1_results = json.loads(v1_proc.stdout)
    
    # Combine and analyze
    combined = []
    concordance_count = 0
    decision_counts = {"ALLOW": 0, "DENY": 0, "HOLD": 0}
    expect = ARM_EXPECTS[arm]
    correct_count = 0
    
    for i, sc in enumerate(scenarios):
        v1_decision = v1_results[i]["decision"]
        v2_decision = v2_results[i]["decision"]
        concordant = (v1_decision == v2_decision)
        if concordant:
            concordance_count += 1
        decision = v2_decision  # use V2 as canonical
        decision_counts[decision] += 1
        if decision == expect:
            correct_count += 1
        combined.append({
            "scenario_id": sc["scenario_id"],
            "arm": arm,
            "v1_decision": v1_decision,
            "v2_decision": v2_decision,
            "concordant": concordant,
            "decision": decision
        })
    
    results_file = RESULTS_DIR / f"arm_{arm}_results.json"
    with open(results_file, "w") as f:
        json.dump(combined, f, indent=2)
    
    concordance_rate = concordance_count / len(scenarios)
    correctness_rate = correct_count / len(scenarios)
    
    print(f"  ALLOW={decision_counts['ALLOW']} DENY={decision_counts['DENY']} HOLD={decision_counts['HOLD']}")
    print(f"  Correctness (vs {expect}): {correct_count}/{len(scenarios)} = {correctness_rate:.4f}")
    print(f"  V1↔V2 concordance: {concordance_count}/{len(scenarios)} = {concordance_rate:.4f}")
    
    return {
        "arm": arm,
        "name": ARM_NAMES[arm],
        "expect": expect,
        "n": len(scenarios),
        "decision_counts": decision_counts,
        "correctness": correctness_rate,
        "concordance": concordance_rate
    }

def main():
    RESULTS_DIR.mkdir(exist_ok=True)
    
    print("="*70)
    print("ARK-479 — Production API Rate Limit · Revocation At Execution")
    print("="*70)
    
    arm_results = []
    for arm in range(1, 9):
        res = run_arm(arm, n=100)
        arm_results.append(res)
    
    # Compute global metrics
    allow_arms = [1, 6, 8]
    deny_arms = [2, 3, 4]
    hold_arms = [5, 7]
    
    g_allow_valid_min = min(
        arm_results[a-1]["correctness"] for a in allow_arms
    )
    g_deny_revoked_min = min(
        arm_results[a-1]["correctness"] for a in deny_arms
    )
    g_hold_inflight_min = min(
        arm_results[a-1]["correctness"] for a in hold_arms
    )
    g_margin = min(g_allow_valid_min, g_deny_revoked_min, g_hold_inflight_min) - 0.05
    
    overall_concordance = sum(r["concordance"] * r["n"] for r in arm_results) / sum(r["n"] for r in arm_results)
    
    # Pass criteria
    c1 = g_allow_valid_min >= 0.95
    c2 = g_deny_revoked_min >= 0.95
    c3 = g_hold_inflight_min >= 0.95
    c4 = g_margin >= 0.90
    verdict = "PASS" if (c1 and c2 and c3 and c4) else "FAIL"
    
    overall = {
        "experiment": "ARK-479",
        "title": "Production API Rate Limit · Revocation At Execution",
        "total_scenarios": sum(r["n"] for r in arm_results),
        "arms": arm_results,
        "metrics": {
            "g_allow_valid_min": round(g_allow_valid_min, 4),
            "g_deny_revoked_min": round(g_deny_revoked_min, 4),
            "g_hold_inflight_min": round(g_hold_inflight_min, 4),
            "g_margin": round(g_margin, 4),
            "overall_concordance": round(overall_concordance, 4)
        },
        "criteria": {
            "C1_allow_valid": {"threshold": 0.95, "value": round(g_allow_valid_min, 4), "pass": c1},
            "C2_deny_revoked": {"threshold": 0.95, "value": round(g_deny_revoked_min, 4), "pass": c2},
            "C3_hold_inflight": {"threshold": 0.95, "value": round(g_hold_inflight_min, 4), "pass": c3},
            "C4_margin": {"threshold": 0.90, "value": round(g_margin, 4), "pass": c4}
        },
        "verdict": verdict
    }
    
    with open(RESULTS_DIR / "overall_results.json", "w") as f:
        json.dump(overall, f, indent=2)
    
    print("\n" + "="*70)
    print("OVERALL RESULTS")
    print("="*70)
    print(f"g_allow_valid_min   = {g_allow_valid_min:.4f} (C1: ≥ 0.95) {'✓' if c1 else '✗'}")
    print(f"g_deny_revoked_min  = {g_deny_revoked_min:.4f} (C2: ≥ 0.95) {'✓' if c2 else '✗'}")
    print(f"g_hold_inflight_min = {g_hold_inflight_min:.4f} (C3: ≥ 0.95) {'✓' if c3 else '✗'}")
    print(f"g_margin            = {g_margin:.4f} (C4: ≥ 0.90) {'✓' if c4 else '✗'}")
    print(f"Overall concordance = {overall_concordance:.4f}")
    print(f"\n{'='*70}")
    print(f"VERDICT: {verdict}")
    print('='*70)

if __name__ == "__main__":
    main()
