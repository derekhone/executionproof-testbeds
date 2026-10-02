# CUDA-EP-001 Real GPU Execution -- Case Results
## Remnant Fieldworks Inc.
## Document: 05_CUDA_EP_001_REAL_GPU_CASE_RESULTS.md
## Status: GPU EXECUTION PENDING -- BLOCKED_NO_GPU
## Date: 2026-10-02

---

## GPU-Phase Case Results: ALL NOT_EXECUTED

No GPU-phase case has been executed on real GPU hardware.
The gateway was invoked but returned BLOCKED_NO_GPU for all 9 cases before any case logic ran.

---

## Result Classification (per RF doctrine)

Each case gets exactly one result:
PASS / FAIL / INCONCLUSIVE / NOT_EXECUTED / GATE-STOP

No vague: "mostly passed," "essentially passed," "functionally passed."

---

## GPU-Phase Results Table (Pre-Execution State)

| Case | Description | Expected Verdict | Observed Verdict | Kernel Launched | Sanitizer | Result Classification |
|---|---|---|---|---|---|---|
| GPU-C0 | Clean baseline | ALLOW | NOT_EXECUTED | -- | -- | NOT_EXECUTED |
| GPU-C1 | Authority failure | DENY | NOT_EXECUTED | -- | -- | NOT_EXECUTED |
| GPU-C2 | Missing evidence | HOLD | NOT_EXECUTED | -- | -- | NOT_EXECUTED |
| GPU-C3 | Policy / expiry constraint | HOLD | NOT_EXECUTED | -- | -- | NOT_EXECUTED |
| GPU-C4 | Evidence / artifact mismatch | DENY | NOT_EXECUTED | -- | -- | NOT_EXECUTED |
| GPU-C5 | Control / gateway not satisfied | HOLD | NOT_EXECUTED | -- | -- | NOT_EXECUTED |
| GPU-C6 | Mutated ProofRecord | VERIFICATION_FAILURE | NOT_EXECUTED | -- | -- | NOT_EXECUTED |
| GPU-C7 | Compute-capability mismatch | DENY | NOT_EXECUTED | -- | -- | NOT_EXECUTED |
| GPU-C8 | Exclusive launcher control | GATED | NOT_EXECUTED | -- | -- | NOT_EXECUTED |
| **TOTAL** | | | | | | **9/9 NOT_EXECUTED** |

---

## CPU-Surrogate Phase Results (Previously Executed)

| Case | Description | Expected Verdict | Observed Verdict | Result |
|---|---|---|---|---|
| C0 (Case A) | Clean baseline | ALLOW | ALLOW | PASS (CPU surrogate only) |
| C1 (Case B) | Authority failure | DENY | DENY | PASS (CPU surrogate only) |
| C2 (Case C) | Missing evidence | HOLD | HOLD | PASS (CPU surrogate only) |
| C3 (Case D) | Policy / expiry constraint | HOLD | HOLD | PASS (CPU surrogate only) |
| C4 (Case E) | Evidence / artifact mismatch | DENY | DENY | PASS (CPU surrogate only) |
| C5 (Case F) | Control / gateway not satisfied | HOLD | HOLD | PASS (CPU surrogate only) |
| C6 (Case G) | Mutated ProofRecord | VERIFICATION_FAILURE | VERIFICATION_FAILURE | PASS (CPU surrogate only) |
| C7 (Case H) | Compute-capability mismatch | DENY | DENY | PASS (CPU surrogate only) |
| C8 | Exclusive launcher control | N/A | NOT_EXECUTED | NOT_EXECUTED (cannot simulate) |
| **TOTAL** | | | | **8/8 PASS (CPU surrogate); 1 NOT_EXECUTED** |

---

## GPU Gateway Hardware Detection Result

The GPU execution gateway was invoked in the previous session.
This is NOT a GPU-phase case result. It is hardware detection confirmation only.

- Gateway invoked: YES
- Hardware detected: NO
- Result for all 9 cases: BLOCKED_NO_GPU
- all_blocked flag: true
- Blocker evidence: nvidia-smi NOT_FOUND, /dev/nvidia* NOT_FOUND, torch.cuda.is_available()=False
- What this confirms: gateway detection logic is correct
- What this does NOT confirm: gateway routing, verdict logic, ProofRecord construction for real GPU outputs

---

## GPU-C8 -- Most Important Governance-Boundary Test

GPU-C8 tests whether any path can bypass the ExecutionProof execution gateway
and reach GPU kernel execution through an unauthorized channel.

STATUS: NOT_EXECUTED (NOT_EXECUTED in CPU-surrogate phase; NOT_EXECUTED in GPU phase)

This is the highest-value unexecuted test in the CUDA-EP-001 corpus.

Preregistered expected behavior: No unauthorized path reaches GPU execution.
Exactly one valid launch: through the sanctioned gateway under the ALLOW condition.

The governance-boundary question remains open until this test executes on real GPU hardware.

Do not report this as PASS. Do not report this as FAIL. Report exactly as: NOT_EXECUTED.

---

## Negative Results Preservation

Per RF doctrine: negative results are publishable results.

The BLOCKED_NO_GPU outcome from the GPU-phase gateway invocation is preserved as evidence.
It is not a failure of the framework -- it is correct behavior when no GPU is present.
It is also not a success of GPU execution -- it is a hardware absence confirmation only.

The NOT_EXECUTED classifications for GPU-C0 through GPU-C8 are preserved unchanged.
They will be updated with real observations after GPU hardware is obtained.
