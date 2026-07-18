#!/usr/bin/env python3
"""
FROZEN from ARK-458/463 for throughput testing
Original: Production Deployment exact-action binding guard
"""
#!/usr/bin/env python3
"""
ARK-463 V2 Guard (Python)
Production Deployment · Exact-Action Binding

Enforces exact string equality across all 5 deployment tuple dimensions.
No normalization, no fuzzy matching.
Independent implementation from V1 (JavaScript).
"""

from typing import Dict, Any


def verify_deployment(authorized: Dict[str, str], presented: Dict[str, str]) -> Dict[str, str]:
    """
    Verify deployment authorization via exact 5-tuple matching.
    
    Args:
        authorized: The authorized deployment tuple (5 fields)
        presented: The deployment tuple being requested (5 fields)
    
    Returns:
        Dict with 'decision' (ALLOW|DENY) and 'reason' (string)
    """
    # Exact string equality on all 5 dimensions
    service_match = authorized["service_name"] == presented["service_name"]
    environment_match = authorized["environment"] == presented["environment"]
    version_match = authorized["version"] == presented["version"]
    region_match = authorized["region"] == presented["region"]
    method_match = authorized["deployment_method"] == presented["deployment_method"]
    
    if service_match and environment_match and version_match and region_match and method_match:
        return {
            "decision": "ALLOW",
            "reason": "All 5 deployment dimensions match exactly"
        }
    
    # Build detailed mismatch reason
    mismatches = []
    if not service_match:
        mismatches.append(f"service_name: '{authorized['service_name']}' vs '{presented['service_name']}'")
    if not environment_match:
        mismatches.append(f"environment: '{authorized['environment']}' vs '{presented['environment']}'")
    if not version_match:
        mismatches.append(f"version: '{authorized['version']}' vs '{presented['version']}'")
    if not region_match:
        mismatches.append(f"region: '{authorized['region']}' vs '{presented['region']}'")
    if not method_match:
        mismatches.append(f"deployment_method: '{authorized['deployment_method']}' vs '{presented['deployment_method']}'")
    
    return {
        "decision": "DENY",
        "reason": f"Deployment tuple mismatch: {'; '.join(mismatches)}"
    }


if __name__ == "__main__":
    # Quick self-test
    auth = {
        "service_name": "user-api",
        "environment": "production",
        "version": "v2.3.1",
        "region": "us-east-1",
        "deployment_method": "rolling-update"
    }
    
    # Test exact match
    result = verify_deployment(auth, auth.copy())
    assert result["decision"] == "ALLOW", "Exact match should ALLOW"
    
    # Test mismatch
    presented = auth.copy()
    presented["version"] = "v2.3.2"
    result = verify_deployment(auth, presented)
    assert result["decision"] == "DENY", "Version mismatch should DENY"
    
    print("✅ V2 guard self-test passed")
