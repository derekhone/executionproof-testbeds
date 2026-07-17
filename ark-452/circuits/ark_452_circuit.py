"""
ARK-452 Circuit Implementation — Multi-Step Workflow With One Invalid Step
ExecutionProof ARK Authorization-Boundary Track
Remnant Fieldworks Inc.

Preregistration: ARK_452_preregistration.md
Repository:      https://github.com/derekhone/executionproof-testbeds
Folder:          ark-452/

Circuit Architecture
--------------------
Q_P — Payload qubit. X gate applied iff c_exec = 1 (drives Q_P → |1⟩).

c_exec = c_s1 AND c_s2 AND c_s3 AND c_s4  [computed in Python before circuit build]

All step authorizations are classical constants (per-arm). No quantum measurement
of step states. No inter-qubit gates. Single-qubit circuit only.

Workflow Steps:
    S1: Read Data (non-destructive)
    S2: Calculate (non-destructive)
    S3: Approve Payment (authorization decision, non-destructive)
    S4: Execute Payment (IRREVERSIBLE — the execution gate)
    S5: Write Record (post-execution, not modeled)

Nine arms, 8192 shots each. SPAM gate: 2048 shots (SPAM_P only).
"""

import json
import os
import sys
import datetime
from pathlib import Path

from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager

# ---------------------------------------------------------------------------
# 0. Configuration
# ---------------------------------------------------------------------------

OUTPUT_DIR = Path(__file__).parent.parent / "results"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SHOTS_SPAM      = 2048
SHOTS_PRINCIPAL = 8192

# Arm definitions: (arm, label, c_s1, c_s2, c_s3, c_s4, scenario)
# c_exec = c_s1 AND c_s2 AND c_s3 AND c_s4 is computed in Python
ARM_DEFINITIONS = [
    (1, "ALLOW-complete",       1, 1, 1, 1, "All steps valid; full workflow authorized"),
    (2, "DENY-s1-invalid",      0, 1, 1, 1, "Read-data step inadmissible; rest valid"),
    (3, "DENY-s2-invalid",      1, 0, 1, 1, "Calculation step inadmissible; rest valid"),
    (4, "DENY-s3-invalid",      1, 1, 0, 1, "Approval step inadmissible; execution step otherwise valid"),
    (5, "DENY-s4-invalid",      1, 1, 1, 0, "Execution step itself inadmissible; all prior steps valid"),
    (6, "DENY-s2s3-both",       1, 0, 0, 1, "Two middle steps invalid; execution step authorization valid"),
    (7, "DENY-blanket-attempt", 1, 1, 1, 0, "Three valid prior steps; execution step not independently authorized"),
    (8, "ALLOW-reauth-complete",1, 1, 1, 1, "Full re-authorization after prior workflow block"),
    (9, "DENY-skip-approval",   1, 1, 0, 0, "Approval and execution steps both absent; data and calculation valid"),
]

# ---------------------------------------------------------------------------
# 1. SPAM Gate Circuit
# ---------------------------------------------------------------------------

def build_spam_circuit():
    """
    Single SPAM_P circuit for ARK-452.
    
    SPAM_P: Prepare Q_P in |+⟩ via H → measure
            SPAM_P = |P(Q_P = 1) − 0.5|  [symmetry deviation]
    
    No SPAM_A in ARK-452 (no authorizer qubit).
    """
    qr = QuantumRegister(1, "q_pay")
    cr = ClassicalRegister(1, "c_pay")
    spam_p = QuantumCircuit(qr, cr, name="spam_p")
    spam_p.h(qr[0])
    spam_p.measure(qr[0], cr[0])
    return spam_p


# ---------------------------------------------------------------------------
# 2. Principal Circuits (9 arms)
# ---------------------------------------------------------------------------

