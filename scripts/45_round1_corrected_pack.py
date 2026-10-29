"""Corrected Round 1 pack: every test-period table rebuilt on ALL 5,648 jobs.

OURS. PRESENTATION ONLY. Every number here comes from the frozen Round 1 rows
file outputs/test_full/all_rows.csv, which was written before this script
existed. No modelling choice is made here. Nothing in engine/ is touched,
imported or changed, and scripts 20, 24, 25, 26 and 28 are read only: their
functions are loaded out of their own source so the arithmetic is literally
theirs, but their files are never edited.

WHAT IS DIFFERENT FROM THE ORIGINAL PACK
  1. No gap exclusion. PROTOCOL.md section 10 says the 22 to 23 September
     publishing gap stays in and the straddling jobs are reported separately.
     The original pack reported them separately but ALSO dropped them from
     every headline. Here they are inside every file, and P5 still reports
     them on their own as well.
  2. fig_d sign. The original computed stale minus shrinkage while its own
     label said "positive = shrinkage better", so the direction was the wrong
     way round. Corrected here to shrinkage minus stale, the same correction
     scripts/20_analyse_results.py already carries from L-049.
  3. Comparison B is reported at 6 h and at 24 h separately, which is what
     PROTOCOL.md section 11 comparison B fixed in advance. The pooled figure
     is kept as a labelled extra, not as the headline.

Sign conventions, unchanged:  regret = ceiling minus strategy
                              gain   = F_strategy minus F_stale

Seeds are each original file's own seed, so a difference between old and new
is the row set and the sign fix, not a different bootstrap.

Usage:  45_round1_corrected_pack.py [--results ...] [--outdir ...]
"""
import argparse
import ast
import importlib.util
import sys
import types
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"

ARMS = ["random", "stale", "window_mean", "std_adjusted", "shrinkage",
        "ceiling"]
DELAYS = [1, 3, 6, 12, 24, 48]
IDX = ["machine", "draw_order", "delay_h", "circuit", "day", "new_states",
       "touches_gap"]

# each original file's own bootstrap seed, so only the data changes
SEED_FIG = 20261017        # scripts/26_report_figures.py
SEED_PREREG = 20261016     # scripts/24_prereg_outputs.py
SEED_SANITY = 20261014     # scripts/20_analyse_results.py


def load_frozen(name):
    """Load a frozen script's functions WITHOUT editing it and WITHOUT
    running its main(). The frozen scripts call main() at the bottom, so a
    plain import would start a whole run. Every top level bare call is
    dropped and the rest is executed unchanged, so the functions that come
    back are the frozen ones byte for byte."""
    src = (SCRIPTS / name).read_text()
    tree = ast.parse(src, filename=name)
    tree.body = [n for n in tree.body
                 if not (isinstance(n, ast.Expr)
                         and isinstance(n.value, ast.Call))]
    mod = types.ModuleType(f"frozen_{name[:2]}")
    mod.__file__ = str(SCRIPTS / name)
    sys.modules[mod.__name__] = mod
    exec(compile(tree, str(SCRIPTS / name), "exec"), mod.__dict__)
    return mod


OUT = []


def say(line=""):
    print(line)
    OUT.append(line)


def show(title, label, frame, note=""):
    say()
    say("=" * 76)
    say(f"{title}   [{label}]")
    if note:
        say(note)
    say("=" * 76)
    say(frame.to_string(index=False))


def show_idx(title, label, frame, note=""):
    say()
    say("=" * 76)
    say(f"{title}   [{label}]")
    if note:
        say(note)
    say("=" * 76)
    say(frame.to_string())


