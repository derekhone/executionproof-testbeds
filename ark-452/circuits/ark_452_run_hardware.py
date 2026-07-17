"""
ARK-452 Hardware Runner — strict submit → commit → retrieve sequence
ExecutionProof ARK Authorization-Boundary Track — Remnant Fieldworks Inc.

POST-LOCK OPERATIONAL HARNESS (not part of the preregistration lock).
This runner imports the LOCKED circuit-building and evaluation functions from
ark_452_circuit.py UNCHANGED and executes the strict execution sequence from
ARK_452_preregistration.md Section 8.1:

    1. Select qubit          -> write selected_qubit.json  (commit before SPAM)
    2. Submit SPAM job (async, no wait) -> record job ID
    3. Submit principal job (async, no wait) -> record job ID
    4. Commit BOTH job IDs BEFORE reading any results
    5. Read SPAM results -> apply gate decision (Section 6.2)
    6a. SPAM PASS -> read principal results -> write raw_results.json
    6b. SPAM FAIL -> record abort -> do NOT read principal data

The async (submit-both-then-retrieve) pattern is required so the SPAM outcome
cannot influence whether the principal job is submitted (no cherry-picking).
This mirrors the ARK-448 submit/retrieve split. Job IDs are committed to git
before any results are retrieved; IBM's server-side job-creation timestamps
are the authoritative ordering proof.

The circuit definitions, SPAM evaluation, qubit selection, and transpilation
are all imported from the locked module; nothing scientific is redefined here.
"""

import json
import subprocess
import sys
import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler

