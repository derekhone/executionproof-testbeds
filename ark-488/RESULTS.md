# ARK-488 — RESULTS · Authority Engine · P95 Decision Latency

**Executed:** 2026-07-18T21:52:07Z · **Verdict:** **PASS**

## Measured (200,000 warm decisions, 10,000 warmup excluded)

| Metric | Value |
|--------|-------|
| mean | 0.293 µs |
| p50 | 0.284 µs |
| p95 | 0.320 µs |
| p99 | 0.407 µs |
| max | 15.220 µs |

## Gate conditions

- **C1 (p95 ≤ 50 µs):** 0.320 µs → ✅
- **C2 (Correctness gate):** valid_allow=True, mutated_deny=True, revoked_deny=True → ✅

## Honest findings

A warm authority check (dict lookup + two set-membership tests, no I/O) completes in sub-microsecond time at p95 (0.320 µs); the 15.22 µs max reflects occasional scheduler/GC noise. Latency is for an in-memory reference on the local test host; production I/O, serialization, and network are not modeled.

**Covenant:** RF Standing Covenant — outcomes preserved as measured, claims bounded to the tested in-memory reference under the stated single-threaded load. These are component performance measurements, **not** legal, patent, security, or production-readiness proofs.

*Soli Deo Gloria.*
