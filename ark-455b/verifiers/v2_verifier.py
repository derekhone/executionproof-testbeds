#!/usr/bin/env python3
"""
ARK-455b Verifier V2 (Python)
Independent ProofRecord verification per preregistration Sections 4.3 and 4.4.

ISOLATION NOTICE: This implementation is built SOLELY from the prose specification
in ARK-455b PREREGISTRATION.md. It does NOT reference:
- Verifier V1 (JavaScript) source code
- Generator source code
- Any other implementation artifacts

The verification procedure is TWO independent gates (both must pass to ACCEPT):

  Gate A — Signature integrity (Section 4.3):
    1. Extract the signature field from the record.
    2. Remove the signature field, leaving the 7 signed fields.
    3. Canonicalize the 7-field record via RFC 8785 (JCS).
    4. Verify the Ed25519 signature against the canonical byte string.
    5. If the signature is invalid → REJECT.

  Gate B — Validity window (Section 4.4):
    6. Parse the (now signature-verified) `timestamp` as an RFC 3339 UTC instant.
    7. Compute age = verification_time - timestamp.
    8. If age < 0 (record issued in the future) → REJECT.
    9. If age > ttl_seconds (record expired) → REJECT.
   10. Otherwise → ACCEPT.

Gate B is the ARK-455b addition. A bare signature check (ARK-455) cannot catch a
record whose timestamp was set out of the validity window BEFORE signing: the
signature is genuinely valid, yet the record is stale/expired. Expiry semantics
follow ARK-442.
"""

import json
import sys
from datetime import datetime, timezone
from typing import Dict, Any, List, Literal, Optional
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError
from nacl.encoding import HexEncoder


def canonicalize_jcs(obj: Dict[str, Any]) -> bytes:
    """
    Canonicalize a JSON object per RFC 8785 (JSON Canonicalization Scheme).

    - Keys sorted lexicographically
    - No whitespace
    - Unicode characters preserved (ensure_ascii=False)
    """
    canonical_str = json.dumps(
        obj,
        sort_keys=True,
        ensure_ascii=False,
        separators=(',', ':')
    )
    return canonical_str.encode('utf-8')


SIGNED_FIELDS = [
    "decision", "timestamp", "payload_hash", "evidence_references",
    "actor", "execution_outcome", "review_path"
]


def _parse_rfc3339_utc(ts: str) -> datetime:
    """
    Parse an RFC 3339 UTC timestamp. Accepts a trailing 'Z' or an explicit
    +00:00 offset. Returns a timezone-aware datetime in UTC. Raises ValueError
    on any non-UTC or malformed input.
    """
    normalized = ts.replace('Z', '+00:00')
    dt = datetime.fromisoformat(normalized)
    if dt.tzinfo is None:
        raise ValueError("timestamp missing timezone")
    dt = dt.astimezone(timezone.utc)
    return dt


def verify_proof_record(
    record: Dict[str, Any],
    public_key_hex: str,
    verification_time_iso: str,
    ttl_seconds: int
) -> Literal["ACCEPT", "REJECT"]:
    """
    Verify a signed ProofRecord under both the signature gate and the
    validity-window gate.

    Args:
        record: ProofRecord dict (must include 'signature').
        public_key_hex: Ed25519 public key as hex.
        verification_time_iso: RFC 3339 UTC instant at which verification occurs.
        ttl_seconds: maximum allowed age (verification_time - timestamp), in seconds.

    Returns:
        "ACCEPT" only if the signature is valid AND the timestamp is within the
        [verification_time - ttl_seconds, verification_time] window. "REJECT"
        otherwise.
    """
    try:
        # ---- Gate A: signature integrity ----
        if 'signature' not in record:
            return "REJECT"

        signature_hex = record['signature']
        signature_bytes = bytes.fromhex(signature_hex)
        if len(signature_bytes) != 64:
            return "REJECT"

        unsigned_record = {k: record[k] for k in SIGNED_FIELDS}
        canonical_bytes = canonicalize_jcs(unsigned_record)

        verify_key = VerifyKey(public_key_hex, encoder=HexEncoder)
        try:
            verify_key.verify(canonical_bytes, signature_bytes)
        except BadSignatureError:
            return "REJECT"

        # ---- Gate B: validity window ----
        record_ts = _parse_rfc3339_utc(record['timestamp'])
        verification_time = _parse_rfc3339_utc(verification_time_iso)
        age_seconds = (verification_time - record_ts).total_seconds()

        if age_seconds < 0:
            return "REJECT"  # issued in the future
        if age_seconds > ttl_seconds:
            return "REJECT"  # expired

        return "ACCEPT"

    except (KeyError, ValueError, TypeError):
        return "REJECT"


def batch_verify(
    records: List[Dict[str, Any]],
    public_key_hex: str,
    verification_time_iso: str,
    ttl_seconds: int
) -> Dict[str, Any]:
    """Batch verify multiple ProofRecords."""
    accepted = 0
    rejected = 0
    for record in records:
        verdict = verify_proof_record(
            record, public_key_hex, verification_time_iso, ttl_seconds)
        if verdict == "ACCEPT":
            accepted += 1
        else:
            rejected += 1
    total = len(records)
    return {
        'verifier': 'V2-Python',
        'total': total,
        'accepted': accepted,
        'rejected': rejected,
        'rate_accept': accepted / total if total > 0 else 0.0,
        'rate_reject': rejected / total if total > 0 else 0.0
    }


if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("Usage: python3 v2_verifier.py <public_key_hex> <records.json> "
              "<verification_time_iso> <ttl_seconds>", file=sys.stderr)
        sys.exit(1)

    public_key_hex = sys.argv[1]
    records_file = sys.argv[2]
    verification_time_iso = sys.argv[3]
    ttl_seconds = int(sys.argv[4])

    with open(records_file, 'r') as f:
        records_data = json.load(f)

    if isinstance(records_data, dict):
        records = [records_data]
    else:
        records = records_data

    result = batch_verify(records, public_key_hex, verification_time_iso, ttl_seconds)
    print(json.dumps(result, indent=2))
