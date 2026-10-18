"""Part C: tune the per-field shrinkage on TRAINING DAYS ONLY.

OURS. Amendment A1.3 fixes the grid and the metric before any tuning happens:

  metric : the ANALYTIC estimated success probability, not simulation
  grid   : N in {3, 5, 10}
           w in {0, 0.5, 1} for each of three field groups
             readout = readout error
             gate    = sx error and cz error
             times   = T1 and T2
           3 x 3 x 3 x 3 = 81 settings
  tuning on training days only, simulation only for the chosen setting

SELECTION RULE, WRITTEN DOWN BEFORE ANY NUMBER WAS LOOKED AT:
    choose the setting with the LOWEST MEAN ESP REGRET against the ceiling,
    pooled over machines, circuits and delays, on TRAINING days.
    Ties are broken by the SMALLER N. If N also ties, by the smaller total
    weight w_readout + w_gate + w_times, which prefers the simpler rule.

No test day is read anywhere in this file.
"""
import argparse
import itertools
import json
import os
import time
from multiprocessing import Pool

import numpy as np
from qiskit.transpiler import generate_preset_pass_manager

import circuits as circ_mod
import engine_config as cfg
import jobs as jobs_mod
import real_data as rd
import strategies as strat

MACHINES = ["ibm_fez", "ibm_kingston", "ibm_marrakesh"]
CIRCUITS = ["ghz5", "ghz8", "ghz10", "bv8", "bv10"]
GRID_N = [3, 5, 10]
GRID_W = [0.0, 0.5, 1.0]
GROUPS = ["readout", "gate", "times"]


def settings():
    out = []
    for n in GRID_N:
        for wr, wg, wt in itertools.product(GRID_W, repeat=3):
            out.append({"N": n, "readout": wr, "gate": wg, "times": wt})
    return out


def err_map(target):
    """Flatten a Target to {(gate name, qargs): error} so ESP is a cheap lookup."""
    out = {}
    for name in target.operation_names:
        for qargs, props in target[name].items():
            if props is not None and props.error is not None:
                out[(name, qargs)] = props.error
    return out


def esp_from_map(isa, emap):
    p = 1.0
    for inst in isa.data:
        name = inst.operation.name
        if name in ("barrier", "delay"):
            continue
        q = tuple(isa.find_bit(x).index for x in inst.qubits)
        e = emap.get((name, q))
        if e is not None:
            p *= (1.0 - e)
    return p


_CTX = {}


def setup():
    """Per worker: stores, base targets, permanent defects, truth error maps."""
    built = {c: circ_mod.build(c) for c in CIRCUITS}
    for m in MACHINES:
        store = rd.open_store(m)
        base = rd.load_base_target(m)[0]
        perm = None
        for i, t in enumerate(store.times):
            if not jobs_mod.in_training(t):
                continue
            d = rd.dead_qubits(store.snapshot(i))
            perm = set(d) if perm is None else (perm & d)
        _CTX[m] = {"store": store, "base": base, "perm": perm or set(),
                   "emap": {}}
    _CTX["circ"] = built


def truth_emap(m, truth_state):
    c = _CTX[m]
    if truth_state not in c["emap"]:
        tt, _ = rd.truth_target(c["store"].snapshot(truth_state), c["base"],
                                c["perm"])
        c["emap"][truth_state] = err_map(tt)
    return c["emap"][truth_state]


def isa_for(m, snap, circuit):
    c = _CTX[m]
    target, _, _ = rd.strategy_target(snap, c["base"], c["perm"])
    pm = generate_preset_pass_manager(optimization_level=cfg.OPT_LEVEL,
                                      target=target,
                                      seed_transpiler=cfg.SEED_TRANSPILE)
    return pm.run(_CTX["circ"][circuit])


