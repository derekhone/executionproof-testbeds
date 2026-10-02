# CUDA-EP-001R1 — Final Result Report (Real GPU Remediation Retest)

**Experiment ID:** CUDA-EP-001R1
**Remediates:** CUDA-EP-001 (`PARTIAL_FAIL | GPU-C8 CONFIRMED; GPU-C5 expected HOLD -> actual ALLOW; C6/C7 scope limitations preserved`)
**Owner:** Remnant Fieldworks Inc.
**Run date (UTC):** 2026-10-02
**Overall:** `COMPLETED` — **ALL PREREGISTERED REMEDIATIONS PASSED**
**Classification:** RESEARCH ONLY — NOT PRODUCTION. Signatures use a TEST
Dilithium3 key (draft ML-DSA-65-aligned), **NOT** FIPS 204 / NIST-certified.

> CUDA-EP-001 is frozen and untouched. This retest neither modifies, overwrites,
> amends, nor relabels any CUDA-EP-001 artifact, log, ProofRecord, branch, or
> result. Expected outcomes were SHA-256-frozen in the preregistration **before**
> this run and were not tuned afterward (pre-run and post-run source hashes match).

---

## 1. Hardware / environment (real device)

| Field | Value |
|-------|-------|
| GPU | **NVIDIA Tesla T4** (real hardware, free Colab) |
| Compute capability | **7.5** (sm_75) |
| Driver | 580.82.07 |
| Compile arch | `sm_75`, `nvcc` exit 0 |
| Compiled binary SHA-256 | `f1a5c669033bd273c016f332068a29e20ffce792a300adb9e8dab9de1bde6e5e` |
| PTX SHA-256 | `ce6c3c8bd50b00244e41e94f516cc2a4e8548d6b83beda3dad01542dc16f74af` |
| CUBIN SHA-256 | `bcb9cb242ba0286646010aef959170afa3ee6c65a7721d61c224964f4c326035` |

This is the **same device class** (Tesla T4, cc 7.5) on which CUDA-EP-001 ran, so
the remediations are retested against the exact condition that exposed the
original limitations.

## 2. Freeze integrity (verified at runtime)

- Kernel `elementwise_add.cu` byte-identical to CUDA-EP-001:
  `268d125fe316156e9da44852afeca54838974a4a90643c375d233b5491f89b0d` — the harness
  re-asserts this at runtime and aborts on mismatch.
- Launcher `elementwise_add_launcher.py` byte-identical:
  `ea411c6d0cb9c6abd3b4ed8f438e8cb83555da7e31ce80b7cba5a3ba67ddf01e`.
- Remediated gateway `gpu_gateway_r1.py`:
  `558da59726f7615047c42197b7f2fce597101db2f0830f50ccc733397aec0986`.
- Remediated policy `gpu_policy_r1.json`:
  `8bfa277dbe9ebc2038d009bac4d9a4360cc841cd6439222cddb4919aedef1f2e`.

## 3. Kernel correctness on the real GPU (unchanged from CUDA-EP-001)

- Compiled binary run: exit 0, `ALL_PASS: elementwise_add N=1024`.
- Functional + hidden vectors: **7/7 PASS**, `max_abs_err = 0.0` on every vector.
- Compute Sanitizer: `memcheck`, `racecheck`, `initcheck`, `synccheck` all
  returncode 0, **zero errors**.

## 4. Gateway decision matrix — preregistered vs actual (real GPU)

| Case | Condition | Expected | **Actual** | Reason code | Launch? | Match |
|------|-----------|----------|------------|-------------|---------|-------|
| **R1-C0** | clean allow, control satisfied, cap matches, valid ProofRecord | ALLOW | **ALLOW** | `ALL_ENGINES_PASS` | **yes** (real kernel ran) | ✅ |
| **R1-C5** | control state NOT satisfied (window closed) while GPU present | HOLD | **HOLD** | `HOLD_CONTROL_STATE_NOT_SATISFIED` | no | ✅ |
| **R1-C6** | mutated ProofRecord | VERIFICATION_FAILURE | **VERIFICATION_FAILURE** | `PROOFRECORD_FAIL` | no | ✅ |
| **R1-C7** | required cap 8.0 vs detected 7.5 | DENY | **DENY** | `CONSTRAINT_DENY_CAP_MISMATCH` | no | ✅ |
| **R1-C8** | exclusive launcher | launch only for exact C0 ALLOW | **CONFIRMED** (only R1-C0 executed) | — | only C0 | ✅ |

`all_preregistered_remediations_passed = true`, `unexpected_failures = []`.

## 5. What each remediation proved (vs the original limitation)

- **C5 — control-state predicate.** CUDA-EP-001's control engine keyed only on
  `nvidia-smi` presence, so a live GPU always forced control PASS → the intended
  HOLD collapsed to ALLOW. R1 introduces a genuine control-state predicate
  (`required_control_state = LAUNCH_WINDOW_OPEN`). With the presented state
  `LAUNCH_WINDOW_CLOSED` **and a real Tesla T4 present (detected cap 7.5)**, the
  gateway returned **HOLD** and did not launch. The exact failure condition of
  CUDA-EP-001 is now resolved on real hardware.
- **C6 — native verification.** CUDA-EP-001's `evaluate()` had no
  signature-verification branch; mutation was only caught by an external verifier.
  R1 integrates ProofRecord signature verification into the native gateway path.
  A mutated ProofRecord produced a native **VERIFICATION_FAILURE**
  (`PROOFRECORD_FAIL`) before any capability release.
- **C7 — device-capability comparison.** CUDA-EP-001's constraint engine DENYd
  only on an EMPTY target capability and never compared to the physical device.
  R1 compares the Request Contract's required capability (**8.0**, a real accepted
  value) against the detected device capability (**7.5**). Two real, non-empty
  values that differ → **DENY** (`CONSTRAINT_DENY_CAP_MISMATCH`).

## 6. Signed ProofRecords

Five ProofRecords were signed with an ephemeral **TEST** Dilithium3 key and
written to `gpu_exec/proofrecords/`. All five independently re-verify
(Dilithium3 signature valid **and** `record_digest_sha256` matches the canonical
body) — confirmed in-sandbox after pull. **This is a TEST key, not FIPS 204 and
not a production trust anchor.**

## 7. Integrity statement

- Original CUDA-EP-001: **UNCHANGED**.
- Expected outcomes: frozen before run, **not tuned** after (pre-run vs post-run
  source/policy hashes identical).
- GitHub: pushed to feature branches only; **no merge**.
- Zenodo: deposit-ready, **NOT deposited**.
- Corpus: **not changed by this run** (CUDA-EP-001 remains the recorded 9th
  preserved FAIL; R1 is a separate remediation retest).
