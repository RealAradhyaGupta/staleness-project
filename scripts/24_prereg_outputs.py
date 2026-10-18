"""Produce the outputs PROTOCOL.md pre-registered but the run never emitted.

OURS. Written 14 October 2026, after the test run finished. It adds NO new
modelling choice: every number here is a different cut of the same merged
rows in outputs/test_full/all_rows.csv. Nothing in engine/ is touched.

Each output carries a label:
  PRE-REGISTERED  named in PROTOCOL.md or an amendment before any result
  EXPLORATORY     not named there, so it cannot support a claim

What is produced, and where it was pre-registered:
  P1  stale regret against the age at run time of the cz numbers used
      PROTOCOL.md section 9, axis 2                        PRE-REGISTERED
  P2  the same against readout error age, shown separately
      PROTOCOL.md section 9, closing paragraph             PRE-REGISTERED
  P3  mean ESP per arm per delay, alongside fidelity
      PROTOCOL.md section 8, secondary metric              PRE-REGISTERED
  P4  stale regret per machine per delay, with intervals
      PROTOCOL.md section 15, prediction 7                 PRE-REGISTERED
  P5  the 22 to 23 September gap jobs, reported separately
      PROTOCOL.md section 10                               PRE-REGISTERED
  P6  the permanent defect exclusion, audited
      PROTOCOL.md section 7, Amendment A1.5                PRE-REGISTERED
  P7  jobs dropped per delay, with the reason
      PROTOCOL.md section 3, Amendment A1.7                PRE-REGISTERED
  P8  stale regret per circuit per delay
      NOT named in PROTOCOL.md                             EXPLORATORY
  P9  the full six strategy table, mean fidelity and regret per delay
      section 6 names the six arms; the per delay table is a presentation
      of them                                              EXPLORATORY

Usage:  24_prereg_outputs.py [--results ...] [--outdir outputs/prereg]
"""
import argparse
import re
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
ARMS = ["random", "stale", "window_mean", "std_adjusted", "shrinkage", "ceiling"]
SEED_BOOT = 20261016        # a third seed, distinct from 20261014 and 20261015
N_BOOT = 4000

# Publishing gaps measured in L-033.
GAPS = {
    "ibm_fez":       ("2026-09-22T14:00:30Z", "2026-09-23T16:44:52Z"),
    "ibm_kingston":  ("2026-09-22T14:13:16Z", "2026-09-23T17:27:02Z"),
    "ibm_marrakesh": ("2026-09-20T22:53:12Z", "2026-09-22T05:14:59Z"),
}
# Permanent defects, training days only, as recorded in L-033 under A1.5.
PERMANENT = {"ibm_fez": [72], "ibm_kingston": [113, 121, 146],
             "ibm_marrakesh": [82, 94, 113, 130]}

AGE_BINS = [0, 6, 12, 18, 24, 36, 48, np.inf]
AGE_LABELS = ["0 to 6", "6 to 12", "12 to 18", "18 to 24", "24 to 36",
              "36 to 48", "48 or more"]


def load(results):
    df = pd.read_csv(results)
    df["t_s"] = pd.to_datetime(df.t_s, utc=True)
    df["t_r"] = pd.to_datetime(df.t_r, utc=True)
    df["day"] = df.t_s.dt.date.astype(str)
    g = {m: (pd.Timestamp(a), pd.Timestamp(b)) for m, (a, b) in GAPS.items()}
    df["touches_gap"] = [(ts < g[m][1]) and (tr > g[m][0])
                         for m, ts, tr in zip(df.machine, df.t_s, df.t_r)]
    return df


def boot(frame, col, rng, n_boot=N_BOOT):
    """95 percent interval, resampling WHOLE DAYS (PROTOCOL.md section 11)."""
    frame = frame[frame[col].notna()]
    if len(frame) == 0:
        return np.nan, np.nan, np.nan, 0
    pools = [g[col].to_numpy(float) for _, g in frame.groupby("day")]
    obs = float(np.concatenate(pools).mean())
    n = len(pools)
    draws = np.empty(n_boot)
    for i in range(n_boot):
        idx = rng.integers(0, n, size=n)
        draws[i] = np.concatenate([pools[j] for j in idx]).mean()
    lo, hi = (float(x) for x in np.percentile(draws, [2.5, 97.5]))
    return obs, lo, hi, n


