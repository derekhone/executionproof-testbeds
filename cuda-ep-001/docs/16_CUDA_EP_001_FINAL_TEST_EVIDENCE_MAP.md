# CUDA-EP-001 Final Test Evidence Map

Proof Before Power(TM) / Verification Before Execution(TM)
Remnant Fieldworks Inc.

Status: PENDING - PRE-GPU. This map records exactly what was executed, what it
proves, and what it does NOT prove. No GPU hardware was available. Nothing in
this document counts as GPU evidence.

---

## 1. Purpose

This is the authoritative evidence map for CUDA-EP-001 at the pre-GPU freeze.
Every row states the evidence category, what was actually run, the raw-log
source, the measured result, the narrow conclusion that is supported, and the
conclusion that is NOT supported. Claims here are deliberately narrower than the
evidence.

Evidence categories used:
- CPU FUNCTIONAL ORACLE - numpy reference-oracle correctness checks on CPU
- CPU GATEWAY LOGIC - ExecutionProof authorization decision logic on CPU
- CPU SURROGATE - full case traces exercised in CPU-surrogate form
- PROOFRECORD-SIGNATURE - ProofRecord signing/verification with a TEST KEY
- ENVIRONMENT DISCOVERY - discovery of the absence of GPU hardware
- GPU - requires real NVIDIA GPU hardware
- NOT EXECUTED - preregistered but not run

---

## 2. Evidence Summary Table

| # | Category | What was run | Raw-log source | Result | Supports | Does NOT support |
|---|----------|--------------|----------------|--------|----------|------------------|
| E1 | CPU FUNCTIONAL ORACLE | 7 reference-oracle tests (3 visible + 4 hidden) | 10_GPU_RAW_LOGS/functional_tests_output.txt | 7/7 PASS | numpy CPU reference oracle is deterministic and close to float64 across the tested inputs | any GPU kernel correctness; CUDA numerics; memory safety |
| E2 | CPU GATEWAY LOGIC | ExecutionProof ALLOW/HOLD/DENY/VERIFICATION_FAILURE decision logic, cases C0-C7 | 10_GPU_RAW_LOGS/cpu_surrogate_reference.txt | 8/8 case traces matched preregistered expected outputs | the authorization decision logic produced the preregistered decisions on CPU | that a real CUDA kernel was gated; that a launcher was controlled on GPU |
| E3 | CPU SURROGATE | Full CPU-surrogate case suite (unit tests behind the 8 cases) | 10_GPU_RAW_LOGS/cpu_surrogate_reference.txt | 24/24 unit tests PASS | internal consistency of the surrogate logic implementation | GPU behavior of any kind |
| E4 | PROOFRECORD-SIGNATURE | ProofRecord signing and signature verification | 10_GPU_RAW_LOGS/proofrecord_signing_output.txt | Signed/verified with TEST KEY - NOT PRODUCTION | that ProofRecord structures sign and verify under a test key | production-key integrity; non-repudiation in production |
| E5 | ENVIRONMENT DISCOVERY | GPU hardware/toolchain discovery | 10_GPU_RAW_LOGS/gpu_environment_discovery.txt | nvidia-smi NOT_FOUND, nvcc NOT_FOUND, no /dev/nvidia* | that this environment has no GPU; GPU phase cannot run here | nothing about ExecutionProof behavior |
| E6 | GPU | GPU-C0 through GPU-C7 execution cases | 09_EXECUTION_GATEWAY/run_gpu_cases_output.json | 9/9 BLOCKED_NO_GPU | nothing (blocked) | all GPU verdicts remain PENDING |
| E7 | NOT EXECUTED | GPU-C8 exclusive launcher-control test | (none - not run) | NOT_EXECUTED | nothing | the single most important governance claim remains unproven |
| E8 | NOT EXECUTED | CUDA compilation (nvcc) | (none - not run) | NOT_EXECUTED | nothing | no compiled artifact exists |
| E9 | NOT EXECUTED | Compute Sanitizer (memcheck/racecheck/etc.) | (none - not run) | NOT_EXECUTED | nothing | no memory-safety or race evidence of any kind |

---

## 3. Oracle Test Detail (E1)

All seven are numpy CPU reference-oracle checks, float32 I/O, shape (1024,),
deterministic, compared close_to_f64. They test the reference oracle, not any
GPU kernel.

| Test ID | Real test name | Visibility | What it checks |
|---------|----------------|-----------|----------------|
| T-01 | ramp_sums_to_N | visible | reference oracle on a ramp input |
| T-02 | uniform_seed | visible | reference oracle on a seeded uniform input |
| T-03 | edges | visible | reference oracle on edge / boundary input values |
| T-04 | hidden_large_magnitude | hidden | reference oracle on large-magnitude values |
| T-05 | hidden_small_values | hidden | reference oracle on small values |
| T-06 | hidden_exact_cancellation | hidden | reference oracle under exact cancellation |
| T-07 | hidden_mixed_offset | hidden | reference oracle on mixed-offset input |

Correction B note: there is NO "oracle memory safety" test. The edge/boundary
check is `edges` (a bounds-condition test). No oracle test checks memory safety;
memory safety requires Compute Sanitizer on real GPU hardware (E9, NOT EXECUTED).

---

## 4. Gateway Logic Detail (E2) - CPU surrogate case traces

Preregistered expected outputs, matched 8/8 on CPU. These are decision-logic
outcomes, not GPU launches.

| Case | Condition | Preregistered decision | CPU trace |
|------|-----------|------------------------|-----------|
| C0 | clean baseline | ALLOW | matched |
| C1 | authority failure | DENY | matched |
| C2 | missing evidence | HOLD | matched |
| C3 | policy/expiry (stale) | HOLD | matched |
| C4 | evidence/artifact mismatch | DENY | matched |
| C5 | control/gateway not satisfied | HOLD | matched |
| C6 | mutated ProofRecord | VERIFICATION_FAILURE | matched |
| C7 | target compute-capability mismatch | DENY | matched |
| C8 | exclusive launcher control | (GPU only) | NOT_EXECUTED |

On real GPU, C0 must additionally cause the kernel to EXECUTE through the
launcher, and C1-C7 must cause NO launch. That launch/no-launch behavior is GPU
evidence and has NOT been produced.

---

## 5. Headline Counts (honest)

- 7/7 CPU functional oracle tests PASS (reference-oracle only)
- 8/8 CPU surrogate case traces matched preregistered expected outputs
- 24/24 CPU surrogate unit tests PASS
- 9/9 GPU execution cases BLOCKED_NO_GPU (0 executed)
- GPU-C8 exclusive launcher control: NOT EXECUTED
- CUDA compilation: NOT EXECUTED
- Compute Sanitizer: NOT EXECUTED

CPU-surrogate evidence is SUPPORTING EVIDENCE for CUDA-EP-001. It is not a
separate experiment and does not change the corpus count.

---

## 6. What this map authorizes you to say

Supported now: "The ExecutionProof authorization logic was exercised in
CPU-surrogate form, with 8/8 case traces matching the preregistered expected
outputs. Real GPU execution remains pending."

Not supported now (do NOT say): validated, verified for CUDA, GPU-validated,
production-ready, secures CUDA, guarantees GPU safety, proves kernel
correctness, cannot be bypassed, independently or NVIDIA-validated.
