#!/bin/bash
# ARK-484 — Compute SHA-256 hashes for preregistration lock

echo "Computing SHA-256 hashes for ARK-484 source files..."

sha256sum \
  PREREGISTRATION.md \
  generator/scenario_generator.py \
  verifiers/v1_guard_frozen.js \
  verifiers/v2_guard_frozen.py \
  measure_throughput.py \
  > MANIFEST.txt

echo "✅ MANIFEST.txt created"
cat MANIFEST.txt
