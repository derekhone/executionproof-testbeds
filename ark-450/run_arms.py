#!/usr/bin/env python3
"""
ARK-450 Full Execution Harness
Runs all 8 arms (800 scenarios total) and computes final verdict.
"""

import json
import subprocess
import sys
from collections import defaultdict

# Import generator
sys.path.insert(0, 'generator')
from scenario_generator import generate_all_scenarios, is_substitution_effective


def run_arm(arm_id, scenarios):
    """Execute one arm with both guards and return results."""
    print(f"\nArm {arm_id}: Processing {len(scenarios)} scenarios...")
    
    # Save arm scenarios to temp file
    arm_file = f"results/arm_{arm_id}_scenarios.json"
    with open(arm_file, "w") as f:
        json.dump(scenarios, f)
    
    # Run V1 (JavaScript)
    v1_result = subprocess.run(
        ["node", "verifiers/v1_guard.js", arm_file],
        capture_output=True,
        text=True
    )
    v1_decisions = json.loads(v1_result.stdout)
    
    # Run V2 (Python)
    v2_result = subprocess.run(
        ["python3", "verifiers/v2_guard.py", arm_file],
        capture_output=True,
        text=True
    )
    v2_decisions = json.loads(v2_result.stdout)
    
    # Compute metrics
    v1_allow = sum(1 for d in v1_decisions if d["decision"] == "ALLOW")
    v1_deny = sum(1 for d in v1_decisions if d["decision"] == "DENY")
    v2_allow = sum(1 for d in v2_decisions if d["decision"] == "ALLOW")
    v2_deny = sum(1 for d in v2_decisions if d["decision"] == "DENY")
    
    # Check concordance
    concordance = sum(1 for v1, v2 in zip(v1_decisions, v2_decisions) if v1["decision"] == v2["decision"])
    concordance_rate = concordance / len(scenarios)
    
    # Check substitution effectiveness
    effective_count = sum(1 for s in scenarios if is_substitution_effective(s))
    effectiveness_rate = effective_count / len(scenarios)
    
    # Compute rates (using V1 as primary, since concordance should be 100%)
    rate_allow = v1_allow / len(scenarios)
    rate_deny = v1_deny / len(scenarios)
    
    arm_results = {
        "arm_id": arm_id,
        "scenario_count": len(scenarios),
        "v1_allow": v1_allow,
        "v1_deny": v1_deny,
        "v2_allow": v2_allow,
        "v2_deny": v2_deny,
        "rate_allow": rate_allow,
        "rate_deny": rate_deny,
        "concordance": concordance,
        "concordance_rate": concordance_rate,
        "effectiveness": effective_count,
        "effectiveness_rate": effectiveness_rate
    }
    
    # Save arm results
    with open(f"results/arm_{arm_id}_results.json", "w") as f:
        json.dump(arm_results, f, indent=2)
    
    print(f"  V1: {v1_allow} ALLOW, {v1_deny} DENY")
    print(f"  V2: {v2_allow} ALLOW, {v2_deny} DENY")
    print(f"  Concordance: {concordance}/{len(scenarios)} = {concordance_rate:.4f}")
    print(f"  Effectiveness: {effective_count}/{len(scenarios)} = {effectiveness_rate:.4f}")
    
    return arm_results


