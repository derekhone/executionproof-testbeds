# ARK-488 — Authority Engine · P95 Decision Latency

**Status:** EXECUTED — VERDICT **PASS** (executed 2026-07-18 post-lock)

- Warm per-decision latency **p95 = 0.320 µs**, p99 = 0.407 µs over 200,000 decisions (threshold p95 ≤ 50 µs ✓)
- **Correctness gate PASS:** valid→ALLOW, mutated→DENY, revoked→DENY
- See `RESULTS.md` for full analysis.

## Overview

ARK-488 measures warm per-decision latency of the reference **Authority Engine** — how much latency an at-execution "does this principal still hold this authority?" check adds to the critical path.

**Scope:** minimal in-process reference implementation for MEASUREMENT ONLY — not the production Authority Engine.

**Covenant:** RF Standing Covenant — outcomes preserved as measured, claims bounded to the tested in-memory reference under the stated single-threaded load. These are component performance measurements, **not** legal, patent, security, or production-readiness proofs.

*Soli Deo Gloria.*
