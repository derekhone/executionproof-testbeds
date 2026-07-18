# ARK-489 — Authority Engine · Burst Throughput

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21434407.svg)](https://doi.org/10.5281/zenodo.21434407)

**Status:** EXECUTED — VERDICT **PASS** (executed 2026-07-18 post-lock)

- Burst throughput **3,090,730 decisions/sec** over 10s (threshold ≥200K ✓)
- 100% accuracy (30,907,309/30,907,309 decisions correct)
- **Correctness gate PASS:** valid→ALLOW, mutated→DENY, revoked→DENY
- See `RESULTS.md` for full analysis.

## Overview

ARK-489 measures peak (burst) throughput of the reference **Authority Engine** — current-state authority decisions/second in a short high-intensity window.

**Scope:** minimal in-process reference implementation for MEASUREMENT ONLY — not the production Authority Engine.

**Covenant:** RF Standing Covenant — outcomes preserved as measured, claims bounded to the tested in-memory reference under the stated single-threaded load. These are component performance measurements, **not** legal, patent, security, or production-readiness proofs.

*Soli Deo Gloria.*