def build_arm_circuit(arm_num: int, c_s1: int, c_s2: int, c_s3: int, c_s4: int, label: str) -> QuantumCircuit:
    """
    Build one principal circuit for a single arm.
    
    Architecture (preregistration Section 4.3):
        c_exec ← c_s1 AND c_s2 AND c_s3 AND c_s4  [computed in Python]
        
        if c_exec == 1:
            Apply X to Q_P   [irreversible execution step proceeds; Q_P → |1⟩]
        else:
            Q_P remains in |0⟩  [workflow halted before execution]
        
        Measure Q_P
    
    Execution-gate correction (pre-lock, see preregistration "Pre-Lock
    Drafting Correction Notice"): the execution gate is X, not H. An X gate deterministically
    drives Q_P to |1⟩ so that the ALLOW retention S_A → 1.00, which is required for
    criterion C1 (S_A_min ≥ 0.90) to be satisfiable. An H gate would produce
    P(Q_P=1) ≈ 0.50, making C1 mathematically impossible and guaranteeing a spurious
    FAIL. This mirrors the ARK-449 v1.1 correction. The SPAM_P circuit retains H by
    design (it needs the |+⟩ symmetry diagnostic).
    
    Implementation note (preregistration Section 4.4):
    Since all four step authorization bits are classical constants (not quantum
    measurement outcomes), c_exec is computed in Python. The circuit uses a
    single classical register initialized to c_exec, avoiding nested if_test
    blocks entirely. This eliminates the IBM hardware error 1524 that ARK-444
    encountered with multi-register nested conditionals.
    """
    # Compute c_exec in Python
    c_exec = int(c_s1 and c_s2 and c_s3 and c_s4)
    
    qr = QuantumRegister(1, "q_pay")
    cr_exec = ClassicalRegister(1, "c_exec")  # holds the AND result
    cr_pay = ClassicalRegister(1, "c_pay")    # holds the measurement outcome
    
    qc = QuantumCircuit(qr, cr_exec, cr_pay, name=f"arm{arm_num:02d}_{label}")
    
    # Set c_exec register to the precomputed value
    # Qiskit doesn't support direct classical register assignment in the gate model,
    # so we encode it by conditionally applying a gate based on the value.
    # Simpler: just build the circuit structure based on c_exec directly.
    
    # If c_exec == 1: apply X (drives Q_P deterministically to |1⟩)
    # If c_exec == 0: do nothing (Q_P stays in |0⟩)
    if c_exec == 1:
        qc.x(qr[0])
    
    qc.measure(qr[0], cr_pay[0])
    
    return qc


def build_principal_circuits() -> list:
    """
    Build all nine principal circuits per the preregistration arm table.
    """
    circuits = []
    for arm_num, label, c_s1, c_s2, c_s3, c_s4, scenario in ARM_DEFINITIONS:
        qc = build_arm_circuit(arm_num, c_s1, c_s2, c_s3, c_s4, label)
        circuits.append({
            "arm":      arm_num,
            "label":    label,
            "c_s1":     c_s1,
            "c_s2":     c_s2,
            "c_s3":     c_s3,
            "c_s4":     c_s4,
            "c_exec":   int(c_s1 and c_s2 and c_s3 and c_s4),
            "scenario": scenario,
            "circuit":  qc,
        })
    return circuits


# ---------------------------------------------------------------------------
# 3. Qubit Selection
# ---------------------------------------------------------------------------

def select_qubit(backend) -> dict:
    """
    Select the single qubit Q_P with the lowest readout error from the
    current calibration snapshot.
    
    Selection rule (preregistration Section 7):
    - Readout error must be ≤ 0.02.
    - If no qubit satisfies this constraint, select the lowest-error qubit
      available and record the deviation explicitly.
    - No connectivity constraint (single-qubit circuit).
    """
    props = backend.properties()
    
    readout_errors = {}
    for qubit_idx in range(backend.num_qubits):
        try:
            re = props.readout_error(qubit_idx)
            readout_errors[qubit_idx] = re if re is not None else 1.0
        except Exception:
            readout_errors[qubit_idx] = 1.0
    
    q_p = min(readout_errors, key=readout_errors.get)
    re_p = readout_errors[q_p]
    
    RE_THRESHOLD = 0.02
    constraint_met = re_p <= RE_THRESHOLD
    
    try:
        cal_ts = str(props.last_update_date)
    except Exception:
        cal_ts = datetime.datetime.utcnow().isoformat() + "Z"
    
    result = {
        "Q_P":            q_p,
        "RE_P":           round(re_p, 6),
        "RE_threshold":   RE_THRESHOLD,
        "constraint_met": constraint_met,
        "calibration_ts": cal_ts,
    }
    
    if not constraint_met:
        result["deviation_note"] = (
            f"Q_P readout error {re_p:.4f} exceeds {RE_THRESHOLD}. "
            "Selected the lowest-error qubit available per preregistration Section 7."
        )
    
    return result


