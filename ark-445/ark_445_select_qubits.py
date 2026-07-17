"""
ARK-445 — Qubit Selection (execution-time) on ibm_marrakesh
Tri-State Authorization Discrimination (ALLOW / HOLD / DENY)
Remnant Fieldworks Inc. — Derek Hone

Selects 2 physical qubits (Q_A authorizer, Q_P payload) for the tri-state test.

Selection rule (Field 5.2, frozen BEFORE any hardware job):
  1. Readout error (RE) < 0.02 for BOTH qubits.
  2. Q_A and Q_P must be CONNECTED (a native 2-qubit gate exists between them,
     though ARK-445 uses no inter-qubit gate — classical feedforward only).
  3. Minimize the sum: argmin(RE_A + RE_P) across all valid connected pairs.
  4. Selected from LIVE calibration data on execution day (not preregistered).
  5. initial_layout = [Q_A, Q_P] enforced at transpile time.

Outputs (committed BEFORE any job):
  - selected_qubits.json         : Q_A, Q_P, readout errors + selection rationale
  - calibration_snapshot_marrakesh_YYYYMMDD.json : backend calibration snapshot
"""

import json
import os
import sys
from datetime import datetime, timezone

from qiskit_ibm_runtime import QiskitRuntimeService

HERE = os.path.dirname(os.path.abspath(__file__))
SECRETS = "/home/ubuntu/.config/abacusai_auth_secrets.json"

BACKEND_NAME = "ibm_marrakesh"
FALLBACK_BACKEND = "ibm_fez"
CHANNEL = "ibm_quantum_platform"
INSTANCE = "open-instance"
RE_CEILING = 0.02


def load_token():
    with open(SECRETS) as f:
        return json.load(f)["ibm quantum"]["secrets"]["api_token"]["value"]


def get_backend(service):
    try:
        b = service.backend(BACKEND_NAME)
        print(f"[SELECT] backend = {BACKEND_NAME} ({b.num_qubits} qubits)")
        return b
    except Exception as e:
        print(f"[SELECT] {BACKEND_NAME} unavailable ({e}); trying {FALLBACK_BACKEND} ...")
        b = service.backend(FALLBACK_BACKEND)
        print(f"[SELECT] backend = {FALLBACK_BACKEND} ({b.num_qubits} qubits)")
        return b


def select_qubits(backend):
    props = backend.properties()
    readout_errors = {}
    for q in range(backend.num_qubits):
        try:
            readout_errors[q] = props.readout_error(q)
        except Exception:
            readout_errors[q] = 1.0  # unavailable -> disqualified

    coupling_map = backend.coupling_map
    candidates = []
    seen = set()
    for pair in coupling_map:
        q1, q2 = int(pair[0]), int(pair[1])
        key = tuple(sorted((q1, q2)))
        if key in seen:
            continue
        seen.add(key)
        re1 = readout_errors.get(q1, 1.0)
        re2 = readout_errors.get(q2, 1.0)
        if re1 < RE_CEILING and re2 < RE_CEILING:
            # Assign the LOWER-RE qubit as Q_P (payload; the PRIMARY endpoint we read).
            if re1 <= re2:
                qP, reP, qA, reA = q1, re1, q2, re2
            else:
                qP, reP, qA, reA = q2, re2, q1, re1
            candidates.append({
                "Q_A": qA, "Q_P": qP,
                "RE_A": reA, "RE_P": reP,
                "sum_RE": reA + reP,
                "connected": True,
            })

    if not candidates:
        raise ValueError(
            f"No connected qubit pair found with both RE < {RE_CEILING}. "
            "ARK-445 requires 2 connected low-readout-error qubits.")

    best = min(candidates, key=lambda c: c["sum_RE"])
    best["selection_rule"] = (
        f"2 connected qubits, RE(Q_A) < {RE_CEILING}, RE(Q_P) < {RE_CEILING}, "
        "argmin(RE_A + RE_P); lower-RE qubit assigned Q_P (payload/PRIMARY).")
    return best, readout_errors, props


def main():
    token = load_token()
    service = QiskitRuntimeService(channel=CHANNEL, token=token, instance=INSTANCE)
    backend = get_backend(service)
    backend_name = backend.name

    sel, readout_errors, props = select_qubits(backend)
    print("\n[SELECT] Selected qubits:")
    print(f"   Q_A (authorizer): {sel['Q_A']}  RE={sel['RE_A']:.4f}")
    print(f"   Q_P (payload):    {sel['Q_P']}  RE={sel['RE_P']:.4f}")
    print(f"   sum_RE={sel['sum_RE']:.4f}  connected={sel['connected']}")
    print(f"   rule: {sel['selection_rule']}")

    out = {
        "experiment_id": "ARK-445",
        "backend": backend_name,
        "instance": INSTANCE,
        "selection_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "re_ceiling": RE_CEILING,
        "Q_A": sel["Q_A"],
        "Q_P": sel["Q_P"],
        "RE_A": sel["RE_A"],
        "RE_P": sel["RE_P"],
        "sum_RE": sel["sum_RE"],
        "connected": sel["connected"],
        "selection_rule": sel["selection_rule"],
        "initial_layout_order": "[Q_A, Q_P]",
        "num_qubits": 2,
    }
    sel_path = os.path.join(HERE, "selected_qubits.json")
    with open(sel_path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"[SELECT] wrote {sel_path}")

    # Calibration snapshot for the selected qubits (provenance).
    snap = {
        "experiment_id": "ARK-445",
        "backend": backend_name,
        "num_qubits": backend.num_qubits,
        "snapshot_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "re_ceiling": RE_CEILING,
        "selected_pair": [sel["Q_A"], sel["Q_P"]],
        "readout_errors_selected": {
            str(sel["Q_A"]): sel["RE_A"],
            str(sel["Q_P"]): sel["RE_P"],
        },
    }
    try:
        snap["T1_us"] = {
            str(sel["Q_A"]): props.t1(sel["Q_A"]) * 1e6,
            str(sel["Q_P"]): props.t1(sel["Q_P"]) * 1e6,
        }
        snap["T2_us"] = {
            str(sel["Q_A"]): props.t2(sel["Q_A"]) * 1e6,
            str(sel["Q_P"]): props.t2(sel["Q_P"]) * 1e6,
        }
    except Exception as e:
        snap["T1_T2_note"] = f"T1/T2 unavailable: {e}"

    date_tag = datetime.now(timezone.utc).strftime("%Y%m%d")
    snap_path = os.path.join(HERE, f"calibration_snapshot_{backend_name}_{date_tag}.json")
    with open(snap_path, "w") as f:
        json.dump(snap, f, indent=2)
    print(f"[SELECT] wrote {snap_path}")
    print("[SELECT] Qubit selection complete. Commit selected_qubits.json before any job.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
