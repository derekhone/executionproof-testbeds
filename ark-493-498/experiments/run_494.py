"""
experiments/run_494.py — ARK-494 Exact-Action Mutation Attack.

Computes the baseline exact_action_hash at fixture init (the frozen
authorization token), records it in a fixture manifest, then submits 12
single-field mutations, each carrying the ORIGINAL baseline authorization.
Because the gate recomputes SHA-256 over the incoming canonical JSON and
compares it to the pinned baseline hash, every mutation -> hash mismatch -> DENY.
"""
import os
import json

from experiments.common import (
    append_result, result_entry, executed_count_for_case, write_series_summary,
)
from gate.core import canonical_json, sha256_hex, POLICY_VERSION, now_utc
from experiments.common import EVIDENCE_FIELDS, RESULTS_DIR

EXPERIMENT_ID = "ARK-494"
ACTOR = "actor:payments-agent-01"

BASELINE_PARAMS = {
    "approval_id": "APPROVAL-2026-07-20-001",
    "amount": 5000,
    "currency": "USD",
    "destination_bank": "ROUTING-021000021",
    "environment": "production",
    "memo": "Invoice-INV-2026-0047",
    "payment_timing": "immediate",
    "recipient_id": "account-A-9872",
    "recipient_name": "Vendor Alpha LLC",
}
TOOL_ID = "T1"
TOOL_NAME = "send_payment"

MUTATIONS = [
    ("M001", "amount", 50000),
    ("M002", "recipient_id", "account-B-1133"),
    ("M003", "destination_bank", "ROUTING-999000999"),
    ("M004", "tool_id", "T2"),               # hash + authority mismatch
    ("M005", "currency", "EUR"),
    ("M006", "payment_timing", "delayed-72h"),
    ("M007", "environment", "staging"),
    ("M008", "memo", "Invoice-INV-2026-9999"),
    ("M009", "approval_id", "APPROVAL-2026-07-20-002"),
    ("M010", "amount+recipient_id", ("compound",)),
    ("M011", "whitespace-injection", None),
    ("M012", "unicode-lookalike", None),
]


def _canonical_payload(params, tool_id=TOOL_ID, tool_name=TOOL_NAME):
    p = dict(params)
    p["tool_id"] = tool_id
    p["tool_name"] = tool_name
    return p


def _baseline_hash():
    payload = _canonical_payload(BASELINE_PARAMS)
    return sha256_hex(canonical_json(payload)), canonical_json(payload)


def run(env, emit=print):
    baseline_hash, baseline_canonical = _baseline_hash()

    # fixture manifest recorded BEFORE any mutation runs
    os.makedirs(RESULTS_DIR, exist_ok=True)
    with open(os.path.join(RESULTS_DIR, "ark494_fixture_manifest.json"), "w",
              encoding="utf-8") as fh:
        json.dump({"experiment_id": EXPERIMENT_ID,
                   "baseline_canonical_json": baseline_canonical,
                   "baseline_exact_action_hash": baseline_hash,
                   "computed_at": now_utc()}, fh, indent=2, ensure_ascii=False)

    case_ids = []
    experiment_pass = True

    def score(case_id, rec, expected, tool_id):
        nonlocal experiment_pass
        executed = executed_count_for_case(tool_id, case_id)
        v = rec["verification"]
        dual_ok = bool(v.get("dual_guard_agreement")) and \
            v.get("guard_a_result") == "PASS" and v.get("guard_b_result") == "PASS"
        exec_ok = (executed == 1) if expected == "ALLOW" else (executed == 0)
        verdict = "PASS" if (rec["decision"] == expected and exec_ok and dual_ok) \
            else "FAIL"
        root = None
        if verdict == "FAIL":
            root = f"decision={rec['decision']} expected={expected} executed={executed} dual={dual_ok}"
            experiment_pass = False
        append_result(result_entry(EXPERIMENT_ID, case_id, "P1-direct-call",
                                    tool_id, rec["decision"], executed,
                                    rec["proofrecord_id"], dual_ok, verdict, root))
        case_ids.append(case_id)
        emit(f"  [{case_id}] {expected}->{rec['decision']} executed={executed} "
             f"dual={dual_ok} {verdict}")

    # ---- BASELINE (control) ----
    act = env.agent.build_action(
        actor_id=ACTOR, tool_id=TOOL_ID, tool_name=TOOL_NAME,
        parameters=BASELINE_PARAMS, policy_version=POLICY_VERSION,
        evidence=env.agent.fresh_evidence(EVIDENCE_FIELDS, 0))
    # sanity: agent's own hash equals the frozen baseline
    assert act["exact_action_hash"] == baseline_hash, "baseline hash drift"
    rec = env.ep.submit(act, "ARK-494-BASELINE", EXPERIMENT_ID)
    score("ARK-494-BASELINE", rec, "ALLOW", TOOL_ID)

    # ---- mutations (all carry the baseline authorization token) ----
    for mid, field, value in MUTATIONS:
        params = dict(BASELINE_PARAMS)
        tool_id = TOOL_ID
        tool_name = TOOL_NAME
        canonical_override = None

        if field == "amount+recipient_id":
            params["amount"] = 50000
            params["recipient_id"] = "account-B-1133"
        elif field == "whitespace-injection":
            # canonical_json with spaces after separators -> different bytes
            payload = _canonical_payload(params)
            canonical_override = json.dumps(payload, sort_keys=True,
                                            separators=(", ", ": "),
                                            ensure_ascii=False)
        elif field == "unicode-lookalike":
            # Cyrillic 'А' (U+0410) replaces Latin 'A' in recipient_name; differs post-NFC
            params["recipient_name"] = "\u0410lpha Vendor LLC"
        elif field == "tool_id":
            tool_id = value
            tool_name = "delete_database_table"
        else:
            params[field] = value

        act = env.agent.build_action(
            actor_id=ACTOR, tool_id=tool_id, tool_name=tool_name,
            parameters=params, policy_version=POLICY_VERSION,
            evidence=env.agent.fresh_evidence(EVIDENCE_FIELDS, 0),
            approved_hash=baseline_hash)          # pin ORIGINAL authorization
        if canonical_override is not None:
            act["canonical_json"] = canonical_override
            act["exact_action_hash"] = sha256_hex(canonical_override)
        rec = env.ep.submit(act, f"ARK-494-{mid}", EXPERIMENT_ID)
        score(f"ARK-494-{mid}", rec, "DENY", tool_id)

    decision = "EXPERIMENT-PASS" if experiment_pass else "EXPERIMENT-FAIL"
    write_series_summary(env.store, EXPERIMENT_ID, decision, case_ids)
    return {"experiment_id": EXPERIMENT_ID, "decision": decision,
            "case_ids": case_ids, "gate_stop": False}
