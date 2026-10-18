"""Part C: rebuild data/clean/qubits.csv and pairs.csv from EVERY snapshot.

Reads every snapshot on disk, plain .json and gzipped .json.gz alike, and
streams the rows straight to the CSV files so memory stays small. The old
tables are copied to *_pre_all.csv.bak first and never deleted.

Then prints the summary: snapshots per machine per day (min, median, max),
the biggest gaps between neighbouring snapshots and when they happened, and
the total size on disk.

Same columns as before, so existing analysis scripts keep working.
No network calls.
"""
import csv
import gzip
import json
import shutil
import statistics
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

RAW = Path("data/raw")
CLEAN = Path("data/clean")
ONE_Q_GATE = "sx"
TWO_Q_GATE = "cz"


def load(path):
    if path.name.endswith(".gz"):
        with gzip.open(path, "rt") as fh:
            return json.load(fh)
    with open(path) as fh:
        return json.load(fh)


def pick(entries, key):
    for e in entries:
        if e["name"] == key:
            return e["value"]
    return None


def gate_error(params):
    for p in params:
        if p["name"] == "gate_error":
            return p["value"]
    return None


def backup_old():
    for name in ("qubits.csv", "pairs.csv"):
        src = CLEAN / name
        if src.exists():
            dst = CLEAN / (name.replace(".csv", "_pre_all.csv.bak"))
            if dst.exists():
                print(f"  backup already exists, keeping it: {dst.name}")
            else:
                shutil.copy2(src, dst)
                print(f"  backed up {name} -> {dst.name}")


def main():
    CLEAN.mkdir(parents=True, exist_ok=True)
    print("=== backups ===")
    backup_old()

    files = sorted(list(RAW.glob("*/*.json")) + list(RAW.glob("*/*.json.gz")),
                   key=lambda p: (p.parent.name, p.name))
    print(f"\n=== reading {len(files)} snapshot files ===")

    q_fields = ["machine", "snapshot_utc", "qubit", "t1_us", "t2_us",
                "readout_error", "sx_error"]
    p_fields = ["machine", "snapshot_utc", "qubit_a", "qubit_b", "cz_error"]

    q_rows = p_rows = 0
    q_missing = p_missing = 0
    asymmetric = 0
    duplicate_stamps = 0
    stamps = defaultdict(set)      # machine -> set of snapshot times
    raw_bytes = 0

    with open(CLEAN / "qubits.csv", "w", newline="") as qf, \
         open(CLEAN / "pairs.csv", "w", newline="") as pf:
        qw = csv.DictWriter(qf, fieldnames=q_fields)
        pw = csv.DictWriter(pf, fieldnames=p_fields)
        qw.writeheader()
        pw.writeheader()

        for n, path in enumerate(files, 1):
            machine = path.parent.name
            raw_bytes += path.stat().st_size
            data = load(path)
            stamp = datetime.fromisoformat(
                str(data["last_update_date"])).astimezone(timezone.utc)
            if stamp in stamps[machine]:
                duplicate_stamps += 1
                continue
            stamps[machine].add(stamp)
            snap = stamp.isoformat()

            sx_err, cz_err = {}, {}
            for g in data["gates"]:
                if g["gate"] == ONE_Q_GATE and len(g["qubits"]) == 1:
                    sx_err[g["qubits"][0]] = gate_error(g["parameters"])
                elif g["gate"] == TWO_Q_GATE and len(g["qubits"]) == 2:
                    a, b = g["qubits"]
                    key = (min(a, b), max(a, b))
                    err = gate_error(g["parameters"])
                    if key in cz_err and cz_err[key] != err:
                        asymmetric += 1
                    cz_err[key] = err

            for idx, entries in enumerate(data["qubits"]):
                row = {
                    "machine": machine,
                    "snapshot_utc": snap,
                    "qubit": idx,
                    "t1_us": pick(entries, "T1"),
                    "t2_us": pick(entries, "T2"),
                    "readout_error": pick(entries, "readout_error"),
                    "sx_error": sx_err.get(idx),
                }
                if None in row.values():
                    q_missing += 1
                qw.writerow(row)
                q_rows += 1

            for (a, b), err in sorted(cz_err.items()):
                row = {"machine": machine, "snapshot_utc": snap,
                       "qubit_a": a, "qubit_b": b, "cz_error": err}
                if None in row.values():
                    p_missing += 1
                pw.writerow(row)
                p_rows += 1

            if n % 500 == 0:
                print(f"  ...{n}/{len(files)} files")

    print(f"\n=== tables ===")
    print(f"qubits.csv rows: {q_rows}   ({(CLEAN/'qubits.csv').stat().st_size/1048576:.1f} MB)")
    print(f"pairs.csv rows:  {p_rows}   ({(CLEAN/'pairs.csv').stat().st_size/1048576:.1f} MB)")
    print(f"rows with a missing value: qubits {q_missing}, pairs {p_missing}")
    print(f"cz pairs where the two directions disagreed: {asymmetric}")
    print(f"files skipped as a repeated timestamp: {duplicate_stamps}")

    # ---------- summary ----------
    print(f"\n=== snapshots per machine ===")
    for machine in sorted(stamps):
        per_day = defaultdict(int)
        for s in stamps[machine]:
            per_day[s.date().isoformat()] += 1
        counts = sorted(per_day.values())
        print(f"\n{machine}: {len(stamps[machine])} snapshots over "
              f"{len(per_day)} days")
        print(f"  per day: min {counts[0]}, median "
              f"{statistics.median(counts):.0f}, max {counts[-1]}")
        # only the dense window tells us the true cadence
        dense = sorted(v for k, v in per_day.items() if k >= "2026-08-28")
        if dense:
            print(f"  per day inside 2026-08-28 onwards: min {dense[0]}, "
                  f"median {statistics.median(dense):.0f}, max {dense[-1]}")
        days_low = sorted(k for k, v in per_day.items()
                          if v <= 2 and k >= "2026-08-28")
        if days_low:
            print(f"  days in the window with 2 or fewer snapshots: "
                  f"{len(days_low)} -> {', '.join(days_low[:10])}"
                  f"{' ...' if len(days_low) > 10 else ''}")

    print(f"\n=== biggest gaps between neighbouring snapshots ===")
    for machine in sorted(stamps):
        ordered = sorted(stamps[machine])
        gaps = [(ordered[i + 1] - ordered[i], ordered[i], ordered[i + 1])
                for i in range(len(ordered) - 1)]
        in_window = [g for g in gaps if g[1].date().isoformat() >= "2026-08-28"]
        print(f"\n{machine}")
        if in_window:
            hrs = sorted(g[0].total_seconds() / 3600 for g in in_window)
            print(f"  gap hours inside the window: min {hrs[0]:.2f}, median "
                  f"{statistics.median(hrs):.2f}, max {hrs[-1]:.2f}")
        for gap, a, b in sorted(gaps, key=lambda g: -g[0].total_seconds())[:5]:
            print(f"  {gap.total_seconds()/3600:8.2f} h  from "
                  f"{a.strftime('%Y-%m-%d %H:%M')} to {b.strftime('%Y-%m-%d %H:%M')} UTC")

    total = sum(len(v) for v in stamps.values())
    print(f"\n=== total size ===")
    print(f"distinct snapshots used: {total}")
    print(f"data/raw on disk: {raw_bytes/1048576:.1f} MB")
    clean_bytes = sum(f.stat().st_size for f in CLEAN.glob("*"))
    print(f"data/clean on disk: {clean_bytes/1048576:.1f} MB "
          f"(includes the .bak backups)")


main()
