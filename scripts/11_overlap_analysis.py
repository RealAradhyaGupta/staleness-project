"""Part B: does a stale snapshot still pick the same best qubits?

Reads only data/clean/*.csv. No network calls, no quantum jobs.
Writes outputs/overlap_qubits.png, outputs/overlap_pairs.png and
outputs/overlap_table.csv.
"""
import itertools
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

CLEAN = Path("data/clean")
OUT = Path("outputs")
TOP_Q = 10
TOP_P = 20
MAX_GAP = 30

# Dead qubit thresholds. A working qubit has sx error near 1e-4 and readout
# error near 1e-2, so these cuts are far above normal and only catch qubits
# that are broken, not merely poor.
SX_DEAD = 0.1
RO_DEAD = 0.2

# Categorical slots 1 to 3 of the validated palette, plus text and grid inks.
COLORS = {"ibm_fez": "#2a78d6", "ibm_kingston": "#eb6834",
          "ibm_marrakesh": "#1baf7a"}
INK = "#0b0b0b"
INK2 = "#52514e"
GRID = "#dcdbd6"
SURFACE = "#fcfcfb"


def load():
    q = pd.read_csv(CLEAN / "qubits.csv", parse_dates=["snapshot_utc"])
    p = pd.read_csv(CLEAN / "pairs.csv", parse_dates=["snapshot_utc"])
    q["dead"] = (
        (q.sx_error > SX_DEAD)
        | (q.readout_error > RO_DEAD)
        | q.t1_us.isna()
        | q.t2_us.isna()
    )
    q["score"] = q.readout_error + q.sx_error
    return q, p


def report_dead(q):
    print("=== dead qubits ===")
    print(f"rule: sx_error > {SX_DEAD}, or readout_error > {RO_DEAD}, "
          f"or T1 missing, or T2 missing")
    per_snap = q.groupby(["machine", "snapshot_utc"]).dead.sum()
    out = {}
    for m, g in per_snap.groupby(level=0):
        out[m] = (g.mean(), g.min(), g.max(), len(g))
        print(f"  {m}: mean {g.mean():.2f} dead of 156, "
              f"min {int(g.min())}, max {int(g.max())}, over {len(g)} snapshots")
    reasons = q[q.dead]
    print("  reason counts (a qubit can trip more than one):")
    print(f"    sx_error > {SX_DEAD}:      {(reasons.sx_error > SX_DEAD).sum()}")
    print(f"    readout_error > {RO_DEAD}: {(reasons.readout_error > RO_DEAD).sum()}")
    print(f"    T1 missing:            {reasons.t1_us.isna().sum()}")
    print(f"    T2 missing:            {reasons.t2_us.isna().sum()}")
    return out


def best_sets(q, p):
    """Top qubits and top pairs per machine and snapshot."""
    qbest, pbest, n_live, n_elig = {}, {}, {}, {}
    live = q[~q.dead]
    for (m, s), g in live.groupby(["machine", "snapshot_utc"]):
        qbest[(m, s)] = frozenset(
            g.nsmallest(TOP_Q, "score").qubit.tolist()
        )
        n_live[(m, s)] = len(g)
    live_sets = {k: set(g.qubit) for k, g in live.groupby(["machine", "snapshot_utc"])}
    for (m, s), g in p.groupby(["machine", "snapshot_utc"]):
        alive = live_sets.get((m, s))
        if alive is None:
            continue
        ok = g[g.qubit_a.isin(alive) & g.qubit_b.isin(alive)]
        if ok.empty:
            continue
        pbest[(m, s)] = frozenset(
            map(tuple, ok.nsmallest(TOP_P, "cz_error")[["qubit_a", "qubit_b"]].values)
        )
        n_elig[(m, s)] = len(ok)
    return qbest, pbest, n_live, n_elig


def overlaps(best, top_n):
    """Average overlap per machine and rounded gap in days."""
    rows = []
    keys = {}
    for (m, s) in best:
        keys.setdefault(m, []).append(s)
    for m, stamps in keys.items():
        stamps = sorted(stamps)
        for a, b in itertools.combinations(stamps, 2):
            gap_days = (b - a).total_seconds() / 86400.0
            bucket = int(round(gap_days))
            if bucket < 1 or bucket > MAX_GAP:
                continue
            shared = len(best[(m, a)] & best[(m, b)])
            rows.append({"machine": m, "gap": bucket,
                         "gap_exact": gap_days,
                         "overlap": shared / top_n})
    df = pd.DataFrame(rows)
    return df.groupby(["machine", "gap"]).overlap.agg(["mean", "count"]).reset_index(), df


def chance_level(n_map, k):
    """Expected overlap fraction when picking k at random from n candidates."""
    vals = list(n_map.values())
    return k / float(np.mean(vals)), float(np.mean(vals))


