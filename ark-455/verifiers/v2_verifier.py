#!/usr/bin/env python3
"""
ARK-455 Verifier V2 (Python)
Independent ProofRecord signature verification per preregistration Section 4.3

ISOLATION NOTICE: This implementation is built SOLELY from the prose specification
in ARK-455 PREREGISTRATION.md Sections 4.2, 4.3, and 6. It does NOT reference:
- Verifier V1 (TypeScript) source code
- Generator source code
- Any other implementation artifacts

The verification procedure per Section 4.3:
1. Extract the signature field from the record
2. Remove the signature field, leaving the original 7 fields
3. Canonicalize the 7-field record via RFC 8785 (JCS)
4. Verify the signature against the canonical byte string using Ed25519
5. ACCEPT if signature is valid; REJECT if invalid
"""

import json
import sys
from typing import Dict, Any, List, Literal
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError
from nacl.encoding import HexEncoder


def canonicalize_jcs(obj: Dict[str, Any]) -> bytes:
    """
    Canonicalize a JSON object per RFC 8785 (JSON Canonicalization Scheme).
    
    Per RFC 8785:
    - Keys are sorted lexicographically
    - No whitespace
    - Unicode characters preserved (ensure_ascii=False)
    - Deterministic serialization
    
    Returns the canonical byte representation.
    """
    canonical_str = json.dumps(
        obj,
        sort_keys=True,
        ensure_ascii=False,
        separators=(',', ':')
    )
    return canonical_str.encode('utf-8')


def verify_proof_record(
    record: Dict[str, Any],
    public_key_hex: str
) -> Literal["ACCEPT", "REJECT"]:
    """
    Verify a signed ProofRecord.
    
    Per ARK-455 Section 4.3 verification procedure:
    1. Extract signature field
    2. Remove signature, leaving original 7 fields
    3. Canonicalize via RFC 8785
    4. Verify Ed25519 signature
    5. ACCEPT if valid, REJECT if invalid
    
    Args:
        record: ProofRecord dictionary (must include 'signature' field)
        public_key_hex: Ed25519 public key as hex string
    
    Returns:
        "ACCEPT" if signature is valid, "REJECT" otherwise
    """
    try:
        # Step 1: Extract signature field
        if 'signature' not in record:
            return "REJECT"  # No signature present
        
        signature_hex = record['signature']
        signature_bytes = bytes.fromhex(signature_hex)
        
        if len(signature_bytes) != 64:
            return "REJECT"  # Invalid signature length (Ed25519 signatures are 64 bytes)
        
        # Step 2: Remove signature field, leaving original 7 fields
        # Per Section 4.1, the 7 required fields are:
        # decision, timestamp, payload_hash, evidence_references, actor, execution_outcome, review_path
        unsigned_record = {
            'decision': record['decision'],
            'timestamp': record['timestamp'],
            'payload_hash': record['payload_hash'],
            'evidence_references': record['evidence_references'],
            'actor': record['actor'],
            'execution_outcome': record['execution_outcome'],
            'review_path': record['review_path']
        }
        
        # Step 3: Canonicalize the 7-field record via RFC 8785
        canonical_bytes = canonicalize_jcs(unsigned_record)
        
        # Step 4: Verify Ed25519 signature
        verify_key = VerifyKey(public_key_hex, encoder=HexEncoder)
        
        try:
            verify_key.verify(canonical_bytes, signature_bytes)
            # Step 5: Signature is valid → ACCEPT
            return "ACCEPT"
        except BadSignatureError:
            # Step 5: Signature is invalid → REJECT
            return "REJECT"
    
    except (KeyError, ValueError, TypeError) as e:
        # Any exception during verification (missing field, malformed data) → REJECT
        return "REJECT"


def batch_verify(
    records: List[Dict[str, Any]],
    public_key_hex: str
) -> Dict[str, Any]:
    """
    Batch verify multiple ProofRecords.
    
    Returns:
        Dictionary with verification statistics
    """
    accepted = 0
    rejected = 0
    
    for record in records:
        verdict = verify_proof_record(record, public_key_hex)
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
    if len(sys.argv) < 3:
        print("Usage: python3 v2_verifier.py <public_key_hex> <records.json>", file=sys.stderr)
        sys.exit(1)
    
    public_key_hex = sys.argv[1]
    records_file = sys.argv[2]
    
    with open(records_file, 'r') as f:
        records_data = json.load(f)
    
    # Handle both single record and array of records
    if isinstance(records_data, dict):
        records = [records_data]
    else:
        records = records_data
    
    result = batch_verify(records, public_key_hex)
    print(json.dumps(result, indent=2))
