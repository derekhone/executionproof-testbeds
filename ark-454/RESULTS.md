# ARK-454 Results
# Self-Approval and Circular Delegation Must Fail Closed

**Verdict: PASS**
**Execution date:** 2026-07-17
**Substrate:** Classical software (no QPU, no cryptography)
**Guards:** Dual independent — V1 (JavaScript), V2 (Python)
**Lock commit:** `ddaa795` (preregistration + code + MANIFEST hashed before execution)

---

## 1. Summary

ARK-454 tested whether an independent authorization guard refuses to treat a
request as independently approved whenever the approving authority reduces —
directly or transitively — to the requester. Two independent guards, built from the
prose specification with no shared source, evaluated 800 modeled decision scenarios
across eight arms.

The result is a clean **PASS**. The guard ALLOWed 100% of genuinely independent
approvals and failed closed on 100% of self-approval, controlled-identity,
shared-controller, delegation-to-self, circular-delegation, and inherited
self-initiated-workflow scenarios. It correctly returned **HOLD** (not ALLOW, not
DENY) on 100% of scenarios where approver independence was merely *unverifiable*.
V1–V2 exact-verdict concordance was 100% (800/800).

## 2. Kill-Gate

| Check | Result |
|---|---|
| Attack-effectiveness (50 attacks effective / 50 legit clean) | 50/50 and 50/50 ✅ |
| Both guards ALLOW all 50 legitimate | ✅ |
| Both guards fail-closed all 50 attacks | ✅ |
| V1–V2 exact-verdict concordance | 100/100 (≥99%) ✅ |
| **Kill-gate verdict** | **PASS** |

Calibration seed: `80568941947212748512692993019025823041524121853608344978736084415953485593698`

## 3. Per-Arm Results (100 scenarios each)

| Arm | Label | V1 (A/H/D) | V2 (A/H/D) | Fail-closed (worst) | Concordance | Expected | Met |
|---|---|---|---|---|---|---|---|
| 1 | LEGITIMATE-independent | 100/0/0 | 100/0/0 | ALLOW 100% | 100% | ALLOW | ✅ |
| 2 | DIRECT-self-approval | 0/0/100 | 0/0/100 | 1.0000 | 100% | DENY | ✅ |
| 3 | SOCKPUPPET-controlled-identity | 0/0/100 | 0/0/100 | 1.0000 | 100% | DENY | ✅ |
| 4 | DELEGATION-to-self | 0/0/100 | 0/0/100 | 1.0000 | 100% | DENY | ✅ |
| 5 | CIRCULAR-delegation | 0/0/100 | 0/0/100 | 1.0000 | 100% | DENY | ✅ |
| 6 | SHARED-CONTROLLER-collusion | 0/0/100 | 0/0/100 | 1.0000 | 100% | DENY | ✅ |
| 7 | INHERITED-parent-workflow-self | 0/0/100 | 0/0/100 | 1.0000 | 100% | DENY | ✅ |
| 8 | AMBIGUOUS-independence | 0/100/0 | 0/100/0 | 1.0000 (HOLD) | 100% | HOLD | ✅ |

*(A/H/D = ALLOW / HOLD / DENY counts.)* Every arm's attack-effectiveness (arms 2–8)
or control-cleanliness (arm 1) gate passed at 100/100 before scoring.

## 4. Primary Criteria (preregistered, Section 6)

| Criterion | Definition | Value | Threshold | Result |
|---|---|---|---|---|
| C1 | `G_allow_legit` (Arm 1 ALLOW, worst of V1/V2) | 1.0000 | ≥ 0.95 | ✅ PASS |
| C2 | `G_failclosed_min` (min over Arms 2–8, worst of V1/V2) | 1.0000 | ≥ 0.95 | ✅ PASS |
| C3 | `G_margin = G_failclosed_min − (1 − G_allow_legit)` | 1.0000 | ≥ 0.85 | ✅ PASS |
| — | V1–V2 exact-verdict concordance (overall) | 100.00% (800/800) | ≥ 99% | ✅ PASS |

