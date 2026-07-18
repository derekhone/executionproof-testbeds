# Remnant Fieldworks Inc. — Master Summary
## Science Research · Patents · Trademarks

**Prepared:** 2026-07-18 · **Maintained by:** Remnant Fieldworks Inc. · **Sole inventor/author:** Derek Adam Hone
**Team:** Derek Hone (Founder) + Adith Kadam Ramesh (Systems Engineer)
**Contact:** derek@ownerremnantfieldworks.com

> *Proof Before Power™ — built to a world-class standard, for Christ.*

---

## 0. How to read this document

This is the single reconciled record of everything Remnant Fieldworks (RF) has **proven** (science), everything RF has **filed to protect** (patents), and everything RF has **claimed as a mark** (trademarks). It is written to the RF Standing Covenant: claims are kept **narrower than the evidence**, failures and gate-stops are **preserved honestly**, and every experimental result is traceable to a public GitHub commit and a Zenodo DOI.

Three reinforcing pillars govern the whole program:

> **The experiments build evidence and credibility. The patents protect invention. The pilots prove customer value.**
> All three reinforce one another without overstating what any one establishes.

---

# PART I — SCIENCE RESEARCH

RF's public scientific corpus spans **five research programs**, all preregistered, executed, and published with raw-data provenance (GitHub + Zenodo DOI, CC BY 4.0).

| Program | Theme | Substrate | Status |
|---|---|---|---|
| **ARK** | ExecutionProof authorization boundary (Verification Before Execution) | Quantum hardware (441–448) + classical software (449–492) | 38 experiment IDs, 60 records — active |
| **WITNESS** | Quantum-sourced authorization nonces with verifiable provenance | IBM quantum hardware (`ibm_fez`) | 2 experiments, 6 cases — complete + published |
| **BELLWETHER** | Nonclassicality (Bell/Mermin/contextuality) witness bound into a nonce | IBM quantum hardware (`ibm_fez`) | 3 experiments — complete + published |
| **CHRONO** | Temporal nonclassicality (Leggett–Garg) witness bound into a nonce | IBM quantum hardware (`ibm_fez`) | 1 experiment — complete + published |
| **UIP Phase 1** | Foundational physics program (precursor) | — | Closed |

**Corpus totals (ARK + WITNESS, reconciled 2026-07-18):** 60 case records across 38 experiment IDs → **57 PASS · 2 honest FAIL · 1 GATE-STOP**, **56/56 Zenodo publications complete (100%)**. P02 Latency/Throughput/Scale (ARK-483–492) complete 10/10. The BELLWETHER (3) and CHRONO (1) quantum-witness experiments are additionally published (4 more DOIs).

---

## 1. ARK Series — ExecutionProof Authorization Boundary

**Core claim tested (VBE):** *Permission at approval time is not permission at execution time.* Authorization must be re-verified against current state at the **moment of execution**.

### 1.1 Hardware Quantum ARKs (ARK-441–448) — 9 records
Backends: ARK-441 `ibm_kingston`; ARK-442–448 `ibm_marrakesh` (all 156-qubit Heron r2).

| ARK | Question | Verdict | DOI |
|---|---|---|---|
| 441 | VBE authorization boundary baseline | ✅ PASS | 10.5281/zenodo.21404867 |
| 442 | Delay / expiry boundary (stale authority fails closed) | ✅ PASS | 10.5281/zenodo.21404867 |
| 443 | Two-of-three quorum (single compromised authorizer) | ✅ PASS | 10.5281/zenodo.21404867 |
| 444 | Decision-to-execution integrity (tampered action caught) | ✅ PASS | 10.5281/zenodo.21404867 |
| 445 | Tri-state ALLOW/HOLD/DENY | ❌ FAIL (honest) | 10.5281/zenodo.21404867 |
| 445b | Reset-free re-test | ✅ PASS | 10.5281/zenodo.21418404 |
| 446 | Cross-device replication | ✅ PASS | 10.5281/zenodo.21404867 |
| 447 | Pauli twirling vs baseline | ✅ PASS | 10.5281/zenodo.21404867 |
| 448 | Dynamical decoupling vs baseline | ⛔ GATE-STOP | 10.5281/zenodo.21404867 |

