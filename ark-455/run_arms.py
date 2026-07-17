#!/usr/bin/env python3
"""
ARK-455 Arm Execution
Execute all 8 arms (100 records each) with recorded seeds.
"""

import json
import subprocess
import sys
import secrets
from datetime import datetime, timezone

sys.path.insert(0, '/home/ubuntu/executionproof-testbeds/ark-455/generator')
sys.path.insert(0, '/home/ubuntu/executionproof-testbeds/ark-455/verifiers')

from record_generator import ProofRecordGenerator
import v2_verifier

print("=== ARK-455 ARM EXECUTION ===")
print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}\n")

# Load kill-gate results
with open('/home/ubuntu/executionproof-testbeds/ark-455/results/killgate_calibration.json', 'r') as f:
    killgate = json.load(f)

if killgate['verdict'] != "PASS":
    print("⛔ Kill-gate did not pass. Aborting arm execution per preregistration.")
    sys.exit(1)

print(f"✅ Kill-gate passed ({killgate['concordance']['percentage']:.1f}% concordance)\n")

# Arm specifications
arms = {
    1: {"label": "ACCEPT-original", "tampering_target": None},
    2: {"label": "REJECT-decision", "tampering_target": "decision"},
    3: {"label": "REJECT-timestamp", "tampering_target": "timestamp"},
    4: {"label": "REJECT-payload_hash", "tampering_target": "payload_hash"},
    5: {"label": "REJECT-evidence_refs", "tampering_target": "evidence_references"},
    6: {"label": "REJECT-actor", "tampering_target": "actor"},
    7: {"label": "REJECT-outcome", "tampering_target": "execution_outcome"},
    8: {"label": "REJECT-review_path", "tampering_target": "review_path"}
}

all_results = {}

