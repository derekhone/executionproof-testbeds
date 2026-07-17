#!/usr/bin/env python3
"""
ARK-455 Kill-Gate Calibration
Generate 100 test pairs (50 valid, 50 tampered), verify with both V1 and V2, check concordance.
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

print("=== ARK-455 KILL-GATE CALIBRATION ===")
print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}\n")

# Generate calibration seed
calibration_seed = secrets.randbits(256)
print(f"Calibration seed: {calibration_seed}\n")

# Generate test pairs
gen = ProofRecordGenerator(seed=calibration_seed)
public_key = gen.get_public_key_hex()

print(f"Public key: {public_key}\n")
print("Generating 100 test records (50 valid, 50 tampered)...")

# 50 valid records (arm 1)
valid_records = gen.generate_arm_records(arm_id=1, count=50)

# 50 tampered records (random tampering across different fields)
tampered_records = []
for i in range(50):
    # Cycle through tampering targets (arms 2-8)
    arm_id = 2 + (i % 7)
    records = gen.generate_arm_records(arm_id=arm_id, count=1)
    tampered_records.extend(records)

all_test_records = valid_records + tampered_records

# Save to temp file for V1
test_file = '/tmp/ark455_killgate_records.json'
with open(test_file, 'w') as f:
    json.dump(all_test_records, f, indent=2)

print(f"✅ Generated 100 test records\n")

# Run V2 (Python) on all records
print("=== Running V2 (Python) ===")
v2_results = []
for i, record in enumerate(all_test_records):
    verdict = v2_verifier.verify_proof_record(record, public_key)
    v2_results.append(verdict)
    expected = "ACCEPT" if i < 50 else "REJECT"
    mark = "✅" if verdict == expected else "❌"
    if i < 5 or i == 50 or (verdict != expected):  # Print first 5, transition, and any mismatches
        print(f"  Record {i+1:3d}: {verdict:6s} (expected: {expected:6s}) {mark}")

v2_accept = v2_results[:50].count("ACCEPT")
v2_reject = v2_results[50:].count("REJECT")
print(f"\nV2 summary: {v2_accept}/50 valid accepted, {v2_reject}/50 tampered rejected")

# Run V1 (JavaScript) on all records
print("\n=== Running V1 (JavaScript) ===")
try:
    result = subprocess.run(
        ['node', '/home/ubuntu/executionproof-testbeds/ark-455/verifiers/v1_verifier.js',
         public_key, test_file],
        capture_output=True,
        text=True,
        timeout=30
    )
    
    if result.returncode != 0:
        print(f"❌ V1 execution failed:")
        print(result.stderr)
        print("\n⛔ KILL-GATE FAILED: V1 verifier error")
        sys.exit(1)
    
    v1_batch_result = json.loads(result.stdout)
    print(f"V1 summary: {v1_batch_result['accepted']}/100 accepted, {v1_batch_result['rejected']}/100 rejected")
    
    # V1 doesn't give per-record verdicts in batch mode, so we need to run individually
    print("\nRunning V1 per-record for concordance check...")
    v1_results = []
    for i, record in enumerate(all_test_records):
        single_file = f'/tmp/ark455_killgate_single_{i}.json'
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
            v1_results.append(verdict)
        else:
            print(f"❌ V1 failed on record {i+1}")
            v1_results.append("ERROR")
    
    v1_accept = v1_results[:50].count("ACCEPT")
    v1_reject = v1_results[50:].count("REJECT")
    print(f"\nV1 per-record: {v1_accept}/50 valid accepted, {v1_reject}/50 tampered rejected")
    
except Exception as e:
    print(f"❌ V1 execution exception: {e}")
    print("\n⛔ KILL-GATE FAILED: V1 verifier error")
    sys.exit(1)

# Check concordance
print("\n=== Concordance Check ===")
agreements = sum(1 for v1, v2 in zip(v1_results, v2_results) if v1 == v2)
concordance_pct = (agreements / 100) * 100

print(f"V1-V2 agreement: {agreements}/100 records ({concordance_pct:.1f}%)")
print(f"Threshold: ≥99% (≥99 agreements)")

# Check sanity (both verifiers accept all 50 valid records)
v2_sanity = v2_accept == 50
v1_sanity = v1_accept == 50

print(f"\n=== Sanity Check ===")
print(f"V2 accepts all 50 valid records: {'✅ PASS' if v2_sanity else '❌ FAIL'} ({v2_accept}/50)")
print(f"V1 accepts all 50 valid records: {'✅ PASS' if v1_sanity else '❌ FAIL'} ({v1_accept}/50)")

# Verdict
concordance_pass = concordance_pct >= 99.0
sanity_pass = v2_sanity and v1_sanity

print(f"\n=== KILL-GATE VERDICT ===")
if concordance_pass and sanity_pass:
    print("✅ KILL-GATE PASSED")
    print(f"   Concordance: {concordance_pct:.1f}% ≥ 99% ✅")
    print(f"   Sanity: Both verifiers accept all valid records ✅")
    verdict = "PASS"
else:
    print("⛔ KILL-GATE FAILED")
    if not concordance_pass:
        print(f"   Concordance: {concordance_pct:.1f}% < 99% ❌")
    if not sanity_pass:
        print(f"   Sanity: At least one verifier rejects valid records ❌")
    verdict = "FAIL"

# Save kill-gate results
killgate_results = {
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "calibration_seed": calibration_seed,
    "public_key": public_key,
    "total_records": 100,
    "valid_records": 50,
    "tampered_records": 50,
    "v1_results": {
        "valid_accepted": v1_accept,
        "tampered_rejected": v1_reject
    },
    "v2_results": {
        "valid_accepted": v2_accept,
        "tampered_rejected": v2_reject
    },
    "concordance": {
        "agreements": agreements,
        "percentage": concordance_pct,
        "threshold": 99.0,
        "pass": concordance_pass
    },
    "sanity": {
        "v1_pass": v1_sanity,
        "v2_pass": v2_sanity,
        "both_pass": sanity_pass
    },
    "verdict": verdict
}

with open('/home/ubuntu/executionproof-testbeds/ark-455/results/killgate_calibration.json', 'w') as f:
    json.dump(killgate_results, f, indent=2)

print(f"\n✅ Results saved to results/killgate_calibration.json")

sys.exit(0 if verdict == "PASS" else 1)