*Honest-record note: ARK-446 has no MANIFEST.txt in the repo (only RESULTS.pdf + PREREGISTRATION.pdf were deposited). Preserved as-executed.*

### 1.2 Classical / Software ARKs, pre-P01 (ARK-449–457) — 10 records
Substrate: pure classical software.

| ARK | Question | Verdict | DOI |
|---|---|---|---|
| 449 | State change after verification | ✅ PASS | 10.5281/zenodo.21406335 |
| 450 | Verified-action substitution attack | ✅ PASS | 10.5281/zenodo.21420310 |
| 451 | Authority revocation during execution | ✅ PASS | 10.5281/zenodo.21419480 |
| 452 | Multi-step workflow, one invalid step | ✅ PASS | 10.5281/zenodo.21406668 |
| 453 | Conflicting evidence must HOLD | ✅ PASS | 10.5281/zenodo.21419198 |
| 454 | Self-approval & circular delegation | ✅ PASS | 10.5281/zenodo.21418935 |
| 455 | ProofRecord tamper (dual-verifier) | ❌ FAIL (honest) | 10.5281/zenodo.21418388 |
| 455b | ProofRecord tamper — corrected retest | ✅ PASS | 10.5281/zenodo.21418404 |
| 456 | Fail-closed dependency loss | ✅ PASS | 10.5281/zenodo.21420107 |
| 457 | Cross-context authorization replay | ✅ PASS | 10.5281/zenodo.21421742 |

### 1.3 P01 Production-Boundary Series (ARK-458–482) — ✅ COMPLETE
**25/25 experiments PASS.** Real, end-to-end authorization boundaries across 5 action domains × 5 failure modes. Dual independent guards (V1 JavaScript + V2 Python).

| # | Series (action tuple) | ARKs | Verdicts | DOIs (version) |
|---|---|---|---|---|
| 1 | **Cloud IAM Role Grant** `(principal, role, resource_arn, account, grant_action)` | 458–462 | 5 PASS | 21432645, 21432879, 21432883, 21432887, 21432889 |
| 2 | **Production Deployment** `(service, environment, version, deploy_type, approver)` | 463–467 | 5 PASS | 21433070, 21433072, 21433074, 21433077, 21433081 |
| 3 | **Database Destructive Query** `(database, table, operation, schema_ver, exec_mode)` | 468–472 | 5 PASS | 21433449, 21433451, 21433453, 21433455, 21433457 |
| 4 | **Financial Transaction** `(from, to, amount, currency, txn_type)` | 473–477 | 5 PASS | 21433459, 21433461, 21433463, 21433465, 21433469 |
| 5 | **API Rate Limit** `(api_key, endpoint, rate_limit, window, tier)` | 478–482 | 5 PASS | 21433473, 21433476, 21433479, 21433483, 21433485 |

Each series tests the same 5 failure modes: **Exact-Action Binding · Revocation At Execution · Dependency Loss · Cross-Context Replay · Human Escalation.**

**P01 aggregate metrics:**
- Total decisions tested: **20,000**
- Verdicts: **25 PASS (100%)**
- Dual-guard concordance: **20,000 / 20,000 (100%)**
- Kill-gate falsifiability: **5,306 / 5,306 wrong-allows detected (100%)**
- All gate metrics met: g_allow = 1.0000, g_deny/hold_min = 1.0000, g_margin ≥ 0.9500

### 1.4 P02 Latency / Throughput / Scale Series (ARK-483–492) — ✅ 10/10 COMPLETE
CUT = frozen ARK-458 guard (Verification Decision) + minimal in-memory reference Authority/Evidence engines (measurement only, **not** production engines).

