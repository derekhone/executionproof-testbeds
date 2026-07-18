# ARK-483 — Preregistration

## Verification Decision Latency

**Series:** ExecutionProof authorization-boundary corpus — **Production-Boundary phase (P01)**
**Experiment ID:** ARK-483
**Institution:** Remnant Fieldworks Inc.
**PI:** Derek Adam Hone
**Substrate:** Classical software (no quantum hardware, no cryptographic security claims)
**Benches:** Dual independent — V1 (JavaScript), V2 (Python)
**Component Under Test (CUT):** the ARK-458 exact-action-binding guard (`evaluate()`)
**Preregistration status:** LOCKED before official execution (see `MANIFEST.txt`)

---

### Commercial / standards / IP justification (required by RF covenant)

- **Commercial purpose:** Directly answers **Prospect Question #2** — *"What is the verification latency?"* — the single most-asked buyer question that the RF corpus had **never measured**. Every prior experiment established *whether* ExecutionProof decides correctly; none had established *how fast* a decision is. This is the first RF latency measurement, and it measures the real production-boundary decision path built in ARK-458.
- **RF-100 requirement:** Provides the quantitative basis for a future **verification-overhead budget** clause — the claim that gate verification adds negligible latency to an approved action.
- **Patent-family connection:** Produces dated **working-example** evidence that the exact-action verification mechanism (filed parent `19/529,283` and the AI-governance / proof CIP family) is computationally cheap enough to sit inline on an authorization path. *Working-example evidence only — it does not legally validate any claim, and adds no new matter to any filed application.*

---

### Question

How long does a single ExecutionProof **verification decision** take? Specifically, for the ARK-458 exact-action-binding guard, what is the per-decision wall-clock latency (mean and tail percentiles) for the ALLOW path (exact match, all dimensions compared) and the DENY paths (mismatch), on the reported reference machine — and is it low enough to sit inline on a production authorization path without a meaningful latency penalty?

### Component Under Test

The **frozen** ARK-458 guard `evaluate()` — measured directly, in-process, with no network, no I/O, no process spawn between calls. ARK-458 established this guard's *correctness* (verdict PASS, dual-guard concordance 800/800). ARK-483 measures only its *speed*. The ARK-458 guard files are locked and are **not modified**:

- **V2 (Python):** `ark-458/verifiers/v2_guard.py :: evaluate` — imported directly.
- **V1 (JavaScript):** `ark-458/verifiers/v1_guard.js :: evaluate` — loaded as its exact **locked bytes** into a `vm` sandbox (its stdin `main()` loop is not executed). No edit is made to the locked file; the bytes measured are the frozen guard.

### Design

Three decision paths are measured **independently in each implementation** (V1 and V2):

| Path | Description | Decision | Work performed |
|------|-------------|----------|----------------|
| `allow_exact_match` | execution action equals approved action on all 5 dimensions | ALLOW | all 5 dimensions compared |
| `deny_first_dim_mismatch` | first binding dimension (`principal`) differs | DENY | early exit on dimension 1 |
| `deny_last_dim_mismatch` | last binding dimension (`condition`) differs | DENY | worst-case DENY — all 5 compared before mismatch |

- **Warmup:** 5,000 discarded iterations per implementation (JIT / cache warm).
- **Cold start:** the first-ever decision latency is recorded separately (not folded into the warm sample).
- **Timed sample:** N = 100,000 timed iterations **per path**, each timed individually with a high-resolution monotonic clock (`time.perf_counter_ns` in Python, `process.hrtime.bigint()` in Node).
- **Reported statistics per path:** mean, median, p50, p95, p99, p99.9, min, max, stdev, throughput (decisions/sec).
- **Environment** (CPU model, language/runtime version, OS) is captured into the results file so every absolute number is bound to the machine that produced it.

### Metrics

- `p95_us` per path = 95th-percentile per-decision latency in microseconds.
- `worst_path_p95_us` = max p95 across the three paths (the figure judged against the ceiling).
- Secondary: cross-implementation concordance — V1 and V2 worst-path p95 should fall in the **same order of magnitude** (both are independent implementations of the identical procedure; a large divergence would indicate a harness artefact).

### Pass criterion (fixed before execution)

- **C1 (latency ceiling):** `worst_path_p95_us` ≤ **1000 µs** (1 ms) for a single in-process decision, **in each implementation independently**.
- **Verdict = PASS** iff C1 holds for both V1 and V2; else FAIL. The measured numbers are published either way.

> The 1 ms ceiling is a deliberately generous, buyer-legible bar ("a verification decision adds under a millisecond"). It is preregistered so the result cannot be reverse-fit; the honest expectation is that the true figure is far below it, and the published numbers — not the ceiling — are the deliverable.

### Kill conditions / validity gate

1. **Decision-sanity gate:** before timing each path, the CUT is invoked once and its decision **must** equal the path's expected decision (ALLOW/DENY). If any path does not produce its expected decision, the run **ABORTS** (no verdict) — a latency number for the wrong decision is meaningless.
2. **Non-triviality:** N ≥ 100,000 timed iterations per path and warmup ≥ 5,000, fixed before execution, so the sample is not a micro-artefact.

### Publication rule

The outcome (PASS, FAIL, or ABORT) will be published to GitHub with the raw per-path results JSON for both implementations, and defensively published to Zenodo (CC BY 4.0), regardless of verdict.

### Honest bounds

- This measures the **in-process decision only.** It explicitly **excludes** network round-trips, authorization-token retrieval, evidence/ProofRecord persistence, logging, serialization at a service boundary, and process startup. A real deployed gate will be slower; this is the **floor**, the cost of the decision logic itself.
- Absolute latencies are **bound to the reference machine** reported in the results file. They are not a guarantee on any other hardware, runtime, or load condition.
- This is a micro-benchmark of **control logic**, not a load test, not a concurrency/throughput test under contention, and not a production SLA.
- No claim that this experiment legally validates any patent claim or certifies RF-100 conformance. Working-example evidence only.

---

*Preregistered under the Remnant Fieldworks Standing Covenant (preregister → lock → execute → publish all outcomes). To God be the glory. Proof Before Power. Verification Before Execution.*
