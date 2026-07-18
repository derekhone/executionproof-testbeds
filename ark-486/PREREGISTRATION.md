# ARK-486 — Verification Decision · Cost At Scale

**Status:** PREREGISTRATION (locked before execution)
**Experiment Date:** 2026-07-18
**Series:** ExecutionProof P02 Latency/Throughput/Scale

## Question

What is the marginal compute cost per verification decision at scale for the frozen ARK-458 guard, under the deployment model that actually matches how the verification engine runs?

## Modeling note (read first — this is a pre-lock design decision)

The ExecutionProof verification decision is an **in-process function call**. ARK-483/484/485 measured it running at **1.5M–9.5M decisions/sec inside a single process**. Therefore the correct unit of cost is **CPU time**, priced against a running-compute rate (per vCPU-second), amortized across the decisions that CPU second produces.

A naive serverless model that bills **one function invocation per individual decision** is a category error for this component: you do not pay a per-request charge for each internal function call — you pay it once for the enclosing API request, which itself processes many decisions. We therefore evaluate the verdict against the **realistic running-service model (Scenario B)** and **additionally disclose the naive per-invocation figure (Scenario A) as an explicit unrealistic upper bound**, so the reader sees both.

## Hypothesis

Under the realistic running-service model (Scenario B), marginal compute cost:
- **V2 (Python):** ≤ $0.01 per 1,000,000 decisions
- **V1 (JavaScript):** ≤ $0.01 per 1,000,000 decisions

## Component Under Test

**Frozen ARK-458 Cloud IAM Role Grant Guard** — cost derived from ARK-485 measured sustained throughput.

## Methodology

### Two cost scenarios (both reported; verdict on B)

**Scenario A — Serverless-naive (disclosed upper bound, NOT the verdict basis):**
- AWS Lambda: $0.20 per 1M requests + $0.0000166667/GB-second @ 128MB
- Assumes 1 Lambda invocation per single decision (unrealistic for an in-process engine)

**Scenario B — Realistic running service (verdict basis):**
- Priced on compute time only, at AWS Fargate vCPU rate **$0.04048/vCPU-hour** = **$0.00001124/vCPU-second** (us-east-1)
- Cost per decision = vCPU-second price ÷ sustained throughput (decisions per vCPU-second)
- Per-request/API cost amortizes across the millions of decisions in each invocation → negligible per decision

### Arms

| Arm | Implementation | Throughput Source | Threshold (Scenario B) |
|-----|----------------|-------------------|------------------------|
| A1  | V2 (Python)    | ARK-485 sustained | ≤ $0.01 / 1M decisions |
| A2  | V1 (JavaScript)| ARK-485 sustained | ≤ $0.01 / 1M decisions |

### Metrics

**Primary (Scenario B):** `cost_per_million_decisions_realistic`
**Disclosed (Scenario A):** `cost_per_million_decisions_naive`

### Thresholds (Gate Conditions)

**C1 (Realistic cost):** Both implementations ≤ $0.01 per 1M decisions under Scenario B
**C2 (Disclosure):** Scenario A naive bound is computed and reported (transparency gate)

**Verdict:** PASS if C1 ∧ C2; otherwise FAIL

## Honest Findings Commitment

Both scenarios are reported. If Scenario B exceeds threshold, the verdict is FAIL and preserved. The Scenario A naive figure is disclosed regardless, even though it is not the verdict basis, so no cost framing is hidden.

## Execution Protocol

1. **Lock:** Commit this preregistration + compute MANIFEST.txt hashes
2. **Execute:** Run `calculate_cost.py` using ARK-485 results
3. **Record:** Save results to `results/cost_results.json`
4. **Evaluate:** Compare Scenario B against C1; confirm C2 disclosure
5. **Report:** Document both scenarios in RESULTS.md

---

**Preregistered:** 2026-07-18
**Investigator:** Remnant Fieldworks Inc. / ExecutionProof Research Program
**Covenant:** RF Standing Covenant (preserve outcomes, bound claims, honest disclosure)