# Import LOCKED functions unchanged
from ark_452_circuit import (
    build_spam_circuit,
    build_principal_circuits,
    select_qubit,
    transpile_circuits,
    evaluate_spam_gate,
    SHOTS_SPAM,
    SHOTS_PRINCIPAL,
    OUTPUT_DIR,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
ARK_DIR = Path(__file__).resolve().parents[1]


def git_commit(paths, message):
    """Commit specific paths with a message. Returns commit SHA or None."""
    try:
        rel = [str(p) for p in paths]
        subprocess.run(["git", "-C", str(REPO_ROOT), "add", *rel], check=True)
        subprocess.run(["git", "-C", str(REPO_ROOT), "commit", "-m", message], check=True)
        sha = subprocess.check_output(
            ["git", "-C", str(REPO_ROOT), "rev-parse", "HEAD"]
        ).decode().strip()
        print(f"[COMMIT] {sha[:8]}  {message}")
        return sha
    except subprocess.CalledProcessError as e:
        print(f"[COMMIT WARNING] {e}")
        return None


def utcnow():
    return datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def extract_counts(result):
    """Extract c_pay counts from a SamplerV2 result object."""
    counts_list = []
    for pub_result in result:
        bit_array = pub_result.data
        register_names = list(bit_array.keys())
        if "c_pay" in register_names:
            counts = bit_array["c_pay"].get_counts()
        else:
            counts = bit_array[register_names[0]].get_counts()
        counts_list.append(counts)
    return counts_list


def main():
    print("=" * 70)
    print("ARK-452 HARDWARE RUN — Multi-Step Workflow With One Invalid Step")
    print("Strict submit -> commit -> retrieve sequence (prereg Section 8.1)")
    print("=" * 70)

    manifest = ARK_DIR / "MANIFEST.txt"
    if not manifest.exists():
        print("[ERROR] MANIFEST.txt missing — lock must exist before hardware run.")
        sys.exit(1)
    print(f"[OK] Lock MANIFEST present: {manifest}")

    print("\n[1] Connecting to IBM Quantum…")
    service = QiskitRuntimeService()
    backend = service.backend("ibm_marrakesh")
    print(f"    Backend: {backend.name}")

    # ---- Step 1: qubit selection ----
    print("\n[2] Selecting payload qubit Q_P (lowest readout error)…")
    qubit_info = select_qubit(backend)
    print(f"    Q_P = {qubit_info['Q_P']}  RE = {qubit_info['RE_P']:.4f}  "
          f"constraint_met = {qubit_info['constraint_met']}")
    qubit_info["selection_committed_at"] = utcnow()
    qubit_path = OUTPUT_DIR / "selected_qubit.json"
    with open(qubit_path, "w") as f:
        json.dump(qubit_info, f, indent=2)
    git_commit([qubit_path], "ARK-452 exec: qubit selection (Q_P) committed before SPAM submission")

    # ---- Build + transpile ----
    print("\n[3] Building + transpiling circuits…")
    spam_circ = build_spam_circuit()
    principal_defs = build_principal_circuits()
    principal_circs = [a["circuit"] for a in principal_defs]

    spam_t = transpile_circuits([spam_circ], backend, qubit_info["Q_P"])
    principal_t = transpile_circuits(principal_circs, backend, qubit_info["Q_P"])
    print(f"    SPAM transpiled: {len(spam_t)}   Principal transpiled: {len(principal_t)}")

    # ---- Step 2+3: submit BOTH jobs async (no result() yet) ----
    print("\n[4] Submitting SPAM gate job (async)…")
    sampler_spam = Sampler(mode=backend)
    spam_job = sampler_spam.run(spam_t, shots=SHOTS_SPAM)
    spam_job_id = spam_job.job_id()
    print(f"    SPAM job ID: {spam_job_id}")

    print("[5] Submitting principal job (async, before reading SPAM)…")
    sampler_prin = Sampler(mode=backend)
    prin_job = sampler_prin.run(principal_t, shots=SHOTS_PRINCIPAL)
    prin_job_id = prin_job.job_id()
    print(f"    Principal job ID: {prin_job_id}")

    # ---- Step 4: commit both IDs BEFORE reading any results ----
    exec_log = {
        "experiment": "ARK-452",
        "backend": backend.name,
        "Q_P": qubit_info["Q_P"],
        "spam_job_id": spam_job_id,
        "principal_job_id": prin_job_id,
        "spam_job_submitted_at": utcnow(),
        "principal_job_submitted_at": utcnow(),
        "note": "Both job IDs committed BEFORE any results are read (prereg Section 8.1).",
    }
    exec_log_path = OUTPUT_DIR / "execution_log.json"
    with open(exec_log_path, "w") as f:
        json.dump(exec_log, f, indent=2)
    git_commit([exec_log_path],
               "ARK-452 exec: SPAM + principal job IDs committed BEFORE reading any results")

    # ---- Step 5: retrieve + evaluate SPAM gate ----
    print("\n[6] Retrieving SPAM results + evaluating gate…")
    spam_counts = extract_counts(spam_job.result())
    spam_result = evaluate_spam_gate(spam_counts[0], SHOTS_SPAM)
    spam_path = OUTPUT_DIR / "spam_results.json"
    with open(spam_path, "w") as f:
        json.dump(spam_result, f, indent=2)
    print(f"    SPAM_P = {spam_result['SPAM_P']:.4f}  "
          f"({'PASS' if spam_result['SPAM_P_pass'] else 'FAIL'})  "
          f"gate_passed={spam_result['gate_passed']}")

    if not spam_result["gate_passed"]:
        print("\n[7] *** SPAM GATE FAILED — ABORT ***")
        print("    Principal results are NOT read (prereg Section 6.2 / 8.1 step 6b).")
        proofrecord = {
            "experiment": "ARK-452",
            "title": "Multi-Step Workflow With One Invalid Step",
            "verdict": "ABORTED AT SPAM GATE",
            "abort_reason": f"SPAM_P = {spam_result['SPAM_P']:.4f} > 0.02",
            "spam_gate": spam_result,
            "qubit_selection": qubit_info,
            "spam_job_id": spam_job_id,
            "principal_job_id": prin_job_id,
            "principal_data_read": False,
        }
        pr_path = OUTPUT_DIR / "proofrecord.json"
        with open(pr_path, "w") as f:
            json.dump(proofrecord, f, indent=2)
        git_commit([spam_path, pr_path],
                   "ARK-452 exec: ABORTED AT SPAM GATE — principal data not read")
        print(f"    Gate-stop ProofRecord written: {pr_path}")
        return

    # ---- Step 6a: SPAM passed -> read principal ----
    print("\n[7] SPAM gate PASSED — reading principal results…")
    prin_counts = extract_counts(prin_job.result())

    raw_arms = {}
    for i, adef in enumerate(principal_defs):
        raw_arms[f"arm{adef['arm']:02d}"] = {
            "arm": adef["arm"],
            "label": adef["label"],
            "c_s1": adef["c_s1"],
            "c_s2": adef["c_s2"],
            "c_s3": adef["c_s3"],
            "c_s4": adef["c_s4"],
            "c_exec": adef["c_exec"],
            "scenario": adef["scenario"],
            "counts": prin_counts[i],
        }

    raw_path = OUTPUT_DIR / "raw_results.json"
    with open(raw_path, "w") as f:
        json.dump({
            "experiment": "ARK-452",
            "backend": backend.name,
            "spam_job_id": spam_job_id,
            "principal_job_id": prin_job_id,
            "shots_spam": SHOTS_SPAM,
            "shots_principal": SHOTS_PRINCIPAL,
            "spam_gate": spam_result,
            "qubit_selection": qubit_info,
            "arms": raw_arms,
        }, f, indent=2)
    git_commit([spam_path, raw_path],
               "ARK-452 exec: SPAM PASS + principal raw results committed")
    print(f"    Raw results written: {raw_path}")
    print("\n[8] Run ark_452_analysis.py to compute the verdict.")
    print("[DONE] Hardware run complete.")


if __name__ == "__main__":
    main()
