"""Step 1: connect to IBM Quantum and list the real backends."""
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("IBM_API_KEY")
INSTANCE = os.getenv("IBM_INSTANCE")


def hide_secrets(text):
    """Remove the API key from any text before we show it."""
    safe = str(text)
    if API_KEY:
        safe = safe.replace(API_KEY, "<API_KEY_HIDDEN>")
    return safe


def main():
    if not API_KEY or not INSTANCE:
        print("Missing IBM_API_KEY or IBM_INSTANCE in .env")
        return

    print("API key loaded:", bool(API_KEY), "(length", len(API_KEY), "chars)")
    print("Instance loaded: yes")

    from qiskit_ibm_runtime import QiskitRuntimeService

    service = QiskitRuntimeService(
        channel="ibm_quantum_platform",
        token=API_KEY,
        instance=INSTANCE,
    )

    backends = service.backends(simulator=False, operational=True)
    print("\nReal backends visible to this account:", len(backends))
    print(f"{'name':<22}{'qubits':>8}{'status':>12}{'queue':>8}")
    for b in backends:
        status = b.status()
        print(
            f"{b.name:<22}{b.num_qubits:>8}"
            f"{('online' if status.operational else 'offline'):>12}"
            f"{status.pending_jobs:>8}"
        )


try:
    main()
except Exception as err:
    print("FAILED:", type(err).__name__)
    print(hide_secrets(err))
