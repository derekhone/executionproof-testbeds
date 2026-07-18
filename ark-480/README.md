# ARK-480 — API Rate Limit · Dependency Loss

**Status:** EXECUTED — VERDICT **PASS** (executed 2026-07-18 post-lock)

- g_allow_available=1.0000, g_hold_unavailable_min=1.0000, g_margin=0.9500
- 800/800 decisions correct, 100% dual-guard concordance
- 150/150 kill-gate wrong-allows (falsifiable)
- See `RESULTS.md` for full analysis

---

## Overview

ARK-480 tests API rate limit authorization with dependency loss failure mode.

---

**Series:** P01 — Production Boundary Integrations  
**Experiment:** ARK-480  
**Organization:** Remnant Fieldworks Inc.  
**Executed:** 2026-07-18
