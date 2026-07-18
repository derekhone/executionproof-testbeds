#!/usr/bin/env python3
"""ARK-472 — Kill-gate: broken guard ignores escalation, always ALLOWs."""
import json, subprocess
from pathlib import Path

HERE, RESULTS_DIR = Path(__file__).parent, Path(__file__).parent / "results"

def main():
    RESULTS_DIR.mkdir(exist_ok=True)
    print("="*70 + "\nARK-472 Kill-gate\n" + "="*70)
    all_scenarios = []
    for arm in range(1, 9):
        cmd = ["python3", "-c", f"from generator.scenario_generator import generate_arm; import json; print(json.dumps(generate_arm({arm}, 25)))"]
        all_scenarios.extend(json.loads(subprocess.check_output(cmd, cwd=HERE, text=True)))
    
    results = [{"scenario_id": sc["scenario_id"], "arm": sc["arm"], "decision": "ALLOW",
                "reason": "Broken guard ignores escalation"} for sc in all_scenarios]
    
    hold_arms, hold_count = {3,4,5,8}, sum(1 for sc in all_scenarios if sc["arm"] in {3,4,5,8})
    wrong_allows = sum(1 for r in results if r["arm"] in hold_arms and r["decision"] == "ALLOW")
    wrong_allow_rate = wrong_allows / hold_count if hold_count > 0 else 0
    
    kill_result = {"experiment": "ARK-472-killgate", "hold_arms_count": hold_count,
                   "wrong_allows": wrong_allows, "wrong_allow_rate": round(wrong_allow_rate, 4),
                   "falsifiable": wrong_allow_rate > 0.5}
    
    with open(RESULTS_DIR / "killgate_results.json", "w") as f:
        json.dump(kill_result, f, indent=2)
    
    print(f"Hold arms: {hold_count}, Wrong ALLOWs: {wrong_allows}/{hold_count} = {wrong_allow_rate:.4f}")
    print(f"Falsifiable: {kill_result['falsifiable']}\n" + "="*70)
    return 0 if kill_result["falsifiable"] else 1

if __name__ == "__main__":
    exit(main())
