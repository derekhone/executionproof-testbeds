#!/usr/bin/env python3
"""
sign_gpu_proofrecords.py
------------------------
Generates and cryptographically signs one ProofRecord per GPU case (GPU-C0..GPU-C8)
for experiment CUDA-EP-001-GPU.

IMPORTANT HONESTY NOTES
  - This environment has NO GPU. Every record carries:
        decision               = "BLOCKED_NO_GPU"
        execution_status       = "NOT_EXECUTED"
        environment_verdict    = "NO_GPU_IN_ENVIRONMENT"
        candidate_executed     = false
        gateway_capability_released = false
  - Signatures are REAL. They are produced with ML-DSA / CRYSTALS-Dilithium3 via
    `from dilithium_py.dilithium import Dilithium3` and with HMAC-SHA256.
    They attest ONLY that "a kernel launch was refused because no GPU was present",
    NOT that any GPU computation happened.
  - The signing key is an ephemeral TEST key generated fresh on every run. It is
    labelled "TEST KEY -- NOT PRODUCTION". Running this script again produces new
    keys and therefore new signatures; the record_digest over the signed body is
    reproducible, the signature bytes are not.

No em dashes are used anywhere in emitted content (hyphens only).
"""

import base64
import hashlib
import hmac
import json
import os
import sys

from dilithium_py.dilithium import Dilithium3

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)

