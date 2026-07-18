#!/usr/bin/env python3
"""
ARK-472 — Production Database Query · Human Escalation (scenario generator).

Question: When an database query requires human approval, does the gate HOLD
(fail-safe) until the human approval arrives, then ALLOW? Or does it wrongly
ALLOW without waiting?

Model: Each scenario has an database query action + `requires_human_approval` flag +
`human_approval` dict showing if/when approval was granted.

Decision logic:
  - If NOT requires_human_approval → ALLOW (normal case)
  - If requires_human_approval AND human_approval exists AND valid → ALLOW
  - If requires_human_approval AND human_approval missing/invalid → HOLD (fail-safe)
"""
import hashlib, json, random
from typing import Any, Dict

SEED_BASE = 20260718462
IAM_PRINCIPALS = [f"arn:aws:iam::{10**11 + i:012d}:user/svc-{i:04d}" for i in range(100)]
IAM_ROLES = ["ReadOnlyAuditor", "DataAnalyst", "AdminFull", "SecurityOfficer"]
IAM_ACCOUNTS = [f"{10**11 + i:012d}" for i in range(50)]
IAM_PERMISSION_SETS = [f"ps-{i:016x}" for i in range(50)]
IAM_CONDITIONS = ["region=us-east-1;mfa=true", "region=us-west-2;mfa=true"]

HUMAN_APPROVERS = [f"approver-{i:04d}" for i in range(20)]

def _hash_scenario_id(arm: int, idx: int) -> str:
    return hashlib.sha256(f"ARK-472-arm{arm}-{idx}".encode()).hexdigest()[:16]

def _rng_for_scenario(arm: int, idx: int) -> random.Random:
    return random.Random(SEED_BASE + arm * 1000 + idx)

def _iam_action(rng: random.Random) -> Dict[str, str]:
    return {
        "principal": rng.choice(IAM_PRINCIPALS), "role": rng.choice(IAM_ROLES),
        "account": rng.choice(IAM_ACCOUNTS), "permission_set": rng.choice(IAM_PERMISSION_SETS),
        "condition": rng.choice(IAM_CONDITIONS)
    }

def generate_scenario(arm: int, idx: int) -> Dict[str, Any]:
    rng = _rng_for_scenario(arm, idx)
    scenario_id = _hash_scenario_id(arm, idx)
    action = _iam_action(rng)
    
    requires_human_approval = False
    human_approval = None
    
    if arm == 1:
        # ARM 1: NO-ESCALATION-REQUIRED → ALLOW
        requires_human_approval = False
    elif arm == 2:
        # ARM 2: ESCALATION-REQUIRED-APPROVAL-RECEIVED → ALLOW
        requires_human_approval = True
        human_approval = {"approved_by": rng.choice(HUMAN_APPROVERS), "timestamp": rng.uniform(0, 100), "valid": True}
    elif arm == 3:
        # ARM 3: ESCALATION-REQUIRED-NO-APPROVAL → HOLD
        requires_human_approval = True
        human_approval = None
    elif arm == 4:
        # ARM 4: ESCALATION-REQUIRED-INVALID-APPROVAL → HOLD
        requires_human_approval = True
        human_approval = {"approved_by": rng.choice(HUMAN_APPROVERS), "timestamp": rng.uniform(0, 100), "valid": False}
    elif arm == 5:
        # ARM 5: ESCALATION-REQUIRED-APPROVAL-MISSING-FIELDS → HOLD
        requires_human_approval = True
        human_approval = {"approved_by": rng.choice(HUMAN_APPROVERS)}  # missing 'valid'
    elif arm == 6:
        # ARM 6: NO-ESCALATION (baseline recheck) → ALLOW
        requires_human_approval = False
    elif arm == 7:
        # ARM 7: ESCALATION-APPROVED (valid, baseline recheck) → ALLOW
        requires_human_approval = True
        human_approval = {"approved_by": rng.choice(HUMAN_APPROVERS), "timestamp": rng.uniform(0, 100), "valid": True}
    elif arm == 8:
        # ARM 8: ESCALATION-NO-APPROVAL (baseline recheck) → HOLD
        requires_human_approval = True
        human_approval = None
    
    return {
        "scenario_id": scenario_id, "arm": arm,
        "authorization": {"binding": action},
        "execution": {"action": action},  # exact match
        "requires_human_approval": requires_human_approval,
        "human_approval": human_approval
    }

def generate_arm(arm: int, n: int = 100) -> list:
    return [generate_scenario(arm, i) for i in range(n)]

if __name__ == "__main__":
    for a in range(1, 9):
        sc = generate_scenario(a, 0)
        print(f"ARM {a}: requires_escalation={sc['requires_human_approval']}, approval={sc['human_approval'] is not None}")
