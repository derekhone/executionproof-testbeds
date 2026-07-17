#!/usr/bin/env python3
"""
ARK-454 Decision-Scenario Generator
Self-Approval and Circular Delegation Must Fail Closed.

Generates modeled authorization decision scenarios for eight arms:

  1  LEGITIMATE-independent          control; genuine independent approval  -> ALLOW
  2  DIRECT-self-approval            approver == requester                  -> DENY
  3  SOCKPUPPET-controlled-identity  controller_of(approver) == requester   -> DENY
  4  DELEGATION-to-self              requester in delegation_chain          -> DENY
  5  CIRCULAR-delegation             duplicate principal in chain           -> DENY
  6  SHARED-CONTROLLER-collusion     requester & approver share a 3rd-party -> DENY
  7  INHERITED-parent-workflow-self  authority from requester's own wf      -> DENY
  8  AMBIGUOUS-independence          controller_of(approver) == "UNKNOWN"   -> HOLD

This is a CLASSICAL software test of authorization-graph logic. There is no
cryptography and no QPU. The generator also emits an attack-effectiveness AUDIT
(independent structural oracle, Section 5.2 of the preregistration): every attack
arm must genuinely encode its violation, and the control arm must genuinely encode
NO violation. run_* scripts ABORT otherwise, so a scenario that is not really an
attack can never be silently scored as a fail-closed success (the ARK-454 analogue
of the ARK-455b mutation-effectiveness gate; see ../ark-455/CORRECTION.md).
"""

import secrets
from typing import Dict, List, Any, Tuple, Optional

UNKNOWN = "UNKNOWN"

ACTION_TYPES = ["payment", "config_change", "key_rotation", "data_export", "access_grant"]
RESOURCES = ["treasury:main", "vault:cold", "iam:roles", "db:customers", "infra:prod"]


