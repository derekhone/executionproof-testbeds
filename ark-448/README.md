# ARK-448 — Dynamical Decoupling vs. Baseline Under an Idle Window

**Status: ABORTED AT SPAM GATE (honest gate-stop). No DD-vs-baseline data obtained.**

Part of the ExecutionProof ARK series (Authorization-boundary Repeatability Kit) by
Derek Hone (Remnant Fieldworks Inc.).

## What this experiment asked

When an idle window (τ = 20 µs) is inserted before an authorization-boundary CNOT, does an
XX dynamical-decoupling sequence during that window improve the boundary (higher ALLOW
retention / lower DENY leakage) versus a bare idle delay? This closes the DD gap explicitly
deferred by ARK-447.

## What happened

The preregistered SPAM gate failed: the payload |+⟩ readout symmetry deviated 0.02197 from
0.5, just over the ±0.02 tolerance (≈2σ at 2048 shots). Per the LOCKED preregistration the
principal 4-arm job was **not** run and execution halted. See `RESULTS.md` and `RUN_LOG.md`.

This is a genuine preregistered abort — the protocol halting on a marginal condition — not a
result about dynamical decoupling and not a failure to report.

## Layout

```
ark-448/
├── ARK_448_preregistration.md   # LOCKED design (tag ark-448-v1.0-lock)
├── ark_448_select_qubits.py     # qubit pair selection
├── ark_448_spam_job.py          # SPAM gate (this is where the run stopped)
├── ark_448_circuits.py          # 4-arm DD/baseline circuits (not executed on hardware)
├── ark_448_submit_ibm.py        # principal-job submission (not executed)
├── ark_448_retrieve.py          # results retrieval (not executed)
├── ark_448_analysis.py          # DD-vs-baseline analysis (not executed)
├── MANIFEST.txt                 # SHA-256 of locked files
├── MANIFEST_v1.1.txt            # + post-execution artifacts
├── selected_qubits.json         # Q_A=1, Q_P=2 on ibm_marrakesh
├── calibration_snapshot_*.json  # backend calibration at submission
├── spam_results.json            # REAL SPAM gate data (gate_passed=false)
├── proofrecord.json             # machine-readable gate-stop record
├── RESULTS.md                   # human-readable outcome
└── RUN_LOG.md                   # chronological log
```

## Provenance

- LOCK tag: `ark-448-v1.0-lock` (commit `e947b1c`)
- SPAM job id: `d9cqji4inv1c73ao54eg` on `ibm_marrakesh`
- Principal job: none (halted at gate)
