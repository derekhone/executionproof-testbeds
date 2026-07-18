#!/usr/bin/env python3
"""
ARK-457 Scenario Generator — Cross-Context Authorization Replay (Confused Deputy)

Generates authorization scenarios where an authorization is issued bound to a
specific context tuple, and an execution is attempted under some (possibly
different) context. The guard must ALLOW only when the execution context matches
the authorization's bound context EXACTLY on every binding dimension.

Binding dimensions (the "context tuple"):
  tenant, session, resource, audience, environment
"""
import json
import random
from typing import List, Dict, Any, Tuple

SEED_BASE = 20260717457  # ARK-457 base seed

DIMS = ["tenant", "session", "resource", "audience", "environment"]

# Value pools for each binding dimension (distinct, unambiguous identifiers).
POOLS = {
    "tenant":      [f"tenant-{i:04d}" for i in range(1, 40)],
    "session":     [f"sess-{i:06x}" for i in range(0x100, 0x400)],
    "resource":    [f"wallet-{i:04d}" for i in range(1, 40)],
    "audience":    ["api.payments", "api.trading", "api.custody", "api.admin",
                    "api.reporting", "api.settlement"],
    "environment": ["production", "staging", "sandbox", "dr-failover"],
}

ACTIONS = ["transfer", "approve", "delegate", "execute"]


def _confusable_variant(rng: random.Random, value: str) -> str:
    """
    Produce a string that is NOT byte-equal to `value` but is a superficial
    "near match" — the kind of confusable a naive/normalizing comparator might
    wrongly treat as identical. The guard must still reject it (exact equality).

    All variants stay within the Unicode BMP so that JS (UTF-16) and Python
    (code-point) exact-equality comparisons are identical.
    """
    kind = rng.choice(["trailing_space", "case_flip", "zero_width", "homoglyph"])
    if kind == "trailing_space":
        return value + " "
    if kind == "case_flip":
        # Flip case of the first alphabetic character; guaranteed to differ if
        # such a char exists, otherwise fall back to trailing space.
        chars = list(value)
        for i, c in enumerate(chars):
            if c.isalpha():
                chars[i] = c.upper() if c.islower() else c.lower()
                return "".join(chars)
        return value + " "
    if kind == "zero_width":
        # Insert a zero-width space (U+200B) in the middle.
        mid = len(value) // 2
        return value[:mid] + "\u200b" + value[mid:]
    if kind == "homoglyph":
        # Replace an ASCII 'a' with Cyrillic 'а' (U+0430); if none, use 'e'->'е'.
        if "a" in value:
            return value.replace("a", "\u0430", 1)
        if "e" in value:
            return value.replace("e", "\u0435", 1)
        return value + " "
    return value + " "


def _naive_normalize(s: str) -> str:
    """
    A DELIBERATELY naive normalizer used ONLY by the effectiveness oracle to
    confirm that an Arm-8 variant really is 'confusable' (i.e. a lenient
    comparator would merge it with the original). The guards do NOT use this.
    """
    # strip whitespace, drop zero-width chars, lowercase, map common homoglyphs
    s = s.replace("\u200b", "").strip().lower()
    s = s.replace("\u0430", "a").replace("\u0435", "e")
    return s


class ScenarioGenerator:
    def __init__(self, seed: int):
        self.rng = random.Random(seed)

    def _base_binding(self) -> Dict[str, str]:
        return {d: self.rng.choice(POOLS[d]) for d in DIMS}

    def _different_value(self, dim: str, current: str) -> str:
        """Pick a value from the pool that differs from `current`."""
        choices = [v for v in POOLS[dim] if v != current]
        return self.rng.choice(choices)

    def generate_scenarios(self, arm: int, count: int = 100) -> List[Dict[str, Any]]:
        scenarios = []
        for i in range(count):
            scenario_id = f"ARK457-ARM{arm}-{i:03d}"
            auth_binding = self._base_binding()
            exec_context = dict(auth_binding)  # start identical; mutate per arm

            if arm == 1:
                pass  # exact match — no mutation

            elif arm == 2:  # CROSS-TENANT
                exec_context["tenant"] = self._different_value("tenant", auth_binding["tenant"])
            elif arm == 3:  # CROSS-SESSION
                exec_context["session"] = self._different_value("session", auth_binding["session"])
            elif arm == 4:  # CROSS-RESOURCE
                exec_context["resource"] = self._different_value("resource", auth_binding["resource"])
            elif arm == 5:  # CROSS-AUDIENCE
                exec_context["audience"] = self._different_value("audience", auth_binding["audience"])
            elif arm == 6:  # CROSS-ENVIRONMENT
                exec_context["environment"] = self._different_value("environment", auth_binding["environment"])

            elif arm == 7:  # MULTI-DIMENSION mismatch (>=2 dims differ)
                k = self.rng.randint(2, len(DIMS))
                dims_to_change = self.rng.sample(DIMS, k)
                for d in dims_to_change:
                    exec_context[d] = self._different_value(d, auth_binding[d])

            elif arm == 8:  # CONFUSABLE near-match (exactly one dim, superficial variant)
                d = self.rng.choice(DIMS)
                exec_context[d] = _confusable_variant(self.rng, auth_binding[d])

            else:
                raise ValueError(f"Invalid arm {arm}")

            scenarios.append({
                "scenario_id": scenario_id,
                "arm": arm,
                "authorization": {
                    "action": self.rng.choice(ACTIONS),
                    "subject": f"agent-{self.rng.randint(1, 10)}",
                    "binding": auth_binding,
                },
                "execution": {
                    "context": exec_context,
                },
            })
        return scenarios


