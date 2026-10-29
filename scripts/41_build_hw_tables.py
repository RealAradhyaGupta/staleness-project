"""Stage 6: build the state store the hardware run reads.

The history each arm sees is the Round 2 store PLUS the live cards fetched
into data/hardware_cards, and nothing newer than the compile time. This script
builds that combined store for ONE machine, the device the hardware stage
uses, because no other machine is touched.

  - data/hw_cards/<machine>/  SYMLINKS to every card for that machine in
    data/raw, data/fresh and data/hardware_cards. No card is copied or moved.
  - data/clean_hw/            the combined qubits.csv, pairs.csv, states.csv
  - data/cache_hw/            the npz cache the engine reads

It reuses scripts/15_build_tables_all.py and scripts/17_build_states.py, the
same code that built the Round 1 and Round 2 tables, with their input and
output folders pointed at the new locations. So the combined tables cannot
drift from the earlier ones by a coding difference.

Then it CHECKS, for that machine:
  - cut to before 13 Oct 2026, the new tables equal data/clean (Round 1)
  - cut to before 24 Oct 2026, the new tables equal data/clean_r2 (Round 2)
If either fails it stops and builds nothing further.

The one allowance, the same one Round 2 logged: a calibration state is a run
of neighbouring cards carrying the same five fields, and last_card_utc and
n_cards record how long that run lasted. The LAST state before a cut can
legitimately keep being republished after the cut, so in the wider view that
one run is longer. Those two columns may therefore GROW on the boundary state
only, never shrink, and everything else including first_seen_utc must be
identical on every state before the cut.

No network call. No file in data/raw, data/fresh, data/clean or data/clean_r2
is written. Run it again and it rebuilds from scratch, which is what the
hardware runner does before every compile so the store is current.

Usage:
  python scripts/41_build_hw_tables.py ibm_kingston
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
HW = ROOT / "data/hardware_cards"
LINKS = ROOT / "data/hw_cards"
CLEAN_HW = ROOT / "data/clean_hw"
CACHE_HW = ROOT / "data/cache_hw"

# the two reference stores and the cut each must be compared at
REFERENCES = [("data/clean", ROOT / "data/clean", pd.Timestamp("2026-10-13T00:00:00Z")),
              ("data/clean_r2", ROOT / "data/clean_r2", pd.Timestamp("2026-10-24T00:00:00Z"))]
GROWABLE_ON_BOUNDARY = ["last_card_utc", "n_cards"]


def say(*a):
    print(*a, flush=True)


def build_links(machine):
    """One folder of symlinks for this machine, over all three card folders."""
    dest = LINKS / machine
    if LINKS.exists():
        shutil.rmtree(LINKS)
    dest.mkdir(parents=True)
    counts = {}
    for src_dir, tag in ((RAW / machine, "raw"), (FRESH / machine, "fresh"),
                         (HW / machine, "hardware")):
        n = 0
        if src_dir.exists():
            for f in sorted(src_dir.iterdir()):
                if not (f.name.endswith(".json") or f.name.endswith(".json.gz")):
                    continue
                link = dest / f.name
                if link.exists():
                    continue
                os.symlink(f.resolve(), link)
                n += 1
        counts[tag] = n
    say(f"  {machine}: " + ", ".join(f"{v} from {k}" for k, v in counts.items())
        + f" = {sum(counts.values())} symlinks")
    if counts["hardware"] == 0:
        raise SystemExit(f"STOP: data/hardware_cards/{machine} holds no cards. "
                         "Fetch the live cards first.")
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


def compare(name, key_cols, machine, ref_dir, cut):
    """The new table, cut to before `cut` and to this machine, must equal the
    reference table cut the same way."""
    old = pd.read_csv(ref_dir / name)
    new = pd.read_csv(CLEAN_HW / name)
    cols = list(old.columns)
    if list(new.columns) != cols:
        return False, f"columns differ: ref {cols} vs new {list(new.columns)}"
    tcol = "first_seen_utc" if "first_seen_utc" in cols else "snapshot_utc"

    def cut_to(df):
        d = df[df.machine == machine].copy()
        return d[pd.to_datetime(d[tcol], utc=True) < cut]

    old = cut_to(old).sort_values(key_cols).reset_index(drop=True)[cols]
    new = cut_to(new).sort_values(key_cols).reset_index(drop=True)[cols]
    if len(old) != len(new):
        return False, f"{len(old)} rows in the reference vs {len(new)} new"
    if len(old) == 0:
        return False, "no rows to compare"

    boundary = {int(old.index.max())}        # the last state before the cut
    notes = []
    for c in cols:
        a, b = old[c], new[c]
        if a.dtype.kind in "fc" or b.dtype.kind in "fc":
            av = pd.to_numeric(a, errors="coerce").to_numpy(dtype=float)
            bv = pd.to_numeric(b, errors="coerce").to_numpy(dtype=float)
            same = (av == bv) | (np.isnan(av) & np.isnan(bv))
        else:
            # both sides missing counts as the same. pandas keeps a missing
            # value missing through astype(str) and numpy then makes
            # NaN != NaN true, which would flag identical rows as different.
            na = a.isna().to_numpy() & b.isna().to_numpy()
            eq = (a.astype(object).fillna("").astype(str).to_numpy()
                  == b.astype(object).fillna("").astype(str).to_numpy())
            same = eq | na
        bad = [int(i) for i in np.where(~same)[0]]
        if not bad:
            continue
        if c not in GROWABLE_ON_BOUNDARY or not set(bad) <= boundary:
            return False, (f"column {c} differs in {len(bad)} rows, "
                           f"positions {bad[:5]}")
        for i in bad:
            ov, nv = old[c][i], new[c][i]
            grew = (float(nv) > float(ov) if c == "n_cards"
                    else pd.Timestamp(nv) > pd.Timestamp(ov))
            if not grew:
                return False, (f"column {c} row {i} changed without growing: "
                               f"{ov} -> {nv}")
            notes.append(f"boundary state {c} {ov} -> {nv}")
    if notes:
        return True, (f"{len(old)} rows identical except the boundary state's "
                      "run length, which grew: " + "; ".join(notes))
    return True, f"{len(old)} rows identical"


def build_cache(machine):
    """The engine's npz cache, from the combined tables."""
    sys.path.insert(0, str(ROOT / "engine"))
    os.environ["STALENESS_CLEAN_DIR"] = str(CLEAN_HW)
    os.environ["STALENESS_CACHE_DIR"] = str(CACHE_HW)
    for mod in ("real_data", "prepare_cache"):
        sys.modules.pop(mod, None)
    import real_data as rd
    import prepare_cache as pc
    assert rd.CLEAN == CLEAN_HW, rd.CLEAN
    assert rd.CACHE_DIR == CACHE_HW, rd.CACHE_DIR
    pc.CACHE = CACHE_HW
    states, qubits, pairs = rd.load_tables()
    for m in sorted(states.machine.unique()):
        pc.build(m, states, qubits, pairs)
    return rd


