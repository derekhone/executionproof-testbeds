# ARK-447 Preregistration — Noise-Suppression Comparison: Dynamical Decoupling and Pauli Twirling

**Experiment ID:** ARK-447  
**Track:** ExecutionProof authorization-boundary characterization  
**Status:** PREREGISTRATION (not yet executed)  
**Protocol:** Field 27 (LOCK → SPAM gate → principal job → analyze → verdict)  
**Target backends:** `ibm_marrakesh` or `ibm_fez` (IBM Quantum Heron r2)  
**Date preregistered:** 2026-07-17  
**Principal investigator:** Derek Hone, Remnant Fieldworks Inc.

---

## 1. Central Question

**Do noise-mitigation strategies improve authorization boundary fidelity on current NISQ hardware?**

Specifically: When applying **dynamical decoupling (DD)** or **Pauli twirling** to the idle periods and gates of a binary ALLOW/DENY authorization boundary, do we observe:
- Improved ALLOW discrimination (higher S_A)?
- Reduced DENY leakage (lower L_D)?
- Comparable or better performance vs. the unprotected baseline?

This experiment tests whether standard noise-mitigation techniques can strengthen authorization boundaries without introducing new failure modes.

---

## 2. Background & Motivation

### 2.1 Baseline: ARK-441
ARK-441 established a binary ALLOW/DENY boundary on `ibm_kingston` (PASS verdict):
- **S_A** (ALLOW discrimination) = 0.9979 (raw)
- **L_D** (DENY leakage, SPAM-corrected) = 0.0021
- **Δ_B** (boundary margin) = 0.9779

This was an **unprotected** baseline — no noise mitigation applied.

### 2.2 Noise on NISQ Hardware
IBM Quantum Heron r2 backends exhibit:
- **Decoherence** (T1, T2) during idle periods
- **Gate errors** (depolarizing-like noise on single-qubit and two-qubit gates)
- **Readout (SPAM) errors** (mitigated via baseline jobs)

### 2.3 Noise-Mitigation Techniques
Two standard techniques:
1. **Dynamical Decoupling (DD):** Insert sequences of π-pulses (X gates) during idle periods to average out low-frequency noise and extend coherence.
2. **Pauli Twirling:** Randomize single-qubit Pauli gates before/after operations to convert coherent errors into stochastic (depolarizing-like) noise, which is easier to characterize and correct.

### 2.4 Open Question
**Does applying DD or Pauli twirling to an authorization boundary:**
- Improve fidelity (higher S_A, lower L_D)?
- Introduce new failure modes (e.g., DD pulse errors, twirling overhead)?
- Remain stable under SPAM correction?

**ARK-447 answers this by testing all three configurations on the same backend, same qubits, same protocol.**

---

## 3. Experimental Design

### 3.1 Boundary Structure (Same as ARK-441)
**Binary ALLOW/DENY** authorization boundary:
- **Authorizer qubit (Q_A):** Prepared in |0⟩ (DENY) or |1⟩ (ALLOW)
- **Payload qubit (Q_P):** Target of the controlled operation
- **Boundary gate:** CNOT(Q_A → Q_P) with P(Q_P) = |+⟩
- **Measurement:** Z-basis on both qubits

**Expected outcomes (ideal):**
- **ALLOW path:** Q_A=|1⟩ → CNOT flips P → measure P in |−⟩ → outcome "1" (S_A ≈ 1.0)
- **DENY path:** Q_A=|0⟩ → CNOT does nothing → measure P in |+⟩ → outcome "0" (L_D ≈ 0.0)

### 3.2 Three Configurations
**Configuration 1: Baseline (unprotected)**
- Same circuit as ARK-441
- No noise mitigation applied
- Acts as the control group

**Configuration 2: Dynamical Decoupling (DD)**
- Apply DD sequences (e.g., XY4, CPMG) during idle periods on both Q_A and Q_P
- DD sequences inserted automatically via Qiskit's `PadDynamicalDecoupling` pass
- Uses X gates (π-pulses) to refocus phase errors

