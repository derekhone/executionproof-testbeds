#!/usr/bin/env python3
"""
ARK-451 Revocation Scenario Generator
Generates authorization-lifecycle scenarios with a revocation timeline and
optional re-authorization. Includes a revocation-timing gate (structural
oracle) to prevent ARK-455-style no-op defects where an arm appears to encode
a timing condition but is mathematically inert.
"""
import random
import string
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

# Seed base: 20260717451 (YYYYMMDD + ARK number)
SEED_BASE = 20260717451

# Action types for randomization
ACTION_TYPES = ["transfer", "approve", "execute", "delegate", "revoke"]
REVOKE_REASONS = [
    "credential_compromise",
    "employee_termination",
    "api_key_rotation",
    "emergency_shutdown",
    "policy_change",
]

# Arm definitions: (label, timeline_config_fn)
# Expected decisions:
#   ALLOW arms: 1 (valid-throughout), 6 (revoked-then-reauthorized), 8 (revoked-after-execution)
#   DENY  arms: 2 (revoked-before-bind), 3 (revoked-after-decision-before-contact), 4 (revoked-during-multistep)
#   HOLD  arms: 5 (in-flight-at-contact), 7 (in-flight-boundary)
ARMS = {
    1: ("VALID-throughout", "allow"),
    2: ("REVOKED-before-bind", "deny"),
    3: ("REVOKED-after-decision-before-contact", "deny"),
    4: ("REVOKED-during-multistep", "deny"),
    5: ("IN-FLIGHT-at-contact", "hold"),
    6: ("REVOKED-then-REAUTHORIZED", "allow"),
    7: ("IN-FLIGHT-boundary", "hold"),
    8: ("REVOKED-after-execution", "allow"),
}


