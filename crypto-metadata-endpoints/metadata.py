"""
metadata.py — EXPERIMENTAL software-simulation builder for the ExecutionProof
crypto metadata endpoints described in GitHub issue #25.

    *** EXPERIMENTAL / SOFTWARE SIMULATION / TESTBED ONLY ***

This module assembles the JSON payloads served by the simulated
`/v2/crypto-manifest`, `/v2/crypto/pq-public-key`, and `/v2/version` endpoints.

IMPORTANT — READ BEFORE USING ANY VALUE HERE:

  * This is a SOFTWARE SIMULATION. It does NOT run on AWS KMS, an HSM, a TPM,
    or any hardware security boundary. Nothing here signs anything inside real
    hardware.
  * The custody descriptors below (`mode: aws-kms-native`, `hardware_backed`,
    `in_process_signing`, etc.) are the DOCUMENTED PRODUCTION CONTRACT taken
    verbatim from `docs/crypto-api-metadata-contract.md` (merged in PR #24).
    They are reproduced here only so this testbed can exercise endpoint
    routing, schema shape, and verifier tooling against the expected contract.
    Their presence is NOT an assertion that THIS simulation is hardware-backed.
  * NO FIPS conformance, validation, certification, or CNSA-compliance claim is
    made or implied. `formal_conformance` remains "pending independent external
    review", consistent with the repository's non-claim boundary.

Public-key material is reused read-only from the already-published
`executionproof-pq-verification-pack/` so the simulated manifest stays
consistent with the committed verification vectors.
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Constants / labels
# ---------------------------------------------------------------------------

API_VERSION = "v2"
SIMULATION_BUILD = "crypto-metadata-endpoints-sim-1.0.0"

# One disclaimer string reused across every response so no consumer can read a
# payload without seeing the simulation boundary.
SIMULATION_NOTICE = (
    "EXPERIMENTAL SOFTWARE SIMULATION / TESTBED. This endpoint does NOT run on "
    "AWS KMS, an HSM, a TPM, or any hardware security boundary. Custody fields "
    "such as 'aws-kms-native' and 'hardware_backed' reproduce the documented "
    "production contract (docs/crypto-api-metadata-contract.md) for routing and "
    "schema testing only; they are NOT a claim that this simulation is "
    "hardware-backed. No FIPS conformance, validation, or certification is "
    "claimed. formal_conformance remains pending independent external review."
)

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PACK_KEYS = os.path.join(
    _REPO_ROOT, "executionproof-pq-verification-pack", "public_keys"
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_pack_endpoint_key() -> dict:
    """Load the published pq-public-key endpoint JSON from the verification pack
    (read-only). Falls back to a minimal stub if the pack is not present so the
    simulation still starts in isolation."""
    path = os.path.join(_PACK_KEYS, "pq-public-key-endpoint.json")
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError):
        return {
            "algorithm": "ML-DSA-65",
            "standard": "NIST FIPS 204 (ML-DSA / CRYSTALS-Dilithium), "
                        "security category 3",
            "public_key_id": "SIMULATED-active",
            "key_version": "SIMULATED-active",
            "retired_public_keys": [],
            "_warning": "verification pack not found; using simulation stub key",
        }


def _simulation_block(kind: str) -> dict:
    """The simulation-provenance block embedded at the top of every response."""
    return {
        "experimental": True,
        "simulation": True,
        "testbed": True,
        "hardware_present": False,
        "live_aws_kms": False,
        "endpoint_kind": kind,
        "build": SIMULATION_BUILD,
        "notice": SIMULATION_NOTICE,
        "contract_source": "docs/crypto-api-metadata-contract.md (PR #24)",
        "generated_at": _now_iso(),
    }


def _documented_common_fields() -> dict:
    """The required common fields from the documented metadata contract.

    These mirror docs/crypto-api-metadata-contract.md exactly. `simulated: true`
    and the surrounding `_simulation` block make clear this testbed is not a
    live hardware-backed deployment.
    """
    return {
        "mode": "aws-kms-native",
        "hardware_backed": True,
        "in_process_signing": False,
        "signature_algorithm": "ML-DSA-65",
        "hash_algorithm": "SHA-256",
        "formal_conformance": "pending independent external review",
        # Simulation-specific honesty flags layered on top of the contract:
        "simulated": True,
        "source": "documented production contract mirrored by software simulation",
    }


# ---------------------------------------------------------------------------
# Endpoint payload builders
# ---------------------------------------------------------------------------

def build_version() -> dict:
    """Payload for GET /v2/version."""
    return {
        "_simulation": _simulation_block("version"),
        "api_version": API_VERSION,
        "service": "ExecutionProof crypto metadata (SIMULATED)",
        "signature_algorithm": "ML-DSA-65",
        "hash_algorithm": "SHA-256",
        "custody_mode": "aws-kms-native",
        "formal_conformance": "pending independent external review",
        "contract_document": "docs/crypto-api-metadata-contract.md",
        "related_issue": "https://github.com/derekhone/executionproof-testbeds/issues/25",
    }


def build_crypto_manifest() -> dict:
    """Payload for GET /v2/crypto-manifest."""
    key = _load_pack_endpoint_key()
    active_id = key.get("public_key_id") or key.get("key_version")

    retired = []
    for r in key.get("retired_public_keys", []) or []:
        retired.append(
            {
                "public_key_id": r.get("public_key_id"),
                "revoked": r.get("revoked", False),
                "role": "RETIRED",
                "note": "retained for historical ProofRecord verification",
            }
        )

    manifest = dict(_documented_common_fields())
    manifest["_simulation"] = _simulation_block("crypto-manifest")
    manifest["active_public_key_id"] = active_id
    manifest["active_key_version"] = key.get("key_version", active_id)
    manifest["retired_public_keys"] = retired
    manifest["pq_public_key_endpoint"] = "/v2/crypto/pq-public-key"

    manifest["signature_metadata_schema"] = {
        "algorithm": "ML-DSA-65",
        "standard": "NIST FIPS 204 (ML-DSA / CRYSTALS-Dilithium), category 3",
        "signature_encoding": "base64 (raw ML-DSA-65 signature, 3309 bytes)",
        "public_key_encoding": "base64 / hex (raw ML-DSA-65 public key, 1952 bytes)",
        "fields": [
            "algorithm",
            "public_key_id",
            "key_version",
            "signed_message_form",
            "signature_base64",
        ],
    }

    manifest["canonical_payload_hashing"] = {
        "canonicalization": "deterministic canonical JSON of the ProofRecord "
                            "with signature fields excluded",
        "digest": "SHA-256 of the canonical payload bytes",
        "signed_message_form": "aws-kms-native custody signs the SHA-256 digest "
                               "(KMS RAW ML-DSA message cap); software custody "
                               "signs the canonical payload bytes directly",
        "reference": "docs/proofrecord-verification.md",
    }

    manifest["rotation_retirement_revocation"] = {
        "rotation": "non-destructive; retired keys remain published for "
                   "historical verification",
        "retirement": "retired public keys stay discoverable via this manifest "
                      "and the pq-public-key endpoint",
        "revocation": "revoked flag exposed per retired key "
                      "(revoked=true means do not trust for new verification)",
    }

    manifest["verification_guidance"] = (
        "Verify ProofRecords with any FIPS 204 ML-DSA-65 implementation over the "
        "deterministic canonical-JSON payload (signature fields excluded). Resolve "
        "the public key by public_key_id/key_version; try the SHA-256 digest form "
        "first (aws-kms-native) then the raw canonical-payload form. See "
        "executionproof-pq-verification-pack/independent_verifier.py."
    )

    manifest["references"] = {
        "verification_pack": "executionproof-pq-verification-pack/",
        "pq_public_key_endpoint_json":
            "executionproof-pq-verification-pack/public_keys/"
            "pq-public-key-endpoint.json",
        "contract": "docs/crypto-api-metadata-contract.md",
        "proofrecord_verification": "docs/proofrecord-verification.md",
    }

    return manifest


def build_pq_public_key() -> dict:
    """Payload for GET /v2/crypto/pq-public-key.

    Serves the published public-key endpoint document from the verification pack,
    wrapped with the simulation-provenance block.
    """
    key = _load_pack_endpoint_key()
    out = {"_simulation": _simulation_block("pq-public-key")}
    out.update(key)
    # Ensure the simulation flag is unambiguous even inside the key doc:
    out["simulated"] = True
    return out


# Map route path -> builder, used by the app and snapshot generator.
ENDPOINTS = {
    "/v2/version": build_version,
    "/v2/crypto-manifest": build_crypto_manifest,
    "/v2/crypto/pq-public-key": build_pq_public_key,
}


def build_all() -> dict:
    """Return {route: payload} for every simulated endpoint."""
    return {route: builder() for route, builder in ENDPOINTS.items()}


def payload_sha256(payload: dict) -> str:
    """Deterministic SHA-256 of a payload (sorted keys, excluding volatile
    generated_at timestamps) — used only for snapshot integrity, not signing."""
    def _strip(obj):
        if isinstance(obj, dict):
            return {k: _strip(v) for k, v in obj.items() if k != "generated_at"}
        if isinstance(obj, list):
            return [_strip(v) for v in obj]
        return obj

    canonical = json.dumps(_strip(payload), sort_keys=True,
                           separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()
