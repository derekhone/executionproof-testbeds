# ARK-471 Preregistration — Database Destructive Query · Cross-Context Replay

**Experiment ID:** ARK-471  
**Series:** P01 — Production Boundary Integrations  
**Action Type:** Database Destructive Query  
**Failure Mode:** Cross-Context Replay  
**Preregistration Date:** 2026-07-18  
**Status:** LOCKED (awaiting execution)

---

## Research Question

Can a database query authorized for one context be replayed in another? Tests 5-dimension context binding: tenant, session, resource, audience, environment.

**Hypothesis:** Both guards achieve g_allow_exact=1.0, g_deny_replay_min=1.0, g_margin≥0.95 → PASS

---

## Test Arms (8 × 100 = 800 decisions)

1. **Exact context match (all 5 dims)** → ALLOW
2. **Tenant mismatch** → DENY
3. **Session mismatch** → DENY
4. **Resource mismatch** → DENY
5. **Audience mismatch** → DENY
6. **Environment mismatch** → DENY
7. **Multiple dimension mismatch** → DENY
8. **Exact match stress test** → ALLOW

---

## Success Criteria

- C1: g_allow_exact ≥ 1.0000
- C2: g_deny_replay_min ≥ 1.0000
- C3: g_margin ≥ 0.9500

PASS if all criteria met.

---

**RF Standing Covenant:** ✓ Preregistered, ✓ Locked, ✓ All outcomes preserved
