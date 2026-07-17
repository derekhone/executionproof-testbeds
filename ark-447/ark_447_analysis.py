#!/usr/bin/env python3
"""
ARK-447 Analysis and Verdict (Updated)
Computes metrics for baseline vs. Pauli twirling and determines verdict.
"""
import json
import sys
from datetime import datetime, timezone

def load_results():
    """Load raw results, SPAM results, and metadata."""
    with open('raw_results.json', 'r') as f:
        raw = json.load(f)
    with open('spam_results.json', 'r') as f:
        spam = json.load(f)
    with open('principal_job_meta.json', 'r') as f:
        meta = json.load(f)
    with open('selected_qubits.json', 'r') as f:
        qubits = json.load(f)
    
    return raw, spam, meta, qubits

def compute_prob(counts, outcome, shots=8192):
    """Compute probability of a specific outcome."""
    return counts.get(outcome, 0) / shots

def analyze_configuration(config_name, allow_arm, deny_arm, raw_results, spam_p_prob):
    """
    Analyze a single configuration (baseline or twirling).
    
    Returns:
        dict with S_A, L_D_raw, L_D_corrected, Delta_B, and pass/fail status
    """
    allow_counts = raw_results[allow_arm]
    deny_counts = raw_results[deny_arm]
    
    # Extract payload outcomes (rightmost bit in bitstring)
    allow_total = sum(allow_counts.values())
    allow_payload_1 = sum(count for outcome, count in allow_counts.items() if outcome[-1] == '1')
    S_A = allow_payload_1 / allow_total
    
    deny_total = sum(deny_counts.values())
    deny_payload_1 = sum(count for outcome, count in deny_counts.items() if outcome[-1] == '1')
    L_D_raw = deny_payload_1 / deny_total
    
    # SPAM correction
    L_D_corrected = max(0.0, L_D_raw - spam_p_prob)
    
    # Boundary margin
    Delta_B = S_A - L_D_corrected - 0.20
    
    # Check criteria
    criteria = {
        'S_A >= 0.90': S_A >= 0.90,
        'L_D_corrected <= 0.02': L_D_corrected <= 0.02,
        'Delta_B >= 0.00': Delta_B >= 0.00
    }
    
    all_passed = all(criteria.values())
    
    return {
        'config_name': config_name,
        'allow_arm': allow_arm,
        'deny_arm': deny_arm,
        'S_A': S_A,
        'L_D_raw': L_D_raw,
        'L_D_corrected': L_D_corrected,
        'Delta_B': Delta_B,
        'criteria': criteria,
        'verdict': 'PASS' if all_passed else 'FAIL'
    }

