#!/usr/bin/env python3
"""
ARK-453 Evidence Scenario Generator
Generates scenarios with 6-source evidence signals (ALLOW_SIGNAL/DENY_SIGNAL/UNKNOWN)
Includes conflict-effectiveness gate to prevent ARK-455-style no-op defects
"""
import random
import string
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

# Seed base: 20260717453 (YYYYMMDD + ARK number)
SEED_BASE = 20260717453

# Evidence signals
ALLOW_SIGNAL = "ALLOW_SIGNAL"
DENY_SIGNAL = "DENY_SIGNAL"
UNKNOWN = "UNKNOWN"

# Action types for randomization
ACTION_TYPES = ["transfer", "approve", "execute", "delegate", "revoke"]

# Arm definitions: (label, evidence_config_fn)
ARMS = {
    1: ("CONSENSUS-all-allow", lambda: _all_allow()),
    2: ("CONSENSUS-all-deny", lambda: _all_deny()),
    3: ("CONFLICT-identity-policy", lambda: _conflict_identity_policy()),
    4: ("CONFLICT-risk-elevation", lambda: _conflict_risk()),
    5: ("CONFLICT-registry-revocation", lambda: _conflict_registry()),
    6: ("CONFLICT-approval-mismatch", lambda: _conflict_approval()),
    7: ("CONFLICT-temporal-inconsistency", lambda: _conflict_temporal()),
    8: ("AMBIGUOUS-missing-critical", lambda: _ambiguous_unknown()),
}


class ScenarioGenerator:
    """Generates evidence scenarios for ARK-453"""
    
    def __init__(self, seed: int):
        self.rng = random.Random(seed)
    
    def generate_scenario(self, arm: int, index: int) -> Dict:
        """Generate a single scenario for the given arm"""
        label, config_fn = ARMS[arm]
        
        # Generate randomized metadata
        requester_id = self._random_uuid()
        action_type = self.rng.choice(ACTION_TYPES)
        resource = self._random_resource()
        timestamp_utc = self._random_timestamp()
        
        # Generate evidence sources using arm-specific configuration
        evidence_sources = config_fn()
        
        # Add randomized metadata to each source
        for source_name in evidence_sources:
            evidence_sources[source_name]["metadata"] = self._random_metadata(source_name)
        
        scenario = {
            "scenario_id": f"arm-{arm}-{index:03d}",
            "arm": arm,
            "requester_id": requester_id,
            "action_type": action_type,
            "resource": resource,
            "timestamp_utc": timestamp_utc,
            "evidence_sources": evidence_sources
        }
        
        return scenario
    
    def generate_arm_scenarios(self, arm: int, count: int = 100) -> Tuple[List[Dict], Dict]:
        """Generate scenarios for an arm + audit trail"""
        scenarios = []
        for i in range(count):
            scenario = self.generate_scenario(arm, i)
            scenarios.append(scenario)
        
        label, _ = ARMS[arm]
        audit = {
            "arm": arm,
            "label": label,
            "count": count,
            "seed": SEED_BASE + arm
        }
        
        return scenarios, audit
    
    def _random_uuid(self) -> str:
        """Generate a random UUID-like string"""
        segments = [
            ''.join(self.rng.choices(string.hexdigits.lower(), k=8)),
            ''.join(self.rng.choices(string.hexdigits.lower(), k=4)),
            ''.join(self.rng.choices(string.hexdigits.lower(), k=4)),
            ''.join(self.rng.choices(string.hexdigits.lower(), k=4)),
            ''.join(self.rng.choices(string.hexdigits.lower(), k=12)),
        ]
        return '-'.join(segments)
    
    def _random_resource(self) -> str:
        """Generate a random resource identifier"""
        prefix = self.rng.choice(["res", "asset", "obj", "item"])
        suffix = ''.join(self.rng.choices(string.ascii_lowercase + string.digits, k=12))
        return f"{prefix}_{suffix}"
    
    def _random_timestamp(self) -> str:
        """Generate a random timestamp within the last 30 days"""
        days_ago = self.rng.randint(0, 30)
        hours_ago = self.rng.randint(0, 23)
        minutes_ago = self.rng.randint(0, 59)
        dt = datetime.utcnow() - timedelta(days=days_ago, hours=hours_ago, minutes=minutes_ago)
        return dt.isoformat() + "Z"
    
    def _random_metadata(self, source_name: str) -> Dict:
        """Generate randomized metadata for an evidence source"""
        meta = {
            "provider": f"{source_name}_provider_{self.rng.randint(1, 5)}",
            "version": f"{self.rng.randint(1, 3)}.{self.rng.randint(0, 9)}"
        }
        
        # Source-specific metadata
        if source_name == "risk":
            meta["risk_score"] = round(self.rng.uniform(0.0, 1.0), 3)
        elif source_name == "policy":
            meta["policy_id"] = f"pol_{self.rng.randint(1000, 9999)}"
        elif source_name == "registry":
            meta["registry_id"] = f"reg_{self.rng.randint(100, 999)}"
        elif source_name == "approval":
            meta["workflow_id"] = f"wf_{self.rng.randint(10000, 99999)}"
        
        return meta


