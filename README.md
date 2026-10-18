# Staleness Aware Noise Modeling

Quantifying and Mitigating the Impact of Queue-Delay-Induced Calibration Drift
on Quantum Circuit Fidelity.

A VIT quantum computing course project.

## What this asks and what the experiment does

On real IBM quantum machines you pick which qubits to use from a calibration
card, but your circuit does not run at once: it waits in a queue. By the time
it runs, the machine may have been recalibrated, so the card you chose with is
out of date. This project measures how much accuracy that costs, and tests a
simple fix.

The method, in order. IBM publishes a calibration card for a machine many times
a day, but most new cards repeat the numbers of the card before them, so
neighbouring cards that are equal on all five tracked fields are collapsed into
one distinct calibration state. A job is one submission time plus a queue delay
D, for D in 1, 3, 6, 12, 24 and 48 hours. At submission time each of six
strategies sees only the calibration information its own rule allows and picks a
qubit layout from it. The circuit is then simulated against the state that is
true at run time, so every strategy is judged on the same truth. The six
strategies are `random`, `stale`, `window_mean`, `std_adjusted`, `shrinkage` and
`ceiling`. The `ceiling` arm is allowed to see the run-time state, so it is the
best score available rather than a real strategy, and regret is the gap between
a strategy and that ceiling. Accuracy is the Hellinger fidelity between the
measured output distribution and the circuit's ideal output. Five circuits are
used: ghz5, ghz8, ghz10, bv8 and bv10, each chosen because its ideal answer is
sharp and known.

Everything is simulated with Qiskit Aer using noise models built from real
published calibration numbers. No job was ever run on real quantum hardware.
The only thing fetched from IBM is calibration history, which is read-only.

## Folder map

| Path | What it is |
|---|---|
| `scripts/` | The numbered steps, 01 to 26, in the order they were run: fetch calibration history, build tables, run checks, analyse, draw figures. |
| `engine/` | The experiment engine: job generation, the six strategies, the real-data connector, the runner, and its tests. |
| `engine/_original/` | The teammates' original pipeline files as they arrived, kept unchanged so any edit can be proved by checksum. |
| `team_code/drift_pipeline/` | The teammates' original synthetic-drift pipeline, with its own synthetic snapshots, results and plots. Not real IBM data. |
| `PROTOCOL.md` | The plan, frozen before any result was looked at. Read-only in the original project. |
| `PROTOCOL_AMENDMENTS.md` | The three changes made to the plan afterwards, A1, A2 and A3, appended in order. |
| `PROGRESS_LOG.md` | The project diary, append-only, 48 entries. Every decision, result, fault and fix, with real numbers. |
| `NOTES.md` | Raw facts and numbers only, no story. |
| `DISCLOSURES.md` | What is known to be wrong, uncertain or limited about this work. |

## Setup

Tested with Python 3.12.4 and these versions, which are pinned in
`engine/requirements.txt` and in `team_code/drift_pipeline/requirements.txt`:

```
qiskit==2.5.2
qiskit-aer==0.17.2
qiskit-ibm-runtime==0.50.0
pandas>=2.0
scipy>=1.10
matplotlib>=3.7
```

Those are the versions you listed, and they match the requirements files
exactly. There is no requirements file at the top level of this repository, so
install from the engine one:

```
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r engine/requirements.txt
pip install python-dotenv
```

`python-dotenv` is imported by the fetching scripts but is not listed in
`engine/requirements.txt`, so install it separately.

Then make your own credentials file:

```
cp .env.example .env
```

Fill in `IBM_API_KEY` and `IBM_INSTANCE` with your own values from
quantum.cloud.ibm.com. You need your own IBM Quantum account. `.env` is listed
in `.gitignore` and must never be committed. No key, instance or credential of
any kind is in this repository.

## Run order

Each line is taken from the script's own docstring.

Needs an IBM Quantum account, because it reads calibration history from IBM:

| Script | What it does |
|---|---|
| `01_list_backends.py` | Connect to IBM Quantum and list the real backends. |
| `02_calibration_time.py` | Show the latest calibration timestamp for one real backend. |
| `03_qubit_table.py` | Small calibration table for the first 10 qubits, plus 5 cz errors. |
| `04_save_snapshots.py` | Save current calibration snapshots for all three machines to `data/raw`. |
| `05_test_history.py` | Test whether IBM returns old calibration snapshots at all. |
| `06_history_depth.py` | How far back does IBM calibration history go? |
| `07_earliest_snapshot.py` | Binary search for the earliest snapshot IBM will return. |
| `08_download_history.py` | Download the last 120 days of calibration history for three machines. One request per machine per day. Restartable. |
| `10_probe_cadence.py` | How often does IBM really publish snapshots? Probe 5 days at 7 clock times each. |
| `12_walkback_pilot.py` | Pilot for the walk-back method, and measure its real speed. Writes no files. |
| `13_download_all_snapshots.py` | Download every distinct snapshot in a date window by following the real chain of publications. Restartable. |

