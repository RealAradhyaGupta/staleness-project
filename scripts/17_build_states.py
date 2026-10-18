"""Distinct calibration states, per decision 3 of 13 October 2026.

Checkpoint 4C found that about three quarters of neighbouring cards hold
exactly the same five fields as the card before them. So a card is not a
measurement, it is a publication. This script collapses a run of neighbouring
cards whose five fields are all exactly equal into one "distinct calibration
state" and keeps the publication time of the first card in the run.

It answers:

1. How many distinct states are there per machine per day? Compare with the
   26 to 32 cards a day from Checkpoint 4A and 4C.
2. For each state, how old were its values when the state was first
   published? Measured per field from the `date` printed on each value, which
   is the primary staleness clock from decision 1. The publication time is
   kept as a secondary column, not as the clock.
3. How many qubits does the Checkpoint 3 dead qubit rule kill in each state,
   and which qubits are dead in EVERY state? Those are permanent defects and
   must be excluded for every strategy, per decision 2.

Dead qubit rule, unchanged from scripts/11_overlap_analysis.py:
    sx_error > 0.1, or readout_error > 0.2, or T1 missing, or T2 missing.

"Same state" means: for all five fields, the same set of qubits or pairs is
present AND every value is exactly equal as a float. Exact equality is the
right test, because the question is whether IBM published a new number.

Window: cards with last_update_date on or after 2026-08-28 UTC, the same
window as Checkpoint 4C. Older cards are counted and skipped.

Writes data/clean/states.csv (one row per state) and prints the summary.
No network calls. data/raw is only read, never written.
"""
import csv
import gzip
import json
import statistics
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
EXPECTED_QUBITS = 156

# Dead qubit rule, same as Checkpoint 3 (scripts/11_overlap_analysis.py).
SX_DEAD = 0.1
RO_DEAD = 0.2


def load(path):
    if path.name.endswith(".gz"):
        with gzip.open(path, "rt") as fh:
            return json.load(fh)
    with open(path) as fh:
        return json.load(fh)


def as_utc(text):
    return datetime.fromisoformat(str(text)).astimezone(timezone.utc)


def read_card(path):
    """One card: value and own date per field, keyed by qubit or pair."""
    data = load(path)
    stamp = as_utc(data["last_update_date"])
    values = {f: {} for f in ALL_FIELDS}
    dates = {f: {} for f in ALL_FIELDS}

    qubit_list = data.get("qubits") or []
    for idx, entries in enumerate(qubit_list):
        for e in entries:
            if e["name"] in QUBIT_FIELDS:
                values[e["name"]][idx] = e["value"]
                dates[e["name"]][idx] = as_utc(e["date"])

    for g in (data.get("gates") or []):
        hit = None
        for p in g["parameters"]:
            if p["name"] == "gate_error":
                hit = p
                break
        if hit is None:
            continue
        if g["gate"] == ONE_Q_GATE and len(g["qubits"]) == 1:
            key = g["qubits"][0]
            values["sx_error"][key] = hit["value"]
            dates["sx_error"][key] = as_utc(hit["date"])
        elif g["gate"] == TWO_Q_GATE and len(g["qubits"]) == 2:
            a, b = g["qubits"]
            key = (min(a, b), max(a, b))
            values["cz_error"][key] = hit["value"]
            dates["cz_error"][key] = as_utc(hit["date"])

    return stamp, values, dates, len(qubit_list)


def same_state(a, b):
    """True if every one of the five fields is exactly equal in a and b."""
    for f in ALL_FIELDS:
        if a[f].keys() != b[f].keys():
            return False
        for k, v in a[f].items():
            if b[f][k] != v:
                return False
    return True


def dead_qubits(values, n_qubits):
    """Checkpoint 3 rule. Returns (dead set, reason counts)."""
    dead = set()
    why = {"sx_gt_0.1": 0, "readout_gt_0.2": 0, "t1_or_t2_missing": 0}
    for idx in range(n_qubits):
        t1 = values["T1"].get(idx)
        t2 = values["T2"].get(idx)
        ro = values["readout_error"].get(idx)
        sx = values["sx_error"].get(idx)
        hit = False
        if t1 is None or t2 is None:
            why["t1_or_t2_missing"] += 1
            hit = True
        if sx is not None and sx > SX_DEAD:
            why["sx_gt_0.1"] += 1
            hit = True
        if ro is not None and ro > RO_DEAD:
            why["readout_gt_0.2"] += 1
            hit = True
        if hit:
            dead.add(idx)
    return dead, why


