# ProofRecord Verification — AWS KMS ML-DSA-65 Custody Note

**Status date:** 2026-08-01
**Scope:** Newly generated production ProofRecords after activation of AWS KMS ML-DSA-65 signing.

ExecutionProof has implemented and internally verified hardware-backed ML-DSA-65 signing for newly generated ProofRecords using AWS KMS. A formal RF-100 §8.4 conformance claim remains pending independent external review.

## Production signing posture

The reported production posture is:

- `mode: aws-kms-native`
- `hardware_backed: true`
- `in_process_signing: false`
- signing occurs through the AWS KMS `Sign` operation;
- the private ML-DSA-65 key does not enter the application process;
- newly generated ProofRecords verify against the active HSM-backed key;
- historical ProofRecords remain verifiable through retired public keys;
- tampered ProofRecords fail verification;
- key rotation preserves the existing evidence chain.

## Digest handling

For ProofRecords larger than the KMS RAW-message limit, ExecutionProof signs a SHA-256 digest. This is reasonable for large canonical ProofRecord payloads, but independent external review should verify the precise digest boundary and context controls before any formal RF-100 §8.4 conformance claim is made.

The review packet should document and test:

1. the exact canonical ProofRecord payload that is hashed;
2. the deterministic canonical serialization rules;
3. the SHA-256 digest input bytes and output encoding;
4. the ML-DSA-65 / FIPS 204 algorithm identifiers;
5. signature and public-key encoding identifiers;
6. domain separation so a ProofRecord digest cannot be reused in another signing context;
7. replay protection and nonce/idempotency handling;
8. key-version binding in the ProofRecord signature metadata;
9. active public-key discovery;
10. historical public-key discovery for retired signing keys;
11. rotation, retirement, and revocation behavior;
12. tamper-failure behavior for modified ProofRecords.

## Verification behavior to preserve

A verifier should be able to reconstruct the canonical payload, compute the digest, resolve the correct public key by key ID/version, verify the ML-DSA-65 signature, and reject any record whose canonical payload, digest, signature metadata, public-key binding, replay status, or chain linkage has been altered.

## Non-claim boundary

This note is an implementation-status record. It does not assert formal RF-100 §8.4 conformance. Formal conformance remains pending independent external review.
