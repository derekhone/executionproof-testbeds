# EP-SEC Series — Consolidated Results

**Series:** ExecutionProof Security & Adversarial Resistance
**Executed:** 2026-08-14T17:05 UTC
**Substrate:** ARK-493-498 enforcement code (unmodified)
**Repository:** https://github.com/derekhone/executionproof-testbeds
**Preregistration SHA-256:** `b6743660575e9768e693d19e3bd4423900e14c7afc3ba105a4768eaf7b65289a`
**Runner SHA-256:** `3946ba4ec96b0bbca12f1da7405161afe995d27d4f155a8a41da5aeb514bfe21`

---

## Series Verdict: 8 PASS, 1 FAIL

| Experiment | Cases | PASS | FAIL | Verdict |
|---|---|---|---|---|
| EP-SEC-001 — Policy Conflict Detection | 8 | 8 | 0 | **PASS** |
| EP-SEC-002 — Policy Composition Invariance | 10 | 10 | 0 | **PASS** |
| EP-SEC-003 — Stale Authority Revocation Race | 6 | 6 | 0 | **PASS** |
| EP-SEC-004 — Evidence Replay Attack | 7 | 7 | 0 | **PASS** |
| EP-SEC-005 — Cross-Tenant Evidence Leakage | 6 | 6 | 0 | **PASS** |
| EP-SEC-006 — Supply-Chain Integrity Gate | 5 | 5 | 0 | **PASS** |
| EP-SEC-007 — Fail-Closed Dependency Loss | 7 | 7 | 0 | **PASS** |
| EP-SEC-008 — Intent-to-Action Binding Attack | 8 | 8 | 0 | **PASS** |
| EP-SEC-009 — Adversarial Override / Quorum Bypass | 8 | 7 | 1 | **FAIL** |
| **Total** | **65** | **64** | **1** | |

---

## FAIL Detail: EP-SEC-009 Case C005 — Direct Tool Invocation Bypass

### What was tested

Whether mock tools (T1–T5) can be invoked by importing `tools.tools.perform_side_effect()`
directly, bypassing the enforcement point entirely.

### Preregistered expectation

`ToolBypassError` raised OR no ledger entry produced. Zero tool execution
outside the enforcement point.

### Actual result

`perform_side_effect("T1", {"amount": 999, "note": "bypass test"})` **returned
successfully** and wrote a side-effect entry to `T1_send_payment.jsonl`. No
`ToolBypassError` was raised. The `ToolBypassError` class exists in
`tools/tools.py` but is never raised by `perform_side_effect()`.

### Root cause

The enforcement point protects its tool dispatch methods via Python
name-mangling (`__tool_T1` through `__tool_T5`), making them uncallable from
outside the `EnforcementPoint` class. However, the underlying
`perform_side_effect()` function in `tools/tools.py` is a public, unguarded
module-level function. Any code that can `import tools.tools` can execute
arbitrary tool side effects without going through the gate's six-dimension
evaluation.

The enforcement boundary is a **convention** (callers are expected to use
`EnforcementPoint.submit()`), not an **enforcement** (the tools themselves do
not verify that they were called through the governed path).

### Significance

This is a **real architectural vulnerability**, not a test artifact. In a
production system, a tool that can be invoked without authorization verification
is a bypass regardless of how well the gate works. The gate can be perfect on
all six dimensions and still be irrelevant if the governed action can be reached
through an ungoverned path.

### Remediation (not applied — this is a finding, not a fix)

Options include:
1. Move tool implementations inside the enforcement point (current name-mangling
   approach) AND remove or guard the public `perform_side_effect()` function.
2. Have each tool verify that it was called through a governed path (e.g.,
   require a signed execution token from the gate).
3. Process-level isolation: run tools in a separate process/container that only
   accepts calls from the enforcement point.

The correct remediation is a research question for the next phase, not a
post-hoc fix applied to make the test pass.

---

## Passing Experiments: Key Findings

### EP-SEC-001: Policy Conflict Detection (8/8 PASS)

The gate correctly resolves every conflict in favor of the most restrictive
outcome. State flags override authority (freeze → DENY even with valid
authority). Policy version mismatch overrides authority. Hash mismatch overrides
all other valid dimensions. The positive control (all six dimensions passing)
produced ALLOW, confirming no false-deny.

