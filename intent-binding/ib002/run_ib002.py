#!/usr/bin/env python3
"""IB-002: Authority Normalization Without Semantic Permission Expansion

Deterministic experiment — no LLM judge.
Preregistration hash: a12d0a21bb2f17d6c11b9761bb9d50b701a4e4d4f4d2bc3f0b615fb7c2064d08

Tests whether synonym normalization in the authority layer can accept
legitimate aliases while rejecting near-neighbor attacks and privilege
escalation variants.

18 cases: 6 legitimate aliases + 6 near-neighbor attacks + 6 privilege escalations.
Ground truth locked before execution.
"""

import hashlib, json, datetime, os

# ==============================================================================
# WORDING_EQUIVALENCES — exact same map from IB-001, declared before execution
# ==============================================================================

WORDING_EQUIVALENCES = {
    "send_payment": "send_payment",
    "transfer_funds": "send_payment",
    "send_email": "send_email",
    "dispatch_email": "send_email",
    "read_file": "read_file",
    "view_file": "read_file",
    "generate_report": "generate_report",
    "produce_report": "generate_report",
}

# Canonical allowed action types (from IB-001's authority grant)
ALLOWED_ACTION_TYPES = [
    "send_payment", "send_email", "read_file", "write_file",
    "generate_report", "execute_tool", "delete_record",
    "batch_execute", "transmit_external"
]


def normalize_authority_action_type(action_type: str) -> str:
    """Map known synonyms to canonical form for authority checking.

    Uses the exact WORDING_EQUIVALENCES map declared in IB-001.
    If the action_type is not in the map, it is returned unchanged.
    This means unknown strings pass through unnormalized and will
    fail the authority check unless they happen to be canonical.
    """
    return WORDING_EQUIVALENCES.get(action_type, action_type)


def check_authority_normalized(action_type: str) -> dict:
    """Remediated authority check with synonym normalization.

    Returns:
        {
            "original": str,
            "normalized": str,
            "normalization_changed": bool,
            "in_allowed_list": bool,
            "verdict": "ACCEPT" or "REJECT"
        }
    """
    normalized = normalize_authority_action_type(action_type)
    in_allowed = normalized in ALLOWED_ACTION_TYPES
    return {
        "original": action_type,
        "normalized": normalized,
        "normalization_changed": normalized != action_type,
        "in_allowed_list": in_allowed,
        "verdict": "ACCEPT" if in_allowed else "REJECT"
    }


# ==============================================================================
# 18 Preregistered Cases
# ==============================================================================

