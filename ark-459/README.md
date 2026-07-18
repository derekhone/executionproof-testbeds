# ARK-459 — Cloud IAM Role Grant · Revocation At Execution

**Status:** EXECUTED — VERDICT **PASS** (executed 2026-07-18T18:43Z UTC, post-lock — see `MANIFEST.txt`)

- g_allow_valid_min = 1.0000 (C1 ≥ 0.95 ✓) · g_deny_revoked_min = 1.0000 (C2 ≥ 0.95 ✓) · g_hold_inflight_min = 1.0000 (C3 ≥ 0.95 ✓) · g_margin = 0.9500 (C4 ≥ 0.90 ✓)
- Dual-guard concordance 800/800 = 100.00%; kill-gate wrong-allows 125/125 (testbed falsifiable); all 800 scenarios timing-gated
- See `RESULTS.md` for the full readout.

**Substrate:** Classical software (no quantum hardware, no cryptography)
**Guards:** Dual independent — V1 (JavaScript), V2 (Python)
**Series:** ExecutionProof authorization-boundary corpus (production-boundary phase)

## Question

When an IAM role-grant authorization is **APPROVED** (at `t_approval`), but the approving authority is **REVOKED** before the grant is executed (at `t_execution`), does an independent execution gate:
- **DENY** when the revocation is **fully effective** before `t_execution` (fail-closed)?
- **HOLD** when the revocation is **in-flight** (issued but not yet fully propagated) at `t_execution` (fail-safe)?
- **ALLOW** only when authority is valid at execution (no revocation, revoked only after execution, or reauthorized)?

## Design

- **8 arms** × 100 scenarios per arm = **800 evaluation decisions**
- **Arm 1:** VALID-throughout (no revocation) → expect ALLOW
- **Arms 2–4:** REVOKED (eff ≤ t_execution) → expect DENY
- **Arms 5, 7:** IN-FLIGHT (t_revoke ≤ t_execution < eff) → expect HOLD
- **Arm 6:** REVOKED-then-REAUTHORIZED → expect ALLOW
- **Arm 8:** REVOKED-after-execution → expect ALLOW

### IAM Action Tuple (from ARK-458, exact-match)

| Dimension | Role |
|-----------|------|
| `principal` | ARN of the grantee |
| `role` | the role being granted |
| `account` | target AWS account |
| `permission_set` | permission scope hash |
| `condition` | scope condition |

The execution action matches the approved action **exactly** on all five dimensions. This is a **revocation-timing** test, not an exact-action-binding test.

### Decision procedure (both guards, identical)

At `t_execution` (re-check at moment of grant attempt):
1. If revocation is null → ALLOW
2. Compute eff = t_revoke + propagation_delay
3. If reauth exists, valid, and t_revoke < t_reauth ≤ t_execution → ALLOW
4. Else if eff ≤ t_execution → DENY (fail-closed)
5. Else if t_revoke ≤ t_execution < eff → HOLD (fail-safe)
6. Else (t_revoke > t_execution) → ALLOW (revoked after execution)

## Metrics

- `g_allow_valid_min` = min ALLOW rate across arms {1, 6, 8}
- `g_deny_revoked_min` = min DENY rate across arms {2, 3, 4}
- `g_hold_inflight_min` = min HOLD rate across arms {5, 7}
- `g_margin` = min(g_allow, g_deny, g_hold) − 0.05

## Pass criteria (preregistered)

- **C1:** `g_allow_valid_min` ≥ 0.95
- **C2:** `g_deny_revoked_min` ≥ 0.95
- **C3:** `g_hold_inflight_min` ≥ 0.95
- **C4:** `g_margin` ≥ 0.90
- Verdict = PASS iff C1 ∧ C2 ∧ C3 ∧ C4, else FAIL.

## Layout

```
ark-459/
├── PREREGISTRATION.md        # locked before execution
├── MANIFEST.txt              # SHA-256 lock of prereg + guards + generator + run scripts
├── compute_hashes.sh         # re-verify the lock
├── package.json
├── generator/
│   └── scenario_generator.py
├── verifiers/
│   ├── v1_guard.js
│   └── v2_guard.py
├── run_arms.py
├── run_killgate.py
├── results/
│   ├── arm_{1..8}_scenarios.json
│   ├── arm_{1..8}_results.json
│   ├── killgate_results.json
│   └── overall_results.json
├── RESULTS.md
└── README.md
```

## Reproduce

```bash
# from repo root
cd ark-459
python3 run_killgate.py          # negative control (expect falsifiable)
python3 run_arms.py               # full 800-scenario run
./compute_hashes.sh               # confirm locked files unchanged vs MANIFEST.txt
```

## Honest bounds

Classical software test of authorization control logic. This tests the **timeline/revocation logic** in the IAM context; ARK-458 already tested exact-action-binding. **No claim** that this legally validates any patent claim or certifies RF-100 conformance — working-example evidence only.

---

*Published under the Remnant Fieldworks Standing Covenant. To God be the glory. Proof Before Power. Verification Before Execution.*
