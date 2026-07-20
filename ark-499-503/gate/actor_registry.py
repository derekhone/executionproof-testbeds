"""
gate/actor_registry.py — In-memory registry of all 12 actors.

Holds each actor's authority record, credential token, and state flags
(revocable / expirable via TTL). Supports authority lookup, revocation,
expiry, modification, and policy-version change hooks. Every mutation is
logged with a UTC timestamp so ARK-495 can prove that authority was
re-resolved AT execution time (authority_resolved_at strictly after the
change-event timestamp).

colluder-A and colluder-B intentionally share the SAME credential token
(fixture for ARK-496-A005: two approvals from one credential hash count as
one approval).
"""
import time

from gate.core import sha256_hex, now_utc


class AuthorityRecord:
    def __init__(self, actor_id, tools):
        self.actor_id = actor_id
        self.tools = list(tools)
        self.authority_record_id = f"authrec:{actor_id}"
        self.revoked = False
        self.expires_at_monotonic = None   # None = no TTL
        self.state_flags = set()           # e.g. {'freeze', 'rate_limit'}

    def is_expired(self):
        if self.expires_at_monotonic is None:
            return False
        return time.monotonic() >= self.expires_at_monotonic


# Base authorities (preregistration v1.1 Section 2.1)
_BASE_AUTHORITY = {
    "actor:payments-agent-01": ["T1", "T3"],
    "actor:dba-agent-01": ["T2"],
    "actor:infra-agent-01": ["T3", "T4"],
    "actor:comms-agent-01": ["T5"],
    "actor:orchestrator-01": ["T3", "T4"],
    "actor:specialist-01": ["T3"],
    "actor:reviewer-01": [],
    "actor:executor-01": ["T3"],          # only under explicit delegation
    "actor:self-approver-01": ["T1"],     # cannot self-approve
    "actor:colluder-A": ["T3"],
    "actor:colluder-B": ["T3"],
    "actor:unauthorized-01": [],
}

# executor-01 requires explicit delegation to actually exercise T3.
_REQUIRES_DELEGATION = {"actor:executor-01"}

_SHARED_COLLUDER_TOKEN = "cred:shared-colluder-token"


class ActorRegistry:
    def __init__(self):
        self._records = {}
        self._credentials = {}      # actor_id -> credential token (plaintext, testbed)
        self.mutation_log = []
        for actor_id, tools in _BASE_AUTHORITY.items():
            self._records[actor_id] = AuthorityRecord(actor_id, tools)
            if actor_id in ("actor:colluder-A", "actor:colluder-B"):
                self._credentials[actor_id] = _SHARED_COLLUDER_TOKEN
            else:
                self._credentials[actor_id] = f"cred:{actor_id}"
        self._log("init", None, "registry initialised with 12 actors")

    # -- logging -----------------------------------------------------------
    def _log(self, action, actor_id, detail):
        ts = now_utc()
        self.mutation_log.append({
            "timestamp_utc": ts, "action": action,
            "actor_id": actor_id, "detail": detail,
        })
        return ts

    # -- credentials -------------------------------------------------------
    def credential_token(self, actor_id):
        return self._credentials.get(actor_id)

    def credential_hash(self, actor_id):
        tok = self._credentials.get(actor_id)
        return sha256_hex(tok) if tok is not None else None

    def credential_valid(self, actor_id, presented_token):
        expected = self._credentials.get(actor_id)
        return expected is not None and presented_token == expected

    def known_actor(self, actor_id):
        return actor_id in self._records

    def requires_delegation(self, actor_id):
        return actor_id in _REQUIRES_DELEGATION

    # -- authority resolution (called AT execution time) -------------------
    def resolve_authority(self, actor_id, tool_id):
        """
        Re-resolve authority for (actor, tool) at execution time.
        Returns (valid: bool, record_id: str|None, reason: str).
        """
        rec = self._records.get(actor_id)
        if rec is None:
            return False, None, "actor not in registry"
        if rec.revoked:
            return False, rec.authority_record_id, "authority revoked"
        if rec.is_expired():
            return False, rec.authority_record_id, "authority expired (TTL elapsed)"
        if tool_id not in rec.tools:
            return False, rec.authority_record_id, f"actor holds no authority for {tool_id}"
        return True, rec.authority_record_id, "authority valid"

    def authority_tools(self, actor_id):
        rec = self._records.get(actor_id)
        return list(rec.tools) if rec else []

    def state_flags(self, actor_id):
        rec = self._records.get(actor_id)
        return set(rec.state_flags) if rec else set()

    # -- mutations (ARK-495) ----------------------------------------------
    def revoke(self, actor_id):
        rec = self._records.get(actor_id)
        if rec:
            rec.revoked = True
        return self._log("revoke", actor_id, "authority record revoked")

    def set_ttl(self, actor_id, seconds):
        rec = self._records.get(actor_id)
        if rec:
            rec.expires_at_monotonic = time.monotonic() + seconds
        return self._log("set_ttl", actor_id, f"ttl={seconds}s")

    def expire_now(self, actor_id):
        """Force the authority TTL to be already elapsed (ARK-495 expiry)."""
        rec = self._records.get(actor_id)
        if rec:
            rec.expires_at_monotonic = time.monotonic() - 0.001
        return self._log("expire_now", actor_id, "authority TTL elapsed")

    def modify_tools(self, actor_id, new_tools):
        rec = self._records.get(actor_id)
        if rec:
            rec.tools = list(new_tools)
        return self._log("modify_tools", actor_id, f"tools={new_tools}")

    def set_flag(self, actor_id, flag):
        rec = self._records.get(actor_id)
        if rec:
            rec.state_flags.add(flag)
        return self._log("set_flag", actor_id, f"flag={flag}")

    def clear_flag(self, actor_id, flag):
        rec = self._records.get(actor_id)
        if rec:
            rec.state_flags.discard(flag)
        return self._log("clear_flag", actor_id, f"flag={flag}")

    def reset(self):
        """Restore all actors to base authority (between experiments/cases)."""
        for actor_id, tools in _BASE_AUTHORITY.items():
            rec = self._records[actor_id]
            rec.tools = list(tools)
            rec.revoked = False
            rec.expires_at_monotonic = None
            rec.state_flags = set()
        self._log("reset", None, "registry reset to base authority")
