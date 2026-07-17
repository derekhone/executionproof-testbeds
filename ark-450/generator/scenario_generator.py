#!/usr/bin/env python3
"""
ARK-450 Substitution Attack Scenario Generator
Generates test scenarios for action substitution attacks with effectiveness oracle.
"""

import json
import random
import copy
from datetime import datetime, timedelta

# Fixed seed for reproducibility
SEED = "450_substitution_attack_2026"
random.seed(SEED)

# Configuration
OPERATIONS = ["transfer", "read", "write", "delete", "approve", "deploy", "execute", "access"]
RESOURCE_TYPES = ["file", "account", "token", "database", "api", "contract", "service"]
PRINCIPALS = [f"agent_{chr(97+i)}" for i in range(26)]  # agent_a to agent_z
TARGETS_BASE = [
    "accounts/alice", "accounts/bob", "accounts/charlie",
    "data/public", "data/private", "data/confidential",
    "contracts/main", "contracts/backup",
    "services/auth", "services/payment",
    "files/document", "files/config"
]
CONTEXTS = ["routine_operation", "emergency_access", "scheduled_task", "manual_request"]
SOURCES = ["workflow_engine", "admin_console", "api_gateway", "scheduled_job"]

def generate_base_action(idx):
    """Generate a baseline action with random but valid parameters."""
    operation = random.choice(OPERATIONS)
    principal = random.choice(PRINCIPALS)
    target = random.choice(TARGETS_BASE)
    
    # Amount based on operation type
    if operation in ["transfer", "approve"]:
        amount_usd = round(random.uniform(100, 50000), 2)
    else:
        amount_usd = 0
    
    resource_type = random.choice(RESOURCE_TYPES)
    
    base_time = datetime(2026, 7, 17, 12, 0, 0) + timedelta(minutes=idx)
    timestamp = base_time.isoformat() + "Z"
    
    context = random.choice(CONTEXTS)
    source = random.choice(SOURCES)
    
    return {
        "operation": operation,
        "principal": principal,
        "target": target,
        "amount_usd": amount_usd,
        "resource_type": resource_type,
        "metadata": {
            "timestamp": timestamp,
            "context": context,
            "source": source
        }
    }

def apply_substitution(approved_action, substitution_type):
    """Apply a substitution attack to an approved action."""
    executed_action = copy.deepcopy(approved_action)
    
    if substitution_type == "none":
        # Exact match - no modification
        return executed_action
    
    elif substitution_type == "destination":
        # Swap target to a different destination
        alt_targets = [t for t in TARGETS_BASE if t != approved_action["target"]]
        executed_action["target"] = random.choice(alt_targets)
    
    elif substitution_type == "amount":
        # Inflate amount (if financial operation)
        if approved_action["amount_usd"] > 0:
            multiplier = random.uniform(2.0, 100.0)
            executed_action["amount_usd"] = round(approved_action["amount_usd"] * multiplier, 2)
        else:
            # For non-financial, add an amount
            executed_action["amount_usd"] = round(random.uniform(1000, 10000), 2)
    
    elif substitution_type == "identity":
        # Swap principal
        alt_principals = [p for p in PRINCIPALS if p != approved_action["principal"]]
        executed_action["principal"] = random.choice(alt_principals)
    
    elif substitution_type == "tool":
        # Swap operation or resource type
        if random.random() < 0.5:
            alt_ops = [op for op in OPERATIONS if op != approved_action["operation"]]
            executed_action["operation"] = random.choice(alt_ops)
        else:
            alt_types = [rt for rt in RESOURCE_TYPES if rt != approved_action["resource_type"]]
            executed_action["resource_type"] = random.choice(alt_types)
    
    elif substitution_type == "partial_path":
        # Modify target with path extension or truncation
        original_target = approved_action["target"]
        if random.random() < 0.5:
            # Extend path
            extensions = ["_backup", "/sensitive", "/admin", "_v2", "/archive"]
            executed_action["target"] = original_target + random.choice(extensions)
        else:
            # Modify slightly
            if "/" in original_target:
                base, suffix = original_target.rsplit("/", 1)
                executed_action["target"] = f"{base}/{suffix}_modified"
            else:
                executed_action["target"] = original_target + "_alt"
    
    elif substitution_type == "hash_collision":
        # Create similar-looking target (prefix match attempt)
        original_target = approved_action["target"]
        # Keep prefix, modify suffix subtly
        if "/" in original_target:
            base, suffix = original_target.rsplit("/", 1)
            new_suffix = suffix + chr(ord(suffix[0]) + 1) if suffix else "x"
            executed_action["target"] = f"{base}/{new_suffix}"
        else:
            executed_action["target"] = original_target + "x"
    
    elif substitution_type == "metadata":
        # Swap metadata fields while keeping core action same
        executed_action["metadata"]["timestamp"] = (
            datetime.fromisoformat(approved_action["metadata"]["timestamp"].replace("Z", "")) 
            + timedelta(hours=1)
        ).isoformat() + "Z"
        alt_contexts = [c for c in CONTEXTS if c != approved_action["metadata"]["context"]]
        executed_action["metadata"]["context"] = random.choice(alt_contexts)
        alt_sources = [s for s in SOURCES if s != approved_action["metadata"]["source"]]
        executed_action["metadata"]["source"] = random.choice(alt_sources)
    
    return executed_action

