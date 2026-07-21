"""
actor/actor_agent.py — The actor agent.

Constructs canonical action requests, computes the exact_action_hash
(SHA-256 of the UTF-8 canonical JSON), generates idempotency keys
(secrets.token_hex(16)), and submits to the enforcement point. It CANNOT call
any mock tool directly — every action must pass through the enforcement point.
"""
import secrets

from gate.core import canonical_json, sha256_hex, now_utc


class ActorAgent:
    def __init__(self, registry):
        self._registry = registry

    def new_idempotency_key(self):
        return secrets.token_hex(16)

    def build_action(self, *, actor_id, tool_id, tool_name, parameters,
                     policy_version, evidence=None, approved_hash=None,
                     idempotency_key=None, delegated_by=None,
                     delegation_token=None, approver_id=None, approvals=None,
                     claimed_inheritance=None, tool_alias=None,
                     credential_token=None):
        """
        Build a canonical action request. `parameters` are the material action
        fields; canonical_json/exact_action_hash are computed over the full
        action payload (tool_id + tool_name + parameters).
        """
        payload = dict(parameters)
        payload["tool_id"] = tool_id
        payload["tool_name"] = tool_name
        cjson = canonical_json(payload)
        exact_hash = sha256_hex(cjson)

        if credential_token is None:
            credential_token = self._registry.credential_token(actor_id)

        action = {
            "actor_id": actor_id,
            "credential_token": credential_token,
            "delegated_by": delegated_by,
            "tool_id": tool_id,
            "tool_name": tool_name,
            "parameters": parameters,
            "canonical_json": cjson,
            "exact_action_hash": exact_hash,
            # authorization token: for legitimate actions equals the action's own
            # hash; for mutation attacks (ARK-494) the caller pins the baseline hash.
            "approved_hash": approved_hash if approved_hash is not None else exact_hash,
            "policy_version": policy_version,
            "evidence": evidence or {},
            "idempotency_key": idempotency_key or self.new_idempotency_key(),
        }
        if delegation_token is not None:
            action["delegation_token"] = delegation_token
        if approver_id is not None:
            action["approver_id"] = approver_id
        if approvals is not None:
            action["approvals"] = approvals
        if claimed_inheritance is not None:
            action["claimed_inheritance"] = claimed_inheritance
        if tool_alias is not None:
            action["tool_alias"] = tool_alias
        return action

    @staticmethod
    def fresh_evidence(fields, age_seconds=0):
        """Build an evidence block whose timestamp is `age_seconds` in the past."""
        from datetime import datetime, timezone, timedelta
        ts = (datetime.now(timezone.utc) - timedelta(seconds=age_seconds))
        ts_str = ts.strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"
        snapshot = {f: f"value-{f}" for f in fields}
        return {
            "required_evidence_fields": list(fields),
            "evidence_snapshot": snapshot,
            "evidence_timestamp": ts_str,
        }

    def make_subcall(self, parent_action, *, actor_id, tool_id, tool_name,
                     parameters, policy_version, evidence=None):
        """
        P6 agent-created subcall: builds a NEW sub-request carrying ONLY the
        actor's own credentials. No authority is inherited from the parent.
        """
        return self.build_action(
            actor_id=actor_id, tool_id=tool_id, tool_name=tool_name,
            parameters=parameters, policy_version=policy_version,
            evidence=evidence)
