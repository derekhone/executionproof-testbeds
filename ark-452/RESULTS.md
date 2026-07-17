# ARK-452 — Results

**Multi-Step Workflow With One Invalid Step**
**ExecutionProof ARK Authorization-Boundary Track — Remnant Fieldworks Inc.**

**Status:** ✅ **PASS** — executed on IBM Quantum `ibm_marrakesh` (156-qubit Heron r2), 2026-07-17.

---

## Verdict

**PASS** — all four preregistered criteria met simultaneously (raw-primary analysis).

| # | Criterion | Threshold | Value | Result |
|---|---|---|---|---|
| C1 | S_A_min — minimum ALLOW retention | ≥ 0.90 | **0.9392** | ✅ |
| C2 | L_D_max — maximum DENY leakage | ≤ 0.02 | **0.0017** | ✅ |
| C3 | Δ_B = S_A_min − L_D_max | ≥ 0.70 | **0.9375** | ✅ |
| C4 | SPAM gate — SPAM_P | ≤ 0.02 | **0.0073** | ✅ |

> **Analysis doctrine: raw-primary.** ARK-452 uses a single payload qubit, so there is
> no authorizer-qubit SPAM_A correction and none is applied. Raw payload retention
> P(Q_P=1) is the primary and only metric for both S_A and L_D. `SPAM_P` gates the run
> and is never subtracted from `L_D`. This deliberately avoids the ARK-449 v1.1 error
> (applying an authorizer readout correction to a payload outcome), corrected in ARK-449 v1.2.

---

## Per-Arm Results (raw P(Q_P=1), 8192 shots each)

| Arm | Label | S1 S2 S3 S4 | c_exec | Role | counts(0) | counts(1) | P(Q_P=1) | Expected | Result |
|---|---|---|---|---|---|---|---|---|---|
| 1 | ALLOW-complete | 1 1 1 1 | 1 | ALLOW | 496 | 7696 | **0.9395** | ≥ 0.90 | ✅ |
| 2 | DENY-s1-invalid | 0 1 1 1 | 0 | DENY | 8179 | 13 | 0.0016 | ≈ 0.00 | ✅ |
| 3 | DENY-s2-invalid | 1 0 1 1 | 0 | DENY | 8179 | 13 | 0.0016 | ≈ 0.00 | ✅ |
| 4 | DENY-s3-invalid | 1 1 0 1 | 0 | DENY | 8187 | 5 | 0.0006 | ≈ 0.00 | ✅ |
| 5 | DENY-s4-invalid | 1 1 1 0 | 0 | DENY | 8178 | 14 | 0.0017 | ≈ 0.00 | ✅ |
| 6 | DENY-s2s3-both | 1 0 0 1 | 0 | DENY | 8182 | 10 | 0.0012 | ≈ 0.00 | ✅ |
| 7 | DENY-blanket-attempt | 1 1 1 0 | 0 | DENY | 8178 | 14 | 0.0017 | ≈ 0.00 | ✅ |
| 8 | ALLOW-reauth-complete | 1 1 1 1 | 1 | ALLOW | 498 | 7694 | **0.9392** | ≥ 0.90 | ✅ |
| 9 | DENY-skip-approval | 1 1 0 0 | 0 | DENY | 8179 | 13 | 0.0016 | ≈ 0.00 | ✅ |

**ALLOW retention:** Arm 1 = 0.9395, Arm 8 = 0.9392 (S_A_min = 0.9392).
**DENY leakage:** all seven DENY arms in the range 0.0006–0.0017 (L_D_max = 0.0017, arm 5).
**Boundary separation:** Δ_B = 0.9375 — a wide, commercially meaningful margin.

---

## What the Result Establishes

Every hypothesis in the preregistration is supported on hardware:

- **H1 (primary):** the irreversible execution step (S4) executes only when all four step
  authorizations are valid, and is blocked whenever any step is inadmissible. Confirmed.
- **H2a (step-position universality):** the position of the invalid step is irrelevant —
  S1 (arm 2), S2 (arm 3), S3 (arm 4), S4 (arm 5), and multi-step (arm 6) all fail closed
  at ≤ 0.17% leakage.
- **H2b (no inherited authorization):** three valid prior steps do **not** authorize the
  execution step. The blanket-authorization attempt (arm 7) fails closed at 0.17%.
- **H2c (re-authorization restores execution):** a fully re-authorized workflow (arm 8)
  executes normally at 0.9392 — the control model is not a one-way block.
- **H2d (skip-approval attack fails closed):** presenting an execution attempt while
  skipping the approval step (arm 9) fails closed at 0.16%; execution authority cannot
  substitute for a missing approval.
- **H2e (boundary separation):** Δ_B = 0.9375 ≫ 0.70.

The lower ALLOW retention versus the noiseless dry-run (0.94 vs 1.00) reflects device
readout/gate noise on Q_P — it does not approach the C1 threshold and the boundary
separation remains wide.

### Interpretation boundary (what ARK-452 does and does not establish)

ARK-452 demonstrated that a preregistered execution-control boundary enforces **step-level
admissibility** across a sequential workflow encoded through the **same deterministic
classical control logic**: the four step-authorization bits were classical per-arm constants,
and the AND-gated execution decision was baked into each circuit at build time. It validates
the **control logic** — that any single inadmissible step halts the irreversible step and that
prior valid steps confer no inherited authorization — **not** live multi-service orchestration,
real inter-step data flow, or runtime feedforward between measured quantum steps. The
circuit-equivalent arms (5/7 and 1/8) are semantically distinct but hardware-identical; they
test the granularity and framing of the boundary, not distinct physical mechanisms.

---

## Provenance

- **Backend:** IBM Quantum `ibm_marrakesh` (156-qubit Heron r2)
- **Payload qubit Q_P:** index **1**, readout error **0.0022** (≤ 0.02 constraint met);
  calibration snapshot 2026-07-17 05:54:26 UTC
- **Job IDs:** SPAM `d9cspi4inv1c73ao83ng`, principal `d9cspicjeosc73fgnti0`
- **Shots:** SPAM 2,048; principal 9 × 8,192 = 73,728 (total 75,776)
- **SPAM gate:** SPAM_P = 0.0073 (passed) — read and evaluated only after both job IDs
  were committed to git (prereg Section 8.1)
- **Lock tag:** `ark-452-v1.0-lock` · **Result tag:** `ark-452-v1.0`
- **Analysis:** `circuits/ark_452_analysis.py` (locked at lock; run unmodified on hardware data)
- **Hardware runner:** `circuits/ark_452_run_hardware.py` (post-lock operational harness;
  imports the locked circuit/analysis functions unchanged and enforces submit → commit →
  retrieve ordering)

### Files
```
results/selected_qubit.json     Q_P selection (committed before SPAM submission)
results/execution_log.json      Both job IDs (committed before reading any results)
results/spam_results.json       SPAM gate outcome
results/raw_results.json        Raw per-arm counts
results/analysis_results.json   Full metrics + criteria
results/proofrecord.json        Signed-off verdict record
```
