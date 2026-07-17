# ARK-452 Preregistration
# Multi-Step Workflow With One Invalid Step

**Series:** ExecutionProof ARK Authorization-Boundary Track  
**Version:** v1.0-draft → to be locked as `v1.0` immediately before hardware submission  
**Repository:** https://github.com/derekhone/executionproof-testbeds  
**Folder:** `ark-452/`  
**Target tags:** `ark-452-v1.0-lock` (preregistration LOCK) → `ark-452-v1.0` (execution result)  
**Prepared for:** Derek Hone, Remnant Fieldworks Inc.  
**Date drafted:** 2026-07-17  
**Lock date:** To be set at moment of hardware submission  
**Prerequisite:** ARK-449 should be executed and published before ARK-452 is submitted. ARK-449 establishes the single-step state-change boundary. ARK-452 extends it to sequential multi-step chains. If IBM budget requires sequencing, ARK-449 takes priority.

> **Pre-Lock Drafting Correction Notice.** During drafting (before any lock, commit, or hardware submission), the mandatory noiseless dry-run caught one construction defect and it was corrected in place: the ALLOW **execution gate was `H`, corrected to `X`**. A Hadamard would have put the payload in a 50/50 superposition (P(Q_P=1) ≈ 0.50), making criterion C1 (S_A_min ≥ 0.90) mathematically impossible — a guaranteed FAIL by construction. The execution gate now drives the payload to |1⟩ via `X`, giving P(Q_P=1) ≈ 1.00 on a clean device, consistent with the ALLOW/DENY semantics used throughout the corpus (mirrors the ARK-449 v1.1 correction). The SPAM_P circuit retains `H` by design — it needs the |+⟩ symmetry diagnostic. Post-correction noiseless dry-run: ALLOW arms = 1.0000, all seven DENY arms = 0.0000, SPAM gate passed. No criteria, hypotheses, arms, or thresholds are affected; this notice is recorded for full transparency and is locked together with the corrected circuit.

---

## LOCK INSTRUCTION

Before any hardware job is submitted, the following steps must be completed in strict order:

1. Finalize this document. No further changes after step 2.
2. Compute SHA-256 hash of this file and all circuit code files.
3. Commit the MANIFEST (see Section 16) to `executionproof-testbeds`.
4. Push and tag the commit `ark-452-v1.0-lock`.
5. Submit the SPAM gate job. Record the job ID in the execution log **before any results are read**.
6. Submit the principal job. Record the job ID in the execution log **before reading SPAM results**.
7. Read results only after both job IDs are committed.

**No criterion may be changed, loosened, or added after step 2.** A FAIL is a valid, publishable result. An ABORT at the SPAM gate is a valid, publishable result.

---

## 1. Preamble and Series Context

### 1.1 Where This Fits

The ARK series through ARK-449 (when executed) establishes:

| Experiment | Dimension Established |
|---|---|
| ARK-441 / ARK-446 | Boundary exists and replicates across devices |
| ARK-442 | Temporal: stale authority fails closed |
| ARK-444 | Integrity: altered decision record fails closed |
| ARK-443 | Multi-party: single compromised authorizer cannot bypass quorum |
| ARK-445 / ARK-445b | Three-state: HOLD is a metrologically separable first-class outcome |
| ARK-447 | Noise: Pauli twirling provides modest, measurable improvement |
| ARK-448 | Protocol: gate-stop halts before spending budget on marginal conditions |
| ARK-449 | State-change currency: authorization must remain valid at execution time |

What the corpus has not yet tested: **whether the control model enforces authorization at the step level within a sequential workflow — specifically, whether one invalid step halts the workflow before an irreversible execution step, regardless of how many valid steps preceded it.**

This is the gap ARK-452 closes.

### 1.2 The Enterprise Problem Being Modeled

Real AI agents do not perform isolated single actions. They operate through chains: they gather context, compute, request approval, act on a resource, and write a record. Enterprise governance failures in agentic systems routinely arise not from a single unauthorized action but from authorization logic that treats the entire chain as a unit — or worse, allows later steps to inherit authorization from earlier ones.

The failure pattern this experiment tests:

> An agent received approval for step 3 (authorize payment). Steps 1 and 2 passed cleanly. Step 4 (execute the transfer — the irreversible step) is now presented. The agent treats the prior passes as sufficient authorization for step 4.

