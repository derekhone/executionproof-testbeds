# ARK-445b — Tri-State Authorization Discrimination (Reset-Free Retest)

**Experiment ID:** ARK-445b  
**Predecessor:** ARK-445 (VERDICT: FAIL, tag `ark-445-v1.0`)  
**Status:** Preregistered, pre-execution  
**Repository:** [executionproof-testbeds](https://github.com/derekhone/executionproof-testbeds) (branch `execute/ark-445b`)

---

## Central Question

ARK-445 demonstrated strong tri-state ALLOW/HOLD/DENY discrimination (Δ_H=0.463, S_A_min=0.9626, HOLD symmetric at ~0.49) but failed a single criterion: the mid-circuit **reset + re-prepare** confusion/replay arm leaked 0.0289 > the strict 0.02 DENY ceiling.

**ARK-445b asks:** Was that leak caused by mid-circuit reset infidelity, or by a flaw in the tri-state boundary logic itself?

**Method:** Re-run the **identical 8-arm core** (arm1–arm8: standard ALLOW/DENY, HOLD |±⟩, alt/reverified/expired variants) under the same strict protocol, **omitting the reset-based arm9**. If all 8 arms pass the same ≤0.02 DENY ceiling and ≥0.90 ALLOW floor, the diagnosis is: **ARK-445's FAIL was reset-specific, not boundary-intrinsic.**

---

## Experimental Setup

- **Backend:** `ibm_marrakesh` (156-qubit Heron r2)
- **Qubits:** Q_A (authorizer), Q_P (payload) — rule-selected (lowest RE, connected)
- **Arms:** 8 (omitting ARK-445's arm9)
  - 3 ALLOW arms (Q_A=|1⟩ → ca=1 → x(Q_P) → cp≈1)
  - 3 DENY arms (Q_A=|0⟩ → ca=0 → no-op → cp≈0)
  - 2 HOLD arms (Q_A=|±⟩ → ca ∈{0,1} w.p. ~0.5 → cp ∈{0,1} w.p. ~0.5)
- **Shot count:** 8192 per arm
- **Control logic:** Single-register `if_test((ca,1), [XGate()])` — flat, no nesting, **no mid-circuit reset**
- **SPAM gate:** Separate baseline job (Q_A=|0⟩, Q_P=|0⟩ → measure) committed before principal job

---

## Success Criteria (Preregistered)

Identical to ARK-445, applied to the 8-arm set:

1. **ALLOW discrimination:** S_A_min ≥ 0.90 (all three ALLOW arms)
2. **DENY leakage:** L_D_max ≤ 0.02 (all three DENY arms) — **strict ceiling, same as ARK-445**
3. **HOLD symmetry:** H_3, H_4 ∈ [0.40, 0.60]
4. **HOLD imbalance:** I_H = |H_3 − H_4| ≤ 0.10
5. **ALLOW−HOLD separation:** Δ_H ≥ 0.30

**PASS** = all 5 criteria met. **FAIL** = any criterion violated. **INCONCLUSIVE** = SPAM gate failure or backend error.

---

## Protocol (Field 27 Strict Ordering)

1. **LOCK:** Commit preregistration + code + SHA-256 MANIFEST **before** any hardware job
2. **Qubit selection:** Rule-select Q_A, Q_P; commit `selected_qubits.json`
3. **SPAM gate:** Submit baseline job; commit job-ID + results **before** principal job
4. **Principal job:** Submit 8 arms; commit job-ID **before** reading results
5. **Retrieval:** Save raw counts; commit **before** analysis
6. **Analysis:** Compute SPAM-corrected metrics, determine verdict; commit proofrecord + plots
7. **RESULTS:** Write report; commit

**No rescue** — if verdict is FAIL, it is reported honestly. No post-data corrections.

---

## Interpretation

- **If PASS:** ARK-445's FAIL was caused by mid-circuit reset infidelity (arm9), not by the tri-state boundary logic. The 8 reset-free arms are sound.
- **If FAIL (same arms as ARK-445 passed):** Likely backend drift or calibration change; inconclusive diagnostic.
- **If FAIL (different arm):** New failure mode unrelated to reset; suggests boundary-intrinsic issue.

This is a **bounded diagnostic retest**, not a claim that tri-state authorization is universally sound. It isolates one variable (presence/absence of mid-circuit reset) to determine the root cause of ARK-445's single failing criterion.

---

## Files

- `ARK_445b_preregistration.md` — this preregistration (full detail)
- `README.md` — this file (summary)
- `MANIFEST.txt` — SHA-256 hashes of all files at LOCK time
- `ark_445b_select_qubits.py` — qubit selection script
- `ark_445b_circuits.py` — circuit generation (8 arms + SPAM)
- `ark_445b_spam_job.py` — SPAM baseline job
- `ark_445b_submit_ibm.py` — principal job submission
- `ark_445b_retrieve.py` — result retrieval
- `ark_445b_analysis.py` — SPAM-corrected analysis + verdict

*(Scripts to be committed at LOCK time)*

---

## License

- **Code:** MIT (same as `executionproof-testbeds`)
- **Data/results:** CC BY 4.0

---

## Contact

Derek Hone  
Remnant Fieldworks Inc.  
Westerville, Ohio

- https://executionproof.io
- https://builderexecutionproof.io

**ExecutionProof™** — *If it cannot be verified, it cannot execute.*
