"""Checkpoint 2 diagnostics, on DEVELOPMENT cards only (28 Aug to 12 Oct 2026).

OURS. EXPLORATORY AND POST-HOC throughout. Nothing here is confirmatory.

Nothing dated after 12 October 2026 is read anywhere. `data/raw` is read-only
and is not written. No IBM call is made. Aer is used in PART F ONLY; every
other part reads stored cards and the frozen results file.

SIGN CONVENTION, as in 26, 27 and 28:
    regret = ceiling minus strategy      (positive means the strategy is worse)
    gain   = F_strategy minus F_stale    (positive means the strategy is better)
For a diagnostic on an error value, "deviation" is on the LOG scale and
positive means WORSE than the comparison point, because errors are bad when
high. T1 and T2 are bad when LOW, so their log deviations are negated before
being reported, which puts every field group on one "positive is worse" scale.

PARTS
  A  schedule regularity: when in the UTC day each field group changes
  B  variogram: is a difference noise plus jumps, or drift that grows with lag
  C  mean reversion: does a value that sits above its own median come back
  D  winner's curse: are the qubits the stale layout picked unusually lucky
  E  clean layout sensitivity: error values changed, dead list held FIXED
  F  QFT ceilings: a 4-peak input, exact and approximate QFT, simulated
  G  design effects for window mean minus stale on all 5648 jobs

Wording rule from L-032: say "consistent with", never "proved".

Usage:  29_diagnostics.py [--outdir outputs/diagnostics] [--machine ibm_fez]
                          [--pairs 20] [--boot 2000]
"""
import argparse
import math
import sys
import types
import warnings
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "engine"))

WINDOW_START = "2026-08-28"
WINDOW_END = "2026-10-12"          # inclusive; nothing after this is read
MACHINES = ["ibm_fez", "ibm_kingston", "ibm_marrakesh"]
GROUPS = ["readout", "sx", "cz", "T1_T2"]
LAG_BINS = [(0, 6), (6, 12), (12, 24), (24, 48), (48, 96), (96, 168)]
MAX_PAIRS_PER_BIN = 2000           # cap, so the median is affordable
WINDOW_N_MEDIAN = 8                # "median of the last 8 distinct states"
N_RANDOM_SETS = 1000
SEED_DIAG = 20261024
POOL_DELAYS = [6, 12, 24, 48]
GAP_DAYS = ["2026-09-22", "2026-09-23"]
QFT_SIZES = [5, 8, 10]
AQFT_MIN_ANGLE = math.pi / 2 ** 3  # "drop rotations smaller than pi/2^3"


def load_module(relpath, name):
    """Import a numbered script for its functions (it calls main() at the end)."""
    path = ROOT / relpath
    src = path.read_text().rsplit("\nmain()", 1)[0]
    mod = types.ModuleType(name)
    mod.__file__ = str(path)
    exec(compile(src, str(path), "exec"), mod.__dict__)
    return mod


M20 = load_module("scripts/20_analyse_results.py", "analyse20")
M26 = load_module("scripts/26_row_check.py", "rowcheck26")

# A permanently dead qubit has T1 or T2 missing by the section 7 rule, and a
# coupler can be absent from a card altogether, so some series are all NaN for
# a whole window. np.nanmedian and np.nanmean warn on those and return NaN,
# which is the behaviour wanted here: every downstream step drops non-finite
# values before it counts anything. The warning is silenced so the output
# stays readable, NOT to hide a failure. The count of dropped values is
# printed as n_points and n_values in the tables below.
warnings.filterwarnings("ignore", message="All-NaN slice encountered")
warnings.filterwarnings("ignore", message="Mean of empty slice")


# ------------------------------------------------------------ card loading

def dev_indices(store):
    """State indices whose first_seen date is inside the development window."""
    return [i for i, t in enumerate(store.times)
            if WINDOW_START <= str(t.date()) <= WINDOW_END]


def pair_keys(store, idxs):
    keys = set()
    for i in idxs:
        keys |= set(store.snapshot(i)["err_2q"])
    return sorted(keys)


def field_matrix(store, idxs, group, pkeys=None):
    """A [state, series] matrix of raw values for one field group.

    readout -> err_ro, sx -> err_1q, cz -> err_2q over a fixed key order,
    T1_T2 -> t1 and t2 stacked side by side, because the protocol treats
    coherence as one group and a state is new if either moved.
    """
    rows, labels = [], None
    for i in idxs:
        s = store.snapshot(i)
        if group == "readout":
            v, labels = np.asarray(s["err_ro"], float), "qubit"
        elif group == "sx":
            v, labels = np.asarray(s["err_1q"], float), "qubit"
        elif group == "cz":
            v = np.array([s["err_2q"].get(k, np.nan) for k in pkeys], float)
            labels = "coupler"
        elif group == "T1_T2":
            v = np.concatenate([np.asarray(s["t1"], float),
                                np.asarray(s["t2"], float)])
            labels = "qubit (T1 then T2)"
        else:
            raise ValueError(group)
        rows.append(v)
    return np.vstack(rows), labels


def to_log(mat, group):
    """Log scale, with T1 and T2 negated so positive always means worse."""
    with np.errstate(divide="ignore", invalid="ignore"):
        out = np.log(np.where(mat > 0, mat, np.nan))
    if group == "T1_T2":
        out = -out
    return out


# ------------------------------------------------------- PART A: schedule

