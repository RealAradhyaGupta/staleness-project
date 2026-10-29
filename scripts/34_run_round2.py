"""Round 2 runner. The frozen rule, the fresh window, run once.

This is Round 1's engine with three differences and nothing else:
  1. the arms come from scripts/30_hybrid_rule.py, not engine/strategies.py
  2. the circuit list gains qft5, qft8 and qft10
  3. the submission window is the fresh one, and the store spans both windows

Every shared piece of numerics is IMPORTED from engine/run_engine.py, not
copied: the compiled-circuit key, the ESP, the value ages, and the restart
logic are the same functions Round 1 used.

Restartable: each worker appends to its own part file and skips any job whose
rows are already there. Kill it and start it again; it carries on.

Permanent defects are the frozen ones in scripts/30_hybrid_rule.py, taken from
development cards only, so no fresh card can change which qubits are removed
for every arm.

Usage:
  python scripts/34_run_round2.py --out round2_pilot --pilot 30 --workers 6
  python scripts/34_run_round2.py --out round2_run --workers 6
"""
import argparse
import csv
import os
import sys
import time
from datetime import timedelta
from multiprocessing import Process
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "engine"))
sys.path.insert(0, str(ROOT / "scripts"))

# The combined store. Set BEFORE real_data is imported anywhere.
os.environ.setdefault("STALENESS_CLEAN_DIR", str(ROOT / "data/clean_r2"))
os.environ.setdefault("STALENESS_CACHE_DIR", str(ROOT / "data/cache_r2"))

import importlib                                            # noqa: E402
import numpy as np                                          # noqa: E402
import pandas as pd                                         # noqa: E402
from qiskit.quantum_info import hellinger_fidelity          # noqa: E402
from qiskit.transpiler import generate_preset_pass_manager  # noqa: E402
from qiskit_aer import AerSimulator                         # noqa: E402

import circuits as circ_mod       # noqa: E402
import engine_config as cfg       # noqa: E402
import jobs as jobs_mod           # noqa: E402
import real_data as rd            # noqa: E402
import run_engine as R1           # noqa: E402  the Round 1 runner, for its helpers
import snapshot as team_snapshot  # noqa: E402

rule = importlib.import_module("30_hybrid_rule")

# ----------------------------------------------------------------- settings

CIRCUIT_ORDER = ["ghz5", "ghz8", "ghz10", "bv8", "bv10",
                 "qft5", "qft8", "qft10"]
FRESH_SUBMIT_START = "2026-10-13"
FRESH_SUBMIT_END = "2026-10-23"    # a 48 h job from 23 Oct runs past the window
                                   # and is dropped by the validity rule
COLUMNS = R1.COLUMNS + ["hybrid_w_readout", "guard_removed"]


def job_seed_of(job):
    """Round 1's formula, with the Round 2 circuit order."""
    return (cfg.SEED_SIM + job["draw_order"] * 1000 + job["delay_h"] * 10
            + CIRCUIT_ORDER.index(job["circuit"]))


def build_all_jobs(machines, circuits, delays, limit_subs=0):
    all_subs = jobs_mod.all_submission_times(FRESH_SUBMIT_START,
                                             FRESH_SUBMIT_END)
    out = []
    for m in machines:
        subs = [s for s in all_subs if s[0] == m]
        if limit_subs:
            subs = subs[:limit_subs]
        store = rd.open_store(m)
        js, dropped = jobs_mod.build_jobs(store, subs, delays, circuits)
        for j in js:
            j["machine"] = m
        out.extend(js)
        trimmed = {k: {kk: vv for kk, vv in v.items() if kk != "kept"}
                   for k, v in dropped.items()}
        print(f"  {m}: {len(subs)} submissions -> {len(js)} jobs; "
              f"dropped {trimmed}", flush=True)
    out.sort(key=lambda j: (j["machine"], j["truth_state"], j["draw_order"],
                            j["delay_h"], j["circuit"]))
    return out


# ------------------------------------------------------------------- worker

