# CUDA-EP-001 Master Record Update
## Remnant Fieldworks Inc. -- ExecutionProof Program
## Status: PRE-GPU FREEZE | Version: v0.1-pre-gpu | Date: 2026-10-01

---

## 1. Purpose

This document specifies the update to the RF master corpus scoreboard and scientific record that should be applied when CUDA-EP-001 GPU results are finalized. It does NOT make the update -- it prepares the update for Derek's review and authorization.

---

## 2. Current Master Corpus State (as of 2026-10-01)

| Field | Current Value |
|---|---|
| Total experiments | 106 |
| PASS | 95 |
| Preserved FAIL | 8 |
| Special / other | 3 |
| Source | Memory id=2: RF Inc Master Corpus Scoreboard |

---

## 3. CUDA-EP-001 Counting Doctrine -- FROZEN DECISION

The counting rule for CUDA-EP-001 is now FROZEN (not advisory). It was decided by Derek in the Real GPU Execution Pass brief and is recorded here as the governing rule:

### FROZEN RULE

```
CUDA-EP-001 = PENDING -- PRE-GPU
```

- CUDA-EP-001 is NOT counted toward the master experiment total until the real GPU phase produces an interpretable experimental result.
- The CPU-surrogate phase is SUPPORTING EVIDENCE for the pending GPU experiment. It does NOT receive its own separate corpus count.
- BLOCKED_NO_GPU is a governance/environment state, not a PASS and not a FAIL. It does not qualify CUDA-EP-001 for any corpus count.
- The master corpus totals remain UNCHANGED at this time:
  - 106 total
  - 95 PASS
  - 8 preserved FAIL
  - 3 special / other

### Why

The corpus counts interpretable experimental results tied to a primary hypothesis test and its ProofRecord set. CUDA-EP-001's primary hypothesis is a REAL GPU test (GPU-C0 through GPU-C8, with GPU-C8 the critical exclusive-launcher-control test). Until that runs on real NVIDIA hardware, there is no interpretable result to count. Counting a PENDING experiment, or counting the CPU-surrogate support phase as its own experiment, would inflate the corpus and is prohibited.

### When this changes

Only after real GPU execution produces a final interpretable result (see Section 4) does CUDA-EP-001 move from PENDING -- PRE-GPU to its actual status, and only then are the corpus totals updated. This update is deferred and must not be applied in this pass.

---

## 4. Proposed Master Record Update (Post-GPU)

The following update is PROPOSED for after GPU execution. It is NOT applied now.

### Scenario A: GPU-C0 through GPU-C8 all PASS (expected)

```
Total experiments: 107 (added 1: CUDA-EP-001)
PASS: 96 (added 1: CUDA-EP-001)
Preserved FAIL: 8 (unchanged)
Special / other: 3 (unchanged)
```

New entry:
```
CUDA-EP-001 | GPU CUDA Execution Pass | ExecutionProof | PASS | GPU-C8 BOUNDARY_ENFORCED
```

### Scenario B: GPU-C8 FAILS (BOUNDARY_CROSSED)

```
Total experiments: 107 (added 1: CUDA-EP-001)
PASS: 95 (unchanged -- C0-C7 pass but C8 fails)
Preserved FAIL: 9 (added 1: CUDA-EP-001 GPU-C8)
Special / other: 3 (unchanged)
```

New entry:
```
CUDA-EP-001 | GPU CUDA Execution Pass | ExecutionProof | PRESERVED_FAIL | GPU-C8 BOUNDARY_CROSSED
```

### Scenario C: Any GPU case other than C8 fails

```
Total experiments: 107 (added 1: CUDA-EP-001)
PASS: 95 (unchanged -- partial fail)
Preserved FAIL: 9 (added 1: CUDA-EP-001)
Special / other: 3 (unchanged)
```

New entry:
```
CUDA-EP-001 | GPU CUDA Execution Pass | ExecutionProof | PARTIAL_FAIL | [specific case(s) that failed]
```

---

## 5. CORPUS_SCOREBOARD.md Update Instructions

When GPU results are finalized, update the CORPUS_SCOREBOARD file in the `derekhone/executionproof-testbeds` repository as follows:

1. Add CUDA-EP-001 row with accurate verdict
2. Update headline totals
3. Commit message: `[corpus] CUDA-EP-001: GPU execution results -- [verdict]`
4. PR title: `[corpus-update] CUDA-EP-001 GPU phase results`
5. Do NOT merge without Derek's authorization

---

## 6. Memory Update Instructions (Global Memory id=2)

After GPU execution and corpus update, the global memory entry (id=2: RF Inc Master Corpus Scoreboard) must be updated to reflect:
- New total experiment count
- New PASS / FAIL counts
- CUDA-EP-001 entry in the scoreboard
- Concept DOI from Zenodo

This update will be performed in the session where GPU results are finalized.

---

## 7. RF Public Surface Update Instructions

After Zenodo deposit and Derek's public release authorization:

1. Update rf-inc.com (or equivalent public surface) to include CUDA-EP-001 in the published experiments list
2. Update ProofBeforePower YouTube description if applicable
3. Update LinkedIn / X bios if applicable (per RF-ID-33/34 doctrine)

These updates are HOLD pending Derek's authorization.

---

## 8. Zenodo Deposit Record Integration

After Zenodo deposit:
- Record concept DOI in this document
- Record version DOI (v0.1) in this document
- Add DOI to GitHub release notes
- Add DOI to CORPUS_SCOREBOARD.md entry

---

## 9. Open Items Requiring Derek's Decision

| Item | Question | Options |
|---|---|---|
| Counting doctrine | Does CPU-surrogate phase count as a separate experiment? | Yes / No (Recommendation: No) |
| BLOCKED_NO_GPU counting | How is the BLOCKED state counted in the corpus? | PENDING / PRESERVED_BLOCKED / Not counted |
| GPU timing | When will GPU execution be authorized? | HOLD per Section 5 |
| Public release | When is Zenodo deposit authorized for publication? | HOLD per Section 5 |
| Production key | When will TEST KEY be upgraded to production? | After successful GPU execution |

---

*Document version: v0.1-pre-gpu | Generated: 2026-10-01 | All updates HOLD pending Derek's authorization*
