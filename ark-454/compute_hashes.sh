#!/usr/bin/env bash
# ARK-454 — compute SHA-256 hashes of all locked files for MANIFEST.txt.
# Usage: bash compute_hashes.sh
set -euo pipefail
cd "$(dirname "$0")"

FILES=(
  "PREREGISTRATION.md"
  "schemas/decision_scenario_schema.json"
  "verifiers/v1_guard.js"
  "verifiers/v2_guard.py"
  "generator/scenario_generator.py"
  "run_killgate.py"
  "run_arms.py"
)

echo "SHA-256 hashes (ARK-454 locked files):"
for f in "${FILES[@]}"; do
  if [[ -f "$f" ]]; then
    h=$(sha256sum "$f" | awk '{print $1}')
    printf "  %-42s %s\n" "$f:" "$h"
  else
    printf "  %-42s MISSING\n" "$f:"
  fi
done
