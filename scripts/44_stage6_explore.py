"""Stage 6, Part B: EXPLORATORY, READ ONLY, POST HOC.

Every number in this file is exploratory and was computed AFTER the Round 2
results were known. None of it is confirmatory. None of it changes the rule,
the protocol, any frozen file or any Round 2 result. Nothing is simulated and
no quantum job is submitted. No IBM call is made. No card folder is written.

Wording rule from L-032: "consistent with", never "proved".

PARTS
  J  change intervals: the hours between consecutive changes of each field
     group, per machine, over all 57 days. Is the timing regular in AGE even
     though the clock hour wanders?
  K  winner's curse, wider: for ghz5, ghz10, bv8 and bv10, and for cz, sx,
     readout and T1/T2, do the qubits and couplers the STALE layout chose
     look unusually good against their own trailing median, compared with
     1000 random same size sets, and how much did they rise by the run-time
     card? Development window only.
  M  out of time check: diagnostics PART C (mean reversion) and PART D
     (readout winner's curse) re-run on the FRESH window, 13 to 24 Oct, by
     calling the same functions in scripts/29_diagnostics.py with the window
     moved. Do they hold out of time?
  N  why did the hybrid lose? Round 2 rows only: hybrid minus stale and
     window mean minus stale by delay, by circuit family, by machine, and
     excluding the jobs whose submission to run interval overlaps the fez
     readout episode of 15 Oct. How much of the pooled difference sits in
     jobs where any arm used a dead qubit?

The store is data/clean_r2, which spans 28 Aug to 24 Oct in one chain. Its
development portion was checked row for row against data/clean when it was
built, and Round 1's rows were reproduced from it with every column identical,
so a state index means the same thing in both.

Usage:
  python scripts/44_stage6_explore.py [--parts JKMN] [--boot 2000]
                                      [--sample-per-circuit 0]
"""
import argparse
import os
import sys
import types
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs/stage6_explore"

os.environ["STALENESS_CLEAN_DIR"] = str(ROOT / "data/clean_r2")
os.environ["STALENESS_CACHE_DIR"] = str(ROOT / "data/cache_r2")
sys.path.insert(0, str(ROOT / "engine"))
sys.path.insert(0, str(ROOT / "scripts"))

MACHINES = ["ibm_fez", "ibm_kingston", "ibm_marrakesh"]
GROUPS = ["readout", "sx", "cz", "T1_T2"]
ALL_START, ALL_END = "2026-08-28", "2026-10-24"
DEV_START, DEV_END = "2026-08-28", "2026-10-12"
FRESH_START, FRESH_END = "2026-10-13", "2026-10-24"

K_CIRCUITS = ["ghz5", "ghz10", "bv8", "bv10"]
WINDOW_N_MEDIAN = 8               # "the median of the last 8 distinct states"
N_RANDOM_SETS = 1000
SEED_EXPLORE = 20261025
REGULAR_H, REGULAR_TOL = 24.0, 3.0     # "within 24 +- 3 h"

# The fez readout episode found in Stage 4, 15 Oct 2026. Kept IN the Round 2
# analysis as the protocol required; excluded here only as an exploratory cut.
FEZ_EPISODE = ("ibm_fez", pd.Timestamp("2026-10-15T05:44:28Z"),
               pd.Timestamp("2026-10-15T15:37:18Z"))
FAMILY = {"ghz5": "GHZ", "ghz8": "GHZ", "ghz10": "GHZ",
          "bv8": "BV", "bv10": "BV",
          "qft5": "QFT", "qft8": "QFT", "qft10": "QFT"}
R2_DELAYS = [6, 12, 24, 48]

warnings.filterwarnings("ignore", message="All-NaN slice encountered")
warnings.filterwarnings("ignore", message="Mean of empty slice")
warnings.filterwarnings("ignore", message="Degrees of freedom <= 0")


def say(*a):
    print(*a, flush=True)


def load_module(relpath, name):
    """Import a numbered script for its functions (it calls main() at the end)."""
    path = ROOT / relpath
    src = path.read_text().rsplit("\nmain()", 1)[0]
    mod = types.ModuleType(name)
    mod.__file__ = str(path)
    exec(compile(src, str(path), "exec"), mod.__dict__)
    return mod


# ================================================================ PART J

def group_change_times(store, idxs, grp, pk, M29):
    """The times at which THIS field group's values changed.

    A stored state is a state where ANY of the five fields moved, so a state
    boundary is not a change of every group. A change of this group is a
    state whose values for this group differ from the previous state's, with
    missing compared to missing counting as no change.
    """
    mat, _ = M29.field_matrix(store, idxs, grp, pk)
    out = []
    for t in range(1, len(idxs)):
        if not np.array_equal(mat[t], mat[t - 1], equal_nan=True):
            out.append(store.times[idxs[t]])
    return out


