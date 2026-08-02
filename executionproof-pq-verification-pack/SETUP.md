# Setup — run the verifier from a clean machine

No cloud account, no credentials, no network egress required. Everything runs
offline against the files in this pack.

## Prerequisites

- Linux or macOS
- Python **3.11+**

## Install

```bash
cd executionproof-pq-verification-pack
python3 -m venv .venv && source .venv/bin/activate   # optional but recommended
pip install -r requirements.txt
```

The single dependency is [`dilithium-py`](https://pypi.org/project/dilithium-py/),
a pure-Python FIPS 204 (ML-DSA) implementation. It is **not** the library the
ExecutionProof server uses — that is deliberate. Cross-implementation agreement
is the evidence.

## Run

```bash
python3 independent_verifier.py
echo "exit code: $?"
```

Expected output: every file under `vectors/valid/` prints `[PASS] ... verified`,
every file under `vectors/failure/` prints `[PASS] ... REJECTED`, and the script
exits **0**.

```
RESULT: ALL CHECKS PASSED — every valid vector verified and every
        failure vector was rejected, using only the published keys and
        an independent FIPS 204 implementation.
exit code: 0
```

## Prove it is not rigged

Tampering must break it. Try:

```bash
cp vectors/valid/proof_v001.json /tmp/x.json
python3 - <<'PY'
import json
d=json.load(open('vectors/valid/proof_v001.json'))
d['action']['amount']=1   # change one signed field
json.dump(d,open('vectors/valid/proof_v001.json','w'))
PY
python3 independent_verifier.py ; echo "exit: $?"   # now FAILS, exit 1
cp /tmp/x.json vectors/valid/proof_v001.json          # restore
```

## Confirm the keys are the real published keys

The active and retired public keys in `public_keys/` are the same ones served
live at the ExecutionProof endpoint. Fetch them yourself and diff:

```bash
curl -s https://executionproofdemo.abacusai.app/v2/crypto/pq-public-key \
  | python3 -m json.tool
```

The `public_key_hex`, `public_key_id`, and the `retired_public_keys` entry must
match the files in `public_keys/`.