# Arm-specific evidence configurations

def _all_allow() -> Dict:
    """Arm 1: All sources ALLOW"""
    return {
        "identity": {"signal": ALLOW_SIGNAL},
        "policy": {"signal": ALLOW_SIGNAL},
        "risk": {"signal": ALLOW_SIGNAL},
        "approval": {"signal": ALLOW_SIGNAL},
        "registry": {"signal": ALLOW_SIGNAL},
        "temporal": {"signal": ALLOW_SIGNAL}
    }


def _all_deny() -> Dict:
    """Arm 2: All sources DENY"""
    return {
        "identity": {"signal": DENY_SIGNAL},
        "policy": {"signal": DENY_SIGNAL},
        "risk": {"signal": DENY_SIGNAL},
        "approval": {"signal": DENY_SIGNAL},
        "registry": {"signal": DENY_SIGNAL},
        "temporal": {"signal": DENY_SIGNAL}
    }


def _conflict_identity_policy() -> Dict:
    """Arm 3: Identity and policy DENY, rest ALLOW"""
    return {
        "identity": {"signal": DENY_SIGNAL},
        "policy": {"signal": DENY_SIGNAL},
        "risk": {"signal": ALLOW_SIGNAL},
        "approval": {"signal": ALLOW_SIGNAL},
        "registry": {"signal": ALLOW_SIGNAL},
        "temporal": {"signal": ALLOW_SIGNAL}
    }


def _conflict_risk() -> Dict:
    """Arm 4: Risk DENY, rest ALLOW"""
    return {
        "identity": {"signal": ALLOW_SIGNAL},
        "policy": {"signal": ALLOW_SIGNAL},
        "risk": {"signal": DENY_SIGNAL},
        "approval": {"signal": ALLOW_SIGNAL},
        "registry": {"signal": ALLOW_SIGNAL},
        "temporal": {"signal": ALLOW_SIGNAL}
    }


def _conflict_registry() -> Dict:
    """Arm 5: Registry DENY, rest ALLOW"""
    return {
        "identity": {"signal": ALLOW_SIGNAL},
        "policy": {"signal": ALLOW_SIGNAL},
        "risk": {"signal": ALLOW_SIGNAL},
        "approval": {"signal": ALLOW_SIGNAL},
        "registry": {"signal": DENY_SIGNAL},
        "temporal": {"signal": ALLOW_SIGNAL}
    }


def _conflict_approval() -> Dict:
    """Arm 6: Approval DENY, rest ALLOW"""
    return {
        "identity": {"signal": ALLOW_SIGNAL},
        "policy": {"signal": ALLOW_SIGNAL},
        "risk": {"signal": ALLOW_SIGNAL},
        "approval": {"signal": DENY_SIGNAL},
        "registry": {"signal": ALLOW_SIGNAL},
        "temporal": {"signal": ALLOW_SIGNAL}
    }


