"""Download the last 120 days of calibration history for three machines.

One request per machine per day, asking for that day at 23:59 UTC, which
returns the latest snapshot published before that moment. Files are named by
the snapshot's own last_update_date in UTC, so duplicates collapse. Safe to
stop and restart: a day whose snapshot file already exists is skipped.
Read only, no quantum jobs.
"""
import json
import os
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
N_DAYS = 120
PAUSE_S = 0.7
MAX_TRIES = 3


def hide_secrets(text):
    safe = str(text)
    for secret in (API_KEY, INSTANCE):
        if secret:
            safe = safe.replace(secret, "<HIDDEN>")
    return safe


def say(msg):
    print(msg, flush=True)


def existing_snapshot_dates(out_dir):
    """Dates (YYYY-MM-DD) of snapshots already on disk for this machine."""
    dates = set()
    if out_dir.exists():
        for f in out_dir.glob("*.json"):
            dates.add(f.name[:10])
    return dates


def fetch_one(backend, when):
    """Fetch properties older than `when`, with retries. Returns (props, note)."""
    for attempt in range(1, MAX_TRIES + 1):
        try:
            return backend.properties(datetime=when), None
        except Exception as err:
            msg = hide_secrets(err)
            # Backend did not exist yet: permanent for this date, do not retry.
            if "not found" in msg.lower() or "1216" in msg:
                return None, f"unavailable ({type(err).__name__} code 1216)"
            if attempt == MAX_TRIES:
                return None, f"ERROR after {MAX_TRIES} tries: {type(err).__name__}: {msg}"
            wait = 2 ** attempt
            say(f"      transient {type(err).__name__}, retry {attempt} in {wait}s")
            time.sleep(wait)
    return None, "ERROR unreachable"


def main():
    from qiskit_ibm_runtime import QiskitRuntimeService

    service = QiskitRuntimeService(
        channel="ibm_quantum_platform", token=API_KEY, instance=INSTANCE
    )
    today = datetime.now(timezone.utc).date()
    days = [today - timedelta(days=i) for i in range(N_DAYS - 1, -1, -1)]
    say(f"range: {days[0]} to {days[-1]} ({len(days)} days)")

    totals = {}
    for name in MACHINES:
        say(f"\n=== {name} ===")
        backend = service.backend(name)
        out_dir = RAW / name
        out_dir.mkdir(parents=True, exist_ok=True)
        have = existing_snapshot_dates(out_dir)
        say(f"  already on disk: {len(have)} snapshot files")

        saved = skipped = dup = unavailable = failed = 0
        for day in days:
            if day.isoformat() in have:
                skipped += 1
                continue
            when = datetime(day.year, day.month, day.day, 23, 59, 0,
                            tzinfo=timezone.utc)
            props, note = fetch_one(backend, when)
            time.sleep(PAUSE_S)
            if props is None:
                if note and note.startswith("unavailable"):
                    unavailable += 1
                else:
                    failed += 1
                    say(f"  {day}: {note}")
                continue
            stamp = props.last_update_date.astimezone(timezone.utc)
            tag = stamp.strftime("%Y-%m-%dT%H-%M-%SZ")
            out_file = out_dir / f"{tag}.json"
            if out_file.exists():
                dup += 1
                have.add(tag[:10])
                continue
            tmp = out_dir / (tag + ".part")
            with open(tmp, "w") as fh:
                json.dump(props.to_dict(), fh, indent=2, default=str)
            tmp.rename(out_file)
            os.chmod(out_file, 0o444)
            have.add(tag[:10])
            saved += 1
            if saved % 20 == 0:
                say(f"  ...{saved} saved, latest {tag}")
        totals[name] = dict(saved=saved, skipped=skipped, dup=dup,
                            unavailable=unavailable, failed=failed)
        say(f"  done: saved {saved}, already had {skipped}, duplicate {dup}, "
            f"unavailable {unavailable}, failed {failed}")

    say("\n=== totals ===")
    for name, t in totals.items():
        say(f"  {name}: {t}")


try:
    main()
except KeyboardInterrupt:
    say("\nstopped by user, partial data is kept and the run can be restarted")
    sys.exit(1)
except Exception as err:
    say(f"FAILED: {type(err).__name__}: {hide_secrets(err)}")
    sys.exit(1)
