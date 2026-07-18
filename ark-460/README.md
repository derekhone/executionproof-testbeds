# ARK-460 — Cloud IAM Role Grant · Dependency Loss

**Status:** EXECUTED — VERDICT **PASS** (executed 2026-07-18T18:49Z UTC, post-lock)

- g_allow_available = 1.0000 (C1 ≥ 0.95 ✓) · g_hold_unavailable_min = 1.0000 (C2 ≥ 0.95 ✓) · g_margin = 0.9500 (C3 ≥ 0.90 ✓)
- Dual-guard concordance 800/800 = 100.00%; kill-gate 150/150 wrong-allows (falsifiable)
- See `RESULTS.md` for the full readout.

**Substrate:** Classical software · **Guards:** Dual independent (V1 JS, V2 Python)
**Series:** ExecutionProof authorization-boundary corpus (production-boundary phase)

## Question

When an IAM role-grant authorization is **APPROVED**, but a critical dependency (Policy Registry, Identity Provider, Signature Verifier, Audit Logger) is **UNAVAILABLE** at execution time, does the gate **fail safe** (HOLD — cannot confirm validity) rather than wrongly ALLOW (fail-open)?

## Design

- **8 arms** × 100 scenarios = **800 decisions**
- **Arms 1, 8:** ALL-AVAILABLE → expect ALLOW
- **Arms 2–7:** at least one dependency UNAVAILABLE → expect HOLD

Decision logic:
- If **ALL** critical dependencies are AVAILABLE → ALLOW
- If **ANY** critical dependency is UNAVAILABLE → HOLD (fail-safe)

## Pass criteria (preregistered)

- **C1:** g_allow_available ≥ 0.95
- **C2:** g_hold_unavailable_min ≥ 0.95
- **C3:** g_margin ≥ 0.90

## Layout

```
ark-460/
├── PREREGISTRATION.md + MANIFEST.txt + compute_hashes.sh
├── generator/scenario_generator.py
├── verifiers/{v1_guard.js, v2_guard.py}
├── run_arms.py + run_killgate.py
├── results/{arm_*_scenarios.json, arm_*_results.json, overall_results.json, killgate_results.json}
├── RESULTS.md + README.md
```

## Honest bounds

Classical software test of authorization control logic. This tests **dependency-loss logic**; ARK-458 tested exact-action-binding, ARK-459 tested revocation. **No claim** that this legally validates any patent claim or certifies RF-100 conformance.

---

*Published under the Remnant Fieldworks Standing Covenant. To God be the glory. Proof Before Power. Verification Before Execution.*
