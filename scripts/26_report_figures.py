"""Report figures for the test period, plus the drift study panels.

OURS. PRESENTATION ONLY. Every number plotted here comes from
outputs/test_full/all_rows.csv or from logs/drift_study.log, which were both
written before this script existed. No modelling choice is made here and
nothing in engine/ is touched or imported.

Each figure writes a PNG at 300 dpi and a CSV holding exactly the numbers
drawn, so the picture can be checked against its own data.

Labels: window_mean is marked EXPLORATORY wherever it appears, because it was
not the pre-registered fix (PROTOCOL.md section 6 and L-039).

Usage:  26_report_figures.py [--results ...] [--outdir outputs/figures]
"""
import argparse
import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
SEED_BOOT = 20261017
N_BOOT = 4000
DELAYS = [1, 3, 6, 12, 24, 48]
ARMS = ["random", "stale", "window_mean", "std_adjusted", "shrinkage", "ceiling"]

# Validated categorical slots (dataviz reference palette, light mode).
# Colour follows the ENTITY, so an arm keeps its colour in every figure.
C = {
    "random":       "#2a78d6",   # slot 1 blue
    "stale":        "#eb6834",   # slot 2 orange
    "window_mean":  "#1baf7a",   # slot 3 aqua
    "std_adjusted": "#eda100",   # slot 4 yellow
    "shrinkage":    "#e87ba4",   # slot 5 magenta
    "ceiling":      "#0b0b0b",   # primary ink: a reference line, not a series
}
MACH = {"ibm_fez": "#2a78d6", "ibm_kingston": "#eb6834",
        "ibm_marrakesh": "#1baf7a"}
# Ordinal blue ramp for lag, which is ordered magnitude and not identity.
ORD = ["#86b6ef", "#2a78d6", "#104281"]

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"

PRETTY = {"random": "random", "stale": "stale",
          "window_mean": "window mean (exploratory)",
          "std_adjusted": "std-adjusted", "shrinkage": "shrinkage",
          "ceiling": "ceiling"}

GAPS = {
    "ibm_fez":       ("2026-09-22T14:00:30Z", "2026-09-23T16:44:52Z"),
    "ibm_kingston":  ("2026-09-22T14:13:16Z", "2026-09-23T17:27:02Z"),
    "ibm_marrakesh": ("2026-09-20T22:53:12Z", "2026-09-22T05:14:59Z"),
}


def style():
    plt.rcParams.update({
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
        "savefig.facecolor": SURFACE,
        "font.family": ["DejaVu Sans"], "font.size": 9,
        "axes.edgecolor": AXIS, "axes.linewidth": 0.8,
        "axes.labelcolor": INK2, "axes.titlecolor": INK,
        "xtick.color": MUTED, "ytick.color": MUTED,
        "xtick.labelcolor": INK2, "ytick.labelcolor": INK2,
        "grid.color": GRID, "grid.linewidth": 0.6,
        "legend.frameon": False, "lines.linewidth": 2.0,
        "savefig.dpi": 300, "savefig.bbox": "tight",
    })


def tidy(ax, ygrid=True):
    ax.spines[["top", "right"]].set_visible(False)
    if ygrid:
        ax.yaxis.grid(True)
        ax.set_axisbelow(True)


def load(results):
    df = pd.read_csv(results)
    df["t_s"] = pd.to_datetime(df.t_s, utc=True)
    df["t_r"] = pd.to_datetime(df.t_r, utc=True)
    df["day"] = df.t_s.dt.date.astype(str)
    g = {m: (pd.Timestamp(a), pd.Timestamp(b)) for m, (a, b) in GAPS.items()}
    df["touches_gap"] = [(ts < g[m][1]) and (tr > g[m][0])
                         for m, ts, tr in zip(df.machine, df.t_s, df.t_r)]
    idx = ["machine", "draw_order", "delay_h", "circuit", "day", "new_states",
           "touches_gap"]
    w = df.pivot_table(index=idx, columns="arm", values="fidelity").reset_index()
    for a in ARMS:
        w[f"regret_{a}"] = w["ceiling"] - w[a]
    return df, w[~w.touches_gap].copy()


def boot(frame, col, rng, n_boot=N_BOOT):
    frame = frame[frame[col].notna()]
    if len(frame) == 0:
        return np.nan, np.nan, np.nan
    pools = [g[col].to_numpy(float) for _, g in frame.groupby("day")]
    obs = float(np.concatenate(pools).mean())
    n = len(pools)
    draws = np.empty(n_boot)
    for i in range(n_boot):
        draws[i] = np.concatenate(
            [pools[j] for j in rng.integers(0, n, size=n)]).mean()
    lo, hi = (float(x) for x in np.percentile(draws, [2.5, 97.5]))
    return obs, lo, hi


