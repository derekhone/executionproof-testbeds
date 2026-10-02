# CUDA-EP-001: ExecutionProof Pre-GPU Preregistration and Reproducibility Package

Proof Before Power(TM) / Verification Before Execution(TM)
Remnant Fieldworks Inc.

Status: PENDING - PRE-GPU

## What this is

CUDA-EP-001 is a preregistered experiment that asks a single, narrow question:
on real NVIDIA GPU hardware, does an ExecutionProof authorization gateway permit
the exact attested CUDA artifact to launch only under a valid ALLOW condition,
and prevent launch under HOLD, DENY, and verification-failure conditions
(including GPU-C8 exclusive launcher control)?

This package is the frozen, pre-GPU state of that experiment. It contains the
preregistration, the source under test, the authorization gateway, the CPU
surrogate evidence, and the honestly preserved BLOCKED_NO_GPU records.

## What has and has NOT happened (read this first)

NO REAL GPU EXECUTION HAS OCCURRED.

- GPU-C0 through GPU-C8 have NOT been run on hardware.
- The nine GPU case records show BLOCKED_NO_GPU. This reflects the absence of GPU
  hardware in the preparation environment, NOT observed enforcement against real
  CUDA execution.
- CUDA compilation (nvcc) has NOT been run.
- Compute Sanitizer has NOT been run. No memory-safety or race evidence exists.
- GPU-C8 (exclusive launcher control), the most important governance test, is
  NOT EXECUTED.

What was done, on CPU only, as supporting evidence:
- 7/7 CPU functional reference-oracle tests PASS (numpy oracle, CPU only).
- 8/8 CPU-surrogate case traces matched the preregistered expected outputs.
- 24/24 CPU-surrogate unit tests PASS.
- ProofRecords signed/verified with a TEST KEY (NOT a production key).

The single supportable statement at this stage is:
"The ExecutionProof authorization logic was exercised in CPU-surrogate form,
with 8/8 case traces matching the preregistered expected outputs. Real GPU
execution remains pending."

## Corpus status

CUDA-EP-001 = PENDING - PRE-GPU. It does NOT count as a PASS and does NOT change
the RF experimental corpus count (106 total / 95 PASS / 8 preserved FAIL / 3
special). The CPU-surrogate phase is supporting evidence, not a separate
experiment. See `docs/12_CUDA_EP_001_MASTER_RECORD_UPDATE.md`.

## Layout

- `00_freeze/` - pre-GPU freeze manifest, SHA256SUMS, execution-state record
- `docs/` - claims ledger, limitations, test/evidence map, claim audit,
  preregistration, request contract, reproducibility guide, ProofRecord index,
  case results, hash manifest, final execution report, master-record update
- `source/` - CUDA kernel + compile/sanitizer scripts, authorization gateway,
  launcher, policy, test scripts, ProofRecord sign/verify tools
- `proofrecords/` - GPU-C0 through GPU-C8 ProofRecords (all BLOCKED_NO_GPU) + manifest
- `raw-logs/` - pre-GPU raw logs (functional tests, CPU surrogate reference,
  GPU environment discovery, ProofRecord signing)
- `HONEST_STATUS.md`, `SECURITY_NOTES.md`, `CITATION.cff`, `LICENSE`

## Reproduction

See `docs/06_CUDA_EP_001_REAL_GPU_REPRODUCIBILITY_GUIDE.md`. The GPU phase
section includes a package-availability precondition (Step 0): verify the exact
package is present on the GPU host and that `sha256sum -c
00_freeze/PRE_GPU_SHA256SUMS.txt` reports all files OK BEFORE spending any GPU
money. Do not assume this public path exists until the release is live.

## What this package does NOT claim

It does not claim to secure CUDA, guarantee GPU safety, prove kernel
correctness, be non-bypassable, or be production-ready. It makes no independent
or NVIDIA validation claim. It makes no CIF claim of any kind.

## License

MIT (see `LICENSE`).
