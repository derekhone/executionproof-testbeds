#!/usr/bin/env python3
"""
ARK-468 Kill-Gate — Production Deployment · Exact-Action Binding

Tests a deliberately broken guard that ignores exact-match requirement.
Demonstrates testbed falsifiability: broken guards produce detectable wrong-allows.
"""

import json
from pathlib import Path
from typing import Dict, Any, List


def broken_guard(authorized: Dict[str, str], presented: Dict[str, str]) -> Dict[str, str]:
    """
    DELIBERATELY BROKEN: Always ALLOWs regardless of tuple match.
    This simulates a guard with missing exact-match enforcement.
    """
    return {
        "decision": "ALLOW",
        "reason": "BROKEN: Always allows (ignores exact-match requirement)"
    }


def execute_killgate_scenario(scenario: Dict[str, Any]) -> Dict[str, Any]:
    """Execute scenario against broken guard"""
    authorized = scenario["authorized_query"]
    presented = scenario["presented_query"]
    expected = scenario["expected_decision"]
    
    result = broken_guard(authorized, presented)
    decision = result["decision"]
    
    # A "wrong-allow" is when:
    # - Expected decision is DENY (mismatch scenario)
    # - But broken guard returns ALLOW
    wrong_allow = (expected == "DENY" and decision == "ALLOW")
    
    return {
        "scenario_id": scenario["scenario_id"],
        "arm": scenario["arm"],
        "expected_decision": expected,
        "broken_guard_decision": decision,
        "wrong_allow": wrong_allow
    }


def main():
    """Execute kill-gate test"""
    print("ARK-468 Kill-Gate Test — Production Deployment · Exact-Action Binding")
    print("=" * 70)
    print("Testing deliberately broken guard (always ALLOW)...")
    print()
    
    all_results = []
    
    # Only test DENY scenarios (Arms 2-7) - these should all become wrong-allows
    deny_arms = range(2, 8)
    
    for arm in deny_arms:
        scenario_file = Path(f"results/arm_{arm}_scenarios.json")
        if not scenario_file.exists():
            print(f"⚠️  Skipping Arm {arm}: scenario file not found")
            continue
        
        with open(scenario_file) as f:
            scenarios = json.load(f)
        
        arm_results = []
        for scenario in scenarios:
            result = execute_killgate_scenario(scenario)
            arm_results.append(result)
        
        all_results.extend(arm_results)
        
        wrong_allows = sum(1 for r in arm_results if r["wrong_allow"])
        print(f"Arm {arm}: {wrong_allows}/{len(scenarios)} wrong-allows")
    
    # Summary
    total_deny_scenarios = len(all_results)
    total_wrong_allows = sum(1 for r in all_results if r["wrong_allow"])
    
    print()
    print("=" * 70)
    print("KILL-GATE SUMMARY")
    print("=" * 70)
    print(f"Total DENY scenarios tested: {total_deny_scenarios}")
    print(f"Wrong-allows detected:       {total_wrong_allows}")
    print()
    
    if total_wrong_allows >= 50:
        print("✅ FALSIFIABLE: Testbed successfully detected broken guard")
        print(f"   (Required ≥50 wrong-allows, detected {total_wrong_allows})")
    else:
        print(f"❌ NOT FALSIFIABLE: Only {total_wrong_allows} wrong-allows (need ≥50)")
        print("   Testbed may not be sensitive enough to detect broken guards")
    
    print("=" * 70)
    
    # Save results
    output = {
        "total_deny_scenarios": total_deny_scenarios,
        "total_wrong_allows": total_wrong_allows,
        "falsifiable": total_wrong_allows >= 50,
        "results": all_results
    }
    
    with open("results/killgate_results.json", "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"\nResults saved to results/killgate_results.json")


if __name__ == "__main__":
    main()
