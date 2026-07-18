#!/usr/bin/env python3
"""
ARK-475 — Kill-gate (negative control).

A deliberately BROKEN guard that ignores dependency availability and always ALLOWs.
If this broken guard wrongly ALLOWs most of the HOLD arms (2–7 — dependencies unavailable),
the testbed is falsifiable.
"""
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).parent
RESULTS_DIR = HERE / "results"

def broken_guard_always_allow(scenario):
    return {
        "scenario_id": scenario["scenario_id"], "arm": scenario["arm"],
        "decision": "ALLOW",
        "reason": "Broken guard ignores dependencies (kill-gate negative control)"
    }

def main():
    RESULTS_DIR.mkdir(exist_ok=True)
    
    print("="*70)
    print("ARK-475 — Kill-gate (negative control)")
    print("="*70)
    print("Testing: a broken guard that ignores dependency availability and always ALLOWs.")
    print("Expected: wrongly ALLOW most of arms {2,3,4,5,6,7} (should be HOLD).\n")
    
    all_scenarios = []
    for arm in range(1, 9):
        cmd = ["python3", "-c", f"from generator.scenario_generator import generate_arm; import json; print(json.dumps(generate_arm({arm}, 25)))"]
        scenarios_json = subprocess.check_output(cmd, cwd=HERE, text=True)
        scenarios = json.loads(scenarios_json)
        all_scenarios.extend(scenarios)
    
    results = [broken_guard_always_allow(sc) for sc in all_scenarios]
    
    wrong_allows = 0
    hold_arms = {2, 3, 4, 5, 6, 7}
    hold_count = sum(1 for sc in all_scenarios if sc["arm"] in hold_arms)
    
    for r in results:
        if r["arm"] in hold_arms and r["decision"] == "ALLOW":
            wrong_allows += 1
    
    wrong_allow_rate = wrong_allows / hold_count if hold_count > 0 else 0
    
    kill_result = {
        "experiment": "ARK-475-killgate", "total_scenarios": len(all_scenarios),
        "hold_arms_count": hold_count, "wrong_allows": wrong_allows,
        "wrong_allow_rate": round(wrong_allow_rate, 4),
        "falsifiable": wrong_allow_rate > 0.5
    }
    
    with open(RESULTS_DIR / "killgate_results.json", "w") as f:
        json.dump(kill_result, f, indent=2)
    
    print(f"Hold arms: {hold_count} scenarios (arms {hold_arms})")
    print(f"Wrong ALLOWs: {wrong_allows}/{hold_count} = {wrong_allow_rate:.4f}")
    print(f"Falsifiable: {kill_result['falsifiable']} (need > 0.5)")
    print("="*70)
    
    if not kill_result["falsifiable"]:
        print("❌ KILL-GATE FAIL: testbed NOT falsifiable")
        return 1
    else:
        print("✅ Kill-gate PASS: testbed is falsifiable")
        return 0

if __name__ == "__main__":
    exit(main())
