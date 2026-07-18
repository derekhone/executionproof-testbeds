# ARK-490 — Authority Engine · Sustained Throughput

**Status:** EXECUTED — VERDICT **PASS** (executed 2026-07-18 post-lock)

- Sustained throughput **2,491,235 decisions/sec** over 60s (threshold ≥100K ✓)
- 100% accuracy (149,474,101/149,474,101 decisions correct)
- **Correctness gate PASS:** valid→ALLOW, mutated→DENY, revoked→DENY
- See `RESULTS.md` for full analysis.

## Overview

ARK-490 measures sustained throughput of the reference **Authority Engine** over a 60-second window, and whether it degrades relative to burst (ARK-489).

**Scope:** minimal in-process reference implementation for MEASUREMENT ONLY — not the production Authority Engine.

**Covenant:** RF Standing Covenant — outcomes preserved as measured, claims bounded to the tested in-memory reference under the stated single-threaded load. These are component performance measurements, **not** legal, patent, security, or production-readiness proofs.

*Soli Deo Gloria.*
