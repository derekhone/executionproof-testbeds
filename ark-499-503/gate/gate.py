"""
gate/gate.py — The ExecutionProof gate.

Verifies each incoming action request against SIX dimensions and emits exactly
one of ALLOW / DENY / HOLD (preregistration v1.1 Section 2.2):

  1. Actor identity        actor in registry + credential token valid   -> DENY
  2. Authority             re-resolved AT execution time                -> DENY
  3. Evidence              required fields present, non-null, fresh      -> HOLD
  4. Policy version        matches active version                       -> DENY
  5. System state          no conflicting flag (revocation/freeze/rate) -> DENY
  6. Exact-action integrity SHA-256(canonical_json) == approved hash     -> DENY

Decision logic (fail-closed):
  IF any DENY-dimension fails                 -> DENY
  ELIF evidence missing/stale                 -> HOLD
  ELSE                                        -> ALLOW

Authority is ALWAYS re-resolved from the live registry at evaluation time; it is
never cached from approval time. authority_basis.authority_resolved_at records
the exact instant of re-resolution, which for ARK-495 is strictly after the
authority-change event.
"""
import time
from datetime import datetime, timezone

from gate.core import (
    canonical_hash, now_utc, POLICY_VERSION,
)
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.exceptions import InvalidSignature

# Tool aliases (P5). Enforcement point resolves alias -> canonical id before
# handing the request to the gate; the gate evaluates on the canonical id.
TOOL_ALIASES = {
    "payment_dispatch": "T1",
    "table_remover": "T2",
    "app_deployer": "T3",
    "access_modifier": "T4",
    "message_sender": "T5",
}


class DependencyUnavailable(Exception):
    """Raised inside the gate when a simulated dependency is down (ARK-498)."""


class GateResult:
    def __init__(self, decision, gate_evaluation, decision_reason,
                 authority_basis, evidence_state):
        self.decision = decision
        self.gate_evaluation = gate_evaluation
        self.decision_reason = decision_reason
        self.authority_basis = authority_basis
        self.evidence_state = evidence_state


def _parse_ts(ts: str) -> datetime:
    return datetime.strptime(ts.replace("Z", ""), "%Y-%m-%dT%H:%M:%S.%f").replace(
        tzinfo=timezone.utc)