**Configuration 3: Pauli Twirling**
- Randomize Pauli gates {I, X, Y, Z} before and after the CNOT operation
- Twirling applied to both Q_A and Q_P
- Random Pauli pairs chosen per shot to average over all error channels
- Circuit structure: `[random Pauli] → CNOT → [compensating Pauli] → measure`

### 3.3 Shots & Arms
**6 arms total** (2 boundary conditions × 3 configurations):
1. **arm1:** ALLOW + Baseline
2. **arm2:** DENY + Baseline
3. **arm3:** ALLOW + DD
4. **arm4:** DENY + DD
5. **arm5:** ALLOW + Pauli Twirling
6. **arm6:** DENY + Pauli Twirling

**Shots per arm:** 8192 (same as ARK-441/445/445b)

### 3.4 SPAM Baseline (Gating Condition)
Two SPAM circuits (same as all ARK experiments):
- **SPAM_A:** Prepare |1⟩ on Q_A, measure in Z
- **SPAM_P:** Prepare |+⟩ on Q_P, measure in Z

**Gate:** Both must show SPAM error ≤ 0.02 to proceed.

---

## 4. Quantitative Success Criteria

### 4.1 Primary Metrics (per configuration)
**ALLOW discrimination:**
- **S_A** = P(outcome=1 | ALLOW path, given configuration)
- **Threshold:** S_A ≥ 0.90 (same as ARK-441/445/445b)

**DENY leakage (SPAM-corrected):**
- **L_D_raw** = P(outcome=1 | DENY path, given configuration)
- **L_D_corrected** = max(0, L_D_raw − SPAM_P)
- **Threshold:** L_D_corrected ≤ 0.02 (strict)

**Boundary margin:**
- **Δ_B** = S_A − L_D_corrected − 0.20
- **Threshold:** Δ_B ≥ 0.00 (must be non-negative)

### 4.2 Pass/Fail Per Configuration
Each configuration (Baseline, DD, Pauli Twirling) is evaluated independently:
- **PASS:** All three criteria met (S_A ≥ 0.90, L_D ≤ 0.02, Δ_B ≥ 0.00)
- **FAIL:** Any criterion violated

### 4.3 Comparative Analysis
**Primary comparison:** DD vs. Baseline, Twirling vs. Baseline
- **Improvement:** S_A increases OR L_D decreases (with statistical significance)
- **No change:** Metrics within noise/uncertainty
- **Degradation:** S_A decreases OR L_D increases

**Secondary comparison:** DD vs. Pauli Twirling
- Which technique performs better on this specific backend/qubit pair?

### 4.4 Overall Verdict
**PASS (strong):** All three configurations pass individual criteria; at least one mitigation technique shows improvement over baseline.

**PASS (weak):** All three configurations pass individual criteria; no significant improvement observed (mitigation techniques add no harm, no benefit).

**MIXED:** Baseline passes; one or both mitigation techniques fail (introduces new failure modes).

**FAIL:** Baseline fails (boundary itself unstable on this backend/qubit pair).

---

## 5. Interpretation Boundaries

### 5.1 What This Experiment Tests
✅ Noise-mitigation impact on a binary ALLOW/DENY authorization boundary  
✅ DD and Pauli twirling performance on IBM Quantum Heron r2 hardware  
✅ Comparative fidelity across three configurations (same backend, same qubits, same day)  
✅ SPAM-corrected metrics for honest leakage assessment

### 5.2 What This Experiment Does NOT Test
❌ **Generalization:** Results apply to the specific backend, qubits, and calibration used. No claim that DD/twirling will improve all boundaries on all hardware.  
❌ **Cryptographic security:** This is a metrology experiment, not a cryptographic protocol validation.  
❌ **Error correction:** DD and twirling are noise *mitigation* (not correction); no QEC codes used.  
❌ **Multi-round or complex boundaries:** Single-round, binary boundary only.  
❌ **Optimal DD sequences:** Uses standard DD (e.g., XY4); not optimized for this specific backend.

### 5.3 Known Limitations
- **DD overhead:** DD pulses add gate count, which may introduce errors if pulse fidelity is low.
- **Twirling randomness:** Pauli twirling requires many shots to average over randomness; 8192 shots may be insufficient for strong statistical separation if improvement is small.
- **Idle time dependency:** DD benefit depends on T1/T2 and the duration of idle periods; short circuits may see minimal improvement.

