# ExecutionProof — Enterprise Agent Boundary Testbed (ARK-493 → ARK-498)

ExecutionProof enforces **proof before power**: an autonomous agent's tool call
executes only after an independent gate has verified actor identity, live
authority, evidence, policy version, system state, and exact-action integrity —
and every decision is written to a signed, hash-chained, independently
reconstructable ProofRecord. Fail-closed is the default; failures are preserved,
never retried until they pass.

This directory is a **non-quantum, production-like** enforcement testbed. It is
distinct from the hardware ARK experiments (ARK-441–492): here the boundary is a
real software enforcement point (and, in ARK-498, a real HTTP/loopback-TCP
socket), not an IBM Quantum device. It asks whether ExecutionProof *mechanically
enforces* an authorization decision at a real boundary — not merely records it.

## This series at a glance (frozen preregistration v1.1)

| Experiment | Focus | Result |
|-----------|-------|--------|
| ARK-493 | Enforcement boundary under adversarial load (6 paths × 15 cells) | PASS — 90/90 |
| ARK-494 | Semantic boundary: deep argument mutation | PASS — 13/13 |
| ARK-495 | Temporal boundary: authority change mid-flight | PASS — 11/11 |
| ARK-496 | Multi-agent delegation & self-approval defense | PASS — 8/8 |
| ARK-497 | Independently reconstructable ProofRecord (+ tamper detection) | PASS — 30/30 |
| ARK-498 | Networked production-like performance | PASS — 6/6 hard criteria |

- **161 scored cases this series, 161 PASS, 0 FAIL, 0 enforcement leaks.**
- **GATE-STOP was NOT triggered** — zero DENY or HOLD case produced an executed
  side-effect entry in any tool ledger.
- **Dual-guard verification:** an in-process Guard-A and an *isolated-subprocess*
  Guard-B independently verified all 161 scored records and agreed on every one.
- **ARK-497:** an isolated verifier (permitted imports only, statically proven to
  import nothing from the application) reconstructed all 9 decision elements for
  20 legitimate records and detected **10/10** single-field tamper attempts with
  **0** false positives.
- **ARK-498:** behind a real HTTP/loopback-TCP boundary (~1,810 requests), the
  gate held fail-closed under policy/authority/store failure (**leak count 0**),
  executed **zero** duplicate side effects, produced **100%** complete and
  signature-verifiable ProofRecords, and recovered cleanly with **no** automatic
  re-execution of denied requests.

## Reproduce

```bash
pip install -r requirements.txt
python3 run_all.py     # verifies the frozen preregistration hash, then runs 493→498
```

`run_all.py` refuses to run unless the preregistration hash matches, and halts the
entire series (GATE-STOP) if ARK-493 detects any enforcement leak.

Preregistration: [`preregistration/ARK-493-498-PREREGISTRATION-v1.1.md`](preregistration/ARK-493-498-PREREGISTRATION-v1.1.md)
SHA-256 `464b9fb8be9d6cca052f236dc9deec9f8e89b781cafc58701e79b2d05d52952a`.
The superseded v1.0 is preserved unchanged
([`ARK-493-498-PREREGISTRATION.md`](preregistration/ARK-493-498-PREREGISTRATION.md),
SHA-256 `deb9c43ee252ecd9cb217788f783ebf6fd7113883170749fedaa1509425406ce`).

## Layout

| Path | Contents |
|------|----------|
| `preregistration/` | Frozen preregistration v1.0 (superseded) and v1.1 (governing), with SHA-256 manifests |
| `gate/`, `enforcement/`, `tools/`, `guards/`, `actor/` | Testbed source: gate, sole enforcement path, mock tools, dual guards, actor agent |
| `experiments/` | Per-experiment runners (`run_493.py` … `run_498.py`), ARK-497 isolated verifier, ARK-498 HTTP server |
| `run_all.py` | Master runner — hash check, GATE-STOP enforcement, sequential execution |
| `results/` | Results ledger, reconciliation report, ARK-498 performance report, execution manifest, verifier outputs |
| `proofrecords/` | Signed, hash-chained ProofRecord chain (`proofrecord_chain.jsonl`) + per-record files |
| `ledgers/` | Per-tool side-effect ledgers (executed / blocked / held) |

## Performance note

ARK-498 latency/throughput figures are labeled **PRODUCTION-LIKE OVERHEAD
CHARACTERIZATION · NOT A BENCHMARK CERTIFICATION · NOT A PRODUCTION SLA**. They
characterize overhead on top of simulated dependency latency in this test
environment and must not be published as an SLA or compared to the in-process
microsecond testbed (ARK-483–492).

## License

Code and data released under the repository [`LICENSE`](../LICENSE). Dataset also
archived under CC BY 4.0 on Zenodo.
