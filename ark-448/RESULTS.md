# ARK-448 Results — Dynamical Decoupling vs. Baseline

**Outcome: ABORTED AT SPAM GATE (honest gate-stop).**
**No DD-vs-baseline data was obtained. No verdict is claimed.**

---

## Summary

ARK-448 was locked, the qubit pair was selected, and the preregistered SPAM gate was
executed on real IBM hardware (`ibm_marrakesh`). **The SPAM gate FAILED**, so — per the
LOCKED preregistration — the principal 4-arm job was **not** submitted and execution was
halted. This is a preregistered abort, not a result about dynamical decoupling.

## What ran

| Step | Status |
|------|--------|
| LOCK (preregistration + code, tag `ark-448-v1.0-lock`) | ✅ done |
| Qubit selection (Q_A=1, Q_P=2, `ibm_marrakesh`) | ✅ done |
| SPAM gate (job `d9cqji4inv1c73ao54eg`, 2048 shots) | ❌ **FAILED** |
| Principal 4-arm job (8192 shots) | ⛔ **NOT RUN** (halted per protocol) |

## SPAM gate detail

| Check | Measured | Threshold | Pass? |
|-------|----------|-----------|-------|
| SPAM_A (authorizer \|1⟩ readout error) | 0.01025 | ≤ 0.02 | ✅ |
| SPAM_P (payload \|+⟩ symmetry, \|P(1)−0.5\|) | **0.02197** | ≤ 0.02 | ❌ |

The payload readout symmetry deviated **0.02197** from the ideal 0.5, exceeding the
preregistered ±0.02 tolerance by **0.00197**. At 2048 shots the binomial standard deviation
at p=0.5 is ≈0.011, so the observed deviation is **≈2.0σ** — consistent with a marginal
statistical fluctuation and/or minor readout drift on the calibration snapshot used.

## Why we did not re-run or loosen the gate

The ExecutionProof protocol is **preregistration-first**. The LOCKED preregistration
(`ARK_448_preregistration.md`, Section 5) fixed the SPAM_P tolerance at ±0.02 *before*
execution and does **not** permit:

- re-running the gate until it passes (that would be selection bias / p-hacking on the gate),
- loosening the threshold post-hoc, or
- proceeding to the principal job on a failed gate.

Honoring the lock, we recorded the failure and stopped. This mirrors the honest FAIL in
ARK-445: the value of the protocol is precisely that it halts on marginal conditions instead
of manufacturing a clean-looking result.

## What this does and does not mean

- It does **NOT** mean dynamical decoupling failed, succeeded, or was measured at all — the
  DD-vs-baseline comparison never executed.
- It **does** mean the readout condition on this snapshot/qubit fell just outside the
  preregistered tolerance, and the gate did its job.
- Budget was conserved: the expensive principal job was never submitted.

## Reproducing / re-attempting

A future ARK-448 attempt would re-lock (new tag), re-select qubits against a fresh
calibration snapshot, and re-run the SPAM gate. Because the gate is preregistered, a
re-attempt is a **new locked run**, not a silent retry of this one. This run stands in the
record as a genuine gate-stop.

## Files

- `proofrecord.json` — machine-readable gate-stop record (real SPAM data, no principal data).
- `spam_results.json` — raw SPAM gate counts and computed errors.
- `selected_qubits.json` — selected pair and readout errors.
- `calibration_snapshot_ibm_marrakesh_20260717.json` — backend calibration at submission.
- `RUN_LOG.md` — chronological execution log.
