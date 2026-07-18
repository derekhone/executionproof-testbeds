# ARK-487 — RESULTS · Authority Engine · Cold Start Latency

**Executed:** 2026-07-18T21:52:07Z · **Verdict:** **PASS**

## Measured (200 cold-start cycles)

| Metric | Value |
|--------|-------|
| mean | 7,867 µs (7.87 ms) |
| median | 7,673 µs |
| p95 | 9,337 µs (9.34 ms) |
| min | 7,501 µs |
| max | 10,497 µs |

## Gate conditions

- **C1 (p95 ≤ 50,000 µs):** 9,337 µs → ✅
- **C2 (Correctness gate):** valid_allow=True, mutated_deny=True, revoked_deny=True → ✅

## Honest findings

Cold start is dominated by constructing the reference grant index (1,000 principals × 10 grants + deterministic revocations); the first decision itself is trivial. p95 9.34 ms is well within the 50 ms bound. This is an in-memory reference; a production engine loading state from a persistent store or external IdP would have materially different cold-start behavior, which these testbeds do not model.

**Covenant:** RF Standing Covenant — outcomes preserved as measured, claims bounded to the tested in-memory reference under the stated single-threaded load. These are component performance measurements, **not** legal, patent, security, or production-readiness proofs.

*Soli Deo Gloria.*
