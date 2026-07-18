# ARK-485 — RESULTS · Verification Decision · Sustained Throughput

**Executed:** 2026-07-18T21:19:17Z · **Verdict:** **PASS**

## Measured (60s sustained, 5s warmup excluded)

| Implementation | Sustained throughput | Total decisions | Accuracy | Threshold | Status |
|----------------|----------------------|-----------------|----------|-----------|--------|
| V2 (Python)    | 1,504,355 dec/s | 90,261,313 | 100.0% | ≥50,000 | ✅ |
| V1 (JavaScript)| 9,521,201 dec/s | 571,272,089 | 100.0% | ≥100,000 | ✅ |

## Gate conditions

- **C1 (Throughput):** both implementations far exceed thresholds → ✅
- **C2 (Accuracy):** 100% correct decisions, both implementations → ✅
- **Kill-gate K1 (sustained < 10% of burst):** not triggered — sustained held near burst levels.

## Honest findings

Both implementations sustained multi-million decisions/second over the full 60s with zero accuracy loss and no observed degradation. Python delivered 1,504,355 dec/s; JavaScript 9,521,201 dec/s. Throughput is reported for a single-threaded, in-memory, warm-cache configuration; real deployments add I/O, serialization, and network latency not modeled here.

**Covenant:** RF Standing Covenant — outcomes preserved as measured, claims bounded to the tested in-memory reference under the stated single-threaded load. These are component performance measurements, **not** legal, patent, security, or production-readiness proofs.

*Soli Deo Gloria.*
