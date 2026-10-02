# CUDA-EP-001 Real GPU Execution -- Test Evidence Mapping
## Remnant Fieldworks Inc.
## Document: 04_CUDA_EP_001_REAL_GPU_TEST_EVIDENCE_MAPPING.md
## Status: GPU EXECUTION PENDING -- CPU-SURROGATE EVIDENCE COMPLETE
## Date: 2026-10-02

---

## Evidence Map Structure

This document maps every test, claim, and evidence artifact for CUDA-EP-001.
GPU-phase columns are populated with NOT_EXECUTED until real GPU execution occurs.

---

## TIER 1 -- ORACLE / REFERENCE LAYER

These tests exercise the NumPy reference computation layer only.
They do NOT exercise the GPU execution gateway.

| Test ID | Description | Evidence File | Result | What It Tests | What It Does NOT Test |
|---|---|---|---|---|---|
| T-01 | ramp_sums_to_N (visible reference) | functional_tests_output.txt | PASS (CPU numpy oracle) | numpy reference is deterministic and close to float64 for a ramp input | GPU execution; gateway; CUDA kernel; memory safety |
| T-02 | uniform_seed (visible reference) | functional_tests_output.txt | PASS (CPU numpy oracle) | numpy reference is deterministic and close to float64 for a seeded uniform input | GPU execution; gateway; CUDA kernel; memory safety |
| T-03 | edges / bounds-condition (visible reference) | functional_tests_output.txt | PASS (CPU numpy oracle) | numpy reference handles edge/boundary input values deterministically | GPU execution; gateway; CUDA kernel; CUDA memory safety |
| T-04 | hidden_large_magnitude (hidden reference) | functional_tests_output.txt | PASS (CPU numpy oracle) | numpy reference close to float64 for large-magnitude values | GPU execution; gateway; CUDA kernel; memory safety |
| T-05 | hidden_small_values (hidden reference) | functional_tests_output.txt | PASS (CPU numpy oracle) | numpy reference close to float64 for small values | GPU execution; gateway; CUDA kernel; memory safety |
| T-06 | hidden_exact_cancellation (hidden reference) | functional_tests_output.txt | PASS (CPU numpy oracle) | numpy reference close to float64 under exact cancellation | GPU execution; gateway; CUDA kernel; memory safety |
| T-07 | hidden_mixed_offset (hidden reference) | functional_tests_output.txt | PASS (CPU numpy oracle) | numpy reference close to float64 for mixed-offset input | GPU execution; gateway; CUDA kernel; memory safety |
| **T-01 to T-07 combined** | **7/7 PASS** | functional_tests_output.txt | **7/7 PASS** | numpy reference layer is correct for all tested case types | GPU behavior; compilation; gateway routing |

---

## TIER 2 -- CPU UNIT TESTS

These tests exercise the ExecutionProof CPU-surrogate framework.

| Group | Tests | Evidence File | Result | What It Tests |
|---|---|---|---|---|
| CPU surrogate unit tests | 24 tests | cpu_surrogate_reference.txt | 24/24 PASS | Framework correctness in CPU-only environment |

---

## TIER 3 -- CPU-SURROGATE GATEWAY (CASES C0-C7)

These cases exercise the ExecutionProof gateway with numpy surrogate operations substituted for GPU kernel execution.

| Case | Description | Expected Verdict | Observed Verdict | Evidence | Notes |
|---|---|---|---|---|---|
| C0 (Case A) | Clean baseline | ALLOW | ALLOW | cpu_surrogate_reference.txt | Numpy surrogate; no real GPU |
| C1 (Case B) | Authority failure | DENY | DENY | cpu_surrogate_reference.txt | Numpy surrogate; no real GPU |
| C2 (Case C) | Missing evidence | HOLD | HOLD | cpu_surrogate_reference.txt | Numpy surrogate; no real GPU |
| C3 (Case D) | Policy / expiry constraint | HOLD | HOLD | cpu_surrogate_reference.txt | Numpy surrogate; no real GPU |
| C4 (Case E) | Evidence / artifact mismatch | DENY | DENY | cpu_surrogate_reference.txt | Numpy surrogate; no real GPU |
| C5 (Case F) | Control / gateway not satisfied | HOLD | HOLD | cpu_surrogate_reference.txt | Numpy surrogate; no real GPU |
| C6 (Case G) | Mutated ProofRecord | VERIFICATION_FAILURE | VERIFICATION_FAILURE | cpu_surrogate_reference.txt | Numpy surrogate; no real GPU |
| C7 (Case H) | Compute-capability mismatch | DENY | DENY | cpu_surrogate_reference.txt | Numpy surrogate; no real GPU |
| C8 | Exclusive launcher control | N/A | NOT_EXECUTED | -- | Not executed -- cannot simulate GPU context exclusivity |
| **TOTAL** | | | **8/8 matched** | | CPU surrogate only; no GPU kernel execution |

---

## TIER 4 -- GPU-PHASE GATEWAY INVOCATION

These cases represent the first real-GPU-phase execution attempt. All returned BLOCKED_NO_GPU.

