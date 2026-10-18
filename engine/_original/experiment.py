"""M5 + M6 + M7 - Compile, evaluate, record.

For every starting cycle k, delay d and circuit, the circuit is compiled 5 ways
(only the numbers the compiler sees change) and every version is run on the SAME
true device: the noise model of cycle k + d.

  blind     - compiler sees identical numbers for every qubit       (floor)
  stale     - compiler sees snapshot k                               (what happens today)
  trend     - compiler sees a straight-line forecast for k + d       (the email's forecasting idea)
  stability - compiler sees 5-cycle average + 1 x swing              (main method)
  oracle    - compiler sees the true snapshot k + d                  (ceiling; impossible in reality)

Usage:  python experiment.py synthetic       (or: python experiment.py ibm_torino)
Output: results/results_<source>.csv  - one row per (k, delay, circuit, strategy)
"""
import os
import pickle
import sys
import time
from collections import defaultdict

import pandas as pd
from qiskit.quantum_info import hellinger_fidelity
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_aer import AerSimulator

import circuits
import config
import predictors
import snapshot


def load(source):
    folder = os.path.join(config.SNAPSHOT_DIR, source)
    series = snapshot.load_series(folder)
    if source == "synthetic":
        from qiskit_ibm_runtime.fake_provider import FakeTorino
        base = FakeTorino().target
    else:
        with open(os.path.join(folder, "base_target.pkl"), "rb") as f:
            base = pickle.load(f)
    return series, base


def compile_for(circ, target):
    """Qiskit's standard compiler. Its layout step picks qubits using the error numbers in `target`."""
    pm = generate_preset_pass_manager(optimization_level=config.OPT_LEVEL, target=target,
                                      seed_transpiler=config.SEED_TRANSPILE)
    return pm.run(circ)


def run(source):
    t0 = time.time()
    series, base = load(source)
    K, max_d = len(series), max(config.DELAYS)
    starts = list(range(config.WINDOW - 1, K - max_d))
    if not starts:
        sys.exit(f"Need at least {config.WINDOW + max_d} snapshots, found {K}.")
    print(f"{K} snapshots | starting cycles {starts[0]}..{starts[-1]} | delays {config.DELAYS} | circuits {config.CIRCUITS}")

    circs = {name: circuits.build(name) for name in config.CIRCUITS}
    ideals = {name: circuits.ideal_distribution(c) for name, c in circs.items()}
    targets = {}                                          # cycle -> Target, built once

    def true_target(cycle):
        if cycle not in targets:
            targets[cycle] = snapshot.to_target(series[cycle], base)
        return targets[cycle]

    # ---- compile everything, grouped by the true cycle it will be judged on ----
    jobs = defaultdict(list)
    blind_target = snapshot.to_target(snapshot.uniform(series[0]), base)
    blind = {c: compile_for(circs[c], blind_target) for c in circs}
    oracle = {}
    for k in starts:
        history = series[:k + 1]                          # ONLY data up to submission (decision F5)
        stale_t = true_target(k)
        stab_t = snapshot.to_target(predictors.stability(history, None), base)
        stale = {c: compile_for(circs[c], stale_t) for c in circs}
        stab = {c: compile_for(circs[c], stab_t) for c in circs}
        for d in config.DELAYS:
            truth = k + d
            trend_t = snapshot.to_target(predictors.trend(history, d), base)
            for c in circs:
                if (truth, c) not in oracle:
                    oracle[(truth, c)] = compile_for(circs[c], true_target(truth))
                versions = {"blind": blind[c], "stale": stale[c], "trend": compile_for(circs[c], trend_t),
                            "stability": stab[c], "oracle": oracle[(truth, c)]}
                for strategy, isa in versions.items():
                    jobs[truth].append(({"k": k, "delay": d, "circuit": c, "strategy": strategy}, isa))
    print(f"compiled {sum(len(v) for v in jobs.values())} circuit versions in {time.time() - t0:.0f}s")

    # ---- run each group on its true device ----
    rows = []
    for truth in sorted(jobs):
        sim = AerSimulator(noise_model=snapshot.noise_model(true_target(truth)))
        batch = jobs[truth]
        result = sim.run([isa for _, isa in batch], shots=config.SHOTS,
                         seed_simulator=config.SEED_SIM).result()
        for i, (info, isa) in enumerate(batch):
            counts = result.get_counts(i)
            rows.append({**info, "truth_cycle": truth,
                         "fidelity": hellinger_fidelity(ideals[info["circuit"]], counts),
                         "qubits_used": " ".join(map(str, isa.layout.final_index_layout()))})
        print(f"  true cycle {truth}: {len(batch)} runs done ({time.time() - t0:.0f}s)")

    os.makedirs(config.RESULTS_DIR, exist_ok=True)
    out = os.path.join(config.RESULTS_DIR, f"results_{source}.csv")
    pd.DataFrame(rows).to_csv(out, index=False)
    print(f"wrote {len(rows)} rows to {out} in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    run(sys.argv[1] if len(sys.argv) > 1 else "synthetic")
