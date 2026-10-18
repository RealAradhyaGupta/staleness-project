"""The real runner: parallel, restartable, and numerically identical to the pilot.

OURS.

Speed-ups applied, each chosen because it CANNOT change a number:
  1. per machine npz cache instead of re-reading 114 MB of CSV per process
     (prepare_cache.py, float64 throughout)
  2. one Aer noise model per truth state, held in a small LRU, and jobs sorted
     by truth state so the cache almost always hits
  3. identical compiled circuits inside one job are simulated ONCE. Verified
     safe: the same circuit with the same seed on the same simulator returns
     identical counts every time. This is also exactly what sanity check 1
     asserts, so if it were not true the check would fail.
  4. Aer limited to one thread per process. Measured: counts are identical with
     max_parallel_threads=1, and Aer was already effectively single threaded on
     this workload (0.719s with 8 threads, 0.753s with 1).
  5. one process per core

Deliberately NOT applied: batching circuits into one sim.run() call. It is 4 to
16 times faster but the result depends on the circuit's POSITION in the batch
(position 0 matches a single call, position 1 does not), so it would silently
change every number.

Restartable: each worker appends to its own part file and skips any job whose
rows are already there. Kill it and start it again; it picks up where it left.
"""
import argparse
import csv
import os
import sys
import time
from datetime import datetime, timezone
from multiprocessing import Process

import numpy as np
import pandas as pd
from qiskit.quantum_info import hellinger_fidelity
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_aer import AerSimulator

import circuits as circ_mod
import engine_config as cfg
import jobs as jobs_mod
import real_data as rd
import snapshot as team_snapshot
import strategies as strat

# Canonical order, so a job's simulator seed never depends on which subset of
# circuits a particular run happens to ask for.
CIRCUIT_ORDER = ["ghz5", "ghz8", "ghz10", "bv8", "bv10"]
COLUMNS = ["label", "machine", "draw_order", "t_s", "t_r", "delay_h", "circuit",
           "arm", "info_state", "truth_state", "new_states", "cz_age_at_run_h",
           "readout_age_at_run_h", "fidelity", "esp", "qubits_used",
           "dead_qubits_used", "n_forbidden", "job_seed"]


def job_seed_of(job):
    return (cfg.SEED_SIM + job["draw_order"] * 1000 + job["delay_h"] * 10
            + CIRCUIT_ORDER.index(job["circuit"]))


def isa_key(isa):
    """A key that is equal exactly when two compiled circuits are the same."""
    out = []
    for inst in isa.data:
        qs = tuple(isa.find_bit(q).index for q in inst.qubits)
        cs = tuple(isa.find_bit(c).index for c in inst.clbits)
        ps = tuple(repr(p) for p in inst.operation.params)
        out.append((inst.operation.name, qs, cs, ps))
    return tuple(out)


def esp_of(isa, truth_target):
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


def random_connected(adj, n, rng):
    starts = [q for q in adj if adj[q]]
    for _ in range(200):
        cur = {int(rng.choice(starts))}
        while len(cur) < n:
            frontier = sorted({b for a in cur for b in adj.get(a, ())
                               if b not in cur})
            if not frontier:
                break
            cur.add(int(rng.choice(frontier)))
        if len(cur) == n:
            return sorted(cur)
    raise RuntimeError("no connected set of live qubits")


def age_h(snap, field, t_r):
    d = snap["value_dates"].get(field)
    if d is None or d == "" or (isinstance(d, float) and np.isnan(d)):
        return ""
    ts = pd.Timestamp(d)
    if ts.tzinfo is None:
        ts = ts.tz_localize("UTC")
    return round((t_r - ts).total_seconds() / 3600.0, 3)


def done_keys(path):
    if not os.path.exists(path):
        return set()
    try:
        df = pd.read_csv(path)
    except Exception:
        return set()
    if len(df) == 0:
        return set()
    counts = df.groupby(["machine", "draw_order", "delay_h",
                         "circuit"]).size()
    return {k for k, v in counts.items() if v >= len(strat.ARMS)}


