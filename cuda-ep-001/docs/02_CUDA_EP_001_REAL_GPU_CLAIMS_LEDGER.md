# CUDA-EP-001 Real GPU Execution -- Claims Ledger
## Remnant Fieldworks Inc.
## Document: 02_CUDA_EP_001_REAL_GPU_CLAIMS_LEDGER.md
## Status: GPU EXECUTION PENDING -- CLAIMS AT PRE-EXECUTION CEILING
## Date: 2026-10-02
## Governing principle: Claims narrower than evidence. Always.

---

## Ledger Status

This ledger is in PRE-EXECUTION state. Claims are at the CPU-surrogate ceiling.
All GPU-phase claims are listed as PENDING and will be updated after real GPU execution.

Do not use GPU-phase claim language before GPU execution occurs and results are observed.

---

## SECTION A -- ACTIVE CLAIMS (Supported by Current Evidence)

### A-1: CPU-Surrogate Framework Execution

CLAIM: The CUDA-EP-001 CPU-surrogate framework executed successfully.

EVIDENCE:
- 8 cases (C0-C7 / Cases A-H) executed via the CPU-surrogate gateway
- All 8 verdicts matched preregistered expectations
- 24 unit tests passed (24/24)
- Execution logs: /output/RF_CUDA_GPU_Package/10_GPU_RAW_LOGS/cpu_surrogate_reference.txt
- Case results: 05_CORRECTED_GPU_CASE_RESULTS.md (Phase A corrected package)

BOUNDED WORDING: "The CPU-surrogate phase of CUDA-EP-001 executed in the tested CPU-only
environment with numpy surrogate operations. Results matched preregistered expectations."

### A-2: GPU Gateway Hardware Detection

CLAIM: The ExecutionProof GPU execution gateway correctly detects the absence of
CUDA-capable hardware and blocks execution before any case-specific logic runs.

EVIDENCE:
- run_gpu_cases_output.json: all_blocked=true, 9/9 cases BLOCKED_NO_GPU
- gpu_environment_discovery.txt: nvidia-smi NOT_FOUND, /dev/nvidia* NOT_FOUND, torch.cuda.is_available()=False
- Gateway detection confirmed as correct behavior (should not proceed without hardware)

BOUNDED WORDING: "The GPU execution gateway correctly identifies the absence of
CUDA hardware and halts. This confirms detection-and-halt behavior only; it does not confirm
correct behavior with real GPU hardware present."

### A-3: NumPy Oracle Correctness

CLAIM: The NumPy oracle (reference computation layer) produces correct expected outputs
for all 7 tested case types.

EVIDENCE:
- functional_tests_output.txt: T-01 through T-07, 7/7 PASS
- Oracle tests exercise numpy reference logic, not the GPU execution gateway
- Case types tested: elementwise addition, scalar multiplication, vector normalization,
  dot product, matrix-vector multiply, mixed arithmetic, edge values

BOUNDED WORDING: "In the tested environment, the numpy oracle produces correct reference
vectors for all 7 preregistered test cases."

### A-4: CUDA Source Preparation

CLAIM: A real CUDA C source file (elementwise_add.cu) has been authored with standard
CUDA runtime API constructs and is ready for compilation when GPU hardware is available.

EVIDENCE:
- elementwise_add.cu exists in the package (08_BUILD_ATTESTATION/)
- Uses cudaMalloc, cudaMemcpy, kernel launch syntax, cudaFree
- File has not been passed to nvcc or any compiler
- No PTX, cubin, or executable has been produced

BOUNDED WORDING: "CUDA source (elementwise_add.cu) is prepared with standard CUDA
runtime constructs. It has not been compiled; no syntactic or runtime verdict exists."

### A-5: ProofRecord Signing Under Test Key

CLAIM: ProofRecord signing and verification using the Dilithium post-quantum signature
scheme executed successfully for CPU-surrogate results.

EVIDENCE:
- proofrecord_signing_output.txt: signing completed for GPU-C0 through GPU-C8 templates
- Verification pass confirmed
- KEY LABEL: TEST KEY -- NOT PRODUCTION on all records

BOUNDED WORDING: "ProofRecord signing executed under a TEST KEY -- NOT PRODUCTION.
Signatures establish tamper evidence under the stated key assumption only.
No production key management, key custody, or HSM is in place."

### A-6: NVIDIA Inception Membership

CLAIM: RF is an active NVIDIA Inception member.

EVIDENCE: Confirmed membership status (prior sessions).

---

## SECTION B -- PENDING CLAIMS (Will Be Resolved by GPU Execution)

All items in this section are PENDING. Do not assert them until observed.

| Claim | Pending On | Expected After GPU Execution |
|---|---|---|
| nvcc compilation succeeded | Real GPU environment with nvcc | PASS or FAIL -- both are valid outcomes |
| CUDA kernel executed on real GPU | GPU-C0 execution | ALLOW and kernel launch observable |
| GPU-C0 through GPU-C8 verdicts | All 9 cases | Match or deviate from preregistered expectations |
| GPU-C8 no unauthorized bypass | GPU-C8 execution | Pass: no bypass found; Fail: bypass found -- both preserved |
| Compute Sanitizer passed memcheck | Sanitizer on compiled kernel | PASS or findings -- both preserved |
| Compute Sanitizer passed racecheck | Sanitizer on compiled kernel | PASS or findings -- both preserved |
| Compute Sanitizer passed initcheck | Sanitizer on compiled kernel | PASS or findings -- both preserved |
| Compute Sanitizer passed synccheck | Sanitizer on compiled kernel | PASS or findings -- both preserved |
| ProofRecords signed with real GPU data | Real GPU execution | Signing with actual device output, timestamps |
| Governance boundary holds in tested environment | GPU-C8 | Supported or not -- preserved either way |

---

## SECTION C -- PROHIBITED CLAIMS

These claims are prohibited regardless of GPU results.

| Claim | Reason |
|---|---|
| Universal GPU governance | No finite test set can prove all paths |
| All CUDA workloads governed | Tested a specific kernel only |
| Production safety established | Test keys; no production key management; no production deployment |
| Formal security guarantee | No formal proof; tested pathways only |
| Independent validation occurred | All testing is founder-only at this stage |
| CIF-derived claims of any kind | CIF firewall is absolute -- no revival |
| elementwise_add.cu is syntactically valid | No compiler has processed it |

---

## SECTION D -- REMEDIATION DOCTRINE

If any GPU-phase case fails:

1. Record the FAIL exactly as observed
2. Freeze the failure package (logs, ProofRecord, environment, hashes)
3. Do not automatically rerun
4. Design remediation separately with new experiment identifier (CUDA-EP-001b or GPU-Cxb)
5. Keep FAIL and remediation both in the permanent record
6. Never replace FAIL with PASS

If GPU-C8 fails (unauthorized bypass found):
- Immediately classify: GOVERNANCE BOUNDARY FAIL
- Do not claim hardware-enforced exclusive gateway control
- Preserve bypass path documentation
- Do not publish positive headline
