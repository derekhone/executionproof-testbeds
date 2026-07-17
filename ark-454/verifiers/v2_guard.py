#!/usr/bin/env python3
"""
ARK-454 Guard V2 (Python)
Independent authorization-graph guard per preregistration Section 4.3.

ISOLATION NOTICE: This implementation is built SOLELY from the prose specification
in ARK-454 PREREGISTRATION.md. It does NOT reference:
  - Guard V1 (JavaScript) source code
  - the scenario generator source code
  - any other implementation artifact

The doctrine under test: an action may be ALLOWed only when a genuinely
independent principal approves it. The guard must fail closed (DENY, or HOLD when
independence cannot be established) whenever the approving authority reduces --
directly or transitively -- to the requester.

Decision procedure (evaluate rules in order; return the FIRST that fires; DENY
precedes HOLD precedes ALLOW):

  1. Direct self-approval:            approver == requester                    -> DENY
  2. Controlled identity / shared:    requester and approver share control     -> DENY
  3. Circular delegation:             a principal repeats in delegation_chain  -> DENY
  4. Delegation-to-self:              requester in chain, or a chain principal
                                      is controlled (transitively) by requester -> DENY
  5. Inherited self-initiated wf:     authority_source == parent_workflow and
                                      confers_authority and initiator == requester -> DENY
  6. Independence unverifiable:       controller_of(approver) == "UNKNOWN", or
                                      approver absent from identities            -> HOLD
  7. Otherwise                                                                  -> ALLOW
"""

import json
import sys
from typing import Dict, Any, List, Tuple

UNKNOWN = "UNKNOWN"


def _controller_of(pid: str, identities: Dict[str, Any]):
    entry = identities.get(pid)
    if not isinstance(entry, dict):
        return None
    return entry.get("controller", None)


def _controllers_closure(pid: str, identities: Dict[str, Any]) -> set:
    """Transitive set of controllers of `pid`, stopping at null / UNKNOWN / repeat."""
    seen = set()
    cur = _controller_of(pid, identities)
    guard = 0
    while cur is not None and cur != UNKNOWN and cur not in seen and guard < 1000:
        seen.add(cur)
        cur = _controller_of(cur, identities)
        guard += 1
    return seen


def evaluate(scenario: Dict[str, Any]) -> str:
    """Return 'ALLOW', 'HOLD', or 'DENY' for a decision scenario."""
    try:
        requester = scenario["requester"]
        approver = scenario["approver"]
        identities = scenario.get("identities", {}) or {}
        chain = scenario.get("delegation_chain", []) or []
        authority_source = scenario.get("authority_source", "independent")
        parent_workflow = scenario.get("parent_workflow", None)

        # Rule 1: direct self-approval
        if approver == requester:
            return "DENY"

        # Rule 2: controlled identity / shared controller
        cR = _controllers_closure(requester, identities)
        cA = _controllers_closure(approver, identities)
        if (requester in cA) or (approver in cR) or (cR & cA):
            return "DENY"

        # Rule 3: circular delegation
        if len(chain) != len(set(chain)):
            return "DENY"

        # Rule 4: delegation-to-self
        if requester in chain:
            return "DENY"
        for p in chain:
            if requester in _controllers_closure(p, identities):
                return "DENY"

        # Rule 5: inherited self-initiated workflow authority
        if authority_source == "parent_workflow" and isinstance(parent_workflow, dict):
            if parent_workflow.get("confers_authority") is True \
                    and parent_workflow.get("initiator") == requester:
                return "DENY"

        # Rule 6: independence unverifiable
        if _controller_of(approver, identities) == UNKNOWN or approver not in identities:
            return "HOLD"

        # Rule 7: independent approval
        return "ALLOW"

    except (KeyError, TypeError):
        # Fail closed on malformed input: cannot establish independence.
        return "HOLD"


def batch_evaluate(scenarios: List[Dict[str, Any]]) -> Dict[str, Any]:
    allow = hold = deny = 0
    verdicts = []
    for s in scenarios:
        v = evaluate(s)
        verdicts.append(v)
        if v == "ALLOW":
            allow += 1
        elif v == "HOLD":
            hold += 1
        else:
            deny += 1
    total = len(scenarios)
    return {
        "verifier": "V2-Python",
        "total": total,
        "allow": allow,
        "hold": hold,
        "deny": deny,
        "verdicts": verdicts,
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 v2_guard.py <scenarios.json>", file=sys.stderr)
        sys.exit(1)
    with open(sys.argv[1], "r") as f:
        data = json.load(f)
    scenarios = data if isinstance(data, list) else [data]
    result = batch_evaluate(scenarios)
    # For a single scenario, also expose a top-level verdict for convenience.
    if len(scenarios) == 1:
        result["verdict"] = result["verdicts"][0]
    print(json.dumps(result, indent=2))
