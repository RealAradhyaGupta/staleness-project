# PROTOCOL: staleness cost and recovery

**Status: FROZEN.** Written 13 October 2026, before any engine code exists and
before any result was produced. The text below is never edited. Changes go in
the Amendments section at the bottom, each one dated, and the original wording
stays as it was written.

**Why freeze it.** If I decide the rules after seeing the numbers, the numbers
cannot test anything. Writing the rules first is the only way my own results
can surprise me.

**Scope note.** Nothing in this file has been run. No code was written or
changed and no data was touched on the day it was written.

---

## 1. The question

How much fidelity is lost when the qubits for a job are chosen from an older
calibration state than the one the job actually runs under, and does a
lightweight rule that uses only past states recover part of that loss?

Two numbers answer it:

1. The cost of being stale, as regret in fidelity against the best choice the
   truth state allows.
2. Whether a cheap per-field rule, using nothing but states published before
   submission, reduces that regret.

An answer in overlap of chosen qubit sets is NOT an answer to this question.
Overlap was Checkpoint 3 and it does not price the decision.

## 2. Data

**Reported results use real IBM calibration states only.** The source is the
921 distinct calibration states covering 3 machines (ibm_fez 313,
ibm_kingston 276, ibm_marrakesh 332) over 28 August to 12 October 2026, built
in L-017 and indexed in `data/clean/states.csv`.

`data/clean/states.csv` is an INDEX, not the numbers. Its columns are
timestamps, per field value dates and ages, counts and dead lists. The
calibration values themselves come from `data/clean/qubits.csv` and
`data/clean/pairs.csv`, joined on machine and on `snapshot_utc` equal to the
state's `first_seen_utc`, falling back to the matching card in `data/raw` if a
value is needed that the flat tables do not carry. `data/raw` is read-only and
stays that way.

Curated (synthetic) data in `team_code/` is used ONLY to test that code runs
and to check reproducibility. It never appears in a reported result, a chart or
a claim. This applies to my own synthetic data too, if I ever make any. Any
synthetic output carries SYNTHETIC in its file name. This is decision L-012.

## 3. What a job is

A job is a tuple:

    (machine, submission time t_s, circuit, queue delay D)

- **Information available to a strategy:** every state with
  `first_seen_utc <= t_s`, and nothing else. No value published after `t_s` may
  reach any strategy except the oracle.
- **Run time:** `t_r = t_s + D`.
- **Truth state:** the latest state with `first_seen_utc <= t_r`.
- **Delays D, in hours:** 1, 3, 6, 12, 24, 48.

A job is valid only if all three hold, and invalid jobs are dropped and
counted, never silently skipped:

1. At least 5 distinct states exist at or before `t_s` on that machine, so the
   window strategies have something to look at.
2. A truth state exists at or before `t_r`.
3. `t_r` is not later than the last state on that machine, so truth is real
   and not extrapolated. This drops long delay jobs near 12 October, which
   thins D = 48 most. The count dropped per D is reported.

## 4. Submission times

For each machine and each UTC day in the window, 3 submission times are drawn
uniformly from that day.

- **Seed: `SEED_SUBMIT = 20260828`.** Recorded here so the job list is
  reproducible from this file alone.
- **Exact procedure:** one `numpy.random.default_rng(20260828)` is created
  once. Machines are visited in sorted name order (ibm_fez, ibm_kingston,
  ibm_marrakesh). Within a machine, days are visited in ascending date order.
  For each day, 3 values are drawn uniformly from [0, 86400) seconds, sorted
  ascending, and added to that day's 00:00:00 UTC. The order of visits is part
  of the definition, because changing it changes the draws.

Reason: three fixed times a day stops the sample from favouring an hour of the
day. If submissions always landed just after a publication, staleness would
look cheaper than it is.

## 5. Circuits

`ghz5`, `ghz8`, `ghz10`, `bv8`, `bv10`.

GHZ and Bernstein-Vazirani give two different shapes of ideal answer, one
spread over two outcomes and one concentrated on a single bitstring. Note that
the teammates' `circuits.py` currently builds only `ghz5`, `ghz8` and `bv8`, so
`ghz10` and `bv10` must be added before the engine runs.

**Compiler settings, identical for every strategy:**

- optimization level 2, as in the team's `config.py`
- fixed transpiler seed, fixed simulator seed, fixed shot count, all recorded
  in the engine's own config file and printed in its log

The ONLY thing that differs between strategies is the set of numbers handed to
the compiler's layout step. If anything else differs, the comparison is void.

## 6. Strategies

Six arms. Each one produces a predicted calibration state, which is turned into
a compiler target. All six are then run on the SAME truth state noise model.

| Name | What the compiler sees | Role |
|---|---|---|
| random | a layout drawn at random among live qubits | floor, Huo-style |
| stale | the latest state at `t_s` | today's practice |
| window mean | mean of the last 5 distinct states | published-style baseline |
| std-adjusted | mean plus 1 standard deviation, pushed toward bad | the team's "stability", Kurniawan-style |
| per-field shrinkage | **ours**, see below | the method under test |
| oracle | the truth state | ceiling |

