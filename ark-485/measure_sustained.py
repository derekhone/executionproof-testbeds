#!/usr/bin/env python3
"""
ARK-485 Sustained Throughput Measurement
Measures decisions/second over 60s continuous execution
"""

import sys
import time
import json
import subprocess
import importlib.util
from pathlib import Path

# Load V2 guard
spec = importlib.util.spec_from_file_location("v2_guard", "verifiers/v2_guard.py")
v2_guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v2_guard)

def measure_python_sustained(duration_sec=60, warmup_sec=5):
    """Measure sustained throughput for Python V2 implementation"""
    print(f"Measuring Python V2 sustained throughput ({duration_sec}s)...")
    
    # Test scenario: exact match (should ALLOW)
    scenario = {
        "authorization": {
            "binding": {
                "principal": "user-12345",
                "role": "DataScientist",
                "account": "123456789012",
                "permission_set": "arn:aws:s3:::prod-ml-bucket",
                "condition": "AttachRolePolicy"
            }
        },
        "execution": {
            "action": {
                "principal": "user-12345",
                "role": "DataScientist",
                "account": "123456789012",
                "permission_set": "arn:aws:s3:::prod-ml-bucket",
                "condition": "AttachRolePolicy"
            }
        }
    }
    
    # Warmup
    print(f"  Warming up ({warmup_sec}s)...")
    warmup_start = time.perf_counter()
    warmup_count = 0
    while time.perf_counter() - warmup_start < warmup_sec:
        result = v2_guard.evaluate(scenario)
        warmup_count += 1
    print(f"  Warmup complete ({warmup_count:,} decisions)")
    
    # Sustained measurement
    print(f"  Measuring sustained load ({duration_sec}s)...")
    count = 0
    correct = 0
    start = time.perf_counter()
    end_time = start + duration_sec
    
    while time.perf_counter() < end_time:
        result = v2_guard.evaluate(scenario)
        count += 1
        if result["decision"] == "ALLOW":
            correct += 1
    
    elapsed = time.perf_counter() - start
    throughput = count / elapsed
    accuracy = correct / count if count > 0 else 0
    
    return {
        "implementation": "V2_Python",
        "duration_sec": elapsed,
        "total_decisions": count,
        "correct_decisions": correct,
        "accuracy": accuracy,
        "sustained_throughput": throughput,
        "warmup_decisions": warmup_count,
        "warmup_sec": warmup_sec
    }

