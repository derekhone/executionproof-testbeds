# GPU-C8 Preregistration: Exclusive Launcher Control

- **Preregistration type:** GPU_C8_PREREGISTRATION
- **Experiment ID:** CUDA-EP-001-GPU-C8
- **Date:** 2026-10-01
- **Status:** PREREGISTERED - NOT YET EXECUTED - BLOCKED BY ENVIRONMENT
- **Label:** NOT_EXECUTED - NO GPU

## Hypothesis

Within the bounded experimental launcher path, a real CUDA kernel cannot be launched
unless the ExecutionProof gateway returns ALLOW for that exact artifact with current
valid evidence.

**Null hypothesis:** The launcher has no causal effect on whether the kernel executes.

## Positive control

- **GPU-C0 (clean baseline):** Expected ALLOW - kernel EXECUTES through the launcher.

## Negative controls

| Case | Name | Expected on GPU |
| --- | --- | --- |
| GPU-C1 | authority failure | DENY - no launch |
| GPU-C2 | missing evidence | HOLD - no launch |
| GPU-C3 | policy/expiry constraint | HOLD - no launch |
| GPU-C4 | evidence/artifact mismatch | DENY - no launch |
| GPU-C5 | control/gateway not satisfied | HOLD - no launch |
| GPU-C6 | mutated ProofRecord | VERIFICATION_FAILURE - no launch |
| GPU-C7 | target compute-capability mismatch | DENY - no launch |

## C8-specific procedure

Attempt to release GPU capability through the controlled launcher path WITHOUT a valid
current ALLOW for the exact artifact. Expected observation: no kernel launch occurs.
Then repeat with a valid ALLOW (GPU-C0 evidence) and observe that the launch occurs
exactly once, for the exact attested artifact.

## Failure criteria

- A kernel launches when the gateway verdict is not ALLOW.
- A kernel launches for an artifact whose hash differs from the attested compiled_binary_sha256.
- A kernel launches using expired or missing evidence.
- Capability is released by any path other than the sanctioned launcher (non-exclusive control).
- The positive control GPU-C0 fails to launch a correctly attested, authorized kernel.
- The gateway reports ALLOW but gateway_capability_released is false, or vice versa
  (decision/action divergence).

## Measurement

For each case record: gateway verdict, candidate_executed (bool),
gateway_capability_released (bool), launcher status, and binary hash actually launched
(if any).

## Environment block

- **GPU verdict:** NO_GPU_PRESENT - GPU_EXECUTION_BLOCKED
- **Blockers:**
  - nvidia-smi: NOT_FOUND
  - nvcc: NOT_FOUND
  - /dev/nvidia*: NOT_FOUND
  - compute-sanitizer: NOT_FOUND
- **Consequence:** GPU-C8 cannot be executed here. The ControlEngine fail-closed path is
  exercised in CPU surrogate form in RF_CUDA_Final_Package/10_TESTS, and the GPU gateway
  in this package returns BLOCKED_NO_GPU before any launch is attempted.

## Scope limits

GPU-C8 would test a governance boundary (exclusive capability release), NOT kernel
correctness, memory safety, or production safety.
