"""
experiments/common.py — Shared harness for the ARK-493..498 runners.

Builds the environment (registry, policy store, gate, enforcement point, actor
agent, proof store) and provides fixtures used across experiments: per-tool
evidence fields, ed25519-signed delegation tokens, the results ledger writer,
and the series-summary ProofRecord builder.
"""
import os
import json
import random
import secrets

from gate.core import (
    canonical_json, now_utc, SCHEMA_VERSION, PUBLIC_KEY_ID, signing_key,
    POLICY_VERSION,
)
from gate.actor_registry import ActorRegistry
from gate.policy import PolicyStore
from gate.gate import ExecutionProofGate
from enforcement.enforcement_point import EnforcementPoint
from enforcement.proofstore import ProofStore
from actor.actor_agent import ActorAgent
from tools import tools as toolmod

random.seed(20260720)

_HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_DIR = os.path.join(_HERE, "results")
LEDGER_DIR = os.path.join(_HERE, "ledger")
RESULTS_LEDGER = os.path.join(RESULTS_DIR, "results_ledger.jsonl")

TOOL_NAMES = {tid: meta["name"] for tid, meta in toolmod.TOOLS.items()}
EVIDENCE_FIELDS = ["approval_ref", "risk_review"]

# Which actor legitimately holds each tool (for ALLOW/HOLD fixtures).
TOOL_OWNER = {
    "T1": "actor:payments-agent-01",
    "T2": "actor:dba-agent-01",
    "T3": "actor:infra-agent-01",
    "T4": "actor:infra-agent-01",
    "T5": "actor:comms-agent-01",
}


class Env:
    def __init__(self, store):
        self.registry = ActorRegistry()
        self.policy = PolicyStore()
        self.gate = ExecutionProofGate(self.registry, self.policy)
        self.store = store
        self.ep = EnforcementPoint(self.gate, self.store)
        self.agent = ActorAgent(self.registry)


def build_env(store):
    return Env(store)


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


def append_result(entry: dict):
    os.makedirs(RESULTS_DIR, exist_ok=True)
    with open(RESULTS_LEDGER, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


def result_entry(experiment_id, case_id, path, tool_id, gate_decision,
                 executed_count, proofrecord_id, dual_guard_agreement,
                 verdict, failure_root_cause=None):
    return {
        "experiment_id": experiment_id,
        "case_id": case_id,
        "path": path,
        "tool_id": tool_id,
        "gate_decision": gate_decision,
        "side_effect_executed_count": executed_count,
        "proofrecord_id": proofrecord_id,
        "dual_guard_agreement": dual_guard_agreement,
        "case_verdict": verdict,
        "failure_root_cause": failure_root_cause,
    }


def executed_count_for_case(tool_id, case_id):
    """Count executed side-effect ledger entries for a given case_id + tool."""
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


def write_series_summary(store, experiment_id, decision, case_ids, extra=None):
    """Append one series-summary ProofRecord to the chain (not a scored case)."""
    nnn = experiment_id.split("-")[1]
    case_id = f"ARK-{nnn}-SUMMARY"
    extra = extra or {}
    payload = {"tool_id": "SUMMARY", "tool_name": "series_summary",
               "experiment_id": experiment_id, "case_ids": case_ids}
    payload.update(extra)
    cjson = canonical_json(payload)
    from gate.core import sha256_hex
    record = {
        "schema_version": SCHEMA_VERSION,
        "proofrecord_id": secrets.token_hex(16),
        "case_id": case_id,
        "experiment_id": experiment_id,
        "timestamp_utc": now_utc(),
        "actor": {"actor_id": "actor:series-summary",
                  "credential_token_hash": sha256_hex("series-summary"),
                  "delegated_by": None},
        "requested_action": {
            "tool_id": "SUMMARY", "tool_name": "series_summary",
            "parameters": {"case_ids": case_ids, "case_count": len(case_ids),
                           **extra},
            "canonical_json": cjson, "exact_action_hash": sha256_hex(cjson)},
        "authority_basis": {
            "authority_source": "series-summary", "authority_record_id": "none",
            "delegator_chain": [], "authority_valid_at_execution": True,
            "authority_resolved_at": now_utc()},
        "policy_version": POLICY_VERSION,
        "evidence_state": {"required_evidence_fields": [], "evidence_present": True,
                           "evidence_fresh": True, "evidence_snapshot": {}},
        "gate_evaluation": {k: "PASS" for k in (
            "actor_check", "authority_check", "evidence_check",
            "policy_version_check", "state_check", "exact_action_check")},
        "decision": decision,
        "decision_reason": f"series-summary for {experiment_id}: {decision}",
        "execution_outcome": {"tool_called": False, "tool_ledger_entry_id": None,
                              "idempotency_key": secrets.token_hex(16),
                              "duplicate_prevented": False},
        "chain": {"prior_record_hash": None, "this_record_hash": None},
        "verification": {},
        "signature": {"algorithm": "ed25519", "public_key_id": PUBLIC_KEY_ID,
                      "signature_hex": None,
                      "signed_fields": [
                          "proofrecord_id", "case_id", "experiment_id",
                          "timestamp_utc", "actor", "requested_action",
                          "authority_basis", "policy_version", "evidence_state",
                          "gate_evaluation", "decision", "execution_outcome",
                          "chain.prior_record_hash"]},
    }
    return store.store(record)
