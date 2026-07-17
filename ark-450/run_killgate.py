#!/usr/bin/env python3
"""
ARK-450 Kill-Gate Calibration
Verifies that substitution scenarios are genuinely effective before full execution.
"""

import json
import sys
import subprocess
import random

# Import generator to reuse oracle
sys.path.insert(0, 'generator')
from scenario_generator import is_substitution_effective, generate_arm_scenarios


def run_killgate_calibration(sample_size_per_arm=11):
    """
    Generate small sample of scenarios and verify effectiveness oracle.
    """
    print("ARK-450 Kill-Gate Calibration")
    print("=" * 60)
    print(f"Generating {sample_size_per_arm} scenarios per arm (8 arms)\n")
    
    all_scenarios = []
    for arm_id in range(1, 9):
        arm_scenarios = generate_arm_scenarios(arm_id, count=sample_size_per_arm)
        all_scenarios.extend(arm_scenarios)
    
    print(f"Total scenarios: {len(all_scenarios)}")
    
    # Run effectiveness oracle
    print("\nRunning substitution-effectiveness oracle...")
    effectiveness_results = {
        "by_arm": {},
        "total_effective": 0,
        "total_ineffective": 0
    }
    
    for arm_id in range(1, 9):
        effectiveness_results["by_arm"][arm_id] = {
            "effective": 0,
            "ineffective": 0,
            "rate": 0.0
        }
    
    for scenario in all_scenarios:
        is_effective = is_substitution_effective(scenario)
        arm_id = scenario["arm_id"]
        
        if is_effective:
            effectiveness_results["total_effective"] += 1
            effectiveness_results["by_arm"][arm_id]["effective"] += 1
        else:
            effectiveness_results["total_ineffective"] += 1
            effectiveness_results["by_arm"][arm_id]["ineffective"] += 1
    
    # Compute rates
    for arm_id in range(1, 9):
        arm_data = effectiveness_results["by_arm"][arm_id]
        total_arm = arm_data["effective"] + arm_data["ineffective"]
        if total_arm > 0:
            arm_data["rate"] = arm_data["effective"] / total_arm
    
    print("\nEffectiveness Results:")
    print(f"  Total scenarios: {len(all_scenarios)}")
    print(f"  Effective: {effectiveness_results['total_effective']}")
    print(f"  Ineffective: {effectiveness_results['total_ineffective']}")
    print("\nPer-arm effectiveness rates:")
    
    gate_pass = True
    for arm_id in range(1, 9):
        arm_data = effectiveness_results["by_arm"][arm_id]
        rate = arm_data["rate"]
        status = "✅ PASS" if rate == 1.0 else "❌ FAIL"
        print(f"  Arm {arm_id}: {arm_data['effective']}/{sample_size_per_arm} = {rate:.4f} {status}")
        if rate < 1.0:
            gate_pass = False
    
    # Test dual-guard concordance on sample
    print("\n" + "=" * 60)
    print("Testing dual-guard concordance on sample...")
    
    # Save scenarios to temp file
    with open("results/killgate_scenarios.json", "w") as f:
        json.dump(all_scenarios, f, indent=2)
    
    # Run V1 (JavaScript)
    print("\nRunning V1 guard (JavaScript)...")
    v1_result = subprocess.run(
        ["node", "verifiers/v1_guard.js", "results/killgate_scenarios.json"],
        capture_output=True,
        text=True
    )
    v1_decisions = json.loads(v1_result.stdout)
    
    # Run V2 (Python)
    print("Running V2 guard (Python)...")
    v2_result = subprocess.run(
        ["python3", "verifiers/v2_guard.py", "results/killgate_scenarios.json"],
        capture_output=True,
        text=True
    )
    v2_decisions = json.loads(v2_result.stdout)
    
    # Check concordance
    concordance_count = 0
    discordance_count = 0
    
    for v1_dec, v2_dec in zip(v1_decisions, v2_decisions):
        if v1_dec["decision"] == v2_dec["decision"]:
            concordance_count += 1
        else:
            discordance_count += 1
            print(f"  DISCORDANCE: {v1_dec['scenario_id']} - V1={v1_dec['decision']}, V2={v2_dec['decision']}")
    
    concordance_rate = concordance_count / len(all_scenarios)
    
    print(f"\nConcordance: {concordance_count}/{len(all_scenarios)} = {concordance_rate:.4f}")
    
    if concordance_rate < 1.0:
        print("❌ CONCORDANCE FAIL - Guards disagree on some decisions")
        gate_pass = False
    else:
        print("✅ CONCORDANCE PASS - Perfect V1-V2 agreement")
    
    # Save calibration results
    calibration_results = {
        "sample_size_per_arm": sample_size_per_arm,
        "total_scenarios": len(all_scenarios),
        "effectiveness": effectiveness_results,
        "concordance": {
            "total": len(all_scenarios),
            "concordant": concordance_count,
            "discordant": discordance_count,
            "rate": concordance_rate
        },
        "gate_pass": gate_pass
    }
    
    with open("results/killgate_calibration.json", "w") as f:
        json.dump(calibration_results, f, indent=2)
    
    print("\n" + "=" * 60)
    if gate_pass:
        print("✅ KILL-GATE PASS")
        print("All arms show 100% substitution-effectiveness")
        print("Dual guards show perfect concordance")
        print("Proceeding to full execution is AUTHORIZED")
    else:
        print("❌ KILL-GATE FAIL")
        print("Test design is corrupt. DO NOT proceed to full execution.")
        print("Fix generator or guards before retrying.")
        sys.exit(1)
    
    return calibration_results


if __name__ == "__main__":
    run_killgate_calibration()
