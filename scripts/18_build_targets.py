"""Build one base Target per machine, offline, from the cards already on disk.

A base target is the machine DESCRIPTION: how many qubits, which pairs are
connected, which gates exist, and how long each gate takes. It carries no
staleness question of its own, because the engine overwrites every error and
every T1/T2 with the numbers of whatever state a strategy is allowed to see.

This answers risk 7 of PROTOCOL.md section 17. The teammates' pipeline takes
its base target from FakeTorino, which is a 133 qubit machine and the wrong
device for my three 156 qubit machines.

No network call and no IBM key. Everything needed is already in data/raw:
  - coupling pairs      from the qubit lists on every cz gate record
  - basis gates         from the gate names
  - durations           from each record's gate_length parameter (ns)
  - readout duration    from readout_length on each qubit (ns)

Before building, this CHECKS rather than assumes that the topology and the
durations stay the same across the whole window, and prints every change it
finds.

Durations in a Qiskit Target are in seconds, so ns values are multiplied by
1e-9. rz is virtual on these machines (gate_length 0) so it is written with
duration 0 and error 0 rather than copied from a card.

Writes data/targets/<machine>_base_target.pkl, read-only, each with a metadata
dict recording when it was built, from which card, and the library versions.
data/raw is only read.
"""
import gzip
import json
import pickle
import platform
import stat
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import qiskit
from qiskit.circuit import Parameter
from qiskit.circuit.library import CZGate, Measure, Reset, RZGate, SXGate, XGate
from qiskit.providers import QubitProperties
from qiskit.transpiler import InstructionProperties, Target

RAW = Path("data/raw")
OUT = Path("data/targets")
WINDOW_START = datetime(2026, 8, 28, 0, 0, 0, tzinfo=timezone.utc)
NS = 1e-9


def load(path):
    if path.name.endswith(".gz"):
        with gzip.open(path, "rt") as fh:
            return json.load(fh)
    with open(path) as fh:
        return json.load(fh)


def structure_of(data):
    """The description only: no error values, no T1/T2."""
    durations = {}
    for g in data.get("gates") or []:
        length = None
        for p in g["parameters"]:
            if p["name"] == "gate_length":
                length = p["value"]
        durations[(g["gate"], tuple(g["qubits"]))] = length
    cz = frozenset(tuple(sorted(g["qubits"])) for g in (data.get("gates") or [])
                   if g["gate"] == "cz")
    gates = frozenset(g["gate"] for g in (data.get("gates") or []))
    ro_len = tuple(next((e["value"] for e in q if e["name"] == "readout_length"), None)
                   for q in (data.get("qubits") or []))
    return {"n_qubits": len(data.get("qubits") or []), "cz_pairs": cz,
            "gate_names": gates, "durations": durations, "readout_length": ro_len}


def errors_of(data):
    """gate_error per (gate, qargs), used only to give the base target sane
    starting numbers. The engine overwrites all of these."""
    out = {}
    for g in data.get("gates") or []:
        for p in g["parameters"]:
            if p["name"] == "gate_error":
                out[(g["gate"], tuple(g["qubits"]))] = p["value"]
    return out


def readout_error_of(data):
    return [next((e["value"] for e in q if e["name"] == "readout_error"), 0.01)
            for q in (data.get("qubits") or [])]


def scan(machine):
    files = sorted(list((RAW / machine).glob("*.json"))
                   + list((RAW / machine).glob("*.json.gz")), key=lambda p: p.name)
    seen = defaultdict(list)          # structure signature -> [card names]
    reference = None
    n_used = 0
    for path in files:
        data = load(path)
        stamp = datetime.fromisoformat(str(data["last_update_date"])).astimezone(timezone.utc)
        if stamp < WINDOW_START:
            continue
        n_used += 1
        s = structure_of(data)
        key = (s["n_qubits"], s["cz_pairs"], s["gate_names"],
               tuple(sorted(s["durations"].items())), s["readout_length"])
        seen[key].append(path.name)
        # reference = the newest card that has the full cz topology
        if len(s["cz_pairs"]) == 176:
            reference = (path, data, s)
    return files, n_used, seen, reference


