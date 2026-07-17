"""
ARK-445 — Principal 9-arm job submission on ibm_marrakesh (Heron r2)
Tri-State Authorization Discrimination (ALLOW / HOLD / DENY)
Remnant Fieldworks Inc. — Derek Hone

ORDERING CONSTRAINT (enforced in code, Field 27):
  1. spam_results.json MUST exist and its SPAM gate MUST have passed
     (SPAM_A <= 0.02 AND SPAM_P <= 0.02 from arm10). Otherwise this script ABORTS
     without submitting anything.
  2. On pass, transpiles arms 1-9 (optimization_level=3, seed_transpiler=445, NO
     dynamical decoupling), pins them to the frozen physical qubits from
     selected_qubits.json via initial_layout=[Q_A, Q_P], submits ONE job of 9 circuits
     x 8192 shots via SamplerV2.
  3. Immediately records job_id + submission_timestamp to RUN_LOG.md and
     principal_job_meta.json, BEFORE any result retrieval.

Arm10 (spam_idle) is NOT part of the principal job — it ran as the separate SPAM
kill-gate. The principal job is arms 1-9.

Raw counts are the PRIMARY endpoint; no readout mitigation is applied here.
"""

import json
import os
import sys
from datetime import datetime, timezone

from qiskit import transpile
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2

from ark_445_circuits import build_all_arms, INITIAL_LAYOUT, ARM_NAMES, ARM_CLASS, ARM_EXPECT

HERE = os.path.dirname(os.path.abspath(__file__))
SECRETS = "/home/ubuntu/.config/abacusai_auth_secrets.json"

BACKEND_NAME = "ibm_marrakesh"
CHANNEL = "ibm_quantum_platform"
INSTANCE = "open-instance"
SHOTS = 8192
OPT_LEVEL = 3
SEED_TRANSPILER = 445
SPAM_CEILING = 0.02

# Principal job arms = arms 1-9 (arm10 is the separate SPAM gate).
PRINCIPAL_ARMS = ARM_NAMES[:9]


def load_token():
    with open(SECRETS) as f:
        return json.load(f)["ibm quantum"]["secrets"]["api_token"]["value"]


def check_spam_gate():
    spam_path = os.path.join(HERE, "spam_results.json")
    if not os.path.exists(spam_path):
        print("[SUBMIT] ABORT: spam_results.json not found. Run ark_445_spam_job.py first.")
        sys.exit(2)
    with open(spam_path) as f:
        spam = json.load(f)
    spam_a = spam["SPAM_A"]
    spam_p = spam["SPAM_P"]
    ok_a = spam_a <= SPAM_CEILING
    ok_p = spam_p <= SPAM_CEILING
    print(f"[SUBMIT] SPAM gate: SPAM_A={spam_a:.4f} (<= {SPAM_CEILING}? {ok_a}), "
          f"SPAM_P={spam_p:.4f} (<= {SPAM_CEILING}? {ok_p})")
    if not (ok_a and ok_p):
        print("[SUBMIT] ABORT: SPAM baseline exceeds ceiling. INDETERMINATE. "
              "Principal job will NOT be submitted.")
        sys.exit(2)
    print("[SUBMIT] SPAM gate PASSED. Proceeding to principal job submission.")
    return spam


def record_run_log(job_id, submitted, spam, depths):
    log_path = os.path.join(HERE, "RUN_LOG.md")
    lines = []
    lines.append("# ARK-445 — RUN LOG\n")
    lines.append("Remnant Fieldworks Inc. — Derek Hone\n")
    lines.append("\nTri-State Authorization Discrimination (ALLOW / HOLD / DENY) "
                 "on ibm_marrakesh (Heron r2).\n")
    lines.append("\n## Principal 9-arm job\n")
    lines.append(f"- **Backend:** {BACKEND_NAME}\n")
    lines.append(f"- **Instance:** {INSTANCE}\n")
    lines.append(f"- **Physical qubits [Q_A, Q_P]:** {INITIAL_LAYOUT}\n")
    lines.append(f"- **Shots per arm:** {SHOTS}\n")
    lines.append(f"- **Arms:** {len(PRINCIPAL_ARMS)} ({', '.join(PRINCIPAL_ARMS)})\n")
    lines.append(f"- **Arm expectations:** {ARM_EXPECT}\n")
    lines.append(f"- **Arm classes:** {ARM_CLASS}\n")
    lines.append(f"- **Optimization level:** {OPT_LEVEL} (seed_transpiler={SEED_TRANSPILER}, "
                 "no dynamical decoupling)\n")
    lines.append(f"- **JOB ID:** `{job_id}`\n")
    lines.append(f"- **Submission timestamp (UTC):** {submitted}\n")
    lines.append(f"- **SPAM job id:** `{spam.get('spam_job_id')}`\n")
    lines.append(f"- **SPAM baselines:** SPAM_A={spam['SPAM_A']:.4f}, "
                 f"SPAM_P={spam['SPAM_P']:.4f}, drift={spam['SPAM_drift']:.4f}\n")
    lines.append(f"- **Transpiled depths:** {depths}\n")
    with open(log_path, "w") as f:
        f.writelines(lines)
    print(f"[SUBMIT] wrote {log_path}")


def main():
    spam = check_spam_gate()

    token = load_token()
    service = QiskitRuntimeService(channel=CHANNEL, token=token, instance=INSTANCE)
    backend = service.backend(BACKEND_NAME)

    arms = build_all_arms()
    ordered = [arms[name] for name in PRINCIPAL_ARMS]
    tqcs = transpile(ordered, backend=backend, optimization_level=OPT_LEVEL,
                     seed_transpiler=SEED_TRANSPILER, initial_layout=INITIAL_LAYOUT)
    depths = {name: tqc.depth() for name, tqc in zip(PRINCIPAL_ARMS, tqcs)}
    print(f"[SUBMIT] transpiled depths: {depths}")

    sampler = SamplerV2(mode=backend)
    submitted = datetime.now(timezone.utc).isoformat()
    print(f"[SUBMIT] submitting {len(tqcs)} arms x {SHOTS} shots to {BACKEND_NAME} ...")
    job = sampler.run(tqcs, shots=SHOTS)
    job_id = job.job_id()
    print(f"[SUBMIT] PRINCIPAL JOB ID = {job_id}")

    # Record job id IMMEDIATELY, before any result retrieval.
    record_run_log(job_id, submitted, spam, depths)

    with open(os.path.join(HERE, "principal_job_id.txt"), "w") as f:
        f.write(job_id + "\n")

    meta = {
        "experiment_id": "ARK-445",
        "principal_job_id": job_id,
        "backend": BACKEND_NAME,
        "instance": INSTANCE,
        "initial_layout": INITIAL_LAYOUT,
        "layout_order": "[Q_A, Q_P]",
        "shots_per_arm": SHOTS,
        "arm_order": PRINCIPAL_ARMS,
        "arm_class": {k: ARM_CLASS[k] for k in PRINCIPAL_ARMS},
        "arm_expect": {k: ARM_EXPECT[k] for k in PRINCIPAL_ARMS},
        "optimization_level": OPT_LEVEL,
        "seed_transpiler": SEED_TRANSPILER,
        "dynamical_decoupling": False,
        "submitted_utc": submitted,
        "spam_job_id": spam.get("spam_job_id"),
    }
    with open(os.path.join(HERE, "principal_job_meta.json"), "w") as f:
        json.dump(meta, f, indent=2)
    print("[SUBMIT] job submitted and recorded. Use ark_445_retrieve.py to fetch results.")


if __name__ == "__main__":
    main()
