# ARK-447 — Pauli Twirling vs. Baseline

**Experiment:** Pauli twirling impact on authorization boundaries (vs. unprotected baseline)  
**Track:** ExecutionProof authorization-boundary characterization  
**Status:** EXECUTED (see `RESULTS.md`)  
**Protocol:** Field 27 (LOCK → SPAM gate → principal job → analyze → verdict)

> **⚠️ As-executed note (read `RESULTS.md` for final numbers).** This README preserves the *originally staged* 3-configuration / 6-circuit design for provenance. The experiment was **executed as Pauli twirling vs. baseline only (4 circuits)** — Dynamical Decoupling was omitted due to scheduling complexity. Additionally, DENY leakage is reported as **raw** (no SPAM subtraction); the SPAM_P |+⟩ measurement is a gating diagnostic, not a correction term. Final tag: **`ark-447-v1.1`** (supersedes `ark-447-v1.0`, which contained an invalid SPAM correction).

---

## Central Question

Do noise-mitigation strategies (**Dynamical Decoupling** or **Pauli Twirling**) improve authorization boundary fidelity on current NISQ hardware compared to an unprotected baseline?

---

## Experimental Design

**Three configurations** tested on the same backend, same qubits, same protocol:
1. **Baseline** (unprotected, like ARK-441)
2. **Dynamical Decoupling (DD)** — π-pulse sequences during idle periods
3. **Pauli Twirling** — randomized Pauli gates to convert coherent errors to stochastic noise

**6 circuits total** (2 boundary conditions × 3 configurations):
- arm1: ALLOW + Baseline
- arm2: DENY + Baseline
- arm3: ALLOW + DD
- arm4: DENY + DD
- arm5: ALLOW + Pauli Twirling
- arm6: DENY + Pauli Twirling

**Shots:** 8192 per circuit

---

## Success Criteria (Per Configuration)

Each configuration is evaluated independently:

1. **S_A ≥ 0.90** (ALLOW discrimination)
2. **L_D_raw ≤ 0.02** (DENY leakage, raw — no SPAM subtraction; see as-executed note)
3. **Δ_B ≥ 0.00** (boundary margin: S_A − L_D_raw − 0.20)

**PASS:** All three criteria met  
**FAIL:** Any criterion violated

---

## Overall Verdict Logic

- **PASS (strong):** All configs pass; at least one mitigation shows improvement
- **PASS (weak):** All configs pass; no significant improvement from mitigation
- **MIXED:** Baseline passes; one or both mitigations fail
- **FAIL:** Baseline fails; boundary unstable

---

## Files

**Preregistration:**
- `ARK_447_preregistration.md` — Full experimental design and rationale

**Code (6 scripts):**
- `ark_447_select_qubits.py` — Select Q_A and Q_P (lowest RE sum, connected)
- `ark_447_circuits.py` — Generate 6 circuits (baseline/DD/twirling)
- `ark_447_spam_job.py` — SPAM baseline job (gating condition)
- `ark_447_submit_ibm.py` — Submit principal job
- `ark_447_retrieve.py` — Retrieve results after job completes
- `ark_447_analysis.py` — Compute metrics and verdict

**Integrity:**
- `MANIFEST.txt` — SHA-256 hashes of all 6 code files (LOCK before hardware)

---

## Execution Sequence (Field 27)

1. **LOCK commit** — Preregistration + code + MANIFEST committed before hardware
2. **Qubit selection** — `python3 ark_447_select_qubits.py`
3. **SPAM gate** — `python3 ark_447_spam_job.py` (must pass to proceed)
4. **Principal job** — `python3 ark_447_submit_ibm.py`
5. **Retrieve** — `python3 ark_447_retrieve.py` (after job completes)
6. **Analyze** — `python3 ark_447_analysis.py`
7. **Document** — Generate `RESULTS.md`, update `RUN_LOG.md`
8. **Tag & publish** — Tag `ark-447-v1.0`, push, open PR

---

## Interpretation Boundaries

✅ Tests Pauli twirling impact on a binary ALLOW/DENY boundary (vs. baseline)  
✅ Comparative ALLOW fidelity with a two-proportion significance test  
✅ Raw DENY leakage reported honestly (SPAM used only as a gating diagnostic)  

❌ NOT a cryptographic security validation  
❌ NOT generalizable beyond this specific backend/qubits/calibration  
❌ NOT error correction (mitigation only; no QEC)  
❌ NOT multi-round or complex authorization policies  

---

## Relation to Prior Work

**ARK-441** established a binary ALLOW/DENY baseline (PASS: S_A=0.9979, L_D=0.0021, Δ_B=0.9779) with **no noise mitigation**.

**ARK-447** tests whether **DD or Pauli twirling** can improve on ARK-441's baseline or maintain fidelity while adding robustness.

---

**Repository:** `derekhone/executionproof-testbeds`  
**Principal Investigator:** Derek Hone, Remnant Fieldworks Inc.  
**Date staged:** 2026-07-17
