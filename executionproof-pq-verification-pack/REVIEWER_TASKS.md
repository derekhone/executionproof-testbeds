# Reviewer Tasks — the narrow, adversarial review scope

This review is intentionally **narrow**. It covers the post-quantum signing and
custody boundary only — not the whole ExecutionProof product, not the
governance verdicts, not an SLA. A reviewer who defeats any task below has
falsified part of the claim; a reviewer who cannot has confirmed that part.

For each task, record in `RUBRIC.md`: what you did, what happened, and
PASS / FAIL / PARTIAL in your own judgement, with a pointer to your evidence.

Tasks 1–2 confirm the system does what it claims. Tasks 3–6 are **attempts to
defeat it** — a boundary that holds makes these fail safely.

---

### Task 1 — Reproduce verification from scratch
Follow `SETUP.md` on a machine you control. Install `dilithium-py` (a FIPS 204
implementation you did not write and we do not maintain) and run
`independent_verifier.py`. **PASS if** every valid vector verifies, every
failure vector is rejected, and the script exits 0 — without editing any vector
or key file.

### Task 2 — Re-derive the canonicalization and signature yourself
Read `canonicalization.md` and `independent_verifier.py`. Using your **own**
code (do not import ours), reconstruct the canonical payload of at least one
record in `vectors/valid/`, apply the documented message binding
(SHA-256 digest for the active key; raw payload for the retired key), and verify
the ML-DSA-65 signature against the matching published key. **PASS if** your
independent reconstruction verifies. This is the core cross-implementation
claim: the AWS KMS HSM signer, the server's `@noble/post-quantum` verifier, and
your verifier must all agree on the same bytes.

### Task 3 — Tamper detection (integrity)
Edit any signed field of any record in `vectors/valid/` — flip a decision,
change an amount, alter an evidence reference — and re-run the verifier. Then
flip a single byte of a `proof_signature_pq` and re-run. **PASS if** both cases
are rejected and the script exits non-zero. (Worked examples: `vectors/failure/
tampered_payload.json` and `tampered_signature.json` are exactly these, prebuilt
from a genuine record.)

### Task 4 — Forgery under an unpublished key
Inspect `vectors/failure/forged_unknown_key.json`. It carries a **cryptographically
valid** ML-DSA-65 signature — but produced with a key that was never published.
Confirm the verifier rejects it because it does not match the active or any
retired published key. Then try your own: generate a fresh ML-DSA-65 keypair,
sign a record's canonical digest, drop it in `vectors/failure/`, and re-run.
**PASS if** every signature made under a non-published key is rejected — i.e.
trust is anchored to the *published* keys, not to "any valid signature".

### Task 5 — Rotation and revocation behavior
`vectors/valid/historical_retired_de196a09.json` is a **genuine pre-rotation**
ProofRecord pulled from the production store. Confirm it verifies **only** under
the retired key `13757ac965b41061` (over the raw payload) and **not** under the
active key, while the current records verify only under the active key
`00a69ffbb8a33217` (over the digest). Then simulate revocation: set
`"revoked": true` on a key in `public_keys/` (or the endpoint file) and confirm
the verifier refuses records under that key. **PASS if** rotation is
non-destructive (old proofs stay verifiable) **and** revocation is honored
(a revoked key's records are refused).

### Task 6 — Publication path and custody write-up
Fetch the live public keys yourself from `/v2/crypto/pq-public-key` on the
running service and diff them against `public_keys/`. Read the `custody` block:
`aws-kms-native`, `hardware_backed: true`, `in_process_signing: false`. Then
write one paragraph stating, in your own words, **what a valid signature does
and does not prove** here. **PASS if** the published keys match the live
endpoint **and** your write-up correctly says the system claims *tamper-evident
under a hardware-held key*, **not** that the signature proves the key was never
exportable, the clock was honest, or the governance verdict was correct.

---

## Out of scope for THIS pack (state honestly)

- **Replay / single-use enforcement** is a property of the ExecutionProof
  *enforcement layer* (single-use ProofRecord consumption + decision-token TTL),
  **not** of the signature. A signed record can be presented twice; it is the
  enforcement layer that must reject the second presentation. Reviewing that
  requires the running service, not this offline pack. Note it; do not score it
  here.
- HSM key non-exportability is an AWS KMS property attested by AWS FIPS 140-3
  Level 3 validation, not something this pack can prove by itself.
- The correctness of the governance decisions inside each ProofRecord is a
  separate review (the RF-100 gate-logic review), not this one.
