# Crypto API Metadata Contract

**Status date:** 2026-08-01

This document records the expected public metadata posture for ExecutionProof cryptographic signing endpoints. During this update, the public endpoints below returned 404 from `executionproof.io`, so this repository update documents the intended contract but does not claim the live endpoints were changed here.

Expected endpoints:

- `/v2/crypto-manifest`
- `/v2/crypto/pq-public-key`
- `/v2/version`

## Required common fields

The live metadata should consistently report:

```json
{
  "mode": "aws-kms-native",
  "hardware_backed": true,
  "in_process_signing": false,
  "signature_algorithm": "ML-DSA-65",
  "hash_algorithm": "SHA-256",
  "formal_conformance": "pending independent external review"
}
```

The endpoints should also expose or link to:

- active public-key ID / key version;
- retired public-key IDs still needed for historical ProofRecord verification;
- signature metadata schema and encoding identifiers;
- canonical payload hashing rules;
- rotation, retirement, and revocation behavior;
- verification guidance for newly generated and historical ProofRecords.

## Stale language to avoid

Do not state that formal conformance is pending "hardened key custody and independent review." Hardened AWS KMS custody is now reported as implemented. The accurate public statement is:

> ExecutionProof implements hardware-backed ML-DSA-65 post-quantum signing for ProofRecords through AWS KMS. Formal RF-100 §8.4 conformance remains pending independent external review.

A more conservative version is:

> ExecutionProof has implemented and internally verified hardware-backed ML-DSA-65 signing for newly generated ProofRecords using AWS KMS. A formal RF-100 §8.4 conformance claim remains pending independent external review.

## Live endpoint check performed during this update

The following URLs returned 404 when checked during this repository update:

- `https://executionproof.io/v2/crypto-manifest`
- `https://executionproof.io/v2/crypto/pq-public-key`
- `https://executionproof.io/v2/version`

Those live endpoints still need to be deployed or routed by the website/API project if they are intended to be public metadata endpoints.
