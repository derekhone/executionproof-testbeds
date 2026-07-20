"""
gate/policy.py — Active policy version store.

Default active version: ark-enterprise-v1.0 (the policy under test).
Supports a temporary override used by ARK-495 (policy-version-change attack),
where the active version is incremented to 'ark-enterprise-v1.1-test' between
approval and execution while the execution attempt still presents v1.0.

All mutations are logged with UTC timestamps.
"""
from gate.core import POLICY_VERSION, now_utc


class PolicyStore:
    def __init__(self):
        self._active = POLICY_VERSION
        self.mutation_log = []
        self._log("init", POLICY_VERSION)

    def _log(self, action, value):
        self.mutation_log.append({
            "timestamp_utc": now_utc(),
            "action": action,
            "value": value,
        })

    @property
    def active_version(self) -> str:
        return self._active

    def set_active_version(self, version: str) -> str:
        """Temporary override (ARK-495). Returns the change-event timestamp."""
        ts = now_utc()
        self._active = version
        self.mutation_log.append({
            "timestamp_utc": ts, "action": "set_active_version", "value": version,
        })
        return ts

    def reset(self):
        self._active = POLICY_VERSION
        self._log("reset", POLICY_VERSION)
