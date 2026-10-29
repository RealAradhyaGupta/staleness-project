"""Round 2, Stage 1: fit the hybrid rule on DEVELOPMENT cards only.

Development means cards from 28 Aug 2026 to 12 Oct 2026. Nothing after
12 Oct is read. No transpiling and no simulation happen here, so nothing in
this file can touch a fidelity number.

Why the whole Round 1 window counts as development now. In Round 1 the window
was split into training days (28 Aug to 20 Sep) and test days (21 Sep to
12 Oct), and PROTOCOL.md section 10 forbids tuning on the test days. Round 1
is finished and reported. Round 2's test set is a NEW window, 13 to 24 Oct,
which does not exist on this disk yet and was only probed for existence. So
for Round 2 the entire 28 Aug to 12 Oct window is development data. This is a
deliberate decision and it is recorded in protocol_round2.md and in the log.

Sign conventions, as in every file here:
  regret = ceiling minus strategy (positive means the strategy is worse)
  gain   = F_strategy minus F_stale (positive means the strategy is better)

Parts:
  A  readout weights w(D), with N chosen once for all delays
  B  the same test for sx, cz and T1/T2, with a clustered standard error
  C  the dead qubit guard: dead in any of the last M distinct states
  D  window mean minus stale on the existing Round 1 rows

Outputs go to outputs/round2/. Nothing in data/raw is written.
"""
import json
import sys
import types
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "engine"))

import engine_config as cfg          # noqa: E402
import jobs as jobs_mod              # noqa: E402
import real_data as rd               # noqa: E402
import strategies as strat           # noqa: E402

OUT = ROOT / "outputs" / "round2"
MACHINES = ["ibm_fez", "ibm_kingston", "ibm_marrakesh"]
DELAYS = list(cfg.DELAYS_H)
N_GRID = [3, 5, 8, 12]
W_GRID = np.round(np.arange(0.0, 1.0 + 1e-9, 0.05), 2)
N_BLOCKS = 5
PURGE_H = 48
MAX_N = max(N_GRID)
GUARD_M = [1, 2, 4, 8]
SEED_FIT = 20261024
N_BOOT_W = 400

# field group -> the snapshot fields pooled into it
GROUP_FIELDS = {
    "readout": ["err_ro"],
    "sx": ["err_1q"],
    "cz": ["err_2q"],
    "times": ["t1", "t2"],
}
GROUP_ORDER = ["readout", "sx", "cz", "times"]

# These two are expected and are explained in strategies.py: a qubit missing a
# field in every one of the last N distinct values gives an all-NaN column.
# Every such value is dropped below and the dropped count is printed, so this
# hides no failure.
warnings.filterwarnings("ignore", r"(Mean|All-NaN|Degrees of freedom).*",
                        RuntimeWarning)


def say(*a):
    print(*a, flush=True)


def head(title):
    say()
    say("=" * 72)
    say(title)
    say("=" * 72)


# --------------------------------------------------------------- the points

def field_vector(snap, field):
    """One field as a flat float array. cz is ordered by sorted pair key."""
    if field == "err_2q":
        keys = sorted(snap["err_2q"])
        return np.array([snap["err_2q"][k] for k in keys], dtype=float)
    return np.asarray(snap[field], dtype=float)


def safe_log(v):
    return np.log(np.clip(v, 1e-12, None))


def collect_points():
    """Every (machine, submission, delay) point in the development window.

    A point is kept only when the engine's own validity rule in
    engine/jobs.py would keep it: at least 5 states of history, and a run time
    that is not past the last state on disk. That way the fit is done on the
    same points the engine will run on.
    """
    all_subs = jobs_mod.all_submission_times()
    rows = []
    hist_cache = {}
    for m in MACHINES:
        store = rd.open_store(m)
        last_t = store.times[-1]
        subs = [s for s in all_subs if s[0] == m]
        for _, t_s, order in subs:
            info = store.index_at_or_before(t_s)
            if info < 4:                       # min_history = 5 states
                continue
            key = (m, info)
            if key not in hist_cache:
                h = {}
                for field in ("t1", "t2", "err_1q", "err_ro", "err_2q"):
                    seq = strat.distinct_history(store, info, field, MAX_N)
                    h[field] = (np.array([safe_log(v) for _, v in seq])
                                if seq else np.zeros((0, 0)))
                hist_cache[key] = h
            hist = hist_cache[key]
            for D in DELAYS:
                t_r = t_s + pd.Timedelta(hours=D)
                if t_r > last_t:
                    continue
                truth = store.index_at_or_before(t_r)
                if truth < 0:
                    continue
                rows.append({"machine": m, "draw_order": order, "t_s": t_s,
                             "t_r": t_r, "delay_h": D, "info": info,
                             "truth": truth, "day": t_s.date().isoformat()})
    say(f"  points kept: {len(rows)} over {len({(r['machine'], r['draw_order']) for r in rows})} "
        f"submissions and {len({r['day'] for r in rows})} calendar days")
    return rows, hist_cache


