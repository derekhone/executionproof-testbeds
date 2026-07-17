# ARK-454 — Self-Approval and Circular Delegation Must Fail Closed

**Status:** LOCKED → executed → **VERDICT: PASS** (see `RESULTS.md`)
**Substrate:** Classical software (no QPU, no cryptography)
**Guards:** Dual independent — V1 (JavaScript), V2 (Python)
**Series:** ExecutionProof authorization-boundary corpus (enterprise-failure-mode phase)

---

## What this tests

Can an agent get an action independently "approved" when the approval actually
collapses back onto the requester? ARK-454 models an authorization decision as a
graph of principals, controllers, and a delegation chain, and asks an independent
guard to decide **ALLOW / HOLD / DENY**. The doctrine under test:

> Approval authority must be independent of the requester. Allow only a genuinely
> independent approval; fail closed (DENY, or HOLD when independence cannot be
> established) whenever the approving authority reduces — directly or transitively —
> to the requester.

## Arms (8 × 100 = 800 scenarios)

| Arm | Label | Expected |
|---|---|---|
| 1 | LEGITIMATE-independent | ALLOW |
| 2 | DIRECT-self-approval (`approver == requester`) | DENY |
| 3 | SOCKPUPPET-controlled-identity (`controller(approver) == requester`) | DENY |
| 4 | DELEGATION-to-self (`requester ∈ delegation_chain`) | DENY |
| 5 | CIRCULAR-delegation (cycle in chain) | DENY |
| 6 | SHARED-CONTROLLER-collusion (common third-party controller) | DENY |
| 7 | INHERITED-parent-workflow-self (authority from requester's own workflow) | DENY |
| 8 | AMBIGUOUS-independence (`controller(approver) == "UNKNOWN"`) | HOLD |

Fail-closed = any verdict other than ALLOW. Arms 2–7 are genuine violations
(expected DENY); Arm 8 exercises HOLD as a first-class outcome when independence is
merely *unverifiable*.

## Discipline: the attack-effectiveness gate

Carried forward from the ARK-455 → ARK-455b lesson (a "tamper" that did not tamper;
see `../ark-455/CORRECTION.md`). Before scoring, an independent structural oracle
confirms every attack arm genuinely encodes its violation and the control arm
genuinely encodes none. Any failure ABORTS the run — a scenario that is not really
an attack can never be silently scored as a fail-closed success.

## Layout

```
PREREGISTRATION.md                 locked pre-execution design (+ .pdf/.docx)
schemas/decision_scenario_schema.json
generator/scenario_generator.py    scenario generator + attack-effectiveness oracle
verifiers/v1_guard.js              independent guard V1 (JavaScript)
verifiers/v2_guard.py              independent guard V2 (Python)
run_killgate.py                    kill-gate calibration
run_arms.py                        8-arm execution + scoring
compute_hashes.sh                  SHA-256 MANIFEST helper
MANIFEST.txt                       locked-file hashes
results/                           execution outputs (JSON)
RESULTS.md                         recorded verdict (+ .pdf/.docx)
```

## Reproduce

```bash
# no external dependencies required (pure Node + Python stdlib)
python3 run_killgate.py     # must PASS to proceed
python3 run_arms.py         # executes 8 arms, writes results/ and verdict
```

## Honest boundaries

Classical test of authorization-graph logic over a **modeled** identity/control/
delegation graph. Not a cryptographic-security proof, not a hardware result. It does
not claim coverage of adversarial identity-graph forgery, legitimate-quorum
collusion, off-graph side channels, or runtime compromise of the guard itself.
