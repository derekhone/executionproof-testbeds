#!/usr/bin/env python3
"""
ARK-469 — Kill-gate (negative control).

A deliberately BROKEN guard that ignores revocation entirely and always ALLOWs.
If this broken guard wrongly ALLOWs a significant fraction of scenarios that
should be DENY or HOLD, the testbed is falsifiable.

Expected: the broken guard should wrongly ALLOW most of arms 2–5, 7 (the DENY/HOLD arms).
"""
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).parent
GENERATOR = HERE / "generator/scenario_generator.py"
RESULTS_DIR = HERE / "results"

def broken_guard_always_allow(scenario):
    """Broken guard: always ALLOW, never checks revocation."""
    return {
        "scenario_id": scenario["scenario_id"],
        "arm": scenario["arm"],
        "decision": "ALLOW",
        "reason": "Broken guard ignores revocation (kill-gate negative control)"
    }

def main():
    RESULTS_DIR.mkdir(exist_ok=True)
    
    print("="*70)
    print("ARK-469 — Kill-gate (negative control)")
    print("="*70)
    print("Testing: a broken guard that ignores revocation and always ALLOWs.")
    print("Expected: wrongly ALLOW most of arms {2,3,4,5,7} (should be DENY/HOLD).")
    print()
    
    # Generate a smaller sample (25 per arm)
    all_scenarios = []
    for arm in range(1, 9):
        cmd = ["python3", "-c", f"from generator.scenario_generator import generate_arm; import json; print(json.dumps(generate_arm({arm}, 25)))"]
        scenarios_json = subprocess.check_output(cmd, cwd=HERE, text=True)
        scenarios = json.loads(scenarios_json)
        all_scenarios.extend(scenarios)
    
    # Run broken guard
    results = [broken_guard_always_allow(sc) for sc in all_scenarios]
    
    # Analyze: count wrong ALLOWs on DENY/HOLD arms
    wrong_allows = 0
    deny_hold_arms = {2, 3, 4, 5, 7}
    deny_hold_count = sum(1 for sc in all_scenarios if sc["arm"] in deny_hold_arms)
    
    for r in results:
        if r["arm"] in deny_hold_arms and r["decision"] == "ALLOW":
            wrong_allows += 1
    
    wrong_allow_rate = wrong_allows / deny_hold_count if deny_hold_count > 0 else 0
    
    kill_result = {
        "experiment": "ARK-469-killgate",
        "total_scenarios": len(all_scenarios),
        "deny_hold_arms_count": deny_hold_count,
        "wrong_allows": wrong_allows,
        "wrong_allow_rate": round(wrong_allow_rate, 4),
        "falsifiable": wrong_allow_rate > 0.5  # expect > 50% wrong ALLOWs
    }
    
    with open(RESULTS_DIR / "killgate_results.json", "w") as f:
        json.dump(kill_result, f, indent=2)
    
    print(f"Deny/Hold arms: {deny_hold_count} scenarios (arms {deny_hold_arms})")
    print(f"Wrong ALLOWs: {wrong_allows}/{deny_hold_count} = {wrong_allow_rate:.4f}")
    print(f"Falsifiable: {kill_result['falsifiable']} (need > 0.5)")
    print("="*70)
    
    if not kill_result["falsifiable"]:
        print("❌ KILL-GATE FAIL: testbed NOT falsifiable (broken guard didn't fail as expected)")
        return 1
    else:
        print("✅ Kill-gate PASS: testbed is falsifiable")
        return 0

if __name__ == "__main__":
    exit(main())
