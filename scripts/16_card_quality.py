"""Part D: what is really inside each calibration card, and what changes.

Three questions, all read-only, all over the snapshots already on disk:

1. Full or partial update. For every neighbouring pair of cards on a machine,
   what share of qubits (or cz pairs) had a changed number for each field?
   A share near 1 means IBM republished the whole field, a share of 0 means
   the field was copied over untouched.

2. Age of the values inside a card. Every value carries its own date. The age
   is the card's last_update_date minus that date. A card is not as fresh as
   its own timestamp suggests.

3. Unusable qubits and broken cards. How many qubits in a card have a missing
   or useless number, and how many cards are missing a section or are short.

"Changed" means the float is not exactly equal, which is the right test for
"did IBM publish this number again".

Window: cards with last_update_date on or after 2026-08-28 UTC. Cards older
than that are counted and skipped, so the 45 day answers are not polluted by
the sparse Checkpoint 2 history.

Writes data/clean/card_quality.csv (one row per card) and prints the summary.
No network calls. data/raw is only read.
"""
import csv
import gzip
import json
import statistics
from array import array
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

RAW = Path("data/raw")
CLEAN = Path("data/clean")
WINDOW_START = datetime(2026, 8, 28, 0, 0, 0, tzinfo=timezone.utc)
ONE_Q_GATE = "sx"
TWO_Q_GATE = "cz"
QUBIT_FIELDS = ["T1", "T2", "readout_error"]
ALL_FIELDS = ["T1", "T2", "readout_error", "sx_error", "cz_error"]
NEARLY_ALL = 0.95        # "almost all changed" means this share or more
EXPECTED_QUBITS = 156    # all three machines are the same generation


def load(path):
    if path.name.endswith(".gz"):
        with gzip.open(path, "rt") as fh:
            return json.load(fh)
    with open(path) as fh:
        return json.load(fh)


def read_card(path):
    """Pull out one card as plain dicts: value and own date, per field."""
    data = load(path)
    stamp = datetime.fromisoformat(
        str(data["last_update_date"])).astimezone(timezone.utc)

    values = {f: {} for f in ALL_FIELDS}
    ages = {f: [] for f in ALL_FIELDS}     # hours, one per qubit or pair

    def age_hours(entry):
        d = datetime.fromisoformat(str(entry["date"])).astimezone(timezone.utc)
        return (stamp - d).total_seconds() / 3600.0

    qubit_list = data.get("qubits") or []
    for idx, entries in enumerate(qubit_list):
        for e in entries:
            if e["name"] in QUBIT_FIELDS:
                values[e["name"]][idx] = e["value"]
                ages[e["name"]].append(age_hours(e))

    gate_list = data.get("gates") or []
    for g in gate_list:
        err = None
        err_entry = None
        for p in g["parameters"]:
            if p["name"] == "gate_error":
                err, err_entry = p["value"], p
                break
        if err_entry is None:
            continue
        if g["gate"] == ONE_Q_GATE and len(g["qubits"]) == 1:
            values["sx_error"][g["qubits"][0]] = err
            ages["sx_error"].append(age_hours(err_entry))
        elif g["gate"] == TWO_Q_GATE and len(g["qubits"]) == 2:
            a, b = g["qubits"]
            values["cz_error"][(min(a, b), max(a, b))] = err
            ages["cz_error"].append(age_hours(err_entry))

    return stamp, values, ages, len(qubit_list), len(gate_list)


def quantile(sorted_vals, q):
    if not sorted_vals:
        return float("nan")
    i = int(round(q * (len(sorted_vals) - 1)))
    return sorted_vals[i]


