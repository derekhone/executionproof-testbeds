# ARK-451 — Authority Revocation During Execution

**Status:** EXECUTED → **VERDICT: PASS** (all 4 criteria met; 800/800 dual-monitor concordance)
**Substrate:** Classical software (no quantum hardware, no cryptography)
**Monitors:** Dual independent — V1 (JavaScript), V2 (Python)
**Series:** ExecutionProof authorization-boundary corpus (enterprise-failure-mode phase)

---

## Question

When authority is valid at verification/bind time but **revoked during the execution window**, does an independent execution monitor fail closed (DENY) or fail safe (HOLD) — never silently proceeding as if authority were still valid?

---

## Design

**Structure:** 8 arms × 100 scenarios per arm = **800 evaluation decisions**.

Each scenario is one authorization lifecycle on a monotonic time axis: `t_decision ≤ t_bind ≤ t_execution`, with an optional `revocation` (`t_revoke`, `propagation_delay`) and optional `reauthorization` (`t_reauth`, `valid`). A revocation is fully effective at `eff = t_revoke + propagation_delay`.

**Decision procedure (both monitors, evaluated at `t_execution`):**
1. No revocation → ALLOW
2. `eff = t_revoke + propagation_delay`
3. Valid reauth with `t_revoke < t_reauth ≤ t_execution` → ALLOW
4. `eff ≤ t_execution` → DENY (revoked before contact; fail closed)
5. `t_revoke ≤ t_execution < eff` → HOLD (in-flight; fail safe)
6. `t_revoke > t_execution` → ALLOW (revoked only after contact)

**Arms:**
| Arm | Label | Expected |
|-----|-------|----------|
| 1 | VALID-throughout | ALLOW |
| 2 | REVOKED-before-bind | DENY |
| 3 | REVOKED-after-decision-before-contact | DENY |
| 4 | REVOKED-during-multistep | DENY |
| 5 | IN-FLIGHT-at-contact | HOLD |
| 6 | REVOKED-then-REAUTHORIZED | ALLOW |
| 7 | IN-FLIGHT-boundary | HOLD |
| 8 | REVOKED-after-execution | ALLOW |

**Revocation-timing gate:** Independent structural oracle confirms each arm genuinely encodes its timing relationship (revoked arms effective before contact; in-flight arms genuinely in-flight; reauth arm has a valid reauth before contact; after-execution arm genuinely after contact). Prevents ARK-455-style no-op defects. Aborts the run if any scenario fails.

**Kill-gate:** 100 calibration scenarios cycling all arms. V1–V2 concordance must be ≥ 99% to proceed.

---

## Pass Criteria (preregistered)

- **g_allow_valid_min** = min ALLOW rate across arms {1, 6, 8}
- **g_deny_revoked_min** = min DENY rate across arms {2, 3, 4}
- **g_hold_inflight_min** = min HOLD rate across arms {5, 7}
- **g_margin** = min(above three) − 0.05

- **C1:** g_allow_valid_min ≥ 0.95
- **C2:** g_deny_revoked_min ≥ 0.95
- **C3:** g_hold_inflight_min ≥ 0.95
- **C4:** g_margin ≥ 0.90

**Verdict:** PASS if C1 ∧ C2 ∧ C3 ∧ C4, else FAIL. Recorded verdict stands as executed.

---

## Execution

```bash
# Kill-gate (abort if concordance < 99%)
python3 run_killgate.py

# Arm execution (abort if any scenario fails the revocation-timing gate)
python3 run_arms.py
```

Results written to `results/*.json` and `RESULTS.md`.

---

## Provenance

**LOCK procedure:**
1. Preregistration, schema, dual monitors, generator, run scripts, and MANIFEST (SHA-256 hashes) committed BEFORE any scenario is generated or evaluated.
2. Results committed AFTER execution.
3. Verdict stands as executed; no post-hoc criterion changes.

**Commits are not cryptographically signed.** Provenance = commit history + MANIFEST SHA-256 hashes.

---

## Trademarks

ExecutionProof™, ProofRecord™, VaultProof™, Verification Before Execution™, Proof Before Power™ — Remnant Fieldworks Inc.

---

*If it cannot be verified, it cannot execute.*
