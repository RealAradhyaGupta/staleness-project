"""Part A: download EVERY distinct calibration snapshot in a date window.

Method, per machine: ask IBM for the newest snapshot at or before time T,
read the last_update_date it returns, then ask again for one second before
that timestamp. Each answer tells us where to step next, so we follow the
real chain of published snapshots instead of guessing clock times. Stop once
a returned snapshot is older than the start date.

Files are named by their own last_update_date in UTC and written read-only
(0444). An existing file is never touched or overwritten. Progress is saved
to a state file after every step, so the run can be stopped and restarted
and it will carry on from the oldest point it reached.

Every request has a 60 second time limit. A request that runs past it is
cancelled and tried again up to 3 times; if it still fails the timestamp is
written to logs/skipped_requests.log, the walk steps back 30 minutes and
carries on, so one hung request can no longer stall the whole run.

Read only. No quantum jobs are ever submitted.

Usage:
  python scripts/13_download_all_snapshots.py [--gzip] [--restart]
"""
import gzip
import json
import os
import signal
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("IBM_API_KEY")
INSTANCE = os.getenv("IBM_INSTANCE")

MACHINES = ["ibm_fez", "ibm_kingston", "ibm_marrakesh"]
RAW = Path("data/raw")
STATE_FILE = Path("logs/walkback_state.json")
START_DATE = datetime(2026, 8, 28, 0, 0, 0, tzinfo=timezone.utc)
PAUSE_S = 0.7
MAX_TRIES = 5
MAX_REQUESTS_PER_MACHINE = 3000   # safety stop, far above the estimate

TIMEOUT_S = 60            # one request may not take longer than this
TIMEOUT_TRIES = 3         # how many times to try a request that times out
SKIP_BACK = timedelta(minutes=30)   # how far to jump back after giving up
MAX_SKIPS_IN_A_ROW = 5    # stop the machine if it keeps timing out
SKIP_LOG = Path("logs/skipped_requests.log")

USE_GZIP = "--gzip" in sys.argv
RESTART = "--restart" in sys.argv


def hide_secrets(text):
    safe = str(text)
    for secret in (API_KEY, INSTANCE):
        if secret:
            safe = safe.replace(secret, "<HIDDEN>")
    return safe


def say(msg):
    print(f"{datetime.now(timezone.utc).strftime('%H:%M:%S')} {msg}", flush=True)


def load_state():
    if RESTART or not STATE_FILE.exists():
        return {}
    try:
        return json.load(open(STATE_FILE))
    except Exception:
        return {}


def save_state(state):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = STATE_FILE.with_suffix(".tmp")
    with open(tmp, "w") as fh:
        json.dump(state, fh, indent=2)
    tmp.replace(STATE_FILE)


def snapshot_path(out_dir, tag):
    """Where this snapshot lives, and whether either form already exists."""
    plain = out_dir / f"{tag}.json"
    gz = out_dir / f"{tag}.json.gz"
    if plain.exists():
        return plain, True
    if gz.exists():
        return gz, True
    return (gz if USE_GZIP else plain), False


def write_snapshot(path, payload):
    """Write read-only, via a temp file so a crash cannot leave a half file."""
    tmp = path.with_suffix(path.suffix + ".part")
    if USE_GZIP:
        with gzip.open(tmp, "wt") as fh:
            json.dump(payload, fh, default=str)
    else:
        with open(tmp, "w") as fh:
            json.dump(payload, fh, indent=2, default=str)
    tmp.rename(path)
    os.chmod(path, 0o444)


class RequestTimeout(Exception):
    """Raised when one IBM request runs past TIMEOUT_S seconds."""


def _alarm(signum, frame):
    raise RequestTimeout(f"no answer within {TIMEOUT_S}s")


def log_skip(name, when, note):
    """Record a point we gave up on, so the gap is never silent."""
    SKIP_LOG.parent.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).isoformat()
    with open(SKIP_LOG, "a") as fh:
        fh.write(f"{stamp}\t{name}\t{when.isoformat()}\t{note}\n")


def ask_ibm(backend, when):
    """One request, cancelled if it runs past TIMEOUT_S seconds."""
    old_handler = signal.signal(signal.SIGALRM, _alarm)
    signal.alarm(TIMEOUT_S)
    try:
        return backend.properties(datetime=when)
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)


def fetch_one(backend, when):
    """properties(datetime=when) with a time limit and retries.

    Returns (props, note). note is None on success. A note starting with
    TIMEOUT means every try ran past the time limit, so the caller should
    log the gap and walk on instead of stopping.
    """
    timeouts = 0
    for attempt in range(1, MAX_TRIES + 1):
        try:
            return ask_ibm(backend, when), None
        except RequestTimeout:
            timeouts += 1
            if timeouts >= TIMEOUT_TRIES:
                return None, (f"TIMEOUT: no answer within {TIMEOUT_S}s on "
                              f"{TIMEOUT_TRIES} tries")
            say(f"      no answer within {TIMEOUT_S}s, "
                f"timeout try {timeouts} of {TIMEOUT_TRIES}")
            time.sleep(2)
        except Exception as err:
            msg = hide_secrets(err)
            if "not found" in msg.lower() or "1216" in msg:
                return None, "unavailable (backend did not exist yet)"
            if attempt == MAX_TRIES:
                return None, f"ERROR after {MAX_TRIES} tries: {type(err).__name__}: {msg}"
            wait = min(2 ** attempt, 30)
            say(f"      transient {type(err).__name__}, retry {attempt} in {wait}s")
            time.sleep(wait)
    return None, "ERROR unreachable"


