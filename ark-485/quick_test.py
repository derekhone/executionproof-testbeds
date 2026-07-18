#!/usr/bin/env python3
# Quick 10s test
import sys
sys.path.insert(0, '.')
from measure_sustained import measure_python_sustained, measure_javascript_sustained
import json

print("Quick 10s test...")
py_res = measure_python_sustained(duration_sec=10, warmup_sec=2)
js_res = measure_javascript_sustained(duration_sec=10, warmup_sec=2)

print("\nPython:", py_res['sustained_throughput'], "dec/s")
if js_res:
    print("JavaScript:", js_res['sustained_throughput'], "dec/s")
else:
    print("JavaScript: FAILED")
