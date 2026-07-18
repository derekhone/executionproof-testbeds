#!/usr/bin/env python3
"""
ARK-463 Arms Execution — Production Deployment · Exact-Action Binding

Executes all 800 scenarios against dual guards (V1 JS + V2 Python).
Measures concordance and computes metrics for PASS/FAIL verdict.
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, List

# Import V2 guard
sys.path.insert(0, str(Path(__file__).parent / "verifiers"))
from v2_guard import verify_deployment as v2_verify


def v1_verify_deployment(authorized: Dict[str, str], presented: Dict[str, str]) -> Dict[str, str]:
    """Call V1 JavaScript guard via Node.js"""
    js_code = f"""
    const {{ verifyDeployment }} = require('./verifiers/v1_guard.js');
    const authorized = {json.dumps(authorized)};
    const presented = {json.dumps(presented)};
    const result = verifyDeployment(authorized, presented);
    console.log(JSON.stringify(result));
    """
    
    result = subprocess.run(
        ["node", "-e", js_code],
        cwd=Path(__file__).parent,
        capture_output=True,
        text=True,
        timeout=5
    )
    
    if result.returncode != 0:
        raise RuntimeError(f"V1 guard failed: {result.stderr}")
    
    return json.loads(result.stdout.strip())


def execute_scenario(scenario: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a single scenario against both guards"""
    authorized = scenario["authorized_deployment"]
    presented = scenario["presented_deployment"]
    expected = scenario["expected_decision"]
    
    # V1 guard (JavaScript)
    v1_result = v1_verify_deployment(authorized, presented)
    v1_decision = v1_result["decision"]
    
    # V2 guard (Python)
    v2_result = v2_verify(authorized, presented)
    v2_decision = v2_result["decision"]
    
    # Check concordance
    concordant = (v1_decision == v2_decision)
    
    # Check correctness (against expected)
    v1_correct = (v1_decision == expected)
    v2_correct = (v2_decision == expected)
    
    return {
        "scenario_id": scenario["scenario_id"],
        "arm": scenario["arm"],
        "expected_decision": expected,
        "v1_decision": v1_decision,
        "v2_decision": v2_decision,
        "v1_reason": v1_result["reason"],
        "v2_reason": v2_result["reason"],
        "concordant": concordant,
        "v1_correct": v1_correct,
        "v2_correct": v2_correct
    }