def worker(wid, job_list, part_path, label, progress_every):
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    skip = done_keys(part_path)
    todo = [j for j in job_list
            if (j["machine"], j["draw_order"], j["delay_h"], j["circuit"])
            not in skip]
    new_file = not os.path.exists(part_path) or os.path.getsize(part_path) == 0
    fh = open(part_path, "a", newline="")
    w = csv.DictWriter(fh, fieldnames=COLUMNS)
    if new_file:
        w.writeheader()
        fh.flush()
    if not todo:
        print(f"[w{wid}] nothing to do ({len(skip)} already done)", flush=True)
        fh.close()
        return

    stores, bases, perms = {}, {}, {}
    built = {c: circ_mod.build(c) for c in CIRCUIT_ORDER}
    ideals = {c: circ_mod.ideal_distribution(q) for c, q in built.items()}
    nm_cache = {}                      # (machine, truth_state) -> (target, sim)
    t0 = time.time()
    n_sim = 0
    n_saved = 0

    for n, job in enumerate(todo, 1):
        m = job["machine"]
        if m not in stores:
            stores[m] = rd.open_store(m)
            bases[m] = rd.load_base_target(m)[0]
            perms[m] = permanent_defects(stores[m])
        store, base, permanent = stores[m], bases[m], perms[m]

        key = (m, job["truth_state"])
        if key not in nm_cache:
            if len(nm_cache) >= 3:             # small LRU; jobs are sorted
                nm_cache.pop(next(iter(nm_cache)))
            tt, _ = rd.truth_target(store.snapshot(job["truth_state"]),
                                    base, permanent)
            nm_cache[key] = (tt, AerSimulator(
                noise_model=team_snapshot.noise_model(tt),
                max_parallel_threads=1, max_parallel_experiments=1))
        truth_t, sim = nm_cache[key]
        truth_dead = rd.dead_qubits(store.snapshot(job["truth_state"]))
        qc, ideal = built[job["circuit"]], ideals[job["circuit"]]
        seed = job_seed_of(job)
        seen = {}                              # isa_key -> (fidelity, esp)

        def run_isa(isa):
            nonlocal n_sim, n_saved
            k = isa_key(isa)
            if k in seen:
                n_saved += 1
                return seen[k]
            counts = sim.run(isa, shots=cfg.SHOTS,
                             seed_simulator=seed).result().get_counts()
            val = (hellinger_fidelity(ideal, counts), esp_of(isa, truth_t))
            seen[k] = val
            n_sim += 1
            return val

        rows = []
        for arm in strat.ARMS:
            snap = strat.arm_snapshot(arm, store, job["info_state"],
                                      job["truth_state"])
            s_target, forbid, _ = rd.strategy_target(snap, base, permanent)
            if arm == "random":
                rng = np.random.default_rng(cfg.SEED_RANDOM + seed)
                adj = rd.live_coupling(s_target)
                fs, es, used = [], [], set()
                for _ in range(cfg.RANDOM_DRAWS):
                    pick = random_connected(adj, qc.num_qubits, rng)
                    pm = generate_preset_pass_manager(
                        optimization_level=cfg.OPT_LEVEL, target=s_target,
                        seed_transpiler=cfg.SEED_TRANSPILE,
                        initial_layout=pick)
                    isa = pm.run(qc)
                    f, e = run_isa(isa)
                    fs.append(f)
                    es.append(e)
                    used |= set(isa.layout.final_index_layout())
                fid, esp_v, used = float(np.mean(fs)), float(np.mean(es)), sorted(used)
            else:
                pm = generate_preset_pass_manager(
                    optimization_level=cfg.OPT_LEVEL, target=s_target,
                    seed_transpiler=cfg.SEED_TRANSPILE)
                isa = pm.run(qc)
                fid, esp_v = run_isa(isa)
                used = list(isa.layout.final_index_layout())

            bad = sorted(set(used) & set(forbid))
            assert not bad, f"DEAD QUBIT USED by {arm}: {bad}"
            src = snap if arm != "ceiling" else store.snapshot(job["truth_state"])
            rows.append({
                "label": label, "machine": m, "draw_order": job["draw_order"],
                "t_s": job["t_s"].isoformat(), "t_r": job["t_r"].isoformat(),
                "delay_h": job["delay_h"], "circuit": job["circuit"], "arm": arm,
                "info_state": job["info_state"], "truth_state": job["truth_state"],
                "new_states": job["new_states"],
                "cz_age_at_run_h": age_h(src, "err_2q", job["t_r"]),
                "readout_age_at_run_h": age_h(src, "err_ro", job["t_r"]),
                "fidelity": fid, "esp": esp_v,
                "qubits_used": " ".join(map(str, used)),
                "dead_qubits_used": " ".join(map(str, sorted(set(used) & truth_dead))),
                "n_forbidden": len(forbid), "job_seed": seed,
            })
        w.writerows(rows)
        fh.flush()
        if n % progress_every == 0 or n == len(todo):
            el = time.time() - t0
            print(f"[w{wid}] {n}/{len(todo)} jobs, {n_sim} sims, "
                  f"{n_saved} saved by dedup, {el:.0f}s, "
                  f"{el/n:.2f}s/job, eta {(len(todo)-n)*el/n/60:.1f} min",
                  flush=True)
    fh.close()
    print(f"[w{wid}] DONE {len(todo)} jobs, {n_sim} sims, "
          f"{n_saved} saved, {time.time()-t0:.0f}s", flush=True)


