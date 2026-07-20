"""
guards/guard_b_verifier.py — Guard-B, the isolated subprocess verifier.

Launched via subprocess.Popen(['python3', 'guards/guard_b_verifier.py', ...]).
It imports ONLY the permitted modules (json, hashlib, sys, os, pathlib,
unicodedata, base64, cryptography.hazmat.primitives.asymmetric.ed25519) plus
`ast` for the mandatory self-analysis. It reads ProofRecords from disk,
independently recomputes canonical hashes, and checks the seven properties of
preregistration v1.1 Section 5.2. It imports NOTHING from gate/, enforcement/,
tools/, or actor/. Results are written to stdout as JSON.

Invocation:
  guard_b_verifier.py <record_path> <expected_prior_hash>
  guard_b_verifier.py --job <jobfile.json>     # batch: [{path, expected_prior_hash}]
"""
import json
import hashlib
import sys
import os
import pathlib
import unicodedata
import base64
import ast

from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.exceptions import InvalidSignature

_SIGNED_FIELDS = [
    "proofrecord_id", "case_id", "experiment_id", "timestamp_utc",
    "actor", "requested_action", "authority_basis", "policy_version",
    "evidence_state", "gate_evaluation", "decision", "execution_outcome",
    "chain.prior_record_hash",
]

_REQUIRED_TOP = [
    "schema_version", "proofrecord_id", "case_id", "experiment_id",
    "timestamp_utc", "actor", "requested_action", "authority_basis",
    "policy_version", "evidence_state", "gate_evaluation", "decision",
    "decision_reason", "execution_outcome", "chain", "signature",
]

_FORBIDDEN_PREFIXES = ("gate", "enforcement", "tools", "actor", "guards.guard_a")
_PERMITTED = {"json", "hashlib", "sys", "os", "pathlib", "unicodedata",
              "base64", "ast", "cryptography"}


# -- independent primitives ------------------------------------------------
def _nfc(obj):
    if isinstance(obj, str):
        return unicodedata.normalize("NFC", obj)
    if isinstance(obj, dict):
        return {_nfc(k): _nfc(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_nfc(v) for v in obj]
    return obj


def _canon(obj):
    return json.dumps(_nfc(obj), sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False)


def _sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _record_hash(record):
    tmp = json.loads(json.dumps(record))
    tmp.pop("verification", None)
    tmp.setdefault("chain", {})["this_record_hash"] = "COMPUTING"
    return _sha(_canon(tmp))


def _signed_payload(record):
    payload = {}
    for f in _SIGNED_FIELDS:
        if f == "chain.prior_record_hash":
            payload["chain.prior_record_hash"] = record["chain"]["prior_record_hash"]
        else:
            payload[f] = record[f]
    return _canon(payload)


def _public_key():
    priv = ed25519.Ed25519PrivateKey.from_private_bytes(b"\x00" * 32)
    return priv.public_key()


# -- AST self-analysis -----------------------------------------------------
def self_import_analysis():
    src = pathlib.Path(__file__).read_text(encoding="utf-8")
    tree = ast.parse(src)
    found = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                found.add(n.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                found.add(node.module.split(".")[0])
    forbidden_hits = sorted(
        m for m in found
        if any(m == p or m.startswith(p.split(".")[0] + ".")
               for p in _FORBIDDEN_PREFIXES) and m not in _PERMITTED)
    # also explicitly flag testbed-package roots
    forbidden_hits = sorted(set(forbidden_hits) | {
        m for m in found if m in ("gate", "enforcement", "tools", "actor")})
    return {
        "modules_imported": sorted(found),
        "permitted_only": len(forbidden_hits) == 0,
        "forbidden_imports_found": forbidden_hits,
    }


# -- per-record verification ----------------------------------------------
def verify_record(record, expected_prior_hash, pub):
    fields = []
    ok = True

    fields.append("required_fields_present")
    for f in _REQUIRED_TOP:
        if f not in record or record[f] is None:
            ok = False

    fields.append("exact_action_hash_matches_canonical")
    canonical = record["requested_action"]["canonical_json"]
    computed = _sha(canonical)
    if computed != record["requested_action"]["exact_action_hash"]:
        ok = False

    is_meta = record["decision"] in ("EXPERIMENT-PASS", "EXPERIMENT-FAIL",
                                     "GATE-STOP")
    if not is_meta:
        fields.append("decision_consistent_with_gate_evaluation")
        ge = record["gate_evaluation"]
        deny_dims = ["actor_check", "authority_check", "policy_version_check",
                     "state_check", "exact_action_check"]
        any_deny = any(ge[d] == "FAIL" for d in deny_dims)
        expected = ("DENY" if any_deny else
                    "HOLD" if ge["evidence_check"] == "HOLD" else "ALLOW")
        if record["decision"] != expected:
            ok = False

        fields.append("tool_called_iff_allow")
        called = bool(record["execution_outcome"]["tool_called"])
        if called != (record["decision"] == "ALLOW"):
            ok = False

    fields.append("chain_prior_hash_linkage")
    if expected_prior_hash is not None and \
            record["chain"]["prior_record_hash"] != expected_prior_hash:
        ok = False

    fields.append("this_record_hash_correct")
    if _record_hash(record) != record["chain"]["this_record_hash"]:
        ok = False

    fields.append("signature_valid")
    if sorted(record["signature"]["signed_fields"]) != sorted(_SIGNED_FIELDS):
        ok = False
    else:
        try:
            pub.verify(bytes.fromhex(record["signature"]["signature_hex"]),
                       _signed_payload(record).encode("utf-8"))
        except (InvalidSignature, ValueError):
            ok = False

    return {
        "guard_b_result": "PASS" if ok else "FAIL",
        "guard_b_fields_checked": fields,
        "guard_b_canonical_hash_computed": computed,
    }


def main():
    analysis = self_import_analysis()
    pub = _public_key()
    jobs = []
    if len(sys.argv) >= 3 and sys.argv[1] == "--job":
        jobs = json.loads(pathlib.Path(sys.argv[2]).read_text(encoding="utf-8"))
    else:
        path = sys.argv[1]
        expected = sys.argv[2] if len(sys.argv) > 2 else None
        jobs = [{"path": path, "expected_prior_hash": expected}]

    results = []
    for job in jobs:
        try:
            record = json.loads(pathlib.Path(job["path"]).read_text(encoding="utf-8"))
            res = verify_record(record, job.get("expected_prior_hash"), pub)
        except Exception as exc:  # noqa: BLE001
            res = {"guard_b_result": "FAIL",
                   "guard_b_fields_checked": ["load_error"],
                   "guard_b_canonical_hash_computed": "",
                   "error": str(exc)}
        res["path"] = job["path"]
        results.append(res)

    sys.stdout.write(json.dumps(
        {"self_import_analysis": analysis, "results": results}))


if __name__ == "__main__":
    main()
