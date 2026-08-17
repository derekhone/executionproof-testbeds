# Internal Research Note — ExecutionProof Authorization Integrity

**Date:** 2026-08-16  
**Author:** Derek Hone, Remnant Fieldworks Inc.  
**Status:** Internal working document. Not for publication without review.  
**Framework:** Coherent Inheritance Framework (CIF) / ExecutionProof  
**Governing sentence:** "We will accept the result that is true, not the result we hoped to see."

---

## The Argument

This note consolidates five preregistered, SHA-256-locked experiments into one coherent research narrative. The experiments form a three-layer argument about what happens between intent and execution in an AI authorization system:

1. **Intent must remain faithful.** An approved action must not silently drift into a different action.
2. **Authority must remain narrow.** An actor must hold exactly the capabilities needed — no more.
3. **Composed authority must not silently expand.** Individually safe capabilities must remain safe when delegated, chained, or exercised across agents.

Each layer was tested independently with preregistered cases, locked kill conditions, and preserved verdicts regardless of outcome. The sequence includes two preserved failures that are scientifically essential to the argument.

---

## Layer 1 — Intent Integrity

### IB-001: Intent Binding vs. Semantic Drift
**Verdict: FAIL (K2)**

Tested whether the ExecutionProof pipeline could distinguish harmless wording variations from genuine semantic drift. IntentMatch correctly classified all 12 cases, but the authority layer used exact string matching against canonical action names. Two legitimate controls (C02 `dispatch_email`, C03 `view_file`) were incorrectly blocked because their synonym forms did not appear in the flat `allowed_action_types` list.

*What it taught us:* The intent-checking layer worked. The authority layer had a synonym gap. The pipeline failed as a whole because both layers must pass.

### IB-002: Authority Normalization Safety
**Verdict: FAIL (K3)**

Tested whether a deterministic normalization function could resolve synonyms without expanding privilege. The function resolved all 6 legitimate aliases and rejected all 6 near-neighbor attacks with zero privilege expansions. But 4 of 6 privilege-escalation cases were accepted — not because normalization expanded anything, but because the flat authority grant already included the escalation targets (`execute_tool`, `batch_execute`, `transmit_external`, `delete_record`). The test design conflated normalization safety with authority-grant breadth.

*What it taught us:* The normalization function was safe within its preregistered cases. The flat grant was too broad. The conflation was a test-design error, not a system error — but the experiment correctly failed because the preregistered kill condition triggered.

### IB-003: Intent-Binding Pipeline Retest With Authority Normalization
**Verdict: PASS (12/12)**

Reruns the original 12 IB-001 cases with one isolated change: `normalize_authority_action_type()` applied inside `check_authority()` before the membership test. The two false holds (C02, C03) were resolved. All 8 drift detections were preserved. Zero privilege expansions. All 4 kill conditions clear.

*What it showed:* Within these 12 preregistered cases, a single isolated remediation eliminated the authority synonym gap without weakening drift detection. The result is bounded to this test set.

### Intent Integrity Summary

The IB sequence is a complete FAIL → FAIL → PASS arc:
- IB-001 exposed a real defect (authority synonym gap)
- IB-002 exposed a test-design error (grant-breadth conflation) while confirming the normalization function's safety
- IB-003 fixed the defect with an isolated remediation and passed

The two failures are preserved as-is. They are scientifically necessary: IB-003's pass is credible precisely because the failures that motivated it are on the record.

---

## Layer 2 — Authority Integrity

### AUTH-001: Least-Privilege Authority Grant Partitioning
**Verdict: PASS (18/18)**

IB-002 exposed that the flat `allowed_action_types` grant was too broad. AUTH-001 tested whether it could be replaced with narrow capability grants — each scoped by `(actor, action_type, resource_class, scope, constraints)` — without breaking legitimate workflows.

18 preregistered cases across 8 categories: ordinary low-risk actions, sensitive write/delete, external transmission, batch execution, tool execution with named-tool constraints, composed/chained multi-step workflows, privilege substitution, and resource-class boundary enforcement.

The load-bearing cases were A14 (3-step chain crossing resource classes) and A17 (4-step workflow with 4 distinct capabilities). Both passed using only their declared minimum capabilities — no "just in case" broadening needed.

*What it showed:* Within these 18 preregistered cases, narrow capability-grant partitioning authorized every legitimate action and multi-capability workflow that held exactly its declared minimum capabilities, denied every action lacking a matching capability, and exhibited zero accidental privilege inheritance.

---

## Layer 3 — Composition Safety

### AUTH-002: Capability Composition and Confused-Deputy Resistance
**Verdict: PASS (18/18)**

AUTH-001 tested grants in isolation — one actor, one action. AUTH-002 attacked the assumption behind that result: whether individually safe grants remain safe when composed across agents through delegation, chaining, and confused-deputy patterns.

