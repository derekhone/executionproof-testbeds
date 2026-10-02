# CUDA-EP-001 ProofRecord Index
## Remnant Fieldworks Inc. -- ExecutionProof Program
## Status: PRE-GPU FREEZE | Version: v0.1-pre-gpu | Date: 2026-10-01

---

## 1. Purpose

This document indexes all ProofRecords produced for CUDA-EP-001 across all phases. It specifies:
- Which ProofRecords exist
- Their signing status (TEST KEY vs. production key)
- Their verdict
- What evidence each ProofRecord covers
- What is pending real GPU execution

---

## 2. ProofRecord Status Legend

| Status | Meaning |
|---|---|
| TEST_KEY_SIGNED | Signed with TEST KEY -- not production; valid for research; NOT for production deployment |
| PRODUCTION_PENDING | Will be re-signed with production key after GPU execution + Derek's authorization |
| NOT_YET_CREATED | ProofRecord does not exist; will be created after GPU execution |
| BLOCKED_NO_GPU | Execution attempted but blocked by absent GPU hardware |

---

## 3. GPU-Phase ProofRecords (from RF_CUDA_GPU_Package/08_GPU_PROOFRECORDS/)

All 9 ProofRecords were signed with TEST KEY. All 9 verdicts are BLOCKED_NO_GPU because no GPU hardware was present in the execution environment.

| ProofRecord ID | Filename | Signing Key | Verdict | Evidence Covered | Notes |
|---|---|---|---|---|---|
| GPU-PR-C0 | proofrecord_gpu_c0.json | TEST KEY | BLOCKED_NO_GPU | GPU-C0: clean baseline (correct artifact, valid authority, fresh evidence, matching capability). Preregistered expected-on-GPU: ALLOW + launch | Environment: Intel Xeon, no GPU |
| GPU-PR-C1 | proofrecord_gpu_c1.json | TEST KEY | BLOCKED_NO_GPU | GPU-C1: authority failure (requester not authorized by policy bundle). Preregistered expected-on-GPU: DENY + no launch | Environment: Intel Xeon, no GPU |
| GPU-PR-C2 | proofrecord_gpu_c2.json | TEST KEY | BLOCKED_NO_GPU | GPU-C2: missing required evidence. Preregistered expected-on-GPU: HOLD + no launch | Environment: Intel Xeon, no GPU |
| GPU-PR-C3 | proofrecord_gpu_c3.json | TEST KEY | BLOCKED_NO_GPU | GPU-C3: stale/expired evidence or policy per freshness window. Preregistered expected-on-GPU: HOLD + no launch | Environment: Intel Xeon, no GPU |
| GPU-PR-C4 | proofrecord_gpu_c4.json | TEST KEY | BLOCKED_NO_GPU | GPU-C4: artifact/evidence mismatch (presented hash differs from attested). Preregistered expected-on-GPU: DENY + no launch | Environment: Intel Xeon, no GPU |
| GPU-PR-C5 | proofrecord_gpu_c5.json | TEST KEY | BLOCKED_NO_GPU | GPU-C5: control/gateway precondition not satisfied. Preregistered expected-on-GPU: HOLD + no launch | Environment: Intel Xeon, no GPU |
| GPU-PR-C6 | proofrecord_gpu_c6.json | TEST KEY | BLOCKED_NO_GPU | GPU-C6: mutated ProofRecord (signature/digest no longer verifies). Preregistered expected-on-GPU: VERIFICATION_FAILURE + no launch | Environment: Intel Xeon, no GPU |
| GPU-PR-C7 | proofrecord_gpu_c7.json | TEST KEY | BLOCKED_NO_GPU | GPU-C7: wrong target / compute-capability mismatch. Preregistered expected-on-GPU: DENY + no launch | Environment: Intel Xeon, no GPU |
| GPU-PR-C8 | proofrecord_gpu_c8.json | TEST KEY | NOT_EXECUTED / BLOCKED_NO_GPU | GPU-C8: exclusive launcher control. Preregistered expected-on-GPU: no launch without a current ALLOW for the exact artifact; exactly one authorized launch for the exact attested artifact under clean conditions | Critical governance test; see note below |

**GPU-C8 Note:** GPU-C8 is the critical ExecutionProof governance test. It tests exclusive launcher control: that no launch of the attested CUDA artifact occurs by any path other than the sanctioned launcher given a current ALLOW, and that exactly one authorized launch occurs for the exact attested artifact under clean (GPU-C0) conditions. The ProofRecord currently records NOT_EXECUTED because no GPU hardware was available. When GPU hardware is acquired, GPU-C8 must be executed in full, and the actual result must be preserved in the ProofRecord without modification. Success requires positive evidence that the controlled launch path did not launch the kernel when ALLOW was absent, not merely that the gateway printed DENY. No claim of global non-bypassability beyond the tested path may be made.

