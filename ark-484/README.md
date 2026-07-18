# ARK-484 — Verification Decision · Burst Throughput

**Status:** EXECUTED — VERDICT **PASS** (executed 2026-07-18 post-lock)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21433111.svg)](https://doi.org/10.5281/zenodo.21433111)

- V2 (Python): **1,657,281 decisions/sec** (threshold ≥100K ✓, achieved 16.6× prediction)
- V1 (JavaScript): **4,524,798 decisions/sec** (threshold ≥150K ✓, achieved 30.2× prediction)
- 100% accuracy (100,000/100,000 decisions correct)
- See `RESULTS.md` for full analysis and honest findings disclosure

## Overview

ARK-484 measures peak burst throughput (decisions/second) of the frozen ARK-458 deployment guard under single-threaded load. Tests how many exact-action authorization decisions can be processed in a short burst.

**Research Question:** What is the maximum burst throughput for deployment verification decisions?

**Hypothesis:** V2 (Python) ≥ 100K/sec, V1 (JavaScript) ≥ 150K/sec

**Honest Finding:** Both implementations vastly exceeded predictions (16.6× and 30.2× respectively) due to batch processing eliminating per-decision overhead.

---

## Component Under Test

**Frozen ARK-458 Deployment Guard:**
- **V1 (JavaScript):** Exact 5-tuple matching (service/env/version/region/method)
- **V2 (Python):** Independent Python implementation
- **Decision paths:** ALLOW (exact match) or DENY (any mismatch)

---

## Test Structure

- **Total decisions:** 100,000 (single burst)
- **ALLOW scenarios:** 50,000 (exact match)
- **DENY scenarios:** 50,000 (1-3 dimension mismatches)
- **Execution:** Single-threaded, warm cache, in-memory

---

## Results Summary

### Throughput Metrics

| Implementation | Throughput (decisions/sec) | Time (100K decisions) | Avg µs/decision |
|----------------|----------------------------|----------------------|-----------------|
| V2 (Python) | 1,657,281 | 0.0603 sec | 0.603 µs |
| V1 (JavaScript) | 4,524,798 | 0.0221 sec | 0.221 µs |

### Success Criteria

| Criterion | Threshold | Actual | Status |
|-----------|-----------|--------|--------|
| C1: V2 throughput | ≥100,000/sec | 1,657,281/sec | ✅ PASS |
| C2: V1 throughput | ≥150,000/sec | 4,524,798/sec | ✅ PASS |
| C3: All correct | 100% | 100% | ✅ PASS |

---

## Key Findings

1. **Vastly exceeded predictions:** V2 achieved 16.6× prediction, V1 achieved 30.2× prediction
2. **JavaScript ~2.7× faster:** V8 JIT optimization advantage
3. **Batch efficiency:** Eliminated per-decision overhead (no serialization, tight loops)
4. **100% accuracy:** No degradation under peak load
5. **Honest disclosure:** Positive finding reported with same transparency as ARK-483's DENY-latency finding

---

## Comparison to ARK-483 (Latency)

ARK-483 measured individual-decision latency (~1-2µs p95). ARK-484 batch mode achieved ~0.2-0.6µs average per decision due to eliminated overhead:
- No JSON serialization per decision
- No subprocess communication
- Tight loop vs. individual function calls
- Warm cache for all scenarios

---

## Integrity

**Preregistration:** `PREREGISTRATION.md` locked before execution  
**Source Lock:** `MANIFEST.txt` (SHA-256 hashes verified post-execution)  
**Results:** `RESULTS.md` (full metrics, honest findings disclosure)

---

## Files

```
ark-484/
├── PREREGISTRATION.md              # Research design (locked)
├── MANIFEST.txt                    # SHA-256 source hashes
├── RESULTS.md                      # Full results + honest findings
├── README.md                       # This file
├── package.json                    # Node.js metadata
├── compute_hashes.sh               # Hash computation
├── measure_throughput.py           # Main execution script
├── generator/
│   └── scenario_generator.py      # Generates 100K scenarios
├── verifiers/
│   ├── v1_guard_frozen.js         # Frozen ARK-458 JS guard
│   └── v2_guard_frozen.py         # Frozen ARK-458 Python guard
└── results/
    ├── burst_scenarios.json       # 100K test scenarios (39.64 MB)
    └── throughput_results.json    # Measured metrics
```

---

## Compliance

**RF Standing Covenant:**
- ✓ Preregistered before execution
- ✓ Cryptographic lock (MANIFEST.txt)
- ✓ All outcomes preserved (PASS, with honest positive finding)
- ✓ No legal/patent claims
- ✓ Synthetic data only
- ✓ Results published regardless of outcome

**Limitations:**
- Single-threaded measurement (production would use multi-core)
- Warm cache only (no cold-start penalty)
- No I/O, network, or external services
- Burst throughput only (not sustained — see ARK-485)

---

**Series:** P02 — Latency, Throughput, and Scale  
**Experiment:** ARK-484 (12/25 in P02)  
**Organization:** Remnant Fieldworks Inc.  
**Executed:** 2026-07-18

**Honest Finding:** Performance exceeded predictions by 16.6–30.2×, demonstrating batch-mode efficiency not captured by individual-decision latency measurements (ARK-483).
