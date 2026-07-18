# ARK-487 — Authority Engine · Cold Start Latency

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21434402.svg)](https://doi.org/10.5281/zenodo.21434402)

**Status:** EXECUTED — VERDICT **PASS** (executed 2026-07-18 post-lock)

- Cold start **p95 = 9.34 ms** (9,337 µs), mean 7.87 ms, over 200 runs (threshold ≤50 ms ✓)
- **Correctness gate PASS:** valid→ALLOW, mutated→DENY, revoked→DENY
- See `RESULTS.md` for full analysis.

## Overview

ARK-487 measures cold-start latency of the reference **Authority Engine** — time from constructing a fresh engine (1,000 principals × 10 grants) to the first correct current-state authority decision. The Authority Engine answers the AUTHORITY half of Verification-Before-Execution: *does this principal CURRENTLY hold the authority claimed, at execution time — not merely at approval time?*

**Scope:** minimal in-process reference implementation for MEASUREMENT ONLY — **not** the production Authority Engine (persistent store, replication, external IdP are out of scope).

**Covenant:** RF Standing Covenant — outcomes preserved as measured, claims bounded to the tested in-memory reference under the stated single-threaded load. These are component performance measurements, **not** legal, patent, security, or production-readiness proofs.

*Soli Deo Gloria.*
