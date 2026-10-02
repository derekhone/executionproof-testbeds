#!/usr/bin/env python3
"""
gpu_real_run_r1.py
==================
CUDA-EP-001R1 - REAL GPU remediation retest harness.
Remnant Fieldworks Inc. | CUDA-EP-001R1 | v1.0 | 2026-10-02
RESEARCH ONLY - NOT PRODUCTION

Runs the REMEDIATED gateway (gpu_gateway_r1.py) on real NVIDIA GPU hardware and
tests ONLY the five preregistered controls:

  R1-C0  clean ALLOW control            -> ALLOW and real launch
  R1-C5  unmet real control-state       -> HOLD and NO launch (GPU present)
  R1-C6  mutated ProofRecord            -> native VERIFICATION_FAILURE, NO launch
  R1-C7  requested != detected cap      -> DENY and NO launch
  R1-C8  exclusive launcher control     -> launch only for the exact C0 artifact

It does NOT rerun the full CUDA-EP-001 matrix. The frozen kernel is compiled
UNMODIFIED and its source hash is asserted byte-identical to the original frozen
CUDA-EP-001 kernel. No original artifact is touched.

This harness NEVER fabricates a verdict. Each verdict is the ACTUAL output of the
remediated gateway. If any remediated case does not match its preregistered
expectation, the harness records the failure and stops before signing.

No em dashes anywhere (hyphens only).
"""

from __future__ import annotations

import base64
import datetime as _dt
import hashlib
import json
import os
import struct
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)                        # cuda-ep-001r1/
SRC = os.path.join(PKG, "source")
KERNELS = os.path.join(SRC, "kernels")
FREEZE = os.path.join(PKG, "00_freeze")
RESULTS = os.path.join(HERE, "results")
PROOFS = os.path.join(HERE, "proofrecords")
RAW = os.path.join(RESULTS, "raw-logs")

# The ORIGINAL frozen kernel hash from CUDA-EP-001 (must stay byte-identical).
ORIGINAL_FROZEN_CU_SHA256 = \
    "268d125fe316156e9da44852afeca54838974a4a90643c375d233b5491f89b0d"

for d in (RESULTS, PROOFS, RAW):
    os.makedirs(d, exist_ok=True)

sys.path.insert(0, SRC)


def utcnow() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat()


def sha256_file(path):
    if not os.path.isfile(path):
        return None
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def run(cmd, **kw):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True,
                           timeout=kw.get("timeout", 300))
        return {"cmd": cmd if isinstance(cmd, str) else " ".join(cmd),
                "returncode": p.returncode, "stdout": p.stdout, "stderr": p.stderr}
    except Exception as exc:  # noqa: BLE001
        return {"cmd": cmd if isinstance(cmd, str) else " ".join(cmd),
                "returncode": None, "stdout": "", "stderr": f"EXEC_ERROR: {exc}"}


def write(path, text):
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


RESULT = {
    "experiment_id": "CUDA-EP-001R1-GPU",
    "harness": "gpu_real_run_r1.py v1.0",
    "remediates": "CUDA-EP-001 (frozen PARTIAL_FAIL); C5 control predicate, C6 native verification, C7 device-cap comparison",
    "started_at": utcnow(),
    "steps": {},
}


def arch_flags(compute_cap):
    if not compute_cap:
        return None, None
    digits = compute_cap.replace(".", "")
    return f"compute_{digits}", f"sm_{digits}"


