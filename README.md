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
used in Round 1: ghz5, ghz8, ghz10, bv8 and bv10, each chosen because its ideal
answer is sharp and known. Round 2 adds three quantum Fourier transform
circuits on a four-peak input.

The main results are simulated with Qiskit Aer using noise models built from
real published calibration numbers. Rounds 1 and 2 never touched quantum
hardware. A small Stage 6 check (12 jobs on `ibm_kingston`, 37 s of QPU time)
was run on real hardware as a sanity check, and it is described below. Apart
from that, the only thing fetched from IBM is calibration history, which is
read-only.

## Rounds in this repository

**Round 1** (`PROTOCOL.md`) measured the cost of staleness on 5,648 simulated
jobs and tested a per-field shrinkage rule against the newest card. Staleness
costs a mean Hellinger fidelity of 0.0057 at a 1 hour delay, rising to 0.0367
at 48 hours. Shrinkage did not separate from the newest card.

**Round 2** (`protocol_round2.md`, frozen by `FREEZE.txt`) tested a fitted hybrid
rule on a fresh 11 day window (13 to 24 October 2026) that did not exist when the
rule was frozen. Both pre-registered hypotheses failed. This is reported as the
main result. The plain window mean did beat the newest card at 6 to 48 hours,
but it is harmful at 1 and 3 hours, and the dead-qubit guard made the hybrid
worse. Eight circuits were used: ghz5, ghz8, ghz10, bv8, bv10, qft5, qft8 and
qft10.

**Stage 6** (`protocol_hardware.md`, frozen by `FREEZE_HARDWARE.txt`) is a 12 job
hardware check on `ibm_kingston` with a deliberate 6 hour local hold. It did not
reproduce the window mean's simulated advantage, and one job carries most of its
primary number. It is a sanity check, not a significance test. Part B of Stage 6
is exploratory and post hoc throughout.

Four analysis scripts (31, 34, 35 and 44) were corrected after the freeze. The
reasons and the limits of the assurance are written up in
`results/round2/NOTE_frozen_script_mismatch.md` and in `PROGRESS_LOG.md` entry
L-062.

## Folder map

| Path | What it is |
|---|---|
| `scripts/` | The numbered steps, 01 to 46, in the order they were run: fetch calibration history, build tables, run checks, analyse, draw figures, then the Round 2 and Stage 6 steps. |
| `engine/` | The experiment engine: job generation, the six strategies, the real-data connector, the runner, and its tests. |
| `engine/_original/` | The teammates' original pipeline files as they arrived, kept unchanged so any edit can be proved by checksum. |
| `team_code/drift_pipeline/` | The teammates' original synthetic-drift pipeline, with its own synthetic snapshots, results and plots. Not real IBM data. |
| `protocol_round2.md`, `protocol_hardware.md` | The Round 2 and Stage 6 plans, each frozen before the data or jobs they cover. |
| `FREEZE.txt`, `FREEZE_HARDWARE.txt` | The freeze records: UTC time and SHA-256 checksums of the rule, protocol, engine and scripts at the moment of each freeze. |
| `results/` | Written reports and aggregate summary tables only (see Data). `round1/`, `round2/`, `hardware/`, `part_b_exploratory/`. |
| `docs/aer_issue_draft/` | A draft report of a Qiskit Aer fault met during Round 1, with reproductions that need no IBM data. |
| `PROTOCOL.md` | The plan, frozen before any result was looked at. Read-only in the original project. |
| `PROTOCOL_AMENDMENTS.md` | The three changes made to the plan afterwards, A1, A2 and A3, appended in order. |
| `PROGRESS_LOG.md` | The project diary, append-only, 62 entries. Every decision, result, fault and fix, with real numbers. |
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

### Round 2 and Stage 6 scripts

Scripts 26_row_check to 29 are Round 1 follow-ups (row check, audit, the
protocol-faithful headline on all 5,648 jobs, and diagnostics on development
cards only). Scripts 30 to 39 are Round 2: the frozen hybrid rule, the
analysis, the fit, the runner, the freeze tests and the fresh-window fetch.
Scripts 40 to 46 are Stage 6 and the corrected Round 1 pack.

