# ROUND 2 REPORT

Written from the files in `outputs/round2/` and `outputs/round2_run/`. Every
number below is copied from them. Nothing is rounded up in the rule's favour.

Sign conventions: `regret = ceiling minus strategy`, so positive regret means
worse. `gain = F_strategy minus F_stale`, so positive gain means better than
trusting the newest card.

## The short version

**Both pre-registered hypotheses failed. The fitted rule did not beat the
newest calibration card on fresh data.** The simpler window mean did, and the
dead qubit guard made things actively worse. This is a null result for the
rule, and it is reported as the main finding rather than buried.

## What was run

Cards from 13 October 2026 00:00 UTC to 24 October 2026 00:00 UTC, fetched
after the rule was frozen and its checksums written. 1184 cards, which collapse
to 323 distinct calibration states: 112 on ibm_fez, 87 on ibm_kingston, 124 on
ibm_marrakesh. Every machine published on every one of the 11 days. No date is
missing and nothing was filled in.

4392 jobs, 6 arms each, 26352 rows, in 2.88 hours on 6 workers with no worker
failure. 8 circuits, 6 delays, 3 machines. Jobs whose run time fell past the
last card were dropped and counted per delay, 45 in all, rising with the delay
as expected: 13 on fez, 17 on kingston, 15 on marrakesh.

All four sanity checks passed. Stale regret is exactly 0 on the 920 jobs where
no new state appeared. Ceiling regret is exactly 0. Every job carries all 6
arms. 771 rows picked a qubit that was dead on the run-time card, which is a
real outcome and not an error.

## H1 and H2

| test | n jobs | days | mean | 95% low | 95% high | needs | verdict |
| --- | --- | --- | --- | --- | --- | --- | --- |
| H1 hybrid minus stale, D = 1 and 3 h | 1568 | 11 | -0.000758 | -0.003269 | 0.001220 | low above -0.002 | **FAIL** |
| H2 hybrid minus stale, D = 6 to 48 h | 2824 | 11 | 0.000151 | -0.008865 | 0.007510 | low above 0 | **FAIL** |

H1 is worth reading carefully. The rule did not measurably harm anything at
short delay: the point estimate is -0.000758, which is under a tenth of a
percent of fidelity. H1 failed because the interval is wide, with a lower bound
of -0.003269 against a threshold of -0.002, not because harm was observed. That
is a failure to show no harm, which is not the same as showing harm.

H2 is a clean null. The point estimate is 0.000151, essentially zero, and the
interval runs from -0.008865 to 0.007510.

By delay, hybrid minus stale:

| D (h) | n jobs | mean | 95% low | 95% high |
| --- | --- | --- | --- | --- |
| 1 | 784 | -0.000480 | -0.002655 | 0.001104 |
| 3 | 784 | -0.001036 | -0.004283 | 0.001748 |
| 6 | 776 | -0.002282 | -0.009570 | 0.004588 |
| 12 | 736 | -0.004916 | -0.013400 | 0.003169 |
| 24 | 680 | 0.002968 | -0.006888 | 0.011493 |
| 48 | 632 | 0.006010 | -0.008390 | 0.020066 |

The shape is the one the rule was built for, negative at short delay and
positive at long delay, and the two named delays are 6 h at -0.002282 and 24 h
at 0.002968. But every single interval crosses zero, so none of it is
distinguishable from noise.

## Why the intervals are so wide

The design effect, pooled over D = 6 to 48 h on 2824 jobs over 11 calendar
days, is **9.400**. The paired standard deviation is 0.071575, the naive
standard error 0.001347, and the honest clustered standard error 0.004130. So
the naive interval would have been about three times too narrow, and a naive
analysis would have declared H2 a win.

Round 1 measured a design effect of 5.247 on 22 calendar days. Round 2 has 9.4
on 11 days. Jobs on the same day move together strongly, and with only 11 days
there are only 11 effectively independent units. **The fresh window was too
short to settle a difference this small.** That is a design fault in Round 2,
and it was foreseeable: the Round 1 power calibration in L-051 said as much.

## The secondary results, which are more interesting than the primary ones

Every arm against stale, pooled over D = 6 to 48 h:

| arm | mean gain | 95% low | 95% high |
| --- | --- | --- | --- |
| window_mean | 0.005346 | 0.001584 | 0.008923 |
| hybrid_no_guard | 0.001897 | -0.007345 | 0.008998 |
| shrinkage_r1 | 0.000843 | -0.000495 | 0.002100 |
| hybrid | 0.000151 | -0.008739 | 0.007228 |

**The plain window mean is the only arm whose interval clears zero.** It beat
the newest card by 0.005346 with an interval from 0.001584 to 0.008923. The
carefully fitted hybrid came last of the four.