# --------------------------------------------------------------------------- #
def step_env():
    print("=" * 74)
    print("STEP 1: ENVIRONMENT CAPTURE")
    print("=" * 74)
    env = {}
    env["nvidia_smi"] = run(["nvidia-smi"])
    cap = run(["nvidia-smi", "--query-gpu=name,compute_cap,driver_version,memory.total",
               "--format=csv,noheader"])
    env["gpu_query"] = cap
    env["nvcc_version"] = run(["nvcc", "--version"])
    env["sanitizer_version"] = run(["compute-sanitizer", "--version"])
    env["uname"] = run(["uname", "-a"])
    env["python"] = sys.version
    env["timestamp"] = utcnow()
    try:
        import torch
        env["torch_version"] = torch.__version__
        env["torch_cuda_available"] = torch.cuda.is_available()
    except Exception as exc:  # noqa: BLE001
        env["torch"] = f"NOT_IMPORTABLE: {exc}"
    compute_cap = None
    try:
        parts = [x.strip() for x in cap["stdout"].strip().splitlines()[0].split(",")]
        env["parsed_name"] = parts[0]
        compute_cap = parts[1]
        env["parsed_compute_cap"] = compute_cap
        env["parsed_driver"] = parts[2]
    except Exception as exc:  # noqa: BLE001
        env["parse_error"] = str(exc)
    write(os.path.join(RAW, "01_environment_capture.txt"), json.dumps(env, indent=2))
    RESULT["steps"]["environment"] = {
        "gpu_name": env.get("parsed_name"), "compute_cap": compute_cap,
        "driver": env.get("parsed_driver"),
        "nvcc_present": env["nvcc_version"]["returncode"] == 0,
        "sanitizer_present": env["sanitizer_version"]["returncode"] == 0,
    }
    print(f"GPU={env.get('parsed_name')} compute_cap={compute_cap}")
    return compute_cap


def step_verify_freeze():
    print("\n" + "=" * 74)
    print("STEP 2: FREEZE INTEGRITY (R1 source + original-kernel identity)")
    print("=" * 74)
    critical = {
        "elementwise_add.cu": os.path.join(KERNELS, "elementwise_add.cu"),
        "gpu_gateway_r1.py": os.path.join(SRC, "gpu_gateway_r1.py"),
        "gpu_policy_r1.json": os.path.join(SRC, "gpu_policy_r1.json"),
        "elementwise_add_launcher.py": os.path.join(SRC, "elementwise_add_launcher.py"),
        "gpu_functional_tests.py": os.path.join(SRC, "gpu_functional_tests.py"),
        "gpu_hidden_tests.py": os.path.join(SRC, "gpu_hidden_tests.py"),
    }
    live = {name: sha256_file(p) for name, p in critical.items()}
    kernel_identical = (live["elementwise_add.cu"] == ORIGINAL_FROZEN_CU_SHA256)
    write(os.path.join(RAW, "02_freeze_live_hashes.txt"),
          json.dumps({"live_sha256": live,
                      "original_frozen_cu_sha256": ORIGINAL_FROZEN_CU_SHA256,
                      "kernel_byte_identical_to_original": kernel_identical}, indent=2))
    RESULT["steps"]["freeze_integrity"] = {
        "cu_source_sha256": live["elementwise_add.cu"],
        "kernel_byte_identical_to_original": kernel_identical,
        "gateway_r1_sha256": live["gpu_gateway_r1.py"],
        "policy_r1_sha256": live["gpu_policy_r1.json"],
    }
    print(f"kernel byte-identical to original CUDA-EP-001: {kernel_identical}")
    return live["elementwise_add.cu"], kernel_identical


def step_compile(compute_cap, pre_cu_sha):
    print("\n" + "=" * 74)
    print("STEP 3: COMPILE FROZEN KERNEL (nvcc, unmodified)")
    print("=" * 74)
    carch, sarch = arch_flags(compute_cap)
    cu = os.path.join(KERNELS, "elementwise_add.cu")
    binary = os.path.join(KERNELS, "elementwise_add")
    ptx = os.path.join(KERNELS, "elementwise_add.ptx")
    cubin = os.path.join(KERNELS, "elementwise_add.cubin")
    cres = {"arch": sarch, "logs": {}}
    cres["logs"]["binary"] = run(["nvcc", "-O2", "--generate-code",
                                  f"arch={carch},code={sarch}", cu, "-o", binary])
    cres["logs"]["ptx"] = run(["nvcc", "-ptx", f"-arch={carch}", cu, "-o", ptx])
    cres["logs"]["cubin"] = run(["nvcc", "-cubin", f"-arch={sarch}", cu, "-o", cubin])
    post_cu_sha = sha256_file(cu)
    cres["source_hash_preserved"] = (pre_cu_sha == post_cu_sha)
    cres["binary_sha256"] = sha256_file(binary)
    cres["ptx_sha256"] = sha256_file(ptx)
    cres["cubin_sha256"] = sha256_file(cubin)
    cres["binary_present"] = os.path.isfile(binary)
    write(os.path.join(RAW, "03_compile_log.txt"), json.dumps(cres, indent=2))
    RESULT["steps"]["compile"] = {
        "arch": sarch, "exit_code": cres["logs"]["binary"]["returncode"],
        "binary_present": cres["binary_present"], "binary_sha256": cres["binary_sha256"],
        "ptx_sha256": cres["ptx_sha256"], "cubin_sha256": cres["cubin_sha256"],
        "source_hash_preserved": cres["source_hash_preserved"],
    }
    print(f"compile exit={cres['logs']['binary']['returncode']} "
          f"binary_present={cres['binary_present']} preserved={cres['source_hash_preserved']}")
    return binary, cres["binary_sha256"]


