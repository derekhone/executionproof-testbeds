# CUDA-EP-001 Real GPU Execution -- Limitations
## Remnant Fieldworks Inc.
## Document: 03_CUDA_EP_001_REAL_GPU_LIMITATIONS.md
## Status: GPU EXECUTION PENDING
## Date: 2026-10-02

---

## Current Limitations (Pre-GPU Execution)

The following limitations apply to CUDA-EP-001 as of the pre-GPU-execution state.
Limitations will be updated when GPU execution occurs. Even after successful GPU execution,
permanent limitations (Section B) will remain.

---

## SECTION A -- Limitations from Non-Execution (Temporary)

These limitations exist because GPU execution has not yet occurred.
They will be partially resolved when real GPU hardware is accessed.

**A-1. No real GPU execution**
All GPU-phase cases (GPU-C0 through GPU-C8) returned BLOCKED_NO_GPU.
No GPU kernel has executed under ExecutionProof control or outside it.

**A-2. CUDA source not compiled**
elementwise_add.cu has been authored but not passed to nvcc or any compiler.
No syntactic, semantic, or performance verdict exists for this kernel.

**A-3. Compute Sanitizer not run**
Memory safety, race conditions, uninitialized access, and synchronization errors
have not been checked. No memory safety claim can be made.

**A-4. GPU-C8 not executed in any environment**
Exclusive launcher control has not been tested on real GPU hardware or in CPU surrogate.
The governance-boundary question (can any path bypass the gateway?) remains open.

**A-5. GPU functional tests not run**
The real-GPU visible and hidden functional test suites have not executed.
Only CPU-surrogate tests and numpy oracle tests have run.

**A-6. ProofRecords reflect TEST KEY -- NOT PRODUCTION**
All signed ProofRecords use a test key generated for this experiment.
No production key management, key custody service, or hardware security module is in place.
ProofRecord signatures establish tamper evidence only under the stated key assumption.

---

## SECTION B -- Permanent Limitations (Persist Even After GPU Execution)

These limitations will remain true even if every GPU-phase test passes.

**B-1. Finite test coverage**
The 9 preregistered cases cover a designed set of authorization scenarios.
They do not exhaust all possible CUDA invocation paths, GPU architectures, driver
versions, or application contexts. Untested paths are outside the evidence boundary.

**B-2. Single kernel tested**
Only elementwise_add.cu has been tested. Conclusions do not extend to other CUDA
kernels, JIT-compiled code, or multi-kernel workloads without additional testing.

**B-3. Bounded GPU architectures**
Testing will be conducted on specific GPU hardware (A40, T4, or A100).
Results do not automatically extend to other GPU architectures or compute capabilities.

**B-4. Test key, not production key**
Even after GPU execution, ProofRecords will continue to use TEST KEY -- NOT PRODUCTION
unless a separately authorized managed key is introduced.
No production security properties can be claimed from test key signing.

**B-5. No independent validation**
All testing is conducted by RF (founder-only). No third party has independently
reproduced, challenged, or validated any CUDA-EP-001 result.
UW capstone teams (staffing pending) and UD student team (kickoff pending)
represent future independent work, not current independent validation.

**B-6. No universal GPU control claim**
Even if GPU-C8 passes, the result applies only to the tested bypass paths
in the tested hardware/software environment. No universal claim that ExecutionProof
controls all CUDA workloads is warranted.

**B-7. No formal proof of all bypass paths**
The test matrix covers preregistered bypass scenarios. Untested bypass paths,
novel driver behaviors, kernel launch mechanisms introduced after testing, or
hardware-level bypass techniques are outside the evidence boundary.

**B-8. Source-to-binary / JIT / driver attestation not established**
elementwise_add.cu is the tested source. The relationship between the compiled
binary and the source is established only within the tested environment.
JIT compilation, driver-level transformations, and multi-stage compilation
pipelines may alter the artifact relationship in production settings.

**B-9. Oracle blindness**
The NumPy oracle produces expected results computed in advance. If the oracle itself
has an error for any case, the comparison will not catch it. Oracle correctness
has been tested only for the 7 visible+hidden case types.

**B-10. Deployment differences**
Results obtained in a controlled single-GPU test environment may not represent
behavior in shared GPU environments, container-based execution, virtualized GPU
access (e.g., CUDA MPS, vGPU), or production multi-tenant infrastructure.

**B-11. Production safety not established**
No production deployment has been tested or validated. The experiment establishes
research-stage framework behavior, not production operational safety.

**B-12. CIF firewall -- absolute**
No claim based on Coherence-Inheritance Fusion (CIF) theory is permitted in any
public RF communication. CIF is frozen and may not be cited in connection with
any CUDA-EP-001 result, claim, or implication.
