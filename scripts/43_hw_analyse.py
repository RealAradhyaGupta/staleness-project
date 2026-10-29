"""Stage 6, Part A: analyse the hardware jobs. Exactly protocol_hardware.md
section 10, written from that text and frozen with it before any job ran.

Reads outputs/hardware/hw_state.json and outputs/hardware/results/*.json.
Submits nothing. Reads no card. Changes no Round 2 file.

  - Hellinger fidelity of each arm's measured counts against the circuit's
    ideal distribution
  - paired differences per job: window_mean minus stale (primary) and
    hybrid minus stale (secondary). A job whose two arms gave an IDENTICAL
    transpiled circuit contributes exactly 0 and is counted, not dropped.
  - n, mean, SD and a bootstrap 95 percent interval over jobs, 4000 resamples
    of the jobs with replacement, percentile interval, seed 20261025
  - the share of jobs whose layouts differ
  - the same differences by circuit
  - the queue wait distribution: median, range, share under 1 hour
  - the usage of every job, the total, and the cap

Usage:
  python scripts/43_hw_analyse.py
"""
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs/hardware"
RESULTS = OUT / "results"

os.environ.setdefault("STALENESS_CLEAN_DIR", str(ROOT / "data/clean_hw"))
os.environ.setdefault("STALENESS_CACHE_DIR", str(ROOT / "data/cache_hw"))
sys.path.insert(0, str(ROOT / "engine"))

ARMS = ["stale", "window_mean", "hybrid"]
COMPARISONS = [("window_mean", "stale", "PRIMARY"),
               ("hybrid", "stale", "secondary"),
               ("hybrid", "window_mean", "extra")]
N_BOOT = 4000
SEED_BOOT = 20261025
CAP_TOTAL_S = 180.0


def say(*a):
    print(*a, flush=True)


def boot_ci(x, n_boot=N_BOOT, seed=SEED_BOOT):
    """Percentile bootstrap over jobs. The job is the resampling unit because
    the three arms of a job share one queue position and one calibration
    epoch, so they are not independent of each other."""
    x = np.asarray(x, dtype=float)
    if len(x) == 0:
        return float("nan"), float("nan"), float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(x), size=(n_boot, len(x)))
    means = x[idx].mean(axis=1)
    sd = float(x.std(ddof=1)) if len(x) > 1 else float("nan")
    return (float(x.mean()), sd,
            float(np.percentile(means, 2.5)),
            float(np.percentile(means, 97.5)))