def build_target(machine, data, struct):
    n = struct["n_qubits"]
    err = errors_of(data)
    ro_err = readout_error_of(data)
    dur = struct["durations"]

    target = Target(num_qubits=n, qubit_properties=[
        QubitProperties(t1=None, t2=None, frequency=None) for _ in range(n)])

    def props_1q(gate_name, virtual=False):
        out = {}
        for q in range(n):
            d = dur.get((gate_name, (q,)))
            if d is None:
                continue
            out[(q,)] = InstructionProperties(
                duration=0.0 if virtual else d * NS,
                error=0.0 if virtual else err.get((gate_name, (q,)), 0.0))
        return out

    target.add_instruction(SXGate(), props_1q("sx"))
    target.add_instruction(XGate(), props_1q("x"))
    target.add_instruction(RZGate(Parameter("theta")), props_1q("rz", virtual=True))

    meas = {}
    reset = {}
    for q in range(n):
        d = dur.get(("measure", (q,)))
        if d is not None:
            meas[(q,)] = InstructionProperties(duration=d * NS, error=ro_err[q])
        dr = dur.get(("reset", (q,)))
        if dr is not None:
            reset[(q,)] = InstructionProperties(duration=dr * NS, error=0.0)
    target.add_instruction(Measure(), meas)
    target.add_instruction(Reset(), reset)

    cz = {}
    for (gate, qargs), d in dur.items():
        if gate != "cz":
            continue
        cz[qargs] = InstructionProperties(duration=d * NS,
                                          error=err.get((gate, qargs), 0.01))
    target.add_instruction(CZGate(), cz)
    return target


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    machines = sorted(d.name for d in RAW.iterdir() if d.is_dir())
    print(f"qiskit {qiskit.__version__} | python {platform.python_version()}")
    print(f"window from {WINDOW_START.isoformat()}\n")

    for machine in machines:
        t0 = time.time()
        print(f"=== {machine} ===", flush=True)
        files, n_used, seen, reference = scan(machine)
        print(f"  cards read: {len(files)}, in window: {n_used}, "
              f"scan took {time.time()-t0:.0f}s")
        print(f"  DISTINCT machine descriptions in the window: {len(seen)}")
        for i, (key, names) in enumerate(sorted(seen.items(), key=lambda kv: -len(kv[1])), 1):
            n_q, cz_pairs, gate_names, durations, ro = key
            print(f"    description {i}: {len(names)} cards, {n_q} qubits, "
                  f"{len(cz_pairs)} cz pairs, {len(gate_names)} gate types")
            if len(names) <= 6:
                print(f"       cards: {', '.join(names)}")
        # what actually differs between descriptions
        if len(seen) > 1:
            keys = list(seen)
            base = keys[0]
            for k in keys[1:]:
                diffs = []
                if k[0] != base[0]:
                    diffs.append(f"n_qubits {base[0]} vs {k[0]}")
                if k[1] != base[1]:
                    diffs.append(f"cz pairs differ by {len(base[1] ^ k[1])}")
                if k[2] != base[2]:
                    diffs.append(f"gate names differ: {set(base[2]) ^ set(k[2])}")
                if k[3] != base[3]:
                    d1, d2 = dict(base[3]), dict(k[3])
                    moved = [g for g in d1 if d1.get(g) != d2.get(g)]
                    diffs.append(f"{len(moved)} durations differ, e.g. "
                                 f"{moved[:3]}")
                if k[4] != base[4]:
                    diffs.append("readout_length differs")
                print(f"       vs description 1: {'; '.join(diffs)}")

        path, data, struct = reference
        print(f"  reference card: {path.name} "
              f"(backend_version {data.get('backend_version')})")
        target = build_target(machine, data, struct)
        print(f"  built Target: {target.num_qubits} qubits, "
              f"operations {sorted(target.operation_names)}, "
              f"{len(target['cz'])} directed cz entries")

        meta = {
            "machine": machine,
            "built_utc": datetime.now(timezone.utc).isoformat(),
            "built_from_card": str(path),
            "backend_version": data.get("backend_version"),
            "cards_in_window": n_used,
            "distinct_descriptions_in_window": len(seen),
            "qiskit_version": qiskit.__version__,
            "python_version": platform.python_version(),
            "source": "built offline from data/raw, no IBM API call",
            "note": ("errors and T1/T2 in this target are placeholders from the "
                     "reference card. The engine overwrites every one of them "
                     "with the state a strategy is allowed to see."),
        }
        out = OUT / f"{machine}_base_target.pkl"
        if out.exists():
            out.chmod(0o644)
        with open(out, "wb") as fh:
            pickle.dump({"target": target, "meta": meta}, fh)
        out.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
        print(f"  wrote {out} ({out.stat().st_size} bytes, mode 444) "
              f"in {time.time()-t0:.0f}s\n", flush=True)

    print("No IBM API call was made. No key was read. data/raw was only read.")


main()