def sum_stats(rows, hist_cache, group):
    """Per point, the three sums that make MSE(w) a quadratic in w.

    pred = (1-w) * newest + w * median_N, so the residual is a + w * b with
      a = newest - target
      b = median_N - newest
    and MSE(w) = (S0 + 2 w S1 + w^2 S2) / n with
      S0 = sum a^2, S1 = sum a*b, S2 = sum b^2.
    Summing these over points is exact, so one pass serves every w and every
    bootstrap resample.
    """
    stores = {m: rd.open_store(m) for m in MACHINES}
    out = {N: [] for N in N_GRID}
    n_dropped = 0
    n_used = 0
    for r in rows:
        hist = hist_cache[(r["machine"], r["info"])]
        tsnap = stores[r["machine"]].snapshot(r["truth"])
        for field in GROUP_FIELDS[group]:
            logs = hist[field]
            if logs.ndim != 2 or logs.shape[0] == 0:
                continue
            target = safe_log(field_vector(tsnap, field))
            newest = logs[0]
            if target.shape != newest.shape:
                n_dropped += int(max(target.size, newest.size))
                continue
            for N in N_GRID:
                med = np.nanmedian(logs[:N], axis=0)
                a = newest - target
                b = med - newest
                ok = np.isfinite(a) & np.isfinite(b)
                if not ok.any():
                    continue
                a, b = a[ok], b[ok]
                out[N].append({
                    "machine": r["machine"], "day": r["day"],
                    "delay_h": r["delay_h"], "t_s": r["t_s"], "t_r": r["t_r"],
                    "n": int(ok.sum()),
                    "S0": float(np.dot(a, a)), "S1": float(np.dot(a, b)),
                    "S2": float(np.dot(b, b)),
                })
                if N == N_GRID[0]:
                    n_used += int(ok.sum())
    say(f"  {group}: {n_used} usable (point, qubit) values at N={N_GRID[0]}, "
        f"{n_dropped} dropped for a changed field shape")
    return {N: pd.DataFrame(v) for N, v in out.items()}


# ------------------------------------------------------------ cv machinery

def blocks_of(days):
    """Five chronological blocks of calendar days, as equal as possible."""
    days = sorted(days)
    cuts = np.array_split(np.arange(len(days)), N_BLOCKS)
    return [[days[i] for i in c] for c in cuts if len(c)]


def mse_curve(frame):
    """MSE at every w on the grid, from the pooled sums."""
    n = frame["n"].sum()
    if n == 0:
        return np.full(len(W_GRID), np.nan), 0
    S0, S1, S2 = frame.S0.sum(), frame.S1.sum(), frame.S2.sum()
    return (S0 + 2 * W_GRID * S1 + W_GRID ** 2 * S2) / n, int(n)


def cv_curves(frame, days):
    """Pooled training and pooled held-out MSE curves over the 5 blocks.

    The purge: a training point is dropped when its run-time card could sit
    inside, or within 48 hours of, the test block. Concretely it is dropped if
    its run time is at or after (test block start minus 48 h) and its
    submission time is at or before (test block end plus 48 h).
    """
    tr_num = np.zeros(len(W_GRID))
    te_num = np.zeros(len(W_GRID))
    tr_n = te_n = 0
    dropped = 0
    for blk in blocks_of(days):
        lo = pd.Timestamp(blk[0], tz="UTC")
        hi = pd.Timestamp(blk[-1], tz="UTC") + pd.Timedelta(days=1)
        test = frame[frame.day.isin(blk)]
        rest = frame[~frame.day.isin(blk)]
        keep = ~((rest.t_r >= lo - pd.Timedelta(hours=PURGE_H)) &
                 (rest.t_s <= hi + pd.Timedelta(hours=PURGE_H)))
        dropped += int(len(rest) - keep.sum())
        train = rest[keep]
        c, n = mse_curve(train)
        if n:
            tr_num += c * n
            tr_n += n
        c, n = mse_curve(test)
        if n:
            te_num += c * n
            te_n += n
    tr = tr_num / tr_n if tr_n else np.full(len(W_GRID), np.nan)
    te = te_num / te_n if te_n else np.full(len(W_GRID), np.nan)
    return tr, te, tr_n, te_n, dropped


