"""Step 2: test whether IBM returns OLD calibration snapshots for ibm_kingston.

A try only counts as success if the returned last_update_date is strictly
older than today's current snapshot.
"""
import os
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("IBM_API_KEY")
INSTANCE = os.getenv("IBM_INSTANCE")
BACKEND_NAME = "ibm_kingston"
DAYS_BACK = [1, 3, 7, 30]


def hide_secrets(text):
    safe = str(text)
    if API_KEY:
        safe = safe.replace(API_KEY, "<API_KEY_HIDDEN>")
    if INSTANCE:
        safe = safe.replace(INSTANCE, "<INSTANCE_HIDDEN>")
    return safe


def utc(stamp):
    return stamp.astimezone(timezone.utc)


def main():
    from qiskit_ibm_runtime import QiskitRuntimeService

    service = QiskitRuntimeService(
        channel="ibm_quantum_platform", token=API_KEY, instance=INSTANCE
    )
    backend = service.backend(BACKEND_NAME)

    current = backend.properties()
    today_stamp = utc(current.last_update_date)
    print("TODAY'S SNAPSHOT (the thing we compare against)")
    print("  last_update_date:", today_stamp.isoformat())
    print("  backend.calibration_id attribute:", repr(backend.calibration_id))
    print()

    print("TEST A: backend.properties(datetime=...)")
    for days in DAYS_BACK:
        asked = datetime.now(timezone.utc) - timedelta(days=days)
        label = f"  {days:>2}d ago (asked {asked.date()})"
        try:
            props = backend.properties(datetime=asked)
            if props is None:
                print(f"{label}: returned None, no snapshot")
                continue
            got = utc(props.last_update_date)
            older = got < today_stamp
            delta_h = (today_stamp - got).total_seconds() / 3600.0
            verdict = "REALLY OLDER" if older else "SAME AS TODAY, NOT OLDER"
            print(f"{label}: got {got.isoformat()}  -> {verdict} "
                  f"(gap {delta_h:.2f} h)")
        except Exception as err:
            print(f"{label}: ERROR {type(err).__name__}: {hide_secrets(err)}")
    print()

    print("TEST B: service.backend(name, calibration_id=...)")
    # The package documents calibration_id but gives no endpoint to list ids,
    # and the properties payload carries no id. Test what the server says.
    for cal_id in ["latest", today_stamp.date().isoformat()]:
        try:
            b2 = service.backend(BACKEND_NAME, calibration_id=cal_id)
            p2 = b2.properties()
            got = utc(p2.last_update_date) if p2 else None
            print(f"  calibration_id={cal_id!r}: got {got}")
        except Exception as err:
            print(f"  calibration_id={cal_id!r}: ERROR {type(err).__name__}: "
                  f"{hide_secrets(err)}")


try:
    main()
except Exception as err:
    print("FAILED:", type(err).__name__)
    print(hide_secrets(err))
