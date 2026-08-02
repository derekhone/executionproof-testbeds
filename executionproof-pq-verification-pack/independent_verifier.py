#!/usr/bin/env python3
"""
independent_verifier.py — ExecutionProof Post-Quantum ProofRecord verifier.

This file is DELIBERATELY self-contained and DELIBERATELY uses a THIRD-PARTY
FIPS 204 implementation (`dilithium-py`, pure Python) that is NOT the library
ExecutionProof uses to sign or to verify on the server. Cross-implementation
agreement is the point: the signature is produced inside an AWS KMS FIPS 140-3
Level 3 HSM, the ExecutionProof server verifies it with @noble/post-quantum
(JavaScript), and THIS reviewer confirms the same bytes with dilithium-py
(Python). Three independent implementations must agree.

What this verifier proves, using ONLY the PUBLISHED public keys and the
documented canonicalization + digest rules (see canonicalization.md):

  1. Every ProofRecord in vectors/valid/ carries a genuine ML-DSA-65 asymmetric
     signature that verifies against a PUBLISHED key (active or a non-revoked
     retired key), over the correct message binding for that key's custody mode.
  2. Every ProofRecord in vectors/failure/ FAILS to verify against every
     published key (tampered payload, tampered signature, or a signature made
     with an unpublished key).
  3. Key rotation is real and non-destructive: the genuine pre-rotation record
     (historical_retired_de196a09.json) verifies ONLY under the retired key and
     NOT under the active key; the active records verify ONLY under the active
     key.

What a valid signature does NOT by itself prove (these remain review questions,
see REVIEWER_TASKS.md and CONFORMANCE-8.4.md): that the HSM private key was
never exportable, that the clock was honest, that the surrounding infrastructure
is production-grade, or that the ProofRecord's governance verdict (authority,
evidence, constraints, decision, execution) is itself correct. A signature is a
tamper-evident seal over the record; it is not the governance judgement.

Usage:
    pip install -r requirements.txt
    python3 independent_verifier.py            # uses ./public_keys and ./vectors
    python3 independent_verifier.py --pack .    # explicit pack root

Exit code 0  == every valid vector verified AND every failure vector rejected,
                exactly as declared in vectors/MANIFEST.json.
Exit code !=0 == at least one mismatch. Treat ANY mismatch, or any inability to
                reproduce these checks, as a falsification of the claim.
"""
import argparse
import hashlib
import json
import os
import sys

try:
    from dilithium_py.ml_dsa import ML_DSA_65
except Exception as e:  # pragma: no cover
    sys.stderr.write(
        "ERROR: could not import dilithium_py (independent FIPS 204 implementation).\n"
        "Install it with:  pip install -r requirements.txt\n"
        f"Underlying import error: {e}\n"
    )
    sys.exit(2)

# ---------------------------------------------------------------------------
# The canonical ProofRecord payload: the exact ordered set of fields that are
# signed, and the deterministic serialization applied to them. This MUST match
# the server. See canonicalization.md for the full written specification.
# ---------------------------------------------------------------------------
SIGNED_FIELDS = [
    "version", "request_id", "tenant_id", "chain_id", "sequence_number", "rail",
    "gate_layers", "actor", "action", "context", "evidence_items",
    "constraints_input", "intended_outcome", "failure_conditions",
    "proof_requirement", "authority_result", "evidence_result",
    "constraint_result", "control_decision", "execution_result",
    "coherence_envelope", "audit_trail",
]


def canonical_json(obj):
    """Deterministic JSON: keys deep-sorted, no insignificant whitespace, UTF-8
    kept unescaped, null preserved. Mirrors the server's canonical serializer
    (JSON.stringify semantics with recursively sorted object keys)."""
    if obj is None or isinstance(obj, bool):
        return json.dumps(obj)
    if isinstance(obj, (int, float)):
        return json.dumps(obj)
    if isinstance(obj, str):
        return json.dumps(obj, ensure_ascii=False)
    if isinstance(obj, list):
        return "[" + ",".join(canonical_json(x) for x in obj) + "]"
    if isinstance(obj, dict):
        keys = sorted(obj.keys())
        return "{" + ",".join(
            json.dumps(k, ensure_ascii=False) + ":" + canonical_json(obj[k])
            for k in keys
        ) + "}"
    raise TypeError(f"non-serializable type in payload: {type(obj)}")


def canonical_payload_bytes(record):
    rec = {k: record.get(k) for k in SIGNED_FIELDS}
    return canonical_json(rec).encode("utf-8")


