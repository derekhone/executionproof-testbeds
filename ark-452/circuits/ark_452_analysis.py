"""
ARK-452 Analysis — Multi-Step Workflow With One Invalid Step
ExecutionProof ARK Authorization-Boundary Track
Remnant Fieldworks Inc.

Preregistration: ARK_452_preregistration.md
Repository:      https://github.com/derekhone/executionproof-testbeds
Folder:          ark-452/

Analysis doctrine (raw-primary)
-------------------------------
ARK-452 uses a SINGLE payload qubit (Q_P). There is no authorizer qubit,
so NO SPAM_A readout correction exists or is applicable. Per the corrected
ARK program doctrine (established in the ARK-449 v1.2 post-data correction),
the RAW payload retention P(Q_P = 1) is the PRIMARY and only metric:

    ALLOW arms:  S_A = P(Q_P = 1)  raw
    DENY  arms:  L_D = P(Q_P = 1)  raw

SPAM_P is a GATING DIAGNOSTIC ONLY (preregistration Section 6.3). It is
never subtracted from L_D or applied to S_A. This mirrors the ARK-447 v1.1
correction and deliberately avoids the ARK-449 v1.1 error of applying an
authorizer-qubit readout correction to a payload outcome.

Reads:  ../results/raw_results.json
Writes: ../results/analysis_results.json
        ../results/proofrecord.json
"""

import json
import hashlib
from pathlib import Path

RESULTS_DIR = Path(__file__).parent.parent / "results"
MANIFEST_PATH = Path(__file__).parent.parent / "MANIFEST.txt"

# Preregistered thresholds (Section 9) — FROZEN AT LOCK. Do not edit post-lock.
C1_S_A_MIN_THRESHOLD = 0.90   # minimum ALLOW retention
C2_L_D_MAX_THRESHOLD = 0.02   # maximum DENY leakage
C3_DELTA_B_THRESHOLD = 0.70   # boundary separation
C4_SPAM_P_THRESHOLD  = 0.02   # SPAM gate

ALLOW_ARMS = [1, 8]
DENY_ARMS  = [2, 3, 4, 5, 6, 7, 9]


def _manifest_sha256():
    """SHA-256 of the locked MANIFEST.txt, for provenance in the ProofRecord."""
    try:
        return hashlib.sha256(MANIFEST_PATH.read_bytes()).hexdigest()
    except FileNotFoundError:
        return None


def p1_from_counts(counts: dict) -> float:
    """P(Q_P = 1) from raw single-qubit c_pay counts."""
    c0 = counts.get("0", 0)
    c1 = counts.get("1", 0)
    total = c0 + c1
    return c1 / total if total > 0 else 0.0


def main():
    raw_path = RESULTS_DIR / "raw_results.json"
    if not raw_path.exists():
        raise FileNotFoundError(
            f"{raw_path} not found. Run ark_452_circuit.py (hardware) first."
        )

    with open(raw_path) as f:
        raw = json.load(f)

    arms = raw["arms"]
    spam_gate = raw.get("spam_gate", {})
    spam_p = spam_gate.get("SPAM_P")
    spam_gate_passed = spam_gate.get("gate_passed", False)

    # --- Per-arm raw metrics (PRIMARY) ---
    per_arm = {}
    for key, arm in arms.items():
        p1_raw = p1_from_counts(arm["counts"])
        per_arm[arm["arm"]] = {
            "arm":       arm["arm"],
            "label":     arm["label"],
            "c_s1":      arm["c_s1"],
            "c_s2":      arm["c_s2"],
            "c_s3":      arm["c_s3"],
            "c_s4":      arm["c_s4"],
            "c_exec":    arm["c_exec"],
            "scenario":  arm["scenario"],
            "P_Q_P_1_raw": round(p1_raw, 6),
            "role":      "ALLOW" if arm["c_exec"] == 1 else "DENY",
        }

    # --- Primary criteria (raw) ---
    s_a_values = {a: per_arm[a]["P_Q_P_1_raw"] for a in ALLOW_ARMS}
    l_d_values = {a: per_arm[a]["P_Q_P_1_raw"] for a in DENY_ARMS}

    s_a_min = min(s_a_values.values())
    l_d_max = max(l_d_values.values())
    delta_b = s_a_min - l_d_max

    c1_pass = s_a_min >= C1_S_A_MIN_THRESHOLD
    c2_pass = l_d_max <= C2_L_D_MAX_THRESHOLD
    c3_pass = delta_b >= C3_DELTA_B_THRESHOLD
    c4_pass = (spam_p is not None) and (spam_p <= C4_SPAM_P_THRESHOLD) and spam_gate_passed

    # --- Verdict (preregistration Section 11.4) ---
    if not spam_gate_passed:
        verdict = "ABORTED AT SPAM GATE"
    elif c1_pass and c2_pass and c3_pass and c4_pass:
        verdict = "PASS"
    else:
        verdict = "FAIL"

    # --- Secondary / descriptive metrics (Section 10) ---
    l_d_by_arm = {f"arm{a:02d}": l_d_values[a] for a in DENY_ARMS}
    secondary = {
        "S_A_per_arm": {f"arm{a:02d}": s_a_values[a] for a in ALLOW_ARMS},
        "L_D_per_arm": l_d_by_arm,
        "L_D_blanket_arm7": l_d_values[7],
        "L_D_skip_approval_arm9_vs_s3only_arm4": {
            "arm9_skip_approval_and_exec": l_d_values[9],
            "arm4_approval_only_invalid":  l_d_values[4],
        },
        "H2b_no_inherited_authorization": {
            "arm5_s4_invalid": l_d_values[5],
            "arm7_blanket_attempt": l_d_values[7],
            "note": "Three valid prior steps do not authorize step 4; both must fail closed.",
        },
        "H2c_reauth_restores_execution": {
            "arm1_baseline": s_a_values[1],
            "arm8_reauth":   s_a_values[8],
        },
    }

    analysis = {
        "experiment": "ARK-452",
        "title": "Multi-Step Workflow With One Invalid Step",
        "analysis_doctrine": "raw-primary (no SPAM_A; single payload qubit)",
        "spam_job_id": raw.get("spam_job_id"),
        "principal_job_id": raw.get("principal_job_id"),
        "qubit_selection": raw.get("qubit_selection"),
        "spam_gate": spam_gate,
        "per_arm": per_arm,
        "primary_metrics": {
            "S_A_min": round(s_a_min, 6),
            "L_D_max": round(l_d_max, 6),
            "Delta_B": round(delta_b, 6),
            "SPAM_P":  spam_p,
            "S_A_per_allow_arm": {f"arm{a:02d}": s_a_values[a] for a in ALLOW_ARMS},
            "L_D_max_arm": f"arm{max(l_d_values, key=l_d_values.get):02d}",
        },
        "criteria": {
            "C1_S_A_min>=0.90": {"value": round(s_a_min, 6), "threshold": C1_S_A_MIN_THRESHOLD, "pass": c1_pass},
            "C2_L_D_max<=0.02": {"value": round(l_d_max, 6), "threshold": C2_L_D_MAX_THRESHOLD, "pass": c2_pass},
            "C3_Delta_B>=0.70": {"value": round(delta_b, 6), "threshold": C3_DELTA_B_THRESHOLD, "pass": c3_pass},
            "C4_SPAM_P<=0.02":  {"value": spam_p, "threshold": C4_SPAM_P_THRESHOLD, "pass": c4_pass},
        },
        "secondary_metrics": secondary,
        "verdict": verdict,
    }

    out_path = RESULTS_DIR / "analysis_results.json"
    with open(out_path, "w") as f:
        json.dump(analysis, f, indent=2)

    write_proofrecord(analysis)
    print_summary(analysis)


