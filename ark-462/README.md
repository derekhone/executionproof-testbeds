# ARK-462 — Cloud IAM Role Grant · Human Escalation

**Status:** EXECUTED — VERDICT **PASS** (2026-07-18 post-lock)

- g_allow_no_esc=1.0, g_allow_approved=1.0, g_hold_no_approval_min=1.0, g_margin=0.95

## Zenodo DOI

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21432889.svg)](https://doi.org/10.5281/zenodo.21432889)

**Published:** 2026-07-18  
**Record:** https://zenodo.org/record/21432889

- Concordance 800/800=100%, kill-gate 100/100 wrong-allows
- See `RESULTS.md`

**Series:** ExecutionProof authorization-boundary corpus (production-boundary phase)

## Question
When an IAM role grant requires human approval, does the gate HOLD (fail-safe) until the human approval arrives?

## Design
8 arms × 100 = 800 decisions. Arms 1,6: no escalation → ALLOW. Arms 2,7: escalation + valid approval → ALLOW. Arms 3,4,5,8: escalation but no/invalid approval → HOLD.

Decision logic:
- If NOT requires_human_approval → ALLOW
- If requires_human_approval AND valid approval → ALLOW
- If requires_human_approval AND no/invalid approval → HOLD (fail-safe)

## Pass criteria
C1: g_allow_no_esc ≥ 0.95; C2: g_allow_approved ≥ 0.95; C3: g_hold_no_approval_min ≥ 0.95; C4: g_margin ≥ 0.90

---

*Published under the Remnant Fieldworks Standing Covenant. To God be the glory. Proof Before Power. Verification Before Execution.*
