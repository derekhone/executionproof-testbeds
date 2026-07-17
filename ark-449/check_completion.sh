#!/bin/bash
# Check if execution completed and show results
if [ -f EXECUTION_COMPLETE ]; then
    echo "✅ ARK-449 COMPLETED"
    cat EXECUTION_COMPLETE
    echo ""
    echo "=== RESULTS ==="
    ls -1 results/
    if [ -f results/proofrecord.json ]; then
        echo ""
        echo "=== VERDICT ==="
        python3 -c "import json; pr=json.load(open('results/proofrecord.json')); print(f\"Verdict: {pr.get('verdict')}\"); print(f\"SPAM gate: {pr.get('spam_gate',{}).get('gate_passed')}\"); print(f\"S_A_min: {pr.get('primary_metrics',{}).get('S_A_min')}\"); print(f\"L_D_max: {pr.get('primary_metrics',{}).get('L_D_max')}\"); print(f\"Delta_B: {pr.get('primary_metrics',{}).get('Delta_B')}\")"
    fi
elif ps aux | grep -q "[a]rk_449_circuit.py"; then
    echo "⏳ Still running..."
    echo "Job status:"
    python3 -c "from qiskit_ibm_runtime import QiskitRuntimeService; s=QiskitRuntimeService(); j=s.job('d9crr82neu4c739mcsd0'); print(f'  Status: {j.status()}')" 2>/dev/null || echo "  (query failed)"
    tail -3 hardware_execution.log
else
    echo "❓ Process stopped but no completion flag. Checking log..."
    tail -20 hardware_execution.log
fi