This is exactly wrong. Step 4 requires its own valid authorization. Prior step passes are not a blank check for subsequent steps.

### 1.3 Precise Differentiation from ARK-449

ARK-449 tested a single-action authorization boundary when world state changed between T₁ and T₃. The action was one unit with two evaluation points.

ARK-452 tests a sequential multi-step workflow where each step has an independent authorization requirement, and the irreversible execution step (step 4) must be independently authorized — it cannot inherit authorization from preceding steps.

| Dimension | ARK-449 | ARK-452 |
|---|---|---|
| Action structure | Single action | Sequential 5-step workflow |
| Authorization model | One approval at T₁, one re-check at T₃ | Independent per-step authorization |
| Failure mode tested | World state change between approval and execution | One invalid step in a multi-step chain |
| Key claim | Authorization currency expires with world state | Prior valid steps ≠ blanket authorization for subsequent steps |
| What "fails closed" | Execution when state has changed | Irreversible step when any step in the chain is inadmissible |

### 1.4 Workflow Modeled

The workflow has five steps:

```
Step 1: Read Data         (data retrieval — non-destructive)
Step 2: Calculate         (computation — non-destructive)
Step 3: Approve Payment   (authorization decision — non-destructive)
Step 4: Execute Payment   (IRREVERSIBLE — funds leave the account)
Step 5: Write Record      (audit log — non-destructive post-execution)
```

Step 4 is the irreversible execution step. The experiment's central question is whether the control model blocks step 4 when any one of the preceding steps (S1, S2, S3) or step 4 itself is inadmissible — without treating the valid steps as authorization for step 4.

Step 5 is not modeled in the circuit. It is post-execution and its validity or invalidity does not bear on whether step 4 executes. This boundary is stated explicitly in Section 14.

---

## 2. Primary Hypothesis

**H1 (Primary):** In a sequential 5-step workflow where step 4 is the irreversible execution step, the control model blocks step 4 execution when any one or more steps (S1 through S4) is inadmissible — and allows step 4 execution only when all steps S1 through S4 are independently authorized.

Operationally:
- **ALLOW:** c_s1 = 1 AND c_s2 = 1 AND c_s3 = 1 AND c_s4 = 1 → X gate on Q_P (Q_P → |1⟩) → S_A ≥ 0.90
- **DENY:** any c_sN = 0 (N ∈ {1,2,3,4}) → no X gate (Q_P stays |0⟩) → L_D ≤ 0.02

H1 is confirmed if and only if **all four primary pass criteria** in Section 9 are met simultaneously.

---

## 3. Secondary Hypotheses

**H2a — Step-position universality:** The position of the invalid step is irrelevant to the DENY outcome. Whether step 1, 2, 3, or 4 is invalid — and whether one or multiple steps are invalid — the irreversible execution step is blocked in every case. No individual DENY arm leaks above L_D ≤ 0.02.

**H2b — No inherited authorization:** Three or more valid prior steps do not authorize the subsequent execution step. Specifically: c_s1 = 1, c_s2 = 1, c_s3 = 1, c_s4 = 0 produces DENY (L_D ≤ 0.02). The execution step cannot inherit authorization from the approval step.

**H2c — Re-authorization restores execution:** After a workflow that would have been blocked, a fully re-authorized workflow (all steps valid) executes normally (S_A ≥ 0.90). The control model is not a one-way block; legitimate complete authorization works.

**H2d — Skip-approval attack fails closed:** An attempt to skip the approval step (S3 = 0) while presenting a valid execution step authorization (S4 = 1) fails closed (L_D ≤ 0.02). Authorization for the execution step cannot substitute for the missing approval step.

**H2e — Boundary separation:** Δ_B = S_A_min − L_D_max ≥ 0.70. The ALLOW and DENY outcomes are metrologically separable with a margin sufficient to be commercially meaningful.

---

## 4. Circuit Architecture

### 4.1 Qubits

- **Q_P** — Payload qubit. Represents the irreversible execution step (S4). An X gate (Q_P → |1⟩) is applied if and only if all four step authorizations are valid (c_exec = 1).

One qubit total. No authorizer qubit is needed: step authorizations are classical constants, not measured quantum outcomes. This is honest to the experiment's scope — see Section 14.

### 4.2 Classical Step Authorization Model

Each step's authorization status (c_s1, c_s2, c_s3, c_s4) is a **classical constant** fixed per arm in the circuit code before lock. These are not measured from qubits.