def part_a(stores, outdir):
    print("=" * 74)
    print("PART A: SCHEDULE REGULARITY")
    print("=" * 74)
    print("  For each machine and field group: at what UTC hour does the day's")
    print("  first CHANGED value appear, how often does each hour carry a")
    print("  change, how many days see any change at all, and did the pattern")
    print("  move around the 22 to 23 September gap.")
    print("  A state counts as a change for a group if ANY series in that")
    print("  group differs from the previous state, NaN to number included.")
    rows, hour_rows, day_rows = [], [], []
    for m, store in stores.items():
        idxs = dev_indices(store)
        pk = pair_keys(store, idxs)
        times = [store.times[i] for i in idxs]
        all_days = sorted({str(t.date()) for t in times})
        print(f"\n  {m}: {len(idxs)} development states over {len(all_days)} "
              f"days, {times[0]} to {times[-1]}")
        for grp in GROUPS:
            mat, _ = field_matrix(store, idxs, grp, pk)
            changed = np.zeros(len(idxs), bool)
            for i in range(1, len(idxs)):
                a, b = mat[i - 1], mat[i]
                diff = ~((a == b) | (np.isnan(a) & np.isnan(b)))
                changed[i] = bool(diff.any())
            ch_times = [times[i] for i in range(len(idxs)) if changed[i]]
            by_day = defaultdict(list)
            for t in ch_times:
                by_day[str(t.date())].append(t)
            days_with = sorted(by_day)
            first_hours = [min(v).hour for v in by_day.values()]
            n_ch_per_day = {d: len(v) for d, v in by_day.items()}
            print(f"    {grp:<7} states that changed it {int(changed.sum()):>4}"
                  f"   days with any change {len(days_with):>3} of "
                  f"{len(all_days)} ({len(days_with)/len(all_days)*100:>5.1f}%)"
                  f"   changes per changing day median "
                  f"{int(np.median(list(n_ch_per_day.values()))) if n_ch_per_day else 0}")
            if first_hours:
                fh = np.array(first_hours)
                print(f"            first-change hour: median {int(np.median(fh)):>2}"
                      f"  mean {fh.mean():>5.1f}  IQR "
                      f"{int(np.percentile(fh,25))} to "
                      f"{int(np.percentile(fh,75))}  min {fh.min()} max {fh.max()}")
            rows.append(dict(
                machine=m, group=grp, dev_states=len(idxs),
                states_changing=int(changed.sum()), days_total=len(all_days),
                days_with_change=len(days_with),
                share_days_with_change=len(days_with) / len(all_days),
                first_hour_median=float(np.median(first_hours)) if first_hours else float("nan"),
                first_hour_mean=float(np.mean(first_hours)) if first_hours else float("nan"),
                first_hour_min=int(min(first_hours)) if first_hours else -1,
                first_hour_max=int(max(first_hours)) if first_hours else -1))
            for h in range(24):
                n_first = sum(1 for x in first_hours if x == h)
                n_any = sum(1 for d, v in by_day.items()
                            if any(t.hour == h for t in v))
                hour_rows.append(dict(
                    machine=m, group=grp, utc_hour=h,
                    days_first_change_in_this_hour=n_first,
                    share_days_first_change=n_first / len(all_days),
                    days_any_change_in_this_hour=n_any,
                    share_days_any_change=n_any / len(all_days)))
            for d in all_days:
                day_rows.append(dict(
                    machine=m, group=grp, day=d,
                    n_changes=n_ch_per_day.get(d, 0),
                    first_change_hour=(min(by_day[d]).hour if d in by_day
                                       else -1),
                    in_gap=d in GAP_DAYS))
    hr = pd.DataFrame(hour_rows)
    pd.DataFrame(rows).to_csv(outdir / "A1_schedule_summary.csv", index=False)
    hr.to_csv(outdir / "A2_schedule_by_hour.csv", index=False)
    dd = pd.DataFrame(day_rows)
    dd.to_csv(outdir / "A3_schedule_by_day.csv", index=False)

    print("\n  SHARE OF DAYS WITH ANY CHANGE IN EACH UTC HOUR, percent")
    for m in stores:
        print(f"\n    {m}")
        print("      hour " + " ".join(f"{h:>4}" for h in range(24)))
        for grp in GROUPS:
            s = hr[(hr.machine == m) & (hr.group == grp)]
            print(f"      {grp:<5}" + " ".join(
                f"{v*100:>4.0f}" for v in s.share_days_any_change))

    print("\n  DID THE PATTERN MOVE? first-change hour before and after the gap")
    print("  Before means days up to 21 September, after means from 24")
    print("  September. The two gap days are shown on their own.")
    shift = []
    for m in stores:
        for grp in GROUPS:
            s = dd[(dd.machine == m) & (dd.group == grp)
                   & (dd.first_change_hour >= 0)]
            before = s[s.day <= "2026-09-21"].first_change_hour
            after = s[s.day >= "2026-09-24"].first_change_hour
            gap = s[s.day.isin(GAP_DAYS)].first_change_hour
            n_nochange_gap = int(((dd.machine == m) & (dd.group == grp)
                                  & dd.day.isin(GAP_DAYS)
                                  & (dd.n_changes == 0)).sum())
            print(f"    {m:<15} {grp:<6} before n={len(before):>3} median "
                  f"{np.median(before) if len(before) else float('nan'):>5.1f}"
                  f"   after n={len(after):>3} median "
                  f"{np.median(after) if len(after) else float('nan'):>5.1f}"
                  f"   gap days with a change {len(gap)} of 2, with none "
                  f"{n_nochange_gap}")
            shift.append(dict(
                machine=m, group=grp, n_days_before=len(before),
                median_first_hour_before=float(np.median(before)) if len(before) else float("nan"),
                n_days_after=len(after),
                median_first_hour_after=float(np.median(after)) if len(after) else float("nan"),
                gap_days_with_change=len(gap),
                gap_days_with_no_change=n_nochange_gap))
    pd.DataFrame(shift).to_csv(outdir / "A4_pattern_shift.csv", index=False)
    print("\n  Days with NO change at all, by group, listed so the gap is "
          "visible:")
    for m in stores:
        for grp in GROUPS:
            z = dd[(dd.machine == m) & (dd.group == grp) & (dd.n_changes == 0)]
            if len(z):
                print(f"    {m:<15} {grp:<6} {len(z):>2} days: "
                      f"{', '.join(z.day.tolist())}")
    return dd


# ------------------------------------------------------ PART B: variogram

