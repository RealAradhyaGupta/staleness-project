"""Row check for the 1025 truth-dead-qubit rows, plus a power calibration.

OURS. EXPLORATORY AND POST-HOC. Nothing here is confirmatory. No new
simulation was run, no IBM call was made, nothing in data/raw was touched, and
no confirmatory number or file already reported was changed. This script only
re-reads the frozen results file outputs/test_full/all_rows.csv.

SIGN CONVENTION, used everywhere in this file and in every file it writes:
    regret = ceiling minus strategy      (positive means the strategy is worse)
    gain   = F_strategy minus F_stale    (positive means the strategy is better)

What it does.
  Part 1, four views of the same frozen rows:
    View 1   all rows as they are, the current numbers.
    View 2a  drop every job that has a dead-qubit row in ANY arm, in all arms
             together, so the pairing across arms is kept.
    View 2b  drop every job where any INFORMED arm (stale, window mean,
             std-adjusted, shrinkage) has a dead-qubit row. The random arm is
             ignored when deciding.
    View 3   keep all rows, but set the fidelity of every dead-qubit row to 0,
             the worst case, so its regret becomes ceiling minus 0.
  Part 2, a power calibration from View 1 only: paired SDs, naive against
  clustered standard errors, the design effect, the ICC by (machine, day), and
  the number of jobs needed for 80 and 90 percent power.

Gap jobs. Jobs whose submission-to-run interval overlaps a 22 to 23 September
publishing gap are excluded in every view, exactly as PROTOCOL.md section 10
requires and as the reported confirmatory numbers already do. That is why
View 1 reproduces the headline table.

The bootstrap. The interval function, the seed (20261014) and the number of
resamples (4000) are taken from scripts/20_analyse_results.py by importing
that file, not by copying the code. The random generator is re-seeded at the
start of each block, so each block's numbers do not depend on how many
bootstrap calls ran before it.

Wording rule from L-032: say "consistent with", never "proved".

Usage:  26_row_check.py [--results ...] [--outdir outputs/row_check]
"""
import argparse
import math
import types
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
ARMS = ["random", "stale", "window_mean", "std_adjusted", "shrinkage", "ceiling"]
STRATS = [a for a in ARMS if a != "ceiling"]
INFORMED = ["stale", "window_mean", "std_adjusted", "shrinkage"]
JOB = ["machine", "draw_order", "delay_h", "circuit"]
POOL_DELAYS = [6, 12, 24, 48]
B_DELAYS = [6, 24]

# Step 0 of the task, typed in so any mismatch is printed and not eyeballed.
EXPECT = dict(
    rows=33888, jobs=5648, arms=6, dead_rows=1025, dead_jobs=842,
    by_arm={"random": 786, "stale": 81, "window_mean": 42,
            "std_adjusted": 50, "shrinkage": 66, "ceiling": 0},
    marrakesh=729,
    stale_regret={1: 0.0059, 3: 0.0171, 6: 0.0230, 12: 0.0259,
                  24: 0.0245, 48: 0.0367},
    b_pooled=0.00176, b_6=0.00345, b_24=-0.00003,
)
TOL = 0.0005
Z = {0.80: 0.8416212336, 0.90: 1.2815515655, "two_sided_05": 1.9599639845}


def load_script20():
    """Import scripts/20_analyse_results.py for its bootstrap, seed and count.

    That file calls main() at the bottom, so it cannot simply be imported.
    The trailing call is dropped and the rest is executed as a module, which
    reuses the real function instead of copying it.
    """
    path = ROOT / "scripts/20_analyse_results.py"
    src = path.read_text().rsplit("\nmain()", 1)[0]
    mod = types.ModuleType("analyse20")
    mod.__file__ = str(path)
    exec(compile(src, str(path), "exec"), mod.__dict__)
    return mod


M20 = load_script20()


def fresh_rng():
    return np.random.default_rng(M20.SEED_BOOT)


def ci(frame, col, rng=None):
    """Mean and 95 percent interval from script 20's whole-day block bootstrap."""
    if len(frame) == 0:
        return (float("nan"),) * 3 + (0,)
    return M20.block_boot(frame, col, rng if rng is not None else fresh_rng())


