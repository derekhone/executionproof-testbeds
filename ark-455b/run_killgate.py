#!/usr/bin/env python3
"""
ARK-455b Kill-Gate Calibration

Generate 100 test records (50 valid, 50 tampered across arms 2-9), verify with
both V1 (JavaScript) and V2 (Python), and check:
  - V1-V2 concordance >= 99%
  - Sanity: both verifiers accept all 50 valid records
  - Mutation-effectiveness: every tampered record has an effective mutation
    (post-signing byte change, or pre-signing out-of-window timestamp). This gate
    is the ARK-455b safeguard against a no-op tamper masquerading as a detection
    failure (the ARK-455 v1.0 Arm-3 defect; see ../ark-455/CORRECTION.md).

All paths are resolved relative to this file so the testbed is portable.
"""

import json
import os
import subprocess
import sys
import secrets
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
GEN_DIR = os.path.join(HERE, 'generator')
VER_DIR = os.path.join(HERE, 'verifiers')
RESULTS_DIR = os.path.join(HERE, 'results')

sys.path.insert(0, GEN_DIR)
sys.path.insert(0, VER_DIR)

from record_generator import ProofRecordGenerator, VALIDITY_TTL_SECONDS
import v2_verifier

V1_PATH = os.path.join(VER_DIR, 'v1_verifier.js')
TTL = VALIDITY_TTL_SECONDS

print("=== ARK-455b KILL-GATE CALIBRATION ===")
start_time = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
print(f"Start timestamp: {start_time}")
print(f"Validity TTL: {TTL}s")
print("Note: verification_time is captured AFTER record generation, modelling an "
      "auditor who verifies a record once it has been issued.\n")

calibration_seed = secrets.randbits(256)
print(f"Calibration seed: {calibration_seed}\n")

gen = ProofRecordGenerator(seed=calibration_seed)
public_key = gen.get_public_key_hex()
print(f"Public key: {public_key}\n")
print("Generating 100 test records (50 valid, 50 tampered across arms 2-9)...")

# 50 valid records (arm 1)
valid_records, valid_audit = gen.generate_arm_records(arm_id=1, count=50)

# 50 tampered records cycling through arms 2-9 (8 tamper arms)
tampered_records = []
tampered_audit = []
for i in range(50):
    arm_id = 2 + (i % 8)  # arms 2..9
    recs, aud = gen.generate_arm_records(arm_id=arm_id, count=1)
    tampered_records.extend(recs)
    tampered_audit.extend(aud)

all_test_records = valid_records + tampered_records

# --- Mutation-effectiveness gate (tampered records only) ---
ineffective = [i for i, a in enumerate(tampered_audit)
               if a.get("mutation_effective") is not True]
print(f"\n=== Mutation-Effectiveness Gate ===")
print(f"Tampered records with effective mutation: "
      f"{len(tampered_audit) - len(ineffective)}/{len(tampered_audit)}")
if ineffective:
    print(f"❌ {len(ineffective)} tampered record(s) had an INEFFECTIVE mutation "
          f"(indices {ineffective[:10]}...).")
    print("⛔ KILL-GATE FAILED: ineffective tamper detected (no-op guard).")
    sys.exit(1)
print("✅ All tampered records carry an effective mutation.")

test_file = '/tmp/ark455b_killgate_records.json'
with open(test_file, 'w') as f:
    json.dump(all_test_records, f, indent=2)
print(f"\n✅ Generated 100 test records\n")

# Capture verification_time AFTER generation: an auditor verifies records once
# they exist. This keeps valid (Arm-1) records strictly in-window and expired
# (Arm-9) records out-of-window.
verification_time = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
print(f"verification_time: {verification_time}\n")

# --- V2 (Python) ---
print("=== Running V2 (Python) ===")
v2_results = []
for i, record in enumerate(all_test_records):
    verdict = v2_verifier.verify_proof_record(record, public_key, verification_time, TTL)
    v2_results.append(verdict)
    expected = "ACCEPT" if i < 50 else "REJECT"
    if i < 3 or i == 50 or verdict != expected:
        mark = "✅" if verdict == expected else "❌"
        print(f"  Record {i+1:3d}: {verdict:6s} (expected: {expected:6s}) {mark}")