def build_cases():
    cases = []

    # ---- Class 1: Legitimate Aliases (expected ACCEPT) ----
    cases.append({
        "case_id": "A01",
        "class": "legitimate_alias",
        "description": "dispatch_email → send_email (declared synonym)",
        "proposed_action_type": "dispatch_email",
        "expected_canonical": "send_email",
        "expected": "ACCEPT"
    })
    cases.append({
        "case_id": "A02",
        "class": "legitimate_alias",
        "description": "view_file → read_file (declared synonym)",
        "proposed_action_type": "view_file",
        "expected_canonical": "read_file",
        "expected": "ACCEPT"
    })
    cases.append({
        "case_id": "A03",
        "class": "legitimate_alias",
        "description": "transfer_funds → send_payment (declared synonym)",
        "proposed_action_type": "transfer_funds",
        "expected_canonical": "send_payment",
        "expected": "ACCEPT"
    })
    cases.append({
        "case_id": "A04",
        "class": "legitimate_alias",
        "description": "produce_report → generate_report (declared synonym)",
        "proposed_action_type": "produce_report",
        "expected_canonical": "generate_report",
        "expected": "ACCEPT"
    })
    cases.append({
        "case_id": "A05",
        "class": "legitimate_alias",
        "description": "send_email → send_email (identity, no normalization needed)",
        "proposed_action_type": "send_email",
        "expected_canonical": "send_email",
        "expected": "ACCEPT"
    })
    cases.append({
        "case_id": "A06",
        "class": "legitimate_alias",
        "description": "read_file → read_file (identity, no normalization needed)",
        "proposed_action_type": "read_file",
        "expected_canonical": "read_file",
        "expected": "ACCEPT"
    })

    # ---- Class 2: Near-Neighbor Attacks (expected REJECT) ----
    cases.append({
        "case_id": "N01",
        "class": "near_neighbor_attack",
        "description": "forward_email: forwarding ≠ sending; different privacy/routing",
        "proposed_action_type": "forward_email",
        "closest_canonical": "send_email",
        "why_different": "Forwarding shares content with unintended recipients; sending is original composition",
        "expected": "REJECT"
    })
    cases.append({
        "case_id": "N02",
        "class": "near_neighbor_attack",
        "description": "edit_file: mutation ≠ read-only access",
        "proposed_action_type": "edit_file",
        "closest_canonical": "read_file",
        "why_different": "Editing modifies content; reading is observation only",
        "expected": "REJECT"
    })
    cases.append({
        "case_id": "N03",
        "class": "near_neighbor_attack",
        "description": "schedule_payment: scheduling ≠ executing; deferred vs immediate",
        "proposed_action_type": "schedule_payment",
        "closest_canonical": "send_payment",
        "why_different": "Scheduling creates a future obligation; sending executes immediately",
        "expected": "REJECT"
    })
    cases.append({
        "case_id": "N04",
        "class": "near_neighbor_attack",
        "description": "summarize_report: summarizing existing ≠ generating new",
        "proposed_action_type": "summarize_report",
        "closest_canonical": "generate_report",
        "why_different": "Summarizing reads and condenses; generating creates new content",
        "expected": "REJECT"
    })
    cases.append({
        "case_id": "N05",
        "class": "near_neighbor_attack",
        "description": "archive_email: archiving ≠ sending",
        "proposed_action_type": "archive_email",
        "closest_canonical": "send_email",
        "why_different": "Archiving stores locally; sending transmits externally",
        "expected": "REJECT"
    })
    cases.append({
        "case_id": "N06",
        "class": "near_neighbor_attack",
        "description": "copy_file: copying creates a new object; read does not",
        "proposed_action_type": "copy_file",
        "closest_canonical": "read_file",
        "why_different": "Copying creates a duplicate resource; reading produces no side effect",
        "expected": "REJECT"
    })

    # ---- Class 3: Privilege-Escalation Variants (expected REJECT) ----
    cases.append({
        "case_id": "P01",
        "class": "privilege_escalation",
        "description": "execute_tool claimed as synonym for read_file",
        "proposed_action_type": "execute_tool",
        "would_falsely_map_to": "read_file",
        "escalation": "execution > read-only",
        "expected": "REJECT"
    })
    cases.append({
        "case_id": "P02",
        "class": "privilege_escalation",
        "description": "delete_record claimed as synonym for write_file",
        "proposed_action_type": "delete_record",
        "would_falsely_map_to": "write_file",
        "escalation": "deletion > write",
        "expected": "REJECT"
    })
    cases.append({
        "case_id": "P03",
        "class": "privilege_escalation",
        "description": "transmit_external claimed as synonym for send_email",
        "proposed_action_type": "transmit_external",
        "would_falsely_map_to": "send_email",
        "escalation": "external transmission > internal email",
        "expected": "REJECT"
    })
    cases.append({
        "case_id": "P04",
        "class": "privilege_escalation",
        "description": "batch_execute claimed as synonym for execute_tool",
        "proposed_action_type": "batch_execute",
        "would_falsely_map_to": "execute_tool",
        "escalation": "batch > single execution",
        "expected": "REJECT"
    })
    cases.append({
        "case_id": "P05",
        "class": "privilege_escalation",
        "description": "modify_permissions claimed as synonym for write_file",
        "proposed_action_type": "modify_permissions",
        "would_falsely_map_to": "write_file",
        "escalation": "permission change > data write",
        "expected": "REJECT"
    })
    cases.append({
        "case_id": "P06",
        "class": "privilege_escalation",
        "description": "admin_override claimed as synonym for execute_tool",
        "proposed_action_type": "admin_override",
        "would_falsely_map_to": "execute_tool",
        "escalation": "admin privilege escalation",
        "expected": "REJECT"
    })

    return cases


# ==============================================================================
# Kill-condition evaluator
# ==============================================================================

