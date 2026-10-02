# CUDA-EP-001R1 — Claims Ledger

Each claim is stated at the narrowest scope the evidence supports. Anything not
listed here is **not** claimed.

**Classification:** RESEARCH ONLY — NOT PRODUCTION. TEST Dilithium3 key, NOT FIPS 204.

| # | Claim (bounded) | Evidence | Status |
|---|-----------------|----------|--------|
| 1 | On a real NVIDIA Tesla T4 (cc 7.5), with the control state unsatisfied (`LAUNCH_WINDOW_CLOSED`) **while the GPU was present**, the R1 gateway returned HOLD and did not launch. | `results.json` R1-C5 (`HOLD_CONTROL_STATE_NOT_SATISFIED`, `detected_compute_capability=7.5`, `candidate_executed=false`); signed ProofRecord R1-C5. | CONFIRMED |
| 2 | A mutated ProofRecord produced a **native** gateway VERIFICATION_FAILURE before capability release. | `results.json` R1-C6 (`verification_result=FAIL`, `reason_code=PROOFRECORD_FAIL`, `capability_released=false`); ProofRecord R1-C6. | CONFIRMED |
| 3 | A required compute capability (8.0) differing from the detected device capability (7.5) — two real non-empty values — produced DENY. | `results.json` R1-C7 (`CONSTRAINT_DENY_CAP_MISMATCH`, `required=8.0`, `detected=7.5`, `candidate_executed=false`); ProofRecord R1-C7. | CONFIRMED |
| 4 | A fully valid contract (control satisfied, cap match, valid ProofRecord) produced ALLOW and the real kernel executed correctly. | `results.json` R1-C0 (`ALLOW`, `ALL_PASS: elementwise_add N=1024`); 7/7 vectors `max_abs_err=0.0`; sanitizer zero-error. | CONFIRMED |
| 5 | The real GPU kernel executed **only** under the single ALLOW case; every HOLD/DENY/VERIFICATION_FAILURE case had no launch. | `results.json` R1-C8 (`executed: ['R1-C0']`). | CONFIRMED |
| 6 | The retest used the byte-identical frozen kernel and launcher from CUDA-EP-001. | Runtime SHA-256 re-assertion `268d125f…` (kernel) / `ea411c6d…` (launcher). | CONFIRMED |
| 7 | All five ProofRecords carry valid Dilithium3 signatures over canonical bodies with matching SHA-256 digests. | In-sandbox re-verification: 5/5 `sig_verify=True`, `digest_match=True`. | CONFIRMED (TEST key) |
| 8 | Expected outcomes were frozen before the run and not tuned afterward. | Pre-run manifest == post-run source/policy hashes. | CONFIRMED |

## Explicitly NOT claimed

- No claim that these signatures are FIPS 204 / NIST-certified or production trust anchors (TEST key).
- No claim of coverage beyond the five retested cases (C0, C5, C6, C7, C8). The
  full CUDA-EP-001 matrix was deliberately **not** rerun.
- No claim that CUDA-EP-001's recorded result changed — it stands as the frozen PARTIAL_FAIL.
- No claim of security against adversaries beyond the specific mutation tested in C6.
- No claim of performance, throughput, or multi-GPU behavior.
