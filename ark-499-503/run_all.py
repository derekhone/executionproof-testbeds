"""
run_all.py — ExecutionProof Enterprise Adapter Series orchestrator (ARK-499-503).

Verifies the frozen preregistration + gate-under-test by SHA-256 BEFORE running
anything, then executes:

  ARK-499  real PostgreSQL transaction boundary        -> EXPERIMENT-PASS/FAIL
  ARK-500  real CI/CD release boundary                 -> EXPERIMENT-PASS/FAIL
  ARK-501  real external OIDC/IAM identity boundary     -> EXPERIMENT-PASS/FAIL
  ARK-502  operational-continuity BOUNDED SMOKE         -> SMOKE-PASS/FAIL
           (>=14-day endurance is NOT executed and stays NOT-EXECUTED)
  ARK-503  independent adversarial review               -> NOT-EXECUTED (human)

Every outcome is preserved (no retry-until-pass). If the preregistration or any
frozen gate/guard file fails its hash check, the run ABORTS — an unregistered
run is not a registered result.

Usage:  python3 run_all.py
"""
import os
import sys
import glob
import json
import hashlib
import datetime

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

PREREG = os.path.join(_HERE, "preregistration",
                      "ARK-499-503-PREREGISTRATION-v1.0.md")
PREREG_SHA256 = "84bd915e7d7aab8268f40a339e71dbd96ac2440f929dca6d37bfdde990d24b61"

FROZEN = {
    "gate/core.py": "7bfb92f4485b69c272b37b6a06ef9f428e461b490ee043e52d6c13d6d858398e",
    "gate/gate.py": "9f08f2b7bbc1bce84aa3cd2637e9c328868eccf6624434ed622cdbe7e5722acd",
    "gate/policy.py": "1dc4ee187074713ef1dbcfec108477dedceb0c31bd8d5f3e749864096f3e4356",
    "gate/actor_registry.py": "e444ed9edcf0087bc95bc5d58c4fd5303d9d59f41a61f44a5273a3739dbe1e91",
    "guards/guard_a.py": "8e18ff4cb2671b5e6fdbc6705e3a69bed66ee14818ba3d0dbc84c233e445eb54",
    "guards/guard_b_verifier.py": "2eb5d2a0d7de4317e61eeae296cf1e09905e7dbcee93d5f12ab79e44b73a0419",
    "enforcement/proofstore.py": "878a8e6691daa454b5a569ad063ae2f2657c053fdd941d7f031a174cf1e305c4",
    "actor/actor_agent.py": "fe7cdf207351c560adf7e6847d98113b20f2cf43ca083dd1e8f477c340d8874a",
}


def _sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _clean():
    for pat in ("proofrecords/*.json", "proofrecords/*.jsonl",
                "results/*.jsonl"):
        for p in glob.glob(os.path.join(_HERE, pat)):
            os.remove(p)


def _verify_frozen():
    ok = True
    actual = _sha256_file(PREREG)
    match = actual == PREREG_SHA256
    print(f"Preregistration ARK-499-503-PREREGISTRATION-v1.0.md")
    print(f"  expected {PREREG_SHA256}")
    print(f"  actual   {actual}   match={match}")
    ok = ok and match
    print("Frozen gate-under-test (byte-identical to ARK-493-498):")
    for rel, expected in FROZEN.items():
        a = _sha256_file(os.path.join(_HERE, rel))
        m = a == expected
        ok = ok and m
        print(f"  {'OK ' if m else 'BAD'}  {rel}")
    return ok


def main():
    print("=" * 74)
    print("ExecutionProof Enterprise Adapter Series — ARK-499..503")
    print("Remnant Fieldworks Inc.  |  results preserved, claims kept narrow")
    print("=" * 74)

    if not _verify_frozen():
        print("\nABORT: preregistration / frozen-gate hash mismatch — "
              "refusing to run (an unregistered run is not a registered result).")
        sys.exit(2)

    _clean()
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()

    from experiments import run_499, run_500, run_501, run_502

    summary = {}

    print("\n--- ARK-499: Real PostgreSQL Transaction Boundary ---")
    summary["ARK-499"] = run_499.main()

    print("\n--- ARK-500: Real CI/CD Release Boundary ---")
    summary["ARK-500"] = run_500.main()

    print("\n--- ARK-501: Real External OIDC/IAM Identity Boundary ---")
    summary["ARK-501"] = run_501.main()

    print("\n--- ARK-502: Operational-Continuity BOUNDED SMOKE (NOT 14-day) ---")
    summary["ARK-502"] = run_502.main()

    print("\n--- ARK-503: Independent Adversarial Review ---")
    print("  STATUS: NOT-EXECUTED — requires an independent human reviewer.")
    print("  Package ready at ark503_review_package/ (0 scored PASS until signed).")
    summary["ARK-503"] = {"decision": "NOT-EXECUTED",
                          "reason": "requires independent human reviewer"}

    finished = datetime.datetime.now(datetime.timezone.utc).isoformat()
    manifest = {
        "series": "ARK-499-503",
        "started_utc": started, "finished_utc": finished,
        "preregistration_sha256": PREREG_SHA256,
        "results": {k: (v.get("decision") if isinstance(v, dict) else str(v))
                    for k, v in summary.items()},
        "notes": [
            "ARK-499/500/501 executed with REAL backing systems (native "
            "PostgreSQL 17 / local git CI runner / self-hosted RS256 OIDC).",
            "NOT Docker/K8s/cloud; NOT Okta/AzureAD/Auth0.",
            "ARK-502 is a bounded smoke ONLY; >=14-day endurance is NOT-EXECUTED.",
            "ARK-503 is NOT-EXECUTED; awaiting a signed independent rubric.",
        ],
    }
    out = os.path.join(_HERE, "results", "execution_manifest.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as fh:
        json.dump(manifest, fh, indent=2)

    print("\n" + "=" * 74)
    print("SERIES RESULTS")
    for k, v in manifest["results"].items():
        print(f"  {k}: {v}")
    print(f"\nExecution manifest written to {out}")
    print("=" * 74)


if __name__ == "__main__":
    main()
