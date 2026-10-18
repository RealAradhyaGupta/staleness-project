"""M3 + M7 - Drift analysis, summary statistics and plots.

Usage:  python analysis.py synthetic      (or: python analysis.py ibm_torino)
Output:
  results/volatility_<source>.csv      per-qubit average error and swing (M3)
  results/summary_<source>.csv         per delay: mean fidelity per strategy, staleness cost,
                                       gap recovered, paired test of stability vs stale (M7)
  plots/drift_heatmap_<source>.png     how every qubit's error moves across cycles
  plots/fidelity_vs_delay_<source>.png mean fidelity of each strategy as the delay grows
  plots/gain_over_stale_<source>.png   how much each strategy beats (or loses to) Stale
"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap
from scipy.stats import wilcoxon

import config
import snapshot

# Colours: validated colour-blind-safe categorical slots; reference lines in neutral grey.
SURFACE, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e6e5e1"
COLOR = {"stale": "#2a78d6", "trend": "#eb6834", "stability": "#1baf7a", "oracle": INK2}
LABEL = {"blind": "Blind", "stale": "Stale (today)", "trend": "Trend forecast",
         "stability": "Stability (ours)", "oracle": "Oracle (ceiling)"}
BLUES = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
    "text.color": INK, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8,
    "axes.spines.top": False, "axes.spines.right": False, "font.size": 10,
})


def label_note(source):
    return "SYNTHETIC drift on ibm_torino's published calibration" if source == "synthetic" \
        else f"Real calibration history: {source}"


def ci95(x):
    x = np.asarray(x, dtype=float)
    return 1.96 * x.std(ddof=1) / np.sqrt(len(x)) if len(x) > 1 else 0.0


# ---------- M3: how much does each qubit drift? ----------

def drift_analysis(source):
    series = snapshot.load_series(os.path.join(config.SNAPSHOT_DIR, source))
    err = np.array([snapshot.clean(s)["err_1q"] for s in series])          # cycles x qubits
    log_err = np.log10(err)
    swing = log_err.std(0)
    vol = pd.DataFrame({"qubit": np.arange(err.shape[1]),
                        "mean_err_1q": err.mean(0), "swing_log10": swing}).sort_values("swing_log10")
    vol.to_csv(os.path.join(config.RESULTS_DIR, f"volatility_{source}.csv"), index=False)

    order = np.argsort(swing)
    fig, ax = plt.subplots(figsize=(7.5, 8))
    cmap = LinearSegmentedColormap.from_list("blues", BLUES)
    im = ax.imshow(log_err[:, order].T, aspect="auto", cmap=cmap, interpolation="nearest")
    ax.grid(False)
    ax.set_xlabel("calibration cycle")
    ax.set_ylabel(f"qubits ({err.shape[1]}), sorted: steadiest at top, swingiest at bottom")
    ax.set_yticks([])
    ax.set_xticks(range(0, log_err.shape[0], max(1, log_err.shape[0] // 10)))
    cb = fig.colorbar(im, ax=ax, fraction=0.04, pad=0.02)
    cb.set_label("single-qubit gate error (log10)  -  darker = worse", color=INK2)
    cb.outline.set_visible(False)
    ax.set_title("How each qubit's error moves between calibrations", loc="left", fontsize=12)
    fig.text(0.01, 0.005, label_note(source), color=INK2, fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(config.PLOTS_DIR, f"drift_heatmap_{source}.png"), dpi=160)
    plt.close(fig)
    return vol


# ---------- M7: summary table ----------

def summarize(df):
    wide = df.pivot_table(index=["k", "delay", "circuit"], columns="strategy", values="fidelity").reset_index()
    rows = []
    for d, g in wide.groupby("delay"):
        stale, stab, trend, oracle = g["stale"].mean(), g["stability"].mean(), g["trend"].mean(), g["oracle"].mean()
        cost = oracle - stale
        try:
            p = wilcoxon(g["stability"], g["stale"]).pvalue
        except ValueError:                      # all differences zero
            p = 1.0
        rows.append({
            "delay_cycles": d, "n_pairs": len(g),
            "blind": g["blind"].mean(), "stale": stale, "trend": trend, "stability": stab, "oracle": oracle,
            "staleness_cost": cost,
            "gap_recovered_stability": (stab - stale) / cost if cost > 1e-9 else np.nan,
            "gap_recovered_trend": (trend - stale) / cost if cost > 1e-9 else np.nan,
            "stability_beats_stale_share": (g["stability"] > g["stale"]).mean(),
            "wilcoxon_p_stability_vs_stale": p,
        })
    return pd.DataFrame(rows), wide


# ---------- M7: plots ----------

def plot_fidelity_vs_delay(df, source):
    fig, ax = plt.subplots(figsize=(8, 5))
    delays = sorted(df["delay"].unique())
    x = np.array(delays, dtype=float)              # real spacing: 7 sits far to the right of 3
    ends = []
    for s in ["oracle", "stale", "trend", "stability"]:
        g = df[df.strategy == s].groupby("delay")["fidelity"]
        m = g.mean().reindex(delays).values
        style = dict(linestyle="--", linewidth=1.5) if s == "oracle" else dict(linewidth=2)
        ax.plot(x, m, color=COLOR[s], marker="o", markersize=6, label=LABEL[s], **style)
        ends.append((m[-1], s))
    # direct labels at the right end, nudged apart only as much as needed so they don't collide
    lo, hi = ax.get_ylim()
    gap = 0.035 * (hi - lo)
    ends.sort()
    placed = []
    for y, s in ends:
        if placed and y - placed[-1] < gap:
            y = placed[-1] + gap
        placed.append(y)
        ax.text(x[-1] + 0.15, y, LABEL[s], color=INK, va="center", fontsize=9)
    blind = df[df.strategy == "blind"]["fidelity"].mean()
    ax.set_xticks(x, [str(d) for d in delays])
    ax.set_xlim(x[0] - 0.3, x[-1] + 1.8)
    ax.set_xlabel("delay (calibration cycles crossed while the job waits in the queue)")
    ax.set_ylabel("mean Hellinger fidelity (1 = perfect)")
    ax.set_title("Fidelity of each placement strategy as the queue delay grows", loc="left", fontsize=12)
    ax.legend(loc="lower left", frameon=False, fontsize=9)
    fig.text(0.01, 0.005, label_note(source) + "  |  averages over all circuits and starting cycles "
             "(uncertainty shown in the gain chart)\n"
             f"Not shown: Blind placement (compiler sees no quality info) averages {blind:.2f}, far below this axis",
             color=INK2, fontsize=8)
    fig.tight_layout(rect=[0, 0.07, 1, 1])
    fig.savefig(os.path.join(config.PLOTS_DIR, f"fidelity_vs_delay_{source}.png"), dpi=160)
    plt.close(fig)


def plot_gain_over_stale(wide, source):
    delays = sorted(wide["delay"].unique())
    strategies = ["oracle", "trend", "stability"]
    fig, ax = plt.subplots(figsize=(8, 4.8))
    width = 0.26
    for i, s in enumerate(strategies):
        means, cis = [], []
        for d in delays:
            diff = (wide.loc[wide.delay == d, s] - wide.loc[wide.delay == d, "stale"]) * 100
            means.append(diff.mean()); cis.append(ci95(diff))
        xs = np.arange(len(delays)) + (i - 1) * width
        ax.bar(xs, means, width=width - 0.03, color=COLOR[s], label=LABEL[s],
               yerr=cis, error_kw=dict(ecolor=INK2, elinewidth=1, capsize=3))
    ax.axhline(0, color=INK2, linewidth=1)
    ax.set_xticks(np.arange(len(delays)), [str(d) for d in delays])
    ax.set_xlabel("delay (calibration cycles crossed)")
    ax.set_ylabel("fidelity gain over Stale (percentage points)")
    ax.set_title("Gain over today's approach. Oracle bar = the most that could be recovered",
                 loc="left", fontsize=12)
    ax.legend(frameon=False, fontsize=9, ncol=3, loc="upper left")
    fig.text(0.01, 0.005, label_note(source) + "  |  whiskers = 95% confidence interval", color=INK2, fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(config.PLOTS_DIR, f"gain_over_stale_{source}.png"), dpi=160)
    plt.close(fig)


def main(source):
    os.makedirs(config.PLOTS_DIR, exist_ok=True)
    os.makedirs(config.RESULTS_DIR, exist_ok=True)
    vol = drift_analysis(source)
    print(f"Drift: steadiest qubit swings {vol.swing_log10.min():.2f}, swingiest {vol.swing_log10.max():.2f} (log10 units)")
    df = pd.read_csv(os.path.join(config.RESULTS_DIR, f"results_{source}.csv"))
    summary, wide = summarize(df)
    summary.to_csv(os.path.join(config.RESULTS_DIR, f"summary_{source}.csv"), index=False)
    plot_fidelity_vs_delay(df, source)
    plot_gain_over_stale(wide, source)
    with pd.option_context("display.width", 200, "display.max_columns", 20):
        print(summary.round(3).to_string(index=False))
    print(f"plots written to {config.PLOTS_DIR}/")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "synthetic")