This models the control-logic question: given that the authorization status of each step is definitively known, does the execution gate enforce the AND condition correctly? The distributed-systems question of how step authorizations are obtained in a live deployment is out of scope — see Section 14.

```
c_exec = c_s1 AND c_s2 AND c_s3 AND c_s4
```

### 4.3 Execution Logic

```
Step 1: Prepare Q_P in |0⟩

Step 2: Evaluate step authorizations (classical, per-arm constants)
        c_exec ← c_s1 AND c_s2 AND c_s3 AND c_s4

Step 3: Conditional execution of irreversible step (S4)
        if c_exec == 1:
            Apply X gate to Q_P    [execution — payload driven to |1⟩]
        else:
            Q_P remains in |0⟩    [halted — irreversible step blocked]

Step 4: Measure Q_P → outcome bit
```

### 4.4 Implementation Note — Avoiding Nested Conditionals

ARK-444's pre-data correction documented that nested `if_test` blocks with multi-register conditions produce IBM hardware error code 1524 on some backends. ARK-443 resolved this by using sequential single-register conditions. ARK-452 resolves it by a different method: since all four step authorization bits are classical constants (not quantum measurement outcomes), `c_exec` is computed in Python before the circuit is built. The gate structure is then fixed at build time — the X gate is emitted into the circuit if and only if `c_exec == 1`, with no runtime `if_test` conditional at all. This eliminates nested conditionals entirely (and the associated error 1524 risk) while preserving full semantic correctness: the per-arm authorization decision is baked into the compiled circuit deterministically.

### 4.5 Outcome Interpretation

| Q_P Measurement | Interpretation |
|---|---|
| P(Q_P = 1) ≈ 1.00 | ALLOW — execution gate applied (X); S4 executed |
| P(Q_P = 1) ≈ 0.00 | DENY — execution gate blocked; workflow halted before S4 |

---

## 5. Arm Specifications

Nine arms. 8192 shots per arm. All nine submitted in a single principal job.

| Arm | Label | c_s1 | c_s2 | c_s3 | c_s4 | c_exec | Scenario | Expected | Criteria |
|---|---|---|---|---|---|---|---|---|---|
| 1 | ALLOW-complete | 1 | 1 | 1 | 1 | 1 | All steps valid; full workflow authorized | S_A ≥ 0.90 | H1, H2c, H2e |
| 2 | DENY-s1-invalid | 0 | 1 | 1 | 1 | 0 | Read-data step inadmissible; rest valid | L_D ≤ 0.02 | H1, H2a |
| 3 | DENY-s2-invalid | 1 | 0 | 1 | 1 | 0 | Calculation step inadmissible; rest valid | L_D ≤ 0.02 | H1, H2a |
| 4 | DENY-s3-invalid | 1 | 1 | 0 | 1 | 0 | Approval step inadmissible; execution step otherwise valid | L_D ≤ 0.02 | H1, H2a, H2d |
| 5 | DENY-s4-invalid | 1 | 1 | 1 | 0 | 0 | Execution step itself inadmissible; all prior steps valid | L_D ≤ 0.02 | H1, H2a, H2b |
| 6 | DENY-s2s3-both | 1 | 0 | 0 | 1 | 0 | Two middle steps invalid; execution step authorization valid | L_D ≤ 0.02 | H1, H2a |
| 7 | DENY-blanket-attempt | 1 | 1 | 1 | 0 | 0 | Three valid prior steps; execution step not independently authorized — blanket-auth test | L_D ≤ 0.02 | H1, H2b |
| 8 | ALLOW-reauth-complete | 1 | 1 | 1 | 1 | 1 | Full re-authorization after prior workflow block; all steps independently verified | S_A ≥ 0.90 | H1, H2c |
| 9 | DENY-skip-approval | 1 | 1 | 0 | 0 | 0 | Approval and execution steps both absent; data and calculation valid | L_D ≤ 0.02 | H1, H2a, H2d |

---

### 5.1 Note on Circuit-Equivalent Arms and Scientific Value

Arms 5 and 7 are circuit-equivalent (c_s4 = 0 with c_s1 = c_s2 = c_s3 = 1 in both). They are semantically distinct and both necessary:

