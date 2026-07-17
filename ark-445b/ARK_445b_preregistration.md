# ARK-445b Preregistration — Tri-State Authorization Discrimination (Reset-Free Retest)

**Status:** Phase 1 — preregistration LOCK, pre-execution  
**Preregistered:** 2026-07-17 (UTC)  
**Experiment ID:** ARK-445b  
**Predecessor:** ARK-445 (VERDICT: FAIL, tag `ark-445-v1.0`)  
**Claim under test:** The tri-state ALLOW/HOLD/DENY boundary discrimination demonstrated in ARK-445 was fundamentally sound; the single failing criterion (arm9 confusion/replay leak of 0.0289 > 0.02) was caused by **mid-circuit reset infidelity**, not by the tri-state authorization logic itself.

---

## 1. Context and Motivation

ARK-445 (executed 2026-07-17, `ibm_marrakesh`, job `d9codk9htsac739c1dug`) tested whether quantum hardware can faithfully realize **HOLD** as a first-class authorization outcome — a symmetric ambiguity region (|±⟩ superposition, discrimination ≈0.50) distinct from both ALLOW (|1⟩, discrimination ≥0.90) and DENY (|0⟩, leakage ≤0.02).

**ARK-445 verdict: FAIL** (4 of 5 criteria met):
- ✅ ALLOW discrimination S_A_min = 0.9626 (≥0.90)
- ✅ HOLD symmetry: arm3(|+⟩)=0.4946, arm4(|−⟩)=0.4918, both ∈ [0.40,0.60], imbalance I_H=0.0028
- ✅ Standard DENY paths: arm2=0.0029, arm6=0.0018, arm8=0.0011 (all ≤0.02)
- ❌ **arm9 confusion/replay** (mid-circuit reset + re-prepare): L_conf_corrected=0.0289 > 0.02 DENY ceiling
- ✅ ALLOW−HOLD separation Δ_H = 0.4629 (≥0.30)

The failing arm (arm9) performed:
1. Prepare authorizer Q_A=|1⟩ → measure → classical bit ca=1
2. **Mid-circuit reset** of payload Q_P → attempt to return to |0⟩
3. Re-prepare Q_P to |0⟩
4. Apply controlled gate if_test(ca): x(Q_P)

The 0.0289 leak is consistent with **mid-circuit reset infidelity** on ibm_marrakesh: after `reset(Q_P)`, the qubit was not perfectly |0⟩, leaving residual |1⟩ population that the subsequent X gate did not fully cancel. This arm was mislabeled as "confusion/replay" — it actually tested reset fidelity, not anti-replay logic.

**Diagnostic question:** Was the ARK-445 FAIL caused by:
1. **Hypothesis A (reset-specific):** Mid-circuit reset infidelity on the specific qubit, while the 8 reset-free arms (arm1–arm8) were all sound?
2. **Hypothesis B (boundary-intrinsic):** A flaw in the tri-state boundary discrimination itself, independent of reset?

**ARK-445b tests Hypothesis A** by re-running the **identical 8-arm core** (arm1–arm8) under the same strict protocol, **omitting arm9 entirely**. No mid-circuit reset operations. If all 8 arms pass the same ≤0.02 DENY ceiling and ≥0.90 ALLOW floor, Hypothesis A is supported: the leak was reset-specific, not boundary-intrinsic.

---

## 2. Experimental Setup

### 2.1 Backend and Qubits

- **Target backend:** `ibm_marrakesh` (156-qubit Heron r2, basis gates {cz, id, rz, sx, x})
- **Qubit selection rule (identical to ARK-445):**
  - Q_A (authorizer): single qubit, lowest readout error (RE) among all 156 qubits
  - Q_P (payload): single qubit, second-lowest RE among qubits **connected** to Q_A
  - Connectivity: require direct coupling (Q_A, Q_P) ∈ edges
  - Selection: deterministic, from `calibration_snapshot_ibm_marrakesh_YYYYMMDD.json` (captured at preregistration LOCK time)
  - **No manual override** — accept the rule-selected pair even if RE sum is suboptimal

### 2.2 Circuit Structure (8 arms, reset-free)

Each arm initializes Q_A (authorizer) and Q_P (payload), measures Q_A into classical register `ca`, applies a **single-register if_test** over `ca`, and measures Q_P into `cp`.

**Arm definitions (same as ARK-445, omitting arm9):**

