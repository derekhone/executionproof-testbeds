#!/usr/bin/env bash
# ARK-455b — compute SHA-256 hashes of all locked files for MANIFEST.txt.
# Usage: bash compute_hashes.sh
set -euo pipefail
cd "$(dirname "$0")"

FILES=(
  "PREREGISTRATION.md"
  "schemas/proofrecord_schema.json"
  "verifiers/v1_verifier.js"
  "verifiers/v2_verifier.py"
  "generator/record_generator.py"
  "run_killgate.py"
  "run_arms.py"
)

echo "SHA-256 hashes (ARK-455b locked files):"
for f in "${FILES[@]}"; do
  if [[ -f "$f" ]]; then
    h=$(sha256sum "$f" | awk '{print $1}')
    printf "  %-34s %s\n" "$f:" "$h"
  else
    printf "  %-34s MISSING\n" "$f:"
  fi
done
