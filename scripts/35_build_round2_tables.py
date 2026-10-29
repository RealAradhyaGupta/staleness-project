"""Round 2: build the combined state store that spans BOTH windows.

Why this is needed. A job submitted on 13 Oct has to look back at the last 12
distinct values of each field, and those sit in the development window. So the
store the engine reads must cover 28 Aug to 24 Oct in one continuous chain.

Why it is built in a new folder. data/raw is read only and data/clean is the
Round 1 record, which must not change. So:
  - data/round2_cards/<machine>/  holds SYMLINKS to every card in
    data/raw/<machine> and data/fresh/<machine>. No card is copied or moved.
  - data/clean_r2/   holds the combined qubits.csv, pairs.csv and states.csv
  - data/cache_r2/   holds the per machine npz cache the engine reads

Why it reuses the old scripts. The tables are built by importing
scripts/15_build_tables_all.py and scripts/17_build_states.py and pointing
their input and output folders at the new locations. That is the SAME code
that built the Round 1 tables, so the combined tables cannot drift from them
by a coding difference.

Then it CHECKS that: restricted to the development window, the new tables are
identical to data/clean, row for row and value for value. If they are not,
this script stops.

No network calls. No file in data/raw or data/clean is written.
"""
import os
import shutil
import sys
import types
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data/raw"
FRESH = ROOT / "data/fresh"
LINKS = ROOT / "data/round2_cards"
CLEAN_R1 = ROOT / "data/clean"
CLEAN_R2 = ROOT / "data/clean_r2"
CACHE_R2 = ROOT / "data/cache_r2"
MACHINES = ["ibm_fez", "ibm_kingston", "ibm_marrakesh"]
DEV_END = pd.Timestamp("2026-10-13T00:00:00Z")


def say(*a):
    print(*a, flush=True)


def build_links():
    """One folder of symlinks per machine, pointing at both card folders."""
    if LINKS.exists():
        shutil.rmtree(LINKS)
    counts = {}
    for m in MACHINES:
        dest = LINKS / m
        dest.mkdir(parents=True)
        n_raw = n_fresh = 0
        for src_dir, tag in ((RAW / m, "raw"), (FRESH / m, "fresh")):
            if not src_dir.exists():
                continue
            for f in sorted(src_dir.iterdir()):
                if not (f.name.endswith(".json") or f.name.endswith(".json.gz")):
                    continue
                link = dest / f.name
                if link.exists():
                    continue
                os.symlink(f.resolve(), link)
                if tag == "raw":
                    n_raw += 1
                else:
                    n_fresh += 1
        counts[m] = (n_raw, n_fresh)
        say(f"  {m}: {n_raw} development cards + {n_fresh} fresh cards "
            f"= {n_raw + n_fresh} symlinks")
    return counts


def run_script(relpath, overrides):
    """Import a numbered script with its main() stripped, override its module
    level folders, then call main(). Same code, different folders."""
    path = ROOT / relpath
    src = path.read_text().rsplit("\nmain()", 1)[0]
    mod = types.ModuleType(Path(relpath).stem.replace(".", "_"))
    mod.__file__ = str(path)
    code = compile(src, str(path), "exec")
    cwd = os.getcwd()
    os.chdir(ROOT)
    try:
        exec(code, mod.__dict__)
        for k, v in overrides.items():
            if not hasattr(mod, k):
                raise SystemExit(f"{relpath} has no module level {k}")
            setattr(mod, k, v)
        mod.main()
    finally:
        os.chdir(cwd)
    return mod


# DEVIATION, logged. A calibration state is a run of neighbouring cards that
# all carry the same five fields, and two of its columns record how long that
# run lasted: last_card_utc and n_cards. The LAST development state of a
# machine can legitimately keep being republished into the fresh window, so in
# the combined view that one run is longer than data/clean recorded when the
# fresh cards did not exist. That is the state genuinely continuing, not a
# difference in the numbers. So those two columns are allowed to GROW on the
# boundary state only, and are required to be identical everywhere else.
# Everything else, including first_seen_utc, which is the clock the engine
# reads, must still be identical on every development state.
GROWABLE_ON_BOUNDARY = ["last_card_utc", "n_cards"]


