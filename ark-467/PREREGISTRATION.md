# ARK-467 — Preregistration
## Production Deployment · Human Escalation

**Series:** ExecutionProof authorization-boundary corpus — **Production-Boundary phase (P01)**
**Experiment ID:** ARK-467 · **Institution:** Remnant Fieldworks Inc. · **PI:** Derek Adam Hone
**Substrate:** Classical software · **Guards:** Dual independent (V1 JS, V2 Python)
**Preregistration status:** LOCKED before official execution (see `MANIFEST.txt`)

### Commercial / standards / IP justification
- **Commercial purpose:** Answers **Prospect Question #7** — *"Can a high-risk action requiring human approval proceed without it?"* — in the AWS-style IAM context. High-privilege deployments (AdminFull, SecurityOfficer) often require human approval. A correct gate must **fail safe** (HOLD when approval required but not yet received), never wrongly ALLOW.
- **RF-100 requirement:** Exercises the **human-escalation** conformance requirement — that an approval requiring human review must HOLD until that review arrives.
- **Patent-family connection:** Produces dated **working-example** evidence for the human-escalation mechanisms. *Working-example evidence only — it does not legally validate any claim.*

### Question
When an IAM role grant requires human approval, does the gate **HOLD** (fail-safe) until the human approval arrives, then ALLOW? Or does it wrongly ALLOW without waiting?

### Model
- **IAM action tuple** (from ARK-458, exact-match)
- **requires_human_approval** flag
- **human_approval** dict: `{approved_by, timestamp, valid}` or `null`

Decision logic:
- If NOT requires_human_approval → ALLOW
- If requires_human_approval AND human_approval exists AND valid → ALLOW
- If requires_human_approval AND human_approval missing/invalid → HOLD (fail-safe)

### Arms
8 arms × 100 = **800 decisions**.

| Arm | Condition | Expected |
|-----|-----------|----------|
| 1, 6 | NO-ESCALATION-REQUIRED | ALLOW |
| 2, 7 | ESCALATION-APPROVED | ALLOW |
| 3, 8 | ESCALATION-NO-APPROVAL | HOLD |
| 4 | ESCALATION-INVALID | HOLD |
| 5 | ESCALATION-INCOMPLETE | HOLD |

### Metrics
- **g_allow_no_esc** = ALLOW rate on arms {1, 6}
- **g_allow_approved** = ALLOW rate on arms {2, 7}
- **g_hold_no_approval_min** = min HOLD rate on arms {3, 4, 5, 8}
- **g_margin** = min(all three) − 0.05

### Pass criteria
- **C1:** g_allow_no_esc ≥ 0.95
- **C2:** g_allow_approved ≥ 0.95
- **C3:** g_hold_no_approval_min ≥ 0.95
- **C4:** g_margin ≥ 0.90
- Verdict = PASS iff C1 ∧ C2 ∧ C3 ∧ C4, else FAIL.

### Kill-gate
Broken guard ignores escalation, always ALLOWs. Must wrongly ALLOW > 50% of HOLD arms {3,4,5,8}.

### Honest bounds
Classical software test. This tests **human-escalation logic**. **No claim** that this legally validates any patent claim or certifies RF-100 conformance.

---

*Preregistered under the Remnant Fieldworks Standing Covenant. To God be the glory. Proof Before Power. Verification Before Execution.*
