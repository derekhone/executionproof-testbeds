#!/usr/bin/env python3
"""
ARK-451 V2 Execution Monitor (Python)
Independent implementation of the revocation-during-execution decision procedure.
Reads scenarios (JSON array) from stdin, outputs decisions (ALLOW/HOLD/DENY).

Decision procedure (re-check authority at the moment of resource contact,
t_execution):
  1. If there is no revocation -> ALLOW (authority valid throughout).
  2. Compute eff = t_revoke + propagation_delay (revocation fully effective).
  3. If a VALID re-authorization was issued after the revoke and at/before
     execution -> ALLOW (a new, independent decision governs).
  4. Else if eff <= t_execution -> DENY (authority provably revoked before
     resource contact; fail closed).
  5. Else if t_revoke <= t_execution < eff -> HOLD (revocation in-flight /
     unconfirmed at contact; fail safe, do not optimistically allow).
  6. Else (t_revoke > t_execution) -> ALLOW (revocation issued only after the
     action already contacted the resource under valid authority).
"""
import sys
import json
from typing import Dict, List

ALLOW = "ALLOW"
HOLD = "HOLD"
DENY = "DENY"


def resolve_scenario(scenario: Dict) -> str:
    t_exec = scenario["t_execution"]
    rev = scenario.get("revocation")
    reauth = scenario.get("reauthorization")

    # Rule 1: no revocation -> authority valid throughout
    if rev is None:
        return ALLOW

    eff = rev["t_revoke"] + rev["propagation_delay"]

    # Rule 3: valid re-authorization issued after the revoke and at/before execution
    if reauth is not None and reauth.get("valid") is True \
            and reauth["t_reauth"] > rev["t_revoke"] and reauth["t_reauth"] <= t_exec:
        return ALLOW

    # Rule 4: revocation provably effective before resource contact -> fail closed
    if eff <= t_exec:
        return DENY

    # Rule 5: revocation in-flight (issued but not yet effective at contact) -> HOLD
    if rev["t_revoke"] <= t_exec < eff:
        return HOLD

    # Rule 6: revocation issued only after execution -> action already governed by valid authority
    return ALLOW


def resolve_batch(scenarios: List[Dict]) -> Dict:
    verdicts = []
    counts = {ALLOW: 0, HOLD: 0, DENY: 0}
    for scenario in scenarios:
        decision = resolve_scenario(scenario)
        verdicts.append({"scenario_id": scenario["scenario_id"], "decision": decision})
        counts[decision] += 1
    return {
        "verifier": "v2_monitor.py",
        "total": len(scenarios),
        "allow": counts[ALLOW],
        "hold": counts[HOLD],
        "deny": counts[DENY],
        "verdicts": verdicts,
    }


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("Usage: python3 v2_monitor.py < scenarios.json")
        print("Reads JSON array of revocation scenarios, outputs decisions.")
        sys.exit(0)

    try:
        scenarios = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"Error: invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)

    if not isinstance(scenarios, list):
        print("Error: input must be a JSON array", file=sys.stderr)
        sys.exit(1)

    result = resolve_batch(scenarios)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
