# ARK-448 Preregistration — Dynamical Decoupling vs. Baseline Under an Idle Window

**Status:** 🔒 LOCKED (preregistered before execution)
**Experiment ID:** ARK-448
**Series:** ExecutionProof ARK (Authorization-boundary Repeatability Kit)
**Author:** Derek Hone (Remnant Fieldworks Inc.)
**Date:** 2026-07-17
**Protocol:** Field 27 (LOCK → SPAM gate → principal job → analyze → verdict)

---

## 1. Motivation

ARK-447 compared **Pauli Twirling vs. Baseline** on the single-round authorization boundary and
explicitly **omitted Dynamical Decoupling (DD)** due to circuit-scheduling complexity. ARK-448 closes
that gap: it is the deferred DD experiment.

DD suppresses **dephasing (T2)** noise that accumulates while a qubit sits idle. Real authorization
workflows are not instantaneous — a decision qubit may hold its state across an idle window before the
boundary gate fires. ARK-448 asks a concrete, falsifiable question:

> **When an idle window is deliberately inserted before the authorization boundary gate, does an
> XX dynamical-decoupling sequence during that window improve the authorization boundary
> (higher ALLOW retention S_A and/or lower DENY leakage L_D) relative to a bare idle delay?**

## 2. Hypothesis (stated before execution)

- **H1 (DD helps):** DD arms show higher S_A and/or lower L_D_raw than baseline arms.
- **H0 (null):** DD produces no statistically significant change (Δ within noise), OR DD is net
  negative because the extra X-pulse gate overhead adds more error than the dephasing it removes.

**We explicitly pre-commit to reporting whichever outcome occurs, including a null or negative
result.** The dominant decay channel of the ALLOW authorizer state |1⟩ during idle is **amplitude
damping (T1)**, which DD does *not* mitigate; DD principally protects the superposition (T2). We
therefore consider a null / modest / negative DD effect a genuinely plausible and scientifically
valid outcome, consistent with the honest-reporting ethos demonstrated by ARK-445 (FAIL).

## 3. Design

Four arms, submitted in a **single principal job** on one backend and one qubit pair, so DD-on vs
DD-off is compared with no cross-job confound. DD is **baked into the circuits** (explicit delays +
X pulses), not applied as a runtime option, ensuring baseline and DD arms differ only by the pulse
insertion.

| Arm | Authorizer (Q_A) | Idle window | DD sequence |
|-----|------------------|-------------|-------------|
| arm1_ALLOW_baseline | \|1⟩ (X) | τ bare delay | none |
| arm2_DENY_baseline  | \|0⟩      | τ bare delay | none |
| arm3_ALLOW_dd       | \|1⟩ (X) | τ            | XX |
| arm4_DENY_dd        | \|0⟩      | τ            | XX |

- **Payload (Q_P):** prepared in |+⟩ (H), as in ARK-447.
- **Boundary gate:** CNOT(Q_A → Q_P) after the idle window.
- **Idle window:** **τ = 20 µs**, applied to BOTH Q_A and Q_P after state preparation and before the
  boundary CNOT.
- **DD sequence (XX):** `delay(τ/4) – X – delay(τ/2) – X – delay(τ/4)` on both qubits (net idle = τ,
  two X pulses). This is the standard two-pulse CPMG-style refocusing sequence.
- **Measurement & analysis convention:** identical to ARK-447 (measure Q_A → c[0], Q_P → c[1];
  metrics computed on the same classical bit as ARK-447 for direct comparability).

## 4. Fixed parameters (LOCKED)

- **Backend:** `ibm_marrakesh` (series-consistent). Fallback `ibm_fez` only if marrakesh is
  non-operational at submission time; the backend actually used is recorded in the proofrecord.
- **Qubit selection:** lowest connected-pair readout-error sum (same selector as ARK-447).
- **Shots:** principal job **8192/circuit**; SPAM gate **2048/circuit**. If the post-SPAM budget check
  shows < 90 s remaining, principal shots drop to 4096 (recorded in RUN_LOG). No other design change.
- **Transpilation:** `optimization_level=1`, delays preserved (scheduling honored on hardware).

## 5. SPAM gate (must pass before principal job)

- SPAM_A: prepare |1⟩ on Q_A, measure Z. Require readout error ≤ 0.02.
- SPAM_P: prepare |+⟩ on Q_P, measure Z. Require |P('1') − 0.5| ≤ 0.02.
- **SPAM_P is a GATING diagnostic ONLY.** Per the ARK-447 v1.1 correction, the ~0.5 outcome is the
  expected physics of a superposition and is **NEVER subtracted** from DENY leakage. DENY leakage is
  reported RAW.

## 6. Metrics (per arm)

- **S_A** = fraction of ALLOW shots reading '1' on the authorizer classical bit.
- **L_D_raw** = fraction of DENY shots reading '1' on the same bit (RAW leakage, no SPAM subtraction).
- **Δ_B** (boundary margin) = S_A − L_D_raw − 0.20.

## 7. Pass criteria (per configuration)

- S_A ≥ 0.90
- L_D_raw ≤ 0.02
- Δ_B ≥ 0.00

A configuration PASSES only if all three hold.

## 8. Verdict rules (stated before execution)

- **PASS (strong):** both baseline and DD pass AND DD improves S_A or L_D_raw.
- **PASS (weak):** both pass but DD shows no improvement (null).
- **MIXED:** exactly one of {baseline, DD} passes.
- **FAIL:** neither passes (e.g., the 20 µs idle window degrades the boundary below threshold —
  an honest negative demonstrating idle-time sensitivity).

**Primary statistical comparison:** two-proportion z-test on S_A (DD vs baseline) and on L_D_raw
(DD vs baseline). Significance threshold α = 0.05 (two-sided).

## 9. Interpretation boundaries

- Results apply only to this backend, qubit pair, calibration snapshot, and τ = 20 µs.
- This is a hardware noise-mitigation study, **not** a cryptographic security validation.
- DD is error *mitigation*, not error *correction*; no QEC is used.
- Single-round binary boundary only; not a multi-round or production protocol.
- The authorizer |1⟩ state decays primarily via T1, which DD does not address; a limited DD benefit
  is expected and does not indicate methodological failure.

## 10. Files (to be committed at LOCK)

- `ARK_448_preregistration.md` (this file)
- `ark_448_select_qubits.py`
- `ark_448_spam_job.py`
- `ark_448_circuits.py`
- `ark_448_submit_ibm.py`
- `ark_448_retrieve.py`
- `ark_448_analysis.py`
- `MANIFEST.txt` (SHA-256 of all locked files)

Post-execution artifacts (`selected_qubits.json`, `spam_results.json`, `principal_job_*`,
`raw_results.json`, `proofrecord.json`, `RESULTS.md`, `RUN_LOG.md`, `README.md`) are added after the
run and never alter the locked preregistration.

---

**LOCK statement:** The hypothesis, arms, idle window, DD sequence, shot counts, SPAM gate, metrics,
pass criteria, and verdict rules above are fixed prior to execution. Any deviation forced by hardware
(e.g., shot reduction under budget) is logged in `RUN_LOG.md` and does not alter these criteria.
