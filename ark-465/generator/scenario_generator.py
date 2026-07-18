#!/usr/bin/env python3
"""
ARK-465 — Production Deployment · Dependency Loss (scenario generator).

Question: When a critical dependency (Policy Registry, Identity Provider, Signature
Verifier, Audit Logger) is UNAVAILABLE at execution time, does the gate fail safe
(HOLD — cannot confirm validity) rather than wrongly ALLOW?

Model: Each scenario has an deployment action tuple (exact-match, from ARK-458) plus a
`dependencies` dict showing which dependencies are AVAILABLE or UNAVAILABLE at
t_execution.

Decision logic:
  - If ALL critical dependencies are AVAILABLE → evaluate normally (ALLOW)
  - If ANY critical dependency is UNAVAILABLE → HOLD (cannot confirm validity, fail-safe)

8 arms × 100 scenarios = 800 decisions.
"""
import hashlib
import json
import random
from typing import Any, Dict

SEED_BASE = 20260718460

IAM_PRINCIPALS = [f"arn:aws:iam::{10**11 + i:012d}:user/svc-{i:04d}" for i in range(100)]
IAM_ROLES = ["ReadOnlyAuditor", "DataAnalyst", "DeploymentManager", "AdminFull",
             "SecurityOfficer", "BillingViewer", "NetworkEngineer", "DatabaseAdmin"]
IAM_ACCOUNTS = [f"{10**11 + i:012d}" for i in range(50)]
IAM_PERMISSION_SETS = [f"ps-{i:016x}" for i in range(50)]
IAM_CONDITIONS = [
    "region=us-east-1;mfa=true", "region=us-west-2;mfa=true",
    "region=eu-west-1;mfa=false", "region=*;mfa=true", "region=us-east-1;mfa=false"
]

# Critical dependencies
CRITICAL_DEPS = ["ServiceRegistry", "ConfigStore", "SecretVault", "DeploymentAuditor"]

def _hash_scenario_id(arm: int, idx: int) -> str:
    s = f"ARK-465-arm{arm}-{idx}"
    return hashlib.sha256(s.encode()).hexdigest()[:16]

def _rng_for_scenario(arm: int, idx: int) -> random.Random:
    seed = SEED_BASE + arm * 1000 + idx
    return random.Random(seed)

def _iam_action(rng: random.Random) -> Dict[str, str]:
    return {
        "principal": rng.choice(IAM_PRINCIPALS),
        "role": rng.choice(IAM_ROLES),
        "account": rng.choice(IAM_ACCOUNTS),
        "permission_set": rng.choice(IAM_PERMISSION_SETS),
        "condition": rng.choice(IAM_CONDITIONS),
    }

def _dependencies(rng: random.Random, arm: int) -> Dict[str, str]:
    """
    Generate dependency availability for the given arm.
    
    Returns: {"ServiceRegistry": "AVAILABLE"|"UNAVAILABLE", ...}
    """
    if arm == 1:
        # ARM 1: ALL-AVAILABLE → expect ALLOW
        return {dep: "AVAILABLE" for dep in CRITICAL_DEPS}
    
    elif arm == 2:
        # ARM 2: ServiceRegistry UNAVAILABLE → expect HOLD
        deps = {dep: "AVAILABLE" for dep in CRITICAL_DEPS}
        deps["ServiceRegistry"] = "UNAVAILABLE"
        return deps
    
    elif arm == 3:
        # ARM 3: ConfigStore UNAVAILABLE → expect HOLD
        deps = {dep: "AVAILABLE" for dep in CRITICAL_DEPS}
        deps["ConfigStore"] = "UNAVAILABLE"
        return deps
    
    elif arm == 4:
        # ARM 4: SecretVault UNAVAILABLE → expect HOLD
        deps = {dep: "AVAILABLE" for dep in CRITICAL_DEPS}
        deps["SecretVault"] = "UNAVAILABLE"
        return deps
    
    elif arm == 5:
        # ARM 5: DeploymentAuditor UNAVAILABLE → expect HOLD
        deps = {dep: "AVAILABLE" for dep in CRITICAL_DEPS}
        deps["DeploymentAuditor"] = "UNAVAILABLE"
        return deps
    
    elif arm == 6:
        # ARM 6: MULTIPLE deps UNAVAILABLE → expect HOLD
        deps = {dep: "AVAILABLE" for dep in CRITICAL_DEPS}
        # Randomly pick 2-3 deps to make unavailable
        unavailable_count = rng.randint(2, 3)
        unavailable_deps = rng.sample(CRITICAL_DEPS, unavailable_count)
        for dep in unavailable_deps:
            deps[dep] = "UNAVAILABLE"
        return deps
    
    elif arm == 7:
        # ARM 7: ALL-UNAVAILABLE (total outage) → expect HOLD
        return {dep: "UNAVAILABLE" for dep in CRITICAL_DEPS}
    
    elif arm == 8:
        # ARM 8: ALL-AVAILABLE (baseline recheck) → expect ALLOW
        return {dep: "AVAILABLE" for dep in CRITICAL_DEPS}
    
    return {}

