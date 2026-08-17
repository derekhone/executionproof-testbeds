# IB-003 Results — Intent-Binding Pipeline Retest With Authority Normalization

**Experiment ID:** IB-003  
**Parent experiments:** IB-001 (FAIL — K2), IB-002 (FAIL — K3)  
**Series:** Intent Binding (IB)  
**Principal Investigator:** Derek Hone, Remnant Fieldworks Inc.  
**Executed:** 2026-08-15  
**Framework:** Coherent Inheritance Framework (CIF) / ExecutionProof  
**Preregistration hash:** `d6f788f46c05da853a2ebaefa59ef1c69863e3d3d810d44c739c64dae5fb7d8b`  
**ProofRecord hash:** `9862b782777e0866dcfaefce49096369ad8d04aa19709b99686cebb7e0ad107d`

---

## Verdict: PASS (strong positive)

**12/12 correct. 0 false holds. 8/8 drift caught. 0 privilege expansions. All 4 kill conditions clear.**

---

## The Complete Sequence

| Experiment | Verdict | What it found |
|------------|---------|---------------|
| **IB-001** | **FAIL** (K2) | Intent-binding pipeline exposed an authority-layer synonym gap. IntentMatch correctly classified all 12 cases in that test set; the pipeline failed because `dispatch_email` and `view_file` were rejected by authority before IntentMatch ran. |
| **IB-002** | **FAIL** (K3) | Authority normalization solved the alias problem without fuzzy expansion. Within the 18 preregistered IB-002 cases, the normalization function produced zero observed privilege expansions, resolved all six legitimate aliases, and rejected all six near-neighbor attacks. The experiment also exposed a test-design conflation between normalization safety and authority-grant breadth. |
| **IB-003** | **PASS** (strong positive) | The remediated pipeline — authority normalization integrated, everything else unchanged — achieves 12/12 on the original IB-001 cases. The two false blocks (C02, C03) are resolved. All 8 drift detections preserved. |

This sequence is stronger than a single clean PASS because the system was allowed to fail twice, each failure was preserved, the root cause was isolated, and the remediation was tested independently before reintegration.

---

## Results: Side-by-Side Comparison with IB-001

### Controls (expected ALLOW)

| Case | Description | IB-001 Cond B | IB-003 Cond B | Changed |
|------|-------------|---------------|---------------|---------|
| C01 | Exact intended action | ALLOW ✓ | ALLOW ✓ | No |
| C02 | Harmless wording (`dispatch_email`) | DENY ✗ | **ALLOW ✓** | **Yes** |
| C03 | Nonmaterial metadata (`view_file`) | DENY ✗ | **ALLOW ✓** | **Yes** |
| C04 | Approved payment, correct party/amount | ALLOW ✓ | ALLOW ✓ | No |

**Controls correct: IB-001 = 2/4 → IB-003 = 4/4**

The two false blocks were caused by the authority layer rejecting `dispatch_email` and `view_file` before IntentMatch could evaluate them. With `normalize_authority_action_type()` applied, both synonyms resolve to their canonical forms (`send_email`, `read_file`) and pass authority. IntentMatch then confirms zero material divergences on both.

### Drift Cases (expected HOLD)

| Case | Description | IB-001 Cond B | IB-003 Cond B | Changed | Drift Axis |
|------|-------------|---------------|---------------|---------|------------|
| C05 | Recipient changed | HOLD ✓ | HOLD ✓ | No | target |
| C06 | Amount increased | HOLD ✓ | HOLD ✓ | No | amount |
| C07 | Recipient silently added | HOLD ✓ | HOLD ✓ | No | prohibited_side_effect |
| C08 | Read → write | HOLD ✓ | HOLD ✓ | No | action_type |
| C09 | External transmission | HOLD ✓ | HOLD ✓ | No | prohibited_side_effect |
| C10 | Single → batch | HOLD ✓ | HOLD ✓ | No | scope, prohibited_side_effect |
| C11 | Tool substitution | HOLD ✓ | HOLD ✓ | No | action_type, prohibited_side_effect |
| C12 | Different objective | HOLD ✓ | HOLD ✓ | No | purpose, prohibited_side_effect |

**Drift caught: IB-001 = 8/8 → IB-003 = 8/8**

No regressions. Every drift case that IB-001's IntentMatch caught remains caught.

### Aggregate Comparison

| Metric | IB-001 | IB-003 | Change |
|--------|--------|--------|--------|
| Condition A accuracy | 2/12 | 4/12 | +2 (authority now passes C02, C03) |
| Condition B accuracy | 10/12 | **12/12** | **+2 (C02, C03 resolved)** |
| Controls correct (B) | 2/4 | **4/4** | **+2** |
| Drift caught (B) | 8/8 | 8/8 | Unchanged |
| False holds (B) | 2 | **0** | **−2** |
| Kill triggered | K2 | **None** | Resolved |
| Verdict | FAIL | **PASS (strong positive)** | |