def worker(wid, job_list, part_path, label, progress_every):
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    skip = R1.done_keys(part_path) if os.path.exists(part_path) else set()
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

    stores, bases = {}, {}
    built = {c: circ_mod.build(c) for c in CIRCUIT_ORDER}
    ideals = {c: circ_mod.ideal_distribution(q) for c, q in built.items()}
    nm_cache = {}
    t0 = time.time()
    n_sim = n_saved = 0

    for n, job in enumerate(todo, 1):
        m = job["machine"]
        if m not in stores:
            stores[m] = rd.open_store(m)
            bases[m] = rd.load_base_target(m)[0]
        store, base = stores[m], bases[m]
        permanent = rule.permanent(m)

        key = (m, job["truth_state"])
        if key not in nm_cache:
            if len(nm_cache) >= 3:
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
        seen = {}

        def run_isa(isa):
            nonlocal n_sim, n_saved
            k = R1.isa_key(isa)
            if k in seen:
                n_saved += 1
                return seen[k]
            counts = sim.run(isa, shots=cfg.SHOTS,
                             seed_simulator=seed).result().get_counts()
            val = (hellinger_fidelity(ideal, counts), R1.esp_of(isa, truth_t))
            seen[k] = val
            n_sim += 1
            return val

        rows = []
        for arm in rule.ARMS:
            snap = rule.arm_snapshot(arm, store, job["info_state"],
                                     job["truth_state"], job["delay_h"])
            extra = rule.arm_extra_forbid(arm, store, job["info_state"])
            s_target, forbid, _ = rd.strategy_target(snap, base,
                                                     permanent | extra)
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
                "delay_h": job["delay_h"], "circuit": job["circuit"],
                "arm": arm, "info_state": job["info_state"],
                "truth_state": job["truth_state"],
                "new_states": job["new_states"],
                "cz_age_at_run_h": R1.age_h(src, "err_2q", job["t_r"]),
                "readout_age_at_run_h": R1.age_h(src, "err_ro", job["t_r"]),
                "fidelity": fid, "esp": esp_v,
                "qubits_used": " ".join(map(str, used)),
                "dead_qubits_used": " ".join(
                    map(str, sorted(set(used) & truth_dead))),
                "n_forbidden": len(forbid), "job_seed": seed,
                "hybrid_w_readout": snap.get("hybrid_w", {}).get("err_ro", ""),
                "guard_removed": len(extra - set(rd.dead_qubits(snap))
                                     - permanent),
            })
        w.writerows(rows)
        fh.flush()
        if n % progress_every == 0 or n == len(todo):
            el = time.time() - t0
            print(f"[w{wid}] {n}/{len(todo)} jobs, {n_sim} sims, "
                  f"{n_saved} saved by dedup, {el:.0f}s, {el/n:.2f}s/job, "
                  f"eta {(len(todo)-n)*el/n/60:.1f} min", flush=True)
    fh.close()
    print(f"[w{wid}] DONE {len(todo)} jobs, {n_sim} sims, {n_saved} saved, "
          f"{time.time()-t0:.0f}s", flush=True)


# --------------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--machines", default="ibm_fez,ibm_kingston,ibm_marrakesh")
    ap.add_argument("--circuits", default=",".join(CIRCUIT_ORDER))
    ap.add_argument("--delays", default=",".join(map(str, cfg.DELAYS_H)))
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--out", required=True)
    ap.add_argument("--label", default="round2")
    ap.add_argument("--progress-every", type=int, default=25)
    ap.add_argument("--pilot", type=int, default=0,
                    help="keep only this many jobs per circuit, for timing")
    ap.add_argument("--limit-subs", type=int, default=0)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    machines = a.machines.split(",")
    circuits = [c for c in CIRCUIT_ORDER if c in a.circuits.split(",")]
    delays = [int(x) for x in a.delays.split(",")]
    out_dir = ROOT / "outputs" / a.out
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"ROUND 2 RUN  label={a.label}")
    print(f"  store: {rd.CLEAN}  cache: {rd.CACHE_DIR}")
    print(f"  arms: {rule.ARMS}")
    print(f"  circuits: {circuits}")
    print(f"  delays: {delays}   workers: {a.workers}")
    print(f"  submission window: {FRESH_SUBMIT_START} to {FRESH_SUBMIT_END}")
    print(f"  rule cross check: {rule.CHECK_NOTE}")
    for m in machines:
        store = rd.open_store(m)
        print(f"  {m}: {len(store)} states, "
              f"{store.times[0].isoformat()} to {store.times[-1].isoformat()}")

    job_list = build_all_jobs(machines, circuits, delays, a.limit_subs)
    if a.pilot:
        kept, per = [], {}
        for j in job_list:
            if per.get(j["circuit"], 0) < a.pilot:
                kept.append(j)
                per[j["circuit"]] = per.get(j["circuit"], 0) + 1
        job_list = kept
        print(f"  PILOT: {a.pilot} jobs per circuit -> {len(job_list)} jobs")
    print(f"total jobs {len(job_list)}, arm rows "
          f"{len(job_list)*len(rule.ARMS)}, simulations at most "
          f"{len(job_list)*len(rule.ARMS)}")
    if a.dry_run:
        return 0

    groups = {}
    for j in job_list:
        groups.setdefault((j["machine"], j["truth_state"]), []).append(j)
    keys = sorted(groups)
    shards = [[] for _ in range(a.workers)]
    for i, k in enumerate(keys):
        shards[i % a.workers].extend(groups[k])
    print(f"{len(keys)} distinct (machine, truth state) groups -> "
          f"{a.workers} workers; each noise model is built once", flush=True)

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
    elapsed = time.time() - t0
    print(f"\nall workers finished in {elapsed:.0f}s "
          f"({elapsed/3600:.2f} h)", flush=True)
    bad = [p.exitcode for p in procs if p.exitcode != 0]
    if bad:
        print(f"WORKER FAILURES: exit codes {bad}")

    parts = sorted(out_dir.glob("part_*.csv"))
    df = pd.concat([pd.read_csv(p) for p in parts], ignore_index=True)
    merged = out_dir / "all_rows.csv"
    df.sort_values(["machine", "draw_order", "delay_h", "circuit", "arm"],
                   inplace=True)
    df.to_csv(merged, index=False)
    # job counts only. Nothing is aggregated here.
    print(f"merged {len(parts)} parts -> {merged} ({len(df)} rows, "
          f"{len(df)//len(rule.ARMS)} jobs)")
    return 1 if bad else 0


# The __main__ guard is required, not decoration. On macOS multiprocessing uses
# "spawn", so every worker process re-imports this module; without the guard
# each child would run main() again and try to start its own workers, which
# fails with "An attempt has been made to start a new process before the
# current process has finished its bootstrapping phase". engine/run_engine.py
# has the same guard for the same reason.
if __name__ == "__main__":
    sys.exit(main())
