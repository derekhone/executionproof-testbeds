# ARK-445 — RESULTS

**Tri-State Authorization Discrimination (ALLOW / HOLD / DENY)**
Remnant Fieldworks Inc. — Derek Hone
Backend: `ibm_marrakesh` (156-qubit Heron r2) · Instance: `open-instance`

---

## Verdict: **FAIL** (preregistered decision rule, Field 7)

The experiment executed cleanly on hardware with an in-situ SPAM baseline far within
ceiling, so the result is a **valid FAIL**, not INDETERMINATE. It fails on **exactly one**
of the five preregistered PASS criteria: the reset-based **confusion/replay DENY arm
(arm9)** leaked `L_conf_corrected = 0.0289`, above the strict `≤ 0.02` DENY ceiling.

The **core tri-state discrimination is strong and clearly demonstrated**: ALLOW, HOLD, and
DENY map to well-separated payload-execution probabilities with a tri-state margin
`Δ_H = 0.463`, comfortably above the required `0.30`. The failure is confined to one
adversarial DENY arm whose mechanism (mid-circuit `reset` then re-prepare) is sensitive to
hardware reset infidelity. **No post-data rescue is applied** (Field 19): the preregistered
rule requires ALL four DENY arms to clear the ceiling, so the overall verdict is FAIL.

---

## Provenance (strict ordering — Field 27)

| Step | Artifact | Job ID | Commit-before |
|------|----------|--------|---------------|
| LOCK | `MANIFEST.txt` (SHA-256), prereg + 6 code files | — | `b0b56b0` |
| Qubit selection | `selected_qubits.json` | — | `893b147` |
| SPAM kill-gate | `spam_results.json` | `d9coda9htsac739c1djg` | `cc745e5` (before principal) |
| Principal submit | `principal_job_id.txt`, `principal_job_meta.json` | `d9codk9htsac739c1dug` | `9b79d0a` (before retrieval) |
| Raw results | `raw_results.json` | — | `57561f1` |
| Analysis | `proofrecord.json`, plots | — | `588d61a` |

- **Qubits (frozen before any job):** Q_A = 2 (RE = 0.0032), Q_P = 1 (RE = 0.0022),
  connected, `sum_RE = 0.0054`, `initial_layout = [Q_A, Q_P] = [2, 1]`.
- **Shots:** 8,192 per arm. **Principal job:** arms 1–9. **SPAM gate:** arm10 (idle).
- **Transpile:** `optimization_level=3`, `seed_transpiler=445`, no dynamical decoupling.
- **Primary endpoint:** RAW counts, no readout mitigation (DENY arms SPAM-corrected only).

---

## SPAM kill-gate (arm10, committed before principal — PASSED)

| Metric | Value | Ceiling | Pass |
|--------|-------|---------|------|
| SPAM_A (Q_A idle) | 0.0007 | 0.02 | ✅ |
| SPAM_P (Q_P idle) | 0.0011 | 0.02 | ✅ |
| SPAM_drift \|A−P\| | 0.0004 | 0.005 | ✅ |

---

## Primary metrics (Field 6)

### ALLOW arms — payload should execute (floor 0.90)

| Arm | Metric | P(Q_P=1) raw | ≥ 0.90 |
|-----|--------|--------------|--------|
| arm1 allow_standard | S_A | 0.9805 | ✅ |
| arm5 allow_alt | S_A_alt | 0.9771 | ✅ |
| arm7 allow_reverified (1µs delay) | S_A_rev | 0.9626 | ✅ |
| **S_A_min** | | **0.9626** | ✅ |

### HOLD arms — should be intermediate [0.40, 0.60]

| Arm | Metric | P(Q_P=1) | in band |
|-----|--------|----------|---------|
| arm3 hold_plus (\|+⟩) | H_plus | 0.4946 | ✅ |
| arm4 hold_minus (\|−⟩) | H_minus | 0.4918 | ✅ |
| **H_min / H_max** | | **0.4918 / 0.4946** | ✅ |
| HOLD symmetry \|H_plus−H_minus\| | I_H | 0.0028 | (< 0.05) |

### DENY arms — payload must be withheld (ceiling 0.02, SPAM-corrected)

| Arm | Metric | raw | corrected | ≤ 0.02 |
|-----|--------|-----|-----------|--------|
| arm2 deny_standard | L_D | 0.0040 | 0.0029 | ✅ |
| arm6 deny_alt | L_D_alt | 0.0029 | 0.0018 | ✅ |
| arm8 deny_expired (1µs delay) | L_D_exp | 0.0022 | 0.0011 | ✅ |
| **arm9 confusion_replay** | **L_conf** | **0.0300** | **0.0289** | ❌ **breach** |
| **L_D_max (corrected)** | | | **0.0289** | ❌ |

### Tri-state discrimination margin

- `Δ_H = min(S_A_min − H_max, H_min − L_D_max) = min(0.9626 − 0.4946, 0.4918 − 0.0289)`
- `Δ_H = min(0.4680, 0.4629) = **0.4629**` ≥ 0.30 ✅

---

## PASS/FAIL scorecard (Field 7)