# ----------------------------------------------------------------- the views

def build_views(df):
    """Return {view name: wide frame}, gap jobs already dropped."""
    dead_rows = df[df.dead]
    jobs_any = set(map(tuple, dead_rows[JOB].drop_duplicates().to_numpy()))
    inf = dead_rows[dead_rows.arm.isin(INFORMED)]
    jobs_inf = set(map(tuple, inf[JOB].drop_duplicates().to_numpy()))

    w1 = M20.widen(df)
    keys1 = list(map(tuple, w1[JOB].to_numpy()))
    w1 = w1.assign(dead_any=[k in jobs_any for k in keys1],
                   dead_informed=[k in jobs_inf for k in keys1])

    z = df.copy()
    z.loc[z.dead, "fidelity"] = 0.0
    w3 = M20.widen(z)

    main = lambda w: w[~w.touches_gap].copy()
    return {
        "View 1 all rows": main(w1),
        "View 2a drop dead-qubit jobs in any arm": main(w1[~w1.dead_any]),
        "View 2b drop dead-qubit jobs in an informed arm":
            main(w1[~w1.dead_informed]),
        "View 3 dead rows forced to fidelity 0": main(w3),
    }, jobs_any, jobs_inf


def report_view(name, w, rows_sr, rows_all, rows_b, rows_wm, rows_mach):
    print("\n" + "=" * 74)
    print(name.upper())
    print("=" * 74)
    print(f"  jobs used: {len(w)}   days: {w.day.nunique()}   "
          f"machines: {sorted(w.machine.unique())}")

    print("\n  stale regret by delay (regret = ceiling minus stale, "
          "positive means stale is worse)")
    print(f"  {'D (h)':>6} {'n':>6} {'mean':>10} {'95 pct interval':>24} "
          f"{'days':>5}")
    rng = fresh_rng()
    for D, g in w.groupby("delay_h"):
        o, lo, hi, nd = ci(g, "regret_stale", rng)
        print(f"  {D:>6} {len(g):>6} {o:>+10.4f}   [{lo:>+8.4f}, {hi:>+8.4f}]"
              f" {nd:>5}")
        rows_sr.append(dict(view=name, delay_h=D, n=len(g), mean=o, lo=lo,
                            hi=hi, days=nd))

    print("\n  mean regret of every strategy by delay, with intervals")
    rng = fresh_rng()
    for s in STRATS:
        line = []
        for D, g in w.groupby("delay_h"):
            o, lo, hi, nd = ci(g, f"regret_{s}", rng)
            rows_all.append(dict(view=name, strategy=s, delay_h=D, n=len(g),
                                 mean=o, lo=lo, hi=hi, days=nd))
            line.append(f"{D}h {o:+.4f} [{lo:+.4f},{hi:+.4f}]")
        print(f"    {s:<13} " + "  ".join(line))

    print("\n  Comparison B, shrinkage against stale, paired "
          "(gain = shrinkage minus stale, positive means shrinkage is better)")
    rng = fresh_rng()
    sub = w[w.delay_h.isin(B_DELAYS)].copy()
    sub["gain"] = sub["shrinkage"] - sub["stale"]
    for scope, g in [("pooled 6 and 24 h", sub)] + \
            [(f"{D} h", sub[sub.delay_h == D]) for D in B_DELAYS]:
        o, lo, hi, nd = ci(g, "gain", rng)
        verdict = ("shrinkage better" if lo > 0 else "stale better" if hi < 0
                   else "interval includes zero, no difference")
        print(f"    {scope:<20} n={len(g):>5}  {o:+.5f}  "
              f"[{lo:+.5f}, {hi:+.5f}]  {verdict}")
        rows_b.append(dict(view=name, scope=scope, n=len(g), mean=o, lo=lo,
                           hi=hi, verdict=verdict))

    print("\n  window mean against stale by delay, EXPLORATORY "
          "(gain = window mean minus stale, positive means window mean better)")
    rng = fresh_rng()
    ww = w.copy()
    ww["gain_wm"] = ww["window_mean"] - ww["stale"]
    for D, g in ww.groupby("delay_h"):
        o, lo, hi, nd = ci(g, "gain_wm", rng)
        print(f"    EXPLORATORY  D={D:>3}h  n={len(g):>5}  {o:+.5f}  "
              f"[{lo:+.5f}, {hi:+.5f}]")
        rows_wm.append(dict(view=name, delay_h=D, n=len(g), mean=o, lo=lo,
                            hi=hi, days=nd, status="EXPLORATORY"))

    print("\n  by machine: mean stale regret by delay, with intervals")
    rng = fresh_rng()
    for m, gm in w.groupby("machine"):
        line = []
        for D, g in gm.groupby("delay_h"):
            o, lo, hi, nd = ci(g, "regret_stale", rng)
            rows_mach.append(dict(view=name, machine=m, delay_h=D, n=len(g),
                                  mean_stale_regret=o, lo=lo, hi=hi, days=nd))
            line.append(f"{D}h {o:+.4f}")
        print(f"    {m:<15} n={len(gm):>5}  " + "  ".join(line))
    print("\n  by machine: pooled mean regret of every strategy")
    for m, gm in w.groupby("machine"):
        print(f"    {m:<15} " + "  ".join(
            f"{s} {gm[f'regret_{s}'].mean():+.4f}" for s in STRATS))


