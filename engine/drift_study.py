"""Part B: how the numbers actually move. EXPLORATORY. No simulation.

OURS. Training days only (28 Aug to 20 Sep, Amendment A1.6). Nothing here
touches a test day and nothing here is a confirmatory result.

Per machine and per field (T1, T2, readout error, sx error, cz error):
  1. how often a new value arrives, and what time of day the sweeps land
  2. how big the changes are
  3. rank persistence, Spearman, at lags of 1, 3 and 10 distinct values
  4. prediction error of the NEXT distinct value, in log space
  5. the winner's curse: do the best ranked qubits fall back?

"A new value" means that field's numbers changed, by exact float inequality.
That is the per field clock of Amendment A1.2, not the per state clock.
"""
import sys
from collections import Counter

import numpy as np
from scipy.stats import spearmanr

import engine_config as cfg
import jobs as jobs_mod
import real_data as rd

MACHINES = ["ibm_fez", "ibm_kingston", "ibm_marrakesh"]
FIELDS = ["t1", "t2", "err_ro", "err_1q", "err_2q"]
NICE = {"t1": "T1", "t2": "T2", "err_ro": "readout", "err_1q": "sx error",
        "err_2q": "cz error"}
IST_OFFSET = 5.5


def series(store, field):
    """Distinct values of ONE field on training days, oldest first.
    Returns (times, array of shape (n_distinct, n_items))."""
    times, vals = [], []
    last = None
    for i, t in enumerate(store.times):
        if not jobs_mod.in_training(t):
            continue
        snap = store.snapshot(i)
        v = (np.array([snap["err_2q"][k] for k in sorted(snap["err_2q"])])
             if field == "err_2q" else np.asarray(snap[field], float))
        if v.size == 0:
            continue
        # equal_nan=True: NaN != NaN would make every state look like a new
        # distinct value for any field with a missing qubit.
        if last is None or v.shape != last.shape or not np.array_equal(
                v, last, equal_nan=True):
            times.append(t)
            vals.append(v)
            last = v
    return times, np.array(vals)


def live_mask(arr):
    """Items that are finite and positive in every distinct value."""
    return np.all(np.isfinite(arr) & (arr > 0), axis=0)


