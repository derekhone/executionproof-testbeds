# ARK-455 — ProofRecord Verification After Tampering

> ## ⚠️ CORRECTION / ERRATUM v1.1 (2026-07-17)
> A post-publication source audit resolved the ambiguity flagged in the
> Conclusion below. The Arm-3 (timestamp) FAIL was caused by a **test-harness
> no-op** — the timestamp "tamper" `(microsecond + 1000000) % 1000000` never
> changed the record, so both verifiers correctly accepted unaltered inputs. It
> is **not** a verifier defect and **not** a signed-payload/spec gap: the
> timestamp *is* in the JCS-signed form and both verifiers *do* check it.
> **The FAIL verdict stands as recorded; only its root cause is reclassified.**
> See [`CORRECTION.md`](./CORRECTION.md). Follow-up: [`../ark-455b/`](../ark-455b/).

**Status:** LOCKED → Executed (FAIL, v1.0) → Corrected (v1.1 erratum)

**Question:** Can an independent verifier detect every tampering attempt in a ProofRecord and reject altered records while accepting the original?

**Substrate:** Classical software (local execution, no IBM QPU)

**Locked:** 2026-07-17 (tag `ark-455-v1.0-lock`)

---

## Experiment Overview

ARK-455 tests whether dual independent verifiers (V1 in JavaScript, V2 in Python), built from the same prose specification with no shared source code, can:

1. **ACCEPT** original valid signed ProofRecords (≥95% acceptance rate)
2. **REJECT** tampered records where exactly one field was altered post-signing (≥95% rejection rate across all 7 tampering targets)
3. **Agree** with each other on verification outcomes (≥99% concordance during kill-gate calibration)

This is the first ARK experiment to validate the **commercial ProofRecord artifact** that external auditors would inspect.

---

## Three Possible Verdicts

- **PASS:** All criteria met (V_accept ≥ 0.95, V_reject_min ≥ 0.95, V_margin ≥ 0.85, kill-gate passed)
- **FAIL:** Kill-gate passed but at least one criterion failed
- **KILLED:** Kill-gate failed (V1-V2 concordance < 99% OR sanity check failed)

---

## Files

- `PREREGISTRATION.md` — Full experimental specification (locked before execution)
- `MANIFEST.txt` — SHA-256 hashes of all locked files
- `schemas/proofrecord_schema.json` — ProofRecord JSON schema (7 required fields, Ed25519 signature)
- `generator/record_generator.py` — Generates valid signed records and tampered variants
- `verifiers/v1_verifier.js` — Independent verifier V1 (JavaScript/Node.js)
- `verifiers/v2_verifier.py` — Independent verifier V2 (Python, built from spec only, isolated from V1)
- `results/` — Execution data (generated during run)

---

## Execution Notes

**Kill-gate calibration:** ✅ PASSED (100% V1-V2 concordance, both verifiers accepted all 50 valid records)

**Arms executed:** All 8 arms (100 records each, 800 total records)

**Verdict:** ❌ **FAIL** — Timestamp field tampering (Arm 3) was NOT detected by either verifier (0% rejection rate). Six other tampering targets detected with 100% reliability.

---

## Connection to Corpus

ARK-455 is the first experiment to connect the research program directly to the independently verifiable ProofRecord artifact that enterprise buyers demand. Prior experiments (ARK-441 through ARK-452) established authorization boundaries on IBM quantum hardware. ARK-455 validates the **audit trail** — can external parties verify records after issuance?

---

*Remnant Fieldworks Inc. — ExecutionProof ARK Series*  
*Repository: https://github.com/derekhone/executionproof-testbeds*