def circular_spread_h(times):
    """How widely the clock hour of these events is spread, in hours.

    The clock hour is an angle, so 23:30 and 00:30 are one hour apart, not 23.
    R is the length of the mean unit vector: R near 1 means the events cluster
    at one hour of the day, R near 0 means they are spread right round the
    clock. The spread is reported as the circular SD, converted to hours.
    """
    if len(times) < 2:
        return float("nan"), float("nan")
    frac = np.array([t.hour + t.minute / 60 + t.second / 3600 for t in times])
    ang = 2 * np.pi * frac / 24.0
    R = np.hypot(np.cos(ang).mean(), np.sin(ang).mean())
    if R <= 1e-12:
        return 0.0, 24.0 / np.sqrt(12)          # as spread as it can be
    sd_rad = np.sqrt(-2.0 * np.log(R))
    return float(R), float(sd_rad * 24.0 / (2 * np.pi))


def busiest_6h_share(times):
    """The share of changes falling in the busiest 6 hour block of the clock.

    A bounded companion to R, because the circular SD is NOT bounded: as the
    changes spread evenly round the clock, R goes to 0 and the circular SD
    grows without limit. This number cannot be misread that way. Changes
    spread evenly round the day give 0.25; changes all at one hour give 1.0.
    """
    if not len(times):
        return float("nan")
    frac = np.array([t.hour + t.minute / 60 + t.second / 3600 for t in times])
    best = 0.0
    for start in np.arange(0, 24, 0.25):
        inside = ((frac - start) % 24.0) < 6.0
        best = max(best, float(inside.mean()))
    return best


def part_j(stores, M29):
    say("\n" + "=" * 74)
    say("PART J: HOW OFTEN EACH FIELD GROUP CHANGES (EXPLORATORY)")
    say("=" * 74)
    say(f"  all {len(pd.date_range(ALL_START, ALL_END))} days, "
        f"{ALL_START} to {ALL_END}")
    say("  interval = hours between one change of that group and the next.")
    say(f"  'in band' = the share of intervals inside "
        f"{REGULAR_H:.0f} +- {REGULAR_TOL:.0f} h, which the task asks for cz")
    say("  and T1/T2. clock SD is how widely the TIME OF DAY of the changes")
    say("  is spread, treating the hour as an angle: a large clock SD with a")
    say("  small interval IQR is the signature of a schedule that is regular")
    say("  in AGE while its clock hour wanders. clock R runs from 0, changes")
    say("  spread right round the clock, to 1, changes all at one hour. The")
    say("  busiest 6 h share is 25% when the clock hour is spread evenly.")
    rows = []
    for m, store in stores.items():
        idxs = [i for i, t in enumerate(store.times)
                if ALL_START <= str(t.date()) <= ALL_END]
        pk = M29.pair_keys(store, idxs)
        say(f"\n  {m}: {len(idxs)} states in the window")
        say(f"    {'group':<7}{'changes':>8}{'median h':>10}{'IQR h':>16}"
            f"{'in band':>9}{'clock R':>9}{'busiest 6h':>12}")
        for grp in GROUPS:
            ts = group_change_times(store, idxs, grp, pk, M29)
            if len(ts) < 3:
                say(f"    {grp:<7}{len(ts):>8}   too few changes to summarise")
                continue
            iv = np.array([(ts[k + 1] - ts[k]).total_seconds() / 3600.0
                           for k in range(len(ts) - 1)])
            q1, med, q3 = np.percentile(iv, [25, 50, 75])
            band = float(np.mean(np.abs(iv - REGULAR_H) <= REGULAR_TOL))
            R, sd_h = circular_spread_h(ts)
            b6 = busiest_6h_share(ts)
            say(f"    {grp:<7}{len(ts):>8}{med:>10.2f}"
                f"{f'{q1:.2f} to {q3:.2f}':>16}{100 * band:>8.1f}%"
                f"{R:>9.3f}{100 * b6:>11.1f}%")
            rows.append(dict(machine=m, group=grp, n_changes=len(ts),
                             median_interval_h=med, iqr_lo_h=q1, iqr_hi_h=q3,
                             iqr_width_h=q3 - q1,
                             share_in_24pm3=band, clock_R=R,
                             clock_sd_h=sd_h, busiest_6h_share=b6))
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "J1_change_intervals.csv", index=False)

    say("\n  the question the task asks: is the timing regular in age even")
    say("  though the clock hour wanders?")
    for grp in GROUPS:
        s = out[out.group == grp]
        if not len(s):
            continue
        say(f"    {grp:<7} median interval "
            f"{s.median_interval_h.mean():.2f} h, mean IQR width "
            f"{s.iqr_width_h.mean():.2f} h, mean clock SD "
            f"{s.clock_sd_h.mean():.2f} h, share within 24 +- 3 h "
            f"{100 * s.share_in_24pm3.mean():.1f}%, mean clock R "
            f"{s.clock_R.mean():.3f}, mean busiest 6 h share "
            f"{100 * s.busiest_6h_share.mean():.1f}%")
    say("\n  read it this way. A schedule regular in AGE shows a tight")
    say("  interval IQR. A schedule regular on the CLOCK shows a clock R near")
    say("  1 and a busiest 6 h share well above 25%. A NOTE ON THE CIRCULAR")
    say("  SD, which is in the CSV but no longer printed: it is not bounded.")
    say("  As the changes spread evenly round the clock, R goes to 0 and the")
    say("  circular SD grows without limit, so it cannot be compared against")
    say("  any fixed ceiling. clock R and the busiest 6 h share can.")
    return out


