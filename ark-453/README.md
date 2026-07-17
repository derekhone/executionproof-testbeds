# ARK-453 — Conflicting Evidence Must HOLD

**Status:** LOCKED → awaiting execution  
**Substrate:** Classical software (no quantum hardware, no cryptography)  
**Resolvers:** Dual independent — V1 (JavaScript), V2 (Python)  
**Series:** ExecutionProof authorization-boundary corpus (enterprise-failure-mode phase)

---

## Question

When evidence sources disagree about an authorization decision, does an independent resolver choose HOLD (request human/elevated review) rather than optimistically allowing or denying?

---

## Design

**Structure:** 8 arms × 100 scenarios per arm = **800 evaluation decisions**.

**Evidence model:** Each scenario presents signals from 6 independent sources (identity, policy, risk, approval, registry, temporal). Each source emits `ALLOW_SIGNAL`, `DENY_SIGNAL`, or `UNKNOWN`.

**Decision procedure (both resolvers):**
1. If any source = UNKNOWN → HOLD
2. Collect unique non-UNKNOWN signals
3. If all sources emit ALLOW_SIGNAL → ALLOW
4. If all sources emit DENY_SIGNAL → DENY
5. If sources disagree (mixed ALLOW/DENY) → HOLD

**Arms:**
| Arm | Label | Expected |
|-----|-------|----------|
| 1 | CONSENSUS-all-allow | ALLOW |
| 2 | CONSENSUS-all-deny | DENY |
| 3 | CONFLICT-identity-policy | HOLD |
| 4 | CONFLICT-risk-elevation | HOLD |
| 5 | CONFLICT-registry-revocation | HOLD |
| 6 | CONFLICT-approval-mismatch | HOLD |
| 7 | CONFLICT-temporal-inconsistency | HOLD |
| 8 | AMBIGUOUS-missing-critical | HOLD |

**Conflict-effectiveness gate:** Independent structural oracle confirms each conflict arm genuinely encodes a conflict and consensus arms genuinely encode consensus. Prevents ARK-455-style no-op defects. Aborts run if any scenario fails effectiveness check.

**Kill-gate:** 100 calibration scenarios (50 consensus, 50 conflict/ambiguous). V1–V2 concordance must be ≥ 99% to proceed to arm execution.

---

## Pass Criteria (preregistered)

Let:
- **g_allow_consensus** = ALLOW rate in Arm 1
- **g_hold_conflict_min** = minimum HOLD rate across Arms 3–8
- **g_margin** = min(g_allow_consensus, g_hold_conflict_min) − 0.05

**Primary criteria:**
- **C1:** g_allow_consensus ≥ 0.95
- **C2:** g_hold_conflict_min ≥ 0.95
- **C3:** g_margin ≥ 0.90

**Verdict:** PASS if C1 ∧ C2 ∧ C3, else FAIL. Recorded verdict stands as executed.

---

## Execution

```bash
# Kill-gate (abort if concordance < 99%)
python3 run_killgate.py

# Arm execution (abort if any scenario fails conflict-effectiveness gate)
python3 run_arms.py
```

Results written to `results/*.json` and `RESULTS.md`.

---

## Provenance

**LOCK procedure:**
1. Preregistration, dual resolvers, generator, run scripts, and MANIFEST (SHA-256 hashes) committed BEFORE any scenario is generated or evaluated.
2. Results committed AFTER execution.
3. Verdict stands as executed; no post-hoc criterion changes.

**Commits are not cryptographically signed.** Provenance = commit history + MANIFEST SHA-256 hashes.

---

## Trademarks

ExecutionProof™, ProofRecord™, VaultProof™, Verification Before Execution™, Proof Before Power™ — Remnant Fieldworks Inc.

---

*If it cannot be verified, it cannot execute.*
