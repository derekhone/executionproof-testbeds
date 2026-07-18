# ARK-478 — API Rate Limit · Exact-Action Binding

**Status:** EXECUTED — VERDICT **PASS** (executed 2026-07-18 post-lock)

- g_allow_exact=1.0000, g_deny_mismatch_min=1.0000, g_margin=1.0000
- 800/800 decisions correct, 100% dual-guard concordance
- 600/600 kill-gate wrong-allows (falsifiable)
- See `RESULTS.md` for full analysis

---

## Overview

ARK-478 tests API rate limit authorization with exact-action binding failure mode.

---

**Series:** P01 — Production Boundary Integrations  
**Experiment:** ARK-478  
**Organization:** Remnant Fieldworks Inc.  
**Executed:** 2026-07-18
