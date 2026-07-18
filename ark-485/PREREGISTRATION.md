# ARK-485 — Verification Decision · Sustained Throughput

**Status:** PREREGISTRATION (locked before execution)
**Experiment Date:** 2026-07-18
**Series:** ExecutionProof P02 Latency/Throughput/Scale

## Question

What is the sustained throughput (decisions/second over extended duration) of the frozen ARK-458 deployment guard under continuous load?

ARK-484 measured **burst** throughput (peak capacity in short intervals). ARK-485 measures **sustained** throughput — how many decisions/second the guard can maintain over a longer duration (60 seconds) without degradation.

## Hypothesis

**V2 (Python):** ≥ 50,000 decisions/second sustained over 60s  
**V1 (JavaScript):** ≥ 100,000 decisions/second sustained over 60s

Lower than burst (ARK-484) due to thermal throttling, garbage collection, and memory pressure over extended runs.

## Component Under Test

**Frozen ARK-458 Cloud IAM Role Grant Guard** — exact-action-binding logic, LOCKED and unchanged since ARK-458 execution.

- **V2 Implementation:** Python (`verifiers/v2_guard.py`)
- **V1 Implementation:** JavaScript (`verifiers/v1_guard.js`)

## Methodology

### Test Design
- **Duration:** 60 seconds continuous execution per implementation
- **Decision path:** `allow_exact_match` (all 5 IAM dimensions match)
- **Measurement:** Total decisions completed / 60s = decisions/second sustained
- **Correctness check:** All decisions must return correct verdict (ALLOW for exact match)

### Arms

| Arm | Implementation | Duration | Threshold |
|-----|----------------|----------|-----------|
| A1  | V2 (Python)    | 60s      | ≥ 50K dec/s |
| A2  | V1 (JavaScript)| 60s      | ≥ 100K dec/s |

### Metrics

**Primary:**
- `sustained_throughput` — total decisions / 60 seconds (decisions/second)
- `accuracy` — correct decisions / total decisions (must be 1.0)

**Secondary:**
- `total_decisions` — raw count over 60s
- `warmup_time` — excluded from measurement (first 5s)

### Thresholds (Gate Conditions)

**C1 (Throughput):** Both implementations must meet their respective thresholds  
**C2 (Accuracy):** Both implementations must achieve 100% accuracy (all decisions correct)

**Verdict:** PASS if C1 ∧ C2; otherwise FAIL

### Kill-Gate / Effectiveness Conditions

**K1:** If sustained throughput < 10% of burst throughput → possible implementation error  
**K2:** If accuracy < 100% → guard logic compromised

## Honest Findings Commitment

Any deviation from hypothesis (higher/lower than predicted, unexpected degradation patterns, accuracy failures) will be disclosed in RESULTS.md.

## Execution Protocol

1. **Lock:** Commit this preregistration + compute MANIFEST.txt hashes
2. **Execute:** Run `measure_sustained.py` for both implementations
3. **Record:** Save results to `results/sustained_results.json`
4. **Evaluate:** Compare against thresholds C1, C2
5. **Report:** Document findings in RESULTS.md with honesty

---

**Preregistered:** 2026-07-18  
**Investigator:** Remnant Fieldworks Inc. / ExecutionProof Research Program  
**Covenant:** RF Standing Covenant (preserve outcomes, bound claims, honest disclosure)
