#!/bin/bash
echo "Computing SHA-256 hashes for ARK-468..."
sha256sum \
  PREREGISTRATION.md \
  generator/scenario_generator.py \
  verifiers/v1_guard.js \
  verifiers/v2_guard.py \
  run_arms.py \
  run_killgate.py \
  > MANIFEST.txt
echo "✅ MANIFEST.txt created"
cat MANIFEST.txt
