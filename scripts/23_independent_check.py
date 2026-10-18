"""Independent recomputation of the headline test-period numbers.

OURS. Written from scratch on 14 October 2026 to check L-039 by a second
route. It deliberately shares NO code with scripts/20_analyse_results.py:
nothing is imported from it, no function is copied, the reshape is done by
hand instead of with pivot_table, and the bootstrap uses a different seed.

What it recomputes:
  1. Table A: mean stale regret against the ceiling at each delay, with a
     95 percent block bootstrap interval over whole days, gap jobs excluded.
  2. The states-crossed split of stale regret: 0, 1, 2 or more.
  3. Comparison B: shrinkage against stale, paired, D = 6 and 24 h pooled.

The only inputs taken from elsewhere are the merged results CSV and the
three publishing-gap windows measured in L-033, which are data, not code.

Usage:  23_independent_check.py <results.csv> [--seed 20261015] [--boot 4000]
"""
import argparse
import csv
import json
from collections import defaultdict
from datetime import datetime

import numpy as np

# Publishing gaps measured in L-033. Data, not borrowed code.
GAP_WINDOWS = {
    "ibm_fez":       ("2026-09-22T14:00:30Z", "2026-09-23T16:44:52Z"),
    "ibm_kingston":  ("2026-09-22T14:13:16Z", "2026-09-23T17:27:02Z"),
    "ibm_marrakesh": ("2026-09-20T22:53:12Z", "2026-09-22T05:14:59Z"),
}
TOL = 0.0005

# The L-039 numbers this script is checking, typed in from PROGRESS_LOG.md
# so the comparison is explicit and any gap is printed, not eyeballed.
L039_TABLE_A = {
    1:  dict(n=930, nochange=0.726, mean=0.0059, lo=0.0020, hi=0.0109),
    3:  dict(n=920, nochange=0.397, mean=0.0171, lo=0.0102, hi=0.0250),
    6:  dict(n=909, nochange=0.149, mean=0.0230, lo=0.0169, hi=0.0292),
    12: dict(n=880, nochange=0.034, mean=0.0259, lo=0.0199, hi=0.0330),
    24: dict(n=855, nochange=0.000, mean=0.0245, lo=0.0184, hi=0.0315),
    48: dict(n=794, nochange=0.000, mean=0.0367, lo=0.0250, hi=0.0510),
}
L039_STATES = {"0": dict(n=1205, mean=0.0000),
               "1": dict(n=935, mean=0.0289),
               "2 or more": dict(n=3148, mean=0.0280)}
# The Comparison B numbers to check against. CORRECTED 19 October 2026,
# PROGRESS_LOG.md L-049. L-039 printed these with the sign the wrong way
# round, because of the fault fixed in this file and in
# scripts/20_analyse_results.py. The values below are the same numbers in
# the corrected direction, where positive means shrinkage is better: the
# mean and the per-delay means are negated, and the interval bounds are
# negated and swapped. L-039 itself is left exactly as it was written.
L039_B = dict(n=1764, mean=0.00176, lo=-0.00147, hi=0.00482,
              at6=0.00345, at24=-0.00003)


def parse_iso(s):
    """ISO 8601 with offset or trailing Z, to an aware datetime."""
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def read_jobs(path):
    """Read the long file and fold it into one record per job, by hand.

    A job is identified by (machine, draw_order, delay_h, circuit). Each job
    must carry exactly one row per arm.
    """
    jobs = {}
    n_rows = 0
    gaps = {m: (parse_iso(a), parse_iso(b)) for m, (a, b) in GAP_WINDOWS.items()}
    with open(path, newline="") as fh:
        for row in csv.DictReader(fh):
            n_rows += 1
            key = (row["machine"], int(row["draw_order"]),
                   int(row["delay_h"]), row["circuit"])
            rec = jobs.get(key)
            if rec is None:
                t_s, t_r = parse_iso(row["t_s"]), parse_iso(row["t_r"])
                g = gaps.get(row["machine"])
                rec = jobs[key] = {
                    "machine": row["machine"],
                    "delay_h": int(row["delay_h"]),
                    "circuit": row["circuit"],
                    "day": t_s.date().isoformat(),
                    "new_states": int(row["new_states"]),
                    "truth_state": int(row["truth_state"]),
                    # overlap test: interval [t_s, t_r] meets (gap_start, gap_end)
                    "touches_gap": bool(g) and (t_s < g[1] and t_r > g[0]),
                    "fid": {},
                }
            assert row["arm"] not in rec["fid"], f"duplicate arm for {key}"
            rec["fid"][row["arm"]] = float(row["fidelity"])
    return list(jobs.values()), n_rows


