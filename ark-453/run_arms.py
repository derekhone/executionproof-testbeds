#!/usr/bin/env python3
"""
ARK-453 Arm Execution
Executes all 8 arms (800 scenarios total), enforces conflict-effectiveness gate,
evaluates with dual resolvers, computes criteria C1/C2/C3, outputs verdict.
"""
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Add generator to path
sys.path.insert(0, str(Path(__file__).parent / "generator"))
from scenario_generator import ScenarioGenerator, conflict_effective, SEED_BASE, ARMS


def run_arm(arm: int) -> dict:
    """Execute a single arm: generate, gate, evaluate, score"""
    label, _ = ARMS[arm]
    print(f"\n{'=' * 70}")
    print(f"ARM {arm}: {label}")
    print(f"{'=' * 70}")
    
    # Generate scenarios
    print(f"[1/4] Generating 100 scenarios (seed {SEED_BASE + arm})...")
    gen = ScenarioGenerator(SEED_BASE + arm)
    scenarios, audit = gen.generate_arm_scenarios(arm, count=100)
    print(f"  → Generated {len(scenarios)} scenarios")
    
    # Conflict-effectiveness gate
    print("[2/4] Checking conflict-effectiveness...")
    all_effective = True
    for scenario in scenarios:
        effective, reason = conflict_effective(scenario, arm)
        if not effective:
            print(f"  ✗ FAIL: {scenario['scenario_id']} not effective: {reason}")
            all_effective = False
    
    if not all_effective:
        print(f"\n✗ ARM {arm} ABORT: Conflict-effectiveness gate failed")
        sys.exit(1)
    
    print(f"  ✓ All scenarios conflict-effective")
    
    # Write scenarios to temp file
    scenarios_file = Path(__file__).parent / "results" / f"arm_{arm}_scenarios.json"
    scenarios_file.parent.mkdir(exist_ok=True)
    with open(scenarios_file, "w") as f:
        json.dump(scenarios, f)
    
    # Evaluate with V1 (JavaScript)
    print("[3/4] Evaluating with V1 resolver (JavaScript)...")
    v1_path = Path(__file__).parent / "verifiers" / "v1_resolver.js"
    with open(scenarios_file, "r") as f:
        result_v1 = subprocess.run(
            ["node", str(v1_path)],
            stdin=f,
            capture_output=True,
            text=True
        )
    
    if result_v1.returncode != 0:
        print(f"  ✗ V1 failed:\n{result_v1.stderr}")
        sys.exit(1)
    
    v1_output = json.loads(result_v1.stdout)
    print(f"  → V1: {v1_output['allow']} ALLOW, {v1_output['hold']} HOLD, {v1_output['deny']} DENY")
    
    # Evaluate with V2 (Python)
    print("[4/4] Evaluating with V2 resolver (Python)...")
    v2_path = Path(__file__).parent / "verifiers" / "v2_resolver.py"
    with open(scenarios_file, "r") as f:
        result_v2 = subprocess.run(
            ["python3", str(v2_path)],
            stdin=f,
            capture_output=True,
            text=True
        )
    
    if result_v2.returncode != 0:
        print(f"  ✗ V2 failed:\n{result_v2.stderr}")
        sys.exit(1)
    
    v2_output = json.loads(result_v2.stdout)
    print(f"  → V2: {v2_output['allow']} ALLOW, {v2_output['hold']} HOLD, {v2_output['deny']} DENY")
    
    # Concordance
    agreements = sum(
        1 for i in range(len(scenarios))
        if v1_output["verdicts"][i]["decision"] == v2_output["verdicts"][i]["decision"]
    )
    concordance_pct = (agreements / len(scenarios)) * 100 if scenarios else 0.0
    
    print(f"  → Concordance: {agreements}/{len(scenarios)} = {concordance_pct:.2f}%")
    
    # Rates (use V2 as reference; V1 agrees per concordance)
    total = len(scenarios)
    allow_rate = v2_output["allow"] / total if total > 0 else 0.0
    hold_rate = v2_output["hold"] / total if total > 0 else 0.0
    deny_rate = v2_output["deny"] / total if total > 0 else 0.0
    
    # Arm result
    arm_result = {
        "arm": arm,
        "label": label,
        "scenarios": len(scenarios),
        "seed": SEED_BASE + arm,
        "conflict_effectiveness": "PASS",
        "v1_output": v1_output,
        "v2_output": v2_output,
        "concordance": {
            "agreements": agreements,
            "total": total,
            "percentage": round(concordance_pct, 2)
        },
        "rates": {
            "allow": round(allow_rate, 4),
            "hold": round(hold_rate, 4),
            "deny": round(deny_rate, 4)
        }
    }
    
    # Write arm result
    result_file = Path(__file__).parent / "results" / f"arm_{arm}_results.json"
    with open(result_file, "w") as f:
        json.dump(arm_result, f, indent=2)
    
    return arm_result


