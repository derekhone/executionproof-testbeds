#!/usr/bin/env python3
"""
ARK-453 V2 Resolver (Python)
Independent implementation of the evidence conflict resolution procedure.
Reads scenarios (JSON array), outputs decisions (ALLOW/HOLD/DENY).
"""
import sys
import json
from typing import Dict, List

# Decision types
ALLOW = "ALLOW"
HOLD = "HOLD"
DENY = "DENY"

# Evidence signals
ALLOW_SIGNAL = "ALLOW_SIGNAL"
DENY_SIGNAL = "DENY_SIGNAL"
UNKNOWN = "UNKNOWN"


def resolve_scenario(scenario: Dict) -> str:
    """
    Resolve a single evidence scenario to ALLOW, HOLD, or DENY.
    
    Decision procedure:
    1. If any source = UNKNOWN → HOLD
    2. Collect unique non-UNKNOWN signals
    3. If all sources emit ALLOW_SIGNAL → ALLOW
    4. If all sources emit DENY_SIGNAL → DENY
    5. If sources disagree (mixed ALLOW/DENY) → HOLD
    """
    sources = scenario["evidence_sources"]
    
    # Extract signals from all 6 sources
    signals = [
        sources["identity"]["signal"],
        sources["policy"]["signal"],
        sources["risk"]["signal"],
        sources["approval"]["signal"],
        sources["registry"]["signal"],
        sources["temporal"]["signal"]
    ]
    
    # Rule 1: Any UNKNOWN → HOLD
    if UNKNOWN in signals:
        return HOLD
    
    # Rule 2: Collect unique non-UNKNOWN signals
    unique_signals = set(signals)
    
    # Rule 3: All ALLOW → ALLOW
    if unique_signals == {ALLOW_SIGNAL}:
        return ALLOW
    
    # Rule 4: All DENY → DENY
    if unique_signals == {DENY_SIGNAL}:
        return DENY
    
    # Rule 5: Mixed signals → HOLD
    return HOLD


def resolve_batch(scenarios: List[Dict]) -> Dict:
    """Resolve a batch of scenarios and return summary + verdicts"""
    verdicts = []
    counts = {ALLOW: 0, HOLD: 0, DENY: 0}
    
    for scenario in scenarios:
        decision = resolve_scenario(scenario)
        verdicts.append({
            "scenario_id": scenario["scenario_id"],
            "decision": decision
        })
        counts[decision] += 1
    
    return {
        "verifier": "v2_resolver.py",
        "total": len(scenarios),
        "allow": counts[ALLOW],
        "hold": counts[HOLD],
        "deny": counts[DENY],
        "verdicts": verdicts
    }


def main():
    """CLI: read JSON array of scenarios from stdin, output results"""
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("Usage: python3 v2_resolver.py < scenarios.json")
        print("Reads JSON array of evidence scenarios, outputs decisions.")
        sys.exit(0)
    
    # Read scenarios from stdin
    try:
        scenarios = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"Error: invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)
    
    if not isinstance(scenarios, list):
        print("Error: input must be a JSON array", file=sys.stderr)
        sys.exit(1)
    
    # Resolve batch
    result = resolve_batch(scenarios)
    
    # Output JSON
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
