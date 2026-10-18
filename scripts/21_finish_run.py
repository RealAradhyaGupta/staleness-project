"""Finish the jobs the frozen runner could not finish, with the same numbers.

OURS. Written for L-037, after two of the six workers of the full test run
died on Aer's "Kraus is empty" error and left 335 of 5650 jobs undone.

Why this file is here and not in engine/. engine/ was frozen in L-033 with a
sha256 for every file and I was told not to edit engine code until the run
finished. So this script does not edit anything there: it imports
engine/run_engine.py and uses its own functions for the job list, the
sharding, the seeds, the dead qubit removal, the ESP and the restart logic.
The only thing it adds is one try/except: if a simulation raises "Kraus is
empty", the same simulation is retried in a fresh process
(scripts/_kraus_retry.py), where it is the first simulation and therefore
works. Counts for a simulation that succeeds do not depend on what ran
before it in the process (checked in L-037), so a retried number is the
number the frozen runner would have written.

Modes:
  --verify N    re-run N jobs that are ALREADY done into a scratch file and
                require every row to be byte-identical to the rows on disk.
                Nothing is appended to the real part files.
  --finish      run only the jobs still missing and append them to the same
                part files the runner used.

Usage:
  21_finish_run.py --out test_full --verify 10
  21_finish_run.py --out test_full --finish --workers 6
"""
import argparse
import csv
import json
import os
import pickle
import subprocess
import sys
import tempfile
import time
from multiprocessing import Process
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "engine"))

import numpy as np                                        # noqa: E402
from qiskit.quantum_info import hellinger_fidelity        # noqa: E402
from qiskit.transpiler import generate_preset_pass_manager  # noqa: E402
from qiskit_aer import AerSimulator                       # noqa: E402

import circuits as circ_mod                               # noqa: E402
import engine_config as cfg                               # noqa: E402
import real_data as rd                                    # noqa: E402
import run_engine as R                                    # noqa: E402
import snapshot as team_snapshot                          # noqa: E402
import strategies as strat                                # noqa: E402

PY_BIN = str(ROOT / "team_code" / ".venv" / "bin" / "python")


class Unsimulatable(Exception):
    """Aer cannot run this circuit on this noise model, in any process.

    Found while finishing the test run: with more than one Aer thread the
    same input segfaults, so this is a memory fault inside Aer 0.17.2, not a
    property of our data. A job that hits it is skipped whole. No row is
    written for it, so no arm gets an average over fewer draws than the
    others, and nothing is invented.
    """
RETRY = str(ROOT / "scripts" / "_kraus_retry.py")


def shards_for(machines, circuits, delays, days, workers):
    """Exactly the split the runner used, so part files keep their meaning."""
    job_list = R.build_all_jobs(machines, circuits, delays, days, 0)
    groups = {}
    for j in job_list:
        groups.setdefault((j["machine"], j["truth_state"]), []).append(j)
    keys = sorted(groups)
    shards = [[] for _ in range(workers)]
    for i, k in enumerate(keys):
        shards[i % workers].extend(groups[k])
    return job_list, shards


def retry_in_fresh_process(isa, seed, machine, truth_state):
    with tempfile.NamedTemporaryFile(suffix=".pkl", delete=False) as fh:
        fh.write(pickle.dumps({"isa": isa, "seed": seed, "machine": machine,
                               "truth_state": truth_state,
                               "shots": cfg.SHOTS}))
        path = fh.name
    try:
        out = subprocess.run([PY_BIN, RETRY, path], capture_output=True,
                             text=True)
        if out.returncode != 0:
            return None
        return json.loads(out.stdout)
    finally:
        os.unlink(path)