for arm_id in range(1, 9):
    arm_info = arms[arm_id]
    print(f"=== ARM {arm_id}: {arm_info['label']} ===")
    
    # Generate seed for this arm
    arm_seed = secrets.randbits(256)
    print(f"Seed: {arm_seed}")
    
    # Generate records
    gen = ProofRecordGenerator(seed=arm_seed)
    public_key = gen.get_public_key_hex()
    records = gen.generate_arm_records(arm_id=arm_id, count=100)
    
    print(f"Generated 100 records (tampering: {arm_info['tampering_target'] or 'none'})")
    
    # Save records for V1
    arm_file = f'/tmp/ark455_arm{arm_id}_records.json'
    with open(arm_file, 'w') as f:
        json.dump(records, f, indent=2)
    
    # Run V2 (Python)
    print("Running V2 (Python)...", end=" ")
    v2_verdicts = []
    for record in records:
        verdict = v2_verifier.verify_proof_record(record, public_key)
        v2_verdicts.append(verdict)
    
    v2_accept = v2_verdicts.count("ACCEPT")
    v2_reject = v2_verdicts.count("REJECT")
    v2_rate_accept = v2_accept / 100
    v2_rate_reject = v2_reject / 100
    print(f"{v2_accept} ACCEPT, {v2_reject} REJECT (rate: {v2_rate_accept:.2f} / {v2_rate_reject:.2f})")
    
    # Run V1 (JavaScript)
    print("Running V1 (JavaScript)...", end=" ")
    try:
        # Run V1 per-record for detailed results
        v1_verdicts = []
        for i, record in enumerate(records):
            single_file = f'/tmp/ark455_arm{arm_id}_single_{i}.json'
            with open(single_file, 'w') as f:
                json.dump(record, f)
            
            result = subprocess.run(
                ['node', '/home/ubuntu/executionproof-testbeds/ark-455/verifiers/v1_verifier.js',
                 public_key, single_file],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                single_result = json.loads(result.stdout)
                verdict = "ACCEPT" if single_result['accepted'] == 1 else "REJECT"
                v1_verdicts.append(verdict)
            else:
                print(f"\n❌ V1 failed on record {i+1}")
                v1_verdicts.append("ERROR")
        
        v1_accept = v1_verdicts.count("ACCEPT")
        v1_reject = v1_verdicts.count("REJECT")
        v1_rate_accept = v1_accept / 100
        v1_rate_reject = v1_reject / 100
        print(f"{v1_accept} ACCEPT, {v1_reject} REJECT (rate: {v1_rate_accept:.2f} / {v1_rate_reject:.2f})")
        
    except Exception as e:
        print(f"\n❌ V1 execution error: {e}")
        v1_accept = v1_reject = 0
        v1_rate_accept = v1_rate_reject = 0.0
        v1_verdicts = ["ERROR"] * 100
    
    # Check concordance for this arm
    agreements = sum(1 for v1, v2 in zip(v1_verdicts, v2_verdicts) if v1 == v2)
    concordance = agreements / 100
    print(f"V1-V2 concordance: {agreements}/100 ({concordance*100:.1f}%)")
    
    # Save arm results
    arm_results = {
        "arm_id": arm_id,
        "label": arm_info['label'],
        "tampering_target": arm_info['tampering_target'],
        "seed": arm_seed,
        "public_key": public_key,
        "total_records": 100,
        "v1": {
            "accepted": v1_accept,
            "rejected": v1_reject,
            "rate_accept": v1_rate_accept,
            "rate_reject": v1_rate_reject
        },
        "v2": {
            "accepted": v2_accept,
            "rejected": v2_reject,
            "rate_accept": v2_rate_accept,
            "rate_reject": v2_rate_reject
        },
        "concordance": {
            "agreements": agreements,
            "percentage": concordance * 100
        }
    }
    
    all_results[f"arm_{arm_id}"] = arm_results
    
    with open(f'/home/ubuntu/executionproof-testbeds/ark-455/results/arm_{arm_id}_results.json', 'w') as f:
        json.dump(arm_results, f, indent=2)
    
    print()

# Compute overall metrics
print("=== OVERALL METRICS ===\n")

# C1: V_accept_original (Arm 1, worst case between V1 and V2)
v_accept_v1_arm1 = all_results['arm_1']['v1']['rate_accept']
v_accept_v2_arm1 = all_results['arm_1']['v2']['rate_accept']
v_accept_original = min(v_accept_v1_arm1, v_accept_v2_arm1)
print(f"C1 — V_accept_original (Arm 1):")
print(f"  V1: {v_accept_v1_arm1:.4f}")
print(f"  V2: {v_accept_v2_arm1:.4f}")
print(f"  Worst case: {v_accept_original:.4f} (threshold: ≥0.95) {'✅' if v_accept_original >= 0.95 else '❌'}\n")

# C2: V_reject_min (Arms 2-8, minimum rejection rate across all tampering targets, worst case between V1 and V2)
v_reject_per_arm = []
print("C2 — V_reject per tampering target (Arms 2-8):")
for arm_id in range(2, 9):
    arm_key = f"arm_{arm_id}"
    v_reject_v1 = all_results[arm_key]['v1']['rate_reject']
    v_reject_v2 = all_results[arm_key]['v2']['rate_reject']
    v_reject_arm = min(v_reject_v1, v_reject_v2)
    v_reject_per_arm.append(v_reject_arm)
    label = arms[arm_id]['label']
    target = arms[arm_id]['tampering_target']
    mark = "✅" if v_reject_arm >= 0.95 else "❌"
    print(f"  Arm {arm_id} ({target:20s}): V1={v_reject_v1:.4f}, V2={v_reject_v2:.4f}, worst={v_reject_arm:.4f} {mark}")

v_reject_min = min(v_reject_per_arm)
print(f"\n  V_reject_min: {v_reject_min:.4f} (threshold: ≥0.95) {'✅' if v_reject_min >= 0.95 else '❌'}\n")

# C3: V_margin
v_margin = v_reject_min - (1 - v_accept_original)
print(f"C3 — V_margin:")
print(f"  V_reject_min - (1 - V_accept_original)")
print(f"  = {v_reject_min:.4f} - {(1 - v_accept_original):.4f}")
print(f"  = {v_margin:.4f} (threshold: ≥0.85) {'✅' if v_margin >= 0.85 else '❌'}\n")

# Determine verdict
c1_pass = v_accept_original >= 0.95
c2_pass = v_reject_min >= 0.95
c3_pass = v_margin >= 0.85

print("=== VERDICT ===")
if c1_pass and c2_pass and c3_pass:
    verdict = "PASS"
    print("✅ PASS")
else:
    verdict = "FAIL"
    print("❌ FAIL")

print(f"  C1 (V_accept_original ≥ 0.95): {'✅ PASS' if c1_pass else '❌ FAIL'}")
print(f"  C2 (V_reject_min ≥ 0.95):      {'✅ PASS' if c2_pass else '❌ FAIL'}")
print(f"  C3 (V_margin ≥ 0.85):          {'✅ PASS' if c3_pass else '❌ FAIL'}")

# Save overall results
overall_results = {
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "killgate_verdict": killgate['verdict'],
    "arms_executed": list(range(1, 9)),
    "primary_metrics": {
        "v_accept_original": v_accept_original,
        "v_reject_min": v_reject_min,
        "v_margin": v_margin
    },
    "criteria": {
        "c1_v_accept_pass": c1_pass,
        "c2_v_reject_pass": c2_pass,
        "c3_v_margin_pass": c3_pass
    },
    "verdict": verdict,
    "per_arm_summary": {
        f"arm_{i}": {
            "label": all_results[f"arm_{i}"]['label'],
            "v_reject_worst": min(all_results[f"arm_{i}"]['v1']['rate_reject'], 
                                   all_results[f"arm_{i}"]['v2']['rate_reject']) if i > 1 else None
        }
        for i in range(1, 9)
    }
}

with open('/home/ubuntu/executionproof-testbeds/ark-455/results/overall_results.json', 'w') as f:
    json.dump(overall_results, f, indent=2)

print(f"\n✅ Results saved to results/overall_results.json")
