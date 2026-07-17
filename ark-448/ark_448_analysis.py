#!/usr/bin/env python3
"""
ARK-448 Analysis and Verdict — Dynamical Decoupling vs. Baseline.

Computes S_A, L_D_raw, Delta_B for the baseline and DD configurations, applies
the preregistered pass criteria and verdict rules, and runs a two-proportion
z-test on the DD-vs-baseline change in S_A and L_D_raw.

SPAM note (per ARK-447 v1.1): SPAM_P (|+> -> ~0.5) is a GATING diagnostic only
and is NEVER subtracted from DENY leakage. DENY leakage is reported RAW.
"""
import json
import sys
import math
from datetime import datetime, timezone

def load_results():
    with open('raw_results.json', 'r') as f:
        raw = json.load(f)
    with open('spam_results.json', 'r') as f:
        spam = json.load(f)
    with open('principal_job_meta.json', 'r') as f:
        meta = json.load(f)
    with open('selected_qubits.json', 'r') as f:
        qubits = json.load(f)
    return raw, spam, meta, qubits

def analyze_configuration(config_name, allow_arm, deny_arm, raw_results):
    allow_counts = raw_results[allow_arm]
    deny_counts = raw_results[deny_arm]

    allow_total = sum(allow_counts.values())
    allow_1 = sum(c for o, c in allow_counts.items() if o[-1] == '1')
    S_A = allow_1 / allow_total

    deny_total = sum(deny_counts.values())
    deny_1 = sum(c for o, c in deny_counts.items() if o[-1] == '1')
    L_D_raw = deny_1 / deny_total

    Delta_B = S_A - L_D_raw - 0.20

    criteria = {
        'S_A >= 0.90': S_A >= 0.90,
        'L_D_raw <= 0.02': L_D_raw <= 0.02,
        'Delta_B >= 0.00': Delta_B >= 0.00,
    }
    return {
        'config_name': config_name,
        'allow_arm': allow_arm, 'deny_arm': deny_arm,
        'allow_1': allow_1, 'allow_total': allow_total,
        'deny_1': deny_1, 'deny_total': deny_total,
        'S_A': S_A, 'L_D_raw': L_D_raw, 'Delta_B': Delta_B,
        'criteria': criteria,
        'verdict': 'PASS' if all(criteria.values()) else 'FAIL',
    }

def two_proportion_z(x1, n1, x2, n2):
    """Two-proportion z-test. Returns (z, two-sided p). Group1 vs group2."""
    if n1 == 0 or n2 == 0:
        return 0.0, 1.0
    p1, p2 = x1 / n1, x2 / n2
    p_pool = (x1 + x2) / (n1 + n2)
    se = math.sqrt(p_pool * (1 - p_pool) * (1 / n1 + 1 / n2))
    if se == 0:
        return 0.0, 1.0
    z = (p1 - p2) / se
    p = math.erfc(abs(z) / math.sqrt(2))  # two-sided
    return z, p

