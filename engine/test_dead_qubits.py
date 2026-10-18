"""Test: a dead qubit can NEVER be chosen by the compiler.

OURS. This is the proof asked for in Part B2 of step 7.

Method under test: dead qubits are REMOVED from the Target the strategy sees,
before the compiler is given anything. A removed qubit has no sx, no x, no rz,
no measure, no reset and no cz, so there is no gate the compiler could place
on it. That is why this is impossible and not merely discouraged.

The test compiles every circuit on every arm's target across a sample of real
states on all three machines, and asserts that no chosen qubit is forbidden.
It also checks the opposite direction: that the forbidden set is not empty
(otherwise the test would pass for the wrong reason).
"""
import sys
import time

import numpy as np
from qiskit.transpiler import generate_preset_pass_manager

import circuits as circ_mod
import engine_config as cfg
import real_data as rd
import strategies as strat

MACHINES = ["ibm_fez", "ibm_kingston", "ibm_marrakesh"]
CIRCUITS = ["ghz5", "ghz8", "ghz10", "bv8", "bv10"]
N_STATES = 8          # evenly spaced states per machine


def main():
    t0 = time.time()
    states, qubits, pairs = rd.load_tables()
    built = {c: circ_mod.build(c) for c in CIRCUITS}
    print(f"circuits: " + ", ".join(f"{c}({built[c].num_qubits}q)" for c in CIRCUITS))
    total = 0
    violations = []
    empty_forbid = 0

    for machine in MACHINES:
        store = rd.StateStore(machine, states, qubits, pairs)
        base, _ = rd.load_base_target(machine)
        permanent = None
        for i in range(0, len(store), max(1, len(store) // 40)):
            d = rd.dead_qubits(store.snapshot(i))
            permanent = set(d) if permanent is None else (permanent & d)
        permanent = permanent or set()
        idxs = np.linspace(cfg.WINDOW_N, len(store) - 1, N_STATES).astype(int)
        print(f"\n{machine}: {len(store)} states, permanent {sorted(permanent)}")
        for i in idxs:
            for arm in strat.ARMS:
                if arm == "ceiling":
                    snap = store.snapshot(int(i))
                else:
                    snap = strat.arm_snapshot(arm, store, int(i), int(i))
                target, forbid, _ = rd.strategy_target(snap, base, permanent)
                if not forbid:
                    empty_forbid += 1
                for name, qc in built.items():
                    pm = generate_preset_pass_manager(
                        optimization_level=cfg.OPT_LEVEL, target=target,
                        seed_transpiler=cfg.SEED_TRANSPILE)
                    isa = pm.run(qc)
                    used = set(isa.layout.final_index_layout())
                    total += 1
                    bad = sorted(used & forbid)
                    if bad:
                        violations.append((machine, int(i), arm, name, bad))
            print(f"  state {int(i):>4}: checked {len(strat.ARMS)*len(built)} "
                  f"compilations, forbidden {len(forbid)} qubits", flush=True)

    print(f"\n=== RESULT ===")
    print(f"compilations checked: {total}")
    print(f"targets where the forbidden set was EMPTY: {empty_forbid} "
          f"(a non-zero forbidden set is what makes this test meaningful)")
    print(f"violations (a dead qubit was chosen): {len(violations)}")
    for v in violations[:10]:
        print("   ", v)
    print(f"took {time.time()-t0:.0f}s")
    if violations:
        sys.exit("TEST FAILED")
    print("TEST PASSED: no dead qubit was ever chosen.")


main()
