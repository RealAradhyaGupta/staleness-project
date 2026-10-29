# Stage 6 Part B: exploratory findings

**EXPLORATORY AND POST HOC throughout.** Every number here was computed after
the Round 2 results were known. None of it is confirmatory. None of it changes
the rule, the protocol, any frozen file or any Round 2 result. Nothing was
simulated, no quantum job was submitted and no IBM call was made. The word for
agreement is "consistent with", never proved.

Produced by `scripts/44_stage6_explore.py`. Store: `data/clean_r2`, 28 Aug to
24 Oct 2026. Console: `KM_console.txt` and the J output.

## J. How often does each field group change?

The question was whether the publishing schedule is regular in AGE even though
the clock hour wanders. For three of the four groups, yes.

| group | median interval | mean IQR width | within 24 +- 3 h | clock R | busiest 6 h block |
| --- | --- | --- | --- | --- | --- |
| readout | 4.71 h | 4.96 h | 0.9% | 0.096 | 32.1% |
| sx | 25.05 h | 1.85 h | 66.3% | 0.367 | 49.4% |
| cz | 25.03 h | 3.57 h | 65.1% | 0.366 | 48.6% |
| T1/T2 | 24.83 h | 2.45 h | 68.3% | 0.364 | 51.4% |

`clock R` runs from 0 (changes spread right round the clock) to 1 (all at one
hour). The busiest 6 hour block holds 25 percent of changes when the clock hour
is spread evenly.

sx, cz and T1/T2 change about once a day with a tight spread in the interval
and a much looser spread on the clock. The median interval is slightly ABOVE
24 h, which is exactly what makes the clock hour drift forward by roughly an
hour a day: regular in age, wandering on the clock.

Readout is a different process. It changes every 4.7 hours, almost never at a
24 hour spacing, and its clock hour is close to uniform.

A note on a number I got wrong and fixed: an earlier version of this part
printed a circular SD and compared it with a claimed maximum of 6.93 h. The
circular SD is not bounded, so that ceiling does not exist. The fez readout row
showed 10.48 h, above the claimed maximum, which is how it was caught. The
unbounded number is still in `J1_change_intervals.csv`; the printed columns are
now `clock R` and the busiest 6 hour share, both of which are bounded.

## K. Winner's curse, wider

4518 stale rows over ghz5, ghz10, bv8 and bv10, development window only. Each
chosen set is scored against 1000 random same size sets from the live qubits of
the same card. Deviation is on the log scale and positive means worse, so a
negative chosen deviation means the chosen set looked better than its own
median of the last 8 distinct states. `rise` is the log change from the
submission card to the run-time card.

For the cz group the random sets are **connected** patches. An unconnected
random set of 5 qubits on a heavy hex lattice usually induces no coupler at
all, so a plain random set cannot serve as a comparison for coupler quality and
would have guaranteed the answer.

| group | chosen dev | random dev | percentile | below 5th | chosen rise | random rise | rise gap |
| --- | --- | --- | --- | --- | --- | --- | --- |
| readout | -0.1418 | +0.0254 | 18.4% | 34.7% | +0.1649 | +0.0118 | **+0.1531** |
| sx | -0.0178 | -0.0057 | 30.4% | 37.9% | +0.0097 | -0.0026 | +0.0123 |
| cz | -0.0593 | -0.0051 | 29.7% | 28.2% | +0.0313 | -0.0024 | **+0.0336** |
| T1/T2 | +0.0066 | +0.0047 | 27.7% | 47.2% | +0.0006 | +0.0001 | +0.0006 |

The readout curse is large and it replicates on all four circuits. cz carries a
clear one too, which is new: the curse is not readout only. sx is weak and
T1/T2 is effectively absent.

The rise gap by delay matters for the rule:

| D (h) | readout | sx | cz | T1/T2 |
| --- | --- | --- | --- | --- |
| 1 | +0.0322 | +0.0008 | +0.0008 | +0.0004 |
| 3 | +0.0913 | +0.0007 | +0.0055 | +0.0024 |
| 6 | +0.1658 | +0.0031 | +0.0140 | +0.0033 |
| 12 | +0.2153 | +0.0091 | +0.0293 | -0.0015 |
| 24 | +0.2086 | +0.0341 | +0.0650 | -0.0054 |
| 48 | +0.2141 | +0.0278 | +0.0928 | +0.0043 |

Readout saturates near +0.21 by 12 hours. cz keeps growing all the way to 48
hours. T1/T2 never goes anywhere.

By circuit, BV has the strongest readout curse: bv10 sits at the 9.9th
percentile with a rise gap of +0.2000, bv8 at the 13.3rd with +0.1886, against
ghz5 at 23.7 percent and ghz10 at 26.6 percent.

## M. Do the diagnostics hold out of time?

The same functions in `scripts/29_diagnostics.py` were called with the window
moved to the fresh window, 13 to 24 Oct. The code was not rewritten, so a
difference cannot come from writing the calculation a second way.

