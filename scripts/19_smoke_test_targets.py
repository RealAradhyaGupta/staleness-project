"""Prove the base targets work, without running any experiment.

For each machine, four steps and nothing more:
  1. load data/targets/<machine>_base_target.pkl
  2. take ONE real calibration state, read its numbers from data/clean per
     amendment A1.1, and write them into the base target using the teammates'
     own snapshot.py logic (snapshot.to_target)
  3. compile ghz5 once, with the team's optimisation level 2
  4. build the Aer noise model once

No circuit is simulated. No regret is measured. No fidelity is produced. This
only answers "does the machinery assemble", which is risk 7 of PROTOCOL.md
section 17.

Run with team_code/.venv (Python 3.12), because qiskit-aer has no build for the
Python 3.13 in the main project venv.
"""
import pickle
import sys
import time
from pathlib import Path

import pandas as pd
import numpy as np

TEAM = Path("team_code/drift_pipeline").resolve()
sys.path.insert(0, str(TEAM))

import qiskit                                          # noqa: E402
import qiskit_aer                                      # noqa: E402
import circuits                                        # noqa: E402  (teammates')
import config                                          # noqa: E402  (teammates')
import snapshot                                        # noqa: E402  (teammates')
from qiskit.transpiler import generate_preset_pass_manager   # noqa: E402

TARGETS = Path("data/targets")
CLEAN = Path("data/clean")

# One real state per machine: the latest state in the window holding all 176
# cz pairs. Chosen before running, written here so the check is reproducible.
STATES = {
    "ibm_fez": "2026-10-12T14:27:19+00:00",
    "ibm_kingston": "2026-10-12T13:09:02+00:00",
    "ibm_marrakesh": "2026-10-12T19:53:05+00:00",
}


def state_to_snapshot(machine, stamp, qubits, pairs):
    """Amendment A1.1: states.csv is the index, the numbers live here.
    Join on machine plus snapshot_utc equal to the state's first_seen_utc."""
    q = qubits[(qubits.machine == machine) & (qubits.snapshot_utc == stamp)]
    p = pairs[(pairs.machine == machine) & (pairs.snapshot_utc == stamp)]
    q = q.sort_values("qubit")
    n = int(q.qubit.max()) + 1
    t1 = np.full(n, np.nan)
    t2 = np.full(n, np.nan)
    e1 = np.full(n, np.nan)
    ro = np.full(n, np.nan)
    t1[q.qubit.to_numpy()] = q.t1_us.to_numpy() * 1e-6      # us -> seconds
    t2[q.qubit.to_numpy()] = q.t2_us.to_numpy() * 1e-6
    e1[q.qubit.to_numpy()] = q.sx_error.to_numpy()
    ro[q.qubit.to_numpy()] = q.readout_error.to_numpy()
    e2 = {snapshot.edge_key(int(a), int(b)): float(v)
          for a, b, v in zip(p.qubit_a, p.qubit_b, p.cz_error)}
    return {"source": machine, "cycle": 0, "timestamp": stamp,
            "t1": t1, "t2": t2, "err_1q": e1, "err_ro": ro, "err_2q": e2}, len(q), len(p)


def main():
    print(f"qiskit {qiskit.__version__} | qiskit-aer {qiskit_aer.__version__} "
          f"| python {sys.version.split()[0]}")
    print(f"teammates' modules loaded from {TEAM}")
    print(f"optimisation level {config.OPT_LEVEL}, "
          f"seed_transpiler {config.SEED_TRANSPILE}\n")

    t0 = time.time()
    qubits = pd.read_csv(CLEAN / "qubits.csv")
    pairs = pd.read_csv(CLEAN / "pairs.csv")
    print(f"loaded clean tables: qubits {len(qubits)} rows, "
          f"pairs {len(pairs)} rows, in {time.time()-t0:.1f}s\n")

    ghz5 = circuits.build("ghz5")
    print(f"ghz5 built: {ghz5.num_qubits} qubits, depth {ghz5.depth()}\n")

    ok = {}
    for machine, stamp in STATES.items():
        print(f"=== {machine}  (state first seen {stamp}) ===")
        timings = {}
        try:
            t = time.time()
            with open(TARGETS / f"{machine}_base_target.pkl", "rb") as fh:
                blob = pickle.load(fh)
            base, meta = blob["target"], blob["meta"]
            timings["1 load pickle"] = time.time() - t
            print(f"  1 loaded base target: {base.num_qubits} qubits, "
                  f"{len(base['cz'])} directed cz, built {meta['built_utc'][:19]} "
                  f"with qiskit {meta['qiskit_version']}")

            t = time.time()
            snap, nq, npair = state_to_snapshot(machine, stamp, qubits, pairs)
            target = snapshot.to_target(snap, base)
            timings["2 state -> target"] = time.time() - t
            miss_t1 = int(np.isnan(snap["t1"]).sum())
            miss_t2 = int(np.isnan(snap["t2"]).sum())
            print(f"  2 wrote one real state in: {nq} qubit rows, {npair} cz rows, "
                  f"{miss_t1} missing T1, {miss_t2} missing T2")
            sx_err = target["sx"][(0,)].error
            cz_key = next(iter(target["cz"]))
            print(f"    check: sx error on q0 = {sx_err:.6g} "
                  f"(table says {snap['err_1q'][0]:.6g}), "
                  f"cz{cz_key} error = {target['cz'][cz_key].error:.6g}, "
                  f"duration {target['cz'][cz_key].duration*1e9:.0f} ns")

            t = time.time()
            pm = generate_preset_pass_manager(optimization_level=config.OPT_LEVEL,
                                              target=target,
                                              seed_transpiler=config.SEED_TRANSPILE)
            isa = pm.run(ghz5)
            timings["3 compile ghz5"] = time.time() - t
            layout = isa.layout.final_index_layout()
            print(f"  3 compiled ghz5: depth {isa.depth()}, "
                  f"{isa.size()} ops, qubits chosen {layout}")

            t = time.time()
            nm = snapshot.noise_model(target)
            timings["4 Aer noise model"] = time.time() - t
            print(f"  4 noise model: {len(nm.noise_instructions)} noisy "
                  f"instruction types, {len(nm.noise_qubits)} noisy qubits")

            ok[machine] = True
        except Exception as err:
            ok[machine] = False
            print(f"  FAILED: {type(err).__name__}: {err}")
            raise
        finally:
            for k, v in timings.items():
                print(f"    time {k}: {v:.2f}s")
            print()

    print("=== summary ===")
    for machine in STATES:
        print(f"  {machine:<16} all 4 steps: {'PASS' if ok.get(machine) else 'FAIL'}")
    print(f"\ntotal {time.time()-t0:.1f}s")
    print("No circuit was simulated. No regret was measured. "
          "data/raw was not touched.")


main()
