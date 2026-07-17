#!/usr/bin/env python3
"""
ARK-448 Principal Job Submission — DD vs. baseline (4 circuits, single job).
Requires a passing SPAM gate. Shots default 8192; pass --shots to override
(e.g. 4096 if the post-SPAM budget check requires it).
"""
import json
import sys
from ark_448_circuits import main as create_circuits
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler

def load_token():
    with open('/home/ubuntu/.config/abacusai_auth_secrets.json', 'r') as f:
        secrets = json.load(f)
    return secrets['ibm quantum']['secrets']['api_token']['value']

def load_qubit_selection():
    with open('selected_qubits.json', 'r') as f:
        return json.load(f)

def main():
    shots = 8192
    if '--shots' in sys.argv:
        shots = int(sys.argv[sys.argv.index('--shots') + 1])

    try:
        with open('spam_results.json', 'r') as f:
            spam = json.load(f)
        if not spam['gate_passed']:
            print("SPAM gate failed. Cannot proceed with principal job.")
            return 1
    except FileNotFoundError:
        print("spam_results.json not found. Run ark_448_spam_job.py first.")
        return 1

    qubit_sel = load_qubit_selection()
    backend_name = qubit_sel['backend']

    print(f"Creating circuits for {backend_name}...")
    circuits_dict = create_circuits()
    circuit_names = ['arm1_ALLOW_baseline', 'arm2_DENY_baseline',
                     'arm3_ALLOW_dd', 'arm4_DENY_dd']
    circuits = [circuits_dict[name] for name in circuit_names]

    token = load_token()
    service = QiskitRuntimeService(channel='ibm_quantum_platform', token=token, instance='open-instance')
    backend = service.backend(backend_name)

    print(f"\nTranspiling circuits to {backend_name} (delays preserved)...")
    pm = generate_preset_pass_manager(backend=backend, optimization_level=1)
    circuits_t = [pm.run(qc) for qc in circuits]

    print(f"\nSubmitting principal job to {backend_name}...")
    print(f"   Circuits: {len(circuits_t)}   Shots: {shots} per circuit")
    sampler = Sampler(backend)
    job = sampler.run(circuits_t, shots=shots)
    job_id = job.job_id()
    print(f"\nPrincipal job submitted: {job_id}")

    job_meta = {
        'job_id': job_id,
        'backend': backend_name,
        'num_circuits': len(circuits),
        'circuit_names': circuit_names,
        'shots_per_circuit': shots,
        'Q_A': qubit_sel['Q_A'],
        'Q_P': qubit_sel['Q_P'],
        'tau_us': 20.0,
        'dd_sequence': 'XX',
        'note': 'DD vs. baseline under 20us idle window'
    }
    with open('principal_job_id.txt', 'w') as f:
        f.write(job_id)
    with open('principal_job_meta.json', 'w') as f:
        json.dump(job_meta, f, indent=2)

    print("Job ID saved to principal_job_id.txt")
    print("Job metadata saved to principal_job_meta.json")
    print("\nRun ark_448_retrieve.py after the job completes.")
    return 0

if __name__ == '__main__':
    sys.exit(main())