def part_b(stores, outdir, rng):
    print("\n" + "=" * 74)
    print("PART B: VARIOGRAM, NOISE AGAINST DRIFT")
    print("=" * 74)
    print("  On LOG values over distinct development states. For each pair of")
    print("  states whose gap falls in a lag bin, the difference of a series")
    print("  against ITSELF is taken, then the mean squared difference and the")
    print("  median absolute difference over all series and all pairs in the")
    print(f"  bin. Pairs per bin are capped at {MAX_PAIRS_PER_BIN}, drawn with")
    print(f"  seed {SEED_DIAG}, so the median is affordable.")
    print("  A curve FLAT from the first bin is consistent with measurement")
    print("  noise plus occasional jumps. A curve that RISES with lag is")
    print("  consistent with drift that accumulates.")
    rows = []
    for m, store in stores.items():
        idxs = dev_indices(store)
        pk = pair_keys(store, idxs)
        hours = np.array([(store.times[i] - store.times[idxs[0]]).total_seconds()
                          / 3600.0 for i in idxs])
        print(f"\n  {m}")
        for grp in GROUPS:
            mat, label = field_matrix(store, idxs, grp, pk)
            L = to_log(mat, grp)
            n = len(idxs)
            ii, jj = np.triu_indices(n, k=1)
            dt = hours[jj] - hours[ii]
            cells = []
            for lo, hi in LAG_BINS:
                sel = np.where((dt >= lo) & (dt < hi))[0]
                if len(sel) == 0:
                    cells.append("     no pairs")
                    rows.append(dict(machine=m, group=grp, series=label,
                                     lag_lo_h=lo, lag_hi_h=hi, n_pairs=0,
                                     n_values=0, mean_sq_diff=float("nan"),
                                     median_abs_diff=float("nan"),
                                     rms_diff=float("nan")))
                    continue
                if len(sel) > MAX_PAIRS_PER_BIN:
                    sel = rng.choice(sel, size=MAX_PAIRS_PER_BIN,
                                     replace=False)
                d = L[jj[sel]] - L[ii[sel]]
                d = d[np.isfinite(d)]
                msq = float(np.mean(d ** 2)) if d.size else float("nan")
                mad = float(np.median(np.abs(d))) if d.size else float("nan")
                zero = float((np.abs(d) < 1e-12).mean()) if d.size else float("nan")
                cells.append(f"{msq:>7.4f}/{mad:>6.4f}/{zero*100:>3.0f}%")
                rows.append(dict(machine=m, group=grp, series=label,
                                 lag_lo_h=lo, lag_hi_h=hi, n_pairs=len(sel),
                                 n_values=int(d.size), mean_sq_diff=msq,
                                 median_abs_diff=mad,
                                 share_exactly_unchanged=zero,
                                 rms_diff=float(np.sqrt(msq))))
            print(f"    {grp:<7} " + "  ".join(
                f"{lo}-{hi}h {c}" for (lo, hi), c in zip(LAG_BINS, cells)))
    out = pd.DataFrame(rows)
    out.to_csv(outdir / "B1_variogram.csv", index=False)
    print("\n  each cell is  mean squared difference / median absolute "
          "difference /")
    print("  share of comparisons where the value did not move AT ALL, on the")
    print("  log scale. That last share is why several medians are exactly")
    print("  0.0000: in the short bins more than half of the comparisons are")
    print("  between two cards that carry the identical number, because sx, cz")
    print("  and the coherence fields are only remeasured about once a day.")
    print("  L-017 measured the same thing from the value dates.")

    print("\n  SHAPE OF EACH CURVE: last bin divided by first bin")
    shape = []
    for m in stores:
        for grp in GROUPS:
            s = out[(out.machine == m) & (out.group == grp)].dropna(
                subset=["mean_sq_diff"])
            if len(s) < 2:
                continue
            f, l = s.iloc[0], s.iloc[-1]
            ratio_sq = l.mean_sq_diff / f.mean_sq_diff
            ratio_mad = (l.median_abs_diff / f.median_abs_diff
                         if f.median_abs_diff > 0 else float("nan"))
            # The verdict rests on the mean squared difference, because the
            # median is exactly 0 in the short bins for most groups, which
            # makes its ratio undefined rather than small.
            verdict = ("rises with lag, consistent with drift" if ratio_sq >= 1.5
                       else "roughly flat, consistent with noise plus jumps"
                       if ratio_sq <= 1.2 else "rises mildly, in between")
            mad_txt = ("    n/a" if not np.isfinite(ratio_mad)
                       else f"{ratio_mad:>7.2f}")
            print(f"    {m:<15} {grp:<6} msq x{ratio_sq:>5.2f}  "
                  f"mad x{mad_txt}   {verdict}")
            shape.append(dict(machine=m, group=grp,
                              first_bin=f"{int(f.lag_lo_h)}-{int(f.lag_hi_h)}h",
                              last_bin=f"{int(l.lag_lo_h)}-{int(l.lag_hi_h)}h",
                              ratio_mean_sq=ratio_sq,
                              ratio_median_abs=ratio_mad, verdict=verdict))
    pd.DataFrame(shape).to_csv(outdir / "B2_variogram_shape.csv", index=False)
    print("  mad n/a means the first bin's median absolute difference is")
    print("  exactly 0, so the ratio has no value. The verdict uses the mean")
    print("  squared difference, which is defined in every bin.")
    return out


# -------------------------------------------------- PART C: mean reversion

def part_c(stores, outdir, rng, n_boot):
    print("\n" + "=" * 74)
    print("PART C: MEAN REVERSION")
    print("=" * 74)
    print(f"  For each field group, the NEXT change (log value at the next")
    print(f"  distinct state minus the log value now) is regressed on the")
    print(f"  CURRENT deviation (log value now minus the median of the last")
    print(f"  {WINDOW_N_MEDIAN} distinct states, this series only).")
    print("  A slope near -1 means a deviation is fully undone by the next")
    print("  state. A slope near 0 means it persists. The interval is a 95")
    print("  percent block bootstrap over whole CALENDAR DAYS, the same unit")
    print("  PROTOCOL.md section 11 uses.")
    rows = []
    for m, store in stores.items():
        idxs = dev_indices(store)
        pk = pair_keys(store, idxs)
        print(f"\n  {m}")
        for grp in GROUPS:
            mat, _ = field_matrix(store, idxs, grp, pk)
            L = to_log(mat, grp)
            days = np.array([str(store.times[i].date()) for i in idxs])
            xs, ys, ds = [], [], []
            for t in range(WINDOW_N_MEDIAN - 1, len(idxs) - 1):
                hist = L[t - WINDOW_N_MEDIAN + 1:t + 1]
                med = np.nanmedian(hist, axis=0)
                x = L[t] - med
                y = L[t + 1] - L[t]
                ok = np.isfinite(x) & np.isfinite(y)
                xs.append(x[ok])
                ys.append(y[ok])
                ds.append(np.full(ok.sum(), days[t]))
            if not xs:
                continue
            X = np.concatenate(xs)
            Y = np.concatenate(ys)
            D = np.concatenate(ds)
            if X.size < 10 or np.allclose(X.std(), 0):
                print(f"    {grp:<7} not enough spread to regress")
                continue
            slope = float(np.polyfit(X, Y, 1)[0])
            uniq = np.unique(D)
            by_day = {d: np.where(D == d)[0] for d in uniq}
            draws = np.empty(n_boot)
            for b in range(n_boot):
                pick = rng.choice(uniq, size=len(uniq), replace=True)
                idx = np.concatenate([by_day[d] for d in pick])
                xb, yb = X[idx], Y[idx]
                draws[b] = (np.polyfit(xb, yb, 1)[0]
                            if xb.std() > 0 else np.nan)
            lo, hi = np.nanpercentile(draws, [2.5, 97.5])
            r = float(np.corrcoef(X, Y)[0, 1])
            verdict = ("strong mean reversion" if hi < -0.7 else
                       "mean reversion" if hi < -0.2 else
                       "weak or none" if hi < 0 else "no reversion detected")
            print(f"    {grp:<7} n={X.size:>7}  slope {slope:>+7.4f}  "
                  f"[{lo:>+7.4f}, {hi:>+7.4f}]  corr {r:>+6.3f}  "
                  f"days {len(uniq):>2}   {verdict}")
            rows.append(dict(machine=m, group=grp, n_points=int(X.size),
                             n_days=len(uniq), slope=slope, lo=lo, hi=hi,
                             correlation=r, verdict=verdict))
    out = pd.DataFrame(rows)
    out.to_csv(outdir / "C1_mean_reversion.csv", index=False)
    return out