def compare(name, key_cols):
    """The new table, cut to the development window, must equal the old one."""
    old = pd.read_csv(CLEAN_R1 / name)
    new = pd.read_csv(CLEAN_R2 / name)
    tcol = "first_seen_utc" if "first_seen_utc" in old.columns else "snapshot_utc"
    new_dev = new[pd.to_datetime(new[tcol], utc=True) < DEV_END].copy()
    cols = [c for c in old.columns]
    if list(new.columns) != cols:
        return False, (f"columns differ: old {cols} vs new "
                       f"{list(new.columns)}")
    old = old.sort_values(key_cols).reset_index(drop=True)[cols]
    new_dev = new_dev.sort_values(key_cols).reset_index(drop=True)[cols]
    if len(old) != len(new_dev):
        return False, f"{len(old)} rows in data/clean vs {len(new_dev)} new"

    # the last development row of each machine, which is where a run may grow
    boundary = set()
    if "machine" in cols:
        boundary = {int(old[old.machine == m].index.max())
                    for m in old.machine.unique()}

    notes = []
    for c in cols:
        a, b = old[c], new_dev[c]
        if a.dtype.kind in "fc" or b.dtype.kind in "fc":
            av = pd.to_numeric(a, errors="coerce").to_numpy(dtype=float)
            bv = pd.to_numeric(b, errors="coerce").to_numpy(dtype=float)
            same_mask = (av == bv) | (np.isnan(av) & np.isnan(bv))
        else:
            # Both sides missing counts as the same. pandas keeps a missing
            # value missing through astype(str), and a numpy comparison then
            # makes NaN != NaN true, which would flag 918 identical rows.
            na = a.isna().to_numpy() & b.isna().to_numpy()
            eq = (a.astype(object).fillna("").astype(str).to_numpy()
                  == b.astype(object).fillna("").astype(str).to_numpy())
            same_mask = eq | na
        bad = [int(i) for i in np.where(~same_mask)[0]]
        if not bad:
            continue
        if c not in GROWABLE_ON_BOUNDARY or not set(bad) <= boundary:
            return False, (f"column {c} differs in {len(bad)} rows, "
                           f"positions {bad[:5]}")
        # on the boundary state the run may only have grown, never shrunk
        for i in bad:
            ov, nv = old[c][i], new_dev[c][i]
            grew = (float(nv) > float(ov) if c == "n_cards"
                    else pd.Timestamp(nv) > pd.Timestamp(ov))
            if not grew:
                return False, (f"column {c} row {i} changed without growing: "
                               f"{ov} -> {nv}")
            notes.append(f"{old.machine[i]} boundary state {c} "
                         f"{ov} -> {nv}")
    if notes:
        return True, (f"{len(old)} rows identical except the boundary state's "
                      f"run length, which grew: " + "; ".join(notes))
    return True, f"{len(old)} rows identical"


def build_cache():
    """The engine's npz cache, from the combined tables."""
    sys.path.insert(0, str(ROOT / "engine"))
    os.environ["STALENESS_CLEAN_DIR"] = str(CLEAN_R2)
    os.environ["STALENESS_CACHE_DIR"] = str(CACHE_R2)
    for mod in ("real_data", "prepare_cache"):
        sys.modules.pop(mod, None)
    import real_data as rd
    import prepare_cache as pc
    assert rd.CLEAN == CLEAN_R2, rd.CLEAN
    assert rd.CACHE_DIR == CACHE_R2, rd.CACHE_DIR
    pc.CACHE = CACHE_R2
    states, qubits, pairs = rd.load_tables()
    for m in sorted(states.machine.unique()):
        pc.build(m, states, qubits, pairs)
    return rd


def main():
    say("=" * 72)
    say("ROUND 2: build the combined store (development cards plus fresh cards)")
    say("=" * 72)
    if not FRESH.exists() or not any(FRESH.rglob("*.json*")):
        raise SystemExit("data/fresh holds no cards yet. Run Stage 3 first.")

    say("\nstep 1: symlink both card folders into one place")
    build_links()

    if CLEAN_R2.exists():
        shutil.rmtree(CLEAN_R2)
    CLEAN_R2.mkdir(parents=True)

    say("\nstep 2: qubits.csv and pairs.csv, by scripts/15_build_tables_all.py")
    run_script("scripts/15_build_tables_all.py",
               {"RAW": LINKS, "CLEAN": CLEAN_R2})

    say("\nstep 3: states.csv, by scripts/17_build_states.py")
    run_script("scripts/17_build_states.py",
               {"RAW": LINKS, "CLEAN": CLEAN_R2})

    say("\n" + "=" * 72)
    say("step 4: CHECK the development part against data/clean")
    say("=" * 72)
    checks = [("qubits.csv", ["machine", "snapshot_utc", "qubit"]),
              ("pairs.csv", ["machine", "snapshot_utc", "qubit_a", "qubit_b"]),
              ("states.csv", ["machine", "first_seen_utc"])]
    bad = []
    for name, keys in checks:
        ok, note = compare(name, keys)
        say(f"  {name:<14} {'IDENTICAL' if ok else 'DIFFERENT'}   {note}")
        if not ok:
            bad.append(name)
    if bad:
        raise SystemExit(f"STOP: the combined tables do not reproduce "
                         f"data/clean for {bad}. Nothing further was built.")

    say("\nstep 5: the npz cache the engine reads")
    if CACHE_R2.exists():
        shutil.rmtree(CACHE_R2)
    rd = build_cache()

    say("\n" + "=" * 72)
    say("the combined store")
    say("=" * 72)
    st = pd.read_csv(CLEAN_R2 / "states.csv")
    st["first_seen_utc"] = pd.to_datetime(st.first_seen_utc, utc=True)
    say(f"  {'machine':<16}{'states':>8}{'dev':>7}{'fresh':>7}"
        f"   first state            last state")
    for m in MACHINES:
        s = st[st.machine == m]
        dev = int((s.first_seen_utc < DEV_END).sum())
        say(f"  {m:<16}{len(s):>8}{dev:>7}{len(s) - dev:>7}"
            f"   {s.first_seen_utc.min()}  {s.first_seen_utc.max()}")
    say(f"  total states {len(st)}, of which "
        f"{int((st.first_seen_utc < DEV_END).sum())} development and "
        f"{int((st.first_seen_utc >= DEV_END).sum())} fresh")
    say("\n  data/raw and data/clean were only read. No card was copied.")
    return 0


sys.exit(main())
