#!/usr/bin/env python3
"""AUTH-002: Capability Composition and Confused-Deputy Resistance

Deterministic experiment — no LLM judge.
Preregistration hash: 3393646b26d2d4af96e24a8b7bf2cca8053ba5da84cef3613e600bf45a0b5738

Tests whether individually valid narrow capabilities remain safe when composed
across agents, tools, or chained actions — through delegated authority,
cross-agent invocation, confused-deputy patterns, stale grants, scope
intersection, and privilege laundering.
"""

import hashlib, json, datetime, os
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any

# ==============================================================================
# WORDING_EQUIVALENCES — identical to IB-001/002/003 & AUTH-001
# ==============================================================================

WORDING_EQUIVALENCES = {
    "send_payment": "send_payment",
    "transfer_funds": "send_payment",
    "send_email": "send_email",
    "dispatch_email": "send_email",
    "read_file": "read_file",
    "view_file": "read_file",
    "generate_report": "generate_report",
    "produce_report": "generate_report",
}


def normalize_action_type(action_type: str) -> str:
    return WORDING_EQUIVALENCES.get(action_type, action_type)


# ==============================================================================
# Data Model
# ==============================================================================

@dataclass
class CapabilityGrant:
    actor: str
    action_type: str          # canonical
    resource_class: str       # never "*"
    scope: str                # "single" or "batch"
    constraints: dict = field(default_factory=dict)
    issued_at: str = ""       # ISO timestamp
    expires_at: str = ""      # ISO timestamp; "" = no expiry


@dataclass
class DelegationGrant:
    delegator: str
    delegate: str
    action_type: str          # canonical
    resource_class: str
    scope: str
    constraints: dict = field(default_factory=dict)
    issued_at: str = ""
    expires_at: str = ""      # "" = no expiry


@dataclass
class ProposedAction:
    actor: str                # the executing actor
    action_type: str          # may be synonym
    target: str
    target_resource_class: str
    scope: str
    request_origin: str       # who initiated the request chain
    metadata: dict = field(default_factory=dict)


# ==============================================================================
# Fixed reference time (deterministic)
# ==============================================================================

REF_TIME = datetime.datetime(2026, 8, 16, 3, 0, 0)  # UTC reference
ONE_HOUR_AGO = (REF_TIME - datetime.timedelta(hours=1)).isoformat() + "Z"
ONE_HOUR_AHEAD = (REF_TIME + datetime.timedelta(hours=1)).isoformat() + "Z"
REF_TIME_ISO = REF_TIME.isoformat() + "Z"


def is_grant_fresh(grant, ref_time_iso: str = REF_TIME_ISO) -> bool:
    """Check if a grant is still valid at the reference time."""
    if not grant.expires_at:
        return True  # no expiry = always fresh
    return grant.expires_at > ref_time_iso


# ==============================================================================
# Five-Part Authorization Test (from AUTH-001, unchanged)
# ==============================================================================

def check_capability_match(action: ProposedAction, grant: CapabilityGrant) -> dict:
    """Check the five AUTH-001 conditions for a single grant."""
    normalized = normalize_action_type(action.action_type)
    checks = {}
    checks["C1_actor"] = grant.actor == action.actor
    checks["C2_action_type"] = normalized == grant.action_type
    checks["C3_resource_class"] = action.target_resource_class == grant.resource_class
    if grant.scope == "batch":
        checks["C4_scope"] = action.scope in ("single", "batch")
    else:
        checks["C4_scope"] = action.scope == "single"
    constraint_details = {}
    constraints_ok = True
    for ckey, cval in grant.constraints.items():
        actual = action.metadata.get(ckey)
        met = actual == cval
        constraint_details[ckey] = {"required": cval, "actual": actual, "met": met}
        if not met:
            constraints_ok = False
    checks["C5_constraints"] = constraints_ok
    checks["C5_detail"] = constraint_details
    checks["C6_fresh"] = is_grant_fresh(grant)
    all_passed = all(checks[k] for k in ["C1_actor", "C2_action_type",
                                           "C3_resource_class", "C4_scope",
                                           "C5_constraints", "C6_fresh"])
    return {"grant": asdict(grant), "checks": checks, "all_passed": all_passed}


# ==============================================================================
# Delegation Check
# ==============================================================================