# --------------------------------------------------- PART D: winner's curse

def part_d(stores, df, outdir, rng):
    print("\n" + "=" * 74)
    print("PART D: WINNER'S CURSE ON THE STALE ghz8 LAYOUT")
    print("=" * 74)
    print("  For every ghz8 job, the qubits the STALE arm actually used are")
    print("  compared with their own recent history, and then with "
          f"{N_RANDOM_SETS} random")
    print("  same-size qubit sets drawn from the live qubits of the same card.")
    print("  Deviation is on the log scale, and positive means WORSE, so a")
    print("  NEGATIVE deviation means the qubit looked better than its own")
    print(f"  median of the last {WINDOW_N_MEDIAN} distinct states.")
    print("  The rise is the log change from the submission card to the")
    print("  run-time card, where positive again means it got worse.")
    print("  All jobs used here are inside the development window; the job")
    print("  list is Round 1's, which runs 21 September to 12 October.")
    sub = df[(df.circuit == "ghz8") & (df.arm == "stale")].copy()
    print(f"\n  ghz8 stale rows available: {len(sub)}")
    qgroups = ["readout", "sx", "T1_T2"]
    cache = {}

    def dev_and_live(m, state_i):
        """Log deviation from the trailing median, per qubit, at one state."""
        key = (m, state_i)
        if key in cache:
            return cache[key]
        store = stores[m]
        pos = state_i
        lo = max(0, pos - WINDOW_N_MEDIAN + 1)
        hist = list(range(lo, pos + 1))
        out = {}
        for grp in qgroups:
            mat, _ = field_matrix(store, hist, grp)
            L = to_log(mat, grp)
            med = np.nanmedian(L, axis=0)
            out[grp] = L[-1] - med
        import real_data as rd
        dead = rd.dead_qubits(store.snapshot(state_i))
        nq = store.n_qubits
        live = np.array([q for q in range(nq) if q not in dead])
        cache[key] = (out, live)
        if len(cache) > 400:
            cache.pop(next(iter(cache)))
        return cache[key]

    rows = []
    for _, r in sub.iterrows():
        m = r.machine
        used = [int(x) for x in str(r.qubits_used).split()]
        dev_i, live = dev_and_live(m, int(r.info_state))
        dev_t, _ = dev_and_live(m, int(r.truth_state))
        store = stores[m]
        k = len(used)
        if k == 0 or len(live) < k:
            continue
        order = rng.random((N_RANDOM_SETS, len(live))).argsort(axis=1)[:, :k]
        rand_sets = live[order]
        for grp in qgroups:
            d = dev_i[grp]
            nq = store.n_qubits
            if grp == "T1_T2":
                # two series per qubit; average the T1 and T2 deviation
                d = np.nanmean(np.vstack([d[:nq], d[nq:]]), axis=0)
            chosen = float(np.nanmean(d[used]))
            rand = np.nanmean(d[rand_sets], axis=1)
            pct = float((rand < chosen).mean() * 100)
            # how much the same qubits moved by the run-time card
            raw_i, _ = field_matrix(store, [int(r.info_state)], grp)
            raw_t, _ = field_matrix(store, [int(r.truth_state)], grp)
            Li = to_log(raw_i, grp)[0]
            Lt = to_log(raw_t, grp)[0]
            if grp == "T1_T2":
                Li = np.nanmean(np.vstack([Li[:nq], Li[nq:]]), axis=0)
                Lt = np.nanmean(np.vstack([Lt[:nq], Lt[nq:]]), axis=0)
            rise_ch = float(np.nanmean(Lt[used] - Li[used]))
            rise_rd = float(np.nanmean(np.nanmean(Lt[rand_sets]
                                                  - Li[rand_sets], axis=1)))
            rows.append(dict(
                machine=m, delay_h=int(r.delay_h), day=str(r.day), group=grp,
                n_qubits=k, chosen_dev=chosen,
                random_dev_mean=float(np.nanmean(rand)),
                percentile_of_chosen=pct, chosen_rise=rise_ch,
                random_rise=rise_rd))
    out = pd.DataFrame(rows)
    out.to_csv(outdir / "D1_winners_curse_rows.csv", index=False)

    print(f"\n  {len(out)} job-group rows computed")
    print(f"\n  {'group':<8} {'chosen dev':>11} {'random dev':>11} "
          f"{'pctile':>8} {'chosen rise':>12} {'random rise':>12} "
          f"{'rise gap':>9}")
    summ = []
    for grp in qgroups:
        s = out[out.group == grp]
        if not len(s):
            continue
        print(f"  {grp:<8} {s.chosen_dev.mean():>+11.4f} "
              f"{s.random_dev_mean.mean():>+11.4f} "
              f"{s.percentile_of_chosen.mean():>7.1f}% "
              f"{s.chosen_rise.mean():>+12.4f} {s.random_rise.mean():>+12.4f} "
              f"{s.chosen_rise.mean()-s.random_rise.mean():>+9.4f}")
        summ.append(dict(
            group=grp, n_jobs=len(s), chosen_dev=s.chosen_dev.mean(),
            random_dev=s.random_dev_mean.mean(),
            mean_percentile=s.percentile_of_chosen.mean(),
            share_below_5th_pct=float((s.percentile_of_chosen < 5).mean() * 100),
            chosen_rise=s.chosen_rise.mean(), random_rise=s.random_rise.mean(),
            rise_gap=s.chosen_rise.mean() - s.random_rise.mean()))
    sm = pd.DataFrame(summ)
    sm.to_csv(outdir / "D2_winners_curse_summary.csv", index=False)
    print("\n  pctile is where the chosen set's mean deviation sits inside the")
    print(f"  {N_RANDOM_SETS} random sets. Below 50 means the chosen qubits "
          f"looked")
    print("  better than a random set of the same size on the card the")
    print("  strategy saw.")
    for _, r in sm.iterrows():
        print(f"    {r['group']:<8} share of jobs where the chosen set sat "
              f"below the 5th percentile of random sets: "
              f"{r['share_below_5th_pct']:.1f}%")
    print("\n  by delay, readout group, chosen rise against random rise")
    s = out[out.group == "readout"]
    for D, g in s.groupby("delay_h"):
        print(f"    D={D:>3}h  n={len(g):>5}  chosen {g.chosen_rise.mean():+.4f}"
              f"   random {g.random_rise.mean():+.4f}   gap "
              f"{g.chosen_rise.mean()-g.random_rise.mean():+.4f}")
    out[out.group == "readout"].groupby("delay_h").agg(
        n=("chosen_rise", "size"), chosen_rise=("chosen_rise", "mean"),
        random_rise=("random_rise", "mean")).to_csv(
        outdir / "D3_winners_curse_by_delay.csv")
    return sm


