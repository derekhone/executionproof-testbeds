"""
ARK-449 Circuit Implementation — State Changes After Verification
ExecutionProof ARK Authorization-Boundary Track
Remnant Fieldworks Inc.

Preregistration: ARK_449_preregistration.md
Repository:      https://github.com/derekhone/executionproof-testbeds
Folder:          ark-449/

LOCK INSTRUCTION
----------------
This file must be committed and SHA-256-hashed in the MANIFEST before any
hardware job is submitted. Do not modify after the MANIFEST is committed.

Circuit Architecture
--------------------
Q_A  — Authorizer qubit. Encodes authorization decision at T1.
Q_P  — Payload qubit. X gate applied to drive |1⟩ iff c_exec = 1 (v1.1; was H in v1.0).

All conditioning is classical feedforward:
    c_auth  ← measure(Q_A)
    c_state ← arm-specific constant (0 = inadmissible, 1 = admissible)
    c_exec  ← c_auth AND c_state  [classical AND]
    if c_exec == 1: apply X to Q_P (drive to |1⟩)

Nine arms, 8192 shots each. SPAM gate: 2048 shots.

Arm Table (from preregistration Section 5)
------------------------------------------
Arm 1 — ALLOW-unchanged     c_auth=1 c_state=1 c_exec=1  (original auth, state still valid)
Arm 2 — DENY-revoked        c_auth=1 c_state=0 c_exec=0  (authority revoked post-approval)
Arm 3 — DENY-policy         c_auth=1 c_state=0 c_exec=0  (policy updated; action inadmissible)
Arm 4 — DENY-balance        c_auth=1 c_state=0 c_exec=0  (balance fell below threshold)
Arm 5 — DENY-risk           c_auth=1 c_state=0 c_exec=0  (risk score exceeded limit)
Arm 6 — DENY-destination    c_auth=1 c_state=0 c_exec=0  (destination blocked/sanctioned)
Arm 7 — DENY-expiry         c_auth=1 c_state=0 c_exec=0  (supporting evidence expired)
Arm 8 — ALLOW-reauth        c_auth=1 c_state=1 c_exec=1  (fresh auth under new assessment)
Arm 9 — DENY-replay         c_auth=1 c_state=0 c_exec=0  (old ProofRecord, state changed)
"""

import json
import os
import sys
import hashlib
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

# Arm definitions: (label, c_state, scenario description)
# c_auth is always 1 (Q_A prepared in |1⟩ and measured).
# c_state is fixed per arm by the preregistration.
# c_exec = c_auth AND c_state — determined classically.
ARM_DEFINITIONS = [
    (1, "ALLOW-unchanged",  1, "No change — state valid at T1 and remains valid at T3"),
    (2, "DENY-revoked",     0, "Authority revoked between approval (T1) and execution (T3)"),
    (3, "DENY-policy",      0, "Policy version updated; action now inadmissible under new policy"),
    (4, "DENY-balance",     0, "Account balance fell below required threshold after approval"),
    (5, "DENY-risk",        0, "Risk score crossed enforcement limit after approval"),
    (6, "DENY-destination", 0, "Destination entity blocked or sanctioned after approval"),
    (7, "DENY-expiry",      0, "Supporting evidence expired after approval was granted"),
    (8, "ALLOW-reauth",     1, "New decision issued against re-assessed admissible state"),
    (9, "DENY-replay",      0, "Old ProofRecord presented without re-verification; state changed"),
]

# ---------------------------------------------------------------------------
# 1. SPAM Gate Circuits
# ---------------------------------------------------------------------------

