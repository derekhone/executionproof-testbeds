#!/usr/bin/env python3
"""
ARK-457 Arm Execution — Cross-Context Authorization Replay (Confused Deputy)
Run all 8 arms, compute metrics, and determine verdict.
"""
import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime
from generator.scenario_generator import (
    ScenarioGenerator, context_replay_effective, SEED_BASE, ARMS,
)

BASELINE_ARM = 1
CROSS_CONTEXT_ARMS = [2, 3, 4, 5, 6, 7, 8]


def run_arm(arm: int) -> dict:
    print("=" * 70)
    print(f"ARM {arm}: {ARMS[arm]['label']} (expect {ARMS[arm]['expected']})")
    print("=" * 70)

    print(f"[1/4] Generating 100 scenarios (seed {SEED_BASE + arm})...")
    gen = ScenarioGenerator(SEED_BASE + arm)
    scenarios = gen.generate_scenarios(arm, count=100)
    print(f"  → Generated {len(scenarios)} scenarios")

    print("[2/4] Checking context-replay effectiveness...")
    failures = []
    for sc in scenarios:
        is_eff, reason = context_replay_effective(sc, arm)
        if not is_eff:
            failures.append((sc["scenario_id"], reason))
            print(f"  ✗ FAIL: {sc['scenario_id']} not effective: {reason}")
    if failures:
        print(f"\n✗ ARM {arm} ABORT: context-replay effectiveness gate failed")
        sys.exit(1)
    print("  ✓ All scenarios context-replay-effective")

    print("[3/4] Evaluating with V1 guard (JavaScript)...")
    result_v1 = subprocess.run(
        ["node", "verifiers/v1_guard.js"],
        input=json.dumps(scenarios), capture_output=True, text=True,
        cwd=Path(__file__).parent,
    )
    if result_v1.returncode != 0:
        print(f"  ✗ V1 failed:\n{result_v1.stderr}")
        sys.exit(1)
    results_v1 = json.loads(result_v1.stdout)
    v1_allow = sum(1 for r in results_v1 if r["decision"] == "ALLOW")
    v1_hold = sum(1 for r in results_v1 if r["decision"] == "HOLD")
    v1_deny = sum(1 for r in results_v1 if r["decision"] == "DENY")
    print(f"  → V1: {v1_allow} ALLOW, {v1_hold} HOLD, {v1_deny} DENY")

    print("[4/4] Evaluating with V2 guard (Python)...")
    result_v2 = subprocess.run(
        ["python3", "verifiers/v2_guard.py"],
        input=json.dumps(scenarios), capture_output=True, text=True,
        cwd=Path(__file__).parent,
    )
    if result_v2.returncode != 0:
        print(f"  ✗ V2 failed:\n{result_v2.stderr}")
        sys.exit(1)
    results_v2 = json.loads(result_v2.stdout)
    v2_allow = sum(1 for r in results_v2 if r["decision"] == "ALLOW")
    v2_hold = sum(1 for r in results_v2 if r["decision"] == "HOLD")
    v2_deny = sum(1 for r in results_v2 if r["decision"] == "DENY")
    print(f"  → V2: {v2_allow} ALLOW, {v2_hold} HOLD, {v2_deny} DENY")

    agreements = sum(1 for r1, r2 in zip(results_v1, results_v2) if r1["decision"] == r2["decision"])
    concordance_pct = (agreements / len(scenarios)) * 100
    print(f"  → Concordance: {agreements}/{len(scenarios)} = {concordance_pct:.2f}%")

    results_dir = Path(__file__).parent / "results"
    results_dir.mkdir(exist_ok=True)

    allow_rate = v2_allow / 100.0
    hold_rate = v2_hold / 100.0
    deny_rate = v2_deny / 100.0

    arm_result = {
        "run_start_time": datetime.utcnow().isoformat() + "Z",
        "arm": arm,
        "label": ARMS[arm]["label"],
        "expected": ARMS[arm]["expected"],
        "scenarios_count": len(scenarios),
        "v1": {"allow": v1_allow, "hold": v1_hold, "deny": v1_deny},
        "v2": {"allow": v2_allow, "hold": v2_hold, "deny": v2_deny},
        "concordance": {"agreements": agreements, "total": len(scenarios), "percentage": concordance_pct},
        "rates": {"allow": round(allow_rate, 4), "hold": round(hold_rate, 4), "deny": round(deny_rate, 4)},
    }

    with open(results_dir / f"arm_{arm}_results.json", "w") as f:
        json.dump(arm_result, f, indent=2)
    with open(results_dir / f"arm_{arm}_scenarios.json", "w") as f:
        json.dump(scenarios, f, indent=2, ensure_ascii=False)

    return arm_result


