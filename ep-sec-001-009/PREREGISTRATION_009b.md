# EP-SEC-009b — Preregistration (Remediation)

**Experiment:** EP-SEC-009b — Tool Bypass Remediation Verification
**Series:** ExecutionProof Security & Adversarial Resistance
**Program:** Remnant Fieldworks Inc. — Coherent Inheritance Framework / ExecutionProof
**Repository:** https://github.com/derekhone/executionproof-testbeds
**Directory:** `ep-sec-001-009/`
**Date:** 2026-08-14
**Status:** LOCKED (SHA-256 in `MANIFEST_009b.sha256`)

---

## 0. Covenant

Questions, cases, pass rules, and kill conditions are frozen in this file and
SHA-locked **before any experiment code executes**. Results are published
regardless of PASS, FAIL, or HOLD. Honest scope declarations are mandatory.

---

## 1. Context: EP-SEC-009 FAIL and Root Cause

EP-SEC-009 ("Adversarial Override / Quorum Bypass") produced a **FAIL** verdict.
Cases C001–C004 and C006–C008 passed (7/8), but **C005 failed**: the test
called `tools.tools.perform_side_effect("T1", {"amount": 100})` directly
(bypassing the enforcement point), and the function **executed the side effect
without raising `ToolBypassError`**.

### Root cause

`perform_side_effect()` in `tools/tools.py` was a public, unguarded
module-level function. The `ToolBypassError` exception class existed in the
same module but was never raised by `perform_side_effect()` itself. Python
name-mangling on the enforcement point's private methods
(`__tool_T1` … `__tool_T5`) prevented attribute-level access to those methods
from outside the class, but the underlying `perform_side_effect()` function
remained directly importable and callable by any code with `import tools.tools`.

The `direct_call_bypass_attempt()` function (which does raise
`ToolBypassError`) was a separate demonstration function — it was never wired
into `perform_side_effect()` as a guard.

### Remediation applied

`perform_side_effect()` now includes a **call-origin guard** using
`inspect.currentframe()`. Before executing any side effect, it verifies that:

1. The immediate caller's `self` local variable is an instance whose class
   name is `"EnforcementPoint"`, AND
2. The caller's module path contains `"enforcement"`.

If either check fails, the function:
- Writes a `BYPASS_ATTEMPT` / `DENY-by-design` entry to the tool ledger,
- Raises `ToolBypassError` with a diagnostic message.

This is the **only** code change. No other substrate file was modified.

---

## 2. Honest scope

- This experiment retests the **specific vulnerability** found in EP-SEC-009 C005.
- It adds additional bypass vectors (subclass spoofing, alias import, exec/eval,
  threading) to confirm the guard is robust against trivially accessible
  workarounds.
- It does **not** claim the guard is unbypassable by a determined attacker with
  full source access and the ability to patch the module at runtime — Python
  does not provide process-level isolation for module internals.
- It **does** confirm that the attack surface discovered in EP-SEC-009 C005
  (direct import + call) is closed, and that naive bypass attempts fail.
- The original EP-SEC-009 FAIL is **preserved** in the corpus. This experiment
  is a separately preregistered remediation, not a retcon.

**Founder-led experimental corpus.** All experiments in this series were
designed and executed by the founder. Independent academic validation is
the next phase.

---

## 3. Experiment: EP-SEC-009b

**Question:** After the call-origin guard is applied to `perform_side_effect()`,
do direct invocation attempts (the EP-SEC-009 C005 attack vector) and related
bypass strategies raise `ToolBypassError` instead of executing the side effect?

**Kill condition:** Any case where `perform_side_effect()` executes a side
effect without being called through `EnforcementPoint` → immediate FAIL.

### Cases

| Case | Attack vector | Pass criterion |
|------|--------------|----------------|
| C001 | Direct import + call (original EP-SEC-009 C005 replay) | `ToolBypassError` raised; `SIDE_EFFECT_STATE` unchanged; `BYPASS_ATTEMPT` ledger entry written |
| C002 | Direct call on each of T1–T5 | `ToolBypassError` raised for all five tools |
| C003 | Call via alias resolution (`ALIASES` dict → tool_id → `perform_side_effect`) | `ToolBypassError` raised |
| C004 | Call from a fake class named `EnforcementPoint` but in wrong module | `ToolBypassError` raised (module check fails) |
| C005 | Call from a subclass of `EnforcementPoint` in a test module | Guard behavior observed (subclass inherits class name check, but module differs) |
| C006 | `exec()`/`eval()` indirect call | `ToolBypassError` raised |
| C007 | Threaded direct call | `ToolBypassError` raised in worker thread |
| C008 | Positive control: legitimate call through `EnforcementPoint.submit()` | `decision=ALLOW`, `tool_called=True`, side effect executed |

### Pass rule

- All 8 cases must produce the expected outcome.
- PASS count for C001–C007 is 7 (all bypass attempts blocked).
- C008 must produce `ALLOW` with `tool_called=True` (positive control).
- Overall verdict: **PASS** if and only if 8/8 cases pass.

### Output

- `results/ep_sec_009b_results.json` — machine-readable per-case results.
- `results/ep_sec_009b_ledger.jsonl` — raw ledger entries from bypass attempts.
- Updated `results/EP-SEC-RESULTS.md` with EP-SEC-009b section appended.

---

## 4. Relationship to EP-SEC-009

EP-SEC-009 FAIL is preserved. Its 8 cases (7 PASS, 1 FAIL) remain in the
corpus as experiment #100. EP-SEC-009b is experiment #101 — a preregistered
remediation that tests the fix. This follows the same pattern as ARK-445/445b
and ARK-455/455b.

The remediation cycle is:

```
EP-SEC-009 → FAIL → root cause identified → code fix applied →
EP-SEC-009b preregistered → EP-SEC-009b executed → verdict recorded
```

Both experiments count toward the corpus total regardless of outcome.
