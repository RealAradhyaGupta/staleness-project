"""Round 2 analysis. Written from protocol_round2.md, run once on the fresh rows.

Nothing is excluded except what protocol_round2.md declares. In particular the
jobs that straddle a publishing gap STAY IN and are reported separately, which
is PROTOCOL.md section 10 carried forward. Round 1's headline script departed
from that and the departure is recorded in L-052 and L-053; this script does
not repeat it.

The bootstrap is Round 1's, imported from scripts/20_analyse_results.py so it
is literally the same function with the same seed and the same number of
resamples: whole calendar days are resampled, as PROTOCOL.md section 11 says.

Sign conventions:
  regret = ceiling minus strategy (positive means the strategy is worse)
  gain   = F_strategy minus F_stale (positive means the strategy is better)

Hypotheses, in the order protocol_round2.md fixes them:
  H1 no harm   hybrid minus stale pooled over D = 1 and 3 h,
               lower 95 percent bound above -0.002
  H2 primary   hybrid minus stale pooled over D = 6, 12, 24 and 48 h,
               lower 95 percent bound above 0, and 6 h and 24 h separately

Usage:
  python scripts/31_analyse_round2.py --rows outputs/round2_run/all_rows.csv
  python scripts/31_analyse_round2.py --dry-run-round1
"""
import argparse
import os
import sys
import types
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "engine"))

# DEVIATION, logged. Without these, real_data falls back to its Round 1
# default, data/clean, and the publishing gap scan reads the DEVELOPMENT store.
# The first run of this script therefore printed the September gaps and found
# zero fresh jobs straddling a gap, when the fresh window has one on
# ibm_marrakesh from 22 Oct 20:25 to 23 Oct 19:17. The engine was always
# reading the right store; only this script's gap scan was not.
os.environ.setdefault("STALENESS_CLEAN_DIR", str(ROOT / "data/clean_r2"))
os.environ.setdefault("STALENESS_CACHE_DIR", str(ROOT / "data/cache_r2"))

OUT = ROOT / "outputs" / "round2"
JOB = ["machine", "draw_order", "delay_h", "circuit"]
ARMS = ["stale", "window_mean", "shrinkage_r1", "hybrid", "hybrid_no_guard",
        "ceiling"]
INFORMED = ["stale", "window_mean", "shrinkage_r1", "hybrid",
            "hybrid_no_guard"]
H1_DELAYS = [1, 3]
H2_DELAYS = [6, 12, 24, 48]
H1_BOUND = -0.002
GAP_MIN_H = 18.0          # an interval longer than this is a publishing gap
FAMILY = {"ghz5": "GHZ", "ghz8": "GHZ", "ghz10": "GHZ",
          "bv8": "BV", "bv10": "BV",
          "qft5": "QFT", "qft8": "QFT", "qft10": "QFT"}

_lines = []


def say(*a):
    msg = " ".join(str(x) for x in a)
    print(msg, flush=True)
    _lines.append(msg)


def head(title):
    say("")
    say("=" * 72)
    say(title)
    say("=" * 72)


def load_script20():
    """Import Round 1's analysis module so the bootstrap is the same code."""
    path = ROOT / "scripts/20_analyse_results.py"
    src = path.read_text().rsplit("\nmain()", 1)[0]
    mod = types.ModuleType("analyse20")
    mod.__file__ = str(path)
    sys.modules["analyse20"] = mod
    exec(compile(src, str(path), "exec"), mod.__dict__)
    return mod


M20 = load_script20()


# ------------------------------------------------------------------ loading

def find_gaps(store_times, min_h=GAP_MIN_H):
    """Intervals between neighbouring distinct states longer than min_h."""
    out = []
    for a, b in zip(store_times[:-1], store_times[1:]):
        hours = (b - a).total_seconds() / 3600.0
        if hours > min_h:
            out.append((a, b, hours))
    return out


