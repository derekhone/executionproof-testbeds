"""
ARK-449 Analysis Script — State Changes After Verification
ExecutionProof ARK Series — Remnant Fieldworks Inc.

Preregistration: ARK_449_preregistration.md (Section 11)
Repository:      https://github.com/derekhone/executionproof-testbeds
Folder:          ark-449/

Usage
-----
    python ark_449_analysis.py

Reads raw_results.json from ../results/ and produces:
    ../results/analysis_results.json   — full metric table + verdict
    ../results/proofrecord.json        — machine-readable ProofRecord artifact
    stdout                             — human-readable summary

LOCK RULE
---------
This script must be committed at lock time (included in MANIFEST SHA-256).
No changes to metric definitions, thresholds, verdict logic, or SPAM
correction rules are permitted after the MANIFEST is committed.

Analysis Rules (preregistration Section 11)
--------------------------------------------
1. S_A computed on ALLOW arms (Arms 1 and 8): P(Q_P=1), SPAM_A-corrected.
2. L_D computed on DENY arms (Arms 2–7 and 9): P(Q_P=1), RAW — NOT corrected
   by SPAM_P. SPAM_P is a gating diagnostic only. (ARK-447 v1.1 correction,
   fixed in preregistration.)
3. S_A_min = min(S_A_arm1, S_A_arm8)
4. L_D_max = max(L_D for all DENY arms)
5. Delta_B  = S_A_min − L_D_max
6. Verdict:
       PASS  → S_A_min ≥ 0.90  AND  L_D_max ≤ 0.02  AND  Delta_B ≥ 0.70
       FAIL  → any criterion not met
       ABORTED AT SPAM GATE → read from raw_results.json (gate-stop case)

Pass Criteria (preregistration Section 9)
------------------------------------------
C1: S_A_min ≥ 0.90
C2: L_D_max ≤ 0.02
C3: Delta_B  ≥ 0.70
C4: SPAM gate passed (evaluated before this script runs; encoded in raw_results.json)
"""

import json
import sys
import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# 0. Configuration — all thresholds fixed at preregistration lock
# ---------------------------------------------------------------------------

RESULTS_DIR = Path(__file__).parent.parent / "results"
RAW_RESULTS_FILE   = RESULTS_DIR / "raw_results.json"
ANALYSIS_OUT_FILE  = RESULTS_DIR / "analysis_results.json"
PROOFRECORD_FILE   = RESULTS_DIR / "proofrecord.json"

# Shot counts — must match ark_449_circuit.py; used only as fallbacks if a
# raw_results.json omits them (hardware runs always record the real values).
SHOTS_SPAM       = 2048
SHOTS_PRINCIPAL  = 8192

# Pass/fail thresholds — preregistered, immutable after MANIFEST commit
C1_THRESHOLD_S_A_MIN  = 0.90   # minimum ALLOW retention
C2_THRESHOLD_L_D_MAX  = 0.02   # maximum DENY leakage
C3_THRESHOLD_DELTA_B  = 0.70   # boundary separation

# Arm classification (preregistration Section 5)
ALLOW_ARMS = {1, 8}
DENY_ARMS  = {2, 3, 4, 5, 6, 7, 9}
REPLAY_ARM = 9    # H2c — old ProofRecord replay with changed state

# ---------------------------------------------------------------------------
# 1. Helpers
# ---------------------------------------------------------------------------

def load_raw(path: Path) -> dict:
    if not path.exists():
        print(f"[ERROR] Raw results file not found: {path}")
        print("Run ark_449_circuit.py first to execute the hardware job.")
        sys.exit(1)
    with open(path) as f:
        return json.load(f)