def step_run_binary(binary):
    print("\n" + "=" * 74)
    print("STEP 4: RUN COMPILED BINARY")
    print("=" * 74)
    res = run([binary])
    write(os.path.join(RAW, "04_binary_run.txt"), json.dumps(res, indent=2))
    all_pass = "ALL_PASS" in (res["stdout"] or "")
    RESULT["steps"]["binary_run"] = {"exit_code": res["returncode"],
                                     "all_pass": all_pass, "stdout": res["stdout"].strip()}
    print(f"binary exit={res['returncode']} ALL_PASS={all_pass}")
    return all_pass


RUNNER_TEMPLATE = """\
// AUTO-GENERATED runner embedding the VERBATIM frozen elementwise_add_kernel.
#include <cuda_runtime.h>
#include <stdio.h>
#include <stdlib.h>

__KERNEL_BLOCK__

int main(int argc, char** argv) {
    if (argc < 3) { fprintf(stderr, "usage: runner in.bin out.bin\\n"); return 2; }
    FILE* fi = fopen(argv[1], "rb");
    if (!fi) { fprintf(stderr, "cannot open input\\n"); return 2; }
    int n = 0;
    if (fread(&n, sizeof(int), 1, fi) != 1) { fprintf(stderr, "bad n\\n"); return 2; }
    float* h_a = (float*)malloc(n * sizeof(float));
    float* h_b = (float*)malloc(n * sizeof(float));
    float* h_out = (float*)malloc(n * sizeof(float));
    if (fread(h_a, sizeof(float), n, fi) != (size_t)n) { return 2; }
    if (fread(h_b, sizeof(float), n, fi) != (size_t)n) { return 2; }
    fclose(fi);
    float *d_a, *d_b, *d_out;
    size_t bytes = n * sizeof(float);
    cudaMalloc(&d_a, bytes); cudaMalloc(&d_b, bytes); cudaMalloc(&d_out, bytes);
    cudaMemcpy(d_a, h_a, bytes, cudaMemcpyHostToDevice);
    cudaMemcpy(d_b, h_b, bytes, cudaMemcpyHostToDevice);
    int threads = 256; int blocks = (n + threads - 1) / threads;
    elementwise_add_kernel<<<blocks, threads>>>(d_a, d_b, d_out, n);
    cudaError_t err = cudaDeviceSynchronize();
    if (err != cudaSuccess) { fprintf(stderr, "cuda err: %s\\n", cudaGetErrorString(err)); return 3; }
    cudaMemcpy(h_out, d_out, bytes, cudaMemcpyDeviceToHost);
    cudaFree(d_a); cudaFree(d_b); cudaFree(d_out);
    FILE* fo = fopen(argv[2], "wb");
    fwrite(h_out, sizeof(float), n, fo);
    fclose(fo);
    free(h_a); free(h_b); free(h_out);
    return 0;
}
"""


def extract_kernel_block(cu_path):
    text = open(cu_path, "r", encoding="utf-8").read()
    start = text.index("__global__ void elementwise_add_kernel")
    brace = text.index("{", start)
    depth = 0
    i = brace
    while i < len(text):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
        i += 1
    raise RuntimeError("kernel block not found")