# ------------------------------------------------- dead rows and total regret

def regret_share(df, w1, outdir):
    """How much of each arm's total regret sits in its own dead-qubit rows."""
    print("\n" + "=" * 74)
    print("SHARE OF TOTAL REGRET THAT COMES FROM THE DEAD-QUBIT ROWS")
    print("=" * 74)
    print("  View 1 rows, gap jobs excluded. Regret is summed, not averaged.")
    rows = []
    keys = list(map(tuple, w1[JOB].to_numpy()))
    for arm in ["stale", "window_mean", "shrinkage"]:
        dead_keys = set(map(tuple, df[df.dead & (df.arm == arm)][JOB]
                            .drop_duplicates().to_numpy()))
        flag = np.array([k in dead_keys for k in keys])
        col = w1[f"regret_{arm}"].to_numpy()
        def block(mask, scope):
            tot, part = col[mask].sum(), col[mask & flag].sum()
            n_dead = int((mask & flag).sum())
            rows.append(dict(arm=arm, scope=scope, n_jobs=int(mask.sum()),
                             n_dead_rows=n_dead, total_regret=tot,
                             regret_in_dead_rows=part,
                             share_pct=(part / tot * 100) if tot else float("nan")))
        block(np.ones(len(w1), bool), "overall")
        for D in sorted(w1.delay_h.unique()):
            block((w1.delay_h == D).to_numpy(), f"delay {D} h")
        for m in sorted(w1.machine.unique()):
            block((w1.machine == m).to_numpy(), f"machine {m}")
    out = pd.DataFrame(rows)
    print(out.to_string(index=False, float_format=lambda x: f"{x:.4f}"))
    out.to_csv(outdir / "dead_row_regret_share.csv", index=False)
    return out


def dead_vs_other_fidelity(df, outdir):
    print("\n" + "=" * 74)
    print("MEAN REAL SIMULATED FIDELITY: DEAD-QUBIT ROWS AGAINST OTHER ROWS")
    print("=" * 74)
    print("  These are the fidelities the engine really simulated, not the")
    print("  forced zeros of View 3. Gap jobs excluded.")
    rows = []
    for arm in ARMS:
        sub = df[df.arm == arm]
        d, o = sub[sub.dead], sub[~sub.dead]
        rows.append(dict(arm=arm, n_dead_rows=len(d), n_other_rows=len(o),
                         mean_fidelity_dead=d.fidelity.mean() if len(d) else float("nan"),
                         mean_fidelity_other=o.fidelity.mean(),
                         difference=(d.fidelity.mean() - o.fidelity.mean())
                         if len(d) else float("nan")))
    out = pd.DataFrame(rows)
    print(out.to_string(index=False, float_format=lambda x: f"{x:.4f}"))
    print("\n  Note on the random arm. engine/run_engine.py averages the")
    print("  fidelity over RANDOM_DRAWS = 5 separate layouts but writes the")
    print("  UNION of the qubits those 5 layouts touched, so the random arm")
    print("  gets flagged far more often than the single-layout arms. Its")
    print("  row count is not comparable with the informed arms' counts.")
    print("  The counts here are smaller than the 1025 of Step 0 because gap")
    print("  jobs are excluded; the full 1025 count includes them.")
    out.to_csv(outdir / "dead_vs_other_fidelity.csv", index=False)
    return out


