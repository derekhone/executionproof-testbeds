# ARK-458 — Results

## Cloud IAM Role Grant · Exact-Action Binding

**Verdict: PASS**
**Executed:** 2026-07-18T18:13:54Z UTC (post-lock)
**Substrate:** Classical software (no quantum hardware, no cryptographic security claim)
**Guards:** Dual independent — V1 (JavaScript), V2 (Python)

---

### Headline

- `g_allow_exact` = **1.0000** (C1 ≥ 0.95 ✓)
- `g_deny_mutation_min` = **1.0000** (C2 ≥ 0.95 ✓)
- `g_margin` = **0.9500** (C3 ≥ 0.90 ✓)
- Dual-guard concordance: **800/800 = 100.00%**
- Every one of the 700 mutated IAM actions across arms 2–8 was **DENIED**; every exact match in arm 1 was **ALLOWED**.

### Per-arm readout (100 scenarios each)

| Arm | Condition | Expected | V2 ALLOW | V2 DENY | V1↔V2 concordance |
|-----|-----------|----------|----------|---------|-------------------|
| 1 | BASELINE-exact-action-match | ALLOW | 100 | 0 | 100% |
| 2 | ROLE-ESCALATION | DENY | 0 | 100 | 100% |
| 3 | PRINCIPAL-SWAP | DENY | 0 | 100 | 100% |
| 4 | ACCOUNT-SWAP | DENY | 0 | 100 | 100% |
| 5 | PERMISSION-EXPANSION | DENY | 0 | 100 | 100% |
| 6 | CONDITION-STRIP | DENY | 0 | 100 | 100% |
| 7 | MULTI-DIM-TAMPER | DENY | 0 | 100 | 100% |
| 8 | CONFUSABLE-NEAR-MATCH | DENY | 0 | 100 | 100% |

### Kill-gate (negative control)

A deliberately lenient comparator (case/whitespace-folding, homoglyph-mapping, ignoring the effective-policy hash, and accepting any "at-least-as-privileged" role) was run against the same 700 attack scenarios. It **wrongly ALLOWED 281/700** mutated actions:

| Arm | Bad-guard wrong-allows |
|-----|------------------------|
| 2 ROLE-ESCALATION | 100 |
| 5 PERMISSION-EXPANSION | 100 |
| 7 MULTI-DIM-TAMPER | 5 |
| 8 CONFUSABLE-NEAR-MATCH | 76 |

This confirms the testbed is **falsifiable** — the arms are genuine attacks that a naive guard fails, and the exact-action-binding guard's clean sweep is meaningful rather than trivial. (Full detail in `results/killgate_results.json`.)

### Effectiveness gate

All 800 scenarios passed the effectiveness oracle: every attack arm genuinely mutated the action, arm 2 was a strict privilege escalation in every case, arm 8 was confusable-under-normalization in every case, and arm 1 was a true exact match.

### What this shows (bounded)

Within this scenario model, an ExecutionProof exact-action-binding guard authorizes an IAM role grant **only** when the execution action is byte-identical to the approved action across all five binding dimensions, and **fails closed** on every mutation — including the two failure modes a lenient comparator most often gets wrong: **privilege escalation** and **confusable near-matches**. Two independent implementations agreed on all 800 decisions.

### Honest bounds / what this does NOT show

- This is a classical test of **authorization control logic**, not a test of AWS IAM itself, not a cryptographic security proof, and not a production-readiness or RF-100 conformance certification.
- `permission_set` is a plain SHA-256 identity token for "the exact policy body," not a security primitive.
- Results are bounded to this scenario model, these eight arms, and this seed family.
- This experiment provides dated **working-example** evidence for disclosed mechanisms; it does **not** legally validate any patent claim and adds no new matter to any filed application.

### Reproduce

```bash
cd ark-458
node --version         # dual-guard V1 requires Node
python3 run_killgate.py   # negative control
python3 run_arms.py       # 8 arms × 100 scenarios, dual guards
./compute_hashes.sh       # verify locked files match MANIFEST.txt
```

Artifacts: `results/arm_1_results.json` … `results/arm_8_results.json`, `results/overall_results.json`, `results/killgate_results.json`, and per-arm `results/arm_N_scenarios.json`.

---

*To God be the glory. Proof Before Power. Verification Before Execution.*