| Arm | Label | Q_A init | Q_P init | Control logic | Expected outcome | Class |
|-----|-------|----------|----------|---------------|------------------|-------|
| 1 | `arm1_allow_standard` | \|1⟩ | \|0⟩ | if ca=1: x(Q_P) | ALLOW (cp≈1) | allow |
| 2 | `arm2_deny_standard` | \|0⟩ | \|0⟩ | if ca=1: x(Q_P) | DENY (cp≈0) | deny |
| 3 | `arm3_hold_plus` | \|+⟩ | \|0⟩ | if ca=1: x(Q_P) | HOLD (cp≈0.5) | hold |
| 4 | `arm4_hold_minus` | \|−⟩ | \|0⟩ | if ca=1: x(Q_P) | HOLD (cp≈0.5) | hold |
| 5 | `arm5_allow_alt` | \|1⟩ | \|0⟩ | if ca=1: x(Q_P) | ALLOW (cp≈1) | allow |
| 6 | `arm6_deny_alt` | \|0⟩ | \|0⟩ | if ca=1: x(Q_P) | DENY (cp≈0) | deny |
| 7 | `arm7_allow_reverified` | \|1⟩ | \|0⟩ | if ca=1: x(Q_P) | ALLOW (cp≈1) | allow |
| 8 | `arm8_deny_expired` | \|0⟩ | \|0⟩ | if ca=1: x(Q_P) | DENY (cp≈0) | deny |

**Notes:**
- Arms 1/5/7 are ALLOW variants (Q_A=|1⟩ → ca=1 w.p. ~1 → x(Q_P) fires → cp=1).
- Arms 2/6/8 are DENY variants (Q_A=|0⟩ → ca=0 w.p. ~1 → x(Q_P) does not fire → cp=0).
- Arms 3/4 are HOLD (Q_A=|±⟩ → ca ∈ {0,1} w.p. ~0.5 each → cp ∈ {0,1} w.p. ~0.5).
- Labels "alt," "reverified," "expired" are semantic (testing that multiple ALLOW/DENY paths behave identically); circuits are structurally identical within each class.
- **No arm9** (the reset-based confusion/replay arm from ARK-445 is omitted).

**Control logic:** Flat, single-register `if_test((ca, 1), true_body=[XGate()], qubits=[Q_P], clbits=[])`. No nested conditionals. No mid-circuit reset, no mid-circuit measurements beyond the single Q_A measurement.

**Shot count:** 8192 per arm (same as ARK-445).

### 2.3 SPAM Kill-Gate (Baseline Drift Check)

A separate **9th circuit** (not an authorization arm) measures SPAM baselines:
- Prepare Q_A=|0⟩, Q_P=|0⟩ → measure immediately → count P(ca=1), P(cp=1)
- Definitions:
  - SPAM_A = P(ca=1 | Q_A prepared |0⟩) — authorizer readout error floor
  - SPAM_P = P(cp=1 | Q_P prepared |0⟩) — payload readout error floor
  - drift = |SPAM_A − RE_A_calib| (authorizer drift from calibration snapshot)

**SPAM gate pass criteria:**
- SPAM_A ≤ 0.02
- SPAM_P ≤ 0.02
- drift ≤ 0.01

If SPAM gate fails, the principal job is **aborted before submission**; the experiment is re-attempted on a different day or backend. The SPAM job is committed (job-ID recorded) **before** the principal job is submitted.

---

## 3. Quantitative Success Criteria (Preregistered)

All criteria identical to ARK-445, applied to the 8-arm set:

### 3.1 Primary Criteria (all must pass for PASS verdict)

Let:
- S_i = SPAM-corrected discrimination for ALLOW arm i: S_i = (P(cp=1 | arm i) − SPAM_P) / (1 − SPAM_P)
- L_j = SPAM-corrected leakage for DENY arm j: L_j = (P(cp=1 | arm j) − SPAM_P) / (1 − SPAM_P)
- H_k = SPAM-corrected HOLD-band discrimination for HOLD arm k: H_k = (P(cp=1 | arm k) − SPAM_P) / (1 − SPAM_P)

**Criteria:**

1. **ALLOW discrimination:** S_A_min ≥ 0.90, where S_A_min = min(S_1, S_5, S_7) — all three ALLOW arms must exceed 0.90.
2. **DENY leakage:** L_D_max ≤ 0.02, where L_D_max = max(L_2, L_6, L_8) — all three DENY arms must stay below the strict 0.02 ceiling.
3. **HOLD symmetry:** 0.40 ≤ H_3 ≤ 0.60 **and** 0.40 ≤ H_4 ≤ 0.60 — both |+⟩ and |−⟩ HOLD arms must land in the ambiguity band.
4. **HOLD imbalance:** I_H = |H_3 − H_4| ≤ 0.10 — the two HOLD arms must be approximately symmetric (no strong basis bias).
5. **ALLOW−HOLD separation:** Δ_H ≥ 0.30, where Δ_H = S_A_min − max(H_3, H_4) — ALLOW and HOLD must be clearly separated.

