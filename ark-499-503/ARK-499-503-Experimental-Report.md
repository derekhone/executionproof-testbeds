# ARK-499 → ARK-503 — Enterprise Adapter & Operational Readiness Series
## Experimental Report v1.0

**Program:** ExecutionProof™ · Verification Before Execution™ · Proof Before Power™
**Organization:** Remnant Fieldworks Inc.
**Author / Sole Inventor:** Derek Adam Hone
**Series ID:** ARK-499-503 · **Report date:** 2026-07-20
**Preregistration SHA-256 (locked before execution):**
`84bd915e7d7aab8268f40a339e71dbd96ac2440f929dca6d37bfdde990d24b61`

---

### Executive summary — in one honest paragraph

The ARK-441…ARK-498 corpus showed, inside self-contained synthetic testbeds, that
the ExecutionProof gate makes and *enforces* correct authorization decisions and
emits independently verifiable ProofRecords. This series asked a harder,
previously-unanswered question: **does the SAME, byte-for-byte unmodified gate
still hold when it is wired to real, self-hosted enterprise surfaces?** Against a
real PostgreSQL 17 transaction boundary (ARK-499), a real git-based CI/CD release
boundary (ARK-500), and a real self-hosted RS256 OIDC/JWKS identity boundary
(ARK-501), the answer measured here is **yes**: all three returned
**EXPERIMENT-PASS**, 21 scored cases, all PASS, with **zero enforcement leaks** and
**100% dual-guard agreement**, confirmed by inspecting the *real* external systems
rather than trusting the testbed. Two experiments are deliberately **not** scored:
ARK-502 ran only a **bounded operational smoke** (the preregistered ≥14-day
endurance soak is **NOT-EXECUTED** — impossible on an ephemeral VM), and ARK-503 is
a **NOT-EXECUTED** package awaiting a human independent reviewer. The entire series
forms **one continuous 428-record hash chain** that an outside party can verify with
the published ed25519 key. Nothing here is a production certification.

---

### 0. What to read first, and how to read it

Read the frozen preregistration
(`preregistration/ARK-499-503-PREREGISTRATION-v1.0.md`) before this report. Its
SHA-256 was locked in `PREREGISTRATION-MANIFEST.txt` *before* any experiment ran,
together with the SHA-256 of the eight frozen gate/guard/store files. `run_all.py`
recomputes and checks all nine hashes and **refuses to run** if any differ — so the
executed code provably matches what was preregistered.

**Honesty covenant governing every claim below.** Claims stay narrower than the
evidence. Every PASS / FAIL / HOLD / SMOKE / NOT-EXECUTED is reported exactly as it
ran. FAIL and GATE-STOP, where they occur, are correct and valuable results, never
hidden or rewritten. **When the narrative and the machine record disagree, the
machine record governs — even against the founder.**

---

### 1. Load-bearing honesty labels

These labels are the difference between an honest report and an overclaim. Do not
upgrade them when quoting this work.

| Label | What it means here | What it does **not** mean |
|---|---|---|
| **Real, but self-hosted** | Genuine PostgreSQL 17, a genuine git release boundary, a genuine RS256 OIDC issuer/JWKS/resource server, exercised over their real protocol surfaces | NOT Docker/Kubernetes/managed cloud; NOT Okta / Azure AD / Auth0 |
| **Smoke, not endurance** | ARK-502 ran minutes / 418 operations with restart, outage, key-rotation, policy-change and malformed-input stressors | NOT a ≥14-day soak; endurance remains NOT-EXECUTED |
| **Packaged, not scored** | ARK-503 ships a complete reviewer package + self-contained verifier | NOT a completed independent review; contributes 0 scored PASS |
| **Tamper-evident** | Undetected alteration is made hard by hash-chaining + ed25519 signatures, and is demonstrably caught (§7) | NOT "unforgeable" |
| **Engineering evidence** | Bounded integration experiments in the tested environments | NOT a production security certification, audit, or peer review |

---

### 2. The gate is frozen — only the world around it changed