SIGNING_KEY_ID = "RF-GPU-TESTKEY-2026-10-01 (TEST KEY -- NOT PRODUCTION)"
HMAC_KEY = b"RF-CUDA-EP-001-GPU TEST KEY -- NOT PRODUCTION"


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_json(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


# Digests over real files in this package.
ENV_DIGEST = sha256_file(os.path.join(PKG, "01_GPU_ENVIRONMENT_RECORD.json"))
POLICY_DIGEST = sha256_file(
    os.path.join(PKG, "09_GPU_EXECUTION_GATEWAY", "gpu_policy.json")
)
SOURCE_DIGEST = sha256_file(
    os.path.join(PKG, "09_GPU_EXECUTION_GATEWAY", "kernels", "elementwise_add.cu")
)

# Per-case definitions: what each case WOULD decide on real GPU hardware.
CASES = [
    ("GPU-C0", "clean baseline", "launch_kernel", "ALLOW",
     "On GPU: authorized, evidence fresh, artifact matches, capability matches. Launch expected."),
    ("GPU-C1", "authority failure", "launch_kernel", "DENY",
     "On GPU: requester not authorized by policy bundle."),
    ("GPU-C2", "missing evidence", "launch_kernel", "HOLD",
     "On GPU: required functional/sanitizer evidence absent."),
    ("GPU-C3", "policy/expiry constraint", "launch_kernel", "HOLD",
     "On GPU: evidence stale/expired per freshness window."),
    ("GPU-C4", "evidence/artifact mismatch", "launch_kernel", "DENY",
     "On GPU: presented artifact hash does not match evidence binding."),
    ("GPU-C5", "control/gateway not satisfied", "launch_kernel", "HOLD",
     "On GPU: control preconditions for capability release not met."),
    ("GPU-C6", "mutated ProofRecord", "launch_kernel", "VERIFICATION_FAILURE",
     "On GPU: tampered record fails signature/digest verification."),
    ("GPU-C7", "target compute-capability mismatch", "launch_kernel", "DENY",
     "On GPU: requested target compute capability differs from attested build target."),
    ("GPU-C8", "exclusive launcher control", "release_capability", "ALLOW_ONLY_WITH_PROOF",
     "On GPU: capability released only through sanctioned launcher given a valid ALLOW."),
]


def build_record(case_id, condition_name, requested_action, expected_on_gpu, note):
    # Ordered canonical body. Hyphens only; no em dashes.
    body = {
        "schema": "rf.proofrecord.v1",
        "experiment_id": "CUDA-EP-001-GPU",
        "decision_id": case_id,
        "condition_name": condition_name,
        "requested_action": requested_action,
        "requester_identity": "Remnant Fieldworks Inc. - Derek Hone",
        "artifact_digest_presented": SOURCE_DIGEST,
        "artifact_digest_attested": "NOT_EXECUTED - nvcc not available (no compiled binary)",
        "environment_digest": ENV_DIGEST,
        "environment_label": "NOT_EXECUTED - NO GPU",
        "environment_verdict": "NO_GPU_IN_ENVIRONMENT",
        "target_compute_capability": "8.0 (preferred), 7.5 acceptable, 8.6 acceptable",
        "hidden_test_policy": "hidden tests sealed; HIDDEN_SEED applied at run time on GPU",
        "policy_bundle_digest": POLICY_DIGEST,
        "expected_verdict_on_gpu": expected_on_gpu,
        "decision": "BLOCKED_NO_GPU",
        "execution_status": "NOT_EXECUTED",
        "verdict": "NOT_EXECUTED - BLOCKED_NO_GPU",
        "reason_code": "NO_GPU_IN_ENVIRONMENT",
        "candidate_executed": False,
        "gateway_capability_released": False,
        "blocker_evidence": [
            "nvidia-smi: NOT_FOUND",
            "nvcc: NOT_FOUND",
            "/dev/nvidia*: NOT_FOUND",
            "compute-sanitizer: NOT_FOUND",
            "torch.cuda.is_available(): False",
        ],
        "note": note,
        "signing_key_id": SIGNING_KEY_ID,
        "signature_algorithm": "CRYSTALS-Dilithium3 (ML-DSA-65) + HMAC-SHA256",
        "timestamp": "2026-10-01T00:00:00Z",
    }
    return body


def main():
    # Fresh ephemeral TEST keypair per run.
    pk, sk = Dilithium3.keygen()
    pk_b64 = base64.b64encode(pk).decode("ascii")

    manifest = {
        "document_type": "GPU_PROOFRECORD_MANIFEST",
        "experiment_id": "CUDA-EP-001-GPU",
        "label": "NOT_EXECUTED - NO GPU",
        "signature_algorithm": "CRYSTALS-Dilithium3 (ML-DSA-65) + HMAC-SHA256",
        "signing_key_id": SIGNING_KEY_ID,
        "dilithium_public_key_b64_this_run": pk_b64,
        "key_note": (
            "Ephemeral TEST key generated fresh on this run. Signatures are real but "
            "attest only that a launch was refused for lack of a GPU. Re-running "
            "regenerates keys and signature bytes; the record_digest over the signed "
            "body is reproducible."
        ),
        "environment_digest": ENV_DIGEST,
        "policy_bundle_digest": POLICY_DIGEST,
        "source_digest": SOURCE_DIGEST,
        "records": [],
    }

    print("GPU ProofRecord signing - CUDA-EP-001-GPU")
    print("Dilithium3 public key length (bytes):", len(pk))
    print("Secret key length (bytes):", len(sk))
    print("-" * 60)

    for case_id, condition_name, requested_action, expected, note in CASES:
        body = build_record(case_id, condition_name, requested_action, expected, note)
        cjson = canonical_json(body)
        record_digest = hashlib.sha256(cjson.encode("ascii")).hexdigest()

        sig = Dilithium3.sign(sk, cjson.encode("ascii"))
        sig_b64 = base64.b64encode(sig).decode("ascii")

        hmac_sig = hmac.new(HMAC_KEY, cjson.encode("ascii"), hashlib.sha256).hexdigest()

        # Verify our own signature immediately (real cryptographic check).
        verify_ok = Dilithium3.verify(pk, cjson.encode("ascii"), sig)

        signed = dict(body)
        signed["record_digest"] = record_digest
        signed["hmac_sha256"] = hmac_sig
        signed["dilithium3_signature_b64"] = sig_b64
        signed["dilithium3_public_key_b64"] = pk_b64
        signed["self_verify_ok"] = bool(verify_ok)
        signed["signature_note"] = (
            "TEST KEY -- NOT PRODUCTION. Signature attests refusal due to no GPU; "
            "it does NOT attest any GPU computation."
        )

        out_path = os.path.join(HERE, f"proofrecord_{case_id}.json")
        with open(out_path, "w") as f:
            json.dump(signed, f, indent=2)
            f.write("\n")

        manifest["records"].append({
            "case_id": case_id,
            "file": f"proofrecord_{case_id}.json",
            "record_digest": record_digest,
            "self_verify_ok": bool(verify_ok),
        })

        print(f"{case_id}: verdict=BLOCKED_NO_GPU self_verify_ok={verify_ok} "
              f"digest={record_digest[:16]}...")

    man_path = os.path.join(HERE, "proofrecord_manifest.json")
    with open(man_path, "w") as f:
        json.dump(manifest, f, indent=2)
        f.write("\n")

    all_ok = all(r["self_verify_ok"] for r in manifest["records"])
    print("-" * 60)
    print("Records written:", len(manifest["records"]))
    print("All self-verify OK:", all_ok)
    print("Manifest:", man_path)
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
