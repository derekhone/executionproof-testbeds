"""
experiments/run_496.py — ARK-496 Multi-Agent Delegation and Self-Approval Defense.

Proves no agent can create, inherit, or expand authority via delegation,
self-approval, or collusion. Delegation tokens are ed25519-signed with the
testbed key. The gate checks: signature validity, allowed_tools subset of the
delegator's own authority, non-expiry, requesting-actor != approving-actor at
every chain link, and shared-credential collusion (two approvals with identical
credential_token_hash count as one).
"""
from datetime import datetime, timezone, timedelta

from experiments.common import (
    append_result, result_entry, executed_count_for_case, write_series_summary,
    sign_delegation, EVIDENCE_FIELDS, TOOL_NAMES,
)
from gate.core import POLICY_VERSION, now_utc, canonical_json, sha256_hex

EXPERIMENT_ID = "ARK-496"


def _ts(offset_seconds):
    t = datetime.now(timezone.utc) + timedelta(seconds=offset_seconds)
    return t.strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"


def run(env, emit=print):
    case_ids = []
    experiment_pass = True
    ag = env.agent

    def submit_and_score(case_id, act, expected, tool_id, *,
                         need_chain=False, need_selfapproval=False):
        nonlocal experiment_pass
        rec = env.ep.submit(act, case_id, EXPERIMENT_ID)
        executed = executed_count_for_case(tool_id, case_id)
        v = rec["verification"]
        dual_ok = bool(v.get("dual_guard_agreement")) and \
            v.get("guard_a_result") == "PASS" and v.get("guard_b_result") == "PASS"
        exec_ok = (executed == 1) if expected == "ALLOW" else (executed == 0)
        chain_ok = True
        if need_chain:
            chain_ok = len(rec["authority_basis"]["delegator_chain"]) >= 1
        selfapp_ok = True
        if need_selfapproval:
            selfapp_ok = "self-approval" in rec["decision_reason"].lower()
        verdict = "PASS" if (rec["decision"] == expected and exec_ok and dual_ok
                             and chain_ok and selfapp_ok) else "FAIL"
        root = None
        if verdict == "FAIL":
            root = (f"decision={rec['decision']} expected={expected} exec={executed} "
                    f"dual={dual_ok} chain={chain_ok} selfapproval={selfapp_ok}")
            experiment_pass = False
        append_result(result_entry(EXPERIMENT_ID, case_id, "P1-direct-call", tool_id,
                                    rec["decision"], executed, rec["proofrecord_id"],
                                    dual_ok, verdict, root))
        case_ids.append(case_id)
        emit(f"  [{case_id}] {expected}->{rec['decision']} exec={executed} "
             f"dual={dual_ok} {verdict}")
        return rec

    ev = lambda: ag.fresh_evidence(EVIDENCE_FIELDS, 0)

    # ---- CONTROL: valid delegation orchestrator -> executor for T3 ----
    env.registry.reset(); env.policy.reset()
    tok = sign_delegation("actor:orchestrator-01", "actor:executor-01", ["T3"],
                          now_utc(), _ts(3600))
    act = ag.build_action(actor_id="actor:executor-01", tool_id="T3",
                          tool_name=TOOL_NAMES["T3"], parameters={"app": "svc-a"},
                          policy_version=POLICY_VERSION, evidence=ev(),
                          delegation_token=tok, delegated_by="actor:orchestrator-01")
    submit_and_score("ARK-496-CONTROL", act, "ALLOW", "T3", need_chain=True)

    # ---- A001: delegate T1 (beyond orchestrator's T3/T4 authority) ----
    env.registry.reset(); env.policy.reset()
    tok = sign_delegation("actor:orchestrator-01", "actor:specialist-01", ["T1"],
                          now_utc(), _ts(3600))
    act = ag.build_action(actor_id="actor:specialist-01", tool_id="T1",
                          tool_name=TOOL_NAMES["T1"], parameters={"amount": 10},
                          policy_version=POLICY_VERSION, evidence=ev(),
                          delegation_token=tok, delegated_by="actor:orchestrator-01")
    submit_and_score("ARK-496-A001", act, "DENY", "T1")

    # ---- A002: specialist claims T2 by asserting inheritance ----
    env.registry.reset(); env.policy.reset()
    act = ag.build_action(actor_id="actor:specialist-01", tool_id="T2",
                          tool_name=TOOL_NAMES["T2"], parameters={"table": "orders"},
                          policy_version=POLICY_VERSION, evidence=ev(),
                          claimed_inheritance=True)
    submit_and_score("ARK-496-A002", act, "DENY", "T2")

    # ---- A003: self-approval (direct) ----
    env.registry.reset(); env.policy.reset()
    act = ag.build_action(actor_id="actor:self-approver-01", tool_id="T1",
                          tool_name=TOOL_NAMES["T1"], parameters={"amount": 99},
                          policy_version=POLICY_VERSION, evidence=ev(),
                          approver_id="actor:self-approver-01")
    submit_and_score("ARK-496-A003", act, "DENY", "T1", need_selfapproval=True)

    # ---- A004: self-approval (delegated loop) ----
    env.registry.reset(); env.policy.reset()
    tok = sign_delegation("actor:self-approver-01", "actor:self-approver-01", ["T1"],
                          now_utc(), _ts(3600))
    act = ag.build_action(actor_id="actor:self-approver-01", tool_id="T1",
                          tool_name=TOOL_NAMES["T1"], parameters={"amount": 99},
                          policy_version=POLICY_VERSION, evidence=ev(),
                          delegation_token=tok, delegated_by="actor:self-approver-01")
    submit_and_score("ARK-496-A004", act, "DENY", "T1",
                     need_chain=True, need_selfapproval=True)

    # ---- A005: colluding agents share one credential ----
    env.registry.reset(); env.policy.reset()
    shared_hash = env.registry.credential_hash("actor:colluder-A")
    approvals = [
        {"actor_id": "actor:colluder-A", "credential_token_hash": shared_hash},
        {"actor_id": "actor:colluder-B", "credential_token_hash": shared_hash},
    ]
    act = ag.build_action(actor_id="actor:colluder-A", tool_id="T3",
                          tool_name=TOOL_NAMES["T3"], parameters={"app": "svc-b"},
                          policy_version=POLICY_VERSION, evidence=ev(),
                          approvals=approvals)
    submit_and_score("ARK-496-A005", act, "DENY", "T3")

    # ---- A006: expired delegation reuse ----
    env.registry.reset(); env.policy.reset()
    tok = sign_delegation("actor:orchestrator-01", "actor:executor-01", ["T3"],
                          _ts(-3600), _ts(-1))   # already expired
    act = ag.build_action(actor_id="actor:executor-01", tool_id="T3",
                          tool_name=TOOL_NAMES["T3"], parameters={"app": "svc-c"},
                          policy_version=POLICY_VERSION, evidence=ev(),
                          delegation_token=tok, delegated_by="actor:orchestrator-01")
    submit_and_score("ARK-496-A006", act, "DENY", "T3", need_chain=True)

    # ---- A007: task modified after review (X approved, Y submitted) ----
    env.registry.reset(); env.policy.reset()
    task_x = {"app": "svc-x", "replicas": 1}
    payload_x = dict(task_x); payload_x["tool_id"] = "T3"; payload_x["tool_name"] = TOOL_NAMES["T3"]
    hash_x = sha256_hex(canonical_json(payload_x))
    task_y = {"app": "svc-x", "replicas": 99}     # orchestrator modifies to Y
    act = ag.build_action(actor_id="actor:orchestrator-01", tool_id="T3",
                          tool_name=TOOL_NAMES["T3"], parameters=task_y,
                          policy_version=POLICY_VERSION, evidence=ev(),
                          approved_hash=hash_x)     # authorization was for X
    submit_and_score("ARK-496-A007", act, "DENY", "T3")

    env.registry.reset(); env.policy.reset()
    decision = "EXPERIMENT-PASS" if experiment_pass else "EXPERIMENT-FAIL"
    write_series_summary(env.store, EXPERIMENT_ID, decision, case_ids)
    return {"experiment_id": EXPERIMENT_ID, "decision": decision,
            "case_ids": case_ids, "gate_stop": False}
