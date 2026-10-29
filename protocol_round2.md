# PROTOCOL, ROUND 2

**Status: FROZEN.** Written and frozen before any fresh calibration card was
downloaded. After the freeze the rule cannot change. The checksums in
`FREEZE.txt` pin this file and the code that implements it.

This document stands on top of `PROTOCOL.md` and `PROTOCOL_AMENDMENTS.md`.
Where it is silent, those still apply. Where it speaks, it is because Round 2
needs something Round 1 did not have.

Sign conventions, as in every file in this project:

* `regret = ceiling minus strategy`, so a positive regret means the strategy
  is worse than the best available reported numbers.
* `gain = F_strategy minus F_stale`, so a positive gain means the strategy is
  better than trusting the newest card.

Language rule: results are described as "consistent with" something. Nothing
in this project is described as proved.

## 1. What Round 2 is for

Round 1 measured how much an out-of-date calibration snapshot costs when
choosing qubits, and showed that a per field shrinkage fix moved the number a
little. Round 2 asks a sharper question: if the blend weight is fitted properly
on data we already have, does the fitted rule beat the newest card on a window
of cards that did not exist when the rule was fixed?

## 2. Development data and test data

* **Development data** is every calibration card from 28 August 2026 to
  12 October 2026 inclusive. The rule was fitted on this and on nothing else.
* **Test data** is every calibration card from 13 October 2026 00:00 UTC to
  24 October 2026 00:00 UTC. At the moment of the freeze not one of these cards
  was on disk. Stage 0 proved that, and recorded the proof in
  `outputs/round2/stage0_console.txt`.

Round 1 split its window into training days and test days, and `PROTOCOL.md`
section 10 forbids tuning on the test days. Round 1 is finished and reported.
Its test days are therefore past data for Round 2's purposes, and the whole
28 August to 12 October window counts as development data here. This is a
deliberate decision, taken knowingly, and it is the reason Round 2 needs a
genuinely new window rather than a new split of the old one.

Before the freeze, the only thing asked of IBM about the test window was
whether a card exists near 13, 18 and 23 October. The answer was yes for all
three machines. No value from those cards was read, saved or printed.

## 3. The rule, exactly

The rule is called `hybrid`. It is implemented in `scripts/30_hybrid_rule.py`,
where the table below is written out by hand so that the file and its checksum
are the rule.

At submission time `t_s` the rule may see the newest calibration state
published at or before `t_s`, and no state after it. For each field it predicts
the run-time value as

    predicted log value = (1 - w(D)) * newest + w(D) * median of the last N
                          distinct values of that same field

and then exponentiates. All averaging is on the log of each value, because
error rates span orders of magnitude. "The last N distinct values of that
field" is Amendment A1.2: a value counts as new only when that field's numbers
actually changed, not when any field changed.

**N, the number of distinct values the median is taken over:**

| field group | fields | N |
| --- | --- | --- |
| readout | `readout_error` | 12 |
| sx | `sx_error` | 5 |
| cz | `cz_error` | 12 |
| times | `T1`, `T2` | 12 |

**w(D), the weight on the median, by delay in hours:**

| field group | D=1 | D=3 | D=6 | D=12 | D=24 | D=48 |
| --- | --- | --- | --- | --- | --- | --- |
| readout | 0.15 | 0.40 | 0.65 | 0.85 | 0.90 | 0.90 |
| sx | 0.05 | 0.05 | 0.15 | 0.30 | 0.55 | 0.70 |
| cz | 0.00 | 0.05 | 0.10 | 0.25 | 0.45 | 0.55 |
| times | 0.00 | 0.10 | 0.15 | 0.35 | 0.80 | 0.90 |

Round 1 grouped the five fields into three (`readout`, `gate`, `times`) and
tuned one weight per group by lowest mean ESP regret. Round 2 splits `gate`
into `sx` and `cz`, because they were fitted separately and came out
differently, and it fits by directly predicting the run-time card instead of
by ESP regret. The analytic ESP is blind to T1 and T2, which is why Round 1
settled `times` by a tie-break (Amendment A2.2) rather than by evidence. The
direct prediction test is not blind to them.

