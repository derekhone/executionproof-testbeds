# ARK-492 — Evidence Engine · Cold Start Latency

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21434413.svg)](https://doi.org/10.5281/zenodo.21434413)

**Status:** EXECUTED — VERDICT **PASS** (executed 2026-07-18 post-lock)

- Cold start **p95 = 44.00 ms** (43,998 µs), mean 43.45 ms, over 200 runs (threshold ≤100 ms ✓)
- **Correctness gate PASS:** intact→ALLOW, tampered→DENY, broken-chain→DENY
- See `RESULTS.md` for full analysis.

## Overview

ARK-492 measures cold-start latency of the reference **Evidence Engine** — time from constructing a fresh hash-chained evidence ledger (10,000 records) to the first correct tamper-evidence verification. The Evidence Engine answers the EVIDENCE half of Verification-Before-Execution: *is there a complete, tamper-evident record proving the execution matched what was authorized?* This completes P02 component coverage (Verification Decision, Authority Engine, Evidence Engine).

**Scope:** minimal in-process reference implementation for MEASUREMENT ONLY — **not** the production Evidence Engine (durable append-only store, replication, external notarization are out of scope).

**Covenant:** RF Standing Covenant — outcomes preserved as measured, claims bounded to the tested in-memory reference under the stated single-threaded load. These are component performance measurements, **not** legal, patent, security, or production-readiness proofs.

*Soli Deo Gloria.*
