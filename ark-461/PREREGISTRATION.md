# ARK-461 — Preregistration
## Cloud IAM Role Grant · Cross-Context Replay

**Series:** ExecutionProof authorization-boundary corpus — **Production-Boundary phase (P01)**
**Experiment ID:** ARK-461 · **Institution:** Remnant Fieldworks Inc. · **PI:** Derek Adam Hone
**Substrate:** Classical software · **Guards:** Dual independent (V1 JS, V2 Python)
**Preregistration status:** LOCKED before official execution (see `MANIFEST.txt`)

### Commercial / standards / IP justification
- **Commercial purpose:** Answers **Prospect Question #6** — *"Can an approval granted for one context be replayed in another?"* — in the AWS-style IAM context. An IAM grant APPROVED for a specific tenant/session/resource/audience/environment must NOT be usable cross-context (different tenant, session, etc.). Correct gate must **fail closed** (DENY cross-context replay).
- **RF-100 requirement:** Exercises the **context-binding** conformance requirement — that an approval is bound to its context and cannot be replayed elsewhere.
- **Patent-family connection:** Produces dated **working-example** evidence for the context-binding mechanisms. *Working-example evidence only — it does not legally validate any claim.*

### Question
When an IAM role-grant authorization is **APPROVED** bound to a specific context (tenant/session/resource/audience/environment), can it be replayed to authorize the grant under a **DIFFERENT** context? A correct gate must DENY cross-context replay.

### Model
- **IAM action tuple** (from ARK-458, exact-match on all 5 dimensions)
- **Context tuple** (5 dimensions: tenant/session/resource/audience/environment)
- Grant APPROVED for `original_context`, attempted under `presented_context`.

Decision logic:
- If presented_context == original_context (exact match on all 5 dims) → ALLOW
- If ANY dimension differs → DENY (cross-context replay, fail-closed)

### Arms
8 arms × 100 scenarios = **800 decisions**.

| Arm | Condition | Expected |
|-----|-----------|----------|
| 1, 8 | EXACT-MATCH (context same) | ALLOW |
| 2 | CROSS-TENANT | DENY |
| 3 | CROSS-SESSION | DENY |
| 4 | CROSS-RESOURCE | DENY |
| 5 | CROSS-AUDIENCE | DENY |
| 6 | CROSS-ENVIRONMENT | DENY |
| 7 | MULTI-DIM (≥2 dims differ) | DENY |

### Metrics
- **g_allow_exact** = ALLOW rate on arms {1, 8}
- **g_deny_replay_min** = min DENY rate across arms {2,3,4,5,6,7}
- **g_margin** = min(g_allow_exact, g_deny_replay_min) − 0.05

### Pass criteria
- **C1:** g_allow_exact ≥ 0.95
- **C2:** g_deny_replay_min ≥ 0.95
- **C3:** g_margin ≥ 0.90
- Verdict = PASS iff C1 ∧ C2 ∧ C3, else FAIL.

### Kill-gate
Broken guard ignores context, always ALLOWs. Must wrongly ALLOW > 50% of DENY arms {2-7}.

### Honest bounds
Classical software test of authorization control logic. This tests **cross-context replay detection**; ARK-458 tested exact-action-binding, ARK-459 revocation, ARK-460 dependency loss. **No claim** that this legally validates any patent claim or certifies RF-100 conformance.

---

*Preregistered under the Remnant Fieldworks Standing Covenant. To God be the glory. Proof Before Power. Verification Before Execution.*