**How N and w were chosen.** For every field group, every delay, every
`N` in {3, 5, 8, 12} and every `w` in {0, 0.05, ..., 1}, the mean squared error
of the predicted log value against the run-time card was computed over every
qubit and every development submission time. The development window was cut
into five chronological blocks of calendar days. For each block in turn, that
block is the test fold and the rest is the training fold, with a 48 hour purge:
a training point is dropped if its run time is at or after the test block start
minus 48 hours and its submission time is at or before the test block end plus
48 hours, so a test block never shares a run-time card with its training folds.
`N` was chosen once per field group as the value with the lowest pooled
training mean squared error averaged over the six delays. Then, at that `N`,
`w` was chosen per delay as the value with the lowest pooled held-out mean
squared error. The six weights were then forced to be non-decreasing in `D` by
pool adjacent violators, and rounded to the nearest 0.05. Every table is in
`outputs/round2/`.

**The dead qubit guard.** A qubit that is dead in any of the last `M` distinct
states at or before `t_s` is removed from the device the compiler sees, on top
of whatever the rule's own blended numbers would call dead. `M = 1`, chosen as
the value with the best F1 at `D = 24` hours pooled over machines, ties going
to the smaller `M`. "Dead" is the `PROTOCOL.md` section 7 rule unchanged:
`sx_error > 0.1`, or `readout_error > 0.2`, or T1 missing, or T2 missing, with
the engine's logged extension that a missing `sx_error` or `readout_error` also
counts as dead.

At `M = 1` the guard removes exactly the qubits that were dead on the card at
`t_s`. For the `stale` arm that is already what gets removed, so a "stale plus
guard" arm would be identical to `stale`, value for value. For `hybrid` the
guard is not a no-op, because blending readout error with a trailing median can
pull a qubit that has just failed back under the 0.2 threshold and make it look
usable. Freeze test (iv) checks the first claim and the freeze test run
measured the second: the guard adds at least one qubit the blended numbers
would not have rejected in 178 of 400 checks.

**Permanent defects.** Qubits dead in every development state are removed for
every arm including the ceiling, which is `PROTOCOL.md` section 7 as amended by
A1.5. They are computed from development cards only and frozen in
`scripts/30_hybrid_rule.py`, so no fresh card can change which qubits are
removed: `ibm_fez` 72; `ibm_kingston` 113, 121, 146; `ibm_marrakesh` 82, 94,
113, 130.

**Compiler settings, unchanged from Round 1.** `optimization_level = 2`,
`seed_transpiler = 11`, `shots = 4000`, one simulator seed per job from
`SEED_SIM = 3` by Round 1's formula with the Round 2 circuit order, Hellinger
fidelity against the exact noise-free distribution, Aer's measured ceilings
`AER_MAX_1Q = 0.75` and `AER_MAX_2Q = 0.9375` for truth values. No
`layout_trials` override anywhere.

## 4. Circuits

Eight circuits. The first five are Round 1's, unchanged.

| circuit | qubits | what it is | ideal output |
| --- | --- | --- | --- |
| ghz5 | 5 | GHZ chain | half all zeros, half all ones |
| ghz8 | 8 | GHZ chain | half all zeros, half all ones |
| ghz10 | 10 | GHZ chain | half all zeros, half all ones |
| bv8 | 8 | Bernstein Vazirani, secret 1011011 | the secret, all of it |
| bv10 | 10 | Bernstein Vazirani, secret 101101101 | the secret, all of it |
| qft5 | 5 | exact QFT on the 4-peak input | 4 outcomes at 1/4 each |
| qft8 | 8 | exact QFT on the 4-peak input | 4 outcomes at 1/4 each |
| qft10 | 10 | approximate QFT on the 4-peak input | 4 outcomes at 1/4 each |

