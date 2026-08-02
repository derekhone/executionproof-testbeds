# ExecutionProof PQ Custody v1.0 — AWS KMS ML-DSA-65

**Status date:** 2026-08-01

ExecutionProof has implemented and internally verified hardware-backed ML-DSA-65 signing for newly generated ProofRecords using AWS KMS.

## What changed

- Production ProofRecords are signed through the AWS KMS `Sign` operation.
- The private ML-DSA-65 signing key does not enter the application process.
- Production reports `hardware_backed = true`.
- Production uses `mode: aws-kms-native`.
- Production disables in-process signing for newly generated ProofRecords.
- New ProofRecords verify against the active HSM-backed key.
- Historical ProofRecords remain verifiable through retired public keys.
- Tampered ProofRecords fail verification.
- Key rotation preserves the existing evidence chain.

## Test scope

This milestone covers targeted post-quantum custody/sign-and-verify suites and the reported **33/33 acceptance gate**. It does not claim that the full 577-test suite was run for this milestone unless separately documented.

## Conformance boundary

ExecutionProof implements hardware-backed ML-DSA-65 post-quantum signing for ProofRecords through AWS KMS. Formal RF-100 §8.4 conformance remains pending independent external review.

External review should confirm:

- exactly which canonical payload is hashed;
- deterministic canonical serialization;
- SHA-256 digest handling for ProofRecords larger than the KMS RAW-message limit;
- algorithm and encoding identifiers;
- domain separation;
- replay protection;
- key-version binding;
- active and retired public-key discovery;
- rotation, retirement, and revocation behavior.
