# ARK-502 Synthetic 1-Year Simulation

## What this is

A **synthetic 1-year simulation** that compresses 365 days of operations, events, and restarts into **~30-60 minutes** of runtime. It tests the **LOGIC** of long-running safety (chain continuity, restart resume, stressor survival) without requiring wall-clock endurance.

**Honest label:** SYNTHETIC 1-YEAR SIMULATION — logic-tested, NOT wall-clock endurance. Real ≥14-day endurance = NOT-EXECUTED (requires persistent machine). Contributes **0 scored PASS** to corpus (design choice).

---

## What it simulates

| Category | Count | What happens |
|---|---|---|
| **Simulated days** | 365 | One full year compressed |
| **Total operations** | ~13,000-15,000 | Mixed ALLOW/DENY/HOLD traffic |
| **Process restarts** | 12 | Monthly (simulating crashes, planned maintenance) |
| **Key rotations** | 4 | Quarterly checkpoints (restart + chain resume) |
| **Policy changes** | 12 | Monthly version-mismatch tests |
| **Dependency outages** | 9 | Scattered across the year; all fail-closed |
| **Malformed bursts** | 4 | Fail-closed stress tests |
| **Concurrency bursts** | 3 | Exactly-once under parallel load |

---

## Hard criteria (all must pass)

| Criterion | Requirement |
|---|---|
| **SY-1** | Zero chain linkage breaks across all restarts |
| **SY-2** | Zero enforcement leaks (all commits = expected commits) |
| **SY-3** | 100% dual-guard agreement on all ProofRecords |
| **SY-4** | All 12+ restarts successfully resumed the chain |
| **SY-5** | Simulated year completed (365 days) |

---

## How to run

### Quick demo (no PostgreSQL required, ~1 second)
```bash
cd /home/ubuntu/ark-499-503-testbed
python3 demo_synthetic_year.py
```
Shows the simulation structure and events without needing the full testbed.

### Real synthetic-year test (~30-60 minutes)
**Prerequisites:** PostgreSQL 17 binaries on PATH (`initdb`, `pg_ctl`, `postgres`)

```bash
cd /home/ubuntu/ark-499-503-testbed
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Run the full synthetic year
python3 experiments/run_502.py --mode=synthetic-year
```

The real run:
- Executes through the **frozen ExecutionProof gate** (byte-identical to ARK-493-498)
- Commits real rows to **PostgreSQL 17**
- Builds a continuous **hash-chained ProofRecord** ledger
- Verifies chain integrity after **every restart**
- Outputs:
  - `results/results_ledger.jsonl` (synthetic-year entry)
  - `proofrecords/proofrecord_chain.jsonl` (continuous chain)
  - Summary ProofRecord with all metrics

### Original bounded smoke mode (default, ~1 minute)
```bash
python3 experiments/run_502.py
# or explicitly:
python3 experiments/run_502.py --mode=smoke
```

---

## What this proves vs. what it doesn't

### ✓ What the synthetic year proves
- **Chain continuity logic** works across restarts
- **Fail-closed behavior** survives dependency outages
- **Exactly-once semantics** hold under concurrency
- **Policy/key rotation checkpoints** preserve chain integrity
- The enforcement harness can handle **thousands of operations** and **dozens of events** without leaking or breaking

### ✗ What it does NOT prove (and honestly doesn't claim)
- **NOT** wall-clock endurance (it's compressed time, not real time)
- **NOT** clock-drift resistance (no real clock passage)
- **NOT** sustained load over days/weeks (it's minutes)
- **NOT** real operational wear (simulated events, not production traffic)

**For wall-clock endurance:** the ≥14-day real-time soak remains **NOT-EXECUTED** and requires a persistent machine (e.g., SuperComputer).

---

## Cost comparison

| Mode | Runtime | Operations | What it tests | Cost |
|---|---|---|---|---|
| **Bounded smoke** | ~1 min | ~400 | Sanity check | Ephemeral VM (free) |
| **Synthetic year** | ~30-60 min | ~13K-15K | Logic of long-running safety | Ephemeral VM (free) |
| **Real 14-day** | 14 days | millions+ | Wall-clock endurance | SuperComputer ~$336-$1,008 |

The synthetic year gives you **strong logic evidence** at **zero incremental cost** before committing to the wall-clock run.

---

## Output example (from demo)

```
======================================================================
SYNTHETIC YEAR COMPLETE (0.0s runtime)
======================================================================
  Simulated days:         365
  Total operations:       13,116
  Restarts:               12 (monthly)
  Key rotations:          4 (quarterly)
  Policy changes:         12 (monthly)
  Dependency outages:     9

  Decisions:
    ALLOW:  7,786
    DENY:   4,048
    HOLD:   1,282

  Database commits:       7,741
  Expected commits:       7,741
  Enforcement leaks:      0 ✓
  Chain linkage breaks:   0 ✓
  Dual-guard failures:    0 ✓

  Hard criteria:
    SY-1_zero_chain_breaks: ✓ PASS
    SY-2_zero_leaks: ✓ PASS
    SY-3_dual_guard_100pct: ✓ PASS
    SY-4_all_restarts_resumed: ✓ PASS
    SY-5_simulated_year_complete: ✓ PASS

  DECISION: SYNTHETIC-YEAR-PASS
```

---

*Built in faith. Tested in public. Claims kept narrower than the evidence.*
