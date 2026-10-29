# Why H2 has three different 95 percent intervals

Read-only investigation, 29 October 2026. No analysis was re-run to produce a
new result and no file other than this one was written. The Round 2 report and
`scripts/31_analyse_round2.py` are unchanged.

## The three intervals

`outputs/round2/REPORT.md` reports H2 (hybrid minus stale, D = 6 to 48 h)
three times:

| where | n jobs | days | mean | 95 pct low | 95 pct high |
| --- | --- | --- | --- | --- | --- |
| headline H1/H2 table | 2824 | 11 | 0.00015143555252041018 | -0.008864566261782756 | 0.007509823322503146 |
| dead-qubit view 1, all rows as they are | 2824 | 11 | 0.00015143555252041018 | -0.009152662289362018 | 0.007569614076630489 |
| every-arm table, hybrid row | 2824 | 11 | 0.00015143555252041018 | -0.008738882555828496 | 0.007228414815846933 |

All three come from `outputs/round2/r2_results.csv`, rows 3, 40 and 32.

## The cause: position in one bootstrap stream

**It is not the row set and it is not the job order. It is the position each
test occupies in a single shared random number stream.**

The row set is provably identical. All three report n = 2824 jobs over 11
calendar days, and all three report the same mean to all 17 significant digits:
`0.00015143555252041018`. A mean that agrees to the last digit cannot come from
a different set of rows or a different ordering of them, because the mean is
computed from the rows themselves and not from the bootstrap.

What differs is only the resampling. `scripts/31_analyse_round2.py` creates one
generator at line 283:

    rng = np.random.default_rng(M20.SEED_BOOT)

and then threads that same `rng` object through every test in the file: H1 and
H2 at lines 322 and 324, the per-delay table, the per-machine and per-circuit
cuts, the gap split, the every-arm table at line 370, and the three dead-qubit
views at line 386. Each call to `block_boot` draws 4000 resamples of whole
calendar days and leaves the stream advanced. So the second, twentieth and
fortieth computation of the identical quantity each get a different set of day
draws, and therefore a different pair of percentiles, while the observed mean
is unaffected.

### Verified, not assumed

Starting a fresh generator at seed 20261014 and making the same two calls the
script makes first, H1 then H2, reproduces the headline interval exactly:

    call 1 (H1): mean -0.000758  [-0.003269, 0.001220]
    call 2 (H2): mean +0.000151  [-0.008864566261782749, 0.007509823322503141]

against the reported `[-0.008864566261782756, 0.007509823322503146]`. The
agreement is to 15 decimal places; the last-digit difference is float
formatting, not arithmetic.

Repeating the very same computation on the very same frame at later positions
in that one stream gives intervals that wander over the range the three
reported values sit in:

    call 3: [-0.008592, 0.007473]
    call 4: [-0.009348, 0.007429]
    call 5: [-0.008652, 0.007332]
    call 6: [-0.008597, 0.007363]
    call 7: [-0.008413, 0.007531]
    call 8: [-0.008776, 0.007217]

Over 200 such repeats the low bound ranges from -0.009348 to -0.008108
(standard deviation 0.000295) and the high bound from 0.007018 to 0.007749
(standard deviation 0.000118). **All three reported intervals fall inside that
pure Monte Carlo range.** The spread between the three reported low bounds is
0.000414, which is about 1.4 standard deviations of the Monte Carlo noise. So
the three intervals are three draws of the same interval, not three different
answers.

This is the same effect L-042 measured in Round 1, where changing the bootstrap
seed moved an interval bound by about 0.0004.

## Which one is the pre-registered H2 interval

**The headline H1/H2 table: -0.008865 to 0.007510.**

That row is the output of the `one_test("H2 hybrid minus stale, D = 6 to 48 h",
...)` call, which is the pre-registered confirmatory test named in
`protocol_round2.md`. It carries the pre-stated bound and the pass/fail
decision; in `r2_results.csv` it is the only one of the three with the `bound`
and `passes` fields filled in. It is also the second bootstrap call in the
file, so it is computed before any exploratory cut has touched the stream.

The other two are later recomputations of the same quantity for presentational
tables:

- the **every-arm table** exists to put all four arms side by side, and happens
  to recompute the hybrid row;
- **dead-qubit view 1** is the "all rows as they are" baseline of the three
  dead-row sensitivity views, and view 1 is by construction the same pool as
  H2.

Neither is a separate test. Both are exploratory presentation.

## What to quote in a paper

Quote **mean +0.000151, 95 percent interval [-0.008865, 0.007510], n = 2824
jobs over 11 calendar days**, and cite it as the pre-registered H2 result.

Three further points belong with it:

1. **Do not quote the other two intervals as if they were separate evidence.**
   They are the same test resampled again. Reporting three intervals for one
   quantity invites a reader to think three analyses were run.
2. **Round the interval to 3 significant figures at most, for example
   [-0.0089, +0.0075].** Printing more digits than the method supports is
   misleading: the Monte Carlo standard deviation on the low bound is 0.0003,
   so the fourth decimal place is not stable across seeds. The existing
   `r2_results.csv` keeps full precision, which is right for a data file and
   wrong for prose.
3. **The verdict is identical under all three.** Every version has a point
   estimate essentially at zero, a low bound near -0.009 and a high bound near
   +0.0075, so H2 fails its "low above 0" criterion whichever is used. Nothing
   about the conclusion depends on this choice, and the note is about reporting
   hygiene, not about a result in doubt.

## Is the shared stream a fault?

Not in itself. Threading one generator through a script is normal and keeps the
whole run reproducible from one seed: re-running
`scripts/31_analyse_round2.py` unchanged reproduces all three intervals
exactly. The fault is only in presentation, in that the report prints three
numerically different intervals for one quantity without saying they are the
same test. A cleaner pattern for future rounds is to compute each distinct
quantity once and reuse the stored result in every table, or to give each named
test its own seeded generator so a table's position in the file cannot change
its numbers.

Nothing here changes any Round 2 number or verdict.