| ARK | Question | Verdict | Result | DOI |
|---|---|---|---|---|
| 483 | Verification decision — latency | ✅ PASS | worst-path p95 **1.822 µs** (Py) / **0.652 µs** (JS); ceiling 1000 µs | 10.5281/zenodo.21432647 |
| 484 | Verification decision — burst throughput | ✅ PASS | **1.66M dec/s** (Py, 16.6× pred) / **4.52M dec/s** (JS, 30.2× pred) | 10.5281/zenodo.21433111 |
| 485 | Verification decision — sustained throughput | ✅ PASS | **1.50M dec/s** (Py) / **9.52M dec/s** (JS), 100% acc over 60s | 10.5281/zenodo.21434398 |
| 486 | Verification decision — cost at scale | ✅ PASS | **fixed prior FAIL**; Scenario B realistic **$7.47e-06/M** (Py) / **$1.18e-06/M** (JS); naive $0.20/M disclosed | 10.5281/zenodo.21434400 |
| 487 | Authority Engine — cold start | ✅ PASS | p95 **9.34 ms** (mean 7.87 ms); correctness gate PASS | 10.5281/zenodo.21434402 |
| 488 | Authority Engine — p95 latency | ✅ PASS | warm p95 **0.32 µs**, p99 0.41 µs (200k decisions) | 10.5281/zenodo.21434405 |
| 489 | Authority Engine — burst throughput | ✅ PASS | **3.09M dec/s**, 100% acc | 10.5281/zenodo.21434407 |
| 490 | Authority Engine — sustained throughput | ✅ PASS | **2.49M dec/s** over 60s, 100% acc (~81% of burst) | 10.5281/zenodo.21434409 |
| 491 | Authority Engine — cost at scale | ✅ PASS | Scenario B **$3.59e-06/M**; naive $0.20/M disclosed | 10.5281/zenodo.21434411 |
| 492 | Evidence Engine — cold start | ✅ PASS | p95 **44.0 ms**; tamper + broken-chain correctly DENY | 10.5281/zenodo.21434413 |

*Honest findings: (a) DENY slower than ALLOW in ARK-483 (reason-string formatting dominates tail). (b) ARK-486 corrected a cost-model category error (per-request serverless price per in-process decision) → verdict on realistic running-service model, naive bound disclosed. (c) ARK-487–492 measure minimal in-memory reference engines, not production engines; claims bounded to single-threaded in-memory load. All disclosed.*

---

## 2. WITNESS Series — Quantum-Sourced Authorization Nonces
Repo: `github.com/derekhone/witness-testbeds` · Concept DOI 10.5281/zenodo.21424323

| Exp | Title | Hardware | Result | DOI (version) |
|---|---|---|---|---|
| WITNESS-1 | Quantum-sourced nonces with verifiable provenance | `ibm_fez` (Heron r2), job `d9dgp6kjeosc73fhigsg`, 4000 shots, 256 unique outcomes | 3/3 PASS (honest verify · tamper detect · replay prevention) | 10.5281/zenodo.21424324 |
| WITNESS-2 | Length-prefixed nonce with record-hash field integrity | `ibm_fez`, job `d9di7nkinv1c73ap4ed0`, 4000 shots, 256 unique outcomes | 3/3 PASS (9-check honest verify · 4/4 tamper · cross-context replay) | 10.5281/zenodo.21425381 |

WITNESS-2 `quantum_nonce` = `e425dc92…659b`; `record_hash` = `271ff5ea…7ae1`.

---

## 3. BELLWETHER Series — Nonclassicality Witness Bound Into a Nonce
Repo: `github.com/derekhone/bellwether-testbeds`. Physical nonclassicality (spatial/measurement) cryptographically bound into an authorization nonce/ProofRecord as a tamper-evident entropy witness.