**Mean reversion (Part C) holds.** Readout slopes in the fresh window are
-0.3021, -0.3321 and -0.3868 on fez, kingston and marrakesh, against -0.3670,
-0.3151 and -0.4607 in development. 11 of the 12 machine-group intervals
overlap. The one that does not is kingston T1/T2, where both slopes are tiny
(-0.0132 against -0.0001), so the disagreement is between two numbers that are
both near zero.

Only readout mean-reverts. sx, cz and T1/T2 have slopes of essentially zero in
both windows.

**The readout winner's curse (Part D) holds, and is stronger out of time.** The
rise gap is +0.1139 in development against +0.1781 in the fresh window, same
sign, and the chosen sets sit at the 26.7th and 27.9th percentile. The sx and
T1/T2 rise gaps flip sign (-0.0004 to +0.0121 and -0.0037 to +0.0116) but all
four numbers are near zero, so that reads as noise about zero rather than a
real reversal.

This is consistent with the development picture. It does not prove it.

## N. Why did the hybrid lose?

Round 2 rows only. Nothing re-simulated, no row changed.

**The hybrid is not the worse rule at short delay. It is the better one.**

| D (h) | hybrid minus stale | window mean minus stale |
| --- | --- | --- |
| 1 | -0.000480 | **-0.008416 [-0.012258, -0.004930]** |
| 3 | -0.001036 | **-0.005270 [-0.010084, -0.000569]** |
| 6 | -0.002282 | -0.001018 |
| 12 | -0.004916 | +0.003026 |
| 24 | +0.002968 | **+0.008774 [0.002547, 0.014848]** |
| 48 | +0.006010 | **+0.012173 [0.004863, 0.020044]** |

The plain window mean HARMS at short delay, with intervals clearly below zero.
The hybrid's tapering of the weight towards 0 at short delay does exactly the
job it was designed for: it would have passed a no-harm test that the window
mean fails badly. At long delay the order reverses and the window mean is two
to three times larger than the hybrid.

So the hybrid lost the pooled 6 to 48 h test because its weights are too timid
at long delay, not because blending is the wrong idea.

**Where the hybrid's gain actually sits.** Of the 2824 pooled jobs, the 270
where some arm used a qubit that was dead at run time are 9.6 percent of the
jobs and carry +4.4838 of the summed difference, while the whole total is only
+0.4277. The other 2554 jobs therefore sum to about -4.06 and average -0.001588.
The hybrid has no edge except where a dead qubit is involved. The window mean is
far less dependent on that: those same 270 jobs hold 47.4 percent of its total
and it still averages +0.003107 on the clean majority.

**The fez readout episode of 15 Oct 05:44 to 15:37 UTC** touches 136 pooled
jobs. Those jobs were kept in the Round 2 analysis as the protocol required;
this is an exploratory cut, not a correction. Excluding it, the hybrid falls
from +0.000151 to -0.000617 and the window mean from +0.005346 to +0.004998.
Inside the episode the hybrid gains +0.015334 [0.004746, 0.042191].

That corrects a guess made in L-057, where the episode was described as the
worst case for a rule leaning on a trailing median. The opposite is true: the
episode was helping the hybrid. The failure lasted about ten hours, so for most
of these jobs the run-time card had already recovered, which makes the trailing
median the better picture and the newest card the misleading one.

## What K, M and N say together

This is the part worth carrying forward, and it is post hoc.

Only readout mean-reverts, with slopes of -0.30 to -0.46. Only readout and cz
carry a real winner's curse. sx, and especially T1/T2, show slopes near zero and
a rise gap of +0.0006: no reversion and no curse.

But the Stage 1 fit gave T1/T2 a weight of 0.90 at D = 48 h, the joint highest
of the four groups, and gave cz only 0.55 even though the cz curse is the one
still growing at 48 hours.

The reason is visible in how the fit was defined. It chose weights by the mean
squared error of PREDICTING the run-time value, and shrinking a noisy series
towards its own median lowers that error whether or not the series
mean-reverts. The layout DECISION only benefits when the deviation is
transient. So the fit put its heaviest weight on the group with the least to
gain and was too cautious on the group with the most.

That is a concrete and testable explanation for the Round 2 null. It was not
pre-stated, and testing it would need a new pre-registration and a new window.

## Files

`J1_change_intervals.csv`, `K1_winners_curse_wide_rows.csv`,
`K2_winners_curse_wide_summary.csv`, `K3_winners_curse_wide_by_delay.csv`,
`N1_hybrid_vs_window.csv`, `N2_dead_qubit_share.csv`,
`M_fresh/C1_mean_reversion.csv`, `M_fresh/D1_winners_curse_rows.csv`,
`M_fresh/D2_winners_curse_summary.csv`,
`M_fresh/D3_winners_curse_by_delay.csv`,
`M_fresh/M1_part_c_dev_vs_fresh.csv`, `M_fresh/M2_part_d_dev_vs_fresh.csv`.