def series_table(w, rng, cols, group="delay_h", extra=None):
    """mean, lo, hi for each column at each delay. Returns a tidy frame."""
    rows = []
    for key, g in w.groupby(group):
        for col in cols:
            o, lo, hi = boot(g, col, rng)
            r = {group: key, "column": col, "n": len(g), "mean": o,
                 "lo95": lo, "hi95": hi}
            if extra:
                r.update(extra)
            rows.append(r)
    return pd.DataFrame(rows)


def dodge(x, i, k, strength=0.035):
    """Small multiplicative offset so overlapping intervals stay readable
    on a log x axis."""
    if k == 1:
        return x
    return x * (1.0 + strength * (i - (k - 1) / 2.0))


def line_panel(ax, tab, cols, value="mean", label_right=True, dashed=()):
    k = len(cols)
    for i, col in enumerate(cols):
        arm = col.replace("regret_", "")
        sub = tab[tab.column == col].sort_values("delay_h")
        xs = np.array([dodge(d, i, k) for d in sub.delay_h])
        ys = sub[value].to_numpy()
        ax.errorbar(xs, ys, yerr=[ys - sub.lo95, sub.hi95 - ys],
                    color=C[arm], lw=0, elinewidth=1.1, capsize=2.5,
                    capthick=1.1, alpha=0.9, zorder=2)
        kw = dict(ls="--", dashes=(4, 3)) if arm in dashed else dict(ls="-")
        ax.plot(sub.delay_h, ys, color=C[arm], marker="o", ms=4.5,
                label=PRETTY[arm], zorder=3,
                markeredgecolor=SURFACE, markeredgewidth=0.8, **kw)
        if label_right:
            ax.annotate(PRETTY[arm], (sub.delay_h.iloc[-1], ys[-1]),
                        xytext=(6, 0), textcoords="offset points",
                        color=C[arm], fontsize=7.5, va="center")
    ax.set_xscale("log")
    ax.set_xticks(DELAYS)
    ax.set_xticklabels([str(d) for d in DELAYS])
    ax.minorticks_off()
    tidy(ax)


# ------------------------------------------------------------------ (a)
def fig_a(w, rng, outdir, machine=None, tag="all_machines"):
    sub = w if machine is None else w[w.machine == machine]
    fid = series_table(sub, rng, ARMS)
    reg = series_table(sub, rng, [f"regret_{a}" for a in ARMS if a != "ceiling"])
    both = pd.concat([fid.assign(panel="mean fidelity"),
                      reg.assign(panel="regret vs ceiling")])
    both["machine"] = machine or "all three"
    both["label"] = "EXPLORATORY (six arm comparison); A and B are the only "\
                    "confirmatory tests"

    fig, axes = plt.subplots(1, 2, figsize=(11.4, 4.3))
    # six series on the left, so the legend carries identity and the right-end
    # labels are left off: at six lines they collide with each other.
    line_panel(axes[0], fid, ARMS, dashed=("ceiling",), label_right=False)
    axes[0].set_title("Mean fidelity by queue delay", fontsize=10.5,
                      loc="left", pad=10)
    axes[0].set_xlabel("queue delay D (hours, log scale)")
    axes[0].set_ylabel("mean Hellinger fidelity")

    informed = [f"regret_{a}" for a in ("stale", "window_mean",
                                        "std_adjusted", "shrinkage")]
    line_panel(axes[1], reg, informed)
    axes[1].set_xlim(right=48 * 3.4)   # room for the right-end direct labels
    axes[1].axhline(0, color=C["ceiling"], ls="--", dashes=(4, 3), lw=1.2)
    axes[1].annotate("ceiling (regret 0 by definition)", (1.0, 0),
                     xytext=(2, 5), textcoords="offset points",
                     color=INK2, fontsize=7.5)
    axes[1].set_title("Regret against the ceiling, random arm left out",
                      fontsize=10.5, loc="left", pad=10)
    axes[1].set_xlabel("queue delay D (hours, log scale)")
    axes[1].set_ylabel("mean regret (lower is better)")

    axes[0].legend(loc="lower left", fontsize=7.5, ncol=2)
    axes[1].legend(loc="upper left", fontsize=7.5)
    who = "all three machines" if machine is None else machine
    fig.suptitle(f"Six strategies on {who}, test days 21 Sep to 12 Oct 2026",
                 fontsize=11.5, x=0.005, y=1.04, ha="left", color=INK)
    fig.text(0.005, -0.04,
             "Bars are 95 percent block bootstrap intervals over whole days. "
             "Jobs touching the 22 to 23 Sep publishing gap are excluded. "
             "The random arm is omitted from the right panel because it would "
             "squash the scale.\nOnly stale vs ceiling (A) and shrinkage vs "
             "stale (B) are confirmatory; every other arm comparison is "
             "exploratory.", fontsize=7, color=MUTED, ha="left")
    png = outdir / f"fig_a_six_strategies_{tag}.png"
    fig.savefig(png)
    plt.close(fig)
    both.to_csv(outdir / f"fig_a_six_strategies_{tag}.csv", index=False)
    return png


