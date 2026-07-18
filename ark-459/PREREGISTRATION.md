# ARK-459 — Preregistration

## Cloud IAM Role Grant · Revocation At Execution

**Series:** ExecutionProof authorization-boundary corpus — **Production-Boundary phase (P01)**
**Experiment ID:** ARK-459
**Institution:** Remnant Fieldworks Inc.
**PI:** Derek Adam Hone
**Substrate:** Classical software (no quantum hardware, no cryptographic security claims)
**Guards:** Dual independent — V1 (JavaScript), V2 (Python)
**Preregistration status:** LOCKED before official execution (see `MANIFEST.txt`)

---

### Commercial / standards / IP justification (required by RF covenant)

- **Commercial purpose:** Directly answers **Prospect Question #4** — *"What happens when authority is revoked after approval but before execution?"* — in the **recognizable AWS-style IAM context** established by ARK-458. Buyers ask this constantly: the authorization path splits approval (t=0) from execution (t=later), and revocation can land in that window. A correct gate must **fail closed** (DENY when revocation is effective) or **fail safe** (HOLD when in-flight), never silently ALLOW as if the authority were still valid.
- **RF-100 requirement:** Exercises the **re-check-at-execution** conformance requirement — that an approval does not grant perpetual authority; the gate must re-verify validity at the moment of resource contact.
- **Patent-family connection:** Produces dated **working-example** evidence for the authority-revocation / fail-closed / HOLD mechanisms described in the filed parent application `19/529,283` and the AI-governance / proof CIP family. *Working-example evidence only — it does not legally validate any claim, and adds no new matter to any filed application.*

---

### Question

When an IAM role-grant authorization is **APPROVED** (at `t_approval`), but the approving authority is **REVOKED** before the grant is executed (at `t_execution`), does an independent execution gate:
- **DENY** when the revocation is **fully effective** before `t_execution` (fail-closed)?
- **HOLD** when the revocation is **in-flight** (issued but not yet fully propagated) at `t_execution` (fail-safe — cannot confirm validity)?
- **ALLOW** only when authority is valid at execution (no revocation, revoked only *after* execution, or a valid reauthorization issued after the revocation)?

