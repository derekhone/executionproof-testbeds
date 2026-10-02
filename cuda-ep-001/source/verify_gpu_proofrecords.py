#!/usr/bin/env python3
"""
verify_gpu_proofrecords.py
--------------------------
Independently re-verifies every signed GPU ProofRecord in this directory.

For each proofrecord_GPU-*.json file it:
  1. Reconstructs the canonical signed body (strips the appended signature fields).
  2. Recomputes record_digest = sha256(canonical_json(body)) and compares.
  3. Recomputes HMAC-SHA256 and compares.
  4. Verifies the Dilithium3 signature against the embedded public key.

Exit code 0 only if every record passes all four checks.

Note: the Dilithium public key is embedded per record from the run that produced it.
Because signing uses an ephemeral TEST key, verification here confirms internal
consistency of each record, not a long-lived production identity.
"""

import base64
import glob
import hashlib
import hmac
import json
import os
import sys

from dilithium_py.dilithium import Dilithium3

HERE = os.path.dirname(os.path.abspath(__file__))
HMAC_KEY = b"RF-CUDA-EP-001-GPU TEST KEY -- NOT PRODUCTION"

APPENDED = {
    "record_digest",
    "hmac_sha256",
    "dilithium3_signature_b64",
    "dilithium3_public_key_b64",
    "self_verify_ok",
    "signature_note",
}


def canonical_json(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def main():
    files = sorted(glob.glob(os.path.join(HERE, "proofrecord_GPU-*.json")))
    if not files:
        print("No proofrecord_GPU-*.json files found. Run sign_gpu_proofrecords.py first.")
        return 1

    all_ok = True
    for path in files:
        rec = json.load(open(path))
        body = {k: v for k, v in rec.items() if k not in APPENDED}
        cjson = canonical_json(body)

        digest_ok = hashlib.sha256(cjson.encode("ascii")).hexdigest() == rec["record_digest"]
        hmac_ok = hmac.compare_digest(
            hmac.new(HMAC_KEY, cjson.encode("ascii"), hashlib.sha256).hexdigest(),
            rec["hmac_sha256"],
        )
        pk = base64.b64decode(rec["dilithium3_public_key_b64"])
        sig = base64.b64decode(rec["dilithium3_signature_b64"])
        sig_ok = bool(Dilithium3.verify(pk, cjson.encode("ascii"), sig))

        ok = digest_ok and hmac_ok and sig_ok
        all_ok = all_ok and ok
        print(f"{os.path.basename(path)}: digest={digest_ok} hmac={hmac_ok} "
              f"dilithium={sig_ok} -> {'OK' if ok else 'FAIL'}")

    print("-" * 60)
    print("ALL RECORDS VERIFIED:", all_ok)
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