def _conflict_temporal() -> Dict:
    """Arm 7: Temporal DENY, rest ALLOW"""
    return {
        "identity": {"signal": ALLOW_SIGNAL},
        "policy": {"signal": ALLOW_SIGNAL},
        "risk": {"signal": ALLOW_SIGNAL},
        "approval": {"signal": ALLOW_SIGNAL},
        "registry": {"signal": ALLOW_SIGNAL},
        "temporal": {"signal": DENY_SIGNAL}
    }


def _ambiguous_unknown() -> Dict:
    """Arm 8: One or more sources UNKNOWN, rest mixed"""
    # For simplicity and consistency: 2 UNKNOWN, 2 ALLOW, 2 DENY
    return {
        "identity": {"signal": UNKNOWN},
        "policy": {"signal": ALLOW_SIGNAL},
        "risk": {"signal": DENY_SIGNAL},
        "approval": {"signal": UNKNOWN},
        "registry": {"signal": ALLOW_SIGNAL},
        "temporal": {"signal": DENY_SIGNAL}
    }


# Conflict-effectiveness oracle

def conflict_effective(scenario: Dict, arm: int) -> Tuple[bool, str]:
    """
    Check if a scenario genuinely encodes its arm's conflict/consensus class.
    Returns (is_effective, reason).
    
    Prevents ARK-455-style no-op defects where a test case appears to encode
    a condition but is mathematically inert.
    """
    sources = scenario["evidence_sources"]
    signals = [sources[name]["signal"] for name in sources]
    
    # Count signal types
    allow_count = signals.count(ALLOW_SIGNAL)
    deny_count = signals.count(DENY_SIGNAL)
    unknown_count = signals.count(UNKNOWN)
    
    if arm == 1:
        # CONSENSUS-all-allow: all 6 should be ALLOW
        if allow_count == 6 and deny_count == 0 and unknown_count == 0:
            return (True, "all-allow consensus valid")
        else:
            return (False, f"arm 1 expects all ALLOW, got {allow_count} ALLOW, {deny_count} DENY, {unknown_count} UNKNOWN")
    
    elif arm == 2:
        # CONSENSUS-all-deny: all 6 should be DENY
        if deny_count == 6 and allow_count == 0 and unknown_count == 0:
            return (True, "all-deny consensus valid")
        else:
            return (False, f"arm 2 expects all DENY, got {allow_count} ALLOW, {deny_count} DENY, {unknown_count} UNKNOWN")
    
    elif arm in [3, 4, 5, 6, 7]:
        # CONFLICT arms: must have at least 1 ALLOW and 1 DENY (no UNKNOWN)
        if allow_count >= 1 and deny_count >= 1 and unknown_count == 0:
            return (True, f"conflict valid: {allow_count} ALLOW, {deny_count} DENY")
        else:
            return (False, f"arm {arm} expects conflict (ALLOW+DENY, no UNKNOWN), got {allow_count} ALLOW, {deny_count} DENY, {unknown_count} UNKNOWN")
    
    elif arm == 8:
        # AMBIGUOUS: must have at least 1 UNKNOWN
        if unknown_count >= 1:
            return (True, f"ambiguous valid: {unknown_count} UNKNOWN")
        else:
            return (False, f"arm 8 expects at least 1 UNKNOWN, got {unknown_count}")
    
    else:
        return (False, f"unknown arm {arm}")


# CLI for testing
if __name__ == "__main__":
    print("ARK-453 Scenario Generator Self-Test")
    print("=" * 60)
    
    # Test one scenario per arm
    all_effective = True
    for arm in range(1, 9):
        gen = ScenarioGenerator(SEED_BASE + arm)
        scenario = gen.generate_scenario(arm, 0)
        effective, reason = conflict_effective(scenario, arm)
        
        label, _ = ARMS[arm]
        status = "✓ PASS" if effective else "✗ FAIL"
        print(f"Arm {arm} ({label}): {status}")
        print(f"  → {reason}")
        
        if not effective:
            all_effective = False
    
    print("=" * 60)
    if all_effective:
        print("✓ All arms generate effective scenarios")
        exit(0)
    else:
        print("✗ Some arms generate ineffective scenarios")
        exit(1)
