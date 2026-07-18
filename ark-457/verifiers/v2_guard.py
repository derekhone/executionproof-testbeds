#!/usr/bin/env python3
"""
ARK-457 V2 Guard (Python)
Cross-Context Authorization Replay (Confused Deputy).

An authorization is bound to a context tuple. Execution presents its own
context. The guard ALLOWs only if the execution context matches the
authorization's bound context EXACTLY on every binding dimension.

Exact string equality — NO normalization, NO case folding, NO whitespace
trimming, NO homoglyph mapping. A confusable near-match is a MISMATCH.

Independent re-implementation of the same procedure as v1_guard.js.
"""
import json
import sys
from typing import Dict, Any

BINDING_DIMS = ["tenant", "session", "resource", "audience", "environment"]


def evaluate(scenario: Dict[str, Any]) -> Dict[str, Any]:
    binding = scenario["authorization"]["binding"]
    ctx = scenario["execution"]["context"]

    for dim in BINDING_DIMS:
        a = binding.get(dim)
        b = ctx.get(dim)
        # Strict, code-point-exact comparison; reject non-strings / absence.
        if not isinstance(a, str) or not isinstance(b, str) or a != b:
            return {
                "decision": "DENY",
                "reason": (
                    f"Context mismatch on '{dim}': authorization bound to "
                    f"{json.dumps(a)} but execution context is {json.dumps(b)} "
                    f"(authorization does not transfer across contexts)"
                ),
            }

    return {
        "decision": "ALLOW",
        "reason": "Execution context matches the authorization's bound context on all binding dimensions",
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
