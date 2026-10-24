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
import copy
import json
import math
import secrets
import threading

from gate.core import now_utc, sha256_hex, SCHEMA_VERSION, PUBLIC_KEY_ID
from gate.gate import ExecutionProofGate
from tools import tools as toolmod


# ---- execution-identity binding (proposed fix, 2026-10-23) -----------------
# The gate verifies canonical_json against the approved hash, but the tool is
# dispatched with action["parameters"]. This check freezes the parameters that
# will actually be dispatched and requires that, re-serialized WITHOUT any
# normalization, they are byte-identical to the approved canonical_json.
_RESERVED_PARAM_KEYS = ("tool_id", "tool_name")


def _plain_json(value, depth=0):
    if depth > 32:
        return False
    # exact built-in types only: subclasses can serialize one way and behave another
    if value is None or type(value) in (bool, str, int):
        return True
    if type(value) is float:
        return math.isfinite(value)
    if type(value) is list:
        return all(_plain_json(v, depth + 1) for v in value)
    if type(value) is dict:
        return all(type(k) is str and _plain_json(v, depth + 1)
                   for k, v in value.items())
    return False  # tuple, set, bytes, custom objects: not dispatchable


# ---- trusted-representation intake (RT6/RT7 class, 2026-10-24) --------------
# Every decision-relevant comparison (hash, canonical bytes, credential, policy
# version, alias/idempotency lookups) is only meaningful if the operands are the
# exact built-in types. A caller-supplied subclass can override __eq__/__ne__,
# encode() or __hash__ and win the comparison from either side, so the action is
# accepted only if it is an exact dict of exact plain-JSON values. Anything else
# is replaced by an inert plain copy (for the DENY record only) and denied before
# evaluation is trusted or anything is dispatched.
_MAX_UNTRUSTED_PATHS = 8


def _untrusted_paths(value, path="action", out=None, depth=0):
    out = [] if out is None else out
    if len(out) >= _MAX_UNTRUSTED_PATHS:
        return out
    t = type(value)
    if depth > 32:
        out.append(f"{path}(too deep)")
    elif value is None or t in (bool, str, int):
        pass
    elif t is float:
        if not math.isfinite(value):
            out.append(f"{path}(non-finite float)")
    elif t is list:
        for i, v in enumerate(list.copy(value)):
            _untrusted_paths(v, f"{path}[{i}]", out, depth + 1)
    elif t is dict:
        for k, v in dict.items(value):
            if type(k) is not str:
                out.append(f"{path}.<key:{type(k).__name__[:40]}>")
            else:
                _untrusted_paths(v, f"{path}.{k[:64]}", out, depth + 1)
    else:
        out.append(f"{path}({t.__name__[:40]})")
    return out


def _inert(value, depth=0):
    """Plain, exact-type copy built without calling caller-overridable methods."""
    if depth > 32:
        return "<untrusted:too-deep>"
    if value is None or type(value) in (bool, str, int):
        return value
    if type(value) is float:
        return value if math.isfinite(value) else "<untrusted:non-finite>"
    if isinstance(value, bool):
        return bool.__bool__(value)
    if isinstance(value, str):
        return str.__str__(value)          # exact str copy of the content
    if isinstance(value, int):
        return int.__int__(value)
    if isinstance(value, float):
        f = float.__float__(value)
        return f if math.isfinite(f) else "<untrusted:non-finite>"
    if isinstance(value, (list, tuple)):
        seq = list.copy(value) if isinstance(value, list) else list(tuple.__iter__(value))
        return [_inert(v, depth + 1) for v in seq]
    if isinstance(value, dict):
        out = {}
        for k, v in dict.items(value):
            key = str.__str__(k) if isinstance(k, str) else f"<untrusted-key:{type(k).__name__[:40]}>"
            out[key] = _inert(v, depth + 1)
        return out
    return f"<untrusted:{type(value).__name__[:40]}>"


