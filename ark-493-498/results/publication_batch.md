# Publication Batch — ARK-493 → ARK-498 Series

**Prepared for:** Remnant Fieldworks Inc. — ExecutionProof program
**Source of truth:** this series' run artifacts (`results/`, `proofrecords/`, `ledgers/`) + reconciled corpus totals in `reconciliation_report.md`
**Framing rule:** every public number below is the **reconciled post-series total**; negative results (FAIL, GATE-STOP) are reported, not suppressed.

**Reconciled public headline numbers (use everywhere):**
**72 preregistered experiments · 232 case records · 229 PASS · 2 FAIL · 1 GATE-STOP · 10 repositories.**
This series (ARK-493–498) contributed 6 experiments and 161 scored cases, all PASS, with 0 new FAIL and 0 GATE-STOP.

---

## 1. GitHub README text (drop-in section)

```markdown
## ExecutionProof — Enterprise Agent Boundary Testbed (ARK-493 → ARK-498)

ExecutionProof enforces **proof before power**: an autonomous agent's tool call
executes only after an independent gate has verified actor identity, live
authority, evidence, policy version, system state, and exact-action integrity —
and every decision is written to a signed, hash-chained, independently
reconstructable ProofRecord. Fail-closed is the default; failures are preserved,
never retried until they pass.

### This series at a glance (frozen preregistration v1.1)

| Experiment | Focus | Result |
|-----------|-------|--------|
| ARK-493 | Enforcement boundary under adversarial load (6 paths × 15 cells) | PASS — 90/90 |
| ARK-494 | Semantic boundary: deep argument mutation | PASS — 13/13 |
| ARK-495 | Temporal boundary: authority change mid-flight | PASS — 11/11 |
| ARK-496 | Multi-agent delegation & self-approval defense | PASS — 8/8 |
| ARK-497 | Independently reconstructable ProofRecord (+ tamper detection) | PASS — 30/30 |
| ARK-498 | Networked production-like performance | PASS — 6/6 hard criteria |

- **161 scored cases this series, 161 PASS, 0 FAIL, 0 enforcement leaks.**
- **Dual-guard verification:** an in-process Guard-A and an *isolated-subprocess*
  Guard-B independently verified all 161 scored records and agreed on every one.
- **ARK-497:** an isolated verifier (permitted imports only, statically proven to
  import nothing from the application) reconstructed all 9 decision elements for
  20 legitimate records and detected **10/10** single-field tamper attempts with
  **0** false positives.
- **ARK-498:** behind a real HTTP/loopback-TCP boundary (~1,810 requests), the
  gate held fail-closed under policy/authority/store failure (**leak count 0**),
  executed **zero** duplicate side effects, produced **100%** complete and
  signature-verifiable ProofRecords, and recovered cleanly with **no** automatic
  re-execution of denied requests.

### Standing corpus (reconciled, all series to date)

**72 preregistered experiments · 232 case records · 229 PASS · 2 FAIL ·
1 GATE-STOP · 10 repositories.** The 2 FAIL and 1 GATE-STOP records are retained
unchanged — preserving negative results is part of the methodology.

### Reproduce

```bash
pip install -r requirements.txt
python3 run_all.py     # verifies the frozen preregistration hash, then runs 493→498
```

Preregistration: `preregistration/ARK-493-498-PREREGISTRATION-v1.1.md`
SHA-256 `464b9fb8be9d6cca052f236dc9deec9f8e89b781cafc58701e79b2d05d52952a`.
```

> **Performance note for the README/badge:** ARK-498 latency/throughput figures
> are labeled *PRODUCTION-LIKE OVERHEAD CHARACTERIZATION · NOT A BENCHMARK
> CERTIFICATION · NOT A PRODUCTION SLA*. Do not publish them as an SLA.

---

## 2. Zenodo deposition draft

**Title:** ExecutionProof Enterprise Agent Boundary Testbed — ARK-493 through ARK-498 (Frozen Preregistration v1.1)

**Authors:** Remnant Fieldworks Inc., ExecutionProof Program

**Version:** 1.0 (series ARK-493–498)

**Resource type:** Software / Dataset (preregistered experiment suite + evidence artifacts)

