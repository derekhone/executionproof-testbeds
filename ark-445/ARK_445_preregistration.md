# ARK-445 Preregistration: Tri-State Authorization Discrimination (ALLOW / HOLD / DENY)

**Experiment ID:** ARK-445  
**Series:** Authorization Boundary Characterization (Phase 1)  
**Preregistration Date:** 2026-07-17 (UTC)  
**Execution Status:** PENDING (preregistered, not yet executed)  
**Protocol Version:** 28-field structured preregistration

---

## Field 1: Central Research Question

**Can the system reliably discriminate between THREE distinct authorization states — ALLOW (execute), HOLD (ambiguous/pending), and DENY (refuse) — rather than only binary ALLOW/DENY?**

Specifically: Does the verify-then-execute (VBE) authorization boundary support a tri-state decision space where:
- **ALLOW** → payload executes with high confidence (P(execute) ≥ 0.90),
- **DENY** → payload refuses with high confidence (P(execute) ≤ 0.02 corrected),
- **HOLD** → payload exhibits intermediate behavior, distinguishable from both ALLOW and DENY (P(execute) ∈ [0.40, 0.60]),

...and the three states are metrologically separable with margin Δ_H ≥ 0.30?

---

## Field 2: Primary Hypothesis (H1)

**H1:** The system can discriminate ALLOW, HOLD, and DENY authorization states with clear separation:
- **ALLOW arms** (authorizer A=|1⟩): S_A ≥ 0.90 (SPAM-corrected)
- **DENY arms** (authorizer A=|0⟩): L_D_corrected ≤ 0.02
- **HOLD arms** (authorizer A=|+⟩ or |−⟩): H ∈ [0.40, 0.60]
- **Tri-state discrimination margin:** Δ_H = min(S_A_min − H_max, H_min − L_D_max) ≥ 0.30

where:
- S_A_min = minimum observed P(Q_P=1) across all ALLOW arms (SPAM-corrected)
- H_max, H_min = max/min observed P(Q_P=1) across all HOLD arms
- L_D_max = maximum observed L_D_corrected across all DENY arms

---

## Field 3: Secondary / Exploratory Hypotheses

**H2a (Superposition symmetry):** HOLD arms with A=|+⟩ and A=|−⟩ yield statistically indistinguishable P(execute), confirming basis-independent ambiguity encoding.

**H2b (Reverification escape):** An ALLOW arm with delay + re-verification maintains S_A ≥ 0.90, demonstrating the HOLD state is not an artifact of decoherence but a genuine intermediate encoding.

**H2c (Confusion falls to DENY):** Tampered or replayed authorization attempts collapse to the DENY outcome (L ≤ 0.02 corrected), not to HOLD.

**H2d (SPAM-drift bound):** In-situ SPAM baselines for Q_A and Q_P remain ≤ 0.02 per qubit, and |SPAM_A − SPAM_P| ≤ 0.005 (drift check).

---

## Field 4: Null Hypothesis (H0)

**H0:** The system cannot reliably separate HOLD from ALLOW or DENY — either:
1. HOLD arms collapse into the ALLOW region (H > 0.80), or
2. HOLD arms collapse into the DENY region (H < 0.10), or
3. HOLD arms are statistically indistinguishable from SPAM baseline (|H − SPAM| < 0.05), or
4. Discrimination margin Δ_H < 0.30 (insufficient separation for practical tri-state use).

**Implication if H0 holds:** The VBE boundary is fundamentally binary (ALLOW/DENY only), and intermediate/pending states are not metrologically accessible.

---

## Field 5: Experiment Design & Methodology

### 5.1 Circuit Architecture
- **2-qubit system:** Q_A (authorizer), Q_P (payload execution indicator)
- **10 arms** (single QuantumCircuit with parameter sweep):