def binned(frame, age_col, value_col, rng, label):
    """Mean value in each age bin, with an interval."""
    f = frame[frame[age_col].notna()].copy()
    f["age_bin"] = pd.cut(f[age_col], bins=AGE_BINS, labels=AGE_LABELS,
                          right=False)
    rows = []
    for b in AGE_LABELS:
        g = f[f.age_bin == b]
        if len(g) == 0:
            continue
        o, lo, hi, nd = boot(g, value_col, rng)
        rows.append(dict(label=label, age_bin_h=b, n=len(g), days=nd,
                         median_age_h=round(float(g[age_col].median()), 3),
                         mean=round(o, 6), lo95=round(lo, 6),
                         hi95=round(hi, 6)))
    return pd.DataFrame(rows)


def show(title, label, frame, note=""):
    print("\n" + "=" * 76)
    print(f"{title}   [{label}]")
    if note:
        print(note)
    print("=" * 76)
    print(frame.to_string(index=False))


def parse_dropped(logfile):
    """Pull the per delay dropped counts out of the run log the engine wrote."""
    rows = []
    if not Path(logfile).exists():
        return pd.DataFrame(rows)
    pat = re.compile(r"^\s+(ibm_\w+): (\d+) submissions -> (\d+) jobs; dropped (\{.*\})\s*$")
    for line in Path(logfile).read_text().splitlines():
        m = pat.match(line)
        if not m:
            continue
        machine, subs, njobs, blob = m.group(1), int(m.group(2)), int(m.group(3)), m.group(4)
        for dm in re.finditer(r"'D=(\d+)': \{([^}]*)\}", blob):
            D = int(dm.group(1))
            reasons = dict(re.findall(r"'(\w+)': (\d+)", dm.group(2)))
            rows.append(dict(label="PRE-REGISTERED", machine=machine,
                             submissions=subs, delay_h=D,
                             dropped_no_history=int(reasons.get("no_history", 0)),
                             dropped_no_truth=int(reasons.get("no_truth", 0)),
                             dropped_past_end=int(reasons.get("past_end", 0))))
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default=str(ROOT / "outputs/test_full/all_rows.csv"))
    ap.add_argument("--runlog", default=str(ROOT / "logs/test_run.log"))
    ap.add_argument("--outdir", default=str(ROOT / "outputs/prereg"))
    args = ap.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED_BOOT)

    df = load(args.results)
    print("PRE-REGISTERED OUTPUTS NOT PRODUCED BY THE RUN")
    print(f"source: {args.results}")
    print(f"rows {len(df)}   bootstrap seed {SEED_BOOT}, {N_BOOT} resamples")
    print("Every number below is a different cut of the SAME rows. No new "
          "modelling choice was made.")

    # one row per job per arm, widened so regret is available
    idx = ["machine", "draw_order", "delay_h", "circuit", "day", "new_states",
           "touches_gap"]
    wide = df.pivot_table(index=idx, columns="arm", values="fidelity").reset_index()
    for arm in ARMS:
        wide[f"regret_{arm}"] = wide["ceiling"] - wide[arm]
    main_w = wide[~wide.touches_gap]
    gap_w = wide[wide.touches_gap]

    # per arm long frame with ages, for the age axes
    long = df.copy()
    long["regret"] = long.merge(
        wide[idx[:5] + ["ceiling"]], on=idx[:5], how="left")["ceiling"].to_numpy() \
        - long["fidelity"].to_numpy()
    main_l = long[~long.touches_gap]

    written = []

    # --- P1 cz age at run time -------------------------------------------
    stale_l = main_l[main_l.arm == "stale"]
    p1 = binned(stale_l, "cz_age_at_run_h", "regret", rng, "PRE-REGISTERED")
    show("P1. stale regret against the age at run time of the cz numbers it "
         "used", "PRE-REGISTERED", p1,
         "PROTOCOL.md section 9 axis 2: the clock is the date printed on the "
         "value itself,\nnot the publication time. Gap jobs excluded. "
         f"{int(stale_l.cz_age_at_run_h.isna().sum())} stale rows have no cz "
         "age at all,\nbecause 5 ibm_kingston cards carry no cz gates (L-008), "
         "and are left out of this cut.")
    p1.to_csv(outdir / "P1_cz_age_at_run_stale_regret.csv", index=False)
    written.append("P1_cz_age_at_run_stale_regret.csv")

    p1b = pd.concat([binned(main_l[main_l.arm == a], "cz_age_at_run_h",
                            "regret", rng, "PRE-REGISTERED").assign(arm=a)
                     for a in ARMS if a != "ceiling"])
    p1b = p1b[["label", "arm", "age_bin_h", "n", "days", "median_age_h",
               "mean", "lo95", "hi95"]]
    show("P1b. the same axis for every arm", "PRE-REGISTERED", p1b)
    p1b.to_csv(outdir / "P1b_cz_age_at_run_all_arms.csv", index=False)
    written.append("P1b_cz_age_at_run_all_arms.csv")

    # --- P2 readout age, separately --------------------------------------
    p2 = binned(stale_l, "readout_age_at_run_h", "regret", rng, "PRE-REGISTERED")
    show("P2. stale regret against READOUT error age at run time",
         "PRE-REGISTERED", p2,
         "PROTOCOL.md section 9 requires this shown SEPARATELY, never merged "
         "with cz,\nbecause L-017 measured readout refreshing about ten times "
         "faster.")
    p2.to_csv(outdir / "P2_readout_age_at_run_stale_regret.csv", index=False)
    written.append("P2_readout_age_at_run_stale_regret.csv")

    ages = main_l[main_l.arm == "stale"][["cz_age_at_run_h",
                                          "readout_age_at_run_h"]].describe()
    show("P2b. the two clocks are not the same clock", "PRE-REGISTERED",
         ages.round(3).reset_index())
    ages.round(3).to_csv(outdir / "P2b_age_distributions.csv")
    written.append("P2b_age_distributions.csv")

    # --- P3 ESP alongside fidelity ---------------------------------------
    esp = df[~df.touches_gap].pivot_table(index="delay_h", columns="arm",
                                          values="esp").reset_index()
    fid = main_w.groupby("delay_h")[ARMS].mean().reset_index()
    p3 = esp.merge(fid, on="delay_h", suffixes=("_esp", "_fidelity"))
    p3.insert(0, "label", "PRE-REGISTERED")
    show("P3. mean analytic ESP per arm per delay, ALONGSIDE mean simulated "
         "fidelity", "PRE-REGISTERED", p3.round(4),
         "PROTOCOL.md section 8: the secondary metric is reported alongside "
         "the simulated\nfidelity, never instead of it. Gap jobs excluded.")
    p3.round(6).to_csv(outdir / "P3_esp_alongside_fidelity.csv", index=False)
    written.append("P3_esp_alongside_fidelity.csv")

    # --- P4 per machine, with intervals ----------------------------------
    rows = []
    for (m, D), g in main_w.groupby(["machine", "delay_h"]):
        o, lo, hi, nd = boot(g, "regret_stale", rng)
        rows.append(dict(label="PRE-REGISTERED", machine=m, delay_h=D,
                         n=len(g), days=nd, mean_regret=round(o, 6),
                         lo95=round(lo, 6), hi95=round(hi, 6)))
    p4 = pd.DataFrame(rows)
    show("P4. stale regret per machine per delay, with intervals",
         "PRE-REGISTERED", p4,
         "PROTOCOL.md section 15 prediction 7 named ibm_marrakesh as the "
         "largest, so this\ntable is what judges that prediction.")
    p4.to_csv(outdir / "P4_stale_regret_per_machine.csv", index=False)
    written.append("P4_stale_regret_per_machine.csv")

    # --- P5 gap jobs -----------------------------------------------------
    rows = []
    for D, g in gap_w.groupby("delay_h"):
        o, lo, hi, nd = boot(g, "regret_stale", rng)
        rows.append(dict(label="PRE-REGISTERED", delay_h=D, n=len(g), days=nd,
                         no_change_share=round(float((g.new_states == 0).mean()), 4),
                         mean_regret=round(o, 6), lo95=round(lo, 6),
                         hi95=round(hi, 6)))
    p5 = pd.DataFrame(rows)
    show("P5. the 22 to 23 September publishing gap, reported separately",
         "PRE-REGISTERED", p5,
         f"PROTOCOL.md section 10: the gap stays in and straddling jobs are "
         f"reported\nseparately. {len(gap_w)} of {len(wide)} jobs overlap a "
         f"gap window.")
    p5.to_csv(outdir / "P5_gap_jobs.csv", index=False)
    written.append("P5_gap_jobs.csv")

    rows = []
    for (m, D), g in gap_w.groupby(["machine", "delay_h"]):
        rows.append(dict(label="PRE-REGISTERED", machine=m, delay_h=D,
                         n=len(g),
                         mean_regret=round(float(g.regret_stale.mean()), 6)))
    p5b = pd.DataFrame(rows)
    show("P5b. gap jobs per machine", "PRE-REGISTERED", p5b)
    p5b.to_csv(outdir / "P5b_gap_jobs_per_machine.csv", index=False)
    written.append("P5b_gap_jobs_per_machine.csv")

    # --- P6 permanent defect audit ---------------------------------------
    rows = []
    for m, perm in PERMANENT.items():
        sub = df[df.machine == m]
        used = set()
        for s in sub.qubits_used.dropna():
            used.update(int(x) for x in str(s).split())
        leaked = sorted(set(perm) & used)
        rows.append(dict(label="PRE-REGISTERED", machine=m,
                         permanent_defects=" ".join(map(str, perm)),
                         n_permanent=len(perm),
                         rows_checked=len(sub),
                         min_n_forbidden=int(sub.n_forbidden.min()),
                         median_n_forbidden=float(sub.n_forbidden.median()),
                         max_n_forbidden=int(sub.n_forbidden.max()),
                         permanent_qubit_ever_used=" ".join(map(str, leaked))
                                                   or "none"))
    p6 = pd.DataFrame(rows)
    show("P6. the permanent defect exclusion, audited", "PRE-REGISTERED", p6,
         "PROTOCOL.md section 7 and Amendment A1.5: the list is computed on "
         "TRAINING days\nonly and excluded for every arm including the "
         "ceiling. n_forbidden is that arm's\nown dead list UNION the "
         "permanent list, so it can never fall below n_permanent.")
    p6.to_csv(outdir / "P6_permanent_defect_audit.csv", index=False)
    written.append("P6_permanent_defect_audit.csv")

    rows = []
    for (m, arm), g in df.groupby(["machine", "arm"]):
        rows.append(dict(label="PRE-REGISTERED", machine=m, arm=arm,
                         n_rows=len(g),
                         mean_n_forbidden=round(float(g.n_forbidden.mean()), 3),
                         min_n_forbidden=int(g.n_forbidden.min()),
                         max_n_forbidden=int(g.n_forbidden.max())))
    p6b = pd.DataFrame(rows)
    show("P6b. how many qubits each arm was forbidden, per machine",
         "PRE-REGISTERED", p6b)
    p6b.to_csv(outdir / "P6b_forbidden_per_arm.csv", index=False)
    written.append("P6b_forbidden_per_arm.csv")

    # --- P7 dropped jobs per delay ---------------------------------------
    p7 = parse_dropped(args.runlog)
    if len(p7):
        p7["dropped_submission_delay_slots"] = (p7.dropped_no_history
                                                + p7.dropped_no_truth
                                                + p7.dropped_past_end)
        p7["dropped_jobs_5_circuits"] = p7.dropped_submission_delay_slots * 5
        tot = p7.groupby("delay_h")[["dropped_no_history", "dropped_no_truth",
                                     "dropped_past_end",
                                     "dropped_jobs_5_circuits"]].sum()
        tot.insert(0, "label", "PRE-REGISTERED")
        show("P7. jobs dropped per delay, with the reason", "PRE-REGISTERED",
             tot.reset_index(),
             "PROTOCOL.md section 3 and Amendment A1.7: invalid jobs are "
             "dropped and COUNTED,\nnever silently skipped. past_end means "
             "the run time falls after the last state\non that machine, which "
             "is rule 3 of section 3 and is why D = 48 is thinnest.\nThe "
             "engine printed these into logs/test_run.log; they had never "
             "been collected.")
        p7.to_csv(outdir / "P7_dropped_jobs_per_delay_per_machine.csv",
                  index=False)
        tot.reset_index().to_csv(outdir / "P7_dropped_jobs_per_delay.csv",
                                 index=False)
        written += ["P7_dropped_jobs_per_delay_per_machine.csv",
                    "P7_dropped_jobs_per_delay.csv"]
    else:
        print("\nP7: run log not found, dropped counts not recoverable here")

    # --- P8 per circuit (exploratory) ------------------------------------
    rows = []
    for (c, D), g in main_w.groupby(["circuit", "delay_h"]):
        o, lo, hi, nd = boot(g, "regret_stale", rng)
        rows.append(dict(label="EXPLORATORY", circuit=c, delay_h=D, n=len(g),
                         days=nd, mean_regret=round(o, 6), lo95=round(lo, 6),
                         hi95=round(hi, 6)))
    p8 = pd.DataFrame(rows)
    show("P8. stale regret per circuit per delay", "EXPLORATORY", p8,
         "PROTOCOL.md names the five circuits in section 5 but never "
         "pre-registers a per\ncircuit breakdown, so this is exploratory and "
         "cannot support a claim.")
    p8.to_csv(outdir / "P8_stale_regret_per_circuit_EXPLORATORY.csv",
              index=False)
    written.append("P8_stale_regret_per_circuit_EXPLORATORY.csv")

    # --- P9 full six strategy table --------------------------------------
    rows = []
    for D, g in main_w.groupby("delay_h"):
        r = dict(label="EXPLORATORY", delay_h=D, n=len(g))
        for arm in ARMS:
            o, lo, hi, _ = boot(g, arm, rng)
            r[f"fid_{arm}"] = round(o, 6)
            r[f"fid_{arm}_lo95"] = round(lo, 6)
            r[f"fid_{arm}_hi95"] = round(hi, 6)
        for arm in ARMS:
            if arm == "ceiling":
                continue
            o, lo, hi, _ = boot(g, f"regret_{arm}", rng)
            r[f"regret_{arm}"] = round(o, 6)
            r[f"regret_{arm}_lo95"] = round(lo, 6)
            r[f"regret_{arm}_hi95"] = round(hi, 6)
        rows.append(r)
    p9 = pd.DataFrame(rows)
    show("P9. the full six strategy table, mean fidelity per delay",
         "EXPLORATORY",
         p9[["delay_h", "n"] + [f"fid_{a}" for a in ARMS]].round(4),
         "PROTOCOL.md section 6 pre-registers the six arms. Only A (stale vs "
         "ceiling) and B\n(shrinkage vs stale) are confirmatory; every other "
         "arm comparison here is exploratory.")
    show("P9b. the full six strategy table, mean regret per delay",
         "EXPLORATORY",
         p9[["delay_h", "n"] + [f"regret_{a}" for a in ARMS
                                if a != "ceiling"]].round(4))
    p9.to_csv(outdir / "P9_six_strategy_table_EXPLORATORY.csv", index=False)
    written.append("P9_six_strategy_table_EXPLORATORY.csv")

    rows = []
    for (m, D), g in main_w.groupby(["machine", "delay_h"]):
        r = dict(label="EXPLORATORY", machine=m, delay_h=D, n=len(g))
        for arm in ARMS:
            o, lo, hi, _ = boot(g, arm, rng)
            r[f"fid_{arm}"] = round(o, 6)
            r[f"fid_{arm}_lo95"] = round(lo, 6)
            r[f"fid_{arm}_hi95"] = round(hi, 6)
            if arm != "ceiling":
                o2, l2, h2, _ = boot(g, f"regret_{arm}", rng)
                r[f"regret_{arm}"] = round(o2, 6)
                r[f"regret_{arm}_lo95"] = round(l2, 6)
                r[f"regret_{arm}_hi95"] = round(h2, 6)
        rows.append(r)
    p9c = pd.DataFrame(rows)
    p9c.to_csv(outdir / "P9c_six_strategy_table_per_machine_EXPLORATORY.csv",
               index=False)
    written.append("P9c_six_strategy_table_per_machine_EXPLORATORY.csv")
    show("P9c. six strategy mean fidelity per machine per delay",
         "EXPLORATORY",
         p9c[["machine", "delay_h", "n"] + [f"fid_{a}" for a in ARMS]].round(4))

    print("\n" + "=" * 76)
    print(f"files written to {outdir}")
    for f in written:
        print(f"  {f}")
    print("=" * 76)


main()
