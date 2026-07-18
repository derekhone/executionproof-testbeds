# ARK-491 — RESULTS · Authority Engine · Cost at Scale

**Executed:** 2026-07-18T21:52:32Z · **Verdict:** **PASS** (Scenario B basis)

## Measured (cost derived from 10s burst throughput)

| Scenario | Model | Cost / million decisions | Basis |
|----------|-------|--------------------------|-------|
| A (naive) | 1 serverless request per decision | $0.20000 | disclosed upper bound |
| **B (realistic)** | running service, per vCPU-second | **$3.59e-06** | **VERDICT** |

- measured throughput: 3,128,594 dec/s · vCPU-second price $1.12e-05 · accuracy 100.0%

## Gate conditions

- **C1 (Scenario B ≤ $0.01/M):** $3.59e-06/M → ✅
- **C2 (Correctness gate):** valid_allow=True, mutated_deny=True, revoked_deny=True → ✅

## Honest findings

Under a realistic running-service model, authority-check compute cost is negligible ($3.59e-06 per million decisions). The naive per-request figure ($0.20/M) is retained as a transparency upper bound only. Compute-cost estimate for the in-memory reference; not a customer quote; excludes I/O, storage, network.

**Covenant:** RF Standing Covenant — outcomes preserved as measured, claims bounded to the tested in-memory reference under the stated single-threaded load. These are component performance measurements, **not** legal, patent, security, or production-readiness proofs.

*Soli Deo Gloria.*