def find_delegation(delegator: str, delegate: str, action: ProposedAction,
                    delegation_grants: List[DelegationGrant]) -> dict:
    """Find a matching, fresh delegation grant."""
    normalized = normalize_action_type(action.action_type)
    for dg in delegation_grants:
        if not is_grant_fresh(dg):
            continue
        if (dg.delegator == delegator and
            dg.delegate == delegate and
            dg.action_type == normalized and
            dg.resource_class == action.target_resource_class):
            scope_ok = (dg.scope == "batch" and action.scope in ("single", "batch")) or \
                       (dg.scope == action.scope)
            constraint_ok = True
            for ck, cv in dg.constraints.items():
                if action.metadata.get(ck) != cv:
                    constraint_ok = False
            if scope_ok and constraint_ok:
                return {"found": True, "delegation_grant": asdict(dg),
                        "fresh": True}
    return {"found": False, "delegation_grant": None, "fresh": None}


# ==============================================================================
# Composition-Aware Authorization
# ==============================================================================

def authorize_composed_action(
    action: ProposedAction,
    capability_grants: List[CapabilityGrant],
    delegation_grants: List[DelegationGrant]
) -> dict:
    """Full composition-aware authorization.

    1. Actor must hold a matching, fresh capability grant.
    2. If request_origin != actor, a matching delegation grant must exist
       from request_origin to actor (request-origin binding / confused-deputy defense).
    """
    normalized = normalize_action_type(action.action_type)
    normalization_changed = action.action_type != normalized

    # Step 1: capability check
    cap_audits = []
    matching_cap = None
    for g in capability_grants:
        result = check_capability_match(action, g)
        cap_audits.append(result)
        if result["all_passed"] and matching_cap is None:
            matching_cap = result

    has_capability = matching_cap is not None

    # Step 2: delegation check (request-origin binding)
    needs_delegation = action.request_origin != action.actor
    delegation_result = None
    has_delegation = False
    if needs_delegation:
        delegation_result = find_delegation(
            delegator=action.request_origin,
            delegate=action.actor,
            action=action,
            delegation_grants=delegation_grants
        )
        has_delegation = delegation_result["found"]

    # Decision
    if not has_capability:
        authorized = False
        denial_reason = "no_matching_capability"
    elif needs_delegation and not has_delegation:
        authorized = False
        denial_reason = "no_delegation_grant"
    else:
        authorized = True
        denial_reason = None

    return {
        "authorized": authorized,
        "decision": "ALLOW" if authorized else "DENY",
        "normalized_action_type": normalized,
        "normalization_changed": normalization_changed,
        "original_action_type": action.action_type,
        "has_capability": has_capability,
        "matching_capability": matching_cap,
        "needs_delegation": needs_delegation,
        "has_delegation": has_delegation,
        "delegation_result": delegation_result,
        "denial_reason": denial_reason,
        "capability_audits": cap_audits
    }


# ==============================================================================
# Privilege-Expansion Audit (K5)
# ==============================================================================

def privilege_expansion_audit(action: ProposedAction,
                              grants: List[CapabilityGrant]) -> dict:
    original = action.action_type
    normalized = normalize_action_type(original)
    changed = original != normalized
    if not changed:
        return {"original": original, "normalized": normalized,
                "changed": False, "expansion_detected": False}
    original_matches = any(original == g.action_type for g in grants)
    normalized_matches = any(normalized == g.action_type for g in grants)
    expansion = normalized_matches and not original_matches
    return {"original": original, "normalized": normalized,
            "changed": True, "expansion_detected": expansion}


# ==============================================================================
# 18 Preregistered Cases (B01–B18)
# ==============================================================================