The core claim of this series is a *negative* one, which is why it is credible: we
did **not** modify the authorization boundary to meet enterprise surfaces. The
following eight files are **byte-identical** to the ARK-493-498 testbed, and their
SHA-256 values are locked in the preregistration manifest:

- `gate/core.py`, `gate/gate.py`, `gate/policy.py`, `gate/actor_registry.py`
- `guards/guard_a.py`, `guards/guard_b_verifier.py`
- `enforcement/proofstore.py`
- `actor/actor_agent.py`

Only two categories of code are new: the **real backing-system adapters**
(`adapters/pg_adapter.py`, `adapters/cicd_adapter.py`, `adapters/oidc_adapter.py`)
and the **enforcement point** that performs a real side effect on ALLOW and zero
side effects on DENY/HOLD (`enforcement/real_enforcement_point.py`). The gate that
decided ARK-499-501 is provably the gate that decided ARK-493-498.

**Enforcement-leak definition (series-wide, from the prereg):** any real external
state change with no corresponding ALLOW ProofRecord, or any ALLOW producing zero
or more than one real change. **Measured leak count across the whole series: 0.**

---

### 3. ARK-499 — Real PostgreSQL transaction boundary → EXPERIMENT-PASS

**Question:** can the gate prevent an *actual* unauthorized database state change
through a *real* database protocol, verified by an independent read-only role?

**Real component:** a freshly-initialized native PostgreSQL 17 cluster on a private
port, a real application schema, a privileged writer role used by the adapter, and a
separate read-only `ark_auditor` role used **only** for independent inspection.

| Arm | Scenario | Gate | Real rows committed | Verdict |
|---|---|---|---|---|
| A1 | Authorized write | ALLOW | 1 (exactly once) | PASS |
| A2 | Unauthorized actor | DENY | 0 | PASS |
| A3 | Mutated action (hash mismatch) | DENY | 0 | PASS |
| A4 | Stale authority (revoked pre-exec) | DENY | 0 | PASS |
| A5 | Missing evidence | HOLD | 0 | PASS |
| A6 | Mid-transaction dependency loss | fail-closed DENY | 0 (rolled back) | PASS |
| A7 | Concurrent idempotency (N parallel) | ALLOW | 1 (exactly once) | PASS |

**Hard criteria:** P-499-1 leak=0 ✓ · P-499-2 every ALLOW commits exactly once ✓ ·
P-499-3 A6 rolls back to zero committed rows ✓ · P-499-4 A7 commits exactly once
under concurrency ✓ · P-499-5 dual-guard agreement 100% ✓. Committed rows were
counted by the independent `ark_auditor` connection, not asserted by the testbed:
**2 committed rows total (A1, A7), 0 from any DENY/HOLD arm.**

---

### 4. ARK-500 — Real CI/CD release boundary → EXPERIMENT-PASS

**Evidence sought:** only the exact approved artifact reaches the exact approved
environment, enforced by a real runner acting on real files with real SHA-256
digests. (Explicitly NOT Docker/K8s/cloud CD — a local git repo, a real build
artifact, and an on-disk `environments/` deploy target.)

| Arm | Scenario | Gate | Real deployment | Verdict |
|---|---|---|---|---|
| B1 | Approved digest → approved env | ALLOW | deployed once; digest matches | PASS |
| B2 | Artifact-digest substitution | DENY | none | PASS |
| B3 | Environment substitution (→ prod) | DENY | production never deployed | PASS |
| B4 | Stale scan evidence | HOLD | none | PASS |
| B5 | Revoked reviewer authority | DENY | none | PASS |
| B6 | Retry under one key | ALLOW | deployed exactly once | PASS |
| B7 | Concurrent deploy triggers | ALLOW | deployed exactly once | PASS |

**Hard criteria:** P-500-1 only the approved digest reached the approved
environment ✓ · P-500-2 zero deployments on all DENY/HOLD arms ✓ · P-500-3
exactly-once under retry and concurrency ✓ · P-500-4 dual-guard agreement 100% ✓.
Deployed digests were recomputed **from disk** by independent inspection; staging
held only the approved digest and **production was never deployed to**.

