"""How far back does IBM calibration history go for ibm_kingston?"""
import os
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("IBM_API_KEY")
INSTANCE = os.getenv("IBM_INSTANCE")
BACKEND_NAME = "ibm_kingston"
DAYS_BACK = [60, 90, 180, 365, 730]


def hide_secrets(text):
    safe = str(text)
    for secret in (API_KEY, INSTANCE):
        if secret:
            safe = safe.replace(secret, "<HIDDEN>")
    return safe


def main():
    from qiskit_ibm_runtime import QiskitRuntimeService

    service = QiskitRuntimeService(
        channel="ibm_quantum_platform", token=API_KEY, instance=INSTANCE
    )
    backend = service.backend(BACKEND_NAME)
    today = backend.properties().last_update_date.astimezone(timezone.utc)
    print("today's snapshot:", today.isoformat())
    for days in DAYS_BACK:
        asked = datetime.now(timezone.utc) - timedelta(days=days)
        try:
            props = backend.properties(datetime=asked)
            if props is None:
                print(f"  {days:>4}d ago (asked {asked.date()}): None, nothing stored")
                continue
            got = props.last_update_date.astimezone(timezone.utc)
            age_days = (today - got).total_seconds() / 86400.0
            flag = "older" if got < today else "SAME AS TODAY"
            print(f"  {days:>4}d ago (asked {asked.date()}): got {got.date()} "
                  f"({age_days:.1f} d before today) -> {flag}")
        except Exception as err:
            print(f"  {days:>4}d ago: ERROR {type(err).__name__}: {hide_secrets(err)}")


try:
    main()
except Exception as err:
    print("FAILED:", type(err).__name__)
    print(hide_secrets(err))
