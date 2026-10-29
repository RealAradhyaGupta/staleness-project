"""The protocol-faithful headline: Comparisons A and B on ALL 5648 jobs.

OURS. FIX FORWARD. Nothing is overwritten.

Why this file exists. L-052 found that scripts/20_analyse_results.py runs the
two confirmatory comparisons on `main_set = w[~w.touches_gap]`, which drops the
360 jobs whose submission-to-run interval overlaps a 22 to 23 September
publishing gap. PROTOCOL.md section 10 says the opposite:

    "The 22 to 23 September publishing gap stays in. It is not deleted or
     patched. Results are reported with it included, and the jobs that straddle
     it are reported separately so its effect is visible."

and PROTOCOL_AMENDMENTS.md A1.6 reaffirms it. So the protocol-faithful headline
is computed on ALL jobs, with the straddling jobs ALSO shown on their own. That
is what this script does.

WHAT IS NOT TOUCHED. scripts/20_analyse_results.py is not edited. No existing
output file is overwritten. No confirmatory file already reported is changed.
No IBM call is made, no new simulation is run, and nothing in `data/raw` is
written. Everything comes from re-reading the frozen
outputs/test_full/all_rows.csv.

HOW THE METHOD IS KEPT IDENTICAL. The loader, the reshape and the block
bootstrap are IMPORTED from scripts/20_analyse_results.py, together with its
seed (20261014) and its resample count (4000). The statistics helpers for the
power section are imported from scripts/26_row_check.py. Nothing is copied.
The ONLY thing that differs from the reported numbers is which jobs go in.

SIGN CONVENTION, the same as 26_row_check.py and 27_audit_checks.py:
    regret = ceiling minus strategy      (positive means the strategy is worse)
    gain   = F_strategy minus F_stale    (positive means the strategy is better)

THE POOLING RULE. PROTOCOL.md section 11 defines Comparison B as "per-field
shrinkage against stale, at D = 6 hours and D = 24 hours, pooled over machines
and circuits, on the test days only." That pools over machines and circuits, at
each D. It does NOT say to pool the two delays into one number. So the
protocol-faithful Comparison B is TWO numbers, one at 6 h and one at 24 h. The
single across-delay number that script 20 headlines is reported too, clearly
labelled, so the old and new figures can be put side by side.

Wording rule from L-032: say "consistent with", never "proved".

Usage:  28_protocol_headline.py [--results ...] [--outdir outputs/protocol_headline]
"""
import argparse
import math
import sys
import types
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent

ARMS = ["random", "stale", "window_mean", "std_adjusted", "shrinkage", "ceiling"]
STRATS = [a for a in ARMS if a != "ceiling"]
INFORMED = ["stale", "window_mean", "std_adjusted", "shrinkage"]
JOB = ["machine", "draw_order", "delay_h", "circuit"]
B_DELAYS = [6, 24]
POOL_DELAYS = [6, 12, 24, 48]
TOL = 0.0005

# The reported numbers this script puts side by side with the new ones. Typed
# in from PROGRESS_LOG.md L-039, with Comparison B in the direction corrected
# by L-049, so every comparison below is explicit and nothing is eyeballed.
REPORTED_A = {1: 0.0059, 3: 0.0171, 6: 0.0230, 12: 0.0259, 24: 0.0245,
              48: 0.0367}
REPORTED_B = {"pooled 6 and 24 h": 0.00176, "6 h": 0.00345, "24 h": -0.00003}


def load_module(relpath, name):
    """Import a numbered script for its functions.

    These files call main() at the bottom, so the trailing call is dropped and
    the rest is executed as a module. This reuses the real functions instead of
    copying them, the same approach as scripts/26_row_check.py.
    """
    path = ROOT / relpath
    src = path.read_text().rsplit("\nmain()", 1)[0]
    mod = types.ModuleType(name)
    mod.__file__ = str(path)
    exec(compile(src, str(path), "exec"), mod.__dict__)
    return mod


M20 = load_module("scripts/20_analyse_results.py", "analyse20")
M26 = load_module("scripts/26_row_check.py", "rowcheck26")


