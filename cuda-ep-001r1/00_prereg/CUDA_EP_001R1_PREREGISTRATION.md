# CUDA-EP-001R1 - Preregistration

**Experiment ID:** CUDA-EP-001R1
**Title:** Real GPU Execution Boundary - Remediation Retest
**Remediates:** CUDA-EP-001 (frozen record: `PARTIAL_FAIL | GPU-C8 CONFIRMED; GPU-C5 expected HOLD -> actual ALLOW; C6/C7 scope limitations preserved`)
**Owner:** Remnant Fieldworks Inc.
**Date preregistered:** 2026-10-02
**Status at preregistration:** Source frozen, expected outcomes frozen, NOT YET EXECUTED on real GPU
**Classification:** RESEARCH ONLY - NOT PRODUCTION

> This document is written and SHA-256-frozen BEFORE the real GPU run. The
> original CUDA-EP-001 package and its recorded result are NOT modified,
> overwritten, amended, or relabeled by this experiment. CUDA-EP-001 stands
> exactly as recorded.

---

## 1. Purpose

CUDA-EP-001 produced the first real-GPU (Tesla T4) ExecutionProof boundary result.
It was an honest PARTIAL_FAIL: GPU-C8 (exclusive launcher) CONFIRMED, but three
limitations were recorded and preserved:

- **C5** The frozen control engine keyed only on `nvidia-smi` presence, so the
  intended control-HOLD could not be induced on a live GPU without removing the
  GPU (which collapses to `BLOCKED_NO_GPU`). Observed: expected HOLD, actual ALLOW.
- **C6** `gateway.evaluate()` had no signature-verification branch; mutation was
  caught only by an external ProofRecord verifier, not as a native gateway verdict.
- **C7** The constraint engine DENYd only on an EMPTY target capability and never
  compared the requested capability against the detected physical device capability.

CUDA-EP-001R1 remediates **exactly these three** weaknesses and retests them on
real NVIDIA hardware, plus the two controls (C0 clean ALLOW, C8 exclusive
launcher). Nothing else is changed.

---

## 2. Scope (frozen)

**In scope (the only code changed vs CUDA-EP-001):**
- `source/gpu_gateway_r1.py` - remediated gateway (new file; original `gpu_gateway.py` untouched)
- `source/gpu_policy_r1.json` - remediation policy (adds `required_control_state`)

**Carried verbatim, byte-identical from CUDA-EP-001 (NOT changed):**
- `source/kernels/elementwise_add.cu` (SHA-256 `268d125fe316156e9da44852afeca54838974a4a90643c375d233b5491f89b0d`)
- `source/elementwise_add_launcher.py`
- `source/gpu_functional_tests.py`, `source/gpu_hidden_tests.py`

**Cases retested (ONLY these five):** R1-C0, R1-C5, R1-C6, R1-C7, R1-C8.
The full CUDA-EP-001 C1-C4 matrix is **not** rerun (out of scope; those cases
already matched preregistration in CUDA-EP-001).

---

## 3. Remediation design (frozen)

### C5 - real control-state predicate
Replace the `nvidia-smi`-presence check with a genuine predicate that compares an
explicit `control_state_token` in the Request Contract against the policy field
`required_control_state` (`"LAUNCH_WINDOW_OPEN"`). The predicate is **independent
of GPU presence**, so a control HOLD is inducible while a real GPU remains fully
available.
- token == required -> control PASS
- token != required, or token absent -> control HOLD (no launch)

### C6 - native gateway VERIFICATION_FAILURE
Add a ProofRecord signature-verification engine inside `evaluate()`, executed
BEFORE any capability release. The contract carries a `proofrecord` (`body`,
`dilithium3_signature_b64`, `public_key_b64`). The gateway recomputes the
canonical body and verifies the Dilithium3 signature.
- signature valid -> verification PASS
- signature invalid / body mutated / missing -> native `VERIFICATION_FAILURE`
  verdict and NO launch.

### C7 - true requested-vs-detected compute-capability comparison
Detect the physical device compute capability (`nvidia-smi --query-gpu=compute_cap`,
torch fallback) and compare it to the contract's `target_compute_capability`.
- required empty -> DENY (absent)
- required not in accepted list -> DENY (not accepted)
- required != detected (two real non-empty values) -> `DENY_CAP_MISMATCH`
- required == detected (and accepted) -> PASS

---

## 4. Preregistered expected outcomes (frozen BEFORE execution)

| Case | Condition | Expected verdict | Launch |
|---|---|---|---|
| R1-C0 | clean ALLOW control | **ALLOW** | kernel launches |
| R1-C5 | unmet real control-state predicate | **HOLD** | NO launch |
| R1-C6 | mutated ProofRecord | **VERIFICATION_FAILURE** (native gateway) | NO launch |
| R1-C7 | requested != detected compute capability | **DENY** | NO launch |
| R1-C8 | exclusive launcher control | **NO_LAUNCH_WITHOUT_ALLOW** (executed set == `["R1-C0"]`) | launch only for the exact C0 artifact |

**Pass condition for R1:** all five cases match the expected verdict above AND the
exclusive-launcher set equals exactly `["R1-C0"]`.

---

## 5. Falsification / honesty rules (frozen)

- Every verdict recorded is the ACTUAL output of `gpu_gateway_r1.py`. No verdict
  is forced.
- If ANY remediated case does not match its preregistered expectation, the harness
  records the failure, sets `REMEDIATION_FAILED`, does **not** sign ProofRecords,
  and STOPS before any further remediation. The failure is preserved.
- No tuning after observing results. This document is SHA-256-frozen before the run.
- TEST keys only. Dilithium3 is draft ML-DSA-65-aligned, **NOT FIPS 204 final**,
  **NOT production**.
- The result does NOT claim ExecutionProof secures CUDA, guarantees GPU safety,
  proves kernel correctness, is unbypassable, or carries any independent/NVIDIA
  validation.

---

## 6. Environment constraints (frozen)

- Real NVIDIA GPU required (Colab free T4 or equivalent). No paid spend unless
  separately authorized.
- Frozen kernel compiled UNMODIFIED for the detected arch; source hash asserted
  byte-identical to the original CUDA-EP-001 kernel before proceeding.
- Toolchain recorded: nvidia-smi, nvcc, compute-sanitizer, torch, OS, UTC time.

---

## 7. Deliverables (frozen list)

preregistration (this doc), remediation changelog, machine-readable source diff
vs original frozen implementation, frozen SHA-256 manifest, environment record,
compile record, R1 gateway matrix, launcher evidence (exclusive-launch), signed
ProofRecords, raw logs, Compute Sanitizer results, R1 claims ledger, R1
limitations, final R1 result report.

---

## 8. Downstream holds (frozen)

- Do NOT merge GitHub. Do NOT publish Zenodo. Do NOT update the master corpus.
- Do NOT change the original CUDA-EP-001 record.
- R1 is returned for Derek's review only.
