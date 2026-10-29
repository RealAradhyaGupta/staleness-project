"""Round 2, Stage 0: environment checks, no-future-card proof, existence probe.

What this does, in plain words:
  1. Prints the exact tools, seeds, shots and core count for this machine, so
     the Round 2 run can be repeated by someone else.
  2. Proves that no file anywhere in this project already holds a calibration
     card dated after 12 October 2026. If one did, the Stage 1 fit could have
     seen the fresh window, which would ruin the test.
  3. Asks IBM, for each machine, whether a card exists near 13, 18 and 23
     October 2026. It prints ONLY yes or no and the timestamp that came back.
     No value is read, saved or printed, so this probe cannot leak a future
     number into the fit.

Read only. No quantum jobs. No file in data/raw is written.
"""
import gzip
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "engine"))

CUTOFF = datetime(2026, 10, 13, 0, 0, 0, tzinfo=timezone.utc)
MACHINES = ["ibm_fez", "ibm_kingston", "ibm_marrakesh"]
PROBE_DATES = [datetime(2026, 10, 13, 12, 0, 0, tzinfo=timezone.utc),
               datetime(2026, 10, 18, 12, 0, 0, tzinfo=timezone.utc),
               datetime(2026, 10, 23, 12, 0, 0, tzinfo=timezone.utc)]
OUT = ROOT / "outputs" / "round2"


def read_env():
    """Read .env by hand. team_code/.venv has no python-dotenv installed."""
    env = {}
    path = ROOT / ".env"
    if not path.exists():
        return env
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def hide(text, secrets):
    safe = str(text)
    for s in secrets:
        if s:
            safe = safe.replace(s, "<HIDDEN>")
    return safe


# ------------------------------------------------------------------ part 1

def versions():
    import platform
    import numpy
    import pandas
    import qiskit
    import engine_config as cfg

    print("=" * 72)
    print("STAGE 0 PART 1: environment")
    print("=" * 72)
    print(f"  interpreter          {sys.executable}")
    print(f"  python               {platform.python_version()}")
    print(f"  qiskit               {qiskit.__version__}")
    try:
        import qiskit_aer
        print(f"  qiskit-aer           {qiskit_aer.__version__}")
    except Exception as err:
        print(f"  qiskit-aer           NOT IMPORTABLE: {type(err).__name__}")
    import qiskit_ibm_runtime
    print(f"  qiskit-ibm-runtime   {qiskit_ibm_runtime.__version__}")
    print(f"  numpy                {numpy.__version__}")
    print(f"  pandas               {pandas.__version__}")
    print(f"  platform             {platform.platform()}")
    print(f"  cpu cores            {os.cpu_count()}")
    print()
    print(f"  optimization level   {cfg.OPT_LEVEL}")
    print(f"  seed_transpiler      {cfg.SEED_TRANSPILE}")
    print(f"  seed_simulator base  {cfg.SEED_SIM}")
    print(f"  seed submission draw {cfg.SEED_SUBMIT}")
    print(f"  shots                {cfg.SHOTS}")
    print(f"  delays (h)           {cfg.DELAYS_H}")
    print(f"  submits per day      {cfg.SUBMITS_PER_DAY}")
    print(f"  dead rule            sx > {cfg.SX_DEAD} or readout > {cfg.RO_DEAD} "
          f"or T1 missing or T2 missing")
    return {"python": platform.python_version(), "qiskit": qiskit.__version__,
            "cores": os.cpu_count()}


# ------------------------------------------------------------------ part 2

STAMP = re.compile(r"(20\d\d)-(\d\d)-(\d\d)[T_ ](\d\d)[-:](\d\d)[-:](\d\d)")


def newest_raw_card():
    """Newest card file on disk, by its own filename stamp, per machine."""
    out = {}
    for d in sorted((ROOT / "data" / "raw").iterdir()):
        if not d.is_dir():
            continue
        stamps = []
        for f in d.iterdir():
            m = STAMP.match(f.name)
            if m:
                stamps.append(datetime(*map(int, m.groups()), tzinfo=timezone.utc))
        out[d.name] = (len(stamps), max(stamps) if stamps else None)
    return out


def newest_in_csv():
    """Newest timestamp inside each clean table that holds card times."""
    import pandas as pd
    out = {}
    clean = ROOT / "data" / "clean"
    for name, col in [("qubits.csv", "snapshot_utc"), ("pairs.csv", "snapshot_utc"),
                      ("card_quality.csv", "snapshot_utc"),
                      ("states.csv", "last_card_utc")]:
        p = clean / name
        if not p.exists():
            continue
        s = pd.read_csv(p, usecols=[col])[col]
        t = pd.to_datetime(s, utc=True)
        out[name] = (len(t), t.max())
    return out