# ------------------------------------------------------------------ (b)
def fig_b(w, rng, outdir):
    buckets = [("0", w.new_states == 0), ("1", w.new_states == 1),
               ("2 or more", w.new_states >= 2)]
    arms = ["stale", "window_mean", "std_adjusted", "shrinkage"]
    rows = []
    for name, mask in buckets:
        g = w[mask]
        for a in arms:
            o, lo, hi = boot(g, f"regret_{a}", rng)
            rows.append(dict(new_states_crossed=name, arm=a, n=len(g),
                             mean_regret=o, lo95=lo, hi95=hi,
                             label="PRE-REGISTERED axis (PROTOCOL.md section 9 "
                                   "axis 3); the per arm split is exploratory"))
    tab = pd.DataFrame(rows)

    fig, ax = plt.subplots(figsize=(7.6, 4.3))
    width = 0.19
    xs = np.arange(len(buckets))
    for i, a in enumerate(arms):
        s = tab[tab.arm == a]
        off = (i - (len(arms) - 1) / 2) * (width + 0.012)
        vals = s.mean_regret.to_numpy()
        ax.bar(xs + off, vals, width, color=C[a], label=PRETTY[a],
               edgecolor=SURFACE, linewidth=1.0, zorder=2)
        ax.errorbar(xs + off, vals,
                    yerr=[vals - s.lo95, s.hi95 - vals], fmt="none",
                    ecolor=INK2, elinewidth=1.0, capsize=2.5, zorder=3)
    ax.set_xticks(xs)
    ax.set_xticklabels([f"{name}\nn = {int(tab[tab.new_states_crossed==name].n.iloc[0])} jobs"
                        for name, _ in buckets])
    ax.set_xlabel("number of new calibration states crossed between "
                  "submission and run")
    ax.set_ylabel("mean regret vs ceiling")
    ax.set_title("Regret by how many new states the job crossed",
                 fontsize=11.5, loc="left", pad=10)
    ax.legend(fontsize=7.5, ncol=2, loc="upper left")
    tidy(ax)
    fig.text(0.005, -0.08,
             "PROTOCOL.md section 9 axis 3. With 0 new states the stale arm's "
             "regret is exactly 0 by construction, which is sanity check 1.\n"
             "The other three arms can be non-zero there because their "
             "predicted card is a blend, not the latest card.\nExact values "
             "are in fig_b_regret_by_new_states.csv. Gap jobs excluded.",
             fontsize=7, color=MUTED, ha="left")
    fig.savefig(outdir / "fig_b_regret_by_new_states.png")
    plt.close(fig)
    tab.to_csv(outdir / "fig_b_regret_by_new_states.csv", index=False)


