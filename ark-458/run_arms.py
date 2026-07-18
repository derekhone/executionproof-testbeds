#!/usr/bin/env python3
"""
ARK-458 Arm Execution — Cloud IAM Role Grant · Exact-Action Binding.
Run all 8 arms with dual independent guards, compute metrics, decide verdict.
"""
import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timezone
from generator.scenario_generator import (
    ScenarioGenerator, action_mutation_effective, SEED_BASE, ARMS,
)

BASELINE_ARM = 1
MUTATION_ARMS = [2, 3, 4, 5, 6, 7, 8]
HERE = Path(__file__).parent


def _iso():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def run_arm(arm: int) -> dict:
    print("=" * 70)
    print(f"ARM {arm}: {ARMS[arm]['label']} (expect {ARMS[arm]['expected']})")
    print("=" * 70)

    print(f"[1/4] Generating 100 scenarios (seed {SEED_BASE + arm})...")
    gen = ScenarioGenerator(SEED_BASE + arm)
    scenarios = gen.generate_scenarios(arm, count=100)
    print(f"  -> Generated {len(scenarios)} scenarios")

    print("[2/4] Checking action-mutation effectiveness (kill condition)...")
    failures = []
    for sc in scenarios:
        ok, reason = action_mutation_effective(sc, arm)
        if not ok:
            failures.append((sc["scenario_id"], reason))
    if failures:
        for sid, r in failures[:5]:
            print(f"  x FAIL: {sid}: {r}")
        print(f"\nx ARM {arm} ABORT: effectiveness gate failed ({len(failures)} bad)")
        sys.exit(1)
    print("  ok All scenarios effective (real mutation / true exact match)")

    print("[3/4] Evaluating with V1 guard (JavaScript)...")
    r1 = subprocess.run(["node", "verifiers/v1_guard.js"],
                        input=json.dumps(scenarios), capture_output=True, text=True, cwd=HERE)
    if r1.returncode != 0:
        print(f"  x V1 failed:\n{r1.stderr}"); sys.exit(1)
    results_v1 = json.loads(r1.stdout)
    v1 = {k: sum(1 for r in results_v1 if r["decision"] == k.upper()) for k in ["allow", "hold", "deny"]}
    print(f"  -> V1: {v1['allow']} ALLOW, {v1['hold']} HOLD, {v1['deny']} DENY")

    print("[4/4] Evaluating with V2 guard (Python)...")
    r2 = subprocess.run(["python3", "verifiers/v2_guard.py"],
                        input=json.dumps(scenarios), capture_output=True, text=True, cwd=HERE)
    if r2.returncode != 0:
        print(f"  x V2 failed:\n{r2.stderr}"); sys.exit(1)
    results_v2 = json.loads(r2.stdout)
    v2 = {k: sum(1 for r in results_v2 if r["decision"] == k.upper()) for k in ["allow", "hold", "deny"]}
    print(f"  -> V2: {v2['allow']} ALLOW, {v2['hold']} HOLD, {v2['deny']} DENY")

    agreements = sum(1 for a, b in zip(results_v1, results_v2) if a["decision"] == b["decision"])
    concordance_pct = agreements / len(scenarios) * 100
    print(f"  -> Concordance: {agreements}/{len(scenarios)} = {concordance_pct:.2f}%")

    results_dir = HERE / "results"
    results_dir.mkdir(exist_ok=True)
    arm_result = {
        "run_start_time": _iso(),
        "arm": arm,
        "label": ARMS[arm]["label"],
        "expected": ARMS[arm]["expected"],
        "scenarios_count": len(scenarios),
        "v1": v1,
        "v2": v2,
        "concordance": {"agreements": agreements, "total": len(scenarios), "percentage": concordance_pct},
        "rates": {k: round(v2[k] / 100.0, 4) for k in ["allow", "hold", "deny"]},
    }
    with open(results_dir / f"arm_{arm}_results.json", "w") as f:
        json.dump(arm_result, f, indent=2)
    with open(results_dir / f"arm_{arm}_scenarios.json", "w") as f:
        json.dump(scenarios, f, indent=2, ensure_ascii=False)
    return arm_result


def compute_overall(arm_results: list) -> dict:
    print(f"\n{'=' * 70}\nOVERALL RESULTS\n{'=' * 70}")
    by_arm = {r["arm"]: r for r in arm_results}

    g_allow_exact = by_arm[BASELINE_ARM]["rates"]["allow"]
    g_deny_mutation_min = min(by_arm[a]["rates"]["deny"] for a in MUTATION_ARMS)
    g_margin = min(g_allow_exact, g_deny_mutation_min) - 0.05

    c1 = g_allow_exact >= 0.95
    c2 = g_deny_mutation_min >= 0.95
    c3 = g_margin >= 0.90
    verdict = "PASS" if (c1 and c2 and c3) else "FAIL"

    tot_agree = sum(r["concordance"]["agreements"] for r in arm_results)
    tot = sum(r["concordance"]["total"] for r in arm_results)
    conc = tot_agree / tot * 100 if tot else 0.0

    m = lambda ok: "PASS" if ok else "FAIL"
    print(f"\nPrimary Metrics:")
    print(f"  g_allow_exact (arm 1 ALLOW):            {g_allow_exact:.4f}")
    print(f"  g_deny_mutation_min (arms 2-8 DENY):    {g_deny_mutation_min:.4f}")
    print(f"  g_margin:                               {g_margin:.4f}")
    print(f"\nPass Criteria:")
    print(f"  C1 (g_allow_exact >= 0.95):        {m(c1)}")
    print(f"  C2 (g_deny_mutation_min >= 0.95):  {m(c2)}")
    print(f"  C3 (g_margin >= 0.90):             {m(c3)}")
    print(f"\nSecondary: V1-V2 concordance {conc:.2f}% ({tot_agree}/{tot})")
    print(f"\n{'=' * 70}\nVERDICT: {verdict}\n{'=' * 70}")

    overall = {
        "experiment": "ARK-458",
        "title": "Cloud IAM Role Grant - Exact-Action Binding",
        "run_start_time": arm_results[0].get("run_start_time"),
        "run_end_time": _iso(),
        "substrate": "classical software (no quantum hardware)",
        "arms_executed": [r["arm"] for r in arm_results],
        "primary_metrics": {
            "g_allow_exact": round(g_allow_exact, 4),
            "g_deny_mutation_min": round(g_deny_mutation_min, 4),
            "g_margin": round(g_margin, 4),
        },
        "criteria": {"c1_allow_exact_pass": c1, "c2_deny_mutation_pass": c2, "c3_margin_pass": c3},
        "overall_concordance": {"agreements": tot_agree, "total": tot, "percentage": round(conc, 2)},
        "verdict": verdict,
        "per_arm_summary": {
            f"arm_{r['arm']}": {
                "label": r["label"], "expected": r["expected"],
                "allow_rate": r["rates"]["allow"], "hold_rate": r["rates"]["hold"],
                "deny_rate": r["rates"]["deny"],
                "concordance_pct": r["concordance"]["percentage"],
            } for r in arm_results
        },
    }
    with open(HERE / "results" / "overall_results.json", "w") as f:
        json.dump(overall, f, indent=2)
    return overall


def main():
    print("=" * 70)
    print("ARK-458 ARM EXECUTION - Cloud IAM Role Grant - Exact-Action Binding")
    print("=" * 70)
    arm_results = [run_arm(arm) for arm in range(1, 9)]
    compute_overall(arm_results)


if __name__ == "__main__":
    main()
