# ARK-458 — Cloud IAM Role Grant · Exact-Action Binding

**Status:** EXECUTED — VERDICT **PASS** (executed 2026-07-18T18:13:54Z UTC; preregistration locked in `MANIFEST.txt`)
**DOI:** [10.5281/zenodo.21432645](https://zenodo.org/record/21432645) (version) · [10.5281/zenodo.21398675](https://zenodo.org/record/21398675) (ARK series concept)

- `g_allow_exact` = 1.0000 (C1 ≥ 0.95 ✓) · `g_deny_mutation_min` = 1.0000 (C2 ≥ 0.95 ✓) · `g_margin` = 0.9500 (C3 ≥ 0.90 ✓)
- Dual-guard concordance 800/800 = 100.00%; kill-gate wrong-allows 281/700 (testbed falsifiable); all 800 scenarios effectiveness-gated
- See `RESULTS.md` for the full readout.

**Substrate:** Classical software (no quantum hardware, no cryptography beyond a SHA-256 identity token)
**Guards:** Dual independent — V1 (JavaScript), V2 (Python)
**Series:** ExecutionProof authorization-boundary corpus — **Production-Boundary phase (P01, ARK-458–482)**

## Question

When an authorization is approved to grant a **specific** IAM role (an exact action tuple: `principal`, `role`, `account`, `permission_set`, `condition`), can that approval be used to execute a **mutated** grant? A correct guard must ALLOW only on an **exact** action-tuple match and DENY every mutation — privilege escalation, grantee swap, account swap, permission expansion, condition stripping, multi-dimension tampering, and confusable near-matches.

## Design

8 arms × 100 scenarios = 800 decisions. Arm 1 = exact match (ALLOW); arms 2–8 = action mutations (DENY). Two independently written guards (JS + Python) must agree. A kill-gate proves a lenient comparator fails the same scenarios.

| Arm | Condition | Expected |
|-----|-----------|----------|
| 1 | BASELINE-exact-action-match | ALLOW |
| 2 | ROLE-ESCALATION | DENY |
| 3 | PRINCIPAL-SWAP | DENY |
| 4 | ACCOUNT-SWAP | DENY |
| 5 | PERMISSION-EXPANSION | DENY |
| 6 | CONDITION-STRIP | DENY |
| 7 | MULTI-DIM-TAMPER | DENY |
| 8 | CONFUSABLE-NEAR-MATCH | DENY |

## Why this experiment

- **Prospect Question #3** — "Can a changed action be rejected after approval?" — answered in a recognizable enterprise context (IAM role grant). First ExecutionProof **production-boundary** integration.
- Working-example evidence for exact-action / no-privilege-drift mechanisms disclosed in filed applications. *Not legal validation of any claim; no new matter.*

## Run

```bash
python3 run_killgate.py   # negative control (falsifiability)
python3 run_arms.py       # 8 arms × 100, dual guards
./compute_hashes.sh       # verify MANIFEST.txt lock
```

## Honest bounds

Classical control-logic test — not a test of AWS, not a cryptographic proof, not a production-readiness or RF-100 certification. Results bounded to this scenario model, arms, and seed family.

---

*Preregister → lock → execute → publish all outcomes. To God be the glory. Proof Before Power. Verification Before Execution.*
