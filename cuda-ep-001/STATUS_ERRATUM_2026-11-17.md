# CUDA-EP-001 — Status Erratum (2026-11-17)

**This erratum fixes documentation only. It changes no result.** `README.md` and `HONEST_STATUS.md` in this directory are part of the frozen pre-GPU package. They are hash-bound in `PACKAGE_SHA256SUMS.txt`, so they are deliberately left byte-identical. Their statements "Status: PENDING - PRE-GPU" and "NO REAL GPU EXECUTION HAS OCCURRED" were accurate at the 2026-10-02 freeze. They are **now stale**.

## Current status (from the published records)
- **CUDA-EP-001: PARTIAL_FAIL**, executed on a real NVIDIA Tesla T4. Zenodo 10.5281/zenodo.23094900.
  - GPU-C8 (exclusive launcher control): CONFIRMED.
  - GPU-C5: expected HOLD, actual ALLOW. This mismatch is why the record is PARTIAL_FAIL.
  - GPU-C6 and GPU-C7: scope limitations preserved.
  - The experiment is not counted as a PASS.
- **CUDA-EP-001R1: PASS.** This is a separate preregistered remediation retest of C5/C6/C7 only. Zenodo 10.5281/zenodo.23094904; see `../cuda-ep-001r1/`. It does **not** overwrite the original PARTIAL_FAIL.

## Corpus count
`README.md` cites a program-wide count of 106 total / 95 PASS / 8 preserved FAIL / 3 special. That count is not reconciled with `../CORPUS_SCOREBOARD.md`. Do not cite any aggregate total until a reconciliation is published.

Claim ceiling: single GPU, test key, research only, not independently validated.
