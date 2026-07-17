"""
ARK-445b — Circuit definitions (9 arms: reset-free retest)
Tri-State Authorization Discrimination (ALLOW / HOLD / DENY)
Remnant Fieldworks Inc. — Derek Hone

ARK-445b is a diagnostic retest of ARK-445. It runs the identical 8-arm core (arm1–arm8)
under the same strict protocol, omitting the single failing arm (arm9, the mid-circuit
reset + re-prepare confusion/replay path that leaked 0.0289 > the 0.02 DENY ceiling).
The question: was ARK-445's FAIL caused by mid-circuit reset infidelity, or by a flaw
in the tri-state boundary logic itself?

Each arm is a two-qubit dynamic circuit on IBM Heron (basis gates: cz, id, rz, sx, x).
  - Virtual qubit 0 = Q_A  (authorizer)
  - Virtual qubit 1 = Q_P  (payload; PRIMARY endpoint)
These map to the ARK-445b rule-selected physical qubits on ibm_marrakesh
(loaded from selected_qubits.json) via initial_layout=[Q_A, Q_P] at transpile time.

Mechanism under test — a tri-state verify-then-execute (VBE) authorization boundary:
    Authorization phase:  prepare Q_A per its arm ; measure Q_A -> classical bit ca[0]
    Gate:                 if ca == 1:  X(Q_P)          # single-register feedforward
    Payload readout:      measure Q_P -> cp            (PRIMARY endpoint)

There are NO inter-qubit two-qubit gates. The gate is realized purely by CLASSICAL
feedforward on the single measured authorization bit. The payload fires iff the
recorded authorization bit is 1.

The three authorization STATES are encoded in how Q_A is prepared:
  - ALLOW : Q_A = |1>  -> ca collapses to 1 every shot -> X fires -> P=1  (S_A ~ 1.0)
  - DENY  : Q_A = |0>  -> ca collapses to 0 every shot -> no X    -> P=0  (L_D ~ 0.0)
  - HOLD  : Q_A = |+> or |->  -> ca collapses to 0/1 with ~50% each shot ->
            aggregate P(Q_P=1) ~ 0.50 (intermediate, distinct from both basis states)

CONTROL-FLOW PATTERN: IBM Qiskit Runtime does NOT support NESTED if_test (job errors
with code 1524). It DOES support a single-register if_test block. ARK-445b uses ONE
flat conditional per arm: `with qc.if_test((ca, 1)): qc.x(Q_P)`.
**No mid-circuit reset operations in any arm** (this is the key design change from ARK-445).

This is a metrological characterization of a tri-state authorization rule on this
hardware, NOT new physics (superposition -> probabilistic measurement is textbook QM)
and NOT a cryptographic guarantee. The committed bit is a hardware abstraction of an
approval decision. Findings apply only to the selected qubits/backend at this calibration.

Arms (Field 5.1, 8 core arms + 1 SPAM baseline)
------------------------------------------------
1  allow_standard      Q_A=X(|1>)             -> ALLOW -> S_A       PRIMARY
2  deny_standard       Q_A=I(|0>)             -> DENY  -> L_D       PRIMARY
3  hold_plus           Q_A=H(|+>)             -> HOLD  -> H_plus    PRIMARY
4  hold_minus          Q_A=X,H(|->)           -> HOLD  -> H_minus   PRIMARY
5  allow_alt           Q_A=X(|1>)             -> ALLOW -> S_A_alt
6  deny_alt            Q_A=I(|0>)             -> DENY  -> L_D_alt
7  allow_reverified    Q_A=X, delay 1us       -> ALLOW -> S_A_rev   (H2b)
8  deny_expired        Q_A=I, delay 1us       -> DENY  -> L_D_exp
9  spam_idle           Q_A=I, Q_P idle (no gate)  -> SPAM baseline

**OMITTED (ARK-445 arm9):** confusion_replay (mid-circuit reset + re-prepare) — the
single failing arm in ARK-445, omitted to isolate the reset variable.
"""

import os as _os
import json as _json

from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit.circuit import Delay