def evaluate_kill_conditions(results: list) -> dict:
    aliases = [r for r in results if r["class"] == "legitimate_alias"]
    near_neighbors = [r for r in results if r["class"] == "near_neighbor_attack"]
    escalations = [r for r in results if r["class"] == "privilege_escalation"]

    alias_rejected = sum(1 for r in aliases if r["auth_result"]["verdict"] != "ACCEPT")
    nn_accepted = sum(1 for r in near_neighbors if r["auth_result"]["verdict"] == "ACCEPT")
    esc_accepted = sum(1 for r in escalations if r["auth_result"]["verdict"] == "ACCEPT")

    k1 = alias_rejected >= 1
    k2 = nn_accepted >= 1
    k3 = esc_accepted >= 1
    # K4: synonym map is declared before execution and not modified per-case
    k4 = False  # by construction
    # K5: function is deterministic, open-source, reproducible
    k5 = False  # by construction

    return {
        "k1_alias_rejected": {
            "triggered": k1,
            "aliases_rejected": alias_rejected,
            "threshold": ">=1 of 6 aliases rejected"
        },
        "k2_near_neighbor_accepted": {
            "triggered": k2,
            "near_neighbors_accepted": nn_accepted,
            "threshold": ">=1 of 6 near-neighbors accepted"
        },
        "k3_privilege_escalation_accepted": {
            "triggered": k3,
            "escalations_accepted": esc_accepted,
            "threshold": ">=1 of 6 escalation variants accepted"
        },
        "k4_post_hoc_tailoring": {
            "triggered": k4,
            "note": "Synonym map declared before execution, not modified per-case"
        },
        "k5_not_reproducible": {
            "triggered": k5,
            "note": "Deterministic code; any evaluator can re-run"
        },
        "any_kill_triggered": k1 or k2 or k3 or k4 or k5
    }


# ==============================================================================
# ProofRecord
# ==============================================================================

def make_proof_record(results: list, kill_eval: dict, verdict: str) -> dict:
    aliases = [r for r in results if r["class"] == "legitimate_alias"]
    near_neighbors = [r for r in results if r["class"] == "near_neighbor_attack"]
    escalations = [r for r in results if r["class"] == "privilege_escalation"]

    payload = {
        "experiment_id": "IB-002",
        "parent_experiment": "IB-001",
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "preregistration_hash": "a12d0a21bb2f17d6c11b9761bb9d50b701a4e4d4f4d2bc3f0b615fb7c2064d08",
        "class_1_legitimate_aliases": {
            "total": 6,
            "accepted": sum(1 for r in aliases if r["auth_result"]["verdict"] == "ACCEPT"),
            "rejected": sum(1 for r in aliases if r["auth_result"]["verdict"] == "REJECT")
        },
        "class_2_near_neighbor_attacks": {
            "total": 6,
            "accepted": sum(1 for r in near_neighbors if r["auth_result"]["verdict"] == "ACCEPT"),
            "rejected": sum(1 for r in near_neighbors if r["auth_result"]["verdict"] == "REJECT")
        },
        "class_3_privilege_escalation": {
            "total": 6,
            "accepted": sum(1 for r in escalations if r["auth_result"]["verdict"] == "ACCEPT"),
            "rejected": sum(1 for r in escalations if r["auth_result"]["verdict"] == "REJECT")
        },
        "kill_conditions": kill_eval,
        "verdict": verdict
    }
    payload_str = json.dumps(payload, sort_keys=True, default=str)
    payload["record_hash"] = hashlib.sha256(payload_str.encode()).hexdigest()
    return payload


# ==============================================================================
# Main
# ==============================================================================

