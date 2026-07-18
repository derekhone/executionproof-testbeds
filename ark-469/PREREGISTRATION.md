# ARK-469 Preregistration — Database Destructive Query · Revocation At Execution

**Experiment ID:** ARK-469  
**Series:** P01 — Production Boundary Integrations  
**Action Type:** Database Destructive Query  
**Failure Mode:** Revocation At Execution  
**Preregistration Date:** 2026-07-18  
**Status:** LOCKED (awaiting execution)

---

## Research Question

Does the database query guard handle revocation timing correctly, producing ALLOW/DENY/HOLD decisions based on authorization revocation status at execution time?

**Hypothesis:** Both guards achieve g_allow_valid=1.0, g_deny_revoked=1.0, g_hold_inflight=1.0, g_margin≥0.95 → PASS

---

## Test Arms (8 × 100 = 800 decisions)

1. **Valid (not revoked)** → ALLOW
2. **Revoked before execution** → DENY
3. **Revoked after execution** → ALLOW
4. **Revocation in-flight (race)** → HOLD (fail-safe)
5. **Never granted** → DENY
6. **Granted then revoked then re-granted** → ALLOW
7. **Multiple revocations** → DENY
8. **Valid stress test** → ALLOW

---

## Success Criteria

- C1: g_allow_valid ≥ 1.0000
- C2: g_deny_revoked ≥ 1.0000  
- C3: g_hold_inflight ≥ 1.0000
- C4: g_margin ≥ 0.9500

PASS if all criteria met.

---

**RF Standing Covenant:** ✓ Preregistered, ✓ Locked, ✓ All outcomes preserved