**Verdict:**
- **PASS** if all 5 criteria met.
- **FAIL** if any criterion violated.
- **INCONCLUSIVE** if SPAM gate failed (experiment not run) or if backend errors prevent analysis.

### 3.2 Secondary Observations (Not Pass/Fail)

- **ALLOW consistency:** standard deviation σ_A = std(S_1, S_5, S_7) — should be small (< 0.05) if all ALLOW paths are equivalent.
- **DENY consistency:** standard deviation σ_D = std(L_2, L_6, L_8) — should be small (< 0.01) if all DENY paths are equivalent.

---

## 4. Execution Protocol (Field 27 Strict Ordering)

This experiment follows the **preregistration-first, no-rescue** protocol established in ARK-441–ARK-445.

### 4.1 Pre-Execution (Steps 1–2)

1. **LOCK preregistration + code + SHA-256 MANIFEST** — commit to `executionproof-testbeds` repository (branch `execute/ark-445b`) before any hardware job is submitted. MANIFEST includes:
   - `ARK_445b_preregistration.md` (this file)
   - `README.md` (experiment summary)
   - `ark_445b_select_qubits.py` (qubit selection script)
   - `ark_445b_circuits.py` (circuit generation)
   - `ark_445b_spam_job.py` (SPAM gate script)
   - `ark_445b_submit_ibm.py` (principal job submission)
   - `ark_445b_retrieve.py` (result retrieval)
   - `ark_445b_analysis.py` (SPAM-corrected analysis + verdict)
   
   Git commit timestamp of the LOCK commit proves: code frozen before data.

2. **Pre-lock validation** (local, before LOCK commit):
   - AerSimulator logic test: verify ALLOW arms → ~1.0, DENY arms → ~0.0, HOLD arms → ~0.5 (no SPAM correction, ideal gates)
   - Transpile all 8 arms + SPAM circuit to the selected real backend (optimization_level=3, seed_transpiler fixed) → verify all transpile without error, `if_test` preserved, depths recorded

### 4.2 Execution (Steps 3–7)

3. **Qubit selection** (run `ark_445b_select_qubits.py`):
   - Capture calibration snapshot from `ibm_marrakesh` via `backend.properties()` → save as `calibration_snapshot_ibm_marrakesh_YYYYMMDD.json`
   - Select Q_A, Q_P per rule (lowest RE, connected)
   - Save `selected_qubits.json` (Q_A, Q_P, RE_A, RE_P, connected=True)
   - Commit this file (Step 2 in execution log)

4. **SPAM gate** (run `ark_445b_spam_job.py`):
   - Submit the 9th circuit (idle SPAM baseline) to `ibm_marrakesh` with 8192 shots
   - Retrieve results → compute SPAM_A, SPAM_P, drift
   - **If SPAM gate FAILS:** abort; do not submit principal job. Record failure in `RUN_LOG.md`, commit, stop.
   - **If SPAM gate PASSES:** commit `spam_results.json` + job-ID (Step 4) **before** submitting the principal job.

5. **Principal job submission** (run `ark_445b_submit_ibm.py`):
   - Submit all 8 arms as a batch job to `ibm_marrakesh` (session or primitive per SDK)
   - Transpile with `optimization_level=3`, `seed_transpiler=445` (same as ARK-445 for reproducibility)
   - **Commit the job-ID** (`principal_job_id.txt` + `principal_job_meta.json`) **before** the job completes (Step 7)
   - Do NOT poll for results yet

6. **Wait** — allow job to complete (minutes to hours depending on queue)

7. **Result retrieval** (run `ark_445b_retrieve.py`):
   - Poll job status until DONE or ERROR
   - If ERROR: record error message, commit, VERDICT=INCONCLUSIVE, stop
   - If DONE: save raw counts for all 8 arms to `raw_results.json`, commit (before analysis)

### 4.3 Post-Execution (Steps 8–11)

8. **Analysis** (run `ark_445b_analysis.py`):
   - Load `raw_results.json`, `spam_results.json`, `selected_qubits.json`
   - Compute SPAM-corrected S_i (ALLOW), L_j (DENY), H_k (HOLD) for all 8 arms
   - Evaluate all 5 primary criteria
   - **Determine VERDICT:** PASS / FAIL / INCONCLUSIVE
   - Save `proofrecord.json` (all metrics + verdict + provenance)
   - Generate plots: `plots/arm_results.png` (bar chart), `plots/tristate_discrimination.png` (ALLOW/HOLD/DENY regions)
   - Commit analysis outputs (Step 9)

