#!/bin/bash
# Compute SHA-256 hashes of locked files for MANIFEST verification
cd "$(dirname "$0")"
echo "SHA-256 hashes (ARK-458 locked files):"
for f in PREREGISTRATION.md schemas/iam_action_scenario_schema.json \
         verifiers/v1_guard.js verifiers/v2_guard.py \
         generator/scenario_generator.py run_killgate.py run_arms.py; do
  printf "  %-48s %s\n" "$f:" "$(sha256sum "$f" | cut -d' ' -f1)"
done
