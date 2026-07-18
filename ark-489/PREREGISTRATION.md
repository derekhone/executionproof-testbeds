# ARK-489 — Authority Engine · Burst Throughput

**Status:** PREREGISTRATION (locked before execution)
**Experiment Date:** 2026-07-18
**Series:** ExecutionProof P02 Latency/Throughput/Scale

## Question

What is the peak (burst) throughput — authority decisions/second in a short high-intensity interval — of the reference **Authority Engine**?

Analogous to ARK-484 (Verification Decision burst), applied to the current-state authority check.

## Scope & Honesty Boundary

Minimal in-process reference `AuthorityEngine`, built to MEASURE, not the production engine. Claims bounded to this reference under the stated load.

## Hypothesis

Burst throughput **≥ 200,000 decisions/second** over a 10-second window, at **100% accuracy**.

## Component Under Test

Reference `AuthorityEngine` (exact, fail-closed). `engine/perf_harness.py --dimension burst`.

## Methodology

- **Warmup:** 10,000 decisions (excluded)
- **Burst window:** 10 seconds of continuous decisions on the valid grant path
- Count total decisions and correct decisions; throughput = total / elapsed

### Metrics

**Primary:** `burst_throughput_dps` (decisions/second), `accuracy`
**Secondary:** `total_decisions`, `duration_sec`

### Thresholds (Gate Conditions)

**C1 (Throughput):** ≥ 200,000 dec/s
**C2 (Accuracy):** 100% (all decisions correct)
**C3 (Correctness gate):** valid→ALLOW, mutated→DENY, revoked→DENY

**Verdict:** PASS if C1 ∧ C2 ∧ C3; otherwise FAIL

### Kill-Gate

**K1:** Accuracy < 100% → guard logic compromised → GATE-STOP.

## Honest Findings Commitment

Any deviation disclosed in RESULTS.md.

## Execution Protocol

1. **Lock** prereg + MANIFEST.txt hashes
2. **Execute** `engine/perf_harness.py --dimension burst`
3. **Record** to `results/burst_results.json`
4. **Evaluate** against C1–C3
5. **Report** in RESULTS.md

---

**Preregistered:** 2026-07-18
**Investigator:** Remnant Fieldworks Inc. / ExecutionProof Research Program
**Covenant:** RF Standing Covenant (preserve outcomes, bound claims, honest disclosure)
