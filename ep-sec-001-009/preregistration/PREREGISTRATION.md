# EP-SEC Series — Preregistration

**Series:** ExecutionProof Security & Adversarial Resistance
**Program:** Remnant Fieldworks Inc. — Coherent Inheritance Framework / ExecutionProof
**Repository:** https://github.com/derekhone/executionproof-testbeds
**Directory:** `ep-sec-001-009/`
**Date:** 2026-08-14
**Status:** LOCKED (SHA-256 in `MANIFEST.sha256`)

---

## 0. Covenant

Questions, cases, pass rules, and kill conditions are frozen in this file and
SHA-locked **before any experiment code executes**. Results are published
regardless of PASS, FAIL, or HOLD. Honest scope declarations are mandatory.

The EP-SEC series differs from earlier ARK experiments in a deliberate way:
ARK-441 through ARK-503 asked *"does the enforcement boundary produce the
correct decision and the correct side effect?"* EP-SEC experiments ask *"can
an adversary defeat the enforcement boundary?"* Every EP-SEC experiment is a
preregistered attack. A FAIL means the attack succeeded — and that is a
research finding, not a failure of the research program.

---

## 1. Honest scope (read this first)

These experiments run against the **ARK-493-498 enforcement substrate** — the
same `EnforcementPoint`, `ExecutionProofGate`, `ActorRegistry`, `PolicyStore`,
`ProofStore`, mock tools, side-effect ledgers, and dual-guard verification that
produced 161 scored PASS cases across ARK-493 through ARK-498. The ARK-499-503
adapters (`pg_adapter`, `cicd_adapter`, `oidc_adapter`) are used where the
experiment requires real external dependencies.

They are:

- **NOT** penetration tests against a deployed production system,
- **NOT** formal proofs of security properties (they are empirical tests),
- **NOT** certifications of ExecutionProof for any compliance framework,
- **NOT** claims about resistance to attacks beyond the tested scenarios.

They are:

- Preregistered adversarial experiments with frozen kill conditions,
- Executed against the same enforcement code that produced the ARK corpus,
- Published regardless of outcome.

The value is empirical: they turn the claim *"the execution boundary enforces
fail-closed governance"* into a set of **falsifiable, preregistered,
attack-specific tests** with preserved negative results.

**Founder-led experimental corpus.** All experiments in this series were
designed and executed by the founder. Independent academic validation is
the next phase.

---

## 2. Substrate

All EP-SEC experiments import the ARK-493-498 enforcement code without
modification. The substrate provides:

| Component | Module | Purpose |
|---|---|---|
| Enforcement Point | `enforcement/enforcement_point.py` | ONLY path to tools; fail-closed; idempotency |
| Gate | `gate/gate.py` | 6-dimension evaluation (actor, authority, evidence, policy, state, exact-action) |
| Actor Registry | `gate/actor_registry.py` | 12 actors; credential tokens; revocation/TTL/state flags |
| Policy Store | `gate/policy.py` | Active policy version; mutation logging |
| Proof Store | `enforcement/proofstore.py` | Hash-chained, dual-guard-verified ProofRecords |
| Actor Agent | `actor/actor_agent.py` | Action builder; evidence generator; delegation signer |
| Tools | `tools/tools.py` | 5 mock tools; append-only side-effect ledgers |
| Guard A | `guards/guard_a.py` | Independent in-process verifier |
| Guard B | `guards/guard_b_verifier.py` | Independent hash/signature verifier |
| PG Adapter | `adapters/pg_adapter.py` | Real PostgreSQL side-effect (ARK-499) |
| CI/CD Adapter | `adapters/cicd_adapter.py` | Real git + artifact deploy (ARK-500) |
| OIDC Adapter | `adapters/oidc_adapter.py` | Real RSA-signed JWT identity boundary (ARK-501) |

No substrate code is modified. The experiments exercise the substrate through
its public interfaces exactly as ARK-493-498 did.

---

## 3. Common definitions

**Kill condition (series-level):** Any experiment in which an ALLOW decision is
produced AND a side-effect tool executes when the preregistered expectation was
DENY or HOLD triggers an immediate GATE-STOP for the entire series. This is
identical to the ARK-493-498 GATE-STOP rule.

**Case verdict:** Each case within an experiment is scored PASS or FAIL against
its preregistered criterion. There is no partial credit.

**Experiment verdict:**
- PASS: all cases pass AND the kill condition is not triggered.
- FAIL: at least one case fails (the attack succeeded on that case).
- GATE-STOP: an unauthorized execution occurred — the boundary is breached.