v2_accept = v2_results[:50].count("ACCEPT")
v2_reject = v2_results[50:].count("REJECT")
print(f"\nV2 summary: {v2_accept}/50 valid accepted, {v2_reject}/50 tampered rejected")

# --- V1 (JavaScript), per-record for concordance ---
print("\n=== Running V1 (JavaScript) per-record ===")
v1_results = []
for i, record in enumerate(all_test_records):
    single_file = f'/tmp/ark455b_killgate_single_{i}.json'
    with open(single_file, 'w') as f:
        json.dump(record, f)
    result = subprocess.run(
        ['node', V1_PATH, public_key, single_file, verification_time, str(TTL)],
        capture_output=True, text=True, timeout=10
    )
    if result.returncode == 0:
        single_result = json.loads(result.stdout)
        verdict = "ACCEPT" if single_result['accepted'] == 1 else "REJECT"
        v1_results.append(verdict)
    else:
        print(f"❌ V1 failed on record {i+1}: {result.stderr}")
        v1_results.append("ERROR")

v1_accept = v1_results[:50].count("ACCEPT")
v1_reject = v1_results[50:].count("REJECT")
print(f"V1 per-record: {v1_accept}/50 valid accepted, {v1_reject}/50 tampered rejected")

# --- Concordance ---
print("\n=== Concordance Check ===")
agreements = sum(1 for v1, v2 in zip(v1_results, v2_results) if v1 == v2)
concordance_pct = (agreements / 100) * 100
print(f"V1-V2 agreement: {agreements}/100 records ({concordance_pct:.1f}%)")
print(f"Threshold: >=99%")

# --- Sanity ---
v2_sanity = v2_accept == 50
v1_sanity = v1_accept == 50
print(f"\n=== Sanity Check ===")
print(f"V2 accepts all 50 valid records: {'✅ PASS' if v2_sanity else '❌ FAIL'} ({v2_accept}/50)")
print(f"V1 accepts all 50 valid records: {'✅ PASS' if v1_sanity else '❌ FAIL'} ({v1_accept}/50)")

concordance_pass = concordance_pct >= 99.0
sanity_pass = v2_sanity and v1_sanity

print(f"\n=== KILL-GATE VERDICT ===")
if concordance_pass and sanity_pass:
    print("✅ KILL-GATE PASSED")
    verdict = "PASS"
else:
    print("⛔ KILL-GATE FAILED")
    if not concordance_pass:
        print(f"   Concordance: {concordance_pct:.1f}% < 99% ❌")
    if not sanity_pass:
        print(f"   Sanity: at least one verifier rejects valid records ❌")
    verdict = "FAIL"

os.makedirs(RESULTS_DIR, exist_ok=True)
killgate_results = {
    "start_time": start_time,
    "verification_time": verification_time,
    "ttl_seconds": TTL,
    "calibration_seed": calibration_seed,
    "public_key": public_key,
    "total_records": 100,
    "valid_records": 50,
    "tampered_records": 50,
    "mutation_effectiveness": {
        "tampered_total": len(tampered_audit),
        "effective": len(tampered_audit) - len(ineffective),
        "ineffective": len(ineffective),
        "pass": len(ineffective) == 0
    },
    "v1_results": {"valid_accepted": v1_accept, "tampered_rejected": v1_reject},
    "v2_results": {"valid_accepted": v2_accept, "tampered_rejected": v2_reject},
    "concordance": {
        "agreements": agreements,
        "percentage": concordance_pct,
        "threshold": 99.0,
        "pass": concordance_pass
    },
    "sanity": {"v1_pass": v1_sanity, "v2_pass": v2_sanity, "both_pass": sanity_pass},
    "verdict": verdict
}
with open(os.path.join(RESULTS_DIR, 'killgate_calibration.json'), 'w') as f:
    json.dump(killgate_results, f, indent=2)
print(f"\n✅ Results saved to results/killgate_calibration.json")
sys.exit(0 if verdict == "PASS" else 1)
