#!/usr/bin/env python3
"""
ARK-447 Results Retrieval
Retrieves results from the principal job.
"""
import json
import sys
from qiskit_ibm_runtime import QiskitRuntimeService

def load_token():
    """Load IBM Quantum API token."""
    with open('/home/ubuntu/.config/abacusai_auth_secrets.json', 'r') as f:
        secrets = json.load(f)
    return secrets['ibm quantum']['secrets']['api_token']['value']

def main():
    # Load job ID
    try:
        with open('principal_job_id.txt', 'r') as f:
            job_id = f.read().strip()
    except FileNotFoundError:
        print("❌ principal_job_id.txt not found. Run ark_447_submit_ibm.py first.")
        return 1
    
    print(f"Retrieving job {job_id}...")
    
    # Get service
    token = load_token()
    service = QiskitRuntimeService(channel='ibm_quantum_platform', token=token, instance='open-instance')
    
    # Retrieve job
    job = service.job(job_id)
    
    # Check status
    status = job.status()
    print(f"Job status: {status}")
    
    if status.name != 'DONE':
        print(f"❌ Job not complete yet. Current status: {status}")
        return 1
    
    # Get results
    result = job.result()
    
    # Load circuit names
    with open('principal_job_meta.json', 'r') as f:
        meta = json.load(f)
    circuit_names = meta['circuit_names']
    
    # Extract counts for each circuit
    raw_results = {}
    for i, name in enumerate(circuit_names):
        counts = result[i].data.c.get_counts()
        raw_results[name] = counts
    
    # Save raw results
    with open('raw_results.json', 'w') as f:
        json.dump(raw_results, f, indent=2)
    
    print(f"\n✅ Raw results retrieved and saved to raw_results.json")
    print(f"\nCircuit results:")
    for name, counts in raw_results.items():
        print(f"   {name}: {counts}")
    
    print(f"\nRun ark_447_analysis.py to compute verdict.")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
