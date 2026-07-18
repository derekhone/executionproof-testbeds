# ARK-485 — Verification Decision · Sustained Throughput

**Status:** EXECUTED — VERDICT **PASS** (executed 2026-07-18 post-lock)

- V2 (Python): **1,504,355 decisions/sec** sustained over 60s (threshold ≥50K ✓)
- V1 (JavaScript): **9,521,201 decisions/sec** sustained over 60s (threshold ≥100K ✓)
- 100% accuracy (90,261,313/90,261,313 Python, 571,272,089/571,272,089 JS)
- See `RESULTS.md` for full analysis and honest findings.

## Overview

ARK-485 measures **sustained** throughput of the frozen ARK-458 deployment guard — decisions/second maintained over a 60-second window (vs. ARK-484's short burst). Answers Prospect Question #2: can verification hold up under continuous production load?

**Component under test:** Frozen ARK-458 Cloud IAM Role Grant Guard (exact 5-tuple action binding), unchanged since ARK-458.

**Covenant:** RF Standing Covenant — outcomes preserved as measured, claims bounded to the tested in-memory reference under the stated single-threaded load. These are component performance measurements, **not** legal, patent, security, or production-readiness proofs.

*Soli Deo Gloria.*
