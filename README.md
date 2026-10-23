> **Repository Role:** Preregistered Experiment Series — ExecutionProof Authorization Boundaries · Part of the [Remnant Fieldworks](https://remnantfieldworks.com) research and product ecosystem

### Reference vs. Production

This repository publishes research/reference material or public integration interfaces; its specific scope is below. It does not ship RF's private production backend. Experimental behavior, fixture policies, local/test keys and published results apply only to the identified implementation and stated conditions. Do not use public test keys as production trust roots or treat fixture conformance as proof of production security. This notice does not change existing licenses, results, preregistrations or preserved failures.

> **Advisory (2026-10-23): execution-binding defect in ARK-493–498, with an analog in ARK-499–503.** In the published reference code the gate verified the hash of `canonical_json`, but on ALLOW the tool was dispatched with a separate `parameters` object that was never re-checked against it, so parameters altered after hashing could execute under an ALLOW decision. **Demonstrated:** ARK-493–498, and the ARK-500 CI/CD adapter path (isolated rerun). **Suspected, not executed:** the ARK-499 PostgreSQL and ARK-502 paths (PostgreSQL 17 server binaries were unavailable in the review environment). The fix-forward correction and regression tests are in this change (`ark-493-498/tests/`, `ark-499-503/tests/`). Original published PASS outcomes remain valid only for the scenarios actually tested; those scenarios did not exercise this path, and the outcomes are not withdrawn or altered. Historical ProofRecords, ledgers and preserved failures are unchanged. RF's private production backend is a separate implementation: the corresponding defect was not reproduced in prior isolated source tests; live deployment and real-executor non-bypassability remain untested. Details: `ark-493-498/README.md`, `ark-499-503/README.md`.

This is a collection of experiment-specific reference implementations and evidence. Key types, signing behavior and enforcement models vary by experiment. Neither one unsigned example nor one signed example describes the whole collection.


**Where this fits:** [ExecutionProof](https://executionproof.io) is an independent pre-execution governance layer for consequential AI actions — returning ALLOW / HOLD / DENY before Stripe or any downstream system is ever called. Payment authorization is the first production deployment boundary; the same architecture governs infrastructure commands, data release, access changes, and other irreversible actions. This repository records preregistered authorization-boundary experiments that validate the ALLOW/HOLD/DENY enforcement claims.

---

# ExecutionProof Testbeds

**Product:** ExecutionProof™ — *"If it cannot be verified, it cannot execute."*
**Track:** ARK authorization-boundary series — Verify-Before-Execute (VBE) characterization on IBM Quantum hardware
**Maintainer:** Derek Hone — Remnant Fieldworks Inc.

---

## Production cryptographic custody status

ExecutionProof has implemented and internally verified hardware-backed ML-DSA-65 signing for newly generated ProofRecords using AWS KMS. Formal RF-100 §8.4 conformance remains pending independent external review.

Operationally, the reported production posture is:

- signing occurs through the AWS KMS `Sign` operation;
- private ML-DSA-65 signing material does not enter the application process;
- production reports `hardware_backed = true`;
- in-process signing is disabled for production ProofRecords;
- new ProofRecords verify against the active HSM-backed key;
- historical ProofRecords remain verifiable through retired public keys;
- tampered records fail verification;
- key rotation preserves the existing evidence chain.

The external review should specifically confirm canonical payload hashing, deterministic serialization, algorithm and encoding identifiers, domain separation, replay protection, key-version binding, and rotation/retirement/revocation behavior.

---

## What this repository is

This repository (`executionproof-testbeds`) holds the **ARK authorization-boundary experiment series** — a set of preregistered,
hardware-executed metrological tests of a verify-then-execute (VBE) authorization boundary on IBM
Quantum superconducting devices. Each experiment asks a narrow, falsifiable question about whether an
authorization decision can be reliably enforced at the moment of execution, and each is published with
its full preregistration, code, raw job data, and analysis.

This is **applied verification-layer R&D** (the ExecutionProof product lineage). It is **distinct from**
the Coherent Inheritance Framework (CIF) Phase 1 physics falsification program — formerly published under the working title Unified Inheritance Physics (UIP) — a separate academic effort with its own repository and DOI.
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

## Enterprise Agent Boundary Testbed (ARK-493 → ARK-498)

A **non-quantum, production-like** enforcement series lives in
[`ark-493-498/`](ark-493-498/). Unlike the hardware ARKs above, the boundary here
is a real software enforcement point (and, in ARK-498, a real HTTP/loopback-TCP
socket). It tests whether ExecutionProof *mechanically enforces* an authorization
decision at a real boundary — not merely records it.

| Experiment | Focus | Result |
|-----------|-------|--------|
| **ARK-493** | Enforcement boundary under adversarial load (6 paths × 15 cells) | ✅ PASS — 90/90 |
| **ARK-494** | Semantic boundary: deep argument mutation | ✅ PASS — 13/13 |
| **ARK-495** | Temporal boundary: authority change mid-flight | ✅ PASS — 11/11 |
| **ARK-496** | Multi-agent delegation & self-approval defense | ✅ PASS — 8/8 |
| **ARK-497** | Independently reconstructable ProofRecord (+ tamper detection) | ✅ PASS — 30/30 |
| **ARK-498** | Networked production-like performance | ✅ PASS — 6/6 hard criteria |

161 scored cases, 161 PASS, 0 enforcement leaks, GATE-STOP not triggered, dual-guard
agreement on every record. Frozen preregistration v1.1 (SHA-256
`464b9fb8be9d6cca052f236dc9deec9f8e89b781cafc58701e79b2d05d52952a`). See
[`ark-493-498/README.md`](ark-493-498/README.md) for the full breakdown and the
mandatory ARK-498 performance-characterization caveat.

---

## Standing corpus (reconciled, all series to date)

**72 preregistered experiments · 232 case records · 229 PASS · 2 FAIL ·
1 GATE-STOP · 9 repositories.** The 2 FAIL and 1 GATE-STOP records are retained
unchanged — preserving negative results is part of the methodology.

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

### License scope map

- Root LICENSE: MIT for material within its applicable scope.
- executionproof-pq-verification-pack/LICENSE: expressly overrides root MIT inside that directory with reviewer-use terms. Its associated Zenodo terms are separately stated as CC BY-NC-ND 4.0. Those notices are unchanged.
- Experiment-specific document/data and third-party notices retain their stated scope. Do not infer one uniform license across the collection.
- This map does not license absent private implementations or alter historical grants, experiments, failures or releases.
