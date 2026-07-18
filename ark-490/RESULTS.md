# ARK-490 — RESULTS · Authority Engine · Sustained Throughput

**Executed:** 2026-07-18T21:53:03Z · **Verdict:** **PASS**

## Measured (60s sustained, 5s warmup excluded)

| Metric | Value |
|--------|-------|
| sustained throughput | 2,491,235 dec/s |
| total decisions | 149,474,101 |
| correct decisions | 149,474,101 |
| accuracy | 100.0% |
| burst reference (ARK-489) | 3,090,730 dec/s |
| sustained / burst | 81% |

## Gate conditions

- **C1 (≥100,000 dec/s):** 2,491,235 dec/s → ✅
- **C2 (Accuracy 100%):** 100.0% → ✅
- **C3 (Correctness gate):** valid_allow=True, mutated_deny=True, revoked_deny=True → ✅
- **Kill-gate K1 (sustained < 10% of burst):** not triggered (81% of burst).

## Honest findings

The authority check held 2,491,235 dec/s for the full 60s at 100% accuracy — 81% of burst, showing minimal degradation over the extended window. In-memory reference; production I/O/network not modeled.

**Covenant:** RF Standing Covenant — outcomes preserved as measured, claims bounded to the tested in-memory reference under the stated single-threaded load. These are component performance measurements, **not** legal, patent, security, or production-readiness proofs.

*Soli Deo Gloria.*
