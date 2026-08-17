# Authority Partitioning (AUTH) Series

**Series:** Authority Partitioning · **Framework:** Coherent Inheritance Framework (CIF) / ExecutionProof
**Principal Investigator:** Derek Hone, Remnant Fieldworks Inc.
**Governing sentence:** "We will accept the result that is true, not the result we hoped to see."

This series tests whether a broad, flat authority grant can be replaced with narrow, least-privilege capability grants without breaking legitimate multi-step work, and whether individually safe grants remain safe when composed across agents through delegation, chaining, and confused-deputy patterns. Every experiment was preregistered and SHA-256 locked before execution; every verdict is preserved regardless of outcome.

| Experiment | Verdict | Summary |
|-----------|---------|---------|
| AUTH-001 | **PASS (18/18)** | Least-Privilege Authority Grant Partitioning. Replaced the flat grant with narrow capability grants scoped by `(actor, action_type, resource_class, scope, constraints)`. Every legitimate action and multi-capability workflow that held exactly its declared minimum capabilities was authorized; every action lacking a matching capability was denied; zero accidental privilege inheritance. Bounded to these 18 cases. |
| AUTH-002 | **PASS (18/18)** | Capability Composition and Confused-Deputy Resistance. Extended the model with five composition rules (no implicit delegation, explicit delegation grants, request-origin binding, grant freshness, no scope intersection). Denied every tested composition-level threat — including three confused-deputy variants and a privilege-laundering delegation chain — while permitting every tested legitimate multi-agent workflow. Bounded to these 18 cases. |

AUTH-001 and AUTH-002 were motivated by the failures in the Intent Binding series: IB-002 exposed that the flat `allowed_action_types` grant was too broad. The full three-layer argument (Intent Integrity → Authority Integrity → Composition Safety) is documented in `RESEARCH-NOTE-001.md`.

**STATE-001** (in `state001/`) is **preregistered but NOT executed** — it is the next research direction (temporal / state-bound authorization) and is **not** counted as a completed experiment. Its preregistration is included here for transparency and provenance only.

**What this does not establish:** general robustness beyond the preregistered test sets, behavior under concurrent/distributed execution or mid-flight state change, LLM-mediated intent interpretation, or independent academic validation. Internal/founder-led experimental corpus; independent academic validation is the next phase.

Each experiment folder contains its preregistration, runnable script, machine-readable results, append-only ledger, ProofRecord, a `MANIFEST.sha256`, and a human-readable results write-up.
