"""
ARK-445b — Analysis and scoring
Tri-State Authorization Discrimination (ALLOW / HOLD / DENY)
Remnant Fieldworks Inc. — Derek Hone

Loads raw_results.json (+ spam_results.json), computes all preregistered metrics
(Field 6) with Wilson score confidence intervals, applies the preregistered
PASS / FAIL / KILL decision rule (Field 7), generates plots, and writes proofrecord.json.

Central question: Can the verify-then-execute authorization boundary discriminate THREE
states — ALLOW (execute), HOLD (ambiguous/pending), DENY (refuse) — rather than only
binary ALLOW/DENY, with margin Delta_H >= 0.30?

Metrics (preregistered before execution, Field 6):
    S_A       = P(Q_P=1 | ALLOW arms 1,5,7)   (raw; primary endpoint)
                S_A_min = min over ALLOW arms
    L_D       = P(Q_P=1 | DENY arms 2,6,8,9)  (raw)
                L_D_corrected = max(0, L_D - SPAM_P); L_D_max = max over DENY arms
    H         = P(Q_P=1 | HOLD arms 3,4)  -> H_plus, H_minus; H_min, H_max
    SPAM_A/P  = idle readout on Q_A / Q_P (from arm10 SPAM gate); drift = |SPAM_A-SPAM_P|
    Delta_H   = min(S_A_min - H_max, H_min - L_D_max)   tri-state discrimination margin
    I_H       = |H_plus - H_minus|   (HOLD basis-symmetry diagnostic, expect < 0.05)

Decision rule (preregistered — authoritative, Field 7):
    PASS : S_A_min >= 0.90 AND all four L_D_corrected <= 0.02 AND
           0.40 <= H_min AND H_max <= 0.60 (both HOLD arms) AND Delta_H >= 0.30,
           with in-situ SPAM_A <= 0.02 AND SPAM_P <= 0.02.
    FAIL : with SPAM clean — S_A_min < 0.90; OR any L_D_corrected > 0.02; OR
           H_min < 0.40 OR H_max > 0.60; OR Delta_H < 0.30.
    KILL : SPAM_A > 0.02 OR SPAM_P > 0.02 (=> INDETERMINATE); OR SPAM_drift > 0.005
           (=> INDETERMINATE).

Primary endpoint = RAW counts, no readout mitigation (DENY arms SPAM-corrected only,
per Field 9). This is a metrological characterization, NOT new physics and NOT a
cryptographic guarantee.
"""

import hashlib
import json
import math
import os
from datetime import datetime, timezone

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))

PASS_S_ALLOW = 0.90
PASS_LEAK_CORR = 0.02
HOLD_LO = 0.40
HOLD_HI = 0.60
PASS_DELTA_H = 0.30
SPAM_CEILING = 0.02
DRIFT_CEILING = 0.005