def compute_overall(arm_results: list) -> dict:
    print(f"\n{'=' * 70}")
    print("OVERALL RESULTS")
    print(f"{'=' * 70}")

    by_arm = {r["arm"]: r for r in arm_results}

    g_allow_exact = by_arm[BASELINE_ARM]["rates"]["allow"]
    g_deny_crosscontext_min = min(by_arm[a]["rates"]["deny"] for a in CROSS_CONTEXT_ARMS)
    g_margin = min(g_allow_exact, g_deny_crosscontext_min) - 0.05

    c1_pass = g_allow_exact >= 0.95
    c2_pass = g_deny_crosscontext_min >= 0.95
    c3_pass = g_margin >= 0.90
    verdict = "PASS" if (c1_pass and c2_pass and c3_pass) else "FAIL"

    total_agreements = sum(r["concordance"]["agreements"] for r in arm_results)
    total_scenarios = sum(r["concordance"]["total"] for r in arm_results)
    overall_concordance_pct = (total_agreements / total_scenarios) * 100 if total_scenarios > 0 else 0.0

    print("\nPrimary Metrics:")
    print(f"  g_allow_exact (arm {BASELINE_ARM} ALLOW):          {g_allow_exact:.4f}")
    print(f"  g_deny_crosscontext_min (arms 2-8 DENY):  {g_deny_crosscontext_min:.4f}")
    print(f"  g_margin:                                  {g_margin:.4f}")

    def _mark(ok):
        return "✓ PASS" if ok else "✗ FAIL"

    print("\nPass Criteria:")
    print(f"  C1 (g_allow_exact ≥ 0.95):            {_mark(c1_pass)}")
    print(f"  C2 (g_deny_crosscontext_min ≥ 0.95):  {_mark(c2_pass)}")
    print(f"  C3 (g_margin ≥ 0.90):                 {_mark(c3_pass)}")

    print("\nSecondary Observations:")
    print(f"  Overall V1-V2 concordance:            {overall_concordance_pct:.2f}% ({total_agreements}/{total_scenarios})")

    print(f"\n{'=' * 70}")
    print(f"VERDICT: {verdict}")
    print(f"{'=' * 70}")

    overall_result = {
        "run_start_time": arm_results[0].get("run_start_time"),
        "run_end_time": datetime.utcnow().isoformat() + "Z",
        "arms_executed": [r["arm"] for r in arm_results],
        "primary_metrics": {
            "g_allow_exact": round(g_allow_exact, 4),
            "g_deny_crosscontext_min": round(g_deny_crosscontext_min, 4),
            "g_margin": round(g_margin, 4),
        },
        "criteria": {
            "c1_allow_exact_pass": c1_pass,
            "c2_deny_crosscontext_pass": c2_pass,
            "c3_margin_pass": c3_pass,
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

    results_dir = Path(__file__).parent / "results"
    with open(results_dir / "overall_results.json", "w") as f:
        json.dump(overall_result, f, indent=2)

    return overall_result


def main():
    print("=" * 70)
    print("ARK-457 ARM EXECUTION")
    print("=" * 70)
    arm_results = []
    for arm in range(1, 9):
        arm_results.append(run_arm(arm))
    compute_overall(arm_results)


if __name__ == "__main__":
    main()
