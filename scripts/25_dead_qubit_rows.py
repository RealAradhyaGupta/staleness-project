"""Count the rows where an arm chose a qubit its own card called alive but the
truth device calls dead.

OURS. DESCRIPTIVE ONLY. No test, no interval, no claim. The column
`dead_qubits_used` is written by the engine per row: it lists the qubits in
that row's chosen layout that are dead under the TRUTH state. A value can only
appear there if the arm's own card said the qubit was alive, because
PROTOCOL.md section 7 forbids every arm from picking a qubit its own card
calls dead, and L-038 recorded that the assertion never fired in 33888 rows.

Usage:  25_dead_qubit_rows.py [--results ...] [--outdir outputs/prereg]
"""
import argparse
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
ARMS = ["random", "stale", "window_mean", "std_adjusted", "shrinkage", "ceiling"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default=str(ROOT / "outputs/test_full/all_rows.csv"))
    ap.add_argument("--outdir", default=str(ROOT / "outputs/prereg"))
    args = ap.parse_args()
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(args.results)
    df["dead_str"] = df.dead_qubits_used.fillna("").astype(str).str.strip()
    hit = df[df.dead_str != ""].copy()
    hit["n_dead_used"] = hit.dead_str.str.split().apply(len)

    print("ROWS WHERE AN ARM USED A QUBIT THE TRUTH DEVICE CALLS DEAD")
    print("DESCRIPTIVE ONLY. Counts, not a result. No interval and no test.")
    print(f"source: {args.results}")
    print(f"\ntotal rows {len(df)}   rows with at least one such qubit "
          f"{len(hit)}   share {len(hit)/len(df)*100:.2f}%")
    print(f"distinct jobs touched: "
          f"{hit.groupby(['machine','draw_order','delay_h','circuit']).ngroups}")
    print("\nEvery one of these is a qubit the arm's OWN card called alive. No "
          "arm ever used a\nqubit its own card called dead; L-038 recorded "
          "that assertion never firing.")

    print("\n" + "=" * 64)
    print("1. BY ARM")
    print("=" * 64)
    by_arm = (hit.groupby("arm")
              .agg(rows=("arm", "size"),
                   qubit_instances=("n_dead_used", "sum"),
                   mean_per_row=("n_dead_used", "mean"),
                   max_in_one_row=("n_dead_used", "max"))
              .reindex([a for a in ARMS if a in set(hit.arm)]))
    by_arm["rows_of_5648"] = by_arm.rows
    by_arm["share_of_arm_rows_pct"] = (
        by_arm.rows / df.groupby("arm").size().reindex(by_arm.index) * 100)
    print(by_arm.round(3).to_string())
    by_arm.round(6).to_csv(outdir / "D1_dead_qubit_rows_by_arm.csv")

    print("\n" + "=" * 64)
    print("2. BY DELAY")
    print("=" * 64)
    by_D = (hit.groupby("delay_h")
            .agg(rows=("delay_h", "size"),
                 qubit_instances=("n_dead_used", "sum")))
    by_D["all_rows_at_this_delay"] = df.groupby("delay_h").size()
    by_D["share_pct"] = by_D.rows / by_D.all_rows_at_this_delay * 100
    print(by_D.round(3).to_string())
    by_D.round(6).to_csv(outdir / "D2_dead_qubit_rows_by_delay.csv")

    print("\n" + "=" * 64)
    print("3. BY ARM AND DELAY, rows")
    print("=" * 64)
    tab = (hit.pivot_table(index="delay_h", columns="arm", values="dead_str",
                           aggfunc="size")
           .reindex(columns=[a for a in ARMS if a in set(hit.arm)])
           .fillna(0).astype(int))
    tab["all arms"] = tab.sum(axis=1)
    print(tab.to_string())
    tab.to_csv(outdir / "D3_dead_qubit_rows_by_arm_and_delay.csv")

    print("\n" + "=" * 64)
    print("4. BY ARM AND DELAY, excluding the random arm")
    print("=" * 64)
    print("The random arm dominates every total, so the informed arms are "
          "shown alone too.")
    cols = [c for c in tab.columns if c not in ("random", "all arms")]
    t2 = tab[cols].copy()
    t2["informed arms"] = t2.sum(axis=1)
    print(t2.to_string())
    t2.to_csv(outdir / "D4_dead_qubit_rows_informed_arms.csv")

    print("\n" + "=" * 64)
    print("5. BY MACHINE AND ARM, rows")
    print("=" * 64)
    tm = (hit.pivot_table(index="machine", columns="arm", values="dead_str",
                          aggfunc="size")
          .reindex(columns=[a for a in ARMS if a in set(hit.arm)])
          .fillna(0).astype(int))
    tm["all arms"] = tm.sum(axis=1)
    print(tm.to_string())
    tm.to_csv(outdir / "D5_dead_qubit_rows_by_machine_and_arm.csv")

    print("\n" + "=" * 64)
    print("6. HOW MANY NEW STATES THE JOB CROSSED")
    print("=" * 64)
    b = hit.new_states.clip(upper=2).map({0: "0", 1: "1", 2: "2 or more"})
    print(hit.groupby([b, "arm"]).size().unstack(fill_value=0)
          .reindex(columns=[a for a in ARMS if a in set(hit.arm)]).to_string())
    (hit.groupby([b, "arm"]).size().unstack(fill_value=0)
     .to_csv(outdir / "D6_dead_qubit_rows_by_new_states.csv"))

    print("\n" + "=" * 64)
    print("7. THE CEILING ARM")
    print("=" * 64)
    nc = int((hit.arm == "ceiling").sum())
    print(f"rows where the CEILING used a truth-dead qubit: {nc}")
    print("The ceiling reads the truth state itself, so it should be 0 by "
          "construction:\nit cannot pick a qubit its own card calls dead, and "
          "its own card IS the truth card.")

    print("\nfiles written to " + str(outdir))


main()