class ExecutionProofGate:
    def __init__(self, registry, policy_store):
        self.registry = registry
        self.policy = policy_store

    # ------------------------------------------------------------------
    def evaluate(self, req: dict, *, simulate_latency: bool = False,
                 dep_failures=None) -> GateResult:
        dep_failures = dep_failures or set()
        reasons = []
        ev = {
            "actor_check": "FAIL",
            "authority_check": "FAIL",
            "evidence_check": "FAIL",
            "policy_version_check": "FAIL",
            "state_check": "FAIL",
            "exact_action_check": "FAIL",
        }

        # ---- Dimension 1: actor identity --------------------------------
        actor_id = req.get("actor_id")
        token = req.get("credential_token")
        if self.registry.known_actor(actor_id) and \
                self.registry.credential_valid(actor_id, token):
            ev["actor_check"] = "PASS"
        else:
            reasons.append("actor identity/credential invalid")

        # ---- Dimension 4: policy version --------------------------------
        # (simulated dependency: policy lookup)
        if simulate_latency:
            time.sleep(0.050)
        if "policy" in dep_failures:
            reasons.append("policy lookup dependency unavailable (fail-closed)")
            ev["policy_version_check"] = "FAIL"
        else:
            active = self.policy.active_version
            if req.get("policy_version") == active:
                ev["policy_version_check"] = "PASS"
            else:
                reasons.append(
                    f"policy version mismatch: presented "
                    f"{req.get('policy_version')} active {active}")

        # ---- Dimension 2: authority (re-resolved at execution) ----------
        if simulate_latency:
            time.sleep(0.030)
        tool_id = req.get("tool_id")
        authority_resolved_at = now_utc()
        delegator_chain = []
        authority_source = "direct-authority"
        authority_record_id = None

        if "authority" in dep_failures:
            reasons.append("authority lookup dependency unavailable (fail-closed)")
            auth_valid = False
        else:
            auth_valid, authority_source, authority_record_id, delegator_chain, \
                auth_reason = self._resolve_authority(req, tool_id)
            if not auth_valid:
                reasons.append(auth_reason)
        if auth_valid:
            ev["authority_check"] = "PASS"

        # ---- Dimension 5: system state ----------------------------------
        flags = self.registry.state_flags(actor_id) if actor_id else set()
        if not flags:
            ev["state_check"] = "PASS"
        else:
            reasons.append(f"conflicting state flag(s) active: {sorted(flags)}")

        # ---- Dimension 6: exact-action integrity ------------------------
        canonical = req.get("canonical_json", "")
        recomputed = canonical_hash_of_string(canonical)
        approved = req.get("approved_hash")
        declared = req.get("exact_action_hash")
        if recomputed == approved and recomputed == declared:
            ev["exact_action_check"] = "PASS"
        else:
            reasons.append("exact-action hash mismatch (mutation of approved action)")

        # ---- Dimension 3: evidence --------------------------------------
        evidence = req.get("evidence", {}) or {}
        required = evidence.get("required_evidence_fields", [])
        snapshot = evidence.get("evidence_snapshot", {})
        present = bool(required) and all(
            (f in snapshot and snapshot[f] is not None) for f in required)
        fresh = False
        if present and evidence.get("evidence_timestamp"):
            try:
                age = (datetime.now(timezone.utc)
                       - _parse_ts(evidence["evidence_timestamp"])).total_seconds()
                fresh = 0 <= age <= 60
            except Exception:
                fresh = False
        if present and fresh:
            ev["evidence_check"] = "PASS"
        else:
            ev["evidence_check"] = "HOLD"
            if not present:
                reasons.append("required evidence missing/null")
            elif not fresh:
                reasons.append("evidence stale (outside 60s freshness window)")

        # ---- Decision aggregation (fail-closed) -------------------------
        deny_dims = ["actor_check", "authority_check", "policy_version_check",
                     "state_check", "exact_action_check"]
        any_deny = any(ev[d] == "FAIL" for d in deny_dims)
        if any_deny:
            decision = "DENY"
        elif ev["evidence_check"] == "HOLD":
            decision = "HOLD"
        else:
            decision = "ALLOW"

        # authority_valid_at_execution reflects execution-time authorization as a
        # whole: the actor's authority AND its policy binding must both hold at
        # re-resolution time. Authority is policy-scoped, so when the active
        # policy version changes, previously-resolved authority is no longer
        # valid under the new active policy (ARK-495 C009).
        valid_at_exec = (ev["authority_check"] == "PASS"
                         and ev["policy_version_check"] == "PASS")
        authority_basis = {
            "authority_source": authority_source,
            "authority_record_id": authority_record_id or "none",
            "delegator_chain": delegator_chain,
            "authority_valid_at_execution": bool(valid_at_exec),
            "authority_resolved_at": authority_resolved_at,
        }
        evidence_state = {
            "required_evidence_fields": required,
            "evidence_present": bool(present),
            "evidence_fresh": bool(fresh),
            "evidence_snapshot": snapshot,
        }
        reason = "; ".join(reasons) if reasons else "all six dimensions passed"
        return GateResult(decision, ev, reason, authority_basis, evidence_state)

    # ------------------------------------------------------------------
    def _resolve_authority(self, req, tool_id):
        """
        Returns (valid, authority_source, authority_record_id, delegator_chain, reason).
        Handles direct authority, delegation tokens, self-approval detection,
        and shared-credential collusion.
        """
        actor_id = req.get("actor_id")
        delegation = req.get("delegation_token")
        approver_id = req.get("approver_id")
        approvals = req.get("approvals")
        claimed_inheritance = req.get("claimed_inheritance")

        # --- self-approval: direct ---
        if approver_id is not None and approver_id == actor_id:
            return (False, "self-approval", None, [],
                    "self-approval detected: requesting actor is its own approver")

        # --- collusion: shared credential across approvals ---
        if approvals:
            distinct = {a.get("credential_token_hash") for a in approvals}
            if len(distinct) < len(approvals):
                return (False, "collusion", None, [],
                        "shared-credential collusion detected: two approvals with "
                        "identical credential_token_hash count as one approval; "
                        "independent credentials required")

        # --- delegation token path ---
        if delegation:
            valid_sig = self._verify_delegation_signature(delegation)
            if not valid_sig:
                return (False, "delegation", None, [],
                        "delegation token signature invalid")
            delegator = delegation.get("delegator_id")
            delegatee = delegation.get("delegatee_id")
            allowed = delegation.get("allowed_tools", [])
            chain = [{"delegator_id": delegator, "delegatee_id": delegatee,
                      "allowed_tools": allowed}]
            # self-approval via delegated loop
            if delegator == delegatee:
                return (False, "delegation", None, chain,
                        "self-approval detected: delegated loop names the requesting "
                        "actor as its own execution authority")
            if delegatee != actor_id:
                return (False, "delegation", None, chain,
                        "delegation delegatee does not match requesting actor")
            # expiry
            if self._delegation_expired(delegation):
                return (False, "delegation", None, chain,
                        "delegation expired at execution time")
            # allowed_tools subset of delegator's own live authority
            delegator_tools = set(self.registry.authority_tools(delegator))
            if not set(allowed).issubset(delegator_tools):
                return (False, "delegation", None, chain,
                        "delegation exceeds delegator authority: allowed_tools not a "
                        "subset of delegator's own authority")
            if tool_id not in allowed:
                return (False, "delegation", None, chain,
                        f"delegated authority does not cover {tool_id}")
            return (True, "delegation", f"delegrec:{delegator}->{delegatee}",
                    chain, "delegated authority valid")

        # --- claimed inheritance without delegation (A002) ---
        if claimed_inheritance:
            return (False, "claimed-inheritance", None, [],
                    "authority inheritance claimed without valid delegation token")

        # --- executor requires delegation ---
        if self.registry.requires_delegation(actor_id):
            return (False, "direct-authority", f"authrec:{actor_id}", [],
                    "actor requires explicit delegation but none supplied")

        # --- direct authority (re-resolved live) ---
        valid, rec_id, reason = self.registry.resolve_authority(actor_id, tool_id)
        return (valid, "direct-authority", rec_id, [], reason)

    # ------------------------------------------------------------------
    @staticmethod
    def _verify_delegation_signature(delegation):
        from gate.core import canonical_json, signing_key
        payload = {k: delegation[k] for k in
                   ("delegator_id", "delegatee_id", "allowed_tools",
                    "issued_at", "expires_at") if k in delegation}
        data = canonical_json(payload).encode("utf-8")
        sig_hex = delegation.get("signature_hex", "")
        try:
            pub = signing_key().public_key()
            pub.verify(bytes.fromhex(sig_hex), data)
            return True
        except (InvalidSignature, ValueError):
            return False

    @staticmethod
    def _delegation_expired(delegation):
        try:
            exp = _parse_ts(delegation["expires_at"])
            return datetime.now(timezone.utc) >= exp
        except Exception:
            return True


def canonical_hash_of_string(s: str) -> str:
    """SHA-256 hex of the UTF-8 bytes of an already-canonical JSON string."""
    from gate.core import sha256_hex
    return sha256_hex(s)