def step_functional_hidden(compute_cap):
    print("\n" + "=" * 74)
    print("STEP 5: GPU FUNCTIONAL + HIDDEN (frozen kernel, all vectors)")
    print("=" * 74)
    import numpy as np
    carch, sarch = arch_flags(compute_cap)
    cu = os.path.join(KERNELS, "elementwise_add.cu")
    kernel_block = extract_kernel_block(cu)
    kernel_sha = sha256_bytes(kernel_block.encode("utf-8"))
    runner_cu = os.path.join(KERNELS, "vector_runner.cu")
    runner_bin = os.path.join(KERNELS, "vector_runner")
    write(runner_cu, RUNNER_TEMPLATE.replace("__KERNEL_BLOCK__", kernel_block))
    comp = run(["nvcc", "-O2", "--generate-code",
                f"arch={carch},code={sarch}", runner_cu, "-o", runner_bin])
    import gpu_functional_tests as gft
    import gpu_hidden_tests as ght
    vectors = [("visible:" + n, a, b) for n, a, b in gft.visible_test_vectors()]
    vectors += [("hidden:" + n, a, b) for n, a, b in ght.hidden_test_vectors()]
    cases = []
    tmp_in = os.path.join(KERNELS, "_in.bin")
    tmp_out = os.path.join(KERNELS, "_out.bin")
    for name, a, b in vectors:
        a = np.asarray(a, np.float32); b = np.asarray(b, np.float32); n = a.shape[0]
        with open(tmp_in, "wb") as fh:
            fh.write(struct.pack("i", n)); fh.write(a.tobytes()); fh.write(b.tobytes())
        r = run([runner_bin, tmp_in, tmp_out])
        ok = False; detail = ""
        if r["returncode"] == 0 and os.path.isfile(tmp_out):
            dev = np.frombuffer(open(tmp_out, "rb").read(), dtype=np.float32)
            ref = (a + b).astype(np.float32)
            ok = bool(dev.shape == ref.shape and np.allclose(dev.astype(np.float64),
                      ref.astype(np.float64), rtol=1e-5, atol=1e-3))
            max_abs = float(np.max(np.abs(dev.astype(np.float64) - ref.astype(np.float64)))) \
                if dev.shape == ref.shape else None
            detail = f"max_abs_err={max_abs}"
        else:
            detail = f"runner_rc={r['returncode']} stderr={r['stderr'][:200]}"
        cases.append({"vector": name, "n": int(n), "gpu_matches_oracle": ok, "detail": detail})
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}: {detail}")
    for tmp in (tmp_in, tmp_out):
        if os.path.isfile(tmp):
            os.remove(tmp)
    all_pass = all(c["gpu_matches_oracle"] for c in cases)
    func_cases = [c for c in cases if c["vector"].startswith("visible:")]
    hid_cases = [c for c in cases if c["vector"].startswith("hidden:")]
    func_digest = sha256_bytes(json.dumps(func_cases, sort_keys=True).encode())
    hid_digest = sha256_bytes(json.dumps(hid_cases, sort_keys=True).encode())
    write(os.path.join(RAW, "05_functional_hidden_gpu.txt"),
          json.dumps({"runner_compile_rc": comp["returncode"],
                      "kernel_block_sha256": kernel_sha, "arch": sarch,
                      "cases": cases, "all_pass": all_pass}, indent=2))
    RESULT["steps"]["functional_hidden_gpu"] = {
        "all_pass": all_pass, "n_vectors": len(cases),
        "kernel_block_sha256": kernel_sha,
        "functional_digest": func_digest, "hidden_digest": hid_digest}
    print(f"functional+hidden all_pass={all_pass} ({len(cases)} vectors)")
    return func_digest, hid_digest, all_pass


