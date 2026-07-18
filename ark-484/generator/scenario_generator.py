#!/usr/bin/env python3
"""
ARK-484 Scenario Generator — Verification Decision · Burst Throughput

Generates 100,000 deployment authorization test scenarios for burst throughput testing.
50% ALLOW (exact match), 50% DENY (various mismatches).
"""

import json
import random
from typing import List, Dict, Any

# Set seed for reproducibility
random.seed(484_001)

# Base deployment tuples
BASE_DEPLOYMENTS = [
    {
        "service_name": "user-api",
        "environment": "production",
        "version": "v2.3.1",
        "region": "us-east-1",
        "deployment_method": "rolling-update"
    },
    {
        "service_name": "payment-processor",
        "environment": "production",
        "version": "v1.8.5",
        "region": "eu-west-1",
        "deployment_method": "blue-green"
    },
    {
        "service_name": "analytics-engine",
        "environment": "staging",
        "version": "v3.0.0-rc.2",
        "region": "us-west-2",
        "deployment_method": "canary"
    },
    {
        "service_name": "notification-service",
        "environment": "production",
        "version": "sha256:a3f5e9c12b",
        "region": "ap-southeast-1",
        "deployment_method": "recreate"
    },
    {
        "service_name": "auth-gateway",
        "environment": "production",
        "version": "v4.2.0",
        "region": "us-east-2",
        "deployment_method": "rolling-update"
    }
]


def generate_exact_match_scenarios(n: int) -> List[Dict[str, Any]]:
    """Generate scenarios where authorized and presented match exactly → ALLOW"""
    scenarios = []
    for i in range(n):
        base = random.choice(BASE_DEPLOYMENTS)
        scenarios.append({
            "scenario_id": f"burst_allow_{i:06d}",
            "authorized_deployment": base.copy(),
            "presented_deployment": base.copy(),
            "expected_decision": "ALLOW"
        })
    return scenarios


def generate_mismatch_scenarios(n: int) -> List[Dict[str, Any]]:
    """Generate scenarios with mismatches → DENY"""
    scenarios = []
    dimensions = ["service_name", "environment", "version", "region", "deployment_method"]
    
    for i in range(n):
        base = random.choice(BASE_DEPLOYMENTS).copy()
        authorized = base.copy()
        presented = base.copy()
        
        # Pick 1-3 dimensions to mismatch
        num_mismatches = random.randint(1, 3)
        mismatch_dims = random.sample(dimensions, num_mismatches)
        
        for dim in mismatch_dims:
            if dim == "service_name":
                presented[dim] = presented[dim] + "-modified"
            elif dim == "environment":
                presented[dim] = "staging" if presented[dim] == "production" else "production"
            elif dim == "version":
                presented[dim] = presented[dim] + ".1"
            elif dim == "region":
                presented[dim] = "us-east-1" if presented[dim] != "us-east-1" else "eu-west-1"
            elif dim == "deployment_method":
                methods = ["rolling-update", "blue-green", "canary"]
                presented[dim] = random.choice([m for m in methods if m != presented[dim]])
        
        scenarios.append({
            "scenario_id": f"burst_deny_{i:06d}",
            "authorized_deployment": authorized,
            "presented_deployment": presented,
            "expected_decision": "DENY"
        })
    
    return scenarios


def main():
    """Generate 100,000 scenarios (50% ALLOW, 50% DENY)"""
    print("Generating 100,000 burst throughput test scenarios...")
    print("=" * 70)
    
    # Generate scenarios
    allow_scenarios = generate_exact_match_scenarios(50_000)
    deny_scenarios = generate_mismatch_scenarios(50_000)
    
    # Combine and shuffle for realistic mix
    all_scenarios = allow_scenarios + deny_scenarios
    random.shuffle(all_scenarios)
    
    print(f"Generated {len(all_scenarios)} scenarios")
    print(f"  ALLOW scenarios: {len(allow_scenarios)}")
    print(f"  DENY scenarios:  {len(deny_scenarios)}")
    
    # Save to file
    output_file = "results/burst_scenarios.json"
    with open(output_file, "w") as f:
        json.dump(all_scenarios, f, indent=2)
    
    print(f"\n✅ Saved to {output_file}")
    print(f"File size: {len(json.dumps(all_scenarios)) / 1024 / 1024:.2f} MB")


if __name__ == "__main__":
    main()
