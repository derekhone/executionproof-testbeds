"""
gate/core.py — Locked technical constants and shared primitives.

Implements the frozen constants from preregistration v1.1 Section 6:
  - Canonical serialization (json.dumps sort_keys=True, separators=(',',':'),
    ensure_ascii=False) after NFC normalization of all string values.
  - SHA-256 hashing over UTF-8 bytes, lowercase hex digest.
  - ed25519 signing via cryptography>=41.0 with testbed key derived from
    seed b'\\x00' * 32 (testbed-only key; NOT a production secret).
  - Time format: datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')+'Z'

This module is imported by gate.py, actor_registry.py, enforcement_point.py,
actor_agent.py, and the experiment runners. It is NOT imported by the guards
(guard_a.py, guard_b_verifier.py) or by ark497_isolated_verifier.py — those
re-implement the primitives independently to preserve verification independence.
"""
import json
import hashlib
import unicodedata
from datetime import datetime, timezone

from cryptography.hazmat.primitives.asymmetric import ed25519

# ---------------------------------------------------------------------------
# Locked constants (preregistration v1.1 Section 6)
# ---------------------------------------------------------------------------
SCHEMA_VERSION = "ark-enterprise-proofrecord-v1.0"
POLICY_VERSION = "ark-enterprise-v1.0"
PUBLIC_KEY_ID = "ark-enterprise-testbed-key-v1"
TESTBED_KEY_SEED = b"\x00" * 32
PYTHON_TEST_SEED = 20260720
EVIDENCE_FRESHNESS_SECONDS = 60

SIGNED_FIELDS = [
    "proofrecord_id", "case_id", "experiment_id", "timestamp_utc",
    "actor", "requested_action", "authority_basis", "policy_version",
    "evidence_state", "gate_evaluation", "decision", "execution_outcome",
    "chain.prior_record_hash",
]


# ---------------------------------------------------------------------------
# Canonical serialization + hashing
# ---------------------------------------------------------------------------
def _nfc_normalize(obj):
    """Recursively NFC-normalize every string value in a JSON-like object."""
    if isinstance(obj, str):
        return unicodedata.normalize("NFC", obj)
    if isinstance(obj, dict):
        return {_nfc_normalize(k): _nfc_normalize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_nfc_normalize(v) for v in obj]
    return obj


def canonical_json(obj) -> str:
    """Locked canonical form: NFC-normalized strings, sorted keys, no whitespace."""
    normalized = _nfc_normalize(obj)
    return json.dumps(normalized, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False)


def sha256_hex(text: str) -> str:
    """SHA-256 hex digest over the UTF-8 bytes of `text`."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def canonical_hash(obj) -> str:
    """SHA-256 hex digest of the canonical JSON of `obj`."""
    return sha256_hex(canonical_json(obj))


# ---------------------------------------------------------------------------
# Time
# ---------------------------------------------------------------------------
def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"


# ---------------------------------------------------------------------------
# ed25519 signing (testbed key)
# ---------------------------------------------------------------------------
def signing_key() -> ed25519.Ed25519PrivateKey:
    return ed25519.Ed25519PrivateKey.from_private_bytes(TESTBED_KEY_SEED)


def public_key_pem() -> bytes:
    from cryptography.hazmat.primitives import serialization
    pub = signing_key().public_key()
    return pub.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )


def build_signed_payload(record: dict) -> str:
    """Build the canonical string over exactly the SIGNED_FIELDS."""
    payload = {}
    for f in SIGNED_FIELDS:
        if f == "chain.prior_record_hash":
            payload["chain.prior_record_hash"] = record["chain"]["prior_record_hash"]
        else:
            payload[f] = record[f]
    return canonical_json(payload)


def sign_record(record: dict) -> str:
    data = build_signed_payload(record).encode("utf-8")
    return signing_key().sign(data).hex()


# ---------------------------------------------------------------------------
# this_record_hash computation
# ---------------------------------------------------------------------------
def compute_record_hash(record: dict) -> str:
    """
    Compute this_record_hash per the hash computation rule.

    The `verification` block (which carries the guards' own outputs) is
    excluded so that a record can be finalised after both guards write their
    results without invalidating the hash. Both guards apply this identical
    rule independently, so they agree. `chain.this_record_hash` is set to the
    literal "COMPUTING" placeholder before serialization.
    """
    import copy
    tmp = copy.deepcopy(record)
    tmp.pop("verification", None)
    tmp.setdefault("chain", {})["this_record_hash"] = "COMPUTING"
    return canonical_hash(tmp)
