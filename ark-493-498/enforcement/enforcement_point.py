"""
enforcement/enforcement_point.py — The ONLY path to the mock tools.

Accepts an action + idempotency key from the actor agent, calls the gate
synchronously, and enforces the decision:
  ALLOW -> executes the tool EXACTLY ONCE, writes an `executed` ledger entry.
  DENY  -> writes a `blocked` ledger entry, runs zero tool logic.
  HOLD  -> writes a `held` ledger entry, runs zero tool logic (non-executable).

The five mock tools are name-mangled PRIVATE methods (`__tool_T1`..`__tool_T5`)
and are not reachable by import from any other module. Idempotency: a dict of
idempotency_key -> ProofRecord; a second presentation of a key that already
produced an ALLOW+executed returns the cached record with duplicate_prevented
= true, without re-executing. Exposes submit() (P1/primary) and submit_via_alt()
(P3/alternate endpoint) — both call the identical internal gate path.
"""
import secrets
import threading

from gate.core import now_utc, sha256_hex, SCHEMA_VERSION, PUBLIC_KEY_ID
from gate.gate import ExecutionProofGate
from tools import tools as toolmod


class EnforcementPoint:
    def __init__(self, gate: ExecutionProofGate, proofstore, *,
                 simulate_latency=False):
        self._gate = gate
        self._store = proofstore
        self._idem = {}                    # idempotency_key -> ProofRecord
        self.simulate_latency = simulate_latency
        # Per-key locks guarantee that concurrent submissions of the SAME
        # idempotency key are serialized (so a key executes at most once), while
        # distinct keys proceed fully in parallel (no global serialization).
        self._key_locks = {}
        self._key_locks_guard = threading.Lock()
        toolmod.ensure_ledgers_exist()

    def _lock_for(self, idem):
        with self._key_locks_guard:
            lk = self._key_locks.get(idem)
            if lk is None:
                lk = threading.Lock()
                self._key_locks[idem] = lk
            return lk

    # ================= PRIVATE MOCK TOOLS (name-mangled) ==================
    def __tool_T1(self, params): return toolmod.perform_side_effect("T1", params)
    def __tool_T2(self, params): return toolmod.perform_side_effect("T2", params)
    def __tool_T3(self, params): return toolmod.perform_side_effect("T3", params)
    def __tool_T4(self, params): return toolmod.perform_side_effect("T4", params)
    def __tool_T5(self, params): return toolmod.perform_side_effect("T5", params)

    def __dispatch_tool(self, tool_id, params):
        table = {
            "T1": self.__tool_T1, "T2": self.__tool_T2, "T3": self.__tool_T3,
            "T4": self.__tool_T4, "T5": self.__tool_T5,
        }
        return table[tool_id](params)

    # ========================= PUBLIC INTERFACE ===========================
    def submit(self, action, case_id, experiment_id, *, dep_failures=None):
        return self._process(action, case_id, experiment_id, via_alt=False,
                             dep_failures=dep_failures)

    def submit_via_alt(self, action, case_id, experiment_id, *, dep_failures=None):
        """P3 alternate endpoint — a thin wrapper over the identical gate path."""
        return self._process(action, case_id, experiment_id, via_alt=True,
                             dep_failures=dep_failures)

    # ============================ INTERNAL ================================
    def _process(self, action, case_id, experiment_id, *, via_alt, dep_failures):
        idem = action["idempotency_key"]
        with self._lock_for(idem):
            return self._process_locked(action, case_id, experiment_id,
                                        via_alt=via_alt, dep_failures=dep_failures)

    def _process_locked(self, action, case_id, experiment_id, *, via_alt,
                        dep_failures):
        dep_failures = set(dep_failures or [])
        idem = action["idempotency_key"]

        # ---- idempotency short-circuit ------------------------------------
        # A previously-seen idempotency key returns the cached ProofRecord
        # WITHOUT re-executing or writing a second ProofRecord. This guarantees
        # both "zero additional executed entries" (P-493-2) and "exactly one
        # ProofRecord per cell" (P-493-3) on the retry (P2) and queued (P4)
        # paths. DENY/HOLD are also cached (they never execute, so there is no
        # re-execution risk). Distinct cases always use distinct keys.
        if idem in self._idem:
            cached = self._idem[idem]
            return _clone_as_duplicate(cached)

        # ---- alias resolution (P5): resolve to canonical tool id ----------
        tool_alias = action.get("tool_alias")
        canonical_tool = toolmod.ALIASES.get(tool_alias, action["tool_id"]) \
            if tool_alias else action["tool_id"]

        gate_req = dict(action)
        gate_req["tool_id"] = canonical_tool

        # ---- gate evaluation (synchronous, fail-closed on error) ----------
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

        # ---- ProofRecord store dependency failure -> fail-closed DENY -----
        if "proofrecord" in dep_failures and decision == "ALLOW":
            decision = "DENY"
            gate_eval = dict(gate_eval)
            gate_eval["state_check"] = "FAIL"
            decision_reason = ("proofrecord store dependency unavailable -> "
                               "fail-closed DENY (no execution)")
            authority_basis = dict(authority_basis)
            authority_basis["authority_valid_at_execution"] = False

        proofrecord_id = secrets.token_hex(16)

        # ---- enforce decision -> tool + ledger ----------------------------
        tool_called = False
        tool_ledger_entry_id = None
        duplicate_prevented = False

        if decision == "ALLOW":
            self.__dispatch_tool(canonical_tool, action.get("parameters", {}))
            tool_called = True
            entry = toolmod.build_ledger_entry(
                canonical_tool, case_id, idem, "executed", "ALLOW",
                action.get("parameters", {}), proofrecord_id)
            toolmod.append_ledger(entry)
            tool_ledger_entry_id = entry["ledger_entry_id"]
        elif decision == "DENY":
            entry = toolmod.build_ledger_entry(
                canonical_tool, case_id, idem, "blocked", "DENY",
                action.get("parameters", {}), proofrecord_id)
            toolmod.append_ledger(entry)
            tool_ledger_entry_id = entry["ledger_entry_id"]
        else:  # HOLD
            entry = toolmod.build_ledger_entry(
                canonical_tool, case_id, idem, "held", "HOLD",
                action.get("parameters", {}), proofrecord_id)
            toolmod.append_ledger(entry)
            tool_ledger_entry_id = entry["ledger_entry_id"]

        # ---- build ProofRecord --------------------------------------------
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
                "duplicate_prevented": duplicate_prevented,
            },
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

        # register idempotency for every terminal decision (see short-circuit)
        self._idem[idem] = record
        return record


def _clone_as_duplicate(record):
    import copy
    dup = copy.deepcopy(record)
    dup["execution_outcome"]["duplicate_prevented"] = True
    dup["_duplicate_short_circuit"] = True
    return dup