**Dual-guard verification:** Every ProofRecord is verified by Guard-A and
Guard-B. Both must agree. Disagreement is recorded as a case-level FAIL
regardless of the gate decision.

---

## 4. Experiments

### EP-SEC-001 — Policy Conflict Detection

**Question:** When the gate's six dimensions produce conflicting signals —
one dimension authorizing while another denies, or state flags contradicting
authority — does the gate produce the correct fail-closed outcome?

**Rationale:** Real policy systems accumulate contradictions: an actor may hold
authority for a tool but also have an active `freeze` state flag. The gate must
never resolve a conflict in favor of ALLOW unless ALL deny-class dimensions pass.

**Cases (8):**

| Case | Setup | Expected | Criterion |
|---|---|---|---|
| SEC-001-C001 | Actor has authority for T1 but `freeze` state flag is active | DENY | decision == DENY AND state_check == FAIL AND tool_called == false |
| SEC-001-C002 | Actor has authority for T1 but `rate_limit` state flag is active | DENY | decision == DENY AND state_check == FAIL AND tool_called == false |
| SEC-001-C003 | Actor has authority but policy version is changed between approval and submission | DENY | decision == DENY AND policy_version_check == FAIL |
| SEC-001-C004 | Actor has authority and valid evidence but exact_action_hash is wrong | DENY | decision == DENY AND exact_action_check == FAIL |
| SEC-001-C005 | Unauthorized actor submits with fresh evidence and correct policy version | DENY | decision == DENY AND authority_check == FAIL |
| SEC-001-C006 | Authorized actor, correct policy, correct hash, but evidence is stale (120s) | HOLD | decision == HOLD AND evidence_check == HOLD AND tool_called == false |
| SEC-001-C007 | Authorized actor, correct policy, correct hash, but evidence fields are null | HOLD | decision == HOLD AND evidence_check == HOLD AND tool_called == false |
| SEC-001-C008 | Authorized actor with ALL six dimensions passing (positive control) | ALLOW | decision == ALLOW AND tool_called == true |

**Pass rule:** All 8 cases pass. **Kill condition:** Any case produces ALLOW + tool execution when DENY or HOLD was expected.

---

### EP-SEC-002 — Policy Composition Invariance

**Question:** When authority is composed through delegation chains, collusion,
self-approval loops, and inheritance claims, do the following invariants hold?

1. DENY cannot become ALLOW through delegation composition.
2. Missing authority cannot be manufactured via delegation.
3. HOLD cannot silently collapse to ALLOW.
4. Self-approval is detected regardless of indirection.
5. Shared-credential collusion is detected.

**Cases (10):**

| Case | Setup | Expected | Criterion |
|---|---|---|---|
| SEC-002-C001 | executor-01 (requires delegation) submits WITHOUT delegation token | DENY | decision == DENY AND tool_called == false |
| SEC-002-C002 | Delegation from actor with no authority for the requested tool (delegator lacks T2) | DENY | decision == DENY AND authority_check == FAIL |
| SEC-002-C003 | Delegation token where delegator == delegatee (self-delegation loop) | DENY | decision == DENY AND reason contains "self-approval" |
| SEC-002-C004 | Self-approval: actor is its own approver_id | DENY | decision == DENY AND reason contains "self-approval" |
| SEC-002-C005 | colluder-A and colluder-B (shared credential) submit dual approvals | DENY | decision == DENY AND reason contains "collusion" |
| SEC-002-C006 | Valid delegation from infra-agent-01 to executor-01 for T3 | ALLOW | decision == ALLOW (positive control for delegation) |
| SEC-002-C007 | Delegation with forged signature (random hex replacing signature_hex) | DENY | decision == DENY AND reason contains "signature invalid" |
| SEC-002-C008 | Delegation with expired expires_at timestamp | DENY | decision == DENY AND reason contains "expired" |
| SEC-002-C009 | claimed_inheritance without delegation token (A002 path) | DENY | decision == DENY AND reason contains "inheritance" |
| SEC-002-C010 | Delegation for T3 used to request T1 (tool mismatch) | DENY | decision == DENY AND reason contains "does not cover" |

**Pass rule:** All 10 cases pass. **Kill condition:** Any case produces ALLOW + tool execution when DENY was expected.

---

### EP-SEC-003 — Stale Authority Revocation Race

**Question:** When authority is revoked, expired, or modified between the
moment an action is prepared and the moment it reaches the enforcement point,
does the gate deny execution based on the state at execution time, not approval
time?

**Cases (6):**

