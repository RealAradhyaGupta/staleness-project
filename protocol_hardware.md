# Protocol: Stage 6 hardware validation

Written and frozen BEFORE any quantum job was submitted, including the pilot.
The SHA-256 of this file and of `scripts/42_hw_run.py` are recorded in
`FREEZE_HARDWARE.txt` with the UTC time they were taken.

This is a NEW and SEPARATE pre-statement. It does not change the rule, the
Round 2 protocol, any frozen Round 2 file, or any Round 2 result. The frozen
rule in `scripts/30_hybrid_rule.py` is imported and used exactly as it stands.

## 1. Purpose

Round 2 compared the strategies in simulation, on Aer noise models built from
real calibration cards. Every number there came from a simulator. This stage
asks a narrower question on the real machine:

  when the same circuit is compiled from three different pictures of the same
  device, and then run on that device after a 6 hour hold, do the measured
  fidelities differ in the direction the simulation said?

Twelve jobs cannot answer that with significance. This is a sanity check that
the pipeline survives contact with hardware and that the sign of the effect is
not reversed. Section 10 states the limits.

## 2. Device rule

Fixed before any job and not changed afterwards:

  - use `ibm_kingston` if its status is Online (status_msg `active` and
    operational true)
  - otherwise use `ibm_fez` if it is Online
  - never use `ibm_marrakesh`, which is paused
  - never use any other device
  - if neither allowed device is Online, STOP and report, submitting nothing

Checked at 2026-10-25 16:12 UTC by `scripts/40_hw_probe.py`: `ibm_kingston`
status active, operational true, 2 pending jobs, 156 qubits. `ibm_fez` also
active. The device for this stage is therefore `ibm_kingston`.

The device status is re-checked before every submission. If the chosen device
stops being Online part way through, the remaining jobs are marked
`DEVICE_OFFLINE` in the state file and in the log. The device is never
switched mid run, because changing device would change the layout and make the
jobs incomparable.

## 3. Account and the hardware usage cap

Instance name `open-instance`, plan `open`. Read from IBM at 2026-10-25
16:12 UTC: usage consumed 0 seconds, usage limit 600 seconds, usage remaining
600 seconds. The API key and the CRN live in `.env`. They are never printed,
never logged and never written to any output. Every line this stage prints is
passed through a `hide()` filter first.

The cap for this whole stage is **180 seconds of QPU usage in total**. It is
the user's approved estimate and it is smaller than the account allocation.
The cap is enforced by these rules, all fixed in advance:

  1. Jobs are submitted strictly one at a time. After each job the script
     waits for it to finish, reads its usage from IBM, adds it to the running
     total, and only then considers the next job.
  2. Before every submission the script computes
     `usage_so_far + 1.5 * max_per_job_usage_seen_so_far`
     using the pilot estimate when no full job has run yet. If that number is
     above **150 seconds** the job is not submitted. The remaining jobs are
     marked `SKIPPED_FOR_CAP` in the state file and the log.
  3. Before every submission the script reads the instance's remaining time
     from IBM. If less than **8 minutes (480 seconds)** remain on the account,
     nothing is submitted.
  4. FAIL CLOSED. If the usage cannot be read, for any reason, nothing is
     submitted. The script waits and retries. It never submits while the usage
     total is unknown.
  5. A failed or cancelled job can still consume time, so its usage is read
     and added to the total like any other. No job is ever retried before the
     usage has been read.

The cap of 180 seconds is a hard ceiling. Rule 2 stops the run at 150 seconds
so that one unexpectedly expensive job cannot cross 180.

## 4. The pilot and the usage projection

Before anything else, one pilot job: a single 2 qubit Bell circuit
(`h`, `cx`, `measure`) at **100 shots** on the chosen device. Its reported
usage is recorded.

  - if the pilot uses more than **10 seconds**, STOP and submit nothing else

