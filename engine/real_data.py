"""Connector: real IBM calibration states -> the teammates' snapshot format.

OURS. This file is not part of the teammates' pipeline. It is the bridge
between my 921 real calibration states and their snapshot/Target/Aer machinery.

What it does:
  1. Amendment A1.1. states.csv is an INDEX. The numbers come from
     data/clean/qubits.csv and pairs.csv, joined on machine plus snapshot_utc
     equal to the state's first_seen_utc. T1 and T2 are converted from
     microseconds to seconds, because the team's format stores seconds.
  2. Dead qubits (L-016 rule) are made IMPOSSIBLE for the compiler to pick, by
     removing them from the Target the strategy sees, BEFORE any number
     reaches the compiler. See forbid_dead() for the method and its costs.
  3. The TRUTH device keeps every qubit with its real values, so a stale pick
     that lands on a now dead qubit is punished instead of being quietly
     rescued.

Truth values are clipped only at Aer's own ceiling, never below it. Measured,
not assumed: Aer silently clamps 1 qubit gate error at 0.75 and 2 qubit gate
error at 0.9375, giving the identical channel above those and no warning. The
team's ERR_CAP of 0.5 is far below that and would hide how bad a dead gate is,
so it is NOT used for truth. Every clip is counted and reported.
"""
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from qiskit.transpiler import InstructionProperties, Target
from qiskit.providers import QubitProperties

import engine_config as cfg

ROOT = Path(__file__).resolve().parent.parent      # the project root
CLEAN = ROOT / "data/clean"
TARGETS = ROOT / "data/targets"
CACHE_DIR = ROOT / "data/cache"
FIELDS = ["t1", "t2", "err_ro", "err_1q", "err_2q"]
MISSING_T1_S = 10e-6        # the team's stand in for a missing T1, in seconds


# ---------------------------------------------------------------- loading

def load_tables():
    states = pd.read_csv(CLEAN / "states.csv")
    qubits = pd.read_csv(CLEAN / "qubits.csv")
    pairs = pd.read_csv(CLEAN / "pairs.csv")
    for df in (states, qubits, pairs):
        col = "first_seen_utc" if "first_seen_utc" in df else "snapshot_utc"
        df[col] = pd.to_datetime(df[col], utc=True)
    return states, qubits, pairs


def _index_at_or_before(self, when):
    """Position of the newest state published at or before `when`."""
    lo, hi = 0, len(self.times) - 1
    best = -1
    while lo <= hi:
        mid = (lo + hi) // 2
        if self.times[mid] <= when:
            best, lo = mid, mid + 1
        else:
            hi = mid - 1
    return best


def open_store(machine, tables=None):
    """Use the fast cache when it exists, otherwise read data/clean."""
    if (CACHE_DIR / f"{machine}.npz").exists():
        return CachedStateStore(machine)
    states, qubits, pairs = tables if tables else load_tables()
    return StateStore(machine, states, qubits, pairs)


def load_base_target(machine):
    with open(TARGETS / f"{machine}_base_target.pkl", "rb") as fh:
        blob = pickle.load(fh)
    return blob["target"], blob["meta"]


class CachedStateStore:
    """Same interface as StateStore, loaded from the compact npz cache.

    OURS, speed only. Every array is the float64 written by prepare_cache.py,
    which took it straight from data/clean, so the numbers are identical.
    """

    _ORDER = ["t1", "t2", "err_ro", "err_1q", "err_2q"]

    def __init__(self, machine):
        z = np.load(CACHE_DIR / f"{machine}.npz", allow_pickle=False)
        self.machine = machine
        self._z = {k: z[k] for k in z.files}
        self.n_qubits = int(self._z["n_qubits"][0])
        self._keys = [str(k) for k in self._z["pair_keys"]]
        self.times = [pd.Timestamp(int(t), unit="s", tz="UTC")
                      for t in self._z["times"]]
        self._cache = {}

    def __len__(self):
        return len(self.times)

    index_at_or_before = None     # bound below, shared with StateStore

    def snapshot(self, i):
        if i in self._cache:
            return self._cache[i]
        z = self._z
        dates = {f: str(z["value_dates"][i, j])
                 for j, f in enumerate(self._ORDER)}
        snap = {
            "source": self.machine, "cycle": i,
            "timestamp": str(self.times[i]), "first_seen": self.times[i],
            "t1": z["t1"][i], "t2": z["t2"][i],
            "err_1q": z["err_1q"][i], "err_ro": z["err_ro"][i],
            "err_2q": {k: float(v) for k, v in zip(self._keys, z["err_2q"][i])
                       if not np.isnan(v)},
            "value_dates": dates,
        }
        self._cache[i] = snap
        return snap