def walk_machine(backend, name, state):
    out_dir = RAW / name
    out_dir.mkdir(parents=True, exist_ok=True)

    resume = state.get(name, {}).get("frontier_utc")
    if resume:
        when = datetime.fromisoformat(resume)
        say(f"  resuming from saved frontier {when.isoformat()}")
    else:
        when = datetime.now(timezone.utc)
        say(f"  starting from now {when.isoformat()}")

    saved = already = requests = 0
    skipped = skips_in_a_row = 0
    newest = oldest = None
    prev_stamp = None

    while True:
        if requests >= MAX_REQUESTS_PER_MACHINE:
            say(f"  STOPPED: hit the {MAX_REQUESTS_PER_MACHINE} request safety cap")
            break

        props, note = fetch_one(backend, when)
        requests += 1
        time.sleep(PAUSE_S)

        if props is None and note.startswith("TIMEOUT"):
            skipped += 1
            skips_in_a_row += 1
            log_skip(name, when, note)
            say(f"  gave up on {when.isoformat()}: {note}. "
                f"logged it and stepping back {SKIP_BACK}")
            if skips_in_a_row >= MAX_SKIPS_IN_A_ROW:
                say(f"  STOPPED: {MAX_SKIPS_IN_A_ROW} timeouts in a row, "
                    "the link looks dead")
                break
            when = when - SKIP_BACK
            if when < START_DATE:
                say("  stepped past the start date while skipping")
                break
            continue

        if props is None:
            say(f"  stopping at {when.isoformat()}: {note}")
            break

        skips_in_a_row = 0

        stamp = props.last_update_date.astimezone(timezone.utc)

        # Guarantee progress: never let the walk stall or go forwards.
        if prev_stamp is not None and stamp >= prev_stamp:
            say(f"  stopping: no progress, got {stamp.isoformat()} after "
                f"{prev_stamp.isoformat()}")
            break

        if stamp < START_DATE:
            say(f"  reached the start date: {stamp.isoformat()} is older than "
                f"{START_DATE.date()}")
            break

        tag = stamp.strftime("%Y-%m-%dT%H-%M-%SZ")
        path, exists = snapshot_path(out_dir, tag)
        if exists:
            already += 1
        else:
            write_snapshot(path, props.to_dict())
            saved += 1

        if newest is None:
            newest = stamp
        oldest = stamp
        prev_stamp = stamp
        when = stamp - timedelta(seconds=1)

        state[name] = {
            "frontier_utc": when.isoformat(),
            "newest_seen_utc": newest.isoformat(),
            "oldest_seen_utc": oldest.isoformat(),
            "requests": state.get(name, {}).get("requests", 0) + 1,
        }
        save_state(state)

        if requests % 25 == 0:
            say(f"  ...{requests} requests, {saved} new files, at {tag}")

    state.setdefault(name, {})["done"] = True
    save_state(state)
    say(f"  done: {requests} requests, {saved} new files, "
        f"{already} already on disk, {skipped} points skipped after timeouts")
    if newest and oldest:
        say(f"  covered {oldest.isoformat()} to {newest.isoformat()}")
    if skipped:
        say(f"  skipped points are listed in {SKIP_LOG}")
    return dict(requests=requests, saved=saved, already=already, skipped=skipped)


def main():
    from qiskit_ibm_runtime import QiskitRuntimeService

    say(f"Part A walk-back download. window: {START_DATE.date()} to now")
    say(f"storage: {'gzip (.json.gz)' if USE_GZIP else 'plain .json'}")
    service = QiskitRuntimeService(
        channel="ibm_quantum_platform", token=API_KEY, instance=INSTANCE
    )
    state = load_state()
    totals = {}
    for name in MACHINES:
        say(f"\n=== {name} ===")
        if state.get(name, {}).get("done"):
            say("  already finished in an earlier run, skipping "
                "(use --restart to redo)")
            continue
        backend = service.backend(name)
        totals[name] = walk_machine(backend, name, state)

    say("\n=== totals ===")
    for name, t in totals.items():
        say(f"  {name}: {t}")
    say("finished")


try:
    main()
except KeyboardInterrupt:
    say("stopped by user. files already written are kept and the run "
        "can be restarted from the saved state")
    sys.exit(1)
except Exception as err:
    say(f"FAILED: {type(err).__name__}: {hide_secrets(err)}")
    sys.exit(1)
