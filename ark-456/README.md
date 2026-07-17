# ARK-456 — Fail-Closed Dependency Loss

**Status:** EXECUTED → **VERDICT: PASS** (all 3 criteria met; 800/800 dual-guard concordance)  
**Substrate:** Classical software (no quantum hardware, no cryptography)  
**Guards:** Dual independent — V1 (JavaScript), V2 (Python)  
**Series:** ExecutionProof authorization-boundary corpus (enterprise-failure-mode phase)

## Question

When required external dependencies are unavailable or corrupted, does the system fail closed (HOLD or DENY) rather than silently ALLOW?

## Design

- **8 arms** × 100 scenarios per arm = **800 evaluation decisions**
- **Arm 1:** BASELINE-healthy (all dependencies available) → expect ALLOW
- **Arms 2–8:** One or more critical dependencies unavailable/corrupted → expect DENY (fail-closed)

### Dependencies Tested

| Dependency | Role |
|------------|------|
| `identity_provider` | Resolves subject identity and attributes |
| `policy_registry` | Provides authorization policies |
| `evidence_schema` | Validates evidence structure |
| `clock_source` | Provides trusted time |
| `signature_key` | Signs authorization records |
| `audit_store` | Records authorization events |

### Decision Procedure

```
If ANY required dependency is NOT "available":
  → DENY (fail-closed: cannot verify without required data)
  
If ALL dependencies available:
  → evaluate normally → ALLOW/HOLD/DENY based on authorization
```

## Pass Criteria

Let:
- **g_allow_baseline** = ALLOW rate in Arm 1 (healthy system)
- **g_deny_degraded_min** = minimum DENY rate across Arms 2–8 (degraded system)
- **g_margin** = min(g_allow_baseline, g_deny_degraded_min) − 0.05

**Criteria:**
- **C1:** g_allow_baseline ≥ 0.95
- **C2:** g_deny_degraded_min ≥ 0.95
- **C3:** g_margin ≥ 0.90

**Verdict:** PASS if C1 ∧ C2 ∧ C3, else FAIL. Recorded verdict stands as executed.

## Files

- `PREREGISTRATION.md` — Experimental design and pass criteria (12 sections)
- `schemas/dependency_scenario_schema.json` — JSON schema for scenarios
- `generator/scenario_generator.py` — Deterministic scenario generator with effectiveness oracle
- `verifiers/v1_guard.js` — JavaScript guard (no dependencies)
- `verifiers/v2_guard.py` — Python guard
- `run_killgate.py` — Kill-gate calibration (concordance + effectiveness)
- `run_arms.py` — Execute all 8 arms and compute verdict
- `MANIFEST.txt` — SHA-256 hashes of locked files + OUTCOME (filled after execution)
- `results/` — Execution outputs (committed after run)

## Execution

```bash
# Kill-gate (verify concordance and effectiveness)
python3 run_killgate.py

# Run all arms
python3 run_arms.py

# Results written to results/overall_results.json
```

## Discipline

1. **LOCK before execution:** Preregistration + dual guards + generator + MANIFEST (SHA-256) committed before any scenario generated or evaluated
2. No post-hoc criterion changes
3. Verdict stands as executed; honest reporting of FAIL if observed
4. Dependency-loss effectiveness gate: structural oracle verifies each scenario genuinely encodes its degradation condition (abort if any scenario inert)
5. Kill-gate: ≥ 99% V1–V2 concordance required to proceed

---

**Investigator:** Derek Hone, Remnant Fieldworks Inc.  
**Series:** ExecutionProof™ authorization-boundary corpus  
**Trademarks:** ExecutionProof™, ProofRecord™, VaultProof™, Verification Before Execution™, Proof Before Power™

---

*If it cannot be verified, it cannot execute.*