# ---------------------------------------------------------------------------
# 4. Transpilation
# ---------------------------------------------------------------------------

def transpile_circuits(circuits_to_transpile: list, backend, qubit_idx: int) -> list:
    """
    Transpile circuits to the target backend using the selected physical qubit.
    """
    pm = generate_preset_pass_manager(
        optimization_level=3,
        backend=backend,
        initial_layout=[qubit_idx],
    )
    
    transpiled = []
    for c in circuits_to_transpile:
        tc = pm.run(c)
        transpiled.append(tc)
    return transpiled


# ---------------------------------------------------------------------------
# 5. Submission and Raw Result Extraction
# ---------------------------------------------------------------------------

def submit_and_collect(sampler: Sampler, circuits: list, shots: int, job_label: str) -> tuple:
    """
    Submit a batch of circuits via SamplerV2 and extract raw counts.
    """
    job = sampler.run(circuits, shots=shots)
    print(f"[ARK-452] {job_label} submitted — job ID: {job.job_id()}")
    print(f"[ARK-452] Waiting for results…")
    result = job.result()
    
    counts_list = []
    for pub_result in result:
        bit_array = pub_result.data
        register_names = list(bit_array.keys())
        
        if "c_pay" in register_names:
            counts = bit_array["c_pay"].get_counts()
        else:
            counts = bit_array[register_names[0]].get_counts()
        
        counts_list.append(counts)
    
    return job.job_id(), counts_list


# ---------------------------------------------------------------------------
# 6. SPAM Gate Evaluation
# ---------------------------------------------------------------------------

def evaluate_spam_gate(spam_p_counts: dict, shots: int) -> dict:
    """
    Evaluate the SPAM gate per preregistration Section 6.
    
    SPAM_P = |P(Q_P = 1) − 0.5|  [|+⟩ symmetry deviation]
    
    Must be ≤ 0.02 for the gate to pass.
    SPAM_P is a gating diagnostic only — NOT subtracted from L_D.
    """
    THRESHOLD = 0.02
    
    count_0_p = spam_p_counts.get("0", 0)
    count_1_p = spam_p_counts.get("1", 0)
    total_p = count_0_p + count_1_p
    p1_p = count_1_p / total_p if total_p > 0 else 0.0
    spam_p_val = abs(p1_p - 0.5)
    
    spam_p_pass = spam_p_val <= THRESHOLD
    gate_passed = spam_p_pass
    
    return {
        "SPAM_P":       round(spam_p_val, 6),
        "SPAM_P_pass":  spam_p_pass,
        "gate_passed":  gate_passed,
        "threshold":    THRESHOLD,
        "shots":        shots,
        "raw_spam_p":   spam_p_counts,
    }


# ---------------------------------------------------------------------------
# 7. Main Execution Entry Point
# ---------------------------------------------------------------------------