def do_jobs(wid, todo, part_path, label, progress_every, retry_log):
    """The runner's per job loop, with one added retry. Rows are identical."""
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    new_file = not os.path.exists(part_path) or os.path.getsize(part_path) == 0
    fh = open(part_path, "a", newline="")
    w = csv.DictWriter(fh, fieldnames=R.COLUMNS)
    if new_file:
        w.writeheader()
        fh.flush()

    stores, bases, perms = {}, {}, {}
    built = {c: circ_mod.build(c) for c in R.CIRCUIT_ORDER}
    ideals = {c: circ_mod.ideal_distribution(q) for c, q in built.items()}
    nm_cache = {}
    t0, n_sim, n_saved, n_retry, n_skip = time.time(), 0, 0, 0, 0
    skip_log = retry_log.replace('_retries.log', '_skipped.log')

    for n, job in enumerate(todo, 1):
        m = job["machine"]
        if m not in stores:
            stores[m] = rd.open_store(m)
            bases[m] = rd.load_base_target(m)[0]
            perms[m] = R.permanent_defects(stores[m])
        store, base, permanent = stores[m], bases[m], perms[m]

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
        seed = R.job_seed_of(job)
        seen = {}

        def run_isa(isa):
            nonlocal n_sim, n_saved, n_retry
            k = R.isa_key(isa)
            if k in seen:
                n_saved += 1
                return seen[k]
            try:
                counts = sim.run(isa, shots=cfg.SHOTS,
                                 seed_simulator=seed).result().get_counts()
            except Exception as exc:
                if "Kraus is empty" not in str(exc):
                    raise
                counts = retry_in_fresh_process(isa, seed, m,
                                                job["truth_state"])
                if counts is None:
                    raise Unsimulatable(
                        f"{m} truth_state={job['truth_state']} "
                        f"draw={job['draw_order']} D={job['delay_h']} "
                        f"circuit={job['circuit']}")
                n_retry += 1
                with open(retry_log, "a") as rl:
                    rl.write(f"{m} truth_state={job['truth_state']} "
                             f"draw={job['draw_order']} D={job['delay_h']} "
                             f"circuit={job['circuit']} seed={seed} "
                             f"retried in a fresh process\n")
            val = (hellinger_fidelity(ideal, counts), R.esp_of(isa, truth_t))
            seen[k] = val
            n_sim += 1
            return val

        rows = []
        try:
            rows = arms_of(job, store, base, permanent, qc, truth_t,
                           truth_dead, seed, run_isa, label, m)
        except Unsimulatable as exc:
            n_skip += 1
            with open(skip_log, "a") as sl:
                sl.write(f"SKIPPED {exc}\n")
            print(f"[f{wid}] SKIPPED job: {exc}", flush=True)
            continue
        w.writerows(rows)
        fh.flush()
        if n % progress_every == 0 or n == len(todo):
            el = time.time() - t0
            print(f"[f{wid}] {n}/{len(todo)} jobs, {n_sim} sims, "
                  f"{n_saved} saved, {n_retry} retried, "
                  f"{n_skip} skipped, {el:.0f}s, "
                  f"eta {(len(todo)-n)*el/n/60:.1f} min", flush=True)
    fh.close()
    print(f"[f{wid}] DONE {len(todo)} jobs, {n_sim} sims, {n_retry} retried, "
          f"{n_skip} skipped, {time.time()-t0:.0f}s", flush=True)



def arms_of(job, store, base, permanent, qc, truth_t, truth_dead, seed,
            run_isa, label, m):
    """The runner's arm loop, lifted out word for word so that a job that
    Aer cannot simulate can be skipped whole instead of writing part of it.
    """
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
                pick = R.random_connected(adj, qc.num_qubits, rng)
                pm = generate_preset_pass_manager(
                    optimization_level=cfg.OPT_LEVEL, target=s_target,
                    seed_transpiler=cfg.SEED_TRANSPILE,
                    initial_layout=pick)
                isa = pm.run(qc)
                f, e = run_isa(isa)
                fs.append(f)
                es.append(e)
                used |= set(isa.layout.final_index_layout())
            fid, esp_v, used = (float(np.mean(fs)), float(np.mean(es)),
                                sorted(used))
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
            "delay_h": job["delay_h"], "circuit": job["circuit"],
            "arm": arm, "info_state": job["info_state"],
            "truth_state": job["truth_state"],
            "new_states": job["new_states"],
            "cz_age_at_run_h": R.age_h(src, "err_2q", job["t_r"]),
            "readout_age_at_run_h": R.age_h(src, "err_ro", job["t_r"]),
            "fidelity": fid, "esp": esp_v,
            "qubits_used": " ".join(map(str, used)),
            "dead_qubits_used": " ".join(
                map(str, sorted(set(used) & truth_dead))),
            "n_forbidden": len(forbid), "job_seed": seed,
        })
    return rows