_SEL = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "selected_qubits.json")
with open(_SEL) as _f:
    _sel = _json.load(_f)
PHYSICAL_QA = _sel["Q_A"]
PHYSICAL_QP = _sel["Q_P"]
# Virtual q[0]=Q_A, q[1]=Q_P
INITIAL_LAYOUT = [PHYSICAL_QA, PHYSICAL_QP]

# 1 microsecond delay used by the reverified-ALLOW and expired-DENY arms.
DELAY_NS = 1000  # 1 us

ARM_NAMES = [
    "arm1_allow_standard",
    "arm2_deny_standard",
    "arm3_hold_plus",
    "arm4_hold_minus",
    "arm5_allow_alt",
    "arm6_deny_alt",
    "arm7_allow_reverified",
    "arm8_deny_expired",
    "arm9_spam_idle",
]

# Expected authorization semantics per arm (for reporting; descriptive only).
ARM_CLASS = {
    "arm1_allow_standard": "allow",
    "arm2_deny_standard": "deny",
    "arm3_hold_plus": "hold",
    "arm4_hold_minus": "hold",
    "arm5_allow_alt": "allow",
    "arm6_deny_alt": "deny",
    "arm7_allow_reverified": "allow",
    "arm8_deny_expired": "deny",
    "arm9_spam_idle": "idle_spam",
}

# Whether each arm is expected to ALLOW (payload fires), DENY (withheld), HOLD, or SPAM.
ARM_EXPECT = {
    "arm1_allow_standard": "ALLOW",
    "arm2_deny_standard": "DENY",
    "arm3_hold_plus": "HOLD",
    "arm4_hold_minus": "HOLD",
    "arm5_allow_alt": "ALLOW",
    "arm6_deny_alt": "DENY",
    "arm7_allow_reverified": "ALLOW",
    "arm8_deny_expired": "DENY",
    "arm9_spam_idle": "SPAM",
}


def _new():
    """Standard 2Q + 2C register setup."""
    q = QuantumRegister(2, "q")
    ca = ClassicalRegister(1, "ca")  # authorizer vote
    cp = ClassicalRegister(1, "cp")  # payload readout (PRIMARY)
    return q, ca, cp


def _gate(qc, q, ca):
    """VBE authorization gate: if Q_A measured |1> (ca==1), execute payload gate X(Q_P).
    This is a FLAT if_test on a single classical register (ca). No nesting."""
    with qc.if_test((ca, 1)):
        qc.x(q[1])  # Q_P = virtual qubit 1


# ── 8 core arms (arm1–arm8) ────────────────────────────────────────────────────


def arm1_allow_standard():
    """ALLOW baseline: Q_A prepared |1> -> payload executes. S_A = P(Q_P=1)."""
    q, ca, cp = _new()
    qc = QuantumCircuit(q, ca, cp, name="arm1_allow_standard")
    qc.x(q[0]); qc.measure(q[0], ca[0])
    _gate(qc, q, ca)
    qc.measure(q[1], cp[0])
    return qc


def arm2_deny_standard():
    """DENY baseline: Q_A prepared |0> -> payload withheld. L_D = P(Q_P=1)."""
    q, ca, cp = _new()
    qc = QuantumCircuit(q, ca, cp, name="arm2_deny_standard")
    qc.id(q[0]); qc.measure(q[0], ca[0])
    _gate(qc, q, ca)
    qc.measure(q[1], cp[0])
    return qc


def arm3_hold_plus():
    """HOLD (|+> superposition): Q_A prepared H|0> = |+> -> ca={0,1} w.p.~0.5 each
    -> payload fires in half the shots. H_plus = P(Q_P=1)."""
    q, ca, cp = _new()
    qc = QuantumCircuit(q, ca, cp, name="arm3_hold_plus")
    qc.h(q[0]); qc.measure(q[0], ca[0])
    _gate(qc, q, ca)
    qc.measure(q[1], cp[0])
    return qc


