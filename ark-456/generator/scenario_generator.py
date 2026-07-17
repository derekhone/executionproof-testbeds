#!/usr/bin/env python3
"""
ARK-456 Scenario Generator — Fail-Closed Dependency Loss
Generates authorization scenarios under degraded dependency conditions.
"""
import json
import random
from typing import List, Dict, Any

SEED_BASE = 20260717456  # ARK-456 base seed
DEPS = ["identity_provider", "policy_registry", "evidence_schema", 
        "clock_source", "signature_key", "audit_store"]

class ScenarioGenerator:
    def __init__(self, seed: int):
        self.rng = random.Random(seed)
    
    def generate_scenarios(self, arm: int, count: int = 100) -> List[Dict[str, Any]]:
        """Generate {count} scenarios for the given arm."""
        scenarios = []
        for i in range(count):
            scenario_id = f"ARK456-ARM{arm}-{i:03d}"
            auth_req = self._gen_auth_request()
            dep_state = self._gen_dependency_state(arm)
            scenarios.append({
                "scenario_id": scenario_id,
                "arm": arm,
                "authorization_request": auth_req,
                "dependency_state": dep_state
            })
        return scenarios
    
    def _gen_auth_request(self) -> Dict[str, Any]:
        """Generate a baseline authorization request (valid under healthy conditions)."""
        actions = ["transfer", "approve", "delegate", "execute"]
        return {
            "action": self.rng.choice(actions),
            "subject": f"agent-{self.rng.randint(1, 10)}",
            "resource": f"wallet-{self.rng.randint(1, 5)}",
            "context": {
                "amount": self.rng.uniform(10, 1000),
                "destination": f"0x{self.rng.randint(1000, 9999):04x}",
                "meta": {}
            }
        }
    
    def _gen_dependency_state(self, arm: int) -> Dict[str, str]:
        """
        Generate dependency state for the given arm.
        Arm 1: all available
        Arm 2-7: one specific dep unavailable/corrupted, rest available
        Arm 8: 3+ deps degraded
        """
        if arm == 1:
            # BASELINE-healthy: all available
            return {dep: "available" for dep in DEPS}
        
        elif arm == 2:
            # IDENTITY-provider-unavailable
            return {dep: "available" if dep != "identity_provider" else "unavailable" for dep in DEPS}
        
        elif arm == 3:
            # POLICY-registry-unavailable
            return {dep: "available" if dep != "policy_registry" else "unavailable" for dep in DEPS}
        
        elif arm == 4:
            # EVIDENCE-schema-corrupted
            return {dep: "available" if dep != "evidence_schema" else "corrupted" for dep in DEPS}
        
        elif arm == 5:
            # CLOCK-source-unreachable
            return {dep: "available" if dep != "clock_source" else "unavailable" for dep in DEPS}
        
        elif arm == 6:
            # SIGNATURE-key-missing
            return {dep: "available" if dep != "signature_key" else "unavailable" for dep in DEPS}
        
        elif arm == 7:
            # AUDIT-store-unreachable
            return {dep: "available" if dep != "audit_store" else "unavailable" for dep in DEPS}
        
        elif arm == 8:
            # MULTIPLE-deps-degraded: at least 3 degraded
            degraded_count = self.rng.randint(3, 6)
            degraded = self.rng.sample(DEPS, degraded_count)
            state = {}
            for dep in DEPS:
                if dep in degraded:
                    state[dep] = self.rng.choice(["unavailable", "corrupted"])
                else:
                    state[dep] = "available"
            return state
        
        else:
            raise ValueError(f"Invalid arm {arm}")


