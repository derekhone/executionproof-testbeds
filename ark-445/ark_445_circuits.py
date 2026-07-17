"""
ARK-445 — Circuit definitions (10 arms)
Tri-State Authorization Discrimination (ALLOW / HOLD / DENY)
Remnant Fieldworks Inc. — Derek Hone

Each arm is a two-qubit dynamic circuit on IBM Heron (basis gates: cz, id, rz, sx, x).
  - Virtual qubit 0 = Q_A  (authorizer)
  - Virtual qubit 1 = Q_P  (payload; PRIMARY endpoint)
These map to the ARK-445 rule-selected physical qubits on ibm_marrakesh
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

CONTROL-FLOW PATTERN (ARK-443/444 lesson): IBM Qiskit Runtime does NOT support NESTED
if_test (job errors with code 1524). It DOES support a single-register if_test block.
ARK-445 uses ONE flat conditional per arm: `with qc.if_test((ca, 1)): qc.x(Q_P)`.
Mid-circuit `reset` at top level (never inside a conditional) IS supported and is used by
the confusion/replay arm.

This is a metrological characterization of a tri-state authorization rule on this
hardware, NOT new physics (superposition -> probabilistic measurement is textbook QM)
and NOT a cryptographic guarantee. The committed bit is a hardware abstraction of an
approval decision. Findings apply only to the selected qubits/backend at this calibration.

Arms (Field 5.1)
----------------
1  allow_standard      Q_A=X(|1>)             -> ALLOW -> S_A       PRIMARY
2  deny_standard       Q_A=I(|0>)             -> DENY  -> L_D       PRIMARY
3  hold_plus           Q_A=H(|+>)             -> HOLD  -> H_plus    PRIMARY
4  hold_minus          Q_A=X,H(|->)           -> HOLD  -> H_minus   PRIMARY
5  allow_alt           Q_A=X(|1>)             -> ALLOW -> S_A_alt
6  deny_alt            Q_A=I(|0>)             -> DENY  -> L_D_alt
7  allow_reverified    Q_A=X, delay 1us       -> ALLOW -> S_A_rev   (H2b)
8  deny_expired        Q_A=I, delay 1us       -> DENY  -> L_D_exp
9  confusion_replay    Q_A=X, measure->reset->I, then vote read -> DENY -> L_conf (H2c)
10 spam_idle           Q_A=I, Q_P idle (no gate)  -> SPAM baseline
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
    "arm9_confusion_replay",
    "arm10_spam_idle",
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
    "arm9_confusion_replay": "deny",
    "arm10_spam_idle": "idle_spam",
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
    "arm9_confusion_replay": "DENY",
    "arm10_spam_idle": "SPAM",
}


def _new():
    q = QuantumRegister(2, "q")       # q0=Q_A, q1=Q_P
    ca = ClassicalRegister(1, "ca")   # authorization bit from Q_A
    cp = ClassicalRegister(1, "cp")   # payload readout (PRIMARY)
    return q, ca, cp


def _gate(qc, q, ca):
    """Payload fires iff the recorded authorization bit is 1.
    Single-register if_test (no nested conditionals)."""
    with qc.if_test((ca, 1)):
        qc.x(q[1])


def arm1_allow_standard():
    """ALLOW: Q_A prepared |1> -> ca=1 every shot -> X fires -> payload executes.
    S_A = P(Q_P=1). PRIMARY."""
    q, ca, cp = _new()
    qc = QuantumCircuit(q, ca, cp, name="arm1_allow_standard")
    qc.x(q[0]); qc.measure(q[0], ca[0])   # authorizer approves
    _gate(qc, q, ca)
    qc.measure(q[1], cp[0])
    return qc


def arm2_deny_standard():
    """DENY: Q_A prepared |0> -> ca=0 every shot -> no X -> payload withheld.
    L_D = P(Q_P=1). PRIMARY."""
    q, ca, cp = _new()
    qc = QuantumCircuit(q, ca, cp, name="arm2_deny_standard")
    qc.id(q[0]); qc.measure(q[0], ca[0])  # authorizer refuses
    _gate(qc, q, ca)
    qc.measure(q[1], cp[0])
    return qc


def arm3_hold_plus():
    """HOLD: Q_A prepared |+> (H) -> ca collapses 0/1 with ~50% each shot ->
    aggregate P(Q_P=1) ~ 0.50 (intermediate). H_plus. PRIMARY."""
    q, ca, cp = _new()
    qc = QuantumCircuit(q, ca, cp, name="arm3_hold_plus")
    qc.h(q[0]); qc.measure(q[0], ca[0])   # ambiguous authorization (|+>)
    _gate(qc, q, ca)
    qc.measure(q[1], cp[0])
    return qc


def arm4_hold_minus():
    """HOLD: Q_A prepared |-> (X then H) -> ca collapses 0/1 with ~50% each shot ->
    aggregate P(Q_P=1) ~ 0.50. H_minus (basis-independence check vs H_plus). PRIMARY."""
    q, ca, cp = _new()
    qc = QuantumCircuit(q, ca, cp, name="arm4_hold_minus")
    qc.x(q[0]); qc.h(q[0]); qc.measure(q[0], ca[0])   # ambiguous authorization (|->)
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


def arm9_confusion_replay():
    """Confusion/replay -> must collapse to DENY (not HOLD). Q_A prepared |1> and measured
    into a scratch bit (the 'confused' approval), then RESET and re-prepared |0>; the
    authorization bit ca that actually gates the payload is read AFTER the reset (=0), so the
    payload is withheld. A tampered/replayed authorization does not execute. L_conf. (H2c)"""
    q = QuantumRegister(2, "q")
    cscratch = ClassicalRegister(1, "cs")  # discarded confused vote
    ca = ClassicalRegister(1, "ca")        # authoritative vote (post-reset)
    cp = ClassicalRegister(1, "cp")
    qc = QuantumCircuit(q, cscratch, ca, cp, name="arm9_confusion_replay")
    qc.x(q[0]); qc.measure(q[0], cscratch[0])   # confused/replayed approval -> discarded
    qc.barrier(q)
    qc.reset(q[0])                              # top-level reset (supported)
    qc.id(q[0]); qc.measure(q[0], ca[0])        # authoritative vote = 0
    _gate(qc, q, ca)                            # gate reads ca=0 -> DENY
    qc.measure(q[1], cp[0])
    return qc


def arm10_spam_idle():
    """Idle SPAM baseline: Q_A=|0>, Q_P=|0>, no gate. Captures both qubits' idle readout.
    SPAM_A = P(Q_A=1 | idle), SPAM_P = P(Q_P=1 | idle)."""
    q = QuantumRegister(2, "q")
    ca = ClassicalRegister(1, "ca")   # Q_A idle readout
    cp = ClassicalRegister(1, "cp")   # Q_P idle readout
    qc = QuantumCircuit(q, ca, cp, name="arm10_spam_idle")
    qc.id(q[0]); qc.id(q[1])
    qc.measure(q[0], ca[0])
    qc.measure(q[1], cp[0])
    return qc


def build_all_arms():
    """Return all 10 arms in preregistered order as an ordered dict."""
    builders = [
        arm1_allow_standard,
        arm2_deny_standard,
        arm3_hold_plus,
        arm4_hold_minus,
        arm5_allow_alt,
        arm6_deny_alt,
        arm7_allow_reverified,
        arm8_deny_expired,
        arm9_confusion_replay,
        arm10_spam_idle,
    ]
    return {name: b() for name, b in zip(ARM_NAMES, builders)}


if __name__ == "__main__":
    arms = build_all_arms()
    for name, qc in arms.items():
        print(f"{name}: {qc.num_qubits} qubits, {qc.num_clbits} clbits, depth {qc.depth()} "
              f"expect={ARM_EXPECT.get(name)} class={ARM_CLASS.get(name)}")
