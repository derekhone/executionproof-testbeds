# ARK-499 → ARK-503 — Enterprise Adapter Series Testbed

**Remnant Fieldworks Inc. — ExecutionProof program**
Series scope: does the *same* frozen authorization boundary that governed the
ARK-441…ARK-498 corpus continue to hold when wired to **real, self-hosted
enterprise backing systems** — a transactional database, a CI/CD release
boundary, and a federated identity/IAM boundary — plus a bounded operational
soak and a packaged independent-review target?

This README is the entry point. **Read the preregistration first**
(`preregistration/ARK-499-503-PREREGISTRATION-v1.0.md`) — it was written and
its SHA-256 was locked *before* any experiment in this series was executed.

---

## Honesty labels (read before interpreting any result)

This series is deliberately scoped to what an ephemeral build VM can *actually*
prove. The labels below are load-bearing; do not upgrade them.

- **Real, but self-hosted.** ARK-499/500/501 run against genuine components
  (native PostgreSQL 17, a real local git release boundary, a self-hosted
  RS256 OIDC issuer + JWKS + resource server). They are **NOT**
  Docker/Kubernetes/managed-cloud deployments, and the identity boundary is
  **NOT** Okta / Azure AD / Auth0. It is real software exercising the real
  protocol surface, self-hosted on loopback.
- **Smoke, not endurance.** ARK-502 is a **bounded operational smoke test**
  (minutes, hundreds of operations). The preregistered ≥14-day endurance soak
  is **NOT-EXECUTED** — it is impossible on an ephemeral VM. ARK-502 contributes
  **zero** scored case records to the corpus.
- **Packaged, not scored.** ARK-503 is a **NOT-EXECUTED** package prepared for a
  *human* independent reviewer. It contributes **zero** scored case records. No
  self-graded PASS is claimed for it.
- **Tamper-evident, not unforgeable.** The hash chain and ed25519 signatures make
  undetected alteration hard; they are not a proof of unforgeability.
- **Engineering evidence, not certification.** These are engineering experiments,
  not a production security certification, audit, or peer review.

When narrative and machine record disagree, **the machine record governs.**

---

## What was executed (from `results/execution_manifest.json`)

| Experiment | Boundary exercised | Backing system (real, self-hosted) | Verdict |
|---|---|---|---|
| ARK-499 | Transactional write boundary | Native PostgreSQL 17 cluster | **EXPERIMENT-PASS** (7/7 arms) |
| ARK-500 | CI/CD release / promotion boundary | Real local git release repo | **EXPERIMENT-PASS** (7/7 arms) |
| ARK-501 | Federated identity / IAM boundary | Self-hosted RS256 OIDC + JWKS + resource server | **EXPERIMENT-PASS** (7/7 arms) |
| ARK-502 | Bounded operational soak | PostgreSQL + git under sustained load | **SMOKE-PASS** (endurance NOT-EXECUTED) |
| ARK-503 | Independent human review | package only | **NOT-EXECUTED** |

**Scored contribution to corpus:** 21 case records, all PASS (7+7+7).
ARK-502 (smoke) and ARK-503 (package) contribute 0 scored PASS by design.

The full run produces **one continuous hash chain** across every ProofRecord in
the series (genesis → tail, no linkage breaks), independently verifiable with the
published ed25519 public key.

---

## Repository layout

```
ark-499-503-testbed/
├── README.md                      ← you are here
├── requirements.txt               ← Python deps + system prereqs
├── run_all.py                     ← verifies prereg + frozen-gate hashes, then runs 499→502
│
├── preregistration/
│   ├── ARK-499-503-PREREGISTRATION-v1.0.md   ← locked BEFORE execution
│   ├── ...(.pdf/.docx renders)
│   └── PREREGISTRATION-MANIFEST.txt          ← SHA-256 lock of prereg + 8 frozen gate/guard files
│
├── gate/                          ← FROZEN authorization core (byte-identical to ARK-493-498)
│   ├── core.py  gate.py  policy.py  actor_registry.py  __init__.py
├── guards/                        ← FROZEN dual guards (byte-identical to ARK-493-498)
│   ├── guard_a.py  guard_b_verifier.py  __init__.py
├── enforcement/
│   ├── proofstore.py              ← FROZEN hash-chained store (byte-identical)
│   └── real_enforcement_point.py  ← series-specific: real side effects + optional identity validator
├── actor/                         ← FROZEN actor agent (byte-identical)
│
├── adapters/                      ← series-specific REAL backing-system adapters
│   ├── pg_adapter.py              ← native PostgreSQL 17 lifecycle + writes
│   ├── cicd_adapter.py            ← real local-git release boundary
│   └── oidc_adapter.py            ← self-hosted RS256 OIDC issuer + JWKS + resource server
│
├── experiments/
│   ├── run_499.py  run_500.py  run_501.py  run_502.py
│
├── ark503_review_package/         ← NOT-EXECUTED human-review target
│   ├── README.md  SETUP.md  REVIEWER_TASKS.md  RUBRIC.md  STATUS.md (+ renders)
│   └── independent_verifier.py    ← self-contained; embeds published ed25519 public key
│
├── proofrecords/                  ← emitted ProofRecords (one continuous chain)
└── results/
    ├── execution_manifest.json    ← series verdicts + honesty notes
    └── results_ledger.jsonl       ← per-case scored ledger (21 PASS + 1 SMOKE-PASS)
```

**Frozen vs. new.** The `gate/`, `guards/`, `enforcement/proofstore.py`, and
`actor/` files are **byte-identical** to the ARK-493-498 testbed — the same
authorization boundary, reused unmodified and hash-locked in the manifest. Only
the *adapters* (real backing systems) and the *experiment drivers* are new. This
is the core claim of the series: the boundary did not have to change to meet
enterprise surfaces.

---

## Reproduce

```bash
# 0. system prereq: PostgreSQL 17 binaries on PATH (initdb/pg_ctl/postgres)
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 1. run the full series (verifies prereg + 8 frozen hashes BEFORE running)
python3 run_all.py

# 2. independently verify the whole chain with the published public key
python3 ark503_review_package/independent_verifier.py proofrecords/
```

`run_all.py` refuses to run if the preregistration SHA-256 or any of the 8
frozen gate/guard hashes do not match the manifest — execution cannot silently
diverge from what was preregistered.

---

## For an independent reviewer

Start at `ark503_review_package/README.md`, then `SETUP.md`, `REVIEWER_TASKS.md`,
and score against `RUBRIC.md`. `STATUS.md` states plainly that ARK-503 is
NOT-EXECUTED and that no self-assigned PASS exists for it. The verifier is
self-contained and needs only the public key it already embeds.

---

*Prepared under the Remnant Fieldworks honesty covenant: claims stay narrower
than evidence; every PASS / FAIL / HOLD / SMOKE / NOT-EXECUTED is preserved as
run; and the machine record governs when it disagrees with the narrative.*