The pilot is then used to project the total for all 12 jobs. The projection
model is fixed here, before the pilot runs, so it cannot be chosen to suit the
answer. It splits usage into a per job fixed overhead and a per shot physical
cost:

  - the per shot physical cost of a circuit is
    `isa_estimated_duration + default_rep_delay`.
    Both numbers are read from the device itself, not assumed.
    `default_rep_delay` on `ibm_kingston` is 250 microseconds. The estimated
    ISA durations at optimization level 2 are 2.612 microseconds for ghz5,
    2.912 for ghz8, 3.516 for bv8 and 5.128 for qft5, so the rep delay
    dominates and the per shot cost is close to 253 to 255 microseconds.
  - the pilot's own predicted sampling time is
    `100 * (bell_isa_duration + default_rep_delay)`, which is a few tens of
    milliseconds. The pilot is therefore almost entirely overhead, and
    `overhead_per_job = pilot_usage - pilot_predicted_sampling`, floored at 0.
  - the projection is
    `12 * overhead_per_job + sum over all 36 PUBs of 1000 * per_shot_cost`

Why not a plain scaling of the pilot by shots and PUBs. Usage is not
proportional to shots: a job carries a fixed overhead that a 100 shot pilot
pays in full. Scaling a 100 shot measurement up by a factor of 360 would
multiply that overhead 360 times and give a number with no physical meaning.
The model above charges the overhead once per job, which is what actually
happens, and charges the sampling time at the device's own published rate.

  - if the projection is above **150 seconds**, STOP and report to the user
    before submitting anything

The shots and the design are NOT changed to fit under the cap. If the
projection says the design does not fit, the run stops and the user decides.

## 5. Arms

Three arms, all from the existing code, with no parameter changed:

  - `stale`: the newest calibration card at the compile time. Round 1
    definition, `engine/strategies.py` `predict(..., "stale")`.
  - `window_mean`: the Round 1 window mean, `predict(..., "mean")`, with
    `engine_config` parameters unchanged.
  - `hybrid`: the frozen Round 2 rule, `scripts/30_hybrid_rule.py`, imported
    unchanged, called with the weights for the hold `D` of the job. The dead
    qubit guard at `M = 1` applies to this arm, exactly as frozen.

All three arms of one circuit at one compile time go into **one Sampler job as
three PUBs**, 1000 shots each. One Sampler job therefore carries one circuit
compiled three ways. This matters: the three arms of a job share the same
queue position, the same device drift and the same calibration epoch, so the
paired difference within a job is not polluted by the device moving between
submissions.

There is no `ceiling` arm and no regret on hardware. The ceiling needs the
card that will be published at run time, and on hardware the run time is not
known in advance. This stage measures differences between arms only.

### 5.1 The primary comparison, chosen before any job

  - **primary: `window_mean` minus `stale`**
  - secondary: `hybrid` minus `stale`

This order is set now, before a single job is submitted, and it is the
opposite of Round 2's order. The reason is stated honestly: Round 2 found that
`window_mean` was the only arm whose gain over `stale` cleared zero
(0.005346, 95 percent interval 0.001584 to 0.008923), while the frozen
`hybrid` did not (0.000151, interval -0.008865 to 0.007510). Choosing the
primary comparison after seeing Round 2 is legitimate only because this is a
new and separate pre-statement, written before any hardware data exists. It
would not be legitimate to re-read the Round 2 rows and call it a new result,
and that is not done anywhere in this stage.

## 6. Circuits

Four circuits, built by `engine/circuits.py`, unchanged:

  - `ghz5`: ideal output 50 percent all zeros, 50 percent all ones
  - `ghz8`: the same on 8 qubits
  - `bv8`: Bernstein Vazirani, 7 bit secret 1011011, ideal output that string
    with probability 1
  - `qft5`: exact QFT on the 4 peak input, ideal output exactly four outcomes
    (00000, 01000, 10000, 11000) at 1/4 each

`ghz10`, `bv10`, `qft8` and `qft10` are not run. The reason is the cap: 8
circuits would double the QPU time for no extra information about the sign of
the effect.

