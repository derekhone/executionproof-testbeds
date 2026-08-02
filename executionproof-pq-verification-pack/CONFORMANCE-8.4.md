# RF-100 §8.4 Conformance Procedure

RF-100 §8.4 governs cryptographic sealing of ProofRecords: that every decision
is bound to a tamper-evident, independently verifiable signature under a
properly custodied key, with defined rotation and revocation behavior. This
document is the **step-by-step procedure** an assessor follows to determine
conformance. It maps each §8.4 requirement to a concrete, reproducible check in
this pack.

> This pack lets an assessor *perform* the §8.4 procedure. It does not, by
> itself, *declare* conformance — that is the assessor's signed judgement
> (`RUBRIC.md`). Until a signed rubric exists, §8.4 status is `PENDING`.

## Conformance checklist

| §8.4 requirement | Procedure | Artifact / task | Conformant if |
|------------------|-----------|-----------------|---------------|
| **8.4.1 Approved algorithm** | Confirm the signing algorithm is a NIST-approved post-quantum signature at the declared strength. | `canonicalization.md` §4; `public_keys/*` (`algorithm`, `standard`, `key_sizes_bytes`). | Algorithm is ML-DSA-65 / FIPS 204, key 1952 B, signature 3309 B, as published. |
| **8.4.2 Deterministic signed payload** | Confirm the signed bytes are defined by a published, deterministic canonicalization law. | `canonicalization.md` §1–2; `canonical_json()` in the verifier. | An independent reconstruction of the payload reproduces the signed bytes (Task 2). |
| **8.4.3 Independent verifiability** | Verify signatures with an implementation independent of the signer. | `independent_verifier.py` (dilithium-py) vs. server (`@noble/post-quantum`) vs. KMS HSM signer. | All three implementations agree on the same records (Task 1–2). |
| **8.4.4 Integrity / tamper-evidence** | Alter payloads and signatures; confirm rejection. | `vectors/failure/tampered_payload.json`, `tampered_signature.json`; Task 3. | Every alteration is rejected; verifier exits non-zero. |
| **8.4.5 Authenticity anchored to published keys** | Confirm a valid signature under a non-published key is rejected. | `vectors/failure/forged_unknown_key.json`; Task 4. | Trust is anchored to the published active/retired keys, not to "any valid signature". |
| **8.4.6 Key custody** | Confirm the private key is hardware-custodied and signing is not in-process. | `public_keys/pq-public-key-endpoint.json` `custody` block; live `/v2/crypto/pq-public-key`; Task 6. | `mode=aws-kms-native`, `hardware_backed=true`, `in_process_signing=false`; AWS KMS FIPS 140-3 L3 HSM. |
| **8.4.7 Rotation** | Confirm rotation is non-destructive — pre-rotation proofs stay verifiable under the retired key. | `vectors/valid/historical_retired_de196a09.json`; Task 5. | Historical record verifies under the retired key only; current records under the active key only. |
| **8.4.8 Revocation** | Confirm records under a revoked key are refused. | Set `revoked:true` and re-run; Task 5. | Verifier refuses records signed by a revoked key. |
| **8.4.9 Publication** | Confirm public keys are published and match what signed the records. | Diff `public_keys/` against the live endpoint; Task 6. | Published keys equal the live endpoint keys and verify the vectors. |
| **8.4.10 Honest scope statement** | Confirm the claim is stated no wider than the evidence. | `README.md` §2; `STATUS.md`; Task 6 write-up. | The claim says *tamper-evident under a hardware-held key*, not *proves the governance verdict / key secrecy / honest clock*. |

## Procedure summary

1. Run `independent_verifier.py` (8.4.1–8.4.5, mechanically).
2. Reproduce canonicalization independently (8.4.2–8.4.3).
3. Fetch live keys and read the custody block (8.4.6, 8.4.9).
4. Exercise rotation and revocation (8.4.7–8.4.8).
5. Write the honest-scope statement (8.4.10).
6. Record every verdict in `RUBRIC.md`, sign, and date.

A fully `PASS` and signed `RUBRIC.md` is the evidence of §8.4 conformance. Note
that §8.4 covers the **cryptographic seal**; replay/single-use enforcement and
governance-verdict correctness are covered by other RF-100 sections and are out
of scope here (see `REVIEWER_TASKS.md`).