def p1_from_counts(counts: dict) -> float:
    """
    Compute P(Q_P = 1) from a counts dict.

    Counts keys may be:
        "0" / "1"                  — single-qubit result
        "0 0" / "0 1" / etc.       — multi-register result (space-separated)

    In multi-register results the registers are declared in the order
    (c_auth, c_state, c_pay). Qiskit prints classical registers in
    reverse declaration order, space-separated, so the key string is
    "<c_pay> <c_state> <c_auth>" and the payload bit (c_pay) is the
    LEFTMOST field. (v1.1 pre-data correction: v1.0 read the rightmost
    field, which is c_auth — always 1 — not the payload.)
    """
    count_0 = 0
    count_1 = 0
    for key, val in counts.items():
        # Take the leftmost space-separated field as the payload (c_pay) outcome
        payload_bit = key.strip().split()[0] if " " in key else key.strip()
        if payload_bit == "1":
            count_1 += val
        else:
            count_0 += val
    total = count_0 + count_1
    if total == 0:
        return 0.0
    return count_1 / total


def apply_spam_correction(p1_raw: float, spam_a: float) -> float:
    """
    Apply single-qubit readout correction to ALLOW arm retention.

    Correction (standard linear inversion):
        S_A_corrected = (P(Q_P=1) - SPAM_A) / (1 - 2 * SPAM_A)

    Applied ONLY to ALLOW arms.
    DENY arms are reported RAW — SPAM_P is NOT subtracted.
    (Preregistration Section 11.2; ARK-447 v1.1 correction.)

    If SPAM_A is negligible (≤ 0.01), correction is not applied and
    the raw value is returned with a note.
    """
    if spam_a <= 0.01:
        return p1_raw   # negligible; no correction needed
    denominator = 1.0 - 2.0 * spam_a
    if denominator <= 0:
        # Degenerate SPAM — would invert the sign; return raw and flag
        return p1_raw
    corrected = (p1_raw - spam_a) / denominator
    # Clamp to [0, 1] — physical constraint
    return max(0.0, min(1.0, corrected))


def fmt_criterion(value: float, threshold: float, direction: str) -> str:
    """direction: 'ge' for ≥, 'le' for ≤"""
    if direction == "ge":
        passed = value >= threshold
        sym = f"≥ {threshold}"
    else:
        passed = value <= threshold
        sym = f"≤ {threshold}"
    icon = "✅ PASS" if passed else "❌ FAIL"
    return f"{value:.4f}  ({sym})  {icon}"


# ---------------------------------------------------------------------------
# 2. Main Analysis
# ---------------------------------------------------------------------------