def plot(curve, chance, title, ylabel, note, path):
    fig, ax = plt.subplots(figsize=(8.4, 5.0), dpi=200)
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)
    ends = []
    for m, g in curve.groupby("machine"):
        g = g.sort_values("gap")
        ax.plot(g.gap, g["mean"], color=COLORS[m], linewidth=2,
                marker="o", markersize=4, label=m)
        last = g.iloc[-1]
        ends.append([m, float(last.gap), float(last["mean"])])
    # stagger the direct labels so they never overlap
    ends.sort(key=lambda e: -e[2])
    min_sep = 0.045
    for i in range(1, len(ends)):
        if ends[i - 1][2] - ends[i][2] < min_sep:
            ends[i][2] = ends[i - 1][2] - min_sep
    for m, gx, gy in ends:
        ax.annotate(m, (gx, gy), xytext=(8, 0), textcoords="offset points",
                    color=COLORS[m], fontsize=9, va="center")
    ax.axhline(chance, color=INK2, linewidth=1.5, linestyle="--")
    ax.annotate(f"chance level {chance:.2f}", (1, chance), xytext=(0, 6),
                textcoords="offset points", color=INK2, fontsize=9)
    ax.set_xlabel("gap between the two snapshots (days)", color=INK2, fontsize=10)
    ax.set_ylabel(ylabel, color=INK2, fontsize=10)
    ax.set_title(title, color=INK, fontsize=13, pad=12, loc="left")
    ax.set_ylim(0, 1.0)
    ax.set_xlim(0, MAX_GAP + 3.5)
    ax.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)
    ax.tick_params(colors=INK2, labelsize=9)
    ax.legend(frameon=False, fontsize=9, labelcolor=INK2, loc="upper right")
    fig.text(0.013, 0.015, note, fontsize=8, color=INK2)
    fig.tight_layout(rect=(0, 0.035, 1, 1))
    fig.savefig(path, facecolor=SURFACE)
    plt.close(fig)
    print("wrote", path)


def main():
    OUT.mkdir(exist_ok=True)
    q, p = load()
    report_dead(q)
    qbest, pbest, n_live, n_elig = best_sets(q, p)
    print(f"\nsnapshots usable for qubit ranking: {len(qbest)}")
    print(f"snapshots usable for pair ranking:  {len(pbest)}")

    ch_q, mean_live = chance_level(n_live, TOP_Q)
    ch_p, mean_elig = chance_level(n_elig, TOP_P)
    print(f"mean live qubits per snapshot: {mean_live:.1f} "
          f"-> chance overlap {ch_q:.3f}")
    print(f"mean eligible pairs per snapshot: {mean_elig:.1f} "
          f"-> chance overlap {ch_p:.3f}")

    cq, rawq = overlaps(qbest, TOP_Q)
    cp, rawp = overlaps(pbest, TOP_P)
    print(f"\nsnapshot comparisons used: qubits {len(rawq)}, pairs {len(rawp)}")

    plot(cq, ch_q,
         "Best-qubit lists agree only about 1 in 4, even one day apart",
         f"shared best qubits / {TOP_Q}",
         f"each point is the mean over all snapshot pairs with that gap. "
         f"chance = {TOP_Q}/{mean_live:.0f} live qubits.",
         OUT / "overlap_qubits.png")
    plot(cp, ch_p,
         "Best cz pairs: about half agree at 1 day, falling to 43 percent by 30 days",
         f"shared best pairs / {TOP_P}",
         f"each point is the mean over all snapshot pairs with that gap. "
         f"chance = {TOP_P}/{mean_elig:.0f} eligible pairs.",
         OUT / "overlap_pairs.png")

    print("\n=== average overlap at selected gaps ===")
    want = [1, 2, 3, 7, 14, 30]
    tbl = []
    for m in sorted(COLORS):
        row = {"machine": m}
        for gkey, c, lab in ((cq, ch_q, "qubit"), (cp, ch_p, "pair")):
            for g in want:
                hit = gkey[(gkey.machine == m) & (gkey.gap == g)]
                row[f"{lab}_{g}d"] = round(float(hit["mean"].iloc[0]), 3) if len(hit) else None
        tbl.append(row)
    t = pd.DataFrame(tbl)
    qcols = ["machine"] + [f"qubit_{g}d" for g in want]
    pcols = ["machine"] + [f"pair_{g}d" for g in want]
    print("\nbest-10 qubits, shared fraction:")
    print(t[qcols].to_string(index=False))
    print(f"chance level {ch_q:.3f}")
    print("\nbest-20 cz pairs, shared fraction:")
    print(t[pcols].to_string(index=False))
    print(f"chance level {ch_p:.3f}")
    t.to_csv(OUT / "overlap_table.csv", index=False)
    cq.to_csv(OUT / "overlap_curve_qubits.csv", index=False)
    cp.to_csv(OUT / "overlap_curve_pairs.csv", index=False)
    print("\nwrote outputs/overlap_table.csv and the two curve CSVs")


main()