| Arm | Label | Q_A Preparation | Q_P Conditioning | Expected Outcome |
|-----|-------|-----------------|------------------|------------------|
| 1 | `allow_standard` | X (→|1⟩) | if A=1: X on P | ALLOW: S_A |
| 2 | `deny_standard` | I (→|0⟩) | if A=1: X on P | DENY: L_D |
| 3 | `hold_plus` | H (→|+⟩) | if A=1: X on P | HOLD: H_plus |
| 4 | `hold_minus` | X+H (→|−⟩) | if A=1: X on P | HOLD: H_minus |
| 5 | `allow_alt` | X | if A=1: X on P | ALLOW: S_A_alt |
| 6 | `deny_alt` | I | if A=1: X on P | DENY: L_D_alt |
| 7 | `allow_reverified` | X, delay 1µs, re-verify | if A=1: X on P | ALLOW: S_A_rev |
| 8 | `deny_expired` | I, delay 1µs | if A=1: X on P | DENY: L_D_exp |
| 9 | `confusion_replay` | X, measure→discard, reset, I | if A=1: X on P | DENY: L_conf |
| 10 | `spam_idle` | I | I (no gate) | SPAM: baseline |

**Key mechanism:**
- ALLOW: A prepared in |1⟩ → measurement collapses to outcome=1 → X fires on P → P read as |1⟩
- DENY: A prepared in |0⟩ → measurement collapses to outcome=0 → X does NOT fire → P read as |0⟩
- HOLD: A prepared in |+⟩ or |−⟩ → measurement collapses to 0 or 1 with ~50% probability EACH shot → aggregate P(Q_P=1) ≈ 0.5 across shots (intermediate between 0 and 1)

**Classical feedforward:** Measure Q_A → ClassicalRegister `ca`, condition X on Q_P using single-register `if_test(ca==1, ...)` (flat condition, no nested blocks — ARK-444 error-1524 lesson applied).

### 5.2 Qubit Selection (Execution-Time)
- **Rule:** 2 qubits (Q_A, Q_P) with:
  1. Readout error (RE) < 2% for BOTH qubits
  2. Q_A and Q_P are **connected** (CNOTs allowed, though not used in this experiment)
  3. **Minimum sum:** argmin(RE_A + RE_P) across all valid connected pairs
  4. Selected from **live calibration data** on execution day (not preregistered)
  5. `initial_layout = [Q_A, Q_P]` enforced in transpile
- **Selection frozen** at execution and committed to `selected_qubits.json` BEFORE any hardware job.

### 5.3 Execution Parameters
- **Backend:** `ibm_marrakesh` (156-qubit Heron r2, preferred); fallback `ibm_fez` if marrakesh unavailable
- **Shots per arm:** 8,192
- **Total shots:** 81,920 (10 arms × 8,192)
- **Transpiler:** `optimization_level=3`, `seed_transpiler=445`, `initial_layout=[Q_A, Q_P]`, no dynamical decoupling (`None`)
- **Sampler:** `SamplerV2` (shots mode), `default_shots=8192`
- **Estimated runtime:** ~25–30 seconds (principal job)

---

## Field 6: Measured Observables & Metrics

### Primary Metrics
All metrics computed from raw counts (no readout mitigation):

1. **S_A (ALLOW arms 1, 5, 7):** P(Q_P=1 | ALLOW) for each arm
   - S_A_min = min(S_A_arm1, S_A_arm5, S_A_arm7)

2. **L_D (DENY arms 2, 6, 8, 9):** P(Q_P=1 | DENY) for each arm
   - L_D_corrected = max(0, L_D − SPAM_P) for each DENY arm
   - L_D_max = max(L_D_corrected_arm2, ..., L_D_corrected_arm9)

3. **H (HOLD arms 3, 4):** P(Q_P=1 | HOLD) for each arm
   - H_plus = P(Q_P=1 | arm3_hold_plus)
   - H_minus = P(Q_P=1 | arm4_hold_minus)
   - H_min = min(H_plus, H_minus)
   - H_max = max(H_plus, H_minus)

4. **SPAM baselines (arm 10):**
   - SPAM_A = P(Q_A=1 | idle)
   - SPAM_P = P(Q_P=1 | idle)
   - SPAM_drift = |SPAM_A − SPAM_P|