**Per-field shrinkage.** For each field separately (T1, T2, readout error, sx
error, cz error), the predicted value is a blend of the latest value and the
median of the last N distinct states:

    predicted = (1 - w) * latest + w * median(last N distinct states)

with N and w chosen per field. N and w are tuned on training days only, and
the chosen values are recorded in an amendment to this file before the test
days are touched.

**The random arm** needs its own fixed seed and a stated number of draws per
job, both recorded in the engine config, because a single random layout is very
noisy.

All averaging is done on the log of each value, because error rates span orders
of magnitude. Errors are bad when high, T1 and T2 are bad when low.

## 7. Dead qubits

The rule from L-016 decision 2, unchanged:

    dead if  sx_error > 0.1  or  readout_error > 0.2  or  T1 missing  or  T2 missing

- The rule is applied to the state THAT STRATEGY SEES. A stale strategy
  therefore inherits a stale dead list and is allowed to be fooled by it.
- **No strategy is given the fresh dead list.** Only the oracle, which sees the
  truth state by definition, has a current one.
- **Permanent defects are excluded for every strategy**, so no arm earns credit
  for avoiding a qubit nobody could ever have used.

## 8. Metric

- **Primary:** Hellinger fidelity against the circuit's ideal output
  distribution, from an Aer simulation of the truth state.
- **Regret** = oracle fidelity minus strategy fidelity. Lower is better. This
  is the headline number, because it prices the decision rather than the
  machine.
- **Secondary:** analytic estimated success probability for the chosen layout,
  reported alongside the simulated fidelity, never instead of it. It is cheap,
  it carries no shot noise, and it is the sensible metric for any tuning sweep.

## 9. Axes for results

Every result is reported against all three of these:

1. **Queue delay D in hours.** What a user actually experiences.
2. **Age at run time of the cz numbers the strategy used.** Measured from the
   `date` on the value itself, not from the publication time. This is L-016
   decision 1 and it is the clock that matters.
3. **Number of new states between `t_s` and `t_r`:** 0, 1, 2 or more.

**Readout error age is shown separately**, never merged into the others,
because L-017 measured it refreshing roughly ten times faster than the rest
(median 0.5 to 1.1 hours against 13 to 16 hours for sx and cz).

## 10. Split

- **Training days:** 28 August to 28 September 2026 (32 days).
- **Test days:** 29 September to 12 October 2026 (14 days).
- Nothing whatsoever is tuned, chosen or inspected for tuning purposes on test
  days. N, w, the grid searched, and any other choice are fixed on training
  days and written into an amendment before test days are used.
- **The 22 to 23 September publishing gap stays in.** It is not deleted or
  patched. Results are reported with it included, and the jobs that straddle it
  are reported separately so its effect is visible.

## 11. Statistics

- **Intervals:** 95 percent, from a block bootstrap that resamples WHOLE DAYS,
  so jobs from the same day stay together. Number of resamples recorded in the
  engine config.
- **Paired differences** against stale, since every strategy meets the same job
  and the same truth state.

**Primary comparisons, fixed in advance:**

- **(A)** stale regret against oracle, at each D.
- **(B)** per-field shrinkage against stale, at D = 6 hours and D = 24 hours,
  pooled over machines and circuits, on the test days only.

Those are the only confirmatory tests. **Everything else is exploratory and
must be labelled exploratory** wherever it appears, including in the write-up
and in any slide.

## 12. Sanity checks that must pass before any claim

No number from this protocol may be reported as a result until all of these
pass, and the outcome of each is recorded in PROGRESS_LOG.md:

1. **Stale regret is exactly 0** whenever no new state appeared between `t_s`
   and `t_r`. Not approximately zero. If it is not exactly zero, the pipeline
   is not deterministic or the arms are mis-wired.
2. **Oracle is never below stale on average**, at every D.
3. **The random layout arm is the lowest** of the six on average.
4. **The team's curated fixture still reproduces its sha256**, namely
   `results_synthetic.csv` =
   `afd161059ecad53ec35c87450832d920880ecd04504a7d17a830ebc611716f69`, proving
   the environment has not drifted underneath the engine.

## 13. Share of jobs with no change

For every D, report the share of jobs where no new state appeared between
`t_s` and `t_r`, so their regret is exactly zero by construction.

This is a denominator, not a result. Without it a small mean regret can be
misread as "staleness is cheap", when the real story may be that most jobs
crossed nothing at all.

## 14. Limits, stated before any result

- **Truth here is IBM's reported numbers, not the hardware itself.** This
  measures the cost of acting on out of date REPORTS. It does not measure the
  machine's physical condition.
- **The ceiling is not a true oracle.** L-017 measured the values inside a
  state as already a median of 13 to 16 hours old in sx and cz error at the
  moment the state is first published. So the oracle is "best available
  reported numbers", not perfect knowledge.
