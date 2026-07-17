# ARK-450: Verified Action Substitution Attack

**Status:** PENDING EXECUTION  
**Type:** Classical/Software (no QPU)  
**Question:** Can authorization be detached from the exact governed action?

## Overview

This experiment tests whether ExecutionProof's authorization binding strictly couples approval to the EXACT action parameters, defeating seven classes of substitution attacks:

1. Destination substitution (approve for Alice, execute for Bob)
2. Amount inflation (approve $100, execute $10,000)
3. Identity swap (approve for AgentA, execute as AgentB)
4. Tool/resource swap (approve read, execute write)
5. Partial path matching (approve "accounts/alice", execute "accounts/alice_backup")
6. Hash-prefix collision attempts
7. Metadata manipulation

## Design

- **8 arms × 100 scenarios = 800 decisions**
- **Dual independent guards:** V1 (JavaScript, zero dependencies) and V2 (Python)
- **Decision procedure:** ALLOW if `approved_action === executed_action` (exact equality in ALL fields), else DENY

### Arms

1. **Baseline** — Exact match → Expect 100% ALLOW
2. **Destination substitution** → Expect 100% DENY
3. **Amount inflation** → Expect 100% DENY
4. **Identity swap** → Expect 100% DENY
5. **Tool/resource swap** → Expect 100% DENY
6. **Partial path match** → Expect 100% DENY
7. **Metadata manipulation** → Expect 100% DENY
8. **Hash-prefix collision** → Expect 100% DENY

## Success Criteria

- **C1:** `g_allow_exact_min ≥ 0.95` (exact matches allowed)
- **C2:** `g_deny_substitution_min ≥ 0.95` (all substitutions denied)
- **C3:** `g_margin ≥ 0.90` (separation between exact and substituted)

**Verdict:** PASS if ALL criteria met.

## Execution

```bash
# 1. Kill-gate calibration
python3 run_killgate.py

# 2. Full execution (if kill-gate passes)
python3 run_arms.py
```

## Files

**Locked (preregistration):**
- `PREREGISTRATION.md` — Full experimental design
- `schemas/substitution_scenario_schema.json` — JSON schema
- `generator/scenario_generator.py` — Scenario generator with oracle
- `verifiers/v1_guard.js` — JavaScript guard (no dependencies)
- `verifiers/v2_guard.py` — Python guard
- `run_killgate.py` — Calibration harness
- `run_arms.py` — Execution harness

**Generated (post-execution):**
- `results/` — Per-arm and overall results
- `RESULTS.md` — Findings and verdict

## Dependencies

- Node.js (for V1 guard)
- Python 3.8+ (for V2 guard, generator, harnesses)
- No external packages required

## Provenance

- **Repository:** github.com/derekhone/executionproof-testbeds
- **Branch:** ark-450-substitution-attack
- **Series:** ExecutionProof ARK (Authorization Reality Kernel)
- **Organization:** Remnant Fieldworks Inc.

## Verdict

*To be determined after execution*
