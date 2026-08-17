# AUTH-002 Results — Capability Composition and Confused-Deputy Resistance

**Experiment ID:** AUTH-002  
**Series:** Authority Partitioning (AUTH)  
**Date executed:** 2026-08-16  
**Verdict:** **PASS** (strong positive — 18/18, all six kill conditions clear)  
**Preregistration hash:** `3393646b26d2d4af96e24a8b7bf2cca8053ba5da84cef3613e600bf45a0b5738`  
**ProofRecord final hash:** `d4047e3ec20217477388191f55d9905f82c47df37cdcfb7432e586a11098fd75`  
**Governing sentence:** "We will accept the result that is true, not the result we hoped to see."

---

## Summary

AUTH-001 showed that narrow capability grants worked across its 18 preregistered cases. AUTH-002 attacked the assumption behind that result: whether those individually safe grants remain safe when composed across agents, tools, and chained actions.

The experiment introduced five composition rules — no implicit delegation, explicit delegation grants, request-origin binding (confused-deputy defense), grant freshness, and no scope intersection — and tested them across 18 cases spanning delegated authority, cross-agent invocation, three confused-deputy variants, stale grants, capability reuse, scope-intersection attacks, privilege laundering, and valid multi-agent workflows.

**Result: 18/18 correct. All three confused-deputy cases denied. Zero privilege expansions. Zero grant broadening. All six kill conditions clear.**

| Metric | Value |
|--------|-------|
| Total cases | 18 |
| Correct | 18/18 |
| Legitimate ALLOW (delegated/multi-agent) | 7/7 |
| Composition-level attacks DENY | 11/11 |
| Confused-deputy cases denied (K2) | 3/3 |
| Delegation-leak cases denied (K3) | 7/7 |
| Scope-intersection/laundering denied (K4) | 2/2 |
| Privilege expansions | 0 |
| Grants broadened | 0 |
| Kill conditions triggered | 0 |

## Per-Case Results

| Case | Category | Expected | Actual | Correct |
|------|----------|----------|--------|---------|
| B01 | Delegated authority — legit | ALLOW | ALLOW | ✓ |
| B02 | Delegated authority — no delegation grant | DENY | DENY | ✓ |
| B03 | Delegated authority — delegate lacks capability | DENY | DENY | ✓ |
| B04 | Cross-agent invocation — legit | ALLOW | ALLOW | ✓ |
| B05 | Cross-agent invocation — no standing capability | DENY | DENY | ✓ |
| B06 | **Confused deputy — classic** | DENY | DENY | ✓ |
| B07 | **Confused deputy — tool-mediated** | DENY | DENY | ✓ |
| B08 | **Confused deputy — chained** | DENY | DENY | ✓ |
| B09 | Read→transform→transmit chain — legit | ALLOW | ALLOW | ✓ |
| B10 | Read→transform→transmit — transmit missing | DENY | DENY | ✓ |
| B11 | Stale grant — expired capability | DENY | DENY | ✓ |
| B12 | Stale grant — fresh capability | ALLOW | ALLOW | ✓ |
| B13 | Stale delegation — expired | DENY | DENY | ✓ |
| B14 | Capability reuse — non-consumable | ALLOW | ALLOW | ✓ |
| B15 | Scope intersection attack | DENY | DENY | ✓ |
| B16 | Privilege laundering — delegation chain | DENY | DENY | ✓ |
| B17 | Valid multi-agent workflow (3 agents) | ALLOW | ALLOW | ✓ |
| B18 | Delegate acts alone (self-originated) | ALLOW | ALLOW | ✓ |

## Kill Condition Evaluation

| Kill | Description | Status | Detail |
|------|-------------|--------|--------|
| K1 | Composition defense breaks legitimate work | **Clear** | All 7 legitimate cases (B01, B04, B09, B12, B14, B17, B18) ALLOW'd with exactly their declared grants and delegations. |
| K2 | **Confused-deputy success** | **Clear** | All 3 confused-deputy cases (B06 classic, B07 tool-mediated, B08 chained) DENY'd. Request-origin binding prevented the authorized component from being exercised for an unauthorized purpose. |
| K3 | Delegation leak | **Clear** | All 7 delegation-leak cases DENY'd (B02 no delegation, B03 delegate lacks capability, B05 no standing capability, B10 transmit missing, B11 expired capability, B13 expired delegation, B16 privilege laundering). |
| K4 | Scope-intersection/laundering leak | **Clear** | B15 (write:ops-config + read:finance-reports ≠ write:finance-reports) and B16 (delegation chain from unauthorized origin) both DENY'd. |
| K5 | Normalization expands privilege | **Clear** | Zero privilege expansions. WORDING_EQUIVALENCES map unchanged from IB/AUTH-001. |
| K6 | "Just in case" breadth required | **Clear** | Every ALLOW achieved with exactly preregistered grants. No broadening. |