9. **RESULTS report:**
   - Write `RESULTS.md` (human-readable summary: verdict, scorecard, provenance table, interpretation)
   - Auto-generate `RESULTS.docx`, `RESULTS.pdf`
   - Commit (Step 11)

10. **Finalize `RUN_LOG.md`:** Update steps 8–11 with completion timestamps, commit.

### 4.4 Hard Ordering Constraint (Field 27)

**Commit order (enforced by timestamps):**
1. LOCK (prereg + code + MANIFEST) — before any job
2. Qubit selection — before SPAM job
3. SPAM job-ID — before principal job
4. Principal job-ID — before retrieval
5. Raw results — before analysis
6. Analysis + proofrecord — before RESULTS

**No rescue:** If principal job fails, or if verdict is FAIL, no second attempt on the same preregistration. Post-hoc corrections to code/circuits are forbidden. If a bug is found after LOCK, the experiment is INCONCLUSIVE and a new preregistration (ARK-445c) is required.

---

## 5. Interpretation and Scope

### 5.1 What This Experiment Tests

ARK-445b tests whether the **8-arm reset-free core** of ARK-445 meets all quantitative criteria (ALLOW ≥0.90, DENY ≤0.02, HOLD ∈[0.40,0.60], Δ_H ≥0.30) when mid-circuit reset is removed. It does **not** test:
- Anti-replay logic (there is no temporal nonce or time-gating mechanism)
- Reset fidelity directly (the reset-based arm9 is omitted, not redesigned)
- Generalization to other backends, qubit pairs, or shot counts

### 5.2 Honest Boundaries

- **If ARK-445b PASSES:** The tri-state ALLOW/HOLD/DENY boundary discrimination is sound on the selected qubit pair; ARK-445's FAIL was caused by mid-circuit reset infidelity (arm9), not by the core logic.
- **If ARK-445b FAILS on the same arm(s) that passed in ARK-445:** Likely backend drift or calibration change between the two runs; inconclusive diagnostic.
- **If ARK-445b FAILS on a different arm:** New failure mode unrelated to reset; suggests boundary-intrinsic issue (Hypothesis B supported).

This experiment is a **bounded diagnostic retest**, not a claim that the tri-state framework is universally sound. It isolates one variable (presence/absence of mid-circuit reset) to determine the root cause of ARK-445's single failing criterion.

### 5.3 What Is NOT Claimed

- ❌ No security guarantees — this is a hardware characterization study, not a cryptographic proof.
- ❌ No generalization beyond the specific setup (backend, qubits, date, optimization level).
- ❌ No claim that HOLD is "provably secure" or "fault-tolerant" — we are testing whether it can be **discriminated** on current NISQ hardware, not whether it is useful in production.
- ❌ No claim that omitting arm9 "fixes" ARK-445 — we are diagnosing the failure, not redefining success criteria post-hoc.

---

## 6. Provenance and Integrity

- **Preregistration date:** 2026-07-17 (this document, committed before execution)
- **Repository:** `https://github.com/derekhone/executionproof-testbeds` (branch `execute/ark-445b`)
- **Commit SHA of LOCK:** _(to be recorded after LOCK commit)_
- **MANIFEST SHA-256:** _(to be computed and recorded in `MANIFEST.txt` at LOCK time)_
- **Predecessor:** ARK-445 (tag `ark-445-v1.0`, job `d9codk9htsac739c1dug`, VERDICT=FAIL)
- **Series:** ARK-441 → ARK-446 → ARK-442 → ARK-444 → ARK-443 (all PASS) → ARK-445 (FAIL) → **ARK-445b** (pending)

All commit timestamps are UTC, publicly visible on GitHub. No GPG/SSH signing (authored commits are unsigned; only GitHub's server-side merge commits bear the `web-flow` signature).

---

## 7. License and Access

- **Code license:** MIT (same as `executionproof-testbeds` repository)
- **Data/results license:** CC BY 4.0 (same as prior ARK experiments)
- **Public access:** All preregistration, code, raw results, analysis, and provenance records will be committed to the public repository and tagged upon completion. No gated or private data.

---

**Preregistration ends here. Execution begins only after this file, all scripts, README.md, and MANIFEST.txt are committed to `executionproof-testbeds` with a timestamped LOCK commit.**