def isotonic(values, weights):
    """Pool adjacent violators: the closest non-decreasing sequence."""
    vals = [float(v) for v in values]
    wts = [float(w) for w in weights]
    blocks = [[v, w] for v, w in zip(vals, wts)]
    i = 0
    while i < len(blocks) - 1:
        if blocks[i][0] > blocks[i + 1][0] + 1e-12:
            v1, w1 = blocks[i]
            v2, w2 = blocks[i + 1]
            merged = [(v1 * w1 + v2 * w2) / (w1 + w2), w1 + w2]
            blocks[i:i + 2] = [merged]
            i = max(i - 1, 0)
        else:
            i += 1
    out = []
    k = 0
    for v, w in blocks:
        # how many originals went into this block
        used = 0.0
        size = 0
        while k + size < len(vals) and used < w - 1e-9:
            used += wts[k + size]
            size += 1
        out.extend([v] * size)
        k += size
    return out


def snap_to_grid(v):
    return float(W_GRID[int(np.argmin(np.abs(W_GRID - v)))])


# ------------------------------------------------------------------- part A/B

def fit_group(group, stats, days):
    """Choose N once, then w for every delay, then make w(D) non-decreasing."""
    rows_n = []
    for N in N_GRID:
        frame = stats[N]
        per_d = []
        for D in DELAYS:
            sub = frame[frame.delay_h == D]
            tr, te, tr_n, te_n, drop = cv_curves(sub, days)
            j = int(np.nanargmin(tr))
            per_d.append({"N": N, "delay_h": D, "train_best_w": float(W_GRID[j]),
                          "train_mse": float(tr[j]),
                          "train_mse_at_w0": float(tr[0]),
                          "test_mse_at_train_w": float(te[j]),
                          "n_train": tr_n, "n_test": te_n, "purged": drop})
        rows_n.extend(per_d)
    tab_n = pd.DataFrame(rows_n)
    pooled = tab_n.groupby("N").train_mse.mean().sort_values()
    best_N = int(pooled.index[0])

    say(f"\n  [{group}] choosing N by pooled training MSE averaged over the "
        f"six delays:")
    for N, v in pooled.items():
        mark = "  <-- chosen" if N == best_N else ""
        say(f"    N = {N:>2}   pooled training MSE {v:.6f}{mark}")

    frame = stats[best_N]
    rows_w = []
    for D in DELAYS:
        sub = frame[frame.delay_h == D]
        tr, te, tr_n, te_n, drop = cv_curves(sub, days)
        jt = int(np.nanargmin(te))
        rows_w.append({"group": group, "N": best_N, "delay_h": D,
                       "w_heldout": float(W_GRID[jt]),
                       "heldout_mse": float(te[jt]),
                       "heldout_mse_at_w0": float(te[0]),
                       "heldout_gain_vs_w0": float(te[0] - te[jt]),
                       "w_train": float(W_GRID[int(np.nanargmin(tr))]),
                       "n_train": tr_n, "n_test": te_n, "purged": drop})
    tab_w = pd.DataFrame(rows_w)

    raw = tab_w.w_heldout.tolist()
    iso = isotonic(raw, tab_w.n_test.tolist())
    tab_w["w_isotonic"] = iso
    tab_w["w_final"] = [snap_to_grid(v) for v in iso]

    say(f"  [{group}] w by delay at N = {best_N}, chosen on the held-out blocks:")
    say(f"    {'D (h)':>6}{'w raw':>9}{'w isotonic':>12}{'w final':>9}"
        f"{'MSE at w':>12}{'MSE at w=0':>12}{'drop in MSE':>13}")
    for _, r in tab_w.iterrows():
        say(f"    {r.delay_h:>6}{r.w_heldout:>9.2f}{r.w_isotonic:>12.4f}"
            f"{r.w_final:>9.2f}{r.heldout_mse:>12.6f}"
            f"{r.heldout_mse_at_w0:>12.6f}{r.heldout_gain_vs_w0:>13.6f}")
    return best_N, tab_w, tab_n


