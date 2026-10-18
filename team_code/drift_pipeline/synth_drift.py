"""M1b - Synthetic drift (fallback data source, decision D9).

Starts from IBM's REAL published calibration snapshot of ibm_torino (ships with
Qiskit as FakeTorino) and makes up how it might change over SYNTH_CYCLES
calibration cycles. Everything here is an assumption, clearly labelled, and is
replaced by real IBM snapshots once ingest_ibm.py works.

The drift model, in plain words:
  * Each qubit gets its own "swinginess". Most qubits are steady; a few swing a lot.
  * Each cycle, a qubit's errors move up or down randomly. Part of last cycle's
    deviation carries over (SYNTH_PERSISTENCE), so changes fade rather than vanish instantly.
  * Occasionally a qubit takes a sudden jump (3x-10x worse), like a TLS defect
    switching on. Swingy qubits jump more often.
  * When a qubit gets worse: gate error goes up, T1/T2 go down, readout gets
    somewhat worse (square root of the change), and its connections get worse.

Usage:  python synth_drift.py        -> writes snapshots/synthetic/cycle_000.json ...
"""
import os

import numpy as np
from qiskit_ibm_runtime.fake_provider import FakeTorino

import config
import snapshot


def generate():
    rng = np.random.default_rng(config.SYNTH_SEED)
    base_target = FakeTorino().target
    base = snapshot.from_target(base_target, source="synthetic", cycle=0, timestamp="cycle 0")
    n = base_target.num_qubits
    edges = list(base["err_2q"].keys())

    swing = rng.lognormal(np.log(config.SYNTH_VOL_MEDIAN), config.SYNTH_VOL_SPREAD, size=n)
    jump_chance = config.SYNTH_JUMP_RATE * swing / swing.mean()
    edge_swing = 0.1                                   # small extra drift on each connection

    log_m = np.zeros(n)                                # log of each qubit's "worse-by" multiplier
    log_e = np.zeros(len(edges))
    folder = os.path.join(config.SNAPSHOT_DIR, "synthetic")
    for cycle in range(config.SYNTH_CYCLES):
        if cycle > 0:
            log_m = config.SYNTH_PERSISTENCE * log_m + rng.normal(0, swing)
            jumps = rng.random(n) < jump_chance
            log_m += jumps * np.log(rng.uniform(config.SYNTH_JUMP_MIN, config.SYNTH_JUMP_MAX, size=n))
            log_e = config.SYNTH_PERSISTENCE * log_e + rng.normal(0, edge_swing, size=len(edges))
        m = np.exp(log_m)
        snap = {
            "source": "synthetic", "cycle": cycle, "timestamp": f"cycle {cycle}",
            "t1": base["t1"] / m,
            "t2": base["t2"] / m,
            "err_1q": np.minimum(base["err_1q"] * m, config.ERR_CAP),
            "err_ro": np.minimum(base["err_ro"] * np.sqrt(m), config.ERR_CAP),
            "err_2q": {},
        }
        for i, k in enumerate(edges):
            a, b = map(int, k.split("-"))
            snap["err_2q"][k] = float(min(base["err_2q"][k] * max(m[a], m[b]) * np.exp(log_e[i]),
                                          config.ERR_CAP))
        snapshot.save(snap, folder)
    print(f"wrote {config.SYNTH_CYCLES} synthetic snapshots to {folder}/")


if __name__ == "__main__":
    generate()