def main():
    CLEAN.mkdir(parents=True, exist_ok=True)
    machines = sorted(d.name for d in RAW.iterdir() if d.is_dir())

    # per machine, per field: one share per neighbouring pair
    shares = {m: {f: [] for f in ALL_FIELDS} for m in machines}
    # per machine: neighbouring pairs where not one of the 5 fields moved
    frozen = {m: [0, 0] for m in machines}      # [frozen pairs, total pairs]
    # per machine, per field: every age in hours
    ages_all = {m: {f: array("d") for f in ALL_FIELDS} for m in machines}
    # per card counts
    rows = []
    broken = defaultdict(list)       # machine -> list of (stamp, why)
    outside = defaultdict(int)
    read_fail = []

    for machine in machines:
        files = sorted(list((RAW / machine).glob("*.json"))
                       + list((RAW / machine).glob("*.json.gz")),
                       key=lambda p: p.name)
        print(f"\n=== {machine}: {len(files)} files on disk ===", flush=True)
        prev = None
        used = 0
        for n, path in enumerate(files, 1):
            try:
                stamp, values, ages, n_qubits, n_gates = read_card(path)
            except Exception as err:
                read_fail.append((str(path), f"{type(err).__name__}: {err}"))
                continue
            if stamp < WINDOW_START:
                outside[machine] += 1
                continue
            used += 1

            # --- item 3: ages inside this card
            for f in ALL_FIELDS:
                ages_all[machine][f].extend(ages[f])

            # --- item 4: unusable qubits and missing sections
            missing_val = 0
            bad_t = 0
            bad_ro = 0
            bad_sx = 0
            sx_exactly_one = 0
            for idx in range(n_qubits):
                vals = {f: values[f].get(idx) for f in
                        ["T1", "T2", "readout_error", "sx_error"]}
                if any(v is None for v in vals.values()):
                    missing_val += 1
                    continue
                if vals["T1"] <= 0 or vals["T2"] <= 0:
                    bad_t += 1
                if vals["readout_error"] >= 0.5:
                    bad_ro += 1
                if vals["sx_error"] >= 0.5:
                    bad_sx += 1
                if vals["sx_error"] == 1.0:
                    sx_exactly_one += 1

            why = []
            if not values["T1"]:
                why.append("no qubits section")
            if not values["cz_error"]:
                why.append("no cz gates")
            if n_qubits != EXPECTED_QUBITS:
                why.append(f"{n_qubits} qubits not {EXPECTED_QUBITS}")
            for f in ["T1", "T2", "readout_error", "sx_error"]:
                if values[f] and len(values[f]) != n_qubits:
                    why.append(f"{f} only on {len(values[f])}/{n_qubits} qubits")
            if why:
                broken[machine].append((stamp, "; ".join(why)))

            rows.append({
                "machine": machine,
                "snapshot_utc": stamp.isoformat(),
                "n_qubits": n_qubits,
                "n_gates": n_gates,
                "n_cz_pairs": len(values["cz_error"]),
                "qubits_missing_a_value": missing_val,
                "qubits_t1_or_t2_not_positive": bad_t,
                "qubits_readout_error_ge_0.5": bad_ro,
                "qubits_sx_error_ge_0.5": bad_sx,
                "qubits_sx_error_exactly_1": sx_exactly_one,
                "problems": "; ".join(why),
            })

            # --- item 2: compare with the card right before it
            if prev is not None:
                moved = False
                for f in ALL_FIELDS:
                    a, b = prev[f], values[f]
                    both = [k for k in b if k in a]
                    if not both:
                        continue
                    changed = sum(1 for k in both if a[k] != b[k])
                    shares[machine][f].append(changed / len(both))
                    if changed:
                        moved = True
                frozen[machine][1] += 1
                if not moved:
                    frozen[machine][0] += 1
            prev = values

            if n % 500 == 0:
                print(f"  ...{n}/{len(files)} files", flush=True)
        print(f"  cards used in the window: {used}, "
              f"older than the window: {outside[machine]}", flush=True)

    # ---------- write the per card table ----------
    out = CLEAN / "card_quality.csv"
    with open(out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"\nwrote {out} with {len(rows)} rows")
    if read_fail:
        print(f"FILES THAT WOULD NOT READ: {len(read_fail)}")
        for p, e in read_fail[:10]:
            print(f"  {p}: {e}")

    # ---------- item 2 ----------
    print("\n\n=== ITEM 2: full or partial updates, all neighbouring pairs ===")
    print("share of qubits or pairs whose number changed between neighbours")
    for machine in machines:
        print(f"\n{machine}")
        print(f"  {'field':<15} {'pairs':>6} {'median':>8} "
              f"{'none changed':>13} {'>=95% changed':>14}")
        for f in ALL_FIELDS:
            v = sorted(shares[machine][f])
            if not v:
                print(f"  {f:<15} {'0':>6}  no data")
                continue
            zero = sum(1 for x in v if x == 0.0) / len(v)
            most = sum(1 for x in v if x >= NEARLY_ALL) / len(v)
            print(f"  {f:<15} {len(v):>6} {statistics.median(v):>8.3f} "
                  f"{zero*100:>12.1f}% {most*100:>13.1f}%")

        # the median above is 0 because most neighbours change nothing, so
        # also report what happens on the pairs where the field did move
        print(f"\n  when the field did move, how much of it moved:")
        print(f"  {'field':<15} {'pairs moved':>12} {'median share':>13} "
              f"{'of those >=90%':>15}")
        for f in ALL_FIELDS:
            nz = sorted(x for x in shares[machine][f] if x > 0.0)
            if not nz:
                print(f"  {f:<15} {'0':>12}  never moved")
                continue
            big = sum(1 for x in nz if x >= 0.90) / len(nz)
            print(f"  {f:<15} {len(nz):>12} {statistics.median(nz):>13.3f} "
                  f"{big*100:>14.1f}%")
        fz, tot = frozen[machine]
        print(f"\n  neighbouring pairs where not one of the 5 fields moved: "
              f"{fz} of {tot} ({fz/tot*100:.1f}%)")

    # ---------- item 3 ----------
    print("\n\n=== ITEM 3: age of each value inside its own card, hours ===")
    print("card last_update_date minus the date printed on the value itself")
    for machine in machines:
        print(f"\n{machine}")
        print(f"  {'field':<15} {'values':>9} {'median':>9} {'p90':>9} {'max':>10}")
        for f in ALL_FIELDS:
            v = sorted(ages_all[machine][f])
            if not v:
                print(f"  {f:<15} {'0':>9}  no data")
                continue
            print(f"  {f:<15} {len(v):>9} {statistics.median(v):>9.2f} "
                  f"{quantile(v, 0.90):>9.2f} {v[-1]:>10.2f}")

    # ---------- item 4 ----------
    print("\n\n=== ITEM 4: unusable qubits per card, and broken cards ===")
    count_cols = ["qubits_missing_a_value", "qubits_t1_or_t2_not_positive",
                  "qubits_readout_error_ge_0.5", "qubits_sx_error_ge_0.5",
                  "qubits_sx_error_exactly_1"]
    for machine in machines:
        mine = [r for r in rows if r["machine"] == machine]
        print(f"\n{machine}: {len(mine)} cards in the window")
        for col in count_cols:
            v = sorted(r[col] for r in mine)
            if not v:
                continue
            cards_hit = sum(1 for x in v if x > 0)
            print(f"  {col:<32} per card: min {v[0]}, median "
                  f"{statistics.median(v):.0f}, max {v[-1]}; "
                  f"cards with at least one: {cards_hit} "
                  f"({cards_hit/len(mine)*100:.1f}%)")
        pairs = sorted(r["n_cz_pairs"] for r in mine)
        print(f"  {'cz pairs present':<32} per card: min {pairs[0]}, median "
              f"{statistics.median(pairs):.0f}, max {pairs[-1]}")
        bad = broken[machine]
        print(f"  cards with a missing or short section: {len(bad)}")
        for stamp, why in bad[:10]:
            print(f"    {stamp.isoformat()}  {why}")
        if len(bad) > 10:
            print(f"    ... and {len(bad)-10} more, see card_quality.csv")


main()
