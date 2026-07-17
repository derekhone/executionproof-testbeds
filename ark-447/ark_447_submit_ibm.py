#!/usr/bin/env python3
"""
ARK-447 Principal Job Submission
Submits the 6 ARK-447 circuits to IBM Quantum.
"""
import json
import sys
from ark_447_circuits import main as create_circuits

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

def main():
    # Check SPAM gate
    try:
        with open('spam_results.json', 'r') as f:
            spam = json.load(f)
        if not spam['gate_passed']:
            print("❌ SPAM gate failed. Cannot proceed with principal job.")
            return 1
    except FileNotFoundError:
        print("❌ spam_results.json not found. Run ark_447_spam_job.py first.")
        return 1
    
    # Load qubits
    qubit_sel = load_qubit_selection()
    backend_name = qubit_sel['backend']
    
    print(f"Creating circuits for {backend_name}...")
    
    # Create circuits
    circuits_dict = create_circuits()
    
    # Convert to list (ordered)
    circuit_names = ['arm1_ALLOW_baseline', 'arm2_DENY_baseline',
                     'arm3_ALLOW_DD', 'arm4_DENY_DD',
                     'arm5_ALLOW_twirl', 'arm6_DENY_twirl']
    circuits = [circuits_dict[name] for name in circuit_names]
    
    # Get backend
    token = load_token()
    service = QiskitRuntimeService(channel='ibm_quantum', token=token)
    backend = service.backend(backend_name)
    
    print(f"\nSubmitting principal job to {backend_name}...")
    print(f"   Circuits: {len(circuits)}")
    print(f"   Shots: 8192 per circuit")
    
    # Submit job
    sampler = Sampler(backend)
    job = sampler.run(circuits, shots=8192)
    
    job_id = job.job_id()
    print(f"\n✅ Principal job submitted: {job_id}")
    
    # Save job metadata
    job_meta = {
        'job_id': job_id,
        'backend': backend_name,
        'num_circuits': len(circuits),
        'circuit_names': circuit_names,
        'shots_per_circuit': 8192,
        'Q_A': qubit_sel['Q_A'],
        'Q_P': qubit_sel['Q_P']
    }
    
    with open('principal_job_id.txt', 'w') as f:
        f.write(job_id)
    
    with open('principal_job_meta.json', 'w') as f:
        json.dump(job_meta, f, indent=2)
    
    print(f"✅ Job ID saved to principal_job_id.txt")
    print(f"✅ Job metadata saved to principal_job_meta.json")
    print(f"\nRun ark_447_retrieve.py after the job completes.")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
