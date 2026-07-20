# ARK-493 → ARK-498 Series — Reconciliation Report

**Series:** ARK-493 through ARK-498
**Preregistration:** `ARK-493-498-PREREGISTRATION-v1.1.md`
**Preregistration SHA-256:** `464b9fb8be9d6cca052f236dc9deec9f8e89b781cafc58701e79b2d05d52952a` — **verified match at execution time**
**Execution:** single `python3 run_all.py` run, one shared hash-chained ProofRecord store
**GATE-STOP triggered:** No (`halted_by_gate_stop = false`)

> This report reconciles what this series added to the standing ExecutionProof evidence corpus. Every number below is traceable to a file produced by this run (`results/results_ledger.jsonl`, `proofrecords/proofrecord_chain.jsonl`, `ledgers/T*.jsonl`, `results/execution_manifest.json`, `results/ark498_metrics.json`). No number is estimated.

---

## 1. This-series results (measured)

| Experiment | Title | Decision | Scored cases | PASS | FAIL |
|-----------|-------|----------|-------------|------|------|
| ARK-493 | Enforcement Boundary Under Adversarial Load | EXPERIMENT-PASS | 90 | 90 | 0 |
| ARK-494 | Semantic Boundary — Deep Argument Mutation | EXPERIMENT-PASS | 13 | 13 | 0 |
| ARK-495 | Temporal Boundary — Authority Change Mid-Flight | EXPERIMENT-PASS | 11 | 11 | 0 |
| ARK-496 | Multi-Agent Delegation & Self-Approval Defense | EXPERIMENT-PASS | 8 | 8 | 0 |
| ARK-497 | Independently Reconstructable ProofRecord | EXPERIMENT-PASS | 30 | 30 | 0 |
| ARK-498 | Networked Production-Like Performance | EXPERIMENT-PASS | 9 | 9 | 0 |
| **Total** | | **6 / 6 PASS** | **161** | **161** | **0** |

- **Scored cases this series: 161** (preregistration minimum was 152, excluding ARK-498 per-request performance traffic). Met.
- **Dual-guard agreement: 161 / 161** scored cases (Guard-A in-process + Guard-B isolated subprocess agree on every record).
- **Enforcement leaks: 0.** No DENY or HOLD case produced an `executed` side-effect ledger entry in any tool ledger. The GATE-STOP rule (D-5) was therefore not triggered.
- **Failures preserved:** there were 0 failures to preserve this series; had any occurred, they would remain in the ledger with `failure_root_cause` and would not have been retried.

### ARK-493 boundary matrix (the gate-stop gate)

- 6 execution paths × 15 cells = **90 cases**: P1-direct-call, P2-retry, P3-alternate-endpoint, P4-queued-execution, P5-tool-alias, P6-agent-created-subcall (15 each).
- Decision distribution: **30 ALLOW / 30 DENY / 30 HOLD.**
- All 30 ALLOW cases executed **exactly once** (idempotency held across retry/queued/alias paths). All 60 DENY/HOLD cases executed **zero** times. **Leak rows: 0.**

### Side-effect ledger totals (all scenarios, this run)

| Invocation type | Count |
|-----------------|-------|
| executed | 1,719 |
| blocked (DENY) | 139 |
| held (HOLD) | 30 |

(The large `executed` count is dominated by ARK-498's ~1,000 sustained-throughput ALLOW requests against T3; these are performance traffic, not scored cases.)

---

## 2. Corpus reconciliation

### 2.1 Pre-series baseline (as carried into this series)

| Metric | Value |
|--------|-------|
| Experiment IDs | 66 |
| Case records | 71 |
| PASS | 68 |
| FAIL | 2 |
| GATE-STOP | 1 |
| Repositories | 9 |

### 2.2 This series adds

| Metric | Delta |
|--------|-------|
| Experiment IDs | +6 (ARK-493, -494, -495, -496, -497, -498) |
| Scored case records | +161 |
| PASS | +161 |
| FAIL | +0 |
| GATE-STOP | +0 |
| Repositories | +0 (added to the existing `executionproof-testbeds` repository as the `ark-493-498/` subdirectory — no new repository created) |

### 2.3 Projected post-series totals

| Metric | Pre-series | + This series | **Post-series** |
|--------|-----------|---------------|-----------------|
| Experiment IDs | 66 | +6 | **72** |
| Case records | 71 | +161 | **232** |
| PASS | 68 | +161 | **229** |
| FAIL | 2 | +0 | **2** |
| GATE-STOP | 1 | +0 | **1** |
| Repositories | 9 | +0 | **9** |

**Reconciled public headline numbers to use going forward: 72 experiments, 232 case records, 229 PASS, 2 FAIL, 1 GATE-STOP across 9 repositories.**

> The 2 pre-existing FAIL records and the 1 pre-existing GATE-STOP record are **retained unchanged**. Honest framing requires that the historical FAIL/GATE-STOP entries continue to be reported; they are evidence the methodology preserves negative results rather than suppressing them.

---

## 3. ARK-498 characterization (summary; full detail in `ark498_performance_report.md`)

> **PRODUCTION-LIKE OVERHEAD CHARACTERIZATION · NOT A BENCHMARK CERTIFICATION · NOT A PRODUCTION SLA**

ARK-498 ran the gate behind a real Flask HTTP/loopback-TCP boundary across 9 scenarios (~1,810 requests) with simulated dependency latencies (policy lookup 50 ms, authority lookup 30 ms, real ProofRecord disk I/O).

- **Latency (measured, `time.monotonic()`):** cold start ≈ 85.2 ms; warm p50 ≈ 83.9 ms; under 10 concurrent clients p50 ≈ 84.4 ms / p95 ≈ 88.0 ms / p99 ≈ 93.9 ms.
- **Sustained throughput (middle 60% of a 1,000-request run, 5 clients):** ≈ 59.7 req/s. This figure is dominated by the injected 80 ms of simulated dependency sleeps per request and is **characterization data only**.
- **All six hard criteria met:** fail-closed leak count = 0 (S005/S006/S007); duplicate executions = 0 (S009); ProofRecord completeness = 100% (1,766/1,766); error accounting = 0 ALLOW-on-error; recovery with 0 auto re-executions of denied requests (S008); Guard-B signature verification = 100% (1,766/1,766).

These latency/throughput numbers **must not** be compared to the prior microsecond in-process testbed (ARK-483–492): different architecture, different scope. They are not a production SLA and require independent measurement under production conditions before any performance claim.

---

## 4. Artifacts backing this report

| Artifact | Path |
|----------|------|
| Results ledger (161 scored rows) | `results/results_ledger.jsonl` |
| Hash-chained ProofRecords (1,894 records incl. summaries) | `proofrecords/proofrecord_chain.jsonl` |
| Side-effect ledgers T1–T5 | `ledgers/T1_*.jsonl` … `ledgers/T5_*.jsonl` |
| Execution manifest (prereg hash + per-experiment decisions) | `results/execution_manifest.json` |
| ARK-498 raw metrics | `results/ark498_metrics.json` |
| ARK-497 isolated-verifier output | `results/ark497_verifier_output.json` |
