# ARK-462 — Results
## Cloud IAM Role Grant · Human Escalation

**Experiment ID:** ARK-462 · **Institution:** Remnant Fieldworks Inc. · **PI:** Derek Adam Hone
**Official execution:** 2026-07-18 (post-lock)

## Verdict: ✅ PASS

When human approval is required, the gate correctly **fails safe** (HOLD until approval arrives).

| Criterion | Requirement | Value | Result |
|-----------|-------------|-------|--------|
| **C1** g_allow_no_esc | ≥ 0.95 | **1.0000** | ✅ PASS |
| **C2** g_allow_approved | ≥ 0.95 | **1.0000** | ✅ PASS |
| **C3** g_hold_no_approval_min | ≥ 0.95 | **1.0000** | ✅ PASS |
| **C4** g_margin | ≥ 0.90 | **0.9500** | ✅ PASS |

- Concordance: **800/800 = 100%** · Kill-gate: **100/100 wrong-allows** (falsifiable ✓)

### Findings
1. **Perfect fail-safe.** Arms 3,4,5,8 (escalation required, no/invalid approval) all HOLD 100/100.
2. **ALLOW when no escalation or valid approval.** Arms 1,6 (no escalation) + Arms 2,7 (valid approval) all ALLOW 100/100.

### Integrity
Locked files unchanged. Both guards ran clean on first execution.

---

*Published under the Remnant Fieldworks Standing Covenant. To God be the glory. Proof Before Power. Verification Before Execution.*
