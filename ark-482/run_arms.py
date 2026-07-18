#!/usr/bin/env python3
"""ARK-482 — Run all 8 arms (800 scenarios)."""
import json, subprocess
from pathlib import Path

HERE, RESULTS_DIR = Path(__file__).parent, Path(__file__).parent / "results"
ARM_NAMES = {1: "NO-ESCALATION", 2: "ESCALATION-APPROVED", 3: "ESCALATION-NO-APPROVAL",
             4: "ESCALATION-INVALID", 5: "ESCALATION-INCOMPLETE", 6: "NO-ESCALATION-baseline",
             7: "ESCALATION-APPROVED-baseline", 8: "ESCALATION-NO-APPROVAL-baseline"}
ARM_EXPECTS = {1: "ALLOW", 2: "ALLOW", 3: "HOLD", 4: "HOLD", 5: "HOLD", 6: "ALLOW", 7: "ALLOW", 8: "HOLD"}

def run_arm(arm: int, n: int = 100):
    print(f"\n{'='*70}\nARM {arm}: {ARM_NAMES[arm]} (expect {ARM_EXPECTS[arm]}, n={n})\n{'='*70}")
    cmd = ["python3", "-c", f"from generator.scenario_generator import generate_arm; import json; print(json.dumps(generate_arm({arm}, {n})))"]
    scenarios_json = subprocess.check_output(cmd, cwd=HERE, text=True)
    scenarios = json.loads(scenarios_json)
    with open(RESULTS_DIR / f"arm_{arm}_scenarios.json", "w") as f:
        json.dump(scenarios, f, indent=2)
    
    v2_proc = subprocess.run(["python3", str(HERE / "verifiers/v2_guard.py")],
                             input=scenarios_json, capture_output=True, text=True)
    v2_results = json.loads(v2_proc.stdout)
    v1_proc = subprocess.run(["node", str(HERE / "verifiers/v1_guard.js")],
                             input=scenarios_json, capture_output=True, text=True)
    v1_results = json.loads(v1_proc.stdout)
    
    combined, concordance_count, decision_counts, correct_count = [], 0, {"ALLOW": 0, "HOLD": 0}, 0
    expect = ARM_EXPECTS[arm]
    for i, sc in enumerate(scenarios):
        v1_decision, v2_decision = v1_results[i]["decision"], v2_results[i]["decision"]
        if v1_decision == v2_decision: concordance_count += 1
        decision = v2_decision
        decision_counts[decision] += 1
        if decision == expect: correct_count += 1
        combined.append({"scenario_id": sc["scenario_id"], "arm": arm,
                        "v1_decision": v1_decision, "v2_decision": v2_decision,
                        "concordant": v1_decision == v2_decision, "decision": decision})
    
    with open(RESULTS_DIR / f"arm_{arm}_results.json", "w") as f:
        json.dump(combined, f, indent=2)
    
    print(f"  ALLOW={decision_counts['ALLOW']} HOLD={decision_counts['HOLD']}")
    print(f"  Correctness: {correct_count}/{len(scenarios)} = {correct_count/len(scenarios):.4f}")
    print(f"  Concordance: {concordance_count}/{len(scenarios)} = {concordance_count/len(scenarios):.4f}")
    
    return {"arm": arm, "name": ARM_NAMES[arm], "expect": expect, "n": len(scenarios),
            "correctness": correct_count/len(scenarios), "concordance": concordance_count/len(scenarios)}

def main():
    RESULTS_DIR.mkdir(exist_ok=True)
    print("="*70 + "\nARK-482 — Production API Rate Limit · Human Escalation\n" + "="*70)
    arm_results = [run_arm(arm, n=100) for arm in range(1, 9)]
    g_allow_no_esc = min(arm_results[a-1]["correctness"] for a in [1, 6])  # no escalation required
    g_allow_approved = min(arm_results[a-1]["correctness"] for a in [2, 7])  # escalation + valid approval
    g_hold_no_approval_min = min(arm_results[a-1]["correctness"] for a in [3, 4, 5, 8])  # escalation but no/invalid approval
    g_margin = min(g_allow_no_esc, g_allow_approved, g_hold_no_approval_min) - 0.05
    overall_concordance = sum(r["concordance"] * r["n"] for r in arm_results) / sum(r["n"] for r in arm_results)
    c1, c2, c3, c4 = g_allow_no_esc >= 0.95, g_allow_approved >= 0.95, g_hold_no_approval_min >= 0.95, g_margin >= 0.90
    verdict = "PASS" if (c1 and c2 and c3 and c4) else "FAIL"
    
    overall = {"experiment": "ARK-482", "total_scenarios": sum(r["n"] for r in arm_results), "arms": arm_results,
               "metrics": {"g_allow_no_esc": round(g_allow_no_esc, 4), "g_allow_approved": round(g_allow_approved, 4),
                          "g_hold_no_approval_min": round(g_hold_no_approval_min, 4),
                          "g_margin": round(g_margin, 4), "overall_concordance": round(overall_concordance, 4)},
               "criteria": {"C1": {"threshold": 0.95, "value": round(g_allow_no_esc, 4), "pass": c1},
                           "C2": {"threshold": 0.95, "value": round(g_allow_approved, 4), "pass": c2},
                           "C3": {"threshold": 0.95, "value": round(g_hold_no_approval_min, 4), "pass": c3},
                           "C4": {"threshold": 0.90, "value": round(g_margin, 4), "pass": c4}},
               "verdict": verdict}
    
    with open(RESULTS_DIR / "overall_results.json", "w") as f:
        json.dump(overall, f, indent=2)
    
    print(f"\n{'='*70}\nOVERALL\n{'='*70}\ng_allow_no_esc={g_allow_no_esc:.4f} (C1≥0.95){'✓' if c1 else '✗'}\ng_allow_approved={g_allow_approved:.4f} (C2≥0.95){'✓' if c2 else '✗'}\ng_hold_no_approval_min={g_hold_no_approval_min:.4f} (C3≥0.95){'✓' if c3 else '✗'}\ng_margin={g_margin:.4f} (C4≥0.90){'✓' if c4 else '✗'}\nConcordance={overall_concordance:.4f}\n{'='*70}\nVERDICT: {verdict}\n{'='*70}")

if __name__ == "__main__":
    main()