| Script | What it does |
|---|---|
| `26_row_check.py` | Row check for the 1025 truth-dead-qubit rows, plus a power calibration. |
| `27_audit_checks.py` | Three read-only audit checks on the Round 1 results and the installed Qiskit. |
| `28_protocol_headline.py` | The protocol-faithful headline: Comparisons A and B on all 5,648 jobs. |
| `29_diagnostics.py` | Diagnostics on development cards only (28 Aug to 12 Oct 2026). |
| `30_hybrid_rule.py` | The Round 2 hybrid rule, frozen. |
| `31_analyse_round2.py` | Round 2 analysis, written from `protocol_round2.md` and run once on the fresh rows. |
| `32_round2_stage0.py` | Stage 0: environment checks, no-future-card proof, existence probe. |
| `33_round2_fit.py` | Stage 1: fit the hybrid rule on development cards only. |
| `34_run_round2.py` | The Round 2 runner: the frozen rule on the fresh window, run once. |
| `35_build_round2_tables.py` | Build the combined state store that spans both windows. |
| `36_freeze_tests.py` | The freeze tests; the run stops if any of them fails. |
| `37_round2_freeze.py` | The conformance table and `FREEZE.txt`. |
| `38_fetch_fresh.py` | Fetch every card in the fresh window (needs an IBM Quantum account). |
| `39_fresh_window_report.py` | What the fresh window actually contains. |
| `40_hw_probe.py` | Stage 6 pre-flight probe. Read only; submits nothing. |
| `41_build_hw_tables.py` | Build the state store the hardware run reads. |
| `42_hw_run.py` | The hardware run. **Submits real jobs and uses QPU time on your own IBM allocation.** Capped at 180 s. |
| `43_hw_analyse.py` | The frozen hardware analysis, exactly as in `protocol_hardware.md`. |
| `44_stage6_explore.py` | Part B, exploratory, read only, post hoc. |
| `45_round1_corrected_pack.py` | Every Round 1 test-period table rebuilt on all 5,648 jobs. |
| `46_hw_sensitivity.py` | Hardware sensitivity checks, post hoc. |

The engine itself is run through `engine/run_engine.py`, which takes
`--machines`, `--circuits`, `--delays`, `--days train` or `--days test`,
`--workers` and `--out`. `engine/run_pilot.py` is the small training-only pilot.
`engine/drift_study.py` and `engine/tune_shrinkage.py` are the training-day
studies. `engine/test_dead_qubits.py` and `engine/test_t1t2_sensitivity.py` are
the tests.

## Data

**The IBM calibration data is not in this repository, and neither are the
tables or result rows built from it.** That means no `data/` folder, no
`outputs/` folder, no clean tables, no state index, no pickled targets, no
per-job or per-qubit result rows and no raw hardware counts. The one addition
is `results/`, which holds the written reports and small aggregate summary
tables (means, intervals, counts) that the paper quotes. The reason is simple: IBM's terms on redistributing calibration data
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
- Rounds 1 and 2 are Qiskit Aer simulation. The only hardware jobs are the 12
  Stage 6 jobs on `ibm_kingston` (37 s of QPU time by the guard's count, 34 s by
  IBM's counter, against a 180 s cap).
- The Round 2 rule, weights and protocol were frozen with SHA-256 checksums
  before the fresh window was downloaded. Four scripts were corrected after the
  freeze; the freeze preserved checksums and not copies of the files. See
  `results/round2/NOTE_frozen_script_mismatch.md`.

## Honest note on tooling

During the preparation of this work, the authors used Claude Code (Anthropic) as
an assistive tool for code generation and execution, data analysis, text
drafting and formatting, and log management. The research questions,
experimental protocols and the decisions within them were set by the human
authors named below, who reviewed the analytical interpretations. All
AI-assisted code and manuscript drafts were reviewed by the authors. All
quantitative values and empirical results originate from result files produced
by the project's code, and the authors maintain full responsibility for the
content and integrity of the work.

## Team

Aradhya Gupta (23BIT0206)

Siddharth Sharan (23BIT0210)

Bhallamudi Siddarth Parthu (23BIT0217)

Faculty: Prof. Aswani Kumar Cherukuri