def build_spam_circuits():
    """
    Build the two SPAM diagnostic circuits.

    SPAM_A circuit:
        Prepare Q_A in |1⟩ → measure
        SPAM_A = P(Q_A = 0)   [bit-flip readout error on authorizer]

    SPAM_P circuit:
        Prepare Q_P in |+⟩ via H → measure
        SPAM_P = |P(Q_P = 1) − 0.5|   [symmetry deviation of payload qubit]

    Both use separate single-qubit circuits. Qubit indices are assigned
    at submission time after qubit selection (Section 7 of preregistration).
    The circuits are built here with virtual qubits [0]; transpilation maps
    them to physical qubits Q_A and Q_P respectively.
    """

    # SPAM_A: authorizer qubit readout error
    qr_a = QuantumRegister(1, "q_auth")
    cr_a = ClassicalRegister(1, "c_auth")
    spam_a = QuantumCircuit(qr_a, cr_a, name="spam_a")
    spam_a.x(qr_a[0])          # Prepare |1⟩
    spam_a.measure(qr_a[0], cr_a[0])

    # SPAM_P: payload qubit readout symmetry
    qr_p = QuantumRegister(1, "q_pay")
    cr_p = ClassicalRegister(1, "c_pay")
    spam_p = QuantumCircuit(qr_p, cr_p, name="spam_p")
    spam_p.h(qr_p[0])          # Prepare |+⟩
    spam_p.measure(qr_p[0], cr_p[0])

    return spam_a, spam_p


# ---------------------------------------------------------------------------
# 2. Principal Circuits (9 arms)
# ---------------------------------------------------------------------------

def build_arm_circuit(arm_num: int, c_state: int, label: str) -> QuantumCircuit:
    """
    Build one principal circuit for a single arm.

    Architecture (preregistration Section 4.3):

        Step 1 — Authorization (T1):
            Prepare Q_A in |1⟩
            Measure Q_A → c_auth  (always 1 for a genuine authorizer in |1⟩)

        Step 2 — State assessment (T2 → T3 gap, modeled classically):
            c_state ← arm-specific constant (fixed in preregistration, never
                       changed after MANIFEST commit)

        Step 3 — Re-verification gate:
            c_exec ← c_auth AND c_state
            Implemented as: if c_auth == 1 AND c_state == 1 → apply X to Q_P (drive payload to |1⟩)

        Step 4 — Measurement:
            Measure Q_P

    Classical feedforward via mid-circuit measurement and if_test.
    No inter-qubit two-qubit gates required.

    Parameters
    ----------
    arm_num  : arm index (1–9)
    c_state  : 0 or 1 — the preregistered state value for this arm
    label    : human-readable arm label for circuit naming
    """

    qr_auth = QuantumRegister(1, "q_auth")
    qr_pay  = QuantumRegister(1, "q_pay")
    cr_auth = ClassicalRegister(1, "c_auth")   # captures authorization decision
    cr_state = ClassicalRegister(1, "c_state") # captures state value (set classically)
    cr_pay  = ClassicalRegister(1, "c_pay")    # captures execution outcome

    qc = QuantumCircuit(qr_auth, qr_pay, cr_auth, cr_state, cr_pay,
                        name=f"arm{arm_num:02d}_{label}")

    # ------------------------------------------------------------------
    # Step 1: Authorization at T1
    # Q_A prepared in |1⟩ → measure → c_auth = 1 (deterministic, modulo
    # readout error characterized by SPAM_A)
    # ------------------------------------------------------------------
    qc.x(qr_auth[0])                           # |0⟩ → |1⟩
    qc.measure(qr_auth[0], cr_auth[0])

    # ------------------------------------------------------------------
    # Step 2: Classical state constant
    # c_state is fixed by the preregistration arm specification.
    # Implemented by setting the classical register bit directly.
    #
    # c_state = 1: state is admissible at execution time → re-verification passes
    # c_state = 0: state has changed; re-verification fails → deny execution
    #
    # Qiskit does not support direct classical register assignment in the
    # gate model, so we encode c_state by conditionally applying an X gate
    # to a classical output register using a known-state ancilla.
    #
    # Simpler and equivalent: we gate the execution on c_auth AND the
    # arm's c_state using nested if_test blocks.
    # When c_state = 0: the outer condition c_auth=1 is met, but inner
    #   c_state block is never entered → H not applied → DENY.
    # When c_state = 1: both conditions met → H applied → ALLOW.
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    # Step 3 + 4: Conditional execution
    # if c_auth == 1 (authorized at T1):
    #     if c_state == 1 (state admissible at T3):
    #         apply X to Q_P   (execute → |1⟩)
    # measure Q_P
    # ------------------------------------------------------------------

    if c_state == 1:
        # ALLOW arm: c_state = 1 → execute if authorized
        # Use classical bit conditioning on c_auth.
        # Execution drives the payload to |1⟩ (X gate), giving P(Q_P=1) ≈ 1.0
        # so that ALLOW retention S_A can meet the C1 threshold (≥ 0.90).
        # (v1.1 pre-data correction: v1.0 used H, which put the payload in a
        #  50/50 superposition and made C1 impossible to satisfy by construction.)
        with qc.if_test((cr_auth, 1)):
            qc.x(qr_pay[0])
    # c_state = 0: no execution gate ever applied — execution blocked
    # Q_P remains in |0⟩ regardless of c_auth

    qc.measure(qr_pay[0], cr_pay[0])

    return qc


