"""PILOT run. Training days only. Exploratory.

OURS. Implements PROTOCOL.md sections 3, 4, 6, 8, 9, 12 and 13 with Amendment
A1, on a deliberately small slice so the machinery can be checked before any
real claim is made.

Pilot slice (fixed by the instruction that asked for it):
    machine   ibm_kingston
    circuits  ghz5, ghz8
    delays    3 and 24 hours
    times     the first 30 submission times in the protocol's draw order
    days      TRAINING ONLY, 28 Aug to 20 Sep. No test day is touched.

Every output file and column is labelled PILOT, exploratory.
"""
import csv
import itertools
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from qiskit.quantum_info import hellinger_fidelity
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_aer import AerSimulator

import circuits as circ_mod
import engine_config as cfg
import jobs as jobs_mod
import real_data as rd
import strategies as strat

OUT = Path(__file__).resolve().parent.parent / "outputs"
MACHINE = "ibm_kingston"
CIRCUITS = ["ghz5", "ghz8"]
DELAYS = [3, 24]
N_SUBMISSIONS = 30


def random_connected(adj, n, rng):
    """A random CONNECTED set of n live qubits, grown by a random walk.

    Connected rather than n qubits picked at random, because a disconnected
    pick would be beaten by routing overhead alone and would make the floor
    look artificially bad. This is still the Huo-style floor: the choice
    ignores every calibration number.
    """
    starts = [q for q in adj if adj[q]]
    for _ in range(200):
        cur = {int(rng.choice(starts))}
        while len(cur) < n:
            frontier = sorted({b for a in cur for b in adj.get(a, ()) if b not in cur})
            if not frontier:
                break
            cur.add(int(rng.choice(frontier)))
        if len(cur) == n:
            return sorted(cur)
    raise RuntimeError("could not find a connected set of live qubits")


def esp(isa, truth_target):
    """Analytic estimated success probability: the product of (1 - error) over
    every gate the compiled circuit actually runs, using TRUTH numbers."""
    p = 1.0
    for inst in isa.data:
        name = inst.operation.name
        if name in ("barrier", "delay"):
            continue
        qargs = tuple(isa.find_bit(q).index for q in inst.qubits)
        try:
            props = truth_target[name].get(qargs)
        except KeyError:
            continue
        if props is None or props.error is None:
            continue
        p *= (1.0 - props.error)
    return p


