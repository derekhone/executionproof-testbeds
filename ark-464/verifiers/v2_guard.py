#!/usr/bin/env python3
"""
ARK-464 V2 Guard (Python) — Production Deployment · Revocation At Execution.

Decision logic at t_execution (re-check at moment of grant attempt):
  1. If revocation is null → ALLOW (authority valid throughout)
  2. Compute eff = t_revoke + propagation_delay
  3. If reauth exists, valid, and t_revoke < t_reauth ≤ t_execution → ALLOW
  4. Else if eff ≤ t_execution → DENY (revoked before execution, fail-closed)
  5. Else if t_revoke ≤ t_execution < eff → HOLD (in-flight, fail-safe)
  6. Else (t_revoke > t_execution) → ALLOW (revoked after execution)

Independent re-implementation of the same procedure as v1_guard.js.
"""
import json
import sys
from typing import Any, Dict

def evaluate(scenario: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluate whether the deployment should be authorized at t_execution.
    
    Returns: {decision: "ALLOW"|"DENY"|"HOLD", reason: str}
    """
    t_execution = scenario["execution"]["t_execution"]
    revocation = scenario.get("revocation")
    reauth = scenario.get("reauthorization")
    
    # Rule 1: No revocation → ALLOW
    if revocation is None:
        return {
            "decision": "ALLOW",
            "reason": "Authority valid throughout (no revocation)"
        }
    
    t_revoke = revocation["t_revoke"]
    propagation_delay = revocation["propagation_delay"]
    eff = t_revoke + propagation_delay
    
    # Rule 3: Reauth exists, valid, and t_revoke < t_reauth ≤ t_execution → ALLOW
    if reauth is not None and reauth.get("valid") is True:
        t_reauth = reauth["t_reauth"]
        if t_revoke < t_reauth <= t_execution:
            return {
                "decision": "ALLOW",
                "reason": f"Reauthorized at t={t_reauth:.3f} (after revoke t={t_revoke:.3f}, before execution t={t_execution:.3f})"
            }
    
    # Rule 4: eff ≤ t_execution → DENY (revoked before execution)
    if eff <= t_execution:
        return {
            "decision": "DENY",
            "reason": f"Authority revoked before execution (eff={eff:.3f} ≤ t_exec={t_execution:.3f}); {revocation.get('reason', 'no-reason')}"
        }
    
    # Rule 5: t_revoke ≤ t_execution < eff → HOLD (in-flight)
    if t_revoke <= t_execution < eff:
        return {
            "decision": "HOLD",
            "reason": f"Revocation in-flight at execution (t_revoke={t_revoke:.3f}, t_exec={t_execution:.3f}, eff={eff:.3f}); cannot confirm validity"
        }
    
    # Rule 6: t_revoke > t_execution → ALLOW (revoked after execution)
    if t_revoke > t_execution:
        return {
            "decision": "ALLOW",
            "reason": f"Revoked after execution (t_revoke={t_revoke:.3f} > t_exec={t_execution:.3f}); authority was valid at contact"
        }
    
    # Fallback (should not reach here if logic is exhaustive)
    return {
        "decision": "HOLD",
        "reason": "Unexpected timeline state (logic gap)"
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
