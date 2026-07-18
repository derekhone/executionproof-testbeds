# ARK-478 Preregistration — API Rate Limit · Exact-Action Binding

**Experiment ID:** ARK-478  
**Series:** P01 — Production Boundary Integrations  
**Action Type:** API Rate Limit  
**Failure Mode:** Exact-Action Binding  
**Preregistration Date:** 2026-07-18  
**Status:** LOCKED (awaiting execution)

---

## Research Question

Does the API rate limit guard enforce exact 5-tuple binding (api_key, endpoint, method, tier, time_window) to prevent unauthorized API usage?

**Hypothesis:** Both guards achieve g_allow_exact=1.0, g_deny_mismatch_min=1.0, g_margin≥0.95 → PASS

---

## Test Arms (8 × 100 = 800 decisions)

1. **Exact Match** → ALLOW
2. **API Key Mismatch** → DENY
3. **Endpoint Mismatch** → DENY
4. **Method Mismatch** → DENY
5. **Tier Mismatch** → DENY
6. **Time Window Mismatch** → DENY
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
