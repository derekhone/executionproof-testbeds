#!/bin/bash
# Compute SHA-256 hashes for ARK-451 locked files
cd "$(dirname "$0")"

echo "Computing SHA-256 hashes for ARK-451 locked files..."

sha256sum PREREGISTRATION.md
sha256sum schemas/revocation_scenario_schema.json
sha256sum verifiers/v1_monitor.js
sha256sum verifiers/v2_monitor.py
sha256sum generator/scenario_generator.py
sha256sum run_killgate.py
sha256sum run_arms.py

echo "Done."
