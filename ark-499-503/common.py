"""
common.py — Shared harness for ARK-499-503 (enterprise adapter series).

Provides the results ledger writer, a per-case result entry, and the
series-summary ProofRecord builder. The gate/registry/policy/proofstore are the
frozen ARK-493-498 components; each experiment supplies its own REAL adapter.
"""
import os
import json
import secrets

from gate.core import (
    canonical_json, now_utc, sha256_hex, SCHEMA_VERSION, PUBLIC_KEY_ID,
    POLICY_VERSION,
)

_HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(_HERE, "results")
RESULTS_LEDGER = os.path.join(RESULTS_DIR, "results_ledger.jsonl")


def append_result(entry: dict):
    os.makedirs(RESULTS_DIR, exist_ok=True)
    with open(RESULTS_LEDGER, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


def result_entry(experiment_id, case_id, arm, tool_id, gate_decision,
                 real_effect_count, proofrecord_id, dual_guard_agreement,
                 verdict, detail=None):
    return {
        "experiment_id": experiment_id,
        "case_id": case_id,
        "arm": arm,
        "tool_id": tool_id,
        "gate_decision": gate_decision,
        "real_side_effect_count": real_effect_count,
        "proofrecord_id": proofrecord_id,
        "dual_guard_agreement": dual_guard_agreement,
        "case_verdict": verdict,
        "detail": detail or {},
    }


def write_series_summary(store, experiment_id, decision, case_ids, extra=None):
    """Append one series-summary ProofRecord (meta record, not a scored case)."""
    nnn = experiment_id.split("-")[1]
    case_id = f"ARK-{nnn}-SUMMARY"
    extra = extra or {}
    payload = {"tool_id": "SUMMARY", "tool_name": "series_summary",
               "experiment_id": experiment_id, "case_ids": case_ids}
    payload.update(extra)
    cjson = canonical_json(payload)
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


def fresh_evidence(fields, age_seconds=0):
    from datetime import datetime, timezone, timedelta
    ts = (datetime.now(timezone.utc) - timedelta(seconds=age_seconds))
    ts_str = ts.strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"
    return {
        "required_evidence_fields": list(fields),
        "evidence_snapshot": {f: f"value-{f}" for f in fields},
        "evidence_timestamp": ts_str,
    }