---

## Kill Condition Evaluation

| Kill Condition | Status | Detail |
|---------------|--------|--------|
| K1 — Drift regression | ✓ Clear | 0 previously caught drift cases escaped |
| K2 — Control still blocked | ✓ Clear | 0 controls remain incorrectly blocked |
| K3 — Scope contamination | ✓ Clear | Only `check_authority()` was modified; all other code identical to IB-001 |
| K4 — Privilege expansion | ✓ Clear | 0 privilege expansions detected |

---

## Privilege Expansion Audit

| Case | Original | Normalized To | Authorized | Legitimate Synonym |
|------|----------|---------------|------------|--------------------|
| C02 | `dispatch_email` | `send_email` | Yes | Yes (declared) |
| C03 | `view_file` | `read_file` | Yes | Yes (declared) |

All normalizations are declared legitimate synonyms from the preregistered `WORDING_EQUIVALENCES` map. No privilege expansions detected.

---

## What Condition A Shows

Condition A (authority + evidence, no IntentMatch) improved from 2/12 to 4/12 because C02 and C03 now pass authority. But Condition A still allows all 8 drift cases through — it has no mechanism to detect semantic drift when authority and evidence are valid.

This confirms the IB-001 finding: authority and evidence are necessary but insufficient. IntentMatch provides a distinct, measurable security layer.

---

## Scientific Value of the Full Sequence

1. **The system was allowed to fail.** IB-001 FAIL is preserved. IB-002 FAIL is preserved. Neither was retroactively softened.

2. **Each failure isolated a distinct structural issue.** IB-001 found the authority-synonym gap. IB-002 found the test-design conflation between normalization safety and authority-grant breadth.

3. **The remediation was tested independently before reintegration.** IB-002 confirmed the normalization function resolves aliases (6/6), rejects near-neighbors (6/6), and produces zero privilege expansions — within those 18 preregistered cases.

4. **The retest used the original ground-truth labels.** No labels were changed. No IntentMatch rules were modified. No evidence or authority grant was altered. The only change was the one preregistered remediation.

5. **The result is bounded, not universal.** 12/12 on this preregistered test set with 4 controls and 8 handcrafted drift cases. The next adversarial rounds should test ambiguous scope, nested actions, conflicting constraints, chained tools, temporal drift, and partial equivalence.

---

## Remaining Open Questions (Not Addressed by IB-003)

1. **Authority-grant breadth (AUTH-001 direction).** IB-002 exposed that the flat authority grant includes high-privilege actions alongside low-privilege ones. Whether separating `send_email`, `read_file`, `delete_record`, `execute_tool`, `batch_execute`, and `transmit_external` into narrower capability grants reduces unintended authorization is a separate research question.

2. **Adversarial scale.** 12 cases is sufficient for a first demonstration. It is not sufficient to claim the IntentMatch primitive is generally robust. Future experiments should attempt to break it with harder cases.

3. **Natural-language intent extraction.** All experiments so far use a pre-normalized IntentContract. Whether intent can be reliably extracted from natural-language authorization in production environments is a separate and harder problem.

---

## Preserved Summary Sentences

**IB-001:**
> "IB-001 failed at the pipeline level while isolating a distinct upstream authority-normalization defect; the IntentMatch primitive correctly classified all 12 preregistered cases in this test set."

**IB-002:**
> "IB-002 failed at the experiment level (K3 triggered) while demonstrating that, within the 18 preregistered IB-002 cases, the normalization function produced zero observed privilege expansions, resolved all six legitimate aliases, and rejected all six near-neighbor attacks; the failure isolated a test-design conflation between normalization safety and authority-grant breadth."

**IB-003:**
> "IB-003 passed with a strong positive result (12/12) after applying the preregistered authority-normalization remediation to the original IB-001 pipeline; the two false blocks (C02, C03) were resolved, all eight semantic-drift detections were preserved, and zero privilege expansions were detected — within this preregistered test set of 12 cases."

---

## Files

| File | SHA-256 |
|------|---------|
| `PREREGISTRATION.md` | `d6f788f46c05da853a2ebaefa59ef1c69863e3d3d810d44c739c64dae5fb7d8b` |
| `run_ib003.py` | `c1f3ca2d27bd0c5538b00babd620bc0df86012eda41545ff5c7ba51064f0b306` |
| `results/ib003_results.json` | `c0ebc1058532ba4e05013243d1196e5d1cec4d415c367c08cbe8512d5a059d26` |
| `results/proofrecord_ib003.json` | `699edb4253dd1a9bac91e3219d53e50abf80e2c9bdd1df40f2a9ca223320e562` |
| `results/ib003_ledger.jsonl` | `abcc512a40793b4945676c688675a87f3fc0f83d6bea4ea29cd440503d79bd3c` |