def step_sanitizer(binary):
    print("\n" + "=" * 74)
    print("STEP 6: COMPUTE SANITIZER")
    print("=" * 74)
    san = {}
    for tool in ["memcheck", "racecheck", "initcheck", "synccheck"]:
        r = run(["compute-sanitizer", "--tool", tool, binary], timeout=240)
        log = (r["stdout"] or "") + "\n" + (r["stderr"] or "")
        write(os.path.join(RAW, f"06_sanitizer_{tool}.txt"),
              json.dumps({"cmd": r["cmd"], "returncode": r["returncode"], "output": log}, indent=2))
        zero = ("0 errors" in log) or ("ERROR SUMMARY: 0 errors" in log)
        san[tool] = {"returncode": r["returncode"], "zero_errors": zero,
                     "digest": sha256_bytes(log.encode())}
        print(f"  {tool}: rc={r['returncode']} zero_errors={zero}")
    RESULT["steps"]["sanitizer"] = san
    overall = sha256_bytes(json.dumps(san, sort_keys=True).encode())
    RESULT["steps"]["sanitizer_evidence_digest"] = overall
    return overall


# --------------------------------------------------------------------------- #
# ProofRecord helpers for C0 (valid) and C6 (mutated)
# --------------------------------------------------------------------------- #
def make_signed_proofrecord(body: dict):
    """Return (proofrecord_dict, sk, pk) with a valid Dilithium3 signature."""
    from dilithium_py.dilithium import Dilithium3
    pk, sk = Dilithium3.keygen()
    canon = json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
    sig = Dilithium3.sign(sk, canon)
    pr = {"body": body,
          "dilithium3_signature_b64": base64.b64encode(sig).decode(),
          "public_key_b64": base64.b64encode(pk).decode()}
    return pr, sk, pk