def dependency_loss_effective(scenario: Dict[str, Any], arm: int) -> tuple[bool, str]:
    """
    Structural oracle: verify the scenario genuinely encodes the arm's dependency condition.
    
    Returns (is_effective, reason_if_not)
    """
    dep_state = scenario["dependency_state"]
    
    if arm == 1:
        # BASELINE-healthy: all must be "available"
        if all(dep_state[d] == "available" for d in DEPS):
            return (True, "")
        return (False, "Arm 1 scenario has degraded dependencies")
    
    elif arm == 2:
        # IDENTITY-provider-unavailable: identity must be unavailable, rest available
        if dep_state["identity_provider"] != "available":
            if all(dep_state[d] == "available" for d in DEPS if d != "identity_provider"):
                return (True, "")
            return (False, "Other dependencies not all available")
        return (False, "identity_provider is available (should be degraded)")
    
    elif arm == 3:
        # POLICY-registry-unavailable
        if dep_state["policy_registry"] != "available":
            if all(dep_state[d] == "available" for d in DEPS if d != "policy_registry"):
                return (True, "")
            return (False, "Other dependencies not all available")
        return (False, "policy_registry is available (should be degraded)")
    
    elif arm == 4:
        # EVIDENCE-schema-corrupted
        if dep_state["evidence_schema"] != "available":
            if all(dep_state[d] == "available" for d in DEPS if d != "evidence_schema"):
                return (True, "")
            return (False, "Other dependencies not all available")
        return (False, "evidence_schema is available (should be degraded)")
    
    elif arm == 5:
        # CLOCK-source-unreachable
        if dep_state["clock_source"] != "available":
            if all(dep_state[d] == "available" for d in DEPS if d != "clock_source"):
                return (True, "")
            return (False, "Other dependencies not all available")
        return (False, "clock_source is available (should be degraded)")
    
    elif arm == 6:
        # SIGNATURE-key-missing
        if dep_state["signature_key"] != "available":
            if all(dep_state[d] == "available" for d in DEPS if d != "signature_key"):
                return (True, "")
            return (False, "Other dependencies not all available")
        return (False, "signature_key is available (should be degraded)")
    
    elif arm == 7:
        # AUDIT-store-unreachable
        if dep_state["audit_store"] != "available":
            if all(dep_state[d] == "available" for d in DEPS if d != "audit_store"):
                return (True, "")
            return (False, "Other dependencies not all available")
        return (False, "audit_store is available (should be degraded)")
    
    elif arm == 8:
        # MULTIPLE-deps-degraded: at least 3 not available
        degraded_count = sum(1 for d in DEPS if dep_state[d] != "available")
        if degraded_count >= 3:
            return (True, "")
        return (False, f"Only {degraded_count} dependencies degraded (need ≥3)")
    
    else:
        return (False, f"Unknown arm {arm}")


# Arm definitions
ARMS = {
    1: {"label": "BASELINE-healthy", "expected": "ALLOW"},
    2: {"label": "IDENTITY-provider-unavailable", "expected": "DENY"},
    3: {"label": "POLICY-registry-unavailable", "expected": "DENY"},
    4: {"label": "EVIDENCE-schema-corrupted", "expected": "DENY"},
    5: {"label": "CLOCK-source-unreachable", "expected": "DENY"},
    6: {"label": "SIGNATURE-key-missing", "expected": "DENY"},
    7: {"label": "AUDIT-store-unreachable", "expected": "DENY"},
    8: {"label": "MULTIPLE-deps-degraded", "expected": "DENY"},
}


if __name__ == "__main__":
    # Self-test: generate 10 scenarios per arm and verify effectiveness
    print("=== ARK-456 Generator Self-Test ===\n")
    for arm in range(1, 9):
        gen = ScenarioGenerator(SEED_BASE + arm)
        scenarios = gen.generate_scenarios(arm, count=10)
        failures = []
        for sc in scenarios:
            is_eff, reason = dependency_loss_effective(sc, arm)
            if not is_eff:
                failures.append((sc["scenario_id"], reason))
        
        if failures:
            print(f"ARM {arm} ({ARMS[arm]['label']}): FAIL")
            for sid, reason in failures:
                print(f"  {sid}: {reason}")
        else:
            print(f"ARM {arm} ({ARMS[arm]['label']}): OK (10/10 effective)")
    
    print("\nSelf-test complete.")
