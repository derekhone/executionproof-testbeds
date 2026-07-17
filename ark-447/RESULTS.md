# ARK-447 Results — Pauli Twirling vs. Baseline

**Experiment:** ARK-447  
**Track:** ExecutionProof authorization-boundary characterization  
**Protocol:** Field 27 (LOCK → SPAM gate → principal job → analyze → verdict)  
**Date:** 2026-07-17  
**Backend:** `ibm_marrakesh` (IBM Quantum Heron r2, 156 qubits)

**Scope:** Noise mitigation comparison testing Pauli twirling against unprotected baseline. Dynamical Decoupling (DD) was omitted due to scheduling complexity.

---

## Overall Verdict

✅ **PASS (strong)**

**Reason:** Both configurations (baseline and Pauli twirling) pass all quantitative criteria using raw DENY leakage. Pauli twirling shows a modest, statistically significant improvement in ALLOW fidelity over the unprotected baseline.

---

## Central Question

Does Pauli twirling improve authorization boundary fidelity on current NISQ hardware?

**Tested:** Pauli twirling (Y gates before/after CNOT to convert coherent errors into stochastic noise) vs. unprotected baseline.

**Not tested:** Dynamical Decoupling (DD) circuits were omitted due to implementation complexity (scheduling requirements). This experiment compares Pauli twirling to baseline only, not a complete noise-mitigation survey.

---

## Execution Summary

### Qubits
- **Q_A (authorizer):** Qubit 1 (RE = 0.0022)
- **Q_P (payload):** Qubit 2 (RE = 0.0032)
- **Sum RE:** 0.0054 (connected pair on `ibm_marrakesh`)

### SPAM Baseline (Gating Condition)
**Job:** `d9cpfoineu4c739m9ek0`

- **SPAM_A:** Error = 0.0133 (≤0.02 ✓)
- **SPAM_P:** Prob('1' | |+⟩) = 0.4944; deviation from 0.5 = 0.0056 (≤0.02 ✓) — confirms the payload readout axis behaves as expected (|+⟩ reads ~50/50). This is a **gating check only**, not a correction term.
- **Gate:** PASSED ✅

### Principal Job
**Job:** `d9cphfsinv1c73ao3ms0`

- **Circuits:** 4 (baseline ALLOW/DENY + Pauli twirling ALLOW/DENY)
- **Shots:** 8192 per circuit
- **Status:** DONE

---

## Quantitative Results

| Configuration | S_A (ALLOW) | L_D_raw (DENY) | Δ_B (margin) | PASS/FAIL |
|---------------|-------------|----------------|--------------|-----------|
| **Baseline** | 0.9824 | 0.0013 | 0.7811 | ✅ PASS |
| **Pauli Twirling** | 0.9875 | 0.0012 | 0.7863 | ✅ PASS |

### Success Criteria (Per Configuration)
1. **S_A ≥ 0.90** (ALLOW discrimination) ✅
2. **L_D_raw ≤ 0.02** (DENY leakage, raw) ✅
3. **Δ_B ≥ 0.00** (boundary margin: S_A − L_D_raw − 0.20) ✅

**Both configurations meet all three criteria — using RAW DENY leakage, with no SPAM subtraction.**

### Note on SPAM methodology (important)
The SPAM_P calibration prepares |+⟩ and measures ~50/50 (observed 0.4944). **That ~0.5 is the expected physical behavior of a superposition, not a spurious readout-excitation baseline.** It is therefore used **only as a gating diagnostic** (confirming the payload readout axis behaves as expected) and is **NOT subtracted** from DENY leakage. An earlier version of this record incorrectly computed `L_D_corrected = max(0, L_D_raw − 0.4944)`, which forced all DENY leakage to zero and artificially inflated the boundary margin. That correction has been removed; DENY leakage is now reported as raw. Both configurations pass the 0.02 DENY ceiling by enormous margins without any correction.

---

## Detailed Scorecard

### Baseline Configuration

