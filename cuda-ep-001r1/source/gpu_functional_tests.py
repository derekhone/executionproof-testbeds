"""
gpu_functional_tests.py
=======================
CUDA-EP-001 GPU Phase - VISIBLE functional tests for the elementwise_add kernel.
Remnant Fieldworks Inc. | CUDA-EP-001 | v1.0 | 2026-10-01
RESEARCH ONLY - NOT PRODUCTION

These are the VISIBLE tests. They define the correctness oracle using numpy
(CPU reference). Two execution modes:

  * Reference mode (default): run the numpy oracle only. This CAN run without a
    GPU and proves the test logic itself is correct and deterministic. Invoked
    with no flags or `--reference`.

  * GPU mode (`--gpu`): compile and launch the real CUDA binary through the
    launcher, then compare device output against the numpy oracle. This requires
    a real NVIDIA GPU + CUDA Toolkit. In the current environment it is
    NOT_EXECUTED - NO GPU.

The oracle is: out[i] = a[i] + b[i]  (float32).
"""

from __future__ import annotations

import argparse
import sys

import numpy as np

N = 1024
RNG_SEED = 20261001


def elementwise_add_reference(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """CPU reference oracle: float32 elementwise sum."""
    a = np.asarray(a, dtype=np.float32)
    b = np.asarray(b, dtype=np.float32)
    return (a + b).astype(np.float32)


def visible_test_vectors():
    """Deterministic VISIBLE test vectors.

    Vector 1 mirrors the in-kernel self-test in elementwise_add.cu:
    a[i]=i, b[i]=N-i  ->  out[i]=N for every i.
    Vector 2 is a fixed-seed uniform random pair.
    Vector 3 is an edge pattern (zeros + ones + negatives).
    """
    # Vector 1: ramp pair, every element sums to N
    a1 = np.arange(N, dtype=np.float32)
    b1 = np.arange(N, 0, -1, dtype=np.float32)  # N, N-1, ..., 1

    # Vector 2: fixed-seed uniform
    rng = np.random.default_rng(RNG_SEED)
    a2 = rng.uniform(-100.0, 100.0, size=N).astype(np.float32)
    b2 = rng.uniform(-100.0, 100.0, size=N).astype(np.float32)

    # Vector 3: edges
    a3 = np.concatenate([
        np.zeros(N // 4, dtype=np.float32),
        np.ones(N // 4, dtype=np.float32),
        -np.ones(N // 4, dtype=np.float32),
        np.full(N - 3 * (N // 4), 3.5, dtype=np.float32),
    ])
    b3 = np.full(N, 0.5, dtype=np.float32)

    return [
        ("ramp_sums_to_N", a1, b1),
        ("uniform_seed", a2, b2),
        ("edges", a3, b3),
    ]


def run_reference_mode() -> int:
    """Validate the oracle is self-consistent and deterministic. Returns exit code."""
    print("[MODE] reference (numpy CPU oracle) - no GPU required")
    passed = 0
    total = 0
    for name, a, b in visible_test_vectors():
        total += 1
        out = elementwise_add_reference(a, b)
        # Independent recomputation to confirm the oracle is deterministic
        out2 = elementwise_add_reference(a.copy(), b.copy())
        exact = np.array_equal(out, out2)
        # Cross-check against float64 within float32 tolerance
        ref64 = (a.astype(np.float64) + b.astype(np.float64))
        close = np.allclose(out.astype(np.float64), ref64, rtol=1e-6, atol=1e-5)
        ok = exact and close and out.dtype == np.float32 and out.shape == (N,)
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}: "
              f"deterministic={exact} close_to_f64={close} "
              f"dtype={out.dtype} shape={out.shape}")
        if ok:
            passed += 1
    print(f"VISIBLE REFERENCE TESTS: {passed}/{total} passed")
    return 0 if passed == total else 1


def run_gpu_mode() -> int:
    """Compile + launch the CUDA binary and compare to oracle.

    Requires a real GPU. In this environment it is NOT_EXECUTED - NO GPU.
    """
    print("[MODE] gpu - compares real CUDA output to numpy oracle")
    try:
        from elementwise_add_launcher import launch_or_block  # local import
    except Exception as exc:  # noqa: BLE001
        print(f"  launcher import failed: {exc}")
    print("  NOT_EXECUTED - NO GPU IN ENVIRONMENT")
    print("  On a GPU host this would: compile kernels/elementwise_add.cu, "
          "run the binary via the launcher, parse its output, and assert "
          "np.allclose(device_out, elementwise_add_reference(a, b)).")
    # Fail-closed: GPU mode cannot be claimed as passing here.
    return 2


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="CUDA-EP-001 GPU visible tests")
    parser.add_argument("--gpu", action="store_true",
                        help="run against real GPU (requires CUDA + NVIDIA GPU)")
    parser.add_argument("--reference", action="store_true",
                        help="run numpy reference oracle only (default)")
    args = parser.parse_args(argv)

    if args.gpu:
        return run_gpu_mode()
    return run_reference_mode()


if __name__ == "__main__":
    sys.exit(main())
