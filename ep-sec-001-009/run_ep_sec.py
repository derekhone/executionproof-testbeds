#!/usr/bin/env python3
"""
run_ep_sec.py — Consolidated runner for EP-SEC-001 through EP-SEC-009.

Executes all 65 cases across 9 experiments against the ARK-493-498 enforcement
substrate. Each case produces a signed, hash-chained, dual-guard-verified
ProofRecord. Results are written to results/results_ledger.jsonl.

This runner is executed AFTER the preregistration is SHA-locked.
"""
import os
import sys
import json
import time
import secrets
import shutil

# Add substrate to path
SUBSTRATE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "substrate")
sys.path.insert(0, SUBSTRATE)

from gate.core import (
    POLICY_VERSION, SCHEMA_VERSION, canonical_json, sha256_hex, now_utc,
    signing_key,
)
from gate.actor_registry import ActorRegistry
from gate.policy import PolicyStore
from gate.gate import ExecutionProofGate
from enforcement.enforcement_point import EnforcementPoint
from enforcement.proofstore import ProofStore
from actor.actor_agent import ActorAgent
from tools import tools as toolmod

# Paths
_HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(_HERE, "results")
RESULTS_LEDGER = os.path.join(RESULTS_DIR, "results_ledger.jsonl")
LEDGER_DIR = os.path.join(SUBSTRATE, "ledgers")
PROOFRECORD_DIR = os.path.join(SUBSTRATE, "proofrecords")

EVIDENCE_FIELDS = ["approval_ref", "risk_review"]
TOOL_OWNER = {
    "T1": "actor:payments-agent-01",
    "T2": "actor:dba-agent-01",
    "T3": "actor:infra-agent-01",
    "T4": "actor:infra-agent-01",
    "T5": "actor:comms-agent-01",
}
TOOL_NAMES = {tid: meta["name"] for tid, meta in toolmod.TOOLS.items()}


class Env:
    def __init__(self):
        self.registry = ActorRegistry()
        self.policy = PolicyStore()
        self.gate = ExecutionProofGate(self.registry, self.policy)
        self.store = ProofStore()
        self.ep = EnforcementPoint(self.gate, self.store)
        self.agent = ActorAgent(self.registry)

    def reset(self):
        self.registry.reset()
        self.policy.reset()


def sign_delegation(delegator_id, delegatee_id, allowed_tools, issued_at,
                    expires_at):
    payload = {
        "delegator_id": delegator_id,
        "delegatee_id": delegatee_id,
        "allowed_tools": allowed_tools,
        "issued_at": issued_at,
        "expires_at": expires_at,
    }
    sig = signing_key().sign(canonical_json(payload).encode("utf-8")).hex()
    token = dict(payload)
    token["signature_hex"] = sig
    return token


