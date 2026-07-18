#!/usr/bin/env python3
"""ARK-472 V2 Guard (Python) — Production Database Query · Human Escalation."""
import json, sys
from typing import Any, Dict

def evaluate(scenario: Dict[str, Any]) -> Dict[str, Any]:
    requires_human_approval = scenario.get("requires_human_approval", False)
    human_approval = scenario.get("human_approval")
    
    if not requires_human_approval:
        return {"decision": "ALLOW", "reason": "No human approval required"}
    
    # Requires human approval
    if human_approval is None:
        return {"decision": "HOLD", "reason": "Human approval required but not yet received (fail-safe)"}
    
    # Check if approval is valid
    if not isinstance(human_approval, dict) or human_approval.get("valid") is not True:
        return {"decision": "HOLD", "reason": f"Human approval invalid or incomplete (fail-safe): {json.dumps(human_approval)}"}
    
    # Valid approval received
    return {"decision": "ALLOW", "reason": f"Human approval received and valid (approved_by={human_approval.get('approved_by')})"}

if __name__ == "__main__":
    scenarios = json.load(sys.stdin)
    results = [{"scenario_id": sc["scenario_id"], "arm": sc["arm"], **evaluate(sc)} for sc in scenarios]
    json.dump(results, sys.stdout, indent=2)
