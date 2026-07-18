#!/usr/bin/env python3
"""
ARK-471 V2 Guard (Python) — Production Database Query · Cross-Context Replay.

Decision logic:
  - If execution context == authorization context (exact match on all 5 dims) → ALLOW
  - If ANY dimension differs → DENY (cross-context replay, fail-closed)

Independent re-implementation of the same procedure as v1_guard.js.
"""
import json
import sys
from typing import Any, Dict

CONTEXT_DIMS = ["tenant", "session", "resource", "audience", "environment"]

def evaluate(scenario: Dict[str, Any]) -> Dict[str, Any]:
    original_context = scenario["authorization"]["context"]
    presented_context = scenario["execution"]["context"]
    
    for dim in CONTEXT_DIMS:
        orig = original_context.get(dim)
        pres = presented_context.get(dim)
        if orig != pres:
            return {
                "decision": "DENY",
                "reason": f"Cross-context replay detected: context mismatch on '{dim}' (approved={json.dumps(orig)}, presented={json.dumps(pres)})"
            }
    
    return {
        "decision": "ALLOW",
        "reason": "Context matches on all dimensions; authorization valid for this context"
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
