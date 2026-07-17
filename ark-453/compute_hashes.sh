#!/bin/bash
# Compute SHA-256 hashes for ARK-453 locked files
cd "$(dirname "$0")"

echo "Computing SHA-256 hashes for ARK-453 locked files..."

sha256sum PREREGISTRATION.md
sha256sum schemas/evidence_scenario_schema.json
sha256sum verifiers/v1_resolver.js
sha256sum verifiers/v2_resolver.py
sha256sum generator/scenario_generator.py
sha256sum run_killgate.py
sha256sum run_arms.py

echo "Done."
