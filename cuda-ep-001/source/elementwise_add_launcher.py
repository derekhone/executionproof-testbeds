"""
elementwise_add_launcher.py
===========================
CUDA-EP-001 GPU Phase - Python launcher wrapper for the compiled CUDA binary.
Remnant Fieldworks Inc. | CUDA-EP-001 | v1.0 | 2026-10-01
RESEARCH ONLY - NOT PRODUCTION

This launcher is the ONLY sanctioned path to releasing GPU capability in the
bounded experiment. It:

  1. Checks GPU availability first (nvidia-smi + /dev/nvidia*). If absent it
     returns a BLOCKED_NO_GPU result and NEVER attempts a launch.
  2. On a real GPU host, runs the compiled binary as a subprocess, captures
     stdout/stderr/return-code, and timestamps process start and end.

The launcher does NOT make authorization decisions. The gateway
(gpu_gateway.py) must return ALLOW before the launcher is called at all; the
launcher simply refuses to run when no GPU is present (fail-closed).
"""

from __future__ import annotations

import datetime as _dt
import glob
import os
import shutil
import subprocess
from dataclasses import dataclass, field
from typing import List, Optional


def _utcnow() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat()


@dataclass
class LaunchResult:
    status: str                       # EXECUTED | BLOCKED_NO_GPU | LAUNCH_ERROR
    returncode: Optional[int] = None
    stdout: str = ""
    stderr: str = ""
    started_at: Optional[str] = None
    ended_at: Optional[str] = None
    blocker_evidence: List[str] = field(default_factory=list)
    note: str = ""


def gpu_available() -> (bool, List[str]):
    """Return (available, failed_checks). Fail-closed: any missing signal -> unavailable."""
    failed: List[str] = []
    if shutil.which("nvidia-smi") is None:
        failed.append("nvidia-smi: NOT_FOUND")
    if not glob.glob("/dev/nvidia*"):
        failed.append("/dev/nvidia*: NOT_FOUND")
    # Optional torch signal (do not hard-require torch)
    try:
        import torch  # noqa: WPS433
        if not torch.cuda.is_available():
            failed.append("torch.cuda.is_available(): False")
    except Exception:  # noqa: BLE001
        failed.append("torch: NOT_IMPORTABLE (non-fatal signal)")
    available = (shutil.which("nvidia-smi") is not None) and bool(glob.glob("/dev/nvidia*"))
    return available, failed


def launch_or_block(binary_path: str, timeout_s: int = 60) -> LaunchResult:
    """Launch the compiled CUDA binary, or BLOCK if no GPU.

    [NOT_EXECUTED - NO GPU IN ENVIRONMENT] In the current environment this
    returns status=BLOCKED_NO_GPU without attempting any launch.
    """
    available, failed = gpu_available()
    if not available:
        return LaunchResult(
            status="BLOCKED_NO_GPU",
            blocker_evidence=failed,
            note="GPU not present; launcher refused to execute (fail-closed). "
                 "NOT_EXECUTED - NO GPU IN ENVIRONMENT.",
        )

    if not os.path.isfile(binary_path):
        return LaunchResult(
            status="LAUNCH_ERROR",
            blocker_evidence=[f"binary not found: {binary_path}"],
            note="Compile kernels/elementwise_add.cu first (compile_kernel.sh).",
        )

    started = _utcnow()
    try:
        proc = subprocess.run(
            [binary_path],
            capture_output=True,
            text=True,
            timeout=timeout_s,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:  # noqa: BLE001
        return LaunchResult(
            status="LAUNCH_ERROR",
            started_at=started,
            ended_at=_utcnow(),
            note=f"timeout after {timeout_s}s: {exc}",
        )
    ended = _utcnow()
    return LaunchResult(
        status="EXECUTED",
        returncode=proc.returncode,
        stdout=proc.stdout,
        stderr=proc.stderr,
        started_at=started,
        ended_at=ended,
        note="Binary executed on GPU host.",
    )


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    res = launch_or_block(os.path.join(here, "kernels", "elementwise_add"))
    print(f"status={res.status}")
    for b in res.blocker_evidence:
        print(f"  blocker: {b}")
    if res.note:
        print(f"note: {res.note}")