Mean regret against the ceiling, same pool, lower is better: window_mean
0.038707, hybrid_no_guard 0.042156, shrinkage_r1 0.043209, hybrid 0.043901,
stale 0.044053. The ordering agrees.

Hybrid against the others:

| comparison | mean | 95% low | 95% high |
| --- | --- | --- | --- |
| hybrid minus window_mean | -0.005194 | -0.014869 | 0.003354 |
| hybrid minus shrinkage_r1 | -0.000692 | -0.008963 | 0.005680 |
| hybrid minus hybrid_no_guard | -0.001745 | -0.003642 | **-0.000065** |

**The guard hurt, and that interval does not cross zero.** Turning the guard
off improved the rule by 0.001745, with an interval from -0.003642 to
-0.000065. This is the one comparison in the whole run that is clearly
separated from zero in the direction against the frozen rule.

This is consistent with what the fit already showed and I froze anyway. At
D = 24 h the guard's precision was only 0.2424 and its recall 0.2342: a qubit
that was dead on the card at submission time is usually not dead at run time.
Removing it throws away a working qubit about three times out of four. The
pre-stated criterion was best F1, and best F1 picked a rule that is mostly
wrong. Choosing M on F1 was the mistake, not the engine.

By machine: kingston 0.003800 with an interval from 0.000652 to 0.007485, which
clears zero; fez -0.001342 from -0.010877 to 0.006604; marrakesh -0.001979 from
-0.025679 to 0.016887. By circuit family: GHZ -0.002678, BV 0.001808, QFT
0.001876, all crossing zero. The best single circuit is qft5 at 0.006993 and
the worst is ghz8 at -0.005530, both crossing zero. The new QFT circuits worked
as intended and produced nothing anomalous.

## The publishing gap and the dead qubits

One publishing gap in the fresh window: ibm_marrakesh, 22 October 20:25:11 to
23 October 19:17:54, 22.88 hours. It stays in the headline, as section 9 of the
protocol requires, and is reported separately here. 192 jobs straddle it, 96 of
them in the D = 6 to 48 h pool, and on those hybrid minus stale is -0.027813
with an interval from -0.062299 to 0.074353. That interval spans more than
thirteen percentage points of fidelity across 3 calendar days, so it says
almost nothing on its own. Excluding them would have moved the headline from
0.000151 to 0.001136, and still inside a wide interval either way.

The three dead qubit views, H2 recomputed under each:

| view | n jobs | mean | 95% low | 95% high | dead-row share of stale regret |
| --- | --- | --- | --- | --- | --- |
| 1 all rows as they are | 2824 | 0.000151 | -0.009153 | 0.007570 | 0.4389 |
| 2 jobs with a dead row in any arm dropped | 2554 | -0.001588 | -0.006411 | 0.002496 | 0.0000 |
| 3 dead rows forced to fidelity 0 | 2824 | 0.001669 | -0.015783 | 0.018208 | 0.6283 |

H2 fails under all three, so the verdict does not depend on how dead rows are
handled. But the share is striking: **43.89 percent of all stale regret sits on
rows whose chosen qubits were dead at run time**, rising to 62.83 percent when
those rows are scored as total failures. In Round 1 that share was 17.33
percent. Dropping those jobs flips the point estimate negative, which says the
little the rule gains, it gains on exactly those jobs.

The reason is in the data. On 15 October ibm_fez had a readout failure episode
lasting about ten hours, 05:44:28 to 15:37:18, in which 72 to 75 of its 156
qubits had readout error above 0.2 and so counted as dead. That is 16 of the
323 fresh states, 5.0 percent. It was kept in, as the protocol requires. Fez's
median dead count per state is 3 in the fresh window against 1 in development,
while kingston and marrakesh are unchanged.

A sudden ten hour failure is the worst possible case for this rule, and that is
worth saying plainly even though it is reasoning after the fact and not a
pre-registered test. The rule puts weight 0.90 on the median of the last 12
readout values at D = 24 and 48 h. During a real failure the newest card is
right and the trailing median is wrong, so heavy smoothing actively discards
the correct answer. The development fit could not see this, because it scored
how well a blend predicts the next card on average, and an average over 46
quiet days does not price in a rare sharp break.

## What changes

Nothing in the rule, which is frozen. What changes is the conclusion.

Round 1 found that a per field shrinkage fix moved the number a little. Round 2
asked whether a properly fitted version beats the newest card on data that did
not exist when the rule was fixed. **On these 11 days, it does not.** The
honest summary is that the simple window mean remains the only strategy that
beats the newest card by a margin an honest interval can see, and that the more
machinery was added, the worse it got.

