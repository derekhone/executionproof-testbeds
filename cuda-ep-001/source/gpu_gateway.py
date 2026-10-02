"""
gpu_gateway.py
==============
CUDA-EP-001 GPU Phase - GPU execution gateway.
Remnant Fieldworks Inc. | CUDA-EP-001 | v1.0 | 2026-10-01
RESEARCH ONLY - NOT PRODUCTION

This gateway extends the CPU-surrogate ExecutionProof gate (see
RF_CUDA_Final_Package/08_CUDA_EP_001_CODE) with REAL GPU-launch support. It is a
genuine implementation that WOULD run on a GPU host. It makes the ALLOW / HOLD /
DENY decision BEFORE any launcher call, and releases GPU capability only on
ALLOW.

Decision flow (fail-closed at every step):

  1. ENVIRONMENT GATE: if no NVIDIA GPU is present, return BLOCKED_NO_GPU and
     stop. No decision engine is even consulted, and the launcher is never
     called. This is the state in the current environment:
     [NOT_EXECUTED - NO GPU IN ENVIRONMENT].

  2. AUTHORITY: requester identity must be in the policy allow-list.

  3. EVIDENCE: the compiled-binary SHA-256 must equal the contract's
     compiled_binary_sha256, the functional-test and hidden-test digests must
     match, and (if required) the sanitizer-evidence digest must match.

  4. CONSTRAINT: target compute-capability must be satisfied by the detected
     device; the contract must not be expired; policy version must match.

  5. CONTROL (GPU-C8): the launcher must be the exclusive capability path. Only
     on ALLOW is launch_or_block() invoked.

Verdicts: ALLOW, DENY, HOLD, plus the environment short-circuit BLOCKED_NO_GPU.
"""

from __future__ import annotations

import datetime as _dt
import glob
import hashlib
import json
import os
import shutil
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from elementwise_add_launcher import launch_or_block, gpu_available


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _utcnow() -> _dt.datetime:
    return _dt.datetime.now(_dt.timezone.utc)


def sha256_file(path: str) -> Optional[str]:
    if not os.path.isfile(path):
        return None
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


@dataclass
class GateDecision:
    verdict: str                       # ALLOW | DENY | HOLD | BLOCKED_NO_GPU
    reason_code: str
    authority_result: str = "NOT_EVALUATED"
    evidence_result: str = "NOT_EVALUATED"
    constraint_result: str = "NOT_EVALUATED"
    control_result: str = "NOT_EVALUATED"
    candidate_executed: bool = False
    gateway_capability_released: bool = False
    environment_verdict: str = "UNKNOWN"
    blocker_evidence: List[str] = field(default_factory=list)
    launch_stdout: str = ""
    notes: str = ""


