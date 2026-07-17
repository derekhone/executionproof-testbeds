"""
ARK-445 — In-situ SPAM kill-gate job (RUNS FIRST) on ibm_marrakesh
Tri-State Authorization Discrimination (ALLOW / HOLD / DENY)
Remnant Fieldworks Inc. — Derek Hone

Directly characterizes idle SPAM readout error on the ARK-445 rule-selected physical
qubits Q_A and Q_P of ibm_marrakesh, BEFORE the principal 9-arm job (Field 13 step 2).

This is arm10 (spam_idle): both qubits prepared |0>, idle, then measured.
    SPAM_A = P(Q_A read 1 | prepared 0)   (register ca)
    SPAM_P = P(Q_P read 1 | prepared 0)   (register cp)   -> used to correct DENY arms
    SPAM_drift = |SPAM_A - SPAM_P|

Kill gate (preregistered, Field 7): SPAM_A <= 0.02 AND SPAM_P <= 0.02. If violated on
EITHER qubit => KILL: do NOT submit the principal job; classify INDETERMINATE.

Output: spam_results.json (raw counts + derived per-qubit SPAM metrics).
"""

import json
import os
import sys
from datetime import datetime, timezone

from qiskit import transpile
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2

from ark_445_circuits import arm10_spam_idle, INITIAL_LAYOUT

HERE = os.path.dirname(os.path.abspath(__file__))
SECRETS = "/home/ubuntu/.config/abacusai_auth_secrets.json"

BACKEND_NAME = "ibm_marrakesh"
CHANNEL = "ibm_quantum_platform"
INSTANCE = "open-instance"
SHOTS = 8192
OPT_LEVEL = 1
SPAM_CEILING = 0.02
DRIFT_CEILING = 0.005


def load_token():
    with open(SECRETS) as f:
        return json.load(f)["ibm quantum"]["secrets"]["api_token"]["value"]


def load_selection():
    with open(os.path.join(HERE, "selected_qubits.json")) as f:
        return json.load(f)


def main():
    sel = load_selection()
    physical = {"Q_A": sel["Q_A"], "Q_P": sel["Q_P"]}

    token = load_token()
    service = QiskitRuntimeService(channel=CHANNEL, token=token, instance=INSTANCE)
    backend = service.backend(BACKEND_NAME)

    qc = arm10_spam_idle()
    tqc = transpile(qc, backend=backend, optimization_level=OPT_LEVEL,
                    initial_layout=INITIAL_LAYOUT)

    sampler = SamplerV2(mode=backend)
    submitted = datetime.now(timezone.utc).isoformat()
    print(f"[SPAM] submitting arm10_spam_idle x {SHOTS} shots to {BACKEND_NAME} "
          f"(qubits={physical}) ...")
    job = sampler.run([tqc], shots=SHOTS)
    job_id = job.job_id()
    print(f"[SPAM] job_id = {job_id}")
    result = job.result()
    completed = datetime.now(timezone.utc).isoformat()

    ca_counts = result[0].data.ca.get_counts()   # Q_A idle readout
    cp_counts = result[0].data.cp.get_counts()    # Q_P idle readout
    total_a = sum(ca_counts.values())
    total_p = sum(cp_counts.values())
    spam_a = ca_counts.get("1", 0) / total_a
    spam_p = cp_counts.get("1", 0) / total_p
    drift = abs(spam_a - spam_p)

    qubit_metrics = {
        "Q_A": {"physical": physical["Q_A"], "spam_baseline": spam_a,
                "passes_ceiling": bool(spam_a <= SPAM_CEILING),
                "counts": ca_counts, "total": total_a},
        "Q_P": {"physical": physical["Q_P"], "spam_baseline": spam_p,
                "passes_ceiling": bool(spam_p <= SPAM_CEILING),
                "counts": cp_counts, "total": total_p},
    }
    spam_ok = qubit_metrics["Q_A"]["passes_ceiling"] and qubit_metrics["Q_P"]["passes_ceiling"]
    drift_ok = drift <= DRIFT_CEILING

    out = {
        "experiment_id": "ARK-445",
        "job_type": "in_situ_spam_killgate_arm10",
        "backend": BACKEND_NAME,
        "instance": INSTANCE,
        "physical_qubits": physical,
        "shots": SHOTS,
        "spam_ceiling": SPAM_CEILING,
        "drift_ceiling": DRIFT_CEILING,
        "spam_job_id": job_id,
        "submitted_utc": submitted,
        "completed_utc": completed,
        "SPAM_A": spam_a,
        "SPAM_P": spam_p,
        "SPAM_drift": drift,
        "qubit_metrics": qubit_metrics,
        "spam_gate_passed": bool(spam_ok),
        "drift_ok": bool(drift_ok),
        "kill_condition": "SPAM_A > 0.02 OR SPAM_P > 0.02 => KILL (INDETERMINATE); "
                          "principal job MUST NOT be submitted.",
    }
    out_path = os.path.join(HERE, "spam_results.json")
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"[SPAM] wrote {out_path}")
    print(f"[SPAM] SPAM_A={spam_a:.4f} (pass={qubit_metrics['Q_A']['passes_ceiling']})")
    print(f"[SPAM] SPAM_P={spam_p:.4f} (pass={qubit_metrics['Q_P']['passes_ceiling']})")
    print(f"[SPAM] SPAM_drift={drift:.4f} (drift_ok={drift_ok})")
    print(f"[SPAM] gate_passed={spam_ok}")

    if not spam_ok:
        print("[SPAM] KILL: SPAM baseline exceeds 0.02 on at least one qubit. "
              "Principal job MUST NOT be submitted. Result is INDETERMINATE/KILLED.")
        sys.exit(2)
    print("[SPAM] PASS: baselines within ceiling. Principal job may proceed.")


if __name__ == "__main__":
    main()
