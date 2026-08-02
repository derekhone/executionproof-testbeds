# Changelog

## v1.1.0 (2026-08-02)

**Minimized the test vectors to exactly what verification requires.**

Each ProofRecord vector now contains only: the 22 canonical signed fields (see
`canonicalization.md`), the post-quantum signature triple
(`proof_signature_pq`, `signature_algorithm_pq`, `pq_public_key_id`), and
provenance identifiers (`proof_id`, `created_at`, `previous_proof_id`). Failure
vectors additionally keep their `_failure_kind` / `_expected` annotations.

Removed fields that the offline verifier never reads and that carried internal
or operational detail rather than anything needed to check a signature:
`receipts`, `policy_snapshot`, `proof_signature`, `signature_algorithm`,
`proof_signature_secondary`, `signature_algorithm_secondary`,
`idempotency_key`, `invalidated`, `invalidated_by`, `invalidated_at`.

The verifier still exits 0 on the trimmed pack — which demonstrates these fields
were never part of the verifiable claim. The signed fields (including
`coherence_envelope` and `audit_trail`) are unchanged, because a signature can
only be checked against the exact bytes that were signed.

No cryptographic material, canonicalization rule, key, or expected result
changed. `SHA256SUMS.txt` regenerated to match.

## v1.0.0 (2026-08-02)

Initial release: independent FIPS 204 verifier (`dilithium-py`), production
ML-DSA-65 signed vectors, tamper/forgery/rotation failure cases, canonicalization
law, RF-100 §8.4 conformance procedure, and reviewer packet.
