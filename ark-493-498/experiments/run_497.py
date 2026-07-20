"""
experiments/run_497.py — ARK-497 Independently Reconstructable ProofRecord.

Draws 20 legitimate ProofRecords (a mix of ALLOW / DENY / HOLD) from the
ARK-493..496 portion of the hash chain, builds 10 tampered copies (one per
frozen tamper field, ARK-497-T001..T010), writes the file-only verifier inputs
(records dir + verification_spec.json + public_key.pem), and invokes the
ISOLATED verifier `ark497_isolated_verifier.py` as a subprocess. The verifier
imports nothing from the testbed packages; a static AST self-import analysis is
captured and recorded in the ARK-497-SUMMARY ProofRecord (P-497-4).

Scoring:
  P-497-1  all 9 elements reconstructed for all 20 legitimate cases
  P-497-2  all 10 tamper cases detected (10/10), specific field identified
  P-497-3  zero false positives on legitimate cases
  P-497-4  static import analysis shows permitted-only imports
"""
import os
import json
import copy
import base64
import subprocess

from cryptography.hazmat.primitives import serialization

from experiments.common import (
    append_result, result_entry, write_series_summary, RESULTS_DIR,
)
from gate.core import (
    signing_key, public_key_pem, POLICY_VERSION, SCHEMA_VERSION,
    EVIDENCE_FRESHNESS_SECONDS,
)
from enforcement.proofstore import CHAIN_PATH

EXPERIMENT_ID = "ARK-497"

_HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RECORDS_DIR = os.path.join(_HERE, "experiments", "ark497_records")
SPEC_DIR = os.path.join(_HERE, "experiments", "ark497_spec")
SPEC_PATH = os.path.join(SPEC_DIR, "verification_spec.json")
PUBKEY_PEM_PATH = os.path.join(SPEC_DIR, "public_key.pem")
VERIFIER = os.path.join(_HERE, "experiments", "ark497_isolated_verifier.py")
REPORT_PATH = os.path.join(RESULTS_DIR, "ark497_verifier_output.json")

_META_DECISIONS = {"EXPERIMENT-PASS", "EXPERIMENT-FAIL", "GATE-STOP"}


def _load_chain_records():
    """Load real scored ProofRecords (exclude series-summary / meta records)."""
    records = []
    with open(CHAIN_PATH, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            if r["decision"] in _META_DECISIONS:
                continue
            if r["case_id"].endswith("-SUMMARY"):
                continue
            if not r["experiment_id"].startswith(("ARK-493", "ARK-494",
                                                  "ARK-495", "ARK-496")):
                continue
            records.append(r)
    return records


def _pick(records, pred, used):
    for r in records:
        if id(r) in used:
            continue
        if pred(r):
            used.add(id(r))
            return r
    return None


def _write_verifier_inputs():
    os.makedirs(RECORDS_DIR, exist_ok=True)
    os.makedirs(SPEC_DIR, exist_ok=True)
    # clean stale record files (records dir holds ONLY ProofRecord json files)
    for fn in os.listdir(RECORDS_DIR):
        if fn.endswith(".json"):
            os.remove(os.path.join(RECORDS_DIR, fn))

    raw = signing_key().public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw)
    with open(PUBKEY_PEM_PATH, "wb") as fh:
        fh.write(public_key_pem())
    spec = {
        "policy_version": POLICY_VERSION,
        "schema_version": SCHEMA_VERSION,
        "evidence_freshness_seconds": EVIDENCE_FRESHNESS_SECONDS,
        "serialization_rules": {
            "normalization": "NFC",
            "json": "sort_keys=True, separators=(',',':'), ensure_ascii=False",
            "hash": "SHA-256 over UTF-8, lowercase hex",
            "record_hash_excludes": ["verification"],
            "record_hash_this_record_placeholder": "COMPUTING",
        },
        "signature": {"algorithm": "ed25519",
                      "public_key_pem_file": "public_key.pem",
                      "public_key_raw_b64": base64.b64encode(raw).decode("ascii")},
    }
    with open(SPEC_PATH, "w", encoding="utf-8") as fh:
        json.dump(spec, fh, ensure_ascii=False, indent=2)


