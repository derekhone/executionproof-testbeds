# ARK-491 — Authority Engine · Cost at Scale

**Status:** EXECUTED — VERDICT **PASS** (executed 2026-07-18 post-lock)

- **Verdict basis — Scenario B (realistic running service):** **$3.59e-06 per million decisions** (≪ $0.01/M threshold ✓)
- **Disclosed upper bound — Scenario A (serverless-naive):** $0.20/M (transparency only; NOT the verdict basis)
- **Correctness gate PASS:** valid→ALLOW, mutated→DENY, revoked→DENY
- See `RESULTS.md` for full analysis.

## Overview

ARK-491 measures marginal compute cost per authority decision, using the same corrected cost basis established in ARK-486: a per-request serverless price per in-process decision is a category error. Verdict is taken on the realistic running-service model (Fargate per vCPU-second amortized across measured throughput).

**Scope:** minimal in-process reference implementation for MEASUREMENT ONLY — not the production Authority Engine.

**Covenant:** RF Standing Covenant — outcomes preserved as measured, claims bounded to the tested in-memory reference under the stated single-threaded load. These are component performance measurements, **not** legal, patent, security, or production-readiness proofs.

*Soli Deo Gloria.*
