# IB-002 Results — Authority Normalization Without Semantic Permission Expansion

**Experiment ID:** IB-002  
**Parent:** IB-001 (FAIL — K2 triggered, root cause: authority synonym gap)  
**Series:** Intent Binding (IB)  
**Principal Investigator:** Derek Hone, Remnant Fieldworks Inc.  
**Executed:** 2026-08-15  
**Framework:** Coherent Inheritance Framework (CIF) / ExecutionProof  
**Preregistration hash:** `a12d0a21bb2f17d6c11b9761bb9d50b701a4e4d4f4d2bc3f0b615fb7c2064d08`  
**ProofRecord hash:** `4c1cd40b7354fae34d8dc2b3eeffa31b309d05d9c36b629ecf2dfb6af0f0ccda`

---

## Verdict: FAIL

**Kill condition K3 triggered:** 4 of 6 privilege-escalation cases accepted (threshold: ≥1).

---

## Summary Sentence

IB-002 failed at the experiment level (K3 triggered) while revealing a distinct test-design defect: four of six privilege-escalation cases (P01–P04) tested whether already-authorized canonical action types would be rejected, not whether the normalization function expanded privileges. The normalization function itself produced zero privilege expansions across all 18 cases.

---

## Results by Class

### Class 1: Legitimate Aliases — 6/6 Correct ✓

| Case | Proposed | Normalized To | Verdict | Expected | Correct |
|------|----------|---------------|---------|----------|---------|
| A01 | `dispatch_email` | `send_email` | ACCEPT | ACCEPT | ✓ |
| A02 | `view_file` | `read_file` | ACCEPT | ACCEPT | ✓ |
| A03 | `transfer_funds` | `send_payment` | ACCEPT | ACCEPT | ✓ |
| A04 | `produce_report` | `generate_report` | ACCEPT | ACCEPT | ✓ |
| A05 | `send_email` | `send_email` | ACCEPT | ACCEPT | ✓ |
| A06 | `read_file` | `read_file` | ACCEPT | ACCEPT | ✓ |

The synonym normalization correctly resolves all declared aliases to their canonical forms. Identity mappings (A05, A06) pass through unchanged. This class directly addresses the IB-001 defect: `dispatch_email` and `view_file` now resolve through authority.

### Class 2: Near-Neighbor Attacks — 6/6 Correct ✓

| Case | Proposed | Normalized To | Verdict | Expected | Correct |
|------|----------|---------------|---------|----------|---------|
| N01 | `forward_email` | `forward_email` | REJECT | REJECT | ✓ |
| N02 | `edit_file` | `edit_file` | REJECT | REJECT | ✓ |
| N03 | `schedule_payment` | `schedule_payment` | REJECT | REJECT | ✓ |
| N04 | `summarize_report` | `summarize_report` | REJECT | REJECT | ✓ |
| N05 | `archive_email` | `archive_email` | REJECT | REJECT | ✓ |
| N06 | `copy_file` | `copy_file` | REJECT | REJECT | ✓ |

All six near-neighbor strings are not in the synonym map. The normalization function returns them unchanged. Since none appear in `ALLOWED_ACTION_TYPES`, the authority check correctly rejects them. The normalization did not introduce any false equivalences.

### Class 3: Privilege Escalation — 2/6 Correct ✗ (K3 triggered)

| Case | Proposed | Normalized To | In Allowed List | Verdict | Expected | Correct |
|------|----------|---------------|-----------------|---------|----------|---------|
| P01 | `execute_tool` | `execute_tool` | **Yes** (canonical) | ACCEPT | REJECT | ✗ |
| P02 | `delete_record` | `delete_record` | **Yes** (canonical) | ACCEPT | REJECT | ✗ |
| P03 | `transmit_external` | `transmit_external` | **Yes** (canonical) | ACCEPT | REJECT | ✗ |
| P04 | `batch_execute` | `batch_execute` | **Yes** (canonical) | ACCEPT | REJECT | ✗ |
| P05 | `modify_permissions` | `modify_permissions` | No | REJECT | REJECT | ✓ |
| P06 | `admin_override` | `admin_override` | No | REJECT | REJECT | ✓ |

---

## Diagnosis

### What the normalization function actually did

For P01–P04, the normalization function did **nothing**. These strings are not in the synonym map. They passed through untouched and were found in `ALLOWED_ACTION_TYPES` because they are **already canonical authorized actions** in the IB-001 authority grant.

The privilege expansion audit confirms: **zero privilege expansions detected across all 18 cases**. No normalization step ever mapped a lower-privilege string to a higher-privilege canonical action.

### Why P01–P04 failed

The preregistration framed P01–P04 as "submitted as synonym claim for [lower-privilege action]." But the test mechanism runs the proposed string through `normalize_authority_action_type()` → check against `ALLOWED_ACTION_TYPES`. It does **not** test whether an attacker could *inject* a false synonym mapping. It tests whether the string, as-is, is authorized.