def clustered_se_of_w(group, frame, days, rng):
    """Standard error of the best w, clustered on calendar days.

    Resample calendar days with replacement, refit the best w on the resample,
    and take the standard deviation of those best w values. The grid is coarse
    (steps of 0.05) so this standard error is coarse too; it is used only for
    the "clearly above zero" test in Stage 1b.
    """
    days = sorted(days)
    by_day = {d: g for d, g in frame.groupby("day")}
    out = []
    for _ in range(N_BOOT_W):
        pick = rng.choice(days, size=len(days), replace=True)
        parts = [by_day[d] for d in pick if d in by_day]
        if not parts:
            continue
        res = pd.concat(parts, ignore_index=True)
        c, n = mse_curve(res)
        if n:
            out.append(float(W_GRID[int(np.nanargmin(c))]))
    if not out:
        return np.nan, np.nan, np.nan
    arr = np.array(out)
    return float(arr.mean()), float(arr.std(ddof=1)), float(np.median(arr))


# --------------------------------------------------------------- part C guard

def guard_metrics(rows):
    stores = {m: rd.open_store(m) for m in MACHINES}
    perm = {}
    for m in MACHINES:
        st = stores[m]
        p = None
        for i in range(len(st)):
            d = rd.dead_qubits(st.snapshot(i))
            p = set(d) if p is None else (p & d)
        perm[m] = p or set()
        say(f"  permanent defects over the whole development window, {m}: "
            f"{len(perm[m])} qubits {sorted(perm[m])}")

    dead_cache = {}

    def dead_at(m, i):
        key = (m, i)
        if key not in dead_cache:
            dead_cache[key] = rd.dead_qubits(stores[m].snapshot(i))
        return dead_cache[key]

    recs = []
    for r in rows:
        m, info, truth = r["machine"], r["info"], r["truth"]
        truth_dead = dead_at(m, truth) - perm[m]
        for M in GUARD_M:
            pred = set()
            for i in range(info, max(info - M, -1), -1):
                pred |= dead_at(m, i)
            pred -= perm[m]
            tp = len(pred & truth_dead)
            fp = len(pred - truth_dead)
            fn = len(truth_dead - pred)
            recs.append({"machine": m, "delay_h": r["delay_h"], "M": M,
                         "tp": tp, "fp": fp, "fn": fn,
                         "n_truth_dead": len(truth_dead),
                         "n_pred_dead": len(pred)})
    df = pd.DataFrame(recs)

    def agg(g):
        tp, fp, fn = g.tp.sum(), g.fp.sum(), g.fn.sum()
        prec = tp / (tp + fp) if tp + fp else np.nan
        rec = tp / (tp + fn) if tp + fn else np.nan
        f1 = (2 * prec * rec / (prec + rec)
              if prec and rec and np.isfinite(prec) and np.isfinite(rec) and prec + rec > 0
              else 0.0)
        return pd.Series({"tp": tp, "fp": fp, "fn": fn,
                          "precision": prec, "recall": rec, "f1": f1,
                          "healthy_removed_per_card": g.fp.mean(),
                          "truth_dead_per_card": g.n_truth_dead.mean(),
                          "pred_dead_per_card": g.n_pred_dead.mean(),
                          "n_points": len(g)})

    by_md = df.groupby(["M", "delay_h"]).apply(agg, include_groups=False).reset_index()
    by_m = df.groupby("M").apply(agg, include_groups=False).reset_index()
    return df, by_md, by_m, perm


# ---------------------------------------------------------- part D round 1

def load_script20():
    path = ROOT / "scripts/20_analyse_results.py"
    src = path.read_text().rsplit("\nmain()", 1)[0]
    mod = types.ModuleType("analyse20")
    mod.__file__ = str(path)
    sys.modules["analyse20"] = mod
    exec(compile(src, str(path), "exec"), mod.__dict__)
    return mod


