"""Part B: what actually changes between neighbouring snapshots?

Two questions, both answered from files already on disk. No network calls.

1. Between a snapshot and the one just before it, how many qubits have a
   different T1, how many a different readout error, and how many cz pairs a
   different gate error?
2. Inside one snapshot, do all the individual property timestamps agree with
   each other and with last_update_date, or do they differ?

Together these say whether a new snapshot is a full re-measurement of the
machine or only a partial update of a few properties.

Usage:
  python scripts/14_neighbour_diff.py [machine] [YYYY-MM-DD]
"""
import glob
import gzip
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

RAW = Path("data/raw")
MACHINE = sys.argv[1] if len(sys.argv) > 1 else "ibm_kingston"
DAY = sys.argv[2] if len(sys.argv) > 2 else None


def load(path):
    if str(path).endswith(".gz"):
        with gzip.open(path, "rt") as fh:
            return json.load(fh)
    with open(path) as fh:
        return json.load(fh)


def to_utc(text):
    return datetime.fromisoformat(str(text)).astimezone(timezone.utc)


def qubit_values(data, prop):
    """{qubit index: value} for a per-qubit property such as T1."""
    out = {}
    for idx, entries in enumerate(data["qubits"]):
        for e in entries:
            if e["name"] == prop:
                out[idx] = e["value"]
    return out


def qubit_dates(data, prop):
    out = {}
    for idx, entries in enumerate(data["qubits"]):
        for e in entries:
            if e["name"] == prop:
                out[idx] = to_utc(e["date"])
    return out


def cz_values(data):
    out = {}
    for g in data["gates"]:
        if g["gate"] == "cz" and len(g["qubits"]) == 2:
            a, b = g["qubits"]
            for p in g["parameters"]:
                if p["name"] == "gate_error":
                    out[(min(a, b), max(a, b))] = p["value"]
    return out


def cz_dates(data):
    out = {}
    for g in data["gates"]:
        if g["gate"] == "cz" and len(g["qubits"]) == 2:
            a, b = g["qubits"]
            for p in g["parameters"]:
                if p["name"] == "gate_error":
                    out[(min(a, b), max(a, b))] = to_utc(p["date"])
    return out


def n_changed(old, new):
    keys = set(old) & set(new)
    return sum(1 for k in keys if old[k] != new[k]), len(keys)


def main():
    pattern = f"{DAY}*" if DAY else "*"
    files = sorted(glob.glob(str(RAW / MACHINE / f"{pattern}.json"))
                   + glob.glob(str(RAW / MACHINE / f"{pattern}.json.gz")))
    if len(files) < 2:
        print(f"need at least 2 snapshots, found {len(files)} for "
              f"{MACHINE} {DAY or '(all days)'}")
        return

    print(f"machine: {MACHINE}")
    print(f"day: {DAY or 'all days on disk'}")
    print(f"snapshots: {len(files)}\n")

    # ---------- question 1: neighbour to neighbour ----------
    print("=== change from the previous snapshot ===")
    print(f"{'snapshot (UTC)':22} {'gap h':>6} {'T1 chg':>8} {'RO chg':>8} "
          f"{'cz chg':>8}  of 156/{'pairs':>5}")
    prev = None
    prev_stamp = None
    rows = []
    for path in files:
        data = load(path)
        stamp = to_utc(data["last_update_date"])
        if prev is not None:
            t1_c, t1_n = n_changed(qubit_values(prev, "T1"),
                                   qubit_values(data, "T1"))
            ro_c, ro_n = n_changed(qubit_values(prev, "readout_error"),
                                   qubit_values(data, "readout_error"))
            cz_c, cz_n = n_changed(cz_values(prev), cz_values(data))
            gap = (stamp - prev_stamp).total_seconds() / 3600
            print(f"{stamp.strftime('%Y-%m-%d %H:%M:%S'):22} {gap:6.2f} "
                  f"{t1_c:8d} {ro_c:8d} {cz_c:8d}  {t1_n:3d}/{cz_n:5d}")
            rows.append((t1_c, t1_n, ro_c, ro_n, cz_c, cz_n))
        prev, prev_stamp = data, stamp

    if rows:
        n = len(rows)
        print(f"\n  comparisons: {n}")
        for label, ci, ni in (("T1", 0, 1), ("readout_error", 2, 3), ("cz error", 4, 5)):
            vals = sorted(r[ci] for r in rows)
            total = rows[0][ni]
            pct = 100.0 * sum(vals) / (n * total) if total else 0
            print(f"  {label:14}: changed min {vals[0]}, median "
                  f"{vals[n//2]}, max {vals[-1]}  out of {total}  "
                  f"({pct:.1f}% of values on average)")
            unchanged = sum(1 for v in vals if v == 0)
            print(f"  {'':14}  comparisons with nothing changed: {unchanged}/{n}")

    # ---------- question 2: timestamps inside one snapshot ----------
    print("\n=== timestamps inside a single snapshot ===")
    for path in files[-1:] if len(files) == 1 else [files[len(files) // 2], files[-1]]:
        data = load(path)
        stamp = to_utc(data["last_update_date"])
        print(f"\nsnapshot {stamp.strftime('%Y-%m-%d %H:%M:%S')} UTC  "
              f"({Path(path).name})")
        print(f"  last_update_date: {stamp.strftime('%Y-%m-%d %H:%M:%S')} UTC")
        all_dates = []
        for prop in ("T1", "T2", "readout_error", "init_error"):
            d = qubit_dates(data, prop)
            if not d:
                continue
            vals = sorted(d.values())
            all_dates += vals
            uniq = len(set(vals))
            age_h = (stamp - vals[0]).total_seconds() / 3600
            print(f"  {prop:14}: {uniq:4d} distinct times across {len(vals)} qubits, "
                  f"oldest {vals[0].strftime('%m-%d %H:%M')}, "
                  f"newest {vals[-1].strftime('%m-%d %H:%M')}, "
                  f"oldest is {age_h:.1f} h before last_update_date")
        d = cz_dates(data)
        vals = sorted(d.values())
        all_dates += vals
        age_h = (stamp - vals[0]).total_seconds() / 3600
        print(f"  {'cz gate_error':14}: {len(set(vals)):4d} distinct times across "
              f"{len(vals)} pairs, oldest {vals[0].strftime('%m-%d %H:%M')}, "
              f"newest {vals[-1].strftime('%m-%d %H:%M')}, "
              f"oldest is {age_h:.1f} h before last_update_date")
        a = sorted(all_dates)
        print(f"  ALL properties: {len(set(a))} distinct timestamps, spread "
              f"{(a[-1] - a[0]).total_seconds() / 3600:.1f} h "
              f"({a[0].strftime('%m-%d %H:%M')} to {a[-1].strftime('%m-%d %H:%M')})")
        same = sum(1 for x in a if x == stamp)
        print(f"  properties whose date equals last_update_date: {same} of {len(a)}")
        by_day = Counter(x.date().isoformat() for x in a)
        print(f"  measurement dates present: "
              f"{', '.join(f'{k} ({v})' for k, v in sorted(by_day.items()))}")


main()
