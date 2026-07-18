#!/usr/bin/env python3
"""
ARK-468 Scenario Generator — Database Destructive Query · Exact-Action Binding

Generates 800 test scenarios (8 arms × 100 scenarios) for database destructive query authorization.
"""

import json
import random
from typing import List, Dict, Any

# Set seed for reproducibility
random.seed(468_001)

# Base database query tuples
BASE_QUERIES = [
    {
        "database_name": "production_db",
        "table_name": "users",
        "operation": "DROP",
        "schema_version": "v2.3.1",
        "execution_mode": "transaction"
    },
    {
        "database_name": "analytics_db",
        "table_name": "events",
        "operation": "DELETE",
        "schema_version": "v1.8.5",
        "execution_mode": "direct"
    },
    {
        "database_name": "staging_db",
        "table_name": "temp_data",
        "operation": "TRUNCATE",
        "schema_version": "sha256:a3f5e9c12b",
        "execution_mode": "batch"
    },
    {
        "database_name": "production_db",
        "table_name": "audit_logs",
        "operation": "DELETE",
        "schema_version": "v4.2.0",
        "execution_mode": "transaction"
    },
    {
        "database_name": "test_db",
        "table_name": "test_results",
        "operation": "TRUNCATE",
        "schema_version": "v3.0.0-rc.2",
        "execution_mode": "direct"
    }
]


def generate_arm_1_exact_match(n: int) -> List[Dict[str, Any]]:
    """Arm 1: Exact match on all 5 dimensions → ALLOW"""
    scenarios = []
    for i in range(n):
        base = random.choice(BASE_QUERIES)
        scenarios.append({
            "scenario_id": f"arm1_exact_{i:03d}",
            "arm": 1,
            "arm_name": "Exact Match",
            "authorized_query": base.copy(),
            "presented_query": base.copy(),
            "expected_decision": "ALLOW"
        })
    return scenarios


def generate_arm_2_database_mismatch(n: int) -> List[Dict[str, Any]]:
    """Arm 2: Database name mismatch → DENY"""
    scenarios = []
    for i in range(n):
        base = random.choice(BASE_QUERIES).copy()
        authorized = base.copy()
        presented = base.copy()
        presented["database_name"] = presented["database_name"] + "_modified"
        
        scenarios.append({
            "scenario_id": f"arm2_db_mismatch_{i:03d}",
            "arm": 2,
            "arm_name": "Database Name Mismatch",
            "authorized_query": authorized,
            "presented_query": presented,
            "expected_decision": "DENY"
        })
    return scenarios


def generate_arm_3_table_mismatch(n: int) -> List[Dict[str, Any]]:
    """Arm 3: Table name mismatch → DENY"""
    scenarios = []
    for i in range(n):
        base = random.choice(BASE_QUERIES).copy()
        authorized = base.copy()
        presented = base.copy()
        presented["table_name"] = presented["table_name"] + "_backup"
        
        scenarios.append({
            "scenario_id": f"arm3_table_mismatch_{i:03d}",
            "arm": 3,
            "arm_name": "Table Name Mismatch",
            "authorized_query": authorized,
            "presented_query": presented,
            "expected_decision": "DENY"
        })
    return scenarios


def generate_arm_4_operation_mismatch(n: int) -> List[Dict[str, Any]]:
    """Arm 4: Operation mismatch → DENY"""
    scenarios = []
    operations = ["DROP", "DELETE", "TRUNCATE"]
    
    for i in range(n):
        base = random.choice(BASE_QUERIES).copy()
        authorized = base.copy()
        presented = base.copy()
        # Change to different operation
        presented["operation"] = random.choice([op for op in operations if op != presented["operation"]])
        
        scenarios.append({
            "scenario_id": f"arm4_op_mismatch_{i:03d}",
            "arm": 4,
            "arm_name": "Operation Mismatch",
            "authorized_query": authorized,
            "presented_query": presented,
            "expected_decision": "DENY"
        })
    return scenarios


def generate_arm_5_schema_mismatch(n: int) -> List[Dict[str, Any]]:
    """Arm 5: Schema version mismatch → DENY"""
    scenarios = []
    for i in range(n):
        base = random.choice(BASE_QUERIES).copy()
        authorized = base.copy()
        presented = base.copy()
        presented["schema_version"] = presented["schema_version"] + ".1"
        
        scenarios.append({
            "scenario_id": f"arm5_schema_mismatch_{i:03d}",
            "arm": 5,
            "arm_name": "Schema Version Mismatch",
            "authorized_query": authorized,
            "presented_query": presented,
            "expected_decision": "DENY"
        })
    return scenarios


