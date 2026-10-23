"""Regression tests: ARK-493-498 execution-identity binding (proposed, 2026-10-23).
Run from the ark-493-498 directory:  python3 tests/test_execution_binding.py
Exit 0 iff every control is ALLOW with exactly the approved parameters dispatched
and every attack is DENY/HOLD with nothing dispatched."""
# --- sandbox guard: run in a temp copy so the published evidence tree is never written ---
import os as _os, shutil as _sh, sys as _sys, tempfile as _tf
if _os.environ.get("RF_BINDTEST_SANDBOX") != "1":
    _rel = _os.path.relpath(_os.path.abspath(_sys.argv[0]), _os.getcwd())
    _dst = _os.path.join(_tf.mkdtemp(prefix="rf_bindtest_"), "work")
    _sh.copytree(_os.getcwd(), _dst, ignore=_sh.ignore_patterns(".git", "__pycache__"))
    _os.environ["RF_BINDTEST_SANDBOX"] = "1"
    _os.chdir(_dst)
    _os.execv(_sys.executable, [_sys.executable, _os.path.join(_dst, _rel)])
# -----------------------------------------------------------------------------------------
import os, sys, json, unicodedata
sys.path.insert(0, os.getcwd())
from enforcement.proofstore import ProofStore
from experiments.common import build_env, EVIDENCE_FIELDS, TOOL_NAMES
from tools import tools as toolmod
env = build_env(ProofStore())
NFC = unicodedata.normalize("NFC", "Caf\u00e9-Acct")
NFD = unicodedata.normalize("NFD", "Caf\u00e9-Acct")
BASE = {"target": "T1-resource", "amount": "100.00", "note": "binding-regression"}

def run(label, tool_id="T1", params=None, post=None):
    params = dict(BASE) if params is None else params
    act = env.agent.build_action(actor_id="actor:payments-agent-01", tool_id=tool_id,
        tool_name=TOOL_NAMES[tool_id], parameters=params,
        policy_version=env.policy.active_version,
        evidence=env.agent.fresh_evidence(EVIDENCE_FIELDS))
    approved = act["canonical_json"]
    if post: post(act)
    seen, orig = [], toolmod.perform_side_effect
    toolmod.perform_side_effect = lambda t, p: (seen.append((t, json.loads(json.dumps(p)))), orig(t, p))[1]
    try:
        rec = env.ep.submit(act, "BINDREG-" + label, "BINDING-REGRESSION")
    finally:
        toolmod.perform_side_effect = orig
    return rec.get("decision"), seen, approved

def approved_equals_dispatch(approved, seen, tool_id):
    if len(seen) != 1 or seen[0][0] != tool_id:
        return False
    p = dict(seen[0][1]); p["tool_id"] = tool_id; p["tool_name"] = TOOL_NAMES[tool_id]
    return json.dumps(p, sort_keys=True, separators=(",", ":"), ensure_ascii=False) == approved

CONTROLS = {
 "C1_baseline":            dict(),
 "C2_nfc_unicode":         dict(params={"target": NFC, "amount": "100.00"}),
 "C3_consistent_alias":    dict(post=lambda a: a.update(tool_alias="payment_dispatch")),
 "C4_nested_list_param":   dict(params={"target": "T1-resource", "amount": "1.00", "legs": ["a", {"b": 1}]}),
}
ATTACKS = {
 "A1_target_substitution": dict(post=lambda a: a["parameters"].update(target="ATTACKER-resource")),
 "A2_amount_substitution": dict(post=lambda a: a["parameters"].update(amount="999999.00")),
 "A3_extra_parameter":     dict(post=lambda a: a["parameters"].update(beneficiary="ATTACKER")),
 "A4_removed_parameter":   dict(post=lambda a: a["parameters"].pop("note")),
 "A5_type_change":         dict(post=lambda a: a["parameters"].update(amount=100.0)),
 "A6_tool_name_swap":      dict(post=lambda a: a.update(tool_name="something_else")),
 "R1_param_named_tool_id":   dict(params={"target": "T1-resource", "amount": "100.00", "tool_id": "T4"}),
 "R2_param_named_tool_name": dict(params={"target": "T1-resource", "amount": "100.00", "tool_name": "access_modifier"}),
 "R3_nfd_value_from_actor":  dict(params={"target": NFD, "amount": "100.00"}),
 "R4_nfc_approved_nfd_sent": dict(params={"target": NFC, "amount": "100.00"},
                                  post=lambda a: a["parameters"].update(target=NFD)),
 "R5_nfd_key":               dict(params={unicodedata.normalize("NFD", "b\u00e9neficiary"): "X", "amount": "1.00"}),
 "R6_alias_tool_substitution": dict(tool_id="T3", params={"target": "T3-resource", "amount": "100.00"},
                                    post=lambda a: a.update(tool_alias="payment_dispatch")),
 "R7_tuple_for_list":        dict(params={"target": "T1-resource", "amount": "1.00", "legs": ["a", "b"]},
                                  post=lambda a: a["parameters"].update(legs=("a", "b"))),
}
fails = 0
for name, kw in CONTROLS.items():
    d, seen, appr = run(name, **kw)
    ok = d == "ALLOW" and approved_equals_dispatch(appr, seen, kw.get("tool_id", "T1"))
    fails += not ok; print(f"{'PASS' if ok else 'FAIL'} {name}: {d} dispatched={seen}")
for name, kw in ATTACKS.items():
    d, seen, appr = run(name, **kw)
    ok = d in ("DENY", "HOLD") and seen == []
    fails += not ok; print(f"{'PASS' if ok else 'FAIL'} {name}: {d} dispatched={seen}")
total = len(CONTROLS) + len(ATTACKS)
print(f"RESULT {total - fails}/{total} PASS" + ("" if not fails else f" ({fails} FAIL)"))
sys.exit(1 if fails else 0)