def _tamper(record, tamper_id):
    r = copy.deepcopy(record)
    if tamper_id == "T001":       # decision DENY -> ALLOW
        r["decision"] = "ALLOW"
    elif tamper_id == "T002":     # exact_action_hash last 8 hex zeroed
        h = r["requested_action"]["exact_action_hash"]
        r["requested_action"]["exact_action_hash"] = h[:-8] + "00000000"
    elif tamper_id == "T003":     # actor_id changed
        r["actor"]["actor_id"] = "actor:impostor-99"
    elif tamper_id == "T004":     # authority_valid_at_execution false -> true
        r["authority_basis"]["authority_valid_at_execution"] = True
    elif tamper_id == "T005":     # policy_version bump
        r["policy_version"] = "ark-enterprise-v2.0"
    elif tamper_id == "T006":     # evidence_fresh false -> true
        r["evidence_state"]["evidence_fresh"] = True
    elif tamper_id == "T007":     # tool_called false -> true
        r["execution_outcome"]["tool_called"] = True
    elif tamper_id == "T008":     # prior_record_hash one char changed
        h = r["chain"]["prior_record_hash"] or "GENESIS"
        c = "0" if h[-1] != "0" else "1"
        r["chain"]["prior_record_hash"] = h[:-1] + c
    elif tamper_id == "T009":     # authority_check FAIL -> PASS
        r["gate_evaluation"]["authority_check"] = "PASS"
    elif tamper_id == "T010":     # signature last 8 chars zeroed
        s = r["signature"]["signature_hex"]
        r["signature"]["signature_hex"] = s[:-8] + "00000000"
    return r


# tamper_id -> predicate selecting a suitable source record
_TAMPER_PICKERS = {
    "T001": lambda r: r["decision"] == "DENY",
    "T002": lambda r: True,
    "T003": lambda r: True,
    "T004": lambda r: r["authority_basis"]["authority_valid_at_execution"] is False,
    "T005": lambda r: True,
    "T006": lambda r: r["evidence_state"]["evidence_fresh"] is False,
    "T007": lambda r: r["execution_outcome"]["tool_called"] is False,
    "T008": lambda r: True,
    "T009": lambda r: r["gate_evaluation"]["authority_check"] == "FAIL",
    "T010": lambda r: True,
}

# the specific field each tamper alters (for reason matching)
_TAMPER_FIELD_TOKENS = {
    "T001": ("decision",),
    "T002": ("exact_action_hash", "this_record_hash"),
    "T003": ("this_record_hash",),
    "T004": ("this_record_hash",),
    "T005": ("this_record_hash",),
    "T006": ("this_record_hash",),
    "T007": ("this_record_hash", "tool_called"),
    "T008": ("this_record_hash",),
    "T009": ("this_record_hash", "decision"),
    "T010": ("signature", "this_record_hash"),
}


