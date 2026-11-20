"""Regression tests: ARK-499-503 execution-identity binding via the REAL local
git CI/CD adapter (ARK-500 path; no PostgreSQL needed). Writes only /tmp/ark500_cicd
(the adapter's sandbox) and a temporary copy of this directory. Run from the ark-499-503 directory:  python3 tests/test_execution_binding_cicd.py"""
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
APPR, TAMP = ad.artifacts["approved"]["digest"], ad.artifacts["tampered"]["digest"]
def deployed(env):
    p = os.path.join(ENVS, env, "MANIFEST.json")
    return json.load(open(p))["digest"] if os.path.exists(p) else None
def run(label, params=None, post=None):
    for e in ("staging", "production"):
        p = os.path.join(ENVS, e, "MANIFEST.json")
        if os.path.exists(p): os.remove(p)
    params = params or {"artifact_digest": APPR, "environment": "staging", "note": label}
    a = agent.build_action(actor_id=INFRA, tool_id="T3", tool_name="cicd_deploy",
        parameters=params, policy_version=POLICY_VERSION, evidence=fresh_evidence(EV))
    if post: post(a)
    rec = ep.submit(a, "BIND499-" + label, "BINDING-REGRESSION-499")
    return rec["decision"], deployed("staging"), deployed("production")
NFD = unicodedata.normalize("NFD", "st\u00e9ging-note")
class _SubDict(dict):  # serializes as approved, but the adapter reads environment=production
    def __getitem__(self, k):
        return "production" if k == "environment" else dict.__getitem__(self, k)
    def get(self, k, d=None):
        return "production" if k == "environment" else dict.get(self, k, d)
cases = [
 ("C1_baseline_staging", {}, "ALLOW", APPR, None),
 ("A1_env_to_production", dict(post=lambda a: a["parameters"].update(environment="production")), "DENY", None, None),
 ("A2_artifact_to_tampered", dict(post=lambda a: a["parameters"].update(artifact_digest=TAMP)), "DENY", None, None),
 ("A3_extra_parameter", dict(post=lambda a: a["parameters"].update(force="true")), "DENY", None, None),
 ("A4_dict_subclass_after_approval", dict(post=lambda a: a.update(parameters=_SubDict(a["parameters"]))), "DENY", None, None),
 ("R1_param_named_tool_id", dict(params={"artifact_digest": APPR, "environment": "staging", "tool_id": "T4"}), "DENY", None, None),
 ("R4_nfd_note_after_approval", dict(params={"artifact_digest": APPR, "environment": "staging",
      "note": unicodedata.normalize("NFC", NFD)}, post=lambda a: a["parameters"].update(note=NFD)), "DENY", None, None),
]
fails = 0
for name, kw, want, st, pr in cases:
    d, s, p = run(name, **kw)
    ok = (d == want) if want == "ALLOW" else (d in ("DENY", "HOLD"))
    ok = ok and s == st and p == pr
    fails += not ok; print(f"{'PASS' if ok else 'FAIL'} {name}: {d} staging={s and s[:12]} production={p and p[:12]}")
print(f"RESULT {len(cases) - fails}/{len(cases)} PASS" + ("" if not fails else f" ({fails} FAIL)"))
sys.exit(1 if fails else 0)