def analyse(raw: dict) -> dict:
    """
    Run the full preregistered analysis.

    Returns a structured dict ready for JSON serialisation and verdict output.
    """

    # ------------------------------------------------------------------
    # 2.1 Gate-stop case — no principal data to analyse
    # ------------------------------------------------------------------
    if raw.get("verdict") == "ABORTED AT SPAM GATE":
        return {
            "experiment":    "ARK-449",
            "verdict":       "ABORTED AT SPAM GATE",
            "criteria":      {},
            "primary_metrics": {},
            "secondary_metrics": {},
            "spam_gate":     raw.get("spam_gate", {}),
        }

    spam_gate = raw["spam_gate"]

    if not spam_gate.get("gate_passed", False):
        # SPAM gate failed — should have been caught by circuit script,
        # but guard here too.
        return {
            "experiment":    "ARK-449",
            "verdict":       "ABORTED AT SPAM GATE",
            "abort_reason":  "SPAM gate not passed per raw_results.json",
            "criteria":      {},
            "primary_metrics": {},
            "secondary_metrics": {},
            "spam_gate":     spam_gate,
        }

    spam_a_val = spam_gate["SPAM_A"]

    arms_raw = raw["arms"]

    # ------------------------------------------------------------------
    # 2.2 Compute P(Q_P=1) and corrections per arm
    # ------------------------------------------------------------------
    arm_metrics = {}
    for arm_key, arm_data in arms_raw.items():
        arm_num  = arm_data["arm"]
        counts   = arm_data["counts"]
        p1_raw   = p1_from_counts(counts)

        if arm_num in ALLOW_ARMS:
            p1_final = apply_spam_correction(p1_raw, spam_a_val)
            correction_applied = spam_a_val > 0.01
        else:
            p1_final = p1_raw          # DENY arms: RAW, no correction
            correction_applied = False

        arm_metrics[arm_num] = {
            "arm":                arm_num,
            "label":              arm_data["label"],
            "c_state":            arm_data["c_state"],
            "scenario":           arm_data["scenario"],
            "p1_raw":             round(p1_raw,   6),
            "p1_final":           round(p1_final, 6),
            "spam_correction":    correction_applied,
        }

    # ------------------------------------------------------------------
    # 2.3 Primary metrics
    # ------------------------------------------------------------------
    s_a_per_arm = {
        n: arm_metrics[n]["p1_final"]
        for n in ALLOW_ARMS
        if n in arm_metrics
    }
    l_d_per_arm = {
        n: arm_metrics[n]["p1_final"]
        for n in DENY_ARMS
        if n in arm_metrics
    }

    s_a_min = min(s_a_per_arm.values()) if s_a_per_arm else 0.0
    l_d_max = max(l_d_per_arm.values()) if l_d_per_arm else 1.0
    delta_b  = s_a_min - l_d_max

    # Identify which arm produced L_D_max
    l_d_max_arm = max(l_d_per_arm, key=lambda k: l_d_per_arm[k]) if l_d_per_arm else None

    # Secondary: H2c replay arm
    l_replay = l_d_per_arm.get(REPLAY_ARM, None)

    # ------------------------------------------------------------------
    # 2.4 Criterion evaluation
    # ------------------------------------------------------------------
    c1_pass = s_a_min  >= C1_THRESHOLD_S_A_MIN
    c2_pass = l_d_max  <= C2_THRESHOLD_L_D_MAX
    c3_pass = delta_b  >= C3_THRESHOLD_DELTA_B
    c4_pass = spam_gate["gate_passed"]  # already confirmed above

    all_pass = c1_pass and c2_pass and c3_pass and c4_pass

    # ------------------------------------------------------------------
    # 2.5 H2a: universality — every DENY arm must individually pass
    # ------------------------------------------------------------------
    h2a_per_arm = {
        n: {"L_D": round(l_d_per_arm[n], 6),
            "pass": l_d_per_arm[n] <= C2_THRESHOLD_L_D_MAX,
            "scenario": arm_metrics[n]["scenario"]}
        for n in DENY_ARMS
        if n in l_d_per_arm
    }
    h2a_pass = all(v["pass"] for v in h2a_per_arm.values())

    # ------------------------------------------------------------------
    # 2.6 H2b: re-authorization restores execution
    # ------------------------------------------------------------------
    h2b_pass = arm_metrics[8]["p1_final"] >= C1_THRESHOLD_S_A_MIN if 8 in arm_metrics else False

    # ------------------------------------------------------------------
    # 2.7 H2c: replay attack with changed state
    # ------------------------------------------------------------------
    h2c_pass = (l_replay is not None) and (l_replay <= C2_THRESHOLD_L_D_MAX)

    # ------------------------------------------------------------------
    # 2.8 Verdict
    # ------------------------------------------------------------------
    verdict = "PASS" if all_pass else "FAIL"

    # If FAIL, identify contributing criteria
    fail_reasons = []
    if not c1_pass:
        fail_reasons.append(
            f"C1: S_A_min = {s_a_min:.4f} < {C1_THRESHOLD_S_A_MIN} "
            f"(ALLOW arms: {s_a_per_arm})"
        )
    if not c2_pass:
        fail_reasons.append(
            f"C2: L_D_max = {l_d_max:.4f} > {C2_THRESHOLD_L_D_MAX} "
            f"(worst arm: {l_d_max_arm}, scenario: "
            f"{arm_metrics.get(l_d_max_arm, {}).get('scenario', '?')})"
        )
    if not c3_pass:
        fail_reasons.append(
            f"C3: Delta_B = {delta_b:.4f} < {C3_THRESHOLD_DELTA_B}"
        )

    return {
        "experiment":        "ARK-449",
        "doctrine_tested":   "Permission at approval time is not permission at execution time.",
        "verdict":           verdict,
        "analysis_timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "spam_gate":         spam_gate,
        "qubit_selection":   raw.get("qubit_selection", {}),
        "shots_principal":   raw.get("shots_principal", SHOTS_PRINCIPAL),
        "spam_job_id":       raw.get("spam_job_id"),
        "principal_job_id":  raw.get("principal_job_id"),

        "primary_metrics": {
            "S_A_arm1":  round(arm_metrics[1]["p1_final"], 6) if 1 in arm_metrics else None,
            "S_A_arm8":  round(arm_metrics[8]["p1_final"], 6) if 8 in arm_metrics else None,
            "S_A_min":   round(s_a_min, 6),
            "L_D_max":   round(l_d_max, 6),
            "L_D_max_arm": l_d_max_arm,
            "Delta_B":   round(delta_b, 6),
        },

        "secondary_metrics": {
            "S_A_per_allow_arm":  {str(k): round(v, 6) for k, v in s_a_per_arm.items()},
            "L_D_per_deny_arm":   {str(k): round(v, 6) for k, v in l_d_per_arm.items()},
            "L_replay_arm9":      round(l_replay, 6) if l_replay is not None else None,
            "h2a_universality":   {str(k): v for k, v in h2a_per_arm.items()},
            "h2b_reauth_restores": h2b_pass,
            "h2c_replay_fails_closed": h2c_pass,
        },

        "criteria": {
            "C1_S_A_min_pass":  c1_pass,
            "C2_L_D_max_pass":  c2_pass,
            "C3_Delta_B_pass":  c3_pass,
            "C4_SPAM_pass":     c4_pass,
            "all_pass":         all_pass,
        },

        "hypothesis_outcomes": {
            "H1_primary":  all_pass,
            "H2a_universality": h2a_pass,
            "H2b_reauth":  h2b_pass,
            "H2c_replay":  h2c_pass,
            "H2d_separation": c3_pass,
        },

        "fail_reasons":  fail_reasons,
        "arm_metrics":   {str(k): v for k, v in arm_metrics.items()},
    }