# ================================================================ PART K

def build_adjacency(store):
    """live-qubit adjacency from the coupler keys of this machine."""
    import re
    adj = {}
    keys = set()
    for i in (0, len(store) - 1):
        keys |= set(store.snapshot(i)["err_2q"])
    for k in keys:
        nums = [int(x) for x in re.findall(r"\d+", str(k))]
        if len(nums) != 2:
            continue
        a, b = nums
        adj.setdefault(a, set()).add(b)
        adj.setdefault(b, set()).add(a)
    return adj, sorted(keys)


def connected_sets(adj, live, k, n_sets, rng):
    """n_sets random CONNECTED qubit sets of size k, drawn from `live`.

    Why connected. A coupler needs both of its qubits to be in the set. An
    unconnected random set of 5 qubits on a heavy hex lattice usually induces
    NO coupler at all, so it cannot serve as a comparison for coupler
    quality. The compiler must choose a connected patch, so the honest
    comparison for the cz group is a random connected patch of the same size.
    Grown by starting at a random live qubit and repeatedly adding a random
    live neighbour of the set.
    """
    liveset = set(int(x) for x in live)
    out = []
    guard = 0
    while len(out) < n_sets and guard < n_sets * 60:
        guard += 1
        start = int(rng.choice(live))
        cur = {start}
        while len(cur) < k:
            frontier = sorted({n for q in cur
                               for n in adj.get(q, ()) if n in liveset} - cur)
            if not frontier:
                break
            cur.add(int(rng.choice(frontier)))
        if len(cur) == k:
            out.append(sorted(cur))
    return np.array(out, dtype=int) if out else np.zeros((0, k), dtype=int)


def induced_cz(used, pk_index):
    """The couplers whose BOTH qubits are in `used`."""
    s = set(int(x) for x in used)
    return [j for (a, b), j in pk_index.items() if a in s and b in s]