class StateStore:
    """Every state of one machine, in time order, with its numbers and the
    date printed on each value (the clock from L-016 decision 1)."""

    def __init__(self, machine, states, qubits, pairs):
        self.machine = machine
        s = states[states.machine == machine].sort_values("first_seen_utc")
        self.times = list(s.first_seen_utc)
        self.rows = s.to_dict("records")
        q = qubits[qubits.machine == machine]
        p = pairs[pairs.machine == machine]
        self._q = {t: g for t, g in q.groupby("snapshot_utc")}
        self._p = {t: g for t, g in p.groupby("snapshot_utc")}
        self.n_qubits = int(q.qubit.max()) + 1
        self._cache = {}

    def __len__(self):
        return len(self.times)

    def index_at_or_before(self, when):
        """Position of the newest state published at or before `when`."""
        lo, hi = 0, len(self.times) - 1
        best = -1
        while lo <= hi:
            mid = (lo + hi) // 2
            if self.times[mid] <= when:
                best, lo = mid, mid + 1
            else:
                hi = mid - 1
        return best

    def snapshot(self, i):
        """One state as a snapshot dict in the teammates' format."""
        if i in self._cache:
            return self._cache[i]
        stamp = self.times[i]
        row = self.rows[i]
        n = self.n_qubits
        q = self._q[stamp].sort_values("qubit")
        p = self._p.get(stamp)

        t1 = np.full(n, np.nan)
        t2 = np.full(n, np.nan)
        e1 = np.full(n, np.nan)
        ro = np.full(n, np.nan)
        idx = q.qubit.to_numpy()
        t1[idx] = q.t1_us.to_numpy() * 1e-6          # microseconds -> seconds
        t2[idx] = q.t2_us.to_numpy() * 1e-6
        e1[idx] = q.sx_error.to_numpy()
        ro[idx] = q.readout_error.to_numpy()
        e2 = {}
        if p is not None:
            for a, b, v in zip(p.qubit_a, p.qubit_b, p.cz_error):
                a, b = int(a), int(b)
                e2[f"{min(a,b)}-{max(a,b)}"] = float(v)

        snap = {
            "source": self.machine, "cycle": i, "timestamp": str(stamp),
            "first_seen": stamp,
            "t1": t1, "t2": t2, "err_1q": e1, "err_ro": ro, "err_2q": e2,
            # the date printed on each field's values (L-016 decision 1 clock)
            "value_dates": {
                "t1": row.get("T1_date_median_utc"),
                "t2": row.get("T2_date_median_utc"),
                "err_ro": row.get("readout_error_date_median_utc"),
                "err_1q": row.get("sx_error_date_median_utc"),
                "err_2q": row.get("cz_error_date_median_utc"),
            },
        }
        self._cache[i] = snap
        return snap


# ------------------------------------------------------- the dead qubit rule

def dead_qubits(snap):
    """L-016 decision 2 / PROTOCOL.md section 7:
         sx_error > 0.1, or readout_error > 0.2, or T1 missing, or T2 missing.

    ENGINE EXTENSION, logged on purpose: a qubit whose sx_error or
    readout_error is MISSING is also treated as dead. The frozen rule cannot be
    evaluated on a missing number, and a qubit that cannot be scored must not
    be chosen. This is a superset of the frozen rule, never a relaxation.
    """
    n = len(snap["t1"])
    dead = set()
    for i in range(n):
        t1, t2 = snap["t1"][i], snap["t2"][i]
        sx, ro = snap["err_1q"][i], snap["err_ro"][i]
        if np.isnan(t1) or np.isnan(t2) or np.isnan(sx) or np.isnan(ro):
            dead.add(i)
        elif sx > cfg.SX_DEAD or ro > cfg.RO_DEAD:
            dead.add(i)
    return dead


