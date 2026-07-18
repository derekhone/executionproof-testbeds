#!/bin/bash
# ARK-465 — Compute SHA-256 hashes for preregistration lock

echo "Computing SHA-256 hashes for ARK-465 source files..."

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
