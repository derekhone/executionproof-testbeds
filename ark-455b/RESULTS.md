# ARK-455b Results
# ProofRecord Verification After Tampering — Corrected Retest with Validity-Window Semantics

**Verdict: ✅ PASS**

**Execution date:** 2026-07-17
**Substrate:** Local classical software (no IBM QPU)
**Lock commit:** `6776616` (prereg + code + MANIFEST committed before execution)
**Kill-gate:** PASS (100.0% V1–V2 concordance; both verifiers accepted all 50 valid records; 50/50 tampered carried effective mutations)

---

## 1. Summary

ARK-455b is the corrected retest of ARK-455, whose v1.0 FAIL was traced to a
test-harness no-op in the Arm-3 timestamp tamper (see
[`../ark-455/CORRECTION.md`](../ark-455/CORRECTION.md)). With the tamper corrected
and a validity-window gate added, **all three preregistered criteria pass with
perfect margins**, and the two new-in-455b conditions behave exactly as the
doctrine predicts:

- **Arm 3 (timestamp, real post-signing +1s):** now detected at **100%** by both
  verifiers — directly confirming that the ARK-455 0% "detection failure" was an
  artifact of a no-op mutation, not a verifier or specification defect.
- **Arm 9 (timestamp, pre-signing expired, valid signature):** rejected at
  **100%** by the validity-window gate — a record that a bare signature check
  (ARK-455) would have accepted.

| Metric | Value | Threshold | Result |
|---|---|---|---|
| C1 — V_accept_original (Arm 1) | 1.0000 | ≥ 0.95 | ✅ |
| C2 — V_reject_min (Arms 2–9) | 1.0000 | ≥ 0.95 | ✅ |
| C3 — V_margin | 1.0000 | ≥ 0.85 | ✅ |
| V1–V2 concordance (all arms) | 100.00% (900/900) | ≥ 99% | ✅ |
| Mutation-effectiveness (Arms 2–9) | 100% (800/800) | 100% | ✅ |

---

## 2. Design as Executed

- **9 arms × 100 records = 900 records** (the concrete design registered in
  PREREGISTRATION.md; no other variant was run).
- **Dual independent verifiers:** V1 (JavaScript, tweetnacl), V2 (Python, PyNaCl).
- **Two-gate verification:** Gate A = Ed25519 signature over RFC 8785 (JCS)
  canonical form of the 7 signed fields; Gate B = validity window (reject
  future-dated `age < 0` or expired `age > TTL`). **TTL = 300 s.**
- **verification_time** captured after record generation (auditor verifies an
  issued record), modelling realistic issuance→verification ordering.
- **Mutation-effectiveness gate:** every REJECT-arm record was confirmed to carry
  an effective mutation before scoring; the run would have aborted otherwise.

---

## 3. Per-Arm Results

| Arm | Label | Mode | V1 acc / rej | V2 acc / rej | Mut-eff | Concordance |
|---|---|---|---|---|---|---|
| 1 | ACCEPT-original | control | 100 / 0 | 100 / 0 | n/a | 100/100 |
| 2 | REJECT-decision | post-sign | 0 / 100 | 0 / 100 | 100/100 | 100/100 |
| 3 | REJECT-timestamp-postsign | post-sign (real +1s) | 0 / 100 | 0 / 100 | 100/100 | 100/100 |
| 4 | REJECT-payload_hash | post-sign | 0 / 100 | 0 / 100 | 100/100 | 100/100 |
| 5 | REJECT-evidence_refs | post-sign | 0 / 100 | 0 / 100 | 100/100 | 100/100 |
| 6 | REJECT-actor | post-sign | 0 / 100 | 0 / 100 | 100/100 | 100/100 |
| 7 | REJECT-outcome | post-sign | 0 / 100 | 0 / 100 | 100/100 | 100/100 |
| 8 | REJECT-review_path | post-sign | 0 / 100 | 0 / 100 | 100/100 | 100/100 |
| 9 | REJECT-timestamp-presign-expired | pre-sign (valid sig, expired) | 0 / 100 | 0 / 100 | 100/100 | 100/100 |

**Gate attribution:** Arms 2–8 rejected via Gate A (broken signature). Arm 9
rejected via Gate B (valid signature, out-of-window timestamp) — the condition
Gate A alone cannot catch.

---

## 4. Recorded Seeds (256-bit)

**Kill-gate calibration seed:** `74286458217247489335822290487316412859199419933419266139920589335769580693475`
**Kill-gate verification_time:** `2026-07-17T18:04:42.222404Z`

**Arm run window:** start `2026-07-17T18:04:50.268672Z` → end `2026-07-17T18:05:39.138979Z`

| Arm | Seed |
|---|---|
| 1 | 30338702788410171279486108367259501284442999707035235467814445062761844386588 |
| 2 | 114658493849469925467984076741683536542222061775061141230437307184350924665141 |
| 3 | 10539541460530217100803529659772073539471901155054030814084754831114806174598 |
| 4 | 79613172710084360017150326956993828022126191243796839023154829759239404100405 |
| 5 | 31657411637600192849372484230115948889265032213629703382375313655083237893451 |
| 6 | 48298488535432155429788460904874641117646375606993354884950720134018253690161 |
| 7 | 12785898093060915003940639818053630832397609425253820601936312564888581585415 |
| 8 | 47940087078354831943039200380895684112077847902644115690181724852310640318887 |
| 9 | 13412507691496949081260263630318694331612394797312134373558027435505297124233 |

Full per-arm data in `results/arm_1_results.json` … `results/arm_9_results.json`;
kill-gate detail in `results/killgate_calibration.json`; overall metrics in
`results/overall_results.json`.

---

## 5. Interpretation

**H1 (primary) — CONFIRMED.** Independent verifiers accept genuine in-window
originals and reject every tampered and every expired record. All of C1–C3 pass
at 1.0000.

**H2a (tampering universality) — CONFIRMED.** All seven post-signing tampering
targets, including the corrected timestamp arm, are detected at 100%. No target
is exempt.

**H2b (dual verifier agreement) — CONFIRMED.** 100.00% concordance across all 900
records (independent JS and Python implementations).

**H2c (signature binding) — CONFIRMED.** No post-signing tampered record (Arms
2–8) produced a valid signature.

**H2d (validity-window binding) — CONFIRMED.** Arm 9 records, whose signatures
are cryptographically valid, are rejected at 100% because their timestamps are
out of the 300 s window. Temporal validity is enforced independently of signature
validity (expiry doctrine of ARK-442, now at the verification layer).

**H2e (mutation effectiveness) — CONFIRMED.** 800/800 REJECT-arm records carried
an effective mutation. The class of defect that produced the ARK-455 anomaly
cannot pass this harness silently.

### Relationship to ARK-455
ARK-455b does **not** retract ARK-455's recorded FAIL. It (1) confirms the
erratum's root-cause finding by showing that a *real* timestamp tamper is
detected at 100%, and (2) extends the specification with validity-window
semantics. The ARK-455 FAIL stands as an honest record of a harness defect; the
capability it appeared to question is demonstrated intact here.

---

## 6. Honest Boundary Statements

- Classical software test; no quantum claim.
- Single-field tampering only (one mutation per record); multi-field tampering,
  replay across keys, and adversarial signature forgery remain deferred.
- A PASS here validates the verification model and expiry semantics under the
  registered arms; it does not claim coverage beyond them.
- Results are reported exactly as produced by the locked code and recorded seeds.

---

*Remnant Fieldworks Inc. — ExecutionProof ARK Series*
*Repository: https://github.com/derekhone/executionproof-testbeds*