def generate_arm_6_mode_mismatch(n: int) -> List[Dict[str, Any]]:
    """Arm 6: Execution mode mismatch → DENY"""
    scenarios = []
    modes = ["direct", "transaction", "batch"]
    
    for i in range(n):
        base = random.choice(BASE_QUERIES).copy()
        authorized = base.copy()
        presented = base.copy()
        presented["execution_mode"] = random.choice([m for m in modes if m != presented["execution_mode"]])
        
        scenarios.append({
            "scenario_id": f"arm6_mode_mismatch_{i:03d}",
            "arm": 6,
            "arm_name": "Execution Mode Mismatch",
            "authorized_query": authorized,
            "presented_query": presented,
            "expected_decision": "DENY"
        })
    return scenarios


def generate_arm_7_multiple_mismatch(n: int) -> List[Dict[str, Any]]:
    """Arm 7: Multiple dimension mismatches → DENY"""
    scenarios = []
    dimensions = ["database_name", "table_name", "operation", "schema_version", "execution_mode"]
    
    for i in range(n):
        base = random.choice(BASE_QUERIES).copy()
        authorized = base.copy()
        presented = base.copy()
        
        # Mismatch 2-3 dimensions
        num_mismatches = random.randint(2, 3)
        mismatch_dims = random.sample(dimensions, num_mismatches)
        
        for dim in mismatch_dims:
            if dim == "database_name":
                presented[dim] = presented[dim] + "_alt"
            elif dim == "table_name":
                presented[dim] = presented[dim] + "_copy"
            elif dim == "operation":
                ops = ["DROP", "DELETE", "TRUNCATE"]
                presented[dim] = random.choice([o for o in ops if o != presented[dim]])
            elif dim == "schema_version":
                presented[dim] = presented[dim] + ".modified"
            elif dim == "execution_mode":
                modes = ["direct", "transaction", "batch"]
                presented[dim] = random.choice([m for m in modes if m != presented[dim]])
        
        scenarios.append({
            "scenario_id": f"arm7_multi_mismatch_{i:03d}",
            "arm": 7,
            "arm_name": "Multiple Mismatch",
            "authorized_query": authorized,
            "presented_query": presented,
            "expected_decision": "DENY"
        })
    return scenarios


def generate_arm_8_exact_match_stress(n: int) -> List[Dict[str, Any]]:
    """Arm 8: Exact match stress test (high variety) → ALLOW"""
    scenarios = []
    for i in range(n):
        base = random.choice(BASE_QUERIES)
        scenarios.append({
            "scenario_id": f"arm8_exact_stress_{i:03d}",
            "arm": 8,
            "arm_name": "Exact Match Stress",
            "authorized_query": base.copy(),
            "presented_query": base.copy(),
            "expected_decision": "ALLOW"
        })
    return scenarios


def main():
    """Generate all 800 scenarios (8 arms × 100 scenarios)"""
    print("Generating ARK-468 test scenarios...")
    print("=" * 70)
    
    all_scenarios = []
    
    # Generate each arm
    all_scenarios.extend(generate_arm_1_exact_match(100))
    all_scenarios.extend(generate_arm_2_database_mismatch(100))
    all_scenarios.extend(generate_arm_3_table_mismatch(100))
    all_scenarios.extend(generate_arm_4_operation_mismatch(100))
    all_scenarios.extend(generate_arm_5_schema_mismatch(100))
    all_scenarios.extend(generate_arm_6_mode_mismatch(100))
    all_scenarios.extend(generate_arm_7_multiple_mismatch(100))
    all_scenarios.extend(generate_arm_8_exact_match_stress(100))
    
    print(f"Generated {len(all_scenarios)} scenarios across 8 arms")
    
    # Group by arm and save
    for arm_num in range(1, 9):
        arm_scenarios = [s for s in all_scenarios if s["arm"] == arm_num]
        output_file = f"results/arm_{arm_num}_scenarios.json"
        with open(output_file, "w") as f:
            json.dump(arm_scenarios, f, indent=2)
        print(f"  Arm {arm_num}: {len(arm_scenarios)} scenarios → {output_file}")
    
    print(f"\n✅ All scenarios generated")


if __name__ == "__main__":
    main()