Needs only the data already downloaded, no account and no network:

| Script | What it does |
|---|---|
| `09_build_tables.py` | Build `data/clean/qubits.csv` and `pairs.csv` from `data/raw`. |
| `11_overlap_analysis.py` | Does a stale snapshot still pick the same best qubits? |
| `14_neighbour_diff.py` | What actually changes between neighbouring snapshots, and do the timestamps inside one card agree? |
| `15_build_tables_all.py` | Rebuild the clean tables from every snapshot on disk, streaming so memory stays small. |
| `16_card_quality.py` | What is really inside each card: full or partial update, and the age of the values inside it. |
| `17_build_states.py` | Collapse runs of identical cards into distinct calibration states. |
| `18_build_targets.py` | Build one base Target per machine, offline, from the cards on disk. |
| `19_smoke_test_targets.py` | Prove the base targets assemble, without running any experiment. |
| `20_analyse_results.py` | The four sanity checks, then the two confirmatory comparisons. Reports nothing if a check fails. |
| `21_finish_run.py` | Finish jobs the frozen runner could not finish, with the same seeds and numbers. |
| `22_merge_parts.py` | Merge a run's part files into `all_rows.csv` the same way the runner does. |
| `23_independent_check.py` | Recompute the headline numbers from scratch, sharing no code with script 20 and using a different bootstrap seed. |
| `24_prereg_outputs.py` | Produce the outputs the protocol pre-registered but the run never emitted. Each one labelled pre-registered or exploratory. |
| `25_dead_qubit_rows.py` | Count rows where an arm picked a qubit its own card called alive but the truth state calls dead. Descriptive only. |
| `26_report_figures.py` | The report figures, 300 dpi, each with a CSV of exactly the numbers drawn. |
| `_kraus_retry.py` | Run one simulation as the first simulation in a fresh process, to work around an Aer fault. |
| `add_log_entry.py` | Append one `PROGRESS_LOG.md` entry with the timestamp read from the clock, never typed. |

The engine itself is run through `engine/run_engine.py`, which takes
`--machines`, `--circuits`, `--delays`, `--days train` or `--days test`,
`--workers` and `--out`. `engine/run_pilot.py` is the small training-only pilot.
`engine/drift_study.py` and `engine/tune_shrinkage.py` are the training-day
studies. `engine/test_dead_qubits.py` and `engine/test_t1t2_sensitivity.py` are
the tests.

## Data

**The IBM calibration data is not in this repository, and neither is anything
derived from it.** That means no `data/` folder, no `outputs/` folder, no clean
tables, no state index, no pickled targets, no result rows and no figures built
from them. The reason is simple: IBM's terms on redistributing calibration data
have not been checked yet, so none of it is published here.

Anyone with their own IBM Quantum account can fetch it again. Scripts 04, 08,
10 and 13 do the downloading, and script 13 is the one that collected the full
set used in this project. Scripts 09, 15, 17 and 18 then rebuild the clean
tables, the distinct states and the base targets from what was downloaded.
Because IBM serves a limited window of history, a later download will not
return the exact same days as the original run.

The synthetic snapshots, results and plots under
`team_code/drift_pipeline/` are the teammates' invented numbers, marked
`"source": "synthetic"` in the files themselves. They contain no IBM data and
are safe to share.

## Reproducibility notes

- The protocol was frozen before any result was looked at. Its sha256 is
  `dda0f4fc747a65c81206b1360a5b9d38261128ff9099c4f6a98c071b27992ae5`, and
  `PROTOCOL.md` was kept read-only in the original project. The amendments live
  in one append-only file, `PROTOCOL_AMENDMENTS.md`, whose sha256 at the freeze
  was `3355920c487902cc8fcbd50526336e9448a3df2abe0766106719e152b1802867`.
- Every seed and threshold lives in `engine/engine_config.py` and is printed
  into the run log. The submission-time draw uses seed 20260828, the random
  layout arm uses 20261013, transpilation uses 11 and each simulation uses
  seed 3, with 4000 shots and optimisation level 2.
- The tuned settings are N = 3 with weights readout 0.5, gate 0.0 and times
  0.0, chosen on training days only by a rule written down in advance.
- Training days are 28 August to 20 September 2026 and test days are
  21 September to 12 October 2026. Nothing was fitted or inspected on test days.
- The raw calibration files were written read-only, mode 0444, and never
  modified. Every engine file was checksummed at the freeze and verified again
  afterwards.
- No quantum hardware job was ever submitted. Every number comes from Qiskit
  Aer simulation.

## Honest note on tooling

Scripts and analysis were written with the help of Claude Code (an AI
assistant) under the team's direction.

## Team

[Student 1 name, Regd. No.]

[Student 2 name, Regd. No.]

[Student 3 name, Regd. No.]

Faculty: Prof. Aswani Kumar Cherukuri
