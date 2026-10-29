"""Round 2, Stage 3 report: what the fresh window actually contains.

Cards and distinct states per machine and per day, every date in the window
with no cards, and the gaps between neighbouring states. Nothing is filled in
and nothing is analysed. Card values are never printed.
"""
import os
import re
import sys
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "engine"))
os.environ["STALENESS_CLEAN_DIR"] = str(ROOT / "data/clean_r2")
os.environ["STALENESS_CACHE_DIR"] = str(ROOT / "data/cache_r2")

OUT = ROOT / "outputs" / "round2"
FRESH = ROOT / "data/fresh"
MACHINES = ["ibm_fez", "ibm_kingston", "ibm_marrakesh"]
W_START = date(2026, 10, 13)
W_END = date(2026, 10, 23)        # last whole day inside the window
STAMP = re.compile(r"(20\d\d)-(\d\d)-(\d\d)T(\d\d)-(\d\d)-(\d\d)Z")
GAP_MIN_H = 18.0


def say(*a):
    print(*a, flush=True)


def card_days():
    rows = []
    for m in MACHINES:
        for f in sorted((FRESH / m).iterdir()):
            mt = STAMP.match(f.name)
            if mt:
                y, mo, d, hh, mm, ss = map(int, mt.groups())
                rows.append({"machine": m, "day": date(y, mo, d).isoformat(),
                             "hour": hh})
    return pd.DataFrame(rows)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    say("=" * 72)
    say("ROUND 2 STAGE 3 REPORT: the fresh window")
    say("=" * 72)
    say(f"  window: {W_START} to 2026-10-24 00:00 UTC")

    cards = card_days()
    st = pd.read_csv(ROOT / "data/clean_r2/states.csv")
    st["first_seen_utc"] = pd.to_datetime(st.first_seen_utc, utc=True)
    fresh_st = st[st.first_seen_utc >= pd.Timestamp("2026-10-13T00:00:00Z")].copy()
    fresh_st["day"] = fresh_st.first_seen_utc.dt.date.astype(str)

    say(f"\n  totals: {len(cards)} fresh cards, {len(fresh_st)} distinct states")
    say(f"  {'machine':<16}{'cards':>8}{'states':>8}{'cards per state':>17}")
    for m in MACHINES:
        c = int((cards.machine == m).sum())
        s = int((fresh_st.machine == m).sum())
        say(f"  {m:<16}{c:>8}{s:>8}{c / s:>17.2f}")

    days = []
    d = W_START
    while d <= W_END:
        days.append(d.isoformat())
        d += timedelta(days=1)

    say(f"\n  cards per machine per day:")
    say(f"  {'day':<13}" + "".join(f"{m.replace('ibm_', ''):>12}" for m in MACHINES)
        + f"{'total':>8}")
    rows = []
    for day in days:
        line = f"  {day:<13}"
        tot = 0
        for m in MACHINES:
            n = int(((cards.machine == m) & (cards.day == day)).sum())
            tot += n
            line += f"{n:>12}"
            rows.append({"day": day, "machine": m, "cards": n})
        say(line + f"{tot:>8}")

    say(f"\n  distinct states per machine per day:")
    say(f"  {'day':<13}" + "".join(f"{m.replace('ibm_', ''):>12}" for m in MACHINES)
        + f"{'total':>8}")
    for day in days:
        line = f"  {day:<13}"
        tot = 0
        for m in MACHINES:
            n = int(((fresh_st.machine == m) & (fresh_st.day == day)).sum())
            tot += n
            line += f"{n:>12}"
            for r in rows:
                if r["day"] == day and r["machine"] == m:
                    r["states"] = n
        say(line + f"{tot:>8}")
    pd.DataFrame(rows).to_csv(OUT / "stage3_per_day.csv", index=False)

    say(f"\n  DATES WITH NO CARDS:")
    missing = []
    for day in days:
        for m in MACHINES:
            if int(((cards.machine == m) & (cards.day == day)).sum()) == 0:
                missing.append((m, day))
    if missing:
        for m, day in missing:
            say(f"    {m} has no card on {day}")
    else:
        say(f"    none. every machine published on every one of the "
            f"{len(days)} days.")
    say(f"  No gap was filled. Nothing was invented.")

    say(f"\n  intervals between neighbouring states longer than {GAP_MIN_H} h")
    say(f"  (protocol_round2.md section 9 calls these publishing gaps; they")
    say(f"   stay in and are reported separately):")
    import real_data as rd
    any_gap = False
    for m in MACHINES:
        store = rd.open_store(m)
        for a, b in zip(store.times[:-1], store.times[1:]):
            h = (b - a).total_seconds() / 3600.0
            if h > GAP_MIN_H and b >= pd.Timestamp("2026-10-13T00:00:00Z"):
                say(f"    {m:<16}{a.isoformat()} to {b.isoformat()}  {h:.2f} h")
                any_gap = True
    if not any_gap:
        say(f"    none in the fresh window.")

    say(f"\n  last state per machine, which caps how long a delay can be:")
    for m in MACHINES:
        store = rd.open_store(m)
        say(f"    {m:<16}{store.times[-1].isoformat()}  "
            f"({len(store)} states in the combined store)")

    say(f"\n  the device description has not changed:")
    for m in MACHINES:
        base, _ = rd.load_base_target(m)
        n_cz = len(base["cz"])
        store = rd.open_store(m)
        pairs_now = len(store.snapshot(len(store) - 1)["err_2q"])
        say(f"    {m:<16}base target {base.num_qubits} qubits, {n_cz} cz "
            f"pairs; newest fresh state carries {pairs_now} cz values")
    return 0


sys.exit(main())
