# GPU Request Contract - CUDA-EP-001 GPU Phase (annotated)

*Remnant Fieldworks Inc. - Derek Hone - 2026-10-01*

> **NOT_EXECUTED - NO GPU**
> This is the GPU-phase instantiation of the CUDA-EP-001 Request Contract schema
> (`RF_CUDA_Final_Package/06_CUDA_REQUEST_CONTRACT_SCHEMA.json`). The two fields
> that require a build / GPU - `compiled_binary_sha256` and
> `sanitizer_evidence_hash` - are NOT_EXECUTED. Every other digest is a real
> SHA-256 computed from a file written in this package.

## Field-by-field

| Field | Value | Note |
|---|---|---|
| request_id | CUDA-EP-001-GPU-C0-v1.0 | Baseline (GPU-C0) request |
| experiment_phase | GPU_EXECUTION_PHASE | Distinguishes from CPU surrogate |
| kernel_name | elementwise_add | Simplest KernelBench L1-style task |
| kernel_description | Elementwise addition of two 1D float32 tensors of size 1024 | Deterministic, minimal confounds |
| source_file | 09_GPU_EXECUTION_GATEWAY/kernels/elementwise_add.cu | Real CUDA C source |
| **source_sha256** | `268d125f...91f89b0d` | **Computed from the actual .cu file** |
| **compiled_binary_sha256** | `NOT_EXECUTED - nvcc not available` | **Requires nvcc + GPU** |
| build_recipe.compiler | nvcc | |
| build_recipe.version | NOT_EXECUTED | nvcc absent |
| build_recipe.flags | `-O2 --generate-code arch=compute_80,code=sm_80` | sm_80 = A100/A40 class |
| build_recipe.cuda_version | 11.8+ | Minimum |
| build_recipe.container | none | |
| target_gpu | A40 (preferred) OR T4 OR A100 | |
| target_compute_capability | 8.0 (preferred), 7.5 acceptable, 8.6 acceptable | |
| driver_version_min | 525 | |
| **functional_test_hash** | `b19fb40c...03e81fb9` | **SHA-256 of gpu_functional_tests.py** |
| **sanitizer_evidence_hash** | `NOT_EXECUTED` | **Requires Compute Sanitizer** |
| **hidden_test_hash** | `3d9f510d...78e2f4898` | **SHA-256 of gpu_hidden_tests.py** |
| **policy_bundle_hash** | `b617823f...a9dca6df` | **SHA-256 of gpu_policy.json** |
| freshness_window_seconds | 3600 | |
| authority_identity | spiffe://cuda-ep.experiment/proposer/run-gpu-001 | Must be in policy allow-list |
| stage_authorized | COMPILE_AND_EXECUTE | ALLOW for one stage does not imply the next |
| fail_closed | true | |

## What must change on a GPU host

1. Run `09_GPU_EXECUTION_GATEWAY/kernels/compile_kernel.sh` -> set
   `compiled_binary_sha256` to the produced `elementwise_add.sha256`.
2. Run `09_GPU_EXECUTION_GATEWAY/kernels/run_sanitizer.sh` -> set
   `sanitizer_evidence_hash` to the produced `sanitizer_output.sha256`.
3. Re-issue with fresh `issued_at` / `expiry_at` within the freshness window.
4. Submit to the gateway for GPU-C0 authorization.

Until those two hashes are real, the Evidence engine returns HOLD (missing
evidence), which is the correct fail-closed behavior.