| Exp | Witness | Bound | Measured | Hardware | DOI (version) |
|---|---|---|---|---|---|
| BELLWETHER-1 | Bipartite **CHSH** | classical ≤2; Tsirelson 2.828 | **S = 2.514** (>3σ) | `ibm_fez`, job `d9dje2cjeosc73fhm230`, 4000 shots | 10.5281/zenodo.21430442 |
| BELLWETHER-2 | Multipartite **Mermin-3** (GHZ) | classical ≤2; quantum max 4 | **\|M\| = 3.423** (n_σ ≈ 61.6) | `ibm_fez`, job `d9dno91htsac739da4d0`, 8000 shots | 10.5281/zenodo.21430446 |
| BELLWETHER-3 | State-independent **contextuality** (Peres–Mermin) | noncontextual ≤4; quantum 6 | **χ = 5.268–5.376** across 3 states (all >4, all 3σ) | `ibm_fez`, job `d9do1s1htsac739dahpg`, 18000 shots | 10.5281/zenodo.21430451 |

Authorization-model arc: BW1 bipartite → BW2 multipartite (unforgeable by any pair) → BW3 state-robust (holds regardless of preparation). **BW3 is the broadest / most patent-worthy** of the family (state-robust authorization).

---

## 4. CHRONO Series — Temporal Nonclassicality Witness
Repo: `github.com/derekhone/chrono-testbeds`. Three-time **Leggett–Garg** inequality K3 on a single qubit, bound into an authorization ProofRecord — maps directly to "Verification Before Execution" in the time dimension.

| Exp | Bound | Measured | Hardware | DOI (version) |
|---|---|---|---|---|
| CHRONO-1 | macrorealist K3 ≤ 1; quantum (Lüders) max 1.5 | **K3 = 1.450** (>3σ, 97% of ideal) | `ibm_fez`, job `d9dkj6ineu4c739nddrg`, 6000 shots | 10.5281/zenodo.21430455 |

Together the quantum-witness programs span **all three nonclassicality families**: nonlocality (BW1/BW2), contextuality (BW3), and temporality (CHRONO).

---

## 5. Scientific integrity boundary (carried into every artifact)
- Results apply to the **specific backends, qubit pairs, calibration snapshots, shot counts, and parameters** used.
- These are hardware noise-characterization studies and software-harness tests — **not cryptographic security proofs**.
- Error **mitigation** is not error **correction** (no QEC).
- Quantum witnesses (BELLWETHER/CHRONO) are **device-dependent**; locality, detection, compatibility, and clumsiness loopholes remain **open**. Not loophole-free; not device-independent certified randomness.
- Honest FAILs (ARK-445, ARK-455) and the ARK-448 GATE-STOP **stand** alongside clean retests — that preserved record is itself the credibility asset.

---

# PART II — PATENTS

**Portfolio scale (as of 2026-07-18): 56 USPTO filings.** Derek Adam Hone is **sole inventor**.

| Layer | Count | Detail |
|---|---|---|
| Nonprovisional utility | **8** | Parent **19/529,283** (filed Feb 4, 2026) + **7 continuations-in-part** (filed Feb–Jul 2026) |
| Provisional | **48** | 47 provisionals filed Jan 10–12, 2026 + **Commercial Gate 63/971,820** (Jan 30, 2026) |
| **Total** | **56** | Priority for the classical governance / crypto / authorization stack locked **before** any quantum publication |

### 2.1 Named patent-family connections (evidence ↔ invention)
- **No-self-approval patent** — supported by the ARK-454 experimental design (self-approval, delegated, and circular delegation protection).
- **ProofRecord™ integrity** — ARK-455 / ARK-455b directly tested tamper-resistance of the machine-readable, independently verifiable decision record.
- **Three-state control model (ALLOW / HOLD / DENY)** — HOLD as a first-class conservative outcome, evidenced by ARK-445 / ARK-445b (HOLD metrologically separable from ALLOW and DENY).
- **Fail-closed dependency handling, exact-action binding, context binding** — evidenced across ARK-456, ARK-457, and the full P01 production series.

