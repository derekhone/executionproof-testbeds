# ARK-452 — Multi-Step Workflow With One Invalid Step
**ExecutionProof ARK Authorization-Boundary Track**  
**Remnant Fieldworks Inc.**  
**Status:** 🔒 LOCKED AND READY FOR EXECUTION — no hardware job submitted yet.

---

## One-Line Summary

Verifies that in a sequential multi-step workflow, the ExecutionProof control model
blocks the irreversible execution step whenever **any** step in the chain is inadmissible —
and that prior valid steps do **not** confer inherited authorization on later steps.

**Doctrine tested:**
> Prior valid steps in a workflow are not a blank check. The irreversible execution
> step must be independently authorized, or it fails closed.

---

## Where This Fits

ARK-449 established the single-action state-change boundary (authorization must remain
valid at execution time). ARK-452 extends that boundary to **sequential multi-step
workflows**: each step carries an independent authorization requirement, and the
irreversible execution step (step 4 of a 5-step chain) cannot inherit authorization
from the steps that preceded it.

| Dimension | ARK-449 | ARK-452 |
|---|---|---|
| Action structure | Single action | Sequential 5-step workflow |
| Authorization model | One approval, one re-check | Independent per-step authorization |
| Failure mode tested | State change between approval and execution | One invalid step in a multi-step chain |
| Key claim | Authorization currency expires with world state | Prior valid steps ≠ blanket authorization |

---

## Experiment Design

- **Qubits:** one payload qubit `Q_P`. No authorizer qubit — step authorizations are
  classical per-arm constants, so there is nothing to measure on a second qubit.
- **Execution gate:** `X` on `Q_P` iff `c_exec = c_s1 AND c_s2 AND c_s3 AND c_s4`.
  ALLOW → P(Q_P=1) ≈ 1.00; DENY → P(Q_P=1) ≈ 0.00.
- **Arms:** 9 arms × 8192 shots (single principal job). Two ALLOW arms (1, 8), seven
  DENY arms (2–7, 9) covering every invalid-step position plus the blanket-auth and
  skip-approval attack patterns.
- **SPAM gate:** single `|+⟩` symmetry check on `Q_P` (2048 shots), `SPAM_P ≤ 0.02`.
  Gating diagnostic only — never subtracted from leakage.

### Analysis doctrine (raw-primary)

ARK-452 uses **one qubit only**, so there is **no SPAM_A authorizer-readout correction**
and none is applied. The **raw** payload retention P(Q_P=1) is the primary and only metric
for both ALLOW (S_A) and DENY (L_D). This deliberately avoids the ARK-449 v1.1 error of
applying an authorizer-qubit readout correction to a payload outcome (corrected in
ARK-449 v1.2). `SPAM_P` gates the run; it is never subtracted from `L_D`.

---

## Pass / Fail Criteria (preregistered — Section 9)

| # | Criterion | Threshold | Arms |
|---|---|---|---|
| C1 | S_A_min — minimum ALLOW retention | ≥ 0.90 | 1, 8 |
| C2 | L_D_max — maximum DENY leakage | ≤ 0.02 | 2, 3, 4, 5, 6, 7, 9 |
| C3 | Δ_B = S_A_min − L_D_max | ≥ 0.70 | Derived |
| C4 | SPAM gate — SPAM_P | ≤ 0.02 | Pre-principal |

All four must hold simultaneously for a PASS. A FAIL that pinpoints the breaching arm
is worth more than a marginal pass. An ABORT at the SPAM gate is a valid outcome.

---

## Files

```
ark-452/
├── ARK_452_preregistration.md      Locked preregistration (+ .pdf/.docx)
├── MANIFEST.txt                    SHA-256 lock manifest (this lock)
├── README.md                       This file
├── circuits/
│   ├── ark_452_circuit.py          Circuit build + hardware submission + dry-run
│   └── ark_452_analysis.py         Raw-primary verdict computation
└── results/                        (populated at execution time)
```

## Reproduce the dry-run

```bash
cd ark-452
python3 circuits/ark_452_circuit.py --dry-run
```

Expected (noiseless): ALLOW arms (1, 8) → 1.0000, all seven DENY arms → 0.0000,
SPAM gate passes.

## Execution sequence (on hardware — after lock)

1. Commit + tag `ark-452-v1.0-lock`.
2. `python3 circuits/ark_452_circuit.py` — selects qubit, submits SPAM gate, submits
   principal job, commits job IDs before reading results, applies the SPAM gate.
3. `python3 circuits/ark_452_analysis.py` — computes the raw-primary verdict and writes
   `results/proofrecord.json`.

> **Budget note:** ARK-452 has not been submitted to hardware. IBM QPU budget is tight;
> the package is locked and ready so execution can proceed the moment budget is confirmed.