**Description:**
> This deposition contains the frozen preregistration (v1.1), the complete testbed source, and the full evidence artifacts for six preregistered experiments (ARK-493 through ARK-498) characterizing the enforcement boundary of the ExecutionProof agent-authorization gate. The gate verifies six dimensions (actor identity, live authority, evidence, policy version, system state, exact-action integrity) and emits ALLOW / DENY / HOLD, recording every decision in a signed, hash-chained, independently reconstructable ProofRecord.
>
> Results (single reproducible run, preregistration hash verified at execution): 161 scored cases, 161 PASS, 0 FAIL, 0 enforcement leaks; dual-guard (in-process + isolated-subprocess) agreement on all 161 records. ARK-497 demonstrates independent reconstruction of all nine decision elements and 10/10 single-field tamper detection with zero false positives by a verifier statically proven to import nothing from the application. ARK-498 characterizes production-like overhead behind a real HTTP/loopback-TCP boundary (~1,810 requests) and meets all six frozen hard criteria: fail-closed leak count 0, zero duplicate executions, 100% ProofRecord completeness, clean error accounting, recovery with no automatic re-execution of denied requests, and 100% independent signature verification.
>
> Latency/throughput data are explicitly published as *production-like overhead characterization*, not a benchmark certification and not a production SLA, and must not be compared to the prior in-process microsecond testbed (ARK-483–492).
>
> Standing reconciled corpus across all series to date: 72 preregistered experiments, 232 case records, 229 PASS, 2 FAIL, 1 GATE-STOP, across 10 repositories. Negative results (FAIL, GATE-STOP) are retained unchanged.

**Keywords:** AI agent safety, authorization gate, fail-closed enforcement, proof-carrying decisions, hash chain, ed25519, tamper detection, preregistration, reproducibility

**License:** as per program policy (to be confirmed at deposition).

**Files:** `preregistration/`, testbed source tree, `proofrecords/proofrecord_chain.jsonl`, `ledgers/`, `results/` (results ledger, reconciliation report, ARK-498 performance report, execution manifest, verifier outputs).

**Related identifiers:** supersedes preregistration v1.0 (SHA-256 `deb9c43ee252ecd9cb217788f783ebf6fd7113883170749fedaa1509425406ce`).

---

## 3. Evidence-page update (executionproof.io / builderexecutionproof.io)

Replace the standing evidence summary block on **both** executionproof.io and builderexecutionproof.io with:

> ### Evidence corpus (updated — ARK-493 → ARK-498 series added)
>
> **72 preregistered experiments · 232 case records · 229 PASS · 2 FAIL · 1 GATE-STOP · 10 repositories.**
>
> The latest series (ARK-493–498) added six experiments and 161 scored cases, all PASS, with zero enforcement leaks and independent dual-guard verification on every record. The 2 FAIL and 1 GATE-STOP records from prior series are retained unchanged — we publish negative results because preserving them is what makes the corpus trustworthy.
>
> Highlights: independent tamper detection 10/10 with 0 false positives (ARK-497); fail-closed under dependency loss with leak count 0 and 100% independently signature-verifiable proofs in a production-like networked run (ARK-498). ARK-498 latency/throughput figures are published as production-like overhead characterization — **not a benchmark certification and not a production SLA.**
>
> #### Intellectual-property status (corrected)
> ExecutionProof is covered by **48 provisional patent applications (filed January 2026) and 8 pending nonprovisional utility applications — 56 total USPTO filings.**

**Patent-line correction note (for the site editor):** the prior evidence page understated the filing count. The correct, current line — to appear on both executionproof.io and builderexecutionproof.io — is exactly:

> *48 provisional applications (filed Jan 2026) and 8 pending nonprovisional utility applications = 56 total USPTO filings.*

---

## 4. Consistency checklist before publishing

- [x] Public headline uses reconciled **post-series** totals (72 / 232 / 229 / 2 / 1 / 10), not this-series-only numbers.
- [x] FAIL (2) and GATE-STOP (1) reported, not hidden.
- [x] ARK-498 performance carries the mandatory characterization label and no SLA claim.
- [x] No comparison drawn to ARK-483–492 microsecond testbed.
- [x] Patent line corrected to **56 total USPTO filings (48 provisional filed Jan 2026 + 8 pending nonprovisional utility)** on both domains.
- [x] Preregistration SHA-256 cited and verified at run time.
- [x] Every claimed number traces to a run artifact under `results/`, `proofrecords/`, or `ledgers/`.