def build(machine, quiet=False):
    """Build the whole store for one machine. Returns the number of states."""
    say("=" * 72)
    say(f"STAGE 6: build the hardware store for {machine}")
    say("=" * 72)
    say("\nstep 1: symlink all three card folders into one place")
    build_links(machine)

    if CLEAN_HW.exists():
        shutil.rmtree(CLEAN_HW)
    CLEAN_HW.mkdir(parents=True)

    say("\nstep 2: qubits.csv and pairs.csv, by scripts/15_build_tables_all.py")
    run_script("scripts/15_build_tables_all.py",
               {"RAW": LINKS, "CLEAN": CLEAN_HW})
    say("\nstep 3: states.csv, by scripts/17_build_states.py")
    run_script("scripts/17_build_states.py",
               {"RAW": LINKS, "CLEAN": CLEAN_HW})

    say("\n" + "=" * 72)
    say("step 4: CHECK the earlier parts against the stores already recorded")
    say("=" * 72)
    checks = [("qubits.csv", ["machine", "snapshot_utc", "qubit"]),
              ("pairs.csv", ["machine", "snapshot_utc", "qubit_a", "qubit_b"]),
              ("states.csv", ["machine", "first_seen_utc"])]
    bad = []
    for ref_name, ref_dir, cut in REFERENCES:
        if not ref_dir.exists():
            say(f"  {ref_name}: not present, cannot check")
            bad.append(ref_name)
            continue
        say(f"  against {ref_name}, cut to before {cut.date()}")
        for name, keys in checks:
            ok, note = compare(name, keys, machine, ref_dir, cut)
            say(f"    {name:<12} {'IDENTICAL' if ok else 'DIFFERENT'}   {note}")
            if not ok:
                bad.append(f"{ref_name}/{name}")
    if bad:
        raise SystemExit(f"STOP: the combined tables do not reproduce {bad}. "
                         "Nothing further was built.")

    say("\nstep 5: the npz cache the engine reads")
    if CACHE_HW.exists():
        shutil.rmtree(CACHE_HW)
    CACHE_HW.mkdir(parents=True)
    rd = build_cache(machine)
    store = rd.open_store(machine)
    say(f"\n  {machine}: {len(store)} distinct states, "
        f"{store.times[0].isoformat()} to {store.times[-1].isoformat()}")
    say("\n  data/raw, data/fresh, data/clean and data/clean_r2 were only read.")
    return len(store)


def main():
    if len(sys.argv) < 2:
        raise SystemExit("usage: python scripts/41_build_hw_tables.py <machine>")
    build(sys.argv[1])
    return 0


if __name__ == "__main__":
    sys.exit(main())
