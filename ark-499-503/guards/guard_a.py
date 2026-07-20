"""
guards/guard_a.py — Guard-A, the in-process verifier.

Guard-A is a SEPARATE class from the gate with INDEPENDENTLY WRITTEN decision
functions. It shares no decision variable with the gate: it re-derives what the
decision should be purely from the ProofRecord's gate_evaluation fields, and it
re-implements canonical serialization / SHA-256 / ed25519 verification locally
(it does NOT import gate/core.py). It checks the seven properties of
preregistration v1.1 Section 5.2 and records:
  verification.guard_a_result
  verification.guard_a_fields_checked
  verification.guard_a_canonical_hash_computed
"""
import json
import copy
import hashlib
import unicodedata

from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.exceptions import InvalidSignature

_SIGNED_FIELDS = [
    "proofrecord_id", "case_id", "experiment_id", "timestamp_utc",
    "actor", "requested_action", "authority_basis", "policy_version",
    "evidence_state", "gate_evaluation", "decision", "execution_outcome",
    "chain.prior_record_hash",
]

_REQUIRED_TOP = [
    "schema_version", "proofrecord_id", "case_id", "experiment_id",
    "timestamp_utc", "actor", "requested_action", "authority_basis",
    "policy_version", "evidence_state", "gate_evaluation", "decision",
    "decision_reason", "execution_outcome", "chain", "signature",
]


class GuardA:
    """In-process verifier. Independent SHA-256 / canonical / signature paths."""

    # -- independent primitives ---------------------------------------
    @staticmethod
    def _nfc(obj):
        if isinstance(obj, str):
            return unicodedata.normalize("NFC", obj)
        if isinstance(obj, dict):
            return {GuardA._nfc(k): GuardA._nfc(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [GuardA._nfc(v) for v in obj]
        return obj

    @staticmethod
    def _canon(obj):
        return json.dumps(GuardA._nfc(obj), sort_keys=True,
                          separators=(",", ":"), ensure_ascii=False)

    @staticmethod
    def _sha(text):
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def _record_hash(self, record):
        tmp = copy.deepcopy(record)
        tmp.pop("verification", None)
        tmp.setdefault("chain", {})["this_record_hash"] = "COMPUTING"
        return self._sha(self._canon(tmp))

    def _signed_payload(self, record):
        payload = {}
        for f in _SIGNED_FIELDS:
            if f == "chain.prior_record_hash":
                payload["chain.prior_record_hash"] = record["chain"]["prior_record_hash"]
            else:
                payload[f] = record[f]
        return self._canon(payload)

    # -- verification -------------------------------------------------
    def verify(self, record, expected_prior_hash, public_key):
        fields = []
        ok = True

        # Property 1: required fields present + non-null
        fields.append("required_fields_present")
        for f in _REQUIRED_TOP:
            if f not in record or record[f] is None:
                ok = False

        # Property 2: exact_action_hash == SHA256(canonical_json)
        fields.append("exact_action_hash_matches_canonical")
        canonical = record["requested_action"]["canonical_json"]
        computed_action_hash = self._sha(canonical)
        if computed_action_hash != record["requested_action"]["exact_action_hash"]:
            ok = False

        # Summary / GATE-STOP records carry an experiment-level decision, not a
        # per-action ALLOW/DENY/HOLD; properties 3 and 4 do not apply to them.
        is_meta = record["decision"] in ("EXPERIMENT-PASS", "EXPERIMENT-FAIL",
                                         "GATE-STOP")

        # Property 3: decision consistent with gate_evaluation
        if not is_meta:
            fields.append("decision_consistent_with_gate_evaluation")
            ge = record["gate_evaluation"]
            deny_dims = ["actor_check", "authority_check", "policy_version_check",
                         "state_check", "exact_action_check"]
            any_deny = any(ge[d] == "FAIL" for d in deny_dims)
            expected = ("DENY" if any_deny else
                        "HOLD" if ge["evidence_check"] == "HOLD" else "ALLOW")
            if record["decision"] != expected:
                ok = False

            # Property 4: tool_called == True iff decision == ALLOW
            fields.append("tool_called_iff_allow")
            called = bool(record["execution_outcome"]["tool_called"])
            if called != (record["decision"] == "ALLOW"):
                ok = False

        # Property 5: prior_record_hash linkage
        fields.append("chain_prior_hash_linkage")
        if record["chain"]["prior_record_hash"] != expected_prior_hash:
            ok = False

        # Property 6: this_record_hash correctly computed
        fields.append("this_record_hash_correct")
        if self._record_hash(record) != record["chain"]["this_record_hash"]:
            ok = False

        # Property 7: signature covers required fields + verifies
        fields.append("signature_valid")
        if sorted(record["signature"]["signed_fields"]) != sorted(_SIGNED_FIELDS):
            ok = False
        else:
            try:
                public_key.verify(
                    bytes.fromhex(record["signature"]["signature_hex"]),
                    self._signed_payload(record).encode("utf-8"))
            except (InvalidSignature, ValueError):
                ok = False

        return {
            "guard_a_result": "PASS" if ok else "FAIL",
            "guard_a_fields_checked": fields,
            "guard_a_canonical_hash_computed": computed_action_hash,
        }
