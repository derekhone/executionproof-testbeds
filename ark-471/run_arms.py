#!/usr/bin/env python3
"""ARK-471 — Run all 8 arms (800 scenarios) and compute metrics."""
import json, subprocess
from pathlib import Path

HERE = Path(__file__).parent
RESULTS_DIR = HERE / "results"
ARM_NAMES = {1: "EXACT-MATCH", 2: "CROSS-TENANT", 3: "CROSS-SESSION", 4: "CROSS-RESOURCE",
             5: "CROSS-AUDIENCE", 6: "CROSS-ENVIRONMENT", 7: "MULTI-DIM", 8: "EXACT-MATCH-baseline"}
ARM_EXPECTS = {1: "ALLOW", 2: "DENY", 3: "DENY", 4: "DENY", 5: "DENY", 6: "DENY", 7: "DENY", 8: "ALLOW"}

def run_arm(arm: int, n: int = 100):
    print(f"\n{'='*70}\nARM {arm}: {ARM_NAMES[arm]} (expect {ARM_EXPECTS[arm]}, n={n})\n{'='*70}")
    cmd = ["python3", "-c", f"from generator.scenario_generator import generate_arm; import json; print(json.dumps(generate_arm({arm}, {n})))"]
    scenarios_json = subprocess.check_output(cmd, cwd=HERE, text=True)
    scenarios = json.loads(scenarios_json)
    with open(RESULTS_DIR / f"arm_{arm}_scenarios.json", "w") as f:
        json.dump(scenarios, f, indent=2)
    print(f"  Generated {len(scenarios)} scenarios")
    
    v2_proc = subprocess.run(["python3", str(HERE / "verifiers/v2_guard.py")],
                             input=scenarios_json, capture_output=True, text=True)
    v2_results = json.loads(v2_proc.stdout)
    v1_proc = subprocess.run(["node", str(HERE / "verifiers/v1_guard.js")],
                             input=scenarios_json, capture_output=True, text=True)
    v1_results = json.loads(v1_proc.stdout)
    
    combined, concordance_count, decision_counts, correct_count = [], 0, {"ALLOW": 0, "DENY": 0}, 0
    expect = ARM_EXPECTS[arm]
    for i, sc in enumerate(scenarios):
        v1_decision, v2_decision = v1_results[i]["decision"], v2_results[i]["decision"]
        concordant = (v1_decision == v2_decision)
        if concordant: concordance_count += 1
        decision = v2_decision
        decision_counts[decision] += 1
        if decision == expect: correct_count += 1
        combined.append({"scenario_id": sc["scenario_id"], "arm": arm,
                        "v1_decision": v1_decision, "v2_decision": v2_decision,
                        "concordant": concordant, "decision": decision})
    
    with open(RESULTS_DIR / f"arm_{arm}_results.json", "w") as f:
        json.dump(combined, f, indent=2)
    
    print(f"  ALLOW={decision_counts['ALLOW']} DENY={decision_counts['DENY']}")
    print(f"  Correctness: {correct_count}/{len(scenarios)} = {correct_count/len(scenarios):.4f}")
    print(f"  Concordance: {concordance_count}/{len(scenarios)} = {concordance_count/len(scenarios):.4f}")
    
    return {"arm": arm, "name": ARM_NAMES[arm], "expect": expect, "n": len(scenarios),
            "correctness": correct_count/len(scenarios), "concordance": concordance_count/len(scenarios)}

def main():
    RESULTS_DIR.mkdir(exist_ok=True)
    print("="*70 + "\nARK-471 — Production Database Query · Cross-Context Replay\n" + "="*70)
    arm_results = [run_arm(arm, n=100) for arm in range(1, 9)]
    g_allow_exact = min(arm_results[a-1]["correctness"] for a in [1, 8])
    g_deny_replay_min = min(arm_results[a-1]["correctness"] for a in [2,3,4,5,6,7])
    g_margin = min(g_allow_exact, g_deny_replay_min) - 0.05
    overall_concordance = sum(r["concordance"] * r["n"] for r in arm_results) / sum(r["n"] for r in arm_results)
    c1, c2, c3 = g_allow_exact >= 0.95, g_deny_replay_min >= 0.95, g_margin >= 0.90
    verdict = "PASS" if (c1 and c2 and c3) else "FAIL"
    
    overall = {"experiment": "ARK-471", "total_scenarios": sum(r["n"] for r in arm_results), "arms": arm_results,
               "metrics": {"g_allow_exact": round(g_allow_exact, 4), "g_deny_replay_min": round(g_deny_replay_min, 4),
                          "g_margin": round(g_margin, 4), "overall_concordance": round(overall_concordance, 4)},
               "criteria": {"C1": {"threshold": 0.95, "value": round(g_allow_exact, 4), "pass": c1},
                           "C2": {"threshold": 0.95, "value": round(g_deny_replay_min, 4), "pass": c2},
                           "C3": {"threshold": 0.90, "value": round(g_margin, 4), "pass": c3}},
               "verdict": verdict}
    
    with open(RESULTS_DIR / "overall_results.json", "w") as f:
        json.dump(overall, f, indent=2)
    
    print(f"\n{'='*70}\nOVERALL\n{'='*70}\ng_allow_exact={g_allow_exact:.4f} (C1≥0.95){'✓' if c1 else '✗'}\ng_deny_replay_min={g_deny_replay_min:.4f} (C2≥0.95){'✓' if c2 else '✗'}\ng_margin={g_margin:.4f} (C3≥0.90){'✓' if c3 else '✗'}\nConcordance={overall_concordance:.4f}\n{'='*70}\nVERDICT: {verdict}\n{'='*70}")

if __name__ == "__main__":
    main()
