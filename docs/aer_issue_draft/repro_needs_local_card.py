"""Reproduce the Aer "Kraus is empty" fault, and characterise it.

NOT PUBLISHABLE YET. This file holds no calibration numbers, but it READS a
real IBM calibration card from data/raw through the project's own loaders, so
it only runs on this machine. It must not go into a public issue until we
have checked what IBM's terms allow us to redistribute. That is decision
L-040.

Read only. It imports from engine/ but changes nothing there, writes no file,
and makes no network call.

Usage:
    repro_needs_local_card.py all          every check below, in order
    repro_needs_local_card.py fail         just show the fault
    repro_needs_local_card.py methods      the fault under each Aer method
    repro_needs_local_card.py touched      restrict noise to touched qubits
    repro_needs_local_card.py measures     the 6 vs 7 measurement threshold
    repro_needs_local_card.py inspect      look for an empty Kraus in Python
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "engine"))

from collections import Counter                               # noqa: E402

from qiskit import QuantumCircuit, transpile                  # noqa: E402
from qiskit_aer import AerSimulator                           # noqa: E402
from qiskit_aer.noise import NoiseModel                       # noqa: E402

import circuits as C                                          # noqa: E402
import real_data as rd                                        # noqa: E402
import run_engine as R                                        # noqa: E402
import snapshot as team_snapshot                              # noqa: E402

MACHINE = "ibm_marrakesh"
TRUTH_STATE = 237            # 233 fails the same way
CIRCUIT = "bv10"
LAYOUT = [109, 118, 123, 124, 125, 126, 127, 128, 129, 136]
SHOTS = 20
SEED_SIM = 3
SEED_TRANSPILE = 11


def setup():
    store = rd.open_store(MACHINE)
    base = rd.load_base_target(MACHINE)[0]
    target, _ = rd.truth_target(store.snapshot(TRUTH_STATE), base,
                                R.permanent_defects(store))
    isa = transpile(C.build(CIRCUIT), target=target, optimization_level=2,
                    seed_transpiler=SEED_TRANSPILE, initial_layout=LAYOUT)
    return target, team_snapshot.noise_model(target), isa


def attempt(noise, circuit, label):
    """Run once and say what happened.

    Aer does NOT raise on this fault: it returns a result with success False.
    Checking only for an exception gives a false pass, which cost me an hour.
    """
    sim = AerSimulator(noise_model=noise, max_parallel_threads=1)
    try:
        res = sim.run(circuit, shots=SHOTS, seed_simulator=SEED_SIM).result()
    except Exception as exc:
        print(f"  {label:<34} RAISED  {str(exc)[:46]}")
        return False
    if res.success:
        print(f"  {label:<34} ran")
        return True
    print(f"  {label:<34} FAILED  {str(res.status)[:46]}")
    return False


def show_fail(target, noise, isa):
    print("1. the fault, as the first simulation in this process")
    attempt(noise, isa, "full noise model, full circuit")


def show_methods(target, noise, isa):
    print("2. the fault under each simulation method")
    for method in ("statevector", "matrix_product_state", "density_matrix"):
        sim = AerSimulator(noise_model=noise, max_parallel_threads=1,
                           method=method)
        try:
            res = sim.run(isa, shots=SHOTS, seed_simulator=SEED_SIM).result()
            status = "ran" if res.success else str(res.status)[:46]
        except Exception as exc:
            status = f"RAISED {str(exc)[:40]}"
        print(f"  {method:<34} {status}")


def subset_noise(full, keep):
    """A new NoiseModel holding only entries whose qubits are all in `keep`."""
    nm = NoiseModel(basis_gates=full.basis_gates)
    for name, per_qubits in full._local_quantum_errors.items():
        for qubits, err in per_qubits.items():
            if set(qubits) <= keep:
                nm.add_quantum_error(err, name, list(qubits))
    for qubits, ro in full._local_readout_errors.items():
        if set(qubits) <= keep:
            nm.add_readout_error(ro, list(qubits))
    return nm


def show_touched(target, noise, isa):
    print("3. restricting the noise model to the qubits the circuit touches")
    touched = sorted({isa.find_bit(q).index
                      for inst in isa.data for q in inst.qubits})
    print(f"  the circuit touches {len(touched)} qubits: {touched}")
    attempt(subset_noise(noise, set(touched)), isa, "touched qubits only")
    attempt(noise, isa, "all 156 qubits")
    print("  A circuit's result should not depend on noise attached to "
          "qubits it never uses.")


def show_measures(target, noise, isa):
    print("4. how many measurements it takes")
    n_meas = sum(1 for i in isa.data if i.operation.name == "measure")
    for keep in range(n_meas + 1):
        seen = 0
        qc = QuantumCircuit(*isa.qregs, *isa.cregs)
        for inst in isa.data:
            if inst.operation.name == "measure":
                seen += 1
                if seen > keep:
                    continue
            qc.append(inst)
        attempt(noise, qc, f"keeping {keep} of {n_meas} measurements")


def show_inspect(target, noise, isa):
    print("5. is there an empty Kraus on the Python side?")
    counts, empty, single = Counter(), [], []
    for name, per_qubits in noise._local_quantum_errors.items():
        for qubits, err in per_qubits.items():
            n = len(err.circuits)
            counts[(name, n)] += 1
            if n == 0:
                empty.append((name, qubits))
            elif n == 1:
                single.append((name, qubits))
    total = sum(counts.values())
    print(f"  local quantum errors: {total}")
    print(f"  readout errors:       {len(noise._local_readout_errors)}")
    print(f"  entries with ZERO terms: {empty or 'none'}")
    print("  terms per entry:")
    for key in sorted(counts):
        print(f"    {key[0]:<8} {key[1]:>4} terms  x{counts[key]}")
    qp = target.qubit_properties
    hot = [q for q in range(target.num_qubits)
           if qp[q].t1 and qp[q].t2 and qp[q].t2 > qp[q].t1]
    print(f"  qubits with T2 > T1 (these get a non-Pauli Kraus channel): {hot}")
    print(f"  single term entries, which are the Kraus ones: {len(single)}")


def main():
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    print(f"machine {MACHINE}, truth state {TRUTH_STATE}, circuit {CIRCUIT}")
    print(f"layout {LAYOUT}\n")
    target, noise, isa = setup()
    steps = {"fail": show_fail, "methods": show_methods,
             "touched": show_touched, "measures": show_measures,
             "inspect": show_inspect}
    for name, fn in steps.items():
        if what in ("all", name):
            fn(target, noise, isa)
            print()
    print("NOTE: once the fault fires, later simulations in the SAME process "
          "can fail too.\nRun one step at a time if a result looks wrong.")


main()
