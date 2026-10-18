"""M1 - Real calibration data from IBM Quantum.

NOT YET RUN AGAINST THE LIVE SERVICE (needs an IBM account key). Written against
qiskit-ibm-runtime 0.50, where both history methods below exist.

One-time setup (in Python, with your own values from quantum.cloud.ibm.com):
    from qiskit_ibm_runtime import QiskitRuntimeService
    QiskitRuntimeService.save_account(channel="ibm_quantum_platform",
        token="YOUR_API_KEY", instance="YOUR_INSTANCE_CRN", set_as_default=True)

Two modes:
    python ingest_ibm.py history ibm_torino 30   -> pull up to 30 days of past snapshots
    python ingest_ibm.py log ibm_torino          -> save today's snapshot (run twice a day as the fallback)

Output: snapshots/<device>/cycle_000.json ... (same format as synthetic) and base_target.pkl
"""
import datetime as dt
import glob
import hashlib
import os
import pickle
import sys

import numpy as np
from qiskit_ibm_runtime import QiskitRuntimeService

import snapshot


def fingerprint(snap):
    """Two queries that return the same calibration cycle produce the same fingerprint."""
    vals = np.concatenate([snap["err_1q"], snap["err_ro"], list(snap["err_2q"].values())])
    return hashlib.md5(np.nan_to_num(vals).round(8).tobytes()).hexdigest()


def get_backend(name):
    service = QiskitRuntimeService()
    available = [b.name for b in service.backends()]
    print("Devices this account can use:", available)
    if name not in available:
        sys.exit(f"'{name}' is not available to this account. Re-run with one of the names above.")
    return service.backend(name)


def snapshot_at(backend, when, cycle):
    """Try method 1 (properties with a date). If refused, try method 2 (target_history)."""
    try:
        props = backend.properties(datetime=when)
        if props is not None:
            return snapshot.from_properties(props, backend.target, backend.name, cycle)
    except Exception as e:
        print(f"  properties(datetime=) refused: {type(e).__name__}: {e}")
    try:
        t = backend.target_history(datetime=when)
        return snapshot.from_target(t, backend.name, cycle, timestamp=when.isoformat())
    except Exception as e:
        print(f"  target_history(datetime=) refused: {type(e).__name__}: {e}")
    return None


def history(name, days):
    backend = get_backend(name)
    folder = os.path.join("snapshots", name)
    os.makedirs(folder, exist_ok=True)
    with open(os.path.join(folder, "base_target.pkl"), "wb") as f:
        pickle.dump(backend.target, f)
    now = dt.datetime.now(dt.timezone.utc)
    found, seen = [], set()
    for d in range(days):
        when = now - dt.timedelta(days=d)
        snap = snapshot_at(backend, when, cycle=0)
        if snap is None:
            print(f"No historical data for {when.date()}. If this happens for every date, use 'log' mode.")
            continue
        fp = fingerprint(snap)
        if fp in seen:
            continue                      # same calibration cycle as one we already have
        seen.add(fp)
        found.append(snap)
        print(f"  found snapshot {snap['timestamp']}")
    found.reverse()                       # oldest first
    for i, snap in enumerate(found):
        snap["cycle"] = i
        snapshot.save(snap, folder)
    print(f"Saved {len(found)} unique snapshots to {folder}/")


def log(name):
    backend = get_backend(name)
    folder = os.path.join("snapshots", name)
    os.makedirs(folder, exist_ok=True)
    pkl = os.path.join(folder, "base_target.pkl")
    if not os.path.exists(pkl):
        with open(pkl, "wb") as f:
            pickle.dump(backend.target, f)
    props = backend.properties(refresh=True)
    existing = snapshot.load_series(folder)
    snap = snapshot.from_properties(props, backend.target, name, cycle=len(existing))
    if existing and fingerprint(existing[-1]) == fingerprint(snap):
        print("Device has not recalibrated since the last save. Nothing new to store.")
        return
    print("Saved", snapshot.save(snap, folder))


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "history":
        history(sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 30)
    elif len(sys.argv) >= 3 and sys.argv[1] == "log":
        log(sys.argv[2])
    else:
        print(__doc__)
