# ARK-453 — Conflicting Evidence Must HOLD
## RESULTS (recorded as executed)

**Experiment ID:** ARK-453  
**Series:** ExecutionProof authorization-boundary corpus (enterprise-failure-mode phase)  
**Substrate:** Classical software (no quantum hardware, no cryptography)  
**Execution window:** 2026-07-17T19:37:12Z to 2026-07-17T19:37:13Z (UTC)  
**VERDICT:** **PASS**

---

## Summary

ARK-453 tested whether an independent authorization resolver correctly distinguishes **consensus** (all evidence sources agree) from **conflict** (sources disagree or are unavailable) and emits the appropriate decision: ALLOW for unanimous permission, DENY for unanimous prohibition, and HOLD for disagreement or ambiguity.

**Question:** When evidence sources disagree about an authorization decision, does an independent resolver choose HOLD rather than optimistically allowing or denying?

**Answer:** **Yes.** Both independently implemented resolvers (V1 JavaScript, V2 Python) correctly identified all consensus scenarios and all conflict/ambiguous scenarios with 100% accuracy and 100% mutual agreement across 800 evaluation decisions.

---

## Design

**Structure:** 8 arms × 100 scenarios per arm = **800 evaluation decisions**

**Evidence model:** Each scenario presents signals from 6 independent sources (identity, policy, risk, approval, registry, temporal). Each source emits one of three signals: `ALLOW_SIGNAL`, `DENY_SIGNAL`, or `UNKNOWN`.

**Decision procedure (both resolvers):**
1. If any source = UNKNOWN → HOLD
2. Collect unique non-UNKNOWN signals
3. If all sources emit ALLOW_SIGNAL → ALLOW
4. If all sources emit DENY_SIGNAL → DENY
5. If sources disagree (mixed ALLOW/DENY) → HOLD

**Arms:**
| Arm | Label | Configuration | Expected |
|-----|-------|---------------|----------|
| 1 | CONSENSUS-all-allow | All 6 sources = ALLOW | ALLOW |
| 2 | CONSENSUS-all-deny | All 6 sources = DENY | DENY |
| 3 | CONFLICT-identity-policy | Identity + policy DENY, rest ALLOW | HOLD |
| 4 | CONFLICT-risk-elevation | Risk DENY, rest ALLOW | HOLD |
| 5 | CONFLICT-registry-revocation | Registry DENY, rest ALLOW | HOLD |
| 6 | CONFLICT-approval-mismatch | Approval DENY, rest ALLOW | HOLD |
| 7 | CONFLICT-temporal-inconsistency | Temporal DENY, rest ALLOW | HOLD |
| 8 | AMBIGUOUS-missing-critical | 2 sources UNKNOWN, rest mixed | HOLD |

---

## Primary Results

### Pass Criteria (preregistered)

Let:
- **g_allow_consensus** = ALLOW rate in Arm 1 (consensus-all-allow)
- **g_hold_conflict_min** = minimum HOLD rate across Arms 3–8 (conflict/ambiguous)
- **g_margin** = min(g_allow_consensus, g_hold_conflict_min) − 0.05

**Criteria:**
- **C1:** g_allow_consensus ≥ 0.95
- **C2:** g_hold_conflict_min ≥ 0.95
- **C3:** g_margin ≥ 0.90

### Measured Values

| Metric | Value | Criterion | Result |
|--------|-------|-----------|--------|
| g_allow_consensus | **1.0000** | ≥ 0.95 | ✓ PASS |
| g_hold_conflict_min | **1.0000** | ≥ 0.95 | ✓ PASS |
| g_margin | **0.9500** | ≥ 0.90 | ✓ PASS |

**All three criteria met.** VERDICT: **PASS**

---

## Per-Arm Results

| Arm | Label | ALLOW | HOLD | DENY | V1–V2 Concordance |
|-----|-------|-------|------|------|-------------------|
| 1 | CONSENSUS-all-allow | **100%** | 0% | 0% | 100% (100/100) |
| 2 | CONSENSUS-all-deny | 0% | 0% | **100%** | 100% (100/100) |
| 3 | CONFLICT-identity-policy | 0% | **100%** | 0% | 100% (100/100) |
| 4 | CONFLICT-risk-elevation | 0% | **100%** | 0% | 100% (100/100) |
| 5 | CONFLICT-registry-revocation | 0% | **100%** | 0% | 100% (100/100) |
| 6 | CONFLICT-approval-mismatch | 0% | **100%** | 0% | 100% (100/100) |
| 7 | CONFLICT-temporal-inconsistency | 0% | **100%** | 0% | 100% (100/100) |
| 8 | AMBIGUOUS-missing-critical | 0% | **100%** | 0% | 100% (100/100) |

**Observations:**
- Arm 1 (consensus-all-allow): ALLOW 100% — correctly permits when all sources agree to allow
- Arm 2 (consensus-all-deny): DENY 100% — correctly denies when all sources agree to deny
- Arms 3–8 (conflict/ambiguous): HOLD 100% — correctly escalates when sources disagree or are unavailable
- Perfect separation: no false ALLOW on conflict, no false DENY on conflict, no false HOLD on consensus

---

## Secondary Observations

### Dual-Resolver Concordance
- **Overall V1–V2 concordance:** 100.00% (800/800 agreements)
- Both independently written resolvers (JavaScript, Python) agreed on every single decision across all 800 scenarios
- Confirms the decision procedure is clear, deterministic, and implementable without ambiguity

