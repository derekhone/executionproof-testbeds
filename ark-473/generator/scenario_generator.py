"""
ARK-473 Scenario Generator
Financial Transaction · Exact-Action Binding

Generates 800 test scenarios (8 arms × 100 scenarios) testing exact 5-tuple binding:
(account_from, account_to, amount, currency, transaction_type)
"""

import json
import hashlib
import random
from pathlib import Path

# Set seed for reproducibility
random.seed(473)

# Sample values for each dimension
ACCOUNTS = [f"ACC-{i:06d}" for i in range(1000, 1100)]
AMOUNTS = [f"{amt:.2f}" for amt in [100.00, 500.00, 1000.00, 5000.00, 10000.00]]
CURRENCIES = ["USD", "EUR", "GBP", "JPY", "CHF"]
TRANSACTION_TYPES = ["WIRE", "ACH", "SWIFT", "SEPA", "DOMESTIC"]

def generate_transaction():
    """Generate a random financial transaction 5-tuple"""
    return {
        "account_from": random.choice(ACCOUNTS),
        "account_to": random.choice(ACCOUNTS),
        "amount": random.choice(AMOUNTS),
        "currency": random.choice(CURRENCIES),
        "transaction_type": random.choice(TRANSACTION_TYPES)
    }

def scenario_id(authorized, presented):
    """Generate deterministic scenario ID"""
    data = json.dumps({"auth": authorized, "pres": presented}, sort_keys=True)
    return hashlib.sha256(data.encode()).hexdigest()[:16]

def generate_arm_scenarios(arm_num, count=100):
    """Generate scenarios for a specific arm"""
    scenarios = []
    
    for _ in range(count):
        authorized = generate_transaction()
        
        if arm_num == 1:  # Exact match
            presented = authorized.copy()
            expected = "ALLOW"
            mismatch_dims = []
        elif arm_num == 2:  # Account From Mismatch
            presented = authorized.copy()
            presented["account_from"] = random.choice([a for a in ACCOUNTS if a != authorized["account_from"]])
            expected = "DENY"
            mismatch_dims = ["account_from"]
        elif arm_num == 3:  # Account To Mismatch
            presented = authorized.copy()
            presented["account_to"] = random.choice([a for a in ACCOUNTS if a != authorized["account_to"]])
            expected = "DENY"
            mismatch_dims = ["account_to"]
        elif arm_num == 4:  # Amount Mismatch
            presented = authorized.copy()
            presented["amount"] = random.choice([a for a in AMOUNTS if a != authorized["amount"]])
            expected = "DENY"
            mismatch_dims = ["amount"]
        elif arm_num == 5:  # Currency Mismatch
            presented = authorized.copy()
            presented["currency"] = random.choice([c for c in CURRENCIES if c != authorized["currency"]])
            expected = "DENY"
            mismatch_dims = ["currency"]
        elif arm_num == 6:  # Transaction Type Mismatch
            presented = authorized.copy()
            presented["transaction_type"] = random.choice([t for t in TRANSACTION_TYPES if t != authorized["transaction_type"]])
            expected = "DENY"
            mismatch_dims = ["transaction_type"]
        elif arm_num == 7:  # Multiple Dimension Mismatch
            presented = authorized.copy()
            num_mismatches = random.randint(2, 5)
            dims_to_mismatch = random.sample(["account_from", "account_to", "amount", "currency", "transaction_type"], num_mismatches)
            for dim in dims_to_mismatch:
                if dim == "account_from":
                    presented[dim] = random.choice([a for a in ACCOUNTS if a != authorized[dim]])
                elif dim == "account_to":
                    presented[dim] = random.choice([a for a in ACCOUNTS if a != authorized[dim]])
                elif dim == "amount":
                    presented[dim] = random.choice([a for a in AMOUNTS if a != authorized[dim]])
                elif dim == "currency":
                    presented[dim] = random.choice([c for c in CURRENCIES if c != authorized[dim]])
                elif dim == "transaction_type":
                    presented[dim] = random.choice([t for t in TRANSACTION_TYPES if t != authorized[dim]])
            expected = "DENY"
            mismatch_dims = dims_to_mismatch
        elif arm_num == 8:  # Exact match stress
            presented = authorized.copy()
            expected = "ALLOW"
            mismatch_dims = []
        
        scenario = {
            "scenario_id": scenario_id(authorized, presented),
            "authorized_transaction": authorized,
            "presented_transaction": presented,
            "expected_decision": expected,
            "arm": arm_num,
            "mismatch_dimensions": mismatch_dims
        }
        scenarios.append(scenario)
    
    return scenarios

def main():
    print("Generating ARK-473 test scenarios...")
    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)
    
    for arm_num in range(1, 9):
        scenarios = generate_arm_scenarios(arm_num)
        output_path = results_dir / f"arm_{arm_num}_scenarios.json"
        with open(output_path, 'w') as f:
            json.dump(scenarios, f, indent=2)
        print(f"Arm {arm_num}: {len(scenarios)} scenarios → {output_path}")
    
    print(f"\n✅ Generated 800 scenarios across 8 arms")

if __name__ == "__main__":
    main()