def compute_overall_metrics(arm_results):
    """Compute overall metrics across all arms."""
    print("\n" + "=" * 60)
    print("OVERALL METRICS")
    print("=" * 60)
    
    # C1: Exact-match allowance (Arm 1 baseline)
    arm1_data = [r for r in arm_results if r["arm_id"] == 1][0]
    g_allow_exact_min = arm1_data["rate_allow"]
    
    # C2: Substitution rejection (Arms 2-8 minimum DENY rate)
    attack_arms = [r for r in arm_results if r["arm_id"] >= 2]
    g_deny_substitution_min = min(r["rate_deny"] for r in attack_arms)
    
    # C3: Separation margin
    g_margin = g_allow_exact_min - (1 - g_deny_substitution_min)
    
    # Total concordance
    total_scenarios = sum(r["scenario_count"] for r in arm_results)
    total_concordance = sum(r["concordance"] for r in arm_results)
    total_concordance_rate = total_concordance / total_scenarios
    
    # Total effectiveness
    total_effectiveness = sum(r["effectiveness"] for r in arm_results)
    total_effectiveness_rate = total_effectiveness / total_scenarios
    
    print(f"\nPrimary Metrics:")
    print(f"  C1 (g_allow_exact_min):        {g_allow_exact_min:.4f} (threshold ≥ 0.95)")
    print(f"  C2 (g_deny_substitution_min):  {g_deny_substitution_min:.4f} (threshold ≥ 0.95)")
    print(f"  C3 (g_margin):                  {g_margin:.4f} (threshold ≥ 0.90)")
    
    print(f"\nSecondary Metrics:")
    print(f"  Total concordance: {total_concordance}/{total_scenarios} = {total_concordance_rate:.4f}")
    print(f"  Total effectiveness: {total_effectiveness}/{total_scenarios} = {total_effectiveness_rate:.4f}")
    
    # Determine verdict
    c1_pass = g_allow_exact_min >= 0.95
    c2_pass = g_deny_substitution_min >= 0.95
    c3_pass = g_margin >= 0.90
    
    verdict = "PASS" if (c1_pass and c2_pass and c3_pass) else "FAIL"
    
    print(f"\nCriterion Results:")
    print(f"  C1: {'✅ PASS' if c1_pass else '❌ FAIL'}")
    print(f"  C2: {'✅ PASS' if c2_pass else '❌ FAIL'}")
    print(f"  C3: {'✅ PASS' if c3_pass else '❌ FAIL'}")
    
    print(f"\n{'=' * 60}")
    print(f"VERDICT: {verdict}")
    print(f"{'=' * 60}")
    
    overall_results = {
        "total_scenarios": total_scenarios,
        "g_allow_exact_min": g_allow_exact_min,
        "g_deny_substitution_min": g_deny_substitution_min,
        "g_margin": g_margin,
        "total_concordance": total_concordance,
        "total_concordance_rate": total_concordance_rate,
        "total_effectiveness": total_effectiveness,
        "total_effectiveness_rate": total_effectiveness_rate,
        "c1_pass": c1_pass,
        "c2_pass": c2_pass,
        "c3_pass": c3_pass,
        "verdict": verdict,
        "arm_results": arm_results
    }
    
    return overall_results


def main():
    print("ARK-450 Full Execution")
    print("=" * 60)
    print("Generating 8 arms × 100 scenarios = 800 total\n")
    
    # Generate all scenarios
    all_scenarios = generate_all_scenarios(scenarios_per_arm=100)
    
    print(f"Generated {len(all_scenarios)} scenarios")
    
    # Group by arm
    scenarios_by_arm = defaultdict(list)
    for scenario in all_scenarios:
        scenarios_by_arm[scenario["arm_id"]].append(scenario)
    
    # Execute each arm
    arm_results = []
    for arm_id in range(1, 9):
        arm_scenarios = scenarios_by_arm[arm_id]
        arm_result = run_arm(arm_id, arm_scenarios)
        arm_results.append(arm_result)
    
    # Compute overall metrics
    overall_results = compute_overall_metrics(arm_results)
    
    # Save overall results
    with open("results/overall_results.json", "w") as f:
        json.dump(overall_results, f, indent=2)
    
    print("\nResults saved to results/ directory")
    
    if overall_results["verdict"] == "FAIL":
        print("\n⚠️  Experiment FAILED - Authorization binding is broken")
        sys.exit(1)
    else:
        print("\n✅ Experiment PASSED - Authorization strictly bound to exact actions")


if __name__ == "__main__":
    main()
