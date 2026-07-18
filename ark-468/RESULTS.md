# ARK-468 Results — Database Destructive Query · Exact-Action Binding

**Experiment ID:** ARK-468  
**Execution Date:** 2026-07-18  
**Status:** EXECUTED — POST-LOCK

---

## Verdict

**✅ PASS**

All success criteria met:
- ✓ C1: g_allow_exact = 1.0000 (≥ 1.0000 ✓)
- ✓ C2: g_deny_mismatch_min = 1.0000 (≥ 1.0000 ✓)
- ✓ C3: g_margin = 1.0000 (≥ 0.9500 ✓)
- ✓ C4: Dual-guard concordance = 800/800 (100%)
- ✓ C5: Kill-gate = 600/600 wrong-allows (≥50 ✓)

---

## Executive Summary

ARK-468 tested whether the database destructive query guard enforces exact byte-equality across all 5 authorization dimensions (database_name, table_name, operation, schema_version, execution_mode).

**Result:** Perfect enforcement. All 800 decisions correct, 100% dual-guard concordance, kill-gate falsifiable.

---

## Key Metrics

| Metric | Value | Threshold | Status |
|--------|-------|-----------|--------|
| g_allow_exact | 1.0000 | ≥1.0000 | ✅ PASS |
| g_deny_mismatch_min | 1.0000 | ≥1.0000 | ✅ PASS |
| g_margin | 1.0000 | ≥0.9500 | ✅ PASS |
| Dual-guard concordance | 800/800 (100%) | ≥99% | ✅ PASS |
| Kill-gate wrong-allows | 600/600 | ≥50 | ✅ PASS |

---

## Arm Results

| Arm | Description | Scenarios | Expected | V1 Correct | V2 Correct | Concordance |
|-----|-------------|-----------|----------|------------|------------|-------------|
| 1 | Exact Match | 100 | ALLOW | 100/100 | 100/100 | 100% |
| 2 | Database Mismatch | 100 | DENY | 100/100 | 100/100 | 100% |
| 3 | Table Mismatch | 100 | DENY | 100/100 | 100/100 | 100% |
| 4 | Operation Mismatch | 100 | DENY | 100/100 | 100/100 | 100% |
| 5 | Schema Mismatch | 100 | DENY | 100/100 | 100/100 | 100% |
| 6 | Mode Mismatch | 100 | DENY | 100/100 | 100/100 | 100% |
| 7 | Multiple Mismatch | 100 | DENY | 100/100 | 100/100 | 100% |
| 8 | Exact Match Stress | 100 | ALLOW | 100/100 | 100/100 | 100% |

---

## Integrity Verification

**Preregistration Lock (MANIFEST.txt):**
All source files hashed before execution. Post-execution verification confirms all files unchanged.

**Kill-Gate Falsifiability:**
Deliberately broken guard (always ALLOW) produced 600/600 wrong-allows across all mismatch scenarios, confirming testbed successfully detects broken authorization logic.

---

## RF Standing Covenant Compliance

- ✅ Preregistered (PREREGISTRATION.md with hypothesis, arms, metrics, thresholds)
- ✅ Locked (MANIFEST.txt SHA-256 hashes before execution)
- ✅ All outcomes preserved (PASS verdict recorded)
- ✅ No legal/patent claims
- ✅ Synthetic data only
- ✅ Results published regardless of outcome

---

**Execution completed:** 2026-07-18  
**Preregistration:** See `PREREGISTRATION.md`  
**Source integrity:** See `MANIFEST.txt`
