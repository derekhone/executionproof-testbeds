#!/usr/bin/env python3
"""
ARK-455b ProofRecord Generator (corrected retest of ARK-455)

Changes vs ARK-455 v1.0:
  1. Arm 3 (timestamp, post-signing) now applies a REAL mutation (+1 second via
     timedelta), which breaks the Ed25519 signature. ARK-455 v1.0 used
     (microsecond + 1000000) % 1000000, a proven no-op that never altered the
     record — the root cause of the spurious 0% Arm-3 rejection (see
     ../ark-455/CORRECTION.md).
  2. New Arm 9 (timestamp, PRE-signing, expired): the timestamp is backdated
     beyond the validity window BEFORE signing, so the signature is VALID over an
     expired record. This tests validity-window / expiry semantics that bare
     signature checking cannot catch (expiry semantics per ARK-442).
  3. Mutation-effectiveness audit: for every REJECT arm, the generator records
     whether the tamper actually changed the signed content (or, for the
     pre-signing expired arm, whether the signed timestamp is out of window).
     run_* scripts ABORT if any REJECT arm has an ineffective mutation, so a
     no-op can never again masquerade as a detection failure.
"""

import json
import hashlib
import secrets
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Tuple
from nacl.signing import SigningKey
from nacl.encoding import HexEncoder

# Declared validity window for a ProofRecord, in seconds (ARK-455b spec Section 4.4).
VALIDITY_TTL_SECONDS = 300


def canonicalize_jcs(obj: Dict[str, Any]) -> bytes:
    """Canonicalize a JSON object per RFC 8785 (JCS): sorted keys, no whitespace."""
    canonical_str = json.dumps(
        obj,
        sort_keys=True,
        ensure_ascii=False,
        separators=(',', ':')
    )
    return canonical_str.encode('utf-8')


# The 7 signed fields (signature excluded), per schema.
SIGNED_FIELDS = [
    "decision", "timestamp", "payload_hash", "evidence_references",
    "actor", "execution_outcome", "review_path"
]


def _unsigned_view(record: Dict[str, Any]) -> Dict[str, Any]:
    return {k: record[k] for k in SIGNED_FIELDS}