def median_date(dts):
    secs = sorted(d.timestamp() for d in dts)
    mid = statistics.median(secs)
    return datetime.fromtimestamp(mid, tz=timezone.utc)


def quantile(sorted_vals, q):
    if not sorted_vals:
        return float("nan")
    return sorted_vals[int(round(q * (len(sorted_vals) - 1)))]


def main():
    CLEAN.mkdir(parents=True, exist_ok=True)
    machines = sorted(d.name for d in RAW.iterdir() if d.is_dir())
    rows = []
    outside = defaultdict(int)
    read_fail = []
    always_dead = {}
    dead_ever = {}
    cards_used = {}

    for machine in machines:
        files = sorted(list((RAW / machine).glob("*.json"))
                       + list((RAW / machine).glob("*.json.gz")),
                       key=lambda p: p.name)
        print(f"\n=== {machine}: {len(files)} files on disk ===", flush=True)

        prev_values = None
        state = None          # the open state being extended
        used = 0
        states_here = 0
        never_live = None     # qubits dead in every state so far
        ever_dead = set()

        def close(state):
            rows.append(state)

        for n, path in enumerate(files, 1):
            try:
                stamp, values, dates, n_qubits = read_card(path)
            except Exception as err:
                read_fail.append((str(path), f"{type(err).__name__}: {err}"))
                continue
            if stamp < WINDOW_START:
                outside[machine] += 1
                continue
            used += 1

            if prev_values is not None and same_state(prev_values, values):
                state["n_cards"] += 1
                state["last_card_utc"] = stamp.isoformat()
                prev_values = values
                continue

            # a genuinely new set of numbers starts a new state
            if state is not None:
                close(state)
            states_here += 1

            dead, why = dead_qubits(values, n_qubits)
            if never_live is None:
                never_live = set(dead)
            else:
                never_live &= dead
            ever_dead |= dead

            short = []
            if n_qubits != EXPECTED_QUBITS:
                short.append(f"{n_qubits} qubits")
            for f in ALL_FIELDS:
                if not values[f]:
                    short.append(f"no {f}")
            if values["cz_error"] and len(values["cz_error"]) < 100:
                short.append(f"only {len(values['cz_error'])} cz pairs")

            state = {
                "machine": machine,
                "state_id": states_here,
                "first_seen_utc": stamp.isoformat(),
                "last_card_utc": stamp.isoformat(),
                "n_cards": 1,
                "n_qubits": n_qubits,
                "n_cz_pairs": len(values["cz_error"]),
                "dead_qubits": len(dead),
                "dead_sx_gt_0.1": why["sx_gt_0.1"],
                "dead_readout_gt_0.2": why["readout_gt_0.2"],
                "dead_t1_or_t2_missing": why["t1_or_t2_missing"],
                "dead_qubit_list": " ".join(str(x) for x in sorted(dead)),
                "short_section": "; ".join(short),
            }
            # primary clock: each value's own date
            for f in ALL_FIELDS:
                if not dates[f]:
                    state[f"{f}_n_values"] = 0
                    state[f"{f}_date_median_utc"] = ""
                    state[f"{f}_age_at_first_h"] = ""
                    continue
                ds = list(dates[f].values())
                med = median_date(ds)
                ages = sorted((stamp - d).total_seconds() / 3600.0 for d in ds)
                state[f"{f}_n_values"] = len(ds)
                state[f"{f}_date_median_utc"] = med.isoformat()
                state[f"{f}_age_at_first_h"] = round(
                    statistics.median(ages), 3)
            prev_values = values

            if n % 500 == 0:
                print(f"  ...{n}/{len(files)} files, "
                      f"{states_here} states so far", flush=True)

        if state is not None:
            close(state)
        cards_used[machine] = used
        always_dead[machine] = never_live or set()
        dead_ever[machine] = ever_dead
        print(f"  cards in the window: {used}, older than the window: "
              f"{outside[machine]}, distinct states: {states_here}", flush=True)

    # ---------- write ----------
    out = CLEAN / "states.csv"
    cols = list(rows[0].keys())
    with open(out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    print(f"\nwrote {out} with {len(rows)} rows and {len(cols)} columns")
    if read_fail:
        print(f"FILES THAT WOULD NOT READ: {len(read_fail)}")
        for p, e in read_fail[:10]:
            print(f"  {p}: {e}")

    # ---------- 1: states per machine per day ----------
    print("\n\n=== 1: DISTINCT STATES PER MACHINE PER DAY ===")
    print("a state is a run of cards whose five fields are all exactly equal")
    for machine in machines:
        mine = [r for r in rows if r["machine"] == machine]
        per_day = defaultdict(int)
        for r in mine:
            per_day[r["first_seen_utc"][:10]] += 1
        v = sorted(per_day.values())
        cards = cards_used[machine]
        print(f"\n{machine}: {len(mine)} states from {cards} cards "
              f"({cards/len(mine):.2f} cards per state)")
        print(f"  states per day over {len(v)} days: min {v[0]}, "
              f"median {statistics.median(v):.0f}, p90 {quantile(v,0.90):.0f}, "
              f"max {v[-1]}")
        ncards = sorted(r["n_cards"] for r in mine)
        print(f"  cards per state: min {ncards[0]}, median "
              f"{statistics.median(ncards):.0f}, p90 "
              f"{quantile(ncards,0.90):.0f}, max {ncards[-1]}")
        gaps = []
        for a, b in zip(mine, mine[1:]):
            gaps.append((as_utc(b["first_seen_utc"])
                          - as_utc(a["first_seen_utc"])).total_seconds()/3600)
        gaps.sort()
        print(f"  hours between states: min {gaps[0]:.2f}, median "
              f"{statistics.median(gaps):.2f}, p90 {quantile(gaps,0.90):.2f}, "
              f"max {gaps[-1]:.2f}")
        shorts = [r for r in mine if r["short_section"]]
        print(f"  states whose first card has a short or missing section: "
              f"{len(shorts)}")
        for r in shorts[:6]:
            print(f"    state {r['state_id']} {r['first_seen_utc']} "
                  f"{r['short_section']}")

    # ---------- 2: value age per field, per state ----------
    print("\n\n=== 2: AGE OF A STATE'S VALUES WHEN IT WAS FIRST PUBLISHED ===")
    print("median over qubits or pairs of (first publication - value's own date), hours")
    for machine in machines:
        mine = [r for r in rows if r["machine"] == machine]
        print(f"\n{machine}")
        print(f"  {'field':<15} {'states':>7} {'median':>9} {'p90':>9} "
              f"{'max':>10}")
        for f in ALL_FIELDS:
            v = sorted(r[f"{f}_age_at_first_h"] for r in mine
                       if r[f"{f}_age_at_first_h"] != "")
            if not v:
                print(f"  {f:<15} {'0':>7}  no data")
                continue
            print(f"  {f:<15} {len(v):>7} {statistics.median(v):>9.2f} "
                  f"{quantile(v,0.90):>9.2f} {v[-1]:>10.2f}")

    # ---------- 3: dead qubits ----------
    print("\n\n=== 3: DEAD QUBITS UNDER THE CHECKPOINT 3 RULE, PER STATE ===")
    print(f"rule: sx_error > {SX_DEAD}, or readout_error > {RO_DEAD}, "
          f"or T1 or T2 missing")
    for machine in machines:
        mine = [r for r in rows if r["machine"] == machine]
        v = sorted(r["dead_qubits"] for r in mine)
        print(f"\n{machine}: {len(mine)} states")
        print(f"  dead per state: min {v[0]}, median "
              f"{statistics.median(v):.0f}, p90 {quantile(v,0.90):.0f}, "
              f"max {v[-1]}")
        for col in ["dead_sx_gt_0.1", "dead_readout_gt_0.2",
                    "dead_t1_or_t2_missing"]:
            w = sorted(r[col] for r in mine)
            hit = sum(1 for x in w if x > 0)
            print(f"  {col:<24} median {statistics.median(w):.0f}, "
                  f"max {w[-1]}, states with at least one: {hit} "
                  f"({hit/len(mine)*100:.1f}%)")
        perm = sorted(always_dead[machine])
        ever = sorted(dead_ever[machine])
        print(f"  PERMANENT defects, dead in all {len(mine)} states: "
              f"{len(perm)} qubits {perm}")
        sometimes = [q for q in ever if q not in always_dead[machine]]
        print(f"  dead in some states but not all: {len(sometimes)} qubits "
              f"{sometimes}")
    union = set()
    for m in machines:
        union |= always_dead[m]
    print(f"\nPermanent defects are machine specific. Union across machines "
          f"is {len(union)} qubit indices: {sorted(union)}")
    print("\nNo quantum hardware was used. data/raw was only read.")


main()
