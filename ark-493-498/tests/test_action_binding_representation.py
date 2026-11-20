"""Regression tests (RT6/RT7 class) for the ARK-493-498 enforcement point:
caller-controlled Python subclasses must not satisfy action binding, gate hash
verification, policy-version or credential checks. Every case checks the decision
AND what was actually dispatched to the side-effect function.
Run from ark-493-498:  python3 tests/test_action_binding_representation.py"""
# --- sandbox guard: run in a temp copy so the published evidence tree is never written ---
import os as _os, shutil as _sh, sys as _sys, tempfile as _tf
if _os.environ.get("RF_ABRTEST_SANDBOX") != "1":
    _rel = _os.path.relpath(_os.path.abspath(_sys.argv[0]), _os.getcwd())
    _dst = _os.path.join(_tf.mkdtemp(prefix="rf_abrtest_"), "work")
    _sh.copytree(_os.getcwd(), _dst, ignore=_sh.ignore_patterns(".git", "__pycache__"))
    _os.environ["RF_ABRTEST_SANDBOX"] = "1"
    _os.chdir(_dst)
    _os.execv(_sys.executable, [_sys.executable, _os.path.join(_dst, _rel)])
# -----------------------------------------------------------------------------------------
import os, sys, json
sys.path.insert(0, os.getcwd())
from enforcement.proofstore import ProofStore
from experiments.common import build_env, EVIDENCE_FIELDS, TOOL_NAMES
from tools import tools as toolmod
env = build_env(ProofStore())


class EqStr(str):
    def __eq__(self, o): return True
    def __ne__(self, o): return False
    __hash__ = str.__hash__

class EncStr(str):
    def __new__(cls, content, other):
        s = str.__new__(cls, content); s._other = other; return s
    def encode(self, *a, **k): return str.encode(self._other, *a, **k)
    def __deepcopy__(self, memo): return self

class BenignStr(str):
    pass

APPROVED_P = {"target": "T1-resource", "amount": "100.00", "note": "abr"}
MUTATED_P = {"target": "ATTACKER-resource", "amount": "999999.00", "note": "abr"}

def build(params, approved_hash=None):
    return env.agent.build_action(actor_id="actor:payments-agent-01", tool_id="T1",
        tool_name=TOOL_NAMES["T1"], parameters=dict(params),
        policy_version=env.policy.active_version,
        evidence=env.agent.fresh_evidence(EVIDENCE_FIELDS), approved_hash=approved_hash)

APPROVED = build(APPROVED_P)
H, C = APPROVED["exact_action_hash"], APPROVED["canonical_json"]

def c1(): return build(APPROVED_P)
def rt6():
    a = build(MUTATED_P, approved_hash=H); a["canonical_json"] = EqStr(C); a["exact_action_hash"] = H; return a
def rt7():
    a = build(MUTATED_P); a["approved_hash"] = EqStr(H); return a
def rt8():
    a = build(MUTATED_P, approved_hash=H)
    a["canonical_json"] = EncStr(a["canonical_json"], C); a["exact_action_hash"] = H; return a
def rt10():
    a = build(APPROVED_P); a["policy_version"] = EqStr("policy-v0-retired"); return a
def rt11():
    a = build(APPROVED_P); a["credential_token"] = EqStr("not-the-credential"); return a
def rt12():  # alias lookup: caller-controlled key with str.__hash__ but lying __eq__
    a = build(APPROVED_P); a["tool_alias"] = BenignStr("payment_dispatch"); return a
def b1():
    a = build(APPROVED_P); a["canonical_json"] = BenignStr(a["canonical_json"]); return a

cases = [
    ("C1_control_approved", c1, "ALLOW", [("T1", APPROVED_P)]),
    ("RT6_canonical_json_ne_lie_param_mutation", rt6, "DENY", []),
    ("RT7_approved_hash_eq_lie", rt7, "DENY", []),
    ("RT8_canonical_json_encode_lie", rt8, "DENY", []),
    ("RT10_policy_version_eq_lie", rt10, "DENY", []),
    ("RT11_credential_token_eq_lie", rt11, "DENY", []),
    ("B1_benign_subclass_canonical_json", b1, "DENY", []),
    ("B2_benign_subclass_tool_alias", rt12, "DENY", []),
]
fails = 0
for name, fn, want, want_seen in cases:
    a = fn()
    seen, orig = [], toolmod.perform_side_effect
    toolmod.perform_side_effect = lambda t, p: (seen.append((t, json.loads(json.dumps(p)))), orig(t, p))[1]
    try:
        d = env.ep.submit(a, "ABR493-" + name, "ACTION-BINDING-REPR").get("decision")
    except Exception as exc:
        d = f"EXCEPTION:{type(exc).__name__}"
    finally:
        toolmod.perform_side_effect = orig
    ok = d == want and [(t, p) for t, p in seen] == [(t, dict(p)) for t, p in want_seen]
    fails += not ok
    print(f"{'PASS' if ok else 'FAIL'} {name}: {d} dispatched={seen}")
print(f"RESULT {len(cases) - fails}/{len(cases)} PASS" + ("" if not fails else f" ({fails} FAIL)"))
sys.exit(1 if fails else 0)
