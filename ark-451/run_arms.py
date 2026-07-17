#!/usr/bin/env python3
"""
ARK-451 Arm Execution
Executes all 8 arms (800 scenarios total), enforces the revocation-timing gate,
evaluates with dual independent monitors, computes criteria C1-C4, outputs verdict.

Expected decisions:
  ALLOW arms: 1 (valid-throughout), 6 (revoked-then-reauthorized), 8 (revoked-after-execution)
  DENY  arms: 2 (revoked-before-bind), 3 (revoked-after-decision-before-contact), 4 (revoked-during-multistep)
  HOLD  arms: 5 (in-flight-at-contact), 7 (in-flight-boundary)
"""
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "generator"))
from scenario_generator import ScenarioGenerator, revocation_effective, SEED_BASE, ARMS

ALLOW_ARMS = [1, 6, 8]
DENY_ARMS = [2, 3, 4]
HOLD_ARMS = [5, 7]


def run_arm(arm: int) -> dict:
    label, expected = ARMS[arm]
    print(f"\n{'=' * 70}")
    print(f"ARM {arm}: {label} (expect {expected.upper()})")
    print(f"{'=' * 70}")

    print(f"[1/4] Generating 100 scenarios (seed {SEED_BASE + arm})...")
    gen = ScenarioGenerator(SEED_BASE + arm)
    scenarios, audit = gen.generate_arm_scenarios(arm, count=100)
    print(f"  \u2192 Generated {len(scenarios)} scenarios")

    print("[2/4] Checking revocation-timing effectiveness...")
    all_effective = True
    for scenario in scenarios:
        effective, reason = revocation_effective(scenario, arm)
        if not effective:
            print(f"  \u2717 FAIL: {scenario['scenario_id']} not effective: {reason}")
            all_effective = False
    if not all_effective:
        print(f"\n\u2717 ARM {arm} ABORT: revocation-timing gate failed")
        sys.exit(1)
    print(f"  \u2713 All scenarios timing-effective")

    scenarios_file = Path(__file__).parent / "results" / f"arm_{arm}_scenarios.json"
    scenarios_file.parent.mkdir(exist_ok=True)
    with open(scenarios_file, "w") as f:
        json.dump(scenarios, f)

    print("[3/4] Evaluating with V1 monitor (JavaScript)...")
    v1_path = Path(__file__).parent / "verifiers" / "v1_monitor.js"
    with open(scenarios_file, "r") as f:
        result_v1 = subprocess.run(["node", str(v1_path)], stdin=f, capture_output=True, text=True)
    if result_v1.returncode != 0:
        print(f"  \u2717 V1 failed:\n{result_v1.stderr}")
        sys.exit(1)
    v1_output = json.loads(result_v1.stdout)
    print(f"  \u2192 V1: {v1_output['allow']} ALLOW, {v1_output['hold']} HOLD, {v1_output['deny']} DENY")

    print("[4/4] Evaluating with V2 monitor (Python)...")
    v2_path = Path(__file__).parent / "verifiers" / "v2_monitor.py"
    with open(scenarios_file, "r") as f:
        result_v2 = subprocess.run(["python3", str(v2_path)], stdin=f, capture_output=True, text=True)
    if result_v2.returncode != 0:
        print(f"  \u2717 V2 failed:\n{result_v2.stderr}")
        sys.exit(1)
    v2_output = json.loads(result_v2.stdout)
    print(f"  \u2192 V2: {v2_output['allow']} ALLOW, {v2_output['hold']} HOLD, {v2_output['deny']} DENY")

    agreements = sum(
        1 for i in range(len(scenarios))
        if v1_output["verdicts"][i]["decision"] == v2_output["verdicts"][i]["decision"]
    )
    concordance_pct = (agreements / len(scenarios)) * 100 if scenarios else 0.0
    print(f"  \u2192 Concordance: {agreements}/{len(scenarios)} = {concordance_pct:.2f}%")

    total = len(scenarios)
    allow_rate = v2_output["allow"] / total if total > 0 else 0.0
    hold_rate = v2_output["hold"] / total if total > 0 else 0.0
    deny_rate = v2_output["deny"] / total if total > 0 else 0.0

    arm_result = {
        "arm": arm,
        "label": label,
        "expected": expected.upper(),
        "scenarios": len(scenarios),
        "seed": SEED_BASE + arm,
        "revocation_timing_effectiveness": "PASS",
        "v1_output": v1_output,
        "v2_output": v2_output,
        "concordance": {
            "agreements": agreements,
            "total": total,
            "percentage": round(concordance_pct, 2),
        },
        "rates": {
            "allow": round(allow_rate, 4),
            "hold": round(hold_rate, 4),
            "deny": round(deny_rate, 4),
        },
    }
    result_file = Path(__file__).parent / "results" / f"arm_{arm}_results.json"
    with open(result_file, "w") as f:
        json.dump(arm_result, f, indent=2)
    return arm_result