# ----------------------------------------------------------- Part 2, power

def icc_oneway(values, groups):
    """One-way random effects ICC with unequal group sizes (ANOVA estimator)."""
    pools = defaultdict(list)
    for v, g in zip(values, groups):
        pools[g].append(v)
    pools = {g: np.asarray(v, float) for g, v in pools.items() if len(v) > 0}
    k, N = len(pools), sum(len(v) for v in pools.values())
    if k < 2 or N <= k:
        return float("nan"), float("nan"), float("nan"), k, N
    grand = np.concatenate(list(pools.values())).mean()
    ssb = sum(len(v) * (v.mean() - grand) ** 2 for v in pools.values())
    ssw = sum(((v - v.mean()) ** 2).sum() for v in pools.values())
    msb, msw = ssb / (k - 1), ssw / (N - k)
    n_sizes = np.array([len(v) for v in pools.values()], float)
    n0 = (N - (n_sizes ** 2).sum() / N) / (k - 1)
    var_a = (msb - msw) / n0
    icc = var_a / (var_a + msw) if (var_a + msw) != 0 else float("nan")
    return icc, var_a, msw, k, N


def cluster_boot_se(frame, col, cluster_cols, rng, n_boot, within=None):
    """SE of the mean from resampling whole clusters with replacement.

    within: a column name. If given, clusters are resampled inside each level
    of that column (so the number of clusters per machine is held fixed).
    """
    keys = list(map(tuple, frame[cluster_cols].to_numpy()))
    pools = defaultdict(list)
    for k, v in zip(keys, frame[col].to_numpy()):
        pools[k].append(v)
    pools = {k: np.asarray(v, float) for k, v in pools.items()}
    if within is None:
        strata = {"all": list(pools)}
    else:
        strata = defaultdict(list)
        wcol = frame[within].to_numpy()
        seen = {}
        for k, wv in zip(keys, wcol):
            seen.setdefault(k, wv)
        for k, wv in seen.items():
            strata[wv].append(k)
    means = np.empty(n_boot)
    for i in range(n_boot):
        picked = []
        for ks in strata.values():
            idx = rng.integers(0, len(ks), size=len(ks))
            picked.extend(ks[j] for j in idx)
        means[i] = np.concatenate([pools[k] for k in picked]).mean()
    return float(means.std(ddof=1)), len(pools)


def required_n(sd, delta, power, design_effect):
    """Paired two-sided test at alpha 0.05, inflated by the design effect.

        n = DE * (z_(1-alpha/2) + z_(power))^2 * SD^2 / delta^2
    """
    z = Z["two_sided_05"] + Z[power]
    return design_effect * (z ** 2) * (sd ** 2) / (delta ** 2)