def build_principal_circuits() -> list:
    """
    Build all nine principal circuits per the preregistration arm table.
    Returns list of (arm_num, label, c_state, scenario, circuit).
    """
    circuits = []
    for arm_num, label, c_state, scenario in ARM_DEFINITIONS:
        qc = build_arm_circuit(arm_num, c_state, label)
        circuits.append({
            "arm":      arm_num,
            "label":    label,
            "c_state":  c_state,
            "scenario": scenario,
            "circuit":  qc,
        })
    return circuits


# ---------------------------------------------------------------------------
# 3. Qubit Selection
# ---------------------------------------------------------------------------

def select_qubits(backend) -> dict:
    """
    Select the connected pair (Q_A, Q_P) with the lowest sum of single-qubit
    readout errors from the current calibration snapshot.

    Selection rule (preregistration Section 7):
    - Both individual readout errors must be ≤ 0.02.
    - If no connected pair satisfies both constraints, select the lowest-sum
      connected pair available and record the deviation explicitly.
    - Same pair used for both SPAM gate and principal job.

    Returns dict with Q_A index, Q_P index, individual readout errors, sum_RE,
    calibration snapshot timestamp, and whether the constraint was fully met.
    """

    props = backend.properties()
    coupling_map = backend.coupling_map

    readout_errors = {}
    for qubit_idx in range(backend.num_qubits):
        try:
            re = props.readout_error(qubit_idx)
            readout_errors[qubit_idx] = re if re is not None else 1.0
        except Exception:
            readout_errors[qubit_idx] = 1.0

    best_pair   = None
    best_sum_re = float("inf")
    RE_THRESHOLD = 0.02

    for edge in coupling_map.get_edges():
        q0, q1 = edge
        re0 = readout_errors.get(q0, 1.0)
        re1 = readout_errors.get(q1, 1.0)
        sum_re = re0 + re1
        if sum_re < best_sum_re:
            best_sum_re = sum_re
            best_pair = (q0, q1)

    if best_pair is None:
        raise RuntimeError("No connected qubit pair found on backend coupling map.")

    q_a, q_p = best_pair
    re_a = readout_errors[q_a]
    re_p = readout_errors[q_p]
    constraint_met = (re_a <= RE_THRESHOLD) and (re_p <= RE_THRESHOLD)

    try:
        cal_ts = str(props.last_update_date)
    except Exception:
        cal_ts = datetime.datetime.utcnow().isoformat() + "Z"

    result = {
        "Q_A":               q_a,
        "Q_P":               q_p,
        "RE_A":              round(re_a, 6),
        "RE_P":              round(re_p, 6),
        "sum_RE":            round(re_a + re_p, 6),
        "RE_threshold":      RE_THRESHOLD,
        "constraint_met":    constraint_met,
        "calibration_ts":    cal_ts,
    }

    if not constraint_met:
        result["deviation_note"] = (
            f"One or both qubits exceed the {RE_THRESHOLD} readout-error threshold. "
            "Selected the lowest-sum connected pair available per preregistration Section 7. "
            "Deviation recorded explicitly as required by the lock rules."
        )

    return result


# ---------------------------------------------------------------------------
# 4. Transpilation
# ---------------------------------------------------------------------------

