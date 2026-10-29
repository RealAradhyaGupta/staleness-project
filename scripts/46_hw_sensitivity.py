"""Hardware sensitivity checks. POST HOC, EXPLORATORY, not a result.

OURS. The frozen analysis in scripts/43_hw_analyse.py stays as the reported
number and is not touched, re-run or superseded by anything here. This script
only re-cuts the 12 saved paired differences in different ways, to show how
much the single reported number depends on the choices behind it.

Reads outputs/hardware/hw_jobs.csv and outputs/hardware/hw_summary.json only.
No IBM call, no quantum job, no hardware access. Nothing in engine/ is
imported and no frozen file is edited.

Sign convention, unchanged: gain = F_strategy minus F_stale, so positive means
the strategy beat trusting the newest card.

Usage:  46_hw_sensitivity.py [--outdir outputs/hardware]
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
N_BOOT = 4000
SEED = 20261029          # a new seed, distinct from the frozen 20261025
ARMS = ["window_mean", "hybrid"]

OUT = []


def say(line=""):
    print(line)
    OUT.append(line)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", default=str(ROOT / "outputs/hardware/hw_jobs.csv"))
    ap.add_argument("--summary",
                    default=str(ROOT / "outputs/hardware/hw_summary.json"))
    ap.add_argument("--outdir", default=str(ROOT / "outputs/hardware"))
    args = ap.parse_args()

    df = pd.read_csv(args.jobs)
    frozen = json.loads(Path(args.summary).read_text())

    # one row per job, arms as columns
    w = df.pivot_table(index=["key", "slot", "circuit", "compile_utc"],
                       columns="arm", values="fidelity").reset_index()
    w["d_window_mean"] = w["window_mean"] - w["stale"]
    w["d_hybrid"] = w["hybrid"] - w["stale"]
    w = w.sort_values(["slot", "circuit"]).reset_index(drop=True)
    assert len(w) == 12, f"expected 12 jobs, got {len(w)}"

    say("# HARDWARE SENSITIVITY, POST HOC")
    say()
    say("**POST HOC and EXPLORATORY. Not a result and not a test.** The")
    say("reported hardware numbers are the frozen ones from")
    say("`scripts/43_hw_analyse.py`, which is unchanged. Nothing here")
    say("supersedes them. This file exists to show how much that single")
    say("number leans on the choices behind it, which is a limitation to")
    say("state, not a new finding.")
    say()
    say("Source files, read only: `outputs/hardware/hw_jobs.csv`,")
    say("`outputs/hardware/hw_summary.json`. 12 jobs, 3 arms, 36 rows.")
    say()
    say("Sign convention unchanged: gain = F_strategy minus F_stale, so")
    say("positive means the strategy beat trusting the newest card.")
    say()
    say("The frozen numbers this file re-cuts, for reference:")
    say()
    say("| comparison | n | mean | sd | 95 pct low | 95 pct high |")
    say("| --- | --- | --- | --- | --- | --- |")
    for k, v in frozen.items():
        nm = k.replace("('", "").replace("')", "").replace("', '", " minus ")
        say(f"| {nm} | {v['n']} | {v['mean']:+.6f} | {v['sd']:.6f} | "
            f"{v['lo']:+.6f} | {v['hi']:+.6f} |")

    # ---------------------------------------------------------------- (a)
    say()
    say("## (a) The 12 paired differences, by compile time and circuit")
    say()
    say("`slot` is the compile time: slot 1 = t0, slot 2 = t0+2h, slot 3 =")
    say("t0+4h. Each slot compiled against one calibration card, so the four")
    say("jobs in a slot share that card.")
    say()
    say("| slot | compile time (UTC) | circuit | F_stale | F_window_mean | "
        "F_hybrid | window_mean minus stale | hybrid minus stale |")
    say("| --- | --- | --- | --- | --- | --- | --- | --- |")
    for _, r in w.iterrows():
        say(f"| {int(r.slot)} | {r.compile_utc[:19]} | {r.circuit} | "
            f"{r.stale:.6f} | {r.window_mean:.6f} | {r.hybrid:.6f} | "
            f"{r.d_window_mean:+.6f} | {r.d_hybrid:+.6f} |")
    say()
    ties_w = int((w.d_window_mean == 0).sum())
    ties_h = int((w.d_hybrid == 0).sum())
    say(f"Exact ties, counted and kept, never dropped: window_mean {ties_w} "
        f"of 12, hybrid {ties_h} of 12.")
    say("A tie is a job where the two arms transpiled to the identical")
    say("circuit, so it ran once and both arms were given that one result.")
    w.to_csv(Path(args.outdir) / "SENSITIVITY_paired_differences.csv",
             index=False)

    # ---------------------------------------------------------------- (b)
    say()
    say("## (b) Means by compile time and by circuit")
    say()
    say("### By compile time, 3 clusters of 4 jobs")
    say()
    say("| slot | n | window_mean minus stale | hybrid minus stale |")
    say("| --- | --- | --- | --- |")
    by_slot = []
    for s, g in w.groupby("slot"):
        say(f"| {int(s)} | {len(g)} | {g.d_window_mean.mean():+.6f} | "
            f"{g.d_hybrid.mean():+.6f} |")
        by_slot.append(dict(slot=int(s), n=len(g),
                            d_window_mean=g.d_window_mean.mean(),
                            d_hybrid=g.d_hybrid.mean()))
    say()
    sw = [r["d_window_mean"] for r in by_slot]
    sh = [r["d_hybrid"] for r in by_slot]
    say(f"Spread across the 3 compile times: window_mean {min(sw):+.6f} to "
        f"{max(sw):+.6f} (range {max(sw)-min(sw):.6f}),")
    say(f"hybrid {min(sh):+.6f} to {max(sh):+.6f} "
        f"(range {max(sh)-min(sh):.6f}).")
    say()
    say("### By circuit, 4 clusters of 3 jobs")
    say()
    say("| circuit | n | window_mean minus stale | hybrid minus stale |")
    say("| --- | --- | --- | --- |")
    by_circ = []
    for c, g in w.groupby("circuit"):
        say(f"| {c} | {len(g)} | {g.d_window_mean.mean():+.6f} | "
            f"{g.d_hybrid.mean():+.6f} |")
        by_circ.append(dict(circuit=c, n=len(g),
                            d_window_mean=g.d_window_mean.mean(),
                            d_hybrid=g.d_hybrid.mean()))
    pd.DataFrame(by_slot).to_csv(
        Path(args.outdir) / "SENSITIVITY_by_compile_time.csv", index=False)
    pd.DataFrame(by_circ).to_csv(
        Path(args.outdir) / "SENSITIVITY_by_circuit.csv", index=False)
    say()
    cw = [r["d_window_mean"] for r in by_circ]
    say(f"Spread across the 4 circuits: window_mean {min(cw):+.6f} to "
        f"{max(cw):+.6f}.")
    say("With 3 jobs per circuit and 4 per compile time, none of these cells")
    say("carries an interval worth printing. They are shown to display the")
    say("spread, not to support a per-cell claim.")

    # ---------------------------------------------------------------- (c)
    say()
    say("## (c) Leave one job out")
    say()
    say("Each row drops exactly one of the 12 jobs and recomputes the mean")
    say("over the remaining 11. This shows how far one job can move the")
    say("reported figure.")
    say()
    say("| job dropped | window_mean minus stale | hybrid minus stale |")
    say("| --- | --- | --- |")
    loo = []
    for i, r in w.iterrows():
        rest = w.drop(index=i)
        say(f"| {r.key} | {rest.d_window_mean.mean():+.6f} | "
            f"{rest.d_hybrid.mean():+.6f} |")
        loo.append(dict(dropped=r.key,
                        d_window_mean=rest.d_window_mean.mean(),
                        d_hybrid=rest.d_hybrid.mean()))
    L = pd.DataFrame(loo)
    L.to_csv(Path(args.outdir) / "SENSITIVITY_leave_one_out.csv", index=False)
    say()
    say(f"All 12 jobs in: window_mean {w.d_window_mean.mean():+.6f}, "
        f"hybrid {w.d_hybrid.mean():+.6f}.")
    say(f"Leave-one-out range: window_mean {L.d_window_mean.min():+.6f} to "
        f"{L.d_window_mean.max():+.6f}, hybrid "
        f"{L.d_hybrid.min():+.6f} to {L.d_hybrid.max():+.6f}.")
    wi = L.d_window_mean.idxmax()
    say(f"The single most influential job for the primary comparison is "
        f"`{L.dropped[wi]}`: dropping it moves window_mean minus stale from "
        f"{w.d_window_mean.mean():+.6f} to {L.d_window_mean[wi]:+.6f}, a "
        f"change of {L.d_window_mean[wi]-w.d_window_mean.mean():+.6f}.")
    say("One job out of twelve moving the headline by that much is the "
        "point of this section.")
    say(f"Sign changes under leave-one-out: window_mean "
        f"{'yes' if L.d_window_mean.min()*L.d_window_mean.max() < 0 else 'no'}, "
        f"hybrid "
        f"{'yes' if L.d_hybrid.min()*L.d_hybrid.max() < 0 else 'no'}.")

    # ---------------------------------------------------------------- (d)
    say()
    say("## (d) A bootstrap that resamples whole compile times")
    say()
    say("Jobs compiled at the same time share one calibration card, so they")
    say("are not independent of each other. The honest resampling unit is")
    say("therefore the compile time, not the job. That is the same argument")
    say("Round 1 and Round 2 used for resampling whole calendar days.")
    say()
    say(f"Resampling 3 whole compile times with replacement, {N_BOOT} "
        f"resamples, seed {SEED}:")
    say()
    say("| comparison | mean | 95 pct low | 95 pct high | width |")
    say("| --- | --- | --- | --- | --- |")
    rows = []
    for arm in ARMS:
        col = f"d_{arm}"
        pools = [g[col].to_numpy(float) for _, g in w.groupby("slot")]
        rng = np.random.default_rng(SEED)
        n = len(pools)
        draws = np.empty(N_BOOT)
        for i in range(N_BOOT):
            pick = rng.integers(0, n, size=n)
            draws[i] = np.concatenate([pools[j] for j in pick]).mean()
        lo, hi = (float(x) for x in np.percentile(draws, [2.5, 97.5]))
        obs = float(w[col].mean())
        say(f"| {arm} minus stale | {obs:+.6f} | {lo:+.6f} | {hi:+.6f} | "
            f"{hi-lo:.6f} |")
        rows.append(dict(comparison=f"{arm} minus stale", unit="compile_time",
                         n_clusters=n, mean=obs, lo95=lo, hi95=hi,
                         width=hi - lo))
    say()
    say("Against the frozen job-level intervals:")
    say()
    say("| comparison | job-level width (frozen) | compile-time width | "
        "ratio |")
    say("| --- | --- | --- | --- |")
    for arm in ARMS:
        key = f"('{arm}', 'stale')"
        fw = frozen[key]["hi"] - frozen[key]["lo"]
        r = [x for x in rows if x["comparison"] == f"{arm} minus stale"][0]
        say(f"| {arm} minus stale | {fw:.6f} | {r['width']:.6f} | "
            f"{r['width']/fw:.2f}x |")
    pd.DataFrame(rows).to_csv(
        Path(args.outdir) / "SENSITIVITY_cluster_bootstrap.csv", index=False)

    say()
    say("**Three clusters are far too few for a reliable interval, and this")
    say("interval must not be quoted as a result.** Saying it plainly: with")
    say("3 clusters there are only 10 distinct multisets of 3 draws, so the")
    say("bootstrap distribution is built from at most 10 different values of")
    say("the mean. A percentile interval taken from 10 possible values has")
    say("no meaningful 2.5th or 97.5th percentile. The numbers above show")
    say("exactly that degeneracy: both endpoints land precisely on the")
    say("smallest and largest of the 3 compile-time means in the table in")
    say("(b). The interval is the range of 3 numbers and nothing more.")
    say()
    say("**Because of that degeneracy the width ratio above says nothing in")
    say("either direction.** It came out below 1, but a percentile interval")
    say("that collapses onto the range of 3 values is not evidence that the")
    say("frozen interval is too wide, and it would not have been evidence")
    say("that it is too narrow either.")
    say()
    say("### A standard error is the more informative comparison")
    say()
    say("The clustered standard error does not degenerate the same way, so")
    say("it gives a better sense of direction, though 3 clusters still make")
    say("it unreliable.")
    say()
    say("| comparison | naive SE, 12 independent jobs | clustered SE, 3 "
        "compile times | ratio |")
    say("| --- | --- | --- | --- |")
    se_rows = []
    for arm in ARMS:
        col = f"d_{arm}"
        x = w[col].to_numpy(float)
        naive = float(x.std(ddof=1) / np.sqrt(len(x)))
        cm = w.groupby("slot")[col].mean().to_numpy(float)
        clus = float(cm.std(ddof=1) / np.sqrt(len(cm)))
        say(f"| {arm} minus stale | {naive:.6f} | {clus:.6f} | "
            f"{clus/naive:.2f}x |")
        se_rows.append(dict(comparison=f"{arm} minus stale", naive_se=naive,
                            clustered_se=clus, ratio=clus / naive))
    pd.DataFrame(se_rows).to_csv(
        Path(args.outdir) / "SENSITIVITY_standard_errors.csv", index=False)
    say()
    say("**This is the opposite of Round 1 and Round 2.** There the design")
    say("effect was 5.247 and 9.400, so jobs on the same day moved together")
    say("strongly and the naive interval was far too narrow. Here the")
    say("clustered standard error is about the same as the naive one for the")
    say("hybrid and smaller for the window mean, which says most of the")
    say("variation in these 12 jobs sits WITHIN a compile time rather than")
    say("between compile times. The table in (b) shows why: the four")
    say("circuits inside one slot disagree far more than the three slots")
    say("disagree with each other, and `s1_bv8` alone is -0.133.")
    say()
    say("So on this evidence, treating the 12 jobs as independent is not")
    say("obviously anti-conservative, and I am not claiming the frozen")
    say("interval is too narrow. This is consistent with the clustering")
    say("mattering little here; it does not prove it, because 3 clusters")
    say("cannot estimate a design effect with any precision.")
    say()
    say("The correct reading of (d) as a whole: neither the cluster")
    say("bootstrap nor the clustered standard error settles anything at 3")
    say("clusters. A study that wanted to settle it needs many more compile")
    say("times, not more jobs per compile time.")

    # ---------------------------------------------------------------- (e)
    say()
    say("## (e) What the original analysis actually did")
    say()
    say("**The frozen analysis treated the 12 jobs as independent. It did")
    say("NOT group by compile time.** `scripts/43_hw_analyse.py` line 59")
    say("draws `rng.integers(0, len(x), size=(n_boot, len(x)))`, which")
    say("resamples the 12 job-level differences one at a time with")
    say("replacement. `FREEZE_HARDWARE.txt` records the same choice before")
    job_doc = ("the run: \"bootstrap 4000 resamples of the jobs, seed "
               "20261025\".")
    say(job_doc)
    say()
    say("The script's own docstring explains why the JOB rather than the ROW")
    say("is the unit: the three arms of one job share one queue position and")
    say("one calibration epoch, so the 36 rows are not 36 independent")
    say("numbers. That reasoning is right and it was applied. What it does")
    say("not do is take the next step: the same argument applies again one")
    say("level up, because the four jobs in a compile slot share one")
    say("calibration card. So the analysis removed the within-job dependence")
    say("and left the within-slot dependence in place.")
    say()
    say("This was a pre-stated choice, written into FREEZE_HARDWARE.txt")
    say("before any job ran, so it is not a departure from the protocol and")
    say("nothing was changed after seeing the data. It is a limitation of")
    say("the frozen design, and the right place for it is the limits")
    say("section, which is why this file exists.")
    say()
    say("Consistent with, not proved: the standard errors in (d) are")
    say("consistent with the within-slot dependence mattering little in")
    say("these 12 jobs, which would mean the frozen job-level interval is")
    say("not badly wrong. With 3 clusters that cannot be established either")
    say("way, so the limitation stands as a limitation and not as a")
    say("correction to the reported number.")

    outp = Path(args.outdir) / "SENSITIVITY.md"
    outp.write_text("\n".join(OUT) + "\n")
    print(f"\nwritten: {outp}")


if __name__ == "__main__":
    main()
