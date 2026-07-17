#!/usr/bin/env node
/**
 * ARK-455 Verifier V1 (JavaScript/Node.js)
 * Independent ProofRecord signature verification per preregistration Section 4.3
 */

const crypto = require('crypto');
const nacl = require('tweetnacl');

/**
 * Canonicalize a JavaScript object per RFC 8785 (JCS)
 * Returns deterministic byte representation
 */
function canonicalizeJCS(obj) {
  // RFC 8785: serialize with sorted keys, no whitespace
  const canonical = JSON.stringify(obj, Object.keys(obj).sort(), 0);
  return Buffer.from(canonical, 'utf8');
}

/**
 * Verify a signed ProofRecord
 * 
 * Per ARK-455 Section 4.3:
 * 1. Extract signature field
 * 2. Remove signature, leaving original 7 fields
 * 3. Canonicalize via RFC 8785
 * 4. Verify Ed25519 signature
 * 5. ACCEPT if valid, REJECT if invalid
 */
function verifyProofRecord(record, publicKeyHex) {
  try {
    // 1. Extract signature
    if (!record.signature) {
      return "REJECT"; // No signature present
    }
    
    const signatureHex = record.signature;
    const signatureBytes = Buffer.from(signatureHex, 'hex');
    
    if (signatureBytes.length !== 64) {
      return "REJECT"; // Invalid signature length
    }
    
    // 2. Remove signature field, leaving original 7 fields
    const unsignedRecord = {
      decision: record.decision,
      timestamp: record.timestamp,
      payload_hash: record.payload_hash,
      evidence_references: record.evidence_references,
      actor: record.actor,
      execution_outcome: record.execution_outcome,
      review_path: record.review_path
    };
    
    // 3. Canonicalize via RFC 8785
    const canonicalBytes = canonicalizeJCS(unsignedRecord);
    
    // 4. Verify Ed25519 signature
    const publicKeyBytes = Buffer.from(publicKeyHex, 'hex');
    
    if (publicKeyBytes.length !== 32) {
      return "REJECT"; // Invalid public key length
    }
    
    const isValid = nacl.sign.detached.verify(
      canonicalBytes,
      signatureBytes,
      publicKeyBytes
    );
    
    // 5. Return verdict
    return isValid ? "ACCEPT" : "REJECT";
    
  } catch (error) {
    // Any exception during verification → REJECT
    return "REJECT";
  }
}

/**
 * Batch verify multiple records
 */
function batchVerify(records, publicKeyHex) {
  let accepted = 0;
  let rejected = 0;
  
  for (const record of records) {
    const verdict = verifyProofRecord(record, publicKeyHex);
    if (verdict === "ACCEPT") {
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

// CLI interface for standalone execution
if (require.main === module) {
  const fs = require('fs');
  const args = process.argv.slice(2);
  
  if (args.length < 2) {
    console.error("Usage: node v1_verifier.js <public_key_hex> <records.json>");
    process.exit(1);
  }
  
  const publicKeyHex = args[0];
  const recordsFile = args[1];
  
  const recordsData = JSON.parse(fs.readFileSync(recordsFile, 'utf8'));
  const records = Array.isArray(recordsData) ? recordsData : [recordsData];
  
  const result = batchVerify(records, publicKeyHex);
  
  console.log(JSON.stringify({
    verifier: "V1-JavaScript",
    total: records.length,
    accepted: result.accepted,
    rejected: result.rejected,
    rate_accept: result.rate_accept.toFixed(4),
    rate_reject: result.rate_reject.toFixed(4)
  }, null, 2));
}

module.exports = { verifyProofRecord, batchVerify };
