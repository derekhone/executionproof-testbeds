"""
enforcement/real_enforcement_point.py — Adapter-driven enforcement for ARK-499-503.

Identical control flow to the ARK-493-498 EnforcementPoint (frozen gate call,
fail-closed on error, per-idempotency-key locking, idempotency short-circuit,
signed hash-chained dual-guard ProofRecord), EXCEPT the side effect on ALLOW is
performed by a pluggable REAL adapter against a REAL external system
(PostgreSQL / git CI runner / OIDC identity source), instead of a mock tool.

Contract for an adapter:
  - adapter.tool_name(tool_id) -> str
  - adapter.healthy() -> bool                 (execution-time dependency probe)
  - adapter.perform(action) -> (ledger_entry_id: str, real_effect: dict)
        performs the real side effect EXACTLY ONCE; returns an id + the real
        system's own observed result (row id, deployed digest, etc.)
  - adapter.record_blocked(action, decision) -> str   (audit-only, no side effect)

The ProofRecord schema is byte-compatible with ARK-493-498 so the same Guard-A /
Guard-B verify it unchanged.
"""
import secrets
import threading

from gate.core import (now_utc, sha256_hex, canonical_json, SCHEMA_VERSION,
                       PUBLIC_KEY_ID)
from gate.gate import ExecutionProofGate


def _normalize_malformed(action):
    """Make a structurally-incomplete action self-consistent so it can be
    recorded as a fail-closed DENY (never executed) instead of crashing the
    enforcement point. Well-formed actions already carry canonical_json +
    exact_action_hash and are returned unchanged."""
    if "canonical_json" in action and "exact_action_hash" in action:
        return action
    action = dict(action)
    action.setdefault("parameters", {})
    action.setdefault("tool_name", action.get("tool_id", "UNKNOWN"))
    payload = dict(action["parameters"])
    payload["tool_id"] = action.get("tool_id")
    payload["tool_name"] = action.get("tool_name")
    cj = canonical_json(payload)
    action["canonical_json"] = cj
    action["exact_action_hash"] = sha256_hex(cj)
    action.setdefault("approved_hash", action["exact_action_hash"])
    action.setdefault("policy_version", None)
    action.setdefault("evidence", {})
    action.setdefault("credential_token", None)
    action.setdefault("idempotency_key", secrets.token_hex(8))
    action["_malformed"] = True
    return action


