# ARK-448 Run Log

**Experiment:** ARK-448 — Dynamical Decoupling vs. Baseline Under an Idle Window
**Backend:** ibm_marrakesh (IBM Quantum open plan)
**Date:** 2026-07-17
**Final outcome:** ABORTED AT SPAM GATE (honest gate-stop)

---

## Chronology

1. **LOCK.** Preregistration and all analysis code committed on branch `execute/ark-448`
   (branched from `origin/main` @ `bb3cf66`, which includes merged ARK-447). Commit `e947b1c`,
   tag `ark-448-v1.0-lock`. `MANIFEST.txt` records SHA-256 of the 7 locked files.

2. **Offline validation.** Full pipeline validated with a noiseless Aer simulation before any
   hardware submission; all simulator stub files were deleted so no simulated data was ever
   committed as hardware data.

3. **Budget check.** IBM open-plan budget confirmed limited (~186 s remaining pre-run). Backends
   ibm_fez, ibm_marrakesh, ibm_kingston all operational.

4. **Qubit selection.** `ark_448_select_qubits.py` → Q_A=1, Q_P=2 on ibm_marrakesh
   (sum readout error 0.00537, lowest connected pair; series-consistent with ARK-447).
   → `selected_qubits.json`, `calibration_snapshot_ibm_marrakesh_20260717.json`.

5. **SPAM gate.** `ark_448_spam_job.py` submitted (job `d9cqji4inv1c73ao54eg`, 2048 shots/circuit).
   Result:
   - SPAM_A error = 0.01025 (≤ 0.02) → **PASS**
   - SPAM_P |P(1)−0.5| = 0.02197 (≤ 0.02 required) → **FAIL** (over by 0.00197, ≈2.0σ at 2048 shots)
   - **gate_passed = false**
   → `spam_results.json`, `spam_run.log`.

6. **HALT per protocol.** Because the SPAM gate failed, the principal 4-arm job was **not** submitted.
   No `raw_results.json`, no `principal_job_*` files exist. The LOCKED preregistration does not permit
   re-running the gate or loosening the threshold, so execution stopped.

7. **Gate-stop record.** `proofrecord.json` written documenting the abort (real SPAM data only,
   explicit no-fabrication statement, no principal data). `RESULTS.md`, `README.md`, and
   `MANIFEST_v1.1.txt` added.

## Budget accounting

- Post-run IBM budget check: **~183 s remaining, ~417 s consumed** for the session.
- The SPAM job used minimal budget; the principal job never ran, conserving remaining seconds.
- No shot-reduction contingency (Section 4) was triggered because the run never reached the
  principal job.

## Deviations from preregistration

None. The abort is an expected, preregistered branch (SPAM gate must pass before principal job).
No criteria were altered.
