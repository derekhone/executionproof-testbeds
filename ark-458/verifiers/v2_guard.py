#!/usr/bin/env python3
"""
ARK-458 V2 Guard (Python) — Cloud IAM Role Grant · Exact-Action Binding.

An authorization is APPROVED bound to an exact IAM action tuple. At execution
time an IAM grant action is presented. The guard ALLOWs only if the execution
action matches the approved action EXACTLY on every binding dimension.

Exact string equality — NO normalization, NO case folding, NO whitespace
trimming, NO homoglyph mapping, NO privilege "subset" reasoning. A confusable
near-match is a MISMATCH. This is the fail-closed exact-action-binding rule.

Independent re-implementation of the same procedure as v1_guard.js.
"""
import json
import sys
from typing import Dict, Any

BINDING_DIMS = ["principal", "role", "account", "permission_set", "condition"]


def evaluate(scenario: Dict[str, Any]) -> Dict[str, Any]:
    binding = scenario["authorization"]["binding"]
    action = scenario["execution"]["action"]

    for dim in BINDING_DIMS:
        a = binding.get(dim)
        b = action.get(dim)
        # Strict, code-point-exact comparison; reject non-strings / absence.
        if not isinstance(a, str) or not isinstance(b, str) or a != b:
            return {
                "decision": "DENY",
                "reason": (
                    f"Action mismatch on '{dim}': approved grant bound to "
                    f"{json.dumps(a)} but execution action is {json.dumps(b)} "
                    f"(approval does not authorize a mutated IAM action)"
                ),
            }

    return {
        "decision": "ALLOW",
        "reason": "Execution action matches the approved IAM grant on all binding dimensions",
    }


if __name__ == "__main__":
    scenarios = json.load(sys.stdin)
    results = []
    for sc in scenarios:
        result = evaluate(sc)
        results.append({
            "scenario_id": sc["scenario_id"],
            "arm": sc["arm"],
            **result,
        })
    json.dump(results, sys.stdout, indent=2)
