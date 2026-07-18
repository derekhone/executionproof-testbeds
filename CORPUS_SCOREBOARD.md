# Remnant Fieldworks Inc. — Master Corpus Scoreboard
## ARK Series 441–484 + WITNESS Series
**Last updated:** 2026-07-18 (P01 complete — all 25 production-boundary experiments)

---

## EXECUTIVE SUMMARY

**Total RF Corpus:** 33 case records across 30 experiment IDs
- **ARK Series:** 28 experiments (26 PASS, 2 FAIL honest, 1 GATE-STOP) — 21 records prior + 7 new (ARK-459-462, ARK-463-467, ARK-468-482, ARK-484)
- **WITNESS Series:** 2 experiments, 6 cases (all PASS)

**P01 Production-Boundary Series (ARK-458-482):** ✅ **COMPLETE** — 25/25 experiments PASS
- 20,000 authorization decisions tested across 5 critical failure modes
- 100% dual-guard concordance (20,000/20,000)
- 100% kill-gate falsifiability
- All 25 experiments published to Zenodo with DOI badges

**P02 Latency/Throughput Series (ARK-483-492):** 2/10 complete
- ARK-483 (Latency): ✅ PASS
- ARK-484 (Burst Throughput): ✅ PASS

---

## WITNESS SERIES (quantum-sourced nonce provenance)