### 2.2 How experiments support the patent program (and the hard limit)
Experiments create **dated evidence that disclosed systems actually work** — mapping real implementations to existing claims, surfacing narrower dependent-claim opportunities, and distinguishing **working examples** from **prophetic examples**.

> **HARD LIMIT:** An experiment performed *after* filing **cannot repair missing disclosure or add new matter** to an existing application. New matter needs a **continuation-in-part or a new application** with its own later priority date. Actual results are always labeled **working examples** — never implied to have existed at an earlier filing date.

### 2.3 Quantum IP — 12-month defensive-publication posture
The classical stack is protected by the filed provisionals/nonprovisionals above (priority locked before any quantum disclosure). Because budget cannot afford additional filings right now, the quantum layer (**WITNESS, BELLWETHER, CHRONO**) switched to **defensive publication**: a timestamped Zenodo DOI = prior art protecting freedom to operate, at zero cost.

> **Doctrine: "File-first when we can; publish-to-protect when we can't."**

- All quantum publications dated **2026-07-18** → **US grace-period deadline 2027-07-18** (practical cutoff ~2027-06-18). Ex-US rights are likely already barred by publication.
- If exactly one filing is made: a single **small-entity US provisional on the genus** (any-nonclassicality-witness-bound authorization nonce), with **BELLWETHER-3 (contextuality) as lead example** — the broadest, state-robust claim.
- This cannot be bolted onto 19/529,283 (would be new matter) — it needs its own provisional/CIP.
- Full tracking: `RF-Quantum-IP-File-Within-12-Months-Ledger.md` (+ PDF/DOCX).

### 2.4 The IP Gate (run before every public disclosure)
Before anything goes to GitHub / Zenodo / LinkedIn / RF-100, each result must pass:
1. Does it merely demonstrate something **already disclosed** in a filed application? → safe to publish (working-example evidence).
2. Does it reveal an **improvement / new configuration / unexpected result**? → potential new matter.
3. Is that improvement **already supported by a pending application**? → if yes, publish; if no, treat as unprotected.
4. Should we **file before publishing**? → if new matter, **YES**.
5. Can we **publish the result while withholding unnecessary implementation details**?

---

# PART III — TRADEMARKS

**Corrected, authoritative status (Derek, 2026-07-18):** five marks are the subject of **filed, pending federal trademark applications** with the USPTO. Use the ™ symbol; do **not** imply registration (®) until the USPTO grants.

| Mark | Role | Status |
|---|---|---|
| **Remnant Fieldworks™** | Company | Pending federal TM application |
| **ExecutionProof™** | Commercial platform (VBE doctrine) | Pending federal TM application |
| **Proof Before Power™** | Doctrine / brand line | Pending federal TM application |
| **Verification Before Execution™** | Framework | Pending federal TM application |
| **ProofRecord™** | Branded, machine-readable decision artifact | Pending federal TM application |
| **VaultProof™** | Implementation layer | **Common-law mark only** — NOT a filed federal application |

**Language discipline:** describe the first five as *"pending federal trademark applications"* with ™. For **VaultProof™**, only ever claim **common-law** use — never write "filed" or "registered ®" until a separate filing is confirmed.

---

# PART IV — COMPANY ARCHITECTURE & INFRASTRUCTURE

### Stable architecture
- **Remnant Fieldworks™** — company (pending TM)
- **Proof Before Power™** — doctrine (pending TM)
- **Verification Before Execution™** — framework (pending TM)
- **ExecutionProof™** — commercial platform, proprietary (pending TM)
- **ProofRecord™** — branded artifact, proprietary (pending TM)
- **VaultProof™** — implementation layer (common-law)
- **RF-100** — implementation-neutral, publicly reviewable standard: https://conceptradar.notion.site/RF-100-4cf29f7e8ad84cddbe7dea7c4126e94c