def fresh_rng():
    return np.random.default_rng(M20.SEED_BOOT)


def ci(frame, col, rng):
    if len(frame) == 0:
        return float("nan"), float("nan"), float("nan"), 0
    return M20.block_boot(frame, col, rng)


# ------------------------------------------------- the three job selections

def selections(w):
    """All jobs, gap-touching jobs only, and non-gap jobs only.

    The first is the protocol-faithful set. The third is what script 20 used.
    """
    return {
        "ALL jobs (protocol-faithful)": w,
        "GAP-touching jobs only (reported separately)": w[w.touches_gap],
        "NON-GAP jobs only (what script 20 used)": w[~w.touches_gap],
    }


def comparison_a(w, rows, selname):
    print(f"\n  Comparison A: stale regret against the ceiling, at each D")
    print(f"  regret = ceiling minus stale, positive means stale is worse")
    print(f"  {'D (h)':>6} {'n':>6} {'no-change':>10} {'mean':>10} "
          f"{'95 pct interval':>24} {'days':>5}")
    rng = fresh_rng()
    for D, g in w.groupby("delay_h"):
        o, lo, hi, nd = ci(g, "regret_stale", rng)
        nochange = (g.new_states == 0).mean()
        print(f"  {D:>6} {len(g):>6} {nochange*100:>9.1f}% {o:>+10.4f}   "
              f"[{lo:>+8.4f}, {hi:>+8.4f}] {nd:>5}")
        rows.append(dict(selection=selname, comparison="A stale regret",
                         scope=f"delay {D} h", n=len(g),
                         no_change_share=nochange, mean=o, lo=lo, hi=hi,
                         days=nd,
                         interval_excludes_zero=bool(lo > 0 or hi < 0)))


def comparison_b(w, rows, selname):
    print(f"\n  Comparison B: per-field shrinkage against stale, paired")
    print(f"  gain = shrinkage minus stale, positive means shrinkage is better")
    print(f"  PROTOCOL-FAITHFUL: at D = 6 h and at D = 24 h, each pooled over")
    print(f"  machines and circuits. The across-delay number is shown after,")
    print(f"  labelled, because that is the one script 20 headlines.")
    rng = fresh_rng()
    sub = w[w.delay_h.isin(B_DELAYS)].copy()
    sub["gain"] = sub["shrinkage"] - sub["stale"]
    order = [(f"{D} h", sub[sub.delay_h == D]) for D in B_DELAYS]
    order.append(("pooled 6 and 24 h", sub))
    for scope, g in order:
        o, lo, hi, nd = ci(g, "gain", rng)
        tag = "protocol-faithful" if scope != "pooled 6 and 24 h" \
            else "across-delay, script 20 style"
        verdict = ("shrinkage better" if lo > 0 else "stale better" if hi < 0
                   else "interval includes zero, no difference")
        print(f"    {scope:<20} n={len(g):>5}  {o:+.5f}  "
              f"[{lo:+.5f}, {hi:+.5f}]  {verdict}   ({tag})")
        rows.append(dict(selection=selname, comparison="B shrinkage vs stale",
                         scope=scope, n=len(g), no_change_share=float("nan"),
                         mean=o, lo=lo, hi=hi, days=nd,
                         interval_excludes_zero=bool(lo > 0 or hi < 0),
                         note=tag, verdict=verdict))


