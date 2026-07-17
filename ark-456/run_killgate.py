#!/usr/bin/env python3
"""
ARK-456 Kill-Gate Calibration
Verify dual-guard concordance and dependency-loss effectiveness before running arms.
"""
import json
import subprocess
import sys
from pathlib import Path
from generator.scenario_generator import ScenarioGenerator, dependency_loss_effective, SEED_BASE

def main():
    print("=" * 70)
    print("ARK-456 KILL-GATE CALIBRATION")
    print("=" * 70)
    
    # [1/4] Generate calibration scenarios (mixed across all arms)
    print("\n[1/4] Generating 100 calibration scenarios (all 8 arms)...")
    gen = ScenarioGenerator(SEED_BASE + 99)  # killgate seed
    scenarios = []
    for arm in range(1, 9):
        arm_gen = ScenarioGenerator(SEED_BASE + arm)
        scenarios.extend(arm_gen.generate_scenarios(arm, count=12 if arm < 8 else 4))  # 100 total
    scenarios = scenarios[:100]
    print(f"  → Generated {len(scenarios)} scenarios")
    
    # [2/4] Check dependency-loss effectiveness
    print("\n[2/4] Checking dependency-loss effectiveness...")
    failures = []
    for sc in scenarios:
        is_eff, reason = dependency_loss_effective(sc, sc["arm"])
        if not is_eff:
            failures.append((sc["scenario_id"], reason))
    
    if failures:
        print("  ✗ Effectiveness check FAILED:")
        for sid, reason in failures:
            print(f"    {sid}: {reason}")
        print("\n✗ KILL-GATE ABORT: dependency-loss effectiveness failed")
        sys.exit(1)
    print(f"  ✓ All {len(scenarios)} scenarios are dependency-loss-effective")
    
    # [3/4] Evaluate with V2
    print("\n[3/4] Evaluating with V2 guard (Python)...")
    result_v2 = subprocess.run(
        ["python3", "verifiers/v2_guard.py"],
        input=json.dumps(scenarios),
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent
    )
    if result_v2.returncode != 0:
        print(f"  ✗ V2 failed:\n{result_v2.stderr}")
        sys.exit(1)
    results_v2 = json.loads(result_v2.stdout)
    v2_allow = sum(1 for r in results_v2 if r["decision"] == "ALLOW")
    v2_hold = sum(1 for r in results_v2 if r["decision"] == "HOLD")
    v2_deny = sum(1 for r in results_v2 if r["decision"] == "DENY")
    print(f"  → V2: {v2_allow} ALLOW, {v2_hold} HOLD, {v2_deny} DENY")
    
    # [4/4] Evaluate with V1
    print("\n[4/4] Evaluating with V1 guard (JavaScript)...")
    result_v1 = subprocess.run(
        ["node", "verifiers/v1_guard.js"],
        input=json.dumps(scenarios),
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent
    )
    if result_v1.returncode != 0:
        print(f"  ✗ V1 failed:\n{result_v1.stderr}")
        sys.exit(1)
    results_v1 = json.loads(result_v1.stdout)
    v1_allow = sum(1 for r in results_v1 if r["decision"] == "ALLOW")
    v1_hold = sum(1 for r in results_v1 if r["decision"] == "HOLD")
    v1_deny = sum(1 for r in results_v1 if r["decision"] == "DENY")
    print(f"  → V1: {v1_allow} ALLOW, {v1_hold} HOLD, {v1_deny} DENY")
    
    # Concordance
    agreements = sum(1 for r1, r2 in zip(results_v1, results_v2) if r1["decision"] == r2["decision"])
    concordance = agreements / len(scenarios)
    
    print("\n" + "=" * 70)
    print(f"CONCORDANCE: {agreements}/{len(scenarios)} = {concordance:.4f}")
    
    # Save calibration results
    results_dir = Path(__file__).parent / "results"
    results_dir.mkdir(exist_ok=True)
    with open(results_dir / "killgate_scenarios.json", "w") as f:
        json.dump(scenarios, f, indent=2)
    with open(results_dir / "killgate_calibration.json", "w") as f:
        json.dump({
            "concordance": {"agreements": agreements, "total": len(scenarios), "percentage": concordance * 100},
            "v1": {"allow": v1_allow, "hold": v1_hold, "deny": v1_deny},
            "v2": {"allow": v2_allow, "hold": v2_hold, "deny": v2_deny}
        }, f, indent=2)
    print(f"Results written to {results_dir}/killgate_calibration.json")
    
    if concordance >= 0.99:
        print("\n✓ KILL-GATE PASS: Concordance ≥ 99% — proceed to arm execution")
        print("=" * 70)
        sys.exit(0)
    else:
        print(f"\n✗ KILL-GATE FAIL: Concordance {concordance:.4f} < 0.99")
        print("=" * 70)
        sys.exit(1)

if __name__ == "__main__":
    main()