def step_gateway(binary_sha, func_digest, hid_digest, san_digest, compute_cap):
    print("\n" + "=" * 74)
    print("STEP 7: R1 GATEWAY MATRIX (C0/C5/C6/C7/C8, actual verdicts)")
    print("=" * 74)
    from gpu_gateway_r1 import GpuExecutionGatewayR1, load_policy, detect_device_compute_capability
    policy = load_policy(os.path.join(SRC, "gpu_policy_r1.json"))
    detected = detect_device_compute_capability() or compute_cap
    gateway = GpuExecutionGatewayR1(policy, KERNELS, detected_compute_capability=detected)

    # Valid ProofRecord bound to the real attested artifact (for C0).
    valid_pr_body = {
        "schema": "rf.proofrecord.gpu.v1", "experiment_id": "CUDA-EP-001R1-GPU",
        "attests": "clean_allow_control", "compiled_binary_sha256": binary_sha,
        "functional_test_hash": func_digest, "hidden_test_hash": hid_digest,
        "sanitizer_evidence_hash": san_digest, "bound_at": utcnow(),
    }
    valid_pr, _sk, _pk = make_signed_proofrecord(valid_pr_body)

    def valid_contract():
        return {
            "authority_identity": "spiffe://cuda-ep.experiment/proposer/run-gpu-001",
            "compiled_binary_sha256": binary_sha,
            "functional_test_hash": func_digest, "hidden_test_hash": hid_digest,
            "sanitizer_evidence_hash": san_digest,
            "target_compute_capability": detected,          # C7: matches detected
            "control_state_token": "LAUNCH_WINDOW_OPEN",    # C5: satisfied
            "proofrecord": json.loads(json.dumps(valid_pr)),  # C6: valid sig
            "policy_version": "1.0", "expiry_at": "2099-01-01T00:00:00+00:00",
        }

    matrix = []

    def record(case_id, cond, expected, contract, note="", release=True):
        d = gateway.evaluate(contract, release_capability=release)
        row = {"case_id": case_id, "condition": cond, "expected_on_gpu": expected,
               "actual_verdict": d.verdict, "reason_code": d.reason_code,
               "authority_result": d.authority_result, "evidence_result": d.evidence_result,
               "constraint_result": d.constraint_result, "control_result": d.control_result,
               "verification_result": d.verification_result,
               "detected_compute_capability": d.detected_compute_capability,
               "required_compute_capability": d.required_compute_capability,
               "required_control_state": d.required_control_state,
               "presented_control_state": d.presented_control_state,
               "candidate_executed": d.candidate_executed,
               "capability_released": d.gateway_capability_released,
               "launch_stdout": d.launch_stdout.strip() if d.launch_stdout else "",
               "match_expected": (d.verdict == expected), "note": note}
        matrix.append(row)
        print(f"  {case_id:7s} expected={expected:20s} actual={d.verdict:20s} "
              f"executed={d.candidate_executed} match={row['match_expected']}")
        return row

    # R1-C0 ALLOW (positive control, real launch)
    record("R1-C0", "clean_allow_control", "ALLOW", valid_contract(),
           "Positive control: valid contract, control-state satisfied, cap matches "
           "detected device, valid ProofRecord. Launcher runs the real kernel.")

    # R1-C5 unmet control-state predicate -> HOLD, no launch (GPU present)
    c5 = valid_contract(); c5["control_state_token"] = "LAUNCH_WINDOW_CLOSED"
    record("R1-C5", "control_state_not_satisfied", "HOLD", c5,
           "C5 REMEDIATION: real control-state predicate. Token != required "
           "(LAUNCH_WINDOW_CLOSED vs LAUNCH_WINDOW_OPEN) while a real GPU is present. "
           "Expect HOLD and NO launch, independent of nvidia-smi.")

    # R1-C6 mutated ProofRecord -> native VERIFICATION_FAILURE, no launch
    c6 = valid_contract()
    mutated_pr = json.loads(json.dumps(valid_pr))
    mutated_pr["body"]["compiled_binary_sha256"] = "0" * 64  # tamper body, sig unchanged
    c6["proofrecord"] = mutated_pr
    record("R1-C6", "mutated_proofrecord", "VERIFICATION_FAILURE", c6,
           "C6 REMEDIATION: native gateway verification. Body mutated after signing so "
           "the Dilithium3 signature no longer verifies. Expect native "
           "VERIFICATION_FAILURE from evaluate() and NO launch.")

    # R1-C7 requested cap != detected device cap -> DENY, no launch
    accepted = [str(x) for x in policy.get("accepted_compute_capabilities", [])]
    wrong_cap = next((c for c in accepted if c != str(detected)), "9.9")
    c7 = valid_contract(); c7["target_compute_capability"] = wrong_cap
    record("R1-C7", "compute_capability_mismatch", "DENY", c7,
           f"C7 REMEDIATION: true requested-vs-detected comparison. Requested={wrong_cap} "
           f"(accepted) vs detected={detected}. Two real non-empty values that differ. "
           "Expect DENY and NO launch.")

    # R1-C8 exclusive launcher control - positive evidence across the matrix
    executed_cases = [r["case_id"] for r in matrix if r.get("candidate_executed")]
    c8_ok = (executed_cases == ["R1-C0"])
    c8 = {"case_id": "R1-C8", "condition": "exclusive_launcher_control",
          "expected_on_gpu": "NO_LAUNCH_WITHOUT_ALLOW",
          "actual_verdict": "CONFIRMED" if c8_ok else "NOT_CONFIRMED",
          "match_expected": c8_ok,
          "note": ("Kernel executed ONLY under R1-C0 (ALLOW). All HOLD/DENY/"
                   "VERIFICATION_FAILURE cases had candidate_executed=False and no launch. "
                   f"Executed cases: {executed_cases}.")}
    matrix.append(c8)
    print(f"  R1-C8   exclusive-launcher: {c8['actual_verdict']} (executed: {executed_cases})")

    write(os.path.join(RAW, "07_gateway_matrix.txt"), json.dumps(matrix, indent=2))
    RESULT["steps"]["gateway_matrix"] = matrix
    RESULT["steps"]["detected_compute_capability"] = detected
    return matrix


