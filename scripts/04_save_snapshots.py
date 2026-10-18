"""Save current calibration snapshots for all three machines to data/raw."""
import json
import os
from datetime import timezone
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("IBM_API_KEY")
INSTANCE = os.getenv("IBM_INSTANCE")
MACHINES = ["ibm_fez", "ibm_kingston", "ibm_marrakesh"]
RAW = Path("data/raw")


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
    for name in MACHINES:
        backend = service.backend(name)
        props = backend.properties()
        if props is None:
            print(name, "-> no properties snapshot, skipped")
            continue
        stamp = props.last_update_date
        tag = stamp.astimezone(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
        out_dir = RAW / name
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / f"{tag}.json"
        payload = props.to_dict()
        with open(out_file, "w") as fh:
            json.dump(payload, fh, indent=2, default=str)
        size_kb = out_file.stat().st_size / 1024
        print(f"{name:<16} {stamp.isoformat()}  ->  {out_file}  ({size_kb:.1f} KB)")


try:
    main()
except Exception as err:
    print("FAILED:", type(err).__name__)
    print(hide_secrets(err))