# ===================================================================== main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results",
                    default=str(ROOT / "outputs/test_full/all_rows.csv"))
    ap.add_argument("--outdir",
                    default=str(ROOT / "outputs/round1_corrected_pack"))
    ap.add_argument("--fixture",
                    default=str(ROOT / "team_code/zip_originals/results/"
                                       "results_synthetic.csv"))
    args = ap.parse_args()

    outdir = Path(args.outdir)
    figdir = outdir / "numbers" / "figure_csv"
    pregdir = outdir / "numbers" / "prereg"
    for d in (figdir, pregdir):
        d.mkdir(parents=True, exist_ok=True)

    # frozen code, loaded not copied
    f26 = load_frozen("26_report_figures.py")
    f24 = load_frozen("24_prereg_outputs.py")
    f20 = load_frozen("20_analyse_results.py")
    boot_fig = f26.boot                 # (obs, lo, hi)
    series_table = f26.series_table
    boot_pre = f24.boot                 # (obs, lo, hi, n_days)
    binned = f24.binned

    say("CORRECTED ROUND 1 PACK, ALL 5,648 JOBS, NO GAP EXCLUSION")
    say(f"source (read only): {args.results}")
    say("frozen functions loaded from scripts/26_report_figures.py, "
        "scripts/24_prereg_outputs.py, scripts/20_analyse_results.py")
    say("PROTOCOL.md section 10 keeps the 22 to 23 September gap in. "
        "Per-delay numbers follow section 11.")
    say("regret = ceiling minus strategy.  gain = F_strategy minus F_stale.")

    # ---- load with the frozen loader, then widen with NO gap filter -----
    df, old_w = f26.load(args.results)      # df carries day + touches_gap
    wide = df.pivot_table(index=IDX, columns="arm",
                          values="fidelity").reset_index()
    for arm in ARMS:
        wide[f"regret_{arm}"] = wide["ceiling"] - wide[arm]
    w = wide                                   # ALL jobs, nothing dropped
    gap_w = wide[wide.touches_gap]

    say()
    say(f"rows {len(df)}   jobs {len(w)}   days {w.day.nunique()}   "
        f"machines {sorted(w.machine.unique())}")
    say(f"jobs overlapping a gap window: {len(gap_w)} of {len(w)}   "
        f"(kept in, and ALSO reported on their own in P5)")
    say(f"the original pack kept {len(old_w)} of {len(w)} jobs, so "
        f"{len(w) - len(old_w)} were missing from every old headline")

    written = []

    # ================================================= figure_csv ========
    rng = np.random.default_rng(SEED_FIG)

    # ---- fig_a, four files, same call order as 26_report_figures.main ---
    def fig_a(machine, tag):
        sub = w if machine is None else w[w.machine == machine]
        fid = series_table(sub, rng, ARMS)
        reg = series_table(sub, rng,
                           [f"regret_{a}" for a in ARMS if a != "ceiling"])
        both = pd.concat([fid.assign(panel="mean fidelity"),
                          reg.assign(panel="regret vs ceiling")])
        both["machine"] = machine or "all three"
        both["label"] = ("EXPLORATORY (six arm comparison); A and B are the "
                         "only confirmatory tests")
        name = f"fig_a_six_strategies_{tag}.csv"
        both.to_csv(figdir / name, index=False)
        written.append(f"numbers/figure_csv/{name}")
        return both

    a_all = fig_a(None, "all_machines")
    show("fig_a. six strategies, all three machines, all 5,648 jobs",
         "EXPLORATORY",
         a_all[a_all.panel == "mean fidelity"].round(6),
         "Mean fidelity panel shown; the regret panel is in the same CSV.")
    for m in sorted(w.machine.unique()):
        fig_a(m, m)

    # ---- fig_b ----------------------------------------------------------
    buckets = [("0", w.new_states == 0), ("1", w.new_states == 1),
               ("2 or more", w.new_states >= 2)]
    arms_b = ["stale", "window_mean", "std_adjusted", "shrinkage"]
    rows = []
    for name, mask in buckets:
        g = w[mask]
        for a in arms_b:
            o, lo, hi = boot_fig(g, f"regret_{a}", rng)
            rows.append(dict(new_states_crossed=name, arm=a, n=len(g),
                             mean_regret=o, lo95=lo, hi95=hi,
                             label="PRE-REGISTERED axis (PROTOCOL.md section "
                                   "9 axis 3); the per arm split is "
                                   "exploratory"))
    fig_b = pd.DataFrame(rows)
    fig_b.to_csv(figdir / "fig_b_regret_by_new_states.csv", index=False)
    written.append("numbers/figure_csv/fig_b_regret_by_new_states.csv")
    show("fig_b. regret by how many new states the job crossed",
         "PRE-REGISTERED axis", fig_b.round(6))

    # ---- fig_c ----------------------------------------------------------
    rows = []
    for m in sorted(w.machine.unique()):
        for D in DELAYS:
            g = w[(w.machine == m) & (w.delay_h == D)]
            o, lo, hi = boot_fig(g, "regret_stale", rng)
            rows.append(dict(machine=m, delay_h=D, n=len(g), mean_regret=o,
                             lo95=lo, hi95=hi,
                             label="PRE-REGISTERED (PROTOCOL.md section 15 "
                                   "prediction 7)"))
    fig_c = pd.DataFrame(rows)
    fig_c.to_csv(figdir / "fig_c_stale_regret_per_machine.csv", index=False)
    written.append("numbers/figure_csv/fig_c_stale_regret_per_machine.csv")
    show("fig_c. stale regret per machine per delay", "PRE-REGISTERED",
         fig_c.round(6))

    # ---- fig_d, SIGN CORRECTED -----------------------------------------
    wd = w.copy()
    # shrinkage MINUS stale. Higher fidelity is better, so this is the gain
    # of shrinkage over stale and positive means shrinkage is better. The
    # original figure computed stale - shrinkage under this same label.
    wd["gain"] = wd["shrinkage"] - wd["stale"]
    rows = []
    for name, mask in (("6 h", wd.delay_h == 6),
                       ("24 h", wd.delay_h == 24),
                       ("6 and 24 h pooled", wd.delay_h.isin([6, 24]))):
        g = wd[mask]
        o, lo, hi = boot_fig(g, "gain", rng)
        rows.append(dict(delay=name, n=len(g), mean_gain=o, lo95=lo, hi95=hi,
                         label="CONFIRMATORY, PROTOCOL.md section 11 "
                               "comparison B",
                         sign="F_shrinkage minus F_stale"))
    fig_d = pd.DataFrame(rows)
    fig_d.to_csv(figdir / "fig_d_shrinkage_minus_stale.csv", index=False)
    written.append("numbers/figure_csv/fig_d_shrinkage_minus_stale.csv")
    show("fig_d. Comparison B, shrinkage minus stale, paired by job",
         "CONFIRMATORY", fig_d.round(6),
         "6 h and 24 h are the pre-registered rows (PROTOCOL.md section 11\n"
         "comparison B). The pooled row is a labelled extra, not the "
         "headline.\nmean_gain is F_shrinkage minus F_stale, so positive "
         "means shrinkage is better.")

    # ==================================================== prereg P files ==
    # Same call order as 24_prereg_outputs.main, so the bootstrap stream is
    # consumed in the same order. P6, P6b and P7 are not reproduced: they do
    # not depend on the test jobs and the addendum does not need them.
    rng = np.random.default_rng(SEED_PREREG)

    long = df.copy()
    long["regret"] = long.merge(
        wide[IDX[:5] + ["ceiling"]], on=IDX[:5],
        how="left")["ceiling"].to_numpy() - long["fidelity"].to_numpy()
    main_l = long                              # ALL rows, nothing dropped

    # ---- P1 cz age ------------------------------------------------------
    stale_l = main_l[main_l.arm == "stale"]
    p1 = binned(stale_l, "cz_age_at_run_h", "regret", rng, "PRE-REGISTERED")
    p1.to_csv(pregdir / "P1_cz_age_at_run_stale_regret.csv", index=False)
    written.append("numbers/prereg/P1_cz_age_at_run_stale_regret.csv")
    show("P1. stale regret against the age at run time of the cz numbers it "
         "used", "PRE-REGISTERED", p1,
         "PROTOCOL.md section 9 axis 2. ALL jobs, gap jobs included. "
         f"{int(stale_l.cz_age_at_run_h.isna().sum())} stale rows have no cz "
         "age at all,\nbecause 5 ibm_kingston cards carry no cz gates "
         "(L-008), and are left out of this cut.")

    p1b = pd.concat([binned(main_l[main_l.arm == a], "cz_age_at_run_h",
                            "regret", rng, "PRE-REGISTERED").assign(arm=a)
                     for a in ARMS if a != "ceiling"])
    p1b = p1b[["label", "arm", "age_bin_h", "n", "days", "median_age_h",
               "mean", "lo95", "hi95"]]
    p1b.to_csv(pregdir / "P1b_cz_age_at_run_all_arms.csv", index=False)
    written.append("numbers/prereg/P1b_cz_age_at_run_all_arms.csv")
    show("P1b. the same axis for every arm", "PRE-REGISTERED", p1b)

    # ---- P2 readout age -------------------------------------------------
    p2 = binned(stale_l, "readout_age_at_run_h", "regret", rng,
                "PRE-REGISTERED")
    p2.to_csv(pregdir / "P2_readout_age_at_run_stale_regret.csv", index=False)
    written.append("numbers/prereg/P2_readout_age_at_run_stale_regret.csv")
    show("P2. stale regret against READOUT error age at run time",
         "PRE-REGISTERED", p2,
         "PROTOCOL.md section 9 requires this shown SEPARATELY, never merged "
         "with cz.")

    ages = main_l[main_l.arm == "stale"][["cz_age_at_run_h",
                                          "readout_age_at_run_h"]].describe()
    ages.round(3).to_csv(pregdir / "P2b_age_distributions.csv")
    written.append("numbers/prereg/P2b_age_distributions.csv")
    show_idx("P2b. the two clocks are not the same clock", "PRE-REGISTERED",
             ages.round(3))

    # ---- P3 ESP alongside fidelity --------------------------------------
    esp = df.pivot_table(index="delay_h", columns="arm",
                         values="esp").reset_index()
    fid = w.groupby("delay_h")[ARMS].mean().reset_index()
    p3 = esp.merge(fid, on="delay_h", suffixes=("_esp", "_fidelity"))
    p3.insert(0, "label", "PRE-REGISTERED")
    p3.round(6).to_csv(pregdir / "P3_esp_alongside_fidelity.csv", index=False)
    written.append("numbers/prereg/P3_esp_alongside_fidelity.csv")
    show("P3. mean analytic ESP per arm per delay, ALONGSIDE mean simulated "
         "fidelity", "PRE-REGISTERED", p3.round(4),
         "PROTOCOL.md section 8: the secondary metric is reported alongside "
         "the simulated\nfidelity, never instead of it. ALL jobs.")

    # ---- P4 per machine -------------------------------------------------
    rows = []
    for (m, D), g in w.groupby(["machine", "delay_h"]):
        o, lo, hi, nd = boot_pre(g, "regret_stale", rng)
        rows.append(dict(label="PRE-REGISTERED", machine=m, delay_h=D,
                         n=len(g), days=nd, mean_regret=round(o, 6),
                         lo95=round(lo, 6), hi95=round(hi, 6)))
    p4 = pd.DataFrame(rows)
    p4.to_csv(pregdir / "P4_stale_regret_per_machine.csv", index=False)
    written.append("numbers/prereg/P4_stale_regret_per_machine.csv")
    show("P4. stale regret per machine per delay, with intervals",
         "PRE-REGISTERED", p4,
         "PROTOCOL.md section 15 prediction 7 named ibm_marrakesh as the "
         "largest, so this\ntable is what judges that prediction.")

    # ---- P5 gap jobs, still reported on their own -----------------------
    rows = []
    for D, g in gap_w.groupby("delay_h"):
        o, lo, hi, nd = boot_pre(g, "regret_stale", rng)
        rows.append(dict(label="PRE-REGISTERED", delay_h=D, n=len(g), days=nd,
                         no_change_share=round(float((g.new_states == 0)
                                                     .mean()), 4),
                         mean_regret=round(o, 6), lo95=round(lo, 6),
                         hi95=round(hi, 6)))
    p5 = pd.DataFrame(rows)
    p5.to_csv(pregdir / "P5_gap_jobs.csv", index=False)
    written.append("numbers/prereg/P5_gap_jobs.csv")
    show("P5. the 22 to 23 September publishing gap, reported separately",
         "PRE-REGISTERED", p5,
         f"PROTOCOL.md section 10. These {len(gap_w)} of {len(wide)} jobs "
         f"are reported here on their own\nAND are inside every other file "
         f"in this pack.")

    rows = []
    for (m, D), g in gap_w.groupby(["machine", "delay_h"]):
        rows.append(dict(label="PRE-REGISTERED", machine=m, delay_h=D,
                         n=len(g),
                         mean_regret=round(float(g.regret_stale.mean()), 6)))
    p5b = pd.DataFrame(rows)
    p5b.to_csv(pregdir / "P5b_gap_jobs_per_machine.csv", index=False)
    written.append("numbers/prereg/P5b_gap_jobs_per_machine.csv")
    show("P5b. gap jobs per machine", "PRE-REGISTERED", p5b)

    # ---- P8 per circuit -------------------------------------------------
    rows = []
    for (c, D), g in w.groupby(["circuit", "delay_h"]):
        o, lo, hi, nd = boot_pre(g, "regret_stale", rng)
        rows.append(dict(label="EXPLORATORY", circuit=c, delay_h=D, n=len(g),
                         days=nd, mean_regret=round(o, 6), lo95=round(lo, 6),
                         hi95=round(hi, 6)))
    p8 = pd.DataFrame(rows)
    p8.to_csv(pregdir / "P8_stale_regret_per_circuit_EXPLORATORY.csv",
              index=False)
    written.append("numbers/prereg/"
                   "P8_stale_regret_per_circuit_EXPLORATORY.csv")
    show("P8. stale regret per circuit per delay", "EXPLORATORY", p8,
         "PROTOCOL.md never pre-registers a per circuit breakdown, so this "
         "is exploratory\nand cannot support a claim.")

    # ---- P9 six strategy table ------------------------------------------
    rows = []
    for D, g in w.groupby("delay_h"):
        r = dict(label="EXPLORATORY", delay_h=D, n=len(g))
        for arm in ARMS:
            o, lo, hi, _ = boot_pre(g, arm, rng)
            r[f"fid_{arm}"] = round(o, 6)
            r[f"fid_{arm}_lo95"] = round(lo, 6)
            r[f"fid_{arm}_hi95"] = round(hi, 6)
        for arm in ARMS:
            if arm == "ceiling":
                continue
            o, lo, hi, _ = boot_pre(g, f"regret_{arm}", rng)
            r[f"regret_{arm}"] = round(o, 6)
            r[f"regret_{arm}_lo95"] = round(lo, 6)
            r[f"regret_{arm}_hi95"] = round(hi, 6)
        rows.append(r)
    p9 = pd.DataFrame(rows)
    p9.to_csv(pregdir / "P9_six_strategy_table_EXPLORATORY.csv", index=False)
    written.append("numbers/prereg/P9_six_strategy_table_EXPLORATORY.csv")
    show("P9. six strategy table, mean fidelity per delay", "EXPLORATORY",
         p9[["delay_h", "n"] + [f"fid_{a}" for a in ARMS]].round(4),
         "Only A (stale vs ceiling) and B (shrinkage vs stale) are "
         "confirmatory.")
    show("P9b. six strategy table, mean regret per delay", "EXPLORATORY",
         p9[["delay_h", "n"] + [f"regret_{a}" for a in ARMS
                                if a != "ceiling"]].round(4))

    rows = []
    for (m, D), g in w.groupby(["machine", "delay_h"]):
        r = dict(label="EXPLORATORY", machine=m, delay_h=D, n=len(g))
        for arm in ARMS:
            o, lo, hi, _ = boot_pre(g, arm, rng)
            r[f"fid_{arm}"] = round(o, 6)
            r[f"fid_{arm}_lo95"] = round(lo, 6)
            r[f"fid_{arm}_hi95"] = round(hi, 6)
            if arm != "ceiling":
                o2, l2, h2, _ = boot_pre(g, f"regret_{arm}", rng)
                r[f"regret_{arm}"] = round(o2, 6)
                r[f"regret_{arm}_lo95"] = round(l2, 6)
                r[f"regret_{arm}_hi95"] = round(h2, 6)
        rows.append(r)
    p9c = pd.DataFrame(rows)
    p9c.to_csv(pregdir /
               "P9c_six_strategy_table_per_machine_EXPLORATORY.csv",
               index=False)
    written.append("numbers/prereg/"
                   "P9c_six_strategy_table_per_machine_EXPLORATORY.csv")
    show("P9c. six strategy mean fidelity per machine per delay",
         "EXPLORATORY",
         p9c[["machine", "delay_h", "n"]
             + [f"fid_{a}" for a in ARMS]].round(4))

    # ================================= prereg D files, dead qubit rows ===
    # scripts/25_dead_qubit_rows.py never excluded gap jobs, so these six
    # were already computed on all 5,648 jobs. They are regenerated here so
    # the pack is complete and so the claim can be checked, not estimated.
    say()
    say("=" * 76)
    say("D1 to D6. DEAD QUBIT ROWS. DESCRIPTIVE ONLY, no interval, no test.")
    say("scripts/25_dead_qubit_rows.py never applied a gap exclusion, so "
        "these were")
    say("already on all jobs. Regenerated unchanged.")
    say("=" * 76)

    dq = df.copy()
    dq["dead_str"] = dq.dead_qubits_used.fillna("").astype(str).str.strip()
    hit = dq[dq.dead_str != ""].copy()
    hit["n_dead_used"] = hit.dead_str.str.split().apply(len)
    present = [a for a in ARMS if a in set(hit.arm)]

    say(f"total rows {len(dq)}   rows with at least one such qubit "
        f"{len(hit)}   share {len(hit)/len(dq)*100:.2f}%")
    say(f"distinct jobs touched: "
        f"{hit.groupby(['machine','draw_order','delay_h','circuit']).ngroups}")

    d1 = (hit.groupby("arm")
          .agg(rows=("arm", "size"),
               qubit_instances=("n_dead_used", "sum"),
               mean_per_row=("n_dead_used", "mean"),
               max_in_one_row=("n_dead_used", "max"))
          .reindex(present))
    d1["rows_of_5648"] = d1.rows
    d1["share_of_arm_rows_pct"] = (
        d1.rows / dq.groupby("arm").size().reindex(d1.index) * 100)
    d1.round(6).to_csv(pregdir / "D1_dead_qubit_rows_by_arm.csv")
    written.append("numbers/prereg/D1_dead_qubit_rows_by_arm.csv")
    show_idx("D1. by arm", "DESCRIPTIVE", d1.round(3))

    d2 = (hit.groupby("delay_h")
          .agg(rows=("delay_h", "size"),
               qubit_instances=("n_dead_used", "sum")))
    d2["all_rows_at_this_delay"] = dq.groupby("delay_h").size()
    d2["share_pct"] = d2.rows / d2.all_rows_at_this_delay * 100
    d2.round(6).to_csv(pregdir / "D2_dead_qubit_rows_by_delay.csv")
    written.append("numbers/prereg/D2_dead_qubit_rows_by_delay.csv")
    show_idx("D2. by delay", "DESCRIPTIVE", d2.round(3))

    d3 = (hit.pivot_table(index="delay_h", columns="arm", values="dead_str",
                          aggfunc="size")
          .reindex(columns=present).fillna(0).astype(int))
    d3["all arms"] = d3.sum(axis=1)
    d3.to_csv(pregdir / "D3_dead_qubit_rows_by_arm_and_delay.csv")
    written.append("numbers/prereg/D3_dead_qubit_rows_by_arm_and_delay.csv")
    show_idx("D3. by arm and delay", "DESCRIPTIVE", d3)

    cols = [c for c in d3.columns if c not in ("random", "all arms")]
    d4 = d3[cols].copy()
    d4["informed arms"] = d4.sum(axis=1)
    d4.to_csv(pregdir / "D4_dead_qubit_rows_informed_arms.csv")
    written.append("numbers/prereg/D4_dead_qubit_rows_informed_arms.csv")
    show_idx("D4. informed arms only, the random arm dominates every total",
             "DESCRIPTIVE", d4)

    d5 = (hit.pivot_table(index="machine", columns="arm", values="dead_str",
                          aggfunc="size")
          .reindex(columns=present).fillna(0).astype(int))
    d5["all arms"] = d5.sum(axis=1)
    d5.to_csv(pregdir / "D5_dead_qubit_rows_by_machine_and_arm.csv")
    written.append("numbers/prereg/D5_dead_qubit_rows_by_machine_and_arm.csv")
    show_idx("D5. by machine and arm", "DESCRIPTIVE", d5)

    b = hit.new_states.clip(upper=2).map({0: "0", 1: "1", 2: "2 or more"})
    d6 = hit.groupby([b, "arm"]).size().unstack(fill_value=0)
    d6.to_csv(pregdir / "D6_dead_qubit_rows_by_new_states.csv")
    written.append("numbers/prereg/D6_dead_qubit_rows_by_new_states.csv")
    show_idx("D6. by how many new states the job crossed", "DESCRIPTIVE",
             d6.reindex(columns=present))
    say()
    say(f"rows where the CEILING used a truth-dead qubit: "
        f"{int((hit.arm == 'ceiling').sum())}")
    say("The ceiling reads the truth state itself, so it is 0 by "
        "construction.")

    # ============================= Comparison A, stale vs the ceiling ====
    rng = np.random.default_rng(SEED_SANITY)
    rows = []
    for D, g in w.groupby("delay_h"):
        o, lo, hi, nd = f20.block_boot(g, "regret_stale", rng)
        rows.append(dict(label="CONFIRMATORY, PROTOCOL.md section 11 "
                               "comparison A",
                         delay_h=D, n=len(g), days=nd,
                         no_change_share=round(float((g.new_states == 0)
                                                     .mean()), 6),
                         mean_regret=round(float(o), 6), lo95=round(lo, 6),
                         hi95=round(hi, 6),
                         sign="regret = F_ceiling minus F_stale"))
    compA = pd.DataFrame(rows)
    compA.to_csv(outdir / "comparison_A_stale_regret_all_jobs.csv",
                 index=False)
    written.append("comparison_A_stale_regret_all_jobs.csv")
    show("COMPARISON A. stale regret against the ceiling, per delay, with "
         "the no-new-state shares", "CONFIRMATORY", compA,
         "ALL 5,648 jobs, gap jobs included (PROTOCOL.md section 10).")

    # ============================= the four sanity checks, all jobs ======
    sanity_lines = []

    def s(line=""):
        sanity_lines.append(line)
        say(line)

    say()
    say("=" * 76)
    say("SANITY CHECKS, PROTOCOL.md section 12, ON ALL JOBS")
    say("=" * 76)

    s("sanity_checks_all_jobs.txt")
    s()
    s("The four PROTOCOL.md section 12 sanity checks, recomputed on ALL "
      "5,648")
    s("jobs with no gap exclusion. Same layout as the old")
    s("sanity_checks_and_independent_check.txt, but these are real recomputed")
    s("counts, not a quotation of the log.")
    s()
    s("source: outputs/test_full/all_rows.csv (read only)")
    s(f"rows {len(df)}   jobs {len(w)}   days {w.day.nunique()}")
    s("the script that ran them: scripts/45_round1_corrected_pack.py, using "
      "the")
    s("sanity logic of scripts/20_analyse_results.py unchanged")
    s()
    s("1. THE FOUR SANITY CHECKS (test period, all jobs)")
    s()

    nc = w[w.new_states == 0]
    worst = float(np.abs(nc["regret_stale"]).max())
    ok1 = worst == 0.0
    s(f"   1. stale regret EXACTLY 0 when no new state appeared: "
      f"{'PASS' if ok1 else 'FAIL'}")
    s(f"      {len(nc)} jobs, largest absolute regret {worst!r}.")
    s()

    ok2 = True
    s("   2. ceiling at least as good as stale at every delay:")
    diffs = {}
    for D, g in w.groupby("delay_h"):
        c, st = g["ceiling"].mean(), g["stale"].mean()
        diffs[D] = c - st
        ok2 &= (c >= st)
        s(f"      D={D:>3}h  ceiling {c:.4f}  stale {st:.4f}  {c-st:+.4f}  "
          f"{'ok' if c >= st else 'FAIL'}")
    s(f"      {'PASS' if ok2 else 'FAIL'}: {diffs[1]:+.4f} at 1 h rising to "
      f"{diffs[48]:+.4f} at 48 h.")
    s()

    means = {a: float(w[a].mean()) for a in ARMS}
    lowest = min(means, key=means.get)
    ok3 = lowest == "random"
    s(f"   3. random layout is the worst arm: {'PASS' if ok3 else 'FAIL'} "
      f"(lowest is {lowest})")
    s(f"      {means['random']:.4f} against {means['stale']:.4f} for stale.")
    for a in sorted(means, key=means.get):
        s(f"      {a:<14} {means[a]:.4f}")
    s()

    import hashlib
    fx = Path(args.fixture)
    if fx.exists():
        h = hashlib.sha256(fx.read_bytes()).hexdigest()
        ok4 = h == f20.FIXTURE_SHA
        s(f"   4. teammates' fixture checksum unchanged: "
          f"{'PASS' if ok4 else 'FAIL'}")
        s(f"      {h}")
    else:
        ok4 = None
        s(f"   4. fixture not found at {fx}, check could not run.")
        s("      Not estimated and not assumed to pass.")
    s()
    allfour = [ok1, bool(ok2), ok3, ok4]
    if all(x is True for x in allfour):
        s("   All four sanity checks PASS on all 5,648 jobs.")
    else:
        s("   NOT all four checks could be confirmed; see above.")
    s()
    s("2. THE INDEPENDENT CHECK")
    s()
    s("   scripts/23_independent_check.py was written for the "
      "gap-excluded set")
    s("   and was never run with --json-out, so no saved output file exists "
      "for")
    s("   it on any row set. It is NOT rerun or re-estimated here. The old")
    s("   pack's quotation of PROGRESS_LOG.md L-042 stands as the record for")
    s("   the gap-excluded numbers only.")

    (outdir / "sanity_checks_all_jobs.txt").write_text(
        "\n".join(sanity_lines) + "\n")
    written.append("sanity_checks_all_jobs.txt")

    # ---- readable text and console ---------------------------------------
    (outdir / "READABLE_TABLES.txt").write_text("\n".join(OUT) + "\n")
    written.append("READABLE_TABLES.txt")

    print()
    print("=" * 76)
    print(f"files written under {outdir}")
    for f in written:
        print(f"  {f}")
    print("=" * 76)
    return outdir, written


if __name__ == "__main__":
    main()
