"""Regression tests: ARK-501 authority-to-identity binding (token subject vs the
gate-approved actor). Uses the REAL local RS256 issuer + JWKS + protected resource
server from adapters/oidc_adapter.py, with synthetic identities only. Writes only
/tmp/ark501_oidc (the adapter's sandbox) and a temporary copy of this directory.
Run from the ark-499-503 directory:  python3 tests/test_identity_binding_oidc.py
Finding credited to Matthew Visher (PR #35 review comment, static read)."""
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
import os, sys, time, inspect
import jwt
sys.path.insert(0, os.getcwd())
from gate.core import POLICY_VERSION
from gate.actor_registry import ActorRegistry
from gate.policy import PolicyStore
from gate.gate import ExecutionProofGate
from enforcement.proofstore import ProofStore
from enforcement.real_enforcement_point import RealEnforcementPoint
from actor.actor_agent import ActorAgent
from adapters.oidc_adapter import OIDCAdapter, ISSUER, KID
from common import fresh_evidence

EV = ["security_scan", "reviewer_approval"]
INFRA, SUB = "actor:infra-agent-01", "infra-agent-01"
OTHER = "ops-agent-99"                 # not a registered actor
OTHER_REG = "payments-agent-01"        # a registered actor with no T4 authority

ad = OIDCAdapter(); ad.setup()
reg = ActorRegistry(); gate = ExecutionProofGate(reg, PolicyStore())
VALIDATOR = {"fn": lambda a: ad.validate_token(a.get("access_token"))}
kw = dict(identity_validator=lambda a: VALIDATOR["fn"](a))
if "subject_for_actor" in inspect.signature(RealEnforcementPoint.__init__).parameters:
    kw["subject_for_actor"] = lambda actor_id: (
        actor_id[len("actor:"):] if isinstance(actor_id, str) and actor_id.startswith("actor:") else None)
ep = RealEnforcementPoint(gate, ProofStore(guard_b_mode="inline"), ad, **kw)
agent = ActorAgent(reg)

def raw_token(claims, forged=False):
    now = int(time.time())
    base = {"iss": ISSUER, "roles": ["deploy"], "iat": now, "nbf": now, "exp": now + 300,
            "jti": f"jti-test-{os.urandom(4).hex()}"}
    base.update(claims)
    base = {k: v for k, v in base.items() if v is not None}
    key = ad._foreign_priv_pem if forged else ad._priv_pem
    return jwt.encode(base, key, algorithm="RS256", headers={"kid": KID})

def tok(sub, roles=("deploy",)):
    return ad.issue_token(sub, list(roles), ttl_seconds=300)[0]

def action(token, note, evidence=None):
    a = agent.build_action(actor_id=INFRA, tool_id="T4", tool_name="privileged_resource_access",
        parameters={"resource": "prod-secret-store", "note": note}, policy_version=POLICY_VERSION,
        evidence=evidence if evidence is not None else fresh_evidence(EV))
    a["access_token"] = token
    return a

NO_EV = lambda: {"required_evidence_fields": EV, "evidence_snapshot": {},
                 "evidence_timestamp": fresh_evidence(EV)["evidence_timestamp"]}

def swap_after_validation(new_token):
    def fn(a):
        res = ad.validate_token(a.get("access_token"))
        a["access_token"] = new_token          # in-process substitution after validation
        return res
    return fn

RECS = {}
def run(name, token, want, want_grants, evidence=None, validator=None):
    VALIDATOR["fn"] = validator or (lambda a: ad.validate_token(a.get("access_token")))
    before = ad.access_count()
    rec = ep.submit(action(token, name, evidence), "BIND501-" + name, "BINDING-REGRESSION-501")
    VALIDATOR["fn"] = lambda a: ad.validate_token(a.get("access_token"))
    new = ad.access_entries()[before:]
    grants = len(new)
    subs = [e["sub"] for e in new]
    ok = rec["decision"] == want and grants == want_grants and \
        all(s == SUB for s in subs) and bool(rec["verification"].get("dual_guard_agreement"))
    RECS[name] = rec
    return ok, f"{rec['decision']} grants={grants} rs_subjects={subs}"

cases = [
 ("I01_matching_subject",            lambda: tok(SUB),                       "ALLOW", 1, None, None),
 ("I02_other_subject_deploy",        lambda: tok(OTHER),                     "DENY", 0, None, None),
 ("I03_other_registered_actor_sub",  lambda: tok(OTHER_REG),                 "DENY", 0, None, None),
 ("I04_correct_sub_wrong_role",      lambda: tok(SUB, ["viewer"]),           "DENY", 0, None, None),
 ("I05_expired",                     lambda: ad.issue_token(SUB, ["deploy"], ttl_seconds=1, issued_offset=-3600)[0], "DENY", 0, None, None),
 ("I06_forged_signature",            lambda: tok(SUB) and ad.issue_token(SUB, ["deploy"], forged=True)[0], "DENY", 0, None, None),
 ("I07_swap_after_validation",       lambda: tok(SUB),                       "DENY", 0, None, "swap"),
 ("I08_missing_subject",             lambda: raw_token({"sub": None}),       "DENY", 0, None, None),
 ("I09_empty_subject",               lambda: raw_token({"sub": ""}),         "DENY", 0, None, None),
 ("I10_no_token",                    lambda: None,                           "DENY", 0, None, None),
 ("I11_other_audience",              lambda: raw_token({"sub": SUB, "aud": "https://other-rs.local"}), "DENY", 0, None, None),
 ("I12_other_issuer",                lambda: raw_token({"sub": SUB, "iss": "https://other-issuer.local"}), "DENY", 0, None, None),
 ("I13_missing_evidence_match_sub",  lambda: tok(SUB),                       "HOLD", 0, "noev", None),
 ("I14_missing_evidence_other_sub",  lambda: tok(OTHER),                     "DENY", 0, "noev", None),
]
fails = 0
for name, mk, want, g, ev, val in cases:
    validator = swap_after_validation(tok(OTHER)) if val == "swap" else None
    ok, info = run(name, mk(), want, g, NO_EV() if ev == "noev" else None, validator)
    fails += not ok; print(f"{'PASS' if ok else 'FAIL'} {name}: {info}")

# proof integrity: the validated subject must be inside the SIGNED record (authority_basis)
def ext(rec):
    return (rec.get("authority_basis") or {}).get("external_identity")
p1 = ext(RECS["I01_matching_subject"]) or {}
ok = p1.get("subject") == SUB and p1.get("bound_actor_id") == INFRA and p1.get("subject_matches_actor") is True \
     and "authority_basis" in RECS["I01_matching_subject"]["signature"]["signed_fields"]
fails += not ok; print(f"{'PASS' if ok else 'FAIL'} P01_signed_record_binds_subject_on_allow: external_identity={p1 or None}")
p2 = ext(RECS["I02_other_subject_deploy"]) or {}
ok = p2.get("subject") == OTHER and p2.get("subject_matches_actor") is False
fails += not ok; print(f"{'PASS' if ok else 'FAIL'} P02_signed_record_shows_mismatch_on_deny: external_identity={p2 or None}")
n = len(cases) + 2
ad.teardown()
print(f"RESULT {n - fails}/{n} PASS" + ("" if not fails else f" ({fails} FAIL)"))
sys.exit(1 if fails else 0)
