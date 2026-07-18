#!/bin/bash
cd "$(dirname "$0")"
echo "SHA-256 hashes (ARK-461 locked files):"
for f in PREREGISTRATION.md verifiers/v1_guard.js verifiers/v2_guard.py \
         generator/scenario_generator.py run_killgate.py run_arms.py; do
  printf "  %-48s %s\n" "$f:" "$(sha256sum "$f" | cut -d' ' -f1)"
done