# --------------------------------------------------- snapshot -> Target

def _clip(value, ceiling, counter, key):
    if np.isnan(value):
        counter[key + "_missing"] += 1
        return ceiling
    if value > ceiling:
        counter[key + "_clipped"] += 1
        return ceiling
    return float(max(value, 1e-9))


def _times(t1, t2, counter):
    if np.isnan(t1) or t1 <= 0:
        counter["t1_missing"] += 1
        t1 = MISSING_T1_S
    if np.isnan(t2) or t2 <= 0:
        counter["t2_missing"] += 1
        t2 = t1
    if t2 > 2 * t1:                      # physics, and Aer enforces it
        counter["t2_over_2t1"] += 1
        t2 = 2 * t1
    return float(t1), float(t2)


def build_target(snap, base, forbid=frozenset(), counter=None):
    """Write one snapshot's numbers into a copy of the machine description.

    `forbid` is the set of qubits to make UNUSABLE. They are removed from every
    instruction, so the compiler has no gate it can place on them.
    """
    if counter is None:
        counter = {}
    for k in ["err_1q_clipped", "err_1q_missing", "err_2q_clipped",
              "err_2q_missing", "err_ro_clipped", "err_ro_missing",
              "t1_missing", "t2_missing", "t2_over_2t1"]:
        counter.setdefault(k, 0)

    n = base.num_qubits
    live = [q for q in range(n) if q not in forbid]
    qprops = []
    for q in range(n):
        t1, t2 = _times(snap["t1"][q], snap["t2"][q], counter)
        qprops.append(QubitProperties(t1=t1, t2=t2, frequency=None))

    target = Target(num_qubits=n, qubit_properties=qprops)

    def one_q(name, values, ceiling, key):
        out = {}
        for q in live:
            props = base[name].get((q,))
            if props is None:
                continue
            out[(q,)] = InstructionProperties(
                duration=props.duration,
                error=_clip(values[q], ceiling, counter, key))
        return out

    for name in ("sx", "x"):
        target.add_instruction(base.operation_from_name(name),
                               one_q(name, snap["err_1q"], cfg.AER_MAX_1Q, "err_1q"))
    rz = {(q,): InstructionProperties(duration=0.0, error=0.0) for q in live
          if base["rz"].get((q,)) is not None}
    target.add_instruction(base.operation_from_name("rz"), rz)

    target.add_instruction(base.operation_from_name("measure"),
                           one_q("measure", snap["err_ro"], 1.0, "err_ro"))
    reset = {(q,): InstructionProperties(duration=base["reset"][(q,)].duration,
                                         error=0.0)
             for q in live if base["reset"].get((q,)) is not None}
    target.add_instruction(base.operation_from_name("reset"), reset)

    cz = {}
    for qargs, props in base["cz"].items():
        a, b = qargs
        if a in forbid or b in forbid:
            continue
        key = f"{min(a,b)}-{max(a,b)}"
        val = snap["err_2q"].get(key, np.nan)
        cz[qargs] = InstructionProperties(
            duration=props.duration,
            error=_clip(val, cfg.AER_MAX_2Q, counter, "err_2q"))
    target.add_instruction(base.operation_from_name("cz"), cz)
    return target, counter


def strategy_target(snap, base, permanent, counter=None):
    """What the compiler sees. Dead qubits of THIS snapshot plus the permanent
    defects are removed, so the compiler cannot choose them."""
    forbid = dead_qubits(snap) | set(permanent)
    target, counter = build_target(snap, base, forbid=forbid, counter=counter)
    return target, forbid, counter


def truth_target(snap, base, permanent, counter=None):
    """The device the job really runs on. Every qubit keeps its real value, so
    a stale pick that lands on a now dead qubit is punished. Only the permanent
    defects are removed, because PROTOCOL.md section 7 excludes those for every
    arm including the ceiling."""
    return build_target(snap, base, forbid=set(permanent), counter=counter)


def live_coupling(target):
    """Undirected neighbour map of the qubits that still have a cz gate."""
    adj = {}
    for (a, b) in target["cz"]:
        adj.setdefault(a, set()).add(b)
        adj.setdefault(b, set()).add(a)
    return adj


CachedStateStore.index_at_or_before = _index_at_or_before
