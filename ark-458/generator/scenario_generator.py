#!/usr/bin/env python3
"""
ARK-458 Scenario Generator — Cloud IAM Role Grant · Exact-Action Binding

Models a recognizable enterprise production boundary: an authorization is
APPROVED to grant a *specific* cloud IAM role binding, described as an exact
action tuple. At execution time an IAM grant action is presented (possibly
mutated). A correct ExecutionProof guard must ALLOW only when the execution
action matches the approved action EXACTLY on every binding dimension, and
DENY every mutation — privilege escalation, grantee swap, account swap,
permission expansion, condition stripping, multi-dimension tampering, and
superficial "confusable" near-matches.

Binding dimensions (the "IAM action tuple"):
  principal       - ARN of the grantee (who receives the role)
  role            - the role/managed-policy being granted
  account         - target AWS account id
  permission_set  - canonical hash of the effective permission scope (policy)
  condition       - scope condition (region / MFA / resource constraint)

This is CLASSICAL software (no quantum hardware, no cryptography beyond a plain
SHA-256 used only as a compact stand-in for "the exact policy document"). The
experiment tests the *authorization control logic*, not AWS itself.
"""
import hashlib
import json
import random
from typing import List, Dict, Any, Tuple

SEED_BASE = 20260718458  # ARK-458 base seed

DIMS = ["principal", "role", "account", "permission_set", "condition"]

# Value pools for each binding dimension (distinct, unambiguous identifiers).
POOLS = {
    "principal": [f"arn:aws:iam::{100000000000 + i}:user/svc-{i:04d}" for i in range(1, 40)],
    # Roles ordered loosely low->high privilege; escalation arm exploits this.
    "role": [
        "ReadOnlyAuditor", "BillingViewer", "SupportEngineer", "DeployBot",
        "DataAnalyst", "SecurityAuditor", "NetworkAdmin", "DatabaseAdmin",
        "PowerUser", "AdministratorAccess", "OrganizationAdmin",
    ],
    "account": [f"{100000000000 + i}" for i in range(1, 40)],
    "condition": [
        "region=us-east-1;mfa=true", "region=us-west-2;mfa=true",
        "region=eu-west-1;mfa=true", "region=us-east-1;mfa=true;ip=10.0.0.0/8",
        "region=us-east-1;mfa=true;resource=prod-db", "mfa=true;time<=8h",
    ],
}

# Higher index in ROLE pool == broader privilege (used by escalation arm).
ROLE_RANK = {r: i for i, r in enumerate(POOLS["role"])}

ARMS = {
    1: {"label": "BASELINE-exact-action-match", "expected": "ALLOW"},
    2: {"label": "ROLE-ESCALATION",             "expected": "DENY"},
    3: {"label": "PRINCIPAL-SWAP",              "expected": "DENY"},
    4: {"label": "ACCOUNT-SWAP",                "expected": "DENY"},
    5: {"label": "PERMISSION-EXPANSION",        "expected": "DENY"},
    6: {"label": "CONDITION-STRIP",             "expected": "DENY"},
    7: {"label": "MULTI-DIM-TAMPER",            "expected": "DENY"},
    8: {"label": "CONFUSABLE-NEAR-MATCH",       "expected": "DENY"},
}


def _perm_hash(role: str, condition: str, extra: str = "") -> str:
    """Compact stand-in for the exact effective policy document."""
    doc = json.dumps({"role": role, "condition": condition, "extra": extra},
                     sort_keys=True, separators=(",", ":"))
    return "ps-" + hashlib.sha256(doc.encode("utf-8")).hexdigest()[:16]


def _confusable_variant(rng: random.Random, value: str) -> str:
    """
    Produce a string NOT byte-equal to `value` but a superficial near-match —
    the kind a naive/normalizing comparator might wrongly treat as identical.
    The guard must still reject it (exact equality). All variants stay within
    the Unicode BMP so JS (UTF-16) and Python (code-point) exact-equality agree.
    """
    kind = rng.choice(["trailing_space", "case_flip", "zero_width", "homoglyph"])
    if kind == "trailing_space":
        return value + " "
    if kind == "case_flip":
        chars = list(value)
        for i, c in enumerate(chars):
            if c.isalpha():
                chars[i] = c.upper() if c.islower() else c.lower()
                return "".join(chars)
        return value + " "
    if kind == "zero_width":
        mid = len(value) // 2
        return value[:mid] + "\u200b" + value[mid:]
    if kind == "homoglyph":
        if "a" in value:
            return value.replace("a", "\u0430", 1)   # Latin a -> Cyrillic а
        if "e" in value:
            return value.replace("e", "\u0435", 1)   # Latin e -> Cyrillic е
        return value + " "
    return value + " "


def _naive_normalize(s: str) -> str:
    """
    DELIBERATELY lenient normalizer used ONLY by the effectiveness oracle and
    the kill-gate to confirm a confusable really is confusable. Guards never
    use this.
    """
    s = s.replace("\u200b", "").strip().lower()
    s = s.replace("\u0430", "a").replace("\u0435", "e")
    return s