def _dependency_gate_oracle(dependencies: Dict[str, str], arm: int) -> bool:
    """Anti-no-op oracle: verify the scenario genuinely encodes the arm's dependency state."""
    if arm in [1, 8]:
        # ALL-AVAILABLE
        return all(v == "AVAILABLE" for v in dependencies.values())
    elif arm == 2:
        # ServiceRegistry UNAVAILABLE, others available
        return (dependencies["ServiceRegistry"] == "UNAVAILABLE" and
                all(dependencies[d] == "AVAILABLE" for d in CRITICAL_DEPS if d != "ServiceRegistry"))
    elif arm == 3:
        # ConfigStore UNAVAILABLE, others available
        return (dependencies["ConfigStore"] == "UNAVAILABLE" and
                all(dependencies[d] == "AVAILABLE" for d in CRITICAL_DEPS if d != "ConfigStore"))
    elif arm == 4:
        # SecretVault UNAVAILABLE, others available
        return (dependencies["SecretVault"] == "UNAVAILABLE" and
                all(dependencies[d] == "AVAILABLE" for d in CRITICAL_DEPS if d != "SecretVault"))
    elif arm == 5:
        # DeploymentAuditor UNAVAILABLE, others available
        return (dependencies["DeploymentAuditor"] == "UNAVAILABLE" and
                all(dependencies[d] == "AVAILABLE" for d in CRITICAL_DEPS if d != "DeploymentAuditor"))
    elif arm == 6:
        # MULTIPLE UNAVAILABLE (≥2)
        unavailable_count = sum(1 for v in dependencies.values() if v == "UNAVAILABLE")
        return unavailable_count >= 2
    elif arm == 7:
        # ALL-UNAVAILABLE
        return all(v == "UNAVAILABLE" for v in dependencies.values())
    return False

def generate_scenario(arm: int, idx: int) -> Dict[str, Any]:
    rng = _rng_for_scenario(arm, idx)
    scenario_id = _hash_scenario_id(arm, idx)
    
    action = _iam_action(rng)
    dependencies = _dependencies(rng, arm)
    
    if not _dependency_gate_oracle(dependencies, arm):
        raise ValueError(f"Scenario arm={arm} idx={idx} failed dependency gate (no-op)")
    
    return {
        "scenario_id": scenario_id,
        "arm": arm,
        "authorization": {"binding": action},
        "execution": {"action": action},  # exact match
        "dependencies": dependencies
    }

def generate_arm(arm: int, n: int = 100) -> list:
    return [generate_scenario(arm, i) for i in range(n)]

if __name__ == "__main__":
    for a in range(1, 9):
        sc = generate_scenario(a, 0)
        unavailable = [k for k, v in sc["dependencies"].items() if v == "UNAVAILABLE"]
        print(f"ARM {a}: unavailable={unavailable or 'none'}")
