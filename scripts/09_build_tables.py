"""Build data/clean/qubits.csv and data/clean/pairs.csv from data/raw.

Reads only the saved JSON files. No network calls.
qubits.csv: machine, snapshot_utc, qubit, t1_us, t2_us, readout_error, sx_error
pairs.csv:  machine, snapshot_utc, qubit_a, qubit_b, cz_error   (qubit_a < qubit_b)
"""
import csv
import json
from datetime import timezone
from pathlib import Path
from datetime import datetime

RAW = Path("data/raw")
CLEAN = Path("data/clean")
ONE_Q_GATE = "sx"
TWO_Q_GATE = "cz"


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


def main():
    CLEAN.mkdir(parents=True, exist_ok=True)
    q_rows, p_rows = [], []
    asymmetric = 0
    files = sorted(RAW.glob("*/*.json"))
    print(f"reading {len(files)} snapshot files")

    for path in files:
        machine = path.parent.name
        data = json.load(open(path))
        stamp = datetime.fromisoformat(str(data["last_update_date"]))
        snap = stamp.astimezone(timezone.utc).isoformat()

        sx_err = {}
        cz_err = {}
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
            q_rows.append({
                "machine": machine,
                "snapshot_utc": snap,
                "qubit": idx,
                "t1_us": pick(entries, "T1"),
                "t2_us": pick(entries, "T2"),
                "readout_error": pick(entries, "readout_error"),
                "sx_error": sx_err.get(idx),
            })
        for (a, b), err in sorted(cz_err.items()):
            p_rows.append({
                "machine": machine,
                "snapshot_utc": snap,
                "qubit_a": a,
                "qubit_b": b,
                "cz_error": err,
            })

    with open(CLEAN / "qubits.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(q_rows[0].keys()))
        w.writeheader()
        w.writerows(q_rows)
    with open(CLEAN / "pairs.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(p_rows[0].keys()))
        w.writeheader()
        w.writerows(p_rows)

    print(f"qubits.csv rows: {len(q_rows)}")
    print(f"pairs.csv rows:  {len(p_rows)}")
    print(f"cz pairs where the two directions disagreed: {asymmetric}")
    missing_q = sum(1 for r in q_rows if None in r.values())
    missing_p = sum(1 for r in p_rows if None in r.values())
    print(f"rows with a missing value: qubits {missing_q}, pairs {missing_p}")


main()