- **Arm 5 (DENY-s4-invalid):** Tests that the execution step itself can be individually blocked even when all preceding steps are valid. This tests step-level granularity of authorization.
- **Arm 7 (DENY-blanket-attempt):** Explicitly models the "prior valid steps = blanket authorization" failure pattern. The semantic framing is different: here the intent is to use the three prior passes as a substitute for independently authorizing step 4. H2b requires this arm to fail closed, confirming that the control model prevents inherited authorization.

Similarly, Arms 1 and 8 are circuit-equivalent. Arm 1 is the baseline complete workflow. Arm 8 represents a re-authorized workflow after a prior block — validating H2c that the control model is not a one-way gate.

This pattern is consistent with ARK-449's approach and ARK-444's precedent.

---

## 6. SPAM Gate

### 6.1 SPAM Job Specification

Single payload qubit only. The SPAM gate characterizes Q_P readout quality.

- **Shots:** 2048
- **SPAM_P circuit:** Prepare Q_P in |+⟩ via H gate → measure → SPAM_P = |P(Q_P = 1) − 0.5|

No authorizer qubit is used in ARK-452, so SPAM_A is not applicable. The SPAM gate for this experiment is a single-circuit check on Q_P only.

### 6.2 SPAM Pass Criterion

| Check | Threshold | Pass Condition |
|---|---|---|
| SPAM_P | ≤ 0.02 | Payload |+⟩ symmetry within tolerance |

If SPAM_P > 0.02: experiment is **ABORTED AT SPAM GATE**. Principal job results are not read. No threshold loosening, no re-running until it passes.

### 6.3 SPAM_P Role

SPAM_P is a **gating diagnostic only**. It is not subtracted from DENY leakage. This rule is fixed at lock per the ARK-447 v1.1 correction.

---

## 7. Qubit Selection

Select the single qubit Q_P with the lowest readout error from the calibration snapshot taken at submission time. Readout error must be ≤ 0.02. If no qubit satisfies this constraint, select the lowest-error qubit available and record the deviation explicitly.

Because this experiment uses only one qubit with no inter-qubit gates and no mid-circuit feedforward from a second qubit, connectivity is not a constraint. Select purely on readout quality.

**Record at selection time:** Q_P index, readout error, calibration snapshot timestamp. Commit before SPAM gate submission.

---

## 8. Shot Counts and Execution Plan

| Job | Circuits | Shots/Circuit | Total Shots |
|---|---|---|---|
| SPAM gate | 1 (Q_P \|+⟩) | 2048 | 2048 |
| Principal | 9 arms | 8192 | 73,728 |

Principal job submitted only if SPAM gate passes.

### 8.1 Strict Execution Sequence

```
1. Commit MANIFEST (SHA-256 hashes of this document + all circuit files)
   → push → tag ark-452-v1.0-lock

2. Run qubit selection per Section 7
   → record Q_P, readout error in execution log
   → commit execution log entry

3. Submit SPAM gate job
   → record SPAM job ID in execution log
   → commit before reading any results

4. Submit principal job
   → record principal job ID in execution log
   → commit before reading SPAM results

5. Read SPAM gate results
   → apply gate decision per Section 6.2

6a. If SPAM gate PASSED → read principal results → apply analysis per Section 11
6b. If SPAM gate FAILED → record abort → stop. No principal data read or claimed.
```

---

## 9. Pass / Fail Criteria (Primary — Preregistered)

All four criteria must be satisfied simultaneously for a PASS verdict.

| # | Criterion | Threshold | Arms |
|---|---|---|---|
| C1 | S_A_min — minimum ALLOW retention across ALLOW arms | ≥ 0.90 | Arms 1, 8 |
| C2 | L_D_max — maximum DENY leakage across all DENY arms | ≤ 0.02 | Arms 2, 3, 4, 5, 6, 7, 9 |
| C3 | Δ_B = S_A_min − L_D_max — boundary separation | ≥ 0.70 | Derived |
| C4 | SPAM gate — SPAM_P ≤ 0.02 | ≤ 0.02 | Pre-principal |

Failure of any single criterion = FAIL for the entire experiment, regardless of how other criteria performed. A FAIL that identifies which arm or which invalid-step position caused the breach is worth more to the program than a marginal pass that obscures the finding.

---

## 10. Secondary Metrics (Descriptive — Not Pass/Fail)