def part_d():
    M20 = load_script20()
    df = M20.load(ROOT / "outputs/test_full/all_rows.csv")
    w = M20.widen(df)
    stale_dead = (df[df.arm == "stale"]
                  .assign(used=lambda d: d.dead_qubits_used.fillna("").astype(str).str.strip())
                  .set_index(["machine", "draw_order", "delay_h", "circuit"])
                  ["used"])
    idx = pd.MultiIndex.from_frame(
        w[["machine", "draw_order", "delay_h", "circuit"]])
    w = w.copy()
    w["stale_used_dead"] = stale_dead.reindex(idx).fillna("").str.len().to_numpy() > 0
    w["gain_window_mean"] = w["window_mean"] - w["stale"]

    pooled = w[w.delay_h.isin([6, 12, 24, 48])]
    rng = np.random.default_rng(M20.SEED_BOOT)
    out = []
    for name, sub in [("all jobs", pooled),
                      ("stale used a dead qubit", pooled[pooled.stale_used_dead]),
                      ("stale used no dead qubit", pooled[~pooled.stale_used_dead])]:
        obs, lo, hi, n_days = M20.block_boot(sub, "gain_window_mean", rng)
        out.append({"subset": name, "n_jobs": len(sub), "n_days": n_days,
                    "mean_gain": obs, "lo95": lo, "hi95": hi})
    return pd.DataFrame(out), w