def key_of(job):
    return (job["machine"], job["draw_order"], job["delay_h"], job["circuit"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--days", default="test", choices=["train", "test"])
    ap.add_argument("--label", default="TEST")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--verify", type=int, default=0)
    ap.add_argument("--finish", action="store_true")
    ap.add_argument("--progress-every", type=int, default=10)
    a = ap.parse_args()

    out_dir = ROOT / "outputs" / a.out
    retry_log = str(ROOT / "logs" / f"{a.out}_retries.log")
    machines = ["ibm_fez", "ibm_kingston", "ibm_marrakesh"]
    _, shards = shards_for(machines, R.CIRCUIT_ORDER, cfg.DELAYS_H, a.days,
                           a.workers)

    if a.verify:
        import pandas as pd
        scratch = out_dir / "verify"
        scratch.mkdir(parents=True, exist_ok=True)
        print(f"VERIFY: re-running {a.verify} jobs that are already done, "
              f"per worker, and comparing every row")
        all_ok = True
        for wid, sh in enumerate(shards):
            part = out_dir / f"part_{wid:02d}.csv"
            done = R.done_keys(str(part))
            todo = [j for j in sh if key_of(j) in done][:a.verify]
            if not todo:
                continue
            tgt = scratch / f"check_{wid:02d}.csv"
            if tgt.exists():
                tgt.unlink()
            do_jobs(wid, todo, str(tgt), a.label, a.progress_every, retry_log)
            new = pd.read_csv(tgt)
            old = pd.read_csv(part)
            keys = ["machine", "draw_order", "delay_h", "circuit", "arm"]
            old = old.merge(new[keys], on=keys, how="inner")
            new = new.sort_values(keys).reset_index(drop=True)
            old = old.sort_values(keys).reset_index(drop=True)
            same = len(new) == len(old)
            diffs = []
            if same:
                for c in R.COLUMNS:
                    if c == "label":
                        continue
                    # fillna first. An empty cell reads back as NaN, and NaN
                    # never equals NaN, so a plain comparison reports every
                    # empty cell as a difference. dead_qubits_used is empty on
                    # every row by design, which is exactly that case.
                    a_ = new[c].fillna("").astype(str).values
                    b_ = old[c].fillna("").astype(str).values
                    ne = a_ != b_
                    if ne.any():
                        diffs.append((c, int(ne.sum())))
            print(f"  worker {wid}: {len(new)} rows re-run, "
                  f"{'row counts match' if same else 'ROW COUNT MISMATCH'}, "
                  f"{'byte-identical' if not diffs else f'DIFFERENT {diffs}'}")
            all_ok = all_ok and same and not diffs
        print("VERIFY RESULT:", "identical" if all_ok else "NOT IDENTICAL")
        return

    if not a.finish:
        print("nothing to do: pass --verify N or --finish")
        return

    # Which jobs are still missing. Read every part file in the directory,
    # not just the one a given worker id owns, so this is safe to run again
    # after a stop and so the extra part files written below are counted.
    all_jobs = [j for sh in shards for j in sh]
    done = set()
    for part in sorted(out_dir.glob("part_*.csv")):
        done |= R.done_keys(str(part))
    missing = [j for j in all_jobs if key_of(j) not in done]
    print(f"{len(all_jobs)} jobs in the plan, {len(done)} already done, "
          f"{len(missing)} missing")
    if not missing:
        print("nothing missing")
        return

    # The two dead workers held the missing jobs, so finishing them in their
    # original two shards would leave six cores idle. Split by whole
    # (machine, truth state) groups instead, same rule the runner uses, so
    # each noise model is still built once. Rows do not depend on which
    # process writes them, which is what --verify checked.
    groups = {}
    for j in missing:
        groups.setdefault((j["machine"], j["truth_state"]), []).append(j)
    keys = sorted(groups)
    chunks = [[] for _ in range(a.workers)]
    for i, k in enumerate(keys):
        chunks[i % a.workers].extend(groups[k])
    print(f"{len(keys)} groups -> {a.workers} processes")

    procs = []
    t0 = time.time()
    for i, ch in enumerate(chunks):
        if not ch:
            continue
        part = out_dir / f"part_1{i}.csv"
        print(f"  process {i}: {len(ch)} jobs -> {part.name}")
        p = Process(target=do_jobs,
                    args=(f"1{i}", ch, str(part), a.label, a.progress_every,
                          retry_log))
        p.start()
        procs.append(p)
    for p in procs:
        p.join()
    print(f"finished in {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