| Case | Expected Verdict | Gateway Outcome | Kernel Launched | Evidence |
|---|---|---|---|---|
| GPU-C0 | ALLOW | BLOCKED_NO_GPU | NO | run_gpu_cases_output.json |
| GPU-C1 | DENY | BLOCKED_NO_GPU | NO | run_gpu_cases_output.json |
| GPU-C2 | HOLD | BLOCKED_NO_GPU | NO | run_gpu_cases_output.json |
| GPU-C3 | HOLD | BLOCKED_NO_GPU | NO | run_gpu_cases_output.json |
| GPU-C4 | DENY | BLOCKED_NO_GPU | NO | run_gpu_cases_output.json |
| GPU-C5 | HOLD | BLOCKED_NO_GPU | NO | run_gpu_cases_output.json |
| GPU-C6 | VERIFICATION_FAILURE | BLOCKED_NO_GPU | NO | run_gpu_cases_output.json |
| GPU-C7 | DENY | BLOCKED_NO_GPU | NO | run_gpu_cases_output.json |
| GPU-C8 | GATED (see preregistration) | BLOCKED_NO_GPU | NO | run_gpu_cases_output.json |

BLOCKED_NO_GPU confirms: gateway hardware detection works correctly.
BLOCKED_NO_GPU does NOT confirm: gateway routing, verdict logic, ProofRecord construction,
Dilithium signing, or kernel launch for real GPU outputs.

---

## TIER 5 -- REAL GPU EXECUTION (PENDING)

All rows below are NOT_EXECUTED. Column structure is prepared for when execution occurs.

| Case | Expected | Observed | Kernel Launched | Binary Hash | Sanitizer | ProofRecord | Evidence File |
|---|---|---|---|---|---|---|---|
| GPU-C0 | ALLOW | NOT_EXECUTED | -- | -- | -- | -- | PENDING |
| GPU-C1 | DENY | NOT_EXECUTED | -- | -- | -- | -- | PENDING |
| GPU-C2 | HOLD | NOT_EXECUTED | -- | -- | -- | -- | PENDING |
| GPU-C3 | HOLD | NOT_EXECUTED | -- | -- | -- | -- | PENDING |
| GPU-C4 | DENY | NOT_EXECUTED | -- | -- | -- | -- | PENDING |
| GPU-C5 | HOLD | NOT_EXECUTED | -- | -- | -- | -- | PENDING |
| GPU-C6 | VERIFICATION_FAILURE | NOT_EXECUTED | -- | -- | -- | -- | PENDING |
| GPU-C7 | DENY | NOT_EXECUTED | -- | -- | -- | -- | PENDING |
| GPU-C8 | GATED | NOT_EXECUTED | -- | -- | -- | -- | PENDING |

---

## TIER 6 -- COMPUTE SANITIZER (PENDING)

| Mode | Expected | Result | Evidence File |
|---|---|---|---|
| memcheck | PENDING | NOT_EXECUTED | PENDING |
| racecheck | PENDING | NOT_EXECUTED | PENDING |
| initcheck | PENDING | NOT_EXECUTED | PENDING |
| synccheck | PENDING | NOT_EXECUTED | PENDING |

---

## TIER 7 -- BUILD EVIDENCE (PENDING)

| Artifact | Expected | Result | Hash | Evidence File |
|---|---|---|---|---|
| elementwise_add.cu source | Prepared | PREPARED -- NOT COMPILED | (see 14_HASHES/) | PENDING |
| nvcc compilation | PTX + executable | NOT_EXECUTED | -- | PENDING |
| PTX intermediate | If compilation succeeds | NOT_GENERATED | -- | PENDING |
| Executable binary | If compilation succeeds | NOT_GENERATED | -- | PENDING |

---

## Evidence File Registry

| File | Location | Status |
|---|---|---|
| functional_tests_output.txt | 10_GPU_RAW_LOGS/ | PRESENT -- CPU oracle tests |
| cpu_surrogate_reference.txt | 10_GPU_RAW_LOGS/ | PRESENT -- CPU surrogate cases |
| run_gpu_cases_output.json | 09_GPU_EXECUTION_GATEWAY/ | PRESENT -- BLOCKED_NO_GPU record |
| gpu_environment_discovery.txt | 10_GPU_RAW_LOGS/ | PRESENT -- no GPU confirmation |
| proofrecord_signing_output.txt | 10_GPU_RAW_LOGS/ | PRESENT -- test key signing |
| REAL_GPU_ENVIRONMENT_DISCOVERY.txt | 13_ENVIRONMENT/ | NOT_GENERATED -- pending GPU access |
| REAL_GPU_ENVIRONMENT.json | 13_ENVIRONMENT/ | NOT_GENERATED -- pending GPU access |
| Sanitizer output (all 4 modes) | 11_COMPUTE_SANITIZER/ | NOT_GENERATED -- pending GPU access |
| Real GPU ProofRecords | 12_PROOFRECORDS/ | NOT_GENERATED -- pending GPU access |
| REAL_GPU_BUILD_HASHES.json | 14_HASHES/ | NOT_GENERATED -- pending compilation |
