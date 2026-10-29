# The protocol-faithful headline: Comparisons A and B on all 5,648 jobs

Fix forward. Nothing was overwritten. `scripts/20_analyse_results.py` was not
edited, no existing output file was replaced, and no reported number was
changed. No IBM call, no new simulation, `data/raw` untouched.

Why: L-052 found that script 20 runs both confirmatory comparisons on
`main_set = w[~w.touches_gap]`, dropping the 360 jobs that straddle the 22 to
23 September publishing gap. PROTOCOL.md section 10 says the gap "stays in",
results are "reported with it included", and the straddling jobs are
"reported separately so its effect is visible". Amendment A1.6 reaffirms it.
So the protocol-faithful headline uses all 5,648 jobs, with the 360 also shown
on their own.

Script: `scripts/28_protocol_headline.py`. The loader, reshape and block
bootstrap are imported from script 20 with its seed (20261014) and 4,000
resamples; the power helpers are imported from `26_row_check.py`. Only the job
selection differs. The non-gap set reproduced all nine reported numbers inside
0.0005, asserted in code.

Sign convention: regret = ceiling minus strategy (positive means the strategy
is worse). Gain = F_strategy minus F_stale (positive means the strategy is
better).

## Comparison A: stale regret by delay

| D | reported (5,288) | protocol-faithful (5,648) | change | gap jobs only (360) |
|---|---|---|---|---|
| 1 h | +0.0059 [+0.0020, +0.0109] | +0.0057 [+0.0019, +0.0104] | -0.0002 | +0.0000 [+0.0000, +0.0000] |
| 3 h | +0.0171 [+0.0102, +0.0250] | +0.0164 [+0.0096, +0.0242] | -0.0007 | +0.0000 [+0.0000, +0.0000] |
| 6 h | +0.0230 [+0.0169, +0.0292] | +0.0221 [+0.0159, +0.0285] | -0.0008 | +0.0050 [+0.0000, +0.0079] |
| 12 h | +0.0259 [+0.0199, +0.0330] | +0.0251 [+0.0192, +0.0319] | -0.0008 | +0.0138 [+0.0115, +0.0166] |
| 24 h | +0.0245 [+0.0184, +0.0315] | +0.0239 [+0.0182, +0.0307] | -0.0006 | +0.0166 [+0.0114, +0.0212] |
| 48 h | +0.0367 [+0.0250, +0.0510] | +0.0367 [+0.0263, +0.0494] | +0.0001 | +0.0375 [+0.0130, +0.0593] |

Every interval is above zero in both versions, and regret still grows with
delay. The largest change is 0.0008 of fidelity, at 6 h and 12 h.

Why the headline goes slightly **down**: during a publishing gap few or no new
states appear, so a stale card is often still correct. The no-change share
among gap jobs is 87.5 percent at 1 h and 3 h, against 72.6 and 39.7 percent in
the non-gap set, and gap-job regret is exactly 0.0000 at those two delays. By
48 h the gap jobs look like the rest (+0.0375 against +0.0367). So including
them adds a block of easy jobs at short delays and dilutes the mean a little.

## Comparison B: shrinkage against stale, paired

PROTOCOL.md section 11 defines B as "at D = 6 hours and D = 24 hours, pooled
over machines and circuits", which is two numbers. Script 20 headlines a third
number that also pools the two delays. Both are shown.

| scope | reported (5,288) | protocol-faithful (5,648) | gap jobs only (360) |
|---|---|---|---|
| 6 h (protocol) | +0.00345 [-0.00042, +0.00721] | +0.00330 [-0.00037, +0.00694] | +0.00027 |
| 24 h (protocol) | -0.00003 [-0.00307, +0.00271] | -0.00004 [-0.00288, +0.00255] | -0.00017 |
| pooled 6 and 24 h (script 20 style) | +0.00176 [-0.00133, +0.00483] | +0.00165 [-0.00126, +0.00458] | -0.00001 |

Every interval includes zero in every selection. Comparison B stays a null.

## Window mean minus stale, all jobs, EXPLORATORY

-0.00543 [-0.00959, -0.00116] at 1 h, +0.00371 at 3 h, +0.00863 [+0.00306,
+0.01521] at 6 h, +0.00581 at 12 h, +0.00604 [+0.00070, +0.01348] at 24 h,
+0.01532 [+0.00821, +0.02361] at 48 h. Same shape as on the non-gap set:
negative at 1 h, positive and clear of zero from 6 h up.

## The four dead-qubit views, on all jobs

