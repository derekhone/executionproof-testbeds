#!/usr/bin/env python3
"""
ARK-484 Throughput Measurement — Verification Decision · Burst Throughput

Measures peak burst throughput (decisions/second) for frozen ARK-458 guard.
Tests both V1 (JavaScript) and V2 (Python) implementations.
"""

import json
import time
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, List

# Import V2 guard
sys.path.insert(0, str(Path(__file__).parent / "verifiers"))
from v2_guard_frozen import verify_deployment as v2_verify


def measure_v2_python_throughput(scenarios: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Measure Python implementation throughput"""
    print(f"\n{'='*70}")
    print("V2 (Python) - Burst Throughput Test")
    print(f"{'='*70}")
    print(f"Processing {len(scenarios)} scenarios...")
    
    start_time = time.perf_counter()
    
    correct_count = 0
    for scenario in scenarios:
        authorized = scenario["authorized_deployment"]
        presented = scenario["presented_deployment"]
        expected = scenario["expected_decision"]
        
        result = v2_verify(authorized, presented)
        if result["decision"] == expected:
            correct_count += 1
    
    end_time = time.perf_counter()
    elapsed_sec = end_time - start_time
    throughput = len(scenarios) / elapsed_sec
    
    print(f"\n✅ V2 (Python) Results:")
    print(f"   Decisions processed: {len(scenarios)}")
    print(f"   Correct decisions:   {correct_count}/{len(scenarios)}")
    print(f"   Total time:          {elapsed_sec:.4f} seconds")
    print(f"   Throughput:          {throughput:,.2f} decisions/sec")
    
    return {
        "implementation": "V2-Python",
        "decisions_processed": len(scenarios),
        "correct_decisions": correct_count,
        "batch_total_time_sec": elapsed_sec,
        "throughput_decisions_per_sec": throughput
    }


def measure_v1_javascript_throughput(scenarios: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Measure JavaScript implementation throughput via Node.js"""
    print(f"\n{'='*70}")
    print("V1 (JavaScript) - Burst Throughput Test")
    print(f"{'='*70}")
    print(f"Processing {len(scenarios)} scenarios...")
    
    # Write scenarios to temp file for Node.js
    temp_scenarios_file = Path("results/temp_scenarios_v1.json")
    with open(temp_scenarios_file, "w") as f:
        json.dump(scenarios, f)
    
    # JavaScript code to process all scenarios
    js_code = f"""
const {{ verifyDeployment }} = require('./verifiers/v1_guard_frozen.js');
const fs = require('fs');

const scenarios = JSON.parse(fs.readFileSync('{temp_scenarios_file}', 'utf8'));
const startTime = process.hrtime.bigint();

let correctCount = 0;
for (const scenario of scenarios) {{
    const authorized = scenario.authorized_deployment;
    const presented = scenario.presented_deployment;
    const expected = scenario.expected_decision;
    
    const result = verifyDeployment(authorized, presented);
    if (result.decision === expected) {{
        correctCount++;
    }}
}}

const endTime = process.hrtime.bigint();
const elapsedNs = Number(endTime - startTime);
const elapsedSec = elapsedNs / 1e9;
const throughput = scenarios.length / elapsedSec;

const results = {{
    implementation: "V1-JavaScript",
    decisions_processed: scenarios.length,
    correct_decisions: correctCount,
    batch_total_time_sec: elapsedSec,
    throughput_decisions_per_sec: throughput
}};

console.log(JSON.stringify(results, null, 2));
"""
    
    # Run via Node.js
    result = subprocess.run(
        ["node", "-e", js_code],
        cwd=Path(__file__).parent,
        capture_output=True,
        text=True,
        timeout=300  # 5 minute timeout
    )
    
    if result.returncode != 0:
        print(f"❌ V1 execution failed: {result.stderr}")
        return {
            "implementation": "V1-JavaScript",
            "decisions_processed": 0,
            "correct_decisions": 0,
            "batch_total_time_sec": 0,
            "throughput_decisions_per_sec": 0,
            "error": result.stderr
        }
    
    # Parse results
    v1_results = json.loads(result.stdout.strip())
    
    print(f"\n✅ V1 (JavaScript) Results:")
    print(f"   Decisions processed: {v1_results['decisions_processed']}")
    print(f"   Correct decisions:   {v1_results['correct_decisions']}/{v1_results['decisions_processed']}")
    print(f"   Total time:          {v1_results['batch_total_time_sec']:.4f} seconds")
    print(f"   Throughput:          {v1_results['throughput_decisions_per_sec']:,.2f} decisions/sec")
    
    # Clean up temp file
    temp_scenarios_file.unlink(missing_ok=True)
    
    return v1_results


def compute_verdict(v1_results: Dict[str, Any], v2_results: Dict[str, Any]) -> str:
    """Determine PASS/FAIL verdict based on thresholds"""
    # C1: V2 (Python) ≥ 100,000 decisions/sec
    c1_pass = v2_results["throughput_decisions_per_sec"] >= 100_000
    
    # C2: V1 (JavaScript) ≥ 150,000 decisions/sec
    c2_pass = v1_results["throughput_decisions_per_sec"] >= 150_000
    
    # C3: All decisions processed correctly
    c3_pass = (
        v1_results["correct_decisions"] == v1_results["decisions_processed"] and
        v2_results["correct_decisions"] == v2_results["decisions_processed"]
    )
    
    verdict = "PASS" if (c1_pass and c2_pass and c3_pass) else "FAIL"
    
    return verdict, {
        "C1_v2_throughput_gte_100k": c1_pass,
        "C2_v1_throughput_gte_150k": c2_pass,
        "C3_all_correct": c3_pass
    }


def main():
    """Execute burst throughput measurement"""
    print("ARK-484 Burst Throughput Measurement")
    print("=" * 70)
    
    # Load scenarios
    scenarios_file = Path("results/burst_scenarios.json")
    if not scenarios_file.exists():
        print(f"❌ Scenarios file not found: {scenarios_file}")
        print("Run generator/scenario_generator.py first")
        sys.exit(1)
    
    with open(scenarios_file) as f:
        scenarios = json.load(f)
    
    print(f"Loaded {len(scenarios)} scenarios")
    
    # Measure throughput for both implementations
    v2_results = measure_v2_python_throughput(scenarios)
    v1_results = measure_v1_javascript_throughput(scenarios)
    
    # Compute verdict
    verdict, criteria = compute_verdict(v1_results, v2_results)
    
    # Summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    print(f"V2 (Python):     {v2_results['throughput_decisions_per_sec']:>15,.2f} decisions/sec")
    print(f"V1 (JavaScript): {v1_results['throughput_decisions_per_sec']:>15,.2f} decisions/sec")
    print()
    print("Success Criteria:")
    print(f"  C1 (V2 ≥ 100K/sec):  {'✅ PASS' if criteria['C1_v2_throughput_gte_100k'] else '❌ FAIL'}")
    print(f"  C2 (V1 ≥ 150K/sec):  {'✅ PASS' if criteria['C2_v1_throughput_gte_150k'] else '❌ FAIL'}")
    print(f"  C3 (All correct):    {'✅ PASS' if criteria['C3_all_correct'] else '❌ FAIL'}")
    print()
    print(f"VERDICT: {verdict}")
    print(f"{'='*70}")
    
    # Save results
    output = {
        "verdict": verdict,
        "criteria": criteria,
        "v1_results": v1_results,
        "v2_results": v2_results,
        "total_scenarios": len(scenarios)
    }
    
    with open("results/throughput_results.json", "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"\n✅ Results saved to results/throughput_results.json")
    
    if verdict == "FAIL":
        sys.exit(1)


if __name__ == "__main__":
    main()
