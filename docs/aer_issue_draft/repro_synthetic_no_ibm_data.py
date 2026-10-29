"""Attempt to reproduce Aer's "Kraus is empty" from INVENTED numbers only.

PUBLISHABLE. There is not one IBM calibration value in this file. Every T1,
T2, duration and error below is made up by a seeded numpy generator, and the
only things copied from the real device are its SHAPE: 156 qubits, the gate
set, the instruction durations, and the index positions of the 15 qubits that
happen to have T2 > T1.

IT DOES NOT REPRODUCE THE FAULT. It is kept because a failed attempt narrows
the search: the model it builds contains 95 single term Kraus entries, more
than the 18 in the real model that does fail, and it still runs clean. So
"the model contains non-Pauli Kraus channels" is not by itself the trigger.

Usage:  repro_synthetic_no_ibm_data.py [T2_of_qubit_136]
Prints "ok" (no fault) or "FAIL ..." (fault reproduced).
"""
import sys
import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit.circuit import Parameter
from qiskit.circuit.library import CZGate, Measure, Reset, RZGate, SXGate, XGate
from qiskit.providers import BackendV2, Options
from qiskit.transpiler import Target, InstructionProperties, QubitProperties
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel

N = 156
SHORT_T2 = float(sys.argv[1]) if len(sys.argv) > 1 else 1.4e-6
rng = np.random.default_rng(7)

qp = []
for q in range(N):
    t1 = float(rng.uniform(80e-6, 350e-6))
    t2 = float(min(rng.uniform(20e-6, 300e-6), 2 * t1))
    qp.append(QubitProperties(t1=t1, t2=t2, frequency=None))
# one qubit with a T2 far shorter than the measurement duration
qp[136] = QubitProperties(t1=1.44e-4, t2=SHORT_T2, frequency=None)
# 15 qubits with T2 > T1: Aer's thermal_relaxation_error then returns a
# non-Pauli KRAUS channel instead of a Pauli mixture. These are the only
# Kraus-type entries in the real model that fails.
for q in (26, 35, 39, 48, 51, 54, 59, 81, 83, 90, 91, 94, 95, 121, 152):
    t1 = float(rng.uniform(6e-6, 30e-6))
    qp[q] = QubitProperties(t1=t1, t2=float(t1 * 1.2), frequency=None)

t = Target(num_qubits=N, qubit_properties=qp)
D1, DM, DR, D2 = 3.6e-8, 2.684e-6, 2.72e-6, 6.8e-8
live = list(range(N))
for G in (SXGate(), XGate()):
    t.add_instruction(G, {(q,): InstructionProperties(
        duration=D1, error=float(rng.uniform(1e-4, 9e-4))) for q in live})
t.add_instruction(RZGate(Parameter("x")), {(q,): InstructionProperties(
    duration=0.0, error=0.0) for q in live})
t.add_instruction(Measure(), {(q,): InstructionProperties(
    duration=DM, error=float(rng.uniform(3e-3, 6e-2))) for q in live})
t.add_instruction(Reset(), {(q,): InstructionProperties(
    duration=DR, error=0.0) for q in live})
cz = {}
for a in range(N - 1):
    e = float(rng.uniform(1e-3, 8e-3))
    cz[(a, a + 1)] = InstructionProperties(duration=D2, error=e)
    cz[(a + 1, a)] = InstructionProperties(duration=D2, error=e)
for a, b in ((109, 118), (118, 129), (123, 136), (128, 129)):
    e = float(rng.uniform(1e-3, 8e-3))
    cz[(a, b)] = InstructionProperties(duration=D2, error=e)
    cz[(b, a)] = InstructionProperties(duration=D2, error=e)
t.add_instruction(CZGate(), cz)


class B(BackendV2):
    def __init__(s, tg): super().__init__(name="synthetic"); s._t = tg
    @property
    def target(s): return s._t
    @property
    def max_circuits(s): return None
    @classmethod
    def _default_options(cls): return Options()
    def run(s, *a, **k): raise NotImplementedError


nm = NoiseModel.from_backend(B(t))
qc = QuantumCircuit(11, 10)
qc.x(10); qc.h(range(11))
for i, s in enumerate("1011010110"):
    if s == "1":
        qc.cx(i, 10)
qc.h(range(10)); qc.measure(range(10), range(10))
LAY = [109, 118, 123, 124, 125, 126, 127, 128, 129, 136, 135]
isa = transpile(qc, target=t, optimization_level=2, seed_transpiler=11,
                initial_layout=LAY)
sim = AerSimulator(noise_model=nm, max_parallel_threads=1)
try:
    res = sim.run(isa, shots=20, seed_simulator=3).result()
except Exception as e:
    print(f"T2={SHORT_T2:g}  RAISED {str(e)[:70]}"); sys.exit(3)
print(f"T2={SHORT_T2:g}  {'ok' if res.success else 'FAIL ' + str(res.status)[:60]}")
sys.exit(0 if res.success else 3)