def compute_metrics(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compute aggregate metrics from all results"""
    total = len(results)
    concordant_count = sum(1 for r in results if r["concordant"])
    
    # Per-arm metrics
    arm_metrics = {}
    for arm in range(1, 9):
        arm_results = [r for r in results if r["arm"] == arm]
        if not arm_results:
            continue
        
        arm_total = len(arm_results)
        arm_correct_v1 = sum(1 for r in arm_results if r["v1_correct"])
        arm_correct_v2 = sum(1 for r in arm_results if r["v2_correct"])
        
        arm_metrics[f"arm_{arm}"] = {
            "total": arm_total,
            "v1_correct": arm_correct_v1,
            "v2_correct": arm_correct_v2,
            "v1_accuracy": arm_correct_v1 / arm_total,
            "v2_accuracy": arm_correct_v2 / arm_total
        }
    
    # Global metrics
    # g_allow_exact: Arms 1, 8 (exact match → ALLOW)
    allow_arms = [r for r in results if r["arm"] in [1, 8]]
    allow_correct_v1 = sum(1 for r in allow_arms if r["v1_correct"])
    allow_correct_v2 = sum(1 for r in allow_arms if r["v2_correct"])
    g_allow_exact = min(allow_correct_v1, allow_correct_v2) / len(allow_arms) if allow_arms else 0.0
    
    # g_deny_mismatch_min: Arms 2-7 (mismatch → DENY), per-arm minimum
    deny_arm_accuracies = []
    for arm in range(2, 8):
        arm_results = [r for r in results if r["arm"] == arm]
        if arm_results:
            arm_correct = sum(1 for r in arm_results if r["v1_correct"] and r["v2_correct"])
            deny_arm_accuracies.append(arm_correct / len(arm_results))
    
    g_deny_mismatch_min = min(deny_arm_accuracies) if deny_arm_accuracies else 0.0
    
    # g_margin: safety margin
    g_margin = min(g_allow_exact, g_deny_mismatch_min)
    
    # Concordance
    concordance_rate = concordant_count / total
    
    # Verdict
    verdict = "PASS" if (
        g_allow_exact >= 0.95 and
        g_deny_mismatch_min >= 0.95 and
        g_margin >= 0.90 and
        concordance_rate >= 0.95
    ) else "FAIL"
    
    return {
        "total_scenarios": total,
        "concordant_count": concordant_count,
        "concordance_rate": concordance_rate,
        "g_allow_exact": g_allow_exact,
        "g_deny_mismatch_min": g_deny_mismatch_min,
        "g_margin": g_margin,
        "arm_metrics": arm_metrics,
        "verdict": verdict,
        "thresholds": {
            "g_allow_exact_min": 0.95,
            "g_deny_mismatch_min": 0.95,
            "g_margin_min": 0.90,
            "concordance_min": 0.95
        }
    }


def main():
    """Execute all arms and save results"""
    print("ARK-463 Arms Execution — Production Deployment · Exact-Action Binding")
    print("=" * 70)
    
    all_results = []
    
    for arm in range(1, 9):
        scenario_file = Path(f"results/arm_{arm}_scenarios.json")
        if not scenario_file.exists():
            print(f"⚠️  Skipping Arm {arm}: scenario file not found")
            continue
        
        with open(scenario_file) as f:
            scenarios = json.load(f)
        
        print(f"\nArm {arm}: Executing {len(scenarios)} scenarios...")
        arm_results = []
        
        for i, scenario in enumerate(scenarios):
            result = execute_scenario(scenario)
            arm_results.append(result)
            
            if (i + 1) % 25 == 0:
                print(f"  Progress: {i + 1}/{len(scenarios)}")
        
        # Save arm results
        arm_output = Path(f"results/arm_{arm}_results.json")
        with open(arm_output, "w") as f:
            json.dump(arm_results, f, indent=2)
        
        # Quick arm summary
        concordant = sum(1 for r in arm_results if r["concordant"])
        correct_v1 = sum(1 for r in arm_results if r["v1_correct"])
        correct_v2 = sum(1 for r in arm_results if r["v2_correct"])
        
        print(f"  ✅ Arm {arm} complete:")
        print(f"     V1 correct: {correct_v1}/{len(scenarios)}")
        print(f"     V2 correct: {correct_v2}/{len(scenarios)}")
        print(f"     Concordant: {concordant}/{len(scenarios)}")
        
        all_results.extend(arm_results)
    
    # Compute overall metrics
    print("\n" + "=" * 70)
    print("COMPUTING OVERALL METRICS...")
    metrics = compute_metrics(all_results)
    
    # Save overall results
    with open("results/overall_results.json", "w") as f:
        json.dump(metrics, f, indent=2)
    
    # Print summary
    print("\n" + "=" * 70)
    print("VERDICT:", metrics["verdict"])
    print("=" * 70)
    print(f"Total scenarios:        {metrics['total_scenarios']}")
    print(f"Concordance:            {metrics['concordant_count']}/{metrics['total_scenarios']} = {metrics['concordance_rate']:.4f}")
    print(f"g_allow_exact:          {metrics['g_allow_exact']:.4f} (threshold ≥ 0.95)")
    print(f"g_deny_mismatch_min:    {metrics['g_deny_mismatch_min']:.4f} (threshold ≥ 0.95)")
    print(f"g_margin:               {metrics['g_margin']:.4f} (threshold ≥ 0.90)")
    print("=" * 70)
    
    if metrics["verdict"] == "FAIL":
        sys.exit(1)


if __name__ == "__main__":
    main()
