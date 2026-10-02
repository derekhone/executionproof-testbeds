# CUDA-EP-001 Real GPU Reproducibility Guide
## Remnant Fieldworks Inc. -- ExecutionProof Program
## Status: PRE-GPU FREEZE | Version: v0.1-pre-gpu | Date: 2026-10-01

---

## 1. Purpose

This guide enables independent reproduction of CUDA-EP-001. It covers:
- The CPU-surrogate phase (fully reproducible now, no GPU required)
- The GPU phase (reproducible with an NVIDIA GPU meeting the specifications below)
- The environment constraints that produced the BLOCKED_NO_GPU result in the Abacus AI execution environment

All instructions are written for the honest state of the experiment: GPU cases have not yet executed on real hardware. The CPU-surrogate phase is complete and reproducible.

---

## 2. Hardware Requirements

### 2.1 For GPU Phase (mandatory for GPU-C0 through GPU-C8)

| Requirement | Minimum | Recommended |
|---|---|---|
| GPU | NVIDIA T4 (16 GB) | NVIDIA A40 (48 GB) |
| CUDA Compute Capability | 7.0+ | 8.6+ |
| GPU VRAM | 8 GB | 48 GB |
| System RAM | 16 GB | 32 GB |
| Storage | 10 GB | 20 GB |
| Driver | CUDA 11.0+ | CUDA 12.x |

### 2.2 For CPU-Surrogate Phase (no GPU required)

Any modern x86-64 Linux system with:
- Python 3.9+
- 8 GB RAM
- 10 GB storage

---

## 3. Software Environment

### 3.1 Operating System

```
Ubuntu 20.04 LTS or 22.04 LTS (recommended)
```

### 3.2 Python Dependencies

```
numpy>=1.24.0
scipy>=1.10.0
python-dateutil>=2.8.2
hashlib (stdlib)
json (stdlib)
```

Install:
```bash
pip install numpy scipy python-dateutil
```

### 3.3 CUDA Toolkit (GPU phase only)

```bash
# CUDA 12.x recommended
wget https://developer.download.nvidia.com/compute/cuda/12.0.0/local_installers/cuda_12.0.0_525.60.13_linux.run
sudo sh cuda_12.0.0_525.60.13_linux.run
export PATH=/usr/local/cuda/bin:$PATH
export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH
```

### 3.4 CUDA Compiler Verification

```bash
nvcc --version
nvidia-smi
```

Both must succeed before GPU phase begins.

---

## 4. Reproduction Steps -- CPU-Surrogate Phase

### Step 1: Environment Verification

```bash
python3 --version
python3 -c "import numpy; print(numpy.__version__)"
python3 -c "import scipy; print(scipy.__version__)"
```

Expected: Python 3.9+, numpy 1.24+, scipy 1.10+

### Step 2: Run Oracle Tests (T-01 through T-07)

```bash
cd /path/to/cuda-ep-001/
python3 07_REQUEST_CONTRACT/oracle_tests.py 2>&1 | tee functional_tests_output.txt
```

Expected: 7/7 PASS (100%)

### Step 3: Run CPU Surrogate Cases (C0 through C7)

```bash
python3 05_CASE_RESULTS/cpu_surrogate_cases.py 2>&1 | tee cpu_surrogate_reference.txt
```

Expected:
- 8/8 cases matched
- 24/24 unit tests passed
- C8 NOT_EXECUTED (requires real GPU)

### Step 4: Verify SHA256 Hashes

```bash
sha256sum -c PRE_GPU_SHA256SUMS.txt
```

Expected: All 16 files OK

---

## 5. Reproduction Steps -- GPU Phase

### Step 0: Package Availability Precondition (Correction D)

Before renting or paying for any GPU time, confirm the CUDA-EP-001 package is actually present on the target GPU host. Do NOT assume it is already published at a public URL such as `github.com/derekhone/executionproof-testbeds/cuda-ep-001/`; at the time of this freeze the package has NOT been pushed to a public location.

Verify availability by one of these transfer paths, in order of preference:
- Option A (secure archive): copy a `cuda-ep-001.tar.gz` built from the frozen package to the GPU host, then `sha256sum -c PRE_GPU_SHA256SUMS.txt` after extraction.
- Option B (private repo): clone from a private repository you control, using a short-lived credential; never embed tokens in scripts or logs.
- Option C (public repo): clone the public path ONLY if the PR has been merged and the package is confirmed live. Confirm with `git ls-remote` or an HTTP 200 on the directory before spending GPU money.

Do not proceed to Step 1 until the package is present on the host and `sha256sum -c PRE_GPU_SHA256SUMS.txt` reports all files OK.

### Step 1: GPU Environment Discovery

```bash
nvidia-smi --query-gpu=name,memory.total,driver_version,compute_cap --format=csv,noheader
nvcc --version
python3 -c "import subprocess; r = subprocess.run(['nvidia-smi'], capture_output=True, text=True); print(r.stdout)"
```