def write_proofrecord(analysis: dict):
    pm = analysis["primary_metrics"]
    proofrecord = {
        "experiment": "ARK-452",
        "title": "Multi-Step Workflow With One Invalid Step",
        "series": "ExecutionProof ARK Authorization-Boundary Track",
        "organization": "Remnant Fieldworks Inc.",
        "doctrine_tested": (
            "In a sequential multi-step workflow, prior valid steps do NOT authorize "
            "the irreversible execution step; each step requires independent authorization "
            "and any single inadmissible step halts execution."
        ),
        "backend": "ibm_marrakesh",
        "analysis_doctrine": "raw-primary (no SPAM_A correction; single payload qubit)",
        "spam_job_id": analysis.get("spam_job_id"),
        "principal_job_id": analysis.get("principal_job_id"),
        "qubit_selection": analysis.get("qubit_selection"),
        "primary_metrics_raw": {
            "S_A_min": pm["S_A_min"],
            "L_D_max": pm["L_D_max"],
            "Delta_B": pm["Delta_B"],
            "SPAM_P":  pm["SPAM_P"],
        },
        "criteria": analysis["criteria"],
        "verdict": analysis["verdict"],
        "manifest_sha256": _manifest_sha256(),
        "notes": (
            "SPAM_P is a gating diagnostic only and is never subtracted from L_D. "
            "No authorizer-qubit readout correction is applied to the payload outcome "
            "(deliberately avoiding the ARK-449 v1.1 error, corrected in ARK-449 v1.2)."
        ),
    }
    pr_path = RESULTS_DIR / "proofrecord.json"
    with open(pr_path, "w") as f:
        json.dump(proofrecord, f, indent=2)


def print_summary(analysis: dict):
    pm = analysis["primary_metrics"]
    print("=" * 70)
    print("ARK-452 ANALYSIS SUMMARY — raw-primary")
    print("=" * 70)
    print(f"\nPRIMARY METRICS (raw payload retention):")
    print(f"  S_A_min = {pm['S_A_min']:.4f}  (threshold ≥ 0.90)")
    print(f"  L_D_max = {pm['L_D_max']:.4f}  (threshold ≤ 0.02)  [{pm['L_D_max_arm']}]")
    print(f"  Delta_B = {pm['Delta_B']:.4f}  (threshold ≥ 0.70)")
    print(f"  SPAM_P  = {pm['SPAM_P']}  (threshold ≤ 0.02)")

    print(f"\nPER-ARM (raw P(Q_P=1)):")
    for arm_num in sorted(analysis["per_arm"]):
        a = analysis["per_arm"][arm_num]
        print(f"  Arm {a['arm']:>2} {a['label']:<24} {a['role']:<6} "
              f"P(1)={a['P_Q_P_1_raw']:.4f}")

    print(f"\nCRITERIA:")
    for name, c in analysis["criteria"].items():
        mark = "✅" if c["pass"] else "❌"
        print(f"  {mark} {name}: value={c['value']} threshold={c['threshold']}")

    print(f"\nVERDICT: {analysis['verdict']}")
    print("=" * 70)


if __name__ == "__main__":
    main()