- **Simulation, not hardware.** Fidelity comes from Aer. A small hardware check
  is a separate, optional step and is not part of this protocol.
- **Three machines of one generation.** All 156 qubit. Nothing here shows the
  result holds on another design.
- **Fourteen test days** is a small number of blocks for a day-level bootstrap,
  so intervals are expected to be wide.

## 15. Predictions, written before any run

Written 13 October 2026, before the engine exists. Recorded so the results can
later be judged against them, including where I was wrong.

1. Stale regret grows with D and flattens somewhere between 12 and 24 hours,
   because L-017 measured the real measurement sweep at roughly 6 to 8 a day,
   so by about a day almost every job has crossed a fresh sweep and there is
   little more staleness to accumulate.
2. At D = 1 hour, more than half of all jobs cross no new state at all, so
   their regret is exactly zero and mean regret at D = 1 is small for a boring
   reason.
3. The regret gap between stale and oracle is small in absolute terms,
   roughly 0.01 to 0.05 in Hellinger fidelity, in the same range as the
   teammates' synthetic demo though that is not evidence.
4. The random layout arm is far below everything else, a gap much larger than
   any difference among the five informed arms. Choosing good qubits at all
   matters much more than choosing them from fresh numbers.
5. Per-field shrinkage beats stale by a small amount that does not reach
   significance at 95 percent on 14 test days. I expect the honest outcome to
   be "no significant gain", matching what the team found on synthetic data.
6. Shrinkage helps most on cz error and least on readout error, because
   readout is already fresh at submission while cz is 13 to 16 hours old
   before the queue wait even begins.
7. ibm_marrakesh shows the largest regret of the three machines, because
   L-017 found 87 of its 156 qubits dead in some states but not all, so its
   dead list moves the most.

If result 4 fails, I should suspect the layout step is not reading my numbers
at all, before I believe anything else in the run.

## 16. Engine requirements

- The engine runs on **`team_code/.venv`, Python 3.12.4**, the environment
  built in L-018. The main project `.venv` is Python 3.13.7, where `qiskit-aer`
  has no build.
- Every seed, threshold and setting lives in one engine config file, and that
  file is printed into the run log.
- Reruns must be bit identical. If a rerun differs, that is a fault to log and
  fix, not a thing to average over.
- `data/raw` stays mode 555 and read-only throughout.
- No quantum hardware is used anywhere in this protocol.

## 17. Open risks known at freeze time

Recorded on 13 October 2026, before any run. These are known weaknesses in the
design above, written down rather than quietly fixed later. Anything acted on
becomes an amendment.

1. **A window of "the last 5 distinct states" may hold only one distinct cz
   measurement.** A state is new if ANY of the five fields changed, and L-017
   showed readout error moves far more often than the rest. So five
   consecutive states can carry five identical cz values, making the window
   mean equal to the latest value and the standard deviation exactly zero. If
   that happens, the std-adjusted arm silently collapses into the window mean
   arm for cz, which would be an artefact of the definition and not a finding.
   The alternative is to define each window over the last N distinct values OF
   THAT FIELD, which is what L-016 decision 1 implies. NOT changed here,
   because the design above was specified per state. Must be checked and
   amended before conclusions are drawn.
2. **Compute cost.** A rough count is about 414 submissions, times 6 delays,
   times 5 circuits, times 6 strategies, which is roughly 74500 simulated runs.
   Scaling from the teammates' measured 540 runs in 49 seconds, one full pass
   is on the order of 2 hours. A tuning grid over N and w per field multiplies
   the training portion by the grid size and quickly becomes days. The analytic
   success probability in section 8 is the intended way out: tune on it, and
   spend simulation only on the chosen setting.
3. **Permanent defects were computed over all 921 states, which includes the
   test days.** That is a small leak of test information into an exclusion rule
   used by every arm. Defining permanent defects on training days only would
   remove it.
4. **Few blocks.** 14 test days is a thin basis for a day-level block
   bootstrap. Resampling machine-days would give 42 blocks but they are not
   independent, as the 22 to 23 September gap was platform wide.
5. **D = 48 loses jobs at the end of the window.** Submissions near 12 October
   have no truth state 48 hours later, so they are dropped by rule 3 of
   section 3. The longest delay therefore has the fewest jobs, exactly where
   the effect should be largest.
6. **`ghz10` and `bv10` do not exist yet** in the teammates' `circuits.py` and
   must be added, with their ideal distributions, before the engine runs.
7. **A base target per machine is still needed.** Turning a state into a
   compiler target requires the device structure: the coupling map and the gate
   durations. The teammates' pipeline gets this from `FakeTorino`, which is 133
   qubits and the wrong machine for my 156 qubit data. Where my base target
   comes from is not settled in this protocol and must be settled before the
   engine runs.

## 18. Amendments

Append only. Each amendment is dated, says what changed and why, and never
edits the text above.

*(none yet)*