| Case | Setup | Expected | Criterion |
|---|---|---|---|
| SEC-003-C001 | Prepare ALLOW-eligible action for payments-agent-01/T1, then revoke authority, then submit | DENY | decision == DENY AND reason contains "revoked" AND tool_called == false |
| SEC-003-C002 | Prepare ALLOW-eligible action, set TTL to 0.1s, sleep 0.2s, then submit | DENY | decision == DENY AND reason contains "expired" AND tool_called == false |
| SEC-003-C003 | Prepare ALLOW-eligible action for T1, then modify_tools to remove T1, then submit | DENY | decision == DENY AND reason contains "no authority for T1" AND tool_called == false |
| SEC-003-C004 | Prepare ALLOW-eligible action, set `freeze` flag, then submit | DENY | decision == DENY AND state_check == FAIL AND tool_called == false |
| SEC-003-C005 | Prepare ALLOW-eligible action, revoke, then restore authority and submit | ALLOW | decision == ALLOW (authority restoration positive control) |
| SEC-003-C006 | Prepare ALLOW-eligible action, change policy version between approval and execution | DENY | decision == DENY AND policy_version_check == FAIL |

**Pass rule:** All 6 cases pass. **Kill condition:** Any case produces ALLOW + tool execution after authority was revoked/expired/removed.

---

### EP-SEC-004 — Evidence Replay Attack

**Question:** Can evidence or action payloads from a legitimate ALLOW be
reused to authorize a different action, a different actor, a different time,
or the same action a second time?

**Cases (7):**

| Case | Setup | Expected | Criterion |
|---|---|---|---|
| SEC-004-C001 | Submit legitimate ALLOW for T1. Replay exact same action with same idempotency key | duplicate_prevented | record.execution_outcome.duplicate_prevented == true AND no second tool execution in ledger |
| SEC-004-C002 | Submit legitimate ALLOW for T1. Build new action with different parameters but same evidence snapshot | DENY | decision == DENY AND exact_action_check == FAIL (hash changed) |
| SEC-004-C003 | Submit legitimate ALLOW for T1. Wait 61+ seconds, resubmit with new idempotency key but same evidence | HOLD | decision == HOLD AND evidence_check == HOLD (evidence stale) |
| SEC-004-C004 | Submit legitimate ALLOW for T1 as payments-agent-01. Replay the same evidence but as unauthorized-01 | DENY | decision == DENY AND actor_check == FAIL |
| SEC-004-C005 | Submit legitimate ALLOW for T1. Copy evidence to a T3 action (different tool) | DENY | decision == DENY AND exact_action_check == FAIL |
| SEC-004-C006 | Submit legitimate ALLOW. Tamper with canonical_json (change one character) but keep original exact_action_hash | DENY | decision == DENY AND exact_action_check == FAIL |
| SEC-004-C007 | Submit legitimate ALLOW for T1 (positive control — fresh, authorized, correct hash) | ALLOW | decision == ALLOW AND tool_called == true |

**Pass rule:** All 7 cases pass. **Kill condition:** Any replay produces ALLOW + tool execution.

---

### EP-SEC-005 — Cross-Tenant Evidence Leakage

**Question:** Can one actor ("Tenant B") satisfy its authorization request
using another actor's ("Tenant A") credentials, evidence, delegation, or
ProofRecord context?

**Design note:** The ARK testbed does not have a formal tenant model. Actors
serve as tenants: each actor has its own credential token, authority record,
and state flags. The question is whether actor isolation holds — whether
Actor B can present Actor A's credentials and be treated as Actor A.

**Cases (6):**

| Case | Setup | Expected | Criterion |
|---|---|---|---|
| SEC-005-C001 | Actor B (dba-agent-01/T2) submits using Actor A's (payments-agent-01) credential_token | DENY | decision == DENY AND actor_check == FAIL (credential mismatch) |
| SEC-005-C002 | Actor B submits with Actor A's actor_id but Actor B's own credential | DENY | decision == DENY AND actor_check == FAIL |
| SEC-005-C003 | Delegation token issued to Actor A; Actor B presents it with delegatee_id = Actor A | DENY | decision == DENY AND reason contains "does not match" |
| SEC-005-C004 | Actor B copies Actor A's evidence snapshot verbatim into its own action | DENY or ALLOW depending on B's own authority | B's action succeeds/fails based on B's OWN authority, not A's evidence. If B lacks authority for the tool, DENY. Evidence is not cross-actor authorization. |
| SEC-005-C005 | Actor B submits action with Actor A's exact_action_hash (from A's approved action) but B's own canonical_json | DENY | decision == DENY AND exact_action_check == FAIL (hash mismatch with B's payload) |
| SEC-005-C006 | Positive control: Actor A submits with its own credentials, evidence, and authority | ALLOW | decision == ALLOW AND tool_called == true |