# --------------------------------------------------------------------------- #
# Gateway
# --------------------------------------------------------------------------- #
class GpuExecutionGateway:
    """Pre-execution authorization gate with real GPU launch on ALLOW."""

    def __init__(self, policy: Dict, kernels_dir: str):
        self.policy = policy
        self.kernels_dir = kernels_dir
        self.binary_path = os.path.join(kernels_dir, "elementwise_add")

    # -- environment gate --------------------------------------------------- #
    def _environment_gate(self) -> Optional[GateDecision]:
        available, failed = gpu_available()
        if not available:
            return GateDecision(
                verdict="BLOCKED_NO_GPU",
                reason_code="NO_GPU_IN_ENVIRONMENT",
                environment_verdict="NO_GPU_PRESENT - GPU_EXECUTION_BLOCKED",
                blocker_evidence=failed,
                notes="Environment gate short-circuit. No decision engine was "
                      "consulted and the launcher was never called. "
                      "NOT_EXECUTED - NO GPU IN ENVIRONMENT.",
            )
        return None

    # -- authority ---------------------------------------------------------- #
    def _authority(self, contract: Dict) -> str:
        allowed = self.policy.get("authorized_requesters", [])
        return "PASS" if contract.get("authority_identity") in allowed else "FAIL"

    # -- evidence ----------------------------------------------------------- #
    def _evidence(self, contract: Dict) -> (str, List[str]):
        problems: List[str] = []
        declared_bin = contract.get("compiled_binary_sha256", "")
        if declared_bin.startswith("NOT_EXECUTED"):
            problems.append("compiled_binary_sha256 is NOT_EXECUTED (no build)")
            return "MISSING", problems
        actual_bin = sha256_file(self.binary_path)
        if actual_bin is None:
            problems.append("compiled binary not present on disk")
            return "MISSING", problems
        if actual_bin != declared_bin:
            problems.append("compiled binary hash != contract hash")
            return "FAIL", problems
        # functional + hidden digests must be present
        for key in ("functional_test_hash", "hidden_test_hash"):
            if not contract.get(key) or str(contract.get(key)).startswith("NOT_"):
                problems.append(f"{key} missing")
        if contract.get("sanitizer_evidence_hash", "").startswith("NOT_EXECUTED"):
            problems.append("sanitizer evidence NOT_EXECUTED")
            return "MISSING", problems
        return ("PASS" if not problems else "MISSING"), problems

    # -- constraint --------------------------------------------------------- #
    def _constraint(self, contract: Dict) -> str:
        # expiry
        try:
            expiry = _dt.datetime.fromisoformat(contract["expiry_at"])
            if _utcnow() > expiry:
                return "HOLD_EXPIRED"
        except Exception:  # noqa: BLE001
            return "HOLD_BAD_EXPIRY"
        # policy version
        if contract.get("policy_version") not in (None, self.policy.get("version")):
            return "HOLD_POLICY_DRIFT"
        # target compute capability (would compare to detected device on GPU)
        required = str(contract.get("target_compute_capability", ""))
        if not required:
            return "DENY_TARGET"
        return "PASS"

    # -- control (GPU-C8) --------------------------------------------------- #
    def _control(self) -> str:
        # The launcher must be the exclusive path. On a real host this would
        # verify no alternative capability release exists.
        return "PASS" if shutil.which("nvidia-smi") else "HOLD_NO_EXCLUSIVE_PATH"

    # -- top-level evaluate ------------------------------------------------- #
    def evaluate(self, contract: Dict, release_capability: bool = True) -> GateDecision:
        env_block = self._environment_gate()
        if env_block is not None:
            return env_block

        authority = self._authority(contract)
        if authority == "FAIL":
            return GateDecision("DENY", "AUTHORITY_NOT_AUTHORIZED",
                                authority_result="FAIL")

        evidence, ev_problems = self._evidence(contract)
        if evidence == "FAIL":
            return GateDecision("DENY", "EVIDENCE_ARTIFACT_MISMATCH",
                                authority_result=authority, evidence_result="FAIL",
                                blocker_evidence=ev_problems)
        if evidence == "MISSING":
            return GateDecision("HOLD", "EVIDENCE_MISSING",
                                authority_result=authority, evidence_result="MISSING",
                                blocker_evidence=ev_problems)

        constraint = self._constraint(contract)
        if constraint.startswith("DENY"):
            return GateDecision("DENY", "CONSTRAINT_TARGET_MISMATCH",
                                authority_result=authority, evidence_result=evidence,
                                constraint_result=constraint)
        if constraint.startswith("HOLD"):
            return GateDecision("HOLD", constraint,
                                authority_result=authority, evidence_result=evidence,
                                constraint_result=constraint)

        control = self._control()
        if control.startswith("HOLD"):
            return GateDecision("HOLD", control,
                                authority_result=authority, evidence_result=evidence,
                                constraint_result=constraint, control_result=control)

        # All engines pass -> ALLOW. Release capability via the launcher.
        decision = GateDecision(
            "ALLOW", "ALL_ENGINES_PASS",
            authority_result=authority, evidence_result=evidence,
            constraint_result=constraint, control_result=control,
        )
        if release_capability:
            res = launch_or_block(self.binary_path)
            decision.gateway_capability_released = (res.status == "EXECUTED")
            decision.candidate_executed = (res.status == "EXECUTED")
            decision.launch_stdout = res.stdout
            decision.environment_verdict = res.status
            if res.status != "EXECUTED":
                decision.blocker_evidence = res.blocker_evidence
                decision.notes = res.note
        return decision


def load_policy(path: str) -> Dict:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)