def main():
    t0 = time.time()
    OUT.mkdir(exist_ok=True)
    print("PILOT, exploratory. Training days only.")
    print(f"seeds: submit {cfg.SEED_SUBMIT}, random {cfg.SEED_RANDOM}, "
          f"transpile {cfg.SEED_TRANSPILE}, sim base {cfg.SEED_SIM}")
    print(f"shots {cfg.SHOTS}, optimisation level {cfg.OPT_LEVEL}, "
          f"window N {cfg.WINDOW_N}")
    print(f"shrinkage placeholder NOT TUNED: N={cfg.SHRINK_N}, w={cfg.SHRINK_W}")
    print(f"dead rule: sx > {cfg.SX_DEAD}, readout > {cfg.RO_DEAD}, "
          f"T1 or T2 missing, or any scored field missing")
    print(f"Aer ceilings used for truth: 1q {cfg.AER_MAX_1Q}, "
          f"2q {cfg.AER_MAX_2Q}\n")

    states, qubits, pairs = rd.load_tables()
    store = rd.StateStore(MACHINE, states, qubits, pairs)
    base, meta = rd.load_base_target(MACHINE)
    print(f"{MACHINE}: {len(store)} states, base target built "
          f"{meta['built_utc'][:19]}")

    # --- permanent defects, TRAINING DAYS ONLY (Amendment A1.5) ---
    train_idx = [i for i, t in enumerate(store.times)
                 if jobs_mod.in_training(t)]
    permanent = None
    for i in train_idx:
        d = rd.dead_qubits(store.snapshot(i))
        permanent = set(d) if permanent is None else (permanent & d)
    permanent = permanent or set()
    print(f"permanent defects from {len(train_idx)} TRAINING states only: "
          f"{sorted(permanent)}")

    # --- jobs ---
    subs = [s for s in jobs_mod.all_submission_times()
            if s[0] == MACHINE and jobs_mod.in_training(s[1])][:N_SUBMISSIONS]
    print(f"submissions taken: {len(subs)}, first {subs[0][1]}, "
          f"last {subs[-1][1]}")
    job_list, dropped = jobs_mod.build_jobs(store, subs, DELAYS, CIRCUITS)
    print(f"jobs after the validity rule: {len(job_list)}")
    for k, v in sorted(dropped.items()):
        print(f"  {k}: kept {v['kept']}, dropped no_history {v['no_history']}, "
              f"no_truth {v['no_truth']}, past_end {v['past_end']}")

    built = {name: circ_mod.build(name) for name in CIRCUITS}
    ideals = {name: circ_mod.ideal_distribution(c) for name, c in built.items()}
    for name, c in built.items():
        print(f"  {name}: {c.num_qubits} qubits, ideal outcomes "
              f"{len(ideals[name])}")

    truth_cache = {}
    clip_total = {}

    def truth_for(idx):
        if idx not in truth_cache:
            t, counter = rd.truth_target(store.snapshot(idx), base, permanent)
            for k, v in counter.items():
                clip_total[k] = clip_total.get(k, 0) + v
            truth_cache[idx] = (t, AerSimulator(noise_model=_noise_model(t)))
        return truth_cache[idx]

    rows = []
    dead_used_total = 0
    n_run = 0
    print("\nrunning...", flush=True)
    for job in job_list:
        truth_t, sim = truth_for(job["truth_state"])
        truth_dead = rd.dead_qubits(store.snapshot(job["truth_state"]))
        qc = built[job["circuit"]]
        ideal = ideals[job["circuit"]]
        # one simulator seed per JOB, shared by every arm (Amendment A1.7)
        job_seed = (cfg.SEED_SIM + job["draw_order"] * 1000
                    + job["delay_h"] * 10 + CIRCUITS.index(job["circuit"]))

        for arm in strat.ARMS:
            snap = strat.arm_snapshot(arm, store, job["info_state"],
                                      job["truth_state"])
            if arm == "ceiling":
                s_target, forbid, _ = rd.strategy_target(snap, base, permanent)
            else:
                s_target, forbid, _ = rd.strategy_target(snap, base, permanent)

            if arm == "random":
                rng = np.random.default_rng(cfg.SEED_RANDOM + job_seed)
                adj = rd.live_coupling(s_target)
                fids, esps, layouts = [], [], []
                for _ in range(cfg.RANDOM_DRAWS):
                    pick = random_connected(adj, qc.num_qubits, rng)
                    pm = generate_preset_pass_manager(
                        optimization_level=cfg.OPT_LEVEL, target=s_target,
                        seed_transpiler=cfg.SEED_TRANSPILE,
                        initial_layout=pick)
                    isa = pm.run(qc)
                    counts = sim.run(isa, shots=cfg.SHOTS,
                                     seed_simulator=job_seed).result().get_counts()
                    fids.append(hellinger_fidelity(ideal, counts))
                    esps.append(esp(isa, truth_t))
                    layouts.append(isa.layout.final_index_layout())
                    n_run += 1
                fid, e = float(np.mean(fids)), float(np.mean(esps))
                used = sorted({q for L in layouts for q in L})
            else:
                pm = generate_preset_pass_manager(
                    optimization_level=cfg.OPT_LEVEL, target=s_target,
                    seed_transpiler=cfg.SEED_TRANSPILE)
                isa = pm.run(qc)
                counts = sim.run(isa, shots=cfg.SHOTS,
                                 seed_simulator=job_seed).result().get_counts()
                fid, e = hellinger_fidelity(ideal, counts), esp(isa, truth_t)
                used = list(isa.layout.final_index_layout())
                n_run += 1

            # PART B2 PROOF: a forbidden qubit must never appear in a layout
            bad = sorted(set(used) & set(forbid))
            assert not bad, (f"DEAD QUBIT USED by {arm}: {bad} "
                             f"(forbidden {sorted(forbid)})")

            dead_now = sorted(set(used) & truth_dead)
            dead_used_total += bool(dead_now)

            age_src = snap if arm != "ceiling" else store.snapshot(job["truth_state"])

            rows.append({
                "label": "PILOT, exploratory",
                "machine": job["machine"], "draw_order": job["draw_order"],
                "t_s": job["t_s"].isoformat(), "t_r": job["t_r"].isoformat(),
                "delay_h": job["delay_h"], "circuit": job["circuit"],
                "arm": arm,
                "info_state": job["info_state"], "truth_state": job["truth_state"],
                "new_states": job["new_states"],
                "cz_age_at_run_h": _age_h(age_src, "err_2q", job["t_r"]),
                "readout_age_at_run_h": _age_h(age_src, "err_ro", job["t_r"]),
                "fidelity": fid, "esp": e,
                "qubits_used": " ".join(map(str, used)),
                "dead_qubits_used": " ".join(map(str, dead_now)),
                "n_forbidden": len(forbid),
                "job_seed": job_seed,
            })
        if len(rows) % 120 == 0:
            print(f"  {len(rows)} rows, {n_run} sims, {time.time()-t0:.0f}s",
                  flush=True)

    out = OUT / "pilot_kingston_PILOT_exploratory.csv"
    with open(out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"\nwrote {out}: {len(rows)} rows, {n_run} simulations, "
          f"{time.time()-t0:.0f}s")
    print(f"clipping and missing-value counts over all truth targets: "
          f"{ {k: v for k, v in clip_total.items() if v} }")
    print(f"jobs where a chosen qubit was dead under TRUTH: {dead_used_total}")
    return out


def _age_h(snap, field, t_r):
    """Age at RUN TIME of the numbers this arm used, from the date printed on
    the value itself. L-016 decision 1 and PROTOCOL.md section 9."""
    d = snap["value_dates"].get(field)
    if d is None or (isinstance(d, float) and np.isnan(d)) or d == "":
        return ""
    ts = pd.Timestamp(d)
    if ts.tzinfo is None:
        ts = ts.tz_localize("UTC")
    return round((t_r - ts).total_seconds() / 3600.0, 3)


def _noise_model(target):
    import snapshot
    return snapshot.noise_model(target)


if __name__ == "__main__":
    main()