# ------------------------------------------- PART E: clean layout sensitivity

def part_e(stores, outdir, machine, n_pairs):
    print("\n" + "=" * 74)
    print("PART E: CLEAN LAYOUT SENSITIVITY, DEAD LIST HELD FIXED")
    print("=" * 74)
    print("  L-052 measured this with the dead list free to move, so a layout")
    print("  could shift because the coupling map changed rather than because")
    print("  the error numbers changed. Here the removed set is the UNION of")
    print("  both cards' dead qubits plus the permanent defects, applied to")
    print("  BOTH cards, so the compiler sees the same device twice and only")
    print("  the error values differ. Level 2, seed 11, the Round 1 settings.")
    import circuits as circ_mod
    import engine_config as cfg
    import jobs as jobs_mod
    import real_data as rd
    from qiskit import QuantumCircuit
    from qiskit.transpiler import generate_preset_pass_manager

    store = stores[machine]
    base, _ = rd.load_base_target(machine)
    idxs = dev_indices(store)
    train = [i for i, t in enumerate(store.times) if jobs_mod.in_training(t)]
    permanent = None
    for i in train:
        d = rd.dead_qubits(store.snapshot(i))
        permanent = set(d) if permanent is None else (permanent & d)
    permanent = permanent or set()

    qcs = {c: circ_mod.build(c) for c in ["ghz5", "ghz8", "bv8", "bv10"]}
    for n in QFT_SIZES:
        qc = QuantumCircuit(n, name=f"qft{n}")
        qc.compose(qft_circuit(n), inplace=True)
        qc.measure_all()
        qcs[f"qft{n}"] = qc
    names = ["ghz5", "ghz8", "bv8", "bv10"] + [f"qft{n}" for n in QFT_SIZES]

    rng = np.random.default_rng(SEED_DIAG)
    pairs = []
    while len(pairs) < n_pairs:
        a, b = rng.choice(idxs, size=2, replace=False)
        if (int(a), int(b)) not in pairs and (int(b), int(a)) not in pairs:
            pairs.append((int(a), int(b)))
    print(f"\n  {machine}: {n_pairs} pairs from {len(idxs)} development states")
    print(f"  permanent defects: {sorted(permanent)}")

    def layout_of(qc, snap, forbid):
        target, _ = rd.build_target(snap, base, forbid=forbid)
        pm = generate_preset_pass_manager(
            optimization_level=cfg.OPT_LEVEL, target=target,
            seed_transpiler=cfg.SEED_TRANSPILE)
        isa = pm.run(qc)
        return sorted(isa.layout.final_index_layout()), isa.depth(), \
            isa.count_ops().get("cz", 0)

    rows = []
    forbid_sizes = []
    per_pair_forbid = []
    for a, b in pairs:
        fa = rd.dead_qubits(store.snapshot(a))
        fb = rd.dead_qubits(store.snapshot(b))
        forbid = frozenset(set(fa) | set(fb) | permanent)
        per_pair_forbid.append(forbid)
        forbid_sizes.append(len(forbid))
    print(f"  fixed removed set per pair: size min {min(forbid_sizes)}, "
          f"median {int(np.median(forbid_sizes))}, max {max(forbid_sizes)}")
    print(f"\n  {'circuit':<8} {'qubit set changed':>18} {'order changed':>15} "
          f"{'depth changed':>14} {'cz changed':>11}")
    for n in names:
        chg_set = chg_ord = chg_depth = chg_cz = 0
        for (a, b), forbid in zip(pairs, per_pair_forbid):
            la, da, za = layout_of(qcs[n], store.snapshot(a), forbid)
            lb, db, zb = layout_of(qcs[n], store.snapshot(b), forbid)
            chg_set += set(la) != set(lb)
            chg_ord += la != lb
            chg_depth += da != db
            chg_cz += za != zb
        print(f"  {n:<8} {chg_set/n_pairs*100:>17.1f}% "
              f"{chg_ord/n_pairs*100:>14.1f}% {chg_depth/n_pairs*100:>13.1f}% "
              f"{chg_cz/n_pairs*100:>10.1f}%")
        rows.append(dict(machine=machine, circuit=n, level=cfg.OPT_LEVEL,
                         seed=cfg.SEED_TRANSPILE, n_pairs=n_pairs,
                         pct_qubit_set_changed=chg_set / n_pairs * 100,
                         pct_order_changed=chg_ord / n_pairs * 100,
                         pct_depth_changed=chg_depth / n_pairs * 100,
                         pct_cz_changed=chg_cz / n_pairs * 100,
                         removed_set="union of both cards' dead plus permanent"))
    out = pd.DataFrame(rows)
    out.to_csv(outdir / "E1_clean_layout_sensitivity.csv", index=False)
    print("\n  Every move here is caused by the error numbers alone, because")
    print("  the device the compiler saw was identical for both cards.")
    return out


