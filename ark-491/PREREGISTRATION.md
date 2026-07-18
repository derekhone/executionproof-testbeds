# ARK-491 — Authority Engine · Cost at Scale

**Status:** PREREGISTRATION (locked before execution)
**Experiment Date:** 2026-07-18
**Series:** ExecutionProof P02 Latency/Throughput/Scale

## Question

What is the marginal compute cost per authority decision (and per million decisions) of the reference **Authority Engine** under a realistic running-service deployment model?

Analogous to ARK-486 (Verification Decision cost), applied to the current-state authority check. ARK-486 established that a per-request serverless price per in-process decision is a **category error** (the engine is an in-process library call executing millions of decisions/second, not a per-request Lambda invocation). ARK-491 adopts the same corrected cost basis.

## Scope & Honesty Boundary

Minimal in-process reference `AuthorityEngine`, built to MEASURE, not the production engine. Cost figures are compute-time estimates for the reference implementation, not a customer quote.

## Cost Model

**Verdict basis — Scenario B (realistic running service):** the engine runs inside an always-on service; marginal cost per decision = compute time × vCPU-second price.
- AWS Fargate: **$0.04048 / vCPU-hour = $0.00001124 / vCPU-second**
- cost_per_decision = vCPU-second price ÷ throughput (dec/s)

**Disclosed upper bound — Scenario A (serverless-naive):** if (incorrectly) billed as one serverless request per decision (~$0.20/M + duration), reported for transparency only. NOT the verdict basis (see ARK-486 rationale).

## Hypothesis

Scenario B cost **≤ $0.01 per million decisions**.

## Component Under Test

Reference `AuthorityEngine` (exact, fail-closed). `engine/perf_harness.py --dimension cost` (derives cost from a 10s burst throughput measurement).

## Methodology

- Measure burst throughput (10s), derive cost_per_decision = Fargate vCPU-second ÷ throughput
- Report both cost_per_decision and cost_per_million_decisions (Scenario B), plus the Scenario A naive bound for disclosure

### Metrics

**Primary:** `cost_per_million_decisions` (Scenario B)
**Secondary:** `cost_per_decision`, `throughput_dps`, `naive_serverless_per_million` (Scenario A), `accuracy`

### Thresholds (Gate Conditions)

**C1 (Cost):** Scenario B cost_per_million_decisions ≤ $0.01
**C2 (Correctness gate):** valid→ALLOW, mutated→DENY, revoked→DENY

**Verdict:** PASS if C1 ∧ C2; otherwise FAIL

## Honest Findings Commitment

Both the realistic (Scenario B) and naive-serverless (Scenario A) figures are disclosed. The verdict is taken on Scenario B; the Scenario A bound is reported so readers can see the worst-case framing.

## Execution Protocol

1. **Lock** prereg + MANIFEST.txt hashes
2. **Execute** `engine/perf_harness.py --dimension cost`
3. **Record** to `results/cost_results.json`
4. **Evaluate** against C1, C2
5. **Report** in RESULTS.md

---

**Preregistered:** 2026-07-18
**Investigator:** Remnant Fieldworks Inc. / ExecutionProof Research Program
**Covenant:** RF Standing Covenant (preserve outcomes, bound claims, honest disclosure)
