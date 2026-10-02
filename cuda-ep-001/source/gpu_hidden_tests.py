"""
gpu_hidden_tests.py
===================
CUDA-EP-001 GPU Phase - HIDDEN test suite for the elementwise_add kernel.
Remnant Fieldworks Inc. | CUDA-EP-001 | v1.0 | 2026-10-01
RESEARCH ONLY - NOT PRODUCTION

The HIDDEN tests are digested (SHA-256) into the Request Contract BEFORE the
candidate kernel is allowed to run. They are deliberately drawn from DIFFERENT
input distributions than the visible tests, so that passing the visible tests
does not guarantee passing the hidden ones. This models the governance split:
the gate binds to the hidden-test attestation digest, not to the visible tests.

Oracle: out[i] = a[i] + b[i]  (float32), using numpy.

Modes:
  * Reference mode (default / `--reference`): run the numpy oracle only. Runs
    without a GPU and proves the hidden-test logic is correct and deterministic.
  * GPU mode (`--gpu`): compare real CUDA output to the oracle. Requires a GPU.
    NOT_EXECUTED - NO GPU in the current environment.
"""

from __future__ import annotations

import argparse
import sys

import numpy as np

N = 1024
HIDDEN_SEED = 770042  # distinct from the visible-test seed on purpose


def elementwise_add_reference(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    a = np.asarray(a, dtype=np.float32)
    b = np.asarray(b, dtype=np.float32)
    return (a + b).astype(np.float32)


def hidden_test_vectors():
    """HIDDEN vectors - different distributions from the visible suite."""
    rng = np.random.default_rng(HIDDEN_SEED)

    # H1: large-magnitude values probing float32 rounding
    a1 = rng.uniform(-1e6, 1e6, size=N).astype(np.float32)
    b1 = rng.uniform(-1e6, 1e6, size=N).astype(np.float32)

    # H2: small denormal-adjacent values
    a2 = rng.uniform(-1e-3, 1e-3, size=N).astype(np.float32)
    b2 = rng.uniform(-1e-3, 1e-3, size=N).astype(np.float32)

    # H3: exact-cancellation pattern (a + (-a) = 0)
    a3 = rng.uniform(-500.0, 500.0, size=N).astype(np.float32)
    b3 = (-a3).astype(np.float32)

    # H4: mixed signs and a constant offset
    a4 = (rng.standard_normal(N) * 50.0).astype(np.float32)
    b4 = np.full(N, -12.25, dtype=np.float32)

    return [
        ("hidden_large_magnitude", a1, b1),
        ("hidden_small_values", a2, b2),
        ("hidden_exact_cancellation", a3, b3),
        ("hidden_mixed_offset", a4, b4),
    ]


def run_reference_mode() -> int:
    print("[MODE] reference (numpy CPU oracle) - no GPU required")
    passed = 0
    total = 0
    for name, a, b in hidden_test_vectors():
        total += 1
        out = elementwise_add_reference(a, b)
        ref64 = a.astype(np.float64) + b.astype(np.float64)
        close = np.allclose(out.astype(np.float64), ref64, rtol=1e-5, atol=1e-3)
        det = np.array_equal(out, elementwise_add_reference(a.copy(), b.copy()))
        # H3 should produce all-zero output
        extra_ok = True
        if name == "hidden_exact_cancellation":
            extra_ok = bool(np.all(out == 0.0))
        ok = close and det and extra_ok and out.dtype == np.float32
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}: close_to_f64={close} "
              f"deterministic={det} extra_ok={extra_ok}")
        if ok:
            passed += 1
    print(f"HIDDEN REFERENCE TESTS: {passed}/{total} passed")
    return 0 if passed == total else 1


def run_gpu_mode() -> int:
    print("[MODE] gpu - compares real CUDA output to numpy oracle")
    print("  NOT_EXECUTED - NO GPU IN ENVIRONMENT")
    print("  On a GPU host this would launch the binary and assert "
          "np.allclose(device_out, elementwise_add_reference(a, b)) for every "
          "hidden vector.")
    return 2


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="CUDA-EP-001 GPU hidden tests")
    parser.add_argument("--gpu", action="store_true")
    parser.add_argument("--reference", action="store_true")
    args = parser.parse_args(argv)
    if args.gpu:
        return run_gpu_mode()
    return run_reference_mode()


if __name__ == "__main__":
    sys.exit(main())