class ScenarioGenerator:
    """Generates modeled decision scenarios per ARK-454 specification."""

    ARMS = {
        1: {"label": "LEGITIMATE-independent",         "violation": None},
        2: {"label": "DIRECT-self-approval",           "violation": "direct_self_approval"},
        3: {"label": "SOCKPUPPET-controlled-identity", "violation": "controlled_identity"},
        4: {"label": "DELEGATION-to-self",             "violation": "delegation_to_self"},
        5: {"label": "CIRCULAR-delegation",            "violation": "circular_delegation"},
        6: {"label": "SHARED-CONTROLLER-collusion",    "violation": "shared_controller"},
        7: {"label": "INHERITED-parent-workflow-self", "violation": "inherited_self_workflow"},
        8: {"label": "AMBIGUOUS-independence",         "violation": "unverifiable"},
    }

    def __init__(self, seed: int = None):
        self.seed = seed if seed is not None else secrets.randbits(256)
        self.rng = secrets.SystemRandom(self.seed)
        self._counter = 0

    # ---- helpers -------------------------------------------------------------

    def _pid(self, role: str) -> str:
        """Fresh unique principal id."""
        self._counter += 1
        n = self.rng.randint(1000, 9999)
        return f"principal:{role}:{n:04d}:{self._counter}"

    def _action(self) -> Dict[str, Any]:
        return {
            "type": self.rng.choice(ACTION_TYPES),
            "amount_usd": round(self.rng.uniform(100, 50000), 2),
            "resource": self.rng.choice(RESOURCES),
        }

    def _independent_authority_chain(self, approver: str, exclude: set) -> List[str]:
        """
        Build a legitimate acyclic delegation chain of independent principals
        ending at `approver`. None of these principals is the requester and none
        is controlled by the requester.
        """
        depth = self.rng.randint(0, 2)
        chain = []
        for _ in range(depth):
            p = self._pid("authority")
            while p in exclude or p in chain:
                p = self._pid("authority")
            chain.append(p)
        chain.append(approver)
        return chain

    # ---- per-arm construction ------------------------------------------------

    def generate_scenario(self, arm_id: int) -> Dict[str, Any]:
        spec = self.ARMS[arm_id]
        label = spec["label"]
        self._counter += 1
        scenario_id = f"ark454-arm{arm_id}-{self.rng.randint(10**11, 10**12):012d}"

        requester = self._pid("req")
        action = self._action()

        # defaults
        approver = self._pid("appr")
        delegation_chain: List[str] = []
        identities: Dict[str, Dict[str, Any]] = {}
        authority_source = "independent"
        parent_workflow: Optional[Dict[str, Any]] = None

        if arm_id == 1:
            # Legitimate independent approval: requester and approver are distinct
            # independent principals; delegation chain (if any) is independent and
            # acyclic; no shared controller; requester not in chain.
            identities[requester] = {"controller": None}
            identities[approver] = {"controller": None}
            delegation_chain = self._independent_authority_chain(
                approver, exclude={requester, approver})
            for p in delegation_chain:
                identities.setdefault(p, {"controller": None})
            authority_source = "independent"

        elif arm_id == 2:
            # Direct self-approval: approver IS the requester.
            approver = requester
            identities[requester] = {"controller": None}
            delegation_chain = [approver]

        elif arm_id == 3:
            # Sockpuppet: approver is a second identity directly controlled by the
            # requester.
            identities[requester] = {"controller": None}
            identities[approver] = {"controller": requester}
            delegation_chain = [approver]

        elif arm_id == 4:
            # Delegation-to-self: the requester appears in the approval authority
            # path, injecting its own authority. Approver is otherwise independent.
            identities[requester] = {"controller": None}
            identities[approver] = {"controller": None}
            root = self._pid("authority")
            identities[root] = {"controller": None}
            # requester sits in the chain between root and approver
            delegation_chain = [root, requester, approver]

        elif arm_id == 5:
            # Circular delegation: the chain contains a cycle (a principal repeats).
            # Approver is otherwise independent of the requester.
            identities[requester] = {"controller": None}
            identities[approver] = {"controller": None}
            a = self._pid("authority")
            b = self._pid("authority")
            identities[a] = {"controller": None}
            identities[b] = {"controller": None}
            # a -> b -> a (cycle) -> approver
            delegation_chain = [a, b, a, approver]

        elif arm_id == 6:
            # Shared-controller collusion: requester and approver are distinct and
            # neither controls the other, but both are controlled by the SAME
            # third-party principal.
            controller = self._pid("controller")
            identities[controller] = {"controller": None}
            identities[requester] = {"controller": controller}
            identities[approver] = {"controller": controller}
            delegation_chain = [approver]

        elif arm_id == 7:
            # Inherited self-initiated workflow authority: the approver's authority
            # derives from a parent workflow that the REQUESTER initiated.
            identities[requester] = {"controller": None}
            identities[approver] = {"controller": None}
            delegation_chain = [approver]
            authority_source = "parent_workflow"
            parent_workflow = {"initiator": requester, "confers_authority": True}

        elif arm_id == 8:
            # Ambiguous independence: the approver's controller cannot be
            # determined. No positive violation, but independence is unverifiable.
            identities[requester] = {"controller": None}
            identities[approver] = {"controller": UNKNOWN}
            delegation_chain = [approver]

        else:
            raise ValueError(f"unknown arm {arm_id}")

        return {
            "scenario_id": scenario_id,
            "action": action,
            "requester": requester,
            "approver": approver,
            "delegation_chain": delegation_chain,
            "identities": identities,
            "authority_source": authority_source,
            "parent_workflow": parent_workflow,
            "arm": arm_id,
            "arm_label": label,
        }

    # ---- attack-effectiveness oracle (independent of both guards) ------------

    @staticmethod
    def _controllers_closure(pid: str, identities: Dict[str, Dict[str, Any]]) -> set:
        seen = set()
        cur = identities.get(pid, {}).get("controller", None)
        guard = 0
        while cur is not None and cur != UNKNOWN and cur not in seen and guard < 1000:
            seen.add(cur)
            cur = identities.get(cur, {}).get("controller", None)
            guard += 1
        return seen

    def attack_effective(self, s: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ground-truth STRUCTURAL check (does not call either guard). Returns
        {"attack_effective": bool, "clean": bool|None, "violation": <label>}.
        """
        arm = s["arm"]
        R = s["requester"]
        A = s["approver"]
        ids = s["identities"]
        chain = s["delegation_chain"]
        ctrl_A = ids.get(A, {}).get("controller", None)
        ctrl_R = ids.get(R, {}).get("controller", None)

        if arm == 1:
            cR = self._controllers_closure(R, ids)
            cA = self._controllers_closure(A, ids)
            shares = (R in cA) or (A in cR) or bool(cR & cA)
            has_cycle = len(chain) != len(set(chain))
            req_in_chain = R in chain
            req_controls_chain = any(R in self._controllers_closure(p, ids) for p in chain)
            inherited_self = (s["authority_source"] == "parent_workflow"
                              and s["parent_workflow"]
                              and s["parent_workflow"].get("confers_authority")
                              and s["parent_workflow"].get("initiator") == R)
            unverifiable = (ctrl_A == UNKNOWN) or (A not in ids)
            clean = (A != R and not shares and not has_cycle and not req_in_chain
                     and not req_controls_chain and not inherited_self and not unverifiable)
            return {"attack_effective": None, "clean": bool(clean), "violation": None}

        if arm == 2:
            ok = (A == R)
            return {"attack_effective": bool(ok), "clean": None, "violation": "direct_self_approval"}

        if arm == 3:
            ok = (ctrl_A == R)
            return {"attack_effective": bool(ok), "clean": None, "violation": "controlled_identity"}

        if arm == 4:
            ok = (R in chain)
            return {"attack_effective": bool(ok), "clean": None, "violation": "delegation_to_self"}

        if arm == 5:
            ok = (len(chain) != len(set(chain)))
            return {"attack_effective": bool(ok), "clean": None, "violation": "circular_delegation"}

        if arm == 6:
            ok = (ctrl_A is not None and ctrl_A != UNKNOWN
                  and ctrl_A == ctrl_R and A != R and ctrl_A != R)
            return {"attack_effective": bool(ok), "clean": None, "violation": "shared_controller"}

        if arm == 7:
            pw = s["parent_workflow"]
            ok = (s["authority_source"] == "parent_workflow" and pw is not None
                  and pw.get("confers_authority") is True and pw.get("initiator") == R)
            return {"attack_effective": bool(ok), "clean": None, "violation": "inherited_self_workflow"}

        if arm == 8:
            ok = (ctrl_A == UNKNOWN)
            return {"attack_effective": bool(ok), "clean": None, "violation": "unverifiable"}

        raise ValueError(f"unknown arm {arm}")

    def generate_arm_scenarios(self, arm_id: int, count: int = 100
                               ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        scenarios, audit = [], []
        for _ in range(count):
            s = self.generate_scenario(arm_id)
            scenarios.append(s)
            audit.append(self.attack_effective(s))
        return scenarios, audit


if __name__ == "__main__":
    gen = ScenarioGenerator(seed=42)
    for arm_id in range(1, 9):
        recs, aud = gen.generate_arm_scenarios(arm_id, count=3)
        if arm_id == 1:
            flags = [a["clean"] for a in aud]
            print(f"Arm {arm_id} [{gen.ARMS[arm_id]['label']}] clean={flags}")
        else:
            flags = [a["attack_effective"] for a in aud]
            print(f"Arm {arm_id} [{gen.ARMS[arm_id]['label']}] attack_effective={flags}")
