# ARK-466 — Production Deployment · Cross-Context Replay

**Status:** EXECUTED — VERDICT **PASS** (2026-07-18 post-lock)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21433076.svg)](https://doi.org/10.5281/zenodo.21433076)

- g_allow_exact = 1.0000 · g_deny_replay_min = 1.0000 · g_margin = 0.9500



- Concordance 800/800 = 100%, kill-gate 150/150 wrong-allows
- See `RESULTS.md`

**Series:** ExecutionProof authorization-boundary corpus (production-boundary phase)

## Question
When an IAM role-grant authorization is **APPROVED** bound to a specific context (tenant/session/resource/audience/environment), can it be replayed under a **DIFFERENT** context? Correct gate must DENY cross-context replay.

## Design
8 arms × 100 = 800 decisions. Arms 1,8: EXACT-MATCH → ALLOW. Arms 2–7: cross-context → DENY.

Decision logic:
- If presented_context == original_context (exact match on all 5 dims) → ALLOW
- If ANY dimension differs → DENY

## Pass criteria
C1: g_allow_exact ≥ 0.95; C2: g_deny_replay_min ≥ 0.95; C3: g_margin ≥ 0.90

## Honest bounds
Classical software test. This tests **cross-context replay detection**. **No claim** that this legally validates any patent claim or certifies RF-100 conformance.

---

*Published under the Remnant Fieldworks Standing Covenant. To God be the glory. Proof Before Power. Verification Before Execution.*