The approximate QFT drops every controlled rotation smaller than `pi / 2^3`.

The 4-peak input answers the objection written into `engine/circuits.py` in
Round 1, that a QFT on a blank input has a flat ideal output which noise
cannot visibly damage. Instead the input is an even mixture of every integer
divisible by 4, which is a comb of spacing 4, built by putting an H on every
qubit from 2 upward and leaving qubits 0 and 1 alone. The QFT of a comb of
spacing 4 is a comb of spacing N/4, so the ideal output is exactly four
outcomes, at 0, N/4, N/2 and 3N/4, each with probability 1/4, and nothing else.
That is a sharp known answer like GHZ and BV. The four surviving outcomes are
multiples of N/4, so they depend only on the top two output bits, which is why
dropping the small rotations leaves the ideal answer unchanged while roughly
halving the two qubit gate count at 10 qubits.

## 5. Strategies

Six arms are run:

| arm | what it sees |
| --- | --- |
| `stale` | the newest card at `t_s`, raw |
| `window_mean` | the mean over the last 5 distinct values per field |
| `shrinkage_r1` | Round 1's tuned rule, unchanged: N = 3, w 0.5 on readout and 0 elsewhere |
| `hybrid` | the frozen rule of section 3, guard on |
| `hybrid_no_guard` | the frozen rule with the guard off |
| `ceiling` | the best available reported numbers, the state at run time |

`random` and `std_adjusted` are dropped, as pre-stated.

`hybrid_no_guard` is the pre-stated ablation named `readout_only`, under a
clearer name and with the same definition, "hybrid without the guard". The old
name fitted Round 1, where only readout carried weight; in Round 2 all four
groups carry weight, so the old name would mislead.

The pre-stated ablation `guard_only`, meaning stale plus the guard, is not run.
At `M = 1` it is identical to `stale`, and freeze test (iv) proves the two
forbidden sets are equal rather than spending simulation to rediscover it.

## 6. Job design

Round 1's job generator, unchanged, with new dates. One
`numpy.random.default_rng(20260828)` is created once. Machines are visited in
sorted name order. Within a machine, days are visited in ascending date order.
For each day, 3 values are drawn uniformly from [0, 86400) seconds, sorted
ascending, and added to that day's 00:00:00 UTC.

* Submission days: 13 October to 23 October 2026 inclusive.
* Delays `D`: 1, 3, 6, 12, 24, 48 hours.
* A job is valid only if at least 5 states of history exist at `t_s` and the
  run time `t_r = t_s + D` is not past the newest state on disk. Invalid jobs
  are dropped and counted per delay, never silently skipped, which is
  `PROTOCOL.md` section 3. Because the fresh window ends at 24 October
  00:00 UTC, this rule by itself stops 48 hour jobs after 22 October, with no
  special case written for it.
* A job's identity is `(machine, draw_order, delay_h, circuit)`.

The state store the engine reads spans BOTH windows, 28 August to 24 October,
because a job submitted on 13 October has to look back at the last 12 distinct
values of each field and those sit in the development window. It is built in
`data/clean_r2` and `data/cache_r2` from symlinks to the cards, and
`scripts/35_build_round2_tables.py` stops unless the development part of the
combined tables reproduces `data/clean` row for row and value for value.
`data/raw` and `data/clean` are only read.

## 7. Hypotheses, in order

**H1, no harm.** `hybrid` minus `stale`, pooled over `D = 1` and `D = 3` hours,
has a lower 95 percent bound above -0.002. This is the first thing tested,
because a rule that helps at long delay and quietly hurts at short delay is not
a usable rule.

**H2, primary.** `hybrid` minus `stale`, pooled over `D = 6`, 12, 24 and 48
hours, has a lower 95 percent bound above 0. `D = 6` and `D = 24` are also
reported separately.

**Secondary, all reported whatever they say:**