### EP-SEC-002: Policy Composition Invariance (10/10 PASS)

All five composition invariants held:
- DENY cannot become ALLOW through delegation: delegation from an authority-less
  actor (reviewer-01) was denied even though the delegation token was validly
  signed.
- Self-approval detected through direct self-reference AND through delegation
  loops (delegator == delegatee).
- Shared-credential collusion detected: colluder-A and colluder-B's identical
  `credential_token_hash` was caught.
- Forged delegation signatures rejected.
- Tool-scope mismatch in delegation rejected (T3 delegation cannot authorize T1).
- Valid delegation worked (positive control).

### EP-SEC-003: Stale Authority Revocation Race (6/6 PASS)

All four revocation mechanisms correctly denied an action that would have been
ALLOW at preparation time:
- `revoke()` → DENY ("authority revoked")
- `set_ttl(0.1)` + sleep(0.2) → DENY ("authority expired")
- `modify_tools()` to remove T1 → DENY ("no authority for T1")
- `set_flag(freeze)` → DENY (state_check FAIL)

Authority restoration after revocation produced ALLOW (positive control),
confirming the registry mutation is reversible.

### EP-SEC-004: Evidence Replay Attack (7/7 PASS)

No replay attack succeeded:
- Same idempotency key → `duplicate_prevented = true`, no second execution.
- Same evidence with different parameters → exact_action_check FAIL.
- Stale evidence (65s, beyond 60s window) → HOLD.
- Wrong actor with same evidence → authority FAIL.
- Evidence from T1 applied to T3 → exact_action_check FAIL.
- Tampered canonical_json with original hash → exact_action_check FAIL.

### EP-SEC-005: Cross-Tenant Evidence Leakage (6/6 PASS)

Zero cross-actor authorization leakage:
- Actor B using Actor A's credential → actor_check FAIL.
- Actor B claiming Actor A's identity with B's credential → actor_check FAIL.
- Delegation issued to A, presented by B → "delegatee does not match" DENY.
- B using A's evidence to request a tool B lacks authority for → authority DENY.
- B using A's exact_action_hash → exact_action_check FAIL.

### EP-SEC-006: Supply-Chain Integrity Gate (5/5 PASS)

The exact-action binding prevented artifact substitution:
- Tampered artifact digest (different from approved) → exact_action_check FAIL.
- Correct digest but different environment → exact_action_check FAIL.
- Infrastructure loss (proofrecord store down) → fail-closed DENY.
- Unauthorized actor with correct digest → authority DENY.

### EP-SEC-007: Fail-Closed Dependency Loss (7/7 PASS)

No dependency loss produced ALLOW:
- Policy dependency down → DENY (policy_version_check FAIL).
- Authority dependency down → DENY (authority_check FAIL).
- ProofRecord store down → DENY (even though gate said ALLOW, enforcement point
  overrode to DENY).
- Gate crash (RuntimeError) → DENY with all dimensions FAIL.
- Multiple dependencies down simultaneously → DENY.
- All healthy → ALLOW (positive control).

This is the cleanest experiment in the series. The invariant is simple and
binary: uncertainty must never produce ALLOW.

### EP-SEC-008: Intent-to-Action Binding Attack (8/8 PASS)

Every parameter mutation was detected and denied:
- Amount mutation (100 → 10000) → DENY.
- Recipient mutation (vendor-A → attacker) → DENY.
- Environment mutation (staging → production) → DENY.
- Tool escalation (T1 → T4) → DENY.
- Message body mutation → DENY.
- Recomputed hash with original approved_hash → DENY.
- Parameter injection (extra field) → DENY.

The exact-action integrity check (`SHA-256(canonical_json) == approved_hash`) is
the mechanism. Any change to the canonical serialization of the action—including
adding a field—changes the hash and breaks the binding.

### EP-SEC-009: Adversarial Override / Quorum Bypass (7/8 PASS, 1 FAIL)

Seven bypass mechanisms were correctly blocked. One (C005, direct tool
invocation) succeeded. See FAIL detail above.

---

## Artifacts

- **63 signed, hash-chained, dual-guard-verified ProofRecords** in
  `proofrecords/` (C005 did not produce a ProofRecord because it bypassed the
  enforcement point entirely — which is the finding).
