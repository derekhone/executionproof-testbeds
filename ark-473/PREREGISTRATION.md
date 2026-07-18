# ARK-473 Preregistration — Financial Transaction · Exact-Action Binding

**Experiment ID:** ARK-473  
**Series:** P01 — Production Boundary Integrations  
**Action Type:** Financial Transaction  
**Failure Mode:** Exact-Action Binding  
**Preregistration Date:** 2026-07-18  
**Status:** LOCKED (awaiting execution)

---

## Research Question

Does the financial transaction guard enforce exact 5-tuple binding (account_from, account_to, amount, currency, transaction_type) to prevent unauthorized fund transfers?

**Hypothesis:** Both guards achieve g_allow_exact=1.0, g_deny_mismatch_min=1.0, g_margin≥0.95 → PASS

---

## Test Arms (8 × 100 = 800 decisions)

1. **Exact Match** → ALLOW
2. **Account From Mismatch** → DENY
3. **Account To Mismatch** → DENY
4. **Amount Mismatch** → DENY
5. **Currency Mismatch** → DENY
6. **Transaction Type Mismatch** → DENY
7. **Multiple Dimension Mismatch** → DENY
8. **Exact Match Stress** → ALLOW

---

## Success Criteria

- C1: g_allow_exact ≥ 1.0000
- C2: g_deny_mismatch_min ≥ 1.0000
- C3: g_margin ≥ 0.9500

PASS if all criteria met.

---

**RF Standing Covenant:** ✓ Preregistered, ✓ Locked, ✓ All outcomes preserved
