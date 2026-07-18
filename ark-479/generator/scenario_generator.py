#!/usr/bin/env python3
"""
ARK-479 — Production API Rate Limit · Revocation At Execution (scenario generator).

Combines ARK-458's 5-dim API rate limit action tuple with ARK-451's timeline/revocation model.
Question: When an IAM role-grant authorization is APPROVED, then REVOKED before
execution, does the gate refuse to authorize the grant?

Timeline model:
  - t_approval: when the API rate limit is approved (≥ 0)
  - t_execution: when the grant is attempted (> t_approval)
  - revocation: {t_revoke, propagation_delay, reason} or null
  - reauthorization: {t_reauth, valid} or null

Decision logic at t_execution:
  1. If revocation is null → ALLOW (valid throughout)
  2. Compute eff = t_revoke + propagation_delay
  3. If reauth exists, valid, and t_revoke < t_reauth ≤ t_execution → ALLOW
  4. Else if eff ≤ t_execution → DENY (revoked before execution, fail-closed)
  5. Else if t_revoke ≤ t_execution < eff → HOLD (in-flight, fail-safe)
  6. Else (t_revoke > t_execution) → ALLOW (revoked after execution)

8 arms × 100 scenarios = 800 decisions.
"""
import hashlib
import json
import random
from typing import Any, Dict, Optional

# Deterministic seed base (date + ARK-ID encoded)
SEED_BASE = 20260718459

# API rate limit action dimensions (from ARK-458)
IAM_PRINCIPALS = [
    f"arn:aws:iam::{10**11 + i:012d}:user/svc-{i:04d}"
    for i in range(100)
]
IAM_ROLES = [
    "ReadOnlyAuditor", "DataAnalyst", "API Rate LimitManager", "AdminFull",
    "SecurityOfficer", "BillingViewer", "NetworkEngineer", "DatabaseAdmin"
]
IAM_ACCOUNTS = [f"{10**11 + i:012d}" for i in range(50)]
IAM_PERMISSION_SETS = [f"ps-{i:016x}" for i in range(50)]
IAM_CONDITIONS = [
    "region=us-east-1;mfa=true",
    "region=us-west-2;mfa=true",
    "region=eu-west-1;mfa=false",
    "region=*;mfa=true",
    "region=us-east-1;mfa=false"
]

REVOKE_REASONS = [
    "credential-compromise", "employee-termination", "api-key-rotation",
    "emergency-shutdown", "policy-change", "account-suspended"
]

def _hash_scenario_id(arm: int, idx: int) -> str:
    """Deterministic scenario ID."""
    s = f"ARK-479-arm{arm}-{idx}"
    return hashlib.sha256(s.encode()).hexdigest()[:16]

def _rng_for_scenario(arm: int, idx: int) -> random.Random:
    """Deterministic RNG per scenario."""
    seed = SEED_BASE + arm * 1000 + idx
    return random.Random(seed)

def _iam_action(rng: random.Random) -> Dict[str, str]:
    """Generate a random API rate limit action tuple."""
    return {
        "principal": rng.choice(IAM_PRINCIPALS),
        "role": rng.choice(IAM_ROLES),
        "account": rng.choice(IAM_ACCOUNTS),
        "permission_set": rng.choice(IAM_PERMISSION_SETS),
        "condition": rng.choice(IAM_CONDITIONS),
    }