## 7. Cards and history

Live cards from 2026-10-24 00:00 UTC up to the moment of each compile are
fetched into `data/hardware_cards/` by the Round 1 collector
(`scripts/13_download_all_snapshots.py`), imported with its folders and window
moved. This folder is new, gitignored, and separate from the Round 2 store.
`data/raw`, `data/fresh` and `data/clean` are read only and are not written.

The history each rule sees is **the Round 2 store plus these new cards, and
only up to the compile time**. It is built in `data/clean_hw/` and
`data/cache_hw/` by `scripts/41_build_hw_tables.py`, which symlinks
`data/raw`, `data/fresh` and `data/hardware_cards` into one folder and runs
the same table building code that built the Round 1 and Round 2 tables, so the
numbers cannot drift from them by a coding difference. Only the chosen
device's machine is built, because only that machine is used.

Nothing above the compile time is ever read. The index handed to every arm is
`store.index_at_or_before(compile_time)`, which is the same mechanism freeze
test (iii) checked in Round 2.

## 8. Design: compile times, holds and the job count

  - three compile times, two hours apart: `t0`, `t0 + 2h`, `t0 + 4h`.
    `t0` is the moment the runner finishes the pilot, the card fetch and the
    store build, recorded to the second in the state file.
  - at each compile time, for each of the four circuits, the three arm
    snapshots are built from the history at that time, and each is transpiled
    at **optimization level 2 with seed_transpiler 11** against a Target built
    from that arm's numbers with its dead qubits removed. These are the Round
    1 and Round 2 settings, unchanged.
  - each compiled job is then **held locally for D = 6 hours** before being
    submitted. So submissions happen at `t0 + 6h`, `t0 + 8h`, `t0 + 10h`.
  - 4 circuits times 3 compile times = **12 Sampler jobs**, each with 3 PUBs,
    1000 shots per PUB. 36 PUBs, 36000 shots in total.

The hold is the point of the design. It reproduces on hardware the thing the
whole project is about: a layout chosen from a 6 hour old picture of the
device, then actually run. The hybrid arm is called with the weights for
`D = 6`, which are readout 0.65, sx 0.15, cz 0.10 and times 0.15.

### 8.1 Identical transpiled circuits are run once and counted

Two arms can produce the **same** transpiled circuit: the same physical qubits
in the same order with the same gates. Sameness is decided by `isa_key` from
`engine/run_engine.py`, the same function Round 1 and Round 2 used, so the
test is not a new one invented here.

When two or three arms of a job give an identical transpiled circuit, that
circuit is submitted **once** as a single PUB. Every arm that produced it is
given that one result. The paired difference between two such arms is then
**exactly 0**, and it **counts** as a job in the mean, the SD and the
bootstrap. It is not dropped.

This is the honest choice. Dropping the ties would compare the arms only on
the jobs where they happened to disagree, which is exactly the subset where a
difference is possible, and would inflate any effect. The number and the share
of tied jobs is reported, because a rule that usually picks the same layout as
`stale` cannot help or harm much, and that is a result in itself.

A job therefore carries 1, 2 or 3 PUBs. Fewer PUBs costs less QPU time, so
ties can only help the cap.

## 9. Network, restart and failure handling

The runner `scripts/42_hw_run.py` is standalone. Once started it needs no
Claude session: it is launched under `caffeinate` and `nohup` and it survives
the terminal closing. It is restartable.

  - every IBM call (card fetch, backend lookup, usage read, submit, status,
    result) is wrapped in a retry: on failure, wait 60 seconds and try again,
    for up to **45 minutes per step**
  - the state file `outputs/hardware/hw_state.json` is written after every
    step: job ids, compile times, card timestamps, submit times, status,
    usage. On restart the runner reads it and carries on. **A job that already
    has a job id is never resubmitted**, it is only retrieved.
  - if a compile is late, it compiles with the newest card available at that
    moment, and records the actual compile time and that card's timestamp. The
    hold is counted from the ACTUAL compile time, so the submit time moves
    with it. The **actual** `D` is recorded for every job and the analysis
    uses the actual `D`, not the planned 6 hours.
  - if a step is still failing after 45 minutes, that job is marked `MISSED`
    in the state file with the reason. An older card is never used without
    recording it. A result is never invented. Nothing is skipped silently.
  - results are written to disk as soon as they arrive. Retrieval is by job
    id and is retried later if it fails.
  - a small status file `outputs/hardware/STATUS.txt` holds the last step
    done, the next step due and the time, so it can be read from another
    terminal while the run is in progress. It contains no secret.