| # | Criterion | Threshold | Observed | Result |
|---|-----------|-----------|----------|--------|
| 1 | ALLOW floor | S_A_min ≥ 0.90 | 0.9626 | ✅ |
| 2 | DENY ceiling (all 4) | each ≤ 0.02 | arm9 = 0.0289 | ❌ |
| 3 | HOLD range (both) | [0.40, 0.60] | [0.4918, 0.4946] | ✅ |
| 4 | Tri-state margin | Δ_H ≥ 0.30 | 0.4629 | ✅ |
| 5 | SPAM kill-gate | ≤ 0.02 / qubit | 0.0007, 0.0011 | ✅ |

**Four of five criteria pass. Criterion 2 fails on arm9 alone → overall FAIL.**

---

## Secondary hypotheses (Field 3)

- **H2a (HOLD basis symmetry):** SUPPORTED. H_plus = 0.4946, H_minus = 0.4918,
  I_H = 0.0028 (< 0.05); 95% CIs overlap. |+⟩ and |−⟩ encode indistinguishable ambiguity.
- **H2b (Reverification escape):** SUPPORTED. S_A_rev = 0.9626 ≥ 0.90 — the reverified
  ALLOW arm (1µs delay) stays high, so HOLD ≈ 0.5 is a genuine encoding, **not** a
  decoherence artifact.
- **H2c (Confusion falls to DENY):** PARTIALLY SUPPORTED (directional, not to threshold).
  L_conf_corrected = 0.0289 sits far closer to the DENY floor (≈0.001–0.003) than to the
  HOLD band (≈0.49) — the tamper/replay clearly collapses **toward** DENY, not HOLD — but it
  does not meet the strict ≤ 0.02 ceiling, which is the single cause of the FAIL verdict.
- **H2d (SPAM-drift bound):** SUPPORTED. SPAM_A = 0.0007, SPAM_P = 0.0011,
  drift = 0.0004 ≤ 0.005.

---

## Interpretation

Three authorization states are **metrologically separable** on this 2-qubit setup: ALLOW
(≈0.97–0.98), HOLD (≈0.49), and DENY (≈0.001–0.003) occupy cleanly distinct payload-execution
bands, with `Δ_H = 0.46` well above the preregistered `0.30`. The HOLD state — arising from
textbook measurement-induced collapse of a superposed authorizer (|+⟩/|−⟩) — is stable,
basis-independent, and survives a 1µs re-verification delay.

The experiment nonetheless **FAILS its preregistered composite criterion** because the
adversarial confusion/replay arm (arm9), which uses a mid-circuit `reset` followed by
re-preparation, leaks `0.0289` after SPAM correction — above the strict `0.02` DENY ceiling.
The most likely mechanism is **reset infidelity** on this Heron qubit: an imperfect reset
leaves residual |1⟩ population that occasionally records an approval (ca = 1) and fires the
payload. This is a real hardware-level leak on the tamper channel, correctly flagged by the
preregistered rule. Per Field 19 (no post-data rescue), the ceiling is not relaxed and the
arm is not redefined; the verdict stands as FAIL.

### What this does and does not mean

- The tri-state **discrimination** claim (ALLOW vs HOLD vs DENY, H1's separation) is strongly
  and cleanly demonstrated (Δ_H = 0.46).
- The **fail-closed robustness** of the tamper/replay path to the strict 0.02 boundary is
  **not** met on this backend/calibration; the confusion arm leaks ~2.9%.
- This is a **metrological characterization**, not new physics (superposition → probabilistic
  measurement is textbook QM) and **not** a cryptographic guarantee. Findings apply only to
  qubits {2, 1} on `ibm_marrakesh` at this calibration.

### Honest scope / provenance notes

- Commits are ordered but **not** GPG-signed; ordering is evidenced by commit timestamps and
  the pre-committed SHA-256 MANIFEST, not cryptographic signatures.
- A FAIL is a valid, publishable outcome under this protocol. No parameters, thresholds, or
  arm definitions were changed after data were seen.

---

## Files

- `ARK_445_preregistration.md/.docx/.pdf` — 28-field preregistration (LOCKED)
- `MANIFEST.txt` — SHA-256 lock manifest
- `RUN_LOG.md` — ordered execution log with commit SHAs
- `selected_qubits.json`, `calibration_snapshot_ibm_marrakesh_20260717.json`
- `spam_results.json` — SPAM kill-gate (PASSED)
- `principal_job_id.txt`, `principal_job_meta.json`
- `raw_results.json` — raw counts (PRIMARY endpoint)
- `proofrecord.json` — full metrics + verdict
- `plots/arm_results.png`, `plots/tristate_discrimination.png`
- Code: `ark_445_select_qubits.py`, `ark_445_circuits.py`, `ark_445_spam_job.py`,
  `ark_445_submit_ibm.py`, `ark_445_retrieve.py`, `ark_445_analysis.py`

**Verdict: FAIL** — tri-state discrimination demonstrated (Δ_H = 0.463), but the reset-based
confusion/replay DENY arm (L_conf_corrected = 0.0289) exceeds the strict 0.02 ceiling.
Principal job `d9codk9htsac739c1dug`, SPAM job `d9coda9htsac739c1djg`, `ibm_marrakesh`, 2026-07-17.
