#!/usr/bin/env python3
"""
ARK-480 V2 Guard (Python) — Production API Rate Limit · Dependency Loss.

Decision logic:
  - If ALL critical dependencies are AVAILABLE → ALLOW (can confirm validity)
  - If ANY critical dependency is UNAVAILABLE → HOLD (cannot confirm validity, fail-safe)

Independent re-implementation of the same procedure as v1_guard.js.
"""
import json
import sys
from typing import Any, Dict

CRITICAL_DEPS = ["RateLimiter", "QuotaStore", "TokenValidator", "API Rate LimitAuditor"]

def evaluate(scenario: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluate whether the API rate limit should be authorized given dependency availability.
    
    Returns: {decision: "ALLOW"|"HOLD", reason: str}
    """
    dependencies = scenario.get("dependencies", {})
    
    unavailable = [dep for dep in CRITICAL_DEPS if dependencies.get(dep) == "UNAVAILABLE"]
    
    if unavailable:
        return {
            "decision": "HOLD",
            "reason": f"Critical dependencies UNAVAILABLE: {', '.join(unavailable)} — cannot confirm validity (fail-safe)"
        }
    
    # All dependencies available → can confirm validity
    return {
        "decision": "ALLOW",
        "reason": "All critical dependencies AVAILABLE; validity confirmed"
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
