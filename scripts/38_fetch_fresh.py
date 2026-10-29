"""Round 2, Stage 3: fetch every card in the fresh window into data/fresh.

The collector is Round 1's, `scripts/13_download_all_snapshots.py`, imported
with its `main()` stripped and its folders and window overridden. The walk is
the same: ask IBM for the newest card at or before time T, read the
last_update_date it returns, then ask again for one second before that. Each
answer says where to step next, so this follows the real chain of published
cards instead of guessing clock times.

Differences from Round 1, and only these:
  - cards go to data/fresh/<machine>, not data/raw, and are gzipped
  - the walk starts at 24 Oct 2026 00:00 UTC, the end of the fresh window,
    not at "now"
  - it stops at 13 Oct 2026 00:00 UTC, the start of the fresh window
  - its own resume file, logs/walkback_state_round2.json

data/raw is not touched. Nothing is analysed here. No gap is filled. No
quantum job is submitted. The API key and the instance are read from .env and
are never printed.
"""
import json
import sys
import types
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

FRESH = ROOT / "data/fresh"
WINDOW_START = datetime(2026, 10, 13, 0, 0, 0, tzinfo=timezone.utc)
WINDOW_END = datetime(2026, 10, 24, 0, 0, 0, tzinfo=timezone.utc)
STATE_FILE = ROOT / "logs/walkback_state_round2.json"
MACHINES = ["ibm_fez", "ibm_kingston", "ibm_marrakesh"]
OUT = ROOT / "outputs" / "round2"


def read_env():
    """Read .env by hand. team_code/.venv has no python-dotenv installed."""
    env = {}
    for line in (ROOT / ".env").read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def load_collector(env):
    """Round 1's collector, with its folders and window moved."""
    path = ROOT / "scripts/13_download_all_snapshots.py"
    src = path.read_text()
    # the file ends with a try/except around main(); cut that off and keep the
    # functions, so the walk is the same code and nothing runs on import
    marker = "\ntry:\n    main()"
    assert marker in src, "the collector no longer ends with try: main()"
    src = src.split(marker, 1)[0]

    # python-dotenv is not installed in team_code/.venv and is not needed:
    # .env is read by hand above. A stub keeps the import line working.
    stub = types.ModuleType("dotenv")
    stub.load_dotenv = lambda *a, **k: None
    sys.modules.setdefault("dotenv", stub)

    mod = types.ModuleType("collector13")
    mod.__file__ = str(path)
    exec(compile(src, str(path), "exec"), mod.__dict__)

    mod.API_KEY = env["IBM_API_KEY"]
    mod.INSTANCE = env["IBM_INSTANCE"]
    mod.RAW = FRESH
    mod.START_DATE = WINDOW_START
    mod.STATE_FILE = STATE_FILE
    mod.USE_GZIP = True
    mod.MACHINES = MACHINES
    return mod


def main():
    print("=" * 72)
    print("ROUND 2 STAGE 3: FETCH THE FRESH WINDOW")
    print("=" * 72)
    print(f"  window: {WINDOW_START.isoformat()} to {WINDOW_END.isoformat()}")
    print(f"  into:   {FRESH}")
    print(f"  the walk starts at the END of the window and steps backwards")
    env = read_env()
    if not env.get("IBM_API_KEY") or not env.get("IBM_INSTANCE"):
        raise SystemExit("missing IBM_API_KEY or IBM_INSTANCE in .env")
    print(f"  credentials loaded from .env: yes")

    col = load_collector(env)
    FRESH.mkdir(parents=True, exist_ok=True)

    from qiskit_ibm_runtime import QiskitRuntimeService
    service = QiskitRuntimeService(channel="ibm_quantum_platform",
                                   token=env["IBM_API_KEY"],
                                   instance=env["IBM_INSTANCE"])

    # resume if an earlier attempt stopped part way, otherwise start at the
    # end of the window
    state = {}
    if STATE_FILE.exists():
        try:
            state = json.loads(STATE_FILE.read_text())
            print(f"  resuming from {STATE_FILE.name}")
        except Exception:
            state = {}
    totals = {}
    for name in MACHINES:
        print(f"\n=== {name} ===", flush=True)
        if state.get(name, {}).get("done"):
            print("  already finished in an earlier run, skipping")
            continue
        state.setdefault(name, {})
        state[name].setdefault("frontier_utc", WINDOW_END.isoformat())
        backend = service.backend(name)
        totals[name] = col.walk_machine(backend, name, state)

    print("\n" + "=" * 72)
    print("FETCH TOTALS")
    print("=" * 72)
    for name, t in totals.items():
        print(f"  {name}: {t}")

    skip_log = ROOT / "logs/skipped_requests.log"
    print(f"\n  requests given up on are listed in {skip_log} if any")
    print("  data/raw was not touched. Nothing was analysed. No gap was filled.")
    return 0


sys.exit(main())
