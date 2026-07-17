#!/bin/bash
LOG="/home/ubuntu/executionproof-testbeds/ark-449/hardware_execution.log"
COMPLETE_FLAG="/home/ubuntu/executionproof-testbeds/ark-449/EXECUTION_COMPLETE"

while ps aux | grep -q "[a]rk_449_circuit.py"; do
    sleep 15
done

# Mark completion
touch "$COMPLETE_FLAG"
echo "ARK-449 execution completed at $(date)" >> "$COMPLETE_FLAG"
echo "Exit code: $?" >> "$COMPLETE_FLAG"
