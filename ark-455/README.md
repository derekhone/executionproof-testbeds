# ARK-455 — ProofRecord Verification After Tampering

**Status:** LOCKED → Execution in progress

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

**Kill-gate calibration:** [TO BE FILLED]

**Arms executed:** [TO BE FILLED]

**Verdict:** [TO BE FILLED]

---

## Connection to Corpus

ARK-455 is the first experiment to connect the research program directly to the independently verifiable ProofRecord artifact that enterprise buyers demand. Prior experiments (ARK-441 through ARK-452) established authorization boundaries on IBM quantum hardware. ARK-455 validates the **audit trail** — can external parties verify records after issuance?

---

*Remnant Fieldworks Inc. — ExecutionProof ARK Series*  
*Repository: https://github.com/derekhone/executionproof-testbeds*
