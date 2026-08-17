# Intent Binding (IB) Series

**Series:** Intent Binding · **Framework:** Coherent Inheritance Framework (CIF) / ExecutionProof
**Principal Investigator:** Derek Hone, Remnant Fieldworks Inc.
**Governing sentence:** "We will accept the result that is true, not the result we hoped to see."

This series tests whether an approved action can silently drift into a different action between intent and execution, and whether a defect exposed by that test can be remediated without weakening drift detection. Every experiment was preregistered and SHA-256 locked before execution; every verdict is preserved regardless of outcome.

| Experiment | Verdict | Summary |
|-----------|---------|---------|
| IB-001 | **FAIL (K2)** | Intent Binding vs. Semantic Drift. IntentMatch classified all 12 cases correctly, but the authority layer used exact string matching and wrongly blocked two legitimate controls (synonym gap). The pipeline fails as a whole because both layers must pass. |
| IB-002 | **FAIL (K3)** | Authority Normalization Safety. The normalization function resolved all legitimate aliases and rejected all near-neighbor attacks with zero privilege expansion, but the flat authority grant already contained escalation targets — a test-design conflation that correctly triggered the preregistered kill condition. |
| IB-003 | **PASS (12/12)** | Intent-Binding Pipeline Retest. Reran the original 12 IB-001 cases with one isolated change (`normalize_authority_action_type()` applied inside `check_authority()`). Both false holds resolved, all 8 drift detections preserved, zero privilege expansions, all 4 kill conditions clear. Bounded to these 12 cases. |

The IB sequence is a complete **FAIL → FAIL → PASS** arc. The two failures are preserved as-is and are scientifically necessary: IB-003's pass is credible precisely because the failures that motivated it are on the record.

**What this does not establish:** general robustness beyond the preregistered test sets, LLM-mediated intent interpretation (all matching is deterministic), or independent academic validation. Internal/founder-led experimental corpus; independent academic validation is the next phase.

Each experiment folder contains its preregistration (`PREREGISTRATION.md`), runnable script (`run_ib0XX.py`), machine-readable results (`*_results.json`), append-only ledger (`*_ledger.jsonl`), ProofRecord (`proofrecord_*.json`), a `MANIFEST.sha256`, and a human-readable results write-up. The connecting narrative across the Intent Binding and Authority Partitioning layers is in `../authority-partitioning/RESEARCH-NOTE-001.md`.