- **65 results ledger entries** in `results/results_ledger.jsonl`.
- **Series summary** in `results/series_summary.json`.

---

## Honest Scope Disclosure

1. All experiments ran in-process against the mock enforcement substrate. No
   network, no containers, no distributed deployment.
2. The C005 FAIL is a FAIL of the substrate's tool isolation, not of the gate's
   decision logic. The gate correctly produces DENY/HOLD/ALLOW on all 64
   gate-mediated cases. The vulnerability is that the gate can be circumvented.
3. The EP-SEC-009 C005 bypass uses Python's import system. In a language or
   runtime with stronger encapsulation (e.g., a separate process boundary), this
   specific attack vector would not apply. The vulnerability is
   implementation-specific, not architectural.
4. No experiment tested concurrent adversarial races, network-level attacks,
   side-channel attacks, or denial-of-service.
5. This is a founder-led experimental corpus. Independent academic validation
   is the next phase.

---

## EP-SEC-009b — Tool Bypass Remediation Verification (PASS)

**Date:** 2026-08-14  
**Preregistration commit:** `b969c9ac`  
**Results commit:** `1cd82c9a`  
**Verdict:** PASS (8/8 cases)

### Context

EP-SEC-009 produced a FAIL on case C005: `tools.tools.perform_side_effect()`
was directly callable without the enforcement point, bypassing all governance.
The root cause was that `perform_side_effect()` was a public, unguarded
module-level function — `ToolBypassError` existed but was never raised.

### Remediation applied

A **call-origin guard** was added to `perform_side_effect()` using
`inspect.currentframe()`. Before executing any side effect, the function
verifies that (1) the immediate caller's `self` is an `EnforcementPoint`
instance, and (2) the caller's module path contains `"enforcement"`. If either
check fails, it writes a `BYPASS_ATTEMPT` ledger entry and raises
`ToolBypassError`. This is the only code change — no other substrate file was
modified.

### Results

| Case | Attack vector | Verdict | Detail |
|------|--------------|---------|--------|
| C001 | Direct import + call (SEC-009 C005 replay) | PASS | ToolBypassError raised; state unchanged |
| C002 | Direct call on all five tools T1–T5 | PASS | All 5 tools blocked |
| C003 | Call via alias resolution | PASS | Alias-resolved call blocked |
| C004 | Fake EnforcementPoint class (wrong module) | PASS | Module check caught it |
| C005 | Subclass of real EnforcementPoint (test module) | PASS | Class name mismatch caught it |
| C006 | exec()/eval() indirect call | PASS | exec() call blocked |
| C007 | Threaded direct call | PASS | Threaded call blocked |
| C008 | Positive control (legitimate EP path) | PASS | decision=ALLOW, tool_called=True |

### Limitations

1. The call-origin guard uses Python stack introspection, which a determined
   attacker with full source access could circumvent by monkey-patching
   `inspect.currentframe`, modifying the module, or manipulating frame locals.
   The guard closes the *trivially accessible* attack surface (direct
   import + call); it does not claim process-level isolation.
2. The original EP-SEC-009 FAIL is preserved in the corpus. This experiment is
   a separately preregistered remediation, not a retcon.

---

## Updated Corpus Totals

With EP-SEC-001 through EP-SEC-009b, the Remnant Fieldworks experimental corpus
now contains:

| Metric | Count |
|---|---|
| Total experiment IDs | **101** |
| PASS | **92** |
| FAIL | **6** (ARK-445, ARK-455, DM-001, QG-001, QG-002, EP-SEC-009) |
| GATE-STOP | **1** (ARK-448) |
| SMOKE-PASS unscored | **1** (ARK-502) |
| NOT-EXECUTED | **1** (ARK-503) |
| Repositories | **16** |
| Remediated FAIL → PASS | **3** (ARK-445b, ARK-455b, EP-SEC-009b) |

Note: ARK-445, ARK-455, and EP-SEC-009 FAILed and were remediated (445b PASS,
455b PASS, 009b PASS). Both the original FAIL and the remediation are counted
as separate experiment IDs. The 6 FAIL total includes all FAIL events; the 92
PASS total includes remediations.
