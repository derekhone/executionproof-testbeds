#!/usr/bin/env python3
"""
ARK-470 — Run all 8 arms (800 scenarios total) and compute metrics.

Arms:
  1, 8: ALL-AVAILABLE → expect ALLOW
  2: QueryValidator UNAVAILABLE → expect HOLD
  3: SchemaRegistry UNAVAILABLE → expect HOLD
  4: PermissionStore UNAVAILABLE → expect HOLD
  5: Database QueryAuditor UNAVAILABLE → expect HOLD
  6: MULTIPLE UNAVAILABLE → expect HOLD
  7: ALL-UNAVAILABLE → expect HOLD

Metrics:
  - g_allow_available = ALLOW rate on arms {1, 8} (all dependencies available)
  - g_hold_unavailable_min = min HOLD rate across arms {2, 3, 4, 5, 6, 7}
  - g_margin = min(g_allow_available, g_hold_unavailable_min) - 0.05

Pass criteria:
  C1: g_allow_available ≥ 0.95
  C2: g_hold_unavailable_min ≥ 0.95
  C3: g_margin ≥ 0.90
  Verdict = PASS iff C1 ∧ C2 ∧ C3, else FAIL.
"""
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).parent
RESULTS_DIR = HERE / "results"

ARM_NAMES = {
    1: "ALL-AVAILABLE", 2: "QueryValidator-UNAVAILABLE",
    3: "SchemaRegistry-UNAVAILABLE", 4: "PermissionStore-UNAVAILABLE",
    5: "Database QueryAuditor-UNAVAILABLE", 6: "MULTIPLE-UNAVAILABLE",
    7: "ALL-UNAVAILABLE", 8: "ALL-AVAILABLE-baseline"
}

ARM_EXPECTS = {1: "ALLOW", 2: "HOLD", 3: "HOLD", 4: "HOLD",
               5: "HOLD", 6: "HOLD", 7: "HOLD", 8: "ALLOW"}

def run_arm(arm: int, n: int = 100):
    print(f"\n{'='*70}\nARM {arm}: {ARM_NAMES[arm]} (expect {ARM_EXPECTS[arm]}, n={n})\n{'='*70}")
    
    cmd = ["python3", "-c", f"from generator.scenario_generator import generate_arm; import json; print(json.dumps(generate_arm({arm}, {n})))"]
    scenarios_json = subprocess.check_output(cmd, cwd=HERE, text=True)
    scenarios = json.loads(scenarios_json)
    
    scenarios_file = RESULTS_DIR / f"arm_{arm}_scenarios.json"
    with open(scenarios_file, "w") as f:
        json.dump(scenarios, f, indent=2)
    print(f"  Generated {len(scenarios)} scenarios → {scenarios_file.name}")
    
    v2_proc = subprocess.run(["python3", str(HERE / "verifiers/v2_guard.py")],
                             input=scenarios_json, capture_output=True, text=True)
    v2_results = json.loads(v2_proc.stdout)
    
    v1_proc = subprocess.run(["node", str(HERE / "verifiers/v1_guard.js")],
                             input=scenarios_json, capture_output=True, text=True)
    v1_results = json.loads(v1_proc.stdout)
    
    combined = []
    concordance_count = 0
    decision_counts = {"ALLOW": 0, "HOLD": 0}
    expect = ARM_EXPECTS[arm]
    correct_count = 0
    
    for i, sc in enumerate(scenarios):
        v1_decision = v1_results[i]["decision"]
        v2_decision = v2_results[i]["decision"]
        concordant = (v1_decision == v2_decision)
        if concordant:
            concordance_count += 1
        decision = v2_decision
        decision_counts[decision] += 1
        if decision == expect:
            correct_count += 1
        combined.append({
            "scenario_id": sc["scenario_id"], "arm": arm,
            "v1_decision": v1_decision, "v2_decision": v2_decision,
            "concordant": concordant, "decision": decision
        })
    
    with open(RESULTS_DIR / f"arm_{arm}_results.json", "w") as f:
        json.dump(combined, f, indent=2)
    
    concordance_rate = concordance_count / len(scenarios)
    correctness_rate = correct_count / len(scenarios)
    
    print(f"  ALLOW={decision_counts['ALLOW']} HOLD={decision_counts['HOLD']}")
    print(f"  Correctness (vs {expect}): {correct_count}/{len(scenarios)} = {correctness_rate:.4f}")
    print(f"  V1↔V2 concordance: {concordance_count}/{len(scenarios)} = {concordance_rate:.4f}")
    
    return {
        "arm": arm, "name": ARM_NAMES[arm], "expect": expect, "n": len(scenarios),
        "decision_counts": decision_counts, "correctness": correctness_rate,
        "concordance": concordance_rate
    }

def main():
    RESULTS_DIR.mkdir(exist_ok=True)
    
    print("="*70 + "\nARK-470 — Production Database Query · Dependency Loss\n" + "="*70)
    
    arm_results = [run_arm(arm, n=100) for arm in range(1, 9)]
    
    allow_arms = [1, 8]
    hold_arms = [2, 3, 4, 5, 6, 7]
    
    g_allow_available = min(arm_results[a-1]["correctness"] for a in allow_arms)
    g_hold_unavailable_min = min(arm_results[a-1]["correctness"] for a in hold_arms)
    g_margin = min(g_allow_available, g_hold_unavailable_min) - 0.05
    
    overall_concordance = sum(r["concordance"] * r["n"] for r in arm_results) / sum(r["n"] for r in arm_results)
    
    c1 = g_allow_available >= 0.95
    c2 = g_hold_unavailable_min >= 0.95
    c3 = g_margin >= 0.90
    verdict = "PASS" if (c1 and c2 and c3) else "FAIL"
    
    overall = {
        "experiment": "ARK-470", "title": "Production Database Query · Dependency Loss",
        "total_scenarios": sum(r["n"] for r in arm_results), "arms": arm_results,
        "metrics": {
            "g_allow_available": round(g_allow_available, 4),
            "g_hold_unavailable_min": round(g_hold_unavailable_min, 4),
            "g_margin": round(g_margin, 4),
            "overall_concordance": round(overall_concordance, 4)
        },
        "criteria": {
            "C1_allow_available": {"threshold": 0.95, "value": round(g_allow_available, 4), "pass": c1},
            "C2_hold_unavailable": {"threshold": 0.95, "value": round(g_hold_unavailable_min, 4), "pass": c2},
            "C3_margin": {"threshold": 0.90, "value": round(g_margin, 4), "pass": c3}
        },
        "verdict": verdict
    }
    
    with open(RESULTS_DIR / "overall_results.json", "w") as f:
        json.dump(overall, f, indent=2)
    
    print(f"\n{'='*70}\nOVERALL RESULTS\n{'='*70}")
    print(f"g_allow_available       = {g_allow_available:.4f} (C1: ≥ 0.95) {'✓' if c1 else '✗'}")
    print(f"g_hold_unavailable_min  = {g_hold_unavailable_min:.4f} (C2: ≥ 0.95) {'✓' if c2 else '✗'}")
    print(f"g_margin                = {g_margin:.4f} (C3: ≥ 0.90) {'✓' if c3 else '✗'}")
    print(f"Overall concordance     = {overall_concordance:.4f}")
    print(f"\n{'='*70}\nVERDICT: {verdict}\n{'='*70}")

if __name__ == "__main__":
    main()