Save output as: `gpu_environment_discovery.txt`

### Step 2: Compile CUDA Kernel

```bash
cd /path/to/cuda-ep-001/
nvcc -O2 -arch=sm_70 elementwise_add.cu -o elementwise_add
```

Note: For A40 use `-arch=sm_86`. For T4 use `-arch=sm_75`.

### Step 3: Run GPU Execution Cases

```bash
python3 09_EXECUTION_GATEWAY/run_gpu_cases.py \
  --kernel elementwise_add \
  --cases GPU-C0,GPU-C1,GPU-C2,GPU-C3,GPU-C4,GPU-C5,GPU-C6,GPU-C7,GPU-C8 \
  --output run_gpu_cases_output.json \
  2>&1 | tee gpu_execution_log.txt
```

### Step 4: Run Compute Sanitizer

```bash
compute-sanitizer --tool memcheck ./elementwise_add
compute-sanitizer --tool racecheck ./elementwise_add
```

Save outputs as: `sanitizer_memcheck.txt`, `sanitizer_racecheck.txt`

### Step 5: GPU-C8 Governance Boundary Test

GPU-C8 is the critical ExecutionProof boundary test. It tests whether the system correctly detects and rejects attempted authorization boundary crossing in a CUDA kernel.

```bash
python3 09_EXECUTION_GATEWAY/run_gpu_cases.py \
  --cases GPU-C8 \
  --mode boundary-governance \
  --output gpu_c8_boundary.json \
  2>&1 | tee gpu_c8_log.txt
```

Expected: BOUNDARY_ENFORCED (the system must reject the crossing attempt)
If actual: BOUNDARY_CROSSED, record as FAIL -- this is critical evidence

### Step 6: Sign ProofRecords

After GPU execution completes:

```bash
python3 12_PROOFRECORDS/sign_proofrecords.py \
  --input run_gpu_cases_output.json \
  --environment gpu_environment_discovery.txt \
  --key TEST_KEY \
  2>&1 | tee proofrecord_signing_output.txt
```

Note: TEST KEY -- NOT PRODUCTION. Replace with production key for official releases only.

### Step 7: Hash Final Artifacts

```bash
sha256sum * > POST_GPU_SHA256SUMS.txt
```

---

## 6. Governance Gates

Before proceeding to public release after GPU execution, the following gates must pass:

| Gate | Criterion | Action if Fail |
|---|---|---|
| G1 | nvidia-smi returns valid GPU | Stop -- not a real GPU run |
| G2 | nvcc compiles elementwise_add.cu | Stop -- environment failure |
| G3 | GPU-C0 through GPU-C7 execute | Record result honestly (PASS or FAIL) |
| G4 | GPU-C8 executes and verdict recorded | If FAIL: preserve and document; do not suppress |
| G5 | compute-sanitizer memcheck: 0 errors | Record any errors honestly |
| G6 | SHA256 hashes match pre-execution freeze | If mismatch: do not release; investigate |
| G7 | ProofRecords signed with TEST KEY | OK for pre-production; upgrade key for production |
| G8 | Derek authorizes public release | Required before any GitHub push or Zenodo deposit |

---

## 7. Expected Outcomes

### CPU Surrogate (confirmed)
- T-01 to T-07: PASS
- C0 to C7: MATCHED
- C8: NOT_EXECUTED
- Unit tests: 24/24

### GPU Phase (pre-execution expectations -- preregistered)
See `00_FREEZE/PRE_GPU_FREEZE_MANIFEST.json` for full preregistered expectations.

Summary preregistered expectations:
- GPU-C0 through GPU-C7: Expect PASS (ExecutionProof boundary enforced)
- GPU-C8: Expect BOUNDARY_ENFORCED (critical governance test)
- compute-sanitizer: Expect 0 memory errors
- elementwise_add compilation: Expect success on CUDA 11+

All deviations from preregistered expectations must be documented in the correction history.

---

## 8. Contact and Attribution

Experiment: CUDA-EP-001
Institution: Remnant Fieldworks Inc.
Principal Investigator: Derek Hone (derek@ownerremnantfieldworks.com)
Program: ExecutionProof

For reproduction questions or discrepancies, open an issue on:
https://github.com/derekhone/executionproof-testbeds

---

## 9. Honesty Statement

This guide describes the procedure as of the PRE-GPU FREEZE state. The GPU phase has not yet been executed on real hardware. Any reproduction of the GPU phase that follows this guide should be done on hardware meeting the specifications in Section 2. CPU-only environments cannot reproduce GPU-C0 through GPU-C8.

Do not substitute CPU results for GPU results. The entire point of CUDA-EP-001 is to execute on real GPU hardware to test ExecutionProof boundary enforcement in a CUDA kernel environment.

---

*Document version: v0.1-pre-gpu | Generated: 2026-10-01 | TEST KEY -- NOT PRODUCTION*
