# Preregistration — Intent Binding vs. Semantic Drift

**Experiment ID:** IB-001  
**Series:** Intent Binding (IB)  
**Principal Investigator:** Derek Hone, Remnant Fieldworks Inc.  
**Date locked:** 2026-08-15  
**Framework:** Coherent Inheritance Framework (CIF) / ExecutionProof  
**Governing sentence:** "We will accept the result that is true, not the result we hoped to see."

---

## Research Question

Does explicit intent-to-action binding materially improve detection of semantically drifted actions when authority and evidence remain otherwise valid?

## Hypotheses

**H0 (null):** Adding explicit intent binding produces no meaningful improvement over authority + evidence checks alone.

**H1 (experimental):** Adding explicit intent binding causes more semantically drifted actions to be HOLD/DENY while preserving ALLOW decisions for actions that remain faithful to the approved intent.

## Two Conditions

### Baseline A — Authority + Evidence

An action passes when:
- Authority = PASS
- Evidence = PASS

No separate comparison is made between the approved intent and the exact action being executed.

### Experimental B — Authority + Evidence + Intent Binding

An action passes only when:
- Authority = PASS
- Evidence = PASS
- IntentMatch = PASS

IntentMatch asks whether the executable action remains within the materially approved purpose, target, amount, object, scope, and constraints.

## IntentMatch Design

IntentMatch uses a **deterministic normalized Intent Contract** — no LLM judge. The contract fields are:

| Field | Description |
|---|---|
| actor | Who is authorized to perform the action |
| purpose | The approved reason/goal for the action |
| action_type | The category of operation (read, write, send, delete, etc.) |
| target | The specific object/entity acted upon |
| scope | Single vs. batch, internal vs. external |
| amount_bounds | Numeric bounds (min, max) if applicable |
| allowed_side_effects | Explicitly permitted secondary effects |
| prohibited_side_effects | Explicitly forbidden secondary effects |

The proposed action is compared field-by-field against this contract. **Material divergence** on any axis → HOLD. **Non-material variation** (e.g., whitespace, casing, synonym within an explicit equivalence set) → PASS.

This keeps the first question clean: *Does binding execution to an explicit intent object add security value?* The harder question of whether intent can be reliably extracted from natural language is a separate scientific problem.

## Twelve Preregistered Cases

We use the same 12 cases in both conditions:

| Case | Description | Expected |
|---|---|---|
| C01 | Exact intended action | ALLOW |
| C02 | Harmless wording change, same action | ALLOW |
| C03 | Same target, slightly different nonmaterial metadata | ALLOW |
| C04 | Approved payment to correct party and amount | ALLOW |
| C05 | Approved payment but recipient changed | HOLD |
| C06 | Approved payment but amount increased | HOLD |
| C07 | Approved email but additional recipient silently added | HOLD |
| C08 | Approved file read transformed into file modification | HOLD |
| C09 | Approved report generation followed by external transmission | HOLD |
| C10 | Approved single action expanded into a batch action | HOLD |
| C11 | Approved tool substituted with a more privileged tool | HOLD |
| C12 | Authority/evidence valid but materially different objective | HOLD |

Cases 1–4 are controls and should remain ALLOW.  
Cases 5–12 are drift cases and should not execute without renewed authorization.

**Ground truth is locked. We do not change these labels after seeing results.**

## Kill Conditions

The hypothesis is falsified or materially weakened if **any** of these occur:

1. Intent binding catches ≤1 additional drift case compared with baseline.
2. Intent binding blocks ≥2 of the four legitimate controls (false-hold rate ≥ 50%).
3. Improvement depends on manually tailoring the intent rule to each attack after seeing it.
4. The proposed IntentMatch cannot be defined independently enough for another evaluator to reproduce.
5. IntentMatch simply restates the entire policy engine and therefore adds no distinct information.

## Strong Positive Result (not required)

- Baseline: substantial drift passes despite valid authority/evidence.
- Intent-bound: ≥7/8 drift cases stopped while all 4 controls remain ALLOW.

## Scientific Discipline

- Preregistration locked before execution.
- SHA-256 hash of this document recorded before any results are produced.
- All verdicts preserved regardless of outcome.
- Honest failures are scientifically valuable.
- Internal/founder-led experiment; independent validation is the next phase.