def gap_table():
    """Publishing gaps in the fresh window, found from the states themselves."""
    import real_data as rd
    rows = []
    for m in ["ibm_fez", "ibm_kingston", "ibm_marrakesh"]:
        try:
            store = rd.open_store(m)
        except Exception as err:
            say(f"  could not open the store for {m}: {type(err).__name__}")
            continue
        for a, b, h in find_gaps(store.times):
            rows.append({"machine": m, "gap_start_utc": a.isoformat(),
                         "gap_end_utc": b.isoformat(), "hours": round(h, 3)})
    return pd.DataFrame(rows)


def load_rows(path, dry_round1=False):
    df = pd.read_csv(path)
    df["t_s"] = pd.to_datetime(df.t_s, utc=True)
    df["t_r"] = pd.to_datetime(df.t_r, utc=True)
    df["day"] = df.t_s.dt.date
    if dry_round1:
        # MECHANICAL DRY RUN ONLY. Round 1 rows do not contain the Round 2
        # arms, so three Round 1 arms are renamed to make the code path run.
        # Every number this produces is meaningless and is labelled as such.
        df = df[df.arm != "random"].copy()
        df["arm"] = df.arm.replace({"shrinkage": "hybrid",
                                    "std_adjusted": "hybrid_no_guard"})
        df["arm"] = df.arm.where(df.arm != "hybrid", "hybrid")
        extra = df[df.arm == "hybrid"].copy()
        extra["arm"] = "shrinkage_r1"
        df = pd.concat([df, extra], ignore_index=True)
    return df


def widen(df, gaps):
    """One row per job, one column per arm, plus regret and gain columns."""
    idx = ["machine", "draw_order", "delay_h", "circuit", "day", "new_states"]
    w = df.pivot_table(index=idx, columns="arm", values="fidelity",
                       aggfunc="first").reset_index()
    w.columns.name = None
    missing = [a for a in ARMS if a not in w.columns]
    if missing:
        raise SystemExit(f"these arms are absent from the rows: {missing}")
    for a in ARMS:
        w[f"regret_{a}"] = w["ceiling"] - w[a]
    for a in INFORMED + ["ceiling"]:
        w[f"gain_{a}"] = w[a] - w["stale"]

    # dead qubit bookkeeping, per arm, from the engine's own column
    used = (df.assign(d=lambda d: d.dead_qubits_used.fillna("")
                      .astype(str).str.strip().str.len() > 0)
            .pivot_table(index=idx, columns="arm", values="d",
                         aggfunc="first").reset_index())
    used.columns.name = None
    for a in ARMS:
        w[f"dead_{a}"] = used[a].to_numpy() if a in used.columns else False
    w["any_informed_dead"] = w[[f"dead_{a}" for a in INFORMED]].any(axis=1)

    # jobs that straddle a publishing gap stay IN and are flagged
    flag = np.zeros(len(w), dtype=bool)
    if len(gaps):
        ts = df.groupby(idx)[["t_s", "t_r"]].first().reset_index()
        key = w[idx].astype(str).agg("|".join, axis=1)
        tkey = ts[idx].astype(str).agg("|".join, axis=1)
        tmap = dict(zip(tkey, zip(ts.t_s, ts.t_r)))
        for i, k in enumerate(key):
            t_s, t_r = tmap.get(k, (None, None))
            if t_s is None:
                continue
            for _, g in gaps.iterrows():
                if g.machine != w.machine.iloc[i]:
                    continue
                a = pd.Timestamp(g.gap_start_utc)
                b = pd.Timestamp(g.gap_end_utc)
                if t_s < b and t_r > a:
                    flag[i] = True
                    break
    w["touches_gap"] = flag
    return w


# ----------------------------------------------------------------- testing

def boot(frame, col, rng):
    """Round 1's block bootstrap, unchanged: whole calendar days."""
    if len(frame) == 0:
        return np.nan, np.nan, np.nan, 0
    return M20.block_boot(frame, col, rng)