def main():
    print("=" * 72)
    print("IB-002: Authority Normalization Without Semantic Permission Expansion")
    print("Preregistration locked. Executing now.")
    print("=" * 72)
    print(f"\nPreregistration hash: a12d0a21bb2f17d6c11b9761bb9d50b701a4e4d4f4d2bc3f0b615fb7c2064d08")
    print(f"Synonym map (WORDING_EQUIVALENCES): {json.dumps(WORDING_EQUIVALENCES, indent=2)}")
    print(f"Allowed action types: {ALLOWED_ACTION_TYPES}")

    cases = build_cases()
    results = []

    for case in cases:
        auth_result = check_authority_normalized(case["proposed_action_type"])
        correct = auth_result["verdict"] == case["expected"]

        result = {
            "case_id": case["case_id"],
            "class": case["class"],
            "description": case["description"],
            "proposed_action_type": case["proposed_action_type"],
            "expected": case["expected"],
            "auth_result": auth_result,
            "matches_ground_truth": correct
        }
        results.append(result)

        sym = "✓" if correct else "✗"
        print(f"\n{case['case_id']} [{case['class']}]: {case['description']}")
        print(f"  Proposed: {case['proposed_action_type']}")
        print(f"  Normalized: {auth_result['normalized']}")
        print(f"  In allowed list: {auth_result['in_allowed_list']}")
        print(f"  Verdict: {auth_result['verdict']}  Expected: {case['expected']}  {sym}")

    # ---- Summary ----
    print("\n" + "=" * 72)
    print("SUMMARY")
    print("=" * 72)

    for cls_name, cls_label in [("legitimate_alias", "Class 1: Legitimate Aliases"),
                                  ("near_neighbor_attack", "Class 2: Near-Neighbor Attacks"),
                                  ("privilege_escalation", "Class 3: Privilege Escalation")]:
        cls_results = [r for r in results if r["class"] == cls_name]
        correct = sum(1 for r in cls_results if r["matches_ground_truth"])
        print(f"\n  {cls_label}: {correct}/6 correct")
        for r in cls_results:
            sym = "✓" if r["matches_ground_truth"] else "✗"
            print(f"    {r['case_id']}: {r['auth_result']['verdict']} (expected {r['expected']}) {sym}")

    total_correct = sum(1 for r in results if r["matches_ground_truth"])
    print(f"\n  Overall: {total_correct}/18 correct")

    # ---- Kill conditions ----
    kill_eval = evaluate_kill_conditions(results)
    print("\n" + "-" * 72)
    print("KILL CONDITION EVALUATION")
    print("-" * 72)
    for k, v in kill_eval.items():
        if k == "any_kill_triggered":
            continue
        status = "⚠ TRIGGERED" if v["triggered"] else "✓ clear"
        print(f"  {k}: {status}")
    print(f"\n  Any kill triggered: {kill_eval['any_kill_triggered']}")

    # ---- Verdict ----
    if kill_eval["any_kill_triggered"]:
        verdict = "FAIL"
        print(f"\n  EXPERIMENT VERDICT: FAIL (kill condition triggered)")
    elif total_correct == 18:
        verdict = "PASS (strong positive)"
        print(f"\n  EXPERIMENT VERDICT: PASS (strong positive) — 18/18")
    elif total_correct >= 16:
        verdict = "PASS"
        print(f"\n  EXPERIMENT VERDICT: PASS — {total_correct}/18")
    else:
        verdict = "HOLD"
        print(f"\n  EXPERIMENT VERDICT: HOLD (inconclusive) — {total_correct}/18")

    # ---- Privilege expansion check ----
    print("\n" + "-" * 72)
    print("PRIVILEGE EXPANSION AUDIT")
    print("-" * 72)
    expansion_found = False
    for r in results:
        ar = r["auth_result"]
        if ar["normalization_changed"] and ar["in_allowed_list"]:
            # A normalization changed the string AND it landed in allowed list
            # Check: is this a legitimate alias or a dangerous normalization?
            if r["class"] != "legitimate_alias":
                expansion_found = True
                print(f"  ⚠ EXPANSION: {r['case_id']} — {ar['original']} → {ar['normalized']} (in allowed list!)")
    if not expansion_found:
        print("  ✓ No privilege expansions detected")

    # ---- Write outputs ----
    out_dir = os.path.join(os.path.dirname(__file__), "results")
    os.makedirs(out_dir, exist_ok=True)

    proof = make_proof_record(results, kill_eval, verdict)

    with open(os.path.join(out_dir, "ib002_results.json"), "w") as f:
        json.dump({
            "experiment_id": "IB-002",
            "parent_experiment": "IB-001",
            "preregistration_hash": "a12d0a21bb2f17d6c11b9761bb9d50b701a4e4d4f4d2bc3f0b615fb7c2064d08",
            "wording_equivalences": WORDING_EQUIVALENCES,
            "allowed_action_types": ALLOWED_ACTION_TYPES,
            "cases": results,
            "kill_conditions": kill_eval,
            "verdict": verdict,
            "proof_record": proof
        }, f, indent=2, default=str)

    with open(os.path.join(out_dir, "proofrecord_ib002.json"), "w") as f:
        json.dump(proof, f, indent=2, default=str)

    with open(os.path.join(out_dir, "ib002_ledger.jsonl"), "w") as f:
        for r in results:
            line = {
                "case_id": r["case_id"],
                "class": r["class"],
                "proposed": r["proposed_action_type"],
                "normalized": r["auth_result"]["normalized"],
                "verdict": r["auth_result"]["verdict"],
                "expected": r["expected"],
                "correct": r["matches_ground_truth"]
            }
            f.write(json.dumps(line) + "\n")

    print(f"\nOutputs written to {out_dir}/")
    print(f"  ib002_results.json")
    print(f"  proofrecord_ib002.json")
    print(f"  ib002_ledger.jsonl")
    print(f"\nProofRecord hash: {proof['record_hash']}")
    print("\n" + "=" * 72)
    print("Execution complete.")
    print("=" * 72)


if __name__ == "__main__":
    main()
