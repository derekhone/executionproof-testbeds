#!/usr/bin/env python3
"""
ARK-447 Analysis and Verdict
Computes metrics for each configuration and determines overall verdict.
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
    Analyze a single configuration (baseline, DD, or twirling).
    
    Returns:
        dict with S_A, L_D_raw, L_D_corrected, Delta_B, and pass/fail status
    """
    # S_A: Probability of outcome '1' on payload qubit for ALLOW path
    # Outcome format: 'c[0]c[1]' where c[0]=Q_A, c[1]=Q_P
    # We care about c[1] (payload)
    allow_counts = raw_results[allow_arm]
    deny_counts = raw_results[deny_arm]
    
    # Extract payload outcomes (rightmost bit in bitstring)
    # '00' -> payload=0, '01' -> payload=1, '10' -> payload=0, '11' -> payload=1
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
    
    # Analyze each configuration
    configs = {}
    
    configs['baseline'] = analyze_configuration(
        'Baseline',
        'arm1_ALLOW_baseline',
        'arm2_DENY_baseline',
        raw,
        spam_p_prob
    )
    
    configs['DD'] = analyze_configuration(
        'Dynamical Decoupling',
        'arm3_ALLOW_DD',
        'arm4_DENY_DD',
        raw,
        spam_p_prob
    )
    
    configs['twirling'] = analyze_configuration(
        'Pauli Twirling',
        'arm5_ALLOW_twirl',
        'arm6_DENY_twirl',
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
    all_pass = all(cfg['verdict'] == 'PASS' for cfg in configs.values())
    baseline_pass = configs['baseline']['verdict'] == 'PASS'
    
    if all_pass:
        # Check for improvement
        dd_improvement = (configs['DD']['S_A'] > configs['baseline']['S_A'] or
                          configs['DD']['L_D_corrected'] < configs['baseline']['L_D_corrected'])
        twirl_improvement = (configs['twirling']['S_A'] > configs['baseline']['S_A'] or
                             configs['twirling']['L_D_corrected'] < configs['baseline']['L_D_corrected'])
        
        if dd_improvement or twirl_improvement:
            overall_verdict = 'PASS (strong)'
            verdict_reason = 'All configurations pass; at least one mitigation shows improvement.'
        else:
            overall_verdict = 'PASS (weak)'
            verdict_reason = 'All configurations pass; no significant improvement from mitigation.'
    elif baseline_pass:
        overall_verdict = 'MIXED'
        verdict_reason = 'Baseline passes; one or both mitigation techniques fail.'
    else:
        overall_verdict = 'FAIL'
        verdict_reason = 'Baseline fails; boundary unstable on this backend/qubit pair.'
    
    print("=== Overall Verdict ===")
    print(f"VERDICT: {overall_verdict}")
    print(f"Reason: {verdict_reason}\n")
    
    # Create proofrecord
    proofrecord = {
        'experiment': 'ARK-447',
        'title': 'Noise-Suppression Comparison: Dynamical Decoupling and Pauli Twirling',
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
        'preregistration': 'ARK_447_preregistration.md',
        'interpretation_boundaries': [
            'Results apply to this specific backend, qubits, and calibration.',
            'Not a cryptographic security validation.',
            'DD and twirling are noise mitigation (not correction); no QEC used.',
            'Single-round binary boundary only; not multi-round or complex policies.'
        ]
    }
    
    with open('proofrecord.json', 'w') as f:
        json.dump(proofrecord, f, indent=2)
    
    print(f"✅ Proofrecord saved to proofrecord.json")
    print(f"✅ ARK-447 analysis complete.")
    print(f"\nNext steps:")
    print(f"   1. Review results and verdict")
    print(f"   2. Generate RESULTS.md documentation")
    print(f"   3. Update RUN_LOG.md")
    print(f"   4. Commit, tag, and push")
    
    return 0 if overall_verdict.startswith('PASS') else 1

if __name__ == '__main__':
    sys.exit(main())
