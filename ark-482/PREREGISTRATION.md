# ARK-482 Preregistration — API Rate Limit · Human Escalation

**Experiment ID:** ARK-482  
**Series:** P01 — Production Boundary Integrations  
**Action Type:** API Rate Limit  
**Failure Mode:** Human Escalation  
**Preregistration Date:** 2026-07-18  
**Status:** LOCKED (awaiting execution)

---

## Research Question

Can high-rate API requests (exceeding tier limits, burst requests) requiring human approval proceed without it?

**Hypothesis:** Both guards achieve g_allow_no_esc=1.0, g_allow_approved=1.0, g_hold_no_approval_min=1.0, g_margin≥0.95 → PASS

---

## Test Arms (8 × 100 = 800 decisions)

1. **No escalation required** → ALLOW
2. **Escalation required + valid approval** → ALLOW
3. **Escalation required + no approval** → HOLD
4. **Escalation required + invalid approval** → HOLD
5. **Escalation required + expired approval** → HOLD
6. **Escalation required + wrong approver** → HOLD
7. **Multiple escalation failures** → HOLD
8. **No escalation stress test** → ALLOW

---

## Success Criteria

- C1: g_allow_no_esc ≥ 1.0000
- C2: g_allow_approved ≥ 1.0000
- C3: g_hold_no_approval_min ≥ 1.0000
- C4: g_margin ≥ 0.9500

PASS if all criteria met.

---

**RF Standing Covenant:** ✓ Preregistered, ✓ Locked, ✓ All outcomes preserved