# ---------------------------------------------------------------------------
# 3. Human-Readable Summary
# ---------------------------------------------------------------------------

def print_summary(result: dict) -> None:
    w = "=" * 70

    print(f"\n{w}")
    print("ARK-449 — Analysis Summary")
    print("State Changes After Verification")
    print("Remnant Fieldworks Inc. — ExecutionProof ARK Series")
    print(w)

    verdict = result["verdict"]
    if verdict == "PASS":
        verdict_display = "✅ PASS"
    elif verdict == "FAIL":
        verdict_display = "❌ FAIL (honest)"
    else:
        verdict_display = "⛔ ABORTED AT SPAM GATE"

    print(f"\nVERDICT: {verdict_display}")

    spam = result.get("spam_gate", {})
    print(f"\nSPAM Gate:")
    print(f"  SPAM_A = {spam.get('SPAM_A', '?'):.4f}  "
          f"({'✅' if spam.get('SPAM_A_pass') else '❌'})")
    print(f"  SPAM_P = {spam.get('SPAM_P', '?'):.4f}  "
          f"({'✅' if spam.get('SPAM_P_pass') else '❌'})")
    print(f"  Gate:   {'✅ PASSED' if spam.get('gate_passed') else '❌ FAILED'}")

    if verdict == "ABORTED AT SPAM GATE":
        print("\nNo principal data was read. Experiment recorded as a "
              "preregistered gate-stop abort.")
        return

    pm = result.get("primary_metrics", {})
    cr = result.get("criteria", {})

    print(f"\nPrimary Metrics:")
    print(f"  S_A (arm 1 — ALLOW-unchanged): {pm.get('S_A_arm1', '?'):.4f}")
    print(f"  S_A (arm 8 — ALLOW-reauth):    {pm.get('S_A_arm8', '?'):.4f}")
    print(f"  S_A_min:  {fmt_criterion(pm.get('S_A_min', 0), C1_THRESHOLD_S_A_MIN, 'ge')}")
    print(f"  L_D_max:  {fmt_criterion(pm.get('L_D_max', 1), C2_THRESHOLD_L_D_MAX, 'le')}"
          f"  (arm {pm.get('L_D_max_arm', '?')})")
    print(f"  Δ_B:      {fmt_criterion(pm.get('Delta_B', 0), C3_THRESHOLD_DELTA_B, 'ge')}")

    sm = result.get("secondary_metrics", {})

    print(f"\nDENY Leakage Per Arm (H2a — universality):")
    h2a = sm.get("h2a_universality", {})
    arm_labels = {
        "2": "revoked",
        "3": "policy",
        "4": "balance",
        "5": "risk",
        "6": "destination",
        "7": "expiry",
        "9": "replay",
    }
    for arm_str, info in sorted(h2a.items(), key=lambda x: int(x[0])):
        icon = "✅" if info["pass"] else "❌"
        print(f"  Arm {arm_str} ({arm_labels.get(arm_str, '?'):>12}): "
              f"L_D = {info['L_D']:.4f}  {icon}")

    print(f"\n  H2a (all DENY arms ≤ 0.02): "
          f"{'✅ CONFIRMED' if sm.get('h2b_reauth_restores') is not None and all(v['pass'] for v in h2a.values()) else '❌ NOT CONFIRMED'}")
    print(f"  H2b (re-auth restores execution): "
          f"{'✅ CONFIRMED' if sm.get('h2b_reauth_restores') else '❌ NOT CONFIRMED'}")
    l_rep = sm.get("L_replay_arm9")
    if l_rep is not None:
        print(f"  H2c (replay with changed state fails closed): "
              f"L_replay = {l_rep:.4f}  "
              f"{'✅ CONFIRMED' if l_rep <= C2_THRESHOLD_L_D_MAX else '❌ NOT CONFIRMED'}")

    print(f"\nCriteria Summary:")
    print(f"  C1 (S_A_min ≥ 0.90):   {'✅ PASS' if cr.get('C1_S_A_min_pass') else '❌ FAIL'}")
    print(f"  C2 (L_D_max ≤ 0.02):   {'✅ PASS' if cr.get('C2_L_D_max_pass') else '❌ FAIL'}")
    print(f"  C3 (Δ_B ≥ 0.70):       {'✅ PASS' if cr.get('C3_Delta_B_pass') else '❌ FAIL'}")
    print(f"  C4 (SPAM gate):        {'✅ PASS' if cr.get('C4_SPAM_pass') else '❌ FAIL'}")

    fail_reasons = result.get("fail_reasons", [])
    if fail_reasons:
        print(f"\nFail Reasons:")
        for reason in fail_reasons:
            print(f"  • {reason}")

    print(f"\nJob IDs:")
    print(f"  SPAM:      {result.get('spam_job_id', 'N/A')}")
    print(f"  Principal: {result.get('principal_job_id', 'N/A')}")

    qs = result.get("qubit_selection", {})
    if qs:
        def _fmt_re(v):
            return f"{v:.4f}" if isinstance(v, (int, float)) else str(v)
        print(f"\nQubit Selection:")
        print(f"  Q_A = {qs.get('Q_A')}  (RE = {_fmt_re(qs.get('RE_A', '?'))})")
        print(f"  Q_P = {qs.get('Q_P')}  (RE = {_fmt_re(qs.get('RE_P', '?'))})")

    print(f"\n{w}")
    print("Doctrine tested: Permission at approval time is not permission")
    print("at execution time.")
    print(f"{w}\n")