def one_test(name, frame, col, rng, bound=None):
    obs, lo, hi, nd = boot(frame, col, rng)
    row = {"test": name, "n_jobs": len(frame), "n_days": nd, "mean": obs,
           "lo95": lo, "hi95": hi}
    if bound is not None:
        row["bound"] = bound
        row["passes"] = bool(lo > bound) if np.isfinite(lo) else False
    return row


def show(rows, title, with_verdict=False):
    say(f"\n  {title}")
    wv = f"{'verdict':>10}" if with_verdict else ""
    say(f"    {'what':<42}{'n jobs':>8}{'days':>6}{'mean':>11}"
        f"{'95% low':>11}{'95% high':>11}{wv}")
    for r in rows:
        v = ""
        if with_verdict and "passes" in r:
            v = f"{('PASS' if r['passes'] else 'FAIL'):>10}"
        say(f"    {r['test']:<42}{r['n_jobs']:>8}{r['n_days']:>6}"
            f"{r['mean']:>11.6f}{r['lo95']:>11.6f}{r['hi95']:>11.6f}{v}")


# -------------------------------------------------------------- the views

def build_views(df, w, gaps):
    """The three dead qubit views of protocol_round2.md.

    Round 1 had four views because the random arm could carry a dead row on
    its own. Round 2 drops the random arm, so "any arm" and "any informed arm"
    are the same set and the two middle views coincide. Three remain.
    """
    views = {}
    views["1 all rows as they are"] = w
    views["2 drop jobs with a dead row in any arm"] = w[~w.any_informed_dead
                                                        & ~w.dead_ceiling]
    d3 = df.copy()
    hit = d3.dead_qubits_used.fillna("").astype(str).str.strip().str.len() > 0
    d3.loc[hit, "fidelity"] = 0.0
    views["3 dead rows forced to fidelity 0"] = widen(d3, gaps)
    return views


