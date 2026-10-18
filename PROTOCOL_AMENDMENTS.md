# PROTOCOL AMENDMENTS

Amendments to `PROTOCOL.md` (frozen 13 October 2026,
sha256 `dda0f4fc747a65c81206b1360a5b9d38261128ff9099c4f6a98c071b27992ae5`).

**This file is append-only.** A new amendment is added at the bottom with its
own date. No amendment is ever edited or deleted after it is written. If an
amendment turns out to be wrong, a later amendment corrects it and the wrong
one stays visible.

`PROTOCOL.md` itself is never edited. It stays at mode 444. Where an amendment
here disagrees with the frozen protocol, the amendment wins, and the frozen
text stays as a record of what was originally decided.

This file is left writable, unlike `PROTOCOL.md`, because new amendments must
be appended to it. Its sha256 is recorded in PROGRESS_LOG.md each time it
changes, which is what makes tampering visible.

---

## Amendment A1

**Date:** 13 October 2026, 23:08 IST (17:38 UTC).

**Status: made before any run.** At the time of writing, no regret has been
measured, no simulation has been run, and no result of any kind exists under
this protocol. Every change below is therefore a design decision taken blind,
not a reaction to a number I did not like. This matters most for change 6,
which moves the train and test split.

These changes answer the seven open risks recorded in section 17 of the frozen
protocol.

### A1.1 Where the calibration numbers come from

**Change.** `data/clean/states.csv` is an INDEX, not the numbers. The
calibration values for a state come from `data/clean/qubits.csv` and
`data/clean/pairs.csv`, joined on `machine` plus `snapshot_utc` equal to that
state's `first_seen_utc`.

**Reason.** The 28 columns of `states.csv` are timestamps, per field value
dates and ages, counts and dead lists. There is not a single T1, T2 or error
value in the file. Section 2 of the protocol as frozen could therefore be read
as an instruction that cannot be carried out. This change names the real source
so the engine has somewhere to read from. It also keeps `data/raw` read-only
and untouched, since the flat tables already hold every value the engine needs.

### A1.2 Windows are per field, not per state

**Change.** In every strategy, "the last N" means the last N DISTINCT VALUES OF
THAT FIELD, not the last N states. Each field (T1, T2, readout error, sx error,
cz error) keeps its own history and its own window.

**Reason.** This was risk 1 in section 17 and it is the change that matters
most. A state is new if ANY of the five fields changed, and L-017 measured
readout error moving far more often than the rest. So five consecutive states
can easily carry five identical cz values. Under the frozen wording the window
mean for cz would then equal the latest value and its standard deviation would
be exactly zero, which would silently collapse the std-adjusted arm into the
window mean arm. That would have been an artefact of my own definition
masquerading as a result about the method. Counting distinct values per field
also matches L-016 decision 1, which already said the clock is the value's own
date.

### A1.3 Tuning uses the analytic success probability, on a small fixed grid

**Change.** Tuning is done on the analytic estimated success probability, on
training days only, over this grid, fixed now and not extended later:

- N in {3, 5, 10} distinct values per field
- weight w in {0, 0.5, 1} for each of three field groups:
  1. readout error
  2. sx error and cz error
  3. T1 and T2

That is 3 x 3 x 3 x 3 = 81 settings. Simulation is run ONLY for the single
chosen setting.

**Reason.** This was risk 2. A full simulated pass is roughly 74500 runs, about
2 hours by the scaling in section 17, and running a grid under simulation would
turn that into days. The analytic success probability carries no shot noise and
costs almost nothing, so it is the right thing to sweep. Fixing the grid in
advance and writing it down is what stops me from quietly widening the search
until something wins. Grouping the five fields into three keeps the grid at 81
instead of 243 and reflects what L-017 found: readout behaves differently from
sx and cz, and T1 and T2 always share a date so they move together.

### A1.4 "Oracle" is renamed "ceiling"

**Change.** The arm called `oracle` in the frozen protocol is called `ceiling`
in all reports, charts, tables and code. It is defined as "best available
reported numbers".

**Reason.** This was risk 4. The word oracle promises perfect knowledge, and
this arm does not have it. L-017 measured the values inside a state as already
a median of 13 to 16 hours old in sx and cz error at the moment the state is
first published. So the arm sees the best REPORT available at run time, not the
machine's true condition. A reader who sees "oracle" will overestimate what the
ceiling means and therefore underestimate the true cost of staleness.

### A1.5 Permanent defects come from training days only

**Change.** The permanent defect list is computed from states on TRAINING DAYS
ONLY, and that list is then held fixed and unchanged for the test days.

**Reason.** This was risk 3. The permanent list in L-017 (qubit 72 on ibm_fez,
113, 121 and 146 on ibm_kingston, 82, 94, 113 and 130 on ibm_marrakesh) was
computed over all 921 states, which includes the test fortnight. Since every
arm uses that list, a little information from the test days leaks into every
arm's choice. The leak is small, but a leak that is easy to remove should be
removed rather than defended. The training-only list may differ from the L-017
list, and whatever it turns out to be is recorded before the test days are
touched.

