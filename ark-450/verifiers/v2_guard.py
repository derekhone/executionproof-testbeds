#!/usr/bin/env python3
"""
ARK-450 V2 Guard (Python)
Independent implementation of substitution attack detection.
Tests exact action matching: authorization for A cannot be used for B.
"""

import json
import sys


def decide(scenario):
    """
    ARK-450 Decision Function
    
    Logic: Authorization proof for approved_action can ONLY be used for
    an executed_action that matches EXACTLY in ALL fields.
    
    Args:
        scenario: Dict containing approved_action and executed_action
    
    Returns:
        str: "ALLOW" if exact match, "DENY" if any field differs
    """
    approved = scenario["approved_action"]
    executed = scenario["executed_action"]
    
    # Exact equality check - Python's == does deep comparison for dicts
    if approved == executed:
        return "ALLOW"
    else:
        return "DENY"


def process_scenario(scenario):
    """Process a single scenario and return decision."""
    decision = decide(scenario)
    
    return {
        "scenario_id": scenario["scenario_id"],
        "arm_id": scenario["arm_id"],
        "substitution_type": scenario["substitution_type"],
        "decision": decision,
        "verifier": "v2_py"
    }


def main():
    """Process all scenarios from stdin or file."""
    if len(sys.argv) > 1:
        # File provided as argument
        with open(sys.argv[1], 'r') as f:
            scenarios = json.load(f)
    else:
        # Read from stdin
        scenarios = json.load(sys.stdin)
    
    print(f"V2 Guard (Python) - Processing {len(scenarios)} scenarios", file=sys.stderr)
    
    results = [process_scenario(scenario) for scenario in scenarios]
    
    # Output results as JSON
    print(json.dumps(results, indent=2))
    
    # Statistics to stderr
    allow_count = sum(1 for r in results if r["decision"] == "ALLOW")
    deny_count = sum(1 for r in results if r["decision"] == "DENY")
    
    print(f"V2 Results: {allow_count} ALLOW, {deny_count} DENY", file=sys.stderr)


if __name__ == "__main__":
    main()
