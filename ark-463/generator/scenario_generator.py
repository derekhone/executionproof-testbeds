#!/usr/bin/env python3
"""
ARK-463 Scenario Generator — Production Deployment · Exact-Action Binding

Generates 8 arms × 100 scenarios = 800 deployment authorization decisions.
Tests exact-match enforcement across 5-tuple deployment dimensions.
"""

import json
import random
from typing import List, Dict, Any

# Set seed for reproducibility
random.seed(463_001)

# Canonical deployment tuples for exact-match testing
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
    }
]

# Mismatch variants for each dimension
SERVICE_NAME_VARIANTS = [
    ("user-api", "User-API"),  # case
    ("user-api", "user-api-v2"),  # suffix
    ("payment-processor", "payment_processor"),  # underscore vs hyphen
    ("analytics-engine", "analytics-engien"),  # typo
    ("notification-service", " notification-service"),  # leading space
]

ENVIRONMENT_VARIANTS = [
    ("production", "Production"),  # case
    ("production", "prod"),  # abbreviation
    ("staging", "stage"),  # abbreviation
    ("production", "production-eu"),  # suffix
]

VERSION_VARIANTS = [
    ("v2.3.1", "v2.3.2"),  # patch bump
    ("v1.8.5", "v1.8.5-hotfix"),  # suffix
    ("v3.0.0-rc.2", "v3.0.0-rc.3"),  # RC increment
    ("sha256:a3f5e9c12b", "sha256:a3f5e9c12c"),  # SHA diff
    ("v2.3.1", "2.3.1"),  # missing prefix
]

REGION_VARIANTS = [
    ("us-east-1", "us-east-2"),  # different AZ
    ("eu-west-1", "EU-WEST-1"),  # case
    ("us-west-2", "us-west-2a"),  # AZ suffix
    ("ap-southeast-1", "ap-south-1"),  # different region
]

METHOD_VARIANTS = [
    ("rolling-update", "rolling_update"),  # underscore vs hyphen
    ("blue-green", "blue_green"),  # underscore vs hyphen
    ("canary", "Canary"),  # case
    ("recreate", "rolling-update"),  # completely different
]


def generate_arm_1_exact_match(n=100) -> List[Dict[str, Any]]:
    """Arm 1: Exact match on all 5 dimensions → ALLOW"""
    scenarios = []
    for i in range(n):
        base = random.choice(BASE_DEPLOYMENTS)
        scenarios.append({
            "scenario_id": f"arm_1_{i:03d}",
            "authorized_deployment": base.copy(),
            "presented_deployment": base.copy(),
            "expected_decision": "ALLOW",
            "arm": 1,
            "mismatch_dimensions": []
        })
    return scenarios


def generate_arm_2_service_mismatch(n=100) -> List[Dict[str, Any]]:
    """Arm 2: Service name mismatch → DENY"""
    scenarios = []
    for i in range(n):
        base = random.choice(BASE_DEPLOYMENTS).copy()
        original, variant = random.choice(SERVICE_NAME_VARIANTS)
        
        authorized = base.copy()
        if authorized["service_name"] == original:
            authorized["service_name"] = original
        
        presented = base.copy()
        if presented["service_name"] == original:
            presented["service_name"] = variant
        else:
            # Use a generic mismatch
            presented["service_name"] = presented["service_name"] + "-modified"
        
        scenarios.append({
            "scenario_id": f"arm_2_{i:03d}",
            "authorized_deployment": authorized,
            "presented_deployment": presented,
            "expected_decision": "DENY",
            "arm": 2,
            "mismatch_dimensions": ["service_name"]
        })
    return scenarios


def generate_arm_3_environment_mismatch(n=100) -> List[Dict[str, Any]]:
    """Arm 3: Environment mismatch → DENY"""
    scenarios = []
    for i in range(n):
        base = random.choice(BASE_DEPLOYMENTS).copy()
        original, variant = random.choice(ENVIRONMENT_VARIANTS)
        
        authorized = base.copy()
        if authorized["environment"] == original:
            authorized["environment"] = original
        
        presented = base.copy()
        if presented["environment"] == original:
            presented["environment"] = variant
        else:
            # Toggle between production/staging
            presented["environment"] = "staging" if presented["environment"] == "production" else "production"
        
        scenarios.append({
            "scenario_id": f"arm_3_{i:03d}",
            "authorized_deployment": authorized,
            "presented_deployment": presented,
            "expected_decision": "DENY",
            "arm": 3,
            "mismatch_dimensions": ["environment"]
        })
    return scenarios


def generate_arm_4_version_mismatch(n=100) -> List[Dict[str, Any]]:
    """Arm 4: Version mismatch → DENY"""
    scenarios = []
    for i in range(n):
        base = random.choice(BASE_DEPLOYMENTS).copy()
        original, variant = random.choice(VERSION_VARIANTS)
        
        authorized = base.copy()
        if authorized["version"] == original:
            authorized["version"] = original
        
        presented = base.copy()
        if presented["version"] == original:
            presented["version"] = variant
        else:
            # Generic version bump
            presented["version"] = presented["version"] + ".1"
        
        scenarios.append({
            "scenario_id": f"arm_4_{i:03d}",
            "authorized_deployment": authorized,
            "presented_deployment": presented,
            "expected_decision": "DENY",
            "arm": 4,
            "mismatch_dimensions": ["version"]
        })
    return scenarios