class ScenarioGenerator:
    """Generates authority-revocation scenarios for ARK-451"""

    def __init__(self, seed: int):
        self.rng = random.Random(seed)

    def generate_scenario(self, arm: int, index: int) -> Dict:
        """Generate a single scenario for the given arm."""
        label, _ = ARMS[arm]

        requester_id = self._random_uuid()
        action_type = self.rng.choice(ACTION_TYPES)
        resource = self._random_resource()

        timeline = self._build_timeline(arm)

        scenario = {
            "scenario_id": f"arm-{arm}-{index:03d}",
            "arm": arm,
            "requester_id": requester_id,
            "action_type": action_type,
            "resource": resource,
            "t_decision": timeline["t_decision"],
            "t_bind": timeline["t_bind"],
            "t_execution": timeline["t_execution"],
            "multistep": timeline["multistep"],
            "revocation": timeline["revocation"],
            "reauthorization": timeline["reauthorization"],
        }
        return scenario

    def generate_arm_scenarios(self, arm: int, count: int = 100) -> Tuple[List[Dict], Dict]:
        scenarios = [self.generate_scenario(arm, i) for i in range(count)]
        label, _ = ARMS[arm]
        audit = {"arm": arm, "label": label, "count": count, "seed": SEED_BASE + arm}
        return scenarios, audit

    # ---------- timeline construction ----------

    def _build_timeline(self, arm: int) -> Dict:
        """
        Build a randomized-but-valid timeline for the arm.

        Base ordering constraint (always): t_decision <= t_bind <= t_execution.
        Times are monotonic seconds relative to an arbitrary base (0..1000).
        """
        t_decision = round(self.rng.uniform(0, 100), 3)
        t_bind = round(t_decision + self.rng.uniform(1, 30), 3)
        t_execution = round(t_bind + self.rng.uniform(30, 120), 3)

        multistep = False
        revocation = None
        reauthorization = None

        if arm == 1:
            # VALID-throughout: no revocation at all.
            revocation = None

        elif arm == 2:
            # REVOKED-before-bind: revocation effective before the record is even bound.
            # Effective time strictly < t_bind (and thus < t_execution).
            eff = round(self.rng.uniform(t_decision + 0.5, t_bind - 0.5), 3) if t_bind - t_decision > 1.5 else round(t_decision + 0.2, 3)
            prop = round(self.rng.uniform(0.0, max(0.0, eff - t_decision - 0.1)), 3)
            t_revoke = round(eff - prop, 3)
            revocation = self._revocation(t_revoke, prop)

        elif arm == 3:
            # REVOKED-after-decision-before-contact: revoke after bind, effective before execution.
            t_revoke = round(self.rng.uniform(t_bind + 1, t_execution - 20), 3)
            prop = round(self.rng.uniform(0.0, (t_execution - t_revoke) - 5), 3)
            revocation = self._revocation(t_revoke, prop)

        elif arm == 4:
            # REVOKED-during-multistep: multi-step workflow; revocation effective before the
            # irreversible final step at t_execution.
            multistep = True
            t_revoke = round(self.rng.uniform(t_bind + 1, t_execution - 15), 3)
            prop = round(self.rng.uniform(0.0, (t_execution - t_revoke) - 3), 3)
            revocation = self._revocation(t_revoke, prop)

        elif arm == 5:
            # IN-FLIGHT-at-contact: revocation issued before execution, but propagation not
            # complete at execution -> t_revoke <= t_execution < t_revoke + prop.
            t_revoke = round(self.rng.uniform(t_bind + 1, t_execution - 1), 3)
            # ensure effective strictly after execution
            min_prop = (t_execution - t_revoke) + self.rng.uniform(1, 10)
            prop = round(min_prop + self.rng.uniform(0, 20), 3)
            revocation = self._revocation(t_revoke, prop)

        elif arm == 6:
            # REVOKED-then-REAUTHORIZED: revoke (effective before execution) but a NEW valid
            # authorization is issued after the revoke and at/before execution.
            t_revoke = round(self.rng.uniform(t_bind + 1, t_execution - 30), 3)
            prop = round(self.rng.uniform(0.0, 5), 3)
            revocation = self._revocation(t_revoke, prop)
            t_reauth = round(self.rng.uniform(t_revoke + prop + 0.5, t_execution - 1), 3)
            reauthorization = {"t_reauth": t_reauth, "valid": True}

        elif arm == 7:
            # IN-FLIGHT-boundary: revoke very close to execution, still within propagation window.
            t_revoke = round(self.rng.uniform(t_execution - 3, t_execution - 0.2), 3)
            prop = round((t_execution - t_revoke) + self.rng.uniform(0.5, 5), 3)
            revocation = self._revocation(t_revoke, prop)

        elif arm == 8:
            # REVOKED-after-execution: revocation issued strictly after resource contact.
            t_revoke = round(self.rng.uniform(t_execution + 1, t_execution + 60), 3)
            prop = round(self.rng.uniform(0.0, 10), 3)
            revocation = self._revocation(t_revoke, prop)

        return {
            "t_decision": t_decision,
            "t_bind": t_bind,
            "t_execution": t_execution,
            "multistep": multistep,
            "revocation": revocation,
            "reauthorization": reauthorization,
        }

    def _revocation(self, t_revoke: float, propagation_delay: float) -> Dict:
        return {
            "t_revoke": round(t_revoke, 3),
            "propagation_delay": round(max(0.0, propagation_delay), 3),
            "reason": self.rng.choice(REVOKE_REASONS),
        }

    # ---------- randomized identifiers ----------

    def _random_uuid(self) -> str:
        segments = [
            ''.join(self.rng.choices(string.hexdigits.lower(), k=8)),
            ''.join(self.rng.choices(string.hexdigits.lower(), k=4)),
            ''.join(self.rng.choices(string.hexdigits.lower(), k=4)),
            ''.join(self.rng.choices(string.hexdigits.lower(), k=4)),
            ''.join(self.rng.choices(string.hexdigits.lower(), k=12)),
        ]
        return '-'.join(segments)

    def _random_resource(self) -> str:
        prefix = self.rng.choice(["res", "asset", "obj", "item"])
        suffix = ''.join(self.rng.choices(string.ascii_lowercase + string.digits, k=12))
        return f"{prefix}_{suffix}"


# ---------- revocation-timing oracle ----------