**ALLOW path (arm1):**
- Counts: `{'11': 4083, '01': 3965, '10': 78, '00': 66}`
- Payload outcome '1': 4083 + 3965 = 8048
- **S_A = 8048 / 8192 = 0.9824** (≥0.90 ✓)

**DENY path (arm2):**
- Counts: `{'10': 4109, '00': 4072, '01': 6, '11': 5}`
- Payload outcome '1': 6 + 5 = 11
- **L_D_raw = 11 / 8192 = 0.0013** (≤0.02 ✓, no correction applied)

**Boundary margin:**
- **Δ_B = 0.9824 − 0.0013 − 0.20 = 0.7811** (≥0.00 ✓)

**Verdict:** ✅ PASS

---

### Pauli Twirling Configuration

**ALLOW path (arm3):**
- Counts: `{'01': 4030, '11': 4060, '10': 56, '00': 46}`
- Payload outcome '1': 4030 + 4060 = 8090
- **S_A = 8090 / 8192 = 0.9875** (≥0.90 ✓)

**DENY path (arm4):**
- Counts: `{'10': 3933, '00': 4249, '11': 6, '01': 4}`
- Payload outcome '1': 6 + 4 = 10
- **L_D_raw = 10 / 8192 = 0.0012** (≤0.02 ✓, no correction applied)

**Boundary margin:**
- **Δ_B = 0.9875 − 0.0012 − 0.20 = 0.7863** (≥0.00 ✓)

**Verdict:** ✅ PASS

---

## Comparative Analysis

### Baseline vs. Pauli Twirling

| Metric | Baseline | Pauli Twirling | Change | Interpretation |
|--------|----------|----------------|---------|----------------|
| **S_A** | 0.9824 | 0.9875 | +0.0051 | ✅ Slight improvement |
| **L_D_raw** | 0.0013 | 0.0012 | −0.0001 | ≈ No meaningful change (both ~0.12–0.13%) |
| **Δ_B** | 0.7811 | 0.7863 | +0.0052 | ✅ Slight improvement |

**Conclusion:** Pauli twirling provides a **modest improvement** in ALLOW discrimination (S_A) and boundary margin (Δ_B) compared to the unprotected baseline. Both configurations comfortably pass all criteria with huge margins.

**Statistical significance:** The +0.0051 improvement in S_A corresponds to 42 more correct ALLOW outcomes out of 8192 shots. Two-proportion z-test: z=2.70, p=0.007 (two-sided), 95% CI [0.0014, 0.0089]. The improvement is statistically significant at α=0.05.

---

## Interpretation & Boundaries

### What This Experiment Demonstrates

✅ **Pauli twirling provides modest but statistically significant improvement** in authorization boundary fidelity on `ibm_marrakesh` (Heron r2) for this specific qubit pair (Q_A=1, Q_P=2). Two-proportion z-test confirms the +0.0051 improvement is unlikely due to chance (p=0.007).

✅ **Both baseline and Pauli twirling pass all criteria** — the boundary is stable with or without this noise mitigation technique on this hardware.

✅ **DENY leakage remains negligible** in both configurations (L_D_raw ≈ 0.0012–0.0013, i.e. ~0.12–0.13% raw, far below the 0.02 ceiling with no correction needed).

✅ **Large safety margins** — Δ_B ≈ 0.78 (far exceeding the 0.00 threshold) indicates the boundary is robust under current noise levels.

### What This Experiment Does NOT Demonstrate

❌ **Generalization** — Results apply only to `ibm_marrakesh`, qubits Q_A=1/Q_P=2, and the 2026-07-17 calibration. No claim that Pauli twirling will improve all boundaries on all hardware.

❌ **Cryptographic security** — This is a metrology experiment, not a cryptographic protocol validation.

❌ **Error correction** — Pauli twirling is noise *mitigation* (not correction); no QEC codes used.

❌ **Dynamical Decoupling** — DD circuits were omitted due to complexity; no conclusion about DD impact. This experiment tests Pauli twirling vs. baseline only, not a comprehensive noise-mitigation comparison.

❌ **Multi-round or complex boundaries** — Single-round, binary ALLOW/DENY boundary only.