5. **Tri-state discrimination margin:**
   - Δ_H = min(S_A_min − H_max, H_min − L_D_max)

### Diagnostic Metrics
- **I_H (HOLD symmetry index):** |H_plus − H_minus| (expect < 0.05 if symmetric)
- **L_conf (confusion/replay arm 9):** P(Q_P=1 | confusion) — expect ≤ 0.02 corrected
- **S_A_rev (reverified ALLOW arm 7):** expect ≥ 0.90 (HOLD is not decoherence)

---

## Field 7: Success Criteria (Quantitative Thresholds)

### PASS Conditions (ALL must be satisfied):
1. **ALLOW floor:** S_A_min ≥ 0.90 (at least one ALLOW arm corrected if needed)
2. **DENY ceiling:** L_D_corrected ≤ 0.02 for ALL four DENY arms
3. **HOLD range:** 0.40 ≤ H_min AND H_max ≤ 0.60 for BOTH HOLD arms
4. **Tri-state margin:** Δ_H ≥ 0.30
5. **SPAM kill-gate (pre-check):** arm10 SPAM_A ≤ 0.02 AND SPAM_P ≤ 0.02 (executed BEFORE principal job; principal job cancelled if violated)

### FAIL Conditions (any one triggers FAIL):
1. S_A_min < 0.90 after SPAM correction
2. ANY L_D_corrected > 0.02
3. H_min < 0.40 OR H_max > 0.60 (HOLD collapsed to ALLOW or DENY)
4. Δ_H < 0.30 (insufficient discrimination)

### KILL / INDETERMINATE Conditions:
1. **SPAM gate violation:** SPAM_A > 0.02 OR SPAM_P > 0.02 from arm10 → **KILL** experiment immediately, do not submit principal job
2. **Drift violation:** SPAM_drift > 0.005 → **INDETERMINATE**
3. **Job failure:** Principal job returns error, zero counts, or incomplete data → **INDETERMINATE**

---

## Field 8: Statistical Power & Sample Size

- **Shots per arm:** 8,192
- **Binomial SEM** at p=0.50: σ ≈ √(0.5×0.5/8192) ≈ 0.0055 (0.55%)
- **95% CI half-width:** ±1.96σ ≈ ±0.011 (±1.1%)
- **Detectability:** HOLD range [0.40, 0.60] is ±10% from ideal 0.50, well above ±1.1% noise → robustly detectable
- **Discrimination margin 0.30** (30 percentage points) >> 2% noise → clear separation

---

## Field 9: Planned Statistical Analysis

### Analysis Steps:
1. **Raw count extraction:** Parse SamplerV2 results for each arm
2. **SPAM correction:** For DENY arms, compute L_D_corrected = max(0, L_D_raw − SPAM_P)
3. **Metric computation:** Calculate S_A, L_D, H, Δ_H per Field 6 definitions
4. **Criterion scoring:** Evaluate PASS/FAIL per Field 7 thresholds
5. **Secondary hypothesis tests:**
   - H2a: two-sample proportion test for H_plus vs H_minus (expect p > 0.05)
   - H2b: verify S_A_rev ≥ 0.90
   - H2c: verify L_conf ≤ 0.02 corrected
   - H2d: verify SPAM_drift ≤ 0.005

### Outputs:
- `proofrecord.json`: all raw/corrected metrics + verdict + timestamp
- `plots/arm_results.png`: bar chart of P(Q_P=1) for all 10 arms with thresholds
- `plots/tristate_discrimination.png`: scatter plot showing ALLOW/HOLD/DENY regions

---

## Field 10: Interpretation Boundaries

### What this experiment DOES test:
- Whether three authorization states (ALLOW/HOLD/DENY) can be metrologically distinguished on this specific 2-qubit setup with this circuit design.
- Whether superposition-based encoding (|+⟩, |−⟩) produces a stable intermediate outcome distinct from basis states.

