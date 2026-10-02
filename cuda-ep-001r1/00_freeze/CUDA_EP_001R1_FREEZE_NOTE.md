# CUDA-EP-001R1 — Pre-Run Freeze Note

**Experiment ID:** CUDA-EP-001R1
**Frozen:** 2026-10-02, BEFORE any real-GPU execution
**Classification:** RESEARCH ONLY — NOT PRODUCTION

This note records the SHA-256 freeze of the CUDA-EP-001R1 remediation package
*prior to execution* on real NVIDIA hardware. The manifest
`CUDA_EP_001R1_PRERUN_MANIFEST.sha256` lists every source, policy, harness,
preregistration, and diff file as frozen at prereg time.

## 1. Frozen contents (see manifest for hashes)

| Area | File | Role |
|------|------|------|
| Preregistration | `00_prereg/CUDA_EP_001R1_PREREGISTRATION.md` | Frozen scope + expected outcomes |
| Source (changed) | `source/gpu_gateway_r1.py` | Remediated gateway (C5/C6/C7) |
| Source (changed) | `source/gpu_policy_r1.json` | Remediated policy |
| Source (carried) | `source/elementwise_add_launcher.py` | BYTE-IDENTICAL to CUDA-EP-001 |
| Source (carried) | `source/kernels/elementwise_add.cu` | BYTE-IDENTICAL to CUDA-EP-001 |
| Source (carried) | `source/gpu_functional_tests.py` | Carried verbatim |
| Source (carried) | `source/gpu_hidden_tests.py` | Carried verbatim |
| Source (carried) | `source/kernels/compile_kernel.sh` | Carried verbatim |
| Source (carried) | `source/kernels/run_sanitizer.sh` | Carried verbatim |
| Harness | `gpu_exec/gpu_real_run_r1.py` | R1 retest harness (C0/C5/C6/C7/C8 only) |
| Diff | `diff/gpu_gateway__original_vs_r1.diff` | Machine-readable gateway diff |
| Diff | `diff/gpu_policy__original_vs_r1.diff` | Machine-readable policy diff |
| Diff | `diff/R1_CHANGE_DESCRIPTOR.json` | Structured change descriptor |

## 2. Carried-identical assertion (verified)

The kernel and launcher are carried **byte-identical** from the frozen
CUDA-EP-001 package. Verified SHA-256:

- `source/kernels/elementwise_add.cu`
  = `268d125fe316156e9da44852afeca54838974a4a90643c375d233b5491f89b0d`
  (matches CUDA-EP-001 frozen kernel)
- `source/elementwise_add_launcher.py`
  = `ea411c6d0cb9c6abd3b4ed8f438e8cb83555da7e31ce80b7cba5a3ba67ddf01e`
  (matches CUDA-EP-001 frozen launcher)

The R1 harness `gpu_real_run_r1.py` re-asserts the kernel SHA-256 at runtime
and aborts if it differs, so the retest cannot silently run against a mutated
kernel.

## 3. Integrity rules in force

- The original CUDA-EP-001 package, logs, ProofRecords, branches, and recorded
  result are **NOT** modified, overwritten, amended, or relabeled by this
  experiment.
- Expected outcomes are frozen in the preregistration and are **NOT** tuned
  after observing results.
- If any remediated case does not behave as preregistered, the harness records
  the failure, does **NOT** sign a success ProofRecord, and **STOPS** before
  any further remediation.
- A post-run manifest will be generated after execution to capture results,
  logs, and ProofRecords; it will be a *separate* manifest and will not alter
  this pre-run freeze.
