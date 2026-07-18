# ARK-486 — Verification Decision · Cost at Scale

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21434400.svg)](https://doi.org/10.5281/zenodo.21434400)

**Status:** EXECUTED — VERDICT **PASS** (executed 2026-07-18 post-lock; supersedes an earlier FAIL caused by a cost-model category error)

- **Verdict basis — Scenario B (realistic running service):** Python **$7.47 per billion** decisions ($7.47e-06/M), JS $1.18e-06/M — both ≪ $0.01/M threshold ✓
- **Disclosed upper bound — Scenario A (serverless-naive):** $0.20/M (reported for transparency; NOT the verdict basis)
- See `RESULTS.md` for the full cost-model correction rationale.

## Overview

ARK-486 measures the marginal compute cost per verification decision. An earlier run FAILed at $0.20/M by charging one AWS Lambda **request** per in-process decision — a category error: the guard is an in-process library call executing millions of decisions/second, not a per-request serverless invocation. This preregistration corrects the model:

- **Scenario A (naive):** one serverless request per decision → $0.20/M. Disclosed as an unrealistic upper bound.
- **Scenario B (realistic):** running service billed per vCPU-second (Fargate $0.04048/vCPU-hr) amortized across measured throughput → the verdict basis.

**Covenant:** RF Standing Covenant — outcomes preserved as measured, claims bounded to the tested in-memory reference under the stated single-threaded load. These are component performance measurements, **not** legal, patent, security, or production-readiness proofs.

*Soli Deo Gloria.*