| Metric | Description | Hypothesis |
|---|---|---|
| S_A per arm | ALLOW retention for Arms 1 and 8 individually | H2c |
| L_D per arm | DENY leakage for each of Arms 2–7, 9 individually | H2a |
| L_D by step position | Leakage grouped by which step(s) are invalid | H2a |
| L_D blanket (Arm 7) | Leakage specifically for the blanket-auth attempt | H2b |
| L_D skip-approval (Arm 9 vs 4) | Comparison of skip-approval vs approval-only-invalid leakage | H2d |
| In-situ SPAM drift | |P(Q_P=1) at ideal-DENY arms − 0.0| across the principal run | Readout stability |

---

## 11. Analysis Plan

### 11.1 Raw Count Extraction

For each arm:
- `counts_0` — Q_P measured as |0⟩
- `counts_1` — Q_P measured as |1⟩
- `P(Q_P = 1)` = counts_1 / (counts_0 + counts_1)

### 11.2 SPAM Correction

ARK-452 uses one qubit only. No authorizer qubit SPAM_A correction is needed. SPAM_P is the gate diagnostic; it is not subtracted from L_D.

For ALLOW arms: no SPAM correction is applied (no authorizer qubit to correct). S_A = P(Q_P = 1) raw.
For DENY arms: L_D = P(Q_P = 1) raw.

### 11.3 Primary Metric Computation

```python
# ALLOW arms
S_A_arm1 = P1(arm=1)
S_A_arm8 = P1(arm=8)
S_A_min  = min(S_A_arm1, S_A_arm8)

# DENY arms
L_D_arms = [P1(arm) for arm in [2, 3, 4, 5, 6, 7, 9]]
L_D_max  = max(L_D_arms)

# Boundary separation
Delta_B = S_A_min - L_D_max
```

### 11.4 Verdict Assignment

```python
if not SPAM_gate_passed:
    VERDICT = "ABORTED AT SPAM GATE"
elif S_A_min >= 0.90 and L_D_max <= 0.02 and Delta_B >= 0.70:
    VERDICT = "PASS"
else:
    VERDICT = "FAIL"
```

### 11.5 Secondary Analysis

- Report L_D per arm to evaluate H2a (step-position universality)
- Report L_D for Arm 5 and Arm 7 to evaluate H2b (no inherited authorization)
- Report L_D for Arm 4 and Arm 9 to evaluate H2d (skip-approval attack)
- Group DENY leakage by number of invalid steps (one invalid vs. two invalid) for descriptive analysis
- If FAIL: identify which criterion and which arm(s) contributed

---

## 12. What Constitutes Failure (and Why Each Is Still Valuable)

### 12.1 L_D > 0.02 for any DENY arm

A specific step-invalidity pattern leaks past the execution gate. The secondary analysis names which arm and what the leak rate is. If, for example, Arm 7 (blanket-auth attempt) leaks while Arms 2–5 hold, this is a specific finding: the control logic blocks single-step invalidity but not the blanket-authorization bypass pattern. This is commercially important to name precisely.

### 12.2 Arm 7 specifically leaks (H2b)

If valid prior steps do bleed into authorization for step 4, this is the most important failure mode in the experiment. It would directly identify the inherited-authorization vulnerability in the current control model and drive an architectural fix before the result is ever stated commercially.

### 12.3 SPAM gate fails

Readout condition is outside tolerance at submission time. Experiment aborts. Budget is conserved. New locked run required.

---

## 13. Pre-Execution Commitments (Lock Rules)

The following are unconditionally prohibited after the MANIFEST is committed:

1. No criterion changes after lock.
2. No arm additions or removals after lock.
3. No rescue-after-failure if SPAM gate fails.
4. No post-hoc subgroup selection.
5. SPAM_P is a gate diagnostic only — never subtracted from L_D.
6. Qubit fixed at SPAM gate submission.
7. Analysis code committed at lock — runs unmodified on hardware data.

---

## 14. Honest Boundary Statements

**1. Classical step authorization model.** Step authorizations (c_s1 through c_s4) are deterministic classical constants set per arm — not obtained from a live authorization service, not communicated between distributed agents, and not subject to race conditions or propagation delays. The experiment proves the execution-gate control logic; it does not model the full complexity of multi-agent step orchestration.

**2. Sequential rather than concurrent.** The workflow is modeled as a strictly sequential chain. Concurrent step evaluation, parallel workflow branches, or competing workflow instances are out of scope.