### WITNESS-1 — Quantum-Sourced Authorization Nonces with Verifiable Provenance
**Status:** COMPLETE + MERGED + PUBLISHED (2026-07-18)
- **Repository:** https://github.com/derekhone/witness-testbeds
- **Backend:** ibm_fez (156q Heron r2), Job ID: `d9dgp6kjeosc73fhigsg`
- **Shots:** 4000, 256 unique outcomes (full 2⁸ basis coverage)
- **Quantum Nonce:** `2a06cecc238ddcf1e8c2774df2074d9bd3d3fdbc7b1a3e6436281648aadad0ec`
- **DOI (version):** [10.5281/zenodo.21424324](https://zenodo.org/record/21424324)
- **DOI (concept):** [10.5281/zenodo.21424323](https://zenodo.org/record/21424323)
- **Verdicts:**
  - W1-C1 (honest verify): ✅ PASS
  - W1-C2 (tamper detect 3/3): ✅ PASS
  - W1-C3 (replay prevention): ✅ PASS
- **Overall:** 3/3 PASS

### WITNESS-2 — Length-Prefixed Quantum Nonce with Record-Hash Field Integrity
**Status:** COMPLETE + MERGED + PUBLISHED (2026-07-18)
- **Repository:** https://github.com/derekhone/witness-testbeds
- **Backend:** ibm_fez (Heron r2), Job ID: `d9di7nkinv1c73ap4ed0`
- **Shots:** 4000, 256 unique outcomes
- **Quantum Nonce:** `e425dc92c028b344f3f8f46b9c269bf9f8696f87e6b0085d46fad7452770659b`
- **Record Hash:** `271ff5eae1fdfac85f6fd24ebd919a608804d6f1546a4ca9874f481ce5f97ae1`
- **DOI (version):** [10.5281/zenodo.21425381](https://zenodo.org/record/21425381)
- **DOI (concept):** [10.5281/zenodo.21424323](https://zenodo.org/record/21424323)
- **Verdicts:**
  - W2-C1 (honest verify + provenance, 9 checks): ✅ PASS
  - W2-C2 (tamper 4/4): ✅ PASS
  - W2-C3 (cross-context replay): ✅ PASS
- **Overall:** 3/3 PASS

**WITNESS Series Tally:** 2 experiments, 6 cases — all PASS

---

## ARK SERIES (ExecutionProof authorization boundary)

### Hardware Quantum ARKs (ARK-441–448)
**Backends:** ARK-441 on ibm_kingston (156q); ARK-442–448 on ibm_marrakesh (156q)

| ARK | Question | Verdict | Backend | DOI |
|-----|----------|---------|---------|-----|
| ARK-441 | VBE authorization boundary baseline | ✅ PASS | ibm_kingston | 10.5281/zenodo.21404867 |
| ARK-442 | Delay/expiry boundary | ✅ PASS | ibm_marrakesh | 10.5281/zenodo.21404867 |
| ARK-443 | Two-of-three quorum | ✅ PASS | ibm_marrakesh | 10.5281/zenodo.21404867 |
| ARK-444 | Decision-to-execution integrity | ✅ PASS | ibm_marrakesh | 10.5281/zenodo.21404867 |
| ARK-445 | Tri-state ALLOW/HOLD/DENY | ❌ FAIL (honest) | ibm_marrakesh | 10.5281/zenodo.21404867 |
| ARK-445b | Reset-free re-test | ✅ PASS | ibm_marrakesh | 10.5281/zenodo.21418404 |
| ARK-446 | Cross-device replication | ✅ PASS | ibm_marrakesh | 10.5281/zenodo.21404867 |
| ARK-447 | Pauli twirling vs baseline | ✅ PASS | ibm_marrakesh | 10.5281/zenodo.21404867 |
| ARK-448 | Dynamical decoupling vs baseline | ⛔ GATE-STOP | ibm_marrakesh | 10.5281/zenodo.21404867 |

### Classical/Software ARKs (ARK-449–457)
**Substrate:** Pure classical software, no quantum hardware

| ARK | Question | Verdict | DOI |
|-----|----------|---------|-----|
| ARK-449 | State change after verification | ✅ PASS | 10.5281/zenodo.21406335 |
| ARK-450 | Verified action substitution attack | ✅ PASS | 10.5281/zenodo.21420310 |
| ARK-451 | Authority revocation during execution | ✅ PASS | 10.5281/zenodo.21419480 |
| ARK-452 | Multi-step workflow, one invalid step | ✅ PASS | 10.5281/zenodo.21406668 |
| ARK-453 | Conflicting evidence must HOLD | ✅ PASS | 10.5281/zenodo.21419198 |
| ARK-454 | Self-approval & circular delegation | ✅ PASS | 10.5281/zenodo.21418935 |
| ARK-455 | ProofRecord tamper (dual-verifier) | ❌ FAIL (honest) | 10.5281/zenodo.21418388 |
| ARK-455b | ProofRecord tamper — CORRECTED retest | ✅ PASS | 10.5281/zenodo.21418404 |
| ARK-456 | Fail-closed dependency loss | ✅ PASS | 10.5281/zenodo.21420107 |
| ARK-457 | Cross-context authorization replay | ✅ PASS | 10.5281/zenodo.21421742 |

---

## P01 PRODUCTION-BOUNDARY SERIES (ARK-458–482)
**Status:** ✅ **COMPLETE** — 25/25 experiments PASS (executed 2026-07-18)
**Repository:** https://github.com/derekhone/executionproof-testbeds
**Substrate:** Classical software (dual-guard: JavaScript V1 + Python V2)

### Cloud IAM Role Grant (ARK-458–462)
Testing exact-action binding and 4 critical failure modes in cloud IAM authorization.

| ARK | Failure Mode | Arms×Scenarios | Verdict | g_metrics | Concordance | Kill-Gate | DOI |
|-----|--------------|----------------|---------|-----------|-------------|-----------|-----|
| ARK-458 | Exact-Action Binding | 8×100=800 | ✅ PASS | g_allow=1.0000, g_deny_min=1.0000, g_margin=0.9500 | 800/800 (100%) | 281/700 | 10.5281/zenodo.21432645 |
| ARK-459 | Revocation At Execution | 8×100=800 | ✅ PASS | g_allow=1.0000, g_deny=1.0000, g_hold=1.0000, g_margin=0.9500 | 800/800 (100%) | 125/125 | 10.5281/zenodo.21432879 |
| ARK-460 | Dependency Loss | 8×100=800 | ✅ PASS | g_allow=1.0000, g_hold_min=1.0000, g_margin=0.9500 | 800/800 (100%) | 150/150 | 10.5281/zenodo.21432883 |
| ARK-461 | Cross-Context Replay | 8×100=800 | ✅ PASS | g_allow=1.0000, g_deny_min=1.0000, g_margin=0.9500 | 800/800 (100%) | 150/150 | 10.5281/zenodo.21432887 |
| ARK-462 | Human Escalation | 8×100=800 | ✅ PASS | g_allow_no_esc=1.0000, g_allow_approved=1.0000, g_hold_min=1.0000, g_margin=0.9500 | 800/800 (100%) | 100/100 | 10.5281/zenodo.21432889 |

**Series metrics:** 4,000 decisions, 4,000/4,000 concordance, 806 kill-gate wrong-allows detected

### Production Deployment (ARK-463–467)
Testing exact-action binding and 4 critical failure modes in production deployment authorization.

| ARK | Failure Mode | Arms×Scenarios | Verdict | g_metrics | Concordance | Kill-Gate | DOI |
|-----|--------------|----------------|---------|-----------|-------------|-----------|-----|
| ARK-463 | Exact-Action Binding | 8×100=800 | ✅ PASS | g_allow=1.0000, g_deny_min=1.0000, g_margin=1.0000 | 800/800 (100%) | 600/600 | 10.5281/zenodo.21433070 |
| ARK-464 | Revocation At Execution | 8×100=800 | ✅ PASS | g_allow=1.0000, g_deny=1.0000, g_hold=1.0000, g_margin=0.9500 | 800/800 (100%) | 125/125 | 10.5281/zenodo.21433072 |
| ARK-465 | Dependency Loss | 8×100=800 | ✅ PASS | g_allow=1.0000, g_hold_min=1.0000, g_margin=0.9500 | 800/800 (100%) | 150/150 | 10.5281/zenodo.21433074 |
| ARK-466 | Cross-Context Replay | 8×100=800 | ✅ PASS | g_allow=1.0000, g_deny_min=1.0000, g_margin=0.9500 | 800/800 (100%) | 150/150 | 10.5281/zenodo.21433077 |
| ARK-467 | Human Escalation | 8×100=800 | ✅ PASS | g_allow_no_esc=1.0000, g_allow_approved=1.0000, g_hold_min=1.0000, g_margin=0.9500 | 800/800 (100%) | 100/100 | 10.5281/zenodo.21433081 |

**Series metrics:** 4,000 decisions, 4,000/4,000 concordance, 1,125 kill-gate wrong-allows detected

### Database Destructive Query (ARK-468–472)
Testing exact-action binding and 4 critical failure modes for database DROP/DELETE/TRUNCATE operations.

| ARK | Failure Mode | Arms×Scenarios | Verdict | g_metrics | Concordance | Kill-Gate | DOI |
|-----|--------------|----------------|---------|-----------|-------------|-----------|-----|
| ARK-468 | Exact-Action Binding | 8×100=800 | ✅ PASS | g_allow=1.0000, g_deny_min=1.0000, g_margin=1.0000 | 800/800 (100%) | 600/600 | 10.5281/zenodo.21433449 |
| ARK-469 | Revocation At Execution | 8×100=800 | ✅ PASS | g_allow=1.0000, g_deny=1.0000, g_hold=1.0000, g_margin=0.9500 | 800/800 (100%) | 125/125 | 10.5281/zenodo.21433451 |
| ARK-470 | Dependency Loss | 8×100=800 | ✅ PASS | g_allow=1.0000, g_hold_min=1.0000, g_margin=0.9500 | 800/800 (100%) | 150/150 | 10.5281/zenodo.21433453 |
| ARK-471 | Cross-Context Replay | 8×100=800 | ✅ PASS | g_allow=1.0000, g_deny_min=1.0000, g_margin=0.9500 | 800/800 (100%) | 150/150 | 10.5281/zenodo.21433455 |
| ARK-472 | Human Escalation | 8×100=800 | ✅ PASS | g_allow_no_esc=1.0000, g_allow_approved=1.0000, g_hold_min=1.0000, g_margin=0.9500 | 800/800 (100%) | 100/100 | 10.5281/zenodo.21433457 |

**Series metrics:** 4,000 decisions, 4,000/4,000 concordance, 1,125 kill-gate wrong-allows detected

### Financial Transaction (ARK-473–477)
Testing exact-action binding and 4 critical failure modes for TRANSFER/WITHDRAW/DEPOSIT operations.

| ARK | Failure Mode | Arms×Scenarios | Verdict | g_metrics | Concordance | Kill-Gate | DOI |
|-----|--------------|----------------|---------|-----------|-------------|-----------|-----|
| ARK-473 | Exact-Action Binding | 8×100=800 | ✅ PASS | g_allow=1.0000, g_deny_min=1.0000, g_margin=1.0000 | 800/800 (100%) | 600/600 | 10.5281/zenodo.21433459 |
| ARK-474 | Revocation At Execution | 8×100=800 | ✅ PASS | g_allow=1.0000, g_deny=1.0000, g_hold=1.0000, g_margin=0.9500 | 800/800 (100%) | 125/125 | 10.5281/zenodo.21433461 |
| ARK-475 | Dependency Loss | 8×100=800 | ✅ PASS | g_allow=1.0000, g_hold_min=1.0000, g_margin=0.9500 | 800/800 (100%) | 150/150 | 10.5281/zenodo.21433463 |
| ARK-476 | Cross-Context Replay | 8×100=800 | ✅ PASS | g_allow=1.0000, g_deny_min=1.0000, g_margin=0.9500 | 800/800 (100%) | 150/150 | 10.5281/zenodo.21433465 |
| ARK-477 | Human Escalation | 8×100=800 | ✅ PASS | g_allow_no_esc=1.0000, g_allow_approved=1.0000, g_hold_min=1.0000, g_margin=0.9500 | 800/800 (100%) | 100/100 | 10.5281/zenodo.21433469 |

**Series metrics:** 4,000 decisions, 4,000/4,000 concordance, 1,125 kill-gate wrong-allows detected

### API Rate Limit (ARK-478–482)
Testing exact-action binding and 4 critical failure modes for API rate limit authorization.

| ARK | Failure Mode | Arms×Scenarios | Verdict | g_metrics | Concordance | Kill-Gate | DOI |
|-----|--------------|----------------|---------|-----------|-------------|-----------|-----|
| ARK-478 | Exact-Action Binding | 8×100=800 | ✅ PASS | g_allow=1.0000, g_deny_min=1.0000, g_margin=1.0000 | 800/800 (100%) | 600/600 | 10.5281/zenodo.21433473 |
| ARK-479 | Revocation At Execution | 8×100=800 | ✅ PASS | g_allow=1.0000, g_deny=1.0000, g_hold=1.0000, g_margin=0.9500 | 800/800 (100%) | 125/125 | 10.5281/zenodo.21433476 |
| ARK-480 | Dependency Loss | 8×100=800 | ✅ PASS | g_allow=1.0000, g_hold_min=1.0000, g_margin=0.9500 | 800/800 (100%) | 150/150 | 10.5281/zenodo.21433479 |
| ARK-481 | Cross-Context Replay | 8×100=800 | ✅ PASS | g_allow=1.0000, g_deny_min=1.0000, g_margin=0.9500 | 800/800 (100%) | 150/150 | 10.5281/zenodo.21433483 |
| ARK-482 | Human Escalation | 8×100=800 | ✅ PASS | g_allow_no_esc=1.0000, g_allow_approved=1.0000, g_hold_min=1.0000, g_margin=0.9500 | 800/800 (100%) | 100/100 | 10.5281/zenodo.21433485 |

**Series metrics:** 4,000 decisions, 4,000/4,000 concordance, 1,125 kill-gate wrong-allows detected

### P01 Series Total Metrics
- **Total experiments:** 25
- **Total decisions tested:** 20,000
- **Verdicts:** 25 PASS (100%)
- **Dual-guard concordance:** 20,000/20,000 (100%)
- **Kill-gate falsifiability:** 5,306 wrong-allows detected across all experiments (100% falsifiable)
- **RF Standing Covenant compliance:** 25/25 (100%)

---

## P02 LATENCY/THROUGHPUT SERIES (ARK-483–492)
**Status:** 2/10 complete
**Substrate:** Classical software (frozen ARK-458 guard as CUT)

| ARK | Question | Verdict | Metrics | DOI |
|-----|----------|---------|---------|-----|
| ARK-483 | Verification Decision — Latency | ✅ PASS | V2 Py p95: 1.822µs, V1 JS p95: 0.652µs (ceiling: 1000µs) | 10.5281/zenodo.21432647 |
| ARK-484 | Verification Decision — Burst Throughput | ✅ PASS | V2 Py: 1,657,281 dec/sec (16.6× pred), V1 JS: 4,524,798 dec/sec (30.2× pred) | 10.5281/zenodo.21433111 |
| ARK-485 | Verification Decision — Sustained Throughput | ⏳ PENDING | | |
| ARK-486 | Verification Decision — Cost At Scale | ⏳ PENDING | | |
| ARK-487 | Authority Engine — Cold Start | ⏳ PENDING | | |
| ARK-488 | Authority Engine — P95 Latency | ⏳ PENDING | | |
| ARK-489 | Authority Engine — Burst Throughput | ⏳ PENDING | | |
| ARK-490 | Authority Engine — Sustained Throughput | ⏳ PENDING | | |
| ARK-491 | Authority Engine — Cost At Scale | ⏳ PENDING | | |
| ARK-492 | Evidence Engine — Cold Start | ⏳ PENDING | | |

---

## COMPREHENSIVE TALLIES

### By Series
| Series | Experiments | Cases/Records | PASS | FAIL | GATE-STOP | Published |
|--------|-------------|---------------|------|------|-----------|-----------|
| ARK Hardware (441–448) | 9 | 9 | 7 | 1 | 1 | 9/9 ✓ |
| ARK Classical Pre-P01 (449–457) | 10 | 10 | 9 | 1 | 0 | 10/10 ✓ |
| ARK P01 Production (458–482) | 25 | 25 | 25 | 0 | 0 | 25/25 ✓ |
| ARK P02 Latency/Throughput (483–484) | 2 | 2 | 2 | 0 | 0 | 2/2 ✓ |
| WITNESS Series (1–2) | 2 | 6 | 6 | 0 | 0 | 2/2 ✓ |
| **TOTAL** | **48** | **52** | **49** | **2** | **1** | **48/48 ✓** |

### ARK Series Summary
- **Total ARK experiments:** 28 unique IDs (46 records including retests)
- **PASS:** 26 experiments (43 records)
- **FAIL (honest):** 2 experiments (ARK-445, ARK-455) — both have PASS retests (445b, 455b)
- **GATE-STOP:** 1 experiment (ARK-448)
- **Published to Zenodo:** 28/28 (100%)

### Overall RF Corpus (as of 2026-07-18)
- **Total experiments:** 30 unique IDs
- **Total case records:** 52
- **PASS records:** 49
- **FAIL records:** 2 (honest, standing)
- **GATE-STOP records:** 1
- **Zenodo publications:** 48/48 complete with DOI badges (100%)

---

## METHODOLOGICAL INTEGRITY

### Standing Covenant Compliance
All 52 case records maintain full compliance:
1. ✅ Preregistered questions, arms, metrics, thresholds
2. ✅ Pre-execution LOCK records (MANIFEST.txt + SHA-256 hashes)
3. ✅ All outcomes preserved (PASS/FAIL/HOLD/GATE-STOP)
4. ✅ Honest findings disclosure (ARK-483 DENY-latency, ARK-484 performance exceeding predictions)
5. ✅ No post-hoc criterion changes
6. ✅ No rescue-after-failure
7. ✅ Full provenance (GitHub commits + Zenodo DOIs)
8. ✅ Kill-gate/effectiveness-gate mandatory

### Honest Findings Examples
- **ARK-445:** Tri-state FAIL → honest FAIL stands, ARK-445b clean retest PASS
- **ARK-455:** ProofRecord tamper FAIL → honest FAIL stands, ARK-455b corrected PASS
- **ARK-448:** Dynamical decoupling GATE-STOP → execution blocked, no verdict
- **ARK-483:** DENY slower than ALLOW (reason-string formatting overhead) → disclosed
- **ARK-484:** Performance exceeded predictions by 16.6× (Py) and 30.2× (JS) → disclosed

---

## REPOSITORY STRUCTURE

### Primary Repositories
- **executionproof-testbeds:** https://github.com/derekhone/executionproof-testbeds
  - ARK-441 through ARK-482, ARK-483, ARK-484
  - All P01 and P02 experiments
  - Main branch SHA: `293c326` (latest: DOI badges for ARK-468-482)

- **witness-testbeds:** https://github.com/derekhone/witness-testbeds
  - WITNESS-1, WITNESS-2
  - Quantum-sourced nonce provenance experiments
  - Main branch SHA: `533c569`

### Zenodo Collections
- **ARK Series Concept DOI:** [10.5281/zenodo.21398675](https://zenodo.org/record/21398675)
- **WITNESS Series Concept DOI:** [10.5281/zenodo.21424323](https://zenodo.org/record/21424323)

---

## NEXT EXPERIMENTS (Roadmap)

### Immediate P02 Queue (Priority P0)
- ARK-485 through ARK-492: Complete latency/throughput/cost measurements
  - Authority Engine performance (cold start, p95 latency, burst/sustained throughput, cost at scale)
  - Evidence Engine performance

### P03 Dependency Cascade (ARK-493–517)
- Identity Provider failure modes (full outage, timeout, stale cache, split brain, recovery)
- Policy Registry failure modes (full outage, timeout, stale cache, split brain, recovery)

### Future Series (P04–P10+)
- See Remnant_Fieldworks_Next_500_Experiment_Roadmap.md for full 500-experiment architecture

---

## INFRASTRUCTURE STATUS

### GitHub
- **Repository:** executionproof-testbeds
- **Branch:** main (SHA: 293c326)
- **Open PRs:** 0
- **Authentication:** GitHub token available via Git_Tool

### Zenodo
- **Token:** Available (REDACTED_ZENODO_TOKEN)
- **Publications:** 48/48 complete
- **Latest batch:** ARK-468-482 (15 DOIs published 2026-07-18)

### IBM Quantum
- **Budget status:** ~0s or minimal after WITNESS-2
- **Last QPU use:** WITNESS-2 (job d9di7nkinv1c73ap4ed0, 2026-07-18)
- **Backend:** ibm_fez (156q Heron r2)

---

## PHASE STATUS

### COMPLETED PHASES
1. ✅ **Synthetic Exploration Phase** (ARK-441–457): 19 experiments
2. ✅ **P01 Production-Boundary Phase** (ARK-458–482): 25 experiments — **COMPLETE 2026-07-18**

### ACTIVE PHASES
3. 🔄 **P02 Latency/Throughput Phase** (ARK-483–492): 2/10 complete

### PLANNED PHASES
4. ⏳ **P03 Dependency Cascade** (ARK-493–517)
5. ⏳ **P04+ Extended Testing** (ARK-518+)

---

**Document Version:** 2.0 (2026-07-18)
**Maintained by:** Remnant Fieldworks Inc.
**Last Corpus Update:** P01 complete (25/25 experiments PASS, all published)
