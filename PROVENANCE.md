# PROVENANCE — ARK Authorization-Boundary Testbeds

This document records the origin and relocation history of this repository honestly and completely,
consistent with the audit-trail integrity that governs the ARK series.

> **Naming note.** The sibling physics program referenced below was originally published under the working
> title Unified Inheritance Physics (UIP); its active framework name is now the Coherent Inheritance
> Framework (CIF), and its repository is now `cif-phase1-testbeds`. To preserve the audit trail, this
> document deliberately retains the original `uip-phase1-testbeds` repository path, the original program
> labels, and the verbatim quotation of the locked `INDEPENDENCE_NOTICE.md` exactly as committed at lock
> time. GitHub automatically redirects the former `uip-phase1-testbeds` URLs to the renamed repository.

---

## 1. Two distinct tracks (why this repository exists)

Two separate bodies of work were, for a period, committed into a single GitHub repository
(`derekhone/uip-phase1-testbeds`). They are conceptually and administratively distinct:

| | **UIP Phase 1 (physics)** | **ARK authorization boundary (this repo)** |
|---|---|---|
| Nature | Academic physics falsification program | Applied verification-layer R&D (ExecutionProof) |
| Question | Does an inheritance/recirculation field law hold? | Can a verify-then-execute authorization boundary be enforced? |
| Status | **Closed** ("nothing further will be added"); under external review | Ongoing product-validation series |
| Canonical DOI | 10.5281/zenodo.**21246246** | 10.5281/zenodo.**21398676** |
| Ledger | 4 confirmed / 5 falsified | ARK-441/446/442/444/443 all PASS |

The **UIP Phase 1** repository was cited to external reviewers as the closed record of that physics
program. The **ARK authorization-boundary** experiments (ARK-441, ARK-446, ARK-442, ARK-444, ARK-443)
are product-track work and were separated into this dedicated repository so the Phase 1 record stays
clean and unambiguous for review.

**This separation was the documented intent from the beginning.** The original `ark-441/INDEPENDENCE_NOTICE.md`
(committed at ARK-441 lock time, and preserved in this repository) states explicitly:

> "ARK-441 is **NOT part of the UIP (Universal Inheritance Principle) Phase 1 or Phase 2 program** ...
> It is committed to `derekhone/uip-phase1-testbeds` under the isolated `ark-441/` folder solely so Derek
> can review all hardware testbeds in one place ... they do **not** share a research program, hypotheses,
> claims, or conclusions."

Relocating the ARK track into this dedicated repository fulfills that original stated intent, rather than
changing it.

**Note on naming:** the `ARK-` prefix is shared with an unrelated physics experiment, `ARK-DM-1`
(a preregistered galaxy-rotation-curve / dark-matter test inspired by the UIP/Ark library). `ARK-DM-1`
is **physics lineage** and does **not** belong to this authorization-boundary track; it is not included here.

---

## 2. Original commit history (immutable, preserved)

The five authorization experiments were originally developed, preregistered, executed, tagged, and
published inside `derekhone/uip-phase1-testbeds`. That original public history — including the
preregistration LOCK commits, the "job ID committed before results" commits, and the release tags
`ark-441-v1.0`, `ark-446-v1.0`, `ark-442-v1.0`, `ark-444-v1.0`, `ark-443-v1.0` — **remains intact in the
original repository and is not rewritten or deleted.** The preregistration integrity of each experiment
rests on those original timestamped commits, which are left untouched for audit.

This repository is a **forward relocation**: the experiment contents are re-committed here with this
provenance note, rather than a history rewrite. Where the original lock/ordering commit hashes are
referenced inside each experiment's files (e.g. `RUN_LOG.md`, `RESULTS.md`, `MANIFEST.txt`), those hashes
continue to point at the original commits in `uip-phase1-testbeds`, which is the authoritative
preregistration timeline.

---

## 3. Zenodo

The dataset DOI **10.5281/zenodo.21398676** covers the ARK authorization-boundary series. Its repository
reference and related identifiers are being updated to point at this repository
(`https://github.com/derekhone/executionproof-testbeds`) as the canonical code/data home for the track.
The Phase 1 physics DOI (10.5281/zenodo.21246246) is unaffected.

---

## 4. Relocation date

- **Relocated:** 2026-07-17 (UTC)
- **Reason:** administrative separation of the applied authorization-boundary track from the closed UIP
  Phase 1 physics record, so the physics program under external review is not commingled with ongoing
  product-validation work.
- **Method:** forward re-commit with preserved original history in the source repository (no history rewrite).