def revocation_effective(scenario: Dict, arm: int) -> Tuple[bool, str]:
    """
    Independent structural oracle: verify that a scenario genuinely encodes the
    timing relationship its arm claims. Prevents no-op defects where an arm
    labelled 'revoked' actually has its revocation land after execution (inert),
    or an 'in-flight' arm is actually fully propagated, etc.

    Returns (is_effective, reason).
    """
    t_exec = scenario["t_execution"]
    t_dec = scenario["t_decision"]
    t_bind = scenario["t_bind"]
    rev = scenario["revocation"]
    reauth = scenario["reauthorization"]

    # Universal ordering sanity check.
    if not (t_dec <= t_bind <= t_exec):
        return (False, f"ordering violated: t_decision={t_dec}, t_bind={t_bind}, t_execution={t_exec}")

    eff = None
    if rev is not None:
        eff = rev["t_revoke"] + rev["propagation_delay"]

    if arm == 1:
        if rev is None and reauth is None:
            return (True, "valid-throughout: no revocation")
        return (False, "arm 1 expects no revocation")

    if arm == 2:
        # revoked and fully effective before bind (hence before execution), no reauth
        if rev is not None and reauth is None and eff < t_bind:
            return (True, f"revoked-before-bind: eff={eff:.3f} < t_bind={t_bind:.3f}")
        return (False, f"arm 2 expects effective revocation before t_bind (eff={eff}, t_bind={t_bind})")

    if arm == 3:
        # revoked after bind, effective before execution, no reauth
        if rev is not None and reauth is None and t_bind <= rev["t_revoke"] and eff <= t_exec:
            return (True, f"revoked-before-contact: eff={eff:.3f} <= t_execution={t_exec:.3f}")
        return (False, f"arm 3 expects revoke after bind and effective before execution (t_revoke={rev['t_revoke'] if rev else None}, eff={eff}, t_exec={t_exec})")

    if arm == 4:
        # multistep, effective revocation before the irreversible step (t_execution), no reauth
        if rev is not None and reauth is None and scenario["multistep"] is True and eff <= t_exec:
            return (True, f"revoked-during-multistep: eff={eff:.3f} <= t_execution={t_exec:.3f}")
        return (False, f"arm 4 expects multistep=True and effective revocation before execution (multistep={scenario['multistep']}, eff={eff}, t_exec={t_exec})")

    if arm in (5, 7):
        # in-flight: issued at/before execution but NOT yet effective at execution
        if rev is not None and reauth is None and rev["t_revoke"] <= t_exec < eff:
            return (True, f"in-flight: t_revoke={rev['t_revoke']:.3f} <= t_execution={t_exec:.3f} < eff={eff:.3f}")
        return (False, f"arm {arm} expects in-flight revocation (t_revoke<=t_exec<eff): t_revoke={rev['t_revoke'] if rev else None}, t_exec={t_exec}, eff={eff}")

    if arm == 6:
        # revoked (effective before execution) AND a valid reauth issued after revoke, at/before execution
        if rev is not None and reauth is not None and reauth["valid"] is True \
                and reauth["t_reauth"] > rev["t_revoke"] and reauth["t_reauth"] <= t_exec:
            return (True, f"revoked-then-reauthorized: t_reauth={reauth['t_reauth']:.3f} in (t_revoke={rev['t_revoke']:.3f}, t_execution={t_exec:.3f}]")
        return (False, f"arm 6 expects a valid reauth after revoke and at/before execution (reauth={reauth})")

    if arm == 8:
        # revocation issued strictly after resource contact, no reauth
        if rev is not None and reauth is None and rev["t_revoke"] > t_exec:
            return (True, f"revoked-after-execution: t_revoke={rev['t_revoke']:.3f} > t_execution={t_exec:.3f}")
        return (False, f"arm 8 expects revocation strictly after execution (t_revoke={rev['t_revoke'] if rev else None}, t_exec={t_exec})")

    return (False, f"unknown arm {arm}")


# ---------- self-test CLI ----------

if __name__ == "__main__":
    print("ARK-451 Scenario Generator Self-Test")
    print("=" * 60)
    all_ok = True
    for arm in range(1, 9):
        gen = ScenarioGenerator(SEED_BASE + arm)
        # test the full 100 to make sure NONE are inert
        arm_ok = True
        bad_reason = ""
        for i in range(100):
            sc = gen.generate_scenario(arm, i)
            ok, reason = revocation_effective(sc, arm)
            if not ok:
                arm_ok = False
                bad_reason = f"scenario {i}: {reason}"
                break
        label, expected = ARMS[arm]
        status = "\u2713 PASS" if arm_ok else "\u2717 FAIL"
        print(f"Arm {arm} ({label}) [expect {expected.upper()}]: {status}")
        if not arm_ok:
            print(f"  \u2192 {bad_reason}")
            all_ok = False
    print("=" * 60)
    if all_ok:
        print("\u2713 All arms generate timing-effective scenarios (100/100 each)")
        exit(0)
    else:
        print("\u2717 Some arms generate inert scenarios")
        exit(1)
