#!/usr/bin/env python3
"""
ARK-448 SPAM Baseline Job
Submits SPAM characterization circuits as a gating condition.
SPAM_P is a GATING diagnostic ONLY (|+> -> ~0.5 expected); it is NEVER
subtracted from DENY leakage (per ARK-447 v1.1 correction).
"""
import json
import sys
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler

SPAM_SHOTS = 2048  # lean SPAM to conserve open-plan budget

def load_token():
    with open('/home/ubuntu/.config/abacusai_auth_secrets.json', 'r') as f:
        secrets = json.load(f)
    return secrets['ibm quantum']['secrets']['api_token']['value']

def load_qubit_selection():
    with open('selected_qubits.json', 'r') as f:
        return json.load(f)

def create_spam_circuits(Q_A, Q_P):
    """SPAM_A: |1> on Q_A measured in Z. SPAM_P: |+> on Q_P measured in Z."""
    qr_a = QuantumRegister(Q_A + 1, 'q')
    cr_a = ClassicalRegister(1, 'c')
    spam_a = QuantumCircuit(qr_a, cr_a)
    spam_a.x(qr_a[Q_A])
    spam_a.measure(qr_a[Q_A], cr_a[0])

    max_q = max(Q_A, Q_P)
    qr_p = QuantumRegister(max_q + 1, 'q')
    cr_p = ClassicalRegister(1, 'c')
    spam_p = QuantumCircuit(qr_p, cr_p)
    spam_p.h(qr_p[Q_P])
    spam_p.measure(qr_p[Q_P], cr_p[0])

    return {'SPAM_A': spam_a, 'SPAM_P': spam_p}

def main():
    qubit_sel = load_qubit_selection()
    Q_A = qubit_sel['Q_A']
    Q_P = qubit_sel['Q_P']
    backend_name = qubit_sel['backend']

    print(f"Creating SPAM circuits for Q_A={Q_A}, Q_P={Q_P} on {backend_name}...")
    spam_circuits = create_spam_circuits(Q_A, Q_P)

    token = load_token()
    service = QiskitRuntimeService(channel='ibm_quantum_platform', token=token, instance='open-instance')
    backend = service.backend(backend_name)

    print("\nTranspiling SPAM circuits...")
    pm = generate_preset_pass_manager(backend=backend, optimization_level=1)
    spam_a_t = pm.run(spam_circuits['SPAM_A'])
    spam_p_t = pm.run(spam_circuits['SPAM_P'])

    print(f"Submitting SPAM job to {backend_name} ({SPAM_SHOTS} shots)...")
    sampler = Sampler(backend)
    job = sampler.run([spam_a_t, spam_p_t], shots=SPAM_SHOTS)
    job_id = job.job_id()
    print(f"SPAM job submitted: {job_id}\n   Waiting for completion...")

    result = job.result()
    spam_a_counts = result[0].data.c.get_counts()
    spam_p_counts = result[1].data.c.get_counts()

    spam_a_error = spam_a_counts.get('0', 0) / SPAM_SHOTS
    spam_p_1_prob = spam_p_counts.get('1', 0) / SPAM_SHOTS

    print("\n=== SPAM Results ===")
    print(f"SPAM_A: {spam_a_counts}  error(|1>->'0'): {spam_a_error:.4f}")
    print(f"SPAM_P: {spam_p_counts}  P('1'||+>): {spam_p_1_prob:.4f}")

    gate_passed = (spam_a_error <= 0.02 and abs(spam_p_1_prob - 0.5) <= 0.02)

    print("\n=== SPAM Gate ===")
    print(f"SPAM_A <= 0.02: {spam_a_error <= 0.02} ({spam_a_error:.4f})")
    print(f"SPAM_P dev <= 0.02: {abs(spam_p_1_prob - 0.5) <= 0.02} ({abs(spam_p_1_prob - 0.5):.4f})")
    print(f"Gate PASSED: {gate_passed}")

    spam_results = {
        'job_id': job_id,
        'backend': backend_name,
        'Q_A': Q_A,
        'Q_P': Q_P,
        'shots': SPAM_SHOTS,
        'SPAM_A': {'counts': spam_a_counts, 'error': spam_a_error},
        'SPAM_P': {'counts': spam_p_counts, 'prob_1': spam_p_1_prob,
                   'deviation_from_0.5': abs(spam_p_1_prob - 0.5),
                   'role': 'gating diagnostic only; NOT subtracted from DENY leakage'},
        'gate_passed': gate_passed
    }
    with open('spam_results.json', 'w') as f:
        json.dump(spam_results, f, indent=2)
    print("\nSPAM results saved to spam_results.json")

    if not gate_passed:
        print("\nSPAM gate FAILED. Do not proceed with principal job.")
        return 1
    print("\nSPAM gate PASSED. Proceed with principal job.")
    return 0

if __name__ == '__main__':
    sys.exit(main())
