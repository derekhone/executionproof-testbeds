#!/usr/bin/env python3
"""
ARK-451 Kill-Gate Calibration
Confirms both execution monitors implement the revocation decision procedure
correctly and agree across a mixed calibration set spanning all arms (valid,
revoked, in-flight, re-authorized) before running the full 800-scenario corpus.
Requires >= 99% V1-V2 concordance to proceed.
"""
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "generator"))
from scenario_generator import ScenarioGenerator, revocation_effective, SEED_BASE

CALIBRATION_SEED = SEED_BASE + 99  # 20260717550


def run_killgate():
    print("=" * 70)
    print("ARK-451 KILL-GATE CALIBRATION")
    print("=" * 70)

    print("\n[1/4] Generating 100 calibration scenarios (all 8 arms)...")
    gen = ScenarioGenerator(CALIBRATION_SEED)
    scenarios = []
    # Cycle through all 8 arms for balanced coverage of ALLOW/DENY/HOLD outcomes.
    for i in range(100):
        arm = (i % 8) + 1
        scenarios.append(gen.generate_scenario(arm=arm, index=i))
    print(f"  \u2192 Generated {len(scenarios)} scenarios")

    print("\n[2/4] Checking revocation-timing effectiveness...")
    all_effective = True
    for scenario in scenarios:
        arm = scenario["arm"]
        effective, reason = revocation_effective(scenario, arm)
        if not effective:
            print(f"  \u2717 FAIL: scenario {scenario['scenario_id']} not effective: {reason}")
            all_effective = False
    if not all_effective:
        print("\n\u2717 KILL-GATE FAIL: Some scenarios are not timing-effective")
        sys.exit(1)
    print(f"  \u2713 All {len(scenarios)} scenarios are timing-effective")

    scenarios_file = Path(__file__).parent / "results" / "killgate_scenarios.json"
    scenarios_file.parent.mkdir(exist_ok=True)
    with open(scenarios_file, "w") as f:
        json.dump(scenarios, f)

    print("\n[3/4] Evaluating with V2 monitor (Python)...")
    v2_path = Path(__file__).parent / "verifiers" / "v2_monitor.py"
    with open(scenarios_file, "r") as f:
        result_v2 = subprocess.run(["python3", str(v2_path)], stdin=f, capture_output=True, text=True)
    if result_v2.returncode != 0:
        print(f"  \u2717 V2 monitor failed:\n{result_v2.stderr}")
        sys.exit(1)
    v2_output = json.loads(result_v2.stdout)
    print(f"  \u2192 V2: {v2_output['allow']} ALLOW, {v2_output['hold']} HOLD, {v2_output['deny']} DENY")

    print("\n[4/4] Evaluating with V1 monitor (JavaScript)...")
    v1_path = Path(__file__).parent / "verifiers" / "v1_monitor.js"
    with open(scenarios_file, "r") as f:
        result_v1 = subprocess.run(["node", str(v1_path)], stdin=f, capture_output=True, text=True)
    if result_v1.returncode != 0:
        print(f"  \u2717 V1 monitor failed:\n{result_v1.stderr}")
        sys.exit(1)
    v1_output = json.loads(result_v1.stdout)
    print(f"  \u2192 V1: {v1_output['allow']} ALLOW, {v1_output['hold']} HOLD, {v1_output['deny']} DENY")

    agreements = 0
    total = len(scenarios)
    for i in range(total):
        if v1_output["verdicts"][i]["decision"] == v2_output["verdicts"][i]["decision"]:
            agreements += 1
    concordance = agreements / total if total > 0 else 0.0

    print("\n" + "=" * 70)
    print(f"CONCORDANCE: {agreements}/{total} = {concordance:.4f}")

    result = {
        "calibration_seed": CALIBRATION_SEED,
        "scenarios_generated": total,
        "revocation_timing_effectiveness": "PASS",
        "v1_output": v1_output,
        "v2_output": v2_output,
        "concordance": {
            "agreements": agreements,
            "total": total,
            "percentage": round(concordance * 100, 2),
        },
        "verdict": "PASS" if concordance >= 0.99 else "FAIL",
    }
    result_file = Path(__file__).parent / "results" / "killgate_calibration.json"
    with open(result_file, "w") as f:
        json.dump(result, f, indent=2)
    print(f"Results written to {result_file}")

    if concordance >= 0.99:
        print("\n\u2713 KILL-GATE PASS: Concordance \u2265 99% \u2014 proceed to arm execution")
        print("=" * 70)
        return 0
    else:
        print(f"\n\u2717 KILL-GATE FAIL: Concordance {concordance:.4f} < 0.99")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    sys.exit(run_killgate())