def _trusted_intake(action):
    """Return (action, untrusted_paths). Exact plain-JSON actions are returned
    unchanged; anything else is replaced by an inert copy and flagged."""
    try:
        paths = _untrusted_paths(action)
    except Exception as exc:  # noqa: BLE001 - fail closed
        paths = [f"action(inspection error: {type(exc).__name__})"]
    if not paths:
        return action, []
    try:
        safe = _inert(action) if isinstance(action, dict) else {}
    except Exception:  # noqa: BLE001 - fail closed
        safe = {}
    if type(safe) is not dict:
        safe = {}
    return safe, paths


def _execution_binding(action, dispatch_tool_id):
    """Return (ok, reason, frozen_params). Fail-closed on any error."""
    try:
        frozen = copy.deepcopy(action.get("parameters", {}))
        if not isinstance(frozen, dict) or not _plain_json(frozen):
            return False, "parameters are not plain JSON values", {}
        reserved = [k for k in _RESERVED_PARAM_KEYS if k in frozen]
        if reserved:
            return False, f"reserved key(s) in parameters: {reserved}", {}
        if dispatch_tool_id != action.get("tool_id"):
            return False, ("dispatch tool differs from approved tool_id "
                           f"({dispatch_tool_id} != {action.get('tool_id')})"), {}
        rebound = dict(frozen)
        rebound["tool_id"] = action.get("tool_id")
        rebound["tool_name"] = action.get("tool_name")
        raw = json.dumps(rebound, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False)
        approved_cj = action.get("canonical_json")
        if type(approved_cj) is not str or type(raw) is not str \
                or not str.__eq__(raw, approved_cj):
            return False, ("dispatched parameter bytes differ from approved "
                           "canonical_json (post-approval mutation or "
                           "non-NFC text)"), {}
        # dispatch the decoded approved bytes, not the caller's objects
        frozen = json.loads(raw)
        for k in _RESERVED_PARAM_KEYS:
            frozen.pop(k, None)
        return True, None, frozen
    except Exception as exc:  # noqa: BLE001 - fail closed
        return False, f"binding check error: {exc}", {}



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
        action, untrusted = _trusted_intake(action)
        if untrusted:
            action["_untrusted_representation"] = untrusted
            action.setdefault("idempotency_key", secrets.token_hex(8))
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

        binding_ok, binding_reason, frozen_params = _execution_binding(
            action, canonical_tool)

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

        # ---- execution-identity binding violation -> fail-closed DENY ------
        if decision == "ALLOW" and not binding_ok:
            decision = "DENY"
            gate_eval = dict(gate_eval)
            gate_eval["exact_action_check"] = "FAIL"
            decision_reason = ("execution-binding violation: " + binding_reason
                               + " -> DENY (no execution)")

        # ---- ProofRecord store dependency failure -> fail-closed DENY -----
        if "proofrecord" in dep_failures and decision == "ALLOW":
            decision = "DENY"
            gate_eval = dict(gate_eval)
            gate_eval["state_check"] = "FAIL"
            decision_reason = ("proofrecord store dependency unavailable -> "
                               "fail-closed DENY (no execution)")
            authority_basis = dict(authority_basis)
            authority_basis["authority_valid_at_execution"] = False

        # ---- untrusted representation -> fail-closed DENY (RT6/RT7 class) --
        if action.get("_untrusted_representation"):
            decision = "DENY"
            gate_eval = dict(gate_eval)
            gate_eval["exact_action_check"] = "FAIL"
            decision_reason = ("untrusted representation (non-exact built-in "
                               "type) at: "
                               + ", ".join(action["_untrusted_representation"])
                               + " -> DENY before dispatch")
            if isinstance(authority_basis, dict):
                authority_basis = dict(authority_basis)
                authority_basis["authority_valid_at_execution"] = False

        proofrecord_id = secrets.token_hex(16)

        # ---- enforce decision -> tool + ledger ----------------------------
        tool_called = False
        tool_ledger_entry_id = None
        duplicate_prevented = False

        if decision == "ALLOW":
            self.__dispatch_tool(canonical_tool, frozen_params)
            tool_called = True
            entry = toolmod.build_ledger_entry(
                canonical_tool, case_id, idem, "executed", "ALLOW",
                frozen_params, proofrecord_id)
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
