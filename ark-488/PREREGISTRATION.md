# ARK-488 — Authority Engine · P95 Decision Latency

**Status:** PREREGISTRATION (locked before execution)
**Experiment Date:** 2026-07-18
**Series:** ExecutionProof P02 Latency/Throughput/Scale

## Question

On a warm reference **Authority Engine**, what is the per-decision latency distribution (p50 / p95 / p99) for a single current-state authority check?

This is the buyer's most-asked question applied to the authority half of Verification-Before-Execution: *how much latency does an at-execution "does this principal still hold this authority?" check add to the critical path?*

## Scope & Honesty Boundary

Component under test is the minimal in-process reference `AuthorityEngine` — built to MEASURE, not the production engine (persistent store, replication, external IdP). Claims bounded to this reference under the stated load.

## Hypothesis

Warm per-decision latency **p95 ≤ 50 µs** and **p99 ≤ 200 µs** (dict + set membership operations, no I/O).

## Component Under Test

Reference `AuthorityEngine` (exact, fail-closed): principal lookup → grant membership → current-state revocation test. `engine/perf_harness.py --dimension p95_latency`.

## Methodology

- **Warmup:** 10,000 decisions (excluded)
- **Measurement:** 200,000 timed decisions on the valid grant path
- Record per-call elapsed time (µs); compute p50, p95, p99, mean, max

### Metrics

**Primary:** `latency_us` — p50, p95, p99
**Secondary:** mean, max

### Thresholds (Gate Conditions)

**C1 (Latency):** p95 ≤ 50 µs
**C2 (Correctness):** correctness gate must PASS (valid→ALLOW, mutated→DENY, revoked→DENY)

**Verdict:** PASS if C1 ∧ C2; otherwise FAIL

### Kill-Gate

**K1:** Correctness gate failure → GATE-STOP; latency numbers void.

## Honest Findings Commitment

Any deviation (tail latency spikes, correctness failures) disclosed in RESULTS.md.

## Execution Protocol

1. **Lock** prereg + MANIFEST.txt hashes
2. **Execute** `engine/perf_harness.py --dimension p95_latency`
3. **Record** to `results/p95_results.json`
4. **Evaluate** against C1, C2
5. **Report** in RESULTS.md

---

**Preregistered:** 2026-07-18
**Investigator:** Remnant Fieldworks Inc. / ExecutionProof Research Program
**Covenant:** RF Standing Covenant (preserve outcomes, bound claims, honest disclosure)