# ------------------------------------------------------------------ (c)
def fig_c(w, rng, outdir):
    rows = []
    for m in sorted(w.machine.unique()):
        for D in DELAYS:
            g = w[(w.machine == m) & (w.delay_h == D)]
            o, lo, hi = boot(g, "regret_stale", rng)
            rows.append(dict(machine=m, delay_h=D, n=len(g), mean_regret=o,
                             lo95=lo, hi95=hi, label="PRE-REGISTERED "
                             "(PROTOCOL.md section 15 prediction 7)"))
    tab = pd.DataFrame(rows)

    fig, ax = plt.subplots(figsize=(7.6, 4.5))
    ms = sorted(w.machine.unique())
    for i, m in enumerate(ms):
        s = tab[tab.machine == m].sort_values("delay_h")
        xs = np.array([dodge(d, i, len(ms)) for d in s.delay_h])
        v = s.mean_regret.to_numpy()
        ax.errorbar(xs, v, yerr=[v - s.lo95, s.hi95 - v], color=MACH[m],
                    lw=0, elinewidth=1.1, capsize=2.5, capthick=1.1, zorder=2)
        ax.plot(s.delay_h, v, color=MACH[m], marker="o", ms=4.5, label=m,
                markeredgecolor=SURFACE, markeredgewidth=0.8, zorder=3)
        ax.annotate(m, (s.delay_h.iloc[-1], v[-1]), xytext=(6, 0),
                    textcoords="offset points", color=MACH[m], fontsize=8,
                    va="center")
    ax.set_xscale("log")
    ax.set_xticks(DELAYS)
    ax.set_xticklabels([str(d) for d in DELAYS])
    ax.minorticks_off()
    ax.set_xlabel("queue delay D (hours, log scale)")
    ax.set_ylabel("mean stale regret vs ceiling")
    ax.set_title("Cost of a stale card, per machine", fontsize=11.5,
                 loc="left", pad=10)
    ax.legend(fontsize=8, loc="upper left")
    tidy(ax)
    fig.text(0.005, -0.06,
             "95 percent block bootstrap intervals over whole days, gap jobs "
             "excluded. PROTOCOL.md section 15 prediction 7 said "
             "ibm_marrakesh\nwould be the worst of the three, and it is at "
             "every delay.", fontsize=7, color=MUTED, ha="left")
    fig.savefig(outdir / "fig_c_stale_regret_per_machine.png")
    plt.close(fig)
    tab.to_csv(outdir / "fig_c_stale_regret_per_machine.csv", index=False)


# ------------------------------------------------------------------ (d)
def fig_d(w, rng, outdir):
    w = w.copy()
    w["gain"] = w["stale"] - w["shrinkage"]      # positive = shrinkage better
    rows = []
    for name, mask in (("6 h", w.delay_h == 6), ("24 h", w.delay_h == 24),
                       ("6 and 24 h pooled", w.delay_h.isin([6, 24]))):
        g = w[mask]
        o, lo, hi = boot(g, "gain", rng)
        rows.append(dict(delay=name, n=len(g), mean_gain=o, lo95=lo, hi95=hi,
                         label="CONFIRMATORY, PROTOCOL.md section 11 "
                               "comparison B"))
    tab = pd.DataFrame(rows)

    fig, ax = plt.subplots(figsize=(7.2, 3.3))
    ys = np.arange(len(tab))[::-1]
    for y, (_, r) in zip(ys, tab.iterrows()):
        colour = C["shrinkage"] if r.delay != "6 and 24 h pooled" else INK
        ax.plot([r.lo95, r.hi95], [y, y], color=colour, lw=2.2,
                solid_capstyle="round", zorder=2)
        ax.plot([r.mean_gain], [y], marker="o", ms=7, color=colour,
                markeredgecolor=SURFACE, markeredgewidth=1.2, zorder=3)
        ax.annotate(f"{r.mean_gain:+.5f}  [{r.lo95:+.5f}, {r.hi95:+.5f}]",
                    (r.hi95, y), xytext=(8, 0), textcoords="offset points",
                    va="center", fontsize=8, color=INK2)
    ax.axvline(0, color=AXIS, lw=1.2, ls="--", dashes=(4, 3), zorder=1)
    ax.annotate("no difference", (0, ys[0] + 0.3), xytext=(4, 0),
                textcoords="offset points", fontsize=7.5, color=MUTED,
                va="center", annotation_clip=False)
    ax.set_yticks(ys)
    ax.set_yticklabels([f"{r.delay}\nn = {r.n}" for _, r in tab.iterrows()],
                       fontsize=8)
    ax.set_xlabel("shrinkage fidelity minus stale fidelity "
                  "(positive = shrinkage better)")
    ax.set_title("Comparison B: shrinkage minus stale, paired by job",
                 fontsize=11.5, loc="left", pad=10)
    ax.set_xlim(min(tab.lo95) - 0.004, max(tab.hi95) + 0.009)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.xaxis.grid(True)
    ax.set_axisbelow(True)
    ax.tick_params(axis="y", length=0)
    fig.text(0.005, -0.14,
             "CONFIRMATORY. Every interval includes zero, so the "
             "pre-registered fix did not beat using the newest card on the "
             "test days.\nThe point estimate at 6 h is negative. 95 percent "
             "block bootstrap over whole days, gap jobs excluded.",
             fontsize=7, color=MUTED, ha="left")
    fig.savefig(outdir / "fig_d_shrinkage_minus_stale.png")
    plt.close(fig)
    tab.to_csv(outdir / "fig_d_shrinkage_minus_stale.csv", index=False)


