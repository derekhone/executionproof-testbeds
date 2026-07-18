#!/bin/bash
# Compute SHA-256 hashes of locked files for MANIFEST verification

cd "$(dirname "$0")"

echo "SHA-256 hashes (ARK-457 locked files):"
echo "  PREREGISTRATION.md:                              $(sha256sum PREREGISTRATION.md | cut -d' ' -f1)"
echo "  schemas/context_replay_scenario_schema.json:     $(sha256sum schemas/context_replay_scenario_schema.json | cut -d' ' -f1)"
echo "  verifiers/v1_guard.js:                           $(sha256sum verifiers/v1_guard.js | cut -d' ' -f1)"
echo "  verifiers/v2_guard.py:                           $(sha256sum verifiers/v2_guard.py | cut -d' ' -f1)"
echo "  generator/scenario_generator.py:                 $(sha256sum generator/scenario_generator.py | cut -d' ' -f1)"
echo "  run_killgate.py:                                 $(sha256sum run_killgate.py | cut -d' ' -f1)"
echo "  run_arms.py:                                     $(sha256sum run_arms.py | cut -d' ' -f1)"