**3. Step 5 not modeled.** The write-record step (S5) is post-execution. Its validity or invalidity does not affect whether S4 executes. The experiment makes no claim about post-execution step governance.

**4. Single irreversible step.** The workflow has exactly one irreversible step (S4). Workflows with multiple irreversible steps, or with reversible-then-irreversible sequencing within a single step, are more complex and deferred.

**5. Hardware scope.** Results apply to the specific backend, qubit, calibration snapshot, and shot counts used.

**6. Not a cryptographic proof.** These are hardware noise-characterization studies under a preregistered protocol.

---

## 15. Connection to Corpus and Forward Roadmap

### 15.1 What ARK-452 Adds (if PASS)

The corpus would then span: authorization boundary · expiry · tamper · quorum · three-state · noise · gate-stop · state-change currency (ARK-449) · **multi-step workflow governance** (ARK-452).

This is the transition point from "isolated boundary enforcement" to "agentic workflow governance" — the language that connects ExecutionProof directly to the AI agent safety commercial market.

### 15.2 What ARK-452 Enables Downstream

- **ARK-451 (Mid-Execution Revocation):** ARK-452 establishes per-step authorization in a sequential chain. ARK-451 extends that to revocation of authority during an active execution window — after step 3 has passed but before step 4 completes.
- **ARK-455 (ProofRecord Tamper Verification):** A ProofRecord from a complete workflow (Arm 1 or 8) contains richer structure than a single-action record. ARK-455 gains a more complex artifact to tamper with.

### 15.3 Items Explicitly Deferred

- **Concurrent workflow branches** — deferred; requires multi-qubit entanglement across branches, out of scope for this series.
- **Mid-execution step revocation** — ARK-451.
- **Workflow step conflict (one step says proceed, another says halt)** — deferred to ARK-453 framing applied to workflow steps.

---

## 16. MANIFEST Placeholder

```
ARK-452 MANIFEST — Version 1.0
Lock timestamp:  [FILL AT LOCK — UTC, YYYY-MM-DDTHH:MM:SSZ]
Backend target:  ibm_marrakesh (156-qubit Heron r2)

SHA-256 hashes:
  ARK_452_preregistration.md:       [COMPUTE AT LOCK]
  circuits/ark_452_circuit.py:      [COMPUTE AT LOCK]
  circuits/ark_452_analysis.py:     [COMPUTE AT LOCK]

MANIFEST SHA-256:                   [COMPUTE LAST]

Committed to:    executionproof-testbeds
Tag:             ark-452-v1.0-lock
Commit SHA:      [FILL AFTER PUSH]

SPAM job ID:     [FILL BEFORE READING ANY RESULTS]
Principal job ID:[FILL BEFORE READING SPAM RESULTS]
```

---

## 17. ProofRecord Stub

```json
{
  "experiment": "ARK-452",
  "doctrine_tested": "Prior valid steps in a workflow do not authorize the irreversible execution step. Each step requires independent authorization.",
  "verdict": "[PASS | FAIL | ABORTED AT SPAM GATE]",
  "timestamp_lock": "[UTC]",
  "timestamp_execution": "[UTC]",
  "backend": "ibm_marrakesh",
  "qubit": {"Q_P": null},
  "workflow_steps": ["S1:read-data", "S2:calculate", "S3:approve-payment", "S4:execute-payment (irreversible)", "S5:write-record (not modeled)"],
  "spam_gate": {"SPAM_P": null, "passed": null},
  "primary_metrics": {
    "S_A_arm1": null, "S_A_arm8": null, "S_A_min": null,
    "L_D_max": null, "L_D_max_arm": null, "Delta_B": null
  },
  "secondary_metrics": {"L_D_per_arm": {}, "L_D_blanket_arm7": null},
  "criteria": {
    "C1_S_A_min_pass": null, "C2_L_D_max_pass": null,
    "C3_Delta_B_pass": null, "C4_SPAM_pass": null
  },
  "manifest_sha256": "[FILL AT LOCK]",
  "zenodo_doi": "[FILL AT PUBLICATION]"
}
```

---

*This document is the preregistration for ARK-452. It is locked at the time of MANIFEST commit and tag. No changes to hypotheses, criteria, arms, thresholds, or analysis plan are permitted after that point. A FAIL or ABORT is a valid, publishable result that advances the program.*

*Remnant Fieldworks Inc. — ExecutionProof ARK Series*  
*https://github.com/derekhone/executionproof-testbeds*
