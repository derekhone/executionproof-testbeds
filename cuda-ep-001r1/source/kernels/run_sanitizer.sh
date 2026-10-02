#!/bin/bash
# run_sanitizer.sh - NOT_EXECUTED in current environment (no compute-sanitizer, no GPU)
# CUDA-EP-001 GPU Phase | Remnant Fieldworks Inc. | v1.0 | 2026-10-01
# RESEARCH ONLY - NOT PRODUCTION
#
# Runs NVIDIA Compute Sanitizer (memcheck) against the compiled binary and
# emits a SHA-256 of the sanitizer output so it can be bound as evidence in
# the Request Contract. On a GPU host with the CUDA Toolkit installed, run:
#
#   bash run_sanitizer.sh
#
# In the current environment compute-sanitizer is NOT_FOUND.
set -euo pipefail

compute-sanitizer --tool memcheck ./elementwise_add 2>&1 | tee sanitizer_output.txt
sha256sum sanitizer_output.txt > sanitizer_output.sha256
echo "SANITIZER_HASH: $(cat sanitizer_output.sha256)"