# ------------------------------------------------------------------- main

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED_FIT)

    head("STAGE 1: fit on development cards only (28 Aug to 12 Oct 2026)")
    say("  no card after 12 Oct is read; no transpiling and no simulation here")
    rows, hist_cache = collect_points()
    days = sorted({r["day"] for r in rows})
    say(f"  development window: {days[0]} to {days[-1]}")
    blks = blocks_of(days)
    say(f"  {len(blks)} chronological blocks, "
        f"{[f'{b[0]}..{b[-1]} ({len(b)}d)' for b in blks]}")
    say(f"  purge between a test block and its training blocks: {PURGE_H} h")
    say(f"  w grid: 0 to 1 in steps of 0.05 ({len(W_GRID)} values); N grid {N_GRID}")

    results = {}
    tabs_w, tabs_n = [], []
    head("STAGE 1 PARTS A and B: blend weights per field group")
    for group in GROUP_ORDER:
        say(f"\n  --- {group} ---")
        stats = sum_stats(rows, hist_cache, group)
        best_N, tab_w, tab_n = fit_group(group, stats, days)
        frame24 = stats[best_N]
        se_rows = []
        for D in DELAYS:
            mean_w, se_w, med_w = clustered_se_of_w(
                group, frame24[frame24.delay_h == D], days, rng)
            best = float(tab_w[tab_w.delay_h == D].w_heldout.iloc[0])
            se_rows.append({"group": group, "delay_h": D, "w_best": best,
                            "boot_mean_w": mean_w, "clustered_se_w": se_w,
                            "boot_median_w": med_w,
                            "above_zero_by_1se": bool(best - se_w > 0)
                            if np.isfinite(se_w) else False})
        se = pd.DataFrame(se_rows)
        n_clear = int(se.above_zero_by_1se.sum())
        say(f"  [{group}] clustered standard error of the best w "
            f"({N_BOOT_W} day resamples):")
        say(f"    {'D (h)':>6}{'w best':>9}{'boot mean':>11}{'clustered SE':>14}"
            f"{'w - SE > 0':>12}")
        for _, r in se.iterrows():
            say(f"    {r.delay_h:>6}{r.w_best:>9.2f}{r.boot_mean_w:>11.3f}"
                f"{r.clustered_se_w:>14.3f}{str(r.above_zero_by_1se):>12}")
        say(f"    delays where w is above 0 by more than one clustered SE: "
            f"{n_clear} of {len(DELAYS)}")
        blended = n_clear >= 2
        say(f"    -> {group} gets its own w(D)" if blended
            else f"    -> {group} uses the NEWEST value only (w = 0 at every D)")
        results[group] = {"N": best_N, "blended": blended,
                          "n_clear": n_clear,
                          "w_by_delay": {int(d): (float(v) if blended else 0.0)
                                         for d, v in zip(tab_w.delay_h,
                                                         tab_w.w_final)}}
        tabs_w.append(tab_w.assign(clear_delays=n_clear, blended=blended))
        tabs_n.append(tab_n.assign(group=group))
        se.to_csv(OUT / f"stage1_se_w_{group}.csv", index=False)

    pd.concat(tabs_w, ignore_index=True).to_csv(
        OUT / "stage1_w_by_delay.csv", index=False)
    pd.concat(tabs_n, ignore_index=True).to_csv(
        OUT / "stage1_n_choice.csv", index=False)

    head("STAGE 1 PART C: the dead qubit guard")
    say("  rule under test: a qubit dead in ANY of the last M distinct states "
        "is treated as dead at run time")
    say("  permanent defects are excluded from both sides, because they are "
        "removed for every arm anyway")
    graw, by_md, by_m, perm = guard_metrics(rows)
    say(f"\n  pooled over machines and delays:")
    say(f"    {'M':>3}{'precision':>11}{'recall':>9}{'F1':>8}"
        f"{'healthy removed per card':>27}{'truth dead per card':>22}")
    for _, r in by_m.iterrows():
        say(f"    {int(r.M):>3}{r.precision:>11.4f}{r.recall:>9.4f}{r.f1:>8.4f}"
            f"{r.healthy_removed_per_card:>27.4f}{r.truth_dead_per_card:>22.4f}")
    at24 = by_md[by_md.delay_h == 24].sort_values(["f1", "M"],
                                                  ascending=[False, True])
    say(f"\n  at D = 24 h, pooled over machines (this is the choosing rule):")
    say(f"    {'M':>3}{'precision':>11}{'recall':>9}{'F1':>8}"
        f"{'healthy removed per card':>27}")
    for _, r in by_md[by_md.delay_h == 24].iterrows():
        say(f"    {int(r.M):>3}{r.precision:>11.4f}{r.recall:>9.4f}{r.f1:>8.4f}"
            f"{r.healthy_removed_per_card:>27.4f}")
    best_f1 = at24.f1.max()
    best_M = int(min(at24[np.isclose(at24.f1, best_f1)].M))
    say(f"    best F1 at D = 24 h is {best_f1:.4f}; ties go to the smaller M")
    say(f"    -> M = {best_M}")

    say(f"\n  full table, every M and every D:")
    say(f"    {'M':>3}{'D (h)':>7}{'precision':>11}{'recall':>9}{'F1':>8}"
        f"{'healthy removed per card':>27}")
    for _, r in by_md.sort_values(["M", "delay_h"]).iterrows():
        say(f"    {int(r.M):>3}{int(r.delay_h):>7}{r.precision:>11.4f}"
            f"{r.recall:>9.4f}{r.f1:>8.4f}{r.healthy_removed_per_card:>27.4f}")
    by_md.to_csv(OUT / "stage1_guard_by_M_and_delay.csv", index=False)
    by_m.to_csv(OUT / "stage1_guard_pooled.csv", index=False)
    graw.to_csv(OUT / "stage1_guard_rows.csv", index=False)

    head("STAGE 1 PART D: window mean minus stale on the existing Round 1 rows")
    say("  gain = F_window_mean minus F_stale (positive means window mean is "
        "better). Pooled over D = 6, 12, 24 and 48 h. All jobs are included, "
        "gap jobs among them, as PROTOCOL.md section 10 requires.")
    dtab, _ = part_d()
    say(f"\n    {'subset':<28}{'n jobs':>8}{'mean gain':>12}{'95% low':>11}"
        f"{'95% high':>11}{'days':>9}")
    for _, r in dtab.iterrows():
        say(f"    {r.subset:<28}{r.n_jobs:>8}{r.mean_gain:>12.6f}"
            f"{r.lo95:>11.6f}{r.hi95:>11.6f}{r.n_days:>9}")
    dtab.to_csv(OUT / "stage1_round1_window_minus_stale.csv", index=False)

    head("STAGE 1 RESULT: the rule to be frozen")
    fit = {"fitted_utc_window": [days[0], days[-1]],
           "n_points": len(rows), "n_days": len(days),
           "w_grid_step": 0.05, "n_grid": N_GRID,
           "n_blocks": N_BLOCKS, "purge_h": PURGE_H,
           "guard_M": best_M, "guard_best_f1_at_24h": float(best_f1),
           "groups": results}
    say(f"  N (one value for every delay and every field group):")
    for g in GROUP_ORDER:
        say(f"    {g:<10} N = {results[g]['N']}")
    say(f"  w(D) table, the weight on the median of the last N distinct values:")
    say(f"    {'group':<10}" + "".join(f"{'D=' + str(d):>8}" for d in DELAYS)
        + "   blended?")
    for g in GROUP_ORDER:
        wrow = results[g]["w_by_delay"]
        say(f"    {g:<10}" + "".join(f"{wrow[d]:>8.2f}" for d in DELAYS)
            + f"   {'yes' if results[g]['blended'] else 'no'}")
    say(f"  dead qubit guard: M = {best_M} "
        f"(dead in any of the last {best_M} distinct states)")
    (OUT / "stage1_fitted_rule.json").write_text(json.dumps(fit, indent=2))
    say(f"\n  written to {OUT / 'stage1_fitted_rule.json'}")
    return 0


sys.exit(main())
