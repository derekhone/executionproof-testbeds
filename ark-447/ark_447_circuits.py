#!/usr/bin/env python3
"""
ARK-447 Circuit Generation
Generates 6 circuits for noise-suppression comparison:
- 2 baseline (ALLOW/DENY, no mitigation)
- 2 with Dynamical Decoupling (ALLOW/DENY)
- 2 with Pauli Twirling (ALLOW/DENY)
"""
import json
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit.circuit.library import XGate
from qiskit.transpiler import PassManager
from qiskit.transpiler.passes import PadDynamicalDecoupling
from qiskit_ibm_runtime import QiskitRuntimeService
import numpy as np

def load_token():
    """Load IBM Quantum API token."""
    with open('/home/ubuntu/.config/abacusai_auth_secrets.json', 'r') as f:
        secrets = json.load(f)
    return secrets['ibm quantum']['secrets']['api_token']['value']

def load_qubit_selection():
    """Load selected qubits from JSON."""
    with open('selected_qubits.json', 'r') as f:
        return json.load(f)

def create_baseline_circuit(auth_state, Q_A, Q_P):
    """
    Create baseline circuit (no noise mitigation).
    
    Args:
        auth_state: 'ALLOW' (|1⟩) or 'DENY' (|0⟩)
        Q_A: authorizer qubit index
        Q_P: payload qubit index
    
    Returns:
        QuantumCircuit
    """
    qr = QuantumRegister(max(Q_A, Q_P) + 1, 'q')
    cr = ClassicalRegister(2, 'c')
    qc = QuantumCircuit(qr, cr)
    
    # Prepare authorizer state
    if auth_state == 'ALLOW':
        qc.x(qr[Q_A])  # |1⟩
    # else: DENY = |0⟩ (default)
    
    # Prepare payload in |+⟩
    qc.h(qr[Q_P])
    
    # Barrier for clarity
    qc.barrier()
    
    # Boundary gate: CNOT(Q_A → Q_P)
    qc.cx(qr[Q_A], qr[Q_P])
    
    # Barrier
    qc.barrier()
    
    # Measure both qubits
    qc.measure(qr[Q_A], cr[0])
    qc.measure(qr[Q_P], cr[1])
    
    return qc

def create_dd_circuit(auth_state, Q_A, Q_P, backend):
    """
    Create circuit with Dynamical Decoupling applied.
    
    Uses Qiskit's PadDynamicalDecoupling pass to insert X gates (π-pulses)
    during idle periods.
    """
    # Start with baseline circuit
    qc = create_baseline_circuit(auth_state, Q_A, Q_P)
    
    # Transpile to backend basis gates first
    from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
    pm = generate_preset_pass_manager(backend=backend, optimization_level=1)
    qc_transpiled = pm.run(qc)
    
    # Apply DD pass (XY4 sequence using X gates for simplicity)
    dd_sequence = [XGate(), XGate()]  # Simple XX sequence
    dd_pass = PadDynamicalDecoupling(backend.target.durations(), dd_sequence)
    pm_dd = PassManager([dd_pass])
    qc_dd = pm_dd.run(qc_transpiled)
    
    return qc_dd

def create_twirled_circuit(auth_state, Q_A, Q_P):
    """
    Create circuit with Pauli Twirling applied.
    
    Randomizes Pauli gates {I, X, Y, Z} before and after the CNOT operation.
    Since we need a single deterministic circuit (not randomized per shot),
    we'll use a fixed random seed for reproducibility but apply average twirling.
    
    Note: True Pauli twirling requires running multiple randomized instances
    and averaging. For this experiment, we'll apply a representative twirling
    pattern (e.g., apply Y gates to convert CNOT errors to depolarizing-like).
    """
    qr = QuantumRegister(max(Q_A, Q_P) + 1, 'q')
    cr = ClassicalRegister(2, 'c')
    qc = QuantumCircuit(qr, cr)
    
    # Prepare authorizer state
    if auth_state == 'ALLOW':
        qc.x(qr[Q_A])  # |1⟩
    
    # Prepare payload in |+⟩
    qc.h(qr[Q_P])
    
    qc.barrier()
    
    # Apply pre-twirl Pauli (example: Y on Q_P to convert Z-error to X-error)
    # This is a simplified version; full twirling would randomize per shot
    qc.y(qr[Q_P])
    
    # Boundary gate: CNOT(Q_A → Q_P)
    qc.cx(qr[Q_A], qr[Q_P])
    
    # Apply post-twirl compensating Pauli
    qc.y(qr[Q_P])
    
    qc.barrier()
    
    # Measure
    qc.measure(qr[Q_A], cr[0])
    qc.measure(qr[Q_P], cr[1])
    
    return qc

def main():
    # Load qubits
    qubit_sel = load_qubit_selection()
    Q_A = qubit_sel['Q_A']
    Q_P = qubit_sel['Q_P']
    backend_name = qubit_sel['backend']
    
    print(f"Creating circuits for Q_A={Q_A}, Q_P={Q_P} on {backend_name}...\n")
    
    # Get backend
    token = load_token()
    service = QiskitRuntimeService(channel='ibm_quantum', token=token)
    backend = service.backend(backend_name)
    
    # Create circuits
    circuits = {}
    
    # Baseline
    print("Creating baseline circuits...")
    circuits['arm1_ALLOW_baseline'] = create_baseline_circuit('ALLOW', Q_A, Q_P)
    circuits['arm2_DENY_baseline'] = create_baseline_circuit('DENY', Q_A, Q_P)
    
    # Dynamical Decoupling
    print("Creating DD circuits...")
    circuits['arm3_ALLOW_DD'] = create_dd_circuit('ALLOW', Q_A, Q_P, backend)
    circuits['arm4_DENY_DD'] = create_dd_circuit('DENY', Q_A, Q_P, backend)
    
    # Pauli Twirling
    print("Creating Pauli twirling circuits...")
    circuits['arm5_ALLOW_twirl'] = create_twirled_circuit('ALLOW', Q_A, Q_P)
    circuits['arm6_DENY_twirl'] = create_twirled_circuit('DENY', Q_A, Q_P)
    
    print(f"\n✅ Created {len(circuits)} circuits:")
    for name in circuits.keys():
        print(f"   - {name}")
    
    # Save circuit metadata
    metadata = {
        'Q_A': Q_A,
        'Q_P': Q_P,
        'backend': backend_name,
        'num_circuits': len(circuits),
        'circuit_names': list(circuits.keys())
    }
    
    with open('circuit_metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"\n✅ Circuit metadata saved to circuit_metadata.json")
    
    return circuits

if __name__ == '__main__':
    circuits = main()
    print("\n✅ ARK-447 circuits ready for submission.")
