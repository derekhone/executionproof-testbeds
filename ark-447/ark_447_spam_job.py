#!/usr/bin/env python3
"""
ARK-447 SPAM Baseline Job
Submits SPAM characterization circuits as a gating condition.
"""
import json
import sys
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler

def load_token():
    """Load IBM Quantum API token."""
    with open('/home/ubuntu/.config/abacusai_auth_secrets.json', 'r') as f:
        secrets = json.load(f)
    return secrets['ibm quantum']['secrets']['api_token']['value']

def load_qubit_selection():
    """Load selected qubits."""
    with open('selected_qubits.json', 'r') as f:
        return json.load(f)

def create_spam_circuits(Q_A, Q_P):
    """
    Create SPAM baseline circuits.
    
    SPAM_A: Prepare |1⟩ on Q_A, measure in Z
    SPAM_P: Prepare |+⟩ on Q_P, measure in Z
    """
    # SPAM_A
    qr_a = QuantumRegister(Q_A + 1, 'q')
    cr_a = ClassicalRegister(1, 'c')
    spam_a = QuantumCircuit(qr_a, cr_a)
    spam_a.x(qr_a[Q_A])  # Prepare |1⟩
    spam_a.measure(qr_a[Q_A], cr_a[0])
    
    # SPAM_P
    max_q = max(Q_A, Q_P)
    qr_p = QuantumRegister(max_q + 1, 'q')
    cr_p = ClassicalRegister(1, 'c')
    spam_p = QuantumCircuit(qr_p, cr_p)
    spam_p.h(qr_p[Q_P])  # Prepare |+⟩
    spam_p.measure(qr_p[Q_P], cr_p[0])
    
    return {'SPAM_A': spam_a, 'SPAM_P': spam_p}

def main():
    # Load qubits
    qubit_sel = load_qubit_selection()
    Q_A = qubit_sel['Q_A']
    Q_P = qubit_sel['Q_P']
    backend_name = qubit_sel['backend']
    
    print(f"Creating SPAM circuits for Q_A={Q_A}, Q_P={Q_P} on {backend_name}...")
    
    # Create SPAM circuits
    spam_circuits = create_spam_circuits(Q_A, Q_P)
    
    # Get backend
    token = load_token()
    service = QiskitRuntimeService(channel='ibm_quantum_platform', token=token, instance='open-instance')
    backend = service.backend(backend_name)
    
    print(f"\nTranspiling SPAM circuits...")
    pm = generate_preset_pass_manager(backend=backend, optimization_level=1)
    spam_a_transpiled = pm.run(spam_circuits['SPAM_A'])
    spam_p_transpiled = pm.run(spam_circuits['SPAM_P'])
    
    print(f"Submitting SPAM job to {backend_name}...")
    
    # Submit job
    sampler = Sampler(backend)
    job = sampler.run([spam_a_transpiled, spam_p_transpiled], shots=8192)
    
    job_id = job.job_id()
    print(f"✅ SPAM job submitted: {job_id}")
    print(f"   Waiting for completion...")
    
    # Wait for completion
    result = job.result()
    
    # Extract counts
    spam_a_counts = result[0].data.c.get_counts()
    spam_p_counts = result[1].data.c.get_counts()
    
    # Calculate SPAM errors
    # SPAM_A: prepared |1⟩, expect outcome '1'
    spam_a_error = spam_a_counts.get('0', 0) / 8192
    
    # SPAM_P: prepared |+⟩, expect 50/50 split
    spam_p_1_prob = spam_p_counts.get('1', 0) / 8192
    
    print(f"\n=== SPAM Results ===")
    print(f"SPAM_A: {spam_a_counts}")
    print(f"   Error (prob of '0' when prepared |1⟩): {spam_a_error:.4f}")
    print(f"SPAM_P: {spam_p_counts}")
    print(f"   Prob('1' | |+⟩): {spam_p_1_prob:.4f}")
    
    # Gate condition: both SPAM errors ≤ 0.02
    gate_passed = (spam_a_error <= 0.02 and abs(spam_p_1_prob - 0.5) <= 0.02)
    
    print(f"\n=== SPAM Gate ===")
    print(f"SPAM_A ≤ 0.02: {spam_a_error <= 0.02} ({spam_a_error:.4f})")
    print(f"SPAM_P deviation ≤ 0.02: {abs(spam_p_1_prob - 0.5) <= 0.02} ({abs(spam_p_1_prob - 0.5):.4f})")
    print(f"Gate PASSED: {gate_passed}")
    
    # Save results
    spam_results = {
        'job_id': job_id,
        'backend': backend_name,
        'Q_A': Q_A,
        'Q_P': Q_P,
        'shots': 8192,
        'SPAM_A': {
            'counts': spam_a_counts,
            'error': spam_a_error
        },
        'SPAM_P': {
            'counts': spam_p_counts,
            'prob_1': spam_p_1_prob,
            'deviation_from_0.5': abs(spam_p_1_prob - 0.5)
        },
        'gate_passed': gate_passed
    }
    
    with open('spam_results.json', 'w') as f:
        json.dump(spam_results, f, indent=2)
    
    print(f"\n✅ SPAM results saved to spam_results.json")
    
    if not gate_passed:
        print(f"\n❌ SPAM gate FAILED. Do not proceed with principal job.")
        return 1
    else:
        print(f"\n✅ SPAM gate PASSED. Proceed with principal job.")
        return 0

if __name__ == '__main__':
    sys.exit(main())