def context_replay_effective(scenario: Dict[str, Any], arm: int) -> Tuple[bool, str]:
    """
    Structural oracle: confirm the scenario genuinely encodes the arm's intended
    context relationship. Prevents ARK-455-style inert (no-op) test cases.
    """
    binding = scenario["authorization"]["binding"]
    ctx = scenario["execution"]["context"]

    # dims that differ under EXACT equality
    differing = [d for d in DIMS if binding[d] != ctx[d]]

    if arm == 1:
        if len(differing) == 0:
            return (True, "")
        return (False, f"Arm 1 must match exactly; differing dims: {differing}")

    single_dim_map = {2: "tenant", 3: "session", 4: "resource", 5: "audience", 6: "environment"}
    if arm in single_dim_map:
        want = single_dim_map[arm]
        if differing == [want]:
            return (True, "")
        return (False, f"Arm {arm} must differ on exactly [{want}]; got {differing}")

    if arm == 7:
        if len(differing) >= 2:
            return (True, "")
        return (False, f"Arm 7 needs >=2 differing dims; got {differing}")

    if arm == 8:
        if len(differing) != 1:
            return (False, f"Arm 8 needs exactly 1 differing dim; got {differing}")
        d = differing[0]
        # It must be a genuine byte difference...
        if binding[d] == ctx[d]:
            return (False, "Arm 8 dim not actually different")
        # ...that a naive/lenient comparator WOULD merge (i.e. truly confusable).
        if _naive_normalize(binding[d]) == _naive_normalize(ctx[d]):
            return (True, "")
        return (False, f"Arm 8 dim '{d}' differs but is not a confusable near-match")

    return (False, f"Unknown arm {arm}")


ARMS = {
    1: {"label": "BASELINE-exact-context-match", "expected": "ALLOW"},
    2: {"label": "CROSS-TENANT", "expected": "DENY"},
    3: {"label": "CROSS-SESSION", "expected": "DENY"},
    4: {"label": "CROSS-RESOURCE", "expected": "DENY"},
    5: {"label": "CROSS-AUDIENCE", "expected": "DENY"},
    6: {"label": "CROSS-ENVIRONMENT", "expected": "DENY"},
    7: {"label": "MULTI-DIMENSION-mismatch", "expected": "DENY"},
    8: {"label": "CONFUSABLE-near-match", "expected": "DENY"},
}


if __name__ == "__main__":
    print("=== ARK-457 Generator Self-Test ===\n")
    all_ok = True
    for arm in range(1, 9):
        gen = ScenarioGenerator(SEED_BASE + arm)
        scenarios = gen.generate_scenarios(arm, count=100)
        failures = []
        for sc in scenarios:
            is_eff, reason = context_replay_effective(sc, arm)
            if not is_eff:
                failures.append((sc["scenario_id"], reason))
        if failures:
            all_ok = False
            print(f"ARM {arm} ({ARMS[arm]['label']}): FAIL ({len(failures)} inert)")
            for sid, reason in failures[:3]:
                print(f"  {sid}: {reason}")
        else:
            print(f"ARM {arm} ({ARMS[arm]['label']}): OK (100/100 effective)")
    print("\nSelf-test complete." + (" ALL OK." if all_ok else " FAILURES PRESENT."))