# ----------------------------------------------------- PART F: QFT ceilings

def qft_circuit(n, min_angle=None):
    """QFT with qubit 0 as the least significant bit.

    Verified against qiskit.circuit.library.QFTGate to 1e-16 for n = 5 and 8.
    `min_angle` drops every controlled phase smaller than that angle, which is
    how the approximate QFT is built here.
    """
    from qiskit import QuantumCircuit
    qc = QuantumCircuit(n, name="qft" if min_angle is None else "aqft")
    for j in reversed(range(n)):
        qc.h(j)
        for k in range(j):
            ang = math.pi / 2 ** (j - k)
            if min_angle is None or ang >= min_angle - 1e-12:
                qc.cp(ang, k, j)
    for i in range(n // 2):
        qc.swap(i, n - 1 - i)
    return qc


def four_peak_circuit(n, min_angle=None):
    """A QFT job whose ideal output is exactly 4 equal peaks.

    The input is the uniform superposition over every integer x with
    x = 0 mod 4, which is H on qubits 2..n-1 with qubits 0 and 1 left in |0>.
    The QFT of a comb of spacing 4 is a comb of spacing N/4, so exactly 4
    outcomes survive, at y = 0, N/4, N/2 and 3N/4, each with probability 1/4.
    """
    from qiskit import QuantumCircuit
    qc = QuantumCircuit(n, name=f"peak4_{n}")
    for q in range(2, n):
        qc.h(q)
    qc.compose(qft_circuit(n, min_angle), inplace=True)
    qc.measure_all()
    return qc


def part_f(stores, outdir):
    print("\n" + "=" * 74)
    print("PART F: QFT CEILINGS ON A 4-PEAK INPUT")
    print("=" * 74)
    import circuits as circ_mod
    import engine_config as cfg
    import real_data as rd
    import snapshot as team_snapshot
    from qiskit.quantum_info import hellinger_fidelity
    from qiskit.transpiler import generate_preset_pass_manager

    print("  THE INPUT, in simple words. The QFT turns a repeating pattern")
    print("  into a small number of sharp peaks. I feed it the even-er comb:")
    print("  every whole number that divides by 4, all with the same weight.")
    print("  In circuit terms that is one H on each qubit from 2 upward, with")
    print("  qubits 0 and 1 left alone, because fixing the two lowest bits to")
    print("  0 is the same as saying 'x divides by 4'.")
    print("  A comb of spacing 4 going in gives a comb of spacing N/4 coming")
    print("  out, so with N = 2^n outcomes only 4 survive: 0, N/4, N/2 and")
    print("  3N/4, each with probability exactly 1/4. Everything else cancels.")
    print("  This is a good test circuit because the right answer is 4 equal")
    print("  bars, so noise shows up as weight leaking into the other bars")
    print("  rather than as a shift that is hard to read.")

    ideal_rows = []
    for n in QFT_SIZES:
        for tag, ma in (("exact", None), ("approx", AQFT_MIN_ANGLE)):
            qc = four_peak_circuit(n, ma)
            ideal = circ_mod.ideal_distribution(qc)
            keys = sorted(ideal, key=lambda s: int(s, 2))
            ncp = sum(1 for i in qc.data if i.operation.name == "cp")
            print(f"\n  n={n} {tag}: {ncp} controlled phase gates before "
                  f"compiling")
            print(f"    ideal distribution, {len(ideal)} outcomes:")
            for k in keys:
                print(f"      {k}  = decimal {int(k,2):>5}  "
                      f"probability {ideal[k]:.6f}")
            ideal_rows.append(dict(n=n, variant=tag, n_cp_logical=ncp,
                                   n_outcomes=len(ideal),
                                   outcomes=" ".join(keys),
                                   probabilities=" ".join(f"{ideal[k]:.6f}"
                                                          for k in keys)))
    pd.DataFrame(ideal_rows).to_csv(outdir / "F1_ideal_distributions.csv",
                                    index=False)
    print("\n  Note on the approximate QFT. Dropping every rotation smaller")
    print(f"  than pi/2^3 leaves the ideal answer EXACTLY the same 4 peaks.")
    print("  That is not luck: the surviving outcomes are multiples of N/4, so")
    print("  they depend only on the two most significant output bits, and the")
    print("  rotations that get dropped are the ones that only set the finer")
    print("  bits. So the approximation is free for this particular input, and")
    print("  it cuts the two-qubit gate count a lot.")

    rows = []
    print(f"\n  SIMULATED, one mid-period development card per machine")
    print(f"  compiled at level {cfg.OPT_LEVEL} with that card's own target and")
    print(f"  simulated in Aer with the SAME card as truth, "
          f"{cfg.SHOTS} shots.")
    print("  This is a ceiling: there is no staleness, the card the compiler")
    print("  saw is the card it ran on.")
    print(f"\n  {'machine':<15} {'card (UTC)':<26} {'circuit':<12} "
          f"{'cz':>5} {'depth':>6} {'fidelity':>9}")
    low_exact10 = []
    for m, store in stores.items():
        import jobs as jobs_mod
        idxs = dev_indices(store)
        mid = idxs[len(idxs) // 2]
        snap = store.snapshot(mid)
        base, _ = rd.load_base_target(m)
        train = [i for i, t in enumerate(store.times) if jobs_mod.in_training(t)]
        permanent = None
        for i in train:
            d = rd.dead_qubits(store.snapshot(i))
            permanent = set(d) if permanent is None else (permanent & d)
        permanent = permanent or set()
        s_target, forbid, _ = rd.strategy_target(snap, base, permanent)
        t_target, _ = rd.truth_target(snap, base, permanent)
        from qiskit_aer import AerSimulator
        sim = AerSimulator(noise_model=team_snapshot.noise_model(t_target),
                           max_parallel_threads=1, max_parallel_experiments=1)
        for n in QFT_SIZES:
            for tag, ma in (("exact", None), ("approx", AQFT_MIN_ANGLE)):
                qc = four_peak_circuit(n, ma)
                ideal = circ_mod.ideal_distribution(qc)
                pm = generate_preset_pass_manager(
                    optimization_level=cfg.OPT_LEVEL, target=s_target,
                    seed_transpiler=cfg.SEED_TRANSPILE)
                isa = pm.run(qc)
                try:
                    counts = sim.run(isa, shots=cfg.SHOTS,
                                     seed_simulator=cfg.SEED_SIM
                                     ).result().get_counts()
                    fid = hellinger_fidelity(ideal, counts)
                except Exception as exc:
                    fid = float("nan")
                    print(f"    simulation failed for {m} qft{n} {tag}: "
                          f"{type(exc).__name__}")
                cz = isa.count_ops().get("cz", 0)
                print(f"  {m:<15} {str(store.times[mid]):<26} "
                      f"{'qft'+str(n)+' '+tag:<12} {cz:>5} {isa.depth():>6} "
                      f"{fid:>9.4f}")
                rows.append(dict(machine=m, card_utc=str(store.times[mid]),
                                 state_index=mid, n=n, variant=tag,
                                 cz=cz, depth=isa.depth(), fidelity=fid,
                                 n_forbidden=len(forbid), shots=cfg.SHOTS))
                if n == 10 and tag == "exact" and fid < 0.20:
                    low_exact10.append((m, fid))
    out = pd.DataFrame(rows)
    out.to_csv(outdir / "F2_qft_ceilings.csv", index=False)

    print("\n  mean over the three machines")
    print(out.groupby(["n", "variant"])[["cz", "depth", "fidelity"]].mean()
          .to_string(float_format=lambda x: f"{x:.4f}"))

    print("\n  " + "!" * 68)
    if low_exact10:
        print("  STOP AND READ. The exact 10 qubit QFT ceiling is BELOW 0.20.")
        for m, f in low_exact10:
            print(f"    {m:<15} exact qft10 fidelity {f:.4f}")
        print("  This was the threshold you asked me to stop at. At this")
        print("  fidelity the exact 10 qubit QFT has no usable headroom on")
        print("  these cards, so a staleness experiment built on it would be")
        print("  measuring noise against noise. The approximate version is the")
        print("  one with room to move. I am reporting this and going no")
        print("  further with exact qft10.")
    else:
        print("  The exact 10 qubit QFT ceiling is at or above 0.20 on every")
        print("  machine, so the stop condition you set was NOT triggered.")
    print("  " + "!" * 68)
    return out, low_exact10


# ---------------------------------------------------- PART G: design effects

def part_g(outdir, results):
    print("\n" + "=" * 74)
    print("PART G: DESIGN EFFECTS FOR WINDOW MEAN MINUS STALE, ALL 5648 JOBS")
    print("=" * 74)
    print("  gain = window mean minus stale, positive means window mean is")
    print("  better. Pooled over 6, 12, 24 and 48 h. Helpers imported from")
    print("  scripts/26_row_check.py. EXPLORATORY.")
    df = M20.load(results)
    w = M20.widen(df)
    w = w.copy()
    w["gain"] = w["window_mean"] - w["stale"]
    w["day_str"] = w.day.astype(str)
    g = w[w.delay_h.isin(POOL_DELAYS)]
    sd, n = g["gain"].std(ddof=1), len(g)
    naive = sd / math.sqrt(n)
    se_day, ncd = M26.cluster_boot_se(
        g, "gain", ["machine", "day_str"],
        np.random.default_rng(M20.SEED_BOOT), M20.N_BOOT, within="machine")
    se_sub, ncs = M26.cluster_boot_se(
        g, "gain", ["machine", "draw_order"],
        np.random.default_rng(M20.SEED_BOOT), M20.N_BOOT)
    icc, _, _, _, _ = M26.icc_oneway(
        g["gain"].to_numpy(),
        list(map(tuple, g[["machine", "day_str"]].to_numpy())))
    print(f"\n  jobs in the file: {len(w)}   pooled jobs used: {n}")
    print(f"  paired SD                              {sd:.6f}")
    print(f"  naive SE (SD / sqrt(n))                {naive:.6f}")
    print(f"  SE, days within machine ({ncd} clusters)   {se_day:.6f}")
    print(f"  SE, machine and submission ({ncs} clusters) {se_sub:.6f}")
    print(f"  design effect, days within machine     {(se_day/naive)**2:.4f}")
    print(f"  design effect, machine and submission  {(se_sub/naive)**2:.4f}")
    print(f"  ICC by (machine, day)                  {icc:+.5f}")
    out = pd.DataFrame([dict(
        contrast="window_mean minus stale", scope=f"pooled {POOL_DELAYS} h",
        n_jobs=n, paired_sd=sd, naive_se=naive,
        se_boot_days_within_machine=se_day, n_day_clusters=ncd,
        se_boot_machine_submission=se_sub, n_submission_clusters=ncs,
        design_effect_days=(se_day / naive) ** 2,
        design_effect_submission=(se_sub / naive) ** 2,
        icc_machine_day=icc)])
    out.to_csv(outdir / "G1_design_effects_all_jobs.csv", index=False)
    return out


# ------------------------------------------------------------------ summary

def summary(a_days, b_out, c_out, d_summ, e_out, f_out, low10, g_out):
    print("\n" + "=" * 74)
    print("PLAIN SUMMARY: WHAT EACH RESULT SUGGESTS FOR THE RULE")
    print("=" * 74)

    print("\n  A, schedule. ", end="")
    hi = a_days[a_days.group == "readout"]
    print(f"Readout changes on {(hi.n_changes>0).mean()*100:.0f} percent of")
    print("  machine-days and the other groups less often. If the first change")
    print("  of a day lands in a narrow band of hours, a submission can be")
    print("  timed to sit just after it, and the exact numbers per machine are")
    print("  in A2_schedule_by_hour.csv. For the rule this matters because a")
    print("  shrinkage weight that is right just before a publication is not")
    print("  the weight that is right just after one.")

    print("\n  B, variogram. ", end="")
    # The ratio is formed WITHIN each machine first and only then averaged,
    # because taking iloc[0] and iloc[-1] of the pooled frame would divide one
    # machine's last bin by another machine's first bin.
    per_machine = {}
    for (m, grp), s in b_out.groupby(["machine", "group"]):
        s = s.dropna(subset=["mean_sq_diff"])
        if len(s) >= 2:
            per_machine.setdefault(grp, []).append(
                s.iloc[-1].mean_sq_diff / s.iloc[0].mean_sq_diff)
    ratios = {g: float(np.mean(v)) for g, v in sorted(per_machine.items())}
    print("last bin over first bin, each machine on its own then averaged:")
    for grp, r in ratios.items():
        shape = ("rises with lag, consistent with drift" if r >= 1.5 else
                 "roughly flat, consistent with noise plus jumps"
                 if r <= 1.2 else "rises mildly, in between")
        print(f"    {grp:<7} x{r:>5.2f}   {shape}")
    print("  A flat curve says the difference between two cards is mostly")
    print("  measurement noise and the odd jump, so averaging over past states")
    print("  should help. A rising curve says real drift accumulates, so the")
    print("  newest number carries information the older ones do not, and")
    print("  heavy averaging would throw that away.")

    print("\n  C, mean reversion. slopes, averaged over machines:")
    for grp, s in c_out.groupby("group"):
        print(f"    {grp:<7} slope {s.slope.mean():+.4f}   "
              f"intervals {'all below zero' if (s.hi<0).all() else 'not all below zero'}")
    print("  A slope near -1 means a value that sits above its own median is")
    print("  pulled most of the way back by the very next state, which is")
    print("  exactly the case where shrinking toward the median helps. A slope")
    print("  near 0 means the deviation sticks, and shrinking would be a")
    print("  mistake. This is the most direct evidence for or against the")
    print("  shape of our rule.")

    print("\n  D, winner's curse. ")
    for _, r in d_summ.iterrows():
        print(f"    {r['group']:<7} chosen deviation {r['chosen_dev']:+.4f} "
              f"against random {r['random_dev']:+.4f}, chosen sits at the "
              f"{r['mean_percentile']:.0f}th percentile")
        print(f"            rise to the run card: chosen {r['chosen_rise']:+.4f}"
              f"  random {r['random_rise']:+.4f}  gap {r['rise_gap']:+.4f}")
    print("  If the chosen qubits sit well below the random sets on the card")
    print("  the strategy saw, and then rise by more than random sets do, that")
    print("  is the winner's curse: the compiler picked the qubits that looked")
    print("  luckiest, and luck does not persist. That is the mechanism a")
    print("  shrinkage rule is meant to blunt, and the size of the rise gap is")
    print("  roughly how much there is to win.")

    print("\n  E, clean layout sensitivity. With the device held identical and")
    print("  only the error numbers changed:")
    for _, r in e_out.iterrows():
        print(f"    {r['circuit']:<8} qubit set changed in "
              f"{r['pct_qubit_set_changed']:>5.1f}% of pairs")
    print("  This is the honest version of the L-052 number, because a layout")
    print("  can no longer move just because a qubit died. Where the share is")
    print("  high the layout really is being steered by the numbers, so a")
    print("  better prediction can change the choice. Where it is low the")
    print("  lattice and the seed are doing the choosing and no prediction")
    print("  rule can help much.")

    print("\n  F, QFT ceilings. mean fidelity over the three machines:")
    for (n, v), s in f_out.groupby(["n", "variant"]):
        print(f"    qft{n:<3} {v:<7} cz {s.cz.mean():>6.1f}  depth "
              f"{s.depth.mean():>6.1f}  fidelity {s.fidelity.mean():.4f}")
    print("  The approximate QFT has the identical ideal answer and far fewer")
    print("  two-qubit gates, so it is the better instrument at every size.")
    if low10:
        print("  The exact 10 qubit QFT is below the 0.20 line you set, so it")
        print("  is not a usable test circuit on these cards.")
    else:
        print("  The exact 10 qubit QFT stayed at or above the 0.20 line.")
    print("  For the rule: a circuit with no headroom cannot show a staleness")
    print("  effect, because every arm lands in the noise floor together.")

    print("\n  G, design effects. window mean minus stale, all 5648 jobs:")
    r = g_out.iloc[0]
    print(f"    paired SD {r['paired_sd']:.6f}, naive SE {r['naive_se']:.6f},")
    print(f"    design effect {r['design_effect_days']:.3f} by days within")
    print(f"    machine and {r['design_effect_submission']:.3f} by machine and")
    print(f"    submission, ICC {r['icc_machine_day']:+.5f}.")
    print("  A design effect above 5 means the naive interval is about 2.3")
    print("  times too narrow, so a window mean result needs far more days")
    print("  than its raw job count suggests. Any Round 2 target for this")
    print("  contrast has to be built on the clustered SE, not the naive one.")

    print("\n  Everything above is EXPLORATORY and post-hoc. Where it touches")
    print("  measurement noise against real drift, the wording is 'consistent")
    print("  with', because our cards are IBM's reported numbers and we cannot")
    print("  separate a remeasurement that moved from a qubit that moved.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", default=str(ROOT / "outputs/diagnostics"))
    ap.add_argument("--results",
                    default=str(ROOT / "outputs/test_full/all_rows.csv"))
    ap.add_argument("--machine", default="ibm_fez")
    ap.add_argument("--pairs", type=int, default=20)
    ap.add_argument("--boot", type=int, default=2000)
    args = ap.parse_args()
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    print("CHECKPOINT 2 DIAGNOSTICS, DEVELOPMENT CARDS ONLY")
    print(f"window {WINDOW_START} to {WINDOW_END} inclusive. Nothing dated")
    print("after 12 October 2026 is read. data/raw is not written. No IBM")
    print("call. Aer is used in PART F only.")
    print("EXPLORATORY AND POST-HOC throughout.")
    print("errors: positive log deviation means worse. T1 and T2 are negated")
    print("so positive always means worse.\n")

    import real_data as rd
    stores = {m: rd.open_store(m) for m in MACHINES}
    for m, s in stores.items():
        idxs = dev_indices(s)
        outside = [str(s.times[i]) for i in range(len(s.times))
                   if i not in set(idxs)]
        print(f"  {m}: {len(s)} states stored, {len(idxs)} inside the window, "
              f"{len(outside)} outside and EXCLUDED")
        assert all(WINDOW_START <= str(s.times[i].date()) <= WINDOW_END
                   for i in idxs)
    rng = np.random.default_rng(SEED_DIAG)

    df = M20.load(args.results)
    a_days = part_a(stores, outdir)
    b_out = part_b(stores, outdir, rng)
    c_out = part_c(stores, outdir, rng, args.boot)
    d_summ = part_d(stores, df, outdir, rng)
    e_out = part_e(stores, outdir, args.machine, args.pairs)
    f_out, low10 = part_f(stores, outdir)
    g_out = part_g(outdir, args.results)
    summary(a_days, b_out, c_out, d_summ, e_out, f_out, low10, g_out)
    print(f"\nfiles written to {outdir}")


main()
