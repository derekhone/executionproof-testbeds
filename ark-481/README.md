# ARK-481 — API Rate Limit · Cross-Context Replay

**Status:** EXECUTED — VERDICT **PASS** (executed 2026-07-18 post-lock)

- g_allow_exact=1.0000, g_deny_replay_min=1.0000, g_margin=0.9500
- 800/800 decisions correct, 100% dual-guard concordance
- 150/150 kill-gate wrong-allows (falsifiable)
- See `RESULTS.md` for full analysis

---

## Overview

ARK-481 tests API rate limit authorization with cross-context replay failure mode.

---

**Series:** P01 — Production Boundary Integrations  
**Experiment:** ARK-481  
**Organization:** Remnant Fieldworks Inc.  
**Executed:** 2026-07-18
