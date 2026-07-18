#!/usr/bin/env python3
"""
ARK-458 Kill-Gate (Negative Control).

Purpose: prove the testbed can actually CATCH a broken guard. A deliberately
lenient "normalizing" comparator (strips whitespace, case-folds, removes
zero-width chars, maps homoglyphs, and treats a higher-privilege role as an
acceptable 'superset') is run against the same scenarios. If our exact-action
binding test is meaningful, this bad guard MUST wrongly ALLOW a detectable
number of mutated actions — especially the confusable arm (8) and the
role-escalation arm (2).

A test that nothing can fail is not a test. This gate documents falsifiability.
"""
import json
from pathlib import Path
from datetime import datetime, timezone
from generator.scenario_generator import (
    ScenarioGenerator, SEED_BASE, ARMS, ROLE_RANK, _naive_normalize,
)

HERE = Path(__file__).parent
BINDING_DIMS = ["principal", "role", "account", "permission_set", "condition"]


def bad_guard(scenario) -> str:
    """Lenient, INSECURE comparator — the thing a naive vendor might ship."""
    binding = scenario["authorization"]["binding"]
    action = scenario["execution"]["action"]
    for dim in BINDING_DIMS:
        a, b = binding.get(dim), action.get(dim)
        if dim == "role":
            # BUG: accept any role that is "at least as privileged" (superset).
            if ROLE_RANK.get(b, -1) >= ROLE_RANK.get(a, -2):
                continue
            return "DENY"
        if dim == "permission_set":
            continue  # BUG: ignores the effective-policy hash entirely
        if _naive_normalize(str(a)) != _naive_normalize(str(b)):
            return "DENY"
    return "ALLOW"


def main():
    print("=" * 70)
    print("ARK-458 KILL-GATE (negative control)")
    print("=" * 70)
    scenarios = []
    for arm in range(1, 9):
        gen = ScenarioGenerator(SEED_BASE + arm)
        scenarios.extend(gen.generate_scenarios(arm, count=100))

    wrong_allows = []
    for sc in scenarios:
        if sc["expected"] == "DENY" and bad_guard(sc) == "ALLOW":
            wrong_allows.append(sc["scenario_id"])

    by_arm = {}
    for sid in wrong_allows:
        arm = int(sid.split("-A")[1].split("-")[0])
        by_arm[arm] = by_arm.get(arm, 0) + 1

    total_attacks = sum(1 for s in scenarios if s["expected"] == "DENY")
    caught = len(wrong_allows)
    print(f"Bad (lenient) guard wrongly ALLOWED {caught}/{total_attacks} mutated actions")
    for arm in sorted(by_arm):
        print(f"  arm {arm} ({ARMS[arm]['label']}): {by_arm[arm]} wrong-allows")

    gate_pass = caught > 0  # the testbed CAN catch a bad guard
    print(f"\nKILL-GATE: {'PASS (testbed is falsifiable)' if gate_pass else 'FAIL (test catches nothing)'}")

    out = {
        "experiment": "ARK-458",
        "kind": "negative_control_killgate",
        "run_time": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "total_attack_scenarios": total_attacks,
        "bad_guard_wrong_allows": caught,
        "wrong_allows_by_arm": {str(k): v for k, v in sorted(by_arm.items())},
        "gate_pass": gate_pass,
        "note": ("A deliberately lenient comparator wrongly authorizes mutated IAM "
                 "actions, confirming the exact-action-binding testbed is falsifiable "
                 "and that the arms are genuine attacks."),
    }
    (HERE / "results").mkdir(exist_ok=True)
    with open(HERE / "results" / "killgate_results.json", "w") as f:
        json.dump(out, f, indent=2)


if __name__ == "__main__":
    main()
