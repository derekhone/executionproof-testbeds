# CUDA-EP-001R1 — Real GPU Execution Boundary, Remediation Retest

**Experiment ID:** CUDA-EP-001R1
**Remediates:** CUDA-EP-001 (`PARTIAL_FAIL | GPU-C8 CONFIRMED; GPU-C5 expected HOLD -> actual ALLOW; C6/C7 scope limitations preserved`)
**Owner:** Remnant Fieldworks Inc.
**Classification:** RESEARCH ONLY — NOT PRODUCTION. Signatures use a TEST Dilithium
key and are **NOT** FIPS 204 / NIST-certified.

---

## What this is

CUDA-EP-001 was the first real-GPU (Tesla T4) ExecutionProof boundary run. It was
an honest **PARTIAL_FAIL**: the exclusive launcher (C8) was CONFIRMED, but three
limitations were recorded and preserved. CUDA-EP-001R1 is a **completely separate**
remediation package that fixes exactly those three limitations and retests only the
remediated cases plus two controls on real NVIDIA hardware.

**CUDA-EP-001 is frozen and untouched.** This package does not modify, overwrite,
amend, or relabel any CUDA-EP-001 artifact, log, ProofRecord, branch, or result.

## The three remediations

| Case | CUDA-EP-001 limitation | R1 remediation |
|------|------------------------|----------------|
| **C5** | Control engine keyed only on `nvidia-smi` presence; HOLD could not be induced on a live GPU. | Genuine control-state predicate (`required_control_state` vs presented control state) that resolves PASS/HOLD **while a real GPU remains available**. |
| **C6** | `gateway.evaluate()` had no signature-verification branch; mutation caught only by an external verifier. | ProofRecord signature verification integrated into the native gateway path → native `VERIFICATION_FAILURE` before capability release. |
| **C7** | Constraint engine DENYd only on an EMPTY target capability; never compared to the physical device. | Real comparison of Request Contract's required compute capability vs detected physical GPU capability; mismatch (two real non-empty values) → DENY. |

## Preregistered expected outcomes (frozen before run)

| Case | Expectation |
|------|-------------|
| C0 (clean) | ALLOW + launch |
| C5 (remediated control) | HOLD + no launch |
| C6 (remediated verification) | native VERIFICATION_FAILURE + no launch |
| C7 (remediated capability) | DENY + no launch |
| C8 (exclusive launcher) | no launch without a valid ALLOW; launch only for the exact C0 artifact |

No other CUDA-EP-001 case is rerun.

## Layout

```
00_prereg/   Preregistration (scope + expected outcomes, SHA-frozen before run)
00_freeze/   Pre-run SHA-256 manifest + freeze note
source/      Remediated gateway + policy; kernel & launcher carried byte-identical
gpu_exec/    R1 retest harness (C0/C5/C6/C7/C8 only) + results/proofrecords (post-run)
diff/        Machine-readable diffs vs the frozen CUDA-EP-001 implementation
docs/        Post-run records (environment, matrix, claims ledger, limitations, report)
```

## Integrity guarantees

- Source and policy hashes frozen before execution (`00_freeze/`).
- Expected outcomes frozen in `00_prereg/` and **not** tuned after results.
- Harness re-asserts the kernel SHA-256 at runtime; aborts on mismatch.
- If any remediated case deviates from prereg, the harness records the failure,
  does **not** sign a success ProofRecord, and **stops**.
- No GitHub merge, no Zenodo publication, no corpus change performed by this package.
