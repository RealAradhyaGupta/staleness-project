# HARDWARE SENSITIVITY, POST HOC

**POST HOC and EXPLORATORY. Not a result and not a test.** The
reported hardware numbers are the frozen ones from
`scripts/43_hw_analyse.py`, which is unchanged. Nothing here
supersedes them. This file exists to show how much that single
number leans on the choices behind it, which is a limitation to
state, not a new finding.

Source files, read only: `outputs/hardware/hw_jobs.csv`,
`outputs/hardware/hw_summary.json`. 12 jobs, 3 arms, 36 rows.

Sign convention unchanged: gain = F_strategy minus F_stale, so
positive means the strategy beat trusting the newest card.

The frozen numbers this file re-cuts, for reference:

| comparison | n | mean | sd | 95 pct low | 95 pct high |
| --- | --- | --- | --- | --- | --- |
| window_mean minus stale | 12 | -0.012559 | 0.043819 | -0.039064 | +0.007098 |
| hybrid minus stale | 12 | +0.000180 | 0.022462 | -0.012527 | +0.011511 |
| hybrid minus window_mean | 12 | +0.012738 | 0.044077 | -0.002760 | +0.039035 |

## (a) The 12 paired differences, by compile time and circuit

`slot` is the compile time: slot 1 = t0, slot 2 = t0+2h, slot 3 =
t0+4h. Each slot compiled against one calibration card, so the four
jobs in a slot share that card.

| slot | compile time (UTC) | circuit | F_stale | F_window_mean | F_hybrid | window_mean minus stale | hybrid minus stale |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 2026-10-25T16:36:16 | bv8 | 0.829000 | 0.696000 | 0.847000 | -0.133000 | +0.018000 |
| 1 | 2026-10-25T16:36:16 | ghz5 | 0.925153 | 0.943914 | 0.933206 | +0.018762 | +0.008054 |
| 1 | 2026-10-25T16:36:16 | ghz8 | 0.860184 | 0.860184 | 0.860184 | +0.000000 | +0.000000 |
| 1 | 2026-10-25T16:36:16 | qft5 | 0.869395 | 0.882041 | 0.882041 | +0.012646 | +0.012646 |
| 2 | 2026-10-25T18:36:17 | bv8 | 0.832000 | 0.826000 | 0.838000 | -0.006000 | +0.006000 |
| 2 | 2026-10-25T18:36:17 | ghz5 | 0.926978 | 0.923151 | 0.925990 | -0.003827 | -0.000988 |
| 2 | 2026-10-25T18:36:17 | ghz8 | 0.843875 | 0.881500 | 0.881500 | +0.037625 | +0.037625 |
| 2 | 2026-10-25T18:36:17 | qft5 | 0.915892 | 0.886980 | 0.886980 | -0.028912 | -0.028912 |
| 3 | 2026-10-25T20:35:55 | bv8 | 0.868000 | 0.875000 | 0.885000 | +0.007000 | +0.017000 |
| 3 | 2026-10-25T20:35:55 | ghz5 | 0.931325 | 0.938977 | 0.926706 | +0.007652 | -0.004618 |
| 3 | 2026-10-25T20:35:55 | ghz8 | 0.890852 | 0.874368 | 0.874368 | -0.016483 | -0.016483 |
| 3 | 2026-10-25T20:35:55 | qft5 | 0.921492 | 0.875327 | 0.875327 | -0.046164 | -0.046164 |

Exact ties, counted and kept, never dropped: window_mean 1 of 12, hybrid 1 of 12.
A tie is a job where the two arms transpiled to the identical
circuit, so it ran once and both arms were given that one result.

## (b) Means by compile time and by circuit

### By compile time, 3 clusters of 4 jobs

| slot | n | window_mean minus stale | hybrid minus stale |
| --- | --- | --- | --- |
| 1 | 4 | -0.025398 | +0.009675 |
| 2 | 4 | -0.000279 | +0.003431 |
| 3 | 4 | -0.011999 | -0.012567 |

Spread across the 3 compile times: window_mean -0.025398 to -0.000279 (range 0.025120),
hybrid -0.012567 to +0.009675 (range 0.022241).

### By circuit, 4 clusters of 3 jobs

| circuit | n | window_mean minus stale | hybrid minus stale |
| --- | --- | --- | --- |
| bv8 | 3 | -0.044000 | +0.013667 |
| ghz5 | 3 | +0.007529 | +0.000816 |
| ghz8 | 3 | +0.007047 | +0.007047 |
| qft5 | 3 | -0.020810 | -0.020810 |

Spread across the 4 circuits: window_mean -0.044000 to +0.007529.
With 3 jobs per circuit and 4 per compile time, none of these cells
carries an interval worth printing. They are shown to display the
spread, not to support a per-cell claim.

## (c) Leave one job out

Each row drops exactly one of the 12 jobs and recomputes the mean
over the remaining 11. This shows how far one job can move the
reported figure.