def part_k(stores, df, rng, M29, sample_per_circuit=0):
    import re
    import real_data as rd
    say("\n" + "=" * 74)
    say("PART K: WINNER'S CURSE, WIDER (EXPLORATORY)")
    say("=" * 74)
    say(f"  circuits {', '.join(K_CIRCUITS)}; groups "
        f"{', '.join(GROUPS)}; development window only "
        f"({DEV_START} to {DEV_END})")
    say("  Deviation is on the log scale and positive means WORSE, so a")
    say("  NEGATIVE chosen deviation means the chosen set looked BETTER than")
    say(f"  its own median of the last {WINDOW_N_MEDIAN} distinct states.")
    say(f"  pctile is where the chosen set sits inside {N_RANDOM_SETS} random")
    say("  same size sets drawn from the live qubits of the same card. Below")
    say("  50 means the chosen set looked better than a random set.")
    say("  For the cz group the random sets are CONNECTED patches, because an")
    say("  unconnected random set induces no coupler at all.")
    say("  rise = log change from the submission card to the run-time card,")
    say("  positive again meaning it got worse.")
    say("  The random sets and their statistics are cached per (machine,")
    say("  submission state, run state, set size), so every row that shares")
    say("  those four sees the SAME null. That is a speed choice only: the")
    say("  chosen set is still scored row by row against that null.")

    sub = df[(df.arm == "stale") & (df.circuit.isin(K_CIRCUITS))].copy()
    sub = sub[(sub.t_s.dt.strftime("%Y-%m-%d") >= DEV_START)
              & (sub.t_s.dt.strftime("%Y-%m-%d") <= DEV_END)]
    if sample_per_circuit:
        sub = (sub.groupby("circuit", group_keys=False)
               .apply(lambda g: g.sample(min(len(g), sample_per_circuit),
                                         random_state=SEED_EXPLORE)))
        say(f"\n  SUBSAMPLED to {sample_per_circuit} rows per circuit "
            f"(seed {SEED_EXPLORE}) to keep the run affordable")
    say(f"\n  {len(sub)} stale rows over {sub.circuit.nunique()} circuits, "
        f"{sub.info_state.nunique()} distinct submission states")

    adjs, pkidx, pklists = {}, {}, {}
    for m, store in stores.items():
        adj, keys = build_adjacency(store)
        adjs[m] = adj
        pklists[m] = keys
        idx = {}
        for j, k in enumerate(keys):
            nums = [int(x) for x in re.findall(r"\d+", str(k))]
            if len(nums) == 2:
                idx[(nums[0], nums[1])] = j
        pkidx[m] = idx

    dev_cache, set_cache, null_cache, log_cache = {}, {}, {}, {}

    def dev_and_live(m, state_i):
        """Per series log deviation from the trailing median, and live qubits."""
        key = (m, state_i)
        if key not in dev_cache:
            store = stores[m]
            lo = max(0, state_i - WINDOW_N_MEDIAN + 1)
            hist = list(range(lo, state_i + 1))
            out = {}
            for grp in GROUPS:
                mat, _ = M29.field_matrix(store, hist, grp, pklists[m])
                L = M29.to_log(mat, grp)
                out[grp] = L[-1] - np.nanmedian(L, axis=0)
            dead = rd.dead_qubits(store.snapshot(state_i))
            live = np.array([q for q in range(store.n_qubits)
                             if q not in dead])
            dev_cache[key] = (out, live)
        return dev_cache[key]

    def raw_log(m, state_i, grp):
        key = (m, state_i, grp)
        if key not in log_cache:
            mat, _ = M29.field_matrix(stores[m], [state_i], grp, pklists[m])
            v = M29.to_log(mat, grp)[0]
            nq = stores[m].n_qubits
            if grp == "T1_T2":
                v = np.nanmean(np.vstack([v[:nq], v[nq:]]), axis=0)
            log_cache[key] = v
        return log_cache[key]

    def dev_vec(m, state_i, grp):
        d = dev_and_live(m, state_i)[0][grp]
        if grp == "T1_T2":
            nq = stores[m].n_qubits
            d = np.nanmean(np.vstack([d[:nq], d[nq:]]), axis=0)
        return d

    def random_sets(m, state_i, k):
        """Plain and connected random sets of size k, cached."""
        key = (m, state_i, k)
        if key not in set_cache:
            live = dev_and_live(m, state_i)[1]
            if len(live) < k:
                set_cache[key] = (None, None, None)
            else:
                order = rng.random((N_RANDOM_SETS,
                                    len(live))).argsort(axis=1)[:, :k]
                plain = live[order]
                conn = connected_sets(adjs[m], live, k, N_RANDOM_SETS, rng)
                cols = [induced_cz(rs, pkidx[m]) for rs in conn]
                keep = [i for i, c in enumerate(cols) if c]
                set_cache[key] = (plain, [cols[i] for i in keep],
                                  conn[keep] if len(conn) else conn)
        return set_cache[key]

    def null_stats(m, i_state, t_state, k, grp):
        """(deviation array over random sets, mean random rise), cached."""
        key = (m, i_state, t_state, k, grp)
        if key in null_cache:
            return null_cache[key]
        plain, conn_cols, _ = random_sets(m, i_state, k)
        if plain is None:
            null_cache[key] = (None, None)
            return null_cache[key]
        d = dev_vec(m, i_state, grp)
        Li, Lt = raw_log(m, i_state, grp), raw_log(m, t_state, grp)
        if grp == "cz":
            if len(conn_cols) < 50:
                null_cache[key] = (None, None)
                return null_cache[key]
            arr = np.array([np.nanmean(d[c]) for c in conn_cols], float)
            rise = float(np.nanmean([np.nanmean(Lt[c] - Li[c])
                                     for c in conn_cols]))
        else:
            arr = np.nanmean(d[plain], axis=1)
            rise = float(np.nanmean(np.nanmean(Lt[plain] - Li[plain], axis=1)))
        null_cache[key] = (arr, rise)
        return null_cache[key]

    rows = []
    for n_done, (_, r) in enumerate(sub.iterrows(), 1):
        m = r.machine
        used = [int(x) for x in str(r.qubits_used).split()]
        k = len(used)
        i_state, t_state = int(r.info_state), int(r.truth_state)
        if k == 0:
            continue
        for grp in GROUPS:
            arr, rand_rise = null_stats(m, i_state, t_state, k, grp)
            if arr is None:
                continue
            d = dev_vec(m, i_state, grp)
            Li, Lt = raw_log(m, i_state, grp), raw_log(m, t_state, grp)
            if grp == "cz":
                cols = induced_cz(used, pkidx[m])
                if not cols:
                    continue
                chosen = float(np.nanmean(d[cols]))
                rise_ch = float(np.nanmean(Lt[cols] - Li[cols]))
                n_series, null = len(cols), f"connected, {len(arr)} usable"
            else:
                chosen = float(np.nanmean(d[used]))
                rise_ch = float(np.nanmean(Lt[used] - Li[used]))
                n_series, null = k, "plain"
            if not np.isfinite(chosen):
                continue
            rows.append(dict(
                machine=m, circuit=r.circuit, delay_h=int(r.delay_h),
                day=str(r.day), group=grp, n_series=n_series, null=null,
                chosen_dev=chosen, random_dev_mean=float(np.nanmean(arr)),
                percentile_of_chosen=float((arr < chosen).mean() * 100),
                chosen_rise=rise_ch, random_rise=rand_rise))
        if n_done % 1000 == 0:
            say(f"    ...{n_done}/{len(sub)} rows, {len(null_cache)} cached "
                f"nulls")

    out = pd.DataFrame(rows)
    out.to_csv(OUT / "K1_winners_curse_wide_rows.csv", index=False)
    say(f"\n  {len(out)} row-group results from {len(null_cache)} cached nulls")

    say(f"\n  pooled over the four circuits")
    say(f"  {'group':<7}{'n':>7}{'chosen dev':>12}{'random dev':>12}"
        f"{'pctile':>9}{'below 5th':>11}{'chosen rise':>13}"
        f"{'random rise':>13}{'rise gap':>10}")
    summ = []
    for grp in GROUPS:
        s = out[out.group == grp]
        if not len(s):
            continue
        gap = s.chosen_rise.mean() - s.random_rise.mean()
        say(f"  {grp:<7}{len(s):>7}{s.chosen_dev.mean():>+12.4f}"
            f"{s.random_dev_mean.mean():>+12.4f}"
            f"{s.percentile_of_chosen.mean():>8.1f}%"
            f"{100 * (s.percentile_of_chosen < 5).mean():>10.1f}%"
            f"{s.chosen_rise.mean():>+13.4f}{s.random_rise.mean():>+13.4f}"
            f"{gap:>+10.4f}")
        summ.append(dict(group=grp, n=len(s), chosen_dev=s.chosen_dev.mean(),
                         random_dev=s.random_dev_mean.mean(),
                         mean_percentile=s.percentile_of_chosen.mean(),
                         share_below_5th=100 * (s.percentile_of_chosen < 5).mean(),
                         chosen_rise=s.chosen_rise.mean(),
                         random_rise=s.random_rise.mean(), rise_gap=gap))
    pd.DataFrame(summ).to_csv(OUT / "K2_winners_curse_wide_summary.csv",
                              index=False)

    say(f"\n  by circuit and group: mean percentile of the chosen set")
    say("  " + f"{'circuit':<9}" + "".join(f"{g:>12}" for g in GROUPS))
    for c in K_CIRCUITS:
        line = f"  {c:<9}"
        for g in GROUPS:
            s = out[(out.circuit == c) & (out.group == g)]
            line += (f"{s.percentile_of_chosen.mean():>11.1f}%" if len(s)
                     else f"{'n/a':>12}")
        say(line)

    say(f"\n  by circuit and group: rise gap (chosen minus random), "
        "positive means the chosen set got worse faster")
    say("  " + f"{'circuit':<9}" + "".join(f"{g:>12}" for g in GROUPS))
    for c in K_CIRCUITS:
        line = f"  {c:<9}"
        for g in GROUPS:
            s = out[(out.circuit == c) & (out.group == g)]
            line += (f"{s.chosen_rise.mean() - s.random_rise.mean():>+12.4f}"
                     if len(s) else f"{'n/a':>12}")
        say(line)

    say(f"\n  rise gap by delay and group, the shape the hybrid was built for")
    say("  " + f"{'D (h)':<7}" + "".join(f"{g:>12}" for g in GROUPS))
    for D in sorted(out.delay_h.unique()):
        line = f"  {D:<7}"
        for g in GROUPS:
            s = out[(out.delay_h == D) & (out.group == g)]
            line += (f"{s.chosen_rise.mean() - s.random_rise.mean():>+12.4f}"
                     if len(s) else f"{'n/a':>12}")
        say(line)
    out.groupby(["group", "delay_h"]).agg(
        n=("chosen_rise", "size"),
        mean_percentile=("percentile_of_chosen", "mean"),
        chosen_rise=("chosen_rise", "mean"),
        random_rise=("random_rise", "mean")).to_csv(
        OUT / "K3_winners_curse_wide_by_delay.csv")
    return out