def headline(w, outdir):
    print("=" * 74)
    print("THE PROTOCOL-FAITHFUL HEADLINE")
    print("=" * 74)
    print(f"  jobs in the file: {len(w)}   gap-touching: "
          f"{int(w.touches_gap.sum())}   non-gap: {int((~w.touches_gap).sum())}")
    rows = []
    for selname, sel in selections(w).items():
        print("\n" + "-" * 74)
        print(f"  {selname}   n = {len(sel)} jobs, {sel.day.nunique()} days")
        print("-" * 74)
        comparison_a(sel, rows, selname)
        comparison_b(sel, rows, selname)
    out = pd.DataFrame(rows)
    out.to_csv(outdir / "H1_comparisons_by_selection.csv", index=False)

    print("\n" + "=" * 74)
    print("ASSERTION: the NON-GAP set must reproduce the reported numbers")
    print("=" * 74)
    print(f"  tolerance {TOL}. If any line fails, this script stops.")
    ng = out[out.selection == "NON-GAP jobs only (what script 20 used)"]
    fails = []
    for D, want in REPORTED_A.items():
        got = float(ng[(ng.comparison == "A stale regret")
                       & (ng.scope == f"delay {D} h")]["mean"].iloc[0])
        ok = abs(got - want) <= TOL
        print(f"    A at {D:>2} h   got {got:+.5f}   reported {want:+.5f}   "
              f"diff {abs(got-want):.5f}  {'ok' if ok else 'FAIL'}")
        if not ok:
            fails.append(f"A at {D} h")
    for scope, want in REPORTED_B.items():
        got = float(ng[(ng.comparison == "B shrinkage vs stale")
                       & (ng.scope == scope)]["mean"].iloc[0])
        ok = abs(got - want) <= TOL
        print(f"    B {scope:<18} got {got:+.6f}   reported {want:+.6f}   "
              f"diff {abs(got-want):.6f}  {'ok' if ok else 'FAIL'}")
        if not ok:
            fails.append(f"B {scope}")
    assert not fails, f"NON-GAP set did not reproduce: {fails}"
    print("  every line reproduced. The method is unchanged; only the job")
    print("  selection differs.")

    print("\n" + "=" * 74)
    print("OLD AGAINST NEW, side by side")
    print("=" * 74)
    allj = out[out.selection == "ALL jobs (protocol-faithful)"]
    gapj = out[out.selection == "GAP-touching jobs only (reported separately)"]
    print("\n  Comparison A, mean stale regret by delay")
    print(f"  {'D (h)':>6} {'reported (5288)':>24} {'protocol (5648)':>24} "
          f"{'change':>9} {'gap only (360)':>24}")
    cmp_rows = []
    for D in sorted(REPORTED_A):
        a = allj[allj.scope == f"delay {D} h"].iloc[0]
        n = ng[(ng.comparison == "A stale regret")
               & (ng.scope == f"delay {D} h")].iloc[0]
        g = gapj[(gapj.comparison == "A stale regret")
                 & (gapj.scope == f"delay {D} h")].iloc[0]
        print(f"  {D:>6} {f'{n_fmt(n)}':>24} {f'{n_fmt(a)}':>24} "
              f"{a['mean']-n['mean']:>+9.4f} {f'{n_fmt(g)}':>24}")
        cmp_rows.append(dict(comparison="A stale regret", scope=f"delay {D} h",
                             reported_non_gap=n["mean"], protocol_all=a["mean"],
                             change=a["mean"] - n["mean"], gap_only=g["mean"],
                             protocol_lo=a["lo"], protocol_hi=a["hi"],
                             protocol_n=a["n"], gap_n=g["n"]))
    print("\n  Comparison B, paired gain of shrinkage over stale")
    for scope in ["6 h", "24 h", "pooled 6 and 24 h"]:
        a = allj[(allj.comparison == "B shrinkage vs stale")
                 & (allj.scope == scope)].iloc[0]
        n = ng[(ng.comparison == "B shrinkage vs stale")
               & (ng.scope == scope)].iloc[0]
        g = gapj[(gapj.comparison == "B shrinkage vs stale")
                 & (gapj.scope == scope)].iloc[0]
        print(f"  {scope:<18} reported {n['mean']:+.5f} "
              f"[{n['lo']:+.5f}, {n['hi']:+.5f}]   protocol {a['mean']:+.5f} "
              f"[{a['lo']:+.5f}, {a['hi']:+.5f}]   gap only {g['mean']:+.5f}")
        cmp_rows.append(dict(comparison="B shrinkage vs stale", scope=scope,
                             reported_non_gap=n["mean"], protocol_all=a["mean"],
                             change=a["mean"] - n["mean"], gap_only=g["mean"],
                             protocol_lo=a["lo"], protocol_hi=a["hi"],
                             protocol_n=a["n"], gap_n=g["n"]))
    pd.DataFrame(cmp_rows).to_csv(outdir / "H2_old_vs_new.csv", index=False)
    return out


