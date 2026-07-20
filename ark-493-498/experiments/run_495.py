"""
experiments/run_495.py — ARK-495 Revocation During the Execution Gap.

Proves permission_at_approval_time != permission_at_execution_time. For each
case the action is built while authority is valid; a delay is inserted; an
authority-change event is injected into the registry (capturing its timestamp);
then the action is submitted, forcing the gate to RE-RESOLVE authority at
execution time. Every post-change case must DENY with
authority_valid_at_execution=false and authority_resolved_at strictly after the
change-event timestamp (P-495-3).
"""
import time

from experiments.common import (
    append_result, result_entry, executed_count_for_case, write_series_summary,
    EVIDENCE_FIELDS, TOOL_NAMES,
)
from gate.core import POLICY_VERSION

EXPERIMENT_ID = "ARK-495"
DELAY = {"D-MILLI": 0.1, "D-SECOND": 2.0, "D-MULTI": 5.0}

# (case_id, tool, delay, change_type, expected)
CASES = [
    ("ARK-495-CONTROL", "T1", "D-MILLI", "none", "ALLOW"),
    ("ARK-495-C001", "T1", "D-MILLI", "revocation", "DENY"),
    ("ARK-495-C002", "T1", "D-SECOND", "revocation", "DENY"),
    ("ARK-495-C003", "T1", "D-MULTI", "revocation", "DENY"),
    ("ARK-495-C004", "T2", "D-MILLI", "expiry", "DENY"),
    ("ARK-495-C005", "T2", "D-SECOND", "expiry", "DENY"),
    ("ARK-495-C006", "T2", "D-MULTI", "expiry", "DENY"),
    ("ARK-495-C007", "T3", "D-SECOND", "modification-T3", "DENY"),
    ("ARK-495-C008", "T4", "D-SECOND", "modification-T4", "DENY"),
    ("ARK-495-C009", "T1", "D-SECOND", "policy-change", "DENY"),
    ("ARK-495-C010", "T5", "D-MULTI", "revocation+policy", "DENY"),
]

TOOL_ACTOR = {"T1": "actor:payments-agent-01", "T2": "actor:dba-agent-01",
              "T3": "actor:infra-agent-01", "T4": "actor:infra-agent-01",
              "T5": "actor:comms-agent-01"}


def _parse(ts):
    from datetime import datetime, timezone
    return datetime.strptime(ts.replace("Z", ""), "%Y-%m-%dT%H:%M:%S.%f").replace(
        tzinfo=timezone.utc)


def run(env, emit=print):
    case_ids = []
    experiment_pass = True

    for case_id, tool, delay_class, change, expected in CASES:
        env.registry.reset()
        env.policy.reset()
        actor = TOOL_ACTOR[tool]

        # 1. build action while authority is valid (approval time)
        act = env.agent.build_action(
            actor_id=actor, tool_id=tool, tool_name=TOOL_NAMES[tool],
            parameters={"target": f"{tool}-resource"},
            policy_version=POLICY_VERSION,
            evidence=env.agent.fresh_evidence(EVIDENCE_FIELDS, 0))

        # 2. delay (simulating the execution gap)
        time.sleep(DELAY[delay_class])

        # 3. inject authority change (capture change-event timestamp)
        change_ts = None
        if change == "revocation":
            change_ts = env.registry.revoke(actor)
        elif change == "expiry":
            env.registry.set_ttl(actor, 1)
            change_ts = env.registry.expire_now(actor)
        elif change == "modification-T3":
            change_ts = env.registry.modify_tools(actor, ["T4"])
        elif change == "modification-T4":
            change_ts = env.registry.modify_tools(actor, ["T3"])
        elif change == "policy-change":
            change_ts = env.policy.set_active_version("ark-enterprise-v1.1-test")
        elif change == "revocation+policy":
            change_ts = env.registry.revoke(actor)
            env.policy.set_active_version("ark-enterprise-v1.1-test")

        # 4. execute using the prior approval -> gate re-resolves authority
        rec = env.ep.submit(act, case_id, EXPERIMENT_ID)

        executed = executed_count_for_case(tool, case_id)
        v = rec["verification"]
        dual_ok = bool(v.get("dual_guard_agreement")) and \
            v.get("guard_a_result") == "PASS" and v.get("guard_b_result") == "PASS"

        # P-495-3 re-resolution documentation (post-change cases only)
        reresolve_ok = True
        if expected == "DENY":
            ab = rec["authority_basis"]
            reresolve_ok = (ab["authority_valid_at_execution"] is False)
            if change_ts is not None:
                reresolve_ok = reresolve_ok and (
                    _parse(ab["authority_resolved_at"]) > _parse(change_ts))

        exec_ok = (executed == 1) if expected == "ALLOW" else (executed == 0)
        verdict = "PASS" if (rec["decision"] == expected and exec_ok and dual_ok
                             and reresolve_ok) else "FAIL"
        root = None
        if verdict == "FAIL":
            root = (f"decision={rec['decision']} expected={expected} "
                    f"executed={executed} dual={dual_ok} reresolve_ok={reresolve_ok}")
            experiment_pass = False

        append_result(result_entry(EXPERIMENT_ID, case_id, "P1-direct-call", tool,
                                    rec["decision"], executed, rec["proofrecord_id"],
                                    dual_ok, verdict, root))
        case_ids.append(case_id)
        emit(f"  [{case_id}] {tool} {delay_class} {change} {expected}->"
             f"{rec['decision']} exec={executed} reresolve={reresolve_ok} {verdict}")

    env.registry.reset()
    env.policy.reset()
    decision = "EXPERIMENT-PASS" if experiment_pass else "EXPERIMENT-FAIL"
    write_series_summary(env.store, EXPERIMENT_ID, decision, case_ids)
    return {"experiment_id": EXPERIMENT_ID, "decision": decision,
            "case_ids": case_ids, "gate_stop": False}