# ------------------------------------------- drift study log parsing
def parse_drift(path):
    text = Path(path).read_text()
    blocks = re.split(r"={40,}\n(ibm_\w+)\s+\(\d+ training days\)\n={40,}",
                      text)
    out = {}
    for i in range(1, len(blocks), 2):
        out[blocks[i]] = blocks[i + 1]
    hours, persist, curse = [], [], []
    for machine, body in out.items():
        m = re.search(r"arrivals by UTC hour \(cz error\), 0 to 23:\s*\n\s*"
                      r"((?:\s*\d+){24})", body)
        if m:
            counts = [int(x) for x in m.group(1).split()]
            for h, c in enumerate(counts):
                hours.append(dict(machine=machine, utc_hour=h,
                                  cz_new_values=c))
        sec = re.search(r"3\. RANK PERSISTENCE.*?\n(.*?)\n\n", body, re.S)
        if sec:
            for line in sec.group(1).splitlines():
                p = line.split()
                if len(p) >= 4 and re.match(r"^-?\d*\.\d+$", p[-1]):
                    field = " ".join(p[:-3])
                    for lag, v in zip((1, 3, 10), p[-3:]):
                        persist.append(dict(machine=machine, field=field,
                                            lag=lag, spearman=float(v)))
        sec = re.search(r"5\. WINNER'S CURSE.*?rank \+3\n(.*?)(?:\n\n|\Z)",
                        body, re.S)
        if sec:
            for line in sec.group(1).splitlines():
                p = line.split()
                if len(p) >= 4 and re.match(r"^\d+\.\d$", p[-1]):
                    field = " ".join(p[:-4])
                    curse.append(dict(machine=machine, field=field,
                                      top_k=int(p[-4]),
                                      rank_now=float(p[-3]),
                                      rank_next=float(p[-2]),
                                      rank_plus3=float(p[-1])))
    return (pd.DataFrame(hours), pd.DataFrame(persist), pd.DataFrame(curse))