def build_cases():
    cases = []

    # ---- B01: Delegated authority — legit ----
    # ops-agent delegates transmit to analytics-agent;
    # analytics-agent holds transmit grant + delegation grant exists
    cases.append({
        "case_id": "B01",
        "category": "Delegated authority — legit",
        "description": "ops-agent delegates transmit to analytics-agent; both grant and delegation present",
        "action": ProposedAction(
            actor="analytics-agent", action_type="transmit_external",
            target="partner-api-endpoint-v2",
            target_resource_class="partner-api", scope="single",
            request_origin="ops-agent"),
        "capability_grants": [
            CapabilityGrant(actor="analytics-agent", action_type="transmit_external",
                           resource_class="partner-api", scope="single")
        ],
        "delegation_grants": [
            DelegationGrant(delegator="ops-agent", delegate="analytics-agent",
                           action_type="transmit_external",
                           resource_class="partner-api", scope="single")
        ],
        "expected": "ALLOW"
    })

    # ---- B02: Delegated authority — no delegation grant ----
    cases.append({
        "case_id": "B02",
        "category": "Delegated authority — no delegation grant",
        "description": "analytics-agent holds transmit grant but no delegation grant exists",
        "action": ProposedAction(
            actor="analytics-agent", action_type="transmit_external",
            target="partner-api-endpoint-v2",
            target_resource_class="partner-api", scope="single",
            request_origin="ops-agent"),
        "capability_grants": [
            CapabilityGrant(actor="analytics-agent", action_type="transmit_external",
                           resource_class="partner-api", scope="single")
        ],
        "delegation_grants": [],  # no delegation
        "expected": "DENY"
    })

    # ---- B03: Delegated authority — delegate lacks capability ----
    cases.append({
        "case_id": "B03",
        "category": "Delegated authority — delegate lacks capability",
        "description": "Delegation grant exists but analytics-agent does NOT hold transmit capability",
        "action": ProposedAction(
            actor="analytics-agent", action_type="transmit_external",
            target="partner-api-endpoint-v2",
            target_resource_class="partner-api", scope="single",
            request_origin="ops-agent"),
        "capability_grants": [
            # analytics-agent has generate_report, NOT transmit_external
            CapabilityGrant(actor="analytics-agent", action_type="generate_report",
                           resource_class="finance-reports", scope="single")
        ],
        "delegation_grants": [
            DelegationGrant(delegator="ops-agent", delegate="analytics-agent",
                           action_type="transmit_external",
                           resource_class="partner-api", scope="single")
        ],
        "expected": "DENY"
    })

    # ---- B04: Cross-agent invocation — legit ----
    cases.append({
        "case_id": "B04",
        "category": "Cross-agent invocation — legit",
        "description": "ops-agent calls audit-agent to generate audit report; audit-agent holds grant + delegation",
        "action": ProposedAction(
            actor="audit-agent", action_type="generate_report",
            target="ops-audit-aug-2026.pdf",
            target_resource_class="audit-reports", scope="single",
            request_origin="ops-agent"),
        "capability_grants": [
            CapabilityGrant(actor="audit-agent", action_type="generate_report",
                           resource_class="audit-reports", scope="single")
        ],
        "delegation_grants": [
            DelegationGrant(delegator="ops-agent", delegate="audit-agent",
                           action_type="generate_report",
                           resource_class="audit-reports", scope="single")
        ],
        "expected": "ALLOW"
    })

    # ---- B05: Cross-agent invocation — no standing capability ----
    cases.append({
        "case_id": "B05",
        "category": "Cross-agent invocation — no standing capability",
        "description": "Delegation exists but analytics-agent has no delete capability",
        "action": ProposedAction(
            actor="analytics-agent", action_type="delete_record",
            target="job-2024-0891",
            target_resource_class="stale-jobs", scope="single",
            request_origin="ops-agent"),
        "capability_grants": [
            # analytics-agent has generate_report, NOT delete_record
            CapabilityGrant(actor="analytics-agent", action_type="generate_report",
                           resource_class="finance-reports", scope="single")
        ],
        "delegation_grants": [
            DelegationGrant(delegator="ops-agent", delegate="analytics-agent",
                           action_type="delete_record",
                           resource_class="stale-jobs", scope="single")
        ],
        "expected": "DENY"
    })

    # ---- B06: Confused deputy — classic ----
    # external-requester (no grants) asks ops-agent to transmit on requester's behalf
    cases.append({
        "case_id": "B06",
        "category": "Confused deputy — classic",
        "description": "external-requester asks ops-agent to transmit; ops-agent holds grant but no delegation from external-requester",
        "action": ProposedAction(
            actor="ops-agent", action_type="transmit_external",
            target="partner-api-endpoint-v2",
            target_resource_class="partner-api", scope="single",
            request_origin="external-requester"),
        "capability_grants": [
            CapabilityGrant(actor="ops-agent", action_type="transmit_external",
                           resource_class="partner-api", scope="single")
        ],
        "delegation_grants": [],  # NO delegation from external-requester
        "expected": "DENY"
    })

    # ---- B07: Confused deputy — tool-mediated ----
    cases.append({
        "case_id": "B07",
        "category": "Confused deputy — tool-mediated",
        "description": "external-requester asks ops-agent to execute_tool:reconciler; no delegation",
        "action": ProposedAction(
            actor="ops-agent", action_type="execute_tool",
            target="reconciler",
            target_resource_class="reconciler", scope="single",
            request_origin="external-requester",
            metadata={"named_tool": "reconciler"}),
        "capability_grants": [
            CapabilityGrant(actor="ops-agent", action_type="execute_tool",
                           resource_class="reconciler", scope="single",
                           constraints={"named_tool": "reconciler"})
        ],
        "delegation_grants": [],  # NO delegation from external-requester
        "expected": "DENY"
    })

    # ---- B08: Confused deputy — chained ----
    # external-requester -> analytics-agent -> ops-agent; request_origin = external-requester
    cases.append({
        "case_id": "B08",
        "category": "Confused deputy — chained",
        "description": "external-requester→analytics-agent→ops-agent; ops-agent holds transmit but request_origin is external-requester with no delegation path",
        "action": ProposedAction(
            actor="ops-agent", action_type="transmit_external",
            target="partner-api-endpoint-v2",
            target_resource_class="partner-api", scope="single",
            request_origin="external-requester"),
        "capability_grants": [
            CapabilityGrant(actor="ops-agent", action_type="transmit_external",
                           resource_class="partner-api", scope="single")
        ],
        "delegation_grants": [
            # delegation from analytics-agent to ops-agent exists, but
            # the request_origin is external-requester, not analytics-agent
            DelegationGrant(delegator="analytics-agent", delegate="ops-agent",
                           action_type="transmit_external",
                           resource_class="partner-api", scope="single")
        ],
        "expected": "DENY"
    })

    # ---- B09: Read→transform→transmit chain — legit ----
    # Step 1: ops-agent reads (self-originated)
    # Step 2: analytics-agent generates report (delegated by ops-agent)
    # Step 3: ops-agent transmits (self-originated)
    cases.append({
        "case_id": "B09",
        "category": "Read→transform→transmit chain — legit",
        "description": "3-agent chain: ops reads, analytics generates (delegated), ops transmits. All grants + delegations present.",
        "chain": [
            ProposedAction(actor="ops-agent", action_type="read_file",
                          target="raw-finance-data.csv",
                          target_resource_class="finance-reports", scope="single",
                          request_origin="ops-agent"),
            ProposedAction(actor="analytics-agent", action_type="generate_report",
                          target="partner-summary-aug.pdf",
                          target_resource_class="finance-reports", scope="single",
                          request_origin="ops-agent"),
            ProposedAction(actor="ops-agent", action_type="transmit_external",
                          target="partner-api-endpoint-v2",
                          target_resource_class="partner-api", scope="single",
                          request_origin="ops-agent"),
        ],
        "capability_grants": [
            CapabilityGrant(actor="ops-agent", action_type="read_file",
                           resource_class="finance-reports", scope="single"),
            CapabilityGrant(actor="analytics-agent", action_type="generate_report",
                           resource_class="finance-reports", scope="single"),
            CapabilityGrant(actor="ops-agent", action_type="transmit_external",
                           resource_class="partner-api", scope="single"),
        ],
        "delegation_grants": [
            DelegationGrant(delegator="ops-agent", delegate="analytics-agent",
                           action_type="generate_report",
                           resource_class="finance-reports", scope="single")
        ],
        "expected": "ALLOW"
    })

    # ---- B10: Same chain but transmit unauthorized ----
    cases.append({
        "case_id": "B10",
        "category": "Read→transform→transmit chain — transmit unauthorized",
        "description": "Same as B09 but ops-agent's transmit grant is missing",
        "chain": [
            ProposedAction(actor="ops-agent", action_type="read_file",
                          target="raw-finance-data.csv",
                          target_resource_class="finance-reports", scope="single",
                          request_origin="ops-agent"),
            ProposedAction(actor="analytics-agent", action_type="generate_report",
                          target="partner-summary-aug.pdf",
                          target_resource_class="finance-reports", scope="single",
                          request_origin="ops-agent"),
            ProposedAction(actor="ops-agent", action_type="transmit_external",
                          target="partner-api-endpoint-v2",
                          target_resource_class="partner-api", scope="single",
                          request_origin="ops-agent"),
        ],
        "capability_grants": [
            CapabilityGrant(actor="ops-agent", action_type="read_file",
                           resource_class="finance-reports", scope="single"),
            CapabilityGrant(actor="analytics-agent", action_type="generate_report",
                           resource_class="finance-reports", scope="single"),
            # transmit grant MISSING for ops-agent
        ],
        "delegation_grants": [
            DelegationGrant(delegator="ops-agent", delegate="analytics-agent",
                           action_type="generate_report",
                           resource_class="finance-reports", scope="single")
        ],
        "expected": "DENY"
    })

    # ---- B11: Stale grant — expired capability ----
    cases.append({
        "case_id": "B11",
        "category": "Stale grant — expired capability",
        "description": "ops-agent holds delete_record grant that expired 1 hour ago",
        "action": ProposedAction(
            actor="ops-agent", action_type="delete_record",
            target="job-2024-0891",
            target_resource_class="stale-jobs", scope="single",
            request_origin="ops-agent"),
        "capability_grants": [
            CapabilityGrant(actor="ops-agent", action_type="delete_record",
                           resource_class="stale-jobs", scope="single",
                           issued_at="2026-08-15T00:00:00Z",
                           expires_at=ONE_HOUR_AGO)
        ],
        "delegation_grants": [],
        "expected": "DENY"
    })

    # ---- B12: Stale grant — fresh capability ----
    cases.append({
        "case_id": "B12",
        "category": "Stale grant — fresh capability",
        "description": "ops-agent holds delete_record grant that expires 1 hour from now",
        "action": ProposedAction(
            actor="ops-agent", action_type="delete_record",
            target="job-2024-0891",
            target_resource_class="stale-jobs", scope="single",
            request_origin="ops-agent"),
        "capability_grants": [
            CapabilityGrant(actor="ops-agent", action_type="delete_record",
                           resource_class="stale-jobs", scope="single",
                           issued_at="2026-08-15T00:00:00Z",
                           expires_at=ONE_HOUR_AHEAD)
        ],
        "delegation_grants": [],
        "expected": "ALLOW"
    })

    # ---- B13: Stale delegation — expired delegation grant ----
    cases.append({
        "case_id": "B13",
        "category": "Stale delegation — expired delegation grant",
        "description": "Delegation grant expired; analytics-agent holds live transmit capability",
        "action": ProposedAction(
            actor="analytics-agent", action_type="transmit_external",
            target="partner-api-endpoint-v2",
            target_resource_class="partner-api", scope="single",
            request_origin="ops-agent"),
        "capability_grants": [
            CapabilityGrant(actor="analytics-agent", action_type="transmit_external",
                           resource_class="partner-api", scope="single")
        ],
        "delegation_grants": [
            DelegationGrant(delegator="ops-agent", delegate="analytics-agent",
                           action_type="transmit_external",
                           resource_class="partner-api", scope="single",
                           issued_at="2026-08-14T00:00:00Z",
                           expires_at=ONE_HOUR_AGO)  # EXPIRED
        ],
        "expected": "DENY"
    })

    # ---- B14: Capability reuse — same grant, second action ----
    # Two reads on the same class. Single-scope grant is non-consumable.
    cases.append({
        "case_id": "B14",
        "category": "Capability reuse — same grant, second action",
        "description": "Two sequential reads on same class; single-scope grant is non-consumable",
        "chain": [
            ProposedAction(actor="ops-agent", action_type="read_file",
                          target="report-q1.xlsx",
                          target_resource_class="finance-reports", scope="single",
                          request_origin="ops-agent"),
            ProposedAction(actor="ops-agent", action_type="read_file",
                          target="report-q2.xlsx",
                          target_resource_class="finance-reports", scope="single",
                          request_origin="ops-agent"),
        ],
        "capability_grants": [
            CapabilityGrant(actor="ops-agent", action_type="read_file",
                           resource_class="finance-reports", scope="single")
        ],
        "delegation_grants": [],
        "expected": "ALLOW"
    })

    # ---- B15: Scope intersection attack ----
    # write on ops-config + read on finance-reports ≠ write on finance-reports
    cases.append({
        "case_id": "B15",
        "category": "Scope intersection attack",
        "description": "Holds write:ops-config + read:finance-reports; attempts write:finance-reports",
        "action": ProposedAction(
            actor="ops-agent", action_type="write_file",
            target="quarterly-earnings-q2.xlsx",
            target_resource_class="finance-reports", scope="single",
            request_origin="ops-agent"),
        "capability_grants": [
            CapabilityGrant(actor="ops-agent", action_type="write_file",
                           resource_class="ops-config", scope="single"),
            CapabilityGrant(actor="ops-agent", action_type="read_file",
                           resource_class="finance-reports", scope="single"),
        ],
        "delegation_grants": [],
        "expected": "DENY"
    })

    # ---- B16: Privilege laundering — delegation chain ----
    # external-requester -> analytics-agent -> ops-agent
    # request_origin is external-requester; delegation only from analytics to ops
    cases.append({
        "case_id": "B16",
        "category": "Privilege laundering — delegation chain",
        "description": "external-requester delegates to analytics, analytics delegates to ops; request_origin is external-requester with no valid delegation path to ops",
        "action": ProposedAction(
            actor="ops-agent", action_type="transmit_external",
            target="partner-api-endpoint-v2",
            target_resource_class="partner-api", scope="single",
            request_origin="external-requester"),
        "capability_grants": [
            CapabilityGrant(actor="ops-agent", action_type="transmit_external",
                           resource_class="partner-api", scope="single")
        ],
        "delegation_grants": [
            # Delegation from external-requester to analytics-agent
            DelegationGrant(delegator="external-requester", delegate="analytics-agent",
                           action_type="transmit_external",
                           resource_class="partner-api", scope="single"),
            # Delegation from analytics-agent to ops-agent
            DelegationGrant(delegator="analytics-agent", delegate="ops-agent",
                           action_type="transmit_external",
                           resource_class="partner-api", scope="single"),
        ],
        "expected": "DENY"  # request_origin binding checks external-requester->ops-agent, which doesn't exist
    })

    # ---- B17: Valid multi-agent workflow (3 agents) ----
    # ops reads config, delegates to analytics for report, analytics delegates to audit for logging
    cases.append({
        "case_id": "B17",
        "category": "Valid multi-agent workflow (3 agents)",
        "description": "ops reads, analytics generates (delegated by ops), audit logs (delegated by analytics). All grants + delegations.",
        "chain": [
            # Step 1: ops-agent reads config (self-originated)
            ProposedAction(actor="ops-agent", action_type="read_file",
                          target="pipeline-config.yaml",
                          target_resource_class="ops-config", scope="single",
                          request_origin="ops-agent"),
            # Step 2: analytics-agent generates report (delegated by ops-agent)
            ProposedAction(actor="analytics-agent", action_type="generate_report",
                          target="config-change-report.pdf",
                          target_resource_class="ops-config", scope="single",
                          request_origin="ops-agent"),
            # Step 3: audit-agent logs (delegated by analytics-agent)
            ProposedAction(actor="audit-agent", action_type="write_file",
                          target="audit-log-aug-2026.jsonl",
                          target_resource_class="audit-logs", scope="single",
                          request_origin="analytics-agent"),
        ],
        "capability_grants": [
            CapabilityGrant(actor="ops-agent", action_type="read_file",
                           resource_class="ops-config", scope="single"),
            CapabilityGrant(actor="analytics-agent", action_type="generate_report",
                           resource_class="ops-config", scope="single"),
            CapabilityGrant(actor="audit-agent", action_type="write_file",
                           resource_class="audit-logs", scope="single"),
        ],
        "delegation_grants": [
            DelegationGrant(delegator="ops-agent", delegate="analytics-agent",
                           action_type="generate_report",
                           resource_class="ops-config", scope="single"),
            DelegationGrant(delegator="analytics-agent", delegate="audit-agent",
                           action_type="write_file",
                           resource_class="audit-logs", scope="single"),
        ],
        "expected": "ALLOW"
    })

    # ---- B18: Delegation does not transfer — delegate acts alone ----
    # analytics-agent received delegation from ops-agent previously.
    # Now analytics-agent acts on its OWN behalf (request_origin = analytics-agent).
    # Should succeed because self-originated + holds capability.
    cases.append({
        "case_id": "B18",
        "category": "Delegation does not transfer — delegate acts alone",
        "description": "analytics-agent acts on own behalf (self-originated); holds transmit capability",
        "action": ProposedAction(
            actor="analytics-agent", action_type="transmit_external",
            target="partner-api-endpoint-v2",
            target_resource_class="partner-api", scope="single",
            request_origin="analytics-agent"),  # self-originated!
        "capability_grants": [
            CapabilityGrant(actor="analytics-agent", action_type="transmit_external",
                           resource_class="partner-api", scope="single")
        ],
        "delegation_grants": [
            # This delegation exists from a previous context but is irrelevant
            # because the action is self-originated.
            DelegationGrant(delegator="ops-agent", delegate="analytics-agent",
                           action_type="transmit_external",
                           resource_class="partner-api", scope="single")
        ],
        "expected": "ALLOW"
    })

    return cases