### A1.6 The train and test split moves

**Change.**

- Training days: **28 August to 20 September 2026** (24 days).
- Test days: **21 September to 12 October 2026** (22 days).

This replaces the frozen split of 32 training days and 14 test days.

**Reason.** This was risk 5: 14 test days is a thin basis for a block bootstrap
that resamples whole days. Moving the boundary gives 22 test blocks instead of
14, which is more statistical power exactly where the protocol's two
confirmatory comparisons live. Nothing has been measured yet, so this choice
cannot have been influenced by any result. 24 training days is still ample for
an 81 point grid on an analytic metric.

**Consequence I am recording now, before anyone notices it later.** The 22 to
23 September platform wide publishing gap now falls inside the TEST window, not
the training window as it did under the frozen split. Section 10 of the
protocol says that gap stays in and is reported separately, and that still
holds. But it now sits in the test days, so it will affect the headline
numbers, and the jobs that straddle it must be reported separately from the
rest of the test set. I did not move the boundary in order to move the gap, and
I am stating that here because the effect is real either way.

### A1.7 Random arm, dropped jobs, and one simulator seed per job

**Change.**

- The random layout arm draws **5 layouts per job**, with a seed recorded in
  the engine config as `SEED_RANDOM`. The arm's reported fidelity is the mean
  over those 5 draws.
- Jobs whose truth state falls outside the data are **dropped and counted**,
  with the count reported per delay D.
- Within a single job, **every arm uses the same simulator seed**, so identical
  inputs must produce identical outputs.

**Reason.** This was risk 6 and part of risk 5. A single random layout is very
noisy, so one draw would make the floor arm jump around for no reason; five
draws cost almost nothing because the floor needs no precision, only a clear
separation from the informed arms. Dropping jobs with no truth state is forced
by the data ending on 12 October, and counting them keeps the thinning of
D = 48 visible instead of hidden. The shared simulator seed is what makes
sanity check 1 in section 12 meaningful: stale regret can only be EXACTLY zero
when no new state appeared if the two arms, given the same numbers, run the
same circuit with the same randomness.

### Risks from section 17 NOT addressed by this amendment

- **Risk 7, the base target.** Settled separately on the same day, see
  PROGRESS_LOG.md L-021. It needed measurement, not a design decision.
- **`ghz10` and `bv10` still do not exist** in the teammates' `circuits.py` and
  must be added before the engine runs.

---

## Amendment A2

**Date:** 14 October 2026, 00:35 IST (13 October 2026, 19:05 UTC), taken from the `date` command.

