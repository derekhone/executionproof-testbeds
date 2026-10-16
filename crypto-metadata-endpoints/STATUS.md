# Issue #25 — Status Correction

**Scope of this note:** corrects the record for
[issue #25](https://github.com/derekhone/executionproof-testbeds/issues/25)
("Deploy live crypto metadata endpoints for AWS KMS ML-DSA-65 status").

## Two distinct deliverables

| Deliverable | Status |
|---|---|
| **A. Testbed / schema-simulation implementation** (this directory, PR #33) | COMPLETE |
| **B. Live production deployment** of the public `/v2` metadata endpoints | OPEN |

### A. Testbed implementation — COMPLETE
PR #33 added a self-contained **EXPERIMENTAL software simulation** of the
metadata endpoints documented in PR #24
(`docs/crypto-api-metadata-contract.md`):

- `GET /v2/version`
- `GET /v2/crypto-manifest`
- `GET /v2/crypto/pq-public-key`

It exercises the documented response schema and routing **locally** (Flask app
+ static snapshots + tests). Every response is explicitly marked as a
simulation (`_simulation` block, `simulation: true`, `hardware_present: false`,
`live_aws_kms: false`, `X-ExecutionProof-Simulation` / `-Experimental`
headers). No signing, no hardware boundary, no FIPS/CNSA/certification claim.
This remains valid as a **reference / testbed / schema simulation**.

### B. Live production deployment — OPEN
Issue #25 as written tracks **live API metadata availability/routing** on the
public host, i.e. the three `/v2` URLs that were returning `404` from
`executionproof.io`. A software simulation does **not** satisfy that criterion.

**Verification as of 2026-10-16 (read-only checks):**

- `https://executionproof.io/v2/version` -> **HTTP 404**
- `https://executionproof.io/v2/crypto-manifest` -> **HTTP 404**
- `https://executionproof.io/v2/crypto/pq-public-key` -> **HTTP 404**

(`executionproof.io/` root returns 200 — a Next.js site with no `/v2` API
routes mounted.)

The `derekhone/executionproof` repo's `PRODUCTION-STATUS.md` asserts the
hosted `/v2` endpoints are "available under pilot access," but from the
currently authorized evidence the **public** endpoints referenced in issue #25
are still unreachable (404), and no public, independently reachable AWS
KMS-backed `/v2` metadata endpoint has been verified. Independent ProofRecord
verification depends on a reachable public `pq-public-key` endpoint, which is
not currently served at the documented URL.

## Why issue #25 should be REOPENED
Closing #25 via PR #33 was premature: PR #33 is a simulation/testbed, not a
live deployment, and its own description states that routing these responses
onto the public `executionproof.io` domain "remains a separate website/API
deployment task, outside this repo." The live-deployment acceptance criterion
is therefore **not met**.

> **Action requested of the repository owner:** reopen issue #25 (the GitHub
> App used for this correction lacks Issues-write scope and could not reopen it
> automatically), or split it into:
> - **A — Testbed implementation:** CLOSED/COMPLETE (PR #33), and
> - **B — Deploy and verify live AWS KMS-backed crypto metadata endpoints:**
>   OPEN.

## Boundaries preserved
This correction changes **no** simulation flags, headers, or disclaimers in
this directory, introduces **no** production claims, starts **no** new
experiment, and creates **no** new DOI. It only records status accurately.
