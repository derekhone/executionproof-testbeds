#!/usr/bin/env python3
"""
ARK-454 Kill-Gate Calibration

Generate 100 calibration scenarios (50 legitimate Arm-1, 50 attack scenarios
cycling Arms 2-8), evaluate with both guards V1 (JavaScript) and V2 (Python), and
check (per PREREGISTRATION.md Section 7):
  (a) attack-effectiveness 100% on the 50 attacks AND clean 100% on the 50 legit;
  (b) both guards ALLOW all 50 legitimate scenarios (sanity);
  (c) both guards fail-closed (verdict != ALLOW) on all 50 attacks (sanity);
  (d) V1-V2 exact-verdict concordance >= 99%.
Any failure aborts before arms run.

The attack-effectiveness gate is the ARK-454 safeguard against a scenario that is
not really an attack being silently scored as a fail-closed success -- the analogue
of the ARK-455b mutation-effectiveness gate (see ../ark-455/CORRECTION.md).

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


def run_v1_batch(scenarios):
    """Evaluate a list of scenarios with V1 (JavaScript) in one call."""
    tmp = '/tmp/ark454_v1_batch.json'
    with open(tmp, 'w') as f:
        json.dump(scenarios, f)
    result = subprocess.run(['node', V1_PATH, tmp], capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        raise RuntimeError(f"V1 failed: {result.stderr}")
    return json.loads(result.stdout)["verdicts"]


print("=== ARK-454 KILL-GATE CALIBRATION ===")
start_time = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
print(f"Start timestamp: {start_time}")

calibration_seed = secrets.randbits(256)
print(f"Calibration seed: {calibration_seed}\n")

gen = ScenarioGenerator(seed=calibration_seed)

print("Generating 100 calibration scenarios (50 legitimate, 50 attacks 2-8)...")
legit_scen, legit_audit = gen.generate_arm_scenarios(arm_id=1, count=50)

attack_scen, attack_audit, attack_arm_ids = [], [], []
for i in range(50):
    arm_id = 2 + (i % 7)  # arms 2..8
    recs, aud = gen.generate_arm_scenarios(arm_id=arm_id, count=1)
    attack_scen.extend(recs)
    attack_audit.extend(aud)
    attack_arm_ids.append(arm_id)

all_scen = legit_scen + attack_scen

# --- Attack-effectiveness gate ---
print("\n=== Attack-Effectiveness Gate ===")
legit_clean = [i for i, a in enumerate(legit_audit) if a.get("clean") is not True]
attack_eff = [i for i, a in enumerate(attack_audit) if a.get("attack_effective") is not True]
print(f"Legitimate scenarios genuinely clean: {50 - len(legit_clean)}/50")
print(f"Attack scenarios genuinely effective: {50 - len(attack_eff)}/50")
if legit_clean or attack_eff:
    print("⛔ KILL-GATE FAILED: attack-effectiveness gate violated.")
    if legit_clean:
        print(f"   Non-clean legitimate indices: {legit_clean[:10]}")
    if attack_eff:
        print(f"   Ineffective attack indices: {attack_eff[:10]}")
    sys.exit(1)
print("✅ All legitimate scenarios clean; all attack scenarios effective.")

# --- V2 (Python) ---
print("\n=== Running V2 (Python) ===")
v2_verdicts = [v2_guard.evaluate(s) for s in all_scen]
v2_legit_allow = v2_verdicts[:50].count("ALLOW")
v2_attack_failclosed = sum(1 for v in v2_verdicts[50:] if v != "ALLOW")
print(f"V2: {v2_legit_allow}/50 legit ALLOW, {v2_attack_failclosed}/50 attacks fail-closed")

# --- V1 (JavaScript) ---
print("\n=== Running V1 (JavaScript) ===")
v1_verdicts = run_v1_batch(all_scen)
v1_legit_allow = v1_verdicts[:50].count("ALLOW")
v1_attack_failclosed = sum(1 for v in v1_verdicts[50:] if v != "ALLOW")
print(f"V1: {v1_legit_allow}/50 legit ALLOW, {v1_attack_failclosed}/50 attacks fail-closed")

# --- Concordance (exact verdict) ---
print("\n=== Concordance Check ===")
agreements = sum(1 for a, b in zip(v1_verdicts, v2_verdicts) if a == b)
concordance_pct = agreements / 100 * 100
print(f"V1-V2 exact-verdict agreement: {agreements}/100 ({concordance_pct:.1f}%)  threshold >=99%")

# --- Sanity ---
sanity_legit = (v2_legit_allow == 50) and (v1_legit_allow == 50)
sanity_attack = (v2_attack_failclosed == 50) and (v1_attack_failclosed == 50)
print(f"\n=== Sanity Check ===")
print(f"Both guards ALLOW all 50 legit:        {'✅ PASS' if sanity_legit else '❌ FAIL'}")
print(f"Both guards fail-closed all 50 attacks:{'✅ PASS' if sanity_attack else '❌ FAIL'}")

concordance_pass = concordance_pct >= 99.0
verdict = "PASS" if (concordance_pass and sanity_legit and sanity_attack) else "FAIL"

print(f"\n=== KILL-GATE VERDICT ===")
print("✅ KILL-GATE PASSED" if verdict == "PASS" else "⛔ KILL-GATE FAILED")

os.makedirs(RESULTS_DIR, exist_ok=True)
killgate_results = {
    "start_time": start_time,
    "calibration_seed": calibration_seed,
    "total_scenarios": 100,
    "legitimate_scenarios": 50,
    "attack_scenarios": 50,
    "attack_arm_cycle": attack_arm_ids,
    "attack_effectiveness": {
        "legit_clean": 50 - len(legit_clean),
        "attack_effective": 50 - len(attack_eff),
        "pass": (not legit_clean and not attack_eff),
    },
    "v1_results": {"legit_allow": v1_legit_allow, "attack_failclosed": v1_attack_failclosed},
    "v2_results": {"legit_allow": v2_legit_allow, "attack_failclosed": v2_attack_failclosed},
    "concordance": {"agreements": agreements, "percentage": concordance_pct,
                    "threshold": 99.0, "pass": concordance_pass},
    "sanity": {"legit_pass": sanity_legit, "attack_pass": sanity_attack},
    "verdict": verdict,
}
with open(os.path.join(RESULTS_DIR, 'killgate_calibration.json'), 'w') as f:
    json.dump(killgate_results, f, indent=2)
print(f"\n✅ Results saved to results/killgate_calibration.json")
sys.exit(0 if verdict == "PASS" else 1)