### What this experiment DOES NOT claim:
- **Not new physics:** Superposition → probabilistic measurement outcome is textbook quantum mechanics. This is a metrological characterization, not a discovery.
- **Not a security guarantee:** HOLD state accessibility does not imply cryptographic security, tamper evidence, or resistance to any attack model.
- **Not generalizable:** Results apply to the selected qubits on the selected backend on the execution date. No claims about other qubits, backends, or gate implementations.
- **Not a primitive:** This does not define or validate a "quantum tri-state authorization protocol" for real-world use.

---

## Field 11: Dependencies on Prior Experiments

- **ARK-441/ARK-446:** Established binary ALLOW/DENY boundary (Δ_B ≥ 0.70, L_D ≤ 0.02, S_A ≥ 0.90). ARK-445 extends this to a tri-state space.
- **ARK-442:** Characterized delay-induced degradation. ARK-445 arm7 (reverified ALLOW) uses 1µs delay to confirm HOLD is not a decoherence artifact.
- **ARK-444:** Demonstrated integrity gate (tamper→DENY). ARK-445 arm9 (confusion/replay) confirms tamper collapses to DENY, not HOLD.
- **ARK-443:** Validated classical feedforward (single-register `if_test`). ARK-445 uses the same flat-condition pattern (no nested blocks).

**Execution order:** ARK-441 → ARK-446 → ARK-442 → ARK-444 → ARK-443 → **ARK-445** (current) → ARK-447 (planned).

---

## Field 12: Equipment & Resources

- **Platform:** IBM Quantum (`ibm_quantum_platform`), open instance
- **Backend:** `ibm_marrakesh` (156-qubit Heron r2) — preferred
  - Fallback: `ibm_fez` (156-qubit Heron r2) if marrakesh offline
- **Calibration data:** Live backend properties fetched on execution day
- **Qiskit version:** `qiskit-ibm-runtime >= 0.30`, `qiskit >= 1.3`
- **Estimated usage:** ~25–30s (principal) + ~6s (SPAM) = ~31–36s total
- **Budget check:** Confirmed ≥ 40s remaining before submission

---

## Field 13: Data Collection Procedures

1. **Qubit selection:** Execute `ark_445_select_qubits.py` → freeze selection in `selected_qubits.json` + calibration snapshot → commit
2. **SPAM kill-gate:** Execute `ark_445_spam_job.py` (arm10 only) → wait for completion → record SPAM results in `spam_results.json` → **commit SPAM gate BEFORE principal** → KILL if violated, else proceed
3. **Principal job submission:** Execute `ark_445_submit_ibm.py` (arms 1–9) → record job ID in `principal_job_id.txt` + metadata in `principal_job_meta.json` → **commit job ID record BEFORE retrieving results**
4. **Result retrieval:** Execute `ark_445_retrieve.py` → poll job → write `raw_results.json` → commit
5. **Analysis:** Execute `ark_445_analysis.py` → compute metrics → write `proofrecord.json` + plots → commit
6. **RESULTS:** Populate `RESULTS.md` → generate `.docx` / `.pdf` → commit + tag `ark-445-v1.0`

---

## Field 14: Planned Data Transformations

- **No readout error mitigation** (results reported from raw counts)
- **SPAM correction:** For DENY arms only: L_D_corrected = max(0, L_D_raw − SPAM_P)
- **Aggregation:** All metrics aggregate counts within each arm (no cross-arm averaging)
- **Filtering:** None (all shots included)

---

## Field 15: Exclusion Criteria

**Pre-execution exclusions (cancel experiment):**
1. No connected qubit pair with RE < 2% for both qubits available
2. SPAM kill-gate violated (SPAM_A > 0.02 OR SPAM_P > 0.02)

**Post-execution exclusions (classify as INDETERMINATE):**
1. Principal job fails (error code, zero counts, timeout)
2. SPAM_drift > 0.005
3. Backend suffers mid-job recalibration or downtime

**No per-shot exclusions** (outlier shots are not filtered).

---

## Field 16: Missing Data Handling

