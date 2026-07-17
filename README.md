# ExecutionProof Testbeds

**Product:** ExecutionProof™ — *"If it cannot be verified, it cannot execute."*
**Track:** ARK authorization-boundary series — Verify-Before-Execute (VBE) characterization on IBM Quantum hardware
**Maintainer:** Derek Hone — Remnant Fieldworks Inc.

---

## What this repository is

This repository (`executionproof-testbeds`) holds the **ARK authorization-boundary experiment series** — a set of preregistered,
hardware-executed metrological tests of a verify-then-execute (VBE) authorization boundary on IBM
Quantum superconducting devices. Each experiment asks a narrow, falsifiable question about whether an
authorization decision can be reliably enforced at the moment of execution, and each is published with
its full preregistration, code, raw job data, and analysis.

This is **applied verification-layer R&D** (the ExecutionProof product lineage). It is **distinct from**
the UIP Phase 1 physics falsification program (a separate academic effort with its own repository and DOI).
See [`PROVENANCE.md`](PROVENANCE.md) for the relocation history and the relationship between the two tracks.

---

## Experiments

| ID | Title | Verdict | Backend | Key result |
|----|-------|---------|---------|-----------|
| **ARK-441** | VBE authorization boundary (baseline) | ✅ PASS | `ibm_marrakesh` | Binary ALLOW/DENY boundary established (Δ_B ≥ 0.70) |
| **ARK-446** | Cross-device replication | ✅ PASS | `ibm_marrakesh` | L_D_corrected=0.0020, S_A=0.9885, Δ_B=0.9862 |
| **ARK-442** | Delay-boundary characterization | ✅ PASS | `ibm_marrakesh` | L_expired=0.0000, S_reverified=0.9916, Δ_B=0.9877 |
| **ARK-444** | Decision-to-execution integrity | ✅ PASS | `ibm_marrakesh` | Fail-closed on every alteration/replay, Δ_B=0.9696 |
| **ARK-443** | Two-of-three quorum authorization | ✅ PASS | `ibm_marrakesh` | Quorum enforced; single compromised channel denied, Δ_B=0.9685 |

All five carry release tags `ark-4NN-v1.0` and are published to Zenodo (DOI **10.5281/zenodo.21398676**).

---

## Method invariants (applied to every experiment)

1. **Preregistration-first.** A 28-field preregistration + all code + a SHA-256 `MANIFEST.txt` are committed
   **before any hardware job is submitted.** The lock commit hash is recorded in each experiment's `RUN_LOG.md`.
2. **Hard ordering (Field 27).** Qubit selection → SPAM kill-gate → **job ID committed before results are read** →
   raw counts → analysis → results. Commit timestamps prove the ordering.
3. **SPAM kill-gate.** An in-situ state-preparation-and-measurement baseline is measured and committed *before*
   the principal job; if it exceeds the preregistered threshold, the principal job is not submitted.
4. **No rescue after failure.** A failed hypothesis is reported as a failure. No post-data threshold changes,
   arm redefinitions, or re-analysis may change a verdict.
5. **Raw counts, no mitigation.** Metrics are computed from raw device counts; SPAM correction is applied only
   where preregistered and always reported alongside the raw value.

## Governing principles

> **Proof Before Power. Prediction Before Measurement. No Rescue After Failure.**

## Reproducibility

Every experiment can be re-run on a free IBM Quantum open-plan account. Requirements are in
[`requirements.txt`](requirements.txt); per-experiment `README.md` files describe the specific setup.

## License

Code and data released under the license in [`LICENSE`](LICENSE). Dataset also archived under CC BY 4.0 on Zenodo.