def main():
    print("=" * 70)
    print("ARK-452 — Multi-Step Workflow With One Invalid Step")
    print("ExecutionProof ARK Series — Remnant Fieldworks Inc.")
    print("=" * 70)
    
    # Check MANIFEST exists
    manifest_path = Path(__file__).parent.parent / "MANIFEST.txt"
    if not manifest_path.exists():
        print("\n[ERROR] MANIFEST.txt not found in ark-452/.")
        print("Per the lock rules, the MANIFEST must be committed and tagged")
        print("(ark-452-v1.0-lock) before any hardware job is submitted.")
        sys.exit(1)
    
    print(f"\n[OK] MANIFEST found: {manifest_path}")
    
    # Connect to backend
    print("\n[ARK-452] Connecting to IBM Quantum…")
    service = QiskitRuntimeService()
    backend = service.backend("ibm_marrakesh")
    print(f"[ARK-452] Connected to: {backend.name}")
    
    # Qubit selection
    print("\n[ARK-452] Selecting qubit…")
    qubit_info = select_qubit(backend)
    print(f"  Q_P = {qubit_info['Q_P']}  (RE = {qubit_info['RE_P']:.4f})")
    print(f"  Constraint met: {qubit_info['constraint_met']}")
    if not qubit_info["constraint_met"]:
        print(f"  DEVIATION NOTE: {qubit_info.get('deviation_note', '')}")
    
    qubit_path = OUTPUT_DIR / "selected_qubit.json"
    with open(qubit_path, "w") as f:
        json.dump(qubit_info, f, indent=2)
    print(f"[ARK-452] Qubit selection written to {qubit_path}")
    print("[ARK-452] *** Commit this file before submitting the SPAM gate ***")
    
    # Build circuits
    print("\n[ARK-452] Building SPAM gate circuit…")
    spam_circ = build_spam_circuit()
    
    print("[ARK-452] Building 9 principal arm circuits…")
    principal_arm_defs = build_principal_circuits()
    principal_circs = [arm["circuit"] for arm in principal_arm_defs]
    
    # Transpile
    print("\n[ARK-452] Transpiling circuits to ibm_marrakesh…")
    spam_transpiled = transpile_circuits([spam_circ], backend, qubit_info["Q_P"])
    principal_transpiled = transpile_circuits(principal_circs, backend, qubit_info["Q_P"])
    print(f"  SPAM circuit transpiled: {len(spam_transpiled)}")
    print(f"  Principal circuits transpiled: {len(principal_transpiled)}")
    
    # Submit SPAM gate
    print("\n[ARK-452] Submitting SPAM gate job…")
    sampler = Sampler(mode=backend)
    spam_job_id, spam_counts_list = submit_and_collect(
        sampler, spam_transpiled, SHOTS_SPAM, "SPAM gate"
    )
    
    exec_log = {
        "spam_job_id":      spam_job_id,
        "principal_job_id": None,
        "note": "Job IDs committed before results are read, per lock rules."
    }
    exec_log_path = OUTPUT_DIR / "execution_log.json"
    with open(exec_log_path, "w") as f:
        json.dump(exec_log, f, indent=2)
    print(f"[ARK-452] SPAM job ID written to {exec_log_path}")
    print("[ARK-452] *** Commit execution_log.json now, before reading SPAM results ***")
    
    # Submit principal job
    print("\n[ARK-452] Submitting principal job (9 arms × 8192 shots)…")
    sampler = Sampler(mode=backend)
    principal_job_id, principal_counts_list = submit_and_collect(
        sampler, principal_transpiled, SHOTS_PRINCIPAL, "principal"
    )
    
    exec_log["principal_job_id"] = principal_job_id
    with open(exec_log_path, "w") as f:
        json.dump(exec_log, f, indent=2)
    print(f"[ARK-452] Principal job ID written to {exec_log_path}")
    print("[ARK-452] *** Commit execution_log.json now, before reading any results ***")
    
    # Evaluate SPAM gate
    print("\n[ARK-452] Evaluating SPAM gate…")
    spam_result = evaluate_spam_gate(spam_counts_list[0], SHOTS_SPAM)
    
    spam_path = OUTPUT_DIR / "spam_results.json"
    with open(spam_path, "w") as f:
        json.dump(spam_result, f, indent=2)
    
    print(f"  SPAM_P = {spam_result['SPAM_P']:.4f}  ({'✅' if spam_result['SPAM_P_pass'] else '❌'})")
    print(f"  Gate passed: {spam_result['gate_passed']}")
    
    # SPAM gate decision
    if not spam_result["gate_passed"]:
        print("\n[ARK-452] *** SPAM GATE FAILED ***")
        print("Per the locked preregistration (Section 6), the principal job")
        print("results are NOT read. The experiment is recorded as:")
        print("  VERDICT: ABORTED AT SPAM GATE")
        
        proofrecord = {
            "experiment":        "ARK-452",
            "doctrine_tested":   "Prior valid steps in a workflow do not authorize the irreversible execution step.",
            "verdict":           "ABORTED AT SPAM GATE",
            "abort_reason":      f"SPAM_P = {spam_result['SPAM_P']:.4f} > 0.02",
            "spam_gate":         spam_result,
            "qubit_selection":   qubit_info,
            "spam_job_id":       spam_job_id,
            "principal_job_id":  principal_job_id,
            "principal_data_read": False,
        }
        pr_path = OUTPUT_DIR / "proofrecord.json"
        with open(pr_path, "w") as f:
            json.dump(proofrecord, f, indent=2)
        print(f"ProofRecord (gate-stop) written to: {pr_path}")
        return
    
    # Save principal raw results
    print("\n[ARK-452] SPAM gate passed. Reading principal results…")
    
    raw_results = {}
    for i, arm_def in enumerate(principal_arm_defs):
        counts = principal_counts_list[i]
        raw_results[f"arm{arm_def['arm']:02d}"] = {
            "arm":      arm_def["arm"],
            "label":    arm_def["label"],
            "c_s1":     arm_def["c_s1"],
            "c_s2":     arm_def["c_s2"],
            "c_s3":     arm_def["c_s3"],
            "c_s4":     arm_def["c_s4"],
            "c_exec":   arm_def["c_exec"],
            "scenario": arm_def["scenario"],
            "counts":   counts,
        }
    
    raw_path = OUTPUT_DIR / "raw_results.json"
    with open(raw_path, "w") as f:
        json.dump({
            "experiment":       "ARK-452",
            "spam_job_id":      spam_job_id,
            "principal_job_id": principal_job_id,
            "shots_spam":       SHOTS_SPAM,
            "shots_principal":  SHOTS_PRINCIPAL,
            "spam_gate":        spam_result,
            "qubit_selection":  qubit_info,
            "arms":             raw_results,
        }, f, indent=2)
    
    print(f"[ARK-452] Raw results written to {raw_path}")
    print("[ARK-452] Run ark_452_analysis.py to compute verdict.")
    print("\n[ARK-452] Execution complete.")


