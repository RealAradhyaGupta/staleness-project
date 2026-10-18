"""Merge the part files of a run into all_rows.csv, the same way the runner does.

OURS. The frozen runner merges at the end of its own main(), and that merge
never ran for the test period because two workers died (L-037). This does the
same merge: read every part_*.csv, sort by machine, draw order, delay,
circuit and arm, write all_rows.csv. It also reports how many jobs are
present, so a short file cannot be mistaken for a complete one.

Usage: 22_merge_parts.py test_full
"""
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
ARMS = ["random", "stale", "window_mean", "std_adjusted", "shrinkage",
        "ceiling"]


def main():
    out_dir = ROOT / "outputs" / sys.argv[1]
    parts = sorted(p for p in out_dir.glob("part_*.csv"))
    frames = []
    for p in parts:
        d = pd.read_csv(p)
        print(f"  {p.name}: {len(d)} rows")
        frames.append(d)
    df = pd.concat(frames, ignore_index=True)
    keys = ["machine", "draw_order", "delay_h", "circuit", "arm"]
    df.sort_values(keys, inplace=True)
    dup = df.duplicated(subset=keys).sum()
    jobs = df.groupby(keys[:-1]).size()
    print(f"total rows {len(df)}, jobs {len(jobs)}, duplicate rows {dup}")
    print(f"jobs with all {len(ARMS)} arms: {(jobs == len(ARMS)).sum()}, "
          f"jobs with fewer: {(jobs != len(ARMS)).sum()}")
    assert dup == 0, "duplicate rows: a part file was written twice"
    merged = out_dir / "all_rows.csv"
    df.to_csv(merged, index=False)
    print(f"wrote {merged}")


if __name__ == "__main__":
    main()
