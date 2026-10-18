"""Analysis for PROTOCOL.md sections 11, 12 and 13.

OURS. Deliberately NOT inside engine/, because the engine was frozen in L-033
and must not change while the test run is in flight.

Runs the four sanity checks first and reports NOTHING if any fails.

Then the two confirmatory comparisons, fixed in advance by PROTOCOL.md 11:
  (A) stale regret against the ceiling, at each delay D
  (B) per-field shrinkage against stale at D = 6 h and D = 24 h, pooled over
      machines and circuits, paired, on test days

Everything else printed here is EXPLORATORY and says so.

Wording rule from L-032: where a number touches the question of measurement
noise versus real drift, say "consistent with", never "proved". Our cards are
IBM's reported numbers, so we cannot separate a remeasurement that moved from a
qubit that moved.

Usage:  20_analyse_results.py <results.csv> [--label TEST]
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
ARMS = ["random", "stale", "window_mean", "std_adjusted", "shrinkage", "ceiling"]
SEED_BOOT = 20261014
N_BOOT = 4000
PRIMARY_B_DELAYS = [6, 24]
FIXTURE_SHA = "afd161059ecad53ec35c87450832d920880ecd04504a7d17a830ebc611716f69"

# The 22 to 23 September platform wide publishing gaps, measured in L-033.
# A job is flagged when its submission-to-run interval overlaps one of these.
GAPS = {
    "ibm_fez":      ("2026-09-22T14:00:30Z", "2026-09-23T16:44:52Z"),
    "ibm_kingston": ("2026-09-22T14:13:16Z", "2026-09-23T17:27:02Z"),
    "ibm_marrakesh": ("2026-09-20T22:53:12Z", "2026-09-22T05:14:59Z"),
}


def load(path):
    df = pd.read_csv(path)
    df["t_s"] = pd.to_datetime(df.t_s, utc=True)
    df["t_r"] = pd.to_datetime(df.t_r, utc=True)
    df["day"] = df.t_s.dt.date
    gs = {m: (pd.Timestamp(a), pd.Timestamp(b)) for m, (a, b) in GAPS.items()}
    df["touches_gap"] = [
        (t_s < gs[m][1]) and (t_r > gs[m][0]) if m in gs else False
        for m, t_s, t_r in zip(df.machine, df.t_s, df.t_r)]
    return df


def widen(df):
    idx = ["machine", "draw_order", "delay_h", "circuit", "day", "new_states",
           "touches_gap"]
    w = df.pivot_table(index=idx, columns="arm", values="fidelity").reset_index()
    for arm in ARMS:
        if arm in w:
            w[f"regret_{arm}"] = w["ceiling"] - w[arm]
    return w


def block_boot(frame, value_col, rng, n_boot=N_BOOT):
    """Resample WHOLE DAYS, as PROTOCOL.md section 11 requires."""
    days = frame.day.unique()
    by_day = {d: frame[frame.day == d][value_col].to_numpy() for d in days}
    obs = frame[value_col].mean()
    out = np.empty(n_boot)
    for i in range(n_boot):
        pick = rng.choice(days, size=len(days), replace=True)
        out[i] = np.concatenate([by_day[d] for d in pick]).mean()
    lo, hi = np.percentile(out, [2.5, 97.5])
    return obs, lo, hi, len(days)


def sanity(df, w, fixture_path):
    print("=== PROTOCOL.md section 12 sanity checks ===\n")
    fails = []

    nc = w[w.new_states == 0]
    if len(nc) == 0:
        print("1. no-change jobs: none present, check cannot run")
        fails.append("check 1 could not run")
    else:
        worst = float(np.abs(nc["regret_stale"]).max())
        ok = worst == 0.0
        print(f"1. stale regret EXACTLY 0 when no new state appeared: "
              f"{'PASS' if ok else 'FAIL'}  "
              f"({len(nc)} jobs, largest |regret| {worst!r})")
        if not ok:
            fails.append("check 1")

    ok2 = True
    print("2. ceiling at least stale on average, per delay:")
    for D, g in w.groupby("delay_h"):
        c, s = g["ceiling"].mean(), g["stale"].mean()
        good = c >= s
        ok2 &= good
        print(f"     D={D:>3}h  ceiling {c:.4f}  stale {s:.4f}  "
              f"{c-s:+.4f}  {'ok' if good else 'FAIL'}")
    print(f"   {'PASS' if ok2 else 'FAIL'}")
    if not ok2:
        fails.append("check 2")

    means = {a: w[a].mean() for a in ARMS if a in w}
    lowest = min(means, key=means.get)
    ok3 = lowest == "random"
    print(f"3. random layout is the lowest arm: {'PASS' if ok3 else 'FAIL'} "
          f"(lowest is {lowest})")
    for a in sorted(means, key=means.get):
        print(f"     {a:<14} {means[a]:.4f}")
    if not ok3:
        fails.append("check 3")

    import hashlib
    p = Path(fixture_path)
    if p.exists():
        h = hashlib.sha256(p.read_bytes()).hexdigest()
        ok4 = h == FIXTURE_SHA
        print(f"4. teammates' fixture checksum: {'PASS' if ok4 else 'FAIL'}")
        print(f"     {h}")
        if not ok4:
            fails.append("check 4")
    else:
        print(f"4. fixture not found at {p}, check skipped")
        fails.append("check 4 could not run")
    return fails


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("results")
    ap.add_argument("--label", default="TEST")
    ap.add_argument("--fixture",
                    default=str(ROOT / "team_code/zip_originals/results/results_synthetic.csv"))
    ap.add_argument("--allow-failed-checks", action="store_true",
                    help="plumbing only; never use on a real result")
    a = ap.parse_args()

    df = load(a.results)
    w = widen(df)
    print(f"file: {a.results}")
    print(f"label: {a.label}   rows: {len(df)}   jobs: {len(w)}   "
          f"days: {w.day.nunique()}   machines: {sorted(w.machine.unique())}")
    print(f"delays present: {sorted(w.delay_h.unique())}   "
          f"circuits: {sorted(w.circuit.unique())}\n")

    fails = sanity(df, w, a.fixture)
    if fails and not a.allow_failed_checks:
        print(f"\n=== SANITY CHECKS FAILED: {fails}. NOTHING REPORTED. ===")
        sys.exit(1)
    if fails:
        print(f"\n!!! checks not passed ({fails}) but --allow-failed-checks "
              f"was given. PLUMBING ONLY, these numbers are not results. !!!")

    rng = np.random.default_rng(SEED_BOOT)
    main_set = w[~w.touches_gap]
    gap_set = w[w.touches_gap]

    print("\n" + "=" * 70)
    print("PRIMARY COMPARISON A (confirmatory): stale regret vs the ceiling")
    print("=" * 70)
    print("jobs touching the 22 to 23 Sep publishing gap are EXCLUDED here and")
    print("reported separately below, as PROTOCOL.md section 10 requires.")
    print(f"\n{'D (h)':>6} {'n':>6} {'no-change':>10} {'mean regret':>13} "
          f"{'95% interval':>26} {'days':>5}")
    for D, g in main_set.groupby("delay_h"):
        obs, lo, hi, nd = block_boot(g, "regret_stale", rng)
        print(f"{D:>6} {len(g):>6} {(g.new_states==0).mean()*100:>9.1f}% "
              f"{obs:>+13.4f}   [{lo:>+8.4f}, {hi:>+8.4f}] {nd:>5}")

    print("\n" + "=" * 70)
    print("PRIMARY COMPARISON B (confirmatory): shrinkage vs stale,")
    print(f"D = {PRIMARY_B_DELAYS} h, pooled over machines and circuits, paired")
    print("=" * 70)
    sub = main_set[main_set.delay_h.isin(PRIMARY_B_DELAYS)].copy()
    if len(sub) == 0 or "shrinkage" not in sub:
        print("  not available in this file")
    else:
        # CORRECTED 19 October 2026, PROGRESS_LOG.md L-049. Higher fidelity
        # is better, so the gain of shrinkage over stale is shrinkage MINUS
        # stale. This line used to read stale - shrinkage while the comment
        # claimed ">0 = shrinkage better", so the sign of the reported gain
        # was the wrong way round. Only the direction was wrong. The size of
        # the effect and the verdict (the interval includes zero) do not
        # change. The bootstrap seed is untouched.
        sub["paired_gain"] = sub["shrinkage"] - sub["stale"]   # >0 = shrinkage better
        obs, lo, hi, nd = block_boot(sub, "paired_gain", rng)
        print(f"  n = {len(sub)} jobs over {nd} days")
        print(f"  mean paired gain of shrinkage over stale (fidelity, "
              f"positive means shrinkage is better): {obs:+.5f}")
        print(f"  95 percent interval: [{lo:+.5f}, {hi:+.5f}]")
        verdict = ("shrinkage is better" if lo > 0 else
                   "stale is better" if hi < 0 else
                   "no significant difference")
        print(f"  the interval {'excludes' if (lo>0 or hi<0) else 'includes'} "
              f"zero, so: {verdict}")
        for D, g in sub.groupby("delay_h"):
            o2, l2, h2, _ = block_boot(g, "paired_gain", rng)
            print(f"    D={D:>3}h  n={len(g):>5}  {o2:+.5f}  [{l2:+.5f}, {h2:+.5f}]")

    print("\n" + "=" * 70)
    print("THE 22 TO 23 SEPTEMBER GAP, reported separately (EXPLORATORY)")
    print("=" * 70)
    print(f"  jobs whose submission-to-run interval overlaps a gap: "
          f"{len(gap_set)} of {len(w)}")
    if len(gap_set):
        for D, g in gap_set.groupby("delay_h"):
            print(f"    D={D:>3}h  n={len(g):>4}  mean stale regret "
                  f"{g['regret_stale'].mean():+.4f}  "
                  f"no-change {(g.new_states==0).mean()*100:.0f}%")

    print("\n" + "=" * 70)
    print("EXPLORATORY from here down. Not confirmatory. Do not headline.")
    print("=" * 70)
    print("\nmean fidelity per arm per delay:")
    print(main_set.groupby("delay_h")[[a for a in ARMS if a in w]].mean()
          .to_string(float_format=lambda x: f"{x:.4f}"))
    print("\nmean regret per arm per delay:")
    rc = [f"regret_{a}" for a in ARMS if a != "ceiling" and a in w]
    print(main_set.groupby("delay_h")[rc].mean()
          .to_string(float_format=lambda x: f"{x:+.4f}"))
    print("\nmean stale regret by number of new states crossed:")
    bucket = main_set.new_states.clip(upper=2).map({0: "0", 1: "1", 2: "2 or more"})
    print(main_set.groupby(bucket)["regret_stale"].agg(["count", "mean"])
          .to_string(float_format=lambda x: f"{x:.4f}"))
    print("\nmean stale regret per machine per delay:")
    print(main_set.pivot_table(index="delay_h", columns="machine",
                               values="regret_stale")
          .to_string(float_format=lambda x: f"{x:+.4f}"))
    print("\njobs where a chosen qubit was dead under truth, by arm:")
    d = df[df.dead_qubits_used.notna() & (df.dead_qubits_used.astype(str) != "")]
    print("  none" if len(d) == 0 else d.groupby("arm").size().to_string())
    print(f"\n{a.label}. Confirmatory parts are A and B only. Where this "
          f"touches noise versus drift, the wording is 'consistent with'.")


main()
