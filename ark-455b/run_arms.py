#!/usr/bin/env python3
"""
ARK-455b Arm Execution

Execute all 9 arms (100 records each) with recorded seeds, verifying each record
with both V1 (JavaScript) and V2 (Python) under the two-gate procedure
(signature + validity window).

Arms:
  1  ACCEPT-original                    (control; valid, in-window)
  2  REJECT-decision                    (post-signing tamper)
  3  REJECT-timestamp-postsign          (post-signing tamper, CORRECTED: real +1s)
  4  REJECT-payload_hash                (post-signing tamper)
  5  REJECT-evidence_refs               (post-signing tamper)
  6  REJECT-actor                       (post-signing tamper)
  7  REJECT-outcome                     (post-signing tamper)
  8  REJECT-review_path                 (post-signing tamper)
  9  REJECT-timestamp-presign-expired   (pre-signing: valid signature, expired)

Success criteria (per PREREGISTRATION.md Section 6):
  C1  V_accept_original >= 0.95      (Arm 1, worst of V1/V2)
  C2  V_reject_min       >= 0.95     (min over arms 2-9, worst of V1/V2)
  C3  V_margin           >= 0.85     (V_reject_min - (1 - V_accept_original))
Plus a mutation-effectiveness gate: every REJECT arm must have 100% effective
mutations, else the run ABORTS (no-op guard).

All paths resolved relative to this file.
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

print("=== ARK-455b ARM EXECUTION ===")
run_start_time = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
print(f"Run start: {run_start_time}")
print(f"Validity TTL: {TTL}s")
print("Note: verification_time is captured per arm, AFTER that arm's records are "
      "generated (auditor verifies issued records).\n")

# Load kill-gate results
with open(os.path.join(RESULTS_DIR, 'killgate_calibration.json'), 'r') as f:
    killgate = json.load(f)
if killgate['verdict'] != "PASS":
    print("⛔ Kill-gate did not pass. Aborting arm execution per preregistration.")
    sys.exit(1)
print(f"✅ Kill-gate passed ({killgate['concordance']['percentage']:.1f}% concordance)\n")

ARM_LABELS = ProofRecordGenerator.ARMS

all_results = {}

for arm_id in range(1, 10):
    spec = ARM_LABELS[arm_id]
    label = spec['label']
    print(f"=== ARM {arm_id}: {label} ===")

    arm_seed = secrets.randbits(256)
    print(f"Seed: {arm_seed}")

    gen = ProofRecordGenerator(seed=arm_seed)
    public_key = gen.get_public_key_hex()
    records, audit = gen.generate_arm_records(arm_id=arm_id, count=100)
    print(f"Generated 100 records (mode: {spec['mode'] or 'control'})")

    # Mutation-effectiveness gate for REJECT arms (2-9)
    mutation_effective_count = None
    if arm_id > 1:
        mutation_effective_count = sum(1 for a in audit if a.get("mutation_effective") is True)
        if mutation_effective_count != 100:
            print(f"❌ Only {mutation_effective_count}/100 records had an effective mutation.")
            print("⛔ ABORTING per preregistration: ineffective tamper (no-op guard).")
            sys.exit(1)
        print(f"Mutation-effectiveness: {mutation_effective_count}/100 ✅")

    arm_file = f'/tmp/ark455b_arm{arm_id}_records.json'
    with open(arm_file, 'w') as f:
        json.dump(records, f, indent=2)

    # Capture verification_time AFTER this arm's records are generated.
    verification_time = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')

    # V2 (Python)
    print("Running V2 (Python)...", end=" ")
    v2_verdicts = [v2_verifier.verify_proof_record(r, public_key, verification_time, TTL)
                   for r in records]
    v2_accept = v2_verdicts.count("ACCEPT")
    v2_reject = v2_verdicts.count("REJECT")
    print(f"{v2_accept} ACCEPT, {v2_reject} REJECT")

    # V1 (JavaScript), per-record
    print("Running V1 (JavaScript)...", end=" ")
    v1_verdicts = []
    for i, record in enumerate(records):
        single_file = f'/tmp/ark455b_arm{arm_id}_single_{i}.json'
        with open(single_file, 'w') as f:
            json.dump(record, f)
        result = subprocess.run(
            ['node', V1_PATH, public_key, single_file, verification_time, str(TTL)],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            single_result = json.loads(result.stdout)
            v1_verdicts.append("ACCEPT" if single_result['accepted'] == 1 else "REJECT")
        else:
            print(f"\n❌ V1 failed on record {i+1}: {result.stderr}")
            v1_verdicts.append("ERROR")
    v1_accept = v1_verdicts.count("ACCEPT")
    v1_reject = v1_verdicts.count("REJECT")
    print(f"{v1_accept} ACCEPT, {v1_reject} REJECT")

    agreements = sum(1 for v1, v2 in zip(v1_verdicts, v2_verdicts) if v1 == v2)
    concordance = agreements / 100
    print(f"V1-V2 concordance: {agreements}/100 ({concordance*100:.1f}%)\n")

    arm_results = {
        "arm_id": arm_id,
        "label": label,
        "mode": spec['mode'],
        "target": spec['target'],
        "seed": arm_seed,
        "public_key": public_key,
        "total_records": 100,
        "verification_time": verification_time,
        "ttl_seconds": TTL,
        "mutation_effective_count": mutation_effective_count,
        "v1": {
            "accepted": v1_accept, "rejected": v1_reject,
            "rate_accept": v1_accept / 100, "rate_reject": v1_reject / 100
        },
        "v2": {
            "accepted": v2_accept, "rejected": v2_reject,
            "rate_accept": v2_accept / 100, "rate_reject": v2_reject / 100
        },
        "concordance": {"agreements": agreements, "percentage": concordance * 100}
    }
    all_results[f"arm_{arm_id}"] = arm_results
    with open(os.path.join(RESULTS_DIR, f'arm_{arm_id}_results.json'), 'w') as f:
        json.dump(arm_results, f, indent=2)

# --- Overall metrics ---
print("=== OVERALL METRICS ===\n")

v_accept_v1 = all_results['arm_1']['v1']['rate_accept']
v_accept_v2 = all_results['arm_1']['v2']['rate_accept']
v_accept_original = min(v_accept_v1, v_accept_v2)
print(f"C1 — V_accept_original (Arm 1): V1={v_accept_v1:.4f}, V2={v_accept_v2:.4f}, "
      f"worst={v_accept_original:.4f} (>=0.95) {'✅' if v_accept_original >= 0.95 else '❌'}\n")

v_reject_per_arm = []
print("C2 — V_reject per arm (Arms 2-9):")
for arm_id in range(2, 10):
    ak = f"arm_{arm_id}"
    vr1 = all_results[ak]['v1']['rate_reject']
    vr2 = all_results[ak]['v2']['rate_reject']
    worst = min(vr1, vr2)
    v_reject_per_arm.append(worst)
    label = ARM_LABELS[arm_id]['label']
    mark = "✅" if worst >= 0.95 else "❌"
    print(f"  Arm {arm_id} ({label:32s}): V1={vr1:.4f}, V2={vr2:.4f}, worst={worst:.4f} {mark}")

v_reject_min = min(v_reject_per_arm)
print(f"\n  V_reject_min: {v_reject_min:.4f} (>=0.95) {'✅' if v_reject_min >= 0.95 else '❌'}\n")

v_margin = v_reject_min - (1 - v_accept_original)
print(f"C3 — V_margin = {v_reject_min:.4f} - {(1 - v_accept_original):.4f} = "
      f"{v_margin:.4f} (>=0.85) {'✅' if v_margin >= 0.85 else '❌'}\n")

c1_pass = v_accept_original >= 0.95
c2_pass = v_reject_min >= 0.95
c3_pass = v_margin >= 0.85

# Overall concordance across all 9 arms
total_agreements = sum(all_results[f"arm_{i}"]['concordance']['agreements'] for i in range(1, 10))
overall_concordance = total_agreements / 900

print("=== VERDICT ===")
verdict = "PASS" if (c1_pass and c2_pass and c3_pass) else "FAIL"
print("✅ PASS" if verdict == "PASS" else "❌ FAIL")
print(f"  C1 (V_accept_original >= 0.95): {'✅ PASS' if c1_pass else '❌ FAIL'}")
print(f"  C2 (V_reject_min >= 0.95):      {'✅ PASS' if c2_pass else '❌ FAIL'}")
print(f"  C3 (V_margin >= 0.85):          {'✅ PASS' if c3_pass else '❌ FAIL'}")
print(f"  Overall V1-V2 concordance: {overall_concordance*100:.2f}% ({total_agreements}/900)")

overall_results = {
    "run_start_time": run_start_time,
    "run_end_time": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
    "ttl_seconds": TTL,
    "killgate_verdict": killgate['verdict'],
    "arms_executed": list(range(1, 10)),
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
    "overall_concordance": {
        "agreements": total_agreements, "total": 900,
        "percentage": overall_concordance * 100
    },
    "verdict": verdict,
    "per_arm_summary": {
        f"arm_{i}": {
            "label": all_results[f"arm_{i}"]['label'],
            "mode": all_results[f"arm_{i}"]['mode'],
            "v_reject_worst": (min(all_results[f"arm_{i}"]['v1']['rate_reject'],
                                   all_results[f"arm_{i}"]['v2']['rate_reject'])
                               if i > 1 else None),
            "v_accept_worst": (min(all_results[f"arm_{i}"]['v1']['rate_accept'],
                                   all_results[f"arm_{i}"]['v2']['rate_accept'])
                               if i == 1 else None)
        }
        for i in range(1, 10)
    }
}
with open(os.path.join(RESULTS_DIR, 'overall_results.json'), 'w') as f:
    json.dump(overall_results, f, indent=2)
print(f"\n✅ Results saved to results/overall_results.json")
sys.exit(0 if verdict == "PASS" else 1)