def n_fmt(r):
    return f"{r['mean']:+.4f}[{r['lo']:+.3f},{r['hi']:+.3f}]"


def exploratory_window_mean(w, outdir):
    print("\n" + "=" * 74)
    print("WINDOW MEAN AGAINST STALE, BY DELAY, ON ALL JOBS. EXPLORATORY.")
    print("=" * 74)
    print("  Not a confirmatory comparison. PROTOCOL.md section 11 names only")
    print("  A and B, and says everything else must be labelled exploratory.")
    print("  gain = window mean minus stale, positive means window mean better")
    rng = fresh_rng()
    ww = w.copy()
    ww["gain_wm"] = ww["window_mean"] - ww["stale"]
    rows = []
    for D, g in ww.groupby("delay_h"):
        o, lo, hi, nd = ci(g, "gain_wm", rng)
        print(f"    EXPLORATORY  D={D:>3}h  n={len(g):>5}  {o:+.5f}  "
              f"[{lo:+.5f}, {hi:+.5f}]")
        rows.append(dict(status="EXPLORATORY", delay_h=D, n=len(g), mean=o,
                         lo=lo, hi=hi, days=nd))
    pd.DataFrame(rows).to_csv(outdir / "H3_window_mean_vs_stale_all_jobs.csv",
                              index=False)


# ------------------------------------------------ the four dead-qubit views

def dead_views(df, outdir):
    """The four views of 26_row_check.py, recomputed WITHOUT the gap filter.

    This mirrors 26_row_check.build_views exactly except that the final
    `w[~w.touches_gap]` step is not applied, so every view keeps all jobs.
    """
    print("\n" + "=" * 74)
    print("THE FOUR DEAD-QUBIT VIEWS, RECOMPUTED ON ALL JOBS")
    print("=" * 74)
    print("  Same construction as scripts/26_row_check.py, with the gap filter")
    print("  removed. EXPLORATORY and post-hoc, as it was there.")
    dead_rows = df[df.dead]
    jobs_any = set(map(tuple, dead_rows[JOB].drop_duplicates().to_numpy()))
    inf = dead_rows[dead_rows.arm.isin(INFORMED)]
    jobs_inf = set(map(tuple, inf[JOB].drop_duplicates().to_numpy()))
    w1 = M20.widen(df)
    keys = list(map(tuple, w1[JOB].to_numpy()))
    w1 = w1.assign(dead_any=[k in jobs_any for k in keys],
                   dead_informed=[k in jobs_inf for k in keys])
    z = df.copy()
    z.loc[z.dead, "fidelity"] = 0.0
    w3 = M20.widen(z)
    views = {
        "View 1 all rows": w1,
        "View 2a drop dead-qubit jobs in any arm": w1[~w1.dead_any],
        "View 2b drop dead-qubit jobs in an informed arm": w1[~w1.dead_informed],
        "View 3 dead rows forced to fidelity 0": w3,
    }
    print(f"  jobs with a dead-qubit row in any arm: {len(jobs_any)}")
    print(f"  jobs with a dead-qubit row in an informed arm: {len(jobs_inf)}")
    rows = []
    for name, vw in views.items():
        print(f"\n  {name}   n = {len(vw)} jobs")
        print(f"    stale regret by delay")
        rng = fresh_rng()
        cells = []
        for D, g in vw.groupby("delay_h"):
            o, lo, hi, nd = ci(g, "regret_stale", rng)
            cells.append(f"{D}h {o:+.4f}[{lo:+.3f},{hi:+.3f}]")
            rows.append(dict(view=name, metric="stale regret",
                             scope=f"delay {D} h", n=len(g), mean=o, lo=lo,
                             hi=hi, days=nd))
        print("      " + "  ".join(cells))
        rng = fresh_rng()
        sub = vw[vw.delay_h.isin(B_DELAYS)].copy()
        sub["gain"] = sub["shrinkage"] - sub["stale"]
        bits = []
        for scope, g in [("6 h", sub[sub.delay_h == 6]),
                         ("24 h", sub[sub.delay_h == 24]),
                         ("pooled 6 and 24 h", sub)]:
            o, lo, hi, nd = ci(g, "gain", rng)
            bits.append(f"{scope} {o:+.5f}[{lo:+.5f},{hi:+.5f}]")
            rows.append(dict(view=name, metric="B shrinkage vs stale",
                             scope=scope, n=len(g), mean=o, lo=lo, hi=hi,
                             days=nd))
        print(f"    Comparison B: " + "   ".join(bits))
    pd.DataFrame(rows).to_csv(outdir / "H4_dead_qubit_views_all_jobs.csv",
                              index=False)

    print("\n  SHARE OF SUMMED REGRET THAT SITS IN THE DEAD-QUBIT ROWS")
    print("  All jobs now, so the stale arm has its full 81 rows.")
    share = []
    keys = list(map(tuple, w1[JOB].to_numpy()))
    for arm in ["stale", "window_mean", "shrinkage"]:
        dead_keys = set(map(tuple, df[df.dead & (df.arm == arm)][JOB]
                            .drop_duplicates().to_numpy()))
        flag = np.array([k in dead_keys for k in keys])
        col = w1[f"regret_{arm}"].to_numpy()

        def block(mask, scope):
            tot, part = col[mask].sum(), col[mask & flag].sum()
            share.append(dict(arm=arm, scope=scope, n_jobs=int(mask.sum()),
                              n_dead_rows=int((mask & flag).sum()),
                              total_regret=tot, regret_in_dead_rows=part,
                              share_pct=(part / tot * 100) if tot else
                              float("nan")))
        block(np.ones(len(w1), bool), "overall")
        for D in sorted(w1.delay_h.unique()):
            block((w1.delay_h == D).to_numpy(), f"delay {D} h")
        for m in sorted(w1.machine.unique()):
            block((w1.machine == m).to_numpy(), f"machine {m}")
    sh = pd.DataFrame(share)
    print(sh.to_string(index=False, float_format=lambda x: f"{x:.4f}"))
    sh.to_csv(outdir / "H5_dead_row_regret_share_all_jobs.csv", index=False)
    return w1