---

## 4. CPU-Surrogate Phase ProofRecords

The CPU-surrogate phase produced ProofRecords for cases C0 through C7. C8 was not executed in the CPU-surrogate phase either (it requires real GPU semantics to be meaningful).

| ProofRecord ID | Status | Verdict | Evidence |
|---|---|---|---|
| CPU-PR-C0 | TEST_KEY_SIGNED | MATCHED | C0: CPU surrogate matched oracle output |
| CPU-PR-C1 | TEST_KEY_SIGNED | MATCHED | C1: CPU surrogate matched oracle output |
| CPU-PR-C2 | TEST_KEY_SIGNED | MATCHED | C2: CPU surrogate matched oracle output |
| CPU-PR-C3 | TEST_KEY_SIGNED | MATCHED | C3: CPU surrogate matched oracle output |
| CPU-PR-C4 | TEST_KEY_SIGNED | MATCHED | C4: CPU surrogate matched oracle output |
| CPU-PR-C5 | TEST_KEY_SIGNED | MATCHED | C5: CPU surrogate matched oracle output |
| CPU-PR-C6 | TEST_KEY_SIGNED | MATCHED | C6: CPU surrogate matched oracle output |
| CPU-PR-C7 | TEST_KEY_SIGNED | MATCHED | C7: CPU surrogate matched oracle output |
| CPU-PR-C8 | NOT_YET_CREATED | N/A | C8 not executed in CPU-surrogate phase |

---

## 5. Oracle Test ProofRecords

Oracle tests T-01 through T-07 produced individual attestation records as part of the functional test suite.

| Test | Status | Verdict | Description |
|---|---|---|---|
| T-01 | EXISTS | PASS | ramp_sums_to_N (visible reference): numpy oracle deterministic, close to float64 |
| T-02 | EXISTS | PASS | uniform_seed (visible reference): numpy oracle deterministic, close to float64 |
| T-03 | EXISTS | PASS | edges / bounds-condition (visible reference): numpy oracle handles edge/boundary inputs |
| T-04 | EXISTS | PASS | hidden_large_magnitude (hidden reference): numpy oracle close to float64 |
| T-05 | EXISTS | PASS | hidden_small_values (hidden reference): numpy oracle close to float64 |
| T-06 | EXISTS | PASS | hidden_exact_cancellation (hidden reference): numpy oracle close to float64 |
| T-07 | EXISTS | PASS | hidden_mixed_offset (hidden reference): numpy oracle close to float64 |

---

## 6. Pending Real GPU ProofRecords (NOT_YET_CREATED)

After real GPU execution, the following ProofRecords must be created:

| ProofRecord ID | When Created | Contents |
|---|---|---|
| GPU-PR-C0-REAL | After GPU execution | Real GPU C0 result; actual GPU hardware identity; signing key TBD |
| GPU-PR-C1-REAL | After GPU execution | Real GPU C1 result |
| GPU-PR-C2-REAL | After GPU execution | Real GPU C2 result |
| GPU-PR-C3-REAL | After GPU execution | Real GPU C3 result |
| GPU-PR-C4-REAL | After GPU execution | Real GPU C4 result |
| GPU-PR-C5-REAL | After GPU execution | Real GPU C5 result |
| GPU-PR-C6-REAL | After GPU execution | Real GPU C6 result |
| GPU-PR-C7-REAL | After GPU execution | Real GPU C7 result |
| GPU-PR-C8-REAL | After GPU execution | Real GPU C8 GOVERNANCE result -- CRITICAL |

---

## 7. ProofRecord Signing Policy

### Current State (TEST KEY)

All ProofRecords in this package are signed with TEST KEY. This means:
- They are valid for research and documentation purposes
- They are NOT valid for production deployment decisions
- They clearly mark the experimental, pre-GPU-execution state of the research
- The signing key identity is preserved in each ProofRecord for auditability

### Post-GPU State (Production Key -- pending)

After real GPU execution and Derek's authorization:
- A production key will be used to sign the real-GPU ProofRecords
- Test-key ProofRecords remain in the archive as evidence of the pre-GPU state
- Both sets of ProofRecords will be included in the Zenodo deposit

### TEST KEY Notice

Every ProofRecord in the current package contains the notation:
```
"signing_key": "TEST_KEY",
"key_notice": "TEST KEY -- NOT PRODUCTION. This ProofRecord is for research and development use only."
```

This notice must not be removed or overwritten.

---

## 8. ProofRecord Integrity

All existing ProofRecords are SHA256-included in `00_FREEZE/PRE_GPU_SHA256SUMS.txt`.

Any modification to an existing ProofRecord after the pre-GPU freeze is a scientific integrity violation and must be documented in the correction history.

---

*Document version: v0.1-pre-gpu | Generated: 2026-10-01 | TEST KEY -- NOT PRODUCTION*
