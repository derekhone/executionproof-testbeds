"""
test_endpoints.py — self-contained tests for the EXPERIMENTAL simulated crypto
metadata endpoints (issue #25). Uses Flask's test client; no network, no
hardware, no signing.

Run:
    python crypto-metadata-endpoints/test_endpoints.py
"""
from __future__ import annotations

import sys

import app as flask_app
import metadata as md

REQUIRED_CONTRACT_FIELDS = {
    "mode": "aws-kms-native",
    "hardware_backed": True,
    "in_process_signing": False,
    "signature_algorithm": "ML-DSA-65",
    "hash_algorithm": "SHA-256",
    "formal_conformance": "pending independent external review",
}

# Terms that must NEVER appear in any payload (no certified/compliant claims).
FORBIDDEN_SUBSTRINGS = [
    "fips compliant",
    "fips-compliant",
    "cnsa 2.0 compliant",
    "cnsa compliant",
    "fips validated",
    "fips-validated",
    "certified",
    "certification complete",
]

failures = []


def check(cond, msg):
    if cond:
        print(f"  PASS: {msg}")
    else:
        print(f"  FAIL: {msg}")
        failures.append(msg)


def main() -> int:
    client = flask_app.app.test_client()

    print("[health]")
    r = client.get("/health")
    check(r.status_code == 200, "/health returns 200")
    check(r.get_json().get("simulation") is True, "/health flags simulation")

    print("[/v2/version]")
    r = client.get("/v2/version")
    check(r.status_code == 200, "/v2/version returns 200")
    v = r.get_json()
    check(v["_simulation"]["simulation"] is True, "version has simulation block")
    check(v["signature_algorithm"] == "ML-DSA-65", "version reports ML-DSA-65")
    check(r.headers.get("X-ExecutionProof-Simulation") == "true",
          "version carries simulation header")

    print("[/v2/crypto-manifest]")
    r = client.get("/v2/crypto-manifest")
    check(r.status_code == 200, "/v2/crypto-manifest returns 200")
    m = r.get_json()
    for k, expected in REQUIRED_CONTRACT_FIELDS.items():
        check(m.get(k) == expected, f"manifest field {k} == {expected!r}")
    check(m.get("simulated") is True, "manifest marked simulated=true")
    check(m["_simulation"]["hardware_present"] is False,
          "manifest simulation block: hardware_present=false")
    check(bool(m.get("active_public_key_id")), "manifest exposes active key id")
    check("retired_public_keys" in m, "manifest exposes retired keys list")
    check("signature_metadata_schema" in m, "manifest exposes signature schema")
    check("canonical_payload_hashing" in m, "manifest exposes hashing rules")
    check("rotation_retirement_revocation" in m,
          "manifest exposes rotation/retirement/revocation behavior")

    print("[/v2/crypto/pq-public-key]")
    r = client.get("/v2/crypto/pq-public-key")
    check(r.status_code == 200, "/v2/crypto/pq-public-key returns 200")
    k = r.get_json()
    check(k.get("simulated") is True, "pq-public-key marked simulated=true")
    check(k.get("algorithm") == "ML-DSA-65", "pq-public-key reports ML-DSA-65")
    check(bool(k.get("public_key_id")), "pq-public-key exposes active key id")

    print("[no forbidden certified/compliant claims]")
    import json as _json
    blob = _json.dumps(md.build_all()).lower()
    for term in FORBIDDEN_SUBSTRINGS:
        check(term not in blob, f"no forbidden term: {term!r}")

    print()
    if failures:
        print(f"RESULT: {len(failures)} FAILURE(S)")
        return 1
    print("RESULT: ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