- **Incomplete job counts:** If any arm has < 8,192 shots returned → INDETERMINATE
- **Missing SPAM baseline:** If arm10 fails or returns zero counts → KILL (cannot correct)
- **Partial job failure:** If principal job completes but ≥1 arm missing → INDETERMINATE

---

## Field 17: Exploratory Analyses (Post-Hoc, Not Pre-Committed)

After primary analysis, MAY explore (not binding on PASS/FAIL):
- Shot-by-shot correlation between Q_A measurement outcome and Q_P readout in HOLD arms
- Comparison of H_plus and H_minus to ideal 0.50 (Poisson test)
- Cross-arm variance in S_A and L_D (robustness check)

**These are descriptive only** — no exploratory result can change the PASS/FAIL verdict.

---

## Field 18: Limitations & Potential Confounds

1. **Decoherence vs encoding:** HOLD arms use superposition → measurement-induced collapse. If T1/T2 decay is significant (unlikely at <1µs), H might drift from 0.50. Arm7 (reverified ALLOW with 1µs delay) controls for this.
2. **Gate fidelity:** If Hadamard gate fidelity is poor, |+⟩/|−⟩ preparation may be imperfect → H drifts toward basis-state outcomes. No mitigation; reported as-observed.
3. **Transpiler reordering:** `if_test` blocks are fragile to transpilation. Pre-lock validation (test transpile on real backend) will confirm correct gate sequence.
4. **Endianness:** ClassicalRegister bit-order matters for `if_test(ca==1)`. Tested in pre-lock validation.

---

## Field 19: Deviations from Pre-Registration

Any deviation from this protocol (parameter changes, arm redefinition, threshold adjustment, additional SPAM correction) MUST be:
1. Documented in `RUN_LOG.md` with justification
2. Committed BEFORE reading principal job results
3. Flagged in `RESULTS.md` as a protocol deviation

**No post-data rescue** is permitted. If primary hypotheses fail, the experiment fails — no threshold adjustment, no arm redefinition, no re-analysis can change the verdict.

---

## Field 20: Preregistration Timestamp & Commitment

- **Preregistration completed:** 2026-07-17 (UTC)
- **Committed to git:** execute/ark-445 branch
- **LOCK commit (before any hardware job):** This preregistration file + all code files + MANIFEST.txt with SHA-256 hashes
- **Public record:** Pushed to `derekhone/executionproof-testbeds` (public repo)

---

## Field 21: Roles & Responsibilities

- **Principal Investigator:** Derek Hone (Remnant Fieldworks Inc.)
- **Experiment execution:** Automated via preregistered Python scripts
- **Hardware provider:** IBM Quantum (ibm_marrakesh / ibm_fez)
- **Code repository:** https://github.com/derekhone/executionproof-testbeds
- **Funding:** None (open-access IBM Quantum)

---

## Field 22: Conflicts of Interest

None declared. This is an independent metrological characterization with no commercial interest, patent application, or external funding.

---

## Field 23: Ethical Considerations

- **No human subjects, biological materials, or animal use**
- **No dual-use concern:** Quantum gate characterization; no cryptographic claims
- **Environmental:** Negligible energy (~30s compute on shared IBM hardware)

---

## Field 24: Data Sharing & Availability

**All data will be made publicly available upon completion:**
- Preregistration (this file), code, MANIFEST committed BEFORE execution
- `selected_qubits.json` with live calibration data
- `spam_results.json` (SPAM kill-gate)
- `principal_job_id.txt`, `principal_job_meta.json` (job provenance)
- `raw_results.json` (raw counts from IBM backend)
- `proofrecord.json` (all metrics + verdict)
- `RESULTS.md` / `.docx` / `.pdf` (human-readable report)
- Plots: `arm_results.png`, `tristate_discrimination.png`

**Repository:** https://github.com/derekhone/executionproof-testbeds/tree/execute/ark-445  
**Release tag:** `ark-445-v1.0` (created upon completion)  
**Zenodo DOI:** Will be updated in record 21398676 (ARK-441 dataset continuation)

**License:** CC BY 4.0 (open access, attribution required)

---

