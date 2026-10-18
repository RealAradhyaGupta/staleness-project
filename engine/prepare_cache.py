"""Build a compact per-machine cache of the states, once.

OURS. A speed-up only. It must not change a single number, so every value is
stored as float64 exactly as it sits in data/clean, with no rounding and no
dtype narrowing.

Why. Each worker process in the parallel runner would otherwise read
qubits.csv (69 MB) and pairs.csv (45 MB) and group them, which costs time and,
on an 8 GB machine with 8 workers, far too much memory. The real numbers for
one machine are tiny: 276 states x 156 qubits x 4 fields is about 1.4 MB.

Writes data/cache/<machine>.npz. Delete the folder to force a rebuild.
"""
from pathlib import Path

import numpy as np

import real_data as rd

CACHE = rd.ROOT / "data" / "cache"
FIELD_DATE_COL = {
    "t1": "T1_date_median_utc", "t2": "T2_date_median_utc",
    "err_ro": "readout_error_date_median_utc",
    "err_1q": "sx_error_date_median_utc",
    "err_2q": "cz_error_date_median_utc",
}


def build(machine, states, qubits, pairs):
    store = rd.StateStore(machine, states, qubits, pairs)
    n = len(store)
    nq = store.n_qubits
    keys = sorted({f"{min(int(a),int(b))}-{max(int(a),int(b))}"
                   for a, b in zip(pairs[pairs.machine == machine].qubit_a,
                                   pairs[pairs.machine == machine].qubit_b)},
                  key=lambda k: tuple(map(int, k.split("-"))))
    kidx = {k: i for i, k in enumerate(keys)}

    t1 = np.full((n, nq), np.nan)
    t2 = np.full((n, nq), np.nan)
    e1 = np.full((n, nq), np.nan)
    ro = np.full((n, nq), np.nan)
    e2 = np.full((n, len(keys)), np.nan)
    dates = np.empty((n, 5), dtype=object)
    dates[:] = ""
    order = ["t1", "t2", "err_ro", "err_1q", "err_2q"]

    for i in range(n):
        s = store.snapshot(i)
        t1[i], t2[i], e1[i], ro[i] = s["t1"], s["t2"], s["err_1q"], s["err_ro"]
        for k, v in s["err_2q"].items():
            e2[i, kidx[k]] = v
        for j, f in enumerate(order):
            d = s["value_dates"].get(f)
            # keep the EXACT string from data/clean. Truncating to whole
            # seconds shifted the reported ages by up to 0.001 h, which is a
            # changed number and therefore not allowed in a speed-up.
            dates[i, j] = "" if d is None or (isinstance(d, float) and np.isnan(d)) else str(d)

    times = np.array([t.value // 10**9 for t in store.times], dtype=np.int64)
    CACHE.mkdir(parents=True, exist_ok=True)
    out = CACHE / f"{machine}.npz"
    np.savez(out, times=times, t1=t1, t2=t2, err_1q=e1, err_ro=ro,
             err_2q=e2, pair_keys=np.array(keys),
             value_dates=dates.astype(str),
             n_qubits=np.array([nq]))
    print(f"  {machine}: {n} states, {nq} qubits, {len(keys)} cz pairs "
          f"-> {out} ({out.stat().st_size/1e6:.1f} MB)")
    return out


def main():
    print("building per machine caches (speed only, no number changes)")
    states, qubits, pairs = rd.load_tables()
    for machine in sorted(states.machine.unique()):
        build(machine, states, qubits, pairs)


if __name__ == "__main__":
    main()
