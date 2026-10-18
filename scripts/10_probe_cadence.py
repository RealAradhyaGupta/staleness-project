"""Part A: how often does IBM really publish snapshots for ibm_kingston?

Probe 5 days spread over the last 60 days at 7 clock times each. List the
distinct last_update_date values returned per day. Save any snapshot not
already on disk, read-only. Never modify an existing file.
Read only, no quantum jobs.
"""
import json
import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("IBM_API_KEY")
INSTANCE = os.getenv("IBM_INSTANCE")
MACHINE = "ibm_kingston"
RAW = Path("data/raw") / MACHINE
HOURS = [(0, 0), (4, 0), (8, 0), (12, 0), (16, 0), (20, 0), (23, 59)]
DAYS_AGO = [60, 45, 30, 15, 2]   # spread over the last 60 days
PAUSE_S = 0.7


def hide_secrets(text):
    safe = str(text)
    for s in (API_KEY, INSTANCE):
        if s:
            safe = safe.replace(s, "<HIDDEN>")
    return safe


def main():
    from qiskit_ibm_runtime import QiskitRuntimeService

    service = QiskitRuntimeService(
        channel="ibm_quantum_platform", token=API_KEY, instance=INSTANCE
    )
    backend = service.backend(MACHINE)
    today = datetime.now(timezone.utc).date()
    new_files = 0

    for days in DAYS_AGO:
        day = today - timedelta(days=days)
        print(f"\n=== {day} ({days} days ago) ===")
        seen = {}
        for hh, mm in HOURS:
            when = datetime(day.year, day.month, day.day, hh, mm,
                            tzinfo=timezone.utc)
            try:
                props = backend.properties(datetime=when)
            except Exception as err:
                print(f"  {hh:02d}:{mm:02d} -> ERROR {type(err).__name__}: "
                      f"{hide_secrets(err)}")
                time.sleep(PAUSE_S)
                continue
            time.sleep(PAUSE_S)
            if props is None:
                print(f"  {hh:02d}:{mm:02d} -> None")
                continue
            stamp = props.last_update_date.astimezone(timezone.utc)
            tag = stamp.strftime("%Y-%m-%dT%H-%M-%SZ")
            same_day = stamp.date() == day
            print(f"  {hh:02d}:{mm:02d} -> {stamp.isoformat()}"
                  f"{'' if same_day else '   (from an earlier day)'}")
            if tag not in seen:
                seen[tag] = props
        # how many distinct snapshots were published on the day itself
        own = [t for t in seen if t[:10] == day.isoformat()]
        print(f"  distinct snapshots returned: {len(seen)}")
        print(f"  of those, published on {day} itself: {len(own)} -> "
              f"{sorted(t[11:19].replace('-', ':') for t in own)}")
        for tag, props in seen.items():
            out = RAW / f"{tag}.json"
            if out.exists():
                continue
            tmp = RAW / (tag + ".part")
            with open(tmp, "w") as fh:
                json.dump(props.to_dict(), fh, indent=2, default=str)
            tmp.rename(out)
            os.chmod(out, 0o444)
            new_files += 1
            print(f"  saved new file: {out.name}")

    print(f"\nnew snapshot files written: {new_files}")


try:
    main()
except Exception as err:
    print(f"FAILED: {type(err).__name__}: {hide_secrets(err)}")