---

## 6. Protocol: Field 27 (Preregistration-First)

### 6.1 Sequence (Hard Ordering)
1. **LOCK commit** — This preregistration document, all code, and MANIFEST.txt committed to `executionproof-testbeds` on branch `execute/ark-447` with tag `ark-447-v1.0-lock` BEFORE any hardware job.
2. **Qubit selection** — Run `ark_447_select_qubits.py` to choose Q_A and Q_P based on lowest readout error sum, connected pair.
3. **SPAM baseline job** — Run `ark_447_spam_job.py` (SPAM_A and SPAM_P circuits, 8192 shots each). **Gate:** Proceed only if both SPAM ≤ 0.02.
4. **Principal job submission** — Run `ark_447_submit_ibm.py` (6 circuits × 8192 shots).
5. **Retrieve results** — Run `ark_447_retrieve.py` after job completes.
6. **Analysis** — Run `ark_447_analysis.py` to compute S_A, L_D, Δ_B for each configuration, apply SPAM correction, determine verdict.
7. **Documentation** — Generate `RESULTS.md`, `RUN_LOG.md`, and `proofrecord.json`.
8. **Tag & publish** — Tag `ark-447-v1.0`, push to GitHub, open PR.

### 6.2 MANIFEST Integrity
All 6 code files (`ark_447_select_qubits.py`, `ark_447_circuits.py`, `ark_447_spam_job.py`, `ark_447_submit_ibm.py`, `ark_447_retrieve.py`, `ark_447_analysis.py`) will have their SHA-256 hashes recorded in `MANIFEST.txt` and committed in the LOCK commit. Any post-LOCK modification to these files invalidates the preregistration.

### 6.3 No Rescue
If the experiment fails (SPAM gate fails, or any configuration fails its criteria), the result is published as-is with honest FAIL verdict. No re-running, no parameter tuning, no rescue attempts.

---

## 7. Expected Timeline

- **LOCK commit:** 2026-07-17 (today)
- **Qubit selection + SPAM gate:** ~5 minutes
- **Principal job:** ~25-30 seconds (6 circuits × 8192 shots, estimated queue time depends on backend load)
- **Retrieval + analysis:** ~2 minutes
- **Documentation + tag:** ~5 minutes
- **Total:** ~15-20 minutes end-to-end (excluding queue wait)

---

## 8. Relation to Prior Work

**ARK-441** (binary ALLOW/DENY baseline, unprotected) → **PASS** (S_A=0.9979, L_D=0.0021, Δ_B=0.9779)

**ARK-447** tests whether DD or Pauli twirling can **improve** on ARK-441's baseline or maintain fidelity while adding robustness.

If ARK-447 shows improvement, it suggests noise mitigation can strengthen authorization boundaries.  
If ARK-447 shows no change, it suggests the baseline is already near the hardware limit.  
If ARK-447 shows degradation, it suggests mitigation techniques introduce overhead that outweighs their benefit on this backend.

---

## 9. Authorship & Provenance

- **Principal Investigator:** Derek Hone, Remnant Fieldworks Inc.
- **Organization:** Remnant Fieldworks Inc. (ExecutionProof product track)
- **Repository:** `derekhone/executionproof-testbeds`
- **Preregistration commit:** To be tagged `ark-447-v1.0-lock` before hardware execution
- **Backend provider:** IBM Quantum (open-access Heron r2 backends)

---

## 10. Disclosure

**No conflicts of interest.** This experiment is part of the ExecutionProof authorization-boundary R&D program. Results will be published regardless of outcome (PASS/FAIL/MIXED). No financial incentive to suppress negative results.

**Reproducibility:** Full code, circuits, raw counts, and calibration snapshots will be published in the `executionproof-testbeds` repository. Any researcher with IBM Quantum access can attempt to reproduce this experiment on the same or different backends.

---

**This preregistration is locked before hardware execution. Any changes to success criteria, circuit design, or analysis methodology after hardware jobs are submitted invalidate the preregistration protocol.**
