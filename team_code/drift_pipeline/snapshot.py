"""M2 - Snapshot tools.

A "snapshot" is one calibration cycle of a device, stored as a plain dict:
    source, cycle, timestamp      - where and when it came from
    t1, t2                        - per qubit, in seconds
    err_1q                        - per qubit, single-qubit gate (sx) error
    err_ro                        - per qubit, readout (measurement) error
    err_2q                        - per connection "a-b" (a < b), two-qubit gate error

Synthetic and real IBM snapshots use the exact same format, so nothing after
ingestion cares where the data came from.

This file converts:  IBM data -> snapshot,  snapshot -> Qiskit Target (what the
compiler reads),  Target -> Aer NoiseModel (the simulated device).
"""
import copy
import glob
import json
import math
import os

import numpy as np
from qiskit.providers import BackendV2, Options, QubitProperties
from qiskit.transpiler import InstructionProperties
from qiskit_aer.noise import NoiseModel

import config


# ---------- file input / output ----------

def save(snap, folder):
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, f"cycle_{snap['cycle']:03d}.json")
    out = dict(snap)
    for key in ("t1", "t2", "err_1q", "err_ro"):
        out[key] = [None if v is None or math.isnan(v) else float(v) for v in snap[key]]
    out["err_2q"] = {k: (None if v is None or math.isnan(v) else float(v)) for k, v in snap["err_2q"].items()}
    with open(path, "w") as f:
        json.dump(out, f)
    return path


def load_series(folder):
    """Load every snapshot in a folder, sorted by cycle number."""
    snaps = []
    for path in sorted(glob.glob(os.path.join(folder, "cycle_*.json"))):
        with open(path) as f:
            s = json.load(f)
        for key in ("t1", "t2", "err_1q", "err_ro"):
            s[key] = np.array([np.nan if v is None else v for v in s[key]], dtype=float)
        s["err_2q"] = {k: (np.nan if v is None else v) for k, v in s["err_2q"].items()}
        snaps.append(s)
    snaps.sort(key=lambda s: s["cycle"])
    return snaps


# ---------- building snapshots from IBM data ----------

def edge_key(a, b):
    a, b = sorted((a, b))
    return f"{a}-{b}"


def edges_of(target):
    """All undirected connections that have a two-qubit gate."""
    return sorted({edge_key(a, b) for (a, b) in target[config.TWO_QUBIT_GATE].keys()},
                  key=lambda k: tuple(map(int, k.split("-"))))


def from_target(target, source, cycle, timestamp=""):
    n = target.num_qubits
    qp = target.qubit_properties
    def err(gate, qargs):
        props = target[gate].get(qargs)
        return np.nan if props is None or props.error is None else props.error
    snap = {
        "source": source, "cycle": cycle, "timestamp": str(timestamp),
        "t1": np.array([qp[q].t1 if qp[q] and qp[q].t1 else np.nan for q in range(n)]),
        "t2": np.array([qp[q].t2 if qp[q] and qp[q].t2 else np.nan for q in range(n)]),
        "err_1q": np.array([err("sx", (q,)) for q in range(n)]),
        "err_ro": np.array([err("measure", (q,)) for q in range(n)]),
        "err_2q": {},
    }
    for k in edges_of(target):
        a, b = map(int, k.split("-"))
        e = err(config.TWO_QUBIT_GATE, (a, b))
        if np.isnan(e):
            e = err(config.TWO_QUBIT_GATE, (b, a))
        snap["err_2q"][k] = e
    return snap


