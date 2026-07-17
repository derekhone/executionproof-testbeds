#!/usr/bin/env python3
"""
ARK-448 Circuit Generation — Dynamical Decoupling vs. Baseline under an idle window.

Four arms (single principal job):
  arm1_ALLOW_baseline : ALLOW (|1>), bare idle delay tau, no DD
  arm2_DENY_baseline  : DENY  (|0>), bare idle delay tau, no DD
  arm3_ALLOW_dd       : ALLOW (|1>), idle tau filled with XX DD sequence
  arm4_DENY_dd        : DENY  (|0>), idle tau filled with XX DD sequence

Idle window tau = 20 us on BOTH qubits, inserted after state prep and before
the boundary CNOT. DD baked into the circuit (delay + X pulses), so DD-on vs
DD-off is compared within a single job with no cross-job confound.
XX sequence: delay(tau/4) - X - delay(tau/2) - X - delay(tau/4).
"""
import json
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister

TAU_US = 20.0            # total idle window (microseconds)
DD_QUARTER = TAU_US / 4  # 5 us
DD_HALF = TAU_US / 2     # 10 us

def load_qubit_selection():
    with open('selected_qubits.json', 'r') as f:
        return json.load(f)

def _prep(qc, qr, auth_state, Q_A, Q_P):
    """Prepare authorizer and payload states."""
    if auth_state == 'ALLOW':
        qc.x(qr[Q_A])   # |1>
    # DENY = |0> (default)
    qc.h(qr[Q_P])       # payload |+>

def create_baseline_circuit(auth_state, Q_A, Q_P):
    """Bare idle delay tau on both qubits (no DD), then boundary CNOT."""
    qr = QuantumRegister(max(Q_A, Q_P) + 1, 'q')
    cr = ClassicalRegister(2, 'c')
    qc = QuantumCircuit(qr, cr)
    _prep(qc, qr, auth_state, Q_A, Q_P)
    qc.barrier()
    qc.delay(TAU_US, qr[Q_A], unit='us')
    qc.delay(TAU_US, qr[Q_P], unit='us')
    qc.barrier()
    qc.cx(qr[Q_A], qr[Q_P])
    qc.barrier()
    qc.measure(qr[Q_A], cr[0])
    qc.measure(qr[Q_P], cr[1])
    return qc

def create_dd_circuit(auth_state, Q_A, Q_P):
    """Idle tau filled with an XX dynamical-decoupling sequence on both qubits."""
    qr = QuantumRegister(max(Q_A, Q_P) + 1, 'q')
    cr = ClassicalRegister(2, 'c')
    qc = QuantumCircuit(qr, cr)
    _prep(qc, qr, auth_state, Q_A, Q_P)
    qc.barrier()
    # XX DD: d/4 - X - d/2 - X - d/4  (net idle = tau, two X pulses, logical identity)
    for q in (Q_A, Q_P):
        qc.delay(DD_QUARTER, qr[q], unit='us')
    for q in (Q_A, Q_P):
        qc.x(qr[q])
    for q in (Q_A, Q_P):
        qc.delay(DD_HALF, qr[q], unit='us')
    for q in (Q_A, Q_P):
        qc.x(qr[q])
    for q in (Q_A, Q_P):
        qc.delay(DD_QUARTER, qr[q], unit='us')
    qc.barrier()
    qc.cx(qr[Q_A], qr[Q_P])
    qc.barrier()
    qc.measure(qr[Q_A], cr[0])
    qc.measure(qr[Q_P], cr[1])
    return qc

def main():
    qubit_sel = load_qubit_selection()
    Q_A = qubit_sel['Q_A']
    Q_P = qubit_sel['Q_P']
    backend_name = qubit_sel['backend']

    print(f"Creating ARK-448 circuits for Q_A={Q_A}, Q_P={Q_P} on {backend_name}...")
    print(f"Idle window tau = {TAU_US} us; DD sequence = XX\n")

    circuits = {}
    circuits['arm1_ALLOW_baseline'] = create_baseline_circuit('ALLOW', Q_A, Q_P)
    circuits['arm2_DENY_baseline'] = create_baseline_circuit('DENY', Q_A, Q_P)
    circuits['arm3_ALLOW_dd'] = create_dd_circuit('ALLOW', Q_A, Q_P)
    circuits['arm4_DENY_dd'] = create_dd_circuit('DENY', Q_A, Q_P)

    print(f"Created {len(circuits)} circuits:")
    for name in circuits:
        print(f"   - {name}")

    metadata = {
        'Q_A': Q_A, 'Q_P': Q_P, 'backend': backend_name,
        'num_circuits': len(circuits),
        'circuit_names': list(circuits.keys()),
        'tau_us': TAU_US,
        'dd_sequence': 'XX (delay/4 - X - delay/2 - X - delay/4)',
        'note': 'Dynamical Decoupling vs. baseline under a 20us idle window; DD baked into circuits.'
    }
    with open('circuit_metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)
    print("\nCircuit metadata saved to circuit_metadata.json")
    return circuits

if __name__ == '__main__':
    circuits = main()
    print("\nARK-448 circuits ready for submission.")
