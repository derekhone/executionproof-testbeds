"""
run_all.py — ExecutionProof Enterprise Agent Boundary Testbed orchestrator.

Executes ARK-493 → ARK-494 → ARK-495 → ARK-496 → ARK-497 → ARK-498 in order
against a single shared environment and hash-chained ProofRecord store, printing
every case result to stdout. It PRESERVES every failure (no retry-until-pass) and
enforces the GATE-STOP rule: if ARK-493 reveals any enforcement leak (a DENY or
unresolved HOLD producing an *executed* side-effect entry), the series halts
immediately after the GATE-STOP record is written; ARK-494..498 do not run.

Usage:  python3 run_all.py
"""
import os
import sys
import json
import hashlib
import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from enforcement.proofstore import ProofStore, CHAIN_PATH   # noqa: E402
from experiments.common import build_env, RESULTS_DIR, RESULTS_LEDGER  # noqa: E402
from experiments import (                                    # noqa: E402
    run_493, run_494, run_495, run_496, run_497, run_498,
)

_HERE = os.path.dirname(os.path.abspath(__file__))
PREREG = os.path.join(_HERE, "preregistration",
                      "ARK-493-498-PREREGISTRATION-v1.1.md")
PREREG_SHA256 = "464b9fb8be9d6cca052f236dc9deec9f8e89b781cafc58701e79b2d05d52952a"
MANIFEST = os.path.join(RESULTS_DIR, "execution_manifest.json")


def _sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _clean():
    import glob
    for pat in ("ledgers/*.jsonl", "proofrecords/*.json", "proofrecords/*.jsonl",
                "results/*.jsonl", "results/*.json", "ledger/*.md"):
        for p in glob.glob(os.path.join(_HERE, pat)):
            os.remove(p)


def main():
    print("=" * 74)
    print("ExecutionProof Enterprise Agent Boundary Testbed — ARK-493..498")
    print("=" * 74)

    # ---- verify frozen preregistration ----
    actual = _sha256_file(PREREG)
    match = (actual == PREREG_SHA256)
    print(f"Preregistration: ARK-493-498-PREREGISTRATION-v1.1.md")
    print(f"  expected SHA-256 {PREREG_SHA256}")
    print(f"  actual   SHA-256 {actual}")
    print(f"  hash match: {match}")
    if not match:
        print("ABORT: preregistration hash mismatch — refusing to run.")
        sys.exit(2)

    _clean()
    store = ProofStore(guard_b_mode="inline")
    env = build_env(store)

    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    results = []

    # ---- ARK-493 (gate-stop gate) ----
    print("\n--- ARK-493: Enforcement Boundary Under Adversarial Load ---")
    r493 = run_493.run(env, emit=print)
    results.append(r493)
    print(f"ARK-493 decision: {r493['decision']}")

    if r493.get("gate_stop"):
        print("\n" + "!" * 74)
        print("GATE-STOP TRIGGERED IN ARK-493 — enforcement leak detected.")
        print("A DENY/HOLD case produced an 'executed' side-effect ledger entry.")
        print("GATE-STOP record written to the chain and ledger/GATE-STOP-ARK-493.md.")
        print("Series HALTED: ARK-494 through ARK-498 will NOT execute.")
        print("!" * 74)
        _write_manifest(started, results, match, halted=True)
        sys.exit(1)

    # ---- ARK-494..498 (only if no gate-stop) ----
    for mod, title in (
        (run_494, "ARK-494: Semantic Boundary — Deep Argument Mutation"),
        (run_495, "ARK-495: Temporal Boundary — Authority Change Mid-Flight"),
        (run_496, "ARK-496: Multi-Agent Delegation and Self-Approval Defense"),
        (run_497, "ARK-497: Independently Reconstructable ProofRecord"),
        (run_498, "ARK-498: Networked Production-Like Performance"),
    ):
        print(f"\n--- {title} ---")
        r = mod.run(env, emit=print)
        results.append(r)
        print(f"{r['experiment_id']} decision: {r['decision']}")

    print("\n" + "=" * 74)
    print("SERIES COMPLETE")
    for r in results:
        print(f"  {r['experiment_id']}: {r['decision']} "
              f"({len(r['case_ids'])} scored cases)")
    print("=" * 74)
    _write_manifest(started, results, match, halted=False)


def _write_manifest(started, results, prereg_match, halted):
    os.makedirs(RESULTS_DIR, exist_ok=True)
    manifest = {
        "series": "ARK-493 through ARK-498",
        "preregistration": "ARK-493-498-PREREGISTRATION-v1.1.md",
        "preregistration_sha256": PREREG_SHA256,
        "preregistration_hash_match": prereg_match,
        "started_utc": started,
        "finished_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "halted_by_gate_stop": halted,
        "experiments": [
            {"experiment_id": r["experiment_id"], "decision": r["decision"],
             "scored_cases": len(r["case_ids"]), "case_ids": r["case_ids"]}
            for r in results
        ],
        "chain_file": os.path.relpath(CHAIN_PATH, _HERE),
        "results_ledger": os.path.relpath(RESULTS_LEDGER, _HERE),
    }
    with open(MANIFEST, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=2)
    print(f"\nExecution manifest written: {os.path.relpath(MANIFEST, _HERE)}")


if __name__ == "__main__":
    main()