def power_all_jobs(w1, outdir):
    print("\n" + "=" * 74)
    print("DESIGN EFFECT AND POWER, ON ALL JOBS. EXPLORATORY.")
    print("=" * 74)
    print("  Same helpers as scripts/26_row_check.py, imported not copied.")
    print("  gain = F_strategy minus F_stale.")
    w = w1.copy()
    w["gain_shrinkage"] = w["shrinkage"] - w["stale"]
    w["gain_window_mean"] = w["window_mean"] - w["stale"]
    w["day_str"] = w.day.astype(str)
    n_boot = M20.N_BOOT
    rows, store = [], {}
    for col in ["gain_shrinkage", "gain_window_mean"]:
        scopes = [(f"delay {D} h", w[w.delay_h == D])
                  for D in sorted(w.delay_h.unique())]
        scopes.append((f"pooled {POOL_DELAYS} h",
                       w[w.delay_h.isin(POOL_DELAYS)]))
        for scope, g in scopes:
            sd, n = g[col].std(ddof=1), len(g)
            naive = sd / math.sqrt(n)
            se_day, ncd = M26.cluster_boot_se(
                g, col, ["machine", "day_str"], fresh_rng(), n_boot,
                within="machine")
            se_sub, ncs = M26.cluster_boot_se(
                g, col, ["machine", "draw_order"], fresh_rng(), n_boot)
            icc, _, _, _, _ = M26.icc_oneway(
                g[col].to_numpy(),
                list(map(tuple, g[["machine", "day_str"]].to_numpy())))
            rows.append(dict(
                contrast=col.replace("gain_", "") + " minus stale",
                scope=scope, n_jobs=n, paired_sd=sd, naive_se=naive,
                se_boot_days_within_machine=se_day,
                se_boot_machine_submission=se_sub,
                design_effect_days=(se_day / naive) ** 2,
                design_effect_submission=(se_sub / naive) ** 2,
                icc_machine_day=icc))
            if scope.startswith("pooled"):
                store[col] = dict(sd=sd, de_day=(se_day / naive) ** 2,
                                  de_sub=(se_sub / naive) ** 2, icc=icc, n=n)
    out = pd.DataFrame(rows)
    print(out.to_string(index=False, float_format=lambda x: f"{x:.6f}"))
    out.to_csv(outdir / "H6_power_sd_se_all_jobs.csv", index=False)

    jobs_per_machine_day = 5 * len(POOL_DELAYS) * 3
    jobs_per_day = jobs_per_machine_day * 3
    prows = []
    for col, d in store.items():
        for de_name, de in (("days within machine", d["de_day"]),
                            ("machine and submission time", d["de_sub"])):
            for delta in (0.005, 0.01):
                for power in (0.80, 0.90):
                    n = M26.required_n(d["sd"], delta, power, de)
                    prows.append(dict(
                        contrast=col.replace("gain_", "") + " minus stale",
                        cluster_definition=de_name, design_effect=de,
                        paired_sd=d["sd"], effect=delta, power=power,
                        required_jobs=math.ceil(n),
                        required_machine_days=math.ceil(n / jobs_per_machine_day),
                        required_calendar_days=math.ceil(n / jobs_per_day)))
    p = pd.DataFrame(prows)
    print("\n  required jobs, n = DE * (z_0.975 + z_power)^2 * SD^2 / delta^2")
    print(p.to_string(index=False, float_format=lambda x: f"{x:.5f}"))
    p.to_csv(outdir / "H7_power_required_n_all_jobs.csv", index=False)
    return out, p