def permanent_defects(store, training_only=True):
    perm = None
    for i, t in enumerate(store.times):
        if training_only and not jobs_mod.in_training(t):
            continue
        d = rd.dead_qubits(store.snapshot(i))
        perm = set(d) if perm is None else (perm & d)
    return perm or set()


def build_all_jobs(machines, circuits, delays, days, limit_subs):
    all_subs = jobs_mod.all_submission_times()
    out = []
    for m in machines:
        subs = [s for s in all_subs if s[0] == m]
        if days == "train":
            subs = [s for s in subs if jobs_mod.in_training(s[1])]
        elif days == "test":
            subs = [s for s in subs if not jobs_mod.in_training(s[1])]
        if limit_subs:
            subs = subs[:limit_subs]
        store = rd.open_store(m)
        js, dropped = jobs_mod.build_jobs(store, subs, delays, circuits)
        for j in js:
            j["machine"] = m
        out.extend(js)
        print(f"  {m}: {len(subs)} submissions -> {len(js)} jobs; "
              f"dropped { {k: {kk: vv for kk, vv in v.items() if kk != 'kept'} for k, v in dropped.items()} }")
    out.sort(key=lambda j: (j["machine"], j["truth_state"], j["draw_order"],
                            j["delay_h"], j["circuit"]))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--machines", default="ibm_fez,ibm_kingston,ibm_marrakesh")
    ap.add_argument("--circuits", default=",".join(CIRCUIT_ORDER))
    ap.add_argument("--delays", default=",".join(map(str, cfg.DELAYS_H)))
    ap.add_argument("--days", default="train", choices=["train", "test"])
    ap.add_argument("--limit-subs", type=int, default=0)
    # Measured on this Apple M2 (4 performance + 4 efficiency cores):
    # throughput saturates at about 2.3 simulations per second with 4 to 6
    # workers and gets no better with 8, because the efficiency cores are much
    # slower. Default 6.
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--out", required=True)
    ap.add_argument("--label", default="exploratory")
    ap.add_argument("--progress-every", type=int, default=10)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    if a.days == "test":
        print("!!! TEST DAYS requested. PROTOCOL.md section 10 forbids any "
              "tuning or inspection on these. !!!")
    machines = a.machines.split(",")
    circuits = [c for c in CIRCUIT_ORDER if c in a.circuits.split(",")]
    delays = [int(x) for x in a.delays.split(",")]
    out_dir = rd.ROOT / "outputs" / a.out
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"days={a.days} machines={machines} circuits={circuits} "
          f"delays={delays} workers={a.workers}")
    job_list = build_all_jobs(machines, circuits, delays, a.days, a.limit_subs)
    print(f"total jobs {len(job_list)}, arm rows {len(job_list)*len(strat.ARMS)}, "
          f"simulations at most "
          f"{len(job_list)*(len(strat.ARMS)-1+cfg.RANDOM_DRAWS)}")
    if a.dry_run:
        return

    # Shard by WHOLE (machine, truth state) groups, not by striding over jobs.
    # A noise model costs 1.6 to 3 s and depends only on the truth state, so a
    # strided split made several workers build the SAME one. Whole groups mean
    # each noise model is built exactly once in the entire run, and a worker
    # only ever needs one in memory at a time.
    groups = {}
    for j in job_list:
        groups.setdefault((j["machine"], j["truth_state"]), []).append(j)
    keys = sorted(groups)
    shards = [[] for _ in range(a.workers)]
    for i, k in enumerate(keys):
        shards[i % a.workers].extend(groups[k])
    print(f"{len(keys)} distinct (machine, truth state) groups -> "
          f"{a.workers} workers; each noise model is built once")
    procs = []
    t0 = time.time()
    for i, sh in enumerate(shards):
        if not sh:
            continue
        p = Process(target=worker,
                    args=(i, sh, str(out_dir / f"part_{i:02d}.csv"),
                          a.label, a.progress_every))
        p.start()
        procs.append(p)
    for p in procs:
        p.join()
    print(f"\nall workers finished in {time.time()-t0:.0f}s")

    parts = sorted(out_dir.glob("part_*.csv"))
    df = pd.concat([pd.read_csv(p) for p in parts], ignore_index=True)
    merged = out_dir / "all_rows.csv"
    df.sort_values(["machine", "draw_order", "delay_h", "circuit", "arm"],
                   inplace=True)
    df.to_csv(merged, index=False)
    print(f"merged {len(parts)} parts -> {merged} ({len(df)} rows)")


if __name__ == "__main__":
    main()
