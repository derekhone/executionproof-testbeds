# ARK-466 — Results
## Production Deployment · Cross-Context Replay

**Experiment ID:** ARK-466 · **Institution:** Remnant Fieldworks Inc. · **PI:** Derek Adam Hone
**Official execution:** 2026-07-18 (post-lock)

## Verdict: ✅ PASS

Cross-context replay correctly **denied** (fail-closed).

| Criterion | Requirement | Value | Result |
|-----------|-------------|-------|--------|
| **C1** g_allow_exact | ≥ 0.95 | **1.0000** | ✅ PASS |
| **C2** g_deny_replay_min | ≥ 0.95 | **1.0000** | ✅ PASS |
| **C3** g_margin | ≥ 0.90 | **0.9500** | ✅ PASS |

- Dual-guard concordance: **800/800 = 100%**
- Kill-gate: **150/150 wrong-allows** (falsifiable ✓)

### Per-Arm Results
All arms 100% correct, 100% concordance. Arms 2–7 (cross-context) all DENY 100/100.

### Findings
1. **Perfect fail-closed on cross-context replay.** Any context dimension mismatch → DENY.
2. **ALLOW only when context exact-match.** Arms 1, 8 both ALLOW 100/100.

### Integrity
Locked files unchanged. Both guards ran clean on first execution.

### Honest bounds
Classical software test of authorization control logic. This tests **cross-context replay detection**. **No claim** that this legally validates any patent claim or certifies RF-100 conformance.

---

*Published under the Remnant Fieldworks Standing Covenant. To God be the glory. Proof Before Power. Verification Before Execution.*
