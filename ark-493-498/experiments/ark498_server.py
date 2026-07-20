"""
experiments/ark498_server.py — ARK-498 gate HTTP server (Flask, loopback TCP).

Runs the ExecutionProof gate behind a real network socket boundary so the
ARK-498 client exercises it over `requests` on localhost. The server owns its
own registry / policy / gate / enforcement-point / ProofStore. The ProofStore
resumes the existing hash chain via load_tail() so ARK-498 records continue the
same append-only chain written by ARK-493..497.

Simulated dependency latencies (policy 50 ms, authority 30 ms) are applied by
the gate (simulate_latency=True). Per-request dependency failures are passed in
the request body and enforced fail-closed. Guard-B runs in DEFERRED (batch) mode
and is flushed at /finalize to keep ~1,810 requests tractable.

Endpoints:
  GET  /health              -> {"status": "ok"}
  POST /submit              -> run one action through the enforcement point
  POST /finalize            -> flush Guard-B, write ARK-498 summary, return audit
  POST /shutdown            -> stop the server
"""
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, request, jsonify   # noqa: E402

from gate.actor_registry import ActorRegistry          # noqa: E402
from gate.policy import PolicyStore                     # noqa: E402
from gate.gate import ExecutionProofGate                # noqa: E402
from enforcement.enforcement_point import EnforcementPoint   # noqa: E402
from enforcement.proofstore import ProofStore, CHAIN_PATH    # noqa: E402
from experiments.common import write_series_summary     # noqa: E402

app = Flask(__name__)

registry = ActorRegistry()
policy = PolicyStore()
gate = ExecutionProofGate(registry, policy)
store = ProofStore(guard_b_mode="deferred")
store.load_tail()
ep = EnforcementPoint(gate, store, simulate_latency=True)


@app.get("/health")
def health():
    return jsonify({"status": "ok", "chain_tail": store.last_hash})


@app.post("/submit")
def submit():
    body = request.get_json(force=True)
    action = body["action"]
    case_id = body["case_id"]
    experiment_id = body.get("experiment_id", "ARK-498")
    dep_failures = body.get("dep_failures", [])
    try:
        rec = ep.submit(action, case_id, experiment_id, dep_failures=dep_failures)
        return jsonify({
            "ok": True,
            "decision": rec["decision"],
            "proofrecord_id": rec["proofrecord_id"],
            "tool_called": rec["execution_outcome"]["tool_called"],
            "duplicate_prevented": rec["execution_outcome"]["duplicate_prevented"],
            "gate_evaluation": rec["gate_evaluation"],
        })
    except Exception as exc:  # noqa: BLE001 — report server error to client
        return jsonify({"ok": False, "error": repr(exc)}), 500


@app.post("/audit")
def audit_endpoint():
    # flush deferred Guard-B over every ARK-498 record, then audit them
    store.flush_deferred_guard_b()

    # independent signature-verification audit of ARK-498 records (P-498-6)
    total = 0
    guard_b_pass = 0
    complete = 0
    proof_ids = set()
    required_top = [
        "schema_version", "proofrecord_id", "case_id", "experiment_id",
        "timestamp_utc", "actor", "requested_action", "authority_basis",
        "policy_version", "evidence_state", "gate_evaluation", "decision",
        "decision_reason", "execution_outcome", "chain", "signature",
    ]
    with open(CHAIN_PATH, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            if r.get("experiment_id") != "ARK-498":
                continue
            if r["decision"] in ("EXPERIMENT-PASS", "EXPERIMENT-FAIL", "GATE-STOP"):
                continue
            total += 1
            proof_ids.add(r["proofrecord_id"])
            if r.get("verification", {}).get("guard_b_result") == "PASS":
                guard_b_pass += 1
            if all(r.get(f) is not None for f in required_top):
                complete += 1

    audit = {
        "records_total": total,
        "guard_b_pass": guard_b_pass,
        "signature_verification_rate": (guard_b_pass / total) if total else 1.0,
        "complete_records": complete,
        "completeness_rate": (complete / total) if total else 1.0,
        "self_import_analysis": store.last_self_import_analysis,
        "unique_proofrecord_ids": len(proof_ids),
    }
    return jsonify({"ok": True, "audit": audit})


@app.post("/finalize")
def finalize():
    body = request.get_json(force=True)
    decision = body["decision"]
    extra = dict(body.get("extra", {}))
    case_ids = body.get("case_ids", [])
    # write the ARK-498 series-summary as the final chain link
    summary = write_series_summary(store, "ARK-498", decision, case_ids, extra=extra)
    return jsonify({"ok": True,
                    "summary_proofrecord_id": summary["proofrecord_id"]})


@app.post("/shutdown")
def shutdown():
    os._exit(0)


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5050
    # threaded=True so S003/S004 concurrent clients are served in parallel
    app.run(host="127.0.0.1", port=port, threaded=True, debug=False,
            use_reloader=False)