def main():
    import circuits as circ_mod
    from qiskit.quantum_info import hellinger_fidelity

    state = json.loads((OUT / "hw_state.json").read_text())
    jobs = state["jobs"]
    say("=" * 72)
    say("STAGE 6 PART A: HARDWARE RESULTS")
    say("=" * 72)
    say(f"  device: {state['device']}")
    say(f"  t0: {state.get('t0_utc')}")
    say(f"  protocol: protocol_hardware.md, frozen in FREEZE_HARDWARE.txt")

    ideals = {c: circ_mod.ideal_distribution(circ_mod.build(c))
              for c in sorted({j["circuit"] for j in jobs.values()
                               if j.get("circuit")})}

    # ------------------------------------------------- per job, per arm rows
    rows = []
    for key in sorted(jobs):
        j = jobs[key]
        if j.get("status") != "DONE":
            continue
        res = json.loads((RESULTS / f"{key}.json").read_text())
        counts = res["counts_per_pub"]
        ideal = ideals[j["circuit"]]
        for arm in ARMS:
            pub = j["arms"][arm]["pub"]
            fid = hellinger_fidelity(ideal, counts[pub])
            rows.append({
                "key": key, "slot": j["slot"], "circuit": j["circuit"],
                "arm": arm, "pub": pub, "fidelity": fid,
                "layout": " ".join(str(q) for q in j["arms"][arm]["layout"]),
                "n_forbidden": j["arms"][arm]["n_forbidden"],
                "job_id": j.get("job_id"),
                "card_utc": j.get("card_utc"),
                "compile_utc": j.get("actual_compile_utc"),
                "submit_utc": j.get("actual_submit_utc"),
                "D_actual_h": j.get("D_actual_h"),
                "n_pubs": j.get("n_pubs"),
                "usage_s": j.get("usage_s"),
                "queue_wait_s": j.get("queue_wait_s"),
            })

    if not rows:
        say("\n  NO FINISHED JOB. Nothing to analyse. The job states were:")
        for key in sorted(jobs):
            say(f"    {key:<12} {jobs[key].get('status')}")
        return 1

    import csv
    with open(OUT / "hw_jobs.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    say(f"\n  {len(rows)} arm rows from "
        f"{len({r['key'] for r in rows})} finished jobs "
        f"-> {OUT / 'hw_jobs.csv'}")

    fid = {(r["key"], r["arm"]): r["fidelity"] for r in rows}
    done = sorted({r["key"] for r in rows})

    # --------------------------------------------------------- fidelities
    say("\n" + "=" * 72)
    say("MEASURED FIDELITY, one row per job")
    say("=" * 72)
    say(f"  {'job':<12}{'circuit':<8}{'D h':>7}{'PUBs':>6}"
        + "".join(f"{a:>14}" for a in ARMS))
    for key in done:
        j = jobs[key]
        say(f"  {key:<12}{j['circuit']:<8}{j.get('D_actual_h', 0):>7.2f}"
            f"{j.get('n_pubs', 0):>6}"
            + "".join(f"{fid[(key, a)]:>14.4f}" for a in ARMS))
    say("")
    for a in ARMS:
        v = np.array([fid[(k, a)] for k in done])
        say(f"  mean fidelity, {a:<12} {v.mean():.4f}  "
            f"(SD {v.std(ddof=1):.4f})" if len(v) > 1 else
            f"  mean fidelity, {a:<12} {v.mean():.4f}")

    # --------------------------------------------------- paired differences
    say("\n" + "=" * 72)
    say("PAIRED DIFFERENCES OVER JOBS")
    say("=" * 72)
    say("  a job whose two arms gave an IDENTICAL transpiled circuit")
    say("  contributes exactly 0 and is counted, it is not dropped")
    say(f"  bootstrap: {N_BOOT} resamples of the jobs, seed {SEED_BOOT}, "
        "percentile interval")
    say("")
    say(f"  {'comparison':<34}{'role':<11}{'n':>4}{'mean':>11}{'SD':>10}"
        f"{'95% low':>11}{'95% high':>11}{'differ':>9}")
    summary = {}
    for hi, lo, role in COMPARISONS:
        d, tied = [], 0
        for key in done:
            d.append(fid[(key, hi)] - fid[(key, lo)])
            if jobs[key]["arms"][hi]["pub"] == jobs[key]["arms"][lo]["pub"]:
                tied += 1
        m, sd, l, h = boot_ci(d)
        differ = len(done) - tied
        summary[(hi, lo)] = dict(n=len(d), mean=m, sd=sd, lo=l, hi=h,
                                 tied=tied, differ=differ, d=d)
        say(f"  {hi + ' minus ' + lo:<34}{role:<11}{len(d):>4}{m:>11.5f}"
            f"{sd:>10.5f}{l:>11.5f}{h:>11.5f}"
            f"{differ:>5}/{len(done):<3}")

    # ------------------------------------------------------------ ties
    say("\n" + "=" * 72)
    say("IDENTICAL TRANSPILED CIRCUITS, counted as the protocol requires")
    say("=" * 72)
    pubs_total = sum(jobs[k]["n_pubs"] for k in done)
    say(f"  {pubs_total} PUBs were submitted for {len(done)} jobs; "
        f"3 arms x {len(done)} jobs = {3 * len(done)} arm results came back")
    say(f"  {3 * len(done) - pubs_total} arm results were served by a circuit "
        "another arm had already produced")
    for (hi, lo), s in summary.items():
        say(f"  {hi} and {lo}: identical in {s['tied']} of {len(done)} jobs "
            f"({100.0 * s['tied'] / len(done):.1f} percent), "
            f"layouts differ in {s['differ']}")

    # -------------------------------------------------------- by circuit
    say("\n" + "=" * 72)
    say("BY CIRCUIT")
    say("=" * 72)
    say(f"  {'circuit':<9}{'n':>3}" + "".join(
        f"{'mean F ' + a:>19}" for a in ARMS)
        + f"{'wm - stale':>13}{'hyb - stale':>13}")
    for c in sorted({jobs[k]["circuit"] for k in done}):
        ks = [k for k in done if jobs[k]["circuit"] == c]
        line = f"  {c:<9}{len(ks):>3}"
        for a in ARMS:
            line += f"{np.mean([fid[(k, a)] for k in ks]):>19.4f}"
        line += f"{np.mean([fid[(k, 'window_mean')] - fid[(k, 'stale')] for k in ks]):>13.5f}"
        line += f"{np.mean([fid[(k, 'hybrid')] - fid[(k, 'stale')] for k in ks]):>13.5f}"
        say(line)

    # --------------------------------------------------------- queue wait
    say("\n" + "=" * 72)
    say("QUEUE WAIT (running minus created, as IBM reports them)")
    say("=" * 72)
    say("  this is NOT the staleness delay. The 6 h hold is deliberate and")
    say("  local: the circuits sat on this machine before being sent.")
    qw = [jobs[k]["queue_wait_s"] for k in done
          if jobs[k].get("queue_wait_s") is not None]
    if qw:
        qw = np.array(qw, dtype=float)
        say(f"  n {len(qw)}   median {np.median(qw):.1f} s "
            f"({np.median(qw) / 60:.2f} min)")
        say(f"  range {qw.min():.1f} s to {qw.max():.1f} s "
            f"({qw.min() / 60:.2f} to {qw.max() / 60:.2f} min)")
        say(f"  share under 1 hour: {(qw < 3600).sum()}/{len(qw)} "
            f"= {100.0 * (qw < 3600).mean():.1f} percent")
    else:
        say("  IBM reported no usable created and running timestamps")

    # --------------------------------------------------- actual delays D
    say("\n" + "=" * 72)
    say("THE ACTUAL HOLD D, which the analysis uses")
    say("=" * 72)
    for key in done:
        j = jobs[key]
        say(f"  {key:<12} compiled {j['actual_compile_utc']}  "
            f"submitted {j.get('actual_submit_utc')}  "
            f"D = {j.get('D_actual_h')} h   card {j.get('card_utc')} "
            f"({j.get('card_age_at_compile_h')} h old at compile)")

    # -------------------------------------------------------------- usage
    say("\n" + "=" * 72)
    say("QPU USAGE AGAINST THE CAP")
    say("=" * 72)
    per = state.get("per_job_usage_s", {})
    for k in sorted(per):
        say(f"  {k:<12} {float(per[k]):.3f} s")
    total = sum(float(v) for v in per.values())
    acct0 = state.get("account_usage_start_s")
    acct1 = state.get("account_usage_latest_s")
    say(f"  {'TOTAL':<12} {total:.3f} s of the {CAP_TOTAL_S:.0f} s cap "
        f"({100.0 * total / CAP_TOTAL_S:.1f} percent)")
    if acct0 is not None and acct1 is not None:
        say(f"  the account's own counter moved {float(acct0):.1f} s -> "
            f"{float(acct1):.1f} s, a change of {float(acct1) - float(acct0):.3f} s")
    say(f"  cap respected: {'YES' if total <= CAP_TOTAL_S else 'NO'}")

    # ---------------------------------------------- events, honestly listed
    say("\n" + "=" * 72)
    say("EVERY RETRY, DELAY, LATE COMPILE AND MISSED JOB")
    say("=" * 72)
    ev = state.get("events", [])
    if not ev:
        say("  none. No IBM call needed a retry and no job was late or missed.")
    else:
        for e in ev:
            say(f"  {e['utc']}  {e['kind']:<18} {e['note']}")
    say("\n  job states:")
    for key in sorted(jobs):
        say(f"    {key:<12} {jobs[key].get('status')}")

    # --------------------------------------------------------- the limits
    say("\n" + "=" * 72)
    say("WHAT THIS CANNOT SHOW")
    say("=" * 72)
    say(f"  {len(done)} jobs is a sanity check, not a significance test.")
    say("  Round 2 measured a design effect of 9.400 on 11 days, so clustered")
    say("  variation here is large and these intervals are wide on purpose.")
    say("  The 6 h delay is a deliberate local hold, not a queue delay.")
    say("  There is no ceiling arm, so no regret and no absolute claim.")
    say("  Any agreement with Round 2 is 'consistent with', never proved.")

    json.dump({str(k): {kk: vv for kk, vv in v.items() if kk != "d"}
               for k, v in summary.items()},
              open(OUT / "hw_summary.json", "w"), indent=2)
    say(f"\n  summary written to {OUT / 'hw_summary.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