# ----------------------------------------- step 3: protocol conformance scan

CONFORMANCE = [
    dict(
        topic="Gap jobs, section 10",
        protocol='"The 22 to 23 September publishing gap stays in. It is not '
                 'deleted or patched. Results are reported with it included, '
                 'and the jobs that straddle it are reported separately so '
                 'its effect is visible." Reaffirmed by A1.6.',
        code='scripts/20_analyse_results.py: "main_set = w[~w.touches_gap]", '
             'then both confirmatory comparisons run on main_set. The gap set '
             'is printed separately under "THE 22 TO 23 SEPTEMBER GAP, '
             'reported separately (EXPLORATORY)".',
        verdict="DEPARTURE",
        note="The separate reporting is done, but the headline excludes the "
             "gap jobs instead of including them. This script supplies the "
             "included version. Found in L-052."),
    dict(
        topic="Comparison B pooling, section 11",
        protocol='"(B) per-field shrinkage against stale, at D = 6 hours and '
                 'D = 24 hours, pooled over machines and circuits, on the '
                 'test days only."',
        code='scripts/20_analyse_results.py: PRIMARY_B_DELAYS = [6, 24], then '
             '"sub = main_set[main_set.delay_h.isin(PRIMARY_B_DELAYS)]" and '
             'one block_boot over that combined set is printed as the '
             'headline, with the per-delay numbers printed under it.',
        verdict="DEPARTURE IN EMPHASIS",
        note="The protocol pools over machines and circuits AT EACH D, which "
             "is two numbers. Script 20 headlines a third number that also "
             "pools the two delays together. Both are printed, so no number "
             "is hidden, but the headlined one is not the one the protocol "
             "defines. This script reports the two per-delay numbers first."),
    dict(
        topic="Comparison B window, section 11",
        protocol='"on the test days only."',
        code='The results file carries label TEST only, and script 20 takes '
             'the file as given without re-filtering by date.',
        verdict="CONFORMS",
        note="Checked: every row in the file has label TEST, and every t_s "
             "falls on or after the A1.6 test start of 21 September."),
    dict(
        topic="Delays, section 3",
        protocol='"Delays D, in hours: 1, 3, 6, 12, 24, 48."',
        code='engine_config.DELAYS_H = [1, 3, 6, 12, 24, 48]; script 20 '
             'groups by delay_h and never filters a delay out.',
        verdict="CONFORMS", note=""),
    dict(
        topic="Circuits, section 5",
        protocol='"ghz5, ghz8, ghz10, bv8, bv10."',
        code='run_engine.CIRCUIT_ORDER lists exactly those five; script 20 '
             'never filters a circuit out and pools over them.',
        verdict="CONFORMS", note=""),
    dict(
        topic="Invalid jobs, section 3 and A1.7",
        protocol='"invalid jobs are dropped and counted, never silently '
                 'skipped ... The count dropped per D is reported." A1.7: '
                 '"Jobs whose truth state falls outside the data are dropped '
                 'and counted, with the count reported per delay D."',
        code='engine/jobs.py build_jobs returns (jobs, dropped) and the run '
             'log records the per-delay counts. scripts/20_analyse_results.py '
             'does NOT print them; scripts/24_prereg_outputs.py does, as '
             'P7_dropped_jobs_per_delay.csv.',
        verdict="CONFORMS ELSEWHERE",
        note="The obligation is met, but by script 24 rather than by the "
             "headline script. Worth knowing when reading script 20 alone."),
    dict(
        topic="Three result axes, section 9",
        protocol='"Every result is reported against all three of these: '
                 'queue delay D; age at run time of the cz numbers; number of '
                 'new states between t_s and t_r." Readout age "shown '
                 'separately, never merged".',
        code='scripts/20_analyse_results.py reports delay and new states. The '
             'cz age axis and the separate readout age live in '
             'scripts/24_prereg_outputs.py as P1, P1b, P2 and P2b.',
        verdict="CONFORMS ELSEWHERE",
        note="Same shape as the row above: the axis exists, in script 24."),
    dict(
        topic="Secondary metric, section 8",
        protocol='"analytic estimated success probability ... reported '
                 'alongside the simulated fidelity, never instead of it."',
        code='The engine writes an esp column for every row. Script 20 does '
             'not print ESP; scripts/24_prereg_outputs.py does, as '
             'P3_esp_alongside_fidelity.csv.',
        verdict="CONFORMS ELSEWHERE", note=""),
    dict(
        topic="Bootstrap unit, section 11",
        protocol='"a block bootstrap that resamples WHOLE DAYS, so jobs from '
                 'the same day stay together."',
        code='scripts/20_analyse_results.py block_boot resamples '
             'frame.day.unique(), where day is the calendar date of t_s, '
             'pooled across machines.',
        verdict="CONFORMS",
        note="A calendar day, not a machine-day. Section 17 risk 4 names "
             "machine-days as the alternative and declines it, because the "
             "gap was platform wide, so the calendar day is the choice the "
             "protocol points to."),
    dict(
        topic="Dead qubit rule, section 7",
        protocol='"dead if sx_error > 0.1 or readout_error > 0.2 or T1 '
                 'missing or T2 missing", applied to the state THAT STRATEGY '
                 'SEES, with permanent defects excluded for every strategy.',
        code='engine_config.SX_DEAD = 0.1, RO_DEAD = 0.2; '
             'real_data.strategy_target forbids dead_qubits(snap) plus the '
             'permanent set. Permanent defects come from training days only, '
             'which is Amendment A1.5.',
        verdict="CONFORMS", note="A1.5 covers the training-only change."),
    dict(
        topic="Tie handling in the shrinkage tuning",
        protocol="Section 6 says N and w are tuned on training days and "
                 "recorded in an amendment before test days are touched. It "
                 "sets no tie-break rule.",
        code='engine_config.py: "Chosen by the pre-registered rule: lowest '
             'mean ESP regret vs the ceiling, ties to smaller N, then to '
             'smaller total w."',
        verdict="CONFORMS VIA AMENDMENT",
        note="The tie-break is in Amendment A2, and A2.2 records honestly "
             "that w_times was settled by the tie-break and not by evidence; "
             "A3.1 later fixed it by evidence instead."),
    dict(
        topic="Sanity checks, section 12",
        protocol="Four checks, and no number may be reported until all pass.",
        code='scripts/20_analyse_results.py sanity() implements all four and '
             'exits 1 unless --allow-failed-checks is given.',
        verdict="CONFORMS", note=""),
    dict(
        topic="No-change share, section 13",
        protocol='"For every D, report the share of jobs where no new state '
                 'appeared between t_s and t_r."',
        code='scripts/20_analyse_results.py prints the no-change share in the '
             'Comparison A table for every delay.',
        verdict="CONFORMS", note=""),
    dict(
        topic="Exploratory labelling, section 11",
        protocol='"Everything else is exploratory and must be labelled '
                 'exploratory wherever it appears."',
        code='scripts/20_analyse_results.py prints "EXPLORATORY from here '
             'down. Not confirmatory. Do not headline." before the rest.',
        verdict="CONFORMS", note=""),
    dict(
        topic="Split dates, section 10",
        protocol='"Training days: 28 August to 28 September 2026 (32 days). '
                 'Test days: 29 September to 12 October 2026 (14 days)."',
        code='engine_config.TRAIN_END = "2026-09-20", TEST_START = '
             '"2026-09-21".',
        verdict="CONFORMS VIA AMENDMENT",
        note="Amendment A1.6 moved the split to 24 training and 22 test days "
             "and recorded the consequence that the gap moved into the test "
             "window."),
]