def _timeline(rng: random.Random, arm: int) -> Dict[str, Any]:
    """
    Generate timeline + revocation for the given arm.
    
    Returns: {t_approval, t_execution, multistep, revocation, reauthorization}
    """
    t_approval = rng.uniform(0, 10)  # approval at random time in [0,10]
    exec_delay = rng.uniform(5, 30)  # execution 5–30s after approval
    t_execution = t_approval + exec_delay
    
    multistep = rng.choice([True, False])
    
    revocation: Optional[Dict[str, Any]] = None
    reauthorization: Optional[Dict[str, Any]] = None
    
    if arm == 1:
        # ARM 1: VALID-throughout (no revocation)
        pass
    
    elif arm == 2:
        # ARM 2: REVOKED-before-approval (eff < t_approval)
        # Revoke strictly before approval
        propagation_delay = rng.uniform(1, 5)
        t_revoke = t_approval - rng.uniform(propagation_delay + 0.1, propagation_delay + 10)
        revocation = {
            "t_revoke": t_revoke,
            "propagation_delay": propagation_delay,
            "reason": rng.choice(REVOKE_REASONS)
        }
    
    elif arm == 3:
        # ARM 3: REVOKED-after-approval-before-execution (t_approval ≤ t_revoke, eff ≤ t_execution)
        propagation_delay = rng.uniform(1, 5)
        # Revoke after approval, effective before execution
        t_revoke = rng.uniform(t_approval, t_execution - propagation_delay - 0.1)
        revocation = {
            "t_revoke": t_revoke,
            "propagation_delay": propagation_delay,
            "reason": rng.choice(REVOKE_REASONS)
        }
    
    elif arm == 4:
        # ARM 4: REVOKED-during-multistep (multistep=true, eff ≤ t_execution)
        multistep = True
        propagation_delay = rng.uniform(1, 5)
        t_revoke = rng.uniform(t_approval, t_execution - propagation_delay - 0.1)
        revocation = {
            "t_revoke": t_revoke,
            "propagation_delay": propagation_delay,
            "reason": rng.choice(REVOKE_REASONS)
        }
    
    elif arm in [5, 7]:
        # ARM 5,7: IN-FLIGHT-at-execution (t_revoke ≤ t_execution < eff)
        propagation_delay = rng.uniform(2, 10)
        # Revoke before execution, but not yet effective
        t_revoke = rng.uniform(t_approval, t_execution - 0.1)
        # Ensure eff > t_execution
        while t_revoke + propagation_delay <= t_execution:
            propagation_delay += 1
        revocation = {
            "t_revoke": t_revoke,
            "propagation_delay": propagation_delay,
            "reason": rng.choice(REVOKE_REASONS)
        }
    
    elif arm == 6:
        # ARM 6: REVOKED-then-REAUTHORIZED (t_revoke < t_reauth ≤ t_execution)
        propagation_delay = rng.uniform(1, 3)
        t_revoke = rng.uniform(t_approval, t_execution - 5)
        t_reauth = rng.uniform(t_revoke + 0.1, t_execution)
        revocation = {
            "t_revoke": t_revoke,
            "propagation_delay": propagation_delay,
            "reason": rng.choice(REVOKE_REASONS)
        }
        reauthorization = {
            "t_reauth": t_reauth,
            "valid": True
        }
    
    elif arm == 8:
        # ARM 8: REVOKED-after-execution (t_revoke > t_execution)
        propagation_delay = rng.uniform(1, 5)
        t_revoke = t_execution + rng.uniform(0.1, 10)
        revocation = {
            "t_revoke": t_revoke,
            "propagation_delay": propagation_delay,
            "reason": rng.choice(REVOKE_REASONS)
        }
    
    return {
        "t_approval": t_approval,
        "t_execution": t_execution,
        "multistep": multistep,
        "revocation": revocation,
        "reauthorization": reauthorization
    }

def _revocation_effective_oracle(timeline: Dict[str, Any], arm: int) -> bool:
    """
    Anti-no-op oracle: verify the scenario genuinely encodes the arm's timing.
    Returns True if valid, False otherwise.
    """
    t_approval = timeline["t_approval"]
    t_execution = timeline["t_execution"]
    revocation = timeline["revocation"]
    reauth = timeline["reauthorization"]
    multistep = timeline["multistep"]
    
    if arm == 1:
        return revocation is None
    
    if revocation is None:
        return False  # Arms 2–8 require revocation
    
    t_revoke = revocation["t_revoke"]
    propagation_delay = revocation["propagation_delay"]
    eff = t_revoke + propagation_delay
    
    if arm == 2:
        # REVOKED-before-approval: eff < t_approval, no reauth
        return eff < t_approval and reauth is None
    
    if arm == 3:
        # REVOKED-after-approval-before-execution: t_approval ≤ t_revoke, eff ≤ t_execution, no reauth
        return t_approval <= t_revoke and eff <= t_execution and reauth is None
    
    if arm == 4:
        # REVOKED-during-multistep: multistep=True, eff ≤ t_execution, no reauth
        return multistep is True and eff <= t_execution and reauth is None
    
    if arm in [5, 7]:
        # IN-FLIGHT: t_revoke ≤ t_execution < eff, no reauth
        return t_revoke <= t_execution < eff and reauth is None
    
    if arm == 6:
        # REVOKED-then-REAUTHORIZED: reauth exists, valid, t_revoke < t_reauth ≤ t_execution
        if reauth is None or not reauth.get("valid"):
            return False
        t_reauth = reauth["t_reauth"]
        return t_revoke < t_reauth <= t_execution
    
    if arm == 8:
        # REVOKED-after-execution: t_revoke > t_execution, no reauth
        return t_revoke > t_execution and reauth is None
    
    return False

def generate_scenario(arm: int, idx: int) -> Dict[str, Any]:
    """Generate a single scenario for the given arm and index."""
    rng = _rng_for_scenario(arm, idx)
    scenario_id = _hash_scenario_id(arm, idx)
    
    # Generate API rate limit action
    action = _iam_action(rng)
    
    # Generate timeline
    timeline = _timeline(rng, arm)
    
    # Verify oracle
    if not _revocation_effective_oracle(timeline, arm):
        raise ValueError(f"Scenario arm={arm} idx={idx} failed oracle check (no-op)")
    
    return {
        "scenario_id": scenario_id,
        "arm": arm,
        "authorization": {
            "binding": action,
            "t_approval": timeline["t_approval"],
        },
        "execution": {
            "action": action,  # Same action (exact match on action dims)
            "t_execution": timeline["t_execution"],
        },
        "multistep": timeline["multistep"],
        "revocation": timeline["revocation"],
        "reauthorization": timeline["reauthorization"],
    }

def generate_arm(arm: int, n: int = 100) -> list:
    """Generate n scenarios for a given arm."""
    return [generate_scenario(arm, i) for i in range(n)]

if __name__ == "__main__":
    # Test: generate one scenario per arm
    for a in range(1, 9):
        sc = generate_scenario(a, 0)
        print(f"ARM {a}: scenario_id={sc['scenario_id']}, revocation={sc['revocation'] is not None}")