**All three primary criteria met simultaneously → PASS.**

## 5. Secondary Findings

- **H2a — Violation universality:** all six genuine-violation classes (Arms 2–7)
  produced fail-closed at 1.0000. No violation class was exempt.
- **H2b — Dual-guard agreement:** 100% exact-verdict concordance across all 800
  scenarios. Two independent implementations of the prose decision procedure agree
  completely.
- **H2c — HOLD is first-class:** Arm 8 (unverifiable independence) returned HOLD at
  1.0000 on both guards — neither an unsafe ALLOW nor an overclaimed DENY. This is
  the three-state model behaving as designed: HOLD is the correct response to
  *ambiguous* independence, distinct from a *detected* violation.
- **H2d — DENY specificity:** the genuine-violation arms (2–7) returned DENY
  (not merely fail-closed) at 1.0000 (worst of V1/V2). The guard distinguishes a
  detected violation (DENY) from unverifiable independence (HOLD).

## 6. What ARK-454 Establishes (and What It Does Not)

**Establishes (within the modeled graph):**
- Approval authority cannot be sourced, directly or transitively, from the party it
  is meant to constrain: direct self-approval, a requester-controlled sockpuppet, a
  shared third-party controller, the requester injected into the delegation chain,
  a circular delegation loop, and authority inherited from a workflow the requester
  initiated are all refused.
- The guard fails closed with the *right* state: DENY for a detected violation,
  HOLD when independence cannot be established.
- Two independently implemented guards agree exactly, indicating the decision
  procedure is unambiguous as specified.

**Does not establish (out of scope, not claimed):**
- Any cryptographic-security or hardware property (this is classical
  authorization-graph logic).
- Robustness against adversarial forgery of the identity/control graph itself,
  collusion among legitimately independent principals, off-graph side channels, or
  runtime compromise of the guard.
- Coverage of control relationships the model does not represent.

## 7. Provenance and Reproducibility

- **Preregistration-first:** `PREREGISTRATION.md`, both guards, the generator, both
  run scripts, and the schema were hashed in `MANIFEST.txt` and committed (lock
  commit `ddaa795`) before any arm executed. No criterion was changed post-hoc.
- **Attack-effectiveness gate:** every attack arm was confirmed to genuinely encode
  its violation (100/100) and the control arm to be genuinely clean (100/100) by an
  independent structural oracle before scoring — the ARK-455-class defect (a no-op
  "attack") cannot recur silently here.
- **Seeds (256-bit, recorded in `results/`):**
  - Arm 1: `82691181889637171251212273603036076429202821227817565078732824668175041741549`
  - Arm 2: `53374642687217268768178965480644863162135913492927978782666948179527298581939`
  - Arm 3: `54958083510054961535148101813309855893099666371751875985234141202463629886173`
  - Arm 4: `56050031728694687124408581443296536708645223506245147167075317358667488072285`
  - Arm 5: `101439519570473774188143546581375691598057956091151151456345005243462761494315`
  - Arm 6: `66269702923269037997623384234872379626387267732179822939472621339688029062247`
  - Arm 7: `107147963596536186018561574198404597624003736375372313714728870755216804785665`
  - Arm 8: `95044799084371554643609064114012431097839426936785550913385249165089673854807`
- **Run window (UTC):** start `2026-07-17T19:09:59Z`, end `2026-07-17T19:10:00Z`.
- Full machine-readable outputs in `results/` (`killgate_calibration.json`,
  `arm_1_results.json` … `arm_8_results.json`, `overall_results.json`).

## 8. Corpus Placement

ARK-454 extends the integrity dimension (ARK-444 single mutation; ARK-452 workflow
step) and the audit dimension (ARK-455/455b) into the **identity and delegation**
dimension, and complements ARK-443 (multi-party quorum, single compromised
authorizer). Together they frame the separation-of-duties boundary of the
ExecutionProof control model: authorization is bound to a specific action, a
specific current state, an independent approver, and a tamper-evident record.