def generate_arm_5_region_mismatch(n=100) -> List[Dict[str, Any]]:
    """Arm 5: Region mismatch → DENY"""
    scenarios = []
    for i in range(n):
        base = random.choice(BASE_DEPLOYMENTS).copy()
        original, variant = random.choice(REGION_VARIANTS)
        
        authorized = base.copy()
        if authorized["region"] == original:
            authorized["region"] = original
        
        presented = base.copy()
        if presented["region"] == original:
            presented["region"] = variant
        else:
            # Generic region change
            presented["region"] = "us-east-1" if presented["region"] != "us-east-1" else "eu-west-1"
        
        scenarios.append({
            "scenario_id": f"arm_5_{i:03d}",
            "authorized_deployment": authorized,
            "presented_deployment": presented,
            "expected_decision": "DENY",
            "arm": 5,
            "mismatch_dimensions": ["region"]
        })
    return scenarios


def generate_arm_6_method_mismatch(n=100) -> List[Dict[str, Any]]:
    """Arm 6: Deployment method mismatch → DENY"""
    scenarios = []
    for i in range(n):
        base = random.choice(BASE_DEPLOYMENTS).copy()
        original, variant = random.choice(METHOD_VARIANTS)
        
        authorized = base.copy()
        if authorized["deployment_method"] == original:
            authorized["deployment_method"] = original
        
        presented = base.copy()
        if presented["deployment_method"] == original:
            presented["deployment_method"] = variant
        else:
            # Generic method change
            methods = ["rolling-update", "blue-green", "canary", "recreate"]
            presented["deployment_method"] = random.choice([m for m in methods if m != presented["deployment_method"]])
        
        scenarios.append({
            "scenario_id": f"arm_6_{i:03d}",
            "authorized_deployment": authorized,
            "presented_deployment": presented,
            "expected_decision": "DENY",
            "arm": 6,
            "mismatch_dimensions": ["deployment_method"]
        })
    return scenarios


def generate_arm_7_multiple_mismatch(n=100) -> List[Dict[str, Any]]:
    """Arm 7: Multiple dimensions mismatch → DENY"""
    scenarios = []
    dimensions = ["service_name", "environment", "version", "region", "deployment_method"]
    
    for i in range(n):
        base = random.choice(BASE_DEPLOYMENTS).copy()
        authorized = base.copy()
        presented = base.copy()
        
        # Pick 2-4 dimensions to mismatch
        num_mismatches = random.randint(2, 4)
        mismatch_dims = random.sample(dimensions, num_mismatches)
        
        for dim in mismatch_dims:
            if dim == "service_name":
                presented[dim] = presented[dim] + "-alt"
            elif dim == "environment":
                presented[dim] = "staging" if presented[dim] == "production" else "production"
            elif dim == "version":
                presented[dim] = presented[dim] + ".99"
            elif dim == "region":
                presented[dim] = "us-east-1" if presented[dim] != "us-east-1" else "eu-west-1"
            elif dim == "deployment_method":
                methods = ["rolling-update", "blue-green"]
                presented[dim] = methods[0] if presented[dim] != methods[0] else methods[1]
        
        scenarios.append({
            "scenario_id": f"arm_7_{i:03d}",
            "authorized_deployment": authorized,
            "presented_deployment": presented,
            "expected_decision": "DENY",
            "arm": 7,
            "mismatch_dimensions": sorted(mismatch_dims)
        })
    return scenarios


def generate_arm_8_exact_match_stress(n=100) -> List[Dict[str, Any]]:
    """Arm 8: Exact match with edge cases → ALLOW"""
    edge_cases = [
        {
            "service_name": "microservice-with-very-long-hyphenated-name-v2",
            "environment": "production",
            "version": "sha256:9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08",
            "region": "ap-northeast-1",
            "deployment_method": "blue-green"
        },
        {
            "service_name": "svc_with_underscores",
            "environment": "Production-EU",
            "version": "v10.255.9999-beta.1+build.12345",
            "region": "us-gov-west-1",
            "deployment_method": "rolling-update"
        },
        {
            "service_name": "API.Gateway.Service",
            "environment": "staging-canary",
            "version": "2026.07.18.1900",
            "region": "cn-north-1",
            "deployment_method": "canary"
        },
        {
            "service_name": "a",
            "environment": "dev",
            "version": "0.0.1",
            "region": "local",
            "deployment_method": "recreate"
        }
    ]
    
    scenarios = []
    for i in range(n):
        base = random.choice(edge_cases)
        scenarios.append({
            "scenario_id": f"arm_8_{i:03d}",
            "authorized_deployment": base.copy(),
            "presented_deployment": base.copy(),
            "expected_decision": "ALLOW",
            "arm": 8,
            "mismatch_dimensions": []
        })
    return scenarios


def main():
    """Generate all 800 scenarios"""
    all_scenarios = []
    
    all_scenarios.extend(generate_arm_1_exact_match())
    all_scenarios.extend(generate_arm_2_service_mismatch())
    all_scenarios.extend(generate_arm_3_environment_mismatch())
    all_scenarios.extend(generate_arm_4_version_mismatch())
    all_scenarios.extend(generate_arm_5_region_mismatch())
    all_scenarios.extend(generate_arm_6_method_mismatch())
    all_scenarios.extend(generate_arm_7_multiple_mismatch())
    all_scenarios.extend(generate_arm_8_exact_match_stress())
    
    print(f"Generated {len(all_scenarios)} scenarios across 8 arms")
    
    # Save per-arm scenario files
    for arm in range(1, 9):
        arm_scenarios = [s for s in all_scenarios if s["arm"] == arm]
        output_file = f"results/arm_{arm}_scenarios.json"
        with open(output_file, "w") as f:
            json.dump(arm_scenarios, f, indent=2)
        print(f"Arm {arm}: {len(arm_scenarios)} scenarios → {output_file}")
    
    print("\n✅ Scenario generation complete")


if __name__ == "__main__":
    main()