*(Correction made within the same minute, before this file's checksum was recorded anywhere: the first draft of this line carried a guessed time of 01:22 IST. Times must come from `date`, never from a guess, so it was replaced with the real one. Nothing else in A2 changed.)*

**Status: made on TRAINING DAYS ONLY. No test day has been simulated, read for
tuning, or looked at in any way.** The test window under A1.6 is 21 September
to 12 October and nothing in this amendment used it.

### A2.1 The chosen per-field shrinkage setting

**Chosen.**

    N        = 3 distinct values per field
    w_readout = 0.5
    w_gate    = 0.0   (sx error and cz error)
    w_times   = 0.0   (T1 and T2)

**The rule, which was written down in `engine/tune_shrinkage.py` before any
number was looked at.** Lowest mean ESP regret against the ceiling, pooled over
machines, circuits and delays, on training days. Ties broken by the smaller N,
and if N also ties, by the smaller total weight, which prefers the simpler
rule.

**The evidence.** 81 settings, 6330 training jobs (ibm_fez 2160, ibm_kingston
2130, ibm_marrakesh 2040), 1915 distinct ceiling ESPs, 288 seconds on 6
workers. Full grid saved to `outputs/tuning_training_only.json`.

| setting | mean ESP regret |
|---|---|
| chosen: N=3, w=(0.5, 0.0, 0.0) | 0.014548 |
| all weights zero, which IS the stale rule | 0.015243 |
| worst of the grid: N=10, w=(1.0, 1.0, any) | 0.019710 |

So the chosen rule improves the analytic metric by 0.000695 against stale,
which is 4.6 percent of stale's own regret. That is small. It is also measured
on the analytic metric, not on fidelity, and on training days. It is not a
result and it does not predict what the test days will show.

Best value of each knob, holding the others at their best:
w_readout 0.0 gives 0.014981, **0.5 gives 0.014548**, 1.0 gives 0.015526.
w_gate 0.0 gives 0.014548, 0.5 gives 0.014581, 1.0 gives 0.015107.
N=3 gives 0.014548, N=5 gives 0.014640, N=10 gives 0.014581.

### A2.2 An honest limit of this tuning, recorded now

**The analytic success probability cannot see T1 or T2.** ESP is a product of
(1 minus gate error) over the gates a circuit runs, plus readout error. T1 and
T2 do not enter it. I checked rather than assumed: across all 27 combinations
of (N, w_readout, w_gate), the three values of w_times give a score identical
to twelve decimal places.

**Therefore `w_times = 0.0` was chosen by the TIE-BREAK, not by evidence.** The
grid could not distinguish it. I am recording this instead of presenting
w_times as a tuned value, because a reader would otherwise assume all three
weights were measured.

What follows from that. T1 and T2 still reach the simulation through the Aer
thermal relaxation channel, so they do affect fidelity even though they do not
affect ESP. A future amendment may tune w_times on simulated fidelity using
training days only. Until then, w_times stays 0.0, which means T1 and T2 are
taken from the latest value with no shrinkage, which is the same thing the
stale arm does.

### A2.3 What this changes in the code

`engine/engine_config.py` now holds `SHRINK_N = 3` and
`SHRINK_W_BY_GROUP = {"readout": 0.5, "gate": 0.0, "times": 0.0}`, replacing
the untuned placeholder of N=5 and w=0.5 everywhere. Every output from here on
drops the NOT TUNED label for the shrinkage arm and carries these values
instead.

### A2.4 A fault that was fixed BEFORE this tuning ran

The tuning above was run on corrected code. Before it, `distinct_history()`
compared value vectors with `np.array_equal(a, b)`, which returns False
whenever a NaN is present, because NaN is not equal to itself. Any field with a
missing value on any qubit therefore looked like a new distinct value at every
single state. On ibm_kingston that made T1 and T2 appear to have 136 distinct
values on training days when they really have 24.

That is exactly the failure Amendment A1.2 was written to prevent, arriving by
a different door: the per field window silently became a per state window for
T1 and T2. The fix is `equal_nan=True`. It is recorded in PROGRESS_LOG.md
L-027, and the pilot numbers for the window mean, std-adjusted and shrinkage
arms in L-025 are withdrawn because of it. The stale and ceiling arms, and
therefore the headline staleness cost in L-025, are not affected, because
neither of them uses a window.

---

## Amendment A3

**Date:** 14 October 2026, 00:53 IST (13 October 2026, 19:23 UTC), captured from the `date` command and substituted
programmatically, never typed.

**Status: training days only. No test day has been simulated, read for tuning,
or looked at.**

### A3.1 w_times is fixed at 0.0, by evidence rather than by a tie-break

**Change.** `w_times = 0.0`. **N = 3, w_readout = 0.5 and w_gate = 0.0 are
unchanged from Amendment A2.** A3 settles one number and touches nothing else.

**Reason.** A2.2 recorded that the analytic success probability is blind to T1
and T2, so the 81 point grid could not distinguish `w_times` and the value came
from the tie-break. That left an honest gap: T1 and T2 do reach Aer through
thermal relaxation, so they affect fidelity even though they do not affect ESP.

Before spending simulation time on it, I tested the prior question: **can T1
and T2 change which qubits the compiler picks at all?** If they cannot, then
`w_times` cannot change any strategy's decision, and the weight is
unobservable rather than merely hard to measure.

**The test, with no simulation.** For 20 training states on each of the three
machines and all five circuits, I compiled the same circuit against three
targets that differ only in T1 and T2:

  * `base`, the real numbers
  * `halved`, every T1 and T2 divided by 2, which keeps the ranking
  * `shuffled`, T1 and T2 permuted across the live qubits, which destroys it

The shuffle was applied only to qubits that are not forbidden, and missing
values were left in place, so the dead qubit set is identical in all three.
That was checked, not assumed: the sets differed in 0 of the comparisons.

**Result: the chosen layout changed in 0 of 300 comparisons for halved, and 0
of 300 for shuffled.**

I checked that the test was not a no-op, because a null result from a variant
that never reached the target would prove nothing. On ibm_kingston state 100
the halved variant changed 155 of 156 T1 values in the compiled target and the
shuffled variant changed 148 of 156, while the sx and cz errors were identical
in both. So the numbers reached the compiler and the compiler ignored them.

**What this means.** Qiskit's layout step at optimisation level 2 scores
candidate qubits on gate and readout error. T1 and T2 sit in the target's
qubit properties and are read by scheduling, not by the layout choice. So
`w_times` cannot affect any arm's DECISION. T1 and T2 still affect the measured
fidelity, but only through the truth device, which every arm shares equally, so
the weight cancels out of every comparison.

**Therefore `w_times = 0.0` is now fixed on evidence.** No simulation budget was
spent, and the 150 job simulated tuning my supervisor authorised as the
fallback was not needed.

**The limit of this finding, stated plainly.** It is a fact about Qiskit's
preset pass manager at optimisation level 2, not a fact about quantum
computers. A scoring rule that did use T1 and T2, including a future version of
our own, would make `w_times` matter again and this amendment would have to be
revisited.

### A3.2 The settings that go into the test run

    N         = 3 distinct values per field
    w_readout = 0.5     tuned on ESP, Amendment A2
    w_gate    = 0.0     tuned on ESP, Amendment A2
    w_times   = 0.0     fixed by the sensitivity test above, Amendment A3

These are frozen for the test period run. Any change after the run starts is a
new amendment and invalidates the run.

---