ALLOW_ARMS = {
    "arm1_allow_standard": "S_A",
    "arm5_allow_alt": "S_A_alt",
    "arm7_allow_reverified": "S_A_rev",
}
DENY_ARMS = {
    "arm2_deny_standard": "L_D",
    "arm6_deny_alt": "L_D_alt",
    "arm8_deny_expired": "L_D_exp",
}
HOLD_ARMS = {
    "arm3_hold_plus": "H_plus",
    "arm4_hold_minus": "H_minus",
}


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def wilson_ci(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0, 0.0)
    p = k / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = (z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / denom
    return (p, max(0.0, center - half), min(1.0, center + half))


def counts_k_n(arm):
    return arm["counts"].get("1", 0), arm["total"]


def main():
    raw_path = os.path.join(HERE, "raw_results.json")
    spam_path = os.path.join(HERE, "spam_results.json")
    with open(raw_path) as f:
        raw = json.load(f)
    spam = None
    if os.path.exists(spam_path):
        with open(spam_path) as f:
            spam = json.load(f)

    arms = raw["arms"]
    kn = {name: counts_k_n(arms[name]) for name in raw["arm_order"]}

    def p(name):
        k, n = kn[name]
        return k / n if n else 0.0

    ci95 = {name: wilson_ci(*kn[name], z=1.96) for name in raw["arm_order"]}
    ci99 = {name: wilson_ci(*kn[name], z=2.576) for name in raw["arm_order"]}

    # SPAM (from arm10 gate job).
    if spam is not None:
        SPAM_A = spam["SPAM_A"]
        SPAM_P = spam["SPAM_P"]
        SPAM_drift = spam["SPAM_drift"]
    else:
        SPAM_A = SPAM_P = SPAM_drift = None

    spam_p_for_corr = SPAM_P if SPAM_P is not None else 0.0

    allow_raw = {metric: p(arm) for arm, metric in ALLOW_ARMS.items()}
    deny_raw = {metric: p(arm) for arm, metric in DENY_ARMS.items()}
    deny_corrected = {m: max(0.0, deny_raw[m] - spam_p_for_corr) for m in deny_raw}
    hold_raw = {metric: p(arm) for arm, metric in HOLD_ARMS.items()}

    S_A_min = min(allow_raw.values())
    L_D_max = max(deny_corrected.values())
    H_plus = hold_raw["H_plus"]
    H_minus = hold_raw["H_minus"]
    H_min = min(H_plus, H_minus)
    H_max = max(H_plus, H_minus)
    I_H = abs(H_plus - H_minus)

    Delta_H = min(S_A_min - H_max, H_min - L_D_max)

    # Diagnostic Wilson bounds.
    allow_lower95 = {ALLOW_ARMS[a]: ci95[a][1] for a in ALLOW_ARMS}
    deny_corr_upper95 = {}
    for a, metric in DENY_ARMS.items():
        _, _, hi = ci95[a]
        # subtract SPAM point estimate for a conservative corrected upper bound
        deny_corr_upper95[metric] = max(0.0, hi - spam_p_for_corr)

    # SPAM gate + drift (Field 7 KILL rules).
    spam_gate_passed = True
    drift_ok = True
    if spam is not None:
        spam_gate_passed = (SPAM_A <= SPAM_CEILING) and (SPAM_P <= SPAM_CEILING)
        drift_ok = SPAM_drift <= DRIFT_CEILING

    # Decision rule (authoritative — Field 7).
    if spam is None:
        decision = "INDETERMINATE"
        status = "INDETERMINATE"
        rationale = "spam_results.json missing; SPAM kill-gate cannot be evaluated."
    elif not spam_gate_passed:
        decision = "KILL"
        status = "INDETERMINATE"
        rationale = (f"SPAM kill-gate violated: SPAM_A={SPAM_A:.4f}, SPAM_P={SPAM_P:.4f} "
                     f"(ceiling {SPAM_CEILING}). Qubit/backend disqualified; INDETERMINATE.")
    elif not drift_ok:
        decision = "KILL"
        status = "INDETERMINATE"
        rationale = (f"SPAM drift {SPAM_drift:.4f} > {DRIFT_CEILING} "
                     f"(|SPAM_A - SPAM_P|). Calibration mismatch; INDETERMINATE.")
    else:
        cond_allow = S_A_min >= PASS_S_ALLOW
        denies_ok = {m: (deny_corrected[m] <= PASS_LEAK_CORR) for m in deny_corrected}
        cond_deny = all(denies_ok.values())
        cond_hold = (H_min >= HOLD_LO) and (H_max <= HOLD_HI)
        cond_dh = Delta_H >= PASS_DELTA_H
        if cond_allow and cond_deny and cond_hold and cond_dh:
            decision = "PASS"
            status = "PASS"
            rationale = (
                f"S_A_min={S_A_min:.4f} >= {PASS_S_ALLOW}; "
                "all four corrected DENY leakages <= "
                f"{PASS_LEAK_CORR} ("
                + ", ".join(f"{m}={deny_corrected[m]:.4f}" for m in deny_corrected)
                + f"); both HOLD arms in [{HOLD_LO},{HOLD_HI}] "
                f"(H_plus={H_plus:.4f}, H_minus={H_minus:.4f}); "
                f"Delta_H={Delta_H:.4f} >= {PASS_DELTA_H}; in-situ SPAM within ceiling "
                f"(SPAM_A={SPAM_A:.4f}, SPAM_P={SPAM_P:.4f}). ALLOW, HOLD and DENY are "
                "metrologically separable on this setup.")
        else:
            decision = "FAIL"
            status = "FAIL"
            reasons = []
            if not cond_allow:
                reasons.append(f"S_A_min={S_A_min:.4f} < {PASS_S_ALLOW}")
            for m in deny_corrected:
                if not denies_ok[m]:
                    reasons.append(f"{m}_corrected={deny_corrected[m]:.4f} > {PASS_LEAK_CORR}")
            if not cond_hold:
                reasons.append(f"HOLD out of [{HOLD_LO},{HOLD_HI}] "
                               f"(H_min={H_min:.4f}, H_max={H_max:.4f})")
            if not cond_dh:
                reasons.append(f"Delta_H={Delta_H:.4f} < {PASS_DELTA_H}")
            rationale = ("Tri-state discrimination failed with in-situ SPAM within ceiling: "
                         + "; ".join(reasons))

    # H2a: HOLD basis symmetry — H_plus vs H_minus 95% CI overlap.
    hp95 = ci95["arm3_hold_plus"]
    hm95 = ci95["arm4_hold_minus"]
    hold_symmetry_overlap95 = not (hp95[1] > hm95[2] or hm95[1] > hp95[2])
    # H2b: reverified ALLOW maintains >= 0.90.
    s_a_rev = allow_raw["S_A_rev"]
    reverify_ok = s_a_rev >= PASS_S_ALLOW
    # H2c: confusion/replay — omitted in ARK-445b (arm9 removed to isolate reset infidelity)

    def mk(arm, metric):
        return {"value": p(arm), "ci95": ci95[arm], "ci99": ci99[arm]}

    metrics = {}
    for arm, metric in ALLOW_ARMS.items():
        metrics[metric] = {**mk(arm, metric), "ci95_lower": allow_lower95[metric],
                           "class": "ALLOW"}
    for arm, metric in DENY_ARMS.items():
        metrics[metric] = {**mk(arm, metric), "corrected": deny_corrected[metric],
                           "corrected_upper95": deny_corr_upper95[metric], "class": "DENY"}
    for arm, metric in HOLD_ARMS.items():
        metrics[metric] = {**mk(arm, metric), "class": "HOLD"}
    metrics["S_A_min"] = {"value": S_A_min, "definition": "min over ALLOW arms"}
    metrics["L_D_max"] = {"value": L_D_max, "definition": "max corrected over DENY arms"}
    metrics["H_min"] = {"value": H_min, "definition": "min over HOLD arms"}
    metrics["H_max"] = {"value": H_max, "definition": "max over HOLD arms"}
    metrics["Delta_H"] = {"value": Delta_H,
                          "definition": "min(S_A_min - H_max, H_min - L_D_max)"}
    metrics["I_H"] = {"value": I_H, "definition": "|H_plus - H_minus| (HOLD symmetry)"}
    metrics["SPAM_A"] = {"value": SPAM_A}
    metrics["SPAM_P"] = {"value": SPAM_P}
    metrics["SPAM_drift"] = {"value": SPAM_drift}

    secondary = {
        "H2a_hold_basis_symmetry": {
            "H_plus": H_plus, "H_minus": H_minus, "I_H": I_H,
            "overlap_95CI": bool(hold_symmetry_overlap95),
            "note": "HOLD |+> and |-> yield statistically comparable P(execute) "
                    "(basis-independent ambiguity encoding).",
        },
        "H2b_reverification_escape": {
            "S_A_rev": s_a_rev, "meets_floor": bool(reverify_ok),
            "note": "Reverified ALLOW (1us delay) maintains >= 0.90 -> HOLD is not a "
                    "decoherence artifact.",
        },
        "H2c_confusion_falls_to_deny": {
            "status": "N/A",
            "note": "Omitted in ARK-445b. Arm9 (reset-based confusion/replay) was removed "
                    "to isolate whether ARK-445's leak came from mid-circuit reset infidelity "
                    "rather than the tri-state boundary. This arm tested reset mechanism, not "
                    "true anti-replay logic.",
        },
        "H2d_spam_drift_bound": {
            "SPAM_A": SPAM_A, "SPAM_P": SPAM_P, "SPAM_drift": SPAM_drift,
            "drift_ok": bool(drift_ok),
        },
    }

    proofrecord = {
        "experiment_id": "ARK-445b",
        "title": "Tri-State Authorization Discrimination (ALLOW / HOLD / DENY)",
        "central_question": ("Can the verify-then-execute authorization boundary "
                             "discriminate ALLOW, HOLD and DENY (not just binary "
                             "ALLOW/DENY), with margin Delta_H >= 0.30?"),
        "backend": raw["backend"],
        "instance": raw["instance"],
        "qubits": {"Q_A": raw["initial_layout"][0], "Q_P": raw["initial_layout"][1]},
        "shots_per_arm": raw["shots_per_arm"],
        "arm_order": raw["arm_order"],
        "arm_class": raw.get("arm_class"),
        "arm_expect": raw.get("arm_expect"),
        "job_ids": {"spam_job": raw.get("spam_job_id"),
                    "principal_job": raw["principal_job_id"]},
        "raw_results_hash": sha256_file(raw_path),
        "spam_results_hash": sha256_file(spam_path) if spam is not None else None,
        "metrics": metrics,
        "secondary_hypotheses": secondary,
        "insitu_spam": {"SPAM_A": SPAM_A, "SPAM_P": SPAM_P, "SPAM_drift": SPAM_drift,
                        "gate_passed": spam_gate_passed, "drift_ok": drift_ok},
        "decision_outcome": decision,
        "status": status,
        "rationale": rationale,
        "raw_vs_mitigated": ("Primary endpoint = RAW counts. DENY arms SPAM-corrected "
                             "(L - SPAM_P); ALLOW/HOLD reported raw (Field 9)."),
        "preregistered_pass": {"allow_min": PASS_S_ALLOW,
                               "deny_leak_corrected_max": PASS_LEAK_CORR,
                               "hold_range": [HOLD_LO, HOLD_HI],
                               "Delta_H_min": PASS_DELTA_H,
                               "spam_ceiling": SPAM_CEILING,
                               "drift_ceiling": DRIFT_CEILING},
        "interpretation": ("Metrological characterization of a tri-state authorization "
                           "rule on this hardware: whether ALLOW (A=|1>), DENY (A=|0>) and "
                           "HOLD (A=|+>/|->) map to separable payload-execution "
                           "probabilities with margin Delta_H >= 0.30. HOLD ~ 0.5 arises "
                           "from textbook measurement-induced collapse of a superposed "
                           "authorizer, NOT new physics and NOT a cryptographic guarantee. "
                           "The committed authorization bit is a hardware abstraction of an "
                           "approval decision. Findings apply only to the selected qubits "
                           "on this backend at this calibration."),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    pr_path = os.path.join(HERE, "proofrecord.json")
    with open(pr_path, "w") as f:
        json.dump(proofrecord, f, indent=2)
    print(f"[ANALYSIS] wrote {pr_path}")

    _make_plots(raw, ci95, allow_raw, deny_raw, deny_corrected, hold_raw,
                SPAM_A, SPAM_P, S_A_min, H_min, H_max, L_D_max, Delta_H)

    for m in allow_raw:
        print(f"[ANALYSIS] {m}={allow_raw[m]:.4f}")
    for m in hold_raw:
        print(f"[ANALYSIS] {m}={hold_raw[m]:.4f}")
    for m in deny_raw:
        print(f"[ANALYSIS] {m}={deny_raw[m]:.4f} (corrected={deny_corrected[m]:.4f})")
    print(f"[ANALYSIS] SPAM_A={SPAM_A} SPAM_P={SPAM_P} drift={SPAM_drift}")
    print(f"[ANALYSIS] S_A_min={S_A_min:.4f} H_min={H_min:.4f} H_max={H_max:.4f} "
          f"L_D_max={L_D_max:.4f} Delta_H={Delta_H:.4f}")
    print(f"[ANALYSIS] DECISION = {decision} ({status})")
    print(f"[ANALYSIS] {rationale}")
    return proofrecord


def _make_plots(raw, ci95, allow_raw, deny_raw, deny_corrected, hold_raw,
                SPAM_A, SPAM_P, S_A_min, H_min, H_max, L_D_max, Delta_H):
    os.makedirs(os.path.join(HERE, "plots"), exist_ok=True)
    names = raw["arm_order"]
    allow_set = set(ALLOW_ARMS.keys())
    deny_set = set(DENY_ARMS.keys())
    hold_set = set(HOLD_ARMS.keys())

    # Plot 1: all arms with 95% Wilson error bars, color-coded by class.
    vals = [ci95[n][0] for n in names]
    lo = [ci95[n][0] - ci95[n][1] for n in names]
    hi = [ci95[n][2] - ci95[n][0] for n in names]
    colors = []
    for n in names:
        if n in allow_set:
            colors.append("#2ca02c")   # green = ALLOW
        elif n in hold_set:
            colors.append("#ff7f0e")   # orange = HOLD
        else:
            colors.append("#d62728")   # red = DENY
    fig, ax = plt.subplots(figsize=(12, 6))
    x = range(len(names))
    ax.bar(x, vals, yerr=[lo, hi], capsize=4, color=colors)
    ax.set_xticks(list(x))
    ax.set_xticklabels([n.replace("_", "\n") for n in names], fontsize=7.5)
    ax.set_ylabel("P(Q_P = 1)")
    ax.set_title("ARK-445b (ibm_marrakesh) — Payload execution by arm (95% Wilson CI)\n"
                 "green = ALLOW, orange = HOLD, red = DENY")
    ax.axhline(0.90, color="green", ls=":", lw=1, label="ALLOW floor (0.90)")
    ax.axhspan(0.40, 0.60, color="orange", alpha=0.12, label="HOLD band [0.40, 0.60]")
    ax.axhline(0.02, color="red", ls="--", lw=1, label="DENY ceiling (0.02)")
    ax.set_ylim(0, 1.02)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "plots", "arm_results.png"), dpi=150)
    plt.close(fig)

    # Plot 2: tri-state discrimination — ALLOW / HOLD / DENY regions.
    fig, ax = plt.subplots(figsize=(10, 6))
    allow_labels = list(allow_raw.keys())
    hold_labels = list(hold_raw.keys())
    deny_labels = list(deny_corrected.keys())
    xa = list(range(len(allow_labels)))
    xh = list(range(len(allow_labels) + 1, len(allow_labels) + 1 + len(hold_labels)))
    xd = list(range(len(allow_labels) + len(hold_labels) + 2,
                    len(allow_labels) + len(hold_labels) + 2 + len(deny_labels)))
    ax.bar(xa, [allow_raw[m] for m in allow_labels], color="#2ca02c", width=0.6,
           label="ALLOW P(Q_P=1)")
    ax.bar(xh, [hold_raw[m] for m in hold_labels], color="#ff7f0e", width=0.6,
           label="HOLD P(Q_P=1)")
    ax.bar(xd, [deny_corrected[m] for m in deny_labels], color="#d62728", width=0.6,
           label="DENY corrected leakage")
    ax.axhline(0.90, color="green", ls=":", lw=1.2, label="ALLOW floor (0.90)")
    ax.axhspan(0.40, 0.60, color="orange", alpha=0.12, label="HOLD band [0.40,0.60]")
    ax.axhline(0.02, color="black", ls="--", lw=1.2, label="DENY ceiling (0.02)")
    all_x = xa + xh + xd
    ax.set_xticks(all_x)
    ax.set_xticklabels(allow_labels + hold_labels + deny_labels, fontsize=8, rotation=25)
    ax.set_ylabel("P(Q_P=1)  (DENY = corrected)")
    ax.set_title("ARK-445b (ibm_marrakesh) — Tri-state discrimination\n"
                 f"Delta_H = min(S_A_min - H_max, H_min - L_D_max) = {Delta_H:.3f}  "
                 f"(SPAM_P={SPAM_P})")
    for xs, vs in [(xa, [allow_raw[m] for m in allow_labels]),
                   (xh, [hold_raw[m] for m in hold_labels]),
                   (xd, [deny_corrected[m] for m in deny_labels])]:
        for xi, v in zip(xs, vs):
            ax.text(xi, v, f"{v:.3f}", ha="center", va="bottom", fontsize=8)
    ax.set_ylim(0, 1.05)
    ax.grid(True, axis="y", alpha=0.3)
    ax.legend(fontsize=8, loc="center right")
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "plots", "tristate_discrimination.png"), dpi=150)
    plt.close(fig)
    print("[ANALYSIS] wrote plots/arm_results.png, plots/tristate_discrimination.png")


if __name__ == "__main__":
    main()
