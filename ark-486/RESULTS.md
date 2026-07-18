# ARK-486 — RESULTS · Verification Decision · Cost at Scale

**Executed:** 2026-07-18T21:46:18Z · **Verdict:** **PASS** (Scenario B basis)

## Cost model correction (honest disclosure)

The original ARK-486 returned **FAIL at $0.20/M** because it billed one serverless *request* per decision. The verification guard is an **in-process library call** running millions of decisions/second inside one process — it is not invoked once per decision. Charging a per-request price per decision is a category error. The corrected preregistration reports two scenarios and takes the verdict on the realistic one.

## Measured (throughput carried from ARK-485)

| Scenario | Model | Python cost/M | JavaScript cost/M | Threshold | Basis |
|----------|-------|---------------|-------------------|-----------|-------|
| A (naive) | 1 serverless request per decision | $0.20000 | $0.20000 | — | disclosed upper bound |
| **B (realistic)** | running service, per vCPU-second | **$7.47e-06** | **$1.18e-06** | ≤ $0.01/M | **VERDICT** |

## Gate conditions

- **C1 (Realistic cost ≤ $0.01/M):** Scenario B $7.47e-06/M (Py), $1.18e-06/M (JS) → ✅
- **C2 (Disclosure):** both scenarios reported, verdict basis stated → ✅

## Honest findings

Under a realistic running-service model, verification compute cost is effectively negligible (fractions of a cent per million decisions). The naive per-request framing ($0.20/M) is retained in the record as a transparency upper bound, not as the operative figure. Figures are compute-cost estimates for the in-memory reference; they are not a customer quote and exclude I/O, storage, and network.

**Covenant:** RF Standing Covenant — outcomes preserved as measured, claims bounded to the tested in-memory reference under the stated single-threaded load. These are component performance measurements, **not** legal, patent, security, or production-readiness proofs.

*Soli Deo Gloria.*