Three things are consistent with each other and point the same way: fitting a
blend weight to predict the average next card does not optimise the thing we
care about, which is the qubit choice; choosing the guard on F1 picked a rule
that is wrong three times out of four; and 11 calendar days with a design
effect of 9.4 cannot resolve an effect of half a percent.

## Correction (L-058)

**Appended 29 October 2026. Nothing above this line has been changed or
reworded.** This section corrects two things in the text above. Every number
here comes from the Part N output files
`outputs/stage6_explore/N1_hybrid_vs_window.csv` and
`outputs/stage6_explore/N2_dead_qubit_share.csv`, which are exploratory,
Round 2 rows only, and were written on 25 October 2026.

### 1. The paragraph about the 15 October fez readout episode is wrong

The paragraph beginning "A sudden ten hour failure is the worst possible case
for this rule" says that during a real failure the newest card is right and the
trailing median is wrong, so heavy smoothing discards the correct answer. It
labels itself reasoning after the fact rather than a test, which it is. **The
direction is backwards, and Part N measures the opposite.**

Inside the episode the hybrid GAINED:

| cut | n jobs | days | hybrid minus stale | 95 pct low | 95 pct high |
| --- | --- | --- | --- | --- | --- |
| only the episode | 136 | 3 | +0.015334 | +0.004746 | +0.042191 |
| all jobs | 2824 | 11 | +0.000151 | -0.008292 | +0.007371 |
| excluding the episode | 2688 | 11 | -0.000617 | -0.009693 | +0.006989 |

So removing the episode makes the hybrid **worse**, from +0.000151 to
-0.000617. The episode was helping the hybrid, not hurting it. The window mean
behaves the same way: +0.005346 on all jobs falling to +0.004998 with the
episode removed, and +0.012224 inside the episode.

The reason the original guess had the sign backwards: the failure lasted about
ten hours, so for most of these jobs the run-time card had already recovered.
That makes the trailing median the better picture of the device and the newest
card the misleading one, which is the reverse of the sudden-break story. This
is consistent with the episode being a recovery window rather than a break; it
is not proved, and the interval on the episode cut is wide and rests on 3
calendar days.

This correction was recorded in PROGRESS_LOG.md entry L-058 on 25 October
2026, before this report section was written. The superseded paragraph is left
standing above.

### 2. The window mean is worse than stale at D = 1 h and 3 h

The section "The secondary results, which are more interesting than the primary
ones" says the plain window mean is the only arm whose interval clears zero and
that it beat the newest card by 0.005346. That is true **only in the D = 6 to
48 h pool it was computed on**, and the report does not say that the same arm
is clearly harmful at the two short delays:

| cut | n jobs | days | window_mean minus stale | 95 pct low | 95 pct high |
| --- | --- | --- | --- | --- | --- |
| D = 1 h | 784 | 11 | -0.008416 | -0.012258 | -0.004930 |
| D = 3 h | 784 | 11 | -0.005270 | -0.010084 | -0.000569 |

**Both intervals lie entirely below zero.** At short delay the window mean
harms the layout choice, and it does so more clearly than anything the hybrid
was penalised for: H1 failed on a lower bound of -0.003269 against a threshold
of -0.002, while the window mean's point estimate alone is -0.008416 at 1 h.

The hybrid is not the worse rule at short delay. For comparison, from the same
file:

| cut | n jobs | hybrid minus stale | 95 pct low | 95 pct high |
| --- | --- | --- | --- | --- |
| D = 1 h | 784 | -0.000480 | -0.002631 | +0.001098 |
| D = 3 h | 784 | -0.001036 | -0.004219 | +0.001726 |

The hybrid's tapering of its weights towards zero at short delay did the job it
was designed for. Had the window mean been the pre-registered rule it would
have failed the H1 no-harm test considerably worse than the hybrid did.

At long delay the order reverses and the window mean wins: at D = 24 h it is
+0.008774 [+0.002547, +0.014848] against the hybrid's +0.002968, and at D = 48 h
+0.012173 [+0.004863, +0.020044] against +0.006010. Same sign, but the hybrid
captures only about a third to a half of the available gain.

**What this changes.** Neither pre-registered verdict changes: H1 and H2 both
still fail, and the rule still did not beat the newest card. What changes is
the recommendation. The sentence above that the window mean "remains the only
strategy that beats the newest card by a margin an honest interval can see"
should be read as applying to D = 6 to 48 h only. Across all six delays the
window mean is not a safe drop-in replacement, because it is measurably harmful
at 1 h and 3 h. A rule that tapers its weight at short delay, which is what the
hybrid does, is the right shape; the frozen weights were simply too timid at
long delay.

All of this is EXPLORATORY and post hoc. Part N was not pre-registered, the
cuts were chosen after seeing the Round 2 result, and none of it can support a
confirmatory claim.
