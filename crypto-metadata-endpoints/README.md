# Crypto Metadata Endpoints — EXPERIMENTAL Software Simulation

> **⚠️ EXPERIMENTAL / SOFTWARE SIMULATION / TESTBED ONLY.**
> This is **not** a live AWS KMS or HSM deployment. It performs **no signing**
> and touches **no hardware security boundary**. **No FIPS conformance,
> validation, certification, or CNSA-compliance claim is made or implied.**
> `formal_conformance` is reported as *"pending independent external review"*,
> consistent with the repository's non-claim boundary.

## What this is

Addresses [issue #25](https://github.com/derekhone/executionproof-testbeds/issues/25)
("Deploy live crypto metadata endpoints for AWS KMS ML-DSA-65 status").

The public endpoints `/v2/crypto-manifest`, `/v2/crypto/pq-public-key`, and
`/v2/version` were returning `404` from `executionproof.io`. The expected
metadata contract was documented in PR #24 under
[`docs/crypto-api-metadata-contract.md`](../docs/crypto-api-metadata-contract.md)
but no runnable endpoint implementation existed in this repo.

This directory provides a **self-contained software simulation** of those
endpoints so the contract shape, routing, schema, and the existing verification
tooling can be exercised locally and reviewed — **without** standing up live AWS
KMS infrastructure.

### Why the custody fields say `aws-kms-native` / `hardware_backed: true`

Those values are the **documented production contract**, copied verbatim from
`docs/crypto-api-metadata-contract.md` so the simulation reproduces the exact
shape downstream consumers expect. They describe the *intended production
posture*, **not** this testbed. Every response therefore also carries:

- an `_simulation` block (`simulation: true`, `hardware_present: false`,
  `live_aws_kms: false`, full disclaimer `notice`);
- `simulated: true` alongside the contract fields;
- `X-ExecutionProof-Simulation: true` and `X-ExecutionProof-Experimental: true`
  HTTP headers.

So no consumer can read a payload without seeing that this is a simulation.

## Endpoints

| Route | Description |
|-------|-------------|
| `GET /` | Index: simulation notice + route list |
| `GET /health` | Liveness: `{"status":"ok","simulation":true}` |
| `GET /v2/version` | API / algorithm version metadata (simulated) |
| `GET /v2/crypto-manifest` | Full crypto metadata manifest (simulated) |
| `GET /v2/crypto/pq-public-key` | Active + retired ML-DSA-65 public keys (simulated) |

The manifest exposes the required common contract fields plus: active public-key
ID / key version, retired public-key IDs (for historical ProofRecord
verification), signature metadata schema, canonical payload hashing rules, and
rotation / retirement / revocation behavior.

Public-key material is reused **read-only** from the already-published
[`executionproof-pq-verification-pack/`](../executionproof-pq-verification-pack/)
so the simulated manifest stays consistent with the committed verification
vectors.

## Run locally

```bash
pip install -r crypto-metadata-endpoints/requirements.txt
python crypto-metadata-endpoints/app.py            # 127.0.0.1:8088 (loopback)
# then:
curl -s http://127.0.0.1:8088/v2/crypto-manifest | python -m json.tool
```

## Static snapshots (no server)

```bash
python crypto-metadata-endpoints/generate_snapshots.py
# writes snapshots/v2_version.json, v2_crypto-manifest.json,
# v2_crypto_pq-public-key.json, and index.json
```

## Tests

```bash
python crypto-metadata-endpoints/test_endpoints.py
```

Tests assert the required contract fields are present, every payload is flagged
as a simulation, the public keys are exposed, and that **no** forbidden
certified/compliant terminology appears in any payload.

## Scope / boundaries

- Simulation only — no HSM/TPM/hardware boundary, no real signing.
- No FIPS/CNSA compliance, validation, or certification claims.
- No new experiments, no new Zenodo DOIs — this is an endpoint/code fix only.
- Routing these simulated responses (or the static snapshots) onto the public
  `executionproof.io` domain remains a separate website/API-deployment task,
  outside this repository.
