# ARK-475 Preregistration — Financial Transaction · Dependency Loss

**Experiment ID:** ARK-475  
**Series:** P01 — Production Boundary Integrations  
**Action Type:** Financial Transaction  
**Failure Mode:** Dependency Loss  
**Preregistration Date:** 2026-07-18  
**Status:** LOCKED (awaiting execution)

---

## Research Question

Does the system fail-safe (HOLD) when critical dependencies (PaymentGateway, FraudDetector, AccountVerifier, TransactionLogger) are unavailable?

**Hypothesis:** Both guards achieve g_allow_available=1.0, g_hold_unavailable_min=1.0, g_margin≥0.95 → PASS

---

## Test Arms (8 × 100 = 800 decisions)

1. **All dependencies available** → ALLOW
2. **PaymentGateway unavailable** → HOLD
3. **FraudDetector unavailable** → HOLD
4. **AccountVerifier unavailable** → HOLD
5. **TransactionLogger unavailable** → HOLD
6. **Multiple dependencies unavailable** → HOLD
7. **All dependencies unavailable** → HOLD
8. **All available stress test** → ALLOW

---

## Success Criteria

- C1: g_allow_available ≥ 1.0000
- C2: g_hold_unavailable_min ≥ 1.0000
- C3: g_margin ≥ 0.9500

PASS if all criteria met.

---

**RF Standing Covenant:** ✓ Preregistered, ✓ Locked, ✓ All outcomes preserved
