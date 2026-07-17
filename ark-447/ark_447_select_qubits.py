#!/usr/bin/env python3
"""
ARK-447 Qubit Selection
Selects Q_A (authorizer) and Q_P (payload) from ibm_marrakesh or ibm_fez
based on lowest readout error sum, requiring connectivity.
"""
import json
import sys
from qiskit_ibm_runtime import QiskitRuntimeService

def load_token():
    """Load IBM Quantum API token from auth secrets."""
    with open('/home/ubuntu/.config/abacusai_auth_secrets.json', 'r') as f:
        secrets = json.load(f)
    return secrets['ibm quantum']['secrets']['api_token']['value']

def select_qubits(backend_name):
    """
    Select Q_A and Q_P from the specified backend.
    
    Returns:
        dict: {
            'backend': str,
            'Q_A': int,
            'Q_P': int,
            'Q_A_readout_error': float,
            'Q_P_readout_error': float,
            'sum_readout_error': float,
            'connected': bool
        }
    """
    token = load_token()
    service = QiskitRuntimeService(channel='ibm_quantum', token=token)
    backend = service.backend(backend_name)
    
    # Get backend properties
    props = backend.properties()
    config = backend.configuration()
    
    # Extract readout errors
    readout_errors = {}
    for i in range(config.n_qubits):
        re = props.readout_error(i)
        readout_errors[i] = re
    
    # Get coupling map
    coupling_map = config.coupling_map
    
    # Find all connected pairs and their sum readout error
    pairs = []
    for (q0, q1) in coupling_map:
        sum_re = readout_errors[q0] + readout_errors[q1]
        pairs.append({
            'Q_A': q0,
            'Q_P': q1,
            'Q_A_RE': readout_errors[q0],
            'Q_P_RE': readout_errors[q1],
            'sum_RE': sum_re
        })
    
    # Sort by sum readout error (ascending)
    pairs.sort(key=lambda x: x['sum_RE'])
    
    # Select the best pair
    best = pairs[0]
    
    result = {
        'backend': backend_name,
        'Q_A': best['Q_A'],
        'Q_P': best['Q_P'],
        'Q_A_readout_error': best['Q_A_RE'],
        'Q_P_readout_error': best['Q_P_RE'],
        'sum_readout_error': best['sum_RE'],
        'connected': True
    }
    
    return result, props

def main():
    # Try ibm_marrakesh first, fallback to ibm_fez
    backends_to_try = ['ibm_marrakesh', 'ibm_fez']
    
    for backend_name in backends_to_try:
        try:
            print(f"Attempting to select qubits from {backend_name}...")
            result, props = select_qubits(backend_name)
            
            # Save result
            with open('selected_qubits.json', 'w') as f:
                json.dump(result, f, indent=2)
            
            # Save calibration snapshot
            calib_snapshot = {
                'backend': backend_name,
                'date': props.last_update_date.isoformat() if props.last_update_date else None,
                'n_qubits': len(props.qubits),
                'readout_errors': {i: props.readout_error(i) for i in range(len(props.qubits))}
            }
            
            snapshot_filename = f'calibration_snapshot_{backend_name}_{calib_snapshot["date"][:10].replace("-", "")}.json'
            with open(snapshot_filename, 'w') as f:
                json.dump(calib_snapshot, f, indent=2)
            
            print(f"\n✅ Selected qubits from {backend_name}:")
            print(f"   Q_A = {result['Q_A']} (RE = {result['Q_A_readout_error']:.4f})")
            print(f"   Q_P = {result['Q_P']} (RE = {result['Q_P_readout_error']:.4f})")
            print(f"   Sum RE = {result['sum_readout_error']:.4f}")
            print(f"   Connected: {result['connected']}")
            print(f"\n✅ Saved to selected_qubits.json")
            print(f"✅ Calibration snapshot saved to {snapshot_filename}")
            
            return 0
            
        except Exception as e:
            print(f"❌ Failed to select qubits from {backend_name}: {e}")
            if backend_name == backends_to_try[-1]:
                print(f"\n❌ All backends failed. Exiting.")
                return 1
            else:
                print(f"Trying next backend...\n")
    
    return 1

if __name__ == '__main__':
    sys.exit(main())
