# Calibration Drift-Aware Recompilation — pipeline

**The idea in one sentence:** Qiskit chooses which physical qubits to use from the
latest calibration numbers. If the chip recalibrates while a job waits in the queue,
that choice was made on old numbers. We measure how much fidelity that costs, and
test whether choosing qubits from a *prediction* wins some of it back.

---

## 1. Setup (do exactly this)

1. Install Python 3.11 or 3.12.
2. In this folder, run:
   ```
   python -m venv .venv
   .venv\Scripts\activate          (Windows)   or   source .venv/bin/activate   (Mac/Linux)
   pip install -r requirements.txt
   ```

## 2. Run it (3 commands, about 3 minutes total)

```
python synth_drift.py              # makes 20 synthetic calibration cycles   (~5 s)
python experiment.py synthetic     # compiles + simulates 540 runs           (~2.5 min)
python analysis.py synthetic       # summary table + 3 plots                 (~10 s)
```
Check: `results/summary_synthetic.csv` exists and `plots/` has 3 PNG files. The
numbers should match the summary printed in section 6 exactly (all seeds are fixed).
If they do not match, stop and report it.

## 3. What each file does

| File | Module | Job |
|---|---|---|
| `config.py` | — | Every project decision as one setting. Change decisions here only. |
| `ingest_ibm.py` | M1 | Pull real calibration history from IBM (**not yet run against the live service**) |
| `synth_drift.py` | M1b | Fallback: synthetic drift on top of ibm_torino's real published calibration |
| `snapshot.py` | M2 | Snapshot file format; snapshot → Qiskit Target (what the compiler reads) → Aer noise model (the fake device) |
| `predictors.py` | M4 | Stale (= persistence), stability (our method), trend, rolling mean. Only ever see data up to submission. |
| `circuits.py` | — | GHZ-5, GHZ-8, Bernstein–Vazirani-8 and their ideal outputs |
| `experiment.py` | M5–M7 | For each start cycle k, delay d, circuit: compile 5 ways, run all on the true device of cycle k+d, record fidelity |
| `analysis.py` | M3, M7 | Per-qubit drift, summary statistics, plots |

The five strategies differ **only** in the numbers handed to Qiskit's standard compiler:

| Strategy | Compiler sees | Role |
|---|---|---|
| blind | identical numbers for every qubit | floor |
| stale | snapshot k | what happens today |
| trend | straight-line forecast for k+d | the email's "forecasting" idea |
| stability | 5-cycle average + 1 × swing | **our main method** |
| oracle | true snapshot k+d | ceiling (impossible in real life) |

## 4. Switching to real IBM data

1. Make a free account at quantum.cloud.ibm.com. Copy your **API key** and your **instance CRN** (Instances page).
2. Run once in Python:
   ```python
   from qiskit_ibm_runtime import QiskitRuntimeService
   QiskitRuntimeService.save_account(channel="ibm_quantum_platform", token="API_KEY", instance="CRN", set_as_default=True)
   ```
3. `python ingest_ibm.py history ibm_torino 30`
   (if ibm_torino is not in the printed list, use a device that is, and set `DEVICE` in `config.py`)
4. If history works: `python experiment.py ibm_torino` then `python analysis.py ibm_torino`.
   You need at least WINDOW + max(DELAYS) = 12 unique snapshots.
5. If history is refused for every date: run `python ingest_ibm.py log ibm_torino` every morning
   and every night from now on. Report the exact error text.

## 5. Rules

- **Never let a predictor see data after cycle k.** That would make the results fake.
- Do not change values in `config.py` without telling the team; every value is a decision we defend in review.
- **Reject AI-suggested code that uses any of these** (they are removed or outdated):
  `execute`, `IBMQ`, `from qiskit import Aer`, `qiskit.providers.models`,
  `backend.run(...)` on an IBM device, `channel="ibm_quantum"`,
  `ibm_kyoto` / `ibm_osaka` / `ibm_brisbane` / `ibm_sherbrooke` (retired devices).

## 6. Current status (synthetic data, 27 paired comparisons per delay)

| delay (cycles) | blind | stale | trend | stability | oracle | staleness cost |
|---|---|---|---|---|---|---|
| 1 | 0.350 | 0.833 | 0.837 | 0.837 | 0.863 | 0.030 |
| 2 | 0.343 | 0.816 | 0.826 | 0.814 | 0.860 | 0.044 |
| 3 | 0.342 | 0.812 | 0.789 | 0.823 | 0.854 | 0.042 |
| 7 | 0.320 | 0.793 | 0.789 | 0.795 | 0.853 | 0.059 |

Reading: quality-aware placement matters a lot (blind ≈ 0.34 vs stale ≈ 0.81). Old numbers
cost 3–6 fidelity points, growing with the delay. The first version of the stability method
does **not** yet beat stale reliably (no delay has p < 0.05). **These are synthetic numbers that
test the pipeline; they are not findings about real hardware.**

## 7. Next tasks

1. Real data: section 4, steps 1–5. Done when `snapshots/ibm_torino/` has ≥ 12 snapshots or logging has started.
2. Re-run experiment + analysis on real data. Done when the 3 `*_ibm_torino.png` plots exist.
3. Tune WINDOW and PENALTY using only the earliest half of the cycles; report results on the later half.
4. Optional: add a 4th circuit with a sharp known answer (not QFT on a blank input).
