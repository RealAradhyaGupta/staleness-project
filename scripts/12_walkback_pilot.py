"""Pilot for Part A: test the walk-back method and measure its real speed.

Walks back a few snapshots on one machine, printing each returned
last_update_date and how long the request took. Writes NO files. This only
exists to check the method follows the real chain of snapshots and to get a
true seconds-per-request number for the estimate.
Read only, no quantum jobs.
"""
import os
import time
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("IBM_API_KEY")
INSTANCE = os.getenv("IBM_INSTANCE")
MACHINE = "ibm_kingston"
STEPS = 8


def hide_secrets(text):
    safe = str(text)
    for s in (API_KEY, INSTANCE):
        if s:
            safe = safe.replace(s, "<HIDDEN>")
    return safe


def main():
    from qiskit_ibm_runtime import QiskitRuntimeService

    t0 = time.time()
    service = QiskitRuntimeService(
        channel="ibm_quantum_platform", token=API_KEY, instance=INSTANCE
    )
    backend = service.backend(MACHINE)
    print(f"connect + backend lookup: {time.time() - t0:.2f}s")

    when = datetime.now(timezone.utc)
    times = []
    prev = None
    for i in range(STEPS):
        t1 = time.time()
        props = backend.properties(datetime=when)
        dt = time.time() - t1
        times.append(dt)
        if props is None:
            print(f"  step {i}: asked {when.isoformat()} -> None")
            break
        stamp = props.last_update_date.astimezone(timezone.utc)
        n_bytes = len(str(props.to_dict()))
        gap = "" if prev is None else f"  gap from previous: {(prev - stamp).total_seconds()/3600:.2f} h"
        print(f"  step {i}: asked {when.strftime('%Y-%m-%dT%H:%M:%SZ')} -> "
              f"got {stamp.strftime('%Y-%m-%dT%H:%M:%SZ')}  "
              f"({dt:.2f}s, ~{n_bytes/1024:.0f} KB){gap}")
        prev = stamp
        when = stamp - timedelta(seconds=1)

    print(f"\nrequests: {len(times)}")
    print(f"seconds per request: min {min(times):.2f} median "
          f"{sorted(times)[len(times)//2]:.2f} max {max(times):.2f}")


try:
    main()
except Exception as err:
    print(f"FAILED: {type(err).__name__}: {hide_secrets(err)}")
