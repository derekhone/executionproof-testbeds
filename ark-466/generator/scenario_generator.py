#!/usr/bin/env python3
"""
ARK-466 — Production Deployment · Cross-Context Replay (scenario generator).

Question: When an IAM role-grant authorization is APPROVED bound to a specific
context (tenant/session/resource/audience/environment), can it be replayed to
authorize the grant under a DIFFERENT context?

Model: Each scenario has an deployment action tuple (exact-match from ARK-458) PLUS a
5-dim context tuple (from ARK-457). The grant is APPROVED for `original_context`
and attempted under `presented_context`.

Decision logic:
  - If original_context == presented_context (exact match on all 5 dims) → ALLOW
  - If ANY dimension differs → DENY (cross-context replay, fail-closed)

8 arms × 100 scenarios = 800 decisions.
"""
import hashlib
import json
import random
from typing import Any, Dict

SEED_BASE = 20260718461

IAM_PRINCIPALS = [f"arn:aws:iam::{10**11 + i:012d}:user/svc-{i:04d}" for i in range(100)]
IAM_ROLES = ["ReadOnlyAuditor", "DataAnalyst", "DeploymentManager", "AdminFull"]
IAM_ACCOUNTS = [f"{10**11 + i:012d}" for i in range(50)]
IAM_PERMISSION_SETS = [f"ps-{i:016x}" for i in range(50)]
IAM_CONDITIONS = ["region=us-east-1;mfa=true", "region=us-west-2;mfa=true"]

# Context tuple (from ARK-457)
TENANTS = [f"tenant-{i:04d}" for i in range(50)]
SESSIONS = [f"session-{i:08x}" for i in range(100)]
RESOURCES = [f"resource-{i:04d}" for i in range(50)]
AUDIENCES = ["api.iam.aws.com", "api.sts.aws.com", "api.iam.internal.aws.com"]
ENVIRONMENTS = ["production", "staging", "development", "test"]

CONTEXT_DIMS = ["tenant", "session", "resource", "audience", "environment"]

def _hash_scenario_id(arm: int, idx: int) -> str:
    s = f"ARK-466-arm{arm}-{idx}"
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

def _context(rng: random.Random) -> Dict[str, str]:
    return {
        "tenant": rng.choice(TENANTS),
        "session": rng.choice(SESSIONS),
        "resource": rng.choice(RESOURCES),
        "audience": rng.choice(AUDIENCES),
        "environment": rng.choice(ENVIRONMENTS),
    }

def _mutate_context(original: Dict[str, str], rng: random.Random, arm: int) -> Dict[str, str]:
    """Mutate context for the given arm."""
    if arm == 1:
        # ARM 1: EXACT-MATCH → same context
        return dict(original)
    
    presented = dict(original)
    
    if arm == 2:
        # ARM 2: CROSS-TENANT
        presented["tenant"] = rng.choice([t for t in TENANTS if t != original["tenant"]])
    elif arm == 3:
        # ARM 3: CROSS-SESSION
        presented["session"] = rng.choice([s for s in SESSIONS if s != original["session"]])
    elif arm == 4:
        # ARM 4: CROSS-RESOURCE
        presented["resource"] = rng.choice([r for r in RESOURCES if r != original["resource"]])
    elif arm == 5:
        # ARM 5: CROSS-AUDIENCE
        presented["audience"] = rng.choice([a for a in AUDIENCES if a != original["audience"]])
    elif arm == 6:
        # ARM 6: CROSS-ENVIRONMENT
        presented["environment"] = rng.choice([e for e in ENVIRONMENTS if e != original["environment"]])
    elif arm == 7:
        # ARM 7: MULTI-DIM (2-3 dims differ)
        num_diffs = rng.randint(2, 3)
        dims_to_mutate = rng.sample(CONTEXT_DIMS, num_diffs)
        for dim in dims_to_mutate:
            if dim == "tenant":
                presented["tenant"] = rng.choice([t for t in TENANTS if t != original["tenant"]])
            elif dim == "session":
                presented["session"] = rng.choice([s for s in SESSIONS if s != original["session"]])
            elif dim == "resource":
                presented["resource"] = rng.choice([r for r in RESOURCES if r != original["resource"]])
            elif dim == "audience":
                presented["audience"] = rng.choice([a for a in AUDIENCES if a != original["audience"]])
            elif dim == "environment":
                presented["environment"] = rng.choice([e for e in ENVIRONMENTS if e != original["environment"]])
    elif arm == 8:
        # ARM 8: EXACT-MATCH (baseline recheck)
        return dict(original)
    
    return presented

def _cross_context_oracle(original: Dict[str, str], presented: Dict[str, str], arm: int) -> bool:
    """Verify the scenario genuinely encodes the arm's context relationship."""
    if arm in [1, 8]:
        # EXACT-MATCH
        return all(original[dim] == presented[dim] for dim in CONTEXT_DIMS)
    elif arm == 2:
        # CROSS-TENANT: tenant differs, others same
        return (original["tenant"] != presented["tenant"] and
                all(original[dim] == presented[dim] for dim in CONTEXT_DIMS if dim != "tenant"))
    elif arm == 3:
        # CROSS-SESSION
        return (original["session"] != presented["session"] and
                all(original[dim] == presented[dim] for dim in CONTEXT_DIMS if dim != "session"))
    elif arm == 4:
        # CROSS-RESOURCE
        return (original["resource"] != presented["resource"] and
                all(original[dim] == presented[dim] for dim in CONTEXT_DIMS if dim != "resource"))
    elif arm == 5:
        # CROSS-AUDIENCE
        return (original["audience"] != presented["audience"] and
                all(original[dim] == presented[dim] for dim in CONTEXT_DIMS if dim != "audience"))
    elif arm == 6:
        # CROSS-ENVIRONMENT
        return (original["environment"] != presented["environment"] and
                all(original[dim] == presented[dim] for dim in CONTEXT_DIMS if dim != "environment"))
    elif arm == 7:
        # MULTI-DIM: ≥2 dims differ
        diffs = sum(1 for dim in CONTEXT_DIMS if original[dim] != presented[dim])
        return diffs >= 2
    return False

def generate_scenario(arm: int, idx: int) -> Dict[str, Any]:
    rng = _rng_for_scenario(arm, idx)
    scenario_id = _hash_scenario_id(arm, idx)
    
    action = _iam_action(rng)
    original_context = _context(rng)
    presented_context = _mutate_context(original_context, rng, arm)
    
    if not _cross_context_oracle(original_context, presented_context, arm):
        raise ValueError(f"Scenario arm={arm} idx={idx} failed cross-context oracle (no-op)")
    
    return {
        "scenario_id": scenario_id,
        "arm": arm,
        "authorization": {
            "binding": action,
            "context": original_context
        },
        "execution": {
            "action": action,  # exact match on deployment action
            "context": presented_context
        }
    }

def generate_arm(arm: int, n: int = 100) -> list:
    return [generate_scenario(arm, i) for i in range(n)]

if __name__ == "__main__":
    for a in range(1, 9):
        sc = generate_scenario(a, 0)
        orig = sc["authorization"]["context"]
        pres = sc["execution"]["context"]
        diffs = [d for d in CONTEXT_DIMS if orig[d] != pres[d]]
        print(f"ARM {a}: context diffs={diffs or 'none'}")