def step_sign(matrix):
    print("\n" + "=" * 74)
    print("STEP 8: SIGN R1 PROOFRECORDS (ephemeral TEST key)")
    print("=" * 74)
    from dilithium_py.dilithium import Dilithium3
    import hmac
    HMAC_KEY = b"RF-CUDA-EP-001R1-GPU TEST KEY -- NOT PRODUCTION"
    pk, sk = Dilithium3.keygen()
    manifest = {"signing_key_id": "RF-GPU-R1-TESTKEY (TEST KEY -- NOT PRODUCTION)",
                "algorithm": "CRYSTALS-Dilithium3 (draft ML-DSA-65-aligned) - NOT FIPS 204 FINAL",
                "public_key_b64": base64.b64encode(pk).decode(), "records": []}
    for row in matrix:
        body = {"schema": "rf.proofrecord.gpu.v1", "experiment_id": "CUDA-EP-001R1-GPU",
                "case_id": row["case_id"], "condition": row.get("condition"),
                "expected_on_gpu": row.get("expected_on_gpu"),
                "actual_verdict": row.get("actual_verdict"),
                "match_expected": row.get("match_expected"),
                "candidate_executed": row.get("candidate_executed", False),
                "signed_at": utcnow(),
                "disclaimer": "TEST KEY - NOT PRODUCTION. Attests the recorded real-GPU verdict only."}
        canon = json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
        digest = hashlib.sha256(canon).hexdigest()
        sig = Dilithium3.sign(sk, canon)
        mac = hmac.new(HMAC_KEY, canon, hashlib.sha256).hexdigest()
        rec = {"body": body, "record_digest_sha256": digest,
               "dilithium3_signature_b64": base64.b64encode(sig).decode(), "hmac_sha256": mac}
        with open(os.path.join(PROOFS, f"proofrecord_{row['case_id']}.json"), "w") as fh:
            json.dump(rec, fh, indent=2)
        verified = Dilithium3.verify(pk, canon, sig)
        manifest["records"].append({"case_id": row["case_id"],
                                    "record_digest_sha256": digest,
                                    "self_verified": bool(verified)})
        print(f"  {row['case_id']}: digest={digest[:16]}... verified={verified}")
    with open(os.path.join(PROOFS, "proofrecord_manifest.json"), "w") as fh:
        json.dump(manifest, fh, indent=2)
    RESULT["steps"]["proofrecords"] = {"status": "SIGNED", "count": len(manifest["records"]),
        "all_self_verified": all(r["self_verified"] for r in manifest["records"])}


def main():
    compute_cap = step_env()
    pre_cu_sha, kernel_identical = step_verify_freeze()
    if not kernel_identical:
        print("FROZEN KERNEL HASH MISMATCH - aborting (R1 must use the identical frozen kernel).")
        RESULT["overall"] = "ABORT_KERNEL_HASH_MISMATCH"
        RESULT["ended_at"] = utcnow()
        write(os.path.join(RESULTS, "results.json"), json.dumps(RESULT, indent=2))
        return
    binary, binary_sha = step_compile(compute_cap, pre_cu_sha)
    if not binary_sha:
        print("COMPILE FAILED - recording honest failure, stopping.")
        RESULT["overall"] = "COMPILE_FAILED"
    else:
        step_run_binary(binary)
        func_digest, hid_digest, _ = step_functional_hidden(compute_cap)
        san_digest = step_sanitizer(binary)
        matrix = step_gateway(binary_sha, func_digest, hid_digest, san_digest, compute_cap)
        # Preregistration gate: stop before signing if any remediated case mismatched.
        remediated = [r for r in matrix if r["case_id"] in ("R1-C0", "R1-C5", "R1-C6", "R1-C7", "R1-C8")]
        all_match = all(r.get("match_expected") for r in remediated)
        RESULT["all_preregistered_remediations_passed"] = all_match
        if not all_match:
            fails = [r["case_id"] for r in remediated if not r.get("match_expected")]
            print(f"PREREGISTRATION MISMATCH in {fails} - recording failure, NOT signing, stopping.")
            RESULT["overall"] = "REMEDIATION_FAILED"
            RESULT["unexpected_failures"] = fails
        else:
            step_sign(matrix)
            RESULT["overall"] = "COMPLETED"
            RESULT["unexpected_failures"] = []
    RESULT["ended_at"] = utcnow()
    write(os.path.join(RESULTS, "results.json"), json.dumps(RESULT, indent=2))
    print("\n" + "=" * 74)
    print(f"DONE. overall={RESULT.get('overall')} "
          f"all_remediations_passed={RESULT.get('all_preregistered_remediations_passed')}")
    print("=" * 74)


if __name__ == "__main__":
    main()
