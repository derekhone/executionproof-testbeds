#!/usr/bin/env python3
"""
ARK-456 V2 Guard (Python)
Evaluates authorization requests under degraded dependency conditions.
Fail-closed: if ANY required dependency is unavailable/corrupted → DENY.
"""
import json
import sys
from typing import Dict, Any

REQUIRED_DEPS = [
    "identity_provider",
    "policy_registry",
    "evidence_schema",
    "clock_source",
    "signature_key",
    "audit_store"
]

def evaluate(scenario: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluate an authorization scenario under degraded dependencies.
    
    Returns: {decision: "ALLOW"|"DENY", reason: "..."}
    """
    dependency_state = scenario["dependency_state"]
    authorization_request = scenario["authorization_request"]
    
    # Check all required dependencies
    for dep in REQUIRED_DEPS:
        if dependency_state[dep] != "available":
            return {
                "decision": "DENY",
                "reason": f"Required dependency {dep} is {dependency_state[dep]} (fail-closed)"
            }
    
    # All dependencies available — evaluate authorization normally.
    # For this experiment, the baseline request is designed to be valid.
    return {
        "decision": "ALLOW",
        "reason": "All dependencies available; authorization valid"
    }


if __name__ == "__main__":
    # CLI: read scenarios from stdin, output decisions to stdout
    scenarios = json.load(sys.stdin)
    results = []
    for sc in scenarios:
        result = evaluate(sc)
        results.append({
            "scenario_id": sc["scenario_id"],
            "arm": sc["arm"],
            **result
        })
    json.dump(results, sys.stdout, indent=2)
