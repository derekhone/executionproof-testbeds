# ARK-445 — RUN LOG

Remnant Fieldworks Inc. — Derek Hone
Tri-State Authorization Discrimination (ALLOW / HOLD / DENY) on ibm_marrakesh (Heron r2).

Protocol: Proof Before Power. Prediction Before Measurement. No Rescue After Failure.
Each step below writes files + a git commit; commit timestamps prove ordering (Field 27).

## Step 1 — LOCK (preregistration + code + MANIFEST)

- **LOCK commit SHA:** `b0b56b08e58db02040f30937f487f1076cac4de9`
- **Branch:** `execute/ark-445`
- **Locked at (UTC):** 2026-07-17T01:32:55Z (MANIFEST generation timestamp)
- **Locked files (SHA-256 in MANIFEST.txt):** ARK_445_preregistration.md, README.md,
  ark_445_select_qubits.py, ark_445_circuits.py, ark_445_spam_job.py,
  ark_445_submit_ibm.py, ark_445_retrieve.py, ark_445_analysis.py
- **Pre-lock validation (no QPU cost):**
  - Ideal AerSimulator logic check: ALLOW arms P(Q_P=1)~1.000; DENY arms ~0.000;
    HOLD arms ~0.497 (H_plus ~ H_minus, symmetric); confusion/replay ~0.000 (DENY);
    SPAM idle ~0.000.
  - Real-backend transpile check on ibm_marrakesh (opt_level=3, seed_transpiler=445):
    all 9 principal arms + arm10 transpile cleanly; if_test (`if_else`) blocks preserved;
    HOLD H decomposes to rz/sx; arm9 reset+measure intact.
- **No IBM Quantum hardware job has been submitted as of the LOCK commit.**

## Step 2 — Qubit selection

- _(pending)_

## Step 3-4 — SPAM kill-gate

- _(pending)_

## Step 6-7 — Principal job

- _(pending)_
