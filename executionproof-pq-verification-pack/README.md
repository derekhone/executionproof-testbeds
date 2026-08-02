# ExecutionProof — Post-Quantum ProofRecord Verification Pack

**A fixed, self-contained, offline object that lets anyone mechanically verify
the post-quantum signing claim for ExecutionProof ProofRecords — without
talking to the people who built it.**

```
claim under test:   ExecutionProof implements hardware-backed ML-DSA-65
                    (NIST FIPS 204) post-quantum signing for ProofRecords
                    through AWS KMS, with real, non-destructive key rotation.
verifier self-test: PASS  (independent_verifier.py, exit 0 on this pack)
signing custody:    aws-kms-native (AWS KMS FIPS 140-3 Level 3 HSM)
server commit:      8eb9789af253703c83c90b80a334e37c274219fe
formal §8.4 status: PENDING INDEPENDENT EXTERNAL REVIEW
```

---

## 1. What this pack is

A critic can reasonably say: *"You told me a protected key signed a payload.
So what? Show me a fixed carrier I can run."* This pack is that carrier.

It contains the published public keys, a set of **genuine production-signed
ProofRecords**, deliberate **failure cases** (tampered payload, tampered
signature, forgery under an unpublished key), a **real key-rotation vector**
pulled from the production database, the exact **canonicalization law**, and a
single script — `independent_verifier.py` — that checks all of it using a
**third-party** FIPS 204 implementation (`dilithium-py`, pure Python) that is
**not** the library ExecutionProof uses to sign or verify.

Run one command. Either every genuine record verifies and every bad record is
rejected (exit 0), or it does not (exit non-zero). No trust in us is required.

## 2. What it proves — and what it does NOT

**Proven, mechanically, by this pack (using only the published keys):**

1. Each ProofRecord in `vectors/valid/` carries a genuine ML-DSA-65 signature
   that verifies against a **published** key, over the documented message
   binding for that key's custody mode.
2. Each ProofRecord in `vectors/failure/` **fails** to verify — a payload
   altered after signing, a signature with a flipped byte, and a technically
   valid signature made under a key that was never published are all rejected.
3. Key rotation is **real and non-destructive**: a genuine pre-rotation record
   verifies only under the *retired* key and not the active one; current
   records verify only under the *active* key. Old proofs stay verifiable.
4. **Cross-implementation agreement.** The signature is produced inside an AWS
   KMS HSM; the ExecutionProof server verifies it with `@noble/post-quantum`
   (JavaScript); this pack confirms the same bytes with `dilithium-py`
   (Python). Three independent FIPS 204 implementations agree.

**NOT proven by a valid signature — and we say so plainly:**

- A signature is a **tamper-evident seal** over the ProofRecord. It proves the
  record was authored by the holder of that key and has not changed since. It
  does **not** prove the governance verdict inside the record (authority,
  evidence, constraint, decision, execution) is itself *correct*. Signing binds
  integrity, not judgement.
- It does not, by itself, prove the HSM private key was never exportable, that
  the signing clock was honest, or that the surrounding infrastructure is
  production-grade. Those are **review questions**, not signature properties —
  see `REVIEWER_TASKS.md` and `CONFORMANCE-8.4.md`.

> Governing rule (inherited from the whole RF corpus): **when the narrative and
> the machine record disagree, the machine record governs.** If anything in
> this README overstates what the artifacts show, believe the artifacts.

## 3. Files

| Path | Purpose |
|------|---------|
| `README.md` | This overview. |
| `SETUP.md` | Install and run in under a minute. |
| `independent_verifier.py` | Self-contained verifier (third-party FIPS 204 lib). |
| `requirements.txt` | The one dependency (`dilithium-py`). |
| `canonicalization.md` | The exact serialization + message-binding law. |
| `public_keys/` | Published active + retired ML-DSA-65 public keys. |
| `vectors/valid/` | Genuine production-signed ProofRecords (must verify). |
| `vectors/failure/` | Tamper / forgery cases (must be rejected). |
| `vectors/MANIFEST.json` | Every vector + its expected result. |
| `CONFORMANCE-8.4.md` | RF-100 §8.4 conformance procedure. |
| `REVIEWER_TASKS.md` | The narrow, adversarial review scope. |
| `RUBRIC.md` | Human-scored pass/fail rubric (starts NOT-EVALUATED). |
| `STATUS.md` | Machine-readable status declaration. |
| `LICENSE` | Usage terms. |

## 4. How to use it (30 seconds)

```bash
pip install -r requirements.txt
python3 independent_verifier.py
echo "exit code: $?"      # 0 == all checks passed
```

Then, to satisfy yourself it is not self-graded trickery:

1. Read `independent_verifier.py` and `canonicalization.md`; re-derive one
   record's canonical payload and signature check with your own code.
2. Break something on purpose — edit any field of any file in `vectors/valid/`
   and re-run. It must now report a `[FAIL]` and exit non-zero.
3. Fetch the live public keys yourself from the running service endpoint
   `/v2/crypto/pq-public-key` and confirm they match `public_keys/`.
4. Work through `REVIEWER_TASKS.md` and record findings in `RUBRIC.md`.

## 5. Provenance

- **Algorithm:** ML-DSA-65 (CRYSTALS-Dilithium), NIST FIPS 204, security
  category 3. Public key 1952 B, signature 3309 B.
- **Active key id:** `00a69ffbb8a33217` — signs `SHA-256(canonical_payload)`.
- **Retired key id:** `13757ac965b41061` — signed the raw canonical payload
  (in-process software custody, pre-rotation), not revoked, still verifiable.
- **Source:** ExecutionProof / Remnant Fieldworks Inc. ProofRecords in
  `vectors/valid/` were produced by the live service and (for the historical
  vector) pulled directly from the production ProofRecord store.

ExecutionProof™ and Proof Before Power™ are trademarks of Remnant Fieldworks
Inc. Creator: Derek Hone.