The design extended the AUTH-001 model with five composition rules:
1. **No implicit delegation** — an actor's grant authorizes only that actor
2. **Explicit delegation grants** — a narrow tuple naming both delegator and delegate
3. **Request-origin binding** — if the request originated elsewhere, a delegation grant from the origin must exist (the confused-deputy defense)
4. **Grant freshness** — expired grants are non-existent
5. **No scope intersection** — grants on different resource classes do not combine

18 preregistered cases: delegated authority (with and without grants), cross-agent invocation, three confused-deputy variants (classic, tool-mediated, chained), multi-agent workflow chains, stale grants, stale delegation, capability reuse, scope-intersection attack, privilege laundering via delegation chain, and a delegate acting on its own behalf.

The load-bearing results:
- **B06/B07/B08 (confused deputy):** All three denied. Request-origin binding prevented an authorized component from being exercised for an unauthorized requester — including through a tool (B07) and through an intermediate agent chain (B08).
- **B16 (privilege laundering):** Delegation is not transitive. An intermediate delegation chain from `external-requester → analytics-agent → ops-agent` did not create authority for `external-requester` over `ops-agent`.
- **B09/B17 (multi-agent workflows):** Both passed with proper grants and delegation at each hop. The composition defense did not break legitimate multi-agent work.

*What it showed:* Within these 18 preregistered cases, the capability-grant model with request-origin binding denied every tested composition-level threat while permitting every tested legitimate multi-agent workflow.

---

## The Connected Argument

| Layer | Question | Experiments | Result |
|-------|----------|-------------|--------|
| Intent integrity | Does the pipeline preserve intent fidelity? | IB-001 (FAIL), IB-002 (FAIL), IB-003 (PASS) | Yes, after isolated remediation, within 12 cases |
| Authority integrity | Can the flat grant be narrowed without breaking work? | AUTH-001 (PASS) | Yes, within 18 cases |
| Composition safety | Do narrow grants survive delegation and confused deputies? | AUTH-002 (PASS) | Yes, within 18 cases |

The three layers are sequential and dependent:
- Intent integrity is necessary for authority integrity (if intent drifts, correct authority is meaningless)
- Authority integrity is necessary for composition safety (if grants are too broad, composition rules have nothing narrow to protect)
- Composition safety depends on both prior layers holding

The two IB failures are load-bearing: they exposed the defects that motivated AUTH-001 (grant breadth) and IB-003 (synonym gap). Without them, the later passes would lack provenance.

---

## What This Does Not Establish

Each result is bounded to its preregistered test set. Together they form an emerging experimental argument — not a proof.

Specifically, this series does **not** establish:

- General robustness against adversarial inputs not in the test sets
- Behavior under concurrent or distributed execution
- Behavior when state changes between intent approval and action execution (the next research direction: STATE-001)
- Behavior under ambiguous scope, nested actions, or conflicting constraints
- Behavior with LLM-mediated intent interpretation (all experiments use deterministic matching)
- Independent academic validation (all experiments are internal/founder-led)

---

## Corpus Position

| Metric | Value |
|--------|-------|
| Total experiments (internal) | 106 |
| This cluster | 5 (IB-001, IB-002, IB-003, AUTH-001, AUTH-002) |
| Preserved failures | 2 (IB-001, IB-002) |
| FAIL→PASS remediations | 1 (IB-001 → IB-003) |
| Total preregistered cases in cluster | 48 (12 + 18 + 6\* + 18 + 18) |
| Public corpus | Held at 101 pending coordinated release |

\*IB-002 had 18 cases but is counted as a single experiment.

---

## Next Research Direction

**STATE-001 — Temporal and State-Bound Authorization**

The three current layers assume a static world: intent, authority, and delegation are evaluated at a fixed point in time. Real systems are not static. An approval that was valid at T1 may be dangerous at T2. STATE-001 will test whether the authorization system correctly denies actions when the relevant state has changed between approval and execution.

This would add a fourth layer to the argument:

**Intent → Authority → Composition → State → Execution**

Preregistration is locked separately.

---

## ProofRecord Hashes

| Experiment | Prereg SHA-256 | ProofRecord Final Hash |
|------------|---------------|------------------------|
| IB-001 | `b349a9c1...` | `f4d55dcc...` |
| IB-002 | `a12d0a21...` | `4c1cd40b...` |
| IB-003 | `d6f788f4...` | `9862b782...` |
| AUTH-001 | `a8bf62a5...` | `cae5568c...` |
| AUTH-002 | `3393646b...` | `d4047e3e...` |

---

## Scientific Discipline

- Every experiment was preregistered and SHA-256 locked before execution.
- Every verdict was preserved regardless of outcome.
- The two failures (IB-001, IB-002) are on the record and will remain on the record.
- No ground-truth labels were changed after seeing results.
- No kill conditions were modified after seeing results.
- The synonym map (WORDING_EQUIVALENCES) was declared once and reused unchanged across all five experiments.
- Internal/founder-led experimental corpus. Independent academic validation is the next phase.

> "We will accept the result that is true, not the result we hoped to see."
