# Changelog

## 2026-08-01 — ExecutionProof PQ Custody v1.0

ExecutionProof has implemented and internally verified hardware-backed ML-DSA-65 signing for newly generated ProofRecords using AWS KMS.

Updated status language:

> ExecutionProof implements hardware-backed ML-DSA-65 post-quantum signing for ProofRecords through AWS KMS. Formal RF-100 §8.4 conformance remains pending independent external review.

More conservative wording for formal contexts:

> ExecutionProof has implemented and internally verified hardware-backed ML-DSA-65 signing for newly generated ProofRecords using AWS KMS. A formal RF-100 §8.4 conformance claim remains pending independent external review.

Notes:

- Hardened key custody is no longer described as pending.
- Independent external review remains pending.
- The milestone covers targeted PQ custody/sign-and-verify suites and the reported 33/33 acceptance gate, not a claim that the full 577-test suite ran.
- ProofRecord verification documentation has been added under `docs/proofrecord-verification.md`.
- API metadata expectations have been documented under `docs/crypto-api-metadata-contract.md`; the public `/v2/...` endpoints still need live deployment/routing if intended for public use.
