# CUDA-EP-001 Raw Execution Artifact Index
## Remnant Fieldworks Inc. -- ExecutionProof Program
## Status: PRE-GPU FREEZE | Version: v0.1-pre-gpu | Date: 2026-10-01

---

## 1. Purpose

This document indexes all raw execution artifacts produced during CUDA-EP-001. It distinguishes between:
- Artifacts that EXIST and are evidence-complete (CPU-surrogate phase)
- Artifacts that ARE EXPECTED but DO NOT YET EXIST (GPU phase, pending hardware acquisition)
- Artifacts that will NOT exist until after GPU execution and Derek's release authorization

---

## 2. Artifact Status Legend

| Status | Meaning |
|---|---|
| EXISTS | File exists in the package; contents are verified |
| PENDING_GPU | File will be created after real GPU execution completes |
| DERIVED | File derived from existing artifacts; exists now |
| NOT_EXECUTED | Test or kernel not yet run on real hardware |
| FROZEN | File is part of the pre-GPU freeze; immutable |

---

## 3. Pre-GPU Freeze Artifacts (EXISTS + FROZEN)

All files in this section are part of the PRE_GPU SHA256 freeze. Their hashes are recorded in `00_FREEZE/PRE_GPU_SHA256SUMS.txt`.

### 3.1 Corrected Package (15 files from RF_CUDA_Phase_A_Corrected/)

| # | Filename | Status | SHA256 (first 16 chars) |
|---|---|---|---|
| 1 | CUDA_EP_001_Corrected_Report.html | FROZEN | see PRE_GPU_SHA256SUMS.txt |
| 2 | CUDA_EP_001_Corrected_Report.pdf | FROZEN | see PRE_GPU_SHA256SUMS.txt |
| 3 | CUDA_EP_001_Corrected_Report.docx | FROZEN | see PRE_GPU_SHA256SUMS.txt |
| 4 | CUDA_EP_001_Case_Results_Corrected.md | FROZEN | see PRE_GPU_SHA256SUMS.txt |
| 5 | CUDA_EP_001_Claims_Ledger_Corrected.md | FROZEN | see PRE_GPU_SHA256SUMS.txt |
| 6 | CUDA_EP_001_Executive_Summary_Corrected.md | FROZEN | see PRE_GPU_SHA256SUMS.txt |
| 7 | CUDA_EP_001_Limitations_Corrected.md | FROZEN | see PRE_GPU_SHA256SUMS.txt |
| 8 | CUDA_EP_001_Test_Evidence_Mapping_Corrected.md | FROZEN | see PRE_GPU_SHA256SUMS.txt |
| 9 | CUDA_EP_001_Correction_History.md | FROZEN | see PRE_GPU_SHA256SUMS.txt |
| 10 | CUDA_EP_001_NVIDIA_Memo_Corrected.html | FROZEN | see PRE_GPU_SHA256SUMS.txt |
| 11 | CUDA_EP_001_NVIDIA_Memo_Corrected.pdf | FROZEN | see PRE_GPU_SHA256SUMS.txt |
| 12 | CUDA_EP_001_NVIDIA_Memo_Corrected.docx | FROZEN | see PRE_GPU_SHA256SUMS.txt |
| 13 | CUDA_EP_001_Preregistration.md | FROZEN | see PRE_GPU_SHA256SUMS.txt |
| 14 | CUDA_EP_001_Environment_Report.md | FROZEN | see PRE_GPU_SHA256SUMS.txt |
| 15 | SHA256SUMS.txt | FROZEN | see PRE_GPU_SHA256SUMS.txt |

### 3.2 GPU Package Raw Logs (10 files from RF_CUDA_GPU_Package/10_GPU_RAW_LOGS/)

These files were produced during the GPU-phase attempt and document the BLOCKED_NO_GPU outcome.

