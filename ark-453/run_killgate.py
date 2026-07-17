#!/usr/bin/env python3
"""
ARK-453 Kill-Gate Calibration
Confirms both resolvers implement the decision procedure correctly and agree
on consensus + conflict cases before running the full 800-scenario corpus.
"""
import json
import subprocess
import sys
from pathlib import Path

# Add generator to path
sys.path.insert(0, str(Path(__file__).parent / "generator"))
from scenario_generator import ScenarioGenerator, conflict_effective, SEED_BASE

CALIBRATION_SEED = SEED_BASE + 99  # 20260717552


def run_killgate():
    """
    Generate 100 calibration scenarios (50 consensus, 50 conflict/ambiguous),
    check conflict-effectiveness, evaluate with both resolvers, check concordance.
    """
    print("=" * 70)
    print("ARK-453 KILL-GATE CALIBRATION")
    print("=" * 70)
    
    # Generate calibration scenarios
    print("\n[1/4] Generating 100 calibration scenarios...")
    gen = ScenarioGenerator(CALIBRATION_SEED)
    scenarios = []
    
    # 50 consensus: 25 all-allow (arm 1), 25 all-deny (arm 2)
    for i in range(25):
        scenarios.append(gen.generate_scenario(arm=1, index=i))
    for i in range(25):
        scenarios.append(gen.generate_scenario(arm=2, index=i))
    
    # 50 conflict/ambiguous: cycle through arms 3-8
    arms_conflict = [3, 4, 5, 6, 7, 8]
    for i in range(50):
        arm = arms_conflict[i % len(arms_conflict)]
        scenarios.append(gen.generate_scenario(arm=arm, index=i))
    
    print(f"  → Generated {len(scenarios)} scenarios")
    
    # Check conflict-effectiveness on all scenarios
    print("\n[2/4] Checking conflict-effectiveness...")
    all_effective = True
    for scenario in scenarios:
        arm = scenario["arm"]
        effective, reason = conflict_effective(scenario, arm)
        if not effective:
            print(f"  ✗ FAIL: scenario {scenario['scenario_id']} not effective: {reason}")
            all_effective = False
    
    if not all_effective:
        print("\n✗ KILL-GATE FAIL: Some scenarios are not conflict-effective")
        sys.exit(1)
    
    print(f"  ✓ All {len(scenarios)} scenarios are conflict-effective")
    
    # Write scenarios to temp file for resolvers
    scenarios_file = Path(__file__).parent / "results" / "killgate_scenarios.json"
    scenarios_file.parent.mkdir(exist_ok=True)
    with open(scenarios_file, "w") as f:
        json.dump(scenarios, f)
    
    # Evaluate with V2 (Python)
    print("\n[3/4] Evaluating with V2 resolver (Python)...")
    v2_path = Path(__file__).parent / "verifiers" / "v2_resolver.py"
    with open(scenarios_file, "r") as f:
        result_v2 = subprocess.run(
            ["python3", str(v2_path)],
            stdin=f,
            capture_output=True,
            text=True
        )
    
    if result_v2.returncode != 0:
        print(f"  ✗ V2 resolver failed:\n{result_v2.stderr}")
        sys.exit(1)
    
    v2_output = json.loads(result_v2.stdout)
    print(f"  → V2: {v2_output['allow']} ALLOW, {v2_output['hold']} HOLD, {v2_output['deny']} DENY")
    
    # Evaluate with V1 (JavaScript)
    print("\n[4/4] Evaluating with V1 resolver (JavaScript)...")
    v1_path = Path(__file__).parent / "verifiers" / "v1_resolver.js"
    with open(scenarios_file, "r") as f:
        result_v1 = subprocess.run(
            ["node", str(v1_path)],
            stdin=f,
            capture_output=True,
            text=True
        )
    
    if result_v1.returncode != 0:
        print(f"  ✗ V1 resolver failed:\n{result_v1.stderr}")
        sys.exit(1)
    
    v1_output = json.loads(result_v1.stdout)
    print(f"  → V1: {v1_output['allow']} ALLOW, {v1_output['hold']} HOLD, {v1_output['deny']} DENY")
    
    # Check concordance
    agreements = 0
    total = len(scenarios)
    
    for i in range(total):
        v1_verdict = v1_output["verdicts"][i]["decision"]
        v2_verdict = v2_output["verdicts"][i]["decision"]
        if v1_verdict == v2_verdict:
            agreements += 1
    
    concordance = agreements / total if total > 0 else 0.0
    
    print("\n" + "=" * 70)
    print(f"CONCORDANCE: {agreements}/{total} = {concordance:.4f}")
    
    # Write results
    result = {
        "calibration_seed": CALIBRATION_SEED,
        "scenarios_generated": total,
        "conflict_effectiveness": "PASS",
        "v1_output": v1_output,
        "v2_output": v2_output,
        "concordance": {
            "agreements": agreements,
            "total": total,
            "percentage": round(concordance * 100, 2)
        },
        "verdict": "PASS" if concordance >= 0.99 else "FAIL"
    }
    
    result_file = Path(__file__).parent / "results" / "killgate_calibration.json"
    with open(result_file, "w") as f:
        json.dump(result, f, indent=2)
    
    print(f"Results written to {result_file}")
    
    # Gate decision
    if concordance >= 0.99:
        print("\n✓ KILL-GATE PASS: Concordance ≥ 99% — proceed to arm execution")
        print("=" * 70)
        return 0
    else:
        print(f"\n✗ KILL-GATE FAIL: Concordance {concordance:.4f} < 0.99")
        print("  Resolvers disagree. Fix before corpus run.")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    sys.exit(run_killgate())