def arm4_hold_minus():
    """HOLD (|-> superposition): Q_A prepared XH|0> = |-> -> ca={0,1} w.p.~0.5 each.
    H_minus = P(Q_P=1). Should match H_plus (symmetric)."""
    q, ca, cp = _new()
    qc = QuantumCircuit(q, ca, cp, name="arm4_hold_minus")
    qc.x(q[0]); qc.h(q[0]); qc.measure(q[0], ca[0])
    _gate(qc, q, ca)
    qc.measure(q[1], cp[0])
    return qc


def arm5_allow_alt():
    """ALLOW replicate: Q_A prepared |1> -> payload executes. S_A_alt = P(Q_P=1)."""
    q, ca, cp = _new()
    qc = QuantumCircuit(q, ca, cp, name="arm5_allow_alt")
    qc.x(q[0]); qc.measure(q[0], ca[0])
    _gate(qc, q, ca)
    qc.measure(q[1], cp[0])
    return qc


def arm6_deny_alt():
    """DENY replicate: Q_A prepared |0> -> payload withheld. L_D_alt = P(Q_P=1)."""
    q, ca, cp = _new()
    qc = QuantumCircuit(q, ca, cp, name="arm6_deny_alt")
    qc.id(q[0]); qc.measure(q[0], ca[0])
    _gate(qc, q, ca)
    qc.measure(q[1], cp[0])
    return qc


def arm7_allow_reverified():
    """ALLOW with 1us delay before verification: Q_A prepared |1>, idle 1us, then
    measured. Confirms HOLD is a genuine encoding, not a decoherence artifact
    (an approved authorizer that idles then re-verifies still executes). S_A_rev. (H2b)"""
    q, ca, cp = _new()
    qc = QuantumCircuit(q, ca, cp, name="arm7_allow_reverified")
    qc.x(q[0])
    qc.delay(DELAY_NS, q[0], unit="ns")   # idle, then re-verify
    qc.measure(q[0], ca[0])
    _gate(qc, q, ca)
    qc.measure(q[1], cp[0])
    return qc


def arm8_deny_expired():
    """DENY with 1us delay: Q_A prepared |0>, idle 1us, then measured. An expired/idle
    refusal remains a refusal -> payload withheld. L_D_exp = P(Q_P=1)."""
    q, ca, cp = _new()
    qc = QuantumCircuit(q, ca, cp, name="arm8_deny_expired")
    qc.id(q[0])
    qc.delay(DELAY_NS, q[0], unit="ns")
    qc.measure(q[0], ca[0])
    _gate(qc, q, ca)
    qc.measure(q[1], cp[0])
    return qc


# ── SPAM baseline ──────────────────────────────────────────────────────────────


def arm9_spam_idle():
    """Idle SPAM baseline: Q_A=|0>, Q_P=|0>, no gate. Captures both qubits' idle readout.
    SPAM_A = P(Q_A=1 | idle), SPAM_P = P(Q_P=1 | idle)."""
    q = QuantumRegister(2, "q")
    ca = ClassicalRegister(1, "ca")   # Q_A idle readout
    cp = ClassicalRegister(1, "cp")   # Q_P idle readout
    qc = QuantumCircuit(q, ca, cp, name="arm9_spam_idle")
    qc.id(q[0]); qc.id(q[1])
    qc.measure(q[0], ca[0])
    qc.measure(q[1], cp[0])
    return qc


def build_all_arms():
    """Return all 9 arms in preregistered order as an ordered dict."""
    builders = [
        arm1_allow_standard,
        arm2_deny_standard,
        arm3_hold_plus,
        arm4_hold_minus,
        arm5_allow_alt,
        arm6_deny_alt,
        arm7_allow_reverified,
        arm8_deny_expired,
        arm9_spam_idle,
    ]
    return {name: b() for name, b in zip(ARM_NAMES, builders)}


if __name__ == "__main__":
    arms = build_all_arms()
    for name, qc in arms.items():
        print(f"{name}: {qc.num_qubits} qubits, {qc.num_clbits} clbits, depth {qc.depth()} "
              f"expect={ARM_EXPECT.get(name)} class={ARM_CLASS.get(name)}")