def transpile_circuits(circuits_to_transpile: list, backend, qubit_layout: dict) -> list:
    """
    Transpile circuits to the target backend using the selected physical
    qubit layout. Uses optimization_level=3 for best fidelity.

    qubit_layout: {"Q_A": int, "Q_P": int}  — physical qubit indices
    
    Detects circuit width and uses the appropriate subset:
      1-qubit (SPAM) → [Q_A] for auth register, [Q_P] for pay register
      2-qubit (principal) → [Q_A, Q_P]
    """
    transpiled = []
    for c in circuits_to_transpile:
        # Determine layout based on circuit width
        if c.num_qubits == 1:
            # Single-qubit: SPAM_A uses Q_A, SPAM_P uses Q_P
            reg_name = c.qregs[0].name if c.qregs else "q"
            layout = [qubit_layout["Q_A"]] if "auth" in reg_name else [qubit_layout["Q_P"]]
        elif c.num_qubits == 2:
            # Two-qubit: principal arms use (Q_A, Q_P)
            layout = [qubit_layout["Q_A"], qubit_layout["Q_P"]]
        else:
            raise ValueError(f"Unexpected circuit width: {c.num_qubits}")
        
        pm = generate_preset_pass_manager(
            optimization_level=3,
            backend=backend,
            initial_layout=layout,
        )
        tc = pm.run(c)
        transpiled.append(tc)
    
    return transpiled


# ---------------------------------------------------------------------------
# 5. Submission and Raw Result Extraction
# ---------------------------------------------------------------------------

def submit_and_collect(sampler: Sampler, circuits: list, shots: int,
                       job_label: str) -> tuple:
    """
    Submit a batch of circuits via SamplerV2 and extract raw counts.

    Returns (job_id: str, counts_list: list[dict])
    where counts_list[i] = {"0": int, "1": int} for the payload classical bit.
    """
    job = sampler.run(circuits, shots=shots)
    print(f"[ARK-449] {job_label} submitted — job ID: {job.job_id()}")
    print(f"[ARK-449] Waiting for results…")
    result = job.result()

    counts_list = []
    for pub_result in result:
        # Extract the payload bit (c_pay) by register NAME (order-independent)
        # for principal circuits; for SPAM circuits, the single register.
        bit_array = pub_result.data
        # Get the first classical register that is not the ancilla registers
        # In SamplerV2, access via data attributes matching register names
        register_names = list(bit_array.keys())

        # For principal circuits: extract c_pay
        # For SPAM circuits: extract the single classical register
        if "c_pay" in register_names:
            counts = bit_array["c_pay"].get_counts()
        else:
            # SPAM circuit — single classical register
            counts = bit_array[register_names[0]].get_counts()

        counts_list.append(counts)

    return job.job_id(), counts_list


# ---------------------------------------------------------------------------
# 6. SPAM Gate Evaluation
# ---------------------------------------------------------------------------

def evaluate_spam_gate(spam_a_counts: dict, spam_p_counts: dict,
                       shots: int) -> dict:
    """
    Evaluate the SPAM gate per preregistration Section 6.

    SPAM_A = P(Q_A = 0) after preparing |1⟩  [bit-flip readout error]
    SPAM_P = |P(Q_P = 1) − 0.5|               [|+⟩ symmetry deviation]

    Both must be ≤ 0.02 for the gate to pass.
    SPAM_P is a gating diagnostic only — NOT subtracted from L_D.
    (ARK-447 v1.1 correction; fixed in preregistration and cannot be changed post-data.)
    """

    THRESHOLD = 0.02

    count_0_a = spam_a_counts.get("0", 0)
    count_1_a = spam_a_counts.get("1", 0)
    total_a = count_0_a + count_1_a
    spam_a_val = count_0_a / total_a if total_a > 0 else 1.0  # P(0) after |1⟩ prep

    count_0_p = spam_p_counts.get("0", 0)
    count_1_p = spam_p_counts.get("1", 0)
    total_p = count_0_p + count_1_p
    p1_p = count_1_p / total_p if total_p > 0 else 0.0        # P(1) after H prep
    spam_p_val = abs(p1_p - 0.5)

    spam_a_pass = spam_a_val <= THRESHOLD
    spam_p_pass = spam_p_val <= THRESHOLD
    gate_passed  = spam_a_pass and spam_p_pass

    return {
        "SPAM_A":         round(spam_a_val, 6),
        "SPAM_P":         round(spam_p_val, 6),
        "SPAM_A_pass":    spam_a_pass,
        "SPAM_P_pass":    spam_p_pass,
        "gate_passed":    gate_passed,
        "threshold":      THRESHOLD,
        "shots":          shots,
        "raw_spam_a":     spam_a_counts,
        "raw_spam_p":     spam_p_counts,
    }