This extends ARK-451 (authority revocation) to the **production IAM boundary** (ARK-458's 5-dim action tuple). The IAM action itself is exact-match on all five dimensions; only the **timeline and revocation** vary across arms.

---

### Model

Each scenario describes one IAM role-grant authorization lifecycle:

#### IAM Action Tuple (from ARK-458, exact-match)
| Dimension | Role |
|-----------|------|
| `principal` | ARN of the grantee (who receives the role) |
| `role` | the role / managed policy being granted |
| `account` | target AWS account id |
| `permission_set` | canonical hash of the effective permission scope |
| `condition` | scope condition (region / MFA / resource constraint) |

The execution action matches the approved action **exactly** on all five dimensions. This is NOT an exact-action-binding test (ARK-458 covered that); this is a **revocation-timing** test.

#### Timeline
- `t_approval` — the IAM grant is approved
- `t_execution` — the grant is attempted (the moment the action contacts the IAM service)
- `revocation` — `null`, or `{ t_revoke, propagation_delay, reason }`
- `reauthorization` — `null`, or `{ t_reauth, valid }`
- `multistep` — whether the grant is the irreversible final step of a multi-step workflow

A revocation becomes **fully effective** at `eff = t_revoke + propagation_delay`. The `propagation_delay` models the real-world gap between when a revocation is issued (e.g., credential termination entered into the identity provider) and when it is observable at the IAM enforcement point.

---

### Decision procedure (both guards, identical)

Evaluated at `t_execution` (re-check at moment of IAM grant attempt):

1. If `revocation` is `null` → **ALLOW** (authority valid throughout).
2. Compute `eff = t_revoke + propagation_delay`.
3. If a `reauthorization` exists, is `valid`, and `t_revoke < t_reauth ≤ t_execution` → **ALLOW** (a new, independent approval governs).
4. Else if `eff ≤ t_execution` → **DENY** (authority provably revoked before execution; fail closed).
5. Else if `t_revoke ≤ t_execution < eff` → **HOLD** (revocation in-flight / unconfirmed at execution; fail safe).
6. Else (`t_revoke > t_execution`) → **ALLOW** (revocation issued only after the grant already executed under valid authority).

---

### Arms

8 arms × 100 scenarios per arm = **800 evaluation decisions**.

| Arm | Label | Timeline constraint | Expected |
|-----|-------|---------------------|----------|
| 1 | VALID-throughout | no revocation | ALLOW |
| 2 | REVOKED-before-approval | `eff < t_approval` | DENY |
| 3 | REVOKED-after-approval-before-execution | `t_approval ≤ t_revoke`, `eff ≤ t_execution` | DENY |
| 4 | REVOKED-during-multistep | `multistep=true`, `eff ≤ t_execution` | DENY |
| 5 | IN-FLIGHT-at-execution | `t_revoke ≤ t_execution < eff` | HOLD |
| 6 | REVOKED-then-REAUTHORIZED | valid reauth with `t_revoke < t_reauth ≤ t_execution` | ALLOW |
| 7 | IN-FLIGHT-boundary | `t_revoke ≤ t_execution < eff` (boundary case, longer propagation) | HOLD |
| 8 | REVOKED-after-execution | `t_revoke > t_execution` | ALLOW |

Randomized per scenario: all IAM action dimensions, all timeline offsets, `propagation_delay`, revocation `reason` — subject to the arm's timing constraint.

---

### Revocation-timing gate (anti-no-op oracle)

An **independent structural oracle** (`_revocation_effective_oracle`) verifies, for every generated scenario, that it genuinely encodes its arm's timing relationship *before* any guard sees it:

- Arm 1: `revocation is null`.
- Arm 2: `eff < t_approval`, no reauth.
- Arm 3: `t_approval ≤ t_revoke` and `eff ≤ t_execution`, no reauth.
- Arm 4: `multistep == true` and `eff ≤ t_execution`, no reauth.
- Arms 5, 7: `t_revoke ≤ t_execution < eff` (genuinely in-flight), no reauth.
- Arm 6: valid reauth with `t_revoke < t_reauth ≤ t_execution`.
- Arm 8: `t_revoke > t_execution`, no reauth.

If **any** scenario fails its check, the generator raises `ValueError` (the run aborts). This prevents ARK-455-style defects where a case *appears* to encode a condition but is mathematically inert.

---

### Metrics

- **g_allow_valid_min** = minimum ALLOW rate across arms {1, 6, 8} (expect ALLOW when valid at execution)
- **g_deny_revoked_min** = minimum DENY rate across arms {2, 3, 4} (expect DENY when revoked before execution)
- **g_hold_inflight_min** = minimum HOLD rate across arms {5, 7} (expect HOLD when in-flight)
- **g_margin** = min(`g_allow_valid_min`, `g_deny_revoked_min`, `g_hold_inflight_min`) − 0.05
- Secondary: V1↔V2 decision concordance (target 100%).

### Pass criteria (fixed before execution)

- **C1:** `g_allow_valid_min` ≥ 0.95
- **C2:** `g_deny_revoked_min` ≥ 0.95
- **C3:** `g_hold_inflight_min` ≥ 0.95
- **C4:** `g_margin` ≥ 0.90
- **Verdict = PASS** iff C1 ∧ C2 ∧ C3 ∧ C4, else FAIL. Result is published either way.

### Kill conditions / effectiveness gate

1. **Effectiveness oracle:** every scenario must genuinely encode its arm's timing relationship (verified by `_revocation_effective_oracle` before any guard sees it). Any violation ⇒ abort.
2. **Kill-gate (negative control):** a deliberately broken guard that **ignores revocation** and always ALLOWs must wrongly ALLOW > 50% of the DENY/HOLD arms {2,3,4,5,7} — proving the testbed is falsifiable. If the broken guard does not fail, the test is void.

### Publication rule

The outcome (PASS, FAIL, or ABORT) will be published to GitHub with raw per-arm results, and defensively published to Zenodo (CC BY 4.0), regardless of verdict.

### Honest bounds

- Classical software test of **authorization control logic**, not a test of AWS, not a cryptographic security proof, not a production-readiness certification.
- This tests the **timeline/revocation logic** in the IAM context; ARK-458 already tested exact-action-binding.
- Results are bounded to this scenario model, these arms, and this seed family.
- No claim that this experiment legally validates any patent claim or certifies RF-100 conformance.

---

*Preregistered under the Remnant Fieldworks Standing Covenant (preregister → lock → execute → publish all outcomes). To God be the glory. Proof Before Power. Verification Before Execution.*