def main():
    # Load data
    raw, spam, meta, qubits = load_results()
    
    # Extract SPAM_P probability (for correction)
    spam_p_prob = spam['SPAM_P']['prob_1']
    
    print("=== ARK-447 Analysis ===\n")
    print(f"Backend: {meta['backend']}")
    print(f"Q_A = {qubits['Q_A']}, Q_P = {qubits['Q_P']}")
    print(f"SPAM_P (prob '1' | |+⟩): {spam_p_prob:.4f}\n")
    print(f"Note: DD circuits omitted; comparing baseline vs. Pauli twirling only.\n")
    
    # Analyze each configuration
    configs = {}
    
    configs['baseline'] = analyze_configuration(
        'Baseline',
        'arm1_ALLOW_baseline',
        'arm2_DENY_baseline',
        raw,
        spam_p_prob
    )
    
    configs['twirling'] = analyze_configuration(
        'Pauli Twirling',
        'arm3_ALLOW_twirl',
        'arm4_DENY_twirl',
        raw,
        spam_p_prob
    )
    
    # Print results
    print("=== Configuration Results ===\n")
    for key, cfg in configs.items():
        print(f"**{cfg['config_name']}**")
        print(f"   S_A = {cfg['S_A']:.4f} (≥0.90: {cfg['criteria']['S_A >= 0.90']})")
        print(f"   L_D_raw = {cfg['L_D_raw']:.4f}")
        print(f"   L_D_corrected = {cfg['L_D_corrected']:.4f} (≤0.02: {cfg['criteria']['L_D_corrected <= 0.02']})")
        print(f"   Delta_B = {cfg['Delta_B']:.4f} (≥0.00: {cfg['criteria']['Delta_B >= 0.00']})")
        print(f"   VERDICT: {cfg['verdict']}\n")
    
    # Overall verdict
    baseline_pass = configs['baseline']['verdict'] == 'PASS'
    twirl_pass = configs['twirling']['verdict'] == 'PASS'
    
    if baseline_pass and twirl_pass:
        # Check for improvement
        twirl_improvement = (configs['twirling']['S_A'] > configs['baseline']['S_A'] or
                             configs['twirling']['L_D_corrected'] < configs['baseline']['L_D_corrected'])
        
        if twirl_improvement:
            overall_verdict = 'PASS (strong)'
            verdict_reason = 'Both configs pass; Pauli twirling shows improvement over baseline.'
        else:
            overall_verdict = 'PASS (weak)'
            verdict_reason = 'Both configs pass; no significant improvement from Pauli twirling.'
    elif baseline_pass and not twirl_pass:
        overall_verdict = 'MIXED'
        verdict_reason = 'Baseline passes; Pauli twirling fails (introduces overhead).'
    elif not baseline_pass and twirl_pass:
        overall_verdict = 'MIXED'
        verdict_reason = 'Baseline fails; Pauli twirling passes (mitigation helps).'
    else:
        overall_verdict = 'FAIL'
        verdict_reason = 'Both configs fail; boundary unstable on this backend/qubit pair.'
    
    print("=== Overall Verdict ===")
    print(f"VERDICT: {overall_verdict}")
    print(f"Reason: {verdict_reason}\n")
    
    # Create proofrecord
    proofrecord = {
        'experiment': 'ARK-447',
        'title': 'Noise-Suppression Comparison: Pauli Twirling vs. Baseline',
        'note': 'DD circuits omitted due to scheduling complexity',
        'backend': meta['backend'],
        'qubits': {
            'Q_A': qubits['Q_A'],
            'Q_P': qubits['Q_P'],
            'Q_A_readout_error': qubits['Q_A_readout_error'],
            'Q_P_readout_error': qubits['Q_P_readout_error'],
            'sum_readout_error': qubits['sum_readout_error']
        },
        'spam_gate': {
            'job_id': spam['job_id'],
            'SPAM_A_error': spam['SPAM_A']['error'],
            'SPAM_P_prob_1': spam['SPAM_P']['prob_1'],
            'gate_passed': spam['gate_passed']
        },
        'principal_job': {
            'job_id': meta['job_id'],
            'shots_per_circuit': meta['shots_per_circuit'],
            'num_circuits': meta['num_circuits']
        },
        'configurations': configs,
        'verdict': {
            'overall': overall_verdict,
            'reason': verdict_reason,
            'timestamp_utc': datetime.now(timezone.utc).isoformat()
        },
        'protocol': 'Field 27 (LOCK → SPAM gate → principal job → analyze → verdict)',
        'preregistration': 'ARK_447_preregistration.md (modified: DD omitted)',
        'interpretation_boundaries': [
            'Results apply to this specific backend, qubits, and calibration.',
            'Not a cryptographic security validation.',
            'Pauli twirling is noise mitigation (not correction); no QEC used.',
            'Single-round binary boundary only.',
            'DD circuits omitted due to implementation complexity.'
        ]
    }
    
    with open('proofrecord.json', 'w') as f:
        json.dump(proofrecord, f, indent=2)
    
    print(f"✅ Proofrecord saved to proofrecord.json")
    print(f"✅ ARK-447 analysis complete.")
    
    return 0 if overall_verdict.startswith('PASS') else 1

if __name__ == '__main__':
    sys.exit(main())