def bootstrap_days(values_by_day, rng, n_boot):
    """95 percent interval from resampling WHOLE DAYS with replacement."""
    days = sorted(values_by_day)
    pools = [values_by_day[d] for d in days]
    allv = np.concatenate(pools)
    obs = float(allv.mean())
    draws = np.empty(n_boot)
    n = len(days)
    for i in range(n_boot):
        idx = rng.integers(0, n, size=n)
        draws[i] = np.concatenate([pools[j] for j in idx]).mean()
    lo, hi = (float(x) for x in np.percentile(draws, [2.5, 97.5]))
    return obs, lo, hi, n


def group_by_day(records, getter):
    out = defaultdict(list)
    for r in records:
        out[r["day"]].append(getter(r))
    return {d: np.asarray(v, dtype=float) for d, v in out.items()}


def flag(label, mine, theirs, tol=TOL):
    d = abs(mine - theirs)
    mark = "DIFFERS" if d > tol else "ok"
    return f"{label:<34} mine {mine:>+10.5f}   L-039 {theirs:>+10.5f}   " \
           f"diff {d:>8.5f}  {mark}", d > tol


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("results")
    ap.add_argument("--seed", type=int, default=20261015)
    ap.add_argument("--boot", type=int, default=4000)
    ap.add_argument("--json-out", default=None)
    args = ap.parse_args()

    jobs, n_rows = read_jobs(args.results)
    print("INDEPENDENT CHECK of the L-039 headline numbers")
    print("written from scratch, shares no code with 20_analyse_results.py")
    print(f"bootstrap seed {args.seed} (the analysis script used 20261014), "
          f"{args.boot} resamples\n")
    print(f"rows read: {n_rows}   jobs folded: {len(jobs)}")

    arms = sorted({a for j in jobs for a in j["fid"]})
    print(f"arms present: {arms}")
    bad = [j for j in jobs if len(j["fid"]) != len(arms)]
    print(f"jobs missing an arm: {len(bad)}")
    print(f"days: {len({j['day'] for j in jobs})}   "
          f"machines: {sorted({j['machine'] for j in jobs})}")

    for j in jobs:
        j["regret_stale"] = j["fid"]["ceiling"] - j["fid"]["stale"]
        # CORRECTED 19 October 2026, PROGRESS_LOG.md L-049. Higher fidelity
        # is better, so the gain of shrinkage over stale is shrinkage MINUS
        # stale. This line used to read stale - shrinkage while the print
        # below called it "the gain of shrinkage over stale", so the sign
        # was the wrong way round, the same fault as in
        # scripts/20_analyse_results.py. Only the direction was wrong.
        j["gain_shrink"] = j["fid"]["shrinkage"] - j["fid"]["stale"]

    main_set = [j for j in jobs if not j["touches_gap"]]
    gap_set = [j for j in jobs if j["touches_gap"]]
    print(f"gap jobs excluded: {len(gap_set)}   main set: {len(main_set)}\n")

    diffs = []
    rng = np.random.default_rng(args.seed)
    out = {"seed": args.seed, "boot": args.boot, "table_a": {},
           "states": {}, "comparison_b": {}}

    print("=" * 78)
    print("1. TABLE A, stale regret vs ceiling, gap jobs excluded")
    print("=" * 78)
    print(f"{'D (h)':>6} {'n':>6} {'no-change':>10} {'mean':>10} "
          f"{'95 pct interval':>24} {'days':>6}")
    for D in sorted({j["delay_h"] for j in main_set}):
        g = [j for j in main_set if j["delay_h"] == D]
        obs, lo, hi, nd = bootstrap_days(
            group_by_day(g, lambda r: r["regret_stale"]), rng, args.boot)
        nochange = sum(1 for j in g if j["new_states"] == 0) / len(g)
        print(f"{D:>6} {len(g):>6} {nochange*100:>9.1f}% {obs:>+10.4f}   "
              f"[{lo:>+8.4f}, {hi:>+8.4f}] {nd:>6}")
        out["table_a"][D] = dict(n=len(g), nochange=nochange, mean=obs,
                                 lo=lo, hi=hi, days=nd)
        ref = L039_TABLE_A[D]
        for name, mine, theirs in (("mean regret", obs, ref["mean"]),
                                   ("interval low", lo, ref["lo"]),
                                   ("interval high", hi, ref["hi"]),
                                   ("no-change share", nochange,
                                    ref["nochange"])):
            line, is_diff = flag(f"A D={D}h {name}", mine, theirs)
            diffs.append((line, is_diff))
        line, is_diff = flag(f"A D={D}h n", len(g), ref["n"], tol=0)
        diffs.append((line, is_diff))

    print("\n" + "=" * 78)
    print("2. STALE REGRET BY NUMBER OF NEW STATES CROSSED (gap jobs excluded)")
    print("=" * 78)
    for bucket in ("0", "1", "2 or more"):
        if bucket == "2 or more":
            g = [j for j in main_set if j["new_states"] >= 2]
        else:
            g = [j for j in main_set if j["new_states"] == int(bucket)]
        m = float(np.mean([j["regret_stale"] for j in g]))
        mx = float(np.max(np.abs([j["regret_stale"] for j in g])))
        print(f"  {bucket:>10}  n={len(g):>5}  mean {m:>+8.4f}  "
              f"largest |regret| {mx:.6f}")
        out["states"][bucket] = dict(n=len(g), mean=m, max_abs=mx)
        ref = L039_STATES[bucket]
        line, is_diff = flag(f"states {bucket} mean", m, ref["mean"])
        diffs.append((line, is_diff))
        line, is_diff = flag(f"states {bucket} n", len(g), ref["n"], tol=0)
        diffs.append((line, is_diff))

    print("\n" + "=" * 78)
    print("3. COMPARISON B, shrinkage vs stale, paired, D = 6 and 24 h pooled")
    print("=" * 78)
    sub = [j for j in main_set if j["delay_h"] in (6, 24)]
    obs, lo, hi, nd = bootstrap_days(
        group_by_day(sub, lambda r: r["gain_shrink"]), rng, args.boot)
    print(f"  n = {len(sub)} jobs over {nd} days")
    print(f"  mean paired gain of shrinkage over stale "
          f"(positive means shrinkage is better): {obs:+.5f}")
    print(f"  95 percent interval: [{lo:+.5f}, {hi:+.5f}]")
    print(f"  interval {'excludes' if (lo > 0 or hi < 0) else 'includes'} zero")
    out["comparison_b"]["pooled"] = dict(n=len(sub), mean=obs, lo=lo, hi=hi)
    for name, mine, theirs in (("B pooled mean", obs, L039_B["mean"]),
                               ("B pooled low", lo, L039_B["lo"]),
                               ("B pooled high", hi, L039_B["hi"])):
        line, is_diff = flag(name, mine, theirs)
        diffs.append((line, is_diff))
    line, is_diff = flag("B pooled n", len(sub), L039_B["n"], tol=0)
    diffs.append((line, is_diff))
    for D in (6, 24):
        g = [j for j in sub if j["delay_h"] == D]
        o2, l2, h2, _ = bootstrap_days(
            group_by_day(g, lambda r: r["gain_shrink"]), rng, args.boot)
        print(f"    D={D:>3}h  n={len(g):>5}  {o2:+.5f}  [{l2:+.5f}, {h2:+.5f}]")
        out["comparison_b"][f"D{D}"] = dict(n=len(g), mean=o2, lo=l2, hi=h2)
        line, is_diff = flag(f"B at {D}h mean", o2,
                             L039_B["at6"] if D == 6 else L039_B["at24"])
        diffs.append((line, is_diff))

    print("\n" + "=" * 78)
    print(f"4. EVERY NUMBER AGAINST L-039, tolerance {TOL}")
    print("=" * 78)
    print("  The Comparison B rows compare against L-039's numbers with the sign")
    print("  corrected per L-049. Table A and the states split are unaffected.")
    for line, _ in diffs:
        print("  " + line)
    over = [line for line, is_diff in diffs if is_diff]
    print(f"\n  numbers compared: {len(diffs)}   over tolerance: {len(over)}")
    if over:
        print("  OVER TOLERANCE:")
        for line in over:
            print("    " + line)
    else:
        print("  every number agrees with L-039 within tolerance.")

    if args.json_out:
        with open(args.json_out, "w") as fh:
            json.dump(out, fh, indent=2, default=str)
        print(f"\n  wrote {args.json_out}")


main()
