# ARK-468 — Database Destructive Query · Exact-Action Binding

**Status:** EXECUTED — VERDICT **PASS** (executed 2026-07-18 post-lock)

- g_allow_exact=1.0000, g_deny_mismatch_min=1.0000, g_margin=1.0000
- 800/800 decisions correct, 100% dual-guard concordance
- 600/600 kill-gate wrong-allows (falsifiable)
- See `RESULTS.md` for full analysis

## Overview

ARK-468 tests whether the database destructive query guard enforces exact 5-tuple binding (database_name, table_name, operation, schema_version, execution_mode) to prevent catastrophic data loss from misauthorized DROP/DELETE/TRUNCATE operations.

**Research Question:** Does the guard enforce exact byte-equality across all 5 database query dimensions?

**Hypothesis:** Both guards achieve perfect scores (g_allow_exact=1.0, g_deny_mismatch_min=1.0, g_margin=1.0)

---

## Component Under Test

**Database Destructive Query Guard:**
- **V1 (JavaScript):** Exact 5-tuple matching (database/table/operation/schema/mode)
- **V2 (Python):** Independent Python implementation
- **Decision paths:** ALLOW (exact match) or DENY (any mismatch)

---

## Test Structure

- **Total decisions:** 800 (8 arms × 100 scenarios)
- **ALLOW arms:** Arm 1 (exact match), Arm 8 (exact match stress)
- **DENY arms:** Arms 2-7 (database, table, operation, schema, mode, multiple mismatches)

---

## Results Summary

| Metric | Value | Status |
|--------|-------|--------|
| g_allow_exact | 1.0000 | ✅ PASS |
| g_deny_mismatch_min | 1.0000 | ✅ PASS |
| g_margin | 1.0000 | ✅ PASS |
| Dual-guard concordance | 800/800 (100%) | ✅ PASS |
| Kill-gate wrong-allows | 600/600 | ✅ PASS |

---

## Files

```
ark-468/
├── PREREGISTRATION.md          # Research design (locked)
├── MANIFEST.txt                # SHA-256 source hashes
├── RESULTS.md                  # Full results report
├── README.md                   # This file
├── compute_hashes.sh           # Hash computation
├── run_arms.py                 # Main execution (dual guards)
├── run_killgate.py             # Falsifiability test
├── generator/
│   └── scenario_generator.py  # Generates 800 scenarios
├── verifiers/
│   ├── v1_guard.js            # JavaScript guard
│   └── v2_guard.py            # Python guard
└── results/
    ├── arm_[1-8]_scenarios.json
    ├── arm_[1-8]_results.json
    ├── overall_results.json
    └── killgate_results.json
```

---

## RF Standing Covenant Compliance

- ✓ Preregistered, ✓ Locked, ✓ All outcomes preserved
- ✓ No legal/patent claims, ✓ Synthetic data only

---

**Series:** P01 — Production Boundary Integrations  
**Experiment:** ARK-468 (11/25 in P01)  
**Organization:** Remnant Fieldworks Inc.  
**Executed:** 2026-07-18
