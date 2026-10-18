"""Can T1 and T2 change which qubits the compiler picks? No simulation.

OURS. Asked for by my supervisor before spending any simulation time tuning
w_times (see PROGRESS_LOG.md L-032).

The idea: if changing T1 and T2 never changes the chosen layout, then w_times
cannot affect any strategy's DECISION. T1 and T2 would then reach the result
only through the truth device, which every arm shares, so the weight would be
unobservable and must be fixed at 0.

Three targets per state, identical in every other respect:
  base      the real numbers
  halved    every T1 and T2 divided by 2 (same ranking, worse absolute values)
  shuffled  T1 and T2 permuted across the LIVE qubits (ranking destroyed)

The shuffle is done only among qubits that are not forbidden, and missing
values stay where they are, so the dead qubit set is identical in all three.
That matters: if the forbidden set moved, a layout change would prove nothing.
"""
import sys

import numpy as np
from qiskit.transpiler import generate_preset_pass_manager

import circuits as circ_mod
import engine_config as cfg
import jobs as jobs_mod
import real_data as rd

MACHINES = ["ibm_fez", "ibm_kingston", "ibm_marrakesh"]
CIRCUITS = ["ghz5", "ghz8", "ghz10", "bv8", "bv10"]
N_STATES = 20
SEED_SHUFFLE = 20261014


def variants(snap, forbid, rng):
    halved = dict(snap)
    halved["t1"] = snap["t1"] / 2.0
    halved["t2"] = snap["t2"] / 2.0

    shuffled = dict(snap)
    t1, t2 = snap["t1"].copy(), snap["t2"].copy()
    live = [q for q in range(len(t1))
            if q not in forbid and np.isfinite(t1[q]) and np.isfinite(t2[q])]
    perm = rng.permutation(len(live))
    t1[live] = t1[np.array(live)[perm]]
    t2[live] = t2[np.array(live)[perm]]
    shuffled["t1"], shuffled["t2"] = t1, t2
    return {"halved": halved, "shuffled": shuffled}


def layout_of(snap, base, permanent, qc):
    target, forbid, _ = rd.strategy_target(snap, base, permanent)
    pm = generate_preset_pass_manager(optimization_level=cfg.OPT_LEVEL,
                                      target=target,
                                      seed_transpiler=cfg.SEED_TRANSPILE)
    isa = pm.run(qc)
    return tuple(isa.layout.final_index_layout()), forbid


def main():
    rng = np.random.default_rng(SEED_SHUFFLE)
    built = {c: circ_mod.build(c) for c in CIRCUITS}
    total = 0
    changed = {"halved": 0, "shuffled": 0}
    forbid_mismatch = 0
    examples = []

    for machine in MACHINES:
        store = rd.open_store(machine)
        base, _ = rd.load_base_target(machine)
        train = [i for i, t in enumerate(store.times) if jobs_mod.in_training(t)]
        perm = None
        for i in train:
            d = rd.dead_qubits(store.snapshot(i))
            perm = set(d) if perm is None else (perm & d)
        perm = perm or set()
        idxs = np.linspace(train[cfg.WINDOW_N], train[-1], N_STATES).astype(int)
        print(f"\n{machine}: {len(train)} training states, sampling {len(idxs)}, "
              f"permanent {sorted(perm)}", flush=True)
        for i in idxs:
            snap = store.snapshot(int(i))
            _, forbid0 = layout_of(snap, base, perm, built["ghz5"])
            vs = variants(snap, forbid0, rng)
            for name, alt in vs.items():
                for cname, qc in built.items():
                    lay0, f0 = layout_of(snap, base, perm, qc)
                    lay1, f1 = layout_of(alt, base, perm, qc)
                    if f0 != f1:
                        forbid_mismatch += 1
                        continue
                    total += 1 if name == "halved" else 0
                    if lay0 != lay1:
                        changed[name] += 1
                        if len(examples) < 5:
                            examples.append((machine, int(i), name, cname,
                                             lay0, lay1))

    n_pairs = len(MACHINES) * N_STATES * len(CIRCUITS)
    print("\n" + "=" * 68)
    print("RESULT: does changing T1 and T2 change the chosen layout?")
    print("=" * 68)
    print(f"comparisons per variant: {n_pairs}  "
          f"(3 machines x {N_STATES} states x {len(CIRCUITS)} circuits)")
    print(f"  T1/T2 HALVED   : layout changed in {changed['halved']} of {n_pairs}")
    print(f"  T1/T2 SHUFFLED : layout changed in {changed['shuffled']} of {n_pairs}")
    print(f"  dead qubit set differed (comparison skipped): {forbid_mismatch}")
    for e in examples:
        print(f"    example {e}")
    if changed["halved"] == 0 and changed["shuffled"] == 0:
        print("\nT1 and T2 NEVER changed the compiler's choice of qubits.")
        print("w_times therefore cannot affect any strategy's decision.")
    else:
        print("\nT1 and T2 CAN change the choice. w_times must be tuned.")


if __name__ == "__main__":
    main()