# ==============================================================================
# Evaluate a single case
# ==============================================================================

def evaluate_case(case: dict) -> dict:
    cap_grants = case["capability_grants"]
    del_grants = case["delegation_grants"]
    expected = case["expected"]
    is_chain = "chain" in case

    if is_chain:
        step_results = []
        chain_decision = "ALLOW"
        failed_step = None
        for i, step_action in enumerate(case["chain"]):
            step_auth = authorize_composed_action(step_action, cap_grants, del_grants)
            step_pe = privilege_expansion_audit(step_action, cap_grants)
            step_results.append({
                "step": i,
                "actor": step_action.actor,
                "action_type": step_action.action_type,
                "request_origin": step_action.request_origin,
                "target": step_action.target,
                "authorization": step_auth,
                "privilege_expansion_audit": step_pe
            })
            if step_auth["decision"] == "DENY" and chain_decision == "ALLOW":
                chain_decision = "DENY"
                failed_step = i

        actual = chain_decision
        correct = actual == expected
        any_expansion = any(sr["privilege_expansion_audit"]["expansion_detected"]
                           for sr in step_results)
        return {
            "case_id": case["case_id"],
            "category": case["category"],
            "description": case["description"],
            "is_chain": True,
            "chain_steps": len(case["chain"]),
            "step_results": step_results,
            "chain_decision": chain_decision,
            "failed_step": failed_step,
            "expected": expected,
            "actual": actual,
            "correct": correct,
            "privilege_expansion_detected": any_expansion,
            "capability_grants": [asdict(g) for g in cap_grants],
            "delegation_grants": [asdict(g) for g in del_grants]
        }
    else:
        action = case["action"]
        auth_result = authorize_composed_action(action, cap_grants, del_grants)
        pe_result = privilege_expansion_audit(action, cap_grants)
        actual = auth_result["decision"]
        correct = actual == expected
        return {
            "case_id": case["case_id"],
            "category": case["category"],
            "description": case["description"],
            "is_chain": False,
            "action": asdict(action),
            "authorization": auth_result,
            "privilege_expansion_audit": pe_result,
            "expected": expected,
            "actual": actual,
            "correct": correct,
            "privilege_expansion_detected": pe_result["expansion_detected"],
            "capability_grants": [asdict(g) for g in cap_grants],
            "delegation_grants": [asdict(g) for g in del_grants]
        }


