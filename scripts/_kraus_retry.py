"""Run ONE simulation as the first simulation in a fresh process.

OURS. Written for L-037. Aer 0.17.2 raises "QuantumError: Kraus is empty" for
a few compiled circuits, but only when something else has already been
simulated in the same process. The same circuit, same noise model and same
seed succeed when they are the first simulation the process does. This script
is that fresh process. It does nothing else, so the retried simulation is
always first.

Input: a pickle holding {"isa", "seed", "machine", "truth_state", "shots"}.
Output: the counts dictionary as JSON on stdout.

The noise model is rebuilt here from the machine name and the truth state
index through exactly the same calls the runner uses, so it cannot drift from
the one the runner holds.
"""
import json
import pickle
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "engine"))

from qiskit_aer import AerSimulator          # noqa: E402

import real_data as rd                       # noqa: E402
import run_engine as R                       # noqa: E402
import snapshot as team_snapshot             # noqa: E402


def main():
    job = pickle.loads(Path(sys.argv[1]).read_bytes())
    m = job["machine"]
    store = rd.open_store(m)
    base = rd.load_base_target(m)[0]
    perm = R.permanent_defects(store)
    tt, _ = rd.truth_target(store.snapshot(job["truth_state"]), base, perm)
    sim = AerSimulator(noise_model=team_snapshot.noise_model(tt),
                       max_parallel_threads=1, max_parallel_experiments=1)
    counts = sim.run(job["isa"], shots=job["shots"],
                     seed_simulator=job["seed"]).result().get_counts()
    sys.stdout.write(json.dumps(counts))


if __name__ == "__main__":
    main()