| # | Filename | Status | Contents |
|---|---|---|---|
| 1 | functional_tests_output.txt | EXISTS | T-01 to T-07, 7/7 PASS |
| 2 | cpu_surrogate_reference.txt | EXISTS | C0-C7 matched, 24/24 unit tests, C8 NOT_EXECUTED |
| 3 | gpu_environment_discovery.txt | EXISTS | nvidia-smi NOT_FOUND; CUDA toolkit NOT_FOUND |
| 4 | proofrecord_signing_output.txt | EXISTS | TEST KEY signing; GPU-C0 through GPU-C8 signed with BLOCKED_NO_GPU status |
| 5 | gpu_c8_governance_log.txt | EXISTS | C8 governance boundary test: NOT_EXECUTED (no GPU) |
| 6 | sanitizer_memcheck.txt | EXISTS | NOT_EXECUTED -- no GPU; compute-sanitizer not available |
| 7 | sanitizer_racecheck.txt | EXISTS | NOT_EXECUTED -- no GPU |
| 8 | compilation_log.txt | EXISTS | nvcc NOT_FOUND; elementwise_add.cu: NOT COMPILED |
| 9 | gpu_execution_log.txt | EXISTS | All 9 GPU cases: BLOCKED_NO_GPU |
| 10 | environment_metadata.json | EXISTS | Intel Xeon 6975P-C; Python 3.11.7; numpy 1.26.0 |

### 3.3 ProofRecord JSONs (9 files from RF_CUDA_GPU_Package/08_GPU_PROOFRECORDS/)

| # | Filename | Status | Verdict |
|---|---|---|---|
| 1 | proofrecord_gpu_c0.json | EXISTS | BLOCKED_NO_GPU (TEST KEY) |
| 2 | proofrecord_gpu_c1.json | EXISTS | BLOCKED_NO_GPU (TEST KEY) |
| 3 | proofrecord_gpu_c2.json | EXISTS | BLOCKED_NO_GPU (TEST KEY) |
| 4 | proofrecord_gpu_c3.json | EXISTS | BLOCKED_NO_GPU (TEST KEY) |
| 5 | proofrecord_gpu_c4.json | EXISTS | BLOCKED_NO_GPU (TEST KEY) |
| 6 | proofrecord_gpu_c5.json | EXISTS | BLOCKED_NO_GPU (TEST KEY) |
| 7 | proofrecord_gpu_c6.json | EXISTS | BLOCKED_NO_GPU (TEST KEY) |
| 8 | proofrecord_gpu_c7.json | EXISTS | BLOCKED_NO_GPU (TEST KEY) |
| 9 | proofrecord_gpu_c8.json | EXISTS | NOT_EXECUTED / BLOCKED_NO_GPU (TEST KEY) |

### 3.4 Execution Gateway (from RF_CUDA_GPU_Package/09_GPU_EXECUTION_GATEWAY/)

| # | Filename | Status | Contents |
|---|---|---|---|
| 1 | run_gpu_cases_output.json | EXISTS | All 9 cases BLOCKED_NO_GPU; full structured output |
| 2 | gpu_gateway_log.txt | EXISTS | Gateway execution log; no GPU found |

### 3.5 Freeze Records (New -- this pass)

| # | Filename | Status | Contents |
|---|---|---|---|
| 1 | 00_FREEZE/PRE_GPU_SHA256SUMS.txt | EXISTS + FROZEN | SHA256 of all 16 corrected package files |
| 2 | 00_FREEZE/PRE_GPU_FREEZE_MANIFEST.json | EXISTS + FROZEN | Full freeze record; preregistered expectations; claims ceiling |
| 3 | 00_FREEZE/PRE_GPU_EXECUTION_STATE.md | EXISTS + FROZEN | Immutable execution state; GPU acquisition status |

---

## 4. Pending GPU-Phase Artifacts (PENDING_GPU)

These files will be created AFTER real GPU execution on authorized hardware.