def eval_setting(args):
    idx, setting, job_rows = args
    if not _CTX:
        setup()
    w = {g: setting[g] for g in GROUPS}
    N = setting["N"]
    isa_cache = {}
    regrets = []
    for (m, info, truth, circuit, ceil_esp) in job_rows:
        key = (m, info, circuit)
        if key not in isa_cache:
            snap = strat.predict(_CTX[m]["store"], info, "shrink", n=N,
                                 w_by_group=w)
            isa_cache[key] = isa_for(m, snap, circuit)
        e = esp_from_map(isa_cache[key], truth_emap(m, truth))
        regrets.append(ceil_esp - e)
    return idx, float(np.mean(regrets)), len(regrets)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=os.cpu_count())
    ap.add_argument("--out", default="tuning_training_only.json")
    a = ap.parse_args()

    print("PART C: TUNING. Training days only. Analytic ESP, no simulation.")
    print("Selection rule fixed in advance: lowest mean ESP regret vs the "
          "ceiling; ties to smaller N, then to smaller total w.\n")
    setup()
    t0 = time.time()

    # ---- build the training job list and the ceiling ESP for each job ----
    all_subs = jobs_mod.all_submission_times()
    job_rows = []
    ceil_cache = {}
    for m in MACHINES:
        store = _CTX[m]["store"]
        subs = [s for s in all_subs if s[0] == m and jobs_mod.in_training(s[1])]
        js, dropped = jobs_mod.build_jobs(store, subs, cfg.DELAYS_H, CIRCUITS)
        for j in js:
            key = (m, j["truth_state"], j["circuit"])
            if key not in ceil_cache:
                snap = store.snapshot(j["truth_state"])
                isa = isa_for(m, snap, j["circuit"])
                ceil_cache[key] = esp_from_map(isa, truth_emap(m, j["truth_state"]))
            job_rows.append((m, j["info_state"], j["truth_state"],
                             j["circuit"], ceil_cache[key]))
        print(f"  {m}: {len(subs)} submissions -> {len(js)} training jobs")
    print(f"training jobs total: {len(job_rows)}, ceiling ESPs cached: "
          f"{len(ceil_cache)}, prep {time.time()-t0:.0f}s\n")

    grid = settings()
    print(f"grid: {len(grid)} settings, {a.workers} workers")
    tasks = [(i, s, job_rows) for i, s in enumerate(grid)]
    results = {}
    with Pool(a.workers, initializer=setup) as pool:
        for n, (idx, mean_regret, cnt) in enumerate(
                pool.imap_unordered(eval_setting, tasks), 1):
            results[idx] = mean_regret
            if n % 9 == 0:
                print(f"  {n}/{len(grid)} settings, {time.time()-t0:.0f}s",
                      flush=True)

    rows = []
    for i, s in enumerate(grid):
        rows.append({**s, "mean_esp_regret": results[i]})
    rows.sort(key=lambda r: (r["mean_esp_regret"], r["N"],
                             r["readout"] + r["gate"] + r["times"]))

    print("\n=== top 10 settings by the pre-registered rule ===")
    print(f"{'rank':>4} {'N':>3} {'w_readout':>10} {'w_gate':>7} {'w_times':>8} "
          f"{'mean ESP regret':>16}")
    for i, r in enumerate(rows[:10], 1):
        print(f"{i:>4} {r['N']:>3} {r['readout']:>10.1f} {r['gate']:>7.1f} "
              f"{r['times']:>8.1f} {r['mean_esp_regret']:>16.6f}")
    print("\n=== worst 3 ===")
    for r in rows[-3:]:
        print(f"     N={r['N']} w=({r['readout']},{r['gate']},{r['times']}) "
              f"{r['mean_esp_regret']:.6f}")

    best = rows[0]
    base_line = [r for r in rows if r["readout"] == 0 and r["gate"] == 0
                 and r["times"] == 0]
    print(f"\nall-zero weights (which IS the stale rule) sits at mean ESP "
          f"regret {base_line[0]['mean_esp_regret']:.6f}")
    print(f"\nCHOSEN by the rule: N={best['N']}, w_readout={best['readout']}, "
          f"w_gate={best['gate']}, w_times={best['times']}, "
          f"mean ESP regret {best['mean_esp_regret']:.6f}")

    out = rd.ROOT / "outputs" / a.out
    with open(out, "w") as fh:
        json.dump({"label": "TRAINING ONLY, tuning",
                   "rule": "lowest mean ESP regret vs ceiling; ties to smaller "
                           "N, then smaller total w",
                   "n_jobs": len(job_rows), "grid": rows, "chosen": best},
                  fh, indent=1)
    print(f"wrote {out}  ({time.time()-t0:.0f}s total)")


if __name__ == "__main__":
    main()