def main():
    raw, spam, meta, qubits = load_results()
    spam_p_prob = spam['SPAM_P']['prob_1']

    print("=== ARK-448 Analysis (Dynamical Decoupling vs. Baseline) ===\n")
    print(f"Backend: {meta['backend']}")
    print(f"Q_A = {qubits['Q_A']}, Q_P = {qubits['Q_P']}")
    print(f"Idle window tau = {meta.get('tau_us')} us; DD sequence = {meta.get('dd_sequence')}")
    print(f"SPAM_P (P('1')||+>): {spam_p_prob:.4f} — GATING diagnostic only, NOT subtracted\n")
    print("DENY leakage reported as RAW (no SPAM subtraction).\n")

    configs = {}
    configs['baseline'] = analyze_configuration('Baseline (idle, no DD)',
                                                'arm1_ALLOW_baseline', 'arm2_DENY_baseline', raw)
    configs['dd'] = analyze_configuration('Dynamical Decoupling (XX)',
                                          'arm3_ALLOW_dd', 'arm4_DENY_dd', raw)

    print("=== Configuration Results ===\n")
    for cfg in configs.values():
        print(f"**{cfg['config_name']}**")
        print(f"   S_A     = {cfg['S_A']:.4f} (>=0.90: {cfg['criteria']['S_A >= 0.90']})")
        print(f"   L_D_raw = {cfg['L_D_raw']:.4f} (<=0.02: {cfg['criteria']['L_D_raw <= 0.02']})")
        print(f"   Delta_B = {cfg['Delta_B']:.4f} (>=0.00: {cfg['criteria']['Delta_B >= 0.00']})")
        print(f"   VERDICT: {cfg['verdict']}\n")

    # DD vs baseline statistical comparison
    b, d = configs['baseline'], configs['dd']
    z_sa, p_sa = two_proportion_z(d['allow_1'], d['allow_total'], b['allow_1'], b['allow_total'])
    z_ld, p_ld = two_proportion_z(d['deny_1'], d['deny_total'], b['deny_1'], b['deny_total'])
    dS_A = d['S_A'] - b['S_A']
    dL_D = d['L_D_raw'] - b['L_D_raw']

    print("=== DD vs. Baseline (two-proportion z-test) ===")
    print(f"   Delta S_A (DD - baseline)     = {dS_A:+.4f}  (z={z_sa:+.2f}, p={p_sa:.4f})")
    print(f"   Delta L_D_raw (DD - baseline) = {dL_D:+.4f}  (z={z_ld:+.2f}, p={p_ld:.4f})\n")

    baseline_pass = b['verdict'] == 'PASS'
    dd_pass = d['verdict'] == 'PASS'
    dd_helps_SA = dS_A > 0 and p_sa < 0.05
    dd_helps_LD = dL_D < 0 and p_ld < 0.05
    dd_improves = dd_helps_SA or dd_helps_LD

    if baseline_pass and dd_pass:
        if dd_improves:
            overall = 'PASS (strong)'
            reason = 'Both pass; DD gives a statistically significant improvement (S_A up and/or L_D down).'
        else:
            overall = 'PASS (weak)'
            reason = ('Both pass; DD shows no statistically significant improvement over baseline '
                      '(null result — consistent with T1-dominated authorizer decay that DD does not mitigate).')
    elif baseline_pass != dd_pass:
        overall = 'MIXED'
        reason = ('Baseline passes but DD fails.' if baseline_pass else 'DD passes but baseline fails.')
    else:
        overall = 'FAIL'
        reason = ('Neither configuration passes: the 20us idle window degrades the authorization '
                  'boundary below threshold (honest negative demonstrating idle-time sensitivity).')

    print("=== Overall Verdict ===")
    print(f"VERDICT: {overall}")
    print(f"Reason: {reason}\n")

    proofrecord = {
        'experiment': 'ARK-448',
        'title': 'Dynamical Decoupling vs. Baseline under an idle window',
        'idle_window_us': meta.get('tau_us'),
        'dd_sequence': meta.get('dd_sequence'),
        'spam_methodology_note': ('SPAM_P (|+> -> ~0.5) is a gating diagnostic ONLY, never subtracted '
                                  'from DENY leakage. DENY leakage reported RAW.'),
        'backend': meta['backend'],
        'qubits': {
            'Q_A': qubits['Q_A'], 'Q_P': qubits['Q_P'],
            'Q_A_readout_error': qubits['Q_A_readout_error'],
            'Q_P_readout_error': qubits['Q_P_readout_error'],
            'sum_readout_error': qubits['sum_readout_error'],
        },
        'spam_gate': {
            'job_id': spam['job_id'],
            'SPAM_A_error': spam['SPAM_A']['error'],
            'SPAM_P_prob_1': spam['SPAM_P']['prob_1'],
            'SPAM_P_role': 'gating diagnostic only; NOT a correction term',
            'gate_passed': spam['gate_passed'],
        },
        'principal_job': {
            'job_id': meta['job_id'],
            'shots_per_circuit': meta['shots_per_circuit'],
            'num_circuits': meta['num_circuits'],
        },
        'configurations': configs,
        'dd_vs_baseline': {
            'delta_S_A': dS_A, 'z_S_A': z_sa, 'p_S_A': p_sa,
            'delta_L_D_raw': dL_D, 'z_L_D_raw': z_ld, 'p_L_D_raw': p_ld,
            'alpha': 0.05,
            'dd_improves_significantly': bool(dd_improves),
        },
        'verdict': {
            'overall': overall, 'reason': reason,
            'timestamp_utc': datetime.now(timezone.utc).isoformat(),
        },
        'protocol': 'Field 27 (LOCK -> SPAM gate -> principal job -> analyze -> verdict)',
        'preregistration': 'ARK_448_preregistration.md',
        'interpretation_boundaries': [
            'Results apply to this backend, qubit pair, calibration, and tau=20us only.',
            'Hardware noise-mitigation study, NOT a cryptographic security validation.',
            'DD is error mitigation, not correction; no QEC used.',
            'Single-round binary boundary only.',
            'Authorizer |1> decays primarily via T1, which DD does not mitigate; a limited DD '
            'benefit is expected and does not indicate methodological failure.',
            'DENY leakage reported RAW; SPAM_P is a gating diagnostic, not a correction term.',
        ],
    }
    with open('proofrecord.json', 'w') as f:
        json.dump(proofrecord, f, indent=2)

    print("Proofrecord saved to proofrecord.json")
    print("ARK-448 analysis complete.")
    return 0 if overall.startswith('PASS') else 1

if __name__ == '__main__':
    sys.exit(main())
