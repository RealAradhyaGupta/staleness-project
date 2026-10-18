"""Step 2: show the latest calibration timestamp for one real backend."""
import os
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("IBM_API_KEY")
INSTANCE = os.getenv("IBM_INSTANCE")
BACKEND_NAME = "ibm_kingston"


def hide_secrets(text):
    safe = str(text)
    if API_KEY:
        safe = safe.replace(API_KEY, "<API_KEY_HIDDEN>")
    return safe


def main():
    from qiskit_ibm_runtime import QiskitRuntimeService

    service = QiskitRuntimeService(
        channel="ibm_quantum_platform", token=API_KEY, instance=INSTANCE
    )
    backend = service.backend(BACKEND_NAME)
    print("backend:", backend.name)
    print("qubits:", backend.num_qubits)
    print("basis gates:", backend.operation_names)

    props = backend.properties()
    if props is None:
        print("This backend has no properties snapshot (None).")
        return

    stamp = props.last_update_date
    now = datetime.now(timezone.utc)
    age_hours = (now - stamp).total_seconds() / 3600.0
    print("last_update_date (UTC):", stamp.astimezone(timezone.utc).isoformat())
    print("read at (UTC):         ", now.isoformat())
    print(f"snapshot age: {age_hours:.2f} hours")


try:
    main()
except Exception as err:
    print("FAILED:", type(err).__name__)
    print(hide_secrets(err))
