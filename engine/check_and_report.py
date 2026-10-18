"""Sanity checks from PROTOCOL.md section 12, then the pilot report.

OURS. Nothing is reported unless all checks pass. If one fails the script
stops with a non-zero exit and says which.

Checks implemented here (check 4, the teammates' fixture checksum, is run
separately because it needs their pipeline, not this one):
  1. stale regret is EXACTLY 0 whenever no new state appeared between t_s
     and t_r. Not approximately zero.
  2. the ceiling is never below stale on average, at every delay.
  3. the random layout arm is the lowest on average.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
CSV = ROOT / "outputs" / "pilot_kingston_PILOT_exploratory.csv"
ARMS = ["random", "stale", "window_mean", "std_adjusted", "shrinkage", "ceiling"]
SEED_BOOT = 20261013
N_BOOT = 2000


def main():
    df = pd.read_csv(CSV)
    df["t_s"] = pd.to_datetime(df.t_s, utc=True)
    df["day"] = df.t_s.dt.date
    wide = df.pivot_table(index=["draw_order", "delay_h", "circuit", "day",
                                "new_states"],
                          columns="arm", values="fidelity").reset_index()
    for arm in ARMS:
        wide[f"regret_{arm}"] = wide["ceiling"] - wide[arm]

    print("=== PROTOCOL.md section 12 sanity checks ===\n")
    failures = []

    # --- check 1 ---
    nochange = wide[wide.new_states == 0]
    if len(nochange) == 0:
        print("1. no-change jobs: NONE in this slice, check cannot run")
        failures.append("check 1 could not run: no jobs with new_states == 0")
    else:
        worst = float(np.abs(nochange["regret_stale"]).max())
        exact = int((nochange["regret_stale"] == 0.0).sum())
        ok = worst == 0.0
        print(f"1. stale regret exactly 0 when no new state appeared: "
              f"{'PASS' if ok else 'FAIL'}")
        print(f"   {len(nochange)} such jobs, {exact} exactly zero, "
              f"largest absolute regret {worst!r}")
        if not ok:
            failures.append("check 1: stale regret was not exactly zero")

    # --- check 2 ---
    print("\n2. ceiling at least stale on average, per delay:")
    ok2 = True
    for D, g in wide.groupby("delay_h"):
        c, s = g["ceiling"].mean(), g["stale"].mean()
        good = c >= s
        ok2 &= good
        print(f"   D={D:>3}h  ceiling {c:.4f}  stale {s:.4f}  "
              f"diff {c - s:+.4f}  {'ok' if good else 'FAIL'}")
    print(f"   {'PASS' if ok2 else 'FAIL'}")
    if not ok2:
        failures.append("check 2: ceiling fell below stale on average")

    # --- check 3 ---
    means = {a: wide[a].mean() for a in ARMS}
    lowest = min(means, key=means.get)
    ok3 = lowest == "random"
    print(f"\n3. random layout is the lowest arm: {'PASS' if ok3 else 'FAIL'}")
    for a in sorted(means, key=means.get):
        print(f"   {a:<14} {means[a]:.4f}")
    if not ok3:
        failures.append(f"check 3: lowest arm was {lowest}, not random")

    if failures:
        print("\n=== SANITY CHECKS FAILED, NOTHING IS REPORTED ===")
        for f in failures:
            print("  ", f)
        sys.exit(1)
    print("\n=== all checks that could run PASSED ===\n")

    # ------------------------------------------------ the report
    print("=" * 66)
    print("PILOT, exploratory. ibm_kingston, TRAINING DAYS ONLY.")
    print("Shrinkage arm is NOT TUNED (placeholder N=5, w=0.5).")
    print("=" * 66)
    n_jobs = len(wide)
    print(f"\njobs run: {n_jobs} (each = one submission, delay and circuit, "
          f"with all {len(ARMS)} arms)")
    print(f"simulations: {len(df)} rows plus 4 extra draws per random arm")
    print(f"days covered: {wide.day.nunique()}, "
          f"{wide.day.min()} to {wide.day.max()}")

    print("\n--- share of jobs where NO new state appeared ---")
    for D, g in wide.groupby("delay_h"):
        share = (g.new_states == 0).mean()
        print(f"  D={D:>3}h  {int((g.new_states==0).sum())}/{len(g)} "
              f"= {share*100:.1f}%   (median new states {g.new_states.median():.0f})")

    print("\n--- mean Hellinger fidelity per arm, per delay ---")
    tbl = wide.groupby("delay_h")[ARMS].mean()
    print(tbl.to_string(float_format=lambda x: f"{x:.4f}"))

    print("\n--- mean fidelity per arm, per delay and circuit ---")
    tbl2 = wide.groupby(["delay_h", "circuit"])[ARMS].mean()
    print(tbl2.to_string(float_format=lambda x: f"{x:.4f}"))

    print("\n--- mean REGRET of stale against the ceiling ---")
    print("    (ceiling fidelity minus stale fidelity; lower is better)")
    print("    interval: block bootstrap resampling whole DAYS, "
          f"{N_BOOT} resamples, 95 percent")
    rng = np.random.default_rng(SEED_BOOT)
    for D, g in wide.groupby("delay_h"):
        days = g.day.unique()
        obs = g["regret_stale"].mean()
        boots = []
        for _ in range(N_BOOT):
            pick = rng.choice(days, size=len(days), replace=True)
            vals = np.concatenate([g[g.day == d]["regret_stale"].to_numpy()
                                   for d in pick])
            boots.append(vals.mean())
        lo, hi = np.percentile(boots, [2.5, 97.5])
        print(f"  D={D:>3}h  mean regret {obs:+.4f}  "
              f"95% interval [{lo:+.4f}, {hi:+.4f}]  "
              f"({len(days)} day blocks, n={len(g)})")

    print("\n--- mean regret of every arm against the ceiling, per delay ---")
    rcols = [f"regret_{a}" for a in ARMS if a != "ceiling"]
    print(wide.groupby("delay_h")[rcols].mean()
          .to_string(float_format=lambda x: f"{x:+.4f}"))

    print("\n--- jobs where a chosen qubit was DEAD under the truth state ---")
    d = df[df.dead_qubits_used.notna() & (df.dead_qubits_used != "")]
    if len(d) == 0:
        print("  none")
    else:
        print(d.groupby("arm").size().to_string())

    print("\n--- age at run time of the numbers each arm used (hours) ---")
    for col in ["cz_age_at_run_h", "readout_age_at_run_h"]:
        sub = df[df.arm.isin(["stale", "ceiling"])]
        print(f"  {col}:")
        print(sub.groupby(["arm", "delay_h"])[col].mean()
              .to_string(float_format=lambda x: f"{x:.2f}"))

    print("\nPILOT, exploratory. No test day was used. "
          "No claim follows from this.")


main()