## 10. Analysis, fixed before any data exists

Run by `scripts/43_hw_analyse.py` after all jobs have finished or been marked.

  - **fidelity**: Hellinger fidelity between the measured counts and the ideal
    distribution of that circuit, `qiskit.quantum_info.hellinger_fidelity`,
    the same function Round 1 and Round 2 used.
  - **paired differences**, per job: `window_mean` minus `stale` (primary) and
    `hybrid` minus `stale` (secondary). A job where the two arms gave an
    identical transpiled circuit contributes exactly 0 and is counted.
  - **summary**: n, mean, SD, and a **bootstrap 95 percent confidence
    interval over jobs**: 4000 resamples of the 12 jobs with replacement,
    percentile interval, `numpy.random.default_rng(20261025)`. The resampling
    unit is the job, because the three arms of a job share one queue position
    and are not independent of each other.
  - **tie share**: the number and share of jobs whose layouts differ, for each
    comparison, and the number of PUBs actually submitted.
  - **by circuit**: the same paired differences for each of ghz5, ghz8, bv8
    and qft5 separately.
  - **queue wait**: median, minimum, maximum and the share under 1 hour, where
    queue wait is `running_time - created_time` as IBM reports them.
  - **usage**: the usage of every job, the total, and the cap.
  - **every retry, delay, late compile and MISSED job** is listed.

### 10.1 What this stage cannot show

Stated here so it cannot be forgotten when the numbers arrive:

  - **12 jobs is a sanity check, not a significance test.** With 12 paired
    differences the bootstrap interval will be wide, and it is reported to
    show that width, not to declare a winner. Round 2 measured a design effect
    of 9.400 on 11 days of simulated jobs, so clustered variation in this
    system is large. No claim of significance is made from 12 jobs.
  - **the 6 hour delay is a deliberate local hold, not a natural queue
    delay.** The circuits are compiled, kept on this machine for 6 hours, and
    only then sent. The queue wait after submission is reported separately and
    is a different quantity. Nothing here measures how long IBM's queue is.
  - there is no ceiling, so no regret and no absolute quality claim.
  - the word used for any agreement between this stage and Round 2 is
    "consistent with". Nothing here is proved.

## 11. Stop rules

  - neither allowed device Online: STOP, submit nothing
  - pilot usage above 10 seconds: STOP
  - projection for 12 jobs above 150 seconds: STOP and report, submit nothing
  - usage unreadable: do not submit, wait and retry (fail closed)
  - less than 480 seconds remaining on the account: do not submit
  - `usage_so_far + 1.5 * max_per_job_usage` above 150 seconds: submit no
    more, mark the rest `SKIPPED_FOR_CAP`

Anything else is flagged in the log and the run continues.

## 12. Environment

`team_code/.venv`, python 3.12.4, qiskit 2.5.2, qiskit-ibm-runtime 0.50.0.
Optimization level 2, `seed_transpiler` 11, 1000 shots per PUB. These are the
Round 1 and Round 2 settings from `PROTOCOL.md` section 16.

## 13. Outputs

All under `outputs/hardware/`:

  - `hw_state.json`    the restartable state, every job and its usage
  - `STATUS.txt`       one screen of progress, readable mid run
  - `hw_jobs.csv`      one row per job per arm, with layouts and fidelities
  - `hw_console.txt`   everything the runner printed
  - `REPORT.md`        the plain language report