---

### 5. ARK-501 — Self-hosted enterprise identity boundary → EXPERIMENT-PASS

**Question:** can the boundary resolve *current* authority from an *external*
standards-based identity source rather than internal fixtures?

**Real component:** a real RS256 JWT issuer with a real JWKS endpoint over HTTP
(loopback), real signed access tokens (`sub`, roles/groups, `exp`, `jti`), a real
revocation list, and a separate **resource server** that independently re-validates
the token. Authority for the gate is resolved by validating the real signature
against the fetched JWKS, checking real `exp`, checking revocation, and mapping
token roles to tool authority — the token travels in a side channel and is **not**
part of the exact-action hash.

| Arm | Scenario | Gate | Verdict |
|---|---|---|---|
| C1 | Valid token, sufficient role | ALLOW | PASS |
| C2 | Expired token | DENY | PASS |
| C3 | Bad signature / wrong key | DENY | PASS |
| C4 | Insufficient role | DENY | PASS |
| C5 | Revoked token (`jti` on list) | DENY | PASS |
| C6 | Revoked after issue, before exec (re-resolved at exec) | DENY | PASS |
| C7 | Group-membership escalation | DENY | PASS |

**Hard criteria:** P-501-1 only C1 authorized ✓ · P-501-2 all of C2–C7 denied with
zero side effects ✓ · P-501-3 authority provably resolved from the external issuer
(recorded JWKS `kid` + token `jti`) ✓ · P-501-4 dual-guard agreement 100% ✓. As an
extra check, the forged/expired tokens were also rejected by the independent
resource server directly — the deny does not depend on the gate alone.

---

### 6. ARK-502 — Bounded operational smoke → SMOKE-PASS (endurance NOT-EXECUTED)

**Honest status up front:** a defensible endurance claim requires **≥14 days** of
continuous operation with restarts, policy-version changes, key rotation, DB
migration, dependency outages, clock drift, malformed input, and chain continuity.
**That cannot run on an ephemeral VM and is NOT claimed.** What ran is a **bounded
smoke** that proves the harness works and the chain survives disruption.

- **418 operations**, **132 real side effects (commits)**, **0 leaks**.
- Stressors exercised: ≥1 process restart with chain resume; a policy-version
  change; a key-rotation event; a dependency outage + recovery; malformed requests;
  a burst.
- **Hard smoke criteria, all met:** chain continuity across restart ✓ · zero leaks
  during injected outages ✓ · dual-guard agreement 100% ✓ · malformed input
  fail-closed ✓ · every outage-window action fail-closed ✓ · policy + burst handled ✓.

**Claim ceiling (as preregistered):** *"survived a bounded production-like smoke run
with chain continuity across restart."* Explicitly **not** "weeks" and **not**
"production." The ≥14-day run is deferred to a persistent machine and recorded as
**OPEN**. ARK-502 contributes **0 scored PASS** to the corpus.

---

### 7. Independent verification and a worked tamper example

The whole series is one continuous hash chain. Re-running the self-contained
verifier with the **published** ed25519 public key
(`kid = ark-enterprise-testbed-key-v1`) over all emitted records:

```
Verified 428 records via published key 'ark-enterprise-testbed-key-v1': 428 OK, 0 FAIL
```

The verifier imports none of the testbed's gate/guard/enforcement code; it checks
required fields, `exact_action_hash == SHA-256(canonical_json)`, the record hash,
the ed25519 signature over the documented signed fields, prior-hash chain linkage,
and recorded dual-guard agreement.

**Worked tamper demonstration (reproduced for this report).** On a *copy* of the
chain, we flipped a single signed field (`execution_outcome.tool_called`) in one
record (case `ARK-502-P2A3`, index 214) and re-ran the verifier:

