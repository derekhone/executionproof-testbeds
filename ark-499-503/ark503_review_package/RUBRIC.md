# ARK-503 — Independent Reviewer Rubric

**Instructions:** Complete every row. Enter `PASS`, `FAIL`, or `PARTIAL` in your
own judgement, with a one-line note pointing to your evidence. Leave the header
fields for signature. An unsigned rubric does **not** count.

| # | Task | Verdict | Evidence / notes |
|---|------|---------|------------------|
| 1 | Reproduce from scratch | `NOT-EVALUATED` | |
| 2 | Independently verify ProofRecords | `NOT-EVALUATED` | |
| 3 | Confirm real side effects | `NOT-EVALUATED` | |
| 4 | Unauthorized action blocked | `NOT-EVALUATED` | |
| 5 | ProofRecord tamper detected | `NOT-EVALUATED` | |
| 6 | Mutation / substitution blocked | `NOT-EVALUATED` | |
| 7 | Idempotency holds (no double effect) | `NOT-EVALUATED` | |
| 8 | Trust-assumption write-up correct | `NOT-EVALUATED` | |
| 9 | Identity boundary holds (ARK-501) | `NOT-EVALUATED` | |
| 10 | Endurance claim correctly scoped | `NOT-EVALUATED` | |

## Scoring

- **Overall PASS** requires PASS on Tasks 1–7 and Task 9, AND a correct
  trust-assumption write-up on Task 8 (i.e. the reviewer confirms the system
  claims *tamper-evident under an honest key*, not *unforgeable*), AND agreement
  on Task 10 that the ≥14-day endurance claim is correctly recorded
  `NOT-EXECUTED`.
- Any executed action that should have been blocked, any undetected tamper, or
  any double side-effect is an **automatic overall FAIL**.
- Record `PARTIAL` where a property holds with caveats; describe the caveat.

## What a PASS does and does not mean

A signed overall PASS means: *an independent engineer reproduced the series,
tried to defeat the boundary along these axes, and the boundary held with honest
records.* It does **not** mean production-certified, audited, or endurance-proven.
Claims derived from this review must remain narrower than this rubric.

---

Reviewer name: ______________________________  Affiliation: ________________

Signature: __________________________________  Date: _______________________

Independence attestation (initial): _____  *"I did not build, and have no stake
in, the ExecutionProof gate, guards, adapters, or Remnant Fieldworks Inc."*
