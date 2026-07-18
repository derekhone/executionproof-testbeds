# ARK-490 — Authority Engine · Sustained Throughput

**Status:** PREREGISTRATION (locked before execution)
**Experiment Date:** 2026-07-18
**Series:** ExecutionProof P02 Latency/Throughput/Scale

## Question

What is the sustained throughput — authority decisions/second maintained over an extended window — of the reference **Authority Engine**, and does it degrade relative to burst (ARK-489)?

Analogous to ARK-485 (Verification Decision sustained), applied to the current-state authority check.

## Scope & Honesty Boundary

Minimal in-process reference `AuthorityEngine`, built to MEASURE, not the production engine. Claims bounded to this reference under the stated load.

## Hypothesis

Sustained throughput **≥ 100,000 decisions/second** over 60 seconds at **100% accuracy** — lower than burst due to GC and memory pressure over the longer window.

## Component Under Test

Reference `AuthorityEngine` (exact, fail-closed). `engine/perf_harness.py --dimension sustained`.

## Methodology

- **Warmup:** 5 seconds (excluded)
- **Sustained window:** 60 seconds of continuous decisions on the valid grant path
- Count total and correct decisions; throughput = total / elapsed

### Metrics

**Primary:** `sustained_throughput_dps`, `accuracy`
**Secondary:** `total_decisions`, `duration_sec`

### Thresholds (Gate Conditions)

**C1 (Throughput):** ≥ 100,000 dec/s
**C2 (Accuracy):** 100%
**C3 (Correctness gate):** valid→ALLOW, mutated→DENY, revoked→DENY

**Verdict:** PASS if C1 ∧ C2 ∧ C3; otherwise FAIL

### Kill-Gate

**K1:** Sustained < 10% of burst (ARK-489) → possible implementation error.
**K2:** Accuracy < 100% → guard logic compromised → GATE-STOP.

## Honest Findings Commitment

Any deviation (degradation patterns, accuracy failures) disclosed in RESULTS.md.

## Execution Protocol

1. **Lock** prereg + MANIFEST.txt hashes
2. **Execute** `engine/perf_harness.py --dimension sustained`
3. **Record** to `results/sustained_results.json`
4. **Evaluate** against C1–C3
5. **Report** in RESULTS.md

---

**Preregistered:** 2026-07-18
**Investigator:** Remnant Fieldworks Inc. / ExecutionProof Research Program
**Covenant:** RF Standing Covenant (preserve outcomes, bound claims, honest disclosure)