# ================================================================ PART M

def part_m(M29, boot):
    say("\n" + "=" * 74)
    say("PART M: DO PARTS C AND D HOLD OUT OF TIME? (EXPLORATORY)")
    say("=" * 74)
    say(f"  The SAME functions in scripts/29_diagnostics.py are called with")
    say(f"  the window moved to the FRESH window, {FRESH_START} to "
        f"{FRESH_END}.")
    say("  The code is not reimplemented, so a difference cannot come from")
    say("  writing the calculation a second way.")
    say("  The development numbers they are compared with are the ones in")
    say("  outputs/diagnostics/C1_mean_reversion.csv and D2_*.csv.")
    say("  NOTE: PART D's own printed header says 'development window'. That")
    say("  text is its code, unchanged. The window really used here is the")
    say("  fresh one, set just below.")

    outdir = OUT / "M_fresh"
    outdir.mkdir(parents=True, exist_ok=True)
    M29.WINDOW_START, M29.WINDOW_END = FRESH_START, FRESH_END
    import real_data as rd
    stores = {m: rd.open_store(m) for m in MACHINES}
    for m, s in stores.items():
        idxs = M29.dev_indices(s)
        say(f"  {m}: {len(idxs)} states inside the fresh window "
            f"of {len(s)} stored")
    rng = np.random.default_rng(SEED_EXPLORE)

    c_fresh = M29.part_c(stores, outdir, rng, boot)
    df2 = M29.M20.load(ROOT / "outputs/round2_run/all_rows.csv")
    d_fresh = M29.part_d(stores, df2, outdir, rng)

    # --- side by side with the development numbers ---
    say("\n" + "=" * 74)
    say("M: OUT OF TIME COMPARISON")
    say("=" * 74)
    cdev_path = ROOT / "outputs/diagnostics/C1_mean_reversion.csv"
    if cdev_path.exists():
        cdev = pd.read_csv(cdev_path)
        say("\n  PART C, mean reversion slope. A slope near -1 means a")
        say("  deviation is undone by the next state.")
        say(f"  {'machine':<16}{'group':<8}{'dev slope':>11}"
            f"{'dev 95% interval':>24}{'fresh slope':>13}"
            f"{'fresh 95% interval':>24}{'overlap':>9}")
        comp = []
        for _, r in c_fresh.iterrows():
            d = cdev[(cdev.machine == r.machine) & (cdev.group == r.group)]
            if not len(d):
                continue
            d = d.iloc[0]
            overlap = (r.lo <= d.hi) and (d.lo <= r.hi)
            say(f"  {r.machine:<16}{r.group:<8}{d.slope:>+11.4f}"
                f"{f'[{d.lo:+.4f}, {d.hi:+.4f}]':>24}{r.slope:>+13.4f}"
                f"{f'[{r.lo:+.4f}, {r.hi:+.4f}]':>24}"
                f"{'yes' if overlap else 'NO':>9}")
            comp.append(dict(machine=r.machine, group=r.group,
                             dev_slope=d.slope, dev_lo=d.lo, dev_hi=d.hi,
                             fresh_slope=r.slope, fresh_lo=r.lo,
                             fresh_hi=r.hi, intervals_overlap=bool(overlap)))
        cc = pd.DataFrame(comp)
        cc.to_csv(outdir / "M1_part_c_dev_vs_fresh.csv", index=False)
        if len(cc):
            say(f"\n    intervals overlap in {int(cc.intervals_overlap.sum())}"
                f" of {len(cc)} machine-group cells")
            say(f"    mean slope: development {cc.dev_slope.mean():+.4f}, "
                f"fresh {cc.fresh_slope.mean():+.4f}")
            say("    reading: an overlap is consistent with the same")
            say("    behaviour out of time. It does not prove it.")
    else:
        say(f"\n  {cdev_path} is missing, so PART C cannot be compared")

    ddev_path = ROOT / "outputs/diagnostics/D2_winners_curse_summary.csv"
    if ddev_path.exists() and d_fresh is not None and len(d_fresh):
        ddev = pd.read_csv(ddev_path)
        say("\n  PART D, winner's curse on the stale ghz8 layout.")
        say(f"  {'group':<8}{'dev pctile':>12}{'fresh pctile':>14}"
            f"{'dev rise gap':>14}{'fresh rise gap':>16}{'same sign':>11}")
        comp = []
        for _, r in d_fresh.iterrows():
            d = ddev[ddev.group == r.group]
            if not len(d):
                continue
            d = d.iloc[0]
            same = np.sign(d.rise_gap) == np.sign(r.rise_gap)
            say(f"  {r.group:<8}{d.mean_percentile:>11.1f}%"
                f"{r.mean_percentile:>13.1f}%{d.rise_gap:>+14.4f}"
                f"{r.rise_gap:>+16.4f}{'yes' if same else 'NO':>11}")
            comp.append(dict(group=r.group, dev_percentile=d.mean_percentile,
                             fresh_percentile=r.mean_percentile,
                             dev_rise_gap=d.rise_gap,
                             fresh_rise_gap=r.rise_gap,
                             same_sign=bool(same)))
        pd.DataFrame(comp).to_csv(outdir / "M2_part_d_dev_vs_fresh.csv",
                                  index=False)
    else:
        say("\n  PART D could not be compared (a file or a result is missing)")
    return c_fresh, d_fresh


