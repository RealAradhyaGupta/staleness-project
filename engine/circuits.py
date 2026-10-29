"""Benchmark circuits (decision D4) and their ideal (noise-free) output distributions.

Chosen because each has a sharp, known answer, so damage from noise is easy to see:
  ghz5 / ghz8 : entangles 5 / 8 qubits in a chain. Ideal output: 50% all-zeros, 50% all-ones.
  bv8         : Bernstein-Vazirani with a 7-bit secret + 1 helper qubit. Ideal output: the secret, 100%.

OURS (added for PROTOCOL.md section 5, which asks for five circuits):
  ghz10       : the same chain on 10 qubits. Uses the generic ghz(n) already here.
  bv10        : Bernstein-Vazirani with a 9-bit secret + 1 helper qubit = 10 qubits.
                The secret 101101101 is fixed so the circuit is reproducible.
Everything else in this file is the teammates' code, unchanged.
Not used: QFT on a blank input. Its ideal output is spread evenly, and noise also
spreads output evenly, so fidelity would barely show the damage.

ADDED FOR ROUND 2 (nothing above this line changed):
  qft5 / qft8  : exact QFT on the 4-peak input state.
  qft10        : the same on 10 qubits, approximate, dropping every controlled
                 rotation smaller than pi/2^3.
The 4-peak input fixes the objection in the paragraph above. A blank input
gives a flat ideal output, which noise cannot damage in a way fidelity can see.
Instead we feed in an even mixture of every integer divisible by 4, which is a
comb of spacing 4. The QFT of a comb of spacing 4 is a comb of spacing N/4, so
the ideal output has EXACTLY four outcomes, at 0, N/4, N/2 and 3N/4, each with
probability 1/4, and nothing else. That is a sharp known answer, like GHZ and
BV. Built by putting an H on every qubit from 2 upward and leaving qubits 0
and 1 alone, because the low two bits of the input are what must stay at zero.
Checked against Qiskit's own QFTGate in the Round 2 freeze tests.
"""
import math

from qiskit import ClassicalRegister, QuantumCircuit
from qiskit.quantum_info import Statevector


def ghz(n):
    qc = QuantumCircuit(n, name=f"ghz{n}")
    qc.h(0)
    for i in range(n - 1):
        qc.cx(i, i + 1)
    qc.measure_all()
    return qc


def bernstein_vazirani(secret="1011011"):
    n = len(secret)
    qc = QuantumCircuit(n + 1, name=f"bv{n + 1}")
    qc.x(n)
    qc.h(range(n + 1))
    for i, bit in enumerate(reversed(secret)):      # qubit 0 holds the rightmost bit
        if bit == "1":
            qc.cx(i, n)
    qc.h(range(n))
    creg = ClassicalRegister(n, "meas")
    qc.add_register(creg)
    qc.measure(range(n), creg)
    return qc


# OURS: fixed secrets, written down so every run builds the same circuit.
BV_SECRETS = {
    "bv8": "1011011",        # theirs, 7 bits + 1 helper
    "bv10": "101101101",     # OURS, 9 bits + 1 helper
}


# OURS, Round 2. Rotations below this angle are dropped in the approximate QFT.
AQFT_MIN_ANGLE = math.pi / 2 ** 3


def qft(n, min_angle=None):
    """Textbook QFT on n qubits. min_angle=None keeps every rotation."""
    qc = QuantumCircuit(n, name="qft" if min_angle is None else "aqft")
    for j in reversed(range(n)):
        qc.h(j)
        for k in range(j):
            ang = math.pi / 2 ** (j - k)
            if min_angle is None or ang >= min_angle - 1e-12:
                qc.cp(ang, k, j)
    for i in range(n // 2):
        qc.swap(i, n - 1 - i)
    return qc


def qft_four_peak(n, min_angle=None):
    """QFT on the 4-peak input. Ideal output: 4 outcomes at 1/4 each."""
    qc = QuantumCircuit(n, name=f"qft{n}" if min_angle is None else f"aqft{n}")
    for q in range(2, n):            # even mixture of every multiple of 4
        qc.h(q)
    qc.compose(qft(n, min_angle), inplace=True)
    qc.measure_all()
    return qc


# OURS, Round 2. Which QFT circuits exist and whether each is approximate.
QFT_SPECS = {
    "qft5": (5, None),                 # exact
    "qft8": (8, None),                 # exact
    "qft10": (10, AQFT_MIN_ANGLE),     # approximate
}


def build(name):
    if name in QFT_SPECS:                       # OURS, Round 2
        n, min_angle = QFT_SPECS[name]
        return qft_four_peak(n, min_angle)
    if name.startswith("ghz"):
        return ghz(int(name[3:]))
    if name in BV_SECRETS:                      # OURS: was `if name == "bv8"`
        return bernstein_vazirani(BV_SECRETS[name])
    raise ValueError(f"unknown circuit {name}")


def ideal_distribution(qc):
    """Exact noise-free output probabilities, computed by simulating the circuit without measurements."""
    measured = []
    for instr in qc.data:
        if instr.operation.name == "measure":
            measured.append(qc.find_bit(instr.qubits[0]).index)
    sv = Statevector(qc.remove_final_measurements(inplace=False))
    probs = sv.probabilities_dict(qargs=measured)
    return {str(k): float(v) for k, v in probs.items() if v > 1e-9}
