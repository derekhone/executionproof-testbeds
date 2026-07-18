#!/bin/bash
# Compute SHA-256 hashes of locked files for MANIFEST verification
cd "$(dirname "$0")"
echo "SHA-256 hashes (ARK-483 locked files):"
for f in PREREGISTRATION.md bench/latency_bench.py bench/latency_bench_v1.js; do
  printf "  %-40s %s\n" "$f:" "$(sha256sum "$f" | cut -d' ' -f1)"
done