def from_properties(props, base_target, source, cycle):
    """Convert an IBM BackendProperties object (from backend.properties(datetime=...))."""
    n = base_target.num_qubits
    def safe(fn, *args):
        try:
            v = fn(*args)
            return np.nan if v is None else float(v)
        except Exception:
            return np.nan
    snap = {
        "source": source, "cycle": cycle, "timestamp": str(props.last_update_date),
        "t1": np.array([safe(props.t1, q) for q in range(n)]),
        "t2": np.array([safe(props.t2, q) for q in range(n)]),
        "err_1q": np.array([safe(props.gate_error, "sx", q) for q in range(n)]),
        "err_ro": np.array([safe(props.readout_error, q) for q in range(n)]),
        "err_2q": {},
    }
    for k in edges_of(base_target):
        a, b = map(int, k.split("-"))
        e = safe(props.gate_error, config.TWO_QUBIT_GATE, [a, b])
        if np.isnan(e):
            e = safe(props.gate_error, config.TWO_QUBIT_GATE, [b, a])
        snap["err_2q"][k] = e
    return snap


def uniform(snap):
    """Same device, but every qubit and connection gets the median value.
    Used for the 'Blind' strategy: the compiler cannot tell good qubits from bad."""
    u = copy.deepcopy(snap)
    for key in ("t1", "t2", "err_1q", "err_ro"):
        u[key] = np.full_like(snap[key], np.nanmedian(snap[key]))
    med = float(np.nanmedian(list(snap["err_2q"].values())))
    u["err_2q"] = {k: med for k in snap["err_2q"]}
    return u


# ---------- snapshot -> Target (what the compiler reads) ----------

def clean(snap):
    """Apply decision D8: missing or impossible values become 'very bad' values."""
    s = copy.deepcopy(snap)
    for key in ("err_1q", "err_ro"):
        v = s[key]
        s[key] = np.where(np.isnan(v), config.ERR_CAP, np.clip(v, 1e-6, config.ERR_CAP))
    s["err_2q"] = {k: (config.ERR_CAP if np.isnan(v) else float(np.clip(v, 1e-6, config.ERR_CAP)))
                   for k, v in s["err_2q"].items()}
    t1 = np.where(np.isnan(s["t1"]) | (s["t1"] <= 0), config.MISSING_T1, s["t1"])
    t2 = np.where(np.isnan(s["t2"]) | (s["t2"] <= 0), t1, s["t2"])
    s["t1"], s["t2"] = t1, np.minimum(t2, 2 * t1)   # physics: T2 can never exceed 2 x T1 (Aer enforces this)
    return s


def to_target(snap, base_target):
    """Copy the device's structure (connections, gate durations) and write in this snapshot's numbers."""
    s = clean(snap)
    t = copy.deepcopy(base_target)
    t.qubit_properties = [
        QubitProperties(t1=float(s["t1"][q]), t2=float(s["t2"][q]),
                        frequency=(base_target.qubit_properties[q].frequency
                                   if base_target.qubit_properties[q] else None))
        for q in range(t.num_qubits)
    ]
    for gate, values in (("sx", s["err_1q"]), ("x", s["err_1q"]), ("measure", s["err_ro"])):
        for qargs, props in base_target[gate].items():
            if props is None:
                continue
            t.update_instruction_properties(
                gate, qargs, InstructionProperties(duration=props.duration, error=float(values[qargs[0]])))
    for qargs, props in base_target[config.TWO_QUBIT_GATE].items():
        if props is None:
            continue
        e = s["err_2q"].get(edge_key(*qargs), config.ERR_CAP)
        t.update_instruction_properties(
            config.TWO_QUBIT_GATE, qargs, InstructionProperties(duration=props.duration, error=float(e)))
    return t


# ---------- Target -> NoiseModel (the simulated device) ----------

class _TargetOnlyBackend(BackendV2):
    """Tiny wrapper so Aer's standard NoiseModel.from_backend can read any Target we build."""
    def __init__(self, target):
        super().__init__(name="snapshot_backend")
        self._target = target

    @property
    def target(self):
        return self._target

    @property
    def max_circuits(self):
        return None

    @classmethod
    def _default_options(cls):
        return Options()

    def run(self, *args, **kwargs):
        raise NotImplementedError("This backend only describes a device; it cannot run jobs.")


def noise_model(target):
    """Aer's standard device noise: T1/T2 decay + depolarizing error to match each gate's error + readout error."""
    return NoiseModel.from_backend(_TargetOnlyBackend(target))
