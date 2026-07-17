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

- **Committed BEFORE any job.** Q_A=2 (RE=0.0032), Q_P=1 (RE=0.0022), connected, sum_RE=0.0054.
- **Rule:** 2 connected qubits, RE(Q_A) < 0.02, RE(Q_P) < 0.02, argmin(RE_A + RE_P); lower-RE qubit assigned Q_P (payload/PRIMARY).
- **Selection timestamp (UTC):** 2026-07-17T01:34:14.221759+00:00
- **initial_layout=[Q_A, Q_P]=[2, 1]**

## Step 3-4 — SPAM kill-gate (committed BEFORE principal job)

- **SPAM job id:** `d9coda9htsac739c1djg`
- **SPAM_A (Q_A idle):** 0.0007 (ceiling 0.02) — PASS
- **SPAM_P (Q_P idle):** 0.0011 (ceiling 0.02) — PASS
- **SPAM_drift:** 0.0004 (ceiling 0.005) — OK
- **Gate:** PASSED. Principal job authorized to proceed.

## Principal 9-arm job
- **Backend:** ibm_marrakesh
- **Instance:** open-instance
- **Physical qubits [Q_A, Q_P]:** [2, 1]
- **Shots per arm:** 8192
- **Arms:** 9 (arm1_allow_standard, arm2_deny_standard, arm3_hold_plus, arm4_hold_minus, arm5_allow_alt, arm6_deny_alt, arm7_allow_reverified, arm8_deny_expired, arm9_confusion_replay)
- **Arm expectations:** {'arm1_allow_standard': 'ALLOW', 'arm2_deny_standard': 'DENY', 'arm3_hold_plus': 'HOLD', 'arm4_hold_minus': 'HOLD', 'arm5_allow_alt': 'ALLOW', 'arm6_deny_alt': 'DENY', 'arm7_allow_reverified': 'ALLOW', 'arm8_deny_expired': 'DENY', 'arm9_confusion_replay': 'DENY', 'arm10_spam_idle': 'SPAM'}
- **Arm classes:** {'arm1_allow_standard': 'allow', 'arm2_deny_standard': 'deny', 'arm3_hold_plus': 'hold', 'arm4_hold_minus': 'hold', 'arm5_allow_alt': 'allow', 'arm6_deny_alt': 'deny', 'arm7_allow_reverified': 'allow', 'arm8_deny_expired': 'deny', 'arm9_confusion_replay': 'deny', 'arm10_spam_idle': 'idle_spam'}
- **Optimization level:** 3 (seed_transpiler=445, no dynamical decoupling)
- **JOB ID:** `d9codk9htsac739c1dug`
- **Submission timestamp (UTC):** 2026-07-17T01:35:12.046870+00:00
- **SPAM job id:** `d9coda9htsac739c1djg`
- **SPAM baselines:** SPAM_A=0.0007, SPAM_P=0.0011, drift=0.0004
- **Transpiled depths:** {'arm1_allow_standard': 4, 'arm2_deny_standard': 3, 'arm3_hold_plus': 6, 'arm4_hold_minus': 6, 'arm5_allow_alt': 4, 'arm6_deny_alt': 3, 'arm7_allow_reverified': 5, 'arm8_deny_expired': 4, 'arm9_confusion_replay': 6}

- **Job-ID committed BEFORE result retrieval (Field 27 step 7).**

## Step 8-11 — Retrieval / analysis / results

- _(pending)_