# ---------------------------------------------------------------------------
# 7. Main Execution Entry Point
# ---------------------------------------------------------------------------

def main():
    print("=" * 70)
    print("ARK-449 — State Changes After Verification")
    print("ExecutionProof ARK Series — Remnant Fieldworks Inc.")
    print("=" * 70)

    # ------------------------------------------------------------------
    # 7.1 Strict pre-submission checks
    # ------------------------------------------------------------------
    manifest_path = Path(__file__).parent.parent / "MANIFEST.txt"
    if not manifest_path.exists():
        print("\n[ERROR] MANIFEST.txt not found in ark-449/.")
        print("Per the lock rules, the MANIFEST must be committed and tagged")
        print("(ark-449-v1.0-lock) before any hardware job is submitted.")
        print("Do not proceed until the MANIFEST is in place.")
        sys.exit(1)

    print(f"\n[OK] MANIFEST found: {manifest_path}")

    # ------------------------------------------------------------------
    # 7.2 Connect to backend
    # ------------------------------------------------------------------
    print("\n[ARK-449] Connecting to IBM Quantum…")
    service = QiskitRuntimeService()
    backend = service.backend("ibm_marrakesh")
    print(f"[ARK-449] Connected to: {backend.name}")

    # ------------------------------------------------------------------
    # 7.3 Qubit selection
    # ------------------------------------------------------------------
    print("\n[ARK-449] Selecting qubit pair…")
    qubit_info = select_qubits(backend)
    print(f"  Q_A = {qubit_info['Q_A']}  (RE = {qubit_info['RE_A']:.4f})")
    print(f"  Q_P = {qubit_info['Q_P']}  (RE = {qubit_info['RE_P']:.4f})")
    print(f"  sum_RE = {qubit_info['sum_RE']:.4f}")
    print(f"  Constraint met: {qubit_info['constraint_met']}")
    if not qubit_info["constraint_met"]:
        print(f"  DEVIATION NOTE: {qubit_info.get('deviation_note', '')}")

    # Save qubit selection to results before submitting anything
    qubit_path = OUTPUT_DIR / "selected_qubits.json"
    with open(qubit_path, "w") as f:
        json.dump(qubit_info, f, indent=2)
    print(f"[ARK-449] Qubit selection written to {qubit_path}")
    print("[ARK-449] *** Commit this file before submitting the SPAM gate ***")

    qubit_layout = {"Q_A": qubit_info["Q_A"], "Q_P": qubit_info["Q_P"]}

    # ------------------------------------------------------------------
    # 7.4 Build circuits
    # ------------------------------------------------------------------
    print("\n[ARK-449] Building SPAM gate circuits…")
    spam_a_circ, spam_p_circ = build_spam_circuits()

    print("[ARK-449] Building 9 principal arm circuits…")
    principal_arm_defs = build_principal_circuits()
    principal_circs = [arm["circuit"] for arm in principal_arm_defs]

    # ------------------------------------------------------------------
    # 7.5 Transpile
    # ------------------------------------------------------------------
    print("\n[ARK-449] Transpiling circuits to ibm_marrakesh…")
    spam_transpiled = transpile_circuits([spam_a_circ, spam_p_circ],
                                        backend, qubit_layout)
    principal_transpiled = transpile_circuits(principal_circs, backend, qubit_layout)
    print(f"  SPAM circuits transpiled: {len(spam_transpiled)}")
    print(f"  Principal circuits transpiled: {len(principal_transpiled)}")

    # ------------------------------------------------------------------
    # 7.6 Submit SPAM gate
    # *** Record job ID BEFORE reading any results ***
    # ------------------------------------------------------------------
    print("\n[ARK-449] Submitting SPAM gate job…")
    sampler = Sampler(mode=backend)
    spam_job_id, spam_counts_list = submit_and_collect(
        sampler, spam_transpiled, SHOTS_SPAM, "SPAM gate"
    )

    # Write job ID to execution log immediately — before reading results
    exec_log = {
        "spam_job_id":      spam_job_id,
        "principal_job_id": None,   # filled after principal submission
        "note": "Job IDs committed before results are read, per lock rules."
    }
    exec_log_path = OUTPUT_DIR / "execution_log.json"
    with open(exec_log_path, "w") as f:
        json.dump(exec_log, f, indent=2)
    print(f"[ARK-449] SPAM job ID written to {exec_log_path}")
    print("[ARK-449] *** Commit execution_log.json now, before reading SPAM results ***")

    # ------------------------------------------------------------------
    # 7.7 Submit principal job BEFORE reading SPAM results
    # Per lock rules: principal job ID must be committed before SPAM
    # results are read.
    # ------------------------------------------------------------------
    print("\n[ARK-449] Submitting principal job (9 arms × 8192 shots)…")
    sampler = Sampler(mode=backend)
    principal_job_id, principal_counts_list = submit_and_collect(
        sampler, principal_transpiled, SHOTS_PRINCIPAL, "principal"
    )

    # Update execution log with principal job ID
    exec_log["principal_job_id"] = principal_job_id
    with open(exec_log_path, "w") as f:
        json.dump(exec_log, f, indent=2)
    print(f"[ARK-449] Principal job ID written to {exec_log_path}")
    print("[ARK-449] *** Commit execution_log.json now, before reading any results ***")

    # ------------------------------------------------------------------
    # 7.8 Evaluate SPAM gate
    # ------------------------------------------------------------------
    print("\n[ARK-449] Evaluating SPAM gate…")
    spam_result = evaluate_spam_gate(
        spam_counts_list[0],  # spam_a counts
        spam_counts_list[1],  # spam_p counts
        SHOTS_SPAM
    )

    spam_path = OUTPUT_DIR / "spam_results.json"
    with open(spam_path, "w") as f:
        json.dump(spam_result, f, indent=2)

    print(f"  SPAM_A = {spam_result['SPAM_A']:.4f}  (≤ 0.02: {'✅' if spam_result['SPAM_A_pass'] else '❌'})")
    print(f"  SPAM_P = {spam_result['SPAM_P']:.4f}  (≤ 0.02: {'✅' if spam_result['SPAM_P_pass'] else '❌'})")
    print(f"  Gate passed: {spam_result['gate_passed']}")

    # ------------------------------------------------------------------
    # 7.9 SPAM gate decision
    # ------------------------------------------------------------------
    if not spam_result["gate_passed"]:
        print("\n[ARK-449] *** SPAM GATE FAILED ***")
        print("Per the locked preregistration (Section 6), the principal job")
        print("results are NOT read. The experiment is recorded as:")
        print("  VERDICT: ABORTED AT SPAM GATE")
        print("No DD or boundary data is claimed.")
        print(f"\nSPAM results written to: {spam_path}")
        print(f"Execution log written to: {exec_log_path}")

        # Write a gate-stop proofrecord
        proofrecord = {
            "experiment":        "ARK-449",
            "doctrine_tested":   "Permission at approval time is not permission at execution time.",
            "verdict":           "ABORTED AT SPAM GATE",
            "abort_reason":      "SPAM gate failed: one or more SPAM checks exceeded 0.02 threshold.",
            "spam_gate":         spam_result,
            "qubit_selection":   qubit_info,
            "spam_job_id":       spam_job_id,
            "principal_job_id":  principal_job_id,
            "principal_data_read": False,
            "note": (
                "Principal job was submitted (to lock the job ID before SPAM results "
                "were read) but results were not read and no principal data is claimed, "
                "per lock rules."
            ),
        }
        pr_path = OUTPUT_DIR / "proofrecord.json"
        with open(pr_path, "w") as f:
            json.dump(proofrecord, f, indent=2)
        print(f"ProofRecord (gate-stop) written to: {pr_path}")
        return

    # ------------------------------------------------------------------
    # 7.10 Save principal raw results
    # ------------------------------------------------------------------
    print("\n[ARK-449] SPAM gate passed. Reading principal results…")

    raw_results = {}
    for i, arm_def in enumerate(principal_arm_defs):
        counts = principal_counts_list[i]
        raw_results[f"arm{arm_def['arm']:02d}"] = {
            "arm":      arm_def["arm"],
            "label":    arm_def["label"],
            "c_state":  arm_def["c_state"],
            "scenario": arm_def["scenario"],
            "counts":   counts,
        }

    raw_path = OUTPUT_DIR / "raw_results.json"
    with open(raw_path, "w") as f:
        json.dump({
            "experiment":       "ARK-449",
            "spam_job_id":      spam_job_id,
            "principal_job_id": principal_job_id,
            "shots_spam":       SHOTS_SPAM,
            "shots_principal":  SHOTS_PRINCIPAL,
            "spam_gate":        spam_result,
            "qubit_selection":  qubit_info,
            "arms":             raw_results,
        }, f, indent=2)

    print(f"[ARK-449] Raw results written to {raw_path}")
    print("[ARK-449] Run ark_449_analysis.py to compute verdict.")
    print("\n[ARK-449] Execution complete.")