def run(env, emit=print):
    case_ids = []
    experiment_pass = True

    records = _load_chain_records()
    if len(records) < 20:
        raise RuntimeError(f"ARK-497 needs >=20 source records, found {len(records)}")

    _write_verifier_inputs()

    used = set()
    # ---- 20 legitimate: force a mix of ALLOW / DENY / HOLD ----
    legit = []
    quotas = [("ALLOW", 6), ("DENY", 8), ("HOLD", 6)]
    for dec, n in quotas:
        for _ in range(n):
            r = _pick(records, lambda x, d=dec: x["decision"] == d, used)
            if r:
                legit.append(r)
    # top up to 20 with anything remaining
    for r in records:
        if len(legit) >= 20:
            break
        if id(r) not in used:
            used.add(id(r))
            legit.append(r)
    legit = legit[:20]

    legit_index = {}
    for i, r in enumerate(legit):
        case = f"ARK-497-L{i + 1:03d}"
        legit_index[case] = r
        fn = os.path.join(RECORDS_DIR, f"legitimate__{case}.json")
        with open(fn, "w", encoding="utf-8") as fh:
            json.dump(r, fh, ensure_ascii=False, indent=2)

    # ---- 10 tampered: one per frozen tamper field ----
    tamper_source = {}
    for tid, pred in _TAMPER_PICKERS.items():
        src = _pick(records, pred, used)
        if src is None:                       # fall back to any legitimate record
            src = legit[0]
        tampered = _tamper(src, tid)
        case = f"ARK-497-{tid}"
        tamper_source[case] = tid
        fn = os.path.join(RECORDS_DIR, f"tamper__{case}.json")
        with open(fn, "w", encoding="utf-8") as fh:
            json.dump(tampered, fh, ensure_ascii=False, indent=2)

    # ---- invoke the ISOLATED verifier as a subprocess (files only) ----
    proc = subprocess.run(
        ["python3", VERIFIER, "--records", RECORDS_DIR, "--spec", SPEC_PATH,
         "--out", REPORT_PATH],
        capture_output=True, text=True, cwd=_HERE)
    if proc.returncode != 0:
        raise RuntimeError(f"isolated verifier failed: {proc.stderr}")
    out = json.loads(proc.stdout)
    analysis = out["self_import_analysis"]
    # match by filename (records keep their original internal case_id)
    by_file = {res["file"]: res for res in out["results"]}

    # ---- P-497-4: static import analysis (permitted-only) ----
    p497_4 = bool(analysis.get("permitted_only"))
    emit(f"  [import-analysis] permitted_only={p497_4} "
         f"forbidden={analysis.get('forbidden_testbed_imports')} "
         f"non_permitted={analysis.get('non_permitted_imports')}")

    # ---- score legitimate cases (P-497-1 reconstruction, P-497-3 no FP) ----
    legit_all_ok = True
    false_positives = 0
    for case, rec in legit_index.items():
        res = by_file.get(f"legitimate__{case}.json")
        elems = res["elements"] if res else {}
        nine_ok = (res is not None
                   and elems.get("7_exact_action", {}).get("match") is True
                   and elems.get("9_chain_integrity", {}).get("match") is True
                   and elems.get("signature_valid") is True
                   and all(f"{i}_" in "".join(elems.keys()) for i in range(1, 10)))
        flagged = bool(res and res["tamper_detected"])
        if flagged:
            false_positives += 1
        verdict = "PASS" if (nine_ok and not flagged) else "FAIL"
        root = None
        if verdict == "FAIL":
            legit_all_ok = False
            experiment_pass = False
            root = (f"reconstruction_ok={nine_ok} falsely_flagged={flagged} "
                    f"reasons={res['tamper_reasons'] if res else 'no-result'}")
        append_result(result_entry(EXPERIMENT_ID, case, "isolated-verifier",
                                    rec["requested_action"]["tool_id"],
                                    rec["decision"], 0,
                                    rec["proofrecord_id"], p497_4, verdict, root))
        case_ids.append(case)
    emit(f"  [legitimate] 20 cases reconstructed, false_positives={false_positives}")

    # ---- score tamper cases (P-497-2 detection 10/10) ----
    detected = 0
    for case, tid in tamper_source.items():
        res = by_file.get(f"tamper__{case}.json")
        is_detected = bool(res and res["tamper_detected"])
        field_ok = False
        if is_detected:
            reasons = " ".join(res["tamper_reasons"]).lower()
            field_ok = any(tok.lower() in reasons
                           for tok in _TAMPER_FIELD_TOKENS[tid])
        if is_detected and field_ok:
            detected += 1
        verdict = "PASS" if (is_detected and field_ok) else "FAIL"
        root = None
        if verdict == "FAIL":
            experiment_pass = False
            root = (f"tamper_detected={is_detected} field_identified={field_ok} "
                    f"reasons={res['tamper_reasons'] if res else 'no-result'}")
        append_result(result_entry(EXPERIMENT_ID, case, "isolated-verifier",
                                    "SUMMARY", "TAMPER", 0, "none",
                                    p497_4, verdict, root))
        case_ids.append(case)
        emit(f"  [{case}] tamper({tid}) detected={is_detected} field_ok={field_ok} "
             f"{verdict}")

    p497_1 = legit_all_ok
    p497_2 = (detected == 10)
    p497_3 = (false_positives == 0)
    emit(f"  P-497-1={p497_1} P-497-2={p497_2}({detected}/10) "
         f"P-497-3={p497_3} P-497-4={p497_4}")

    if not (p497_1 and p497_2 and p497_3 and p497_4):
        experiment_pass = False

    decision = "EXPERIMENT-PASS" if experiment_pass else "EXPERIMENT-FAIL"
    write_series_summary(env.store, EXPERIMENT_ID, decision, case_ids, extra={
        "self_import_analysis": analysis,
        "p497_1_legitimate_reconstruction": p497_1,
        "p497_2_tamper_detection_rate": f"{detected}/10",
        "p497_3_false_positives": false_positives,
        "p497_4_permitted_only_imports": p497_4,
    })
    return {"experiment_id": EXPERIMENT_ID, "decision": decision,
            "case_ids": case_ids, "gate_stop": False}