def compute_overall(arm_results: list) -> dict:
    print(f"\n{'=' * 70}")
    print("OVERALL RESULTS")
    print(f"{'=' * 70}")

    by_arm = {r["arm"]: r for r in arm_results}

    g_allow_valid_min = min(by_arm[a]["rates"]["allow"] for a in ALLOW_ARMS)
    g_deny_revoked_min = min(by_arm[a]["rates"]["deny"] for a in DENY_ARMS)
    g_hold_inflight_min = min(by_arm[a]["rates"]["hold"] for a in HOLD_ARMS)
    g_margin = min(g_allow_valid_min, g_deny_revoked_min, g_hold_inflight_min) - 0.05

    c1_pass = g_allow_valid_min >= 0.95
    c2_pass = g_deny_revoked_min >= 0.95
    c3_pass = g_hold_inflight_min >= 0.95
    c4_pass = g_margin >= 0.90
    verdict = "PASS" if (c1_pass and c2_pass and c3_pass and c4_pass) else "FAIL"

    total_agreements = sum(r["concordance"]["agreements"] for r in arm_results)
    total_scenarios = sum(r["concordance"]["total"] for r in arm_results)
    overall_concordance_pct = (total_agreements / total_scenarios) * 100 if total_scenarios > 0 else 0.0

    print(f"\nPrimary Metrics:")
    print(f"  g_allow_valid_min (arms 1,6,8 ALLOW):    {g_allow_valid_min:.4f}")
    print(f"  g_deny_revoked_min (arms 2,3,4 DENY):    {g_deny_revoked_min:.4f}")
    print(f"  g_hold_inflight_min (arms 5,7 HOLD):     {g_hold_inflight_min:.4f}")
    print(f"  g_margin:                                {g_margin:.4f}")

    def _mark(ok):
        return "\u2713 PASS" if ok else "\u2717 FAIL"

    print(f"\nPass Criteria:")
    print(f"  C1 (g_allow_valid_min \u2265 0.95):    {_mark(c1_pass)}")
    print(f"  C2 (g_deny_revoked_min \u2265 0.95):   {_mark(c2_pass)}")
    print(f"  C3 (g_hold_inflight_min \u2265 0.95):  {_mark(c3_pass)}")
    print(f"  C4 (g_margin \u2265 0.90):             {_mark(c4_pass)}")

    print(f"\nSecondary Observations:")
    print(f"  Overall V1-V2 concordance:       {overall_concordance_pct:.2f}% ({total_agreements}/{total_scenarios})")

    print(f"\n{'=' * 70}")
    print(f"VERDICT: {verdict}")
    print(f"{'=' * 70}")

    overall_result = {
        "run_start_time": arm_results[0].get("run_start_time"),
        "run_end_time": datetime.utcnow().isoformat() + "Z",
        "arms_executed": [r["arm"] for r in arm_results],
        "primary_metrics": {
            "g_allow_valid_min": round(g_allow_valid_min, 4),
            "g_deny_revoked_min": round(g_deny_revoked_min, 4),
            "g_hold_inflight_min": round(g_hold_inflight_min, 4),
            "g_margin": round(g_margin, 4),
        },
        "criteria": {
            "c1_allow_valid_pass": c1_pass,
            "c2_deny_revoked_pass": c2_pass,
            "c3_hold_inflight_pass": c3_pass,
            "c4_margin_pass": c4_pass,
        },
        "overall_concordance": {
            "agreements": total_agreements,
            "total": total_scenarios,
            "percentage": round(overall_concordance_pct, 2),
        },
        "verdict": verdict,
        "per_arm_summary": {
            f"arm_{r['arm']}": {
                "label": r["label"],
                "expected": r["expected"],
                "allow_rate": r["rates"]["allow"],
                "hold_rate": r["rates"]["hold"],
                "deny_rate": r["rates"]["deny"],
            }
            for r in arm_results
        },
    }
    result_file = Path(__file__).parent / "results" / "overall_results.json"
    with open(result_file, "w") as f:
        json.dump(overall_result, f, indent=2)
    return overall_result


def main():
    print("=" * 70)
    print("ARK-451 ARM EXECUTION")
    print("=" * 70)
    run_start = datetime.utcnow().isoformat() + "Z"
    arm_results = []
    for arm in range(1, 9):
        result = run_arm(arm)
        result["run_start_time"] = run_start
        arm_results.append(result)
    overall = compute_overall(arm_results)
    return 0 if overall["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
