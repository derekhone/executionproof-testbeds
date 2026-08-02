# Canonicalization Law — what is signed, and exactly how

This is the normative specification of the bytes that an ExecutionProof
ProofRecord signature is computed over. `independent_verifier.py` implements
this law in `canonical_json()` / `canonical_payload_bytes()`; the server
implements the same law in `proof-signature.service.ts`. A signature verifies
if and only if a verifier reconstructs **these exact bytes**.

## 1. The signed field set (order is fixed)

Only the following 22 fields of a ProofRecord are signed, in this order. All
other fields (notably `proof_signature_pq`, `proof_signature`, hashes, ids,
timestamps added after signing) are **excluded** from the signed payload:

```
 version, request_id, tenant_id, chain_id, sequence_number, rail,
 gate_layers, actor, action, context, evidence_items, constraints_input,
 intended_outcome, failure_conditions, proof_requirement, authority_result,
 evidence_result, constraint_result, control_decision, execution_result,
 coherence_envelope, audit_trail
```

The signed object is built by taking each field name above from the record (a
missing field is included with value `null`). Field-set ordering is not what
makes serialization deterministic — the canonical JSON rule below does — but the
field **set** is normative: adding or dropping a field changes the bytes.

## 2. Canonical JSON serialization

The signed object is serialized to a byte string by these rules, applied
recursively:

1. **Object keys are sorted** ascending by Unicode code point, at **every**
   level of nesting (deep sort).
2. **No insignificant whitespace** — no spaces or newlines between tokens.
   `{"a":1,"b":2}`, never `{ "a": 1, "b": 2 }`.
3. **Strings are UTF-8, not ASCII-escaped** (`ensure_ascii=False`). A non-ASCII
   character is emitted as its UTF-8 bytes, not as a `\uXXXX` escape.
4. **`null` is preserved** (it is not dropped).
5. Numbers and booleans use standard JSON literal form.
6. The result is encoded to bytes as **UTF-8**.

This matches JavaScript `JSON.stringify` semantics with recursively sorted
object keys. The reference implementation is `canonical_json()` in
`independent_verifier.py` — read it; it is ~15 lines.

## 3. Message binding — what the signature covers

The signature covers a message derived from the canonical payload bytes. The
derivation depends on the signing key's **custody mode**:

| Custody mode | Message that is signed |
|--------------|------------------------|
| `aws-kms-native` (active key `00a69ffbb8a33217`) | `SHA-256(canonical_payload_bytes)` — a 32-byte digest. AWS KMS ML-DSA RAW signing caps the input message at 4096 bytes, so ExecutionProof signs the digest. |
| `software-wrapped` (retired key `13757ac965b41061`) | the `canonical_payload_bytes` **directly** (in-process signing, pre-rotation). |

A correct verifier therefore tries **both** message forms and accepts the
record if either verifies against a published, non-revoked key. The verifier in
this pack does exactly that (`verify_against_published()`): it tries the digest
form first, then the raw form, against each published key.

Which form a given record uses can be read from the record's own custody
metadata, but a verifier does not need to trust that metadata — trying both
forms and requiring a cryptographic match is strictly safer.

## 4. Algorithm and sizes (ML-DSA-65, FIPS 204)

| Quantity | Value |
|----------|-------|
| Algorithm | ML-DSA-65 (CRYSTALS-Dilithium), NIST FIPS 204, security category 3 |
| KMS signing algorithm | `ML_DSA_SHAKE_256` |
| Public key | 1952 bytes (3904 hex chars) |
| Secret key | 4032 bytes (never leaves the HSM under native custody) |
| Signature | 3309 bytes (6618 hex chars) |
| Signature context (`ctx`) | empty (`b""`) |

Signatures and public keys are published/stored as lowercase hex. The verifier
rejects any `proof_signature_pq` whose decoded length is not 3309 bytes before
it even attempts verification.

## 5. Worked reconstruction (do this yourself)

For any record `R` in `vectors/valid/`:

```python
import json, hashlib
from dilithium_py.ml_dsa import ML_DSA_65
from independent_verifier import canonical_payload_bytes  # the law, in code

R   = json.load(open("vectors/valid/proof_v001.json"))
raw = canonical_payload_bytes(R)               # section 1 + 2
dig = hashlib.sha256(raw).digest()             # section 3, native custody
sig = bytes.fromhex(R["proof_signature_pq"])   # 3309 bytes
pk  = bytes.fromhex(json.load(open("public_keys/active_00a69ffbb8a33217.json"))["public_key_hex"])

assert ML_DSA_65.verify(pk, dig, sig)          # True for active records
```

If you can reproduce this with your **own** canonicalizer (not importing ours),
you have independently confirmed the law is correctly documented.