| job dropped | window_mean minus stale | hybrid minus stale |
| --- | --- | --- |
| s1_bv8 | -0.001609 | -0.001440 |
| s1_ghz5 | -0.015406 | -0.000536 |
| s1_ghz8 | -0.013700 | +0.000196 |
| s1_qft5 | -0.014850 | -0.000953 |
| s2_bv8 | -0.013155 | -0.000349 |
| s2_ghz5 | -0.013352 | +0.000286 |
| s2_ghz8 | -0.017121 | -0.003224 |
| s2_qft5 | -0.011072 | +0.002825 |
| s3_bv8 | -0.014337 | -0.001349 |
| s3_ghz5 | -0.014396 | +0.000616 |
| s3_ghz8 | -0.012202 | +0.001695 |
| s3_qft5 | -0.009503 | +0.004393 |

All 12 jobs in: window_mean -0.012559, hybrid +0.000180.
Leave-one-out range: window_mean -0.017121 to -0.001609, hybrid -0.003224 to +0.004393.
The single most influential job for the primary comparison is `s1_bv8`: dropping it moves window_mean minus stale from -0.012559 to -0.001609, a change of +0.010949.
One job out of twelve moving the headline by that much is the point of this section.
Sign changes under leave-one-out: window_mean no, hybrid yes.

## (d) A bootstrap that resamples whole compile times

Jobs compiled at the same time share one calibration card, so they
are not independent of each other. The honest resampling unit is
therefore the compile time, not the job. That is the same argument
Round 1 and Round 2 used for resampling whole calendar days.

Resampling 3 whole compile times with replacement, 4000 resamples, seed 20261029:

| comparison | mean | 95 pct low | 95 pct high | width |
| --- | --- | --- | --- | --- |
| window_mean minus stale | -0.012559 | -0.025398 | -0.000279 | 0.025120 |
| hybrid minus stale | +0.000180 | -0.012567 | +0.009675 | 0.022241 |

Against the frozen job-level intervals:

| comparison | job-level width (frozen) | compile-time width | ratio |
| --- | --- | --- | --- |
| window_mean minus stale | 0.046162 | 0.025120 | 0.54x |
| hybrid minus stale | 0.024038 | 0.022241 | 0.93x |

**Three clusters are far too few for a reliable interval, and this
interval must not be quoted as a result.** Saying it plainly: with
3 clusters there are only 10 distinct multisets of 3 draws, so the
bootstrap distribution is built from at most 10 different values of
the mean. A percentile interval taken from 10 possible values has
no meaningful 2.5th or 97.5th percentile. The numbers above show
exactly that degeneracy: both endpoints land precisely on the
smallest and largest of the 3 compile-time means in the table in
(b). The interval is the range of 3 numbers and nothing more.

**Because of that degeneracy the width ratio above says nothing in
either direction.** It came out below 1, but a percentile interval
that collapses onto the range of 3 values is not evidence that the
frozen interval is too wide, and it would not have been evidence
that it is too narrow either.

### A standard error is the more informative comparison

The clustered standard error does not degenerate the same way, so
it gives a better sense of direction, though 3 clusters still make
it unreliable.

| comparison | naive SE, 12 independent jobs | clustered SE, 3 compile times | ratio |
| --- | --- | --- | --- |
| window_mean minus stale | 0.012649 | 0.007257 | 0.57x |
| hybrid minus stale | 0.006484 | 0.006623 | 1.02x |

**This is the opposite of Round 1 and Round 2.** There the design
effect was 5.247 and 9.400, so jobs on the same day moved together
strongly and the naive interval was far too narrow. Here the
clustered standard error is about the same as the naive one for the
hybrid and smaller for the window mean, which says most of the
variation in these 12 jobs sits WITHIN a compile time rather than
between compile times. The table in (b) shows why: the four
circuits inside one slot disagree far more than the three slots
disagree with each other, and `s1_bv8` alone is -0.133.

So on this evidence, treating the 12 jobs as independent is not
obviously anti-conservative, and I am not claiming the frozen
interval is too narrow. This is consistent with the clustering
mattering little here; it does not prove it, because 3 clusters
cannot estimate a design effect with any precision.

The correct reading of (d) as a whole: neither the cluster
bootstrap nor the clustered standard error settles anything at 3
clusters. A study that wanted to settle it needs many more compile
times, not more jobs per compile time.

## (e) What the original analysis actually did

**The frozen analysis treated the 12 jobs as independent. It did
NOT group by compile time.** `scripts/43_hw_analyse.py` line 59
draws `rng.integers(0, len(x), size=(n_boot, len(x)))`, which
resamples the 12 job-level differences one at a time with
replacement. `FREEZE_HARDWARE.txt` records the same choice before
the run: "bootstrap 4000 resamples of the jobs, seed 20261025".

The script's own docstring explains why the JOB rather than the ROW
is the unit: the three arms of one job share one queue position and
one calibration epoch, so the 36 rows are not 36 independent
numbers. That reasoning is right and it was applied. What it does
not do is take the next step: the same argument applies again one
level up, because the four jobs in a compile slot share one
calibration card. So the analysis removed the within-job dependence
and left the within-slot dependence in place.

This was a pre-stated choice, written into FREEZE_HARDWARE.txt
before any job ran, so it is not a departure from the protocol and
nothing was changed after seeing the data. It is a limitation of
the frozen design, and the right place for it is the limits
section, which is why this file exists.

Consistent with, not proved: the standard errors in (d) are
consistent with the within-slot dependence mattering little in
these 12 jobs, which would mean the frozen job-level interval is
not badly wrong. With 3 clusters that cannot be established either
way, so the limitation stands as a limitation and not as a
correction to the reported number.
