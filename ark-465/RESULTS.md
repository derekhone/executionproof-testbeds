# ARK-465 — Results

## Production Deployment · Dependency Loss

**Experiment ID:** ARK-465 · **Institution:** Remnant Fieldworks Inc. · **PI:** Derek Adam Hone
**Substrate:** Classical software · **Guards:** Dual independent (V1 JS, V2 Python)
**Official execution:** 2026-07-18 (post-lock)

## Verdict: ✅ PASS

When critical dependencies are **UNAVAILABLE** at execution time, the gate correctly **fails safe** (HOLD — cannot confirm validity) rather than wrongly ALLOWing.

| Criterion | Requirement | Value | Result |
|-----------|-------------|-------|--------|
| **C1** g_allow_available | ≥ 0.95 | **1.0000** | ✅ PASS |
| **C2** g_hold_unavailable_min | ≥ 0.95 | **1.0000** | ✅ PASS |
| **C3** g_margin | ≥ 0.90 | **0.9500** | ✅ PASS |

- Dual-guard concordance: **800/800 = 100.00%**
- Kill-gate: wrongly ALLOWs **150/150 = 100%** of HOLD arms (testbed falsifiable ✓)

---

### Per-Arm Results

| Arm | Label | Expect | Correct | Concordance |
|-----|-------|--------|---------|-------------|
| 1 | ALL-AVAILABLE | ALLOW | 100/100 | 100/100 |
| 2 | PolicyRegistry UNAVAILABLE | HOLD | 100/100 | 100/100 |
| 3 | IdentityProvider UNAVAILABLE | HOLD | 100/100 | 100/100 |
| 4 | SignatureVerifier UNAVAILABLE | HOLD | 100/100 | 100/100 |
| 5 | AuditLogger UNAVAILABLE | HOLD | 100/100 | 100/100 |
| 6 | MULTIPLE UNAVAILABLE | HOLD | 100/100 | 100/100 |
| 7 | ALL-UNAVAILABLE | HOLD | 100/100 | 100/100 |
| 8 | ALL-AVAILABLE-baseline | ALLOW | 100/100 | 100/100 |

**Total:** 800 decisions, all 100% correct, 100% dual-guard concordance.

---

### Findings

1. **Perfect fail-safe behavior.** Arms 2–7 (at least one dependency unavailable) all HOLD 100/100. No ALLOW when dependencies are down.
2. **ALLOW only when all dependencies available.** Arms 1, 8 both ALLOW 100/100 when all dependencies available.
3. **Independent dual guards in perfect agreement.** V1 (JS) and V2 (Python) produced identical decisions on all 800 scenarios.

---

### Integrity

- Locked files unchanged (verified via `./compute_hashes.sh`).
- Both guards ran clean on first execution; no post-lock harness fix required.

### Honest bounds

Classical software test of authorization control logic. This tests the **dependency-loss logic**; ARK-458 tested exact-action-binding, ARK-459 tested revocation. **No claim** that this legally validates any patent claim or certifies RF-100 conformance.

---

*Published under the Remnant Fieldworks Standing Covenant. To God be the glory. Proof Before Power. Verification Before Execution.*