* `hybrid` minus `window_mean`, pooled over 6 to 48 hours
* `hybrid` minus `shrinkage_r1`, pooled over 6 to 48 hours
* `hybrid` minus `hybrid_no_guard`, pooled over 6 to 48 hours
* by circuit family, GHZ, BV and QFT, and by individual circuit
* by machine
* the three dead qubit views of section 9
* every arm against `stale`, and every arm's mean regret against the ceiling

Everything that is not H1 or H2 is secondary and is labelled as such. Nothing
outside this list is promoted to a headline afterwards.

## 8. Intervals and the bootstrap

95 percent intervals from a block bootstrap that resamples WHOLE CALENDAR DAYS,
which is `PROTOCOL.md` section 11. `scripts/31_analyse_round2.py` imports
`block_boot` from `scripts/20_analyse_results.py` rather than reimplementing
it, so it is literally the same function Round 1 used, with the same
`SEED_BOOT = 20261014` and the same `N_BOOT = 4000`.

A design effect is also reported: the clustered standard error divided by the
naive one, squared. It says how much the honest interval is widened by jobs on
the same day moving together.

## 9. Exclusions, the publishing gap, and the dead qubit views

**Nothing is excluded except what this section declares.** The only exclusion
is the validity rule of section 6, and its drops are counted per delay.

**The publishing gap stays in.** If the fresh window contains an interval
longer than 18 hours between neighbouring distinct states, that is a publishing
gap. Jobs that straddle one are kept in the headline and are also reported
separately so the effect is visible. The threshold is 18 hours, fixed here
before any fresh card was seen, and it is far above the normal spacing, which
in the development window was under an hour. This is `PROTOCOL.md` section 10
and Amendment A1.6 carried forward. Round 1's headline script departed from it
by dropping the gap jobs; that departure is recorded in L-052 and L-053 and is
not repeated.

**The three dead qubit views.** A stale pick can land on a qubit that has since
failed, and that is a real outcome, not an error. It is reported three ways:

1. every row as it is
2. jobs with a dead row in any arm dropped
3. dead rows forced to fidelity 0

Round 1 had four views because the `random` arm could carry a dead row by
itself. Round 2 drops `random`, so "any arm" and "any informed arm" are the
same set and two of the four coincide. The share of total stale regret that
sits on dead rows is reported under each view.

## 10. Sanity checks

1. Stale regret is exactly 0 on jobs where no new state appeared.
2. Ceiling regret is exactly 0 by construction.
3. The count of rows whose chosen qubits were dead on the run-time card is
   reported, not suppressed.
4. Every job carries all six arms.

The run is reported either way, with any failure stated.

## 11. Compute cuts

The engine run is timed first on a pilot of 30 jobs per circuit. If the
projected full run on all cores is longer than 5 hours, cuts are applied in
this order and no other, and the decision is logged before the full run starts:

1. drop the two ablations
2. reduce from 3 to 2 submissions per machine-day
3. drop `qft10`

A cut changes which jobs are run. It never changes the rule.

## 12. Environment

The run is on `team_code/.venv`, which is Python 3.12.4, qiskit 2.5.2,
qiskit-aer 0.17.2, qiskit-ibm-runtime 0.50.0, on an 8 core Apple machine. This
is the Round 1 run environment, as `PROTOCOL.md` section 16 requires.

## 13. Safety

The API key and the instance CRN live only in `.env` and are never printed or
written to any output or log. `data/raw` is read only. Fresh cards go to
`data/fresh`, which is gitignored, is never printed in full and is never
committed. No hardware job is submitted at any point. Nothing is invented: if
a card or a day is missing it is reported missing and not filled.

## 14. Stop rules

The run stops, rather than continuing, in exactly two cases:

1. Stage 0: no card date is retrievable for any machine.
2. Stage 2: any freeze test fails.

Anything else is flagged in `PROGRESS_LOG.md` as a deviation, with the exact
change, and the run continues.
