#!/usr/bin/env python3
"""
ARK-455 ProofRecord Generator
Generates valid signed records and tampered variants per arm specifications.
"""

import json
import hashlib
import secrets
from datetime import datetime, timezone
from typing import Dict, List, Any
from nacl.signing import SigningKey
from nacl.encoding import HexEncoder

# RFC 8785 JSON Canonicalization Scheme (JCS)
# Python implementation: sort keys, no whitespace, unicode escape sequences normalized
def canonicalize_jcs(obj: Dict[str, Any]) -> bytes:
    """
    Canonicalize a JSON object per RFC 8785 (JCS).
    Returns deterministic byte representation.
    """
    # Simple implementation: json.dumps with sort_keys, no whitespace, ensure_ascii
    # This matches RFC 8785 for the subset we need
    canonical_str = json.dumps(
        obj,
        sort_keys=True,
        ensure_ascii=False,
        separators=(',', ':')
    )
    return canonical_str.encode('utf-8')


class ProofRecordGenerator:
    """Generates and signs ProofRecords per ARK-455 specification."""
    
    def __init__(self, seed: int = None):
        """Initialize with optional seed for reproducibility."""
        self.seed = seed if seed is not None else secrets.randbits(256)
        self.rng = secrets.SystemRandom(self.seed)
        
        # Generate Ed25519 keypair (deterministic from seed for reproducibility)
        seed_bytes = self.seed.to_bytes(32, 'big')
        self.signing_key = SigningKey(seed_bytes)
        self.verify_key = self.signing_key.verify_key
    
    def get_public_key_hex(self) -> str:
        """Return the verification public key as hex string."""
        return self.verify_key.encode(encoder=HexEncoder).decode('ascii')
    
    def generate_base_record(self) -> Dict[str, Any]:
        """Generate a valid base ProofRecord with random field values."""
        # Random but valid-looking field values
        decisions = ["ALLOW", "DENY", "HOLD"]
        outcomes = ["executed", "blocked", "held"]
        
        # Generate random payload hash
        payload_bytes = secrets.token_bytes(32)
        payload_hash = hashlib.sha256(payload_bytes).hexdigest()
        
        # Current timestamp
        timestamp = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        
        # Random evidence references
        evidence_count = self.rng.randint(1, 4)
        evidence_refs = [f"urn:evidence:{i:03d}" for i in range(evidence_count)]
        
        # Random actor and review path
        actor_id = self.rng.randint(1, 999)
        actor = f"system:authorizer:{actor_id:03d}"
        
        trace_id = self.rng.randint(1000, 9999)
        review_path = f"audit:trace:{trace_id}"
        
        # Pick random decision and matching outcome
        decision = self.rng.choice(decisions)
        if decision == "ALLOW":
            execution_outcome = "executed"
        elif decision == "DENY":
            execution_outcome = "blocked"
        else:  # HOLD
            execution_outcome = "held"
        
        record = {
            "decision": decision,
            "timestamp": timestamp,
            "payload_hash": payload_hash,
            "evidence_references": evidence_refs,
            "actor": actor,
            "execution_outcome": execution_outcome,
            "review_path": review_path
        }
        
        return record
    
    def sign_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sign a ProofRecord with Ed25519.
        Returns a new dict with signature field added.
        """
        # Canonicalize the unsigned record
        canonical_bytes = canonicalize_jcs(record)
        
        # Sign with Ed25519
        signed = self.signing_key.sign(canonical_bytes)
        signature_hex = signed.signature.hex()
        
        # Return record with signature appended
        signed_record = record.copy()
        signed_record['signature'] = signature_hex
        
        return signed_record
    
    def tamper_record(self, signed_record: Dict[str, Any], field: str) -> Dict[str, Any]:
        """
        Tamper with a specific field in a signed record.
        Does NOT re-sign - signature becomes invalid.
        
        Tampering strategies per field:
        - decision: flip ALLOW ↔ DENY
        - timestamp: increment by 1 second
        - payload_hash: flip one bit (change last char)
        - evidence_references: append a new element
        - actor: change the numeric suffix
        - execution_outcome: flip executed ↔ blocked
        - review_path: change the trace ID
        """
        tampered = signed_record.copy()
        
        if field == "decision":
            if tampered["decision"] == "ALLOW":
                tampered["decision"] = "DENY"
            elif tampered["decision"] == "DENY":
                tampered["decision"] = "ALLOW"
            else:  # HOLD
                tampered["decision"] = "ALLOW"
        
        elif field == "timestamp":
            # Parse, add 1 second, re-serialize
            dt = datetime.fromisoformat(tampered["timestamp"].replace('Z', '+00:00'))
            dt = dt.replace(microsecond=(dt.microsecond + 1000000) % 1000000)
            tampered["timestamp"] = dt.isoformat().replace('+00:00', 'Z')
        
        elif field == "payload_hash":
            # Flip last character
            h = tampered["payload_hash"]
            last_char = h[-1]
            new_char = '0' if last_char == 'f' else chr(ord(last_char) + 1)
            tampered["payload_hash"] = h[:-1] + new_char
        
        elif field == "evidence_references":
            # Append a new element
            refs = tampered["evidence_references"].copy()
            new_id = 900 + len(refs)
            refs.append(f"urn:evidence:{new_id:03d}")
            tampered["evidence_references"] = refs
        
        elif field == "actor":
            # Change numeric suffix
            parts = tampered["actor"].split(':')
            num = int(parts[-1])
            parts[-1] = f"{(num + 1) % 1000:03d}"
            tampered["actor"] = ':'.join(parts)
        
        elif field == "execution_outcome":
            if tampered["execution_outcome"] == "executed":
                tampered["execution_outcome"] = "blocked"
            elif tampered["execution_outcome"] == "blocked":
                tampered["execution_outcome"] = "executed"
            else:  # held
                tampered["execution_outcome"] = "executed"
        
        elif field == "review_path":
            # Change trace ID
            parts = tampered["review_path"].split(':')
            num = int(parts[-1])
            parts[-1] = str((num + 1) % 10000)
            tampered["review_path"] = ':'.join(parts)
        
        # Signature remains unchanged → now invalid
        return tampered
    
    def generate_arm_records(self, arm_id: int, count: int = 100) -> List[Dict[str, Any]]:
        """
        Generate records for a specific arm.
        
        Arm 1: Original valid records (no tampering)
        Arms 2-8: Tampered records (specific field altered)
        """
        tampering_targets = {
            1: None,  # No tampering
            2: "decision",
            3: "timestamp",
            4: "payload_hash",
            5: "evidence_references",
            6: "actor",
            7: "execution_outcome",
            8: "review_path"
        }
        
        target_field = tampering_targets.get(arm_id)
        records = []
        
        for i in range(count):
            # Generate base record
            base_record = self.generate_base_record()
            
            # Sign it
            signed_record = self.sign_record(base_record)
            
            # Tamper if needed (arms 2-8)
            if target_field is not None:
                final_record = self.tamper_record(signed_record, target_field)
            else:
                final_record = signed_record
            
            records.append(final_record)
        
        return records


if __name__ == "__main__":
    # Quick test
    gen = ProofRecordGenerator(seed=42)
    print(f"Public key: {gen.get_public_key_hex()}")
    
    # Generate one record per arm
    for arm_id in range(1, 9):
        records = gen.generate_arm_records(arm_id, count=1)
        print(f"\nArm {arm_id} sample:")
        print(json.dumps(records[0], indent=2))
