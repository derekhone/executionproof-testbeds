"""Regression tests (RT6/RT7 class): caller-controlled Python subclasses must not
be able to satisfy action/target binding, gate hash verification, policy-version
or credential checks. Uses the REAL local git CI/CD adapter (ARK-500 path; no
PostgreSQL). Every case checks the decision AND the real side effect (what was
actually deployed to staging/production). Writes only /tmp/ark500_cicd and a temp
copy of this directory. Run from ark-499-503:  python3 tests/test_action_binding_representation.py"""
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
from gate.core import POLICY_VERSION
from gate.actor_registry import ActorRegistry
from gate.policy import PolicyStore
from gate.gate import ExecutionProofGate
from enforcement.proofstore import ProofStore
from enforcement.real_enforcement_point import RealEnforcementPoint
from actor.actor_agent import ActorAgent
from adapters.cicd_adapter import CICDAdapter, ENVS
from common import fresh_evidence

EV = ["security_scan", "reviewer_approval"]; INFRA = "actor:infra-agent-01"
ad = CICDAdapter(); ad.setup()
reg = ActorRegistry(); gate = ExecutionProofGate(reg, PolicyStore())
ep = RealEnforcementPoint(gate, ProofStore(guard_b_mode="inline"), ad); agent = ActorAgent(reg)
APPR = ad.artifacts["approved"]["digest"]


class EqStr(str):        # claims equality with anything (RT7, RT10, RT11)
    def __eq__(self, o): return True
    def __ne__(self, o): return False
    __hash__ = str.__hash__

class NeStr(EqStr):      # RT6: same lie, used on canonical_json
    pass

class EncStr(str):       # RT8: content is one string, UTF-8 bytes are another
    def __new__(cls, content, other):
        s = str.__new__(cls, content); s._other = other; return s
    def encode(self, *a, **k): return str.encode(self._other, *a, **k)
    def __deepcopy__(self, memo): return self

class BenignStr(str):    # behaves exactly like str; still not an exact str
    pass


def deployed(env):
    p = os.path.join(ENVS, env, "MANIFEST.json")
    return json.load(open(p))["digest"] if os.path.exists(p) else None

def _clear():
    for e in ("staging", "production"):
        p = os.path.join(ENVS, e, "MANIFEST.json")
        if os.path.exists(p): os.remove(p)

def build(env, approved_hash=None, note="rt"):
    return agent.build_action(actor_id=INFRA, tool_id="T3", tool_name="cicd_deploy",
        parameters={"artifact_digest": APPR, "environment": env, "note": note},
        policy_version=POLICY_VERSION, evidence=fresh_evidence(EV),
        approved_hash=approved_hash)

# The approval the caller actually holds: staging only.
APPROVED = build("staging")
H_STAGE, C_STAGE = APPROVED["exact_action_hash"], APPROVED["canonical_json"]

def c1():            # control: the approved staging action itself
    return build("staging")
def rt6():           # mutated params; canonical_json is the approved text but lies on !=
    a = build("production", approved_hash=H_STAGE)
    a["canonical_json"] = NeStr(C_STAGE); a["exact_action_hash"] = H_STAGE; return a
def rt7():           # honest mutated canonical; approved_hash lies on ==
    a = build("production"); a["approved_hash"] = EqStr(H_STAGE); return a
def rt7b():          # honest mutated canonical; declared + approved both lie
    a = build("production"); a["approved_hash"] = EqStr(H_STAGE)
    a["exact_action_hash"] = EqStr(H_STAGE); return a
def rt8():           # canonical_json content = mutated, its encode() = approved bytes
    a = build("production", approved_hash=H_STAGE)
    a["canonical_json"] = EncStr(a["canonical_json"], C_STAGE)
    a["exact_action_hash"] = H_STAGE; return a
def rt10():          # stale policy version that claims equality with the active one
    a = build("staging"); a["policy_version"] = EqStr("policy-v0-retired"); return a
def rt11():          # wrong credential that claims equality with the registered one
    a = build("staging"); a["credential_token"] = EqStr("not-the-credential"); return a
def b1():            # benign str subclass on canonical_json (no lie): exact-type policy
    a = build("staging"); a["canonical_json"] = BenignStr(a["canonical_json"]); return a
def b2():            # benign str subclass on tool_id
    a = build("staging"); a["tool_id"] = BenignStr("T3"); return a

cases = [  # (name, builder, expected decision, expected staging, expected production)
    ("C1_control_approved_staging", c1, "ALLOW", APPR, None),
    ("RT6_canonical_json_ne_lie_param_mutation", rt6, "DENY", None, None),
    ("RT7_approved_hash_eq_lie", rt7, "DENY", None, None),
    ("RT7b_declared_and_approved_eq_lie", rt7b, "DENY", None, None),
    ("RT8_canonical_json_encode_lie", rt8, "DENY", None, None),
    ("RT10_policy_version_eq_lie", rt10, "DENY", None, None),
    ("RT11_credential_token_eq_lie", rt11, "DENY", None, None),
    ("B1_benign_subclass_canonical_json", b1, "DENY", None, None),
    ("B2_benign_subclass_tool_id", b2, "DENY", None, None),
]
fails = 0
for name, fn, want, st, pr in cases:
    _clear()
    a = fn()
    try:
        rec = ep.submit(a, "ABR-" + name, "ACTION-BINDING-REPR")
        d = rec["decision"]
    except Exception as exc:  # a crash is not a pass
        d = f"EXCEPTION:{type(exc).__name__}"
    s, p = deployed("staging"), deployed("production")
    ok = (d == want) and s == st and p == pr
    fails += not ok
    print(f"{'PASS' if ok else 'FAIL'} {name}: {d} staging={s and s[:12]} production={p and p[:12]}")
print(f"RESULT {len(cases) - fails}/{len(cases)} PASS" + ("" if not fails else f" ({fails} FAIL)"))
sys.exit(1 if fails else 0)