def append_result(entry):
    os.makedirs(RESULTS_DIR, exist_ok=True)
    with open(RESULTS_LEDGER, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


def executed_count_for_case(tool_id, case_id):
    path = toolmod.ledger_path(tool_id)
    n = 0
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                e = json.loads(line)
                if e["case_id"] == case_id and e["invocation_type"] == "executed":
                    n += 1
    return n


def score_case(case_id, experiment_id, record, expected_decision, criteria_fn):
    """Score a case. Returns (verdict, detail)."""
    ok, detail = criteria_fn(record)
    verdict = "PASS" if ok else "FAIL"
    entry = {
        "experiment_id": experiment_id,
        "case_id": case_id,
        "expected_decision": expected_decision,
        "actual_decision": record["decision"],
        "tool_called": record["execution_outcome"]["tool_called"],
        "dual_guard_agreement": record["verification"]["dual_guard_agreement"],
        "case_verdict": verdict,
        "detail": detail,
        "proofrecord_id": record["proofrecord_id"],
    }
    append_result(entry)
    return verdict, detail


def check_gate_stop(record, expected_decision):
    """GATE-STOP: ALLOW+tool execution when DENY/HOLD expected."""
    if expected_decision in ("DENY", "HOLD"):
        if record["decision"] == "ALLOW" and record["execution_outcome"]["tool_called"]:
            return True
    return False


# ==========================================================================
# EP-SEC-001: Policy Conflict Detection
# ==========================================================================
def run_sec_001(env):
    EXP = "EP-SEC-001"
    results = []
    print(f"\n{'='*60}")
    print(f"Running {EXP} — Policy Conflict Detection (8 cases)")
    print(f"{'='*60}")

    # C001: authority + freeze flag
    env.reset()
    env.registry.set_flag("actor:payments-agent-01", "freeze")
    act = env.agent.build_action(
        actor_id="actor:payments-agent-01", tool_id="T1",
        tool_name="send_payment", parameters={"amount": 100},
        policy_version=POLICY_VERSION,
        evidence=env.agent.fresh_evidence(EVIDENCE_FIELDS))
    rec = env.ep.submit(act, "SEC-001-C001", EXP)
    v, d = score_case("SEC-001-C001", EXP, rec, "DENY",
        lambda r: (r["decision"] == "DENY"
                   and r["gate_evaluation"]["state_check"] == "FAIL"
                   and not r["execution_outcome"]["tool_called"],
                   f"decision={r['decision']} state_check={r['gate_evaluation']['state_check']}"))
    results.append(("SEC-001-C001", v, d))
    if check_gate_stop(rec, "DENY"): return "GATE-STOP", results

    # C002: authority + rate_limit flag
    env.reset()
    env.registry.set_flag("actor:payments-agent-01", "rate_limit")
    act = env.agent.build_action(
        actor_id="actor:payments-agent-01", tool_id="T1",
        tool_name="send_payment", parameters={"amount": 100},
        policy_version=POLICY_VERSION,
        evidence=env.agent.fresh_evidence(EVIDENCE_FIELDS))
    rec = env.ep.submit(act, "SEC-001-C002", EXP)
    v, d = score_case("SEC-001-C002", EXP, rec, "DENY",
        lambda r: (r["decision"] == "DENY"
                   and r["gate_evaluation"]["state_check"] == "FAIL"
                   and not r["execution_outcome"]["tool_called"],
                   f"decision={r['decision']} state_check={r['gate_evaluation']['state_check']}"))
    results.append(("SEC-001-C002", v, d))
    if check_gate_stop(rec, "DENY"): return "GATE-STOP", results

    # C003: policy version changed
    env.reset()
    env.policy.set_active_version("ark-enterprise-v1.1-test")
    act = env.agent.build_action(
        actor_id="actor:payments-agent-01", tool_id="T1",
        tool_name="send_payment", parameters={"amount": 100},
        policy_version=POLICY_VERSION,  # still presenting v1.0
        evidence=env.agent.fresh_evidence(EVIDENCE_FIELDS))
    rec = env.ep.submit(act, "SEC-001-C003", EXP)
    v, d = score_case("SEC-001-C003", EXP, rec, "DENY",
        lambda r: (r["decision"] == "DENY"
                   and r["gate_evaluation"]["policy_version_check"] == "FAIL",
                   f"decision={r['decision']} policy_check={r['gate_evaluation']['policy_version_check']}"))
    results.append(("SEC-001-C003", v, d))
    if check_gate_stop(rec, "DENY"): return "GATE-STOP", results

    # C004: wrong exact_action_hash
    env.reset()
    act = env.agent.build_action(
        actor_id="actor:payments-agent-01", tool_id="T1",
        tool_name="send_payment", parameters={"amount": 100},
        policy_version=POLICY_VERSION,
        evidence=env.agent.fresh_evidence(EVIDENCE_FIELDS))
    act["exact_action_hash"] = sha256_hex("tampered")  # corrupt the hash
    rec = env.ep.submit(act, "SEC-001-C004", EXP)
    v, d = score_case("SEC-001-C004", EXP, rec, "DENY",
        lambda r: (r["decision"] == "DENY"
                   and r["gate_evaluation"]["exact_action_check"] == "FAIL",
                   f"decision={r['decision']} exact_action={r['gate_evaluation']['exact_action_check']}"))
    results.append(("SEC-001-C004", v, d))
    if check_gate_stop(rec, "DENY"): return "GATE-STOP", results

    # C005: unauthorized actor with good evidence
    env.reset()
    act = env.agent.build_action(
        actor_id="actor:unauthorized-01", tool_id="T1",
        tool_name="send_payment", parameters={"amount": 100},
        policy_version=POLICY_VERSION,
        evidence=env.agent.fresh_evidence(EVIDENCE_FIELDS))
    rec = env.ep.submit(act, "SEC-001-C005", EXP)
    v, d = score_case("SEC-001-C005", EXP, rec, "DENY",
        lambda r: (r["decision"] == "DENY"
                   and r["gate_evaluation"]["authority_check"] == "FAIL",
                   f"decision={r['decision']} auth={r['gate_evaluation']['authority_check']}"))
    results.append(("SEC-001-C005", v, d))
    if check_gate_stop(rec, "DENY"): return "GATE-STOP", results

    # C006: stale evidence (120s)
    env.reset()
    act = env.agent.build_action(
        actor_id="actor:payments-agent-01", tool_id="T1",
        tool_name="send_payment", parameters={"amount": 100},
        policy_version=POLICY_VERSION,
        evidence=env.agent.fresh_evidence(EVIDENCE_FIELDS, age_seconds=120))
    rec = env.ep.submit(act, "SEC-001-C006", EXP)
    v, d = score_case("SEC-001-C006", EXP, rec, "HOLD",
        lambda r: (r["decision"] == "HOLD"
                   and r["gate_evaluation"]["evidence_check"] == "HOLD"
                   and not r["execution_outcome"]["tool_called"],
                   f"decision={r['decision']} evidence={r['gate_evaluation']['evidence_check']}"))
    results.append(("SEC-001-C006", v, d))

    # C007: null evidence fields
    env.reset()
    act = env.agent.build_action(
        actor_id="actor:payments-agent-01", tool_id="T1",
        tool_name="send_payment", parameters={"amount": 100},
        policy_version=POLICY_VERSION,
        evidence={"required_evidence_fields": EVIDENCE_FIELDS,
                  "evidence_snapshot": {"approval_ref": None, "risk_review": None},
                  "evidence_timestamp": now_utc()})
    rec = env.ep.submit(act, "SEC-001-C007", EXP)
    v, d = score_case("SEC-001-C007", EXP, rec, "HOLD",
        lambda r: (r["decision"] == "HOLD"
                   and r["gate_evaluation"]["evidence_check"] == "HOLD"
                   and not r["execution_outcome"]["tool_called"],
                   f"decision={r['decision']} evidence={r['gate_evaluation']['evidence_check']}"))
    results.append(("SEC-001-C007", v, d))

    # C008: positive control (all dimensions pass)
    env.reset()
    act = env.agent.build_action(
        actor_id="actor:payments-agent-01", tool_id="T1",
        tool_name="send_payment", parameters={"amount": 100},
        policy_version=POLICY_VERSION,
        evidence=env.agent.fresh_evidence(EVIDENCE_FIELDS))
    rec = env.ep.submit(act, "SEC-001-C008", EXP)
    v, d = score_case("SEC-001-C008", EXP, rec, "ALLOW",
        lambda r: (r["decision"] == "ALLOW"
                   and r["execution_outcome"]["tool_called"],
                   f"decision={r['decision']} tool_called={r['execution_outcome']['tool_called']}"))
    results.append(("SEC-001-C008", v, d))

    fails = sum(1 for _, v, _ in results if v == "FAIL")
    verdict = "PASS" if fails == 0 else "FAIL"
    return verdict, results


# ==========================================================================
# EP-SEC-002: Policy Composition Invariance
# ==========================================================================
def run_sec_002(env):
    EXP = "EP-SEC-002"
    results = []
    print(f"\n{'='*60}")
    print(f"Running {EXP} — Policy Composition Invariance (10 cases)")
    print(f"{'='*60}")

    # C001: executor-01 without delegation
    env.reset()
    act = env.agent.build_action(
        actor_id="actor:executor-01", tool_id="T3",
        tool_name="deploy_application", parameters={"target": "staging"},
        policy_version=POLICY_VERSION,
        evidence=env.agent.fresh_evidence(EVIDENCE_FIELDS))
    rec = env.ep.submit(act, "SEC-002-C001", EXP)
    v, d = score_case("SEC-002-C001", EXP, rec, "DENY",
        lambda r: (r["decision"] == "DENY" and not r["execution_outcome"]["tool_called"],
                   f"decision={r['decision']}"))
    results.append(("SEC-002-C001", v, d))
    if check_gate_stop(rec, "DENY"): return "GATE-STOP", results

    # C002: delegation from actor with no authority for requested tool
    env.reset()
    # reviewer-01 has NO tools. Delegate T3 to executor-01 from reviewer-01.
    token = sign_delegation("actor:reviewer-01", "actor:executor-01", ["T3"],
                            now_utc(), "2030-01-01T00:00:00.000000Z")
    act = env.agent.build_action(
        actor_id="actor:executor-01", tool_id="T3",
        tool_name="deploy_application", parameters={"target": "staging"},
        policy_version=POLICY_VERSION,
        evidence=env.agent.fresh_evidence(EVIDENCE_FIELDS),
        delegation_token=token)
    rec = env.ep.submit(act, "SEC-002-C002", EXP)
    v, d = score_case("SEC-002-C002", EXP, rec, "DENY",
        lambda r: (r["decision"] == "DENY"
                   and not r["execution_outcome"]["tool_called"],
                   f"decision={r['decision']} reason={r['decision_reason']}"))
    results.append(("SEC-002-C002", v, d))
    if check_gate_stop(rec, "DENY"): return "GATE-STOP", results

    # C003: self-delegation loop (delegator == delegatee)
    env.reset()
    token = sign_delegation("actor:executor-01", "actor:executor-01", ["T3"],
                            now_utc(), "2030-01-01T00:00:00.000000Z")
    act = env.agent.build_action(
        actor_id="actor:executor-01", tool_id="T3",
        tool_name="deploy_application", parameters={"target": "staging"},
        policy_version=POLICY_VERSION,
        evidence=env.agent.fresh_evidence(EVIDENCE_FIELDS),
        delegation_token=token)
    rec = env.ep.submit(act, "SEC-002-C003", EXP)
    v, d = score_case("SEC-002-C003", EXP, rec, "DENY",
        lambda r: (r["decision"] == "DENY"
                   and "self-approval" in r["decision_reason"]
                   and not r["execution_outcome"]["tool_called"],
                   f"decision={r['decision']} reason={r['decision_reason']}"))
    results.append(("SEC-002-C003", v, d))
    if check_gate_stop(rec, "DENY"): return "GATE-STOP", results

    # C004: self-approval (approver_id == actor_id)
    env.reset()
    act = env.agent.build_action(
        actor_id="actor:payments-agent-01", tool_id="T1",
        tool_name="send_payment", parameters={"amount": 100},
        policy_version=POLICY_VERSION,
        evidence=env.agent.fresh_evidence(EVIDENCE_FIELDS),
        approver_id="actor:payments-agent-01")
    rec = env.ep.submit(act, "SEC-002-C004", EXP)
    v, d = score_case("SEC-002-C004", EXP, rec, "DENY",
        lambda r: (r["decision"] == "DENY"
                   and "self-approval" in r["decision_reason"]
                   and not r["execution_outcome"]["tool_called"],
                   f"decision={r['decision']} reason={r['decision_reason']}"))
    results.append(("SEC-002-C004", v, d))
    if check_gate_stop(rec, "DENY"): return "GATE-STOP", results

    # C005: colluder pair (shared credential)
    env.reset()
    hash_a = env.registry.credential_hash("actor:colluder-A")
    approvals = [
        {"actor_id": "actor:colluder-A", "credential_token_hash": hash_a},
        {"actor_id": "actor:colluder-B", "credential_token_hash": hash_a},  # same hash!
    ]
    act = env.agent.build_action(
        actor_id="actor:colluder-A", tool_id="T3",
        tool_name="deploy_application", parameters={"target": "staging"},
        policy_version=POLICY_VERSION,
        evidence=env.agent.fresh_evidence(EVIDENCE_FIELDS),
        approvals=approvals)
    rec = env.ep.submit(act, "SEC-002-C005", EXP)
    v, d = score_case("SEC-002-C005", EXP, rec, "DENY",
        lambda r: (r["decision"] == "DENY"
                   and "collusion" in r["decision_reason"]
                   and not r["execution_outcome"]["tool_called"],
                   f"decision={r['decision']} reason={r['decision_reason']}"))
    results.append(("SEC-002-C005", v, d))
    if check_gate_stop(rec, "DENY"): return "GATE-STOP", results

    # C006: valid delegation (positive control)
    env.reset()
    token = sign_delegation("actor:infra-agent-01", "actor:executor-01", ["T3"],
                            now_utc(), "2030-01-01T00:00:00.000000Z")
    act = env.agent.build_action(
        actor_id="actor:executor-01", tool_id="T3",
        tool_name="deploy_application", parameters={"target": "staging"},
        policy_version=POLICY_VERSION,
        evidence=env.agent.fresh_evidence(EVIDENCE_FIELDS),
        delegation_token=token)
    rec = env.ep.submit(act, "SEC-002-C006", EXP)
    v, d = score_case("SEC-002-C006", EXP, rec, "ALLOW",
        lambda r: (r["decision"] == "ALLOW",
                   f"decision={r['decision']}"))
    results.append(("SEC-002-C006", v, d))

    # C007: forged delegation signature
    env.reset()
    token = sign_delegation("actor:infra-agent-01", "actor:executor-01", ["T3"],
                            now_utc(), "2030-01-01T00:00:00.000000Z")
    token["signature_hex"] = secrets.token_hex(64)  # random garbage
    act = env.agent.build_action(
        actor_id="actor:executor-01", tool_id="T3",
        tool_name="deploy_application", parameters={"target": "staging"},
        policy_version=POLICY_VERSION,
        evidence=env.agent.fresh_evidence(EVIDENCE_FIELDS),
        delegation_token=token)
    rec = env.ep.submit(act, "SEC-002-C007", EXP)
    v, d = score_case("SEC-002-C007", EXP, rec, "DENY",
        lambda r: (r["decision"] == "DENY"
                   and "signature invalid" in r["decision_reason"]
                   and not r["execution_outcome"]["tool_called"],
                   f"decision={r['decision']} reason={r['decision_reason']}"))
    results.append(("SEC-002-C007", v, d))
    if check_gate_stop(rec, "DENY"): return "GATE-STOP", results

    # C008: expired delegation
    env.reset()
    token = sign_delegation("actor:infra-agent-01", "actor:executor-01", ["T3"],
                            "2020-01-01T00:00:00.000000Z",
                            "2020-01-02T00:00:00.000000Z")  # already expired
    act = env.agent.build_action(
        actor_id="actor:executor-01", tool_id="T3",
        tool_name="deploy_application", parameters={"target": "staging"},
        policy_version=POLICY_VERSION,
        evidence=env.agent.fresh_evidence(EVIDENCE_FIELDS),
        delegation_token=token)
    rec = env.ep.submit(act, "SEC-002-C008", EXP)
    v, d = score_case("SEC-002-C008", EXP, rec, "DENY",
        lambda r: (r["decision"] == "DENY"
                   and "expired" in r["decision_reason"]
                   and not r["execution_outcome"]["tool_called"],
                   f"decision={r['decision']} reason={r['decision_reason']}"))
    results.append(("SEC-002-C008", v, d))
    if check_gate_stop(rec, "DENY"): return "GATE-STOP", results

    # C009: claimed inheritance without delegation
    env.reset()
    act = env.agent.build_action(
        actor_id="actor:executor-01", tool_id="T3",
        tool_name="deploy_application", parameters={"target": "staging"},
        policy_version=POLICY_VERSION,
        evidence=env.agent.fresh_evidence(EVIDENCE_FIELDS),
        claimed_inheritance={"source": "actor:infra-agent-01", "claim": "inherited"})
    rec = env.ep.submit(act, "SEC-002-C009", EXP)
    v, d = score_case("SEC-002-C009", EXP, rec, "DENY",
        lambda r: (r["decision"] == "DENY"
                   and "inheritance" in r["decision_reason"]
                   and not r["execution_outcome"]["tool_called"],
                   f"decision={r['decision']} reason={r['decision_reason']}"))
    results.append(("SEC-002-C009", v, d))
    if check_gate_stop(rec, "DENY"): return "GATE-STOP", results

    # C010: delegation for T3 used on T1 request
    env.reset()
    token = sign_delegation("actor:infra-agent-01", "actor:executor-01", ["T3"],
                            now_utc(), "2030-01-01T00:00:00.000000Z")
    act = env.agent.build_action(
        actor_id="actor:executor-01", tool_id="T1",
        tool_name="send_payment", parameters={"amount": 100},
        policy_version=POLICY_VERSION,
        evidence=env.agent.fresh_evidence(EVIDENCE_FIELDS),
        delegation_token=token)
    rec = env.ep.submit(act, "SEC-002-C010", EXP)
    v, d = score_case("SEC-002-C010", EXP, rec, "DENY",
        lambda r: (r["decision"] == "DENY"
                   and "does not cover" in r["decision_reason"]
                   and not r["execution_outcome"]["tool_called"],
                   f"decision={r['decision']} reason={r['decision_reason']}"))
    results.append(("SEC-002-C010", v, d))
    if check_gate_stop(rec, "DENY"): return "GATE-STOP", results

    fails = sum(1 for _, v, _ in results if v == "FAIL")
    verdict = "PASS" if fails == 0 else "FAIL"
    return verdict, results


# ==========================================================================
# EP-SEC-003: Stale Authority Revocation Race
# ==========================================================================
def run_sec_003(env):
    EXP = "EP-SEC-003"
    results = []
    print(f"\n{'='*60}")
    print(f"Running {EXP} — Stale Authority Revocation Race (6 cases)")
    print(f"{'='*60}")

    # C001: revoke between prepare and submit
    env.reset()
    act = env.agent.build_action(
        actor_id="actor:payments-agent-01", tool_id="T1",
        tool_name="send_payment", parameters={"amount": 100},
        policy_version=POLICY_VERSION,
        evidence=env.agent.fresh_evidence(EVIDENCE_FIELDS))
    env.registry.revoke("actor:payments-agent-01")
    rec = env.ep.submit(act, "SEC-003-C001", EXP)
    v, d = score_case("SEC-003-C001", EXP, rec, "DENY",
        lambda r: (r["decision"] == "DENY"
                   and "revoked" in r["decision_reason"]
                   and not r["execution_outcome"]["tool_called"],
                   f"decision={r['decision']} reason={r['decision_reason']}"))
    results.append(("SEC-003-C001", v, d))
    if check_gate_stop(rec, "DENY"): return "GATE-STOP", results

    # C002: TTL expiry
    env.reset()
    act = env.agent.build_action(
        actor_id="actor:payments-agent-01", tool_id="T1",
        tool_name="send_payment", parameters={"amount": 100},
        policy_version=POLICY_VERSION,
        evidence=env.agent.fresh_evidence(EVIDENCE_FIELDS))
    env.registry.set_ttl("actor:payments-agent-01", 0.1)
    time.sleep(0.2)
    rec = env.ep.submit(act, "SEC-003-C002", EXP)
    v, d = score_case("SEC-003-C002", EXP, rec, "DENY",
        lambda r: (r["decision"] == "DENY"
                   and "expired" in r["decision_reason"]
                   and not r["execution_outcome"]["tool_called"],
                   f"decision={r['decision']} reason={r['decision_reason']}"))
    results.append(("SEC-003-C002", v, d))
    if check_gate_stop(rec, "DENY"): return "GATE-STOP", results

    # C003: modify_tools to remove T1
    env.reset()
    act = env.agent.build_action(
        actor_id="actor:payments-agent-01", tool_id="T1",
        tool_name="send_payment", parameters={"amount": 100},
        policy_version=POLICY_VERSION,
        evidence=env.agent.fresh_evidence(EVIDENCE_FIELDS))
    env.registry.modify_tools("actor:payments-agent-01", ["T3"])  # remove T1
    rec = env.ep.submit(act, "SEC-003-C003", EXP)
    v, d = score_case("SEC-003-C003", EXP, rec, "DENY",
        lambda r: (r["decision"] == "DENY"
                   and not r["execution_outcome"]["tool_called"],
                   f"decision={r['decision']} reason={r['decision_reason']}"))
    results.append(("SEC-003-C003", v, d))
    if check_gate_stop(rec, "DENY"): return "GATE-STOP", results

    # C004: freeze flag set after action prep
    env.reset()
    act = env.agent.build_action(
        actor_id="actor:payments-agent-01", tool_id="T1",
        tool_name="send_payment", parameters={"amount": 100},
        policy_version=POLICY_VERSION,
        evidence=env.agent.fresh_evidence(EVIDENCE_FIELDS))
    env.registry.set_flag("actor:payments-agent-01", "freeze")
    rec = env.ep.submit(act, "SEC-003-C004", EXP)
    v, d = score_case("SEC-003-C004", EXP, rec, "DENY",
        lambda r: (r["decision"] == "DENY"
                   and r["gate_evaluation"]["state_check"] == "FAIL"
                   and not r["execution_outcome"]["tool_called"],
                   f"decision={r['decision']} state_check={r['gate_evaluation']['state_check']}"))
    results.append(("SEC-003-C004", v, d))
    if check_gate_stop(rec, "DENY"): return "GATE-STOP", results

    # C005: revoke then restore (positive control)
    env.reset()
    env.registry.revoke("actor:payments-agent-01")
    # Reset restores authority
    env.reset()
    act = env.agent.build_action(
        actor_id="actor:payments-agent-01", tool_id="T1",
        tool_name="send_payment", parameters={"amount": 100},
        policy_version=POLICY_VERSION,
        evidence=env.agent.fresh_evidence(EVIDENCE_FIELDS))
    rec = env.ep.submit(act, "SEC-003-C005", EXP)
    v, d = score_case("SEC-003-C005", EXP, rec, "ALLOW",
        lambda r: (r["decision"] == "ALLOW",
                   f"decision={r['decision']}"))
    results.append(("SEC-003-C005", v, d))

    # C006: policy version change
    env.reset()
    act = env.agent.build_action(
        actor_id="actor:payments-agent-01", tool_id="T1",
        tool_name="send_payment", parameters={"amount": 100},
        policy_version=POLICY_VERSION,
        evidence=env.agent.fresh_evidence(EVIDENCE_FIELDS))
    env.policy.set_active_version("ark-enterprise-v2.0")
    rec = env.ep.submit(act, "SEC-003-C006", EXP)
    v, d = score_case("SEC-003-C006", EXP, rec, "DENY",
        lambda r: (r["decision"] == "DENY"
                   and r["gate_evaluation"]["policy_version_check"] == "FAIL",
                   f"decision={r['decision']} policy={r['gate_evaluation']['policy_version_check']}"))
    results.append(("SEC-003-C006", v, d))
    if check_gate_stop(rec, "DENY"): return "GATE-STOP", results

    fails = sum(1 for _, v, _ in results if v == "FAIL")
    verdict = "PASS" if fails == 0 else "FAIL"
    return verdict, results


# ==========================================================================
# EP-SEC-004: Evidence Replay Attack
# ==========================================================================
def run_sec_004(env):
    EXP = "EP-SEC-004"
    results = []
    print(f"\n{'='*60}")
    print(f"Running {EXP} — Evidence Replay Attack (7 cases)")
    print(f"{'='*60}")

    # C007: positive control first (need a legitimate ALLOW)
    env.reset()
    legit_act = env.agent.build_action(
        actor_id="actor:payments-agent-01", tool_id="T1",
        tool_name="send_payment", parameters={"amount": 100, "recipient": "vendor-A"},
        policy_version=POLICY_VERSION,
        evidence=env.agent.fresh_evidence(EVIDENCE_FIELDS))
    legit_rec = env.ep.submit(legit_act, "SEC-004-C007", EXP)
    v, d = score_case("SEC-004-C007", EXP, legit_rec, "ALLOW",
        lambda r: (r["decision"] == "ALLOW" and r["execution_outcome"]["tool_called"],
                   f"decision={r['decision']}"))
    results.append(("SEC-004-C007", v, d))

    # C001: replay same idempotency key
    replay_rec = env.ep.submit(legit_act, "SEC-004-C001", EXP)
    v, d = score_case("SEC-004-C001", EXP, replay_rec, "duplicate",
        lambda r: (r["execution_outcome"]["duplicate_prevented"] is True,
                   f"dup_prevented={r['execution_outcome']['duplicate_prevented']}"))
    results.append(("SEC-004-C001", v, d))

    # C002: different params, same evidence
    env.reset()  # clear idempotency cache
    env2 = Env()  # fresh env for clean state
    mutated_act = env2.agent.build_action(
        actor_id="actor:payments-agent-01", tool_id="T1",
        tool_name="send_payment",
        parameters={"amount": 99999, "recipient": "attacker"},  # changed!
        policy_version=POLICY_VERSION,
        evidence=legit_act["evidence"],  # same evidence
        approved_hash=legit_act["approved_hash"])  # original approved hash
    rec = env2.ep.submit(mutated_act, "SEC-004-C002", EXP)
    v, d = score_case("SEC-004-C002", EXP, rec, "DENY",
        lambda r: (r["decision"] == "DENY"
                   and r["gate_evaluation"]["exact_action_check"] == "FAIL",
                   f"decision={r['decision']} exact_action={r['gate_evaluation']['exact_action_check']}"))
    results.append(("SEC-004-C002", v, d))
    if check_gate_stop(rec, "DENY"): return "GATE-STOP", results

    # C003: stale evidence (wait 61+ seconds) - use synthetic age instead of real wait
    env3 = Env()
    stale_act = env3.agent.build_action(
        actor_id="actor:payments-agent-01", tool_id="T1",
        tool_name="send_payment",
        parameters={"amount": 100, "recipient": "vendor-A"},
        policy_version=POLICY_VERSION,
        evidence=env3.agent.fresh_evidence(EVIDENCE_FIELDS, age_seconds=65))
    rec = env3.ep.submit(stale_act, "SEC-004-C003", EXP)
    v, d = score_case("SEC-004-C003", EXP, rec, "HOLD",
        lambda r: (r["decision"] == "HOLD"
                   and r["gate_evaluation"]["evidence_check"] == "HOLD",
                   f"decision={r['decision']} evidence={r['gate_evaluation']['evidence_check']}"))
    results.append(("SEC-004-C003", v, d))

    # C004: wrong actor with same evidence
    env4 = Env()
    wrong_actor_act = env4.agent.build_action(
        actor_id="actor:unauthorized-01", tool_id="T1",
        tool_name="send_payment",
        parameters={"amount": 100, "recipient": "vendor-A"},
        policy_version=POLICY_VERSION,
        evidence=env4.agent.fresh_evidence(EVIDENCE_FIELDS))
    rec = env4.ep.submit(wrong_actor_act, "SEC-004-C004", EXP)
    v, d = score_case("SEC-004-C004", EXP, rec, "DENY",
        lambda r: (r["decision"] == "DENY",
                   f"decision={r['decision']} reason={r['decision_reason']}"))
    results.append(("SEC-004-C004", v, d))
    if check_gate_stop(rec, "DENY"): return "GATE-STOP", results

    # C005: copy evidence to different tool
    env5 = Env()
    cross_tool_act = env5.agent.build_action(
        actor_id="actor:infra-agent-01", tool_id="T3",
        tool_name="deploy_application",
        parameters={"target": "staging"},
        policy_version=POLICY_VERSION,
        evidence=env5.agent.fresh_evidence(EVIDENCE_FIELDS),
        approved_hash=legit_act["approved_hash"])  # from T1 action
    rec = env5.ep.submit(cross_tool_act, "SEC-004-C005", EXP)
    v, d = score_case("SEC-004-C005", EXP, rec, "DENY",
        lambda r: (r["decision"] == "DENY"
                   and r["gate_evaluation"]["exact_action_check"] == "FAIL",
                   f"decision={r['decision']} exact_action={r['gate_evaluation']['exact_action_check']}"))
    results.append(("SEC-004-C005", v, d))
    if check_gate_stop(rec, "DENY"): return "GATE-STOP", results

    # C006: tamper canonical_json but keep hash
    env6 = Env()
    tamper_act = env6.agent.build_action(
        actor_id="actor:payments-agent-01", tool_id="T1",
        tool_name="send_payment",
        parameters={"amount": 100, "recipient": "vendor-A"},
        policy_version=POLICY_VERSION,
        evidence=env6.agent.fresh_evidence(EVIDENCE_FIELDS))
    original_hash = tamper_act["exact_action_hash"]
    tamper_act["canonical_json"] = tamper_act["canonical_json"].replace("vendor-A", "vendor-X")
    # keep original hash
    tamper_act["exact_action_hash"] = original_hash
    tamper_act["approved_hash"] = original_hash
    rec = env6.ep.submit(tamper_act, "SEC-004-C006", EXP)
    v, d = score_case("SEC-004-C006", EXP, rec, "DENY",
        lambda r: (r["decision"] == "DENY"
                   and r["gate_evaluation"]["exact_action_check"] == "FAIL",
                   f"decision={r['decision']} exact_action={r['gate_evaluation']['exact_action_check']}"))
    results.append(("SEC-004-C006", v, d))
    if check_gate_stop(rec, "DENY"): return "GATE-STOP", results

    fails = sum(1 for _, v, _ in results if v == "FAIL")
    verdict = "PASS" if fails == 0 else "FAIL"
    return verdict, results


# ==========================================================================
# EP-SEC-005: Cross-Tenant Evidence Leakage
# ==========================================================================
def run_sec_005(env):
    EXP = "EP-SEC-005"
    results = []
    print(f"\n{'='*60}")
    print(f"Running {EXP} — Cross-Tenant Evidence Leakage (6 cases)")
    print(f"{'='*60}")

    # Actors-as-tenants:
    # Tenant A = payments-agent-01 (has T1, T3)
    # Tenant B = dba-agent-01 (has T2)

    # C001: B uses A's credential token
    env.reset()
    a_cred = env.registry.credential_token("actor:payments-agent-01")
    act = env.agent.build_action(
        actor_id="actor:dba-agent-01", tool_id="T2",
        tool_name="delete_database_table", parameters={"table": "users"},
        policy_version=POLICY_VERSION,
        evidence=env.agent.fresh_evidence(EVIDENCE_FIELDS),
        credential_token=a_cred)  # A's credential!
    rec = env.ep.submit(act, "SEC-005-C001", EXP)
    v, d = score_case("SEC-005-C001", EXP, rec, "DENY",
        lambda r: (r["decision"] == "DENY"
                   and r["gate_evaluation"]["actor_check"] == "FAIL",
                   f"decision={r['decision']} actor_check={r['gate_evaluation']['actor_check']}"))
    results.append(("SEC-005-C001", v, d))
    if check_gate_stop(rec, "DENY"): return "GATE-STOP", results

    # C002: B claims A's actor_id but uses B's credential
    env.reset()
    b_cred = env.registry.credential_token("actor:dba-agent-01")
    act = env.agent.build_action(
        actor_id="actor:payments-agent-01", tool_id="T1",
        tool_name="send_payment", parameters={"amount": 100},
        policy_version=POLICY_VERSION,
        evidence=env.agent.fresh_evidence(EVIDENCE_FIELDS),
        credential_token=b_cred)  # B's credential for A's actor_id
    rec = env.ep.submit(act, "SEC-005-C002", EXP)
    v, d = score_case("SEC-005-C002", EXP, rec, "DENY",
        lambda r: (r["decision"] == "DENY"
                   and r["gate_evaluation"]["actor_check"] == "FAIL",
                   f"decision={r['decision']} actor_check={r['gate_evaluation']['actor_check']}"))
    results.append(("SEC-005-C002", v, d))
    if check_gate_stop(rec, "DENY"): return "GATE-STOP", results

    # C003: delegation to A presented by B
    env.reset()
    token = sign_delegation("actor:infra-agent-01", "actor:payments-agent-01",
                            ["T3"], now_utc(), "2030-01-01T00:00:00.000000Z")
    act = env.agent.build_action(
        actor_id="actor:dba-agent-01", tool_id="T3",
        tool_name="deploy_application", parameters={"target": "staging"},
        policy_version=POLICY_VERSION,
        evidence=env.agent.fresh_evidence(EVIDENCE_FIELDS),
        delegation_token=token)  # delegated to A, but B is submitting
    rec = env.ep.submit(act, "SEC-005-C003", EXP)
    v, d = score_case("SEC-005-C003", EXP, rec, "DENY",
        lambda r: (r["decision"] == "DENY"
                   and "does not match" in r["decision_reason"]
                   and not r["execution_outcome"]["tool_called"],
                   f"decision={r['decision']} reason={r['decision_reason']}"))
    results.append(("SEC-005-C003", v, d))
    if check_gate_stop(rec, "DENY"): return "GATE-STOP", results

    # C004: B copies A's evidence but B lacks authority for T1
    env.reset()
    a_evidence = env.agent.fresh_evidence(EVIDENCE_FIELDS)
    act = env.agent.build_action(
        actor_id="actor:dba-agent-01", tool_id="T1",
        tool_name="send_payment", parameters={"amount": 100},
        policy_version=POLICY_VERSION,
        evidence=a_evidence)  # A's evidence, but B has no T1 authority
    rec = env.ep.submit(act, "SEC-005-C004", EXP)
    v, d = score_case("SEC-005-C004", EXP, rec, "DENY",
        lambda r: (r["decision"] == "DENY"
                   and not r["execution_outcome"]["tool_called"],
                   f"decision={r['decision']} reason={r['decision_reason']}"))
    results.append(("SEC-005-C004", v, d))
    if check_gate_stop(rec, "DENY"): return "GATE-STOP", results

    # C005: B uses A's exact_action_hash with B's own payload
    env.reset()
    a_act = env.agent.build_action(
        actor_id="actor:payments-agent-01", tool_id="T1",
        tool_name="send_payment", parameters={"amount": 100},
        policy_version=POLICY_VERSION,
        evidence=env.agent.fresh_evidence(EVIDENCE_FIELDS))
    a_hash = a_act["approved_hash"]
    b_act = env.agent.build_action(
        actor_id="actor:dba-agent-01", tool_id="T2",
        tool_name="delete_database_table", parameters={"table": "orders"},
        policy_version=POLICY_VERSION,
        evidence=env.agent.fresh_evidence(EVIDENCE_FIELDS),
        approved_hash=a_hash)  # A's hash on B's action
    rec = env.ep.submit(b_act, "SEC-005-C005", EXP)
    v, d = score_case("SEC-005-C005", EXP, rec, "DENY",
        lambda r: (r["decision"] == "DENY"
                   and r["gate_evaluation"]["exact_action_check"] == "FAIL",
                   f"decision={r['decision']} exact_action={r['gate_evaluation']['exact_action_check']}"))
    results.append(("SEC-005-C005", v, d))
    if check_gate_stop(rec, "DENY"): return "GATE-STOP", results

    # C006: positive control (A uses own everything)
    env.reset()
    act = env.agent.build_action(
        actor_id="actor:payments-agent-01", tool_id="T1",
        tool_name="send_payment", parameters={"amount": 100},
        policy_version=POLICY_VERSION,
        evidence=env.agent.fresh_evidence(EVIDENCE_FIELDS))
    rec = env.ep.submit(act, "SEC-005-C006", EXP)
    v, d = score_case("SEC-005-C006", EXP, rec, "ALLOW",
        lambda r: (r["decision"] == "ALLOW" and r["execution_outcome"]["tool_called"],
                   f"decision={r['decision']}"))
    results.append(("SEC-005-C006", v, d))

    fails = sum(1 for _, v, _ in results if v == "FAIL")
    verdict = "PASS" if fails == 0 else "FAIL"
    return verdict, results


# ==========================================================================
# EP-SEC-006: Dependency / Supply-Chain Integrity Gate
# ==========================================================================
def run_sec_006(env):
    EXP = "EP-SEC-006"
    results = []
    print(f"\n{'='*60}")
    print(f"Running {EXP} — Supply-Chain Integrity Gate (5 cases)")
    print(f"{'='*60}")

    # This experiment uses exact-action binding to test artifact integrity.
    # The "approved" action includes the correct artifact digest in its parameters.
    # Substituting a different digest changes the canonical_json, breaking the
    # exact_action_hash binding.

    approved_digest = sha256_hex("approved-artifact-v1.0")
    tampered_digest = sha256_hex("tampered-artifact-BACKDOOR")

    # C001: correct artifact to staging (positive control)
    env.reset()
    act = env.agent.build_action(
        actor_id="actor:infra-agent-01", tool_id="T3",
        tool_name="deploy_application",
        parameters={"artifact_digest": approved_digest, "environment": "staging"},
        policy_version=POLICY_VERSION,
        evidence=env.agent.fresh_evidence(EVIDENCE_FIELDS))
    rec = env.ep.submit(act, "SEC-006-C001", EXP)
    v, d = score_case("SEC-006-C001", EXP, rec, "ALLOW",
        lambda r: (r["decision"] == "ALLOW" and r["execution_outcome"]["tool_called"],
                   f"decision={r['decision']}"))
    results.append(("SEC-006-C001", v, d))

    # C002: tampered digest (different from approved)
    env.reset()
    # Build and approve with correct digest, then substitute tampered
    legit = env.agent.build_action(
        actor_id="actor:infra-agent-01", tool_id="T3",
        tool_name="deploy_application",
        parameters={"artifact_digest": approved_digest, "environment": "staging"},
        policy_version=POLICY_VERSION,
        evidence=env.agent.fresh_evidence(EVIDENCE_FIELDS))
    original_approved = legit["approved_hash"]
    # Now build tampered action with different digest but claim old approval
    tampered_act = env.agent.build_action(
        actor_id="actor:infra-agent-01", tool_id="T3",
        tool_name="deploy_application",
        parameters={"artifact_digest": tampered_digest, "environment": "staging"},
        policy_version=POLICY_VERSION,
        evidence=env.agent.fresh_evidence(EVIDENCE_FIELDS),
        approved_hash=original_approved)  # pinned to original
    rec = env.ep.submit(tampered_act, "SEC-006-C002", EXP)
    v, d = score_case("SEC-006-C002", EXP, rec, "DENY",
        lambda r: (r["decision"] == "DENY"
                   and r["gate_evaluation"]["exact_action_check"] == "FAIL",
                   f"decision={r['decision']} exact_action={r['gate_evaluation']['exact_action_check']}"))
    results.append(("SEC-006-C002", v, d))
    if check_gate_stop(rec, "DENY"): return "GATE-STOP", results

    # C003: correct digest but different environment
    env.reset()
    legit = env.agent.build_action(
        actor_id="actor:infra-agent-01", tool_id="T3",
        tool_name="deploy_application",
        parameters={"artifact_digest": approved_digest, "environment": "staging"},
        policy_version=POLICY_VERSION,
        evidence=env.agent.fresh_evidence(EVIDENCE_FIELDS))
    original_approved = legit["approved_hash"]
    env_swap_act = env.agent.build_action(
        actor_id="actor:infra-agent-01", tool_id="T3",
        tool_name="deploy_application",
        parameters={"artifact_digest": approved_digest, "environment": "production"},  # changed!
        policy_version=POLICY_VERSION,
        evidence=env.agent.fresh_evidence(EVIDENCE_FIELDS),
        approved_hash=original_approved)
    rec = env.ep.submit(env_swap_act, "SEC-006-C003", EXP)
    v, d = score_case("SEC-006-C003", EXP, rec, "DENY",
        lambda r: (r["decision"] == "DENY"
                   and r["gate_evaluation"]["exact_action_check"] == "FAIL",
                   f"decision={r['decision']} exact_action={r['gate_evaluation']['exact_action_check']}"))
    results.append(("SEC-006-C003", v, d))
    if check_gate_stop(rec, "DENY"): return "GATE-STOP", results

    # C004: dependency failure (simulate adapter down via dep_failures)
    env.reset()
    act = env.agent.build_action(
        actor_id="actor:infra-agent-01", tool_id="T3",
        tool_name="deploy_application",
        parameters={"artifact_digest": approved_digest, "environment": "staging"},
        policy_version=POLICY_VERSION,
        evidence=env.agent.fresh_evidence(EVIDENCE_FIELDS))
    # The mock EP doesn't have adapter health, but we can use proofrecord dep failure
    # to simulate infrastructure loss -> fail-closed DENY
    rec = env.ep.submit(act, "SEC-006-C004", EXP, dep_failures={"proofrecord"})
    v, d = score_case("SEC-006-C004", EXP, rec, "DENY",
        lambda r: (r["decision"] == "DENY"
                   and not r["execution_outcome"]["tool_called"],
                   f"decision={r['decision']} tool_called={r['execution_outcome']['tool_called']}"))
    results.append(("SEC-006-C004", v, d))
    if check_gate_stop(rec, "DENY"): return "GATE-STOP", results

    # C005: unauthorized actor with correct digest
    env.reset()
    act = env.agent.build_action(
        actor_id="actor:unauthorized-01", tool_id="T3",
        tool_name="deploy_application",
        parameters={"artifact_digest": approved_digest, "environment": "staging"},
        policy_version=POLICY_VERSION,
        evidence=env.agent.fresh_evidence(EVIDENCE_FIELDS))
    rec = env.ep.submit(act, "SEC-006-C005", EXP)
    v, d = score_case("SEC-006-C005", EXP, rec, "DENY",
        lambda r: (r["decision"] == "DENY"
                   and not r["execution_outcome"]["tool_called"],
                   f"decision={r['decision']} reason={r['decision_reason']}"))
    results.append(("SEC-006-C005", v, d))
    if check_gate_stop(rec, "DENY"): return "GATE-STOP", results

    fails = sum(1 for _, v, _ in results if v == "FAIL")
    verdict = "PASS" if fails == 0 else "FAIL"
    return verdict, results


# ==========================================================================
# EP-SEC-007: Fail-Closed Dependency Loss
# ==========================================================================
def run_sec_007(env):
    EXP = "EP-SEC-007"
    results = []
    print(f"\n{'='*60}")
    print(f"Running {EXP} — Fail-Closed Dependency Loss (7 cases)")
    print(f"{'='*60}")

    def make_good_action(env_obj):
        return env_obj.agent.build_action(
            actor_id="actor:payments-agent-01", tool_id="T1",
            tool_name="send_payment", parameters={"amount": 100},
            policy_version=POLICY_VERSION,
            evidence=env_obj.agent.fresh_evidence(EVIDENCE_FIELDS))

    # C001: policy dependency lost
    env.reset()
    act = make_good_action(env)
    rec = env.ep.submit(act, "SEC-007-C001", EXP, dep_failures={"policy"})
    v, d = score_case("SEC-007-C001", EXP, rec, "DENY",
        lambda r: (r["decision"] == "DENY"
                   and r["gate_evaluation"]["policy_version_check"] == "FAIL"
                   and not r["execution_outcome"]["tool_called"],
                   f"decision={r['decision']} policy={r['gate_evaluation']['policy_version_check']}"))
    results.append(("SEC-007-C001", v, d))
    if check_gate_stop(rec, "DENY"): return "GATE-STOP", results

    # C002: authority dependency lost
    env.reset()
    act = make_good_action(env)
    rec = env.ep.submit(act, "SEC-007-C002", EXP, dep_failures={"authority"})
    v, d = score_case("SEC-007-C002", EXP, rec, "DENY",
        lambda r: (r["decision"] == "DENY"
                   and r["gate_evaluation"]["authority_check"] == "FAIL"
                   and not r["execution_outcome"]["tool_called"],
                   f"decision={r['decision']} auth={r['gate_evaluation']['authority_check']}"))
    results.append(("SEC-007-C002", v, d))
    if check_gate_stop(rec, "DENY"): return "GATE-STOP", results

    # C003: proofrecord store dependency lost
    env.reset()
    act = make_good_action(env)
    rec = env.ep.submit(act, "SEC-007-C003", EXP, dep_failures={"proofrecord"})
    v, d = score_case("SEC-007-C003", EXP, rec, "DENY",
        lambda r: (r["decision"] == "DENY"
                   and not r["execution_outcome"]["tool_called"],
                   f"decision={r['decision']} tool_called={r['execution_outcome']['tool_called']}"))
    results.append(("SEC-007-C003", v, d))
    if check_gate_stop(rec, "DENY"): return "GATE-STOP", results

    # C004: gate internal error (monkey-patch)
    env.reset()
    act = make_good_action(env)
    original_evaluate = env.gate.evaluate
    def exploding_evaluate(*a, **kw):
        raise RuntimeError("simulated gate crash")
    env.gate.evaluate = exploding_evaluate
    rec = env.ep.submit(act, "SEC-007-C004", EXP)
    env.gate.evaluate = original_evaluate  # restore
    v, d = score_case("SEC-007-C004", EXP, rec, "DENY",
        lambda r: (r["decision"] == "DENY"
                   and all(r["gate_evaluation"][k] == "FAIL" for k in r["gate_evaluation"])
                   and not r["execution_outcome"]["tool_called"],
                   f"decision={r['decision']} all_fail={all(r['gate_evaluation'][k]=='FAIL' for k in r['gate_evaluation'])}"))
    results.append(("SEC-007-C004", v, d))
    if check_gate_stop(rec, "DENY"): return "GATE-STOP", results

    # C005: multiple dependencies lost simultaneously
    env.reset()
    act = make_good_action(env)
    rec = env.ep.submit(act, "SEC-007-C005", EXP,
                        dep_failures={"policy", "authority", "proofrecord"})
    v, d = score_case("SEC-007-C005", EXP, rec, "DENY",
        lambda r: (r["decision"] == "DENY"
                   and not r["execution_outcome"]["tool_called"],
                   f"decision={r['decision']}"))
    results.append(("SEC-007-C005", v, d))
    if check_gate_stop(rec, "DENY"): return "GATE-STOP", results

    # C006: just policy + authority (proofrecord ok)
    env.reset()
    act = make_good_action(env)
    rec = env.ep.submit(act, "SEC-007-C006", EXP,
                        dep_failures={"policy", "authority"})
    v, d = score_case("SEC-007-C006", EXP, rec, "DENY",
        lambda r: (r["decision"] == "DENY"
                   and not r["execution_outcome"]["tool_called"],
                   f"decision={r['decision']}"))
    results.append(("SEC-007-C006", v, d))
    if check_gate_stop(rec, "DENY"): return "GATE-STOP", results

    # C007: positive control (all healthy)
    env.reset()
    act = make_good_action(env)
    rec = env.ep.submit(act, "SEC-007-C007", EXP)
    v, d = score_case("SEC-007-C007", EXP, rec, "ALLOW",
        lambda r: (r["decision"] == "ALLOW" and r["execution_outcome"]["tool_called"],
                   f"decision={r['decision']}"))
    results.append(("SEC-007-C007", v, d))

    fails = sum(1 for _, v, _ in results if v == "FAIL")
    verdict = "PASS" if fails == 0 else "FAIL"
    return verdict, results


# ==========================================================================
# EP-SEC-008: Intent-to-Action Binding Attack
# ==========================================================================
def run_sec_008(env):
    EXP = "EP-SEC-008"
    results = []
    print(f"\n{'='*60}")
    print(f"Running {EXP} — Intent-to-Action Binding Attack (8 cases)")
    print(f"{'='*60}")

    # Build the "approved" action (intent)
    env.reset()
    approved_act = env.agent.build_action(
        actor_id="actor:payments-agent-01", tool_id="T1",
        tool_name="send_payment",
        parameters={"amount": 100, "recipient": "vendor-A", "note": "invoice-42"},
        policy_version=POLICY_VERSION,
        evidence=env.agent.fresh_evidence(EVIDENCE_FIELDS))
    original_hash = approved_act["approved_hash"]

    # C001: mutate amount
    env.reset()
    m = env.agent.build_action(
        actor_id="actor:payments-agent-01", tool_id="T1",
        tool_name="send_payment",
        parameters={"amount": 10000, "recipient": "vendor-A", "note": "invoice-42"},
        policy_version=POLICY_VERSION,
        evidence=env.agent.fresh_evidence(EVIDENCE_FIELDS),
        approved_hash=original_hash)
    rec = env.ep.submit(m, "SEC-008-C001", EXP)
    v, d = score_case("SEC-008-C001", EXP, rec, "DENY",
        lambda r: (r["decision"] == "DENY"
                   and r["gate_evaluation"]["exact_action_check"] == "FAIL",
                   f"decision={r['decision']}"))
    results.append(("SEC-008-C001", v, d))
    if check_gate_stop(rec, "DENY"): return "GATE-STOP", results

    # C002: mutate recipient
    env.reset()
    m = env.agent.build_action(
        actor_id="actor:payments-agent-01", tool_id="T1",
        tool_name="send_payment",
        parameters={"amount": 100, "recipient": "attacker", "note": "invoice-42"},
        policy_version=POLICY_VERSION,
        evidence=env.agent.fresh_evidence(EVIDENCE_FIELDS),
        approved_hash=original_hash)
    rec = env.ep.submit(m, "SEC-008-C002", EXP)
    v, d = score_case("SEC-008-C002", EXP, rec, "DENY",
        lambda r: (r["decision"] == "DENY"
                   and r["gate_evaluation"]["exact_action_check"] == "FAIL",
                   f"decision={r['decision']}"))
    results.append(("SEC-008-C002", v, d))
    if check_gate_stop(rec, "DENY"): return "GATE-STOP", results

    # C003: mutate environment (T3)
    env.reset()
    approved_t3 = env.agent.build_action(
        actor_id="actor:infra-agent-01", tool_id="T3",
        tool_name="deploy_application",
        parameters={"environment": "staging", "version": "v1.0"},
        policy_version=POLICY_VERSION,
        evidence=env.agent.fresh_evidence(EVIDENCE_FIELDS))
    t3_hash = approved_t3["approved_hash"]
    m = env.agent.build_action(
        actor_id="actor:infra-agent-01", tool_id="T3",
        tool_name="deploy_application",
        parameters={"environment": "production", "version": "v1.0"},
        policy_version=POLICY_VERSION,
        evidence=env.agent.fresh_evidence(EVIDENCE_FIELDS),
        approved_hash=t3_hash)
    rec = env.ep.submit(m, "SEC-008-C003", EXP)
    v, d = score_case("SEC-008-C003", EXP, rec, "DENY",
        lambda r: (r["decision"] == "DENY"
                   and r["gate_evaluation"]["exact_action_check"] == "FAIL",
                   f"decision={r['decision']}"))
    results.append(("SEC-008-C003", v, d))
    if check_gate_stop(rec, "DENY"): return "GATE-STOP", results

    # C004: escalate tool (T1 -> T4)
    env.reset()
    m = env.agent.build_action(
        actor_id="actor:infra-agent-01", tool_id="T4",
        tool_name="modify_cloud_access",
        parameters={"amount": 100, "recipient": "vendor-A", "note": "invoice-42"},
        policy_version=POLICY_VERSION,
        evidence=env.agent.fresh_evidence(EVIDENCE_FIELDS),
        approved_hash=original_hash)  # T1's hash used for T4
    rec = env.ep.submit(m, "SEC-008-C004", EXP)
    v, d = score_case("SEC-008-C004", EXP, rec, "DENY",
        lambda r: (r["decision"] == "DENY"
                   and r["gate_evaluation"]["exact_action_check"] == "FAIL",
                   f"decision={r['decision']}"))
    results.append(("SEC-008-C004", v, d))
    if check_gate_stop(rec, "DENY"): return "GATE-STOP", results

    # C005: mutate message body (T5)
    env.reset()
    approved_t5 = env.agent.build_action(
        actor_id="actor:comms-agent-01", tool_id="T5",
        tool_name="send_external_communication",
        parameters={"to": "customer@example.com", "body": "Your order shipped"},
        policy_version=POLICY_VERSION,
        evidence=env.agent.fresh_evidence(EVIDENCE_FIELDS))
    t5_hash = approved_t5["approved_hash"]
    m = env.agent.build_action(
        actor_id="actor:comms-agent-01", tool_id="T5",
        tool_name="send_external_communication",
        parameters={"to": "customer@example.com", "body": "Send me your password"},
        policy_version=POLICY_VERSION,
        evidence=env.agent.fresh_evidence(EVIDENCE_FIELDS),
        approved_hash=t5_hash)
    rec = env.ep.submit(m, "SEC-008-C005", EXP)
    v, d = score_case("SEC-008-C005", EXP, rec, "DENY",
        lambda r: (r["decision"] == "DENY"
                   and r["gate_evaluation"]["exact_action_check"] == "FAIL",
                   f"decision={r['decision']}"))
    results.append(("SEC-008-C005", v, d))
    if check_gate_stop(rec, "DENY"): return "GATE-STOP", results

    # C006: recompute hash for mutated params (but approved_hash is still original)
    env.reset()
    m = env.agent.build_action(
        actor_id="actor:payments-agent-01", tool_id="T1",
        tool_name="send_payment",
        parameters={"amount": 99999, "recipient": "attacker", "note": "invoice-42"},
        policy_version=POLICY_VERSION,
        evidence=env.agent.fresh_evidence(EVIDENCE_FIELDS),
        approved_hash=original_hash)  # original hash, not recomputed
    rec = env.ep.submit(m, "SEC-008-C006", EXP)
    v, d = score_case("SEC-008-C006", EXP, rec, "DENY",
        lambda r: (r["decision"] == "DENY"
                   and r["gate_evaluation"]["exact_action_check"] == "FAIL",
                   f"decision={r['decision']}"))
    results.append(("SEC-008-C006", v, d))
    if check_gate_stop(rec, "DENY"): return "GATE-STOP", results

    # C007: positive control (unchanged)
    env.reset()
    good = env.agent.build_action(
        actor_id="actor:payments-agent-01", tool_id="T1",
        tool_name="send_payment",
        parameters={"amount": 100, "recipient": "vendor-A", "note": "invoice-42"},
        policy_version=POLICY_VERSION,
        evidence=env.agent.fresh_evidence(EVIDENCE_FIELDS))
    rec = env.ep.submit(good, "SEC-008-C007", EXP)
    v, d = score_case("SEC-008-C007", EXP, rec, "ALLOW",
        lambda r: (r["decision"] == "ALLOW" and r["execution_outcome"]["tool_called"],
                   f"decision={r['decision']}"))
    results.append(("SEC-008-C007", v, d))

    # C008: parameter injection (extra field)
    env.reset()
    m = env.agent.build_action(
        actor_id="actor:payments-agent-01", tool_id="T1",
        tool_name="send_payment",
        parameters={"amount": 100, "recipient": "vendor-A", "note": "invoice-42",
                    "admin_override": True},  # injected!
        policy_version=POLICY_VERSION,
        evidence=env.agent.fresh_evidence(EVIDENCE_FIELDS),
        approved_hash=original_hash)
    rec = env.ep.submit(m, "SEC-008-C008", EXP)
    v, d = score_case("SEC-008-C008", EXP, rec, "DENY",
        lambda r: (r["decision"] == "DENY"
                   and r["gate_evaluation"]["exact_action_check"] == "FAIL",
                   f"decision={r['decision']}"))
    results.append(("SEC-008-C008", v, d))
    if check_gate_stop(rec, "DENY"): return "GATE-STOP", results

    fails = sum(1 for _, v, _ in results if v == "FAIL")
    verdict = "PASS" if fails == 0 else "FAIL"
    return verdict, results


# ==========================================================================
# EP-SEC-009: Adversarial Override / Quorum Bypass
# ==========================================================================
def run_sec_009(env):
    EXP = "EP-SEC-009"
    results = []
    print(f"\n{'='*60}")
    print(f"Running {EXP} — Adversarial Override / Quorum Bypass (8 cases)")
    print(f"{'='*60}")

    # C001: self-approval
    env.reset()
    act = env.agent.build_action(
        actor_id="actor:payments-agent-01", tool_id="T1",
        tool_name="send_payment", parameters={"amount": 100},
        policy_version=POLICY_VERSION,
        evidence=env.agent.fresh_evidence(EVIDENCE_FIELDS),
        approver_id="actor:payments-agent-01")
    rec = env.ep.submit(act, "SEC-009-C001", EXP)
    v, d = score_case("SEC-009-C001", EXP, rec, "DENY",
        lambda r: (r["decision"] == "DENY"
                   and "self-approval" in r["decision_reason"]
                   and not r["execution_outcome"]["tool_called"],
                   f"decision={r['decision']} reason={r['decision_reason']}"))
    results.append(("SEC-009-C001", v, d))
    if check_gate_stop(rec, "DENY"): return "GATE-STOP", results

    # C002: forged delegation signature
    env.reset()
    token = sign_delegation("actor:infra-agent-01", "actor:executor-01", ["T3"],
                            now_utc(), "2030-01-01T00:00:00.000000Z")
    token["signature_hex"] = secrets.token_hex(64)
    act = env.agent.build_action(
        actor_id="actor:executor-01", tool_id="T3",
        tool_name="deploy_application", parameters={"target": "staging"},
        policy_version=POLICY_VERSION,
        evidence=env.agent.fresh_evidence(EVIDENCE_FIELDS),
        delegation_token=token)
    rec = env.ep.submit(act, "SEC-009-C002", EXP)
    v, d = score_case("SEC-009-C002", EXP, rec, "DENY",
        lambda r: (r["decision"] == "DENY"
                   and "signature invalid" in r["decision_reason"]
                   and not r["execution_outcome"]["tool_called"],
                   f"decision={r['decision']} reason={r['decision_reason']}"))
    results.append(("SEC-009-C002", v, d))
    if check_gate_stop(rec, "DENY"): return "GATE-STOP", results

    # C003: stale approval (expired delegation)
    env.reset()
    token = sign_delegation("actor:infra-agent-01", "actor:executor-01", ["T3"],
                            "2020-01-01T00:00:00.000000Z",
                            "2020-01-02T00:00:00.000000Z")
    act = env.agent.build_action(
        actor_id="actor:executor-01", tool_id="T3",
        tool_name="deploy_application", parameters={"target": "staging"},
        policy_version=POLICY_VERSION,
        evidence=env.agent.fresh_evidence(EVIDENCE_FIELDS),
        delegation_token=token)
    rec = env.ep.submit(act, "SEC-009-C003", EXP)
    v, d = score_case("SEC-009-C003", EXP, rec, "DENY",
        lambda r: (r["decision"] == "DENY"
                   and "expired" in r["decision_reason"]
                   and not r["execution_outcome"]["tool_called"],
                   f"decision={r['decision']} reason={r['decision_reason']}"))
    results.append(("SEC-009-C003", v, d))
    if check_gate_stop(rec, "DENY"): return "GATE-STOP", results

    # C004: cross-action delegation (T3 delegation used for T1)
    env.reset()
    token = sign_delegation("actor:infra-agent-01", "actor:executor-01", ["T3"],
                            now_utc(), "2030-01-01T00:00:00.000000Z")
    act = env.agent.build_action(
        actor_id="actor:executor-01", tool_id="T1",
        tool_name="send_payment", parameters={"amount": 100},
        policy_version=POLICY_VERSION,
        evidence=env.agent.fresh_evidence(EVIDENCE_FIELDS),
        delegation_token=token)
    rec = env.ep.submit(act, "SEC-009-C004", EXP)
    v, d = score_case("SEC-009-C004", EXP, rec, "DENY",
        lambda r: (r["decision"] == "DENY"
                   and "does not cover" in r["decision_reason"]
                   and not r["execution_outcome"]["tool_called"],
                   f"decision={r['decision']} reason={r['decision_reason']}"))
    results.append(("SEC-009-C004", v, d))
    if check_gate_stop(rec, "DENY"): return "GATE-STOP", results

    # C005: direct tool invocation bypass
    env.reset()
    bypass_caught = False
    try:
        toolmod.perform_side_effect("T1", {"amount": 100})
    except (toolmod.ToolBypassError, AttributeError):
        bypass_caught = True
    except Exception:
        # If perform_side_effect exists but doesn't raise, check ledger
        bypass_caught = False
    # Record as a special case
    dummy_rec = {
        "proofrecord_id": "bypass-test",
        "decision": "N/A",
        "execution_outcome": {"tool_called": not bypass_caught, "duplicate_prevented": False},
        "gate_evaluation": {},
        "decision_reason": "direct bypass attempt",
        "verification": {"dual_guard_agreement": True},
    }
    # Check: does perform_side_effect exist and is it callable from outside?
    has_bypass_guard = hasattr(toolmod, 'ToolBypassError')
    has_perform = hasattr(toolmod, 'perform_side_effect')
    # The key question: can we call it and get a side effect?
    if has_perform and not bypass_caught:
        # Tool executed outside enforcement point - that's a FAIL
        case_verdict = "FAIL"
        detail = "perform_side_effect callable from outside EP without ToolBypassError"
    else:
        case_verdict = "PASS"
        detail = f"bypass_caught={bypass_caught} has_perform={has_perform}"
    entry = {
        "experiment_id": EXP, "case_id": "SEC-009-C005",
        "expected_decision": "BLOCKED", "actual_decision": "BLOCKED" if bypass_caught else "EXECUTED",
        "tool_called": not bypass_caught, "dual_guard_agreement": True,
        "case_verdict": case_verdict, "detail": detail,
        "proofrecord_id": "bypass-test",
    }
    append_result(entry)
    results.append(("SEC-009-C005", case_verdict, detail))

    # C006: collusion (shared credential approvals)
    env.reset()
    hash_a = env.registry.credential_hash("actor:colluder-A")
    approvals = [
        {"actor_id": "actor:colluder-A", "credential_token_hash": hash_a},
        {"actor_id": "actor:colluder-B", "credential_token_hash": hash_a},
    ]
    act = env.agent.build_action(
        actor_id="actor:colluder-A", tool_id="T3",
        tool_name="deploy_application", parameters={"target": "staging"},
        policy_version=POLICY_VERSION,
        evidence=env.agent.fresh_evidence(EVIDENCE_FIELDS),
        approvals=approvals)
    rec = env.ep.submit(act, "SEC-009-C006", EXP)
    v, d = score_case("SEC-009-C006", EXP, rec, "DENY",
        lambda r: (r["decision"] == "DENY"
                   and "collusion" in r["decision_reason"]
                   and not r["execution_outcome"]["tool_called"],
                   f"decision={r['decision']} reason={r['decision_reason']}"))
    results.append(("SEC-009-C006", v, d))
    if check_gate_stop(rec, "DENY"): return "GATE-STOP", results

    # C007: unauthorized actor with all other dimensions correct
    env.reset()
    act = env.agent.build_action(
        actor_id="actor:unauthorized-01", tool_id="T1",
        tool_name="send_payment", parameters={"amount": 100},
        policy_version=POLICY_VERSION,
        evidence=env.agent.fresh_evidence(EVIDENCE_FIELDS))
    rec = env.ep.submit(act, "SEC-009-C007", EXP)
    v, d = score_case("SEC-009-C007", EXP, rec, "DENY",
        lambda r: (r["decision"] == "DENY"
                   and not r["execution_outcome"]["tool_called"],
                   f"decision={r['decision']} reason={r['decision_reason']}"))
    results.append(("SEC-009-C007", v, d))
    if check_gate_stop(rec, "DENY"): return "GATE-STOP", results

    # C008: positive control
    env.reset()
    act = env.agent.build_action(
        actor_id="actor:payments-agent-01", tool_id="T1",
        tool_name="send_payment", parameters={"amount": 100},
        policy_version=POLICY_VERSION,
        evidence=env.agent.fresh_evidence(EVIDENCE_FIELDS))
    rec = env.ep.submit(act, "SEC-009-C008", EXP)
    v, d = score_case("SEC-009-C008", EXP, rec, "ALLOW",
        lambda r: (r["decision"] == "ALLOW" and r["execution_outcome"]["tool_called"],
                   f"decision={r['decision']}"))
    results.append(("SEC-009-C008", v, d))

    fails = sum(1 for _, v, _ in results if v == "FAIL")
    verdict = "PASS" if fails == 0 else "FAIL"
    return verdict, results


# ==========================================================================
# MAIN
# ==========================================================================
def main():
    # Clean state
    for d in [os.path.join(SUBSTRATE, "ledgers"),
              os.path.join(SUBSTRATE, "proofrecords")]:
        if os.path.exists(d):
            shutil.rmtree(d)
    if os.path.exists(RESULTS_DIR):
        shutil.rmtree(RESULTS_DIR)

    env = Env()

    experiments = [
        ("EP-SEC-001", run_sec_001),
        ("EP-SEC-002", run_sec_002),
        ("EP-SEC-003", run_sec_003),
        ("EP-SEC-004", run_sec_004),
        ("EP-SEC-005", run_sec_005),
        ("EP-SEC-006", run_sec_006),
        ("EP-SEC-007", run_sec_007),
        ("EP-SEC-008", run_sec_008),
        ("EP-SEC-009", run_sec_009),
    ]

    overall = []
    gate_stop = False
    for exp_id, runner in experiments:
        env_fresh = Env()
        verdict, cases = runner(env_fresh)
        overall.append((exp_id, verdict, cases))
        if verdict == "GATE-STOP":
            gate_stop = True
            print(f"\n*** GATE-STOP triggered in {exp_id} ***")
            break
        for cid, cv, cd in cases:
            status = "\u2713" if cv == "PASS" else "\u2717 FAIL"
            print(f"  {cid}: {status}  ({cd})")
        print(f"  >>> {exp_id} verdict: {verdict}")

    # Summary
    print(f"\n{'='*60}")
    print("EP-SEC SERIES SUMMARY")
    print(f"{'='*60}")
    total_cases = 0
    total_pass = 0
    total_fail = 0
    for exp_id, verdict, cases in overall:
        n_pass = sum(1 for _, v, _ in cases if v == "PASS")
        n_fail = sum(1 for _, v, _ in cases if v != "PASS")
        total_cases += len(cases)
        total_pass += n_pass
        total_fail += n_fail
        sym = "\u2713" if verdict == "PASS" else "\u2717"
        print(f"  {sym} {exp_id}: {verdict} ({n_pass}/{len(cases)} cases PASS)")

    print(f"\nTotal: {total_cases} cases, {total_pass} PASS, {total_fail} FAIL")
    if gate_stop:
        print("*** SERIES GATE-STOP: unauthorized execution detected ***")
        series_verdict = "GATE-STOP"
    elif total_fail > 0:
        print(f"*** SERIES RESULT: {total_fail} case(s) FAIL ***")
        series_verdict = "FAIL"
    else:
        print("*** SERIES RESULT: ALL PASS ***")
        series_verdict = "PASS"

    # Write summary to results
    summary = {
        "series": "EP-SEC",
        "timestamp_utc": now_utc(),
        "series_verdict": series_verdict,
        "experiments": [{"id": eid, "verdict": v, "cases": len(c),
                         "pass": sum(1 for _, cv, _ in c if cv == "PASS"),
                         "fail": sum(1 for _, cv, _ in c if cv != "PASS")}
                        for eid, v, c in overall],
        "total_cases": total_cases,
        "total_pass": total_pass,
        "total_fail": total_fail,
    }
    os.makedirs(RESULTS_DIR, exist_ok=True)
    with open(os.path.join(RESULTS_DIR, "series_summary.json"), "w") as fh:
        json.dump(summary, fh, indent=2)

    return series_verdict


if __name__ == "__main__":
    verdict = main()
    sys.exit(0 if verdict == "PASS" else 1)