| view | jobs | 1 h | 6 h | 24 h | 48 h | B pooled |
|---|---|---|---|---|---|---|
| 1 all rows | 5648 | +0.0057 | +0.0221 | +0.0239 | +0.0367 | +0.00165 |
| 2a drop any-arm dead jobs | 4806 | +0.0015 | +0.0145 | +0.0206 | +0.0283 | +0.00163 |
| 2b drop informed-arm dead jobs | 5503 | +0.0023 | +0.0166 | +0.0208 | +0.0302 | +0.00086 |
| 3 dead rows forced to 0 | 5648 | +0.0097 | +0.0336 | +0.0299 | +0.0518 | +0.00130 |

All intervals above zero for A in all four views; all intervals include zero for
B in all four views. Same verdicts as L-051 gave on the 5,288-job set.

Share of summed regret sitting in the dead-qubit rows, now with the stale arm's
full **81** rows (it was 76): stale **20.99 percent** overall (was 20.41),
window mean 14.17 (was 15.24), shrinkage 16.89 (was 16.99). By machine the
stale share is 35.35 percent on ibm_marrakesh, 6.82 on ibm_fez, 0.00 on
ibm_kingston.

## Design effect and power, all jobs

Pooled over 6, 12, 24 and 48 h, n = 3,718 jobs:

| contrast | paired SD | naive SE | SE days-in-machine | SE (machine, submission) | DE days | DE submission | ICC |
|---|---|---|---|---|---|---|---|
| shrinkage minus stale | 0.059340 | 0.000973 | 0.001369 | 0.001228 | 1.979 | 1.592 | +0.0178 |
| window mean minus stale | 0.070478 | 0.001156 | 0.002648 | 0.002679 | 5.247 | 5.373 | +0.0829 |

Required jobs for shrinkage minus stale at DE = 1.979: effect 0.005 needs
2,188 jobs (80 percent power) or 2,929 (90 percent); effect 0.010 needs 547 or
733. At 60 jobs per machine-day over three machines that is 13 calendar days
for 80 percent and 17 for 90 percent at effect 0.005. The L-051 figures on the
5,288-job set were 2,144 / 2,870 jobs and 12 / 16 days, so the recommendation
of about 16 fresh days is unchanged.

## Other protocol choices checked (step 3)

Fifteen items compared against PROTOCOL.md read in full plus the amendments,
in `H8_protocol_conformance.csv`. **Two departures, neither fixed here.**

1. **Gap jobs, section 10. DEPARTURE.** The one above. The separate reporting
   is done; the headline exclusion is not what section 10 says.
2. **Comparison B pooling, section 11. DEPARTURE IN EMPHASIS.** The protocol
   pools over machines and circuits at each D, giving two numbers. Script 20
   headlines a third number that pools the two delays together. Both are
   printed, so nothing is hidden, but the headlined figure is not the one the
   protocol defines.

Conforming: delays (1, 3, 6, 12, 24, 48), circuits (the five named), test-days
window (every row is label TEST and earliest t_s is 2026-09-21), bootstrap unit
(whole calendar days, with section 17 risk 4 declining machine-days), dead
qubit rule and thresholds, sanity checks (all four implemented, exit 1 on
failure), no-change share per D, exploratory labelling. Conforming via
amendment: split dates (A1.6), permanent defects from training days (A1.5),
shrinkage tie-break (A2, with A2.2 and A3.1).

Three obligations are met by `scripts/24_prereg_outputs.py` rather than by the
headline script, which is worth knowing when reading script 20 alone: the
per-delay dropped-job counts (section 3 and A1.7, as P7), the cz-age and
separate readout-age axes (section 9, as P1, P1b, P2, P2b), and ESP reported
alongside fidelity (section 8, as P3).

## Does any conclusion change?

No. Comparison A stays positive and growing with delay with every interval
above zero, and Comparison B stays a null at 6 h, at 24 h and pooled. The
protocol-faithful numbers are consistent with the reported ones, differing by
at most 0.0008 of fidelity, and the direction of every verdict is the same.

## Files

`H1_comparisons_by_selection.csv`, `H2_old_vs_new.csv`,
`H3_window_mean_vs_stale_all_jobs.csv`, `H4_dead_qubit_views_all_jobs.csv`,
`H5_dead_row_regret_share_all_jobs.csv`, `H6_power_sd_se_all_jobs.csv`,
`H7_power_required_n_all_jobs.csv`, `H8_protocol_conformance.csv`,
`console_output.txt`.
