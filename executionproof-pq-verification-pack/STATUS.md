# Status Declaration

```
pack:                     ExecutionProof Post-Quantum ProofRecord Verification Pack
claim_under_test:         hardware-backed ML-DSA-65 (FIPS 204) signing of ProofRecords
                          via AWS KMS, with real non-destructive key rotation
algorithm:                ML-DSA-65 (CRYSTALS-Dilithium), NIST FIPS 204, category 3
signing_custody:          aws-kms-native (AWS KMS FIPS 140-3 Level 3 HSM)
server_commit:            8eb9789af253703c83c90b80a334e37c274219fe
active_public_key_id:     00a69ffbb8a33217   (signs SHA-256 digest)
retired_public_key_id:    13757ac965b41061   (signed raw payload; not revoked)

verifier_self_test:       PASS
                          - 4 genuine vectors verify against published keys
                          - 3 failure vectors (tamper/forgery) are rejected
                          - exit 0 on this pack, exit 1 on any tamper
independent_impl_check:   PASS (dilithium-py agrees with @noble/post-quantum
                          and with the AWS KMS HSM signer — 3 implementations)

formal_RF100_8.4_status:  PENDING INDEPENDENT EXTERNAL REVIEW
scored_contribution:      0 (until a signed RUBRIC.md from an independent
                          reviewer with no stake in RF Inc. exists)
governing_rule:           when narrative and machine record disagree, the
                          machine record governs
```

## What is settled vs. what is open

**Settled (mechanically, in this pack):** the signing is real ML-DSA-65, the
signatures are produced under AWS KMS native hardware custody, verification
succeeds across three independent FIPS 204 implementations, tampering and
forgery are detected, and key rotation is non-destructive.

**Open (requires a human reviewer, not a machine):** whether the HSM custody,
rotation/revocation operations, publication path, and replay controls hold up
under adversarial review, and formal RF-100 §8.4 conformance sign-off. This pack
deliberately does **not** self-report §8.4 conformance. A machine cannot certify
its own independence; see `REVIEWER_TASKS.md` and `RUBRIC.md`.
