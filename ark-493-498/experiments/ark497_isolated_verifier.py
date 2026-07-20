"""
experiments/ark497_isolated_verifier.py — ARK-497 standalone isolated verifier.

A self-contained verifier that, given ONLY files on disk (ProofRecords, a
verification spec, and the ed25519 public key material), independently
reconstructs every decision element and detects every tampered field WITHOUT
consulting the originating application.

Permitted imports ONLY (preregistration v1.1 Section 13.2):
    json, hashlib, unicodedata, base64, sys, os, pathlib,
    cryptography.hazmat.primitives.asymmetric.ed25519
plus `ast` for the mandatory static self-import analysis. It imports NOTHING
from gate/, enforcement/, tools/, guards/, or actor/.

Usage:
    ark497_isolated_verifier.py --records <dir> --spec <spec.json> [--out <report.json>]

Output: JSON with self_import_analysis, per-record 9-element reconstruction, and
tamper-detection results, written to stdout (and --out if given).
"""
import json
import hashlib
import unicodedata
import base64
import sys
import os
import pathlib
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
_FORBIDDEN_ROOTS = ("gate", "enforcement", "tools", "guards", "actor")
_PERMITTED = {"json", "hashlib", "unicodedata", "base64", "sys", "os",
              "pathlib", "ast", "cryptography"}


# -- independent primitives ------------------------------------------------
def _nfc(o):
    if isinstance(o, str):
        return unicodedata.normalize("NFC", o)
    if isinstance(o, dict):
        return {_nfc(k): _nfc(v) for k, v in o.items()}
    if isinstance(o, list):
        return [_nfc(v) for v in o]
    return o


def _canon(o):
    return json.dumps(_nfc(o), sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False)


def _sha(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


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


# -- mandatory static self-import analysis ---------------------------------
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
    forbidden = sorted(m for m in found if m in _FORBIDDEN_ROOTS)
    non_permitted = sorted(m for m in found if m not in _PERMITTED)
    return {
        "analysis": "ast.walk on self performed before verification",
        "modules_imported": sorted(found),
        "forbidden_testbed_imports": forbidden,
        "non_permitted_imports": non_permitted,
        "permitted_only": len(forbidden) == 0 and len(non_permitted) == 0,
    }


# -- element reconstruction + tamper detection -----------------------------
def reconstruct_and_check(record, pub):
    elements = {}
    tamper_reasons = []

    # 1 actor identity
    elements["1_actor_identity"] = {
        "actor_id": record["actor"]["actor_id"],
        "credential_token_hash": record["actor"]["credential_token_hash"]}
    # 2 requested action
    canonical = record["requested_action"]["canonical_json"]
    elements["2_requested_action"] = {"canonical_json": canonical}
    # 3 applicable authority
    elements["3_authority"] = record["authority_basis"]
    # 4 policy version
    elements["4_policy_version"] = record["policy_version"]
    # 5 evidence state
    elements["5_evidence_state"] = record["evidence_state"]
    # 6 decision
    elements["6_decision"] = record["decision"]
    # 7 exact action approved — recompute + compare
    recomputed_action_hash = _sha(canonical)
    stored_action_hash = record["requested_action"]["exact_action_hash"]
    exact_ok = (recomputed_action_hash == stored_action_hash)
    elements["7_exact_action"] = {
        "recomputed": recomputed_action_hash, "stored": stored_action_hash,
        "match": exact_ok}
    if not exact_ok:
        tamper_reasons.append("exact_action_hash != SHA256(canonical_json)")
    # 8 execution outcome
    elements["8_execution_outcome"] = record["execution_outcome"]
    # 9 chain integrity — recompute this_record_hash
    recomputed_record_hash = _record_hash(record)
    stored_record_hash = record["chain"]["this_record_hash"]
    chain_ok = (recomputed_record_hash == stored_record_hash)
    elements["9_chain_integrity"] = {
        "recomputed_this_record_hash": recomputed_record_hash,
        "stored_this_record_hash": stored_record_hash, "match": chain_ok}
    if not chain_ok:
        tamper_reasons.append("this_record_hash mismatch (a hashed field was altered)")

    # required fields present
    missing = [f for f in _REQUIRED_TOP if f not in record or record[f] is None]
    if missing:
        tamper_reasons.append(f"missing/null required fields: {missing}")

    # decision consistency (skip for summary/meta records)
    is_meta = record["decision"] in ("EXPERIMENT-PASS", "EXPERIMENT-FAIL", "GATE-STOP")
    if not is_meta:
        ge = record["gate_evaluation"]
        deny = any(ge[d] == "FAIL" for d in
                   ("actor_check", "authority_check", "policy_version_check",
                    "state_check", "exact_action_check"))
        expected = ("DENY" if deny else
                    "HOLD" if ge["evidence_check"] == "HOLD" else "ALLOW")
        if record["decision"] != expected:
            tamper_reasons.append(
                f"decision '{record['decision']}' inconsistent with gate_evaluation "
                f"(expected '{expected}')")
        called = bool(record["execution_outcome"]["tool_called"])
        if called != (record["decision"] == "ALLOW"):
            tamper_reasons.append("tool_called inconsistent with decision")

    # signature verification
    sig_ok = False
    try:
        pub.verify(bytes.fromhex(record["signature"]["signature_hex"]),
                   _signed_payload(record).encode("utf-8"))
        sig_ok = True
    except (InvalidSignature, ValueError):
        tamper_reasons.append("ed25519 signature verification failed")
    elements["signature_valid"] = sig_ok

    return {
        "case_id": record.get("case_id"),
        "decision": record.get("decision"),
        "elements": elements,
        "tamper_detected": len(tamper_reasons) > 0,
        "tamper_reasons": tamper_reasons,
    }


def _load_pubkey(spec):
    b64 = spec.get("public_key_raw_b64")
    if b64 is None:
        b64 = spec["signature"]["public_key_raw_b64"]
    raw = base64.b64decode(b64)
    return ed25519.Ed25519PublicKey.from_public_bytes(raw)


def main(argv):
    analysis = self_import_analysis()
    args = {}
    i = 0
    while i < len(argv):
        if argv[i].startswith("--"):
            args[argv[i][2:]] = argv[i + 1]
            i += 2
        else:
            i += 1
    records_dir = pathlib.Path(args["records"])
    spec = json.loads(pathlib.Path(args["spec"]).read_text(encoding="utf-8"))
    pub = _load_pubkey(spec)

    results = []
    for path in sorted(records_dir.glob("*.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        res = reconstruct_and_check(record, pub)
        res["file"] = path.name
        # expected label carried in filename convention: <label>__<case>.json
        res["expected_class"] = path.name.split("__")[0]
        results.append(res)

    out = {"self_import_analysis": analysis,
           "verification_spec_version": spec.get("policy_version"),
           "records_verified": len(results), "results": results}
    payload = json.dumps(out, indent=2, ensure_ascii=False)
    if args.get("out"):
        pathlib.Path(args["out"]).write_text(payload, encoding="utf-8")
    sys.stdout.write(payload)


if __name__ == "__main__":
    main(sys.argv[1:])