def power_part(w1, outdir):
    print("\n" + "=" * 74)
    print("PART 2: POWER CALIBRATION (View 1 only, gap jobs excluded)")
    print("=" * 74)
    print("  gain = F_strategy minus F_stale, positive means the strategy is")
    print("  better. All of Part 2 is EXPLORATORY and post-hoc.")
    w = w1.copy()
    w["gain_shrinkage"] = w["shrinkage"] - w["stale"]
    w["gain_window_mean"] = w["window_mean"] - w["stale"]
    w["day_str"] = w.day.astype(str)
    n_boot = M20.N_BOOT

    rows, de_store = [], {}
    for col in ["gain_shrinkage", "gain_window_mean"]:
        scopes = [(f"delay {D} h", w[w.delay_h == D]) for D in
                  sorted(w.delay_h.unique())]
        scopes.append((f"pooled {POOL_DELAYS} h",
                       w[w.delay_h.isin(POOL_DELAYS)]))
        for scope, g in scopes:
            sd, n = g[col].std(ddof=1), len(g)
            naive = sd / math.sqrt(n)
            rng = fresh_rng()
            se_day, n_cl_day = cluster_boot_se(
                g, col, ["machine", "day_str"], rng, n_boot, within="machine")
            rng = fresh_rng()
            se_sub, n_cl_sub = cluster_boot_se(
                g, col, ["machine", "draw_order"], rng, n_boot)
            de_day = (se_day / naive) ** 2
            de_sub = (se_sub / naive) ** 2
            icc, va, msw, k, N = icc_oneway(
                g[col].to_numpy(), list(map(tuple, g[["machine", "day_str"]]
                                            .to_numpy())))
            rows.append(dict(
                contrast=col.replace("gain_", "") + " minus stale",
                scope=scope, n_jobs=n, paired_sd=sd, naive_se=naive,
                se_boot_days_within_machine=se_day, n_day_clusters=n_cl_day,
                se_boot_machine_submission=se_sub, n_sub_clusters=n_cl_sub,
                design_effect_days=de_day, design_effect_submission=de_sub,
                icc_machine_day=icc))
            if scope.startswith("pooled"):
                de_store[col] = dict(sd=sd, de_day=de_day, de_sub=de_sub,
                                     icc=icc, n=n)
    out = pd.DataFrame(rows)
    print("\n  paired SD, standard errors and design effects")
    print(out.to_string(index=False, float_format=lambda x: f"{x:.6f}"))
    out.to_csv(outdir / "power_sd_se_designeffect.csv", index=False)

    print("\n  Two notes on the table above. A design effect below 1 means")
    print("  the clustered standard error came out SMALLER than the naive one,")
    print("  which happens when the gain varies less between days than inside")
    print("  a day; at a single delay there are only about 15 jobs per")
    print("  machine-day, so these single-delay design effects are themselves")
    print("  noisy. A negative ICC is what the one-way ANOVA estimator returns")
    print("  when the between-day variance is estimated at or below zero; it")
    print("  is consistent with no day-level clustering at that delay, not")
    print("  with a real negative correlation. The pooled rows are the ones to")
    print("  use, because pooling four delays inside the same day is where the")
    print("  clustering actually bites.")
    print("\n  ICC by (machine, day), on the paired gain")
    for col, d in de_store.items():
        print(f"    {col:<22} pooled ICC {d['icc']:+.5f}")

    print("\n  required number of JOBS for 80 and 90 percent power")
    print("  formula: n = DE * (z_0.975 + z_power)^2 * SD^2 / delta^2")
    print("  (paired, two-sided alpha 0.05; DE is the measured design effect)")
    jobs_per_machine_day = 5 * len(POOL_DELAYS) * 3   # circuits x delays x subs
    jobs_per_day = jobs_per_machine_day * 3           # three machines
    prows = []
    for col, d in de_store.items():
        for de_name, de in (("days within machine", d["de_day"]),
                            ("machine and submission time", d["de_sub"])):
            for delta in (0.005, 0.01):
                for power in (0.80, 0.90):
                    n = required_n(d["sd"], delta, power, de)
                    prows.append(dict(
                        contrast=col.replace("gain_", "") + " minus stale",
                        cluster_definition=de_name, design_effect=de,
                        paired_sd=d["sd"], effect=delta,
                        power=power, required_jobs=math.ceil(n),
                        required_machine_days=math.ceil(n / jobs_per_machine_day),
                        required_calendar_days=math.ceil(n / jobs_per_day)))
    p = pd.DataFrame(prows)
    print(p.to_string(index=False, float_format=lambda x: f"{x:.5f}"))
    p.to_csv(outdir / "power_required_n.csv", index=False)
    print(f"\n  day counting assumes the Round 1 shape: 5 circuits x "
          f"{len(POOL_DELAYS)} delays x 3 submissions = "
          f"{jobs_per_machine_day} jobs per machine-day,")
    print(f"  and {jobs_per_day} jobs per calendar day across all three "
          f"machines.")
    return out, p, de_store


# ------------------------------------------------------------- window facts

