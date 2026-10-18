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
"""
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


def build(name):
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
