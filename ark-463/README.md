# ARK-463 — Production Deployment · Exact-Action Binding

**Status:** EXECUTED — VERDICT **PASS** (executed 2026-07-18 post-lock)

- g_allow_exact = 1.0000 (C1 ≥ 0.95 ✓) · g_deny_mismatch_min = 1.0000 (C2 ≥ 0.95 ✓) · g_margin = 1.0000 (C3 ≥ 0.90 ✓)
- Dual-guard concordance 800/800 = 100.00%; kill-gate 600/600 wrong-allows (falsifiable)
- See `RESULTS.md` for full readout

## Overview

ARK-463 tests whether ExecutionProof-based production deployment guards correctly enforce exact-action binding across all 5 deployment tuple dimensions.

**Research Question:** Does a deployment guard correctly enforce exact byte-equality on service_name, environment, version, region, and deployment_method, preventing authorization substitution?

**Hypothesis:** Both guards will ALLOW exact matches and DENY any mismatch (even single-character differences), with 100% dual-guard concordance.

---

## Deployment Tuple (5 dimensions)

```python
{
  "service_name": str,        # e.g. "user-api"
  "environment": str,         # e.g. "production"
  "version": str,            # e.g. "v2.3.1" or "sha256:..."
  "region": str,             # e.g. "us-east-1"
  "deployment_method": str   # e.g. "rolling-update"
}
```

---

## Test Structure

- **8 arms** × **100 scenarios/arm** = **800 decisions**
- **Dual guards:** V1 (JavaScript) + V2 (Python)
- **Kill-gate:** Broken guard (always ALLOW)

### Arms

1. **Exact Match (ALLOW)** — All 5 dimensions identical
2. **Service Name Mismatch (DENY)** — service_name differs
3. **Environment Mismatch (DENY)** — environment differs
4. **Version Mismatch (DENY)** — version differs
5. **Region Mismatch (DENY)** — region differs
6. **Method Mismatch (DENY)** — deployment_method differs
7. **Multiple Mismatch (DENY)** — 2+ dimensions differ
8. **Exact Match Stress (ALLOW)** — Exact match with edge cases

---

## Results Summary

### Metrics

| Metric | Value | Threshold | Status |
|--------|-------|-----------|--------|
| g_allow_exact | 1.0000 | ≥0.95 | ✅ PASS |
| g_deny_mismatch_min | 1.0000 | ≥0.95 | ✅ PASS |
| g_margin | 1.0000 | ≥0.90 | ✅ PASS |
| Concordance | 800/800 (100%) | ≥95% | ✅ PASS |
| Kill-gate wrong-allows | 600 | ≥50 | ✅ PASS |

### Per-Arm Accuracy

All arms achieved 100% accuracy (100/100) for both V1 and V2 guards.

---

## Key Findings

1. **Perfect exact-match enforcement**: All 200 exact-match scenarios correctly allowed
2. **Perfect mismatch rejection**: All 600 mismatch scenarios correctly denied
3. **Zero normalization**: Guards correctly rejected case variants, abbreviations, typos
4. **Edge case robustness**: Long names, SHAs, special characters handled correctly
5. **Implementation independence**: JavaScript and Python guards agreed on all 800 decisions

---

## Integrity

**Preregistration:** `PREREGISTRATION.md` locked before execution  
**Source Lock:** `MANIFEST.txt` (SHA-256 hashes verified post-execution)  
**Results:** `RESULTS.md` (detailed metrics and analysis)

---

## Files

```
ark-463/
├── PREREGISTRATION.md          # Research design (locked pre-execution)
├── MANIFEST.txt                # SHA-256 hashes of source files
├── RESULTS.md                  # Full results report
├── README.md                   # This file
├── package.json                # Node.js package metadata
├── compute_hashes.sh           # Hash computation script
├── run_arms.py                 # Main execution script (dual guards)
├── run_killgate.py             # Falsifiability test
├── generator/
│   ├── __init__.py
│   └── scenario_generator.py  # Generates 800 test scenarios
├── verifiers/
│   ├── v1_guard.js            # Guard implementation (JavaScript)
│   └── v2_guard.py            # Guard implementation (Python)
└── results/
    ├── arm_[1-8]_scenarios.json   # Generated test data
    ├── arm_[1-8]_results.json     # Per-arm execution results
    ├── overall_results.json       # Aggregate metrics
    └── killgate_results.json      # Falsifiability results
```

---

## Compliance

**RF Standing Covenant:**
- ✓ Preregistered before execution
- ✓ Cryptographic lock (MANIFEST.txt)
- ✓ All outcomes preserved (PASS)
- ✓ No legal/patent claims
- ✓ Synthetic data only
- ✓ Results published regardless of outcome

**Limitations:**
- Testbed experiment only (NOT production-ready)
- Synthetic data (no real cloud APIs)
- Does NOT test: credentials, networking, audit, health checks

---

**Series:** P01 — Production Boundary Integrations  
**Experiment:** ARK-463 (1/25 in P01)  
**Organization:** Remnant Fieldworks Inc.  
**Executed:** 2026-07-18
