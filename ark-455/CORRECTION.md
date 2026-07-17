# ARK-455 — CORRECTION / ERRATUM (v1.1)

**Issued:** 2026-07-17 (UTC)
**Applies to:** ARK-455 v1.0 (Zenodo DOI 10.5281/zenodo.21408545; concept 10.5281/zenodo.21398675)
**Nature of correction:** Root-cause reclassification. **No raw data changed. No verdict rescinded.**

---

## Summary

ARK-455 v1.0 recorded a **FAIL** verdict: in Arm 3 (timestamp), the "tampered"
records were accepted by both independent verifiers at a 0% rejection rate, while
all six other tamper targets were rejected at 100%. The v1.0 record speculated the
cause was **either** "a generator flaw (tampering strategy insufficient to break
the signature)" **or** "a verification logic gap."

A post-publication source audit has now **resolved that ambiguity definitively.**
The cause is the **first branch: a generator (test-harness) defect.** The Arm-3
timestamp "tamper" was a **no-op** — it never altered the record. It is **not** a
verifier defect and **not** a specification gap in the signed payload.

**The FAIL verdict stands** as an honest, recorded outcome. What changes is only the
*interpretation* of the failing arm: it reflects a defective tamper generator, not a
detection gap in the dual-verifier architecture.

---

## Evidence (reproducible from the locked v1.0 code)

The Arm-3 timestamp mutation in `generator/record_generator.py` is:

```python
elif field == "timestamp":
    # Parse, add 1 second, re-serialize   <-- comment says +1 second
    dt = datetime.fromisoformat(tampered["timestamp"].replace('Z', '+00:00'))
    dt = dt.replace(microsecond=(dt.microsecond + 1000000) % 1000000)   # <-- no-op
    tampered["timestamp"] = dt.isoformat().replace('+00:00', 'Z')
```

For **every** integer microsecond value `m` in `[0, 1_000_000)`:

```
(m + 1_000_000) % 1_000_000 == m
```

So `dt.replace(microsecond=...)` returns the **same** microsecond, the seconds field
is never touched, and the resulting timestamp is **byte-identical** to the original.
The comment ("add 1 second") does not match the code (adds zero).

Consequently, Arm-3 "tampered" records are identical to Arm-1 (untampered) control
records. Both verifiers therefore **correctly ACCEPTED** them — the signatures are
genuinely valid over unaltered records. The 0% rejection rate is the *correct*
verifier response to a *non*-tampered input.

### What the audit confirmed about the verifiers and the spec

- The `timestamp` field **is** included in the RFC 8785 (JCS) canonical form that is
  Ed25519-signed by the generator (`sign_record` signs the full 7-field record).
- Both verifiers (V1 JS, V2 Python) **do** reconstruct and canonicalize the
  `timestamp` field before verifying. A genuine post-signing change to `timestamp`
  **would** break the signature and be rejected — exactly as the other six arms show.
- Therefore the earlier external hypotheses that "timestamp was not in the signed
  payload" or "the mutation happened before signing" are **both incorrect** for
  ARK-455 v1.0.

---

## Corpus scoreboard impact

- ARK-455 remains a **recorded FAIL** (the verdict is not rescinded; preregistration
  discipline preserved — nothing loosened after the fact).
- The FAIL is now correctly attributed to a **test-harness no-op**, not to a verifier
  or specification weakness. The dual-verifier architecture behaved correctly on all
  arms, including Arm 3.
- Follow-up **ARK-455b** (see the `ark-455b/` directory) re-runs the study with:
  1. a **corrected** timestamp post-signing mutation (a real change that breaks the
     signature),
  2. a **new pre-signing expired-timestamp arm** that tests validity-window/expiry
     semantics beyond bare signature checking, and
  3. a **mutation-effectiveness gate** that aborts the run unless every REJECT arm's
     tamper provably alters the record — so a no-op can never again masquerade as a
     detection failure.

---

## Discipline note

ARK-455 v1.0 was published to Zenodo (DOI-live) under a working instruction to keep
the record as a draft pending review. The record is honest and the raw data are
sound, so no retraction is warranted — this erratum is the appropriate correction
mechanism. The publication-gate instruction has been tightened for future runs
(preregistered "draft, do not publish without human review" is now an explicit gate).

---

*Remnant Fieldworks Inc. — ExecutionProof ARK Series*
*This erratum is distributed with the ARK-455 record and referenced from its README.*