class ScenarioGenerator:
    def __init__(self, seed: int):
        self.rng = random.Random(seed)

    def _base_binding(self) -> Dict[str, str]:
        principal = self.rng.choice(POOLS["principal"])
        role = self.rng.choice(POOLS["role"])
        account = self.rng.choice(POOLS["account"])
        condition = self.rng.choice(POOLS["condition"])
        return {
            "principal": principal,
            "role": role,
            "account": account,
            "permission_set": _perm_hash(role, condition),
            "condition": condition,
        }

    def _different_value(self, dim: str, current: str) -> str:
        choices = [v for v in POOLS[dim] if v != current]
        return self.rng.choice(choices)

    def _escalated_role(self, current: str) -> str:
        """Pick a strictly higher-privilege role than `current`."""
        rank = ROLE_RANK[current]
        higher = [r for r in POOLS["role"] if ROLE_RANK[r] > rank]
        if not higher:  # current is already the top; escalate to itself+broader marker impossible
            return None
        return self.rng.choice(higher)

    def generate_scenarios(self, arm: int, count: int = 100) -> List[Dict[str, Any]]:
        scenarios = []
        i = 0
        attempts = 0
        while i < count:
            attempts += 1
            if attempts > count * 50:
                raise RuntimeError(f"arm {arm}: could not generate enough scenarios")
            binding = self._base_binding()
            # Execution action starts as an exact copy of the approved action.
            action = dict(binding)

            if arm == 1:
                pass  # exact match
            elif arm == 2:  # ROLE-ESCALATION
                new_role = self._escalated_role(binding["role"])
                if new_role is None:
                    continue  # regenerate with a lower base role
                action["role"] = new_role
                # A real escalation also changes the effective permission set.
                action["permission_set"] = _perm_hash(new_role, binding["condition"])
            elif arm == 3:  # PRINCIPAL-SWAP
                action["principal"] = self._different_value("principal", binding["principal"])
            elif arm == 4:  # ACCOUNT-SWAP
                action["account"] = self._different_value("account", binding["account"])
            elif arm == 5:  # PERMISSION-EXPANSION (same role name, broader policy body)
                action["permission_set"] = _perm_hash(
                    binding["role"], binding["condition"], extra="s3:*,iam:PassRole")
            elif arm == 6:  # CONDITION-STRIP (loosen/remove scope constraint)
                action["condition"] = "region=*;mfa=false"
            elif arm == 7:  # MULTI-DIM-TAMPER (2-3 dims at once)
                k = self.rng.choice([2, 3])
                dims = self.rng.sample(DIMS, k)
                for d in dims:
                    if d == "permission_set":
                        action["permission_set"] = _perm_hash(
                            binding["role"], binding["condition"], extra="tampered")
                    else:
                        action[d] = self._different_value(d, binding[d])
            elif arm == 8:  # CONFUSABLE-NEAR-MATCH on one string dim
                dim = self.rng.choice(["principal", "role", "account", "condition"])
                action[dim] = _confusable_variant(self.rng, binding[dim])

            scenarios.append({
                "scenario_id": f"ARK458-A{arm}-{i:03d}",
                "arm": arm,
                "arm_label": ARMS[arm]["label"],
                "expected": ARMS[arm]["expected"],
                "authorization": {"binding": binding},
                "execution": {"action": action},
            })
            i += 1
        return scenarios


def action_mutation_effective(scenario: Dict[str, Any], arm: int) -> Tuple[bool, str]:
    """
    Effectiveness oracle (kill condition). For attack arms, confirm the
    execution action REALLY differs from the approved action (a genuine attack).
    For the baseline arm, confirm the action is a true exact match.
    Arm 2 additionally must be a strict privilege escalation.
    Arm 8 must be a genuine 'confusable' (a lenient normalizer would merge it).
    """
    binding = scenario["authorization"]["binding"]
    action = scenario["execution"]["action"]
    differs = any(binding[d] != action[d] for d in DIMS)

    if arm == 1:
        if differs:
            return False, "baseline must be an exact action match but differs"
        return True, "exact match"

    if not differs:
        return False, "attack arm but execution action equals approved action"

    if arm == 2:
        if ROLE_RANK.get(action["role"], -1) <= ROLE_RANK.get(binding["role"], -1):
            return False, "role-escalation arm but role is not strictly higher-privilege"

    if arm == 8:
        # Exactly one dim differs and it must be confusable under lenient norm.
        diff_dims = [d for d in DIMS if binding[d] != action[d]]
        if len(diff_dims) != 1:
            return False, "confusable arm must mutate exactly one dimension"
        d = diff_dims[0]
        if _naive_normalize(binding[d]) != _naive_normalize(action[d]):
            return False, f"confusable arm dim '{d}' is not confusable under lenient normalization"

    return True, "genuine action mutation"
