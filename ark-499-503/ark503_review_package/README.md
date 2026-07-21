# ARK-503 — Independent Adversarial Review Package

**Status: `NOT-EXECUTED — AWAITING INDEPENDENT REVIEWER`**
**Scored contribution to the RF experimental corpus: `0` (zero) until an
independent human reviewer completes and signs the rubric below.**

---

## 1. What this package is

ARK-499 through ARK-502 were executed *by the builder*, on the builder's own
machine, against components the builder wrote. That is a necessary step, but it
is **not** independent evidence. No system should be trusted because the people
who built it say it works.

ARK-503 is the honesty backstop for the whole enterprise-adapter series: a
package designed to be handed to **an independent engineer who did not build any
of this**, so they can try to *break* the ExecutionProof boundary and judge it
on their own terms.

This package deliberately does **not** self-report a PASS. A machine cannot
grade its own independence. The rubric is filled in by a human, and until that
happens the corpus records ARK-503 as `NOT-EXECUTED`.

## 2. What is being claimed (and what is not)

**Claimed and testable here:**
- On `ALLOW`, exactly the approved action reaches the real backing system,
  exactly once.
- On anything else (`DENY`/`HOLD`, unauthorized actor, mutated action, stale or
  revoked authority, missing evidence, wrong policy version, dependency outage,
  malformed request, forged/expired/revoked identity token), **zero** side
  effects occur.
- Every decision emits a signed, hash-chained, dual-guard ProofRecord that an
  outside party can verify with only the published public key
  (`independent_verifier.py`).

**Explicitly NOT claimed:**
- Not production-hardened, not an SLA, not certified, not audited.
- The backing systems are *real but self-hosted*: a native PostgreSQL 17
  cluster, a local git CI runner with an on-disk deploy target, and a
  self-hosted RS256 issuer + JWKS + bearer-protected resource. They are **not**
  Docker/Kubernetes/cloud, and **not** Okta/Azure AD/Auth0.
- ARK-502's ≥14-day endurance soak was **NOT executed** — only a bounded
  seconds-long smoke ran. Endurance remains unproven.
- A valid signature proves internal consistency and key-holder authorship. It
  does **not** prove the key stayed secret, the clock was honest, or the host
  was trustworthy. Those are review questions (Task 8).

## 3. Files

| File | Purpose |
|------|---------|
| `README.md` | This overview. |
| `SETUP.md` | How to stand up the testbed from a clean machine. |
| `REVIEWER_TASKS.md` | The 10 adversarial tasks to attempt. |
| `RUBRIC.md` | The human-scored rubric (currently all `NOT-EVALUATED`). |
| `STATUS.md` | Machine-readable NOT-EXECUTED declaration. |
| `independent_verifier.py` | Self-contained ProofRecord verifier (no testbed imports). |

The testbed itself (frozen gate, guards, adapters, experiments) lives one level
up in this repository and is referenced by the tasks.

## 4. How to use it

1. Read `SETUP.md`, stand the testbed up from scratch, reproduce ARK-499–502.
2. Work through `REVIEWER_TASKS.md` — most tasks are *attempts to defeat* the
   boundary. A boundary that holds should make these fail safely and record the
   failure.
3. Record findings in `RUBRIC.md`, sign, and date it.
4. Only a signed rubric with an overall PASS converts ARK-503 from
   `NOT-EXECUTED` to an actual result. Even then, claims must stay narrower than
   the evidence.

> Governing rule (inherited from the whole RF corpus): **when the narrative and
> the machine record disagree, the machine record governs.** If anything in this
> README overstates what the artifacts show, believe the artifacts.