def main():
    print("PART B: DRIFT STUDY. EXPLORATORY. Training days only, "
          f"{cfg.WINDOW_START} to {cfg.TRAIN_END}. No simulation.\n")
    for machine in MACHINES:
        store = rd.open_store(machine)
        n_days = len({t.date() for t in store.times if jobs_mod.in_training(t)})
        print("=" * 72)
        print(f"{machine}   ({n_days} training days)")
        print("=" * 72)

        # ---------- 1. how often, and when ----------
        print("\n1. HOW OFTEN A NEW VALUE ARRIVES, AND WHEN")
        print(f"   {'field':<10} {'new values':>11} {'per day':>8} "
              f"{'median gap h':>13} {'busiest UTC hour':>17} {'IST':>7}")
        hours = {}
        for f in FIELDS:
            times, arr = series(store, f)
            gaps = [(b - a).total_seconds() / 3600 for a, b in zip(times, times[1:])]
            hr = Counter(t.hour for t in times)
            hours[f] = hr
            top_utc = max(hr, key=hr.get) if hr else -1
            top_ist = (top_utc + IST_OFFSET) % 24
            print(f"   {NICE[f]:<10} {len(times):>11} {len(times)/n_days:>8.2f} "
                  f"{np.median(gaps):>13.2f} {top_utc:>14}:00 "
                  f"{int(top_ist):>5}:{int((top_ist%1)*60):02d}")
        print("   arrivals by UTC hour (cz error), 0 to 23:")
        print("     " + " ".join(f"{hours['err_2q'].get(h,0):>3}" for h in range(24)))
        print("   same hours in IST (add 5:30):  "
              f"peak {max(hours['err_2q'], key=hours['err_2q'].get)}:00 UTC "
              f"= {(max(hours['err_2q'], key=hours['err_2q'].get)+5)%24}:30 IST")

        # ---------- 2. size of changes ----------
        print("\n2. SIZE OF A CHANGE, as a ratio new/old on items that moved")
        print(f"   {'field':<10} {'moves':>9} {'median x':>10} {'p90 x':>9} "
              f"{'share > 2x':>11}")
        for f in FIELDS:
            _, arr = series(store, f)
            m = live_mask(arr)
            a = arr[:, m]
            ratio = a[1:] / a[:-1]
            moved = ratio[a[1:] != a[:-1]]
            if moved.size == 0:
                print(f"   {NICE[f]:<10} {'0':>9}")
                continue
            fold = np.maximum(moved, 1.0 / moved)
            print(f"   {NICE[f]:<10} {moved.size:>9} {np.median(fold):>10.3f} "
                  f"{np.percentile(fold, 90):>9.3f} "
                  f"{(fold > 2).mean()*100:>10.2f}%")

        # ---------- 3. rank persistence ----------
        print("\n3. RANK PERSISTENCE, Spearman between distinct values")
        print(f"   {'field':<10} {'lag 1':>9} {'lag 3':>9} {'lag 10':>9}")
        for f in FIELDS:
            _, arr = series(store, f)
            m = live_mask(arr)
            a = arr[:, m]
            row = []
            for lag in (1, 3, 10):
                if a.shape[0] <= lag:
                    row.append(float("nan"))
                    continue
                rs = [spearmanr(a[i], a[i + lag]).statistic
                      for i in range(a.shape[0] - lag)]
                row.append(float(np.mean(rs)))
            print(f"   {NICE[f]:<10} " + " ".join(f"{x:>9.3f}" for x in row))

        # ---------- 4. prediction error ----------
        print("\n4. PREDICTION ERROR for the NEXT distinct value")
        print("   mean absolute error in log space (natural log), lower is better")
        print(f"   {'field':<10} {'N':>3} {'latest':>9} {'mean':>9} "
              f"{'median':>9} {'shrink.5':>9}")
        for f in FIELDS:
            _, arr = series(store, f)
            m = live_mask(arr)
            a = np.log(arr[:, m])
            for N in (3, 5, 10):
                if a.shape[0] <= N:
                    continue
                errs = {k: [] for k in ("latest", "mean", "median", "shrink")}
                for i in range(N, a.shape[0]):
                    hist = a[i - N:i]            # oldest..newest
                    truth = a[i]
                    latest = hist[-1]
                    mean = hist.mean(0)
                    med = np.median(hist, 0)
                    shrink = 0.5 * latest + 0.5 * med
                    errs["latest"].append(np.abs(truth - latest).mean())
                    errs["mean"].append(np.abs(truth - mean).mean())
                    errs["median"].append(np.abs(truth - med).mean())
                    errs["shrink"].append(np.abs(truth - shrink).mean())
                print(f"   {NICE[f]:<10} {N:>3} "
                      + " ".join(f"{np.mean(errs[k]):>9.4f}"
                                 for k in ("latest", "mean", "median", "shrink")))

        # ---------- 5. winner's curse ----------
        print("\n5. WINNER'S CURSE: where do the best ranked qubits sit next time?")
        print("   percentile rank, 0 = best. Pure persistence keeps them near 0,")
        print("   pure noise sends them to 50.")
        print(f"   {'field':<10} {'top k':>6} {'rank now':>10} {'rank next':>11} "
              f"{'rank +3':>9}")
        for f in FIELDS:
            _, arr = series(store, f)
            m = live_mask(arr)
            a = arr[:, m]
            n_items = a.shape[1]
            k = max(5, n_items // 15)
            now, nxt, nxt3 = [], [], []
            for i in range(a.shape[0] - 4):
                order = np.argsort(a[i])          # low error / high T is "best"
                best = order[:k] if f.startswith("err") else order[-k:]
                for j, step in ((0, now), (1, nxt), (3, nxt3)):
                    r = np.argsort(np.argsort(a[i + j])) / (n_items - 1)
                    if not f.startswith("err"):
                        r = 1.0 - r
                    step.append(r[best].mean() * 100)
            print(f"   {NICE[f]:<10} {k:>6} {np.mean(now):>10.1f} "
                  f"{np.mean(nxt):>11.1f} {np.mean(nxt3):>9.1f}")
        print()


main()