def window_facts(outdir, df):
    print("\n" + "=" * 74)
    print("THE STUDY WINDOW, 28 AUGUST TO 12 OCTOBER 2026")
    print("=" * 74)
    cq = pd.read_csv(ROOT / "data/clean/card_quality.csv")
    st = pd.read_csv(ROOT / "data/clean/states.csv")
    in_win = cq[(cq.snapshot_utc >= "2026-08-28") & (cq.snapshot_utc < "2026-10-13")]
    raw_counts = {}
    for m in ["ibm_fez", "ibm_kingston", "ibm_marrakesh"]:
        names = [p.name for p in (ROOT / "data/raw" / m).iterdir()
                 if p.name[0].isdigit()]
        raw_counts[m] = dict(
            total=len(names),
            before=sum(1 for n in names if n[:10] < "2026-08-28"),
            in_window=sum(1 for n in names
                          if "2026-08-28" <= n[:10] <= "2026-10-12"),
            after=sum(1 for n in names if n[:10] > "2026-10-12"))
    print(f"  calibration cards in the window: {len(in_win)}")
    print(f"  distinct calibration states in the window: {len(st)}")
    print(f"  card timestamps run {cq.snapshot_utc.min()} to "
          f"{cq.snapshot_utc.max()}")
    print("\n  raw card files per machine:")
    for m, c in raw_counts.items():
        print(f"    {m:<15} total {c['total']:>5}  before 28 Aug "
              f"{c['before']:>4}  in window {c['in_window']:>5}  "
              f"after 12 Oct {c['after']:>3}")
    after_raw = sum(c["after"] for c in raw_counts.values())
    print(f"\n  raw card files dated after 12 October: {after_raw}")
    qb = pd.read_csv(ROOT / "data/clean/qubits.csv", usecols=["snapshot_utc"])
    pr = pd.read_csv(ROOT / "data/clean/pairs.csv", usecols=["snapshot_utc"])
    print(f"  data/clean/qubits.csv runs {qb.snapshot_utc.min()} to "
          f"{qb.snapshot_utc.max()}")
    print(f"  data/clean/pairs.csv  runs {pr.snapshot_utc.min()} to "
          f"{pr.snapshot_utc.max()}")
    print("  These two tables reach BACK to 15 June, from the earlier 120 day")
    print("  download. They do not reach forward past 12 October.")
    print(f"  results file: t_s max {df.t_s.max()}   t_r max {df.t_r.max()}")
    print("  No file checked here holds any data dated after 12 October 2026.")
    rows = [dict(item="calibration cards in window (28 Aug to 12 Oct)",
                 value=len(in_win)),
            dict(item="distinct calibration states in window", value=len(st)),
            dict(item="raw card files total (all three machines)",
                 value=sum(c["total"] for c in raw_counts.values())),
            dict(item="raw card files before 28 Aug",
                 value=sum(c["before"] for c in raw_counts.values())),
            dict(item="raw card files in window",
                 value=sum(c["in_window"] for c in raw_counts.values())),
            dict(item="raw card files after 12 Oct", value=after_raw),
            dict(item="earliest row in data/clean/qubits.csv",
                 value=qb.snapshot_utc.min()),
            dict(item="latest row in data/clean/qubits.csv",
                 value=qb.snapshot_utc.max()),
            dict(item="latest t_r in results file", value=str(df.t_r.max()))]
    pd.DataFrame(rows).to_csv(outdir / "window_facts.csv", index=False)
    return len(in_win), len(st), after_raw


# ------------------------------------------------------------------ step 0