def conformance(df, w, outdir):
    print("\n" + "=" * 74)
    print("STEP 3: EVERY CHOICE THE ANALYSIS CODE MAKES, AGAINST THE PROTOCOL")
    print("=" * 74)
    print("  Read from PROTOCOL.md in full plus PROTOCOL_AMENDMENTS.md.")
    print("  NOTHING IS FIXED HERE. This is a list, not a change.")
    print(f"\n  checks that the two CONFORMS claims above rest on:")
    print(f"    rows whose label is not TEST: "
          f"{int((df.label != 'TEST').sum())}")
    print(f"    earliest t_s in the file: {df.t_s.min()}")
    print(f"    A1.6 test window starts:  2026-09-21")
    print(f"    delays present: {[int(x) for x in sorted(w.delay_h.unique())]}")
    print(f"    circuits present: {sorted(w.circuit.unique())}")
    for i, c in enumerate(CONFORMANCE, 1):
        print(f"\n  {i}. {c['topic']}")
        print(f"     VERDICT: {c['verdict']}")
        print(f"     protocol says: {c['protocol']}")
        print(f"     code does:     {c['code']}")
        if c["note"]:
            print(f"     note:          {c['note']}")
    tab = pd.DataFrame(CONFORMANCE)
    tab.to_csv(outdir / "H8_protocol_conformance.csv", index=False)
    dep = tab[tab.verdict.str.startswith("DEPARTURE")]
    print(f"\n  departures found: {len(dep)} of {len(tab)} items checked")
    for _, r in dep.iterrows():
        print(f"    {r['verdict']:<22} {r['topic']}")
    print("  Neither is fixed by this script beyond supplying the")
    print("  protocol-faithful numbers alongside the reported ones.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results",
                    default=str(ROOT / "outputs/test_full/all_rows.csv"))
    ap.add_argument("--outdir",
                    default=str(ROOT / "outputs/protocol_headline"))
    args = ap.parse_args()
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    print("PROTOCOL-FAITHFUL HEADLINE. FIX FORWARD, NOTHING OVERWRITTEN.")
    print("No IBM call. No new simulation. data/raw untouched.")
    print("scripts/20_analyse_results.py is NOT edited and no existing output")
    print("file is replaced. The method, seed and resample count are imported")
    print("from it; only the job selection differs.")
    print("regret = ceiling minus strategy. gain = F_strategy minus F_stale.")
    print(f"source: {args.results}\n")

    df = M20.load(args.results)
    df["dead"] = df.dead_qubits_used.fillna("").astype(str).str.strip() != ""
    w = M20.widen(df)

    headline(w, outdir)
    exploratory_window_mean(w, outdir)
    w1 = dead_views(df, outdir)
    power_all_jobs(w1, outdir)
    conformance(df, w, outdir)
    print(f"\nfiles written to {outdir}")
    print("Confirmatory parts are A and B only. Everything else is labelled")
    print("EXPLORATORY. Where this touches measurement noise against real")
    print("drift, the wording is 'consistent with'.")


main()