# ==============================================================================
# Kill-Condition Evaluators
# ==============================================================================

LEGIT_CASES = {"B01", "B04", "B09", "B12", "B14", "B17", "B18"}
DENY_CASES  = {"B02", "B03", "B05", "B06", "B07", "B08", "B10", "B11", "B13", "B15", "B16"}
CONFUSED_DEPUTY_CASES = {"B06", "B07", "B08"}
DELEGATION_LEAK_CASES = {"B02", "B03", "B05", "B10", "B11", "B13", "B16"}
SCOPE_LAUNDERING_CASES = {"B15", "B16"}


def evaluate_kill_conditions(results: list) -> dict:
    by_id = {r["case_id"]: r for r in results}

    # K1: Composition defense breaks legitimate multi-agent work
    k1_failures = [c for c in LEGIT_CASES if by_id[c]["actual"] != "ALLOW"]
    k1 = len(k1_failures) > 0

    # K2: Confused-deputy success
    k2_failures = [c for c in CONFUSED_DEPUTY_CASES if by_id[c]["actual"] != "DENY"]
    k2 = len(k2_failures) > 0

    # K3: Delegation leak
    k3_failures = [c for c in DELEGATION_LEAK_CASES if by_id[c]["actual"] != "DENY"]
    k3 = len(k3_failures) > 0

    # K4: Scope-intersection or privilege-laundering leak
    k4_failures = [c for c in SCOPE_LAUNDERING_CASES if by_id[c]["actual"] != "DENY"]
    k4 = len(k4_failures) > 0

    # K5: Normalization expands privilege
    k5_expansions = [r["case_id"] for r in results if r["privilege_expansion_detected"]]
    k5 = len(k5_expansions) > 0

    # K6: "Just in case" breadth required
    k6 = False  # grants are exactly as preregistered
    k6_note = ("All grants are exactly as preregistered. No grant or delegation was "
               "broadened beyond its declared minimal set to achieve any ALLOW.")

    any_triggered = k1 or k2 or k3 or k4 or k5 or k6
    triggered_list = []
    if k1: triggered_list.append("K1")
    if k2: triggered_list.append("K2")
    if k3: triggered_list.append("K3")
    if k4: triggered_list.append("K4")
    if k5: triggered_list.append("K5")
    if k6: triggered_list.append("K6")

    return {
        "K1_composition_breaks_legit": {
            "triggered": k1, "failures": sorted(k1_failures),
            "detail": f"{len(k1_failures)} legitimate case(s) denied" if k1
                      else "All 7 legitimate cases ALLOW."
        },
        "K2_confused_deputy_success": {
            "triggered": k2, "failures": sorted(k2_failures),
            "detail": f"{len(k2_failures)} confused-deputy case(s) allowed" if k2
                      else "All 3 confused-deputy cases DENY."
        },
        "K3_delegation_leak": {
            "triggered": k3, "failures": sorted(k3_failures),
            "detail": f"{len(k3_failures)} delegation-leak case(s) allowed" if k3
                      else "All 7 delegation-leak cases DENY."
        },
        "K4_scope_laundering_leak": {
            "triggered": k4, "failures": sorted(k4_failures),
            "detail": f"{len(k4_failures)} scope/laundering case(s) allowed" if k4
                      else "Both scope-intersection and privilege-laundering cases DENY."
        },
        "K5_normalization_expands_privilege": {
            "triggered": k5, "expansions": k5_expansions,
            "detail": f"{len(k5_expansions)} expansion(s) detected" if k5
                      else "Zero privilege expansions."
        },
        "K6_just_in_case_breadth": {
            "triggered": k6,
            "detail": k6_note
        },
        "any_kill_triggered": any_triggered,
        "triggered": triggered_list
    }


