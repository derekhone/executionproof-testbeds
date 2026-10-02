"""
run_gpu_cases.py
================
CUDA-EP-001 GPU Phase - orchestrates all GPU cases GPU-C0 through GPU-C8
through the GPU gateway.
Remnant Fieldworks Inc. | CUDA-EP-001 | v1.0 | 2026-10-01
RESEARCH ONLY - NOT PRODUCTION

In the current environment there is NO GPU, so the gateway short-circuits every
case to BLOCKED_NO_GPU before any decision engine runs and before the launcher is
ever called. On a real GPU host this script would drive the full 9-case matrix
and record the real verdicts.

Expected matrix (what WOULD happen on a correctly configured GPU host):

  GPU-C0  clean baseline                 -> ALLOW  (kernel EXECUTES)
  GPU-C1  authority failure              -> DENY
  GPU-C2  missing evidence               -> HOLD
  GPU-C3  policy / expiry constraint     -> HOLD
  GPU-C4  evidence/artifact mismatch     -> DENY
  GPU-C5  control / gateway not satisfied-> HOLD
  GPU-C6  mutated ProofRecord            -> VERIFICATION_FAILURE
  GPU-C7  target compute-cap mismatch    -> DENY
  GPU-C8  exclusive launcher control     -> no launch without valid ALLOW
"""

from __future__ import annotations

import json
import os
import sys

from gpu_gateway import GpuExecutionGateway, load_policy

HERE = os.path.dirname(os.path.abspath(__file__))
KERNELS = os.path.join(HERE, "kernels")

EXPECTED = [
    ("GPU-C0", "clean_baseline", "ALLOW"),
    ("GPU-C1", "authority_failure", "DENY"),
    ("GPU-C2", "missing_evidence", "HOLD"),
    ("GPU-C3", "policy_expiry_constraint", "HOLD"),
    ("GPU-C4", "evidence_artifact_mismatch", "DENY"),
    ("GPU-C5", "control_gateway_not_satisfied", "HOLD"),
    ("GPU-C6", "mutated_proofrecord", "VERIFICATION_FAILURE"),
    ("GPU-C7", "target_compute_capability_mismatch", "DENY"),
    ("GPU-C8", "exclusive_launcher_control", "NO_LAUNCH_WITHOUT_ALLOW"),
]


def base_contract() -> dict:
    return {
        "authority_identity": "spiffe://cuda-ep.experiment/proposer/run-gpu-001",
        "compiled_binary_sha256": "NOT_EXECUTED - nvcc not available",
        "functional_test_hash": "PLACEHOLDER",
        "hidden_test_hash": "PLACEHOLDER",
        "sanitizer_evidence_hash": "NOT_EXECUTED",
        "target_compute_capability": "8.0",
        "policy_version": "1.0",
        "expiry_at": "2099-01-01T00:00:00+00:00",
    }


def main() -> int:
    policy_path = os.path.join(HERE, "gpu_policy.json")
    policy = load_policy(policy_path)
    gateway = GpuExecutionGateway(policy, KERNELS)

    print("=" * 74)
    print("CUDA-EP-001 GPU CASE MATRIX (GPU-C0 .. GPU-C8)")
    print("=" * 74)

    results = []
    for case_id, cond, expected in EXPECTED:
        contract = base_contract()
        decision = gateway.evaluate(contract, release_capability=True)
        actual = decision.verdict
        results.append({
            "case_id": case_id,
            "condition": cond,
            "expected_on_gpu": expected,
            "actual_this_env": actual,
            "environment_verdict": decision.environment_verdict,
            "blocker_evidence": decision.blocker_evidence,
        })
        print(f"{case_id:8s} {cond:34s} expected(GPU)={expected:24s} "
              f"actual(this env)={actual}")

    all_blocked = all(r["actual_this_env"] == "BLOCKED_NO_GPU" for r in results)
    print("-" * 74)
    print(f"ALL CASES BLOCKED_NO_GPU IN THIS ENVIRONMENT: {all_blocked}")
    print("NOT_EXECUTED - NO GPU IN ENVIRONMENT")
    print("=" * 74)

    out_path = os.path.join(HERE, "run_gpu_cases_output.json")
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump({"results": results, "all_blocked": all_blocked}, fh, indent=2)
    return 0 if all_blocked else 1


if __name__ == "__main__":
    sys.exit(main())