## Load-Bearing Results

### Confused-Deputy Defense (B06, B07, B08)

This was the central test of AUTH-002 and the load-bearing kill condition (K2).

**B06 (classic):** `external-requester` (zero grants) asked `ops-agent` to transmit. `ops-agent` holds the transmit capability, but `request_origin = external-requester` and no delegation grant from `external-requester` to `ops-agent` exists. **Denied.** The authorized component's capability was not exercised for the unauthorized requester.

**B07 (tool-mediated):** Same pattern through a tool execution. `external-requester` asked `ops-agent` to execute the reconciler tool. `ops-agent` holds `execute_tool:reconciler:single` with the named-tool constraint, but request-origin binding caught the unauthorized origin. **Denied.**

**B08 (chained):** `external-requester → analytics-agent → ops-agent`. A delegation grant from `analytics-agent` to `ops-agent` exists, but the `request_origin` is `external-requester`, and no delegation from `external-requester` to `ops-agent` exists. The intermediate delegation chain does not launder the unauthorized origin. **Denied.**

### Multi-Agent Workflows (B09, B17)

**B09 (3-step cross-agent chain):** `ops-agent` reads finance data (self-originated), `analytics-agent` generates a report (delegated by `ops-agent`, with matching delegation grant), `ops-agent` transmits to partner API (self-originated). Each step authorized with proper grants and delegation. **Allowed.**

**B17 (3-agent workflow):** `ops-agent` reads config, `analytics-agent` generates a report (delegated by `ops-agent`), `audit-agent` writes an audit log (delegated by `analytics-agent`). Three agents, two delegation hops, each with matching capability grants and delegation grants. **Allowed.**

These demonstrate that the composition defense does not break legitimate multi-agent work when delegation is explicit and each agent holds its own capability.

### Privilege Laundering (B16)

`external-requester` delegates to `analytics-agent`, who delegates to `ops-agent`. The `request_origin` is `external-requester`. The authorization check looks for a delegation from `external-requester` to `ops-agent` — which does not exist. The intermediate delegation chain does not create a transitive delegation path. **Denied.** Delegation is not transitive; each hop requires its own explicit grant.

## Relationship to Prior Experiments

| Experiment | Question | Result |
|------------|----------|--------|
| IB-001 | Can the pipeline distinguish synonyms from drift? | FAIL (K2: authority synonym gap) |
| IB-002 | Does normalization solve aliases without expansion? | FAIL (K3: test-design conflation) |
| IB-003 | Does remediated pipeline fix false blocks + preserve drift detection? | PASS (12/12) |
| AUTH-001 | Can the flat grant be replaced with narrow capabilities? | PASS (18/18) |
| **AUTH-002** | **Do narrow capabilities stay safe when composed across agents?** | **PASS (18/18)** |

The three layers are now connected:
- **Intent integrity** (IB): intent must remain faithful through the pipeline.
- **Authority integrity** (AUTH-001): authority must remain narrow per actor.
- **Composition safety** (AUTH-002): narrow authority must survive delegation, chaining, and confused-deputy pressure.

Each result is bounded to its preregistered test set. Together they form an emerging experimental argument, not a proof of general security.

## Bounded Claim

AUTH-002 passed all 18 preregistered cases. The capability-grant model with request-origin binding, explicit delegation grants, and grant freshness denied every tested composition-level threat — including all three confused-deputy variants, all delegation leaks, the scope-intersection attack, and the privilege-laundering chain — while permitting every tested legitimate multi-agent workflow that operated within its declared delegated capabilities. Zero privilege expansions, zero grant broadening. The result is limited to this preregistered test set and does not establish general composition safety.

## Artifacts

| File | Description |
|------|-------------|
| `PREREGISTRATION.md` | Locked preregistration (SHA-256 verified) |
| `run_auth002.py` | Deterministic runner (no LLM judge) |
| `auth002_results.json` | Full case-by-case results with audit trails |
| `proofrecord_auth002.json` | Self-verifying ProofRecord with hash chain |
| `auth002_ledger.jsonl` | One line per case for programmatic consumption |
| `MANIFEST.sha256` | SHA-256 hashes of all artifacts |

## Scientific Discipline

- Preregistration locked before execution. SHA-256 hash recorded before implementation.
- All verdicts preserved regardless of outcome.
- The synonym map was not modified after seeing results.
- IB-001 remains FAIL. IB-002 remains FAIL. IB-003 remains PASS. AUTH-001 remains PASS.
- Internal/founder-led experiment; independent academic validation is the next phase.
- Honest failures are scientifically valuable. This experiment happened to pass, but the discipline that would have preserved a failure is the same discipline that makes this pass credible.