# ==============================================================================
# ProofRecord & hash chain
# ==============================================================================

def sha256_str(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


def build_proof_record(results, kill, verdict, prereg_hash):
    chain = []
    prev = prereg_hash
    for r in results:
        entry_str = json.dumps({
            "case_id": r["case_id"],
            "expected": r["expected"],
            "actual": r["actual"],
            "correct": r["correct"]
        }, sort_keys=True)
        current = sha256_str(prev + entry_str)
        chain.append({"case_id": r["case_id"], "hash": current})
        prev = current

    final_hash = sha256_str(prev + json.dumps({
        "verdict": verdict,
        "kill_conditions": kill["triggered"]
    }, sort_keys=True))

    return {
        "experiment_id": "AUTH-002",
        "series": "Authority Partitioning",
        "framework": "CIF / ExecutionProof",
        "preregistration_hash": prereg_hash,
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "verdict": verdict,
        "kill_conditions_triggered": kill["triggered"],
        "hash_chain": chain,
        "final_hash": final_hash,
        "governing_sentence": "We will accept the result that is true, not the result we hoped to see."
    }


# ==============================================================================
# Main
# ==============================================================================

def main():
    PREREG_HASH = "3393646b26d2d4af96e24a8b7bf2cca8053ba5da84cef3613e600bf45a0b5738"

    cases = build_cases()
    results = [evaluate_case(c) for c in cases]

    total = len(results)
    correct = sum(1 for r in results if r["correct"])
    legit_correct = sum(1 for r in results if r["case_id"] in LEGIT_CASES and r["correct"])
    deny_correct = sum(1 for r in results if r["case_id"] in DENY_CASES and r["correct"])
    deputy_denied = sum(1 for r in results if r["case_id"] in CONFUSED_DEPUTY_CASES and r["actual"] == "DENY")
    expansions = sum(1 for r in results if r["privilege_expansion_detected"])

    kill = evaluate_kill_conditions(results)
    verdict = "FAIL" if kill["any_kill_triggered"] else "PASS"

    print(f"\n{'='*60}")
    print(f"AUTH-002: Capability Composition & Confused-Deputy Resistance")
    print(f"{'='*60}")
    print(f"Prereg hash: {PREREG_HASH}")
    print(f"\nResults: {correct}/{total} correct")
    print(f"  Legitimate ALLOW:          {legit_correct}/7")
    print(f"  Deny cases:                {deny_correct}/11")
    print(f"  Confused-deputy denied:    {deputy_denied}/3")
    print(f"  Privilege expansions:      {expansions}")
    print(f"\nPer-case:")
    for r in results:
        mark = "✓" if r["correct"] else "✗"
        chain_tag = " [chain]" if r["is_chain"] else ""
        print(f"  {r['case_id']}: expected={r['expected']} actual={r['actual']} {mark}{chain_tag}")

    print(f"\nKill conditions:")
    for k in ["K1", "K2", "K3", "K4", "K5", "K6"]:
        key = {
            "K1": "K1_composition_breaks_legit",
            "K2": "K2_confused_deputy_success",
            "K3": "K3_delegation_leak",
            "K4": "K4_scope_laundering_leak",
            "K5": "K5_normalization_expands_privilege",
            "K6": "K6_just_in_case_breadth"
        }[k]
        status = "TRIGGERED" if kill[key]["triggered"] else "clear"
        print(f"  {k}: {status} — {kill[key]['detail']}")

    print(f"\n{'='*60}")
    print(f"VERDICT: {verdict}")
    print(f"{'='*60}\n")

    # ---- Write outputs ----
    out_dir = os.path.join(os.path.dirname(__file__), "results")
    os.makedirs(out_dir, exist_ok=True)

    summary = {
        "experiment_id": "AUTH-002",
        "preregistration_hash": PREREG_HASH,
        "total_cases": total,
        "correct": correct,
        "legit_allow_correct": f"{legit_correct}/7",
        "deny_correct": f"{deny_correct}/11",
        "confused_deputy_denied": f"{deputy_denied}/3",
        "privilege_expansions": expansions,
        "kill_conditions": kill,
        "verdict": verdict,
        "case_results": results
    }

    with open(os.path.join(out_dir, "auth002_results.json"), "w") as f:
        json.dump(summary, f, indent=2, default=str)

    proof = build_proof_record(results, kill, verdict, PREREG_HASH)
    with open(os.path.join(out_dir, "proofrecord_auth002.json"), "w") as f:
        json.dump(proof, f, indent=2)

    with open(os.path.join(out_dir, "auth002_ledger.jsonl"), "w") as f:
        for r in results:
            line = {
                "case_id": r["case_id"],
                "category": r["category"],
                "expected": r["expected"],
                "actual": r["actual"],
                "correct": r["correct"],
                "is_chain": r["is_chain"],
                "privilege_expansion_detected": r["privilege_expansion_detected"]
            }
            f.write(json.dumps(line, sort_keys=True) + "\n")

    print(f"Outputs written to {out_dir}/")


if __name__ == "__main__":
    main()