# ================================================================ PART N

def overlaps_episode(machine, t_s, t_r):
    m, lo, hi = FEZ_EPISODE
    return machine == m and (t_s < hi) and (t_r > lo)


def part_n(M20, rng):
    say("\n" + "=" * 74)
    say("PART N: WHY DID THE HYBRID LOSE? (EXPLORATORY)")
    say("=" * 74)
    say("  Round 2 rows only, outputs/round2_run/all_rows.csv. Nothing is")
    say("  re-simulated and no row is changed. gain = F_arm minus F_stale,")
    say("  positive meaning the arm is better. Intervals are Round 1's block")
    say(f"  bootstrap over whole calendar days, seed {M20.SEED_BOOT}, "
        f"{M20.N_BOOT} resamples.")
    df = M20.load(ROOT / "outputs/round2_run/all_rows.csv")
    w = M20.widen(df)
    w["family"] = w.circuit.map(FAMILY)
    w["gain_hybrid"] = w["hybrid"] - w["stale"]
    w["gain_window"] = w["window_mean"] - w["stale"]

    # which jobs had ANY arm land on a qubit that was dead at run time
    dead_any = (df.assign(has=df.dead_qubits_used.notna())
                .groupby(["machine", "draw_order", "delay_h", "circuit"])
                .has.any().rename("dead_any").reset_index())
    w = w.merge(dead_any, on=["machine", "draw_order", "delay_h", "circuit"],
                how="left")
    w["dead_any"] = w.dead_any.fillna(False)
    # the episode test needs the real submission and run times, from df
    times = (df.groupby(["machine", "draw_order", "delay_h", "circuit"])
             [["t_s", "t_r"]].first().reset_index())
    w = w.merge(times, on=["machine", "draw_order", "delay_h", "circuit"],
                how="left")
    w["in_episode"] = [overlaps_episode(m, ts, tr)
                       for m, ts, tr in zip(w.machine, w.t_s, w.t_r)]

    pool = w[w.delay_h.isin(R2_DELAYS)].copy()
    say(f"\n  {len(w)} jobs, {len(pool)} in the pooled "
        f"D = {', '.join(str(d) for d in R2_DELAYS)} h set")

    def line(label, frame, col):
        if not len(frame):
            say(f"  {label:<46}{'no jobs':>42}")
            return None
        obs, lo, hi, nd = M20.block_boot(frame, col, rng)
        say(f"  {label:<46}{len(frame):>7}{nd:>6}{obs:>12.6f}"
            f"{lo:>12.6f}{hi:>12.6f}")
        return dict(what=label, n=len(frame), days=nd, mean=obs, lo=lo, hi=hi)

    rows = []
    hdr = f"  {'what':<46}{'n jobs':>7}{'days':>6}{'mean':>12}{'95% low':>12}{'95% high':>12}"

    say("\n  by delay")
    say(hdr)
    for D in sorted(w.delay_h.unique()):
        f = w[w.delay_h == D]
        rows.append(line(f"hybrid minus stale, D = {D} h", f, "gain_hybrid"))
        rows.append(line(f"window_mean minus stale, D = {D} h", f,
                         "gain_window"))

    say("\n  by circuit family, pooled over D = 6 to 48 h")
    say(hdr)
    for fam in ["GHZ", "BV", "QFT"]:
        f = pool[pool.family == fam]
        rows.append(line(f"hybrid minus stale, {fam}", f, "gain_hybrid"))
        rows.append(line(f"window_mean minus stale, {fam}", f, "gain_window"))

    say("\n  by machine, pooled over D = 6 to 48 h")
    say(hdr)
    for m in sorted(pool.machine.unique()):
        f = pool[pool.machine == m]
        rows.append(line(f"hybrid minus stale, {m}", f, "gain_hybrid"))
        rows.append(line(f"window_mean minus stale, {m}", f, "gain_window"))

    say(f"\n  excluding the fez readout episode of "
        f"{FEZ_EPISODE[1].strftime('%d %b %H:%M')} to "
        f"{FEZ_EPISODE[2].strftime('%H:%M')} UTC")
    say("  (those jobs were KEPT IN the Round 2 analysis as the protocol")
    say("   required. This is an exploratory cut, not a correction.)")
    say(hdr)
    n_ep = int(pool.in_episode.sum())
    say(f"    jobs whose submission to run interval overlaps it: {n_ep}")
    for label, f in [("all jobs", pool),
                     ("excluding the episode", pool[~pool.in_episode]),
                     ("only the episode", pool[pool.in_episode])]:
        rows.append(line(f"hybrid minus stale, {label}", f, "gain_hybrid"))
        rows.append(line(f"window_mean minus stale, {label}", f,
                         "gain_window"))

    say("\n  jobs where ANY arm used a qubit that was dead at run time")
    say(hdr)
    for label, f in [("all jobs", pool),
                     ("a dead qubit was used", pool[pool.dead_any]),
                     ("no dead qubit was used", pool[~pool.dead_any])]:
        rows.append(line(f"hybrid minus stale, {label}", f, "gain_hybrid"))
        rows.append(line(f"window_mean minus stale, {label}", f,
                         "gain_window"))

    say("\n  how much of the POOLED difference sits in the dead-qubit jobs")
    say(f"  {'comparison':<28}{'share of jobs':>15}{'share of the total':>20}")
    shares = []
    for col, name in [("gain_hybrid", "hybrid minus stale"),
                      ("gain_window", "window_mean minus stale")]:
        tot = pool[col].sum()
        dead_sum = pool.loc[pool.dead_any, col].sum()
        share_jobs = pool.dead_any.mean()
        share_tot = dead_sum / tot if tot != 0 else float("nan")
        say(f"  {name:<28}{100 * share_jobs:>14.1f}%"
            f"{100 * share_tot:>19.1f}%")
        shares.append(dict(comparison=name, n_jobs=len(pool),
                           n_dead_jobs=int(pool.dead_any.sum()),
                           share_of_jobs=share_jobs, total_sum=tot,
                           dead_sum=dead_sum, share_of_total=share_tot))
        say(f"    {pool.dead_any.sum()} of {len(pool)} jobs carry "
            f"{100 * share_tot:.1f} percent of the summed difference "
            f"({dead_sum:+.4f} of {tot:+.4f})")
    pd.DataFrame(shares).to_csv(OUT / "N2_dead_qubit_share.csv", index=False)
    pd.DataFrame([r for r in rows if r]).to_csv(
        OUT / "N1_hybrid_vs_window.csv", index=False)
    return w