def fig_e(drift_log, outdir):
    hours, persist, curse = parse_drift(drift_log)
    note = ("EXPLORATORY. Training days only, 2026-08-28 to 2026-09-20. "
            "No simulation. Source logs/drift_study.log.")

    # e1 update hour of day per machine
    hours["label"] = note
    ms = sorted(hours.machine.unique())
    fig, axes = plt.subplots(1, len(ms), figsize=(11, 3.2), sharey=True)
    for ax, m in zip(np.atleast_1d(axes), ms):
        s = hours[hours.machine == m].sort_values("utc_hour")
        ax.bar(s.utc_hour, s.cz_new_values, width=0.8, color=MACH[m],
               edgecolor=SURFACE, linewidth=0.8, zorder=2)
        ax.set_title(m, fontsize=9.5, loc="left", color=INK)
        ax.set_xticks(range(0, 24, 4))
        ax.set_xlabel("hour of day, UTC")
        tidy(ax)
    np.atleast_1d(axes)[0].set_ylabel("new cz error values arriving")
    fig.suptitle("When a new cz error measurement arrives, by hour of day",
                 fontsize=11.5, x=0.005, y=1.04, ha="left", color=INK)
    fig.text(0.005, -0.1, note + " Counted over the 22 to 26 distinct cz "
             "values per machine in the training window.\nIST is UTC plus 5 "
             "hours 30 minutes.", fontsize=7, color=MUTED, ha="left")
    fig.savefig(outdir / "fig_e1_update_hour_per_machine.png")
    plt.close(fig)
    hours.to_csv(outdir / "fig_e1_update_hour_per_machine.csv", index=False)

    # e2 rank persistence by lag
    persist["label"] = note
    fields = ["T1", "T2", "readout", "sx error", "cz error"]
    fig, axes = plt.subplots(1, len(ms), figsize=(11.5, 3.6), sharey=True)
    xs = np.arange(len(fields))
    width = 0.26
    for ax, m in zip(np.atleast_1d(axes), ms):
        for i, lag in enumerate((1, 3, 10)):
            vals = [float(persist[(persist.machine == m)
                                  & (persist.field == f)
                                  & (persist.lag == lag)].spearman.iloc[0])
                    for f in fields]
            ax.bar(xs + (i - 1) * (width + 0.01), vals, width, color=ORD[i],
                   label=f"lag {lag}", edgecolor=SURFACE, linewidth=0.8,
                   zorder=2)
        ax.set_xticks(xs)
        ax.set_xticklabels(fields, rotation=30, ha="right", fontsize=8)
        ax.set_title(m, fontsize=9.5, loc="left", color=INK)
        ax.set_ylim(0, 1)
        tidy(ax)
    a0 = np.atleast_1d(axes)[0]
    a0.set_ylabel("Spearman rank correlation")
    a0.legend(fontsize=7.5, loc="lower right")
    fig.suptitle("Does the ranking of qubits survive? Rank persistence by lag",
                 fontsize=11.5, x=0.005, y=1.04, ha="left", color=INK)
    fig.text(0.005, -0.18, note + " Lag counts DISTINCT values of that field, "
             "not states and not cards (Amendment A1.2).\n1.0 would mean the "
             "order never changes; 0.0 would mean it is unrelated. Lag is an "
             "ordered quantity, so it uses one hue light to dark, not "
             "separate hues.", fontsize=7, color=MUTED, ha="left")
    fig.savefig(outdir / "fig_e2_rank_persistence_by_lag.png")
    plt.close(fig)
    persist.to_csv(outdir / "fig_e2_rank_persistence_by_lag.csv", index=False)

    # e3 winner's curse
    curse["label"] = note
    fig, axes = plt.subplots(1, len(ms), figsize=(11.5, 3.6), sharey=True)
    for ax, m in zip(np.atleast_1d(axes), ms):
        for i, stage in enumerate(("rank_now", "rank_next", "rank_plus3")):
            vals = [float(curse[(curse.machine == m)
                                & (curse.field == f)][stage].iloc[0])
                    for f in fields]
            ax.bar(xs + (i - 1) * (width + 0.01), vals, width, color=ORD[i],
                   label={"rank_now": "when chosen",
                          "rank_next": "next distinct value",
                          "rank_plus3": "three values later"}[stage],
                   edgecolor=SURFACE, linewidth=0.8, zorder=2)
        ax.set_xticks(xs)
        ax.set_xticklabels(fields, rotation=30, ha="right", fontsize=8)
        ax.set_title(m, fontsize=9.5, loc="left", color=INK)
        ax.set_ylim(0, 50)
        ax.axhline(50, color=AXIS, lw=0.8, ls="--", dashes=(4, 3))
        tidy(ax)
    a0 = np.atleast_1d(axes)[0]
    a0.set_ylabel("percentile rank (0 = best, 50 = pure noise)")
    a0.legend(fontsize=7.5, loc="upper left")
    fig.suptitle("The winner's curse: where the best ten qubits sit next time",
                 fontsize=11.5, x=0.005, y=1.04, ha="left", color=INK)
    fig.text(0.005, -0.18, note + " The top ten qubits sit at percentile 2.9 "
             "when chosen. By the next distinct value they have fallen to "
             "between 10 and 31.\nThey do not fall all the way to 50, so the "
             "choice keeps some value; this is consistent with a mix of real "
             "persistence and measurement noise, which our cards cannot "
             "separate.", fontsize=7, color=MUTED, ha="left")
    fig.savefig(outdir / "fig_e3_winners_curse.png")
    plt.close(fig)
    curse.to_csv(outdir / "fig_e3_winners_curse.csv", index=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results",
                    default=str(ROOT / "outputs/test_full/all_rows.csv"))
    ap.add_argument("--drift-log", default=str(ROOT / "logs/drift_study.log"))
    ap.add_argument("--outdir", default=str(ROOT / "outputs/figures"))
    args = ap.parse_args()
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    style()
    rng = np.random.default_rng(SEED_BOOT)

    df, w = load(args.results)
    print(f"rows {len(df)}   jobs after gap exclusion {len(w)}   "
          f"days {w.day.nunique()}")
    print(f"bootstrap seed {SEED_BOOT}, {N_BOOT} resamples\n")

    fig_a(w, rng, outdir)
    for m in sorted(w.machine.unique()):
        fig_a(w, rng, outdir, machine=m, tag=m)
    fig_b(w, rng, outdir)
    fig_c(w, rng, outdir)
    fig_d(w, rng, outdir)
    fig_e(args.drift_log, outdir)

    for f in sorted(outdir.iterdir()):
        print(f"  {f.name:<52} {f.stat().st_size/1024:>8.1f} KB")


main()
