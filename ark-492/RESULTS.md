# ARK-492 — RESULTS · Evidence Engine · Cold Start Latency

**Executed:** 2026-07-18T21:52:41Z · **Verdict:** **PASS**

## Measured (200 cold-start cycles; each builds a 10,000-record hash chain)

| Metric | Value |
|--------|-------|
| mean | 43,454 µs (43.45 ms) |
| median | 43,218 µs |
| p95 | 43,998 µs (44.00 ms) |
| min | 42,236 µs |
| max | 62,001 µs |

## Gate conditions

- **C1 (p95 ≤ 100,000 µs):** 43,998 µs → ✅
- **C2 (Correctness gate):** intact_allow=True, tampered_deny=True, broken_chain_deny=True → ✅

## Honest findings

Cold start is dominated by computing 10,000 chained SHA-256 hashes to build the reference ledger; p95 44.00 ms is within the 100 ms bound. The tamper-evidence property held: content-mutated and chain-broken records both correctly DENY. This is an in-memory reference — a production evidence store (durable writes, replication, external timestamping) would have materially different cold-start behavior, not modeled here.

**Covenant:** RF Standing Covenant — outcomes preserved as measured, claims bounded to the tested in-memory reference under the stated single-threaded load. These are component performance measurements, **not** legal, patent, security, or production-readiness proofs.

*Soli Deo Gloria.*