# ================================================================== main

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--parts", default="JKMN")
    ap.add_argument("--boot", type=int, default=2000)
    ap.add_argument("--sample-per-circuit", type=int, default=0)
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)

    say("=" * 74)
    say("STAGE 6 PART B: EXPLORATORY, READ ONLY, POST HOC")
    say("=" * 74)
    say("  Every number below is EXPLORATORY and POST HOC. None of it is")
    say("  confirmatory. None of it changes the rule, the protocol, any")
    say("  frozen file or any Round 2 result. Nothing is simulated, no")
    say("  quantum job is submitted and no IBM call is made.")
    say(f"  store: data/clean_r2, {ALL_START} to {ALL_END}")

    M29 = load_module("scripts/29_diagnostics.py", "diag29")
    M20 = M29.M20
    import real_data as rd
    stores = {m: rd.open_store(m) for m in MACHINES}
    for m, s in stores.items():
        say(f"  {m}: {len(s)} states, {s.times[0].date()} to "
            f"{s.times[-1].date()}")
    rng = np.random.default_rng(SEED_EXPLORE)

    if "J" in args.parts:
        part_j(stores, M29)
    if "K" in args.parts:
        df1 = M20.load(ROOT / "outputs/test_full/all_rows.csv")
        part_k(stores, df1, rng, M29, args.sample_per_circuit)
    if "N" in args.parts:
        part_n(M20, np.random.default_rng(SEED_EXPLORE))
    if "M" in args.parts:
        # LAST, because it moves 29's window globals
        part_m(M29, args.boot)

    say(f"\n  files written to {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