### Public repositories
| Repo | Program | Status |
|---|---|---|
| `executionproof-testbeds` | ARK corpus (canonical) | Live, main |
| `witness-testbeds` | WITNESS 1–2 | Complete + published |
| `bellwether-testbeds` | BELLWETHER 1–3 | Complete + published |
| `chrono-testbeds` | CHRONO-1 | Complete + published |
| `vaultproof-agent-guard` | VaultProof implementation | Live (PR #4 open) |
| `uip-phase1-testbeds` | UIP Phase 1 | Closed |

### Concept DOIs
- ARK concept: 10.5281/zenodo.21398675
- WITNESS concept: 10.5281/zenodo.21424323
- BELLWETHER concept: 10.5281/zenodo.21430441 (BW1) / 21430445 (BW2) / 21430450 (BW3)
- CHRONO concept: 10.5281/zenodo.21430454

### Provenance model
Commits are timestamped but **not** GPG/SSH-signed. Provenance = public commit history + MANIFEST SHA-256 preregistration locks + Zenodo DOIs. VaultProof app-layer ed25519 ProofRecord signatures are distinct from git commit signing.

---

# PART V — CONSOLIDATED SCOREBOARD

| Program | Experiments | Records | PASS | FAIL | GATE-STOP | Published |
|---|---|---|---|---|---|---|
| ARK Hardware (441–448) | 9 | 9 | 7 | 1 | 1 | 9/9 ✓ |
| ARK Classical pre-P01 (449–457) | 10 | 10 | 9 | 1 | 0 | 10/10 ✓ |
| ARK P01 Production (458–482) | 25 | 25 | 25 | 0 | 0 | 25/25 ✓ |
| ARK P02 Latency/Throughput/Scale (483–492) | 10 | 10 | 10 | 0 | 0 | 10/10 ✓ |
| WITNESS (1–2) | 2 | 6 | 6 | 0 | 0 | 2/2 ✓ |
| **ARK+WITNESS subtotal** | **56** | **60** | **57** | **2** | **1** | **56/56 ✓** |
| BELLWETHER (1–3) | 3 | 3 | 3 | 0 | 0 | 3/3 ✓ |
| CHRONO (1) | 1 | 1 | 1 | 0 | 0 | 1/1 ✓ |
| **GRAND TOTAL** | **60** | **64** | **61** | **2** | **1** | **60/60 ✓** |

**IP totals:** 56 USPTO patent filings · 5 pending federal trademarks + 1 common-law mark.

---

# PART VI — FORWARD ROADMAP (abbreviated)

The **500-experiment schema (ARK-458–957)** is a floor, not a ceiling — 10 priority groups (P01–P10), with new groups anticipated beyond P10.

- **P01 Production Boundary (458–482)** — ✅ COMPLETE
- **P02 Latency/Throughput/Scale (483–492)** — ✅ complete (10/10 PASS, all published); next P03 Dependency Cascade (ARK-493+)
- **P03 Reliability/Failure Modes (508–532)** — next
- **P04–P10** — ProofRecord & crypto, identity/delegation, evidence policy, AI-agent tool-use, treasury/financial, VaultProof/digital-asset, cloud control-plane

**Operating rhythm:** ~1 meaningful, honestly-published experiment per week + 10–20 targeted commercial conversations. **70/30 rule:** 70% pilot acquisition & delivery, 30% experimentation supporting customers, product, standards, or IP.

---

## Stewardship signal
Strength lies in the preservation of failures, honored gates, corrected language, the clean separation of open standard from proprietary product, and a fully challengeable public record. The next faithful move is patience, security, truthfulness, company protection, and one narrow service act proving the boundary protects a real organization.

> *Soli Deo Gloria — world-class work, offered for Christ.*

---

*This summary reconciles the RF Master Corpus Scoreboard, Infrastructure Record, Strategic Doctrine, Synthetic-Phase Closure, and the BELLWETHER/CHRONO quantum-witness records as of 2026-07-18. Claims are held narrower than the evidence. All experimental outcomes — PASS, FAIL, HOLD, and GATE-STOP — are preserved honestly.*
