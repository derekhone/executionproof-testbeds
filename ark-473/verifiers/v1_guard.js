/**
 * ARK-473 V1 Guard (JavaScript)
 * Financial Transaction · Exact-Action Binding
 * 
 * Enforces exact byte-equality across all 5 financial transaction tuple dimensions.
 * No normalization, no fuzzy matching.
 */

function verifyTransaction(authorized, presented) {
  // Exact string equality on all 5 dimensions
  const accountFromMatch = authorized.account_from === presented.account_from;
  const accountToMatch = authorized.account_to === presented.account_to;
  const amountMatch = authorized.amount === presented.amount;
  const currencyMatch = authorized.currency === presented.currency;
  const typeMatch = authorized.transaction_type === presented.transaction_type;
  
  if (accountFromMatch && accountToMatch && amountMatch && currencyMatch && typeMatch) {
    return {
      decision: "ALLOW",
      reason: "All 5 financial transaction dimensions match exactly"
    };
  }
  
  // Build detailed mismatch reason
  const mismatches = [];
  if (!accountFromMatch) mismatches.push(`account_from: '${authorized.account_from}' vs '${presented.account_from}'`);
  if (!accountToMatch) mismatches.push(`account_to: '${authorized.account_to}' vs '${presented.account_to}'`);
  if (!amountMatch) mismatches.push(`amount: '${authorized.amount}' vs '${presented.amount}'`);
  if (!currencyMatch) mismatches.push(`currency: '${authorized.currency}' vs '${presented.currency}'`);
  if (!typeMatch) mismatches.push(`transaction_type: '${authorized.transaction_type}' vs '${presented.transaction_type}'`);
  
  return {
    decision: "DENY",
    reason: `Financial Transaction tuple mismatch: ${mismatches.join("; ")}`
  };
}

// Export for Node.js
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { verifyTransaction };
}
