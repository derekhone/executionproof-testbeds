#!/usr/bin/env node
/**
 * ARK-455b Verifier V1 (JavaScript/Node.js)
 * Independent ProofRecord verification per preregistration Sections 4.3 and 4.4.
 *
 * ISOLATION NOTICE: built solely from the ARK-455b prose specification; does not
 * reference Verifier V2 (Python), the generator, or any other implementation.
 *
 * Verification is TWO independent gates (both must pass to ACCEPT):
 *   Gate A — Signature integrity (Section 4.3):
 *     remove signature, canonicalize 7 signed fields via RFC 8785, verify Ed25519.
 *     Invalid signature -> REJECT.
 *   Gate B — Validity window (Section 4.4):
 *     parse timestamp as RFC 3339 UTC; age = verificationTime - timestamp.
 *     age < 0 (future) -> REJECT; age > ttlSeconds (expired) -> REJECT; else ACCEPT.
 *
 * Gate B is the ARK-455b addition: a bare signature check cannot catch a record
 * whose timestamp was placed out of the validity window BEFORE signing (the
 * signature is genuinely valid but the record is stale/expired). Expiry
 * semantics follow ARK-442.
 */

const nacl = require('tweetnacl');

const SIGNED_FIELDS = [
  'decision', 'timestamp', 'payload_hash', 'evidence_references',
  'actor', 'execution_outcome', 'review_path'
];

/**
 * Canonicalize a JavaScript object per RFC 8785 (JCS): sorted keys, no whitespace.
 */
function canonicalizeJCS(obj) {
  const canonical = JSON.stringify(obj, Object.keys(obj).sort(), 0);
  return Buffer.from(canonical, 'utf8');
}

/**
 * Parse an RFC 3339 UTC timestamp (trailing 'Z' or +00:00 offset).
 * Returns milliseconds since epoch. Throws on malformed / non-UTC input.
 */
function parseRfc3339Utc(ts) {
  if (typeof ts !== 'string') {
    throw new Error('timestamp not a string');
  }
  // Require an explicit UTC designator: 'Z' or '+00:00'.
  if (!/Z$|\+00:00$/.test(ts)) {
    throw new Error('timestamp not UTC');
  }
  const ms = Date.parse(ts);
  if (Number.isNaN(ms)) {
    throw new Error('unparseable timestamp');
  }
  return ms;
}

/**
 * Verify a signed ProofRecord under both gates.
 */
function verifyProofRecord(record, publicKeyHex, verificationTimeIso, ttlSeconds) {
  try {
    // ---- Gate A: signature integrity ----
    if (!record.signature) {
      return 'REJECT';
    }

    const signatureBytes = Buffer.from(record.signature, 'hex');
    if (signatureBytes.length !== 64) {
      return 'REJECT';
    }

    const unsignedRecord = {};
    for (const field of SIGNED_FIELDS) {
      unsignedRecord[field] = record[field];
    }

    const canonicalBytes = canonicalizeJCS(unsignedRecord);

    const publicKeyBytes = Buffer.from(publicKeyHex, 'hex');
    if (publicKeyBytes.length !== 32) {
      return 'REJECT';
    }

    const isValid = nacl.sign.detached.verify(
      canonicalBytes,
      signatureBytes,
      publicKeyBytes
    );
    if (!isValid) {
      return 'REJECT';
    }

    // ---- Gate B: validity window ----
    const recordMs = parseRfc3339Utc(record.timestamp);
    const verificationMs = parseRfc3339Utc(verificationTimeIso);
    const ageSeconds = (verificationMs - recordMs) / 1000;

    if (ageSeconds < 0) {
      return 'REJECT'; // issued in the future
    }
    if (ageSeconds > ttlSeconds) {
      return 'REJECT'; // expired
    }

    return 'ACCEPT';

  } catch (error) {
    return 'REJECT';
  }
}

/**
 * Batch verify multiple records.
 */
function batchVerify(records, publicKeyHex, verificationTimeIso, ttlSeconds) {
  let accepted = 0;
  let rejected = 0;
  for (const record of records) {
    const verdict = verifyProofRecord(record, publicKeyHex, verificationTimeIso, ttlSeconds);
    if (verdict === 'ACCEPT') {
      accepted++;
    } else {
      rejected++;
    }
  }
  const total = records.length;
  return {
    accepted,
    rejected,
    rate_accept: total > 0 ? accepted / total : 0,
    rate_reject: total > 0 ? rejected / total : 0
  };
}

// CLI interface
if (require.main === module) {
  const fs = require('fs');
  const args = process.argv.slice(2);

  if (args.length < 4) {
    console.error('Usage: node v1_verifier.js <public_key_hex> <records.json> '
      + '<verification_time_iso> <ttl_seconds>');
    process.exit(1);
  }

  const publicKeyHex = args[0];
  const recordsFile = args[1];
  const verificationTimeIso = args[2];
  const ttlSeconds = parseInt(args[3], 10);

  const recordsData = JSON.parse(fs.readFileSync(recordsFile, 'utf8'));
  const records = Array.isArray(recordsData) ? recordsData : [recordsData];

  const result = batchVerify(records, publicKeyHex, verificationTimeIso, ttlSeconds);

  console.log(JSON.stringify({
    verifier: 'V1-JavaScript',
    total: records.length,
    accepted: result.accepted,
    rejected: result.rejected,
    rate_accept: result.rate_accept.toFixed(4),
    rate_reject: result.rate_reject.toFixed(4)
  }, null, 2));
}

module.exports = { verifyProofRecord, batchVerify };