def is_substitution_effective(scenario):
    """
    Effectiveness oracle: Verify that substitution scenarios actually contain a substitution.
    Returns True if the scenario correctly represents its substitution_type.
    """
    approved = scenario["approved_action"]
    executed = scenario["executed_action"]
    sub_type = scenario["substitution_type"]
    
    if sub_type == "none":
        # Baseline: must be exact match
        return approved == executed
    else:
        # Attack arms: must differ somewhere
        return approved != executed

def generate_arm_scenarios(arm_id, count=100):
    """Generate scenarios for a specific arm."""
    scenarios = []
    
    # Arm-to-substitution-type mapping
    arm_substitution_map = {
        1: "none",              # Baseline - exact match
        2: "destination",       # Destination swap
        3: "amount",            # Amount inflation
        4: "identity",          # Identity swap
        5: "tool",              # Tool/resource swap
        6: "partial_path",      # Partial path match
        7: "metadata",          # Metadata manipulation
        8: "hash_collision"     # Hash-prefix collision attempt
    }
    
    substitution_type = arm_substitution_map[arm_id]
    
    for i in range(count):
        approved_action = generate_base_action(arm_id * 1000 + i)
        executed_action = apply_substitution(approved_action, substitution_type)
        
        scenario = {
            "scenario_id": f"sub_{arm_id * 1000 + i}_arm{arm_id}_{substitution_type}",
            "approved_action": approved_action,
            "executed_action": executed_action,
            "substitution_type": substitution_type,
            "arm_id": arm_id
        }
        
        scenarios.append(scenario)
    
    return scenarios

def generate_all_scenarios(scenarios_per_arm=100):
    """Generate all scenarios for all 8 arms."""
    all_scenarios = []
    
    for arm_id in range(1, 9):
        arm_scenarios = generate_arm_scenarios(arm_id, scenarios_per_arm)
        all_scenarios.extend(arm_scenarios)
    
    return all_scenarios

def validate_scenarios(scenarios):
    """Run effectiveness oracle on all scenarios."""
    results = {
        "total": len(scenarios),
        "effective": 0,
        "ineffective": 0,
        "by_arm": {}
    }
    
    for arm_id in range(1, 9):
        results["by_arm"][arm_id] = {"effective": 0, "ineffective": 0}
    
    for scenario in scenarios:
        is_effective = is_substitution_effective(scenario)
        arm_id = scenario["arm_id"]
        
        if is_effective:
            results["effective"] += 1
            results["by_arm"][arm_id]["effective"] += 1
        else:
            results["ineffective"] += 1
            results["by_arm"][arm_id]["ineffective"] += 1
    
    return results

if __name__ == "__main__":
    print("ARK-450 Substitution Attack Scenario Generator")
    print("=" * 60)
    print(f"Seed: {SEED}")
    print(f"Generating 8 arms × 100 scenarios = 800 total\n")
    
    scenarios = generate_all_scenarios(scenarios_per_arm=100)
    
    print(f"Generated {len(scenarios)} scenarios")
    print("\nRunning effectiveness oracle...")
    validation = validate_scenarios(scenarios)
    
    print(f"\nEffectiveness Results:")
    print(f"  Total: {validation['total']}")
    print(f"  Effective: {validation['effective']}")
    print(f"  Ineffective: {validation['ineffective']}")
    print(f"\nPer-arm breakdown:")
    for arm_id in range(1, 9):
        arm_data = validation["by_arm"][arm_id]
        print(f"  Arm {arm_id}: {arm_data['effective']}/100 effective")
    
    # Save scenarios
    output_path = "scenarios.json"
    with open(output_path, "w") as f:
        json.dump(scenarios, f, indent=2)
    print(f"\nScenarios saved to {output_path}")
    
    # Check for any ineffective scenarios (should be 0)
    if validation["ineffective"] > 0:
        print(f"\n⚠️  WARNING: {validation['ineffective']} ineffective scenarios detected!")
        print("This indicates a generator bug. Review and fix before execution.")
    else:
        print("\n✅ All scenarios pass effectiveness oracle.")
