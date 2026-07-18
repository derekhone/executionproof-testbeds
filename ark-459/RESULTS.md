# ARK-459 — Results

## Cloud IAM Role Grant · Revocation At Execution

**Experiment ID:** ARK-459
**Institution:** Remnant Fieldworks Inc.
**PI:** Derek Adam Hone
**Substrate:** Classical software (no quantum hardware, no cryptography)
**Guards:** Dual independent — V1 (JavaScript), V2 (Python)
**Official execution:** 2026-07-18 (post-lock — see `MANIFEST.txt`)

## Verdict: ✅ PASS

All four preregistered criteria met with perfect scores. When IAM role-grant authority is revoked before execution, the gate correctly **fails closed** (DENY when effective) or **fails safe** (HOLD when in-flight), never silently proceeding as if the authority were still valid.

| Criterion | Requirement | Value | Result |
|-----------|-------------|-------|--------|
| **C1** g_allow_valid_min | ≥ 0.95 | **1.0000** | ✅ PASS |
| **C2** g_deny_revoked_min | ≥ 0.95 | **1.0000** | ✅ PASS |
| **C3** g_hold_inflight_min | ≥ 0.95 | **1.0000** | ✅ PASS |
| **C4** g_margin | ≥ 0.90 | **0.9500** | ✅ PASS |

- Dual-guard concordance: **800/800 = 100.00%**
- Kill-gate negative control: wrongly ALLOWs **125/125 = 100%** of DENY/HOLD arms (testbed falsifiable ✓)

---

### Per-Arm Results

| Arm | Label | Expect | Correct | V1↔V2 Concordance |
|-----|-------|--------|---------|-------------------|
| 1 | VALID-throughout | ALLOW | 100/100 | 100/100 |
| 2 | REVOKED-before-approval | DENY | 100/100 | 100/100 |
| 3 | REVOKED-after-approval-before-execution | DENY | 100/100 | 100/100 |
| 4 | REVOKED-during-multistep | DENY | 100/100 | 100/100 |
| 5 | IN-FLIGHT-at-execution | HOLD | 100/100 | 100/100 |
| 6 | REVOKED-then-REAUTHORIZED | ALLOW | 100/100 | 100/100 |
| 7 | IN-FLIGHT-boundary | HOLD | 100/100 | 100/100 |
| 8 | REVOKED-after-execution | ALLOW | 100/100 | 100/100 |

**Total:** 800 decisions across 8 arms. All arms achieved **100% correctness** and **100% dual-guard concordance**.

---

### Findings

1. **Perfect fail-closed and fail-safe behavior.** Arms 2–4 (revoked before execution, fully effective) all DENY 100/100. Arms 5, 7 (revocation in-flight at execution) all HOLD 100/100. No scenario in any DENY/HOLD arm was wrongly ALLOWed.

2. **Reauthorization handled correctly.** Arm 6 (revoked, then a new valid approval issued before execution) correctly ALLOWs 100/100 — the new approval governs, not the revoked one.

3. **"Revoked after execution" is not a failure.** Arm 8 (revocation issued strictly after `t_execution`) correctly ALLOWs 100/100 — the grant already executed under valid authority; the revocation is too late to affect it.

4. **Independent dual guards in perfect agreement.** V1 (JavaScript) and V2 (Python) produced identical decisions on all 800 scenarios — the logic is deterministic and the implementations are concordant.

5. **Anti-no-op oracle prevented defects.** Every generated scenario was validated by `_revocation_effective_oracle` before any guard saw it, ensuring the timing relationships were genuine. No scenario was mathematically inert (e.g., a "revoked-before-execution" arm whose revocation actually landed after execution).

---

### Integrity / lock discipline

- The six locked files (`PREREGISTRATION.md`, both guards, generator, both run scripts) were hashed into `MANIFEST.txt` **before** the official run; post-run `./compute_hashes.sh` reproduced the identical hashes — the locked files were unchanged by execution.
- Both guards and the harness ran clean on first execution; no post-lock harness fix was required.

### Honest bounds (unchanged from preregistration)

- Classical software test of **authorization control logic**, not a test of AWS, not a cryptographic security proof, not a production-readiness certification.
- This tests the **timeline/revocation logic** in the IAM context; ARK-458 already tested exact-action-binding.
- Results are bounded to this scenario model, these arms, and this seed family.
- **No claim** that this experiment legally validates any patent claim or certifies RF-100 conformance.

---

*Published under the Remnant Fieldworks Standing Covenant (preregister → lock → execute → publish all outcomes). To God be the glory. Proof Before Power. Verification Before Execution.*