```
[0214] ARK-502-P2A3 FAIL: this_record_hash mismatch (record altered);
       ed25519 signature INVALID; tool_called inconsistent with decision
Verified 428 records ...: 427 OK, 1 FAIL      (process exit code = 1)
```

A one-field change is caught three independent ways and flips the process exit
code. This is what "tamper-evident" means here — **not** "unforgeable."

---

### 8. ARK-503 — Independent enterprise review → NOT-EXECUTED (packaged)

ARK-503 cannot be self-certified: by definition it needs a human who did not build
the experiment. This series therefore delivers only the **reviewer package**
(`ark503_review_package/`): `README`, `SETUP`, `REVIEWER_TASKS`, a scored `RUBRIC`,
a candid `STATUS`, and the self-contained `independent_verifier.py`. The reviewer
installs from the docs, configures policy, rotates keys, adds an action type,
diagnoses a HOLD, verifies ProofRecords, recovers from a simulated outage, inspects
the real downstream systems, and attempts bypasses — scoring each task. Reviewer
independence is graded honestly (internal reviewer = partial independence; an
outside reviewer is stronger; an unassisted customer would be the real answer).
**Status: NOT-EXECUTED — AWAITING INDEPENDENT REVIEWER. 0 scored PASS.**

---

### 9. Corpus reconciliation (counting rule locked in the prereg)

Consistent with the ARK-493-498 individual-cell counting method, this series adds
**3 scored experiments** (ARK-499/500/501) contributing **21 case records, all
PASS**. ARK-502 (smoke) and ARK-503 (package) add **0 scored PASS** and are recorded
as *executed-but-unscored* and *not-executed* respectively.

| | Experiments | Case records | PASS | FAIL | GATE-STOP |
|---|---|---|---|---|---|
| Corpus before this series | 72 | 232 | 229 | 2 | 1 |
| ARK-499/500/501 (scored) | +3 | +21 | +21 | 0 | 0 |
| **Corpus after this series** | **75** | **253** | **250** | **2** | **1** |
| ARK-502 smoke (unscored) | (executed, not counted) | 0 | 0 | 0 | 0 |
| ARK-503 (not executed) | (packaged, not counted) | 0 | 0 | 0 | 0 |

**Count-method disclosure (must travel with the headline):** experiments are
preregistered experiments; case records are individual scored decision cells;
ARK-502/503 are excluded from the PASS tally by design; the two preserved FAIL and
one preserved GATE-STOP from earlier series remain in the record unchanged.

---

### 10. Limitations and open items (stated plainly)

- **Self-hosted, single host, loopback.** Real components, but not distributed, not
  cloud-managed, not a real enterprise IdP. Results generalize to the *protocol
  surfaces* exercised, not to any specific vendor deployment.
- **Endurance is unproven.** ARK-502's ≥14-day soak is OPEN and must run on a
  persistent machine before any reliability-over-time claim is made.
- **Independent review is pending.** ARK-503 is packaged, not completed. No
  third-party has yet reproduced these results.
- **Tamper-evident ≠ unforgeable.** A valid signature + intact chain proves internal
  consistency and testbed-key provenance; it does not prove the key stayed secret,
  the clock was honest, or the infrastructure was production-grade.
- **Engineering evidence ≠ certification.** These are bounded experiments, not an
  audit, not peer review, not a NIST endorsement, and not legally binding.
- **Testbed key is public by design.** The ed25519 seed is a documented testbed-only
  value, never a production secret.

---

### 11. Reproduce

```bash
# system prereq: PostgreSQL 17 binaries (initdb/pg_ctl/postgres) on PATH
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python3 run_all.py                                            # verifies 9 hashes, then runs 499→502
python3 ark503_review_package/independent_verifier.py proofrecords/   # 428 OK, 0 FAIL
```

`run_all.py` will not run if the preregistration SHA-256 or any of the eight frozen
gate/guard/store hashes fail to match the manifest.

---

*Built in faith. Tested in public. Claims kept narrower than the evidence.*
*Proof Before Power™ · Verification Before Execution™ — Remnant Fieldworks Inc.*