# ---------------------------------------------------------------------------
# 8. Dry-Run / Simulator Validation
# ---------------------------------------------------------------------------

def dry_run():
    """
    Validate all circuits on a noiseless Aer simulator before hardware submission.
    """
    try:
        from qiskit_aer import AerSimulator
    except ImportError:
        print("qiskit-aer not installed. Install with: pip install qiskit-aer")
        return
    
    print("=" * 70)
    print("ARK-452 DRY RUN — Noiseless Aer Simulation")
    print("=" * 70)
    
    sim = AerSimulator()
    
    # SPAM circuit
    spam_p = build_spam_circuit()
    spam_p_counts = sim.run(spam_p, shots=SHOTS_SPAM).result().get_counts()
    spam_eval = evaluate_spam_gate(spam_p_counts, SHOTS_SPAM)
    print(f"\nSPAM gate (noiseless): SPAM_P={spam_eval['SPAM_P']:.4f}  passed={spam_eval['gate_passed']}")
    
    # Principal circuits
    arm_defs = build_principal_circuits()
    print("\n9-Arm Results (noiseless):")
    print(f"{'Arm':<6} {'Label':<25} {'S1 S2 S3 S4':<15} {'P(1)':<8} {'Expected'}")
    print("-" * 75)
    
    for arm_def in arm_defs:
        qc = arm_def["circuit"]
        result = sim.run(qc, shots=SHOTS_PRINCIPAL).result()
        counts = result.get_counts()
        total = sum(counts.values())
        c1 = counts.get("1", 0) + counts.get("0 1", 0) + counts.get("1 1", 0) + counts.get("1 0", 0)
        p1 = c1 / total if total > 0 else 0.0
        steps = f"{arm_def['c_s1']} {arm_def['c_s2']} {arm_def['c_s3']} {arm_def['c_s4']}"
        expected = "≥ 0.90" if arm_def["c_exec"] == 1 else "≈ 0.00"
        status = "✅" if (
            (arm_def["c_exec"] == 1 and p1 >= 0.90) or
            (arm_def["c_exec"] == 0 and p1 <= 0.02)
        ) else "❌"
        print(f"{arm_def['arm']:<6} {arm_def['label']:<25} {steps:<15} {p1:<8.4f} {expected}  {status}")
    
    print("\n[DRY RUN COMPLETE]")


if __name__ == "__main__":
    if "--dry-run" in sys.argv:
        dry_run()
    else:
        main()