class RealEnforcementPoint:
    def __init__(self, gate: ExecutionProofGate, proofstore, adapter, *,
                 simulate_latency=False, identity_validator=None):
        self._gate = gate
        self._store = proofstore
        self._adapter = adapter
        self._idem = {}
        self.simulate_latency = simulate_latency
        # Optional EXTERNAL identity pre-check (ARK-501). When supplied it is a
        # callable(action) -> (valid: bool, identity_info: dict, reason: str)
        # that validates a real bearer token against a real external issuer
        # (RS256 signature over JWKS, exp, jti-revocation, role). A rejection
        # forces the FINAL decision to DENY even if the frozen gate would ALLOW
        # (layered IdP + policy, AND-composed). Defaults to None so ARK-499/500
        # behaviour is byte-for-byte unchanged.
        self._identity_validator = identity_validator
        self._key_locks = {}
        self._key_locks_guard = threading.Lock()

    def _lock_for(self, idem):
        with self._key_locks_guard:
            lk = self._key_locks.get(idem)
            if lk is None:
                lk = threading.Lock()
                self._key_locks[idem] = lk
            return lk

    def submit(self, action, case_id, experiment_id, *, dep_failures=None):
        action = _normalize_malformed(action)
        idem = action["idempotency_key"]
        with self._lock_for(idem):
            return self._process_locked(action, case_id, experiment_id,
                                        dep_failures=dep_failures)

    def _process_locked(self, action, case_id, experiment_id, *, dep_failures):
        dep_failures = set(dep_failures or [])
        idem = action["idempotency_key"]

        # ---- idempotency short-circuit (never re-executes) ----------------
        if idem in self._idem:
            return _clone_as_duplicate(self._idem[idem])

        canonical_tool = action["tool_id"]
        gate_req = dict(action)

        # ---- frozen gate evaluation (fail-closed on error) ----------------
        try:
            result = self._gate.evaluate(
                gate_req, simulate_latency=self.simulate_latency,
                dep_failures=dep_failures)
            decision = result.decision
            gate_eval = result.gate_evaluation
            decision_reason = result.decision_reason
            authority_basis = result.authority_basis
            evidence_state = result.evidence_state
        except Exception as exc:  # noqa: BLE001 — fail closed
            decision = "DENY"
            gate_eval = {k: "FAIL" for k in (
                "actor_check", "authority_check", "evidence_check",
                "policy_version_check", "state_check", "exact_action_check")}
            decision_reason = f"internal gate error -> fail-closed DENY: {exc}"
            authority_basis = {
                "authority_source": "error", "authority_record_id": "none",
                "delegator_chain": [], "authority_valid_at_execution": False,
                "authority_resolved_at": now_utc()}
            evidence_state = {
                "required_evidence_fields": [], "evidence_present": False,
                "evidence_fresh": False, "evidence_snapshot": {}}

        # ---- malformed request -> unconditional fail-closed DENY ---------
        if action.get("_malformed") and decision != "DENY":
            decision = "DENY"
            gate_eval = dict(gate_eval)
            gate_eval["state_check"] = "FAIL"
            decision_reason = "malformed request (missing required fields) -> fail-closed DENY"

        # ---- EXTERNAL identity pre-check (ARK-501) -> fail-closed DENY ----
        # A real bearer token is validated against a real external issuer. A
        # rejection overrides an otherwise-ALLOW decision (AND-composition of
        # external IdP + frozen policy gate). Records the exact rejection cause.
        identity_basis = None
        if self._identity_validator is not None:
            ivalid, identity_basis, ireason = self._identity_validator(action)
            if not ivalid:
                decision = "DENY"
                gate_eval = dict(gate_eval)
                gate_eval["authority_check"] = "FAIL"
                decision_reason = f"external identity rejected: {ireason}"
                authority_basis = dict(authority_basis)
                authority_basis["authority_valid_at_execution"] = False

        # ---- execution-time dependency probe -> fail-closed DENY ----------
        # Models "dependency dropped during an otherwise-ALLOW action": if the
        # real backing system is unhealthy at execution time, the boundary
        # commits NOTHING and records a fail-closed DENY.
        if decision == "ALLOW" and (
                "adapter" in dep_failures or not self._adapter.healthy()):
            decision = "DENY"
            gate_eval = dict(gate_eval)
            gate_eval["state_check"] = "FAIL"
            decision_reason = ("real backing dependency unavailable at execution "
                               "time -> fail-closed DENY (nothing committed)")
            authority_basis = dict(authority_basis)
            authority_basis["authority_valid_at_execution"] = False

        proofrecord_id = secrets.token_hex(16)
        tool_called = False
        tool_ledger_entry_id = None
        real_effect = None

        if decision == "ALLOW":
            tool_ledger_entry_id, real_effect = self._adapter.perform(action)
            tool_called = True
        else:
            tool_ledger_entry_id = self._adapter.record_blocked(action, decision)

        record = {
            "schema_version": SCHEMA_VERSION,
            "proofrecord_id": proofrecord_id,
            "case_id": case_id,
            "experiment_id": experiment_id,
            "timestamp_utc": now_utc(),
            "actor": {
                "actor_id": action["actor_id"],
                "credential_token_hash": sha256_hex(action["credential_token"])
                if action.get("credential_token") is not None else None,
                "delegated_by": action.get("delegated_by"),
            },
            "requested_action": {
                "tool_id": canonical_tool,
                "tool_name": action["tool_name"],
                "parameters": action.get("parameters", {}),
                "canonical_json": action["canonical_json"],
                "exact_action_hash": action["exact_action_hash"],
            },
            "authority_basis": authority_basis,
            "policy_version": action.get("policy_version"),
            "evidence_state": evidence_state,
            "gate_evaluation": gate_eval,
            "decision": decision,
            "decision_reason": decision_reason,
            "execution_outcome": {
                "tool_called": tool_called,
                "tool_ledger_entry_id": tool_ledger_entry_id,
                "idempotency_key": idem,
                "duplicate_prevented": False,
            },
            "real_effect": real_effect,  # extra, non-signed field (audit aid)
            "identity_basis": identity_basis,  # extra, non-signed (ARK-501 IdP)
            "chain": {"prior_record_hash": None, "this_record_hash": None},
            "verification": {},
            "signature": {
                "algorithm": "ed25519",
                "public_key_id": PUBLIC_KEY_ID,
                "signature_hex": None,
                "signed_fields": [
                    "proofrecord_id", "case_id", "experiment_id", "timestamp_utc",
                    "actor", "requested_action", "authority_basis", "policy_version",
                    "evidence_state", "gate_evaluation", "decision",
                    "execution_outcome", "chain.prior_record_hash"],
            },
        }

        record = self._store.store(record)
        self._idem[idem] = record
        return record


def _clone_as_duplicate(record):
    import copy
    dup = copy.deepcopy(record)
    dup["execution_outcome"]["duplicate_prevented"] = True
    dup["_duplicate_short_circuit"] = True
    return dup