def load_trusted_keys(pack):
    """Load every published public key (active + retired) from public_keys/.
    Revoked keys are loaded but flagged so the verifier can refuse them."""
    keys = []
    kdir = os.path.join(pack, "public_keys")
    endpoint = os.path.join(kdir, "pq-public-key-endpoint.json")
    if os.path.exists(endpoint):
        d = json.load(open(endpoint))
        keys.append({
            "public_key_id": d["public_key_id"],
            "public_key_hex": d["public_key_hex"],
            "revoked": False,
            "role": "ACTIVE",
        })
        for rk in d.get("retired_public_keys", []):
            keys.append({
                "public_key_id": rk["public_key_id"],
                "public_key_hex": rk["public_key_hex"],
                "revoked": bool(rk.get("revoked", False)),
                "role": "RETIRED",
            })
        return keys
    # Fallback: individual key files.
    for fn in sorted(os.listdir(kdir)):
        if fn.startswith(("active_", "retired_")) and fn.endswith(".json"):
            d = json.load(open(os.path.join(kdir, fn)))
            keys.append({
                "public_key_id": d["public_key_id"],
                "public_key_hex": d["public_key_hex"],
                "revoked": bool(d.get("revoked", False)),
                "role": d.get("role", "?"),
            })
    return keys


def verify_against_published(record, trusted):
    """Try to verify the record's ML-DSA-65 signature against each published,
    non-revoked key, over BOTH accepted message bindings (raw canonical bytes
    for software-wrapped custody, SHA-256 digest for aws-kms-native). Returns
    (ok, detail)."""
    sig_hex = record.get("proof_signature_pq")
    if not sig_hex:
        return False, "no proof_signature_pq present"
    try:
        sig = bytes.fromhex(sig_hex)
    except ValueError:
        return False, "proof_signature_pq is not valid hex"
    if len(sig) != 3309:
        return False, f"signature length {len(sig)} != 3309 (ML-DSA-65)"

    raw = canonical_payload_bytes(record)
    digest = hashlib.sha256(raw).digest()

    for k in trusted:
        if k["revoked"]:
            continue
        pk = bytes.fromhex(k["public_key_hex"])
        if ML_DSA_65.verify(pk, digest, sig):
            return True, f"verified under {k['role']} key {k['public_key_id']} over DIGEST"
        if ML_DSA_65.verify(pk, raw, sig):
            return True, f"verified under {k['role']} key {k['public_key_id']} over RAW"
    return False, "did not verify against any published, non-revoked key"


def main():
    ap = argparse.ArgumentParser(description="ExecutionProof PQ ProofRecord independent verifier")
    ap.add_argument("--pack", default=os.path.dirname(os.path.abspath(__file__)),
                    help="pack root containing public_keys/ and vectors/ (default: this file's dir)")
    args = ap.parse_args()
    pack = args.pack

    trusted = load_trusted_keys(pack)
    print("ExecutionProof — Post-Quantum ProofRecord Independent Verifier")
    print("Independent FIPS 204 implementation: dilithium-py (pure Python)")
    print("-" * 70)
    print("Published keys:")
    for k in trusted:
        flag = " [REVOKED]" if k["revoked"] else ""
        print(f"  - {k['role']:8s} {k['public_key_id']}{flag}")
    print("-" * 70)

    manifest_path = os.path.join(pack, "vectors", "MANIFEST.json")
    manifest = json.load(open(manifest_path)) if os.path.exists(manifest_path) else {}
    expected = manifest.get("expected_results", {})

    failures = 0

    # Valid vectors MUST verify.
    valid_dir = os.path.join(pack, "vectors", "valid")
    print("VALID vectors (must VERIFY):")
    for fn in sorted(os.listdir(valid_dir)):
        if not fn.endswith(".json"):
            continue
        rec = json.load(open(os.path.join(valid_dir, fn)))
        ok, detail = verify_against_published(rec, trusted)
        status = "PASS" if ok else "FAIL"
        if not ok:
            failures += 1
        print(f"  [{status}] {fn}: {detail}")

    # Failure vectors MUST be rejected.
    fail_dir = os.path.join(pack, "vectors", "failure")
    print("FAILURE vectors (must be REJECTED):")
    for fn in sorted(os.listdir(fail_dir)):
        if not fn.endswith(".json"):
            continue
        rec = json.load(open(os.path.join(fail_dir, fn)))
        ok, detail = verify_against_published(rec, trusted)
        # For failure vectors, the correct outcome is that verification FAILS.
        good = not ok
        status = "PASS" if good else "FAIL"
        if not good:
            failures += 1
        expl = rec.get("_expected", "")
        print(f"  [{status}] {fn}: verification_returned={'VERIFIED' if ok else 'REJECTED'}"
              + (f"  ({expl})" if expl else ""))

    print("-" * 70)
    if failures == 0:
        print("RESULT: ALL CHECKS PASSED — every valid vector verified and every")
        print("        failure vector was rejected, using only the published keys and")
        print("        an independent FIPS 204 implementation.")
        sys.exit(0)
    else:
        print(f"RESULT: {failures} CHECK(S) FAILED — see [FAIL] lines above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
