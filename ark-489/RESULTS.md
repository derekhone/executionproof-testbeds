# ARK-489 — RESULTS · Authority Engine · Burst Throughput

**Executed:** 2026-07-18T21:52:22Z · **Verdict:** **PASS**

## Measured (10s burst, 10,000 warmup excluded)

| Metric | Value |
|--------|-------|
| burst throughput | 3,090,730 dec/s |
| total decisions | 30,907,309 |
| correct decisions | 30,907,309 |
| accuracy | 100.0% |

## Gate conditions

- **C1 (≥200,000 dec/s):** 3,090,730 dec/s → ✅
- **C2 (Accuracy 100%):** 100.0% → ✅
- **C3 (Correctness gate):** valid_allow=True, mutated_deny=True, revoked_deny=True → ✅

## Honest findings

The authority check sustains multi-million decisions/second in burst with zero accuracy loss. Throughput reflects a single-threaded, in-memory, warm configuration; real deployments add I/O and network not modeled here.

**Covenant:** RF Standing Covenant — outcomes preserved as measured, claims bounded to the tested in-memory reference under the stated single-threaded load. These are component performance measurements, **not** legal, patent, security, or production-readiness proofs.

*Soli Deo Gloria.*
