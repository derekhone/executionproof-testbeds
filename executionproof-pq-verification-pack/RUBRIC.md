# Independent Reviewer Rubric

**Instructions:** Complete every row. Enter `PASS`, `FAIL`, or `PARTIAL` in your
own judgement, with a one-line note pointing to your evidence. An unsigned
rubric does **not** count. Until this is completed and signed by an independent
reviewer with no stake in Remnant Fieldworks Inc., the formal RF-100 §8.4
conformance claim remains `PENDING`.

| # | Task | Verdict | Evidence / notes |
|---|------|---------|------------------|
| 1 | Reproduce verification from scratch (exit 0) | `NOT-EVALUATED` | |
| 2 | Re-derive canonicalization + signature independently | `NOT-EVALUATED` | |
| 3 | Tamper detected (payload + signature) | `NOT-EVALUATED` | |
| 4 | Forgery under unpublished key rejected | `NOT-EVALUATED` | |
| 5 | Rotation non-destructive AND revocation honored | `NOT-EVALUATED` | |
| 6 | Published keys match live endpoint AND custody write-up correct | `NOT-EVALUATED` | |

## Scoring

- **Overall PASS** requires PASS on Tasks 1–5 **and** a correct trust-assumption
  write-up on Task 6 (the reviewer confirms the system claims *tamper-evident
  under a hardware-held key*, not *unforgeable regardless of key custody*, and
  not *the governance verdict is correct*).
- Any accepted tamper, any accepted forgery under an unpublished key, any
  verified record under a revoked key, or any old proof that stopped verifying
  after rotation is an **automatic overall FAIL**.
- Record `PARTIAL` where a property holds with caveats; describe the caveat.

## What a PASS does and does not mean

A signed overall PASS means: *an independent engineer reproduced the
verification, tried to defeat the signing/custody boundary along these axes, and
it held with honest records and correctly published keys.*

It does **not** mean production-certified, audited, penetration-tested,
endurance-proven, or that the governance decisions inside the ProofRecords are
correct. Claims derived from this review must remain **narrower** than this
rubric.

---

Reviewer name: ______________________________  Affiliation: ________________

Date: ____________  Signature: ______________________________

(Recommended: sign this file with your own key and publish the signature
alongside your findings, so your review is itself independently verifiable.)
