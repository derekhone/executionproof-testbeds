# CUDA-EP-001R1 — Limitations

CUDA-EP-001R1 successfully remediated the three limitations of CUDA-EP-001 on real
hardware. The following limitations remain and are stated honestly so no claim is
over-read.

## Resolved by R1 (previously CUDA-EP-001 limitations)

- **C5** — control HOLD could not be induced on a live GPU. **Resolved:** genuine
  control-state predicate yields HOLD while the GPU is present.
- **C6** — no native verification branch in `evaluate()`. **Resolved:** signature
  verification integrated into the native gateway path.
- **C7** — constraint engine never compared required vs detected capability.
  **Resolved:** real device-capability comparison with two non-empty values.

## Remaining limitations (not claimed as solved)

1. **TEST signing key, not FIPS 204.** ProofRecords are signed with an ephemeral
   Dilithium3 TEST key (draft ML-DSA-65-aligned), generated at run time. This is
   NOT a FIPS 204 / NIST-certified implementation and NOT a production trust
   anchor or key-management scheme.
2. **Single device class.** Retested only on Tesla T4 (cc 7.5). Behavior on other
   architectures (e.g., sm_80/sm_86/sm_90) is not measured here.
3. **Scoped case set.** Only C0, C5, C6, C7, C8 were rerun, by design. The full
   CUDA-EP-001 matrix was not re-executed in R1.
4. **Single mutation in C6.** C6 tests one representative ProofRecord mutation.
   It does not enumerate the full adversarial space of forgeries or replay attacks.
5. **Control-state source is policy-declared.** The control-state predicate reads
   a presented control-state token; binding that token to an external,
   tamper-evident authority (scheduler, HSM, time service) is out of scope here.
6. **Research harness, not an integrated runtime.** The gateway is evaluated as a
   pre-execution decision layer in a test harness; it is not wired into a
   production CUDA scheduler or driver shim.
7. **No performance characterization.** Latency/throughput overhead of the
   verification and comparison steps is not measured.

## Integrity notes

- CUDA-EP-001 is unchanged; its PARTIAL_FAIL stands as recorded.
- Expected outcomes were frozen before the run; no post-hoc tuning.
- No GitHub merge, no Zenodo deposit, no corpus change performed by this run.