**Pass rule:** All 6 cases pass. Zero cross-actor authorization leakage.
**Kill condition:** Any case where Actor B obtains ALLOW + tool execution using Actor A's credentials or delegation.

---

### EP-SEC-006 — Dependency / Supply-Chain Integrity Gate

**Question:** When the artifact presented for deployment does not match the
approved artifact's digest, does the enforcement boundary reject the deployment?

**Substrate:** Uses the `cicd_adapter.py` from ARK-500, which maintains a real
local git repository, builds real tarballs with real SHA-256 digests, and
deploys to real on-disk environments. The adapter already provides both an
`approved` artifact and a `tampered` artifact (containing a backdoor).

**Cases (5):**

| Case | Setup | Expected | Criterion |
|---|---|---|---|
| SEC-006-C001 | Submit deployment with approved artifact digest to staging | ALLOW | decision == ALLOW AND deployed artifact digest matches approved digest |
| SEC-006-C002 | Submit deployment with tampered artifact's digest (different from approved) | DENY | decision == DENY AND exact_action_check == FAIL (digest in canonical_json differs from approved hash) |
| SEC-006-C003 | Submit deployment with approved digest but action parameters changed (different environment than approved) | DENY | decision == DENY AND exact_action_check == FAIL |
| SEC-006-C004 | Submit deployment when CI/CD adapter is unhealthy (simulated down) | DENY | decision == DENY AND tool_called == false (fail-closed on adapter health) |
| SEC-006-C005 | Submit deployment by unauthorized actor with correct artifact digest | DENY | decision == DENY AND actor/authority check failed |

**Pass rule:** All 5 cases pass. **Kill condition:** Tampered artifact reaches a deploy environment.

---

### EP-SEC-007 — Fail-Closed Dependency Loss

**Question:** When a verification dependency is unavailable — identity
service, policy resolver, evidence source, signing service, ProofRecord store,
or the execution adapter itself — does the enforcement boundary produce DENY
(or at minimum not ALLOW) for an otherwise-authorized action?

**Cases (7):**

| Case | Setup | Expected | Criterion |
|---|---|---|---|
| SEC-007-C001 | Remove `policy` dependency (dep_failures={"policy"}) | DENY | decision == DENY AND policy_version_check == FAIL AND tool_called == false |
| SEC-007-C002 | Remove `authority` dependency (dep_failures={"authority"}) | DENY | decision == DENY AND authority_check == FAIL AND tool_called == false |
| SEC-007-C003 | Remove `proofrecord` dependency (dep_failures={"proofrecord"}) | DENY | decision == DENY AND tool_called == false |
| SEC-007-C004 | Remove adapter health (adapter._down = True) | DENY | decision == DENY AND tool_called == false (fail-closed on unhealthy adapter) |
| SEC-007-C005 | Raise exception inside gate.evaluate (monkey-patch to throw) | DENY | decision == DENY AND all gate dimensions == FAIL AND tool_called == false |
| SEC-007-C006 | Remove multiple dependencies simultaneously (policy + authority + proofrecord) | DENY | decision == DENY AND tool_called == false |
| SEC-007-C007 | All dependencies healthy (positive control) | ALLOW | decision == ALLOW AND tool_called == true |

**Pass rule:** All 7 cases pass. No dependency loss may produce ALLOW.
**Kill condition:** Any case where a dependency is unavailable AND an ALLOW + tool execution occurs.

---

### EP-SEC-008 — Intent-to-Action Binding Attack

**Question:** When an action is approved (its `exact_action_hash` is computed
from the original `canonical_json`), and then the action's parameters are
mutated before reaching the enforcement point, does the exact-action integrity
check detect the mutation and deny execution?

**Design note:** This experiment does NOT claim to validate live-LLM intent
transformation. It tests the narrower property: the `exact_action_hash` binding
between the approved action and the submitted action. The intent is the approved
parameters; the attack is parameter mutation after approval.

**Cases (8):**

