"""
tools/tools.py — Five mock tools (T1-T5) with observable side-effect ledgers.

The tools themselves are NOT directly callable from outside the enforcement
point. Their execution logic is installed as name-mangled PRIVATE methods of the
EnforcementPoint class (see enforcement/enforcement_point.py). This module
provides only:
  - tool metadata (ids, names, ledger filenames, aliases),
  - the append-only side-effect ledger writer,
  - a demonstration bypass guard that records BYPASS_ATTEMPT if any external
    caller tries to invoke a tool directly.

Every invocation ATTEMPT through the enforcement point produces exactly one
ledger entry whose `invocation_type` carries the FINAL outcome:
  executed | blocked | held | BYPASS_ATTEMPT  (v1.1 ledger semantics).
"""
import os
import json
import secrets

from gate.core import now_utc

TOOLS = {
    "T1": {"name": "send_payment", "ledger": "T1_send_payment.jsonl"},
    "T2": {"name": "delete_database_table", "ledger": "T2_delete_database_table.jsonl"},
    "T3": {"name": "deploy_application", "ledger": "T3_deploy_application.jsonl"},
    "T4": {"name": "modify_cloud_access", "ledger": "T4_modify_cloud_access.jsonl"},
    "T5": {"name": "send_external_communication", "ledger": "T5_send_external_communication.jsonl"},
}

ALIASES = {
    "payment_dispatch": "T1",
    "table_remover": "T2",
    "app_deployer": "T3",
    "access_modifier": "T4",
    "message_sender": "T5",
}

LEDGER_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                          "ledgers")


class ToolBypassError(RuntimeError):
    """Raised if a mock tool is invoked outside the enforcement point."""


def ledger_path(tool_id: str) -> str:
    return os.path.join(LEDGER_DIR, TOOLS[tool_id]["ledger"])


def build_ledger_entry(tool_id, case_id, idempotency_key, invocation_type,
                       gate_decision, parameters, proofrecord_id):
    return {
        "ledger_entry_id": secrets.token_hex(16),
        "tool_id": tool_id,
        "tool_name": TOOLS[tool_id]["name"],
        "timestamp_utc": now_utc(),
        "case_id": case_id,
        "idempotency_key": idempotency_key,
        "invocation_type": invocation_type,
        "gate_decision": gate_decision,
        "parameters": parameters,
        "proofrecord_id": proofrecord_id,
    }


def append_ledger(entry: dict):
    os.makedirs(LEDGER_DIR, exist_ok=True)
    with open(ledger_path(entry["tool_id"]), "a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


def ensure_ledgers_exist():
    """Create all five ledger files so their absence is never ambiguous."""
    os.makedirs(LEDGER_DIR, exist_ok=True)
    for tid in TOOLS:
        p = ledger_path(tid)
        if not os.path.exists(p):
            open(p, "a", encoding="utf-8").close()


# In-memory observable side-effect counters (proof that the side effect ran).
SIDE_EFFECT_STATE = {tid: {"executed_count": 0} for tid in TOOLS}


def perform_side_effect(tool_id: str, parameters: dict) -> str:
    """
    The actual mock side effect. Returns an opaque effect token.
    Called ONLY by the enforcement point's private tool methods on ALLOW.
    """
    SIDE_EFFECT_STATE[tool_id]["executed_count"] += 1
    return f"effect:{tool_id}:{secrets.token_hex(8)}"


def direct_call_bypass_attempt(tool_id, case_id):
    """
    Demonstration: a direct call to a tool outside the enforcement point is
    blocked by the Python access model and recorded as a BYPASS_ATTEMPT with
    gate decision DENY-by-design.
    """
    entry = build_ledger_entry(tool_id, case_id, idempotency_key=None,
                               invocation_type="BYPASS_ATTEMPT",
                               gate_decision="DENY-by-design",
                               parameters={}, proofrecord_id=None)
    append_ledger(entry)
    raise ToolBypassError(
        f"direct invocation of {tool_id} blocked; tools are private to the "
        f"enforcement point")