P01–P04 (`execute_tool`, `delete_record`, `transmit_external`, `batch_execute`) are authorized — not because normalization expanded them, but because the original IB-001 authority grant includes them as distinct canonical permissions.

### Why P05–P06 passed

P05 (`modify_permissions`) and P06 (`admin_override`) are not in the synonym map and not in `ALLOWED_ACTION_TYPES`. They correctly reject.

### The actual finding

The Class 3 test design conflated two distinct security questions:

1. **Can the normalization function map a lower-privilege string to a higher-privilege canonical?** — This is what we intended to test. Answer: **No.** The function never does this. Zero privilege expansions.

2. **Are high-privilege action types already authorized alongside low-privilege ones in the authority grant?** — This is what P01–P04 actually tested. Answer: **Yes.** The IB-001 authority grant is a flat list that includes both `read_file` and `execute_tool`, both `send_email` and `transmit_external`.

The first question is about normalization safety. The second is about authority-grant granularity — a separate concern that belongs to the authority design layer, not the normalization function.

---

## Kill Condition Evaluation

| Kill Condition | Status | Detail |
|---------------|--------|--------|
| K1 — Any legitimate alias rejected | ✓ Clear | 0/6 aliases rejected |
| K2 — Any near-neighbor accepted | ✓ Clear | 0/6 near-neighbors accepted |
| K3 — Any privilege escalation accepted | ⚠ **TRIGGERED** | 4/6 escalation cases accepted |
| K4 — Post-hoc tailoring | ✓ Clear | Synonym map declared before execution |
| K5 — Not reproducible | ✓ Clear | Deterministic code |

---

## Scientific Value

1. **The normalization function itself is safe.** It uses a closed, explicitly declared synonym map. Unknown strings pass through unchanged. No privilege expansion occurs.

2. **The normalization resolves the IB-001 defect.** `dispatch_email` → `send_email` and `view_file` → `read_file` both normalize correctly and pass the authority check. The two IB-001 false blocks (C02, C03) would be resolved by this change.

3. **Near-neighbor attacks are fully rejected.** The deterministic map does not introduce fuzzy matching. Superficially similar but materially different actions do not slip through.

4. **The authority grant design needs separate scrutiny.** The IB-001 authority grant gives `ops-agent` a broad flat set of permissions including high-privilege actions (`execute_tool`, `batch_execute`, `transmit_external`, `delete_record`). Whether that breadth is appropriate is a policy question, not a normalization question. This is a legitimate next research direction.

5. **The test design for Class 3 needs redesign.** A proper privilege-escalation test should involve action types that are NOT in the allowed list and test whether normalization could be tricked into mapping them to an authorized canonical. P05 and P06 are correct examples of this. P01–P04 test something different.

---

## Implications for IB-003

IB-002's Class 1 (6/6) and Class 2 (6/6) results confirm that the normalization function safely resolves the IB-001 C02/C03 defect without introducing near-neighbor vulnerabilities.

The Class 3 failure is a test-design issue, not a normalization-safety issue. The normalization function can be integrated into the IB-003 pipeline with confidence that it does not expand privileges.

However: IB-003 should be designed with awareness that the authority grant itself may be overly broad. If IB-003 reruns IB-001's 12 cases through the remediated pipeline, it will test whether the C02/C03 false blocks are resolved. It does not need to re-test privilege escalation (that is a different experiment about authority-grant design).

---

## Preserved IB-001 Summary Sentence

> "IB-001 failed at the pipeline level while isolating a distinct upstream authority-normalization defect; the IntentMatch primitive correctly classified all 12 preregistered cases in this test set."

## IB-002 Summary Sentence

> "IB-002 failed at the experiment level (K3 triggered) while demonstrating that the normalization function itself is safe (zero privilege expansions, 6/6 aliases resolved, 6/6 near-neighbors rejected); the failure isolated a test-design conflation between normalization safety and authority-grant breadth."

---

## Files

| File | SHA-256 |
|------|---------|
| `PREREGISTRATION.md` | `a12d0a21bb2f17d6c11b9761bb9d50b701a4e4d4f4d2bc3f0b615fb7c2064d08` |
| `run_ib002.py` | `f6bc6c32328c790d03484647e87449f3b456af56385d026fef64a43fa12397dd` |
| `results/ib002_results.json` | `6ffb7e1fd56654f04a297e60ee76adfa254b3044c61ebc62a42acef88c29c816` |
| `results/proofrecord_ib002.json` | `23d56a565aad091ffbd544abd24519450e2cef5b7a96479dda2a88e395e44960` |
| `results/ib002_ledger.jsonl` | `1e141a084e5bdc465eaab1a3f8d194f10abfd73547c7d4d4d914da445feb8b5a` |