def compute_overall(arm_results: list) -> dict:
    """Compute overall metrics and verdict"""
    print(f"\n{'=' * 70}")
    print("OVERALL RESULTS")
    print(f"{'=' * 70}")
    
    # Primary metrics
    # g_allow_consensus: ALLOW rate in Arm 1
    arm_1 = next(r for r in arm_results if r["arm"] == 1)
    g_allow_consensus = arm_1["rates"]["allow"]
    
    # g_hold_conflict_min: minimum HOLD rate across arms 3-8
    conflict_arms = [r for r in arm_results if r["arm"] in [3, 4, 5, 6, 7, 8]]
    g_hold_conflict_min = min(r["rates"]["hold"] for r in conflict_arms)
    
    # g_margin
    g_margin = min(g_allow_consensus, g_hold_conflict_min) - 0.05
    
    # Criteria
    c1_pass = g_allow_consensus >= 0.95
    c2_pass = g_hold_conflict_min >= 0.95
    c3_pass = g_margin >= 0.90
    
    verdict = "PASS" if (c1_pass and c2_pass and c3_pass) else "FAIL"
    
    # Secondary: g_deny_consensus (Arm 2 DENY rate)
    arm_2 = next(r for r in arm_results if r["arm"] == 2)
    g_deny_consensus = arm_2["rates"]["deny"]
    
    # Overall concordance
    total_agreements = sum(r["concordance"]["agreements"] for r in arm_results)
    total_scenarios = sum(r["concordance"]["total"] for r in arm_results)
    overall_concordance_pct = (total_agreements / total_scenarios) * 100 if total_scenarios > 0 else 0.0
    
    # Print summary
    print(f"\nPrimary Metrics:")
    print(f"  g_allow_consensus (Arm 1 ALLOW):      {g_allow_consensus:.4f}")
    print(f"  g_hold_conflict_min (Arms 3-8 HOLD):  {g_hold_conflict_min:.4f}")
    print(f"  g_margin:                             {g_margin:.4f}")
    
    print(f"\nPass Criteria:")
    print(f"  C1 (g_allow_consensus ≥ 0.95):  {'✓ PASS' if c1_pass else '✗ FAIL'}")
    print(f"  C2 (g_hold_conflict_min ≥ 0.95): {'✓ PASS' if c2_pass else '✗ FAIL'}")
    print(f"  C3 (g_margin ≥ 0.90):            {'✓ PASS' if c3_pass else '✗ FAIL'}")
    
    print(f"\nSecondary Observations:")
    print(f"  g_deny_consensus (Arm 2 DENY):   {g_deny_consensus:.4f}")
    print(f"  Overall V1-V2 concordance:       {overall_concordance_pct:.2f}% ({total_agreements}/{total_scenarios})")
    
    print(f"\n{'=' * 70}")
    print(f"VERDICT: {verdict}")
    print(f"{'=' * 70}")
    
    overall_result = {
        "run_start_time": arm_results[0].get("run_start_time"),
        "run_end_time": datetime.utcnow().isoformat() + "Z",
        "arms_executed": [r["arm"] for r in arm_results],
        "primary_metrics": {
            "g_allow_consensus": round(g_allow_consensus, 4),
            "g_hold_conflict_min": round(g_hold_conflict_min, 4),
            "g_margin": round(g_margin, 4)
        },
        "criteria": {
            "c1_allow_consensus_pass": c1_pass,
            "c2_hold_conflict_pass": c2_pass,
            "c3_margin_pass": c3_pass
        },
        "secondary": {
            "g_deny_consensus": round(g_deny_consensus, 4)
        },
        "overall_concordance": {
            "agreements": total_agreements,
            "total": total_scenarios,
            "percentage": round(overall_concordance_pct, 2)
        },
        "verdict": verdict,
        "per_arm_summary": {
            f"arm_{r['arm']}": {
                "label": r["label"],
                "allow_rate": r["rates"]["allow"],
                "hold_rate": r["rates"]["hold"],
                "deny_rate": r["rates"]["deny"]
            }
            for r in arm_results
        }
    }
    
    result_file = Path(__file__).parent / "results" / "overall_results.json"
    with open(result_file, "w") as f:
        json.dump(overall_result, f, indent=2)
    
    return overall_result


def main():
    """Execute all arms and compute verdict"""
    print("=" * 70)
    print("ARK-453 ARM EXECUTION")
    print("=" * 70)
    
    run_start = datetime.utcnow().isoformat() + "Z"
    
    # Execute arms 1-8
    arm_results = []
    for arm in range(1, 9):
        result = run_arm(arm)
        result["run_start_time"] = run_start
        arm_results.append(result)
    
    # Compute overall
    overall = compute_overall(arm_results)
    
    # Exit code
    if overall["verdict"] == "PASS":
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())
