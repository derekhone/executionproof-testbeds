#!/bin/bash
# compile_kernel.sh - NOT_EXECUTED in current environment (no nvcc, no GPU)
# CUDA-EP-001 GPU Phase | Remnant Fieldworks Inc. | v1.0 | 2026-10-01
# RESEARCH ONLY - NOT PRODUCTION
#
# This script compiles the candidate kernel and emits a SHA-256 of the
# resulting binary. On a GPU host with the CUDA Toolkit installed, run:
#
#   bash compile_kernel.sh
#
# In the current environment nvcc is NOT_FOUND, so this script WOULD run
# but cannot. The build attestation marks binary hashes NOT_EXECUTED.
set -euo pipefail

SRC="elementwise_add.cu"
OUT="elementwise_add"

nvcc -O2 --generate-code arch=compute_80,code=sm_80 "${SRC}" -o "${OUT}"
sha256sum "${OUT}" > "${OUT}.sha256"
echo "BINARY_HASH: $(cat ${OUT}.sha256)"
