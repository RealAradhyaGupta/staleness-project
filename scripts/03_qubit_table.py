"""Step 3: small calibration table for the first 10 qubits, plus 5 cz errors."""
import os
from dotenv import load_dotenv
import pandas as pd

load_dotenv()
API_KEY = os.getenv("IBM_API_KEY")
INSTANCE = os.getenv("IBM_INSTANCE")
BACKEND_NAME = "ibm_kingston"
N_QUBITS = 10
N_PAIRS = 5


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
    props = backend.properties()
    print("backend:", backend.name)
    print("snapshot:", props.last_update_date.isoformat())

    rows = []
    for q in range(N_QUBITS):
        rows.append(
            {
                "qubit": q,
                "T1_us": props.t1(q) * 1e6,
                "T2_us": props.t2(q) * 1e6,
                "readout_err": props.readout_error(q),
                "sx_err": props.gate_error("sx", q),
            }
        )
    table = pd.DataFrame(rows)
    pd.set_option("display.float_format", lambda v: f"{v:.6g}")
    print("\nFirst", N_QUBITS, "qubits:")
    print(table.to_string(index=False))

    print("\nExample two-qubit (cz) gate errors:")
    shown = 0
    for gate in props.gates:
        if gate.gate == "cz":
            pair = gate.qubits
            err = props.gate_error("cz", pair)
            print(f"  cz{tuple(pair)}  error = {err:.6g}")
            shown += 1
            if shown == N_PAIRS:
                break


try:
    main()
except Exception as err:
    print("FAILED:", type(err).__name__)
    print(hide_secrets(err))
