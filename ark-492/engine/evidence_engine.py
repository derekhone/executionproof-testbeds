#!/usr/bin/env python3
"""
ExecutionProof Evidence Engine (reference measurement implementation).

Answers the EVIDENCE half of Verification-Before-Execution:
  "Is there a complete, tamper-evident record proving the execution matched
   what was authorized — one that cannot be silently altered after the fact?"

This is a deliberately minimal, in-process reference implementation built to
MEASURE component performance (ARK-492). It is NOT the production Evidence
Engine; a production engine (durable append-only store, replication, external
notarization/timestamping) is out of scope for these performance testbeds and
belongs to a governed customer integration.

Design (honest and bounded):
  - Each ProofRecord binds (principal, action, authorization_ref, outcome).
  - Records form a hash chain: entry_hash = sha256(prev_hash || canonical(record)).
  - verify_record(i) recomputes the entry hash and checks it (a) matches the
    stored hash (tamper-evident) and (b) chains to the previous entry's hash.
  - Any mutation of a record's content, or any break in the chain, causes
    verification to FAIL. Exact, fail-closed. No normalization.
"""
import hashlib
import json
from typing import Dict, Any, List

GENESIS = "0" * 64


def _canonical(record: Dict[str, Any]) -> str:
    # Deterministic serialization of the content fields only (not the hashes).
    return json.dumps(
        {k: record[k] for k in ("principal", "action", "authorization_ref", "outcome")},
        sort_keys=True, separators=(",", ":"),
    )


def _entry_hash(prev_hash: str, record: Dict[str, Any]) -> str:
    return hashlib.sha256((prev_hash + _canonical(record)).encode("utf-8")).hexdigest()


class EvidenceEngine:
    def __init__(self) -> None:
        self._chain: List[Dict[str, Any]] = []

    def append(self, principal: str, action: str, authorization_ref: str, outcome: str) -> int:
        prev = self._chain[-1]["entry_hash"] if self._chain else GENESIS
        record = {
            "principal": principal,
            "action": action,
            "authorization_ref": authorization_ref,
            "outcome": outcome,
            "prev_hash": prev,
        }
        record["entry_hash"] = _entry_hash(prev, record)
        self._chain.append(record)
        return len(self._chain) - 1

    def verify_record(self, index: int) -> Dict[str, Any]:
        if index < 0 or index >= len(self._chain):
            return {"decision": "DENY", "reason": "No such evidence record"}
        rec = self._chain[index]
        # (a) tamper check: recomputed hash must match stored hash
        recomputed = _entry_hash(rec["prev_hash"], rec)
        if recomputed != rec["entry_hash"]:
            return {"decision": "DENY", "reason": "Evidence record tampered (hash mismatch)"}
        # (b) chain check: prev_hash must equal predecessor's entry_hash
        expected_prev = self._chain[index - 1]["entry_hash"] if index > 0 else GENESIS
        if rec["prev_hash"] != expected_prev:
            return {"decision": "DENY", "reason": "Evidence chain broken (prev_hash mismatch)"}
        return {"decision": "ALLOW", "reason": "Evidence record intact and correctly chained"}


def build_reference_engine(n_records: int = 10000) -> "EvidenceEngine":
    """Populate a deterministic reference evidence chain for measurement."""
    eng = EvidenceEngine()
    for i in range(n_records):
        eng.append(
            principal=f"user-{i % 1000:05d}",
            action=f"deploy:svc-{i % 50}",
            authorization_ref=f"auth-{i:07d}",
            outcome="executed",
        )
    return eng
