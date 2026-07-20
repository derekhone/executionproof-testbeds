#!/usr/bin/env python3
"""
independent_verifier.py — ARK-503 stand-alone ProofRecord verifier.

This file is DELIBERATELY self-contained: it does NOT import the testbed's gate,
guards, or enforcement code. An independent reviewer runs it against a directory
of ProofRecords (or a chain file) to confirm, using only the PUBLISHED public
key and the documented canonical rules, that every record:

  1. carries all required top-level fields,
  2. has exact_action_hash == SHA-256(requested_action.canonical_json),
  3. has this_record_hash == SHA-256(canonical_json(record - verification block,
     with chain.this_record_hash set to the literal "COMPUTING")),
  4. has a valid ed25519 signature over exactly the SIGNED_FIELDS,
  5. links to the previous record (prior_record_hash chain), and
  6. shows dual_guard_agreement == True in its own recorded verification block.

Meta records (decision in EXPERIMENT-PASS/FAIL, SMOKE-PASS/FAIL, GATE-STOP) skip
the decision<->tool_called consistency check, exactly as the on-line guards do.

Usage:
    python3 independent_verifier.py <chain.jsonl | proofrecords_dir>

Exit code 0 == every record verified; non-zero == at least one failure.
The reviewer should treat ANY failure, or any inability to reproduce these
checks, as a falsification of the tamper-evidence claim for that record.

NOTE ON SCOPE: a valid signature + intact chain proves the records are
internally consistent and were produced by the holder of the testbed key. It
does NOT by itself prove the key was secret, that the clock was honest, or that
the surrounding infrastructure was production-grade. Those remain review
questions (see REVIEWER_TASKS.md).
"""
import os
import sys
import json
import hashlib
import unicodedata
import copy

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.exceptions import InvalidSignature

# ---- PUBLISHED verification parameters (copy of the public artifacts) -------
PUBLIC_KEY_ID = "ark-enterprise-testbed-key-v1"
PUBLIC_KEY_PEM = b"""-----BEGIN PUBLIC KEY-----
MCowBQYDK2VwAyEAO2onvM62pC1io6jQKm8Nc2UyFXcd4kOmOsBIoYtZ2ik=
-----END PUBLIC KEY-----"""

SIGNED_FIELDS = [
    "proofrecord_id", "case_id", "experiment_id", "timestamp_utc", "actor",
    "requested_action", "authority_basis", "policy_version", "evidence_state",
    "gate_evaluation", "decision", "execution_outcome", "chain.prior_record_hash",
]
REQUIRED_TOP = [
    "schema_version", "proofrecord_id", "case_id", "experiment_id",
    "timestamp_utc", "actor", "requested_action", "authority_basis",
    "policy_version", "evidence_state", "gate_evaluation", "decision",
    "execution_outcome", "chain", "verification", "signature",
]
META_DECISIONS = {"EXPERIMENT-PASS", "EXPERIMENT-FAIL", "SMOKE-PASS",
                  "SMOKE-FAIL", "GATE-STOP"}


def nfc(obj):
    if isinstance(obj, str):
        return unicodedata.normalize("NFC", obj)
    if isinstance(obj, dict):
        return {nfc(k): nfc(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [nfc(v) for v in obj]
    return obj


def canonical_json(obj):
    return json.dumps(nfc(obj), sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False)


def sha256_hex(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def compute_record_hash(record):
    tmp = copy.deepcopy(record)
    tmp.pop("verification", None)
    tmp.setdefault("chain", {})["this_record_hash"] = "COMPUTING"
    return sha256_hex(canonical_json(tmp))


def signed_payload(record):
    payload = {}
    for f in SIGNED_FIELDS:
        if f == "chain.prior_record_hash":
            payload[f] = record["chain"]["prior_record_hash"]
        else:
            payload[f] = record[f]
    return canonical_json(payload)


def verify_record(record, expected_prior, pub):
    problems = []
    for f in REQUIRED_TOP:
        if f not in record:
            problems.append(f"missing top-level field '{f}'")
    if problems:
        return problems
    ra = record["requested_action"]
    if ra["exact_action_hash"] != sha256_hex(ra["canonical_json"]):
        problems.append("exact_action_hash != SHA256(canonical_json)")
    if record["chain"]["this_record_hash"] != compute_record_hash(record):
        problems.append("this_record_hash mismatch (record altered)")
    try:
        pub.verify(bytes.fromhex(record["signature"]["signature_hex"]),
                   signed_payload(record).encode("utf-8"))
    except (InvalidSignature, ValueError):
        problems.append("ed25519 signature INVALID")
    if expected_prior is not None and \
            record["chain"]["prior_record_hash"] != expected_prior:
        problems.append(
            f"chain break: prior_record_hash != {expected_prior[:12]}...")
    if record["decision"] not in META_DECISIONS:
        called = record["execution_outcome"]["tool_called"]
        if (record["decision"] == "ALLOW") != bool(called):
            problems.append("tool_called inconsistent with decision")
    if not record["verification"].get("dual_guard_agreement"):
        problems.append("dual_guard_agreement is not True")
    return problems


def load_chain(path):
    if os.path.isdir(path):
        chain = os.path.join(path, "proofrecord_chain.jsonl")
        if os.path.exists(chain):
            path = chain
        else:                       # fall back to individual files, sorted
            recs = []
            for fn in sorted(os.listdir(path)):
                if fn.endswith(".json"):
                    with open(os.path.join(path, fn)) as fh:
                        recs.append(json.load(fh))
            return recs
    recs = []
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if line:
                recs.append(json.loads(line))
    return recs


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    pub = serialization.load_pem_public_key(PUBLIC_KEY_PEM)
    if not isinstance(pub, Ed25519PublicKey):
        print("published key is not ed25519", file=sys.stderr)
        sys.exit(2)
    records = load_chain(sys.argv[1])
    prev = "GENESIS"
    failures = 0
    for i, rec in enumerate(records):
        problems = verify_record(rec, prev, pub)
        status = "OK" if not problems else "FAIL"
        if problems:
            failures += 1
            print(f"[{i:04d}] {rec.get('case_id','?')} {status}: "
                  f"{'; '.join(problems)}")
        prev = rec["chain"]["this_record_hash"]
    print(f"\nVerified {len(records)} records via published key "
          f"'{PUBLIC_KEY_ID}': {len(records) - failures} OK, {failures} FAIL")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