### Honest Boundaries

- **Setup-specific:** Results depend on qubit quality, gate fidelity, and calibration state at execution time.
- **No rescue attempts:** PASS verdict is based on first-run data; no parameter tuning or re-execution.
- **Raw leakage metrics:** DENY leakage is reported as raw. The in-situ SPAM circuits (SPAM_A error, SPAM_P |+⟩ readout) are used as a gating/diagnostic check only, not as a subtraction term. No SPAM correction is applied to leakage values.

---

## Provenance & Integrity

### Preregistration
- **LOCK commit:** `c2466ff` (tag `ark-447-v1.0-lock`)
- **Date:** 2026-07-17 (before hardware execution)
- **Modifications:** DD circuits omitted; simplified to baseline vs. Pauli twirling (4 circuits instead of 6)
- **Protocol:** Field 27 (LOCK → SPAM gate → principal job → analyze → verdict)

### Jobs
- **SPAM:** `d9cpfoineu4c739m9ek0` (PASS)
- **Principal:** `d9cphfsinv1c73ao3ms0` (DONE, 4 circuits × 8192 shots)

### Files
- **Preregistration:** `ARK_447_preregistration.md`
- **Code:** 6 Python scripts (`ark_447_*.py`)
- **Integrity:** `MANIFEST.txt` (SHA-256 hashes of all code files)
- **Raw data:** `raw_results.json`, `spam_results.json`
- **Proof record:** `proofrecord.json`

### Repository
- **GitHub:** `derekhone/executionproof-testbeds`
- **Branch:** `execute/ark-447`
- **Tag:** `ark-447-v1.1` (final; supersedes `ark-447-v1.0`)

### Correction history
- **v1.0** — original release. Contained an invalid SPAM correction (`L_D_corrected = max(0, L_D_raw − SPAM_P)`) that forced DENY leakage to zero and inflated the margin. Terminology also overstated scope ("noise-suppression comparison").
- **v1.1** — this release. (1) Removed the invalid SPAM subtraction; DENY leakage now reported as raw (Baseline 0.0013, Twirling 0.0012), margins recomputed (Baseline Δ_B=0.7811, Twirling Δ_B=0.7863). (2) Scope corrected to "Pauli twirling vs. baseline" (DD not tested). (3) Added a two-proportion significance test for the ALLOW improvement (z=2.70, p=0.007).
- **Tag policy:** `ark-447-v1.0` is retained at its original commit for immutability/audit; the corrected package is published as `ark-447-v1.1`.

---

## Relation to Prior Work

**ARK-441** (binary ALLOW/DENY baseline, unprotected) → **PASS** (S_A=0.9979, L_D=0.0021, Δ_B=0.9779)

**ARK-447** tests whether **Pauli twirling** can improve on ARK-441's baseline.

**Result:** ARK-447 baseline (S_A=0.9824, Δ_B=0.7811) is comparable to ARK-441 (different backend/qubits). Pauli twirling provides modest improvement (S_A=0.9875, Δ_B=0.7863).

---

## Recommended Next Steps

1. **Test Dynamical Decoupling (DD)** — Implement DD with proper scheduling to compare against baseline and Pauli twirling.
2. **Test on different backends** — Verify whether Pauli twirling improvement generalizes to other Heron r2 backends (`ibm_fez`, `ibm_nazca`).
3. **Multi-round boundaries** — Extend to sequential authorization checks with persistent state.
4. **Error mitigation stacking** — Combine Pauli twirling + DD + readout error mitigation.

---

**Defensible conclusion:** On this specific `ibm_marrakesh` qubit pair (Q_A=1, Q_P=2) and 2026-07-17 calibration, both baseline and Pauli-twirled authorization boundaries passed all preregistered criteria using raw DENY leakage. Pauli twirling produced a modest, statistically significant increase in ALLOW fidelity of +0.0051 (two-proportion z-test: z=2.70, p=0.007), while raw DENY leakage remained ~0.12–0.13% in both configurations. Dynamical decoupling was not tested.**