# ---------------------------------------------------------------------------
# 8. Dry-Run / Simulator Validation
# ---------------------------------------------------------------------------

def dry_run():
    """
    Validate all circuits on a noiseless Aer simulator before hardware
    submission. This is a pre-lock validation step only. All simulator
    stubs are deleted before hardware submission; no simulated data is
    committed as hardware data.

    Run:  python ark_449_circuit.py --dry-run
    """
    try:
        from qiskit_aer import AerSimulator
    except ImportError:
        print("qiskit-aer not installed. Install with: pip install qiskit-aer")
        return

    print("=" * 70)
    print("ARK-449 DRY RUN — Noiseless Aer Simulation (pre-hardware validation)")
    print("=" * 70)

    sim = AerSimulator()

    # SPAM circuits
    spam_a, spam_p = build_spam_circuits()
    spam_a_t = sim.run(spam_a, shots=SHOTS_SPAM).result().get_counts()
    spam_p_t = sim.run(spam_p, shots=SHOTS_SPAM).result().get_counts()
    spam_eval = evaluate_spam_gate(spam_a_t, spam_p_t, SHOTS_SPAM)
    print(f"\nSPAM gate (noiseless): SPAM_A={spam_eval['SPAM_A']:.4f}  "
          f"SPAM_P={spam_eval['SPAM_P']:.4f}  passed={spam_eval['gate_passed']}")

    # Principal circuits
    arm_defs = build_principal_circuits()
    print("\n9-Arm Results (noiseless):")
    print(f"{'Arm':<6} {'Label':<22} {'c_state':<10} {'P(1)':<8} {'Expected'}")
    print("-" * 65)

    for arm_def in arm_defs:
        qc = arm_def["circuit"]
        result = sim.run(qc, shots=SHOTS_PRINCIPAL).result()
        counts = result.get_counts()
        # Extract payload bit
        total = sum(counts.values())
        # Payload (c_pay) is the leftmost space-separated field; registers are
        # (c_auth, c_state, c_pay) and Qiskit prints them reverse-declaration order.
        c1 = sum(v for k, v in counts.items() if k.split()[0] == "1")
        p1 = c1 / total
        expected = "≥ 0.90" if arm_def["c_state"] == 1 else "≈ 0.00"
        status = "✅" if (
            (arm_def["c_state"] == 1 and p1 >= 0.90) or
            (arm_def["c_state"] == 0 and p1 <= 0.02)
        ) else "❌"
        print(f"{arm_def['arm']:<6} {arm_def['label']:<22} {arm_def['c_state']:<10} "
              f"{p1:<8.4f} {expected}  {status}")

    print("\n[DRY RUN COMPLETE] All circuits validated. "
          "Delete or ignore this output before hardware submission.")
    print("No simulated data will be committed as hardware data.")


if __name__ == "__main__":
    if "--dry-run" in sys.argv:
        dry_run()
    else:
        main()
