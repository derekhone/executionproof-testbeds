"""ARK-501 token-REPRESENTATION regression (R10 class): an untrusted credential
object must not validate as one subject while dispatching as another. Reproduces
the str-subclass mechanism reported by Matthew Visher with Claude (Anthropic) in
PR #36 (static read + standalone script; NOT run against this harness by him),
through the real ARK-501 enforcement path with synthetic identities only.
Run from the ark-499-503 directory:  python3 tests/test_token_representation_oidc.py
"""
# --- sandbox guard: run in a temp copy so the published evidence tree is never written ---
import os as _os, shutil as _sh, sys as _sys, tempfile as _tf
if _os.environ.get("RF_REPRTEST_SANDBOX") != "1":
    _rel = _os.path.relpath(_os.path.abspath(_sys.argv[0]), _os.getcwd())
    _dst = _os.path.join(_tf.mkdtemp(prefix="rf_reprtest_"), "work")
    _sh.copytree(_os.getcwd(), _dst, ignore=_sh.ignore_patterns(".git", "__pycache__"))
    _os.environ["RF_REPRTEST_SANDBOX"] = "1"
    _os.chdir(_dst)
    _os.execv(_sys.executable, [_sys.executable, _os.path.join(_dst, _rel)])
# -----------------------------------------------------------------------------------------
import os, sys, time, inspect
sys.path.insert(0, os.getcwd())
from gate.core import POLICY_VERSION
from gate.actor_registry import ActorRegistry
from gate.policy import PolicyStore
from gate.gate import ExecutionProofGate
from enforcement.proofstore import ProofStore
from enforcement.real_enforcement_point import RealEnforcementPoint
from actor.actor_agent import ActorAgent
from adapters.oidc_adapter import OIDCAdapter
from common import fresh_evidence

EV = ["security_scan", "reviewer_approval"]
INFRA, SUB = "actor:infra-agent-01", "infra-agent-01"
OTHER = "ops-agent-99"

ad = OIDCAdapter(); ad.setup()
reg = ActorRegistry(); gate = ExecutionProofGate(reg, PolicyStore())
kw = dict(identity_validator=lambda a: ad.validate_token(a.get("access_token")))
if "subject_for_actor" in inspect.signature(RealEnforcementPoint.__init__).parameters:
    kw["subject_for_actor"] = lambda actor_id: (
        actor_id[len("actor:"):] if isinstance(actor_id, str) and actor_id.startswith("actor:") else None)
ep = RealEnforcementPoint(gate, ProofStore(guard_b_mode="inline"), ad, **kw)
agent = ActorAgent(reg)

def tok(sub):
    return ad.issue_token(sub, ["deploy"], ttl_seconds=300)[0]

# --- hostile credential representations -------------------------------------
class FmtTok(str):
    """underlying value validates as `self`; __format__ emits a different token."""
    def __new__(cls, underlying, formatted):
        o = super().__new__(cls, underlying); o._f = formatted; return o
    def __format__(self, spec):
        return self._f

class EqFmtTok(FmtTok):
    """also claims equality to everything, to defeat a `!=` substitution check."""
    def __eq__(self, other):
        return True
    def __ne__(self, other):
        return False
    __hash__ = str.__hash__

def action(token, note, evidence=None):
    a = agent.build_action(actor_id=INFRA, tool_id="T4", tool_name="privileged_resource_access",
        parameters={"resource": "prod-secret-store", "note": note}, policy_version=POLICY_VERSION,
        evidence=evidence if evidence is not None else fresh_evidence(EV))
    a["access_token"] = token
    return a

def run(name, token, want_decision):
    before = ad.access_count()
    try:
        rec = ep.submit(action(token, name), "REPR501-" + name, "REPR-REGRESSION-501")
        decision = rec["decision"]
        dg = bool(rec["verification"].get("dual_guard_agreement"))
    except Exception as exc:  # a crash is NOT a safe DENY
        return False, f"RAISED {type(exc).__name__}: {exc}"
    new = ad.access_entries()[before:]
    subs = [e["sub"] for e in new]
    leaked = [s for s in subs if s == OTHER]
    # PASS only if: decision matches, zero grants, no ops-agent-99 ever reached the RS,
    # the signed record does not falsely claim a subject match, and guards agree.
    ext = (rec.get("authority_basis") or {}).get("external_identity") or {}
    false_claim = bool(ext.get("subject_matches_actor")) and decision != "ALLOW"
    ok = (decision == want_decision and len(new) == 0 and not leaked
          and not false_claim and dg)
    return ok, f"{decision} grants={len(new)} rs_subjects={subs} false_match_claim={false_claim}"

cases = [
    ("R01_plain_str_match",                 lambda: tok(SUB),                               "ALLOW"),
    ("R02_fmt_subclass_infra_to_ops",       lambda: FmtTok(tok(SUB), tok(OTHER)),           "DENY"),
    ("R03_eq_fmt_subclass_defeats_neq",     lambda: EqFmtTok(tok(SUB), tok(OTHER)),         "DENY"),
    ("R04_benign_subclass_still_rejected",  lambda: FmtTok(tok(SUB), tok(SUB)),             "DENY"),
    ("R05_bytes_token",                     lambda: tok(SUB).encode(),                      "DENY"),
]
# R01 is the positive control: a plain str must still ALLOW with exactly one grant.
fails = 0
for name, mk, want in cases:
    if name == "R01_plain_str_match":
        before = ad.access_count()
        rec = ep.submit(action(mk(), name), "REPR501-" + name, "REPR-REGRESSION-501")
        new = ad.access_entries()[before:]
        ok = rec["decision"] == "ALLOW" and len(new) == 1 and new[0]["sub"] == SUB \
            and bool(rec["verification"].get("dual_guard_agreement"))
        info = f"{rec['decision']} grants={len(new)} rs_subjects={[e['sub'] for e in new]}"
    else:
        ok, info = run(name, mk(), want)
    fails += not ok
    print(f"{'PASS' if ok else 'FAIL'} {name}: {info}")

n = len(cases)
ad.teardown()
print(f"RESULT {n - fails}/{n} PASS" + ("" if not fails else f" ({fails} FAIL)"))
sys.exit(1 if fails else 0)
