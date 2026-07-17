#!/bin/bash
# ARK-450: Compute SHA-256 hashes of locked files for MANIFEST

echo "Computing SHA-256 hashes for ARK-450 locked files..."
echo ""

files=(
    "PREREGISTRATION.md"
    "schemas/substitution_scenario_schema.json"
    "generator/scenario_generator.py"
    "verifiers/v1_guard.js"
    "verifiers/v2_guard.py"
    "run_killgate.py"
    "run_arms.py"
)

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        hash=$(sha256sum "$file" | awk '{print $1}')
        echo "$file: $hash"
    else
        echo "$file: FILE NOT FOUND"
    fi
done
