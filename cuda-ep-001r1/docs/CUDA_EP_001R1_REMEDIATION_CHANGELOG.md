# CUDA-EP-001R1 — Remediation Changelog

Every code change made for R1 vs the frozen CUDA-EP-001 implementation, with the
machine-readable diffs that back it. The original `gpu_gateway.py` and
`gpu_policy.json` are **not** modified; R1 introduces new files
(`gpu_gateway_r1.py`, `gpu_policy_r1.json`) so the originals stay byte-frozen.

See: `diff/gpu_gateway__original_vs_r1.diff`, `diff/gpu_policy__original_vs_r1.diff`,
`diff/R1_CHANGE_DESCRIPTOR.json`.

---

## Changed files

| File | Change | Original |
|------|--------|----------|
| `source/gpu_gateway_r1.py` | NEW — remediated gateway (C5/C6/C7) | `gpu_gateway.py` untouched |
| `source/gpu_policy_r1.json` | NEW — adds remediation policy fields | `gpu_policy.json` untouched |
| `gpu_exec/gpu_real_run_r1.py` | NEW — R1 retest harness (C0/C5/C6/C7/C8) + preregistration gate | `gpu_real_run.py` untouched |
| `gpu_exec/colab_entry_r1.py` | NEW — Colab entry for R1 real-GPU run | `colab_entry.py` untouched |

## Carried byte-identical (verified SHA-256)

| File | SHA-256 |
|------|---------|
| `source/kernels/elementwise_add.cu` | `268d125fe316156e9da44852afeca54838974a4a90643c375d233b5491f89b0d` |
| `source/elementwise_add_launcher.py` | `ea411c6d0cb9c6abd3b4ed8f438e8cb83555da7e31ce80b7cba5a3ba67ddf01e` |
| `source/gpu_functional_tests.py` | `b19fb40cf0408742d2f9bdef0e3549f572db6c0f657a85a2cfc189df03e81fb9` |
| `source/gpu_hidden_tests.py` | `3d9f510dde2625002a8f6f05070faffd8b6d65b5dd5af9cc282225178e2f4898` |

---

## C5 — real control-state predicate

- **Was:** control engine returned PASS iff `shutil.which("nvidia-smi")` was
  present. On a live GPU this always passed → HOLD could not be induced.
- **Now:** `_control()` compares the contract's `control_state_token` against the
  policy field `required_control_state` (`"LAUNCH_WINDOW_OPEN"`), independent of
  GPU presence.
  - token == required → control PASS
  - token != required, or token absent → control HOLD, no launch
- **Policy:** added `required_control_state: "LAUNCH_WINDOW_OPEN"`.

## C6 — native gateway VERIFICATION_FAILURE

- **Was:** `evaluate()` had no signature-verification branch; mutation was caught
  only by an external ProofRecord verifier.
- **Now:** a verification engine runs inside `evaluate()` **before** capability
  release. The gateway recomputes the canonical ProofRecord body and verifies the
  Dilithium3 signature.
  - valid → verification PASS
  - invalid / mutated / missing → native `VERIFICATION_FAILURE`, no launch
- **Policy:** added `require_proofrecord_verification: true` and VERIFICATION_FAILURE semantics.

## C7 — requested-vs-detected compute-capability comparison

- **Was:** constraint engine DENYd only on an EMPTY target capability; never
  compared against the physical device.
- **Now:** `detect_device_compute_capability()` reads the real device cap
  (`nvidia-smi --query-gpu=compute_cap`, torch fallback). `_constraint()`:
  - required empty → DENY (absent)
  - required not in `accepted_compute_capabilities` → DENY (not accepted)
  - required != detected (two real non-empty values) → `DENY_CAP_MISMATCH`
  - required == detected (and accepted) → PASS
- **Policy:** added `accepted_compute_capabilities: ["8.0","7.5","8.6"]`.

---

## Verification that no post-hoc tuning occurred

The pre-run manifest (`00_freeze/CUDA_EP_001R1_PRERUN_MANIFEST.sha256`) and the
post-run manifest (`docs/CUDA_EP_001R1_POSTRUN_HASH_MANIFEST.sha256`) list
identical SHA-256 values for `gpu_gateway_r1.py`, `gpu_policy_r1.json`,
`gpu_real_run_r1.py`, the kernel, and the launcher. The source that produced the
results is the source that was frozen before the run.
