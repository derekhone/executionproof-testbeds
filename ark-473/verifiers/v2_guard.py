"""
ARK-473 V2 Guard (Python)
Financial Transaction · Exact-Action Binding

Enforces exact byte-equality across all 5 financial transaction tuple dimensions.
No normalization, no fuzzy matching.
"""

def verify_transaction(authorized: dict, presented: dict) -> dict:
    """
    Verify financial transaction matches exactly across all 5 dimensions.
    
    Returns:
        {"decision": "ALLOW"|"DENY", "reason": str}
    """
    # Exact string equality on all 5 dimensions
    account_from_match = authorized["account_from"] == presented["account_from"]
    account_to_match = authorized["account_to"] == presented["account_to"]
    amount_match = authorized["amount"] == presented["amount"]
    currency_match = authorized["currency"] == presented["currency"]
    type_match = authorized["transaction_type"] == presented["transaction_type"]
    
    if all([account_from_match, account_to_match, amount_match, currency_match, type_match]):
        return {
            "decision": "ALLOW",
            "reason": "All 5 financial transaction dimensions match exactly"
        }
    
    # Build detailed mismatch reason
    mismatches = []
    if not account_from_match:
        mismatches.append(f"account_from: '{authorized['account_from']}' vs '{presented['account_from']}'")
    if not account_to_match:
        mismatches.append(f"account_to: '{authorized['account_to']}' vs '{presented['account_to']}'")
    if not amount_match:
        mismatches.append(f"amount: '{authorized['amount']}' vs '{presented['amount']}'")
    if not currency_match:
        mismatches.append(f"currency: '{authorized['currency']}' vs '{presented['currency']}'")
    if not type_match:
        mismatches.append(f"transaction_type: '{authorized['transaction_type']}' vs '{presented['transaction_type']}'")
    
    return {
        "decision": "DENY",
        "reason": f"Financial Transaction tuple mismatch: {'; '.join(mismatches)}"
    }