class ProofRecordGenerator:
    """Generates and signs ProofRecords per ARK-455b specification."""

    def __init__(self, seed: int = None):
        self.seed = seed if seed is not None else secrets.randbits(256)
        self.rng = secrets.SystemRandom(self.seed)
        seed_bytes = self.seed.to_bytes(32, 'big')
        self.signing_key = SigningKey(seed_bytes)
        self.verify_key = self.signing_key.verify_key

    def get_public_key_hex(self) -> str:
        return self.verify_key.encode(encoder=HexEncoder).decode('ascii')

    def generate_base_record(self, issued_offset_seconds: int = 0) -> Dict[str, Any]:
        """
        Generate a valid base ProofRecord.

        issued_offset_seconds: shift the issuance timestamp by this many seconds
        relative to now (negative = backdated). Used by Arm 9 to produce an
        expired-but-validly-signable record.
        """
        decisions = ["ALLOW", "DENY", "HOLD"]

        payload_bytes = secrets.token_bytes(32)
        payload_hash = hashlib.sha256(payload_bytes).hexdigest()

        issued = datetime.now(timezone.utc) + timedelta(seconds=issued_offset_seconds)
        timestamp = issued.isoformat().replace('+00:00', 'Z')

        evidence_count = self.rng.randint(1, 4)
        evidence_refs = [f"urn:evidence:{i:03d}" for i in range(evidence_count)]

        actor_id = self.rng.randint(1, 999)
        actor = f"system:authorizer:{actor_id:03d}"

        trace_id = self.rng.randint(1000, 9999)
        review_path = f"audit:trace:{trace_id}"

        decision = self.rng.choice(decisions)
        if decision == "ALLOW":
            execution_outcome = "executed"
        elif decision == "DENY":
            execution_outcome = "blocked"
        else:
            execution_outcome = "held"

        return {
            "decision": decision,
            "timestamp": timestamp,
            "payload_hash": payload_hash,
            "evidence_references": evidence_refs,
            "actor": actor,
            "execution_outcome": execution_outcome,
            "review_path": review_path
        }

    def sign_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Sign the 7-field record with Ed25519 over its JCS canonical form."""
        canonical_bytes = canonicalize_jcs(_unsigned_view(record))
        signed = self.signing_key.sign(canonical_bytes)
        signed_record = record.copy()
        signed_record['signature'] = signed.signature.hex()
        return signed_record

    def tamper_record(self, signed_record: Dict[str, Any], field: str) -> Dict[str, Any]:
        """
        Post-signing tamper: alter one field of an already-signed record. The
        signature is NOT recomputed, so a genuine change invalidates it.
        """
        tampered = signed_record.copy()

        if field == "decision":
            if tampered["decision"] == "ALLOW":
                tampered["decision"] = "DENY"
            elif tampered["decision"] == "DENY":
                tampered["decision"] = "ALLOW"
            else:
                tampered["decision"] = "ALLOW"

        elif field == "timestamp":
            # CORRECTED (ARK-455b): add a real 1 second via timedelta.
            # ARK-455 v1.0 used (microsecond + 1000000) % 1000000, a no-op.
            dt = datetime.fromisoformat(tampered["timestamp"].replace('Z', '+00:00'))
            dt = dt + timedelta(seconds=1)
            tampered["timestamp"] = dt.isoformat().replace('+00:00', 'Z')

        elif field == "payload_hash":
            h = tampered["payload_hash"]
            last_char = h[-1]
            new_char = '0' if last_char == 'f' else chr(ord(last_char) + 1)
            tampered["payload_hash"] = h[:-1] + new_char

        elif field == "evidence_references":
            refs = tampered["evidence_references"].copy()
            new_id = 900 + len(refs)
            refs.append(f"urn:evidence:{new_id:03d}")
            tampered["evidence_references"] = refs

        elif field == "actor":
            parts = tampered["actor"].split(':')
            num = int(parts[-1])
            parts[-1] = f"{(num + 1) % 1000:03d}"
            tampered["actor"] = ':'.join(parts)

        elif field == "execution_outcome":
            if tampered["execution_outcome"] == "executed":
                tampered["execution_outcome"] = "blocked"
            elif tampered["execution_outcome"] == "blocked":
                tampered["execution_outcome"] = "executed"
            else:
                tampered["execution_outcome"] = "executed"

        elif field == "review_path":
            parts = tampered["review_path"].split(':')
            num = int(parts[-1])
            parts[-1] = str((num + 1) % 10000)
            tampered["review_path"] = ':'.join(parts)

        return tampered

    # Arm specification (ARK-455b): arms 1-8 mirror ARK-455 (arm 3 corrected);
    # arm 9 is the new pre-signing expired-timestamp arm.
    ARMS = {
        1: {"label": "ACCEPT-original",           "target": None,               "mode": None},
        2: {"label": "REJECT-decision",           "target": "decision",         "mode": "post_sign"},
        3: {"label": "REJECT-timestamp-postsign", "target": "timestamp",        "mode": "post_sign"},
        4: {"label": "REJECT-payload_hash",       "target": "payload_hash",     "mode": "post_sign"},
        5: {"label": "REJECT-evidence_refs",      "target": "evidence_references","mode": "post_sign"},
        6: {"label": "REJECT-actor",              "target": "actor",            "mode": "post_sign"},
        7: {"label": "REJECT-outcome",            "target": "execution_outcome","mode": "post_sign"},
        8: {"label": "REJECT-review_path",        "target": "review_path",      "mode": "post_sign"},
        9: {"label": "REJECT-timestamp-presign-expired", "target": "timestamp", "mode": "pre_sign_expired"},
    }

    def generate_arm_records(self, arm_id: int, count: int = 100
                             ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Generate `count` records for an arm.

        Returns (records, audit) where audit[i] describes the mutation
        effectiveness for record i:
          - post_sign arms: mutation_effective = (canonical(tampered 7 fields)
            != canonical(original 7 fields))
          - pre_sign_expired arm: mutation_effective = (signed timestamp is more
            than VALIDITY_TTL_SECONDS before generation time)
          - control arm (1): mutation_effective = None (not applicable)
        """
        spec = self.ARMS[arm_id]
        target = spec["target"]
        mode = spec["mode"]

        records: List[Dict[str, Any]] = []
        audit: List[Dict[str, Any]] = []

        for _ in range(count):
            if mode == "pre_sign_expired":
                # Backdate BEFORE signing so the signature is valid over an
                # expired timestamp.
                offset = -(VALIDITY_TTL_SECONDS + 60)
                base = self.generate_base_record(issued_offset_seconds=offset)
                signed = self.sign_record(base)
                final = signed
                # Effectiveness: timestamp is out of window relative to now.
                ts = datetime.fromisoformat(final["timestamp"].replace('Z', '+00:00'))
                age = (datetime.now(timezone.utc) - ts).total_seconds()
                effective = age > VALIDITY_TTL_SECONDS
                audit.append({"mutation_effective": bool(effective),
                              "age_seconds_at_gen": age})

            elif mode == "post_sign":
                base = self.generate_base_record()
                signed = self.sign_record(base)
                before = canonicalize_jcs(_unsigned_view(signed))
                final = self.tamper_record(signed, target)
                after = canonicalize_jcs(_unsigned_view(final))
                effective = before != after
                audit.append({"mutation_effective": bool(effective)})

            else:  # control
                base = self.generate_base_record()
                final = self.sign_record(base)
                audit.append({"mutation_effective": None})

            records.append(final)

        return records, audit


if __name__ == "__main__":
    gen = ProofRecordGenerator(seed=42)
    print(f"Public key: {gen.get_public_key_hex()}")
    for arm_id in range(1, 10):
        recs, aud = gen.generate_arm_records(arm_id, count=3)
        eff = [a["mutation_effective"] for a in aud]
        print(f"Arm {arm_id} [{gen.ARMS[arm_id]['label']}] mutation_effective={eff}")
