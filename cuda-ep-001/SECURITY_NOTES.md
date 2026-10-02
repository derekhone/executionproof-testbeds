# Security Notes

- All ProofRecords in this package were signed with a TEST KEY labeled
  "TEST KEY - NOT PRODUCTION". No production signing key is present in this
  repository, and none should ever be committed.
- No API keys, access tokens, passwords, or production secrets are included in
  this package.
- No payment or billing information is included.
- No private university material, unpublished patent text, internal strategic
  documents, or NVIDIA private-portal information is included.
- When transferring this package to a GPU host for the real GPU phase, use a
  short-lived credential and never embed tokens in scripts or logs (see the
  reproducibility guide, GPU phase Step 0).
- Report any security concern to the maintainer listed in CITATION.cff.
