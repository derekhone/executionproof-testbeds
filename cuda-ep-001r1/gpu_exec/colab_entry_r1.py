#!/usr/bin/env python3
"""
colab_entry_r1.py
=================
Thin Colab entry point for the CUDA-EP-001R1 remediation retest harness.
Run from a Colab T4 cell after cloning the repo:

    import os, subprocess
    t = os.environ['GHT']
    subprocess.run(['git','clone','-q',
        f'https://x-access-token:{t}@github.com/derekhone/executionproof-testbeds.git',
        '/content/ep'])
    subprocess.run(['git','-C','/content/ep','checkout','-q','cuda-ep-001r1'])
    exec(open('/content/ep/cuda-ep-001r1/gpu_exec/colab_entry_r1.py').read())

This installs deps, runs gpu_real_run_r1.py on the real GPU, then commits and
pushes the results to branch 'cuda-ep-001r1-gpu-run' using the token in
os.environ['GHT']. Nothing secret is printed. CUDA-EP-001 is not touched.
"""
import os
import subprocess

REPO = "/content/ep"
PKG = os.path.join(REPO, "cuda-ep-001r1")
HARNESS = os.path.join(PKG, "gpu_exec", "gpu_real_run_r1.py")


def sh(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


print("### GPU check ...")
print(sh(["nvidia-smi", "--query-gpu=name,compute_cap,driver_version",
          "--format=csv,noheader"]).stdout.strip() or "NO GPU")

print("### Installing dependencies (dilithium-py, numpy) ...")
sh(["pip", "install", "-q", "dilithium-py", "numpy"])

print("### Running R1 real-GPU harness ...")
r = sh(["python3", HARNESS])
print(r.stdout[-9000:])
if r.stderr.strip():
    print("----- STDERR (tail) -----")
    print(r.stderr[-3000:])

print("### Pushing results back to branch cuda-ep-001r1-gpu-run ...")
tok = os.environ.get("GHT", "")
if tok:
    url = f"https://x-access-token:{tok}@github.com/derekhone/executionproof-testbeds.git"
    sh(["git", "-C", REPO, "remote", "set-url", "origin", url])
sh(["git", "-C", REPO, "config", "user.name", "derekhone"])
sh(["git", "-C", REPO, "config", "user.email", "derek@ownerremnantfieldworks.com"])
sh(["git", "-C", REPO, "checkout", "-B", "cuda-ep-001r1-gpu-run"])
sh(["git", "-C", REPO, "add", "-A"])
sh(["git", "-C", REPO, "commit", "-q", "-m",
    "Real GPU run results (Colab T4) - CUDA-EP-001R1 remediation retest"])
p = sh(["git", "-C", REPO, "push", "-q", "-f", "origin", "cuda-ep-001r1-gpu-run"])
print(f"push_returncode={p.returncode}")
if p.stderr.strip() and "x-access-token" not in p.stderr:
    print(p.stderr[-500:])
print("### DONE. Results on branch cuda-ep-001r1-gpu-run under "
      "cuda-ep-001r1/gpu_exec/results/")