# ----------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", default=str(ROOT / "outputs/round2_run/all_rows.csv"))
    ap.add_argument("--dry-run-round1", action="store_true")
    ap.add_argument("--out", default=str(OUT))
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    rows_path = (ROOT / "outputs/test_full/all_rows.csv" if a.dry_run_round1
                 else Path(a.rows))
    head("ROUND 2 ANALYSIS")
    if a.dry_run_round1:
        say("  *** MECHANICAL DRY RUN ON ROUND 1 ROWS ***")
        say("  This only proves the code runs end to end. Round 1 rows do not")
        say("  contain the Round 2 arms, so three Round 1 arms are renamed to")
        say("  stand in for them. EVERY NUMBER BELOW IS MEANINGLESS.")
    say(f"  rows file: {rows_path}")
    if not rows_path.exists():
        raise SystemExit(f"rows file not found: {rows_path}")

    df = load_rows(rows_path, a.dry_run_round1)
    say(f"  {len(df)} arm rows, arms present: {sorted(df.arm.unique())}")
    gaps = gap_table()
    if len(gaps):
        say(f"\n  publishing gaps found in the state store "
            f"(any interval longer than {GAP_MIN_H} h):")
        for _, g in gaps.iterrows():
            say(f"    {g.machine:<16}{g.gap_start_utc} to {g.gap_end_utc}"
                f"   {g.hours:.2f} h")
    else:
        say(f"\n  no interval longer than {GAP_MIN_H} h between neighbouring "
            f"states: no publishing gap in this window")
    gaps.to_csv(out / "r2_publishing_gaps.csv", index=False)

    w = widen(df, gaps)
    say(f"\n  {len(w)} jobs, {w.day.nunique()} calendar days, "
        f"{w.machine.nunique()} machines, {w.circuit.nunique()} circuits")
    say(f"  delays present: {[int(x) for x in sorted(w.delay_h.unique())]}")
    say(f"  jobs that straddle a publishing gap: {int(w.touches_gap.sum())} "
        f"(kept in, reported separately below)")
    w.to_csv(out / "r2_jobs_wide.csv", index=False)

    rng = np.random.default_rng(M20.SEED_BOOT)
    say(f"\n  bootstrap: Round 1's block_boot, seed {M20.SEED_BOOT}, "
        f"{M20.N_BOOT} resamples of whole calendar days")

    # ------------------------------------------------------- sanity checks
    head("SANITY CHECKS")
    fails = []
    nc = w[w.new_states == 0]
    if len(nc) == 0:
        say("  1. no-change jobs: none present, the check cannot run")
        fails.append("check 1 could not run")
    else:
        worst = float(np.abs(nc.regret_stale).max())
        ok = worst == 0.0
        say(f"  1. stale regret EXACTLY 0 when no new state appeared: "
            f"{'PASS' if ok else 'FAIL'} ({len(nc)} jobs, "
            f"largest absolute regret {worst!r})")
        if not ok:
            fails.append("check 1")
    worst_c = float(np.abs(w.regret_ceiling).max())
    say(f"  2. ceiling regret is exactly 0 by construction: "
        f"{'PASS' if worst_c == 0.0 else 'FAIL'} (largest {worst_c!r})")
    if worst_c != 0.0:
        fails.append("check 2")
    nbad = int((w[[f"dead_{x}" for x in ARMS]].sum().sum()))
    say(f"  3. rows whose chosen qubits were dead on the run-time card: {nbad}")
    say(f"     (these are real outcomes, not errors: a stale pick can land on "
        f"a qubit that has since failed)")
    say(f"  4. every job has all {len(ARMS)} arms: "
        f"{'PASS' if not w[ARMS].isna().any().any() else 'FAIL'}")
    if w[ARMS].isna().any().any():
        fails.append("check 4")

    # --------------------------------------------------------------- H1, H2
    head("H1 (NO HARM) AND H2 (PRIMARY)")
    h1 = w[w.delay_h.isin(H1_DELAYS)]
    h2 = w[w.delay_h.isin(H2_DELAYS)]
    primary = [
        one_test(f"H1 hybrid minus stale, D = 1 and 3 h", h1, "gain_hybrid",
                 rng, bound=H1_BOUND),
        one_test(f"H2 hybrid minus stale, D = 6 to 48 h", h2, "gain_hybrid",
                 rng, bound=0.0),
    ]
    show(primary, "primary tests, in the order the protocol fixes them",
         with_verdict=True)
    say(f"    H1 passes when the lower bound is above {H1_BOUND}")
    say(f"    H2 passes when the lower bound is above 0")

    per_delay = [one_test(f"hybrid minus stale, D = {d} h",
                          w[w.delay_h == d], "gain_hybrid", rng)
                 for d in sorted(w.delay_h.unique())]
    show(per_delay, "hybrid minus stale at every delay (6 h and 24 h are "
                    "named in the protocol)")

    # ----------------------------------------------------------- secondary
    head("SECONDARY RESULTS")
    sec = []
    for other in ["window_mean", "shrinkage_r1", "hybrid_no_guard"]:
        sub = h2.copy()
        sub["d"] = sub["hybrid"] - sub[other]
        sec.append(one_test(f"hybrid minus {other}, D = 6 to 48 h", sub, "d",
                            rng))
    show(sec, "hybrid against the other strategies, pooled over D = 6 to 48 h")

    fam = []
    h2f = h2.assign(family=h2.circuit.map(FAMILY))
    for f in ["GHZ", "BV", "QFT"]:
        fam.append(one_test(f"hybrid minus stale, {f}", h2f[h2f.family == f],
                            "gain_hybrid", rng))
    for c in sorted(h2.circuit.unique()):
        fam.append(one_test(f"hybrid minus stale, {c}", h2[h2.circuit == c],
                            "gain_hybrid", rng))
    show(fam, "by circuit family and by circuit, pooled over D = 6 to 48 h")

    mac = [one_test(f"hybrid minus stale, {m}", h2[h2.machine == m],
                    "gain_hybrid", rng) for m in sorted(h2.machine.unique())]
    show(mac, "by machine, pooled over D = 6 to 48 h")

    gp = [one_test("hybrid minus stale, jobs across a gap",
                   h2[h2.touches_gap], "gain_hybrid", rng),
          one_test("hybrid minus stale, jobs not across a gap",
                   h2[~h2.touches_gap], "gain_hybrid", rng)]
    show(gp, "the publishing gap, kept in and reported separately")

    abl = []
    for arm in INFORMED:
        abl.append(one_test(f"{arm} minus stale, D = 6 to 48 h", h2,
                            f"gain_{arm}", rng))
    show(abl, "every arm against stale, pooled over D = 6 to 48 h")

    reg = []
    for arm in ARMS:
        reg.append(one_test(f"regret of {arm}, D = 6 to 48 h", h2,
                            f"regret_{arm}", rng))
    show(reg, "mean regret against the ceiling, pooled over D = 6 to 48 h "
              "(lower is better)")

    # -------------------------------------------------------- the three views
    head("THE THREE DEAD QUBIT VIEWS")
    views = build_views(df, w, gaps)
    vrows = []
    for vname, vw in views.items():
        sub = vw[vw.delay_h.isin(H2_DELAYS)]
        r = one_test(f"H2 under view {vname}", sub, "gain_hybrid", rng,
                     bound=0.0)
        vrows.append(r)
        tot = sub.regret_stale.sum()
        dead_share = (sub[sub.dead_stale].regret_stale.sum() / tot
                      if tot else np.nan)
        r["dead_row_share_of_stale_regret"] = dead_share
    show(vrows, "H2 recomputed under each view", with_verdict=True)
    say(f"\n    {'view':<44}{'dead-row share of stale regret':>32}")
    for r in vrows:
        s = r["dead_row_share_of_stale_regret"]
        say(f"    {r['test']:<44}{(f'{s:.4f}' if np.isfinite(s) else 'n/a'):>32}")

    # --------------------------------------------------------- design effects
    head("DESIGN EFFECTS ON THE FRESH JOBS")
    sd = h2.gain_hybrid.std(ddof=1)
    n = len(h2)
    naive = sd / np.sqrt(n) if n else np.nan
    obs, lo, hi, nd = boot(h2, "gain_hybrid", rng)
    clustered = (hi - lo) / (2 * 1.959963985)
    de = (clustered / naive) ** 2 if naive and np.isfinite(naive) else np.nan
    say(f"  pooled over D = 6 to 48 h, n = {n} jobs on {nd} calendar days")
    say(f"    paired SD of hybrid minus stale   {sd:.6f}")
    say(f"    naive standard error              {naive:.6f}")
    say(f"    clustered standard error (days)   {clustered:.6f}")
    say(f"    design effect                     {de:.3f}")
    say(f"  the design effect is how many times wider the honest interval is "
        f"than the naive one, squared. A value above 1 means jobs on the same "
        f"day move together.")
    pd.DataFrame([{"n_jobs": n, "n_days": nd, "paired_sd": sd,
                   "naive_se": naive, "clustered_se": clustered,
                   "design_effect": de}]).to_csv(
        out / "r2_design_effects.csv", index=False)

    # ------------------------------------------------------------- write out
    allrows = (primary + per_delay + sec + fam + mac + gp + abl + reg + vrows)
    pd.DataFrame(allrows).to_csv(out / "r2_results.csv", index=False)

    head("SANITY VERDICT")
    if fails:
        say(f"  FAILED CHECKS: {fails}")
    else:
        say("  every sanity check that could run passed")

    (out / "r2_analysis_console.txt").write_text("\n".join(_lines) + "\n")
    say(f"\n  tables written to {out}")
    return 1 if fails else 0


sys.exit(main())