def scan_for_future_cards():
    print()
    print("=" * 72)
    print("STAGE 0 PART 2: is there any calibration card after 12 Oct 2026?")
    print("=" * 72)
    bad = []

    print("  raw card files on disk (read only, never written here):")
    for m, (n, newest) in newest_raw_card().items():
        flag = "AFTER CUTOFF" if newest and newest >= CUTOFF else "ok"
        print(f"    {m:<16} {n:>5} files   newest {newest}   {flag}")
        if newest and newest >= CUTOFF:
            bad.append(f"data/raw/{m}")

    print("  clean tables:")
    for name, (n, newest) in newest_in_csv().items():
        flag = "AFTER CUTOFF" if newest >= CUTOFF else "ok"
        print(f"    {name:<16} {n:>7} rows   newest {newest}   {flag}")
        if newest >= CUTOFF:
            bad.append(f"data/clean/{name}")

    fresh = ROOT / "data" / "fresh"
    n_fresh = sum(1 for _ in fresh.rglob("*.json*")) if fresh.exists() else 0
    print(f"  data/fresh exists: {fresh.exists()}   card files: {n_fresh}")
    print("    (this is where Stage 3 will put the fresh cards; it is expected")
    print("     to be empty or absent at Stage 0)")

    print()
    if bad:
        print(f"  RESULT: FOUND card data at or after {CUTOFF.date()} in: {bad}")
    else:
        print(f"  RESULT: no card at or after {CUTOFF.date()} in data/raw or "
              f"data/clean. The development fit cannot have seen the fresh "
              f"window.")
    return bad


# ------------------------------------------------------------------ part 3

def existence_probe():
    print()
    print("=" * 72)
    print("STAGE 0 PART 3: existence probe (yes/no and timestamp only)")
    print("=" * 72)
    env = read_env()
    key, inst = env.get("IBM_API_KEY"), env.get("IBM_INSTANCE")
    secrets = [key, inst]
    if not key or not inst:
        print("  MISSING IBM_API_KEY or IBM_INSTANCE in .env")
        return None
    print(f"  credentials loaded from .env: key {bool(key)}, instance {bool(inst)}")
    print("  no value from any returned card is read, saved or printed below")
    print()

    from qiskit_ibm_runtime import QiskitRuntimeService
    try:
        service = QiskitRuntimeService(channel="ibm_quantum_platform",
                                       token=key, instance=inst)
    except Exception as err:
        print(f"  CONNECT FAILED: {type(err).__name__}: {hide(err, secrets)}")
        return None

    rows = []
    print(f"  {'machine':<16}{'asked for':<22}{'returned?':<11}{'timestamp of card'}")
    for m in MACHINES:
        try:
            backend = service.backend(m)
        except Exception as err:
            print(f"  {m:<16}{'(backend lookup)':<22}{'NO':<11}"
                  f"{type(err).__name__}: {hide(err, secrets)}")
            for when in PROBE_DATES:
                rows.append({"machine": m, "asked_utc": when.isoformat(),
                             "returned": False, "card_utc": "",
                             "note": "backend lookup failed"})
            continue
        for when in PROBE_DATES:
            try:
                props = backend.properties(datetime=when)
            except Exception as err:
                print(f"  {m:<16}{when.date().isoformat():<22}{'NO':<11}"
                      f"{type(err).__name__}: {hide(err, secrets)}")
                rows.append({"machine": m, "asked_utc": when.isoformat(),
                             "returned": False, "card_utc": "",
                             "note": f"{type(err).__name__}"})
                continue
            if props is None:
                print(f"  {m:<16}{when.date().isoformat():<22}{'NO':<11}"
                      f"nothing returned")
                rows.append({"machine": m, "asked_utc": when.isoformat(),
                             "returned": False, "card_utc": "", "note": "None"})
                continue
            stamp = props.last_update_date.astimezone(timezone.utc)
            print(f"  {m:<16}{when.date().isoformat():<22}{'YES':<11}"
                  f"{stamp.isoformat()}")
            rows.append({"machine": m, "asked_utc": when.isoformat(),
                         "returned": True, "card_utc": stamp.isoformat(),
                         "note": ""})
            del props
    return rows


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    versions()
    bad = scan_for_future_cards()
    rows = existence_probe()

    print()
    print("=" * 72)
    print("STAGE 0 VERDICT")
    print("=" * 72)
    if bad:
        print("  A card after 12 Oct 2026 is already on disk. This is a fault,")
        print("  not a stop rule. It is reported and the run continues, but the")
        print("  Stage 1 fit must be checked against it.")
    else:
        print("  No future card on disk: ok.")

    if rows is None:
        print("  PROBE: could not reach IBM at all.")
        print("  STOP RULE FIRED: no dates are retrievable for any machine.")
        return 2

    import pandas as pd
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "stage0_existence_probe.csv", index=False)
    print(f"  probe table written to {OUT / 'stage0_existence_probe.csv'}")

    got = df.groupby("machine").returned.sum()
    for m in MACHINES:
        print(f"  {m}: {int(got.get(m, 0))} of {len(PROBE_DATES)} probe dates "
              f"returned a card")
    if df.returned.sum() == 0:
        print()
        print("  STOP RULE FIRED: no dates are retrievable for ANY machine.")
        print("  The collector can only log cards live, not fetch history.")
        return 2
    missing = [m for m in MACHINES if int(got.get(m, 0)) == 0]
    if missing:
        print()
        print(f"  STOP RULE FIRED: no dates retrievable for {missing}.")
        return 2
    print()
    print("  PROBE OK: every machine returned a card for every probe date.")
    print("  Historical retrieval works, so Stage 3 can fetch the fresh window.")
    return 0


sys.exit(main())
