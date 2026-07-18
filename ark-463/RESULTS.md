# ARK-463 Results — Production Deployment · Exact-Action Binding

**Experiment ID:** ARK-463  
**Execution Date:** 2026-07-18  
**Status:** EXECUTED — POST-LOCK

---

## Verdict

**✅ PASS**

All success criteria met:
- ✓ C1: g_allow_exact = 1.0000 (≥ 0.95)
- ✓ C2: g_deny_mismatch_min = 1.0000 (≥ 0.95)
- ✓ C3: g_margin = 1.0000 (≥ 0.90)
- ✓ C4: Concordance = 800/800 = 100.00% (≥ 95%)
- ✓ C5: Kill-gate = 600 wrong-allows (≥ 50)

---

## Executive Summary

ARK-463 tested whether ExecutionProof-based deployment guards correctly enforce exact-action binding across all 5 deployment tuple dimensions (service_name, environment, version, region, deployment_method).

**Key Findings:**
- **Perfect exact-match enforcement:** All 200 exact-match scenarios (Arms 1, 8) correctly allowed
- **Perfect mismatch rejection:** All 600 mismatch scenarios (Arms 2-7) correctly denied
- **100% dual-guard concordance:** V1 (JavaScript) and V2 (Python) agreed on all 800 decisions
- **Testbed falsifiable:** Broken guard produced 600 wrong-allows, demonstrating detection capability

---

## Detailed Metrics

### Overall Performance

| Metric | Value | Threshold | Status |
|--------|-------|-----------|--------|
| Total scenarios | 800 | - | - |
| Dual-guard concordance | 800/800 (100.00%) | ≥95% | ✅ PASS |
| g_allow_exact | 1.0000 | ≥0.95 | ✅ PASS |
| g_deny_mismatch_min | 1.0000 | ≥0.95 | ✅ PASS |
| g_margin | 1.0000 | ≥0.90 | ✅ PASS |

### Per-Arm Performance

| Arm | Description | Scenarios | V1 Correct | V2 Correct | Concordant |
|-----|-------------|-----------|------------|------------|------------|
| 1 | Exact Match → ALLOW | 100 | 100/100 | 100/100 | 100/100 |
| 2 | Service Name Mismatch → DENY | 100 | 100/100 | 100/100 | 100/100 |
| 3 | Environment Mismatch → DENY | 100 | 100/100 | 100/100 | 100/100 |
| 4 | Version Mismatch → DENY | 100 | 100/100 | 100/100 | 100/100 |
| 5 | Region Mismatch → DENY | 100 | 100/100 | 100/100 | 100/100 |
| 6 | Method Mismatch → DENY | 100 | 100/100 | 100/100 | 100/100 |
| 7 | Multiple Mismatch → DENY | 100 | 100/100 | 100/100 | 100/100 |
| 8 | Exact Match Stress → ALLOW | 100 | 100/100 | 100/100 | 100/100 |

### Kill-Gate Results

| Metric | Value |
|--------|-------|
| DENY scenarios tested | 600 (Arms 2-7) |
| Wrong-allows detected | 600/600 |
| Falsifiable | ✅ YES (≥50 required) |

---

## Guard Implementations

### V1 Guard (JavaScript)
- Exact byte-equality comparison (`===`) on all 5 dimensions
- Decision path: single conditional checking all fields
- Performance: Average ~0.1ms per decision
- Correctness: 800/800 (100.00%)

### V2 Guard (Python)
- Independent implementation using string equality (`==`)
- Decision path: individual field comparisons with detailed reason building
- Performance: Average ~0.2ms per decision
- Correctness: 800/800 (100.00%)

**Implementation divergence:** None observed - both guards produced identical decisions on all 800 scenarios.

---

## Example Scenarios

### Exact Match (ALLOW)
```json
{
  "authorized": {
    "service_name": "user-api",
    "environment": "production",
    "version": "v2.3.1",
    "region": "us-east-1",
    "deployment_method": "rolling-update"
  },
  "presented": {
    "service_name": "user-api",
    "environment": "production",
    "version": "v2.3.1",
    "region": "us-east-1",
    "deployment_method": "rolling-update"
  },
  "decision": "ALLOW"
}
```

### Version Mismatch (DENY)
```json
{
  "authorized": {
    "service_name": "user-api",
    "environment": "production",
    "version": "v2.3.1",
    "region": "us-east-1",
    "deployment_method": "rolling-update"
  },
  "presented": {
    "service_name": "user-api",
    "environment": "production",
    "version": "v2.3.2",
    "region": "us-east-1",
    "deployment_method": "rolling-update"
  },
  "decision": "DENY",
  "reason": "Deployment tuple mismatch: version: 'v2.3.1' vs 'v2.3.2'"
}
```

---

## Integrity Verification

**Preregistration Lock (MANIFEST.txt):**
All source files were hashed before execution. Post-execution verification confirms:
- ✅ PREREGISTRATION.md — unchanged
- ✅ generator/scenario_generator.py — unchanged
- ✅ verifiers/v1_guard.js — unchanged
- ✅ verifiers/v2_guard.py — unchanged
- ✅ run_arms.py — unchanged
- ✅ run_killgate.py — unchanged

**Result files generated:**
- `results/arm_[1-8]_scenarios.json` — 800 test scenarios
- `results/arm_[1-8]_results.json` — Per-arm execution results
- `results/overall_results.json` — Aggregate metrics
- `results/killgate_results.json` — Falsifiability test results

---

## Conclusions

1. **Exact-action binding works as designed:** Both guard implementations correctly enforce byte-exact matching across all 5 deployment dimensions, with zero tolerance for normalization, prefix matching, or fuzzy logic.

2. **Dual implementation concordance:** 100% agreement between JavaScript and Python guards demonstrates that exact string equality is deterministic and implementation-independent.

3. **Comprehensive mismatch detection:** All 6 mismatch arms (single-dimension and multi-dimension) achieved perfect denial rates, showing the guards catch substitution attempts regardless of which field(s) differ.

4. **Edge case robustness:** Arm 8 (stress test with long names, SHAs, special chars) achieved perfect ALLOW rate, confirming exact matching works with real-world deployment identifiers.

5. **Testbed validity confirmed:** Kill-gate produced 600 wrong-allows, proving the testbed can detect broken guards that skip exact-match enforcement.

---

## Limitations

This experiment demonstrates **necessary but not sufficient** conditions for production deployment security:

- Does NOT test: credential validation, network security, RBAC integration, audit logging
- Does NOT validate: deployment health checks, rollback logic, service mesh integration
- Does NOT guarantee: production-readiness of the guard implementations
- Synthetic data only: no real cloud provider APIs were tested

**Next steps for production use:**
- Integration with real cloud APIs (AWS, GCP, Azure)
- Audit trail and non-repudiation
- Rate limiting and DoS protection
- End-to-end deployment pipeline testing (ARK-463–467 series)

---

**Execution completed:** 2026-07-18  
**Preregistration:** See `PREREGISTRATION.md`  
**Source integrity:** See `MANIFEST.txt`
