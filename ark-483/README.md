# ARK-483 — Verification Decision Latency

**Status:** EXECUTED — VERDICT **PASS** (both implementations; executed 2026-07-18T18:22Z UTC, post-lock — see `MANIFEST.txt`)

- Worst-path p95: **1.822 µs** (Python V2) · **0.652 µs** (JavaScript V1) — both ≤ the preregistered **1000 µs** ceiling (C1 ✓), with ~550×–1,500× headroom.
- A single ExecutionProof verification decision costs **~1 microsecond** on the reference machines; the decision logic is not a meaningful latency source on an authorization path.
- See `RESULTS.md` for the full readout, including the counter-intuitive **DENY-slower-than-ALLOW** finding.

**Substrate:** Classical software (in-process; no network, no I/O, no process spawn)
**Benches:** Dual independent — V1 (JavaScript), V2 (Python)
**Component Under Test:** the LOCKED ARK-458 exact-action-binding guard `evaluate()` (unchanged)
**Series:** ExecutionProof authorization-boundary corpus (production-boundary phase)

## Question

How long does a single ExecutionProof verification decision take? ARK-458 established that the exact-action-binding guard decides *correctly* (verdict PASS, 800/800 dual-guard concordance). ARK-483 measures how *fast* that same, frozen guard decides — answering **Prospect Question #2** ("What is the verification latency?"), the most-asked buyer question the RF corpus had never quantified.

## Design

Three decision paths, measured independently in each implementation, 100,000 timed iterations per path (5,000 warmup discarded, cold-start recorded separately):

| Path | Decision | Work |
|------|----------|------|
| `allow_exact_match` | ALLOW | all 5 dimensions compared |
| `deny_first_dim_mismatch` | DENY | early exit on dimension 1 |
| `deny_last_dim_mismatch` | DENY | worst-case DENY — all 5 compared |

Each call timed individually with a high-resolution monotonic clock (`perf_counter_ns` / `hrtime.bigint()`). Environment captured so every absolute number is bound to its machine.

## Pass criterion (preregistered)

- **C1:** worst-path p95 ≤ **1000 µs** (1 ms), in **each** implementation independently. Verdict = PASS iff C1 holds for both.

## Component-under-test integrity

The CUT is the **frozen** ARK-458 guard (locked under `ark-458/MANIFEST.txt`). The Python guard is imported directly; the JavaScript guard's **exact locked bytes** are loaded into a `vm` sandbox (its stdin `main()` loop is not run). **No ARK-458 file is modified.**

## Layout

```
ark-483/
├── PREREGISTRATION.md        # locked before execution
├── MANIFEST.txt              # SHA-256 lock of prereg + both benches
├── compute_hashes.sh         # re-verify the lock
├── package.json
├── bench/
│   ├── latency_bench.py      # V2 (Python) — CUT imported directly
│   └── latency_bench_v1.js   # V1 (JS) — CUT locked bytes via vm sandbox
├── results/
│   ├── latency_v2_python.json
│   └── latency_v1_js.json
├── RESULTS.md                # full readout + findings
└── README.md
```

## Reproduce

```bash
# from repo root
cd ark-483
python3 bench/latency_bench.py      # writes results/latency_v2_python.json
node    bench/latency_bench_v1.js    # writes results/latency_v1_js.json
./compute_hashes.sh                  # confirm locked files unchanged vs MANIFEST.txt
```

## Honest bounds

Measures the **in-process decision only** — excludes network, auth-token retrieval, evidence persistence, logging, and process startup; this is the **floor**. Absolute latencies are bound to the reference machines in the results files. A micro-benchmark of control logic, **not** a load/concurrency test or a production SLA. **No claim** that this legally validates any patent claim or certifies RF-100 conformance — working-example evidence only.

---

*Published under the Remnant Fieldworks Standing Covenant. To God be the glory. Proof Before Power. Verification Before Execution.*
