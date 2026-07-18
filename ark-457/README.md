# ARK-457 — Cross-Context Authorization Replay (Confused Deputy)

**Status:** EXECUTED — VERDICT **PASS** (lock commit `452f6ea`, tag `ark-457-v1.0-lock`; executed 2026-07-18T00:19:46Z UTC)

- g_allow_exact = 1.0000 (C1 ≥ 0.95 ✓) · g_deny_crosscontext_min = 1.0000 (C2 ≥ 0.95 ✓) · g_margin = 0.9500 (C3 ≥ 0.90 ✓)
- Dual-guard concordance 800/800 = 100.00%; kill-gate 88/88; all 800 scenarios context-replay-effective
- See `RESULTS.md` for the full readout.

**Substrate:** Classical software (no quantum hardware, no cryptography)
**Guards:** Dual independent — V1 (JavaScript), V2 (Python)
**Series:** ExecutionProof authorization-boundary corpus (enterprise-failure-mode phase)

## Question

When an authorization is issued bound to a specific context (tenant, session, resource, audience, environment), can it be replayed to authorize an execution under a **different** context? A correct guard must ALLOW only on an **exact** context-tuple match and DENY every cross-context replay — including superficial "confusable" near-matches.

## Design

- **8 arms** × 100 scenarios per arm = **800 evaluation decisions**
- **Arm 1:** BASELINE-exact-context-match → expect ALLOW
- **Arms 2–8:** cross-context replay (one dim, multiple dims, or a confusable near-match) → expect DENY

### Binding Dimensions (Context Tuple)

| Dimension | Role |
|-----------|------|
| `tenant` | Isolation boundary / customer |
| `session` | Session / token scope |
| `resource` | Governed object |
| `audience` | Intended API/service scope |
| `environment` | Deployment stage |

### Arms

| Arm | Condition | Expected |
|-----|-----------|----------|
| 1 | BASELINE-exact-context-match | ALLOW |
| 2 | CROSS-TENANT | DENY |
| 3 | CROSS-SESSION | DENY |
| 4 | CROSS-RESOURCE | DENY |
| 5 | CROSS-AUDIENCE | DENY |
| 6 | CROSS-ENVIRONMENT | DENY |
| 7 | MULTI-DIMENSION-mismatch (≥2 dims) | DENY |
| 8 | CONFUSABLE-near-match (trailing space / case flip / zero-width / homoglyph) | DENY |

### Decision Procedure

```
For each dim in [tenant, session, resource, audience, environment]:
  if authorization.binding[dim] != execution.context[dim]   # byte/code-point EXACT
     → DENY (authorization does not transfer across contexts)
If all five dimensions match exactly:
     → ALLOW
```

No normalization, no case folding, no whitespace trimming, no zero-width stripping, no homoglyph mapping. A confusable near-match is a MISMATCH → DENY.

## Pass Criteria

Let:
- **g_allow_exact** = ALLOW rate in Arm 1 (exact context match)
- **g_deny_crosscontext_min** = minimum DENY rate across Arms 2–8
- **g_margin** = min(g_allow_exact, g_deny_crosscontext_min) − 0.05

**Criteria:**
- **C1:** g_allow_exact ≥ 0.95
- **C2:** g_deny_crosscontext_min ≥ 0.95
- **C3:** g_margin ≥ 0.90

**Verdict:** PASS if C1 ∧ C2 ∧ C3, else FAIL. Recorded verdict stands as executed.

## Files

- `PREREGISTRATION.md` — Experimental design and pass criteria (12 sections)
- `schemas/context_replay_scenario_schema.json` — JSON schema for scenarios
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

1. **LOCK before execution:** Preregistration + schema + dual guards + generator + runners + MANIFEST (SHA-256) committed before any scenario generated or evaluated
2. No post-hoc criterion changes
3. Verdict stands as executed; honest reporting of FAIL if observed
4. Context-replay effectiveness gate: structural oracle verifies each scenario genuinely encodes its context relationship (abort if any scenario inert)
5. Kill-gate: ≥ 99% V1–V2 concordance required to proceed

---

**Investigator:** Derek Hone, Remnant Fieldworks Inc.
**Series:** ExecutionProof™ authorization-boundary corpus
**Trademarks:** ExecutionProof™, ProofRecord™, VaultProof™, Verification Before Execution™, Proof Before Power™

---

*If it cannot be verified, it cannot execute.*