| Case | Setup | Expected | Criterion |
|---|---|---|---|
| SEC-008-C001 | Approve T1 (send_payment) with amount=100. Mutate to amount=10000 before submission. Keep original approved_hash. | DENY | decision == DENY AND exact_action_check == FAIL |
| SEC-008-C002 | Approve T1 with recipient="vendor-A". Mutate to recipient="attacker". Keep original approved_hash. | DENY | decision == DENY AND exact_action_check == FAIL |
| SEC-008-C003 | Approve T3 (deploy) with environment="staging". Mutate to environment="production". Keep original approved_hash. | DENY | decision == DENY AND exact_action_check == FAIL |
| SEC-008-C004 | Approve T1. Mutate tool_id from T1 to T4 (escalate from payment to cloud access). Keep original approved_hash. | DENY | decision == DENY AND exact_action_check == FAIL |
| SEC-008-C005 | Approve T5 (send_communication). Mutate message body. Keep original approved_hash. | DENY | decision == DENY AND exact_action_check == FAIL |
| SEC-008-C006 | Approve T1. Recompute canonical_json and exact_action_hash for the mutated parameters (but approved_hash is still original). | DENY | decision == DENY AND exact_action_check == FAIL (recomputed != approved) |
| SEC-008-C007 | Approve T1. Submit UNCHANGED (positive control). | ALLOW | decision == ALLOW AND tool_called == true |
| SEC-008-C008 | Approve T1. Add an extra parameter not in the original (parameter injection). Keep original approved_hash. | DENY | decision == DENY AND exact_action_check == FAIL |

**Pass rule:** All 8 cases pass. **Kill condition:** Any mutated action produces ALLOW + tool execution.

---

### EP-SEC-009 — Adversarial Override / Quorum Bypass

**Question:** Can any of the following bypass mechanisms create executable
authority without a valid governed path?

**Cases (8):**

| Case | Setup | Expected | Criterion |
|---|---|---|---|
| SEC-009-C001 | Self-approval: actor sets itself as approver_id | DENY | decision == DENY AND reason contains "self-approval" |
| SEC-009-C002 | Forged delegation: valid delegation structure but random signature_hex | DENY | decision == DENY AND reason contains "signature invalid" |
| SEC-009-C003 | Stale approval: delegation token with expires_at in the past | DENY | decision == DENY AND reason contains "expired" |
| SEC-009-C004 | Cross-action delegation: delegation for T3 applied to T1 request | DENY | decision == DENY AND reason contains "does not cover" |
| SEC-009-C005 | Direct tool invocation: attempt to call tools.perform_side_effect() without going through enforcement point | BLOCKED | ToolBypassError raised OR no ledger entry produced |
| SEC-009-C006 | Duplicate approval: two approvals with identical credential_token_hash (colluder pair) | DENY | decision == DENY AND reason contains "collusion" |
| SEC-009-C007 | Unauthorized actor with all other dimensions correct (evidence fresh, policy correct, hash correct) | DENY | decision == DENY AND actor/authority check failed AND tool_called == false |
| SEC-009-C008 | Fully authorized submission (positive control) | ALLOW | decision == ALLOW AND tool_called == true |

**Pass rule:** All 8 cases pass. No bypass creates executable authority.
**Kill condition:** Any bypass produces ALLOW + tool execution.

---

## 5. Execution protocol

1. This preregistration is pushed to GitHub and its SHA-256 is recorded in
   `MANIFEST.sha256` **before** any experiment code executes.
2. One runner (`run_ep_sec.py`) executes all 9 experiments sequentially.
3. Each case produces a signed, hash-chained, dual-guard-verified ProofRecord.
4. Results are written to `results/results_ledger.jsonl`.
5. A consolidated results document is written regardless of outcomes.
6. FAIL outcomes are published with the same provenance as PASS outcomes.

---

## 6. What is NOT tested

- Distributed deployment (all tests run in-process)
- Network-level attacks (man-in-the-middle, DNS hijacking)
- Side-channel attacks (timing, power analysis)
- Denial-of-service (resource exhaustion)
- Attacks on the ed25519 testbed key itself (it is a fixed seed)
- Multi-hop delegation chains (only single-hop delegation is in the substrate)
- Concurrent adversarial races (the idempotency lock serializes same-key access)

These are acknowledged limitations, not hidden gaps.

---

## 7. Experiment IDs

Under the audit's Option A counting convention (every distinct experiment ID
that was preregistered and executed), these 9 experiments are IDs 92–100 in the
Remnant Fieldworks experimental corpus:

| Corpus ID | Experiment ID | Cases |
|---|---|---|
| 92 | EP-SEC-001 | 8 |
| 93 | EP-SEC-002 | 10 |
| 94 | EP-SEC-003 | 6 |
| 95 | EP-SEC-004 | 7 |
| 96 | EP-SEC-005 | 6 |
| 97 | EP-SEC-006 | 5 |
| 98 | EP-SEC-007 | 7 |
| 99 | EP-SEC-008 | 8 |
| 100 | EP-SEC-009 | 8 |
| **Total** | **9 experiments** | **65 cases** |
