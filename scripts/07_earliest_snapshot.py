"""Binary search for the earliest calibration snapshot IBM will return."""
import os
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("IBM_API_KEY")
INSTANCE = os.getenv("IBM_INSTANCE")
BACKEND_NAME = "ibm_kingston"


def works(backend, days):
    asked = datetime.now(timezone.utc) - timedelta(days=days)
    try:
        props = backend.properties(datetime=asked)
        if props is None:
            return False, "None"
        return True, props.last_update_date.astimezone(timezone.utc).date().isoformat()
    except Exception as err:
        return False, type(err).__name__


def main():
    from qiskit_ibm_runtime import QiskitRuntimeService

    service = QiskitRuntimeService(
        channel="ibm_quantum_platform", token=API_KEY, instance=INSTANCE
    )
    backend = service.backend(BACKEND_NAME)

    lo, hi = 365, 730  # lo works, hi fails
    while hi - lo > 1:
        mid = (lo + hi) // 2
        ok, info = works(backend, mid)
        print(f"  {mid:>4}d ago -> {'ok, got ' + info if ok else 'fail (' + info + ')'}")
        if ok:
            lo = mid
        else:
            hi = mid
    ok, info = works(backend, lo)
    edge = datetime.now(timezone.utc) - timedelta(days=lo)
    print(f"\ndeepest working request: {lo} days back (asked {edge.date()}), "
          f"returned snapshot {info}")
    print(f"first failing request:  {hi} days back")


main()