### Consensus-DENY Performance
- **g_deny_consensus (Arm 2 DENY rate):** 1.0000
- Not a formal pass criterion, but confirms the resolver correctly handles unanimous denial (fail-closed consensus)

---

## Gates and Safeguards

### Kill-Gate Calibration
- **Status:** PASS
- 100 calibration scenarios generated (50 consensus, 50 conflict/ambiguous)
- Conflict-effectiveness gate: all 100 scenarios verified as genuinely encoding their conflict/consensus class
- V1–V2 concordance: 100% (100/100)
- Gate threshold: ≥ 99% concordance required to proceed → **exceeded**

### Conflict-Effectiveness Gate (per arm)
- **Status:** PASS on all 8 arms
- Every scenario in every arm verified by independent structural oracle to genuinely encode its conflict/consensus class
- Prevents ARK-455-style no-op defects where a test case appears to encode a condition but is mathematically inert
- **800/800 scenarios validated** as effective before evaluation

---

## Interpretation

### What This Result Means

ARK-453 demonstrates that an authorization resolver can reliably distinguish:
1. **Consensus → decisive action:** When all evidence sources agree (ALLOW or DENY), act decisively
2. **Conflict → escalation:** When sources disagree or critical data is missing (UNKNOWN), escalate to HOLD rather than guess

The three-state decision model (ALLOW / HOLD / DENY) is not just theoretically necessary — it is **practically implementable** and **commercially meaningful**:
- **HOLD prevents optimistic overreach** (allowing when evidence conflicts)
- **HOLD prevents pessimistic obstruction** (denying when legitimate but uncertain)
- **HOLD acknowledges uncertainty** and routes to appropriate human or elevated review

This validates the ExecutionProof governance model's use of HOLD as a first-class decision outcome, not merely a fallback or error state.

### Real-World Relevance

In enterprise settings, conflicting evidence signals are routine:
- Identity provider reports "valid" while policy engine reports "expired"
- Risk assessment flags "elevated" while approval workflow says "proceed"
- Authoritative registry shows "revoked" while local cache shows "active"
- Critical evidence source is unavailable (network partition, service degradation)

ARK-453 shows that a properly designed resolver will **escalate appropriately** rather than making a binary ALLOW/DENY choice under uncertainty.

---

## Limitations and Scope

**What this experiment tested:**
- Whether a resolver correctly classifies scenarios into consensus vs. conflict in a controlled evidence model
- Whether HOLD is emitted appropriately when conflict or ambiguity is present
- Whether the decision procedure is clear enough for independent implementation

**What this does NOT test:**
- Real-world evidence source reliability or adversarial manipulation of evidence
- Distributed system behavior, network failures, or timing attacks
- Cryptographic integrity of evidence records
- Human escalation procedures after HOLD is emitted
- Performance or scalability under production load
- Multi-layered policy hierarchies or dynamic evidence weighting

**Constraints:** This is a classical/software boundary-logic testbed validating the decision procedure in isolation, not the end-to-end enterprise authorization stack.

---

## Provenance and Integrity

### LOCK Procedure
1. **Preregistration, dual resolvers, generator, MANIFEST (SHA-256 hashes) committed BEFORE execution** at commit `697754f2467984ae29a1b0ccb068d8ac528db5ea` (2026-07-17T19:37:01Z UTC)
2. No scenario was generated or evaluated until after LOCK commit
3. Results recorded AFTER execution complete

### MANIFEST SHA-256 Hashes (locked files)
```
PREREGISTRATION.md:                        528e2dc4057b1ca2788e1a9da3c1c88c3f40ed8c47093f362f4f8a5a289a823d
schemas/evidence_scenario_schema.json:     ef5315bf67fdf2844cac5b6a3a920853b64989324e18a5ee47fcd344f7de8aee
verifiers/v1_resolver.js:                  ea28afa89853cb024035ccaadb40470b9f054f65fef06500677ecbff2c7838ed
verifiers/v2_resolver.py:                  266585c27d0f3f2ae14e5a8b0cc339fa8045bb39d0c782703302d333302131f2
generator/scenario_generator.py:           ab82095e89b549585ac9b1923ff70b07c232ffbdab87ce1941655127e7efdc44
run_killgate.py:                           2ccd805021b714105041396e3623bc1e73e7580a6260ba1caa88fb213001ff9a
run_arms.py:                               bc3d893f3fcf69acff4ef688465248e90a12bd8434d920ae14150adc8419394e
```

**Commits are not cryptographically signed.** Provenance = commit history + MANIFEST SHA-256 hashes. This is an experimental testbed, not a production security claim.

---

## Conclusion

ARK-453 answers the question **"Conflicting evidence must HOLD"** with a clear **YES**:
- Consensus scenarios (all agree) → decisive ALLOW or DENY (100%)
- Conflict scenarios (sources disagree) → appropriate HOLD (100%)
- Ambiguous scenarios (missing data) → appropriate HOLD (100%)
- Dual independent implementations agree (100%)

The three-state authorization model (ALLOW / HOLD / DENY) is validated as both implementable and necessary for responsible governance under uncertainty.

**Verdict stands as executed:** PASS.

---

**Investigator:** Derek Hone, Remnant Fieldworks Inc.  
**Executor:** Abacus.AI autonomous agent (supervised)  
**Series:** ExecutionProof™ authorization-boundary corpus  
**Trademarks:** ExecutionProof™, ProofRecord™, VaultProof™, Verification Before Execution™, Proof Before Power™

---

*If it cannot be verified, it cannot execute.*