def step0(df, outdir):
    print("=" * 74)
    print("STEP 0: SANITY CHECKS. Nothing is reported if any of these fails.")
    print("=" * 74)
    fails = []

    def chk(name, got, want, tol=0):
        ok = abs(got - want) <= tol
        print(f"  {name:<46} got {got!s:>12}  want {want!s:>12}  "
              f"{'ok' if ok else 'FAIL'}")
        if not ok:
            fails.append(name)

    chk("rows", len(df), EXPECT["rows"])
    chk("jobs", df.groupby(JOB).ngroups, EXPECT["jobs"])
    chk("strategies", df.arm.nunique(), EXPECT["arms"])
    chk("dead-qubit rows", int(df.dead.sum()), EXPECT["dead_rows"])
    chk("jobs holding a dead-qubit row",
        df[df.dead].groupby(JOB).ngroups, EXPECT["dead_jobs"])
    counts = df[df.dead].groupby("arm").size()
    for arm, want in EXPECT["by_arm"].items():
        chk(f"dead-qubit rows, {arm}", int(counts.get(arm, 0)), want)
    chk("dead-qubit rows on ibm_marrakesh",
        int(df[df.dead].groupby("machine").size().get("ibm_marrakesh", 0)),
        EXPECT["marrakesh"])

    w = M20.widen(df)
    main = w[~w.touches_gap]
    print(f"\n  reproducing the reported numbers with script 20's bootstrap "
          f"(seed {M20.SEED_BOOT}, {M20.N_BOOT} resamples), tolerance {TOL}")
    rng = fresh_rng()
    for D, g in main.groupby("delay_h"):
        o, lo, hi, nd = ci(g, "regret_stale", rng)
        chk(f"stale regret at {D} h", round(o, 5),
            EXPECT["stale_regret"][D], TOL)
    rng = fresh_rng()
    sub = main[main.delay_h.isin(B_DELAYS)].copy()
    sub["gain"] = sub["shrinkage"] - sub["stale"]
    o, lo, hi, nd = ci(sub, "gain", rng)
    chk("Comparison B pooled", round(o, 6), EXPECT["b_pooled"], TOL)
    for D in B_DELAYS:
        g = sub[sub.delay_h == D]
        o2, _, _, _ = ci(g, "gain", rng)
        chk(f"Comparison B at {D} h", round(o2, 6),
            EXPECT[f"b_{D}"], TOL)

    if fails:
        print(f"\n=== SANITY CHECKS FAILED: {fails}. NOTHING REPORTED. ===")
        raise SystemExit(1)
    print("\n  every Step 0 check passed.")
    return w


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default=str(ROOT / "outputs/test_full/all_rows.csv"))
    ap.add_argument("--outdir", default=str(ROOT / "outputs/row_check"))
    args = ap.parse_args()
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    print("ROW CHECK OF THE 1025 DEAD-QUBIT ROWS, PLUS A POWER CALIBRATION")
    print("EXPLORATORY AND POST-HOC. No new simulation. No IBM call.")
    print("regret = ceiling minus strategy. gain = F_strategy minus F_stale.")
    print(f"source: {args.results}\n")

    df = M20.load(args.results)
    df["dead"] = df.dead_qubits_used.fillna("").astype(str).str.strip() != ""

    w_all = step0(df, outdir)
    views, jobs_any, jobs_inf = build_views(df)
    print(f"\n  jobs with a dead-qubit row in any arm: {len(jobs_any)}")
    print(f"  jobs with a dead-qubit row in an informed arm: {len(jobs_inf)}")

    rows_sr, rows_all, rows_b, rows_wm, rows_mach = [], [], [], [], []
    print("\n" + "#" * 74)
    print("PART 1: FOUR VIEWS")
    print("#" * 74)
    for name, w in views.items():
        report_view(name, w, rows_sr, rows_all, rows_b, rows_wm, rows_mach)

    pd.DataFrame(rows_sr).to_csv(outdir / "views_stale_regret.csv", index=False)
    pd.DataFrame(rows_all).to_csv(outdir / "views_regret_all_strategies.csv",
                                  index=False)
    pd.DataFrame(rows_b).to_csv(outdir / "views_comparison_b.csv", index=False)
    pd.DataFrame(rows_wm).to_csv(outdir / "views_window_mean_vs_stale.csv",
                                 index=False)
    pd.DataFrame(rows_mach).to_csv(outdir / "views_by_machine.csv", index=False)

    v1 = views["View 1 all rows"]
    main_rows = df[~df.set_index(JOB).index.isin(
        set(map(tuple, w_all[w_all.touches_gap][JOB].to_numpy())))]
    regret_share(df, v1, outdir)
    dead_vs_other_fidelity(main_rows, outdir)
    power_part(v1, outdir)
    window_facts(outdir, df)
    print(f"\nfiles written to {outdir}")
    print("EXPLORATORY AND POST-HOC throughout. Where this touches measurement")
    print("noise against real drift, the wording is 'consistent with'.")


main()