# ---------------------------------------------------------------------------
# 4. ProofRecord Generation
# ---------------------------------------------------------------------------

def write_proofrecord(result: dict, path: Path) -> None:
    """
    Write the machine-readable ProofRecord artifact.

    The ProofRecord is the canonical single-document summary of what
    happened, what the outcome was, and where to find the underlying data.
    It is designed to be independently verifiable and referenced by
    future experiments (e.g., ARK-455 — ProofRecord tamper verification).
    """
    proofrecord = {
        "schema":            "ARK-ProofRecord-v1",
        "experiment":        "ARK-449",
        "title":             "State Changes After Verification",
        "doctrine_tested":   "Permission at approval time is not permission at execution time.",
        "repository":        "https://github.com/derekhone/executionproof-testbeds",
        "folder":            "ark-449/",
        "series":            "ExecutionProof ARK Authorization-Boundary Track",
        "company":           "Remnant Fieldworks Inc.",

        "execution": {
            "backend":            "ibm_marrakesh",
            "backend_description": "IBM Quantum 156-qubit Heron r2",
            "spam_job_id":        result.get("spam_job_id"),
            "principal_job_id":   result.get("principal_job_id"),
            "shots_spam":         2048,
            "shots_principal":    8192,
            "arms":               9,
            "qubit_selection":    result.get("qubit_selection", {}),
            "analysis_timestamp": result.get("analysis_timestamp"),
        },

        "spam_gate":     result.get("spam_gate", {}),

        "verdict":       result["verdict"],
        "verdict_emoji": {
            "PASS":                "✅",
            "FAIL":                "❌",
            "ABORTED AT SPAM GATE": "⛔",
        }.get(result["verdict"], "?"),

        "primary_metrics":   result.get("primary_metrics", {}),
        "secondary_metrics": result.get("secondary_metrics", {}),

        "criteria": result.get("criteria", {}),

        "hypothesis_outcomes": result.get("hypothesis_outcomes", {}),

        "fail_reasons": result.get("fail_reasons", []),

        "arm_metrics": result.get("arm_metrics", {}),

        "honest_caveats": [
            "Classical state model: c_state is a deterministic classical parameter per arm, "
            "not measured from a live external system. Tests authorization control logic "
            "under definitive state change, not distributed-systems state propagation.",
            "Deterministic state changes only: ambiguous or probabilistic state signals "
            "are deferred to ARK-453 (Conflicting Evidence Must HOLD).",
            "Timing model: T1/T3 gap modeled logically as sequential circuit arms, "
            "not physical elapsed real-world time.",
            "Results apply to the specific backend, qubit pair, calibration snapshot, "
            "and shot counts used.",
            "These are hardware noise-characterization studies, not cryptographic security proofs.",
            "Error mitigation is not error correction (no QEC).",
        ],

        "corpus_position": {
            "adds_to_corpus": "Temporal state validity dimension — authorization currency.",
            "complements": ["ARK-442 (stale authority)", "ARK-444 (tamper detection)"],
            "enables": ["ARK-451 (mid-execution revocation)", "ARK-452 (multi-step workflow)",
                        "ARK-453 (conflicting evidence)"],
        },

        "zenodo_doi":    None,   # filled at Zenodo publication
        "manifest_sha256": None, # filled at lock time from MANIFEST.txt
    }

    with open(path, "w") as f:
        json.dump(proofrecord, f, indent=2)

    print(f"[ARK-449] ProofRecord written to {path}")


# ---------------------------------------------------------------------------
# 5. Entry Point
# ---------------------------------------------------------------------------

def main():
    print("[ARK-449] Loading raw results…")
    raw = load_raw(RAW_RESULTS_FILE)

    print("[ARK-449] Running preregistered analysis…")
    result = analyse(raw)

    # Write analysis results
    with open(ANALYSIS_OUT_FILE, "w") as f:
        json.dump(result, f, indent=2)
    print(f"[ARK-449] Analysis results written to {ANALYSIS_OUT_FILE}")

    # Write ProofRecord
    write_proofrecord(result, PROOFRECORD_FILE)

    # Human-readable summary to stdout
    print_summary(result)

    # Exit code reflects verdict for CI integration
    if result["verdict"] == "PASS":
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