def measure_javascript_sustained(duration_sec=60, warmup_sec=5):
    """Measure sustained throughput for JavaScript V1 implementation"""
    print(f"Measuring JavaScript V1 sustained throughput ({duration_sec}s)...")
    
    # Create Node.js measurement script
    js_script = f"""
const BINDING_DIMS = ["principal", "role", "account", "permission_set", "condition"];

function evaluate(scenario) {{
  const binding = scenario.authorization.binding;
  const action = scenario.execution.action;

  for (const dim of BINDING_DIMS) {{
    const a = binding[dim];
    const b = action[dim];
    if (typeof a !== "string" || typeof b !== "string" || a !== b) {{
      return {{
        decision: "DENY",
        reason:
          `Action mismatch on '${{dim}}': approved grant bound to ` +
          `${{JSON.stringify(a)}} but execution action is ${{JSON.stringify(b)}} ` +
          `(approval does not authorize a mutated IAM action)`,
      }};
    }}
  }}

  return {{
    decision: "ALLOW",
    reason: "Execution action matches the approved IAM grant on all binding dimensions",
  }};
}}

const scenario = {{
    authorization: {{
        binding: {{
            principal: "user-12345",
            role: "DataScientist",
            account: "123456789012",
            permission_set: "arn:aws:s3:::prod-ml-bucket",
            condition: "AttachRolePolicy"
        }}
    }},
    execution: {{
        action: {{
            principal: "user-12345",
            role: "DataScientist",
            account: "123456789012",
            permission_set: "arn:aws:s3:::prod-ml-bucket",
            condition: "AttachRolePolicy"
        }}
    }}
}};

// Warmup
console.log("  Warming up ({warmup_sec}s)...");
let warmupStart = Date.now();
let warmupCount = 0;
while ((Date.now() - warmupStart) / 1000 < {warmup_sec}) {{
    evaluate(scenario);
    warmupCount++;
}}
console.log(`  Warmup complete (${{warmupCount.toLocaleString()}} decisions)`);

// Sustained measurement
console.log("  Measuring sustained load ({duration_sec}s)...");
let count = 0;
let correct = 0;
const start = Date.now();
const endTime = start + ({duration_sec} * 1000);

while (Date.now() < endTime) {{
    const result = evaluate(scenario);
    count++;
    if (result.decision === "ALLOW") correct++;
}}

const elapsed = (Date.now() - start) / 1000;
const throughput = count / elapsed;
const accuracy = correct / count;

const results = {{
    implementation: "V1_JavaScript",
    duration_sec: elapsed,
    total_decisions: count,
    correct_decisions: correct,
    accuracy: accuracy,
    sustained_throughput: throughput,
    warmup_decisions: warmupCount,
    warmup_sec: {warmup_sec}
}};

console.log(JSON.stringify(results, null, 2));
"""
    
    # Write temp script
    with open("temp_measure.js", "w") as f:
        f.write(js_script)
    
    # Run Node.js
    try:
        result = subprocess.run(
            ["node", "temp_measure.js"],
            capture_output=True,
            text=True,
            timeout=duration_sec + warmup_sec + 10
        )
        
        # Extract JSON from output (last complete JSON block)
        lines = result.stdout.strip().split('\n')
        for line in reversed(lines):
            if line.startswith('{'):
                try:
                    return json.loads('\n'.join(lines[lines.index(line):]))
                except:
                    continue
        
        # Fallback: parse from full output
        json_start = result.stdout.rfind('{')
        if json_start >= 0:
            return json.loads(result.stdout[json_start:])
        
        print("Warning: Could not parse JavaScript results")
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
        return None
        
    except Exception as e:
        print(f"Error running JavaScript measurement: {e}")
        return None
    finally:
        Path("temp_measure.js").unlink(missing_ok=True)

def main():
    print("ARK-485: Sustained Throughput Measurement")
    print("=" * 60)
    
    # Measure both implementations
    py_results = measure_python_sustained()
    js_results = measure_javascript_sustained()
    
    # Combine results
    results = {
        "experiment": "ARK-485",
        "component": "Verification Decision",
        "dimension": "Sustained Throughput",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "results": {
            "python": py_results,
            "javascript": js_results
        },
        "thresholds": {
            "python_min": 50000,
            "javascript_min": 100000,
            "accuracy_required": 1.0
        }
    }
    
    # Evaluate verdict
    py_pass = (py_results["sustained_throughput"] >= 50000 and 
               py_results["accuracy"] == 1.0)
    js_pass = (js_results["sustained_throughput"] >= 100000 and 
               js_results["accuracy"] == 1.0) if js_results else False
    
    results["verdict"] = "PASS" if (py_pass and js_pass) else "FAIL"
    results["verdict_detail"] = {
        "C1_throughput": py_pass and js_pass,
        "C2_accuracy": (py_results["accuracy"] == 1.0 and 
                        (js_results["accuracy"] == 1.0 if js_results else False))
    }
    
    # Save results
    output_file = "results/sustained_results.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    
    # Print summary
    print("\n" + "=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)
    print(f"Python V2:     {py_results['sustained_throughput']:,.0f} dec/s " +
          f"(threshold: 50,000) [{py_results['accuracy']:.1%} accuracy]")
    if js_results:
        print(f"JavaScript V1: {js_results['sustained_throughput']:,.0f} dec/s " +
              f"(threshold: 100,000) [{js_results['accuracy']:.1%} accuracy]")
    print(f"\nVERDICT: {results['verdict']}")
    print(f"Saved to: {output_file}")

if __name__ == "__main__":
    main()