## Field 25: Timeline

- **Preregistration lock:** 2026-07-17 (this document + code + MANIFEST committed)
- **Qubit selection:** 2026-07-17 (execution day, after lock)
- **SPAM gate:** 2026-07-17 (before principal job)
- **Principal job submission:** 2026-07-17 (after SPAM gate passes)
- **Analysis & results:** 2026-07-17 (same day)
- **Public release:** 2026-07-17 (tag + PR opened)

**Total elapsed time (preregistration → results):** < 2 hours (same-day execution)

---

## Field 26: Contingency Plans

### If SPAM kill-gate fails (SPAM > 0.02):
- **Action:** KILL experiment, do NOT submit principal job
- **Outcome:** Report as INDETERMINATE (hardware SPAM too high for reliable measurement)
- **Retry:** MAY retry on a different day or backend (new preregistration freeze required)

### If principal job fails (error, zero counts, timeout):
- **Action:** Classify as INDETERMINATE, do NOT resubmit
- **Outcome:** Report job failure in RESULTS.md
- **No rescue:** Failure is a valid outcome; no retry within this preregistration instance

### If backend goes offline mid-execution:
- **Action:** Report as INDETERMINATE
- **No fallback mid-execution:** Cannot switch backends after LOCK (qubits are backend-specific)

---

## Field 27: Ordering Constraint (Strict Sequence)

**Hard ordering to prevent post-hoc bias or rescue-after-failure:**

```
1. LOCK (this prereg + code + MANIFEST) → commit SHA recorded in RUN_LOG.md
2. Qubit selection (selected_qubits.json + calibration snapshot) → commit
3. SPAM job submission (arm10 only) → wait for completion
4. SPAM gate result (spam_results.json) → commit BEFORE principal job
5. [KILL-GATE] IF SPAM violated → STOP, classify INDETERMINATE, commit RUN_LOG, DONE
6. [IF SPAM passes] → Principal job submission (arms 1–9)
7. Principal job ID record (principal_job_id.txt + metadata) → commit BEFORE reading results
8. Result retrieval (wait for job completion)
9. Raw results (raw_results.json) → commit
10. Analysis (proofrecord.json + plots) → commit
11. RESULTS.md + docx/pdf → commit
12. Tag ark-445-v1.0 → push all commits + tag
13. Open PR (do NOT merge) → request review
```

**Enforcement:** Each step writes files + git commit. Commit timestamps prove ordering. Any violation (e.g., job ID committed after results) invalidates the experiment.

---

## Field 28: Amendment Log

- **Version 1.0 (2026-07-17):** Initial preregistration — LOCKED, no amendments

Any future amendments MUST:
1. Be committed BEFORE the step they affect
2. Be justified in RUN_LOG.md with rationale
3. Preserve original text (amendments append, do not overwrite)

**Post-LOCK, pre-data amendments are permissible ONLY for technical corrections** (e.g., transpiler syntax error discovered in pre-execution test). Post-data amendments are FORBIDDEN.

---

## Summary: Quick Reference

| Parameter | Value |
|-----------|-------|
| Qubits | 2 (Q_A, Q_P) — execution-time selection, RE < 2%, connected |
| Arms | 10 (3 ALLOW, 4 DENY, 2 HOLD, 1 SPAM) |
| Shots/arm | 8,192 |
| Backend | ibm_marrakesh (preferred) / ibm_fez (fallback) |
| PASS rule | S_A ≥ 0.90, L_D ≤ 0.02, H ∈ [0.40,0.60], Δ_H ≥ 0.30, SPAM ≤ 0.02 |
| KILL rule | SPAM > 0.02 (any qubit) → cancel principal job |
| Central claim | Tri-state authorization (ALLOW/HOLD/DENY) is metrologically discriminable |
| Interpretation | Metrological characterization only — not new physics, not cryptographic security |

---

**END OF PREREGISTRATION (28 fields complete)**

This document serves as the LOCK for ARK-445. Commit SHA + timestamp in RUN_LOG.md will timestamp the preregistration freeze.
