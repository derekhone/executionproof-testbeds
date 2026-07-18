#!/usr/bin/env python3
"""
ARK-478 V2 Guard (Python)
API Rate Limit · Exact-Action Binding

Enforces exact byte-equality across 5 API rate limit dimensions:
- database_name, table_name, operation, schema_version, execution_mode
"""

from typing import Dict, Any


def verify_rate_limit(authorized_request: Dict[str, str], presented_request: Dict[str, str]) -> Dict[str, Any]:
    """
    Verify database destructive query authorization.
    
    ALLOW if all 5 dimensions match exactly (byte-equality).
    DENY otherwise.
    """
    # Check exact equality on all 5 dimensions
    database_match = authorized_request["database_name"] == presented_request["database_name"]
    table_match = authorized_request["table_name"] == presented_request["table_name"]
    operation_match = authorized_request["operation"] == presented_request["operation"]
    schema_match = authorized_request["schema_version"] == presented_request["schema_version"]
    mode_match = authorized_request["execution_mode"] == presented_request["execution_mode"]
    
    all_match = database_match and table_match and operation_match and schema_match and mode_match
    
    if all_match:
        return {
            "decision": "ALLOW",
            "reason": "Exact match on all 5 dimensions"
        }
    else:
        mismatches = []
        if not database_match:
            mismatches.append("database_name")
        if not table_match:
            mismatches.append("table_name")
        if not operation_match:
            mismatches.append("operation")
        if not schema_match:
            mismatches.append("schema_version")
        if not mode_match:
            mismatches.append("execution_mode")
        
        return {
            "decision": "DENY",
            "reason": f"Mismatch on: {', '.join(mismatches)}"
        }
