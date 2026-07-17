# ARK-455b — ProofRecord Verification After Tampering (Corrected Retest + Validity Window)

**Status:** LOCKED → Executed → ✅ **PASS** (see [`RESULTS.md`](./RESULTS.md))

**Question:** Can dual independent verifiers reject *every* tampered ProofRecord **and** every out-of-window (expired) record, while accepting only genuine, in-window originals?

**Substrate:** Classical software (local execution, no IBM QPU)

**Locked:** 2026-07-17

**Predecessor:** [ARK-455](../ark-455/) executed a **FAIL** whose root cause was a
test-harness no-op in the Arm-3 timestamp tamper (see
[`../ark-455/CORRECTION.md`](../ark-455/CORRECTION.md)). ARK-455b is the corrected
retest.

---

## Why ARK-455b Exists

ARK-455's Arm-3 timestamp "tamper" was `(microsecond + 1000000) % 1000000` — a
mathematical **no-op** that never changed the record. Both verifiers correctly
accepted unaltered inputs; the 0% "detection" was an artifact of a defect in the
generator, **not** the verifier and **not** the specification. The timestamp *is*
part of the signed payload and both verifiers *do* check it.

ARK-455b fixes the cause and hardens the spec:

1. **Real Arm-3 tamper** — `+1 second` via `timedelta` (changes signed bytes).
2. **New Arm 9** — timestamp backdated beyond the validity window **before**
   signing: signature valid, record expired. Tests temporal validity that a bare
   signature check cannot catch (expiry per ARK-442).
3. **Validity-window gate (Gate B)** in both verifiers — ACCEPT requires a valid
   signature AND an in-window timestamp.
4. **Mutation-effectiveness gate** — every REJECT-arm record must carry an
   effective mutation, else the run aborts. A no-op can never again be scored as
   a detection failure.

---

## Design

- **9 arms × 100 records = 900 records.**
  - Arm 1: valid, in-window control → expect ACCEPT.
  - Arms 2–8: post-signing single-field tampers → expect REJECT (Gate A).
  - Arm 9: pre-signing expired timestamp, valid signature → expect REJECT (Gate B).
- **Dual verifiers:** V1 (JavaScript), V2 (Python), independent implementations
  from the prose spec only.
- **Validity TTL:** 300 seconds.

## Verdicts

- **PASS:** C1 `V_accept_original ≥ 0.95`, C2 `V_reject_min ≥ 0.95` (arms 2–9),
  C3 `V_margin ≥ 0.85`, kill-gate passed.
- **FAIL:** kill-gate passed but a criterion missed (published as executed).
- **KILLED:** kill-gate failed (concordance < 99%, sanity fail, or ineffective
  mutation detected).

---

## Files

- `PREREGISTRATION.md` — full specification, locked before execution.
- `MANIFEST.txt` — SHA-256 hashes of all locked files.
- `schemas/proofrecord_schema.json` — schema v1.1 (adds validity-window notes).
- `generator/record_generator.py` — corrected generator (real Arm-3 tamper, Arm 9, mutation audit).
- `verifiers/v1_verifier.js` — independent verifier V1 (JavaScript), two-gate.
- `verifiers/v2_verifier.py` — independent verifier V2 (Python), two-gate.
- `run_killgate.py` — kill-gate calibration (concordance + sanity + mutation-effectiveness).
- `run_arms.py` — 9-arm execution + metrics + verdict.
- `compute_hashes.sh` — regenerate MANIFEST hashes.
- `results/` — execution data (generated during run).

## Reproduce

```bash
cd ark-455b
pip install -r ../requirements.txt   # pynacl
npm install                          # tweetnacl
python3 run_killgate.py              # must PASS to proceed
python3 run_arms.py                  # writes results/ and prints verdict
```

---

*Remnant Fieldworks Inc. — ExecutionProof ARK Series*
*Repository: https://github.com/derekhone/executionproof-testbeds*