| # | Filename | Expected Contents |
|---|---|---|
| 1 | POST_GPU_ENV/nvidia_smi_output.txt | nvidia-smi output from real GPU environment |
| 2 | POST_GPU_ENV/cuda_version.txt | nvcc --version output from real GPU environment |
| 3 | POST_GPU_EXEC/elementwise_add_compiled | Compiled CUDA binary |
| 4 | POST_GPU_EXEC/compilation_log.txt | nvcc compilation output |
| 5 | POST_GPU_EXEC/run_gpu_cases_output.json | GPU cases: PASS/FAIL/BOUNDARY_ENFORCED for each |
| 6 | POST_GPU_EXEC/gpu_execution_log.txt | Full GPU execution log |
| 7 | POST_GPU_SANIT/sanitizer_memcheck.txt | compute-sanitizer memcheck results |
| 8 | POST_GPU_SANIT/sanitizer_racecheck.txt | compute-sanitizer racecheck results |
| 9 | POST_GPU_PR/proofrecord_gpu_c0_real.json | Real GPU ProofRecord for C0 |
| 10 | POST_GPU_PR/proofrecord_gpu_c8_real.json | Real GPU ProofRecord for C8 (governance boundary) |
| 11 | POST_GPU_HASH/POST_GPU_SHA256SUMS.txt | SHA256 of all post-GPU artifacts |
| 12 | POST_GPU_HASH/DELTA_MANIFEST.json | Diff of pre- vs post-GPU artifact sets |

---

## 5. Index of This Pass's Deliverables (DERIVED)

These documents were produced during the Real GPU Execution Pass (this document generation session).

| # | Filename | Contents |
|---|---|---|
| 1 | 01_CUDA_EP_001_REAL_GPU_EXECUTIVE_SUMMARY.md | Honest executive summary; GPU-BLOCKED status |
| 2 | 02_CUDA_EP_001_REAL_GPU_CLAIMS_LEDGER.md | Claims ledger; all claims narrower than evidence |
| 3 | 03_CUDA_EP_001_REAL_GPU_LIMITATIONS.md | Limitations; GPU-BLOCKED prominently stated |
| 4 | 04_CUDA_EP_001_REAL_GPU_TEST_EVIDENCE_MAPPING.md | Test/evidence mapping table |
| 5 | 05_CUDA_EP_001_REAL_GPU_CASE_RESULTS.md | Case-by-case results table |
| 6 | 06_CUDA_EP_001_REAL_GPU_REPRODUCIBILITY_GUIDE.md | This guide |
| 7 | 07_CUDA_EP_001_REAL_GPU_RAW_EXECUTION_INDEX.md | This document |
| 8 | 08_CUDA_EP_001_REAL_GPU_PROOFRECORD_INDEX.md | ProofRecord index |
| 9 | 09_CUDA_EP_001_REAL_GPU_HASH_MANIFEST.md | Hash manifest |
| 10 | 10_CUDA_EP_001_GITHUB_RELEASE_RECORD.md | GitHub release record |
| 11 | 11_CUDA_EP_001_ZENODO_DEPOSITION_RECORD.md | Zenodo deposition record |
| 12 | 12_CUDA_EP_001_MASTER_RECORD_UPDATE.md | Master record update |
| 13 | 13_CUDA_EP_001_PUBLIC_RELEASE_QA.md | 35/35 QA audit |
| 14 | 14_CUDA_EP_001_EXTERNAL_ACTION_LOG.md | External action log |
| 15 | 15_CUDA_EP_001_FINAL_EXECUTION_REPORT.md | Final execution report |
| 16 | GPU_ACQUISITION/RENTAL_OPTION.md | Exact GPU rental option; HOLD for Derek |

---

## 6. Artifact Integrity Status

All pre-GPU freeze artifacts: SHA256-verified against `00_FREEZE/PRE_GPU_SHA256SUMS.txt`
GPU-phase artifacts: NOT YET CREATED
Post-GPU artifacts: NOT YET CREATED; will be SHA256-frozen after GPU execution

Any discrepancy between the artifact listed here and its actual SHA256 hash must be investigated before public release.

---

*Document version: v0.1-pre-gpu | Generated: 2026-10-01 | TEST KEY -- NOT PRODUCTION*
