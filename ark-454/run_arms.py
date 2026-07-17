#!/usr/bin/env python3
"""
ARK-454 Arm Execution

Execute all 8 arms (100 scenarios each) with recorded seeds, evaluating each
scenario with both guards V1 (JavaScript) and V2 (Python).

Arms:
  1  LEGITIMATE-independent           (control; genuine independent approval) -> ALLOW
  2  DIRECT-self-approval             approver == requester                   -> DENY
  3  SOCKPUPPET-controlled-identity   controller_of(approver) == requester    -> DENY
  4  DELEGATION-to-self               requester in delegation_chain           -> DENY
  5  CIRCULAR-delegation              duplicate principal in chain            -> DENY
  6  SHARED-CONTROLLER-collusion      requester & approver share a 3rd-party  -> DENY
  7  INHERITED-parent-workflow-self   authority from requester's own workflow -> DENY
  8  AMBIGUOUS-independence           controller_of(approver) == "UNKNOWN"    -> HOLD

Success criteria (per PREREGISTRATION.md Section 6), worst of V1/V2 at each point:
  C1  G_allow_legit    >= 0.95   (Arm 1 ALLOW rate)
  C2  G_failclosed_min >= 0.95   (min over Arms 2-8 of verdict != ALLOW rate)
  C3  G_margin         >= 0.85   (G_failclosed_min - (1 - G_allow_legit))
Plus an attack-effectiveness gate: every attack arm must be 100% effective and the
control arm 100% clean, else the run ABORTS.

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

from scenario_generator import ScenarioGenerator
import v2_guard

V1_PATH = os.path.join(VER_DIR, 'v1_guard.js')


def run_v1_batch(scenarios, tag):
    tmp = f'/tmp/ark454_v1_arm_{tag}.json'
    with open(tmp, 'w') as f:
        json.dump(scenarios, f)
    result = subprocess.run(['node', V1_PATH, tmp], capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        raise RuntimeError(f"V1 failed on arm {tag}: {result.stderr}")
    return json.loads(result.stdout)["verdicts"]


print("=== ARK-454 ARM EXECUTION ===")
run_start_time = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
print(f"Run start: {run_start_time}\n")

with open(os.path.join(RESULTS_DIR, 'killgate_calibration.json'), 'r') as f:
    killgate = json.load(f)
if killgate['verdict'] != "PASS":
    print("⛔ Kill-gate did not pass. Aborting arm execution per preregistration.")
    sys.exit(1)
print(f"✅ Kill-gate passed ({killgate['concordance']['percentage']:.1f}% concordance)\n")

ARM_SPECS = ScenarioGenerator.ARMS
all_results = {}

for arm_id in range(1, 9):
    spec = ARM_SPECS[arm_id]
    label = spec['label']
    print(f"=== ARM {arm_id}: {label} ===")

    arm_seed = secrets.randbits(256)
    print(f"Seed: {arm_seed}")

    gen = ScenarioGenerator(seed=arm_seed)
    scenarios, audit = gen.generate_arm_scenarios(arm_id=arm_id, count=100)
    print(f"Generated 100 scenarios")

    # Attack-effectiveness gate
    if arm_id == 1:
        clean_count = sum(1 for a in audit if a.get("clean") is True)
        if clean_count != 100:
            print(f"❌ Only {clean_count}/100 control scenarios genuinely clean.")
            print("⛔ ABORTING per preregistration: control arm carries a hidden violation.")
            sys.exit(1)
        print(f"Control-cleanliness: {clean_count}/100 ✅")
        effective_count = None
    else:
        effective_count = sum(1 for a in audit if a.get("attack_effective") is True)
        if effective_count != 100:
            print(f"❌ Only {effective_count}/100 scenarios carried an effective attack.")
            print("⛔ ABORTING per preregistration: ineffective attack (no-op guard).")
            sys.exit(1)
        print(f"Attack-effectiveness: {effective_count}/100 ✅")

    # V2 (Python)
    print("Running V2 (Python)...", end=" ")
    v2_verdicts = [v2_guard.evaluate(s) for s in scenarios]
    v2_allow = v2_verdicts.count("ALLOW")
    v2_hold = v2_verdicts.count("HOLD")
    v2_deny = v2_verdicts.count("DENY")
    print(f"{v2_allow} ALLOW / {v2_hold} HOLD / {v2_deny} DENY")

    # V1 (JavaScript)
    print("Running V1 (JavaScript)...", end=" ")
    v1_verdicts = run_v1_batch(scenarios, arm_id)
    v1_allow = v1_verdicts.count("ALLOW")
    v1_hold = v1_verdicts.count("HOLD")
    v1_deny = v1_verdicts.count("DENY")
    print(f"{v1_allow} ALLOW / {v1_hold} HOLD / {v1_deny} DENY")

    agreements = sum(1 for a, b in zip(v1_verdicts, v2_verdicts) if a == b)
    concordance = agreements / 100
    print(f"V1-V2 concordance: {agreements}/100 ({concordance*100:.1f}%)\n")

    # rates
    def rates(verdicts):
        n = len(verdicts)
        allow = verdicts.count("ALLOW")
        failclosed = n - allow
        deny = verdicts.count("DENY")
        hold = verdicts.count("HOLD")
        return {
            "allow": allow, "hold": hold, "deny": deny,
            "rate_allow": allow / n, "rate_failclosed": failclosed / n,
            "rate_deny": deny / n, "rate_hold": hold / n,
        }

    arm_results = {
        "arm_id": arm_id,
        "label": label,
        "violation": spec['violation'],
        "seed": arm_seed,
        "total_scenarios": 100,
        "attack_effective_count": effective_count,
        "v1": rates(v1_verdicts),
        "v2": rates(v2_verdicts),
        "concordance": {"agreements": agreements, "percentage": concordance * 100},
    }
    all_results[f"arm_{arm_id}"] = arm_results
    with open(os.path.join(RESULTS_DIR, f'arm_{arm_id}_results.json'), 'w') as f:
        json.dump(arm_results, f, indent=2)

# --- Overall metrics ---
print("=== OVERALL METRICS ===\n")

g_allow_v1 = all_results['arm_1']['v1']['rate_allow']
g_allow_v2 = all_results['arm_1']['v2']['rate_allow']
g_allow_legit = min(g_allow_v1, g_allow_v2)
print(f"C1 — G_allow_legit (Arm 1): V1={g_allow_v1:.4f}, V2={g_allow_v2:.4f}, "
      f"worst={g_allow_legit:.4f} (>=0.95) {'✅' if g_allow_legit >= 0.95 else '❌'}\n")

failclosed_per_arm = []
print("C2 — fail-closed rate per arm (Arms 2-8):")
for arm_id in range(2, 9):
    ak = f"arm_{arm_id}"
    fc1 = all_results[ak]['v1']['rate_failclosed']
    fc2 = all_results[ak]['v2']['rate_failclosed']
    worst = min(fc1, fc2)
    failclosed_per_arm.append(worst)
    label = ARM_SPECS[arm_id]['label']
    mark = "✅" if worst >= 0.95 else "❌"
    print(f"  Arm {arm_id} ({label:32s}): V1={fc1:.4f}, V2={fc2:.4f}, worst={worst:.4f} {mark}")

g_failclosed_min = min(failclosed_per_arm)
print(f"\n  G_failclosed_min: {g_failclosed_min:.4f} (>=0.95) "
      f"{'✅' if g_failclosed_min >= 0.95 else '❌'}\n")

g_margin = g_failclosed_min - (1 - g_allow_legit)
print(f"C3 — G_margin = {g_failclosed_min:.4f} - {(1 - g_allow_legit):.4f} = "
      f"{g_margin:.4f} (>=0.85) {'✅' if g_margin >= 0.85 else '❌'}\n")

# Secondary: DENY-specificity on genuine-violation arms 2-7; HOLD on arm 8
print("Secondary (H2c/H2d): DENY on arms 2-7, HOLD on arm 8 (worst of V1/V2):")
deny_specific = []
for arm_id in range(2, 8):
    ak = f"arm_{arm_id}"
    d = min(all_results[ak]['v1']['rate_deny'], all_results[ak]['v2']['rate_deny'])
    deny_specific.append(d)
    print(f"  Arm {arm_id} DENY rate (worst): {d:.4f}")
hold8 = min(all_results['arm_8']['v1']['rate_hold'], all_results['arm_8']['v2']['rate_hold'])
print(f"  Arm 8 HOLD rate (worst): {hold8:.4f}\n")

c1_pass = g_allow_legit >= 0.95
c2_pass = g_failclosed_min >= 0.95
c3_pass = g_margin >= 0.85

total_agreements = sum(all_results[f"arm_{i}"]['concordance']['agreements'] for i in range(1, 9))
overall_concordance = total_agreements / 800

print("=== VERDICT ===")
verdict = "PASS" if (c1_pass and c2_pass and c3_pass) else "FAIL"
print("✅ PASS" if verdict == "PASS" else "❌ FAIL")
print(f"  C1 (G_allow_legit >= 0.95):    {'✅ PASS' if c1_pass else '❌ FAIL'}")
print(f"  C2 (G_failclosed_min >= 0.95): {'✅ PASS' if c2_pass else '❌ FAIL'}")
print(f"  C3 (G_margin >= 0.85):         {'✅ PASS' if c3_pass else '❌ FAIL'}")
print(f"  Overall V1-V2 concordance: {overall_concordance*100:.2f}% ({total_agreements}/800)")

overall_results = {
    "run_start_time": run_start_time,
    "run_end_time": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
    "killgate_verdict": killgate['verdict'],
    "arms_executed": list(range(1, 9)),
    "primary_metrics": {
        "g_allow_legit": g_allow_legit,
        "g_failclosed_min": g_failclosed_min,
        "g_margin": g_margin,
    },
    "criteria": {
        "c1_g_allow_pass": c1_pass,
        "c2_g_failclosed_pass": c2_pass,
        "c3_g_margin_pass": c3_pass,
    },
    "secondary": {
        "deny_specificity_min_arms_2_7": min(deny_specific),
        "hold_rate_arm_8": hold8,
    },
    "overall_concordance": {
        "agreements": total_agreements, "total": 800,
        "percentage": overall_concordance * 100,
    },
    "verdict": verdict,
    "per_arm_summary": {
        f"arm_{i}": {
            "label": all_results[f"arm_{i}"]['label'],
            "violation": all_results[f"arm_{i}"]['violation'],
            "failclosed_worst": (min(all_results[f"arm_{i}"]['v1']['rate_failclosed'],
                                     all_results[f"arm_{i}"]['v2']['rate_failclosed'])
                                 if i > 1 else None),
            "allow_worst": (min(all_results[f"arm_{i}"]['v1']['rate_allow'],
                                all_results[f"arm_{i}"]['v2']['rate_allow'])
                            if i == 1 else None),
        }
        for i in range(1, 9)
    },
}
with open(os.path.join(RESULTS_DIR, 'overall_results.json'), 'w') as f:
    json.dump(overall_results, f, indent=2)
print(f"\n✅ Results saved to results/overall_results.json")
sys.exit(0 if verdict == "PASS" else 1)
