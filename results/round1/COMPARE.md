# COMPARE.md: old value, new value, difference

Old value means the saved Round 1 pack file under `report_pack/numbers/`.
New value means the matching file in this corrected pack, rebuilt on all
5,648 jobs with no gap exclusion.

## What I could not do, and why

The request asked for one line per number quoted in the report's abstract,
conclusions, Section 4.3.6, Section 5.1, Table 7 and Table 19.

**The Round 1 report itself is not in this project.** I searched every
`.md` and `.txt` file outside `team_code/` and `.venv/` for "Table 7",
"Table 19", "Section 4.3.6", "Figure 16" and for an abstract or a
conclusions section, and there is no such document and no PDF, `.docx`,
`.tex` or `.odt` anywhere in the tree. So I cannot read what those
locations say, which numbers they quote, or how the report numbers its
tables and figures. I have not guessed a mapping and I have not estimated
any old value.

What I did instead: every number in the saved Round 1 CSV files is
compared below, old against new. That is the complete set of saved Round 1
numbers, so whichever of them the report quotes, its old and new value is
in the table. Mapping each one to a report table number needs the report.

## Headline, Comparison A (stale regret against the ceiling)

Source: the regret panel of `fig_a_six_strategies_all_machines.csv`, and
`comparison_A_stale_regret_all_jobs.csv` in this pack.

| location | old value | new value | difference |
| --- | --- | --- | --- |
| Comparison A, D=1 h, n jobs | 930 | 970 | +40 |
| Comparison A, D=1 h, mean stale regret | 0.005937 | 0.005692 | -0.000245 |
| Comparison A, D=3 h, n jobs | 920 | 960 | +40 |
| Comparison A, D=3 h, mean stale regret | 0.017115 | 0.016402 | -0.000713 |
| Comparison A, D=6 h, n jobs | 909 | 954 | +45 |
| Comparison A, D=6 h, mean stale regret | 0.022962 | 0.022116 | -0.000847 |
| Comparison A, D=12 h, n jobs | 880 | 945 | +65 |
| Comparison A, D=12 h, mean stale regret | 0.025887 | 0.025056 | -0.000831 |
| Comparison A, D=24 h, n jobs | 855 | 930 | +75 |
| Comparison A, D=24 h, mean stale regret | 0.024511 | 0.023876 | -0.000636 |
| Comparison A, D=48 h, n jobs | 794 | 889 | +95 |
| Comparison A, D=48 h, mean stale regret | 0.036653 | 0.036739 | +0.000085 |

The direction of Comparison A is unchanged: stale regret rises with delay
and every interval stays clear of zero. Adding the 360 gap jobs lowers the
point estimate slightly at five of the six delays, because most gap jobs
crossed no new state and so carry zero stale regret.

## Headline, Comparison B (shrinkage minus stale), and the sign fix

The old `fig_d_shrinkage_minus_stale.csv` computed `stale - shrinkage`
while its own axis label and `label` column said "positive = shrinkage
better", so the reported direction was the wrong way round. This pack
reports `F_shrinkage minus F_stale`, which is the same correction
`scripts/20_analyse_results.py` already carries from L-049. Two things
therefore changed at once: the sign, and the row set.

| location | old value | new value | difference |
| --- | --- | --- | --- |
| Comparison B, 6 h, n jobs | 909 | 954 | +45 |
| Comparison B, 6 h, mean gain | -0.003447 | +0.003297 | +0.006744 |
| Comparison B, 6 h, lo95 | -0.007431 | -0.000166 | +0.007265 |
| Comparison B, 6 h, hi95 | +0.000265 | +0.006938 | +0.006673 |
| Comparison B, 24 h, n jobs | 855 | 930 | +75 |
| Comparison B, 24 h, mean gain | +0.000030 | -0.000041 | -0.000071 |
| Comparison B, 24 h, lo95 | -0.002680 | -0.002750 | -0.000070 |
| Comparison B, 24 h, hi95 | +0.002953 | +0.002560 | -0.000393 |
| Comparison B, pooled (labelled extra), n jobs | 1764 | 1884 | +120 |
| Comparison B, pooled (labelled extra), mean gain | -0.001762 | +0.001649 | +0.003411 |
| Comparison B, pooled (labelled extra), lo95 | -0.004821 | -0.001391 | +0.003430 |
| Comparison B, pooled (labelled extra), hi95 | +0.001293 | +0.004533 | +0.003240 |

Most of the movement in the 6 h and pooled rows is the sign fix, not the
extra jobs. **The verdict does not change.** Every interval still includes
zero at 6 h, at 24 h and pooled, so on the test days the pre-registered
fix still did not beat using the newest card. What does change is the
reading of the point estimate: the old figure made shrinkage look worse
than stale at 6 h, and with the sign the right way round the 6 h point
estimate is positive (+0.0033) with a lower bound of -0.00017, which is
consistent with no difference and must not be read as shrinkage winning.

## The four sanity checks

`scripts/20_analyse_results.py` ran its sanity checks on the full row set
before any gap exclusion, so these were already all-jobs numbers. The
recomputation reproduces them exactly.

| location | old value | new value | difference |
| --- | --- | --- | --- |
| sanity 1, no-new-state jobs | 1305 | 1305 | 0 |
| sanity 1, largest absolute regret | 0.0 | 0.0 | 0 |
| sanity 2, ceiling minus stale at 1 h | +0.0057 | +0.0057 | 0 |
| sanity 2, ceiling minus stale at 48 h | +0.0367 | +0.0367 | 0 |
| sanity 3, random mean fidelity | 0.7334 | 0.7334 | 0 |
| sanity 3, stale mean fidelity | 0.9027 | 0.9027 | 0 |
| sanity 4, fixture checksum | unchanged | unchanged | 0 |

## The 360 gap jobs

| location | old value | new value | difference |
| --- | --- | --- | --- |
| jobs in every headline | 5288 | 5648 | +360 |
| jobs dropped from the headline | 360 | 0 | -360 |
| jobs reported separately in P5 | 360 | 360 | 0 |

The gap jobs are now inside every file in this pack **and** still reported
on their own in `P5_gap_jobs.csv`, which is what PROTOCOL.md section 10
asks for.

## A note on the bootstrap intervals

Each file keeps its own original bootstrap seed (20261017 for the figure
CSVs, 20261016 for the prereg CSVs, 20261014 for Comparison A and the
sanity checks), so a difference below is the row set or the sign fix, not
a different seed. Interval bounds still move by a few parts in ten
thousand of their own accord, because the number of resampled values
changes when 360 jobs join. L-042 measured that seed-to-seed wobble at
about 0.0004 on an interval bound, so a difference of that size on an
`lo95` or `hi95` should not be read as a real change.

## Dead-qubit tables: no change at all

`scripts/25_dead_qubit_rows.py` never applied a gap exclusion, so D1 to D6
were already computed on all 5,648 jobs. Regenerated here, the files come
out byte identical, which is the check rather than an assumption.

| location | old value | new value | difference |
| --- | --- | --- | --- |
| D1_dead_qubit_rows_by_arm.csv, every cell | unchanged | unchanged | 0 (files byte identical: True) |
| D2_dead_qubit_rows_by_delay.csv, every cell | unchanged | unchanged | 0 (files byte identical: True) |
| D3_dead_qubit_rows_by_arm_and_delay.csv, every cell | unchanged | unchanged | 0 (files byte identical: True) |
| D4_dead_qubit_rows_informed_arms.csv, every cell | unchanged | unchanged | 0 (files byte identical: True) |
| D5_dead_qubit_rows_by_machine_and_arm.csv, every cell | unchanged | unchanged | 0 (files byte identical: True) |
| D6_dead_qubit_rows_by_new_states.csv, every cell | unchanged | unchanged | 0 (files byte identical: True) |

## Every saved Round 1 number, old against new

2698 lines, one per number, in file order. `n/a (text)` means the cell
is not a number. "new row" means the old file had no such row.

| location | old value | new value | difference |
| --- | --- | --- | --- |
| fig_a all machines, mean fidelity 1 random, n | 930 | 970 | +40.000000 |
| fig_a all machines, mean fidelity 1 random, mean | 0.735555 | 0.736305 | +0.000750 |
| fig_a all machines, mean fidelity 1 random, lo95 | 0.714781 | 0.716165 | +0.001384 |
| fig_a all machines, mean fidelity 1 random, hi95 | 0.750289 | 0.750391 | +0.000102 |
| fig_a all machines, mean fidelity 1 stale, n | 930 | 970 | +40.000000 |
| fig_a all machines, mean fidelity 1 stale, mean | 0.911774 | 0.912432 | +0.000658 |
| fig_a all machines, mean fidelity 1 stale, lo95 | 0.890257 | 0.891568 | +0.001311 |
| fig_a all machines, mean fidelity 1 stale, hi95 | 0.925026 | 0.925133 | +0.000107 |
| fig_a all machines, mean fidelity 1 window_mean, n | 930 | 970 | +40.000000 |
| fig_a all machines, mean fidelity 1 window_mean, mean | 0.907005 | 0.907006 | +0.000000 |
| fig_a all machines, mean fidelity 1 window_mean, lo95 | 0.886005 | 0.886722 | +0.000717 |
| fig_a all machines, mean fidelity 1 window_mean, hi95 | 0.919672 | 0.919073 | -0.000599 |
| fig_a all machines, mean fidelity 1 std_adjusted, n | 930 | 970 | +40.000000 |
| fig_a all machines, mean fidelity 1 std_adjusted, mean | 0.907616 | 0.907606 | -0.000010 |
| fig_a all machines, mean fidelity 1 std_adjusted, lo95 | 0.887102 | 0.887881 | +0.000779 |
| fig_a all machines, mean fidelity 1 std_adjusted, hi95 | 0.919414 | 0.918720 | -0.000695 |
| fig_a all machines, mean fidelity 1 shrinkage, n | 930 | 970 | +40.000000 |
| fig_a all machines, mean fidelity 1 shrinkage, mean | 0.912005 | 0.912581 | +0.000576 |
| fig_a all machines, mean fidelity 1 shrinkage, lo95 | 0.891652 | 0.892996 | +0.001343 |
| fig_a all machines, mean fidelity 1 shrinkage, hi95 | 0.924266 | 0.924343 | +0.000077 |
| fig_a all machines, mean fidelity 1 ceiling, n | 930 | 970 | +40.000000 |
| fig_a all machines, mean fidelity 1 ceiling, mean | 0.917711 | 0.918124 | +0.000413 |
| fig_a all machines, mean fidelity 1 ceiling, lo95 | 0.897191 | 0.898294 | +0.001104 |
| fig_a all machines, mean fidelity 1 ceiling, hi95 | 0.928958 | 0.928888 | -0.000070 |
| fig_a all machines, mean fidelity 3 random, n | 920 | 960 | +40.000000 |
| fig_a all machines, mean fidelity 3 random, mean | 0.731715 | 0.732843 | +0.001128 |
| fig_a all machines, mean fidelity 3 random, lo95 | 0.721106 | 0.722771 | +0.001665 |
| fig_a all machines, mean fidelity 3 random, hi95 | 0.741868 | 0.742438 | +0.000570 |
| fig_a all machines, mean fidelity 3 stale, n | 920 | 960 | +40.000000 |
| fig_a all machines, mean fidelity 3 stale, mean | 0.906117 | 0.907031 | +0.000914 |
| fig_a all machines, mean fidelity 3 stale, lo95 | 0.893762 | 0.894849 | +0.001087 |
| fig_a all machines, mean fidelity 3 stale, hi95 | 0.916009 | 0.916795 | +0.000786 |
| fig_a all machines, mean fidelity 3 window_mean, n | 920 | 960 | +40.000000 |
| fig_a all machines, mean fidelity 3 window_mean, mean | 0.910914 | 0.910743 | -0.000171 |
| fig_a all machines, mean fidelity 3 window_mean, lo95 | 0.899531 | 0.899814 | +0.000283 |
| fig_a all machines, mean fidelity 3 window_mean, hi95 | 0.918831 | 0.918162 | -0.000670 |
| fig_a all machines, mean fidelity 3 std_adjusted, n | 920 | 960 | +40.000000 |
| fig_a all machines, mean fidelity 3 std_adjusted, mean | 0.909022 | 0.908949 | -0.000073 |
| fig_a all machines, mean fidelity 3 std_adjusted, lo95 | 0.897849 | 0.898249 | +0.000401 |
| fig_a all machines, mean fidelity 3 std_adjusted, hi95 | 0.916473 | 0.916071 | -0.000402 |
| fig_a all machines, mean fidelity 3 shrinkage, n | 920 | 960 | +40.000000 |
| fig_a all machines, mean fidelity 3 shrinkage, mean | 0.909322 | 0.910028 | +0.000706 |
| fig_a all machines, mean fidelity 3 shrinkage, lo95 | 0.897891 | 0.898813 | +0.000922 |
| fig_a all machines, mean fidelity 3 shrinkage, hi95 | 0.918416 | 0.918849 | +0.000433 |
| fig_a all machines, mean fidelity 3 ceiling, n | 920 | 960 | +40.000000 |
| fig_a all machines, mean fidelity 3 ceiling, mean | 0.923232 | 0.923433 | +0.000201 |
| fig_a all machines, mean fidelity 3 ceiling, lo95 | 0.912431 | 0.913052 | +0.000621 |
| fig_a all machines, mean fidelity 3 ceiling, hi95 | 0.929613 | 0.929534 | -0.000079 |
| fig_a all machines, mean fidelity 6 random, n | 909 | 954 | +45.000000 |
| fig_a all machines, mean fidelity 6 random, mean | 0.737799 | 0.737433 | -0.000366 |
| fig_a all machines, mean fidelity 6 random, lo95 | 0.732385 | 0.732277 | -0.000108 |
| fig_a all machines, mean fidelity 6 random, hi95 | 0.743399 | 0.742817 | -0.000582 |
| fig_a all machines, mean fidelity 6 stale, n | 909 | 954 | +45.000000 |
| fig_a all machines, mean fidelity 6 stale, mean | 0.905697 | 0.906529 | +0.000831 |
| fig_a all machines, mean fidelity 6 stale, lo95 | 0.899170 | 0.899917 | +0.000746 |
| fig_a all machines, mean fidelity 6 stale, hi95 | 0.912181 | 0.912977 | +0.000796 |
| fig_a all machines, mean fidelity 6 window_mean, n | 909 | 954 | +45.000000 |
| fig_a all machines, mean fidelity 6 window_mean, mean | 0.915482 | 0.915162 | -0.000320 |
| fig_a all machines, mean fidelity 6 window_mean, lo95 | 0.912074 | 0.911949 | -0.000125 |
| fig_a all machines, mean fidelity 6 window_mean, hi95 | 0.918749 | 0.918199 | -0.000550 |
| fig_a all machines, mean fidelity 6 std_adjusted, n | 909 | 954 | +45.000000 |
| fig_a all machines, mean fidelity 6 std_adjusted, mean | 0.910691 | 0.910579 | -0.000112 |
| fig_a all machines, mean fidelity 6 std_adjusted, lo95 | 0.905271 | 0.905358 | +0.000088 |
| fig_a all machines, mean fidelity 6 std_adjusted, hi95 | 0.915694 | 0.915246 | -0.000448 |
| fig_a all machines, mean fidelity 6 shrinkage, n | 909 | 954 | +45.000000 |
| fig_a all machines, mean fidelity 6 shrinkage, mean | 0.909144 | 0.909826 | +0.000681 |
| fig_a all machines, mean fidelity 6 shrinkage, lo95 | 0.904426 | 0.904956 | +0.000529 |
| fig_a all machines, mean fidelity 6 shrinkage, hi95 | 0.913835 | 0.914534 | +0.000699 |
| fig_a all machines, mean fidelity 6 ceiling, n | 909 | 954 | +45.000000 |
| fig_a all machines, mean fidelity 6 ceiling, mean | 0.928660 | 0.928644 | -0.000015 |
| fig_a all machines, mean fidelity 6 ceiling, lo95 | 0.926764 | 0.926864 | +0.000100 |
| fig_a all machines, mean fidelity 6 ceiling, hi95 | 0.930323 | 0.930208 | -0.000115 |
| fig_a all machines, mean fidelity 12 random, n | 880 | 945 | +65.000000 |
| fig_a all machines, mean fidelity 12 random, mean | 0.731965 | 0.732024 | +0.000059 |
| fig_a all machines, mean fidelity 12 random, lo95 | 0.720283 | 0.720820 | +0.000536 |
| fig_a all machines, mean fidelity 12 random, hi95 | 0.742211 | 0.742005 | -0.000206 |
| fig_a all machines, mean fidelity 12 stale, n | 880 | 945 | +65.000000 |
| fig_a all machines, mean fidelity 12 stale, mean | 0.897501 | 0.898809 | +0.001308 |
| fig_a all machines, mean fidelity 12 stale, lo95 | 0.885244 | 0.887212 | +0.001968 |
| fig_a all machines, mean fidelity 12 stale, hi95 | 0.907363 | 0.908160 | +0.000796 |
| fig_a all machines, mean fidelity 12 window_mean, n | 880 | 945 | +65.000000 |
| fig_a all machines, mean fidelity 12 window_mean, mean | 0.903919 | 0.904622 | +0.000704 |
| fig_a all machines, mean fidelity 12 window_mean, lo95 | 0.890981 | 0.892466 | +0.001485 |
| fig_a all machines, mean fidelity 12 window_mean, hi95 | 0.914539 | 0.914490 | -0.000048 |
| fig_a all machines, mean fidelity 12 std_adjusted, n | 880 | 945 | +65.000000 |
| fig_a all machines, mean fidelity 12 std_adjusted, mean | 0.902326 | 0.903062 | +0.000735 |
| fig_a all machines, mean fidelity 12 std_adjusted, lo95 | 0.890011 | 0.891382 | +0.001371 |
| fig_a all machines, mean fidelity 12 std_adjusted, hi95 | 0.911757 | 0.911812 | +0.000055 |
| fig_a all machines, mean fidelity 12 shrinkage, n | 880 | 945 | +65.000000 |
| fig_a all machines, mean fidelity 12 shrinkage, mean | 0.900215 | 0.901407 | +0.001192 |
| fig_a all machines, mean fidelity 12 shrinkage, lo95 | 0.887629 | 0.889644 | +0.002015 |
| fig_a all machines, mean fidelity 12 shrinkage, hi95 | 0.910115 | 0.910593 | +0.000477 |
| fig_a all machines, mean fidelity 12 ceiling, n | 880 | 945 | +65.000000 |
| fig_a all machines, mean fidelity 12 ceiling, mean | 0.923388 | 0.923866 | +0.000478 |
| fig_a all machines, mean fidelity 12 ceiling, lo95 | 0.912087 | 0.913373 | +0.001286 |
| fig_a all machines, mean fidelity 12 ceiling, hi95 | 0.929764 | 0.929869 | +0.000105 |
| fig_a all machines, mean fidelity 24 random, n | 855 | 930 | +75.000000 |
| fig_a all machines, mean fidelity 24 random, mean | 0.731442 | 0.731875 | +0.000433 |
| fig_a all machines, mean fidelity 24 random, lo95 | 0.722819 | 0.723766 | +0.000947 |
| fig_a all machines, mean fidelity 24 random, hi95 | 0.739619 | 0.739559 | -0.000060 |
| fig_a all machines, mean fidelity 24 stale, n | 855 | 930 | +75.000000 |
| fig_a all machines, mean fidelity 24 stale, mean | 0.903351 | 0.904078 | +0.000728 |
| fig_a all machines, mean fidelity 24 stale, lo95 | 0.895693 | 0.896832 | +0.001139 |
| fig_a all machines, mean fidelity 24 stale, hi95 | 0.909889 | 0.910092 | +0.000203 |
| fig_a all machines, mean fidelity 24 window_mean, n | 855 | 930 | +75.000000 |
| fig_a all machines, mean fidelity 24 window_mean, mean | 0.909893 | 0.910115 | +0.000222 |
| fig_a all machines, mean fidelity 24 window_mean, lo95 | 0.904325 | 0.904807 | +0.000482 |
| fig_a all machines, mean fidelity 24 window_mean, hi95 | 0.915343 | 0.915048 | -0.000296 |
| fig_a all machines, mean fidelity 24 std_adjusted, n | 855 | 930 | +75.000000 |
| fig_a all machines, mean fidelity 24 std_adjusted, mean | 0.905408 | 0.905976 | +0.000567 |
| fig_a all machines, mean fidelity 24 std_adjusted, lo95 | 0.898477 | 0.899439 | +0.000962 |
| fig_a all machines, mean fidelity 24 std_adjusted, hi95 | 0.911180 | 0.911334 | +0.000154 |
| fig_a all machines, mean fidelity 24 shrinkage, n | 855 | 930 | +75.000000 |
| fig_a all machines, mean fidelity 24 shrinkage, mean | 0.903321 | 0.904037 | +0.000716 |
| fig_a all machines, mean fidelity 24 shrinkage, lo95 | 0.896615 | 0.897596 | +0.000981 |
| fig_a all machines, mean fidelity 24 shrinkage, hi95 | 0.909972 | 0.910105 | +0.000133 |
| fig_a all machines, mean fidelity 24 ceiling, n | 855 | 930 | +75.000000 |
| fig_a all machines, mean fidelity 24 ceiling, mean | 0.927862 | 0.927954 | +0.000092 |
| fig_a all machines, mean fidelity 24 ceiling, lo95 | 0.925653 | 0.925872 | +0.000219 |
| fig_a all machines, mean fidelity 24 ceiling, hi95 | 0.929760 | 0.929713 | -0.000047 |
| fig_a all machines, mean fidelity 48 random, n | 794 | 889 | +95.000000 |
| fig_a all machines, mean fidelity 48 random, mean | 0.728635 | 0.729393 | +0.000758 |
| fig_a all machines, mean fidelity 48 random, lo95 | 0.714821 | 0.717636 | +0.002815 |
| fig_a all machines, mean fidelity 48 random, hi95 | 0.739029 | 0.739131 | +0.000102 |
| fig_a all machines, mean fidelity 48 stale, n | 794 | 889 | +95.000000 |
| fig_a all machines, mean fidelity 48 stale, mean | 0.885147 | 0.886103 | +0.000957 |
| fig_a all machines, mean fidelity 48 stale, lo95 | 0.865008 | 0.867994 | +0.002986 |
| fig_a all machines, mean fidelity 48 stale, hi95 | 0.901767 | 0.900746 | -0.001021 |
| fig_a all machines, mean fidelity 48 window_mean, n | 794 | 889 | +95.000000 |
| fig_a all machines, mean fidelity 48 window_mean, mean | 0.899646 | 0.901420 | +0.001774 |
| fig_a all machines, mean fidelity 48 window_mean, lo95 | 0.884882 | 0.888563 | +0.003681 |
| fig_a all machines, mean fidelity 48 window_mean, hi95 | 0.910850 | 0.911685 | +0.000835 |
| fig_a all machines, mean fidelity 48 std_adjusted, n | 794 | 889 | +95.000000 |
| fig_a all machines, mean fidelity 48 std_adjusted, mean | 0.890824 | 0.893496 | +0.002672 |
| fig_a all machines, mean fidelity 48 std_adjusted, lo95 | 0.867988 | 0.874140 | +0.006152 |
| fig_a all machines, mean fidelity 48 std_adjusted, hi95 | 0.907505 | 0.908464 | +0.000959 |
| fig_a all machines, mean fidelity 48 shrinkage, n | 794 | 889 | +95.000000 |
| fig_a all machines, mean fidelity 48 shrinkage, mean | 0.888859 | 0.890577 | +0.001717 |
| fig_a all machines, mean fidelity 48 shrinkage, lo95 | 0.869583 | 0.873658 | +0.004075 |
| fig_a all machines, mean fidelity 48 shrinkage, hi95 | 0.904029 | 0.903847 | -0.000182 |
| fig_a all machines, mean fidelity 48 ceiling, n | 794 | 889 | +95.000000 |
| fig_a all machines, mean fidelity 48 ceiling, mean | 0.921800 | 0.922842 | +0.001042 |
| fig_a all machines, mean fidelity 48 ceiling, lo95 | 0.909038 | 0.911783 | +0.002745 |
| fig_a all machines, mean fidelity 48 ceiling, hi95 | 0.929098 | 0.929349 | +0.000251 |
| fig_a all machines, regret vs ceiling 1 regret_random, n | 930 | 970 | +40.000000 |
| fig_a all machines, regret vs ceiling 1 regret_random, mean | 0.182156 | 0.181819 | -0.000337 |
| fig_a all machines, regret vs ceiling 1 regret_random, lo95 | 0.174135 | 0.174177 | +0.000042 |
| fig_a all machines, regret vs ceiling 1 regret_random, hi95 | 0.190349 | 0.189412 | -0.000937 |
| fig_a all machines, regret vs ceiling 1 regret_stale, n | 930 | 970 | +40.000000 |
| fig_a all machines, regret vs ceiling 1 regret_stale, mean | 0.005937 | 0.005692 | -0.000245 |
| fig_a all machines, regret vs ceiling 1 regret_stale, lo95 | 0.002115 | 0.001927 | -0.000188 |
| fig_a all machines, regret vs ceiling 1 regret_stale, hi95 | 0.010806 | 0.010391 | -0.000414 |
| fig_a all machines, regret vs ceiling 1 regret_window_mean, n | 930 | 970 | +40.000000 |
| fig_a all machines, regret vs ceiling 1 regret_window_mean, mean | 0.010706 | 0.011119 | +0.000413 |
| fig_a all machines, regret vs ceiling 1 regret_window_mean, lo95 | 0.008067 | 0.008457 | +0.000390 |
| fig_a all machines, regret vs ceiling 1 regret_window_mean, hi95 | 0.013963 | 0.014251 | +0.000287 |
| fig_a all machines, regret vs ceiling 1 regret_std_adjusted, n | 930 | 970 | +40.000000 |
| fig_a all machines, regret vs ceiling 1 regret_std_adjusted, mean | 0.010095 | 0.010518 | +0.000423 |
| fig_a all machines, regret vs ceiling 1 regret_std_adjusted, lo95 | 0.008310 | 0.008746 | +0.000436 |
| fig_a all machines, regret vs ceiling 1 regret_std_adjusted, hi95 | 0.012022 | 0.012410 | +0.000388 |
| fig_a all machines, regret vs ceiling 1 regret_shrinkage, n | 930 | 970 | +40.000000 |
| fig_a all machines, regret vs ceiling 1 regret_shrinkage, mean | 0.005706 | 0.005543 | -0.000163 |
| fig_a all machines, regret vs ceiling 1 regret_shrinkage, lo95 | 0.003508 | 0.003452 | -0.000056 |
| fig_a all machines, regret vs ceiling 1 regret_shrinkage, hi95 | 0.008305 | 0.008113 | -0.000192 |
| fig_a all machines, regret vs ceiling 3 regret_random, n | 920 | 960 | +40.000000 |
| fig_a all machines, regret vs ceiling 3 regret_random, mean | 0.191517 | 0.190590 | -0.000927 |
| fig_a all machines, regret vs ceiling 3 regret_random, lo95 | 0.183690 | 0.183217 | -0.000473 |
| fig_a all machines, regret vs ceiling 3 regret_random, hi95 | 0.199244 | 0.197513 | -0.001731 |
| fig_a all machines, regret vs ceiling 3 regret_stale, n | 920 | 960 | +40.000000 |
| fig_a all machines, regret vs ceiling 3 regret_stale, mean | 0.017115 | 0.016402 | -0.000713 |
| fig_a all machines, regret vs ceiling 3 regret_stale, lo95 | 0.010043 | 0.009536 | -0.000506 |
| fig_a all machines, regret vs ceiling 3 regret_stale, hi95 | 0.025258 | 0.024423 | -0.000834 |
| fig_a all machines, regret vs ceiling 3 regret_window_mean, n | 920 | 960 | +40.000000 |
| fig_a all machines, regret vs ceiling 3 regret_window_mean, mean | 0.012318 | 0.012690 | +0.000372 |
| fig_a all machines, regret vs ceiling 3 regret_window_mean, lo95 | 0.009460 | 0.009945 | +0.000485 |
| fig_a all machines, regret vs ceiling 3 regret_window_mean, hi95 | 0.015532 | 0.015824 | +0.000291 |
| fig_a all machines, regret vs ceiling 3 regret_std_adjusted, n | 920 | 960 | +40.000000 |
| fig_a all machines, regret vs ceiling 3 regret_std_adjusted, mean | 0.014210 | 0.014484 | +0.000274 |
| fig_a all machines, regret vs ceiling 3 regret_std_adjusted, lo95 | 0.011765 | 0.012231 | +0.000466 |
| fig_a all machines, regret vs ceiling 3 regret_std_adjusted, hi95 | 0.016699 | 0.016798 | +0.000099 |
| fig_a all machines, regret vs ceiling 3 regret_shrinkage, n | 920 | 960 | +40.000000 |
| fig_a all machines, regret vs ceiling 3 regret_shrinkage, mean | 0.013910 | 0.013405 | -0.000505 |
| fig_a all machines, regret vs ceiling 3 regret_shrinkage, lo95 | 0.008590 | 0.008348 | -0.000242 |
| fig_a all machines, regret vs ceiling 3 regret_shrinkage, hi95 | 0.019800 | 0.019243 | -0.000557 |
| fig_a all machines, regret vs ceiling 6 regret_random, n | 909 | 954 | +45.000000 |
| fig_a all machines, regret vs ceiling 6 regret_random, mean | 0.190860 | 0.191211 | +0.000351 |
| fig_a all machines, regret vs ceiling 6 regret_random, lo95 | 0.185047 | 0.185479 | +0.000432 |
| fig_a all machines, regret vs ceiling 6 regret_random, hi95 | 0.196537 | 0.196889 | +0.000352 |
| fig_a all machines, regret vs ceiling 6 regret_stale, n | 909 | 954 | +45.000000 |
| fig_a all machines, regret vs ceiling 6 regret_stale, mean | 0.022962 | 0.022116 | -0.000847 |
| fig_a all machines, regret vs ceiling 6 regret_stale, lo95 | 0.016932 | 0.016069 | -0.000863 |
| fig_a all machines, regret vs ceiling 6 regret_stale, hi95 | 0.029323 | 0.028791 | -0.000532 |
| fig_a all machines, regret vs ceiling 6 regret_window_mean, n | 909 | 954 | +45.000000 |
| fig_a all machines, regret vs ceiling 6 regret_window_mean, mean | 0.013177 | 0.013482 | +0.000305 |
| fig_a all machines, regret vs ceiling 6 regret_window_mean, lo95 | 0.010848 | 0.011206 | +0.000359 |
| fig_a all machines, regret vs ceiling 6 regret_window_mean, hi95 | 0.015419 | 0.015603 | +0.000183 |
| fig_a all machines, regret vs ceiling 6 regret_std_adjusted, n | 909 | 954 | +45.000000 |
| fig_a all machines, regret vs ceiling 6 regret_std_adjusted, mean | 0.017969 | 0.018065 | +0.000096 |
| fig_a all machines, regret vs ceiling 6 regret_std_adjusted, lo95 | 0.013661 | 0.014070 | +0.000410 |
| fig_a all machines, regret vs ceiling 6 regret_std_adjusted, hi95 | 0.022364 | 0.022262 | -0.000102 |
| fig_a all machines, regret vs ceiling 6 regret_shrinkage, n | 909 | 954 | +45.000000 |
| fig_a all machines, regret vs ceiling 6 regret_shrinkage, mean | 0.019515 | 0.018819 | -0.000697 |
| fig_a all machines, regret vs ceiling 6 regret_shrinkage, lo95 | 0.015797 | 0.014937 | -0.000860 |
| fig_a all machines, regret vs ceiling 6 regret_shrinkage, hi95 | 0.023145 | 0.022752 | -0.000393 |
| fig_a all machines, regret vs ceiling 12 regret_random, n | 880 | 945 | +65.000000 |
| fig_a all machines, regret vs ceiling 12 regret_random, mean | 0.191423 | 0.191842 | +0.000419 |
| fig_a all machines, regret vs ceiling 12 regret_random, lo95 | 0.183230 | 0.184252 | +0.001022 |
| fig_a all machines, regret vs ceiling 12 regret_random, hi95 | 0.198532 | 0.198757 | +0.000225 |
| fig_a all machines, regret vs ceiling 12 regret_stale, n | 880 | 945 | +65.000000 |
| fig_a all machines, regret vs ceiling 12 regret_stale, mean | 0.025887 | 0.025056 | -0.000831 |
| fig_a all machines, regret vs ceiling 12 regret_stale, lo95 | 0.019836 | 0.019047 | -0.000789 |
| fig_a all machines, regret vs ceiling 12 regret_stale, hi95 | 0.032681 | 0.031848 | -0.000833 |
| fig_a all machines, regret vs ceiling 12 regret_window_mean, n | 880 | 945 | +65.000000 |
| fig_a all machines, regret vs ceiling 12 regret_window_mean, mean | 0.019469 | 0.019243 | -0.000226 |
| fig_a all machines, regret vs ceiling 12 regret_window_mean, lo95 | 0.013534 | 0.013758 | +0.000224 |
| fig_a all machines, regret vs ceiling 12 regret_window_mean, hi95 | 0.027407 | 0.027085 | -0.000322 |
| fig_a all machines, regret vs ceiling 12 regret_std_adjusted, n | 880 | 945 | +65.000000 |
| fig_a all machines, regret vs ceiling 12 regret_std_adjusted, mean | 0.021062 | 0.020804 | -0.000258 |
| fig_a all machines, regret vs ceiling 12 regret_std_adjusted, lo95 | 0.016265 | 0.016280 | +0.000016 |
| fig_a all machines, regret vs ceiling 12 regret_std_adjusted, hi95 | 0.026870 | 0.026185 | -0.000685 |
| fig_a all machines, regret vs ceiling 12 regret_shrinkage, n | 880 | 945 | +65.000000 |
| fig_a all machines, regret vs ceiling 12 regret_shrinkage, mean | 0.023173 | 0.022459 | -0.000714 |
| fig_a all machines, regret vs ceiling 12 regret_shrinkage, lo95 | 0.017820 | 0.017369 | -0.000451 |
| fig_a all machines, regret vs ceiling 12 regret_shrinkage, hi95 | 0.029340 | 0.028403 | -0.000937 |
| fig_a all machines, regret vs ceiling 24 regret_random, n | 855 | 930 | +75.000000 |
| fig_a all machines, regret vs ceiling 24 regret_random, mean | 0.196420 | 0.196079 | -0.000341 |
| fig_a all machines, regret vs ceiling 24 regret_random, lo95 | 0.187777 | 0.187859 | +0.000082 |
| fig_a all machines, regret vs ceiling 24 regret_random, hi95 | 0.205187 | 0.204061 | -0.001126 |
| fig_a all machines, regret vs ceiling 24 regret_stale, n | 855 | 930 | +75.000000 |
| fig_a all machines, regret vs ceiling 24 regret_stale, mean | 0.024511 | 0.023876 | -0.000636 |
| fig_a all machines, regret vs ceiling 24 regret_stale, lo95 | 0.018516 | 0.018187 | -0.000330 |
| fig_a all machines, regret vs ceiling 24 regret_stale, hi95 | 0.031591 | 0.030482 | -0.001108 |
| fig_a all machines, regret vs ceiling 24 regret_window_mean, n | 855 | 930 | +75.000000 |
| fig_a all machines, regret vs ceiling 24 regret_window_mean, mean | 0.017969 | 0.017839 | -0.000130 |
| fig_a all machines, regret vs ceiling 24 regret_window_mean, lo95 | 0.013653 | 0.013894 | +0.000241 |
| fig_a all machines, regret vs ceiling 24 regret_window_mean, hi95 | 0.022454 | 0.022081 | -0.000373 |
| fig_a all machines, regret vs ceiling 24 regret_std_adjusted, n | 855 | 930 | +75.000000 |
| fig_a all machines, regret vs ceiling 24 regret_std_adjusted, mean | 0.022454 | 0.021979 | -0.000475 |
| fig_a all machines, regret vs ceiling 24 regret_std_adjusted, lo95 | 0.017559 | 0.017484 | -0.000075 |
| fig_a all machines, regret vs ceiling 24 regret_std_adjusted, hi95 | 0.027890 | 0.027100 | -0.000790 |
| fig_a all machines, regret vs ceiling 24 regret_shrinkage, n | 855 | 930 | +75.000000 |
| fig_a all machines, regret vs ceiling 24 regret_shrinkage, mean | 0.024541 | 0.023917 | -0.000624 |
| fig_a all machines, regret vs ceiling 24 regret_shrinkage, lo95 | 0.018561 | 0.018517 | -0.000044 |
| fig_a all machines, regret vs ceiling 24 regret_shrinkage, hi95 | 0.030957 | 0.030032 | -0.000925 |
| fig_a all machines, regret vs ceiling 48 regret_random, n | 794 | 889 | +95.000000 |
| fig_a all machines, regret vs ceiling 48 regret_random, mean | 0.193165 | 0.193449 | +0.000284 |
| fig_a all machines, regret vs ceiling 48 regret_random, lo95 | 0.186273 | 0.187184 | +0.000911 |
| fig_a all machines, regret vs ceiling 48 regret_random, hi95 | 0.199852 | 0.199439 | -0.000413 |
| fig_a all machines, regret vs ceiling 48 regret_stale, n | 794 | 889 | +95.000000 |
| fig_a all machines, regret vs ceiling 48 regret_stale, mean | 0.036653 | 0.036739 | +0.000085 |
| fig_a all machines, regret vs ceiling 48 regret_stale, lo95 | 0.025205 | 0.025901 | +0.000696 |
| fig_a all machines, regret vs ceiling 48 regret_stale, hi95 | 0.050781 | 0.048911 | -0.001871 |
| fig_a all machines, regret vs ceiling 48 regret_window_mean, n | 794 | 889 | +95.000000 |
| fig_a all machines, regret vs ceiling 48 regret_window_mean, mean | 0.022154 | 0.021422 | -0.000732 |
| fig_a all machines, regret vs ceiling 48 regret_window_mean, lo95 | 0.015774 | 0.015793 | +0.000019 |
| fig_a all machines, regret vs ceiling 48 regret_window_mean, hi95 | 0.031512 | 0.029540 | -0.001972 |
| fig_a all machines, regret vs ceiling 48 regret_std_adjusted, n | 794 | 889 | +95.000000 |
| fig_a all machines, regret vs ceiling 48 regret_std_adjusted, mean | 0.030976 | 0.029346 | -0.001629 |
| fig_a all machines, regret vs ceiling 48 regret_std_adjusted, lo95 | 0.020089 | 0.019884 | -0.000205 |
| fig_a all machines, regret vs ceiling 48 regret_std_adjusted, hi95 | 0.047406 | 0.043864 | -0.003542 |
| fig_a all machines, regret vs ceiling 48 regret_shrinkage, n | 794 | 889 | +95.000000 |
| fig_a all machines, regret vs ceiling 48 regret_shrinkage, mean | 0.032940 | 0.032265 | -0.000675 |
| fig_a all machines, regret vs ceiling 48 regret_shrinkage, lo95 | 0.023301 | 0.023625 | +0.000324 |
| fig_a all machines, regret vs ceiling 48 regret_shrinkage, hi95 | 0.044899 | 0.042797 | -0.002102 |
| fig_a ibm_fez, mean fidelity 1 random, n | 315 | 325 | +10.000000 |
| fig_a ibm_fez, mean fidelity 1 random, mean | 0.706561 | 0.707751 | +0.001190 |
| fig_a ibm_fez, mean fidelity 1 random, lo95 | 0.694376 | 0.695361 | +0.000985 |
| fig_a ibm_fez, mean fidelity 1 random, hi95 | 0.717982 | 0.719687 | +0.001705 |
| fig_a ibm_fez, mean fidelity 1 stale, n | 315 | 325 | +10.000000 |
| fig_a ibm_fez, mean fidelity 1 stale, mean | 0.927808 | 0.927722 | -0.000086 |
| fig_a ibm_fez, mean fidelity 1 stale, lo95 | 0.925652 | 0.925632 | -0.000020 |
| fig_a ibm_fez, mean fidelity 1 stale, hi95 | 0.930096 | 0.929901 | -0.000195 |
| fig_a ibm_fez, mean fidelity 1 window_mean, n | 315 | 325 | +10.000000 |
| fig_a ibm_fez, mean fidelity 1 window_mean, mean | 0.924528 | 0.924326 | -0.000203 |
| fig_a ibm_fez, mean fidelity 1 window_mean, lo95 | 0.921090 | 0.921021 | -0.000068 |
| fig_a ibm_fez, mean fidelity 1 window_mean, hi95 | 0.927536 | 0.927314 | -0.000222 |
| fig_a ibm_fez, mean fidelity 1 std_adjusted, n | 315 | 325 | +10.000000 |
| fig_a ibm_fez, mean fidelity 1 std_adjusted, mean | 0.922676 | 0.922608 | -0.000068 |
| fig_a ibm_fez, mean fidelity 1 std_adjusted, lo95 | 0.918335 | 0.918274 | -0.000061 |
| fig_a ibm_fez, mean fidelity 1 std_adjusted, hi95 | 0.926354 | 0.926098 | -0.000256 |
| fig_a ibm_fez, mean fidelity 1 shrinkage, n | 315 | 325 | +10.000000 |
| fig_a ibm_fez, mean fidelity 1 shrinkage, mean | 0.926777 | 0.926593 | -0.000183 |
| fig_a ibm_fez, mean fidelity 1 shrinkage, lo95 | 0.924346 | 0.924186 | -0.000160 |
| fig_a ibm_fez, mean fidelity 1 shrinkage, hi95 | 0.929096 | 0.928917 | -0.000180 |
| fig_a ibm_fez, mean fidelity 1 ceiling, n | 315 | 325 | +10.000000 |
| fig_a ibm_fez, mean fidelity 1 ceiling, mean | 0.928949 | 0.928828 | -0.000121 |
| fig_a ibm_fez, mean fidelity 1 ceiling, lo95 | 0.926729 | 0.926690 | -0.000039 |
| fig_a ibm_fez, mean fidelity 1 ceiling, hi95 | 0.931122 | 0.930984 | -0.000138 |
| fig_a ibm_fez, mean fidelity 3 random, n | 315 | 325 | +10.000000 |
| fig_a ibm_fez, mean fidelity 3 random, mean | 0.697775 | 0.699047 | +0.001272 |
| fig_a ibm_fez, mean fidelity 3 random, lo95 | 0.684811 | 0.686745 | +0.001934 |
| fig_a ibm_fez, mean fidelity 3 random, hi95 | 0.709969 | 0.710808 | +0.000840 |
| fig_a ibm_fez, mean fidelity 3 stale, n | 315 | 325 | +10.000000 |
| fig_a ibm_fez, mean fidelity 3 stale, mean | 0.925282 | 0.925263 | -0.000019 |
| fig_a ibm_fez, mean fidelity 3 stale, lo95 | 0.921798 | 0.922008 | +0.000210 |
| fig_a ibm_fez, mean fidelity 3 stale, hi95 | 0.928315 | 0.928180 | -0.000135 |
| fig_a ibm_fez, mean fidelity 3 window_mean, n | 315 | 325 | +10.000000 |
| fig_a ibm_fez, mean fidelity 3 window_mean, mean | 0.923664 | 0.923498 | -0.000165 |
| fig_a ibm_fez, mean fidelity 3 window_mean, lo95 | 0.920183 | 0.920103 | -0.000080 |
| fig_a ibm_fez, mean fidelity 3 window_mean, hi95 | 0.927088 | 0.926726 | -0.000362 |
| fig_a ibm_fez, mean fidelity 3 std_adjusted, n | 315 | 325 | +10.000000 |
| fig_a ibm_fez, mean fidelity 3 std_adjusted, mean | 0.921101 | 0.921088 | -0.000013 |
| fig_a ibm_fez, mean fidelity 3 std_adjusted, lo95 | 0.917047 | 0.917059 | +0.000012 |
| fig_a ibm_fez, mean fidelity 3 std_adjusted, hi95 | 0.924769 | 0.924596 | -0.000173 |
| fig_a ibm_fez, mean fidelity 3 shrinkage, n | 315 | 325 | +10.000000 |
| fig_a ibm_fez, mean fidelity 3 shrinkage, mean | 0.925202 | 0.925107 | -0.000096 |
| fig_a ibm_fez, mean fidelity 3 shrinkage, lo95 | 0.922332 | 0.922353 | +0.000021 |
| fig_a ibm_fez, mean fidelity 3 shrinkage, hi95 | 0.928039 | 0.927764 | -0.000275 |
| fig_a ibm_fez, mean fidelity 3 ceiling, n | 315 | 325 | +10.000000 |
| fig_a ibm_fez, mean fidelity 3 ceiling, mean | 0.928698 | 0.928574 | -0.000124 |
| fig_a ibm_fez, mean fidelity 3 ceiling, lo95 | 0.926652 | 0.926573 | -0.000079 |
| fig_a ibm_fez, mean fidelity 3 ceiling, hi95 | 0.930672 | 0.930553 | -0.000119 |
| fig_a ibm_fez, mean fidelity 6 random, n | 310 | 325 | +15.000000 |
| fig_a ibm_fez, mean fidelity 6 random, mean | 0.698503 | 0.698797 | +0.000294 |
| fig_a ibm_fez, mean fidelity 6 random, lo95 | 0.688258 | 0.688678 | +0.000419 |
| fig_a ibm_fez, mean fidelity 6 random, hi95 | 0.709753 | 0.709580 | -0.000173 |
| fig_a ibm_fez, mean fidelity 6 stale, n | 310 | 325 | +15.000000 |
| fig_a ibm_fez, mean fidelity 6 stale, mean | 0.919132 | 0.918925 | -0.000207 |
| fig_a ibm_fez, mean fidelity 6 stale, lo95 | 0.913609 | 0.914011 | +0.000402 |
| fig_a ibm_fez, mean fidelity 6 stale, hi95 | 0.924301 | 0.924047 | -0.000254 |
| fig_a ibm_fez, mean fidelity 6 window_mean, n | 310 | 325 | +15.000000 |
| fig_a ibm_fez, mean fidelity 6 window_mean, mean | 0.920630 | 0.920509 | -0.000120 |
| fig_a ibm_fez, mean fidelity 6 window_mean, lo95 | 0.916519 | 0.916580 | +0.000061 |
| fig_a ibm_fez, mean fidelity 6 window_mean, hi95 | 0.924606 | 0.924426 | -0.000180 |
| fig_a ibm_fez, mean fidelity 6 std_adjusted, n | 310 | 325 | +15.000000 |
| fig_a ibm_fez, mean fidelity 6 std_adjusted, mean | 0.915742 | 0.915822 | +0.000081 |
| fig_a ibm_fez, mean fidelity 6 std_adjusted, lo95 | 0.908050 | 0.908447 | +0.000397 |
| fig_a ibm_fez, mean fidelity 6 std_adjusted, hi95 | 0.921843 | 0.921715 | -0.000128 |
| fig_a ibm_fez, mean fidelity 6 shrinkage, n | 310 | 325 | +15.000000 |
| fig_a ibm_fez, mean fidelity 6 shrinkage, mean | 0.920013 | 0.919905 | -0.000108 |
| fig_a ibm_fez, mean fidelity 6 shrinkage, lo95 | 0.915000 | 0.915116 | +0.000116 |
| fig_a ibm_fez, mean fidelity 6 shrinkage, hi95 | 0.924715 | 0.924341 | -0.000374 |
| fig_a ibm_fez, mean fidelity 6 ceiling, n | 310 | 325 | +15.000000 |
| fig_a ibm_fez, mean fidelity 6 ceiling, mean | 0.928491 | 0.928437 | -0.000054 |
| fig_a ibm_fez, mean fidelity 6 ceiling, lo95 | 0.926606 | 0.926677 | +0.000071 |
| fig_a ibm_fez, mean fidelity 6 ceiling, hi95 | 0.930330 | 0.930304 | -0.000027 |
| fig_a ibm_fez, mean fidelity 12 random, n | 290 | 315 | +25.000000 |
| fig_a ibm_fez, mean fidelity 12 random, mean | 0.701075 | 0.699722 | -0.001353 |
| fig_a ibm_fez, mean fidelity 12 random, lo95 | 0.688333 | 0.687785 | -0.000548 |
| fig_a ibm_fez, mean fidelity 12 random, hi95 | 0.713288 | 0.712475 | -0.000813 |
| fig_a ibm_fez, mean fidelity 12 stale, n | 290 | 315 | +25.000000 |
| fig_a ibm_fez, mean fidelity 12 stale, mean | 0.915416 | 0.915523 | +0.000107 |
| fig_a ibm_fez, mean fidelity 12 stale, lo95 | 0.909497 | 0.910147 | +0.000650 |
| fig_a ibm_fez, mean fidelity 12 stale, hi95 | 0.920908 | 0.920620 | -0.000288 |
| fig_a ibm_fez, mean fidelity 12 window_mean, n | 290 | 315 | +25.000000 |
| fig_a ibm_fez, mean fidelity 12 window_mean, mean | 0.919563 | 0.919471 | -0.000092 |
| fig_a ibm_fez, mean fidelity 12 window_mean, lo95 | 0.915449 | 0.915410 | -0.000039 |
| fig_a ibm_fez, mean fidelity 12 window_mean, hi95 | 0.923566 | 0.923429 | -0.000137 |
| fig_a ibm_fez, mean fidelity 12 std_adjusted, n | 290 | 315 | +25.000000 |
| fig_a ibm_fez, mean fidelity 12 std_adjusted, mean | 0.918013 | 0.917933 | -0.000080 |
| fig_a ibm_fez, mean fidelity 12 std_adjusted, lo95 | 0.913864 | 0.913953 | +0.000089 |
| fig_a ibm_fez, mean fidelity 12 std_adjusted, hi95 | 0.922029 | 0.921728 | -0.000301 |
| fig_a ibm_fez, mean fidelity 12 shrinkage, n | 290 | 315 | +25.000000 |
| fig_a ibm_fez, mean fidelity 12 shrinkage, mean | 0.918870 | 0.918806 | -0.000064 |
| fig_a ibm_fez, mean fidelity 12 shrinkage, lo95 | 0.914156 | 0.914693 | +0.000537 |
| fig_a ibm_fez, mean fidelity 12 shrinkage, hi95 | 0.923135 | 0.922791 | -0.000344 |
| fig_a ibm_fez, mean fidelity 12 ceiling, n | 290 | 315 | +25.000000 |
| fig_a ibm_fez, mean fidelity 12 ceiling, mean | 0.929736 | 0.929648 | -0.000088 |
| fig_a ibm_fez, mean fidelity 12 ceiling, lo95 | 0.927980 | 0.927933 | -0.000047 |
| fig_a ibm_fez, mean fidelity 12 ceiling, hi95 | 0.931474 | 0.931276 | -0.000198 |
| fig_a ibm_fez, mean fidelity 24 random, n | 280 | 310 | +30.000000 |
| fig_a ibm_fez, mean fidelity 24 random, mean | 0.693137 | 0.693191 | +0.000054 |
| fig_a ibm_fez, mean fidelity 24 random, lo95 | 0.676095 | 0.677587 | +0.001492 |
| fig_a ibm_fez, mean fidelity 24 random, hi95 | 0.709478 | 0.707593 | -0.001885 |
| fig_a ibm_fez, mean fidelity 24 stale, n | 280 | 310 | +30.000000 |
| fig_a ibm_fez, mean fidelity 24 stale, mean | 0.915922 | 0.916100 | +0.000178 |
| fig_a ibm_fez, mean fidelity 24 stale, lo95 | 0.908274 | 0.909235 | +0.000961 |
| fig_a ibm_fez, mean fidelity 24 stale, hi95 | 0.921217 | 0.920894 | -0.000324 |
| fig_a ibm_fez, mean fidelity 24 window_mean, n | 280 | 310 | +30.000000 |
| fig_a ibm_fez, mean fidelity 24 window_mean, mean | 0.920533 | 0.920051 | -0.000482 |
| fig_a ibm_fez, mean fidelity 24 window_mean, lo95 | 0.915197 | 0.915252 | +0.000055 |
| fig_a ibm_fez, mean fidelity 24 window_mean, hi95 | 0.924585 | 0.923811 | -0.000773 |
| fig_a ibm_fez, mean fidelity 24 std_adjusted, n | 280 | 310 | +30.000000 |
| fig_a ibm_fez, mean fidelity 24 std_adjusted, mean | 0.916319 | 0.916134 | -0.000185 |
| fig_a ibm_fez, mean fidelity 24 std_adjusted, lo95 | 0.908682 | 0.909323 | +0.000641 |
| fig_a ibm_fez, mean fidelity 24 std_adjusted, hi95 | 0.921963 | 0.921233 | -0.000731 |
| fig_a ibm_fez, mean fidelity 24 shrinkage, n | 280 | 310 | +30.000000 |
| fig_a ibm_fez, mean fidelity 24 shrinkage, mean | 0.918264 | 0.918035 | -0.000229 |
| fig_a ibm_fez, mean fidelity 24 shrinkage, lo95 | 0.910880 | 0.911425 | +0.000546 |
| fig_a ibm_fez, mean fidelity 24 shrinkage, hi95 | 0.923257 | 0.922536 | -0.000721 |
| fig_a ibm_fez, mean fidelity 24 ceiling, n | 280 | 310 | +30.000000 |
| fig_a ibm_fez, mean fidelity 24 ceiling, mean | 0.928359 | 0.928137 | -0.000222 |
| fig_a ibm_fez, mean fidelity 24 ceiling, lo95 | 0.926769 | 0.926651 | -0.000118 |
| fig_a ibm_fez, mean fidelity 24 ceiling, hi95 | 0.929990 | 0.929665 | -0.000325 |
| fig_a ibm_fez, mean fidelity 48 random, n | 250 | 290 | +40.000000 |
| fig_a ibm_fez, mean fidelity 48 random, mean | 0.692532 | 0.693287 | +0.000756 |
| fig_a ibm_fez, mean fidelity 48 random, lo95 | 0.678348 | 0.680588 | +0.002240 |
| fig_a ibm_fez, mean fidelity 48 random, hi95 | 0.704902 | 0.704279 | -0.000624 |
| fig_a ibm_fez, mean fidelity 48 stale, n | 250 | 290 | +40.000000 |
| fig_a ibm_fez, mean fidelity 48 stale, mean | 0.914115 | 0.915051 | +0.000937 |
| fig_a ibm_fez, mean fidelity 48 stale, lo95 | 0.904770 | 0.907032 | +0.002262 |
| fig_a ibm_fez, mean fidelity 48 stale, hi95 | 0.921950 | 0.921644 | -0.000306 |
| fig_a ibm_fez, mean fidelity 48 window_mean, n | 250 | 290 | +40.000000 |
| fig_a ibm_fez, mean fidelity 48 window_mean, mean | 0.914770 | 0.915856 | +0.001086 |
| fig_a ibm_fez, mean fidelity 48 window_mean, lo95 | 0.905192 | 0.907144 | +0.001952 |
| fig_a ibm_fez, mean fidelity 48 window_mean, hi95 | 0.922849 | 0.922973 | +0.000124 |
| fig_a ibm_fez, mean fidelity 48 std_adjusted, n | 250 | 290 | +40.000000 |
| fig_a ibm_fez, mean fidelity 48 std_adjusted, mean | 0.912056 | 0.913260 | +0.001204 |
| fig_a ibm_fez, mean fidelity 48 std_adjusted, lo95 | 0.903284 | 0.905481 | +0.002197 |
| fig_a ibm_fez, mean fidelity 48 std_adjusted, hi95 | 0.919713 | 0.919954 | +0.000240 |
| fig_a ibm_fez, mean fidelity 48 shrinkage, n | 250 | 290 | +40.000000 |
| fig_a ibm_fez, mean fidelity 48 shrinkage, mean | 0.914602 | 0.915509 | +0.000907 |
| fig_a ibm_fez, mean fidelity 48 shrinkage, lo95 | 0.905533 | 0.907447 | +0.001915 |
| fig_a ibm_fez, mean fidelity 48 shrinkage, hi95 | 0.922659 | 0.922300 | -0.000358 |
| fig_a ibm_fez, mean fidelity 48 ceiling, n | 250 | 290 | +40.000000 |
| fig_a ibm_fez, mean fidelity 48 ceiling, mean | 0.928344 | 0.928259 | -0.000085 |
| fig_a ibm_fez, mean fidelity 48 ceiling, lo95 | 0.925955 | 0.926237 | +0.000282 |
| fig_a ibm_fez, mean fidelity 48 ceiling, hi95 | 0.930601 | 0.930226 | -0.000376 |
| fig_a ibm_fez, regret vs ceiling 1 regret_random, n | 315 | 325 | +10.000000 |
| fig_a ibm_fez, regret vs ceiling 1 regret_random, mean | 0.222389 | 0.221077 | -0.001311 |
| fig_a ibm_fez, regret vs ceiling 1 regret_random, lo95 | 0.210103 | 0.208238 | -0.001865 |
| fig_a ibm_fez, regret vs ceiling 1 regret_random, hi95 | 0.235231 | 0.233713 | -0.001519 |
| fig_a ibm_fez, regret vs ceiling 1 regret_stale, n | 315 | 325 | +10.000000 |
| fig_a ibm_fez, regret vs ceiling 1 regret_stale, mean | 0.001142 | 0.001106 | -0.000035 |
| fig_a ibm_fez, regret vs ceiling 1 regret_stale, lo95 | 0.000440 | 0.000452 | +0.000012 |
| fig_a ibm_fez, regret vs ceiling 1 regret_stale, hi95 | 0.001924 | 0.001871 | -0.000053 |
| fig_a ibm_fez, regret vs ceiling 1 regret_window_mean, n | 315 | 325 | +10.000000 |
| fig_a ibm_fez, regret vs ceiling 1 regret_window_mean, mean | 0.004421 | 0.004503 | +0.000082 |
| fig_a ibm_fez, regret vs ceiling 1 regret_window_mean, lo95 | 0.002988 | 0.003110 | +0.000122 |
| fig_a ibm_fez, regret vs ceiling 1 regret_window_mean, hi95 | 0.006360 | 0.006390 | +0.000030 |
| fig_a ibm_fez, regret vs ceiling 1 regret_std_adjusted, n | 315 | 325 | +10.000000 |
| fig_a ibm_fez, regret vs ceiling 1 regret_std_adjusted, mean | 0.006273 | 0.006220 | -0.000053 |
| fig_a ibm_fez, regret vs ceiling 1 regret_std_adjusted, lo95 | 0.003629 | 0.003690 | +0.000061 |
| fig_a ibm_fez, regret vs ceiling 1 regret_std_adjusted, hi95 | 0.009966 | 0.009950 | -0.000017 |
| fig_a ibm_fez, regret vs ceiling 1 regret_shrinkage, n | 315 | 325 | +10.000000 |
| fig_a ibm_fez, regret vs ceiling 1 regret_shrinkage, mean | 0.002173 | 0.002235 | +0.000062 |
| fig_a ibm_fez, regret vs ceiling 1 regret_shrinkage, lo95 | 0.001454 | 0.001567 | +0.000113 |
| fig_a ibm_fez, regret vs ceiling 1 regret_shrinkage, hi95 | 0.002892 | 0.002903 | +0.000012 |
| fig_a ibm_fez, regret vs ceiling 3 regret_random, n | 315 | 325 | +10.000000 |
| fig_a ibm_fez, regret vs ceiling 3 regret_random, mean | 0.230922 | 0.229527 | -0.001396 |
| fig_a ibm_fez, regret vs ceiling 3 regret_random, lo95 | 0.218166 | 0.217638 | -0.000528 |
| fig_a ibm_fez, regret vs ceiling 3 regret_random, hi95 | 0.243301 | 0.241240 | -0.002061 |
| fig_a ibm_fez, regret vs ceiling 3 regret_stale, n | 315 | 325 | +10.000000 |
| fig_a ibm_fez, regret vs ceiling 3 regret_stale, mean | 0.003416 | 0.003311 | -0.000105 |
| fig_a ibm_fez, regret vs ceiling 3 regret_stale, lo95 | 0.001798 | 0.001728 | -0.000070 |
| fig_a ibm_fez, regret vs ceiling 3 regret_stale, hi95 | 0.005429 | 0.005242 | -0.000187 |
| fig_a ibm_fez, regret vs ceiling 3 regret_window_mean, n | 315 | 325 | +10.000000 |
| fig_a ibm_fez, regret vs ceiling 3 regret_window_mean, mean | 0.005034 | 0.005076 | +0.000041 |
| fig_a ibm_fez, regret vs ceiling 3 regret_window_mean, lo95 | 0.003283 | 0.003387 | +0.000103 |
| fig_a ibm_fez, regret vs ceiling 3 regret_window_mean, hi95 | 0.007005 | 0.007031 | +0.000026 |
| fig_a ibm_fez, regret vs ceiling 3 regret_std_adjusted, n | 315 | 325 | +10.000000 |
| fig_a ibm_fez, regret vs ceiling 3 regret_std_adjusted, mean | 0.007597 | 0.007486 | -0.000111 |
| fig_a ibm_fez, regret vs ceiling 3 regret_std_adjusted, lo95 | 0.004980 | 0.004839 | -0.000141 |
| fig_a ibm_fez, regret vs ceiling 3 regret_std_adjusted, hi95 | 0.011248 | 0.011145 | -0.000104 |
| fig_a ibm_fez, regret vs ceiling 3 regret_shrinkage, n | 315 | 325 | +10.000000 |
| fig_a ibm_fez, regret vs ceiling 3 regret_shrinkage, mean | 0.003495 | 0.003467 | -0.000028 |
| fig_a ibm_fez, regret vs ceiling 3 regret_shrinkage, lo95 | 0.002350 | 0.002314 | -0.000037 |
| fig_a ibm_fez, regret vs ceiling 3 regret_shrinkage, hi95 | 0.004792 | 0.004741 | -0.000051 |
| fig_a ibm_fez, regret vs ceiling 6 regret_random, n | 310 | 325 | +15.000000 |
| fig_a ibm_fez, regret vs ceiling 6 regret_random, mean | 0.229988 | 0.229640 | -0.000348 |
| fig_a ibm_fez, regret vs ceiling 6 regret_random, lo95 | 0.220130 | 0.219650 | -0.000480 |
| fig_a ibm_fez, regret vs ceiling 6 regret_random, hi95 | 0.239442 | 0.238633 | -0.000810 |
| fig_a ibm_fez, regret vs ceiling 6 regret_stale, n | 310 | 325 | +15.000000 |
| fig_a ibm_fez, regret vs ceiling 6 regret_stale, mean | 0.009359 | 0.009512 | +0.000153 |
| fig_a ibm_fez, regret vs ceiling 6 regret_stale, lo95 | 0.005212 | 0.005594 | +0.000383 |
| fig_a ibm_fez, regret vs ceiling 6 regret_stale, hi95 | 0.014108 | 0.013900 | -0.000208 |
| fig_a ibm_fez, regret vs ceiling 6 regret_window_mean, n | 310 | 325 | +15.000000 |
| fig_a ibm_fez, regret vs ceiling 6 regret_window_mean, mean | 0.007862 | 0.007928 | +0.000066 |
| fig_a ibm_fez, regret vs ceiling 6 regret_window_mean, lo95 | 0.005157 | 0.005358 | +0.000201 |
| fig_a ibm_fez, regret vs ceiling 6 regret_window_mean, hi95 | 0.010716 | 0.010650 | -0.000066 |
| fig_a ibm_fez, regret vs ceiling 6 regret_std_adjusted, n | 310 | 325 | +15.000000 |
| fig_a ibm_fez, regret vs ceiling 6 regret_std_adjusted, mean | 0.012750 | 0.012615 | -0.000135 |
| fig_a ibm_fez, regret vs ceiling 6 regret_std_adjusted, lo95 | 0.007687 | 0.007804 | +0.000117 |
| fig_a ibm_fez, regret vs ceiling 6 regret_std_adjusted, hi95 | 0.020062 | 0.019544 | -0.000517 |
| fig_a ibm_fez, regret vs ceiling 6 regret_shrinkage, n | 310 | 325 | +15.000000 |
| fig_a ibm_fez, regret vs ceiling 6 regret_shrinkage, mean | 0.008478 | 0.008533 | +0.000054 |
| fig_a ibm_fez, regret vs ceiling 6 regret_shrinkage, lo95 | 0.005138 | 0.005412 | +0.000274 |
| fig_a ibm_fez, regret vs ceiling 6 regret_shrinkage, hi95 | 0.012266 | 0.012284 | +0.000019 |
| fig_a ibm_fez, regret vs ceiling 12 regret_random, n | 290 | 315 | +25.000000 |
| fig_a ibm_fez, regret vs ceiling 12 regret_random, mean | 0.228660 | 0.229926 | +0.001266 |
| fig_a ibm_fez, regret vs ceiling 12 regret_random, lo95 | 0.216289 | 0.218002 | +0.001712 |
| fig_a ibm_fez, regret vs ceiling 12 regret_random, hi95 | 0.241758 | 0.241905 | +0.000146 |
| fig_a ibm_fez, regret vs ceiling 12 regret_stale, n | 290 | 315 | +25.000000 |
| fig_a ibm_fez, regret vs ceiling 12 regret_stale, mean | 0.014319 | 0.014124 | -0.000195 |
| fig_a ibm_fez, regret vs ceiling 12 regret_stale, lo95 | 0.009697 | 0.009845 | +0.000148 |
| fig_a ibm_fez, regret vs ceiling 12 regret_stale, hi95 | 0.019300 | 0.018685 | -0.000614 |
| fig_a ibm_fez, regret vs ceiling 12 regret_window_mean, n | 290 | 315 | +25.000000 |
| fig_a ibm_fez, regret vs ceiling 12 regret_window_mean, mean | 0.010172 | 0.010176 | +0.000004 |
| fig_a ibm_fez, regret vs ceiling 12 regret_window_mean, lo95 | 0.007359 | 0.007467 | +0.000108 |
| fig_a ibm_fez, regret vs ceiling 12 regret_window_mean, hi95 | 0.013038 | 0.012936 | -0.000102 |
| fig_a ibm_fez, regret vs ceiling 12 regret_std_adjusted, n | 290 | 315 | +25.000000 |
| fig_a ibm_fez, regret vs ceiling 12 regret_std_adjusted, mean | 0.011723 | 0.011715 | -0.000008 |
| fig_a ibm_fez, regret vs ceiling 12 regret_std_adjusted, lo95 | 0.008965 | 0.009357 | +0.000392 |
| fig_a ibm_fez, regret vs ceiling 12 regret_std_adjusted, hi95 | 0.014568 | 0.014444 | -0.000124 |
| fig_a ibm_fez, regret vs ceiling 12 regret_shrinkage, n | 290 | 315 | +25.000000 |
| fig_a ibm_fez, regret vs ceiling 12 regret_shrinkage, mean | 0.010866 | 0.010842 | -0.000024 |
| fig_a ibm_fez, regret vs ceiling 12 regret_shrinkage, lo95 | 0.007738 | 0.008010 | +0.000272 |
| fig_a ibm_fez, regret vs ceiling 12 regret_shrinkage, hi95 | 0.014196 | 0.013879 | -0.000317 |
| fig_a ibm_fez, regret vs ceiling 24 regret_random, n | 280 | 310 | +30.000000 |
| fig_a ibm_fez, regret vs ceiling 24 regret_random, mean | 0.235221 | 0.234945 | -0.000276 |
| fig_a ibm_fez, regret vs ceiling 24 regret_random, lo95 | 0.219641 | 0.220616 | +0.000975 |
| fig_a ibm_fez, regret vs ceiling 24 regret_random, hi95 | 0.251992 | 0.250303 | -0.001689 |
| fig_a ibm_fez, regret vs ceiling 24 regret_stale, n | 280 | 310 | +30.000000 |
| fig_a ibm_fez, regret vs ceiling 24 regret_stale, mean | 0.012437 | 0.012037 | -0.000400 |
| fig_a ibm_fez, regret vs ceiling 24 regret_stale, lo95 | 0.007843 | 0.007835 | -0.000008 |
| fig_a ibm_fez, regret vs ceiling 24 regret_stale, hi95 | 0.019036 | 0.018050 | -0.000986 |
| fig_a ibm_fez, regret vs ceiling 24 regret_window_mean, n | 280 | 310 | +30.000000 |
| fig_a ibm_fez, regret vs ceiling 24 regret_window_mean, mean | 0.007826 | 0.008086 | +0.000260 |
| fig_a ibm_fez, regret vs ceiling 24 regret_window_mean, lo95 | 0.004662 | 0.005030 | +0.000368 |
| fig_a ibm_fez, regret vs ceiling 24 regret_window_mean, hi95 | 0.012614 | 0.012209 | -0.000405 |
| fig_a ibm_fez, regret vs ceiling 24 regret_std_adjusted, n | 280 | 310 | +30.000000 |
| fig_a ibm_fez, regret vs ceiling 24 regret_std_adjusted, mean | 0.012039 | 0.012003 | -0.000037 |
| fig_a ibm_fez, regret vs ceiling 24 regret_std_adjusted, lo95 | 0.007374 | 0.007667 | +0.000293 |
| fig_a ibm_fez, regret vs ceiling 24 regret_std_adjusted, hi95 | 0.019406 | 0.018390 | -0.001016 |
| fig_a ibm_fez, regret vs ceiling 24 regret_shrinkage, n | 280 | 310 | +30.000000 |
| fig_a ibm_fez, regret vs ceiling 24 regret_shrinkage, mean | 0.010095 | 0.010102 | +0.000007 |
| fig_a ibm_fez, regret vs ceiling 24 regret_shrinkage, lo95 | 0.005748 | 0.006176 | +0.000427 |
| fig_a ibm_fez, regret vs ceiling 24 regret_shrinkage, hi95 | 0.016863 | 0.016356 | -0.000507 |
| fig_a ibm_fez, regret vs ceiling 48 regret_random, n | 250 | 290 | +40.000000 |
| fig_a ibm_fez, regret vs ceiling 48 regret_random, mean | 0.235813 | 0.234972 | -0.000841 |
| fig_a ibm_fez, regret vs ceiling 48 regret_random, lo95 | 0.222858 | 0.223407 | +0.000549 |
| fig_a ibm_fez, regret vs ceiling 48 regret_random, hi95 | 0.249830 | 0.247139 | -0.002691 |
| fig_a ibm_fez, regret vs ceiling 48 regret_stale, n | 250 | 290 | +40.000000 |
| fig_a ibm_fez, regret vs ceiling 48 regret_stale, mean | 0.014230 | 0.013208 | -0.001022 |
| fig_a ibm_fez, regret vs ceiling 48 regret_stale, lo95 | 0.008196 | 0.008046 | -0.000150 |
| fig_a ibm_fez, regret vs ceiling 48 regret_stale, hi95 | 0.020881 | 0.019659 | -0.001221 |
| fig_a ibm_fez, regret vs ceiling 48 regret_window_mean, n | 250 | 290 | +40.000000 |
| fig_a ibm_fez, regret vs ceiling 48 regret_window_mean, mean | 0.013575 | 0.012403 | -0.001171 |
| fig_a ibm_fez, regret vs ceiling 48 regret_window_mean, lo95 | 0.007165 | 0.006718 | -0.000447 |
| fig_a ibm_fez, regret vs ceiling 48 regret_window_mean, hi95 | 0.021145 | 0.018900 | -0.002245 |
| fig_a ibm_fez, regret vs ceiling 48 regret_std_adjusted, n | 250 | 290 | +40.000000 |
| fig_a ibm_fez, regret vs ceiling 48 regret_std_adjusted, mean | 0.016289 | 0.014999 | -0.001290 |
| fig_a ibm_fez, regret vs ceiling 48 regret_std_adjusted, lo95 | 0.010332 | 0.009605 | -0.000728 |
| fig_a ibm_fez, regret vs ceiling 48 regret_std_adjusted, hi95 | 0.023631 | 0.021382 | -0.002249 |
| fig_a ibm_fez, regret vs ceiling 48 regret_shrinkage, n | 250 | 290 | +40.000000 |
| fig_a ibm_fez, regret vs ceiling 48 regret_shrinkage, mean | 0.013742 | 0.012750 | -0.000993 |
| fig_a ibm_fez, regret vs ceiling 48 regret_shrinkage, lo95 | 0.007691 | 0.007375 | -0.000316 |
| fig_a ibm_fez, regret vs ceiling 48 regret_shrinkage, hi95 | 0.021152 | 0.019226 | -0.001926 |
| fig_a ibm_kingston, mean fidelity 1 random, n | 300 | 315 | +15.000000 |
| fig_a ibm_kingston, mean fidelity 1 random, mean | 0.773211 | 0.773031 | -0.000180 |
| fig_a ibm_kingston, mean fidelity 1 random, lo95 | 0.713597 | 0.717178 | +0.003582 |
| fig_a ibm_kingston, mean fidelity 1 random, hi95 | 0.809385 | 0.807449 | -0.001937 |
| fig_a ibm_kingston, mean fidelity 1 stale, n | 300 | 315 | +15.000000 |
| fig_a ibm_kingston, mean fidelity 1 stale, mean | 0.905403 | 0.906753 | +0.001350 |
| fig_a ibm_kingston, mean fidelity 1 stale, lo95 | 0.841676 | 0.847602 | +0.005926 |
| fig_a ibm_kingston, mean fidelity 1 stale, hi95 | 0.937556 | 0.937373 | -0.000183 |
| fig_a ibm_kingston, mean fidelity 1 window_mean, n | 300 | 315 | +15.000000 |
| fig_a ibm_kingston, mean fidelity 1 window_mean, mean | 0.902108 | 0.902888 | +0.000780 |
| fig_a ibm_kingston, mean fidelity 1 window_mean, lo95 | 0.838091 | 0.843529 | +0.005438 |
| fig_a ibm_kingston, mean fidelity 1 window_mean, hi95 | 0.934400 | 0.933905 | -0.000494 |
| fig_a ibm_kingston, mean fidelity 1 std_adjusted, n | 300 | 315 | +15.000000 |
| fig_a ibm_kingston, mean fidelity 1 std_adjusted, mean | 0.899758 | 0.900669 | +0.000911 |
| fig_a ibm_kingston, mean fidelity 1 std_adjusted, lo95 | 0.836726 | 0.842301 | +0.005575 |
| fig_a ibm_kingston, mean fidelity 1 std_adjusted, hi95 | 0.931384 | 0.931035 | -0.000349 |
| fig_a ibm_kingston, mean fidelity 1 shrinkage, n | 300 | 315 | +15.000000 |
| fig_a ibm_kingston, mean fidelity 1 shrinkage, mean | 0.904853 | 0.906275 | +0.001422 |
| fig_a ibm_kingston, mean fidelity 1 shrinkage, lo95 | 0.839438 | 0.847196 | +0.007758 |
| fig_a ibm_kingston, mean fidelity 1 shrinkage, hi95 | 0.937110 | 0.937034 | -0.000077 |
| fig_a ibm_kingston, mean fidelity 1 ceiling, n | 300 | 315 | +15.000000 |
| fig_a ibm_kingston, mean fidelity 1 ceiling, mean | 0.906698 | 0.907986 | +0.001289 |
| fig_a ibm_kingston, mean fidelity 1 ceiling, lo95 | 0.842847 | 0.848757 | +0.005911 |
| fig_a ibm_kingston, mean fidelity 1 ceiling, hi95 | 0.938724 | 0.938546 | -0.000178 |
| fig_a ibm_kingston, mean fidelity 3 random, n | 300 | 315 | +15.000000 |
| fig_a ibm_kingston, mean fidelity 3 random, mean | 0.782673 | 0.783274 | +0.000601 |
| fig_a ibm_kingston, mean fidelity 3 random, lo95 | 0.749755 | 0.752115 | +0.002360 |
| fig_a ibm_kingston, mean fidelity 3 random, hi95 | 0.804927 | 0.804421 | -0.000506 |
| fig_a ibm_kingston, mean fidelity 3 stale, n | 300 | 315 | +15.000000 |
| fig_a ibm_kingston, mean fidelity 3 stale, mean | 0.908854 | 0.910082 | +0.001228 |
| fig_a ibm_kingston, mean fidelity 3 stale, lo95 | 0.873806 | 0.874229 | +0.000423 |
| fig_a ibm_kingston, mean fidelity 3 stale, hi95 | 0.932704 | 0.932629 | -0.000075 |
| fig_a ibm_kingston, mean fidelity 3 window_mean, n | 300 | 315 | +15.000000 |
| fig_a ibm_kingston, mean fidelity 3 window_mean, mean | 0.915385 | 0.915552 | +0.000167 |
| fig_a ibm_kingston, mean fidelity 3 window_mean, lo95 | 0.882075 | 0.885231 | +0.003156 |
| fig_a ibm_kingston, mean fidelity 3 window_mean, hi95 | 0.932558 | 0.931748 | -0.000810 |
| fig_a ibm_kingston, mean fidelity 3 std_adjusted, n | 300 | 315 | +15.000000 |
| fig_a ibm_kingston, mean fidelity 3 std_adjusted, mean | 0.912792 | 0.913105 | +0.000312 |
| fig_a ibm_kingston, mean fidelity 3 std_adjusted, lo95 | 0.880603 | 0.882872 | +0.002269 |
| fig_a ibm_kingston, mean fidelity 3 std_adjusted, hi95 | 0.929849 | 0.929430 | -0.000419 |
| fig_a ibm_kingston, mean fidelity 3 shrinkage, n | 300 | 315 | +15.000000 |
| fig_a ibm_kingston, mean fidelity 3 shrinkage, mean | 0.911940 | 0.913035 | +0.001095 |
| fig_a ibm_kingston, mean fidelity 3 shrinkage, lo95 | 0.875564 | 0.880320 | +0.004756 |
| fig_a ibm_kingston, mean fidelity 3 shrinkage, hi95 | 0.933086 | 0.933079 | -0.000007 |
| fig_a ibm_kingston, mean fidelity 3 ceiling, n | 300 | 315 | +15.000000 |
| fig_a ibm_kingston, mean fidelity 3 ceiling, mean | 0.922135 | 0.922730 | +0.000596 |
| fig_a ibm_kingston, mean fidelity 3 ceiling, lo95 | 0.889175 | 0.892823 | +0.003649 |
| fig_a ibm_kingston, mean fidelity 3 ceiling, hi95 | 0.938716 | 0.938582 | -0.000135 |
| fig_a ibm_kingston, mean fidelity 6 random, n | 300 | 315 | +15.000000 |
| fig_a ibm_kingston, mean fidelity 6 random, mean | 0.789599 | 0.788272 | -0.001327 |
| fig_a ibm_kingston, mean fidelity 6 random, lo95 | 0.775731 | 0.774193 | -0.001538 |
| fig_a ibm_kingston, mean fidelity 6 random, hi95 | 0.803423 | 0.801667 | -0.001756 |
| fig_a ibm_kingston, mean fidelity 6 stale, n | 300 | 315 | +15.000000 |
| fig_a ibm_kingston, mean fidelity 6 stale, mean | 0.916728 | 0.917425 | +0.000697 |
| fig_a ibm_kingston, mean fidelity 6 stale, lo95 | 0.900170 | 0.901455 | +0.001286 |
| fig_a ibm_kingston, mean fidelity 6 stale, hi95 | 0.927558 | 0.927808 | +0.000251 |
| fig_a ibm_kingston, mean fidelity 6 window_mean, n | 300 | 315 | +15.000000 |
| fig_a ibm_kingston, mean fidelity 6 window_mean, mean | 0.928579 | 0.928223 | -0.000356 |
| fig_a ibm_kingston, mean fidelity 6 window_mean, lo95 | 0.925885 | 0.925775 | -0.000110 |
| fig_a ibm_kingston, mean fidelity 6 window_mean, hi95 | 0.931010 | 0.930545 | -0.000465 |
| fig_a ibm_kingston, mean fidelity 6 std_adjusted, n | 300 | 315 | +15.000000 |
| fig_a ibm_kingston, mean fidelity 6 std_adjusted, mean | 0.925672 | 0.925480 | -0.000192 |
| fig_a ibm_kingston, mean fidelity 6 std_adjusted, lo95 | 0.923099 | 0.923078 | -0.000021 |
| fig_a ibm_kingston, mean fidelity 6 std_adjusted, hi95 | 0.928176 | 0.927755 | -0.000421 |
| fig_a ibm_kingston, mean fidelity 6 shrinkage, n | 300 | 315 | +15.000000 |
| fig_a ibm_kingston, mean fidelity 6 shrinkage, mean | 0.921445 | 0.921955 | +0.000510 |
| fig_a ibm_kingston, mean fidelity 6 shrinkage, lo95 | 0.910619 | 0.911117 | +0.000498 |
| fig_a ibm_kingston, mean fidelity 6 shrinkage, hi95 | 0.928891 | 0.929121 | +0.000230 |
| fig_a ibm_kingston, mean fidelity 6 ceiling, n | 300 | 315 | +15.000000 |
| fig_a ibm_kingston, mean fidelity 6 ceiling, mean | 0.937181 | 0.937016 | -0.000164 |
| fig_a ibm_kingston, mean fidelity 6 ceiling, lo95 | 0.935467 | 0.935385 | -0.000082 |
| fig_a ibm_kingston, mean fidelity 6 ceiling, hi95 | 0.938916 | 0.938519 | -0.000397 |
| fig_a ibm_kingston, mean fidelity 12 random, n | 290 | 315 | +25.000000 |
| fig_a ibm_kingston, mean fidelity 12 random, mean | 0.781118 | 0.780880 | -0.000237 |
| fig_a ibm_kingston, mean fidelity 12 random, lo95 | 0.746975 | 0.748423 | +0.001448 |
| fig_a ibm_kingston, mean fidelity 12 random, hi95 | 0.806887 | 0.805205 | -0.001681 |
| fig_a ibm_kingston, mean fidelity 12 stale, n | 290 | 315 | +25.000000 |
| fig_a ibm_kingston, mean fidelity 12 stale, mean | 0.896403 | 0.898538 | +0.002135 |
| fig_a ibm_kingston, mean fidelity 12 stale, lo95 | 0.859792 | 0.864634 | +0.004843 |
| fig_a ibm_kingston, mean fidelity 12 stale, hi95 | 0.920959 | 0.921923 | +0.000965 |
| fig_a ibm_kingston, mean fidelity 12 window_mean, n | 290 | 315 | +25.000000 |
| fig_a ibm_kingston, mean fidelity 12 window_mean, mean | 0.910571 | 0.910974 | +0.000403 |
| fig_a ibm_kingston, mean fidelity 12 window_mean, lo95 | 0.878207 | 0.880899 | +0.002692 |
| fig_a ibm_kingston, mean fidelity 12 window_mean, hi95 | 0.927992 | 0.927493 | -0.000498 |
| fig_a ibm_kingston, mean fidelity 12 std_adjusted, n | 290 | 315 | +25.000000 |
| fig_a ibm_kingston, mean fidelity 12 std_adjusted, mean | 0.905787 | 0.906511 | +0.000724 |
| fig_a ibm_kingston, mean fidelity 12 std_adjusted, lo95 | 0.872110 | 0.876287 | +0.004177 |
| fig_a ibm_kingston, mean fidelity 12 std_adjusted, hi95 | 0.924518 | 0.924088 | -0.000431 |
| fig_a ibm_kingston, mean fidelity 12 shrinkage, n | 290 | 315 | +25.000000 |
| fig_a ibm_kingston, mean fidelity 12 shrinkage, mean | 0.901848 | 0.903601 | +0.001754 |
| fig_a ibm_kingston, mean fidelity 12 shrinkage, lo95 | 0.865623 | 0.870907 | +0.005285 |
| fig_a ibm_kingston, mean fidelity 12 shrinkage, hi95 | 0.923846 | 0.924158 | +0.000313 |
| fig_a ibm_kingston, mean fidelity 12 ceiling, n | 290 | 315 | +25.000000 |
| fig_a ibm_kingston, mean fidelity 12 ceiling, mean | 0.921401 | 0.922671 | +0.001270 |
| fig_a ibm_kingston, mean fidelity 12 ceiling, lo95 | 0.888535 | 0.892872 | +0.004337 |
| fig_a ibm_kingston, mean fidelity 12 ceiling, hi95 | 0.938593 | 0.938497 | -0.000096 |
| fig_a ibm_kingston, mean fidelity 24 random, n | 275 | 305 | +30.000000 |
| fig_a ibm_kingston, mean fidelity 24 random, mean | 0.793620 | 0.792765 | -0.000855 |
| fig_a ibm_kingston, mean fidelity 24 random, lo95 | 0.779163 | 0.779963 | +0.000801 |
| fig_a ibm_kingston, mean fidelity 24 random, hi95 | 0.809045 | 0.806536 | -0.002509 |
| fig_a ibm_kingston, mean fidelity 24 stale, n | 275 | 305 | +30.000000 |
| fig_a ibm_kingston, mean fidelity 24 stale, mean | 0.913881 | 0.914064 | +0.000183 |
| fig_a ibm_kingston, mean fidelity 24 stale, lo95 | 0.895567 | 0.898083 | +0.002516 |
| fig_a ibm_kingston, mean fidelity 24 stale, hi95 | 0.925036 | 0.924056 | -0.000980 |
| fig_a ibm_kingston, mean fidelity 24 window_mean, n | 275 | 305 | +30.000000 |
| fig_a ibm_kingston, mean fidelity 24 window_mean, mean | 0.926605 | 0.924984 | -0.001621 |
| fig_a ibm_kingston, mean fidelity 24 window_mean, lo95 | 0.923571 | 0.921604 | -0.001967 |
| fig_a ibm_kingston, mean fidelity 24 window_mean, hi95 | 0.929561 | 0.928219 | -0.001342 |
| fig_a ibm_kingston, mean fidelity 24 std_adjusted, n | 275 | 305 | +30.000000 |
| fig_a ibm_kingston, mean fidelity 24 std_adjusted, mean | 0.922211 | 0.921165 | -0.001046 |
| fig_a ibm_kingston, mean fidelity 24 std_adjusted, lo95 | 0.914307 | 0.914074 | -0.000233 |
| fig_a ibm_kingston, mean fidelity 24 std_adjusted, hi95 | 0.927286 | 0.926403 | -0.000884 |
| fig_a ibm_kingston, mean fidelity 24 shrinkage, n | 275 | 305 | +30.000000 |
| fig_a ibm_kingston, mean fidelity 24 shrinkage, mean | 0.918875 | 0.918434 | -0.000441 |
| fig_a ibm_kingston, mean fidelity 24 shrinkage, lo95 | 0.907259 | 0.908069 | +0.000811 |
| fig_a ibm_kingston, mean fidelity 24 shrinkage, hi95 | 0.926517 | 0.925420 | -0.001097 |
| fig_a ibm_kingston, mean fidelity 24 ceiling, n | 275 | 305 | +30.000000 |
| fig_a ibm_kingston, mean fidelity 24 ceiling, mean | 0.937568 | 0.937534 | -0.000033 |
| fig_a ibm_kingston, mean fidelity 24 ceiling, lo95 | 0.935754 | 0.935726 | -0.000028 |
| fig_a ibm_kingston, mean fidelity 24 ceiling, hi95 | 0.939381 | 0.939237 | -0.000144 |
| fig_a ibm_kingston, mean fidelity 48 random, n | 260 | 300 | +40.000000 |
| fig_a ibm_kingston, mean fidelity 48 random, mean | 0.780187 | 0.779412 | -0.000775 |
| fig_a ibm_kingston, mean fidelity 48 random, lo95 | 0.741953 | 0.747307 | +0.005355 |
| fig_a ibm_kingston, mean fidelity 48 random, hi95 | 0.807629 | 0.803403 | -0.004226 |
| fig_a ibm_kingston, mean fidelity 48 stale, n | 260 | 300 | +40.000000 |
| fig_a ibm_kingston, mean fidelity 48 stale, mean | 0.883884 | 0.887466 | +0.003583 |
| fig_a ibm_kingston, mean fidelity 48 stale, lo95 | 0.835529 | 0.844956 | +0.009426 |
| fig_a ibm_kingston, mean fidelity 48 stale, hi95 | 0.922250 | 0.920499 | -0.001752 |
| fig_a ibm_kingston, mean fidelity 48 window_mean, n | 260 | 300 | +40.000000 |
| fig_a ibm_kingston, mean fidelity 48 window_mean, mean | 0.899097 | 0.900672 | +0.001575 |
| fig_a ibm_kingston, mean fidelity 48 window_mean, lo95 | 0.855600 | 0.863373 | +0.007773 |
| fig_a ibm_kingston, mean fidelity 48 window_mean, hi95 | 0.928275 | 0.926086 | -0.002189 |
| fig_a ibm_kingston, mean fidelity 48 std_adjusted, n | 260 | 300 | +40.000000 |
| fig_a ibm_kingston, mean fidelity 48 std_adjusted, mean | 0.887117 | 0.890548 | +0.003431 |
| fig_a ibm_kingston, mean fidelity 48 std_adjusted, lo95 | 0.829166 | 0.840288 | +0.011122 |
| fig_a ibm_kingston, mean fidelity 48 std_adjusted, hi95 | 0.926243 | 0.924558 | -0.001685 |
| fig_a ibm_kingston, mean fidelity 48 shrinkage, n | 260 | 300 | +40.000000 |
| fig_a ibm_kingston, mean fidelity 48 shrinkage, mean | 0.889397 | 0.891712 | +0.002314 |
| fig_a ibm_kingston, mean fidelity 48 shrinkage, lo95 | 0.844116 | 0.850130 | +0.006014 |
| fig_a ibm_kingston, mean fidelity 48 shrinkage, hi95 | 0.925125 | 0.922061 | -0.003064 |
| fig_a ibm_kingston, mean fidelity 48 ceiling, n | 260 | 300 | +40.000000 |
| fig_a ibm_kingston, mean fidelity 48 ceiling, mean | 0.919909 | 0.922319 | +0.002411 |
| fig_a ibm_kingston, mean fidelity 48 ceiling, lo95 | 0.883264 | 0.890908 | +0.007643 |
| fig_a ibm_kingston, mean fidelity 48 ceiling, hi95 | 0.938934 | 0.939017 | +0.000083 |
| fig_a ibm_kingston, regret vs ceiling 1 regret_random, n | 300 | 315 | +15.000000 |
| fig_a ibm_kingston, regret vs ceiling 1 regret_random, mean | 0.133487 | 0.134955 | +0.001469 |
| fig_a ibm_kingston, regret vs ceiling 1 regret_random, lo95 | 0.117735 | 0.119537 | +0.001803 |
| fig_a ibm_kingston, regret vs ceiling 1 regret_random, hi95 | 0.148854 | 0.149664 | +0.000810 |
| fig_a ibm_kingston, regret vs ceiling 1 regret_stale, n | 300 | 315 | +15.000000 |
| fig_a ibm_kingston, regret vs ceiling 1 regret_stale, mean | 0.001295 | 0.001233 | -0.000062 |
| fig_a ibm_kingston, regret vs ceiling 1 regret_stale, lo95 | 0.000196 | 0.000222 | +0.000026 |
| fig_a ibm_kingston, regret vs ceiling 1 regret_stale, hi95 | 0.002682 | 0.002595 | -0.000087 |
| fig_a ibm_kingston, regret vs ceiling 1 regret_window_mean, n | 300 | 315 | +15.000000 |
| fig_a ibm_kingston, regret vs ceiling 1 regret_window_mean, mean | 0.004589 | 0.005098 | +0.000509 |
| fig_a ibm_kingston, regret vs ceiling 1 regret_window_mean, lo95 | 0.003155 | 0.003456 | +0.000301 |
| fig_a ibm_kingston, regret vs ceiling 1 regret_window_mean, hi95 | 0.006177 | 0.006929 | +0.000752 |
| fig_a ibm_kingston, regret vs ceiling 1 regret_std_adjusted, n | 300 | 315 | +15.000000 |
| fig_a ibm_kingston, regret vs ceiling 1 regret_std_adjusted, mean | 0.006939 | 0.007317 | +0.000378 |
| fig_a ibm_kingston, regret vs ceiling 1 regret_std_adjusted, lo95 | 0.005123 | 0.005334 | +0.000211 |
| fig_a ibm_kingston, regret vs ceiling 1 regret_std_adjusted, hi95 | 0.008930 | 0.009405 | +0.000476 |
| fig_a ibm_kingston, regret vs ceiling 1 regret_shrinkage, n | 300 | 315 | +15.000000 |
| fig_a ibm_kingston, regret vs ceiling 1 regret_shrinkage, mean | 0.001844 | 0.001711 | -0.000133 |
| fig_a ibm_kingston, regret vs ceiling 1 regret_shrinkage, lo95 | 0.000896 | 0.000831 | -0.000066 |
| fig_a ibm_kingston, regret vs ceiling 1 regret_shrinkage, hi95 | 0.002799 | 0.002583 | -0.000216 |
| fig_a ibm_kingston, regret vs ceiling 3 regret_random, n | 300 | 315 | +15.000000 |
| fig_a ibm_kingston, regret vs ceiling 3 regret_random, mean | 0.139461 | 0.139456 | -0.000005 |
| fig_a ibm_kingston, regret vs ceiling 3 regret_random, lo95 | 0.126459 | 0.126764 | +0.000305 |
| fig_a ibm_kingston, regret vs ceiling 3 regret_random, hi95 | 0.152131 | 0.151258 | -0.000872 |
| fig_a ibm_kingston, regret vs ceiling 3 regret_stale, n | 300 | 315 | +15.000000 |
| fig_a ibm_kingston, regret vs ceiling 3 regret_stale, mean | 0.013280 | 0.012648 | -0.000632 |
| fig_a ibm_kingston, regret vs ceiling 3 regret_stale, lo95 | 0.003433 | 0.003615 | +0.000182 |
| fig_a ibm_kingston, regret vs ceiling 3 regret_stale, hi95 | 0.030133 | 0.028859 | -0.001273 |
| fig_a ibm_kingston, regret vs ceiling 3 regret_window_mean, n | 300 | 315 | +15.000000 |
| fig_a ibm_kingston, regret vs ceiling 3 regret_window_mean, mean | 0.006749 | 0.007178 | +0.000429 |
| fig_a ibm_kingston, regret vs ceiling 3 regret_window_mean, lo95 | 0.004858 | 0.005306 | +0.000448 |
| fig_a ibm_kingston, regret vs ceiling 3 regret_window_mean, hi95 | 0.008610 | 0.009084 | +0.000474 |
| fig_a ibm_kingston, regret vs ceiling 3 regret_std_adjusted, n | 300 | 315 | +15.000000 |
| fig_a ibm_kingston, regret vs ceiling 3 regret_std_adjusted, mean | 0.009342 | 0.009626 | +0.000284 |
| fig_a ibm_kingston, regret vs ceiling 3 regret_std_adjusted, lo95 | 0.006992 | 0.007219 | +0.000228 |
| fig_a ibm_kingston, regret vs ceiling 3 regret_std_adjusted, hi95 | 0.012103 | 0.012308 | +0.000205 |
| fig_a ibm_kingston, regret vs ceiling 3 regret_shrinkage, n | 300 | 315 | +15.000000 |
| fig_a ibm_kingston, regret vs ceiling 3 regret_shrinkage, mean | 0.010194 | 0.009695 | -0.000499 |
| fig_a ibm_kingston, regret vs ceiling 3 regret_shrinkage, lo95 | 0.003887 | 0.003631 | -0.000256 |
| fig_a ibm_kingston, regret vs ceiling 3 regret_shrinkage, hi95 | 0.020759 | 0.020025 | -0.000734 |
| fig_a ibm_kingston, regret vs ceiling 6 regret_random, n | 300 | 315 | +15.000000 |
| fig_a ibm_kingston, regret vs ceiling 6 regret_random, mean | 0.147582 | 0.148745 | +0.001163 |
| fig_a ibm_kingston, regret vs ceiling 6 regret_random, lo95 | 0.133129 | 0.134005 | +0.000876 |
| fig_a ibm_kingston, regret vs ceiling 6 regret_random, hi95 | 0.163489 | 0.163298 | -0.000191 |
| fig_a ibm_kingston, regret vs ceiling 6 regret_stale, n | 300 | 315 | +15.000000 |
| fig_a ibm_kingston, regret vs ceiling 6 regret_stale, mean | 0.020453 | 0.019592 | -0.000861 |
| fig_a ibm_kingston, regret vs ceiling 6 regret_stale, lo95 | 0.009656 | 0.009125 | -0.000531 |
| fig_a ibm_kingston, regret vs ceiling 6 regret_stale, hi95 | 0.037614 | 0.036520 | -0.001094 |
| fig_a ibm_kingston, regret vs ceiling 6 regret_window_mean, n | 300 | 315 | +15.000000 |
| fig_a ibm_kingston, regret vs ceiling 6 regret_window_mean, mean | 0.008601 | 0.008794 | +0.000192 |
| fig_a ibm_kingston, regret vs ceiling 6 regret_window_mean, lo95 | 0.006190 | 0.006516 | +0.000326 |
| fig_a ibm_kingston, regret vs ceiling 6 regret_window_mean, hi95 | 0.011250 | 0.011361 | +0.000111 |
| fig_a ibm_kingston, regret vs ceiling 6 regret_std_adjusted, n | 300 | 315 | +15.000000 |
| fig_a ibm_kingston, regret vs ceiling 6 regret_std_adjusted, mean | 0.011508 | 0.011536 | +0.000028 |
| fig_a ibm_kingston, regret vs ceiling 6 regret_std_adjusted, lo95 | 0.008856 | 0.008986 | +0.000130 |
| fig_a ibm_kingston, regret vs ceiling 6 regret_std_adjusted, hi95 | 0.014321 | 0.014239 | -0.000083 |
| fig_a ibm_kingston, regret vs ceiling 6 regret_shrinkage, n | 300 | 315 | +15.000000 |
| fig_a ibm_kingston, regret vs ceiling 6 regret_shrinkage, mean | 0.015736 | 0.015061 | -0.000675 |
| fig_a ibm_kingston, regret vs ceiling 6 regret_shrinkage, lo95 | 0.008368 | 0.007912 | -0.000456 |
| fig_a ibm_kingston, regret vs ceiling 6 regret_shrinkage, hi95 | 0.026732 | 0.025514 | -0.001218 |
| fig_a ibm_kingston, regret vs ceiling 12 regret_random, n | 290 | 315 | +25.000000 |
| fig_a ibm_kingston, regret vs ceiling 12 regret_random, mean | 0.140283 | 0.141791 | +0.001507 |
| fig_a ibm_kingston, regret vs ceiling 12 regret_random, lo95 | 0.123376 | 0.126796 | +0.003419 |
| fig_a ibm_kingston, regret vs ceiling 12 regret_random, hi95 | 0.158077 | 0.158101 | +0.000024 |
| fig_a ibm_kingston, regret vs ceiling 12 regret_stale, n | 290 | 315 | +25.000000 |
| fig_a ibm_kingston, regret vs ceiling 12 regret_stale, mean | 0.024998 | 0.024133 | -0.000865 |
| fig_a ibm_kingston, regret vs ceiling 12 regret_stale, lo95 | 0.013451 | 0.013558 | +0.000107 |
| fig_a ibm_kingston, regret vs ceiling 12 regret_stale, hi95 | 0.042244 | 0.040038 | -0.002206 |
| fig_a ibm_kingston, regret vs ceiling 12 regret_window_mean, n | 290 | 315 | +25.000000 |
| fig_a ibm_kingston, regret vs ceiling 12 regret_window_mean, mean | 0.010830 | 0.011697 | +0.000867 |
| fig_a ibm_kingston, regret vs ceiling 12 regret_window_mean, lo95 | 0.008265 | 0.008896 | +0.000631 |
| fig_a ibm_kingston, regret vs ceiling 12 regret_window_mean, hi95 | 0.013524 | 0.014652 | +0.001128 |
| fig_a ibm_kingston, regret vs ceiling 12 regret_std_adjusted, n | 290 | 315 | +25.000000 |
| fig_a ibm_kingston, regret vs ceiling 12 regret_std_adjusted, mean | 0.015614 | 0.016160 | +0.000546 |
| fig_a ibm_kingston, regret vs ceiling 12 regret_std_adjusted, lo95 | 0.011399 | 0.011991 | +0.000592 |
| fig_a ibm_kingston, regret vs ceiling 12 regret_std_adjusted, hi95 | 0.021004 | 0.021501 | +0.000497 |
| fig_a ibm_kingston, regret vs ceiling 12 regret_shrinkage, n | 290 | 315 | +25.000000 |
| fig_a ibm_kingston, regret vs ceiling 12 regret_shrinkage, mean | 0.019553 | 0.019070 | -0.000484 |
| fig_a ibm_kingston, regret vs ceiling 12 regret_shrinkage, lo95 | 0.011208 | 0.011619 | +0.000410 |
| fig_a ibm_kingston, regret vs ceiling 12 regret_shrinkage, hi95 | 0.031836 | 0.030107 | -0.001729 |
| fig_a ibm_kingston, regret vs ceiling 24 regret_random, n | 275 | 305 | +30.000000 |
| fig_a ibm_kingston, regret vs ceiling 24 regret_random, mean | 0.143948 | 0.144770 | +0.000822 |
| fig_a ibm_kingston, regret vs ceiling 24 regret_random, lo95 | 0.128866 | 0.130151 | +0.001285 |
| fig_a ibm_kingston, regret vs ceiling 24 regret_random, hi95 | 0.158987 | 0.158311 | -0.000675 |
| fig_a ibm_kingston, regret vs ceiling 24 regret_stale, n | 275 | 305 | +30.000000 |
| fig_a ibm_kingston, regret vs ceiling 24 regret_stale, mean | 0.023687 | 0.023471 | -0.000216 |
| fig_a ibm_kingston, regret vs ceiling 24 regret_stale, lo95 | 0.012571 | 0.013350 | +0.000779 |
| fig_a ibm_kingston, regret vs ceiling 24 regret_stale, hi95 | 0.041504 | 0.039756 | -0.001748 |
| fig_a ibm_kingston, regret vs ceiling 24 regret_window_mean, n | 275 | 305 | +30.000000 |
| fig_a ibm_kingston, regret vs ceiling 24 regret_window_mean, mean | 0.010962 | 0.012550 | +0.001588 |
| fig_a ibm_kingston, regret vs ceiling 24 regret_window_mean, lo95 | 0.008634 | 0.009767 | +0.001133 |
| fig_a ibm_kingston, regret vs ceiling 24 regret_window_mean, hi95 | 0.013310 | 0.015425 | +0.002115 |
| fig_a ibm_kingston, regret vs ceiling 24 regret_std_adjusted, n | 275 | 305 | +30.000000 |
| fig_a ibm_kingston, regret vs ceiling 24 regret_std_adjusted, mean | 0.015356 | 0.016369 | +0.001013 |
| fig_a ibm_kingston, regret vs ceiling 24 regret_std_adjusted, lo95 | 0.011007 | 0.011939 | +0.000932 |
| fig_a ibm_kingston, regret vs ceiling 24 regret_std_adjusted, hi95 | 0.022085 | 0.022582 | +0.000496 |
| fig_a ibm_kingston, regret vs ceiling 24 regret_shrinkage, n | 275 | 305 | +30.000000 |
| fig_a ibm_kingston, regret vs ceiling 24 regret_shrinkage, mean | 0.018692 | 0.019100 | +0.000408 |
| fig_a ibm_kingston, regret vs ceiling 24 regret_shrinkage, lo95 | 0.011233 | 0.012162 | +0.000928 |
| fig_a ibm_kingston, regret vs ceiling 24 regret_shrinkage, hi95 | 0.029942 | 0.029821 | -0.000121 |
| fig_a ibm_kingston, regret vs ceiling 48 regret_random, n | 260 | 300 | +40.000000 |
| fig_a ibm_kingston, regret vs ceiling 48 regret_random, mean | 0.139721 | 0.142907 | +0.003186 |
| fig_a ibm_kingston, regret vs ceiling 48 regret_random, lo95 | 0.122293 | 0.126517 | +0.004224 |
| fig_a ibm_kingston, regret vs ceiling 48 regret_random, hi95 | 0.158599 | 0.159486 | +0.000886 |
| fig_a ibm_kingston, regret vs ceiling 48 regret_stale, n | 260 | 300 | +40.000000 |
| fig_a ibm_kingston, regret vs ceiling 48 regret_stale, mean | 0.036025 | 0.034853 | -0.001172 |
| fig_a ibm_kingston, regret vs ceiling 48 regret_stale, lo95 | 0.012028 | 0.013697 | +0.001669 |
| fig_a ibm_kingston, regret vs ceiling 48 regret_stale, hi95 | 0.071510 | 0.065882 | -0.005628 |
| fig_a ibm_kingston, regret vs ceiling 48 regret_window_mean, n | 260 | 300 | +40.000000 |
| fig_a ibm_kingston, regret vs ceiling 48 regret_window_mean, mean | 0.020811 | 0.021647 | +0.000836 |
| fig_a ibm_kingston, regret vs ceiling 48 regret_window_mean, lo95 | 0.007319 | 0.009331 | +0.002013 |
| fig_a ibm_kingston, regret vs ceiling 48 regret_window_mean, hi95 | 0.044603 | 0.042703 | -0.001901 |
| fig_a ibm_kingston, regret vs ceiling 48 regret_std_adjusted, n | 260 | 300 | +40.000000 |
| fig_a ibm_kingston, regret vs ceiling 48 regret_std_adjusted, mean | 0.032791 | 0.031771 | -0.001020 |
| fig_a ibm_kingston, regret vs ceiling 48 regret_std_adjusted, lo95 | 0.009534 | 0.011166 | +0.001632 |
| fig_a ibm_kingston, regret vs ceiling 48 regret_std_adjusted, hi95 | 0.077848 | 0.069503 | -0.008345 |
| fig_a ibm_kingston, regret vs ceiling 48 regret_shrinkage, n | 260 | 300 | +40.000000 |
| fig_a ibm_kingston, regret vs ceiling 48 regret_shrinkage, mean | 0.030511 | 0.030608 | +0.000097 |
| fig_a ibm_kingston, regret vs ceiling 48 regret_shrinkage, lo95 | 0.009591 | 0.012150 | +0.002559 |
| fig_a ibm_kingston, regret vs ceiling 48 regret_shrinkage, hi95 | 0.062989 | 0.057649 | -0.005340 |
| fig_a ibm_marrakesh, mean fidelity 1 random, n | 315 | 330 | +15.000000 |
| fig_a ibm_marrakesh, mean fidelity 1 random, mean | 0.728687 | 0.729371 | +0.000684 |
| fig_a ibm_marrakesh, mean fidelity 1 random, lo95 | 0.719478 | 0.720438 | +0.000960 |
| fig_a ibm_marrakesh, mean fidelity 1 random, hi95 | 0.737651 | 0.738028 | +0.000377 |
| fig_a ibm_marrakesh, mean fidelity 1 stale, n | 315 | 330 | +15.000000 |
| fig_a ibm_marrakesh, mean fidelity 1 stale, mean | 0.901809 | 0.902796 | +0.000986 |
| fig_a ibm_marrakesh, mean fidelity 1 stale, lo95 | 0.884830 | 0.886146 | +0.001317 |
| fig_a ibm_marrakesh, mean fidelity 1 stale, hi95 | 0.915073 | 0.915535 | +0.000462 |
| fig_a ibm_marrakesh, mean fidelity 1 window_mean, n | 315 | 330 | +15.000000 |
| fig_a ibm_marrakesh, mean fidelity 1 window_mean, mean | 0.894146 | 0.893878 | -0.000268 |
| fig_a ibm_marrakesh, mean fidelity 1 window_mean, lo95 | 0.882460 | 0.882537 | +0.000077 |
| fig_a ibm_marrakesh, mean fidelity 1 window_mean, hi95 | 0.904396 | 0.903384 | -0.001012 |
| fig_a ibm_marrakesh, mean fidelity 1 std_adjusted, n | 315 | 330 | +15.000000 |
| fig_a ibm_marrakesh, mean fidelity 1 std_adjusted, mean | 0.900039 | 0.899453 | -0.000586 |
| fig_a ibm_marrakesh, mean fidelity 1 std_adjusted, lo95 | 0.892259 | 0.892309 | +0.000051 |
| fig_a ibm_marrakesh, mean fidelity 1 std_adjusted, hi95 | 0.906813 | 0.906254 | -0.000560 |
| fig_a ibm_marrakesh, mean fidelity 1 shrinkage, n | 315 | 330 | +15.000000 |
| fig_a ibm_marrakesh, mean fidelity 1 shrinkage, mean | 0.904046 | 0.904801 | +0.000755 |
| fig_a ibm_marrakesh, mean fidelity 1 shrinkage, lo95 | 0.893587 | 0.894275 | +0.000688 |
| fig_a ibm_marrakesh, mean fidelity 1 shrinkage, hi95 | 0.912907 | 0.913162 | +0.000255 |
| fig_a ibm_marrakesh, mean fidelity 1 ceiling, n | 315 | 330 | +15.000000 |
| fig_a ibm_marrakesh, mean fidelity 1 ceiling, mean | 0.916962 | 0.917259 | +0.000298 |
| fig_a ibm_marrakesh, mean fidelity 1 ceiling, lo95 | 0.912800 | 0.913203 | +0.000403 |
| fig_a ibm_marrakesh, mean fidelity 1 ceiling, hi95 | 0.920987 | 0.921008 | +0.000020 |
| fig_a ibm_marrakesh, mean fidelity 3 random, n | 305 | 320 | +15.000000 |
| fig_a ibm_marrakesh, mean fidelity 3 random, mean | 0.716644 | 0.717524 | +0.000880 |
| fig_a ibm_marrakesh, mean fidelity 3 random, lo95 | 0.704184 | 0.705168 | +0.000985 |
| fig_a ibm_marrakesh, mean fidelity 3 random, hi95 | 0.728823 | 0.728998 | +0.000175 |
| fig_a ibm_marrakesh, mean fidelity 3 stale, n | 305 | 320 | +15.000000 |
| fig_a ibm_marrakesh, mean fidelity 3 stale, mean | 0.883630 | 0.885510 | +0.001879 |
| fig_a ibm_marrakesh, mean fidelity 3 stale, lo95 | 0.864370 | 0.867085 | +0.002715 |
| fig_a ibm_marrakesh, mean fidelity 3 stale, hi95 | 0.899749 | 0.901447 | +0.001698 |
| fig_a ibm_marrakesh, mean fidelity 3 window_mean, n | 305 | 320 | +15.000000 |
| fig_a ibm_marrakesh, mean fidelity 3 window_mean, mean | 0.893348 | 0.893055 | -0.000294 |
| fig_a ibm_marrakesh, mean fidelity 3 window_mean, lo95 | 0.880075 | 0.880261 | +0.000186 |
| fig_a ibm_marrakesh, mean fidelity 3 window_mean, hi95 | 0.904476 | 0.903735 | -0.000741 |
| fig_a ibm_marrakesh, mean fidelity 3 std_adjusted, n | 305 | 320 | +15.000000 |
| fig_a ibm_marrakesh, mean fidelity 3 std_adjusted, mean | 0.892838 | 0.892530 | -0.000309 |
| fig_a ibm_marrakesh, mean fidelity 3 std_adjusted, lo95 | 0.882521 | 0.881658 | -0.000863 |
| fig_a ibm_marrakesh, mean fidelity 3 std_adjusted, hi95 | 0.903156 | 0.902245 | -0.000910 |
| fig_a ibm_marrakesh, mean fidelity 3 shrinkage, n | 305 | 320 | +15.000000 |
| fig_a ibm_marrakesh, mean fidelity 3 shrinkage, mean | 0.890345 | 0.891753 | +0.001408 |
| fig_a ibm_marrakesh, mean fidelity 3 shrinkage, lo95 | 0.875539 | 0.877835 | +0.002296 |
| fig_a ibm_marrakesh, mean fidelity 3 shrinkage, hi95 | 0.903358 | 0.904870 | +0.001513 |
| fig_a ibm_marrakesh, mean fidelity 3 ceiling, n | 305 | 320 | +15.000000 |
| fig_a ibm_marrakesh, mean fidelity 3 ceiling, mean | 0.918666 | 0.918903 | +0.000237 |
| fig_a ibm_marrakesh, mean fidelity 3 ceiling, lo95 | 0.913478 | 0.914127 | +0.000649 |
| fig_a ibm_marrakesh, mean fidelity 3 ceiling, hi95 | 0.922968 | 0.923249 | +0.000281 |
| fig_a ibm_marrakesh, mean fidelity 6 random, n | 299 | 314 | +15.000000 |
| fig_a ibm_marrakesh, mean fidelity 6 random, mean | 0.726569 | 0.726422 | -0.000147 |
| fig_a ibm_marrakesh, mean fidelity 6 random, lo95 | 0.717860 | 0.718064 | +0.000204 |
| fig_a ibm_marrakesh, mean fidelity 6 random, hi95 | 0.735439 | 0.734767 | -0.000672 |
| fig_a ibm_marrakesh, mean fidelity 6 stale, n | 299 | 314 | +15.000000 |
| fig_a ibm_marrakesh, mean fidelity 6 stale, mean | 0.880701 | 0.882767 | +0.002067 |
| fig_a ibm_marrakesh, mean fidelity 6 stale, lo95 | 0.864504 | 0.866717 | +0.002213 |
| fig_a ibm_marrakesh, mean fidelity 6 stale, hi95 | 0.895106 | 0.897490 | +0.002384 |
| fig_a ibm_marrakesh, mean fidelity 6 window_mean, n | 299 | 314 | +15.000000 |
| fig_a ibm_marrakesh, mean fidelity 6 window_mean, mean | 0.897005 | 0.896526 | -0.000478 |
| fig_a ibm_marrakesh, mean fidelity 6 window_mean, lo95 | 0.889193 | 0.889001 | -0.000192 |
| fig_a ibm_marrakesh, mean fidelity 6 window_mean, hi95 | 0.904074 | 0.903358 | -0.000716 |
| fig_a ibm_marrakesh, mean fidelity 6 std_adjusted, n | 299 | 314 | +15.000000 |
| fig_a ibm_marrakesh, mean fidelity 6 std_adjusted, mean | 0.890422 | 0.890203 | -0.000219 |
| fig_a ibm_marrakesh, mean fidelity 6 std_adjusted, lo95 | 0.879306 | 0.879637 | +0.000332 |
| fig_a ibm_marrakesh, mean fidelity 6 std_adjusted, hi95 | 0.901102 | 0.900515 | -0.000587 |
| fig_a ibm_marrakesh, mean fidelity 6 shrinkage, n | 299 | 314 | +15.000000 |
| fig_a ibm_marrakesh, mean fidelity 6 shrinkage, mean | 0.885534 | 0.887226 | +0.001692 |
| fig_a ibm_marrakesh, mean fidelity 6 shrinkage, lo95 | 0.874188 | 0.875628 | +0.001440 |
| fig_a ibm_marrakesh, mean fidelity 6 shrinkage, hi95 | 0.896425 | 0.897603 | +0.001178 |
| fig_a ibm_marrakesh, mean fidelity 6 ceiling, n | 299 | 314 | +15.000000 |
| fig_a ibm_marrakesh, mean fidelity 6 ceiling, mean | 0.920285 | 0.920460 | +0.000176 |
| fig_a ibm_marrakesh, mean fidelity 6 ceiling, lo95 | 0.916502 | 0.916917 | +0.000415 |
| fig_a ibm_marrakesh, mean fidelity 6 ceiling, hi95 | 0.923839 | 0.923956 | +0.000117 |
| fig_a ibm_marrakesh, mean fidelity 12 random, n | 300 | 315 | +15.000000 |
| fig_a ibm_marrakesh, mean fidelity 12 random, mean | 0.714311 | 0.715468 | +0.001158 |
| fig_a ibm_marrakesh, mean fidelity 12 random, lo95 | 0.703826 | 0.705477 | +0.001651 |
| fig_a ibm_marrakesh, mean fidelity 12 random, hi95 | 0.724658 | 0.724655 | -0.000003 |
| fig_a ibm_marrakesh, mean fidelity 12 stale, n | 300 | 315 | +15.000000 |
| fig_a ibm_marrakesh, mean fidelity 12 stale, mean | 0.881245 | 0.882367 | +0.001122 |
| fig_a ibm_marrakesh, mean fidelity 12 stale, lo95 | 0.864833 | 0.866468 | +0.001635 |
| fig_a ibm_marrakesh, mean fidelity 12 stale, hi95 | 0.895146 | 0.895795 | +0.000649 |
| fig_a ibm_marrakesh, mean fidelity 12 window_mean, n | 300 | 315 | +15.000000 |
| fig_a ibm_marrakesh, mean fidelity 12 window_mean, mean | 0.882365 | 0.883422 | +0.001056 |
| fig_a ibm_marrakesh, mean fidelity 12 window_mean, lo95 | 0.855436 | 0.859299 | +0.003863 |
| fig_a ibm_marrakesh, mean fidelity 12 window_mean, hi95 | 0.900967 | 0.901434 | +0.000467 |
| fig_a ibm_marrakesh, mean fidelity 12 std_adjusted, n | 300 | 315 | +15.000000 |
| fig_a ibm_marrakesh, mean fidelity 12 std_adjusted, mean | 0.883817 | 0.884741 | +0.000924 |
| fig_a ibm_marrakesh, mean fidelity 12 std_adjusted, lo95 | 0.862956 | 0.864036 | +0.001080 |
| fig_a ibm_marrakesh, mean fidelity 12 std_adjusted, hi95 | 0.899990 | 0.900463 | +0.000473 |
| fig_a ibm_marrakesh, mean fidelity 12 shrinkage, n | 300 | 315 | +15.000000 |
| fig_a ibm_marrakesh, mean fidelity 12 shrinkage, mean | 0.880604 | 0.881812 | +0.001208 |
| fig_a ibm_marrakesh, mean fidelity 12 shrinkage, lo95 | 0.861115 | 0.863037 | +0.001923 |
| fig_a ibm_marrakesh, mean fidelity 12 shrinkage, hi95 | 0.896292 | 0.897005 | +0.000713 |
| fig_a ibm_marrakesh, mean fidelity 12 ceiling, n | 300 | 315 | +15.000000 |
| fig_a ibm_marrakesh, mean fidelity 12 ceiling, mean | 0.919173 | 0.919278 | +0.000105 |
| fig_a ibm_marrakesh, mean fidelity 12 ceiling, lo95 | 0.915334 | 0.915632 | +0.000298 |
| fig_a ibm_marrakesh, mean fidelity 12 ceiling, hi95 | 0.922507 | 0.922480 | -0.000027 |
| fig_a ibm_marrakesh, mean fidelity 24 random, n | 300 | 315 | +15.000000 |
| fig_a ibm_marrakesh, mean fidelity 24 random, mean | 0.710197 | 0.710989 | +0.000792 |
| fig_a ibm_marrakesh, mean fidelity 24 random, lo95 | 0.694119 | 0.695687 | +0.001568 |
| fig_a ibm_marrakesh, mean fidelity 24 random, hi95 | 0.723915 | 0.724185 | +0.000270 |
| fig_a ibm_marrakesh, mean fidelity 24 stale, n | 300 | 315 | +15.000000 |
| fig_a ibm_marrakesh, mean fidelity 24 stale, mean | 0.881965 | 0.882580 | +0.000614 |
| fig_a ibm_marrakesh, mean fidelity 24 stale, lo95 | 0.868375 | 0.869252 | +0.000877 |
| fig_a ibm_marrakesh, mean fidelity 24 stale, hi95 | 0.893419 | 0.893625 | +0.000206 |
| fig_a ibm_marrakesh, mean fidelity 24 window_mean, n | 300 | 315 | +15.000000 |
| fig_a ibm_marrakesh, mean fidelity 24 window_mean, mean | 0.884644 | 0.885941 | +0.001297 |
| fig_a ibm_marrakesh, mean fidelity 24 window_mean, lo95 | 0.869611 | 0.872125 | +0.002514 |
| fig_a ibm_marrakesh, mean fidelity 24 window_mean, hi95 | 0.898176 | 0.899103 | +0.000926 |
| fig_a ibm_marrakesh, mean fidelity 24 std_adjusted, n | 300 | 315 | +15.000000 |
| fig_a ibm_marrakesh, mean fidelity 24 std_adjusted, mean | 0.879821 | 0.881271 | +0.001450 |
| fig_a ibm_marrakesh, mean fidelity 24 std_adjusted, lo95 | 0.863390 | 0.864994 | +0.001604 |
| fig_a ibm_marrakesh, mean fidelity 24 std_adjusted, hi95 | 0.894167 | 0.894921 | +0.000754 |
| fig_a ibm_marrakesh, mean fidelity 24 shrinkage, n | 300 | 315 | +15.000000 |
| fig_a ibm_marrakesh, mean fidelity 24 shrinkage, mean | 0.875116 | 0.876322 | +0.001206 |
| fig_a ibm_marrakesh, mean fidelity 24 shrinkage, lo95 | 0.859798 | 0.861761 | +0.001962 |
| fig_a ibm_marrakesh, mean fidelity 24 shrinkage, hi95 | 0.889311 | 0.890740 | +0.001430 |
| fig_a ibm_marrakesh, mean fidelity 24 ceiling, n | 300 | 315 | +15.000000 |
| fig_a ibm_marrakesh, mean fidelity 24 ceiling, mean | 0.918501 | 0.918498 | -0.000003 |
| fig_a ibm_marrakesh, mean fidelity 24 ceiling, lo95 | 0.914239 | 0.914472 | +0.000233 |
| fig_a ibm_marrakesh, mean fidelity 24 ceiling, hi95 | 0.922306 | 0.922158 | -0.000147 |
| fig_a ibm_marrakesh, mean fidelity 48 random, n | 284 | 299 | +15.000000 |
| fig_a ibm_marrakesh, mean fidelity 48 random, mean | 0.713220 | 0.714226 | +0.001006 |
| fig_a ibm_marrakesh, mean fidelity 48 random, lo95 | 0.700593 | 0.702740 | +0.002146 |
| fig_a ibm_marrakesh, mean fidelity 48 random, hi95 | 0.724536 | 0.724927 | +0.000391 |
| fig_a ibm_marrakesh, mean fidelity 48 stale, n | 284 | 299 | +15.000000 |
| fig_a ibm_marrakesh, mean fidelity 48 stale, mean | 0.860803 | 0.856659 | -0.004144 |
| fig_a ibm_marrakesh, mean fidelity 48 stale, lo95 | 0.839739 | 0.835200 | -0.004539 |
| fig_a ibm_marrakesh, mean fidelity 48 stale, hi95 | 0.880093 | 0.876646 | -0.003447 |
| fig_a ibm_marrakesh, mean fidelity 48 window_mean, n | 284 | 299 | +15.000000 |
| fig_a ibm_marrakesh, mean fidelity 48 window_mean, mean | 0.886834 | 0.888168 | +0.001334 |
| fig_a ibm_marrakesh, mean fidelity 48 window_mean, lo95 | 0.876638 | 0.878558 | +0.001920 |
| fig_a ibm_marrakesh, mean fidelity 48 window_mean, hi95 | 0.896628 | 0.897870 | +0.001242 |
| fig_a ibm_marrakesh, mean fidelity 48 std_adjusted, n | 284 | 299 | +15.000000 |
| fig_a ibm_marrakesh, mean fidelity 48 std_adjusted, mean | 0.875528 | 0.877284 | +0.001756 |
| fig_a ibm_marrakesh, mean fidelity 48 std_adjusted, lo95 | 0.858771 | 0.861241 | +0.002470 |
| fig_a ibm_marrakesh, mean fidelity 48 std_adjusted, hi95 | 0.890037 | 0.891715 | +0.001678 |
| fig_a ibm_marrakesh, mean fidelity 48 shrinkage, n | 284 | 299 | +15.000000 |
| fig_a ibm_marrakesh, mean fidelity 48 shrinkage, mean | 0.865706 | 0.865256 | -0.000450 |
| fig_a ibm_marrakesh, mean fidelity 48 shrinkage, lo95 | 0.850049 | 0.849507 | -0.000542 |
| fig_a ibm_marrakesh, mean fidelity 48 shrinkage, hi95 | 0.881480 | 0.879633 | -0.001847 |
| fig_a ibm_marrakesh, mean fidelity 48 ceiling, n | 284 | 299 | +15.000000 |
| fig_a ibm_marrakesh, mean fidelity 48 ceiling, mean | 0.917770 | 0.918112 | +0.000342 |
| fig_a ibm_marrakesh, mean fidelity 48 ceiling, lo95 | 0.913477 | 0.914068 | +0.000591 |
| fig_a ibm_marrakesh, mean fidelity 48 ceiling, hi95 | 0.921974 | 0.922006 | +0.000031 |
| fig_a ibm_marrakesh, regret vs ceiling 1 regret_random, n | 315 | 330 | +15.000000 |
| fig_a ibm_marrakesh, regret vs ceiling 1 regret_random, mean | 0.188275 | 0.187889 | -0.000386 |
| fig_a ibm_marrakesh, regret vs ceiling 1 regret_random, lo95 | 0.180838 | 0.180688 | -0.000150 |
| fig_a ibm_marrakesh, regret vs ceiling 1 regret_random, hi95 | 0.196305 | 0.195350 | -0.000955 |
| fig_a ibm_marrakesh, regret vs ceiling 1 regret_stale, n | 315 | 330 | +15.000000 |
| fig_a ibm_marrakesh, regret vs ceiling 1 regret_stale, mean | 0.015153 | 0.014464 | -0.000689 |
| fig_a ibm_marrakesh, regret vs ceiling 1 regret_stale, lo95 | 0.003375 | 0.003383 | +0.000008 |
| fig_a ibm_marrakesh, regret vs ceiling 1 regret_stale, hi95 | 0.030157 | 0.029018 | -0.001140 |
| fig_a ibm_marrakesh, regret vs ceiling 1 regret_window_mean, n | 315 | 330 | +15.000000 |
| fig_a ibm_marrakesh, regret vs ceiling 1 regret_window_mean, mean | 0.022816 | 0.023382 | +0.000566 |
| fig_a ibm_marrakesh, regret vs ceiling 1 regret_window_mean, lo95 | 0.015073 | 0.015942 | +0.000869 |
| fig_a ibm_marrakesh, regret vs ceiling 1 regret_window_mean, hi95 | 0.031558 | 0.031871 | +0.000313 |
| fig_a ibm_marrakesh, regret vs ceiling 1 regret_std_adjusted, n | 315 | 330 | +15.000000 |
| fig_a ibm_marrakesh, regret vs ceiling 1 regret_std_adjusted, mean | 0.016922 | 0.017806 | +0.000884 |
| fig_a ibm_marrakesh, regret vs ceiling 1 regret_std_adjusted, lo95 | 0.012471 | 0.013259 | +0.000788 |
| fig_a ibm_marrakesh, regret vs ceiling 1 regret_std_adjusted, hi95 | 0.021338 | 0.022628 | +0.001291 |
| fig_a ibm_marrakesh, regret vs ceiling 1 regret_shrinkage, n | 315 | 330 | +15.000000 |
| fig_a ibm_marrakesh, regret vs ceiling 1 regret_shrinkage, mean | 0.012916 | 0.012458 | -0.000458 |
| fig_a ibm_marrakesh, regret vs ceiling 1 regret_shrinkage, lo95 | 0.006533 | 0.006179 | -0.000354 |
| fig_a ibm_marrakesh, regret vs ceiling 1 regret_shrinkage, hi95 | 0.020332 | 0.019911 | -0.000421 |
| fig_a ibm_marrakesh, regret vs ceiling 3 regret_random, n | 305 | 320 | +15.000000 |
| fig_a ibm_marrakesh, regret vs ceiling 3 regret_random, mean | 0.202022 | 0.201379 | -0.000643 |
| fig_a ibm_marrakesh, regret vs ceiling 3 regret_random, lo95 | 0.192107 | 0.191942 | -0.000165 |
| fig_a ibm_marrakesh, regret vs ceiling 3 regret_random, hi95 | 0.211637 | 0.210459 | -0.001178 |
| fig_a ibm_marrakesh, regret vs ceiling 3 regret_stale, n | 305 | 320 | +15.000000 |
| fig_a ibm_marrakesh, regret vs ceiling 3 regret_stale, mean | 0.035035 | 0.033393 | -0.001642 |
| fig_a ibm_marrakesh, regret vs ceiling 3 regret_stale, lo95 | 0.020808 | 0.019432 | -0.001376 |
| fig_a ibm_marrakesh, regret vs ceiling 3 regret_stale, hi95 | 0.051589 | 0.048922 | -0.002667 |
| fig_a ibm_marrakesh, regret vs ceiling 3 regret_window_mean, n | 305 | 320 | +15.000000 |
| fig_a ibm_marrakesh, regret vs ceiling 3 regret_window_mean, mean | 0.025318 | 0.025848 | +0.000531 |
| fig_a ibm_marrakesh, regret vs ceiling 3 regret_window_mean, lo95 | 0.017484 | 0.017646 | +0.000162 |
| fig_a ibm_marrakesh, regret vs ceiling 3 regret_window_mean, hi95 | 0.035418 | 0.034882 | -0.000536 |
| fig_a ibm_marrakesh, regret vs ceiling 3 regret_std_adjusted, n | 305 | 320 | +15.000000 |
| fig_a ibm_marrakesh, regret vs ceiling 3 regret_std_adjusted, mean | 0.025827 | 0.026373 | +0.000546 |
| fig_a ibm_marrakesh, regret vs ceiling 3 regret_std_adjusted, lo95 | 0.018952 | 0.019638 | +0.000686 |
| fig_a ibm_marrakesh, regret vs ceiling 3 regret_std_adjusted, hi95 | 0.032688 | 0.033154 | +0.000465 |
| fig_a ibm_marrakesh, regret vs ceiling 3 regret_shrinkage, n | 305 | 320 | +15.000000 |
| fig_a ibm_marrakesh, regret vs ceiling 3 regret_shrinkage, mean | 0.028321 | 0.027150 | -0.001171 |
| fig_a ibm_marrakesh, regret vs ceiling 3 regret_shrinkage, lo95 | 0.018072 | 0.017247 | -0.000825 |
| fig_a ibm_marrakesh, regret vs ceiling 3 regret_shrinkage, hi95 | 0.039465 | 0.037840 | -0.001626 |
| fig_a ibm_marrakesh, regret vs ceiling 6 regret_random, n | 299 | 314 | +15.000000 |
| fig_a ibm_marrakesh, regret vs ceiling 6 regret_random, mean | 0.193716 | 0.194038 | +0.000323 |
| fig_a ibm_marrakesh, regret vs ceiling 6 regret_random, lo95 | 0.185785 | 0.186347 | +0.000562 |
| fig_a ibm_marrakesh, regret vs ceiling 6 regret_random, hi95 | 0.201219 | 0.200946 | -0.000273 |
| fig_a ibm_marrakesh, regret vs ceiling 6 regret_stale, n | 299 | 314 | +15.000000 |
| fig_a ibm_marrakesh, regret vs ceiling 6 regret_stale, mean | 0.039584 | 0.037693 | -0.001891 |
| fig_a ibm_marrakesh, regret vs ceiling 6 regret_stale, lo95 | 0.025011 | 0.023316 | -0.001694 |
| fig_a ibm_marrakesh, regret vs ceiling 6 regret_stale, hi95 | 0.055257 | 0.052866 | -0.002392 |
| fig_a ibm_marrakesh, regret vs ceiling 6 regret_window_mean, n | 299 | 314 | +15.000000 |
| fig_a ibm_marrakesh, regret vs ceiling 6 regret_window_mean, mean | 0.023280 | 0.023934 | +0.000654 |
| fig_a ibm_marrakesh, regret vs ceiling 6 regret_window_mean, lo95 | 0.017654 | 0.018237 | +0.000583 |
| fig_a ibm_marrakesh, regret vs ceiling 6 regret_window_mean, hi95 | 0.028976 | 0.029601 | +0.000624 |
| fig_a ibm_marrakesh, regret vs ceiling 6 regret_std_adjusted, n | 299 | 314 | +15.000000 |
| fig_a ibm_marrakesh, regret vs ceiling 6 regret_std_adjusted, mean | 0.029863 | 0.030257 | +0.000394 |
| fig_a ibm_marrakesh, regret vs ceiling 6 regret_std_adjusted, lo95 | 0.020829 | 0.021345 | +0.000516 |
| fig_a ibm_marrakesh, regret vs ceiling 6 regret_std_adjusted, hi95 | 0.039033 | 0.038953 | -0.000081 |
| fig_a ibm_marrakesh, regret vs ceiling 6 regret_shrinkage, n | 299 | 314 | +15.000000 |
| fig_a ibm_marrakesh, regret vs ceiling 6 regret_shrinkage, mean | 0.034750 | 0.033235 | -0.001516 |
| fig_a ibm_marrakesh, regret vs ceiling 6 regret_shrinkage, lo95 | 0.024597 | 0.023354 | -0.001243 |
| fig_a ibm_marrakesh, regret vs ceiling 6 regret_shrinkage, hi95 | 0.044614 | 0.043612 | -0.001002 |
| fig_a ibm_marrakesh, regret vs ceiling 12 regret_random, n | 300 | 315 | +15.000000 |
| fig_a ibm_marrakesh, regret vs ceiling 12 regret_random, mean | 0.204862 | 0.203810 | -0.001052 |
| fig_a ibm_marrakesh, regret vs ceiling 12 regret_random, lo95 | 0.196633 | 0.195751 | -0.000882 |
| fig_a ibm_marrakesh, regret vs ceiling 12 regret_random, hi95 | 0.213235 | 0.212429 | -0.000806 |
| fig_a ibm_marrakesh, regret vs ceiling 12 regret_stale, n | 300 | 315 | +15.000000 |
| fig_a ibm_marrakesh, regret vs ceiling 12 regret_stale, mean | 0.037928 | 0.036911 | -0.001016 |
| fig_a ibm_marrakesh, regret vs ceiling 12 regret_stale, lo95 | 0.026110 | 0.025943 | -0.000167 |
| fig_a ibm_marrakesh, regret vs ceiling 12 regret_stale, hi95 | 0.051559 | 0.050303 | -0.001256 |
| fig_a ibm_marrakesh, regret vs ceiling 12 regret_window_mean, n | 300 | 315 | +15.000000 |
| fig_a ibm_marrakesh, regret vs ceiling 12 regret_window_mean, mean | 0.036807 | 0.035856 | -0.000951 |
| fig_a ibm_marrakesh, regret vs ceiling 12 regret_window_mean, lo95 | 0.019949 | 0.019632 | -0.000317 |
| fig_a ibm_marrakesh, regret vs ceiling 12 regret_window_mean, hi95 | 0.060615 | 0.057879 | -0.002736 |
| fig_a ibm_marrakesh, regret vs ceiling 12 regret_std_adjusted, n | 300 | 315 | +15.000000 |
| fig_a ibm_marrakesh, regret vs ceiling 12 regret_std_adjusted, mean | 0.035355 | 0.034537 | -0.000819 |
| fig_a ibm_marrakesh, regret vs ceiling 12 regret_std_adjusted, lo95 | 0.021893 | 0.021500 | -0.000394 |
| fig_a ibm_marrakesh, regret vs ceiling 12 regret_std_adjusted, hi95 | 0.053875 | 0.051459 | -0.002416 |
| fig_a ibm_marrakesh, regret vs ceiling 12 regret_shrinkage, n | 300 | 315 | +15.000000 |
| fig_a ibm_marrakesh, regret vs ceiling 12 regret_shrinkage, mean | 0.038569 | 0.037466 | -0.001103 |
| fig_a ibm_marrakesh, regret vs ceiling 12 regret_shrinkage, lo95 | 0.025220 | 0.024515 | -0.000705 |
| fig_a ibm_marrakesh, regret vs ceiling 12 regret_shrinkage, hi95 | 0.054978 | 0.052566 | -0.002411 |
| fig_a ibm_marrakesh, regret vs ceiling 24 regret_random, n | 300 | 315 | +15.000000 |
| fig_a ibm_marrakesh, regret vs ceiling 24 regret_random, mean | 0.208304 | 0.207509 | -0.000795 |
| fig_a ibm_marrakesh, regret vs ceiling 24 regret_random, lo95 | 0.196419 | 0.196101 | -0.000318 |
| fig_a ibm_marrakesh, regret vs ceiling 24 regret_random, hi95 | 0.221015 | 0.220012 | -0.001002 |
| fig_a ibm_marrakesh, regret vs ceiling 24 regret_stale, n | 300 | 315 | +15.000000 |
| fig_a ibm_marrakesh, regret vs ceiling 24 regret_stale, mean | 0.036536 | 0.035919 | -0.000617 |
| fig_a ibm_marrakesh, regret vs ceiling 24 regret_stale, lo95 | 0.026375 | 0.026264 | -0.000111 |
| fig_a ibm_marrakesh, regret vs ceiling 24 regret_stale, hi95 | 0.049213 | 0.047847 | -0.001366 |
| fig_a ibm_marrakesh, regret vs ceiling 24 regret_window_mean, n | 300 | 315 | +15.000000 |
| fig_a ibm_marrakesh, regret vs ceiling 24 regret_window_mean, mean | 0.033858 | 0.032558 | -0.001300 |
| fig_a ibm_marrakesh, regret vs ceiling 24 regret_window_mean, lo95 | 0.021943 | 0.021163 | -0.000780 |
| fig_a ibm_marrakesh, regret vs ceiling 24 regret_window_mean, hi95 | 0.046895 | 0.045294 | -0.001601 |
| fig_a ibm_marrakesh, regret vs ceiling 24 regret_std_adjusted, n | 300 | 315 | +15.000000 |
| fig_a ibm_marrakesh, regret vs ceiling 24 regret_std_adjusted, mean | 0.038680 | 0.037227 | -0.001453 |
| fig_a ibm_marrakesh, regret vs ceiling 24 regret_std_adjusted, lo95 | 0.026515 | 0.025112 | -0.001403 |
| fig_a ibm_marrakesh, regret vs ceiling 24 regret_std_adjusted, hi95 | 0.053448 | 0.051047 | -0.002401 |
| fig_a ibm_marrakesh, regret vs ceiling 24 regret_shrinkage, n | 300 | 315 | +15.000000 |
| fig_a ibm_marrakesh, regret vs ceiling 24 regret_shrinkage, mean | 0.043385 | 0.042177 | -0.001209 |
| fig_a ibm_marrakesh, regret vs ceiling 24 regret_shrinkage, lo95 | 0.030890 | 0.030618 | -0.000272 |
| fig_a ibm_marrakesh, regret vs ceiling 24 regret_shrinkage, hi95 | 0.056643 | 0.055122 | -0.001521 |
| fig_a ibm_marrakesh, regret vs ceiling 48 regret_random, n | 284 | 299 | +15.000000 |
| fig_a ibm_marrakesh, regret vs ceiling 48 regret_random, mean | 0.204550 | 0.203886 | -0.000664 |
| fig_a ibm_marrakesh, regret vs ceiling 48 regret_random, lo95 | 0.195592 | 0.195513 | -0.000079 |
| fig_a ibm_marrakesh, regret vs ceiling 48 regret_random, hi95 | 0.214626 | 0.213523 | -0.001103 |
| fig_a ibm_marrakesh, regret vs ceiling 48 regret_stale, n | 284 | 299 | +15.000000 |
| fig_a ibm_marrakesh, regret vs ceiling 48 regret_stale, mean | 0.056967 | 0.061453 | +0.004486 |
| fig_a ibm_marrakesh, regret vs ceiling 48 regret_stale, lo95 | 0.039631 | 0.043179 | +0.003548 |
| fig_a ibm_marrakesh, regret vs ceiling 48 regret_stale, hi95 | 0.076136 | 0.081434 | +0.005298 |
| fig_a ibm_marrakesh, regret vs ceiling 48 regret_window_mean, n | 284 | 299 | +15.000000 |
| fig_a ibm_marrakesh, regret vs ceiling 48 regret_window_mean, mean | 0.030936 | 0.029944 | -0.000992 |
| fig_a ibm_marrakesh, regret vs ceiling 48 regret_window_mean, lo95 | 0.022215 | 0.021326 | -0.000889 |
| fig_a ibm_marrakesh, regret vs ceiling 48 regret_window_mean, hi95 | 0.040229 | 0.038657 | -0.001571 |
| fig_a ibm_marrakesh, regret vs ceiling 48 regret_std_adjusted, n | 284 | 299 | +15.000000 |
| fig_a ibm_marrakesh, regret vs ceiling 48 regret_std_adjusted, mean | 0.042242 | 0.040828 | -0.001414 |
| fig_a ibm_marrakesh, regret vs ceiling 48 regret_std_adjusted, lo95 | 0.029169 | 0.027543 | -0.001625 |
| fig_a ibm_marrakesh, regret vs ceiling 48 regret_std_adjusted, hi95 | 0.057662 | 0.055314 | -0.002348 |
| fig_a ibm_marrakesh, regret vs ceiling 48 regret_shrinkage, n | 284 | 299 | +15.000000 |
| fig_a ibm_marrakesh, regret vs ceiling 48 regret_shrinkage, mean | 0.052064 | 0.052856 | +0.000792 |
| fig_a ibm_marrakesh, regret vs ceiling 48 regret_shrinkage, lo95 | 0.038339 | 0.040193 | +0.001854 |
| fig_a ibm_marrakesh, regret vs ceiling 48 regret_shrinkage, hi95 | 0.067150 | 0.067582 | +0.000432 |
| fig_b, 0 stale, n | 1205 | 1305 | +100.000000 |
| fig_b, 0 stale, lo95 | 0.000000 | 0.000000 | +0.000000 |
| fig_b, 0 stale, hi95 | 0.000000 | 0.000000 | +0.000000 |
| fig_b, 0 stale, mean_regret | 0.000000 | 0.000000 | +0.000000 |
| fig_b, 0 window_mean, n | 1205 | 1305 | +100.000000 |
| fig_b, 0 window_mean, lo95 | 0.005777 | 0.006346 | +0.000570 |
| fig_b, 0 window_mean, hi95 | 0.010004 | 0.011880 | +0.001876 |
| fig_b, 0 window_mean, mean_regret | 0.007592 | 0.008840 | +0.001248 |
| fig_b, 0 std_adjusted, n | 1205 | 1305 | +100.000000 |
| fig_b, 0 std_adjusted, lo95 | 0.006068 | 0.006509 | +0.000441 |
| fig_b, 0 std_adjusted, hi95 | 0.008883 | 0.011405 | +0.002522 |
| fig_b, 0 std_adjusted, mean_regret | 0.007400 | 0.008647 | +0.001247 |
| fig_b, 0 shrinkage, n | 1205 | 1305 | +100.000000 |
| fig_b, 0 shrinkage, lo95 | 0.001519 | 0.001577 | +0.000057 |
| fig_b, 0 shrinkage, hi95 | 0.003240 | 0.003141 | -0.000099 |
| fig_b, 0 shrinkage, mean_regret | 0.002367 | 0.002362 | -0.000004 |
| fig_b, 1 stale, n | 935 | 970 | +35.000000 |
| fig_b, 1 stale, lo95 | 0.019413 | 0.018439 | -0.000974 |
| fig_b, 1 stale, hi95 | 0.038214 | 0.036913 | -0.001301 |
| fig_b, 1 stale, mean_regret | 0.028853 | 0.028064 | -0.000788 |
| fig_b, 1 window_mean, n | 935 | 970 | +35.000000 |
| fig_b, 1 window_mean, lo95 | 0.012772 | 0.012658 | -0.000114 |
| fig_b, 1 window_mean, hi95 | 0.021358 | 0.021148 | -0.000210 |
| fig_b, 1 window_mean, mean_regret | 0.016743 | 0.016591 | -0.000151 |
| fig_b, 1 std_adjusted, n | 935 | 970 | +35.000000 |
| fig_b, 1 std_adjusted, lo95 | 0.015187 | 0.015138 | -0.000049 |
| fig_b, 1 std_adjusted, hi95 | 0.023589 | 0.023567 | -0.000022 |
| fig_b, 1 std_adjusted, mean_regret | 0.019464 | 0.019264 | -0.000200 |
| fig_b, 1 shrinkage, n | 935 | 970 | +35.000000 |
| fig_b, 1 shrinkage, lo95 | 0.017881 | 0.017178 | -0.000703 |
| fig_b, 1 shrinkage, hi95 | 0.029965 | 0.029161 | -0.000804 |
| fig_b, 1 shrinkage, mean_regret | 0.023802 | 0.023078 | -0.000724 |
| fig_b, 2 or more stale, n | 3148 | 3373 | +225.000000 |
| fig_b, 2 or more stale, lo95 | 0.021860 | 0.022070 | +0.000210 |
| fig_b, 2 or more stale, hi95 | 0.035874 | 0.034863 | -0.001011 |
| fig_b, 2 or more stale, mean_regret | 0.027955 | 0.027775 | -0.000180 |
| fig_b, 2 or more window_mean, n | 3148 | 3373 | +225.000000 |
| fig_b, 2 or more window_mean, lo95 | 0.015509 | 0.015406 | -0.000103 |
| fig_b, 2 or more window_mean, hi95 | 0.022133 | 0.021783 | -0.000350 |
| fig_b, 2 or more window_mean, mean_regret | 0.018599 | 0.018387 | -0.000213 |
| fig_b, 2 or more std_adjusted, n | 3148 | 3373 | +225.000000 |
| fig_b, 2 or more std_adjusted, lo95 | 0.019060 | 0.019063 | +0.000003 |
| fig_b, 2 or more std_adjusted, hi95 | 0.028833 | 0.028031 | -0.000802 |
| fig_b, 2 or more std_adjusted, mean_regret | 0.023509 | 0.022994 | -0.000515 |
| fig_b, 2 or more shrinkage, n | 3148 | 3373 | +225.000000 |
| fig_b, 2 or more shrinkage, lo95 | 0.019912 | 0.020076 | +0.000164 |
| fig_b, 2 or more shrinkage, hi95 | 0.030830 | 0.029586 | -0.001244 |
| fig_b, 2 or more shrinkage, mean_regret | 0.024862 | 0.024572 | -0.000290 |
| fig_c, ibm_fez 1, n | 315 | 325 | +10.000000 |
| fig_c, ibm_fez 1, lo95 | 0.000458 | 0.000452 | -0.000006 |
| fig_c, ibm_fez 1, hi95 | 0.001898 | 0.001865 | -0.000032 |
| fig_c, ibm_fez 1, mean_regret | 0.001142 | 0.001106 | -0.000035 |
| fig_c, ibm_fez 3, n | 315 | 325 | +10.000000 |
| fig_c, ibm_fez 3, lo95 | 0.001785 | 0.001761 | -0.000024 |
| fig_c, ibm_fez 3, hi95 | 0.005359 | 0.005208 | -0.000152 |
| fig_c, ibm_fez 3, mean_regret | 0.003416 | 0.003311 | -0.000105 |
| fig_c, ibm_fez 6, n | 310 | 325 | +15.000000 |
| fig_c, ibm_fez 6, lo95 | 0.005343 | 0.005715 | +0.000371 |
| fig_c, ibm_fez 6, hi95 | 0.013928 | 0.013870 | -0.000059 |
| fig_c, ibm_fez 6, mean_regret | 0.009359 | 0.009512 | +0.000153 |
| fig_c, ibm_fez 12, n | 290 | 315 | +25.000000 |
| fig_c, ibm_fez 12, lo95 | 0.009786 | 0.009989 | +0.000202 |
| fig_c, ibm_fez 12, hi95 | 0.019252 | 0.018686 | -0.000566 |
| fig_c, ibm_fez 12, mean_regret | 0.014319 | 0.014124 | -0.000195 |
| fig_c, ibm_fez 24, n | 280 | 310 | +30.000000 |
| fig_c, ibm_fez 24, lo95 | 0.007827 | 0.007882 | +0.000055 |
| fig_c, ibm_fez 24, hi95 | 0.019047 | 0.018481 | -0.000567 |
| fig_c, ibm_fez 24, mean_regret | 0.012437 | 0.012037 | -0.000400 |
| fig_c, ibm_fez 48, n | 250 | 290 | +40.000000 |
| fig_c, ibm_fez 48, lo95 | 0.008442 | 0.007915 | -0.000527 |
| fig_c, ibm_fez 48, hi95 | 0.021271 | 0.019768 | -0.001502 |
| fig_c, ibm_fez 48, mean_regret | 0.014230 | 0.013208 | -0.001022 |
| fig_c, ibm_kingston 1, n | 300 | 315 | +15.000000 |
| fig_c, ibm_kingston 1, lo95 | 0.000221 | 0.000230 | +0.000009 |
| fig_c, ibm_kingston 1, hi95 | 0.002792 | 0.002615 | -0.000178 |
| fig_c, ibm_kingston 1, mean_regret | 0.001295 | 0.001233 | -0.000062 |
| fig_c, ibm_kingston 3, n | 300 | 315 | +15.000000 |
| fig_c, ibm_kingston 3, lo95 | 0.003614 | 0.003472 | -0.000142 |
| fig_c, ibm_kingston 3, hi95 | 0.029652 | 0.028656 | -0.000995 |
| fig_c, ibm_kingston 3, mean_regret | 0.013280 | 0.012648 | -0.000632 |
| fig_c, ibm_kingston 6, n | 300 | 315 | +15.000000 |
| fig_c, ibm_kingston 6, lo95 | 0.009479 | 0.009175 | -0.000304 |
| fig_c, ibm_kingston 6, hi95 | 0.037410 | 0.036065 | -0.001345 |
| fig_c, ibm_kingston 6, mean_regret | 0.020453 | 0.019592 | -0.000861 |
| fig_c, ibm_kingston 12, n | 290 | 315 | +25.000000 |
| fig_c, ibm_kingston 12, lo95 | 0.013589 | 0.013578 | -0.000012 |
| fig_c, ibm_kingston 12, hi95 | 0.042665 | 0.039512 | -0.003153 |
| fig_c, ibm_kingston 12, mean_regret | 0.024998 | 0.024133 | -0.000865 |
| fig_c, ibm_kingston 24, n | 275 | 305 | +30.000000 |
| fig_c, ibm_kingston 24, lo95 | 0.012578 | 0.013334 | +0.000756 |
| fig_c, ibm_kingston 24, hi95 | 0.041341 | 0.039238 | -0.002103 |
| fig_c, ibm_kingston 24, mean_regret | 0.023687 | 0.023471 | -0.000216 |
| fig_c, ibm_kingston 48, n | 260 | 300 | +40.000000 |
| fig_c, ibm_kingston 48, lo95 | 0.011924 | 0.013811 | +0.001887 |
| fig_c, ibm_kingston 48, hi95 | 0.072424 | 0.066438 | -0.005985 |
| fig_c, ibm_kingston 48, mean_regret | 0.036025 | 0.034853 | -0.001172 |
| fig_c, ibm_marrakesh 1, n | 315 | 330 | +15.000000 |
| fig_c, ibm_marrakesh 1, lo95 | 0.003461 | 0.002953 | -0.000508 |
| fig_c, ibm_marrakesh 1, hi95 | 0.030453 | 0.029135 | -0.001318 |
| fig_c, ibm_marrakesh 1, mean_regret | 0.015153 | 0.014464 | -0.000689 |
| fig_c, ibm_marrakesh 3, n | 305 | 320 | +15.000000 |
| fig_c, ibm_marrakesh 3, lo95 | 0.020436 | 0.019844 | -0.000592 |
| fig_c, ibm_marrakesh 3, hi95 | 0.051444 | 0.049724 | -0.001720 |
| fig_c, ibm_marrakesh 3, mean_regret | 0.035035 | 0.033393 | -0.001642 |
| fig_c, ibm_marrakesh 6, n | 299 | 314 | +15.000000 |
| fig_c, ibm_marrakesh 6, lo95 | 0.024581 | 0.023686 | -0.000895 |
| fig_c, ibm_marrakesh 6, hi95 | 0.055526 | 0.053606 | -0.001920 |
| fig_c, ibm_marrakesh 6, mean_regret | 0.039584 | 0.037693 | -0.001891 |
| fig_c, ibm_marrakesh 12, n | 300 | 315 | +15.000000 |
| fig_c, ibm_marrakesh 12, lo95 | 0.026342 | 0.025836 | -0.000506 |
| fig_c, ibm_marrakesh 12, hi95 | 0.051724 | 0.050071 | -0.001653 |
| fig_c, ibm_marrakesh 12, mean_regret | 0.037928 | 0.036911 | -0.001016 |
| fig_c, ibm_marrakesh 24, n | 300 | 315 | +15.000000 |
| fig_c, ibm_marrakesh 24, lo95 | 0.026625 | 0.026102 | -0.000524 |
| fig_c, ibm_marrakesh 24, hi95 | 0.048660 | 0.048012 | -0.000648 |
| fig_c, ibm_marrakesh 24, mean_regret | 0.036536 | 0.035919 | -0.000617 |
| fig_c, ibm_marrakesh 48, n | 284 | 299 | +15.000000 |
| fig_c, ibm_marrakesh 48, lo95 | 0.039150 | 0.043468 | +0.004318 |
| fig_c, ibm_marrakesh 48, hi95 | 0.076747 | 0.081833 | +0.005086 |
| fig_c, ibm_marrakesh 48, mean_regret | 0.056967 | 0.061453 | +0.004486 |
| fig_d Comparison B, 6 h, n | 909 | 954 | +45.000000 |
| fig_d Comparison B, 6 h, lo95 | -0.007431 | -0.000166 | +0.007264 |
| fig_d Comparison B, 6 h, hi95 | 0.000265 | 0.006938 | +0.006674 |
| fig_d Comparison B, 6 h, mean_gain | -0.003447 | 0.003297 | +0.006744 |
| fig_d Comparison B, 24 h, n | 855 | 930 | +75.000000 |
| fig_d Comparison B, 24 h, lo95 | -0.002680 | -0.002750 | -0.000070 |
| fig_d Comparison B, 24 h, hi95 | 0.002953 | 0.002560 | -0.000393 |
| fig_d Comparison B, 24 h, mean_gain | 0.000030 | -0.000041 | -0.000071 |
| fig_d Comparison B, 6 and 24 h pooled, n | 1764 | 1884 | +120.000000 |
| fig_d Comparison B, 6 and 24 h pooled, lo95 | -0.004821 | -0.001391 | +0.003430 |
| fig_d Comparison B, 6 and 24 h pooled, hi95 | 0.001293 | 0.004533 | +0.003240 |
| fig_d Comparison B, 6 and 24 h pooled, mean_gain | -0.001762 | 0.001649 | +0.003411 |
| P1, 0 to 6, n | 310 | 310 | +0.000000 |
| P1, 0 to 6, days | 19 | 19 | +0.000000 |
| P1, 0 to 6, mean | 0.005765 | 0.005765 | +0.000000 |
| P1, 0 to 6, lo95 | 0.000480 | 0.000480 | +0.000000 |
| P1, 0 to 6, hi95 | 0.016444 | 0.016444 | +0.000000 |
| P1, 0 to 6, median_age_h | 3.897000 | 3.897000 | +0.000000 |
| P1, 6 to 12, n | 680 | 680 | +0.000000 |
| P1, 6 to 12, days | 20 | 20 | +0.000000 |
| P1, 6 to 12, mean | 0.012983 | 0.012983 | +0.000000 |
| P1, 6 to 12, lo95 | 0.006718 | 0.006718 | +0.000000 |
| P1, 6 to 12, hi95 | 0.021201 | 0.021201 | +0.000000 |
| P1, 6 to 12, median_age_h | 8.957000 | 8.957000 | +0.000000 |
| P1, 12 to 18, n | 820 | 825 | +5.000000 |
| P1, 12 to 18, days | 20 | 21 | +1.000000 |
| P1, 12 to 18, mean | 0.023495 | 0.023352 | -0.000143 |
| P1, 12 to 18, lo95 | 0.015630 | 0.015355 | -0.000275 |
| P1, 12 to 18, hi95 | 0.031731 | 0.031451 | -0.000280 |
| P1, 12 to 18, median_age_h | 15.266000 | 15.276000 | +0.010000 |
| P1, 18 to 24, n | 764 | 779 | +15.000000 |
| P1, 18 to 24, days | 21 | 21 | +0.000000 |
| P1, 18 to 24, mean | 0.016102 | 0.015792 | -0.000310 |
| P1, 18 to 24, lo95 | 0.010056 | 0.009703 | -0.000353 |
| P1, 18 to 24, hi95 | 0.023350 | 0.023460 | +0.000110 |
| P1, 18 to 24, median_age_h | 20.931000 | 20.960000 | +0.029000 |
| P1, 24 to 36, n | 1250 | 1330 | +80.000000 |
| P1, 24 to 36, days | 22 | 22 | +0.000000 |
| P1, 24 to 36, mean | 0.017026 | 0.016618 | -0.000408 |
| P1, 24 to 36, lo95 | 0.012906 | 0.012799 | -0.000107 |
| P1, 24 to 36, hi95 | 0.021021 | 0.020704 | -0.000317 |
| P1, 24 to 36, median_age_h | 27.963000 | 28.098000 | +0.135000 |
| P1, 36 to 48, n | 495 | 580 | +85.000000 |
| P1, 36 to 48, days | 21 | 21 | +0.000000 |
| P1, 36 to 48, mean | 0.030487 | 0.026762 | -0.003725 |
| P1, 36 to 48, lo95 | 0.017005 | 0.014601 | -0.002404 |
| P1, 36 to 48, hi95 | 0.050578 | 0.045034 | -0.005544 |
| P1, 36 to 48, median_age_h | 39.664000 | 40.674000 | +1.010000 |
| P1, 48 or more, n | 939 | 1114 | +175.000000 |
| P1, 48 or more, days | 21 | 21 | +0.000000 |
| P1, 48 or more, mean | 0.038608 | 0.036742 | -0.001866 |
| P1, 48 or more, lo95 | 0.024155 | 0.024408 | +0.000253 |
| P1, 48 or more, hi95 | 0.058011 | 0.054034 | -0.003977 |
| P1, 48 or more, median_age_h | 58.277000 | 59.594000 | +1.317000 |
| P1b, random 0 to 6, n | 310 | 310 | +0.000000 |
| P1b, random 0 to 6, days | 19 | 19 | +0.000000 |
| P1b, random 0 to 6, mean | 0.184880 | 0.184880 | +0.000000 |
| P1b, random 0 to 6, lo95 | 0.167075 | 0.166856 | -0.000219 |
| P1b, random 0 to 6, hi95 | 0.201117 | 0.201325 | +0.000208 |
| P1b, random 0 to 6, median_age_h | 3.897000 | 3.897000 | +0.000000 |
| P1b, random 6 to 12, n | 680 | 680 | +0.000000 |
| P1b, random 6 to 12, days | 20 | 20 | +0.000000 |
| P1b, random 6 to 12, mean | 0.187683 | 0.187683 | +0.000000 |
| P1b, random 6 to 12, lo95 | 0.174469 | 0.174700 | +0.000231 |
| P1b, random 6 to 12, hi95 | 0.199335 | 0.199405 | +0.000070 |
| P1b, random 6 to 12, median_age_h | 8.957000 | 8.957000 | +0.000000 |
| P1b, random 12 to 18, n | 820 | 825 | +5.000000 |
| P1b, random 12 to 18, days | 20 | 21 | +1.000000 |
| P1b, random 12 to 18, mean | 0.192457 | 0.192353 | -0.000104 |
| P1b, random 12 to 18, lo95 | 0.180550 | 0.180895 | +0.000345 |
| P1b, random 12 to 18, hi95 | 0.204598 | 0.204286 | -0.000312 |
| P1b, random 12 to 18, median_age_h | 15.266000 | 15.276000 | +0.010000 |
| P1b, random 18 to 24, n | 764 | 779 | +15.000000 |
| P1b, random 18 to 24, days | 21 | 21 | +0.000000 |
| P1b, random 18 to 24, mean | 0.189735 | 0.190227 | +0.000492 |
| P1b, random 18 to 24, lo95 | 0.179072 | 0.179653 | +0.000581 |
| P1b, random 18 to 24, hi95 | 0.200370 | 0.200402 | +0.000032 |
| P1b, random 18 to 24, median_age_h | 20.931000 | 20.960000 | +0.029000 |
| P1b, random 24 to 36, n | 1250 | 1330 | +80.000000 |
| P1b, random 24 to 36, days | 22 | 22 | +0.000000 |
| P1b, random 24 to 36, mean | 0.192444 | 0.193106 | +0.000662 |
| P1b, random 24 to 36, lo95 | 0.185303 | 0.186185 | +0.000882 |
| P1b, random 24 to 36, hi95 | 0.200894 | 0.200913 | +0.000019 |
| P1b, random 24 to 36, median_age_h | 27.963000 | 28.098000 | +0.135000 |
| P1b, random 36 to 48, n | 495 | 580 | +85.000000 |
| P1b, random 36 to 48, days | 21 | 21 | +0.000000 |
| P1b, random 36 to 48, mean | 0.196001 | 0.194455 | -0.001546 |
| P1b, random 36 to 48, lo95 | 0.187221 | 0.186797 | -0.000424 |
| P1b, random 36 to 48, hi95 | 0.205987 | 0.203209 | -0.002778 |
| P1b, random 36 to 48, median_age_h | 39.664000 | 40.674000 | +1.010000 |
| P1b, random 48 or more, n | 939 | 1114 | +175.000000 |
| P1b, random 48 or more, days | 21 | 21 | +0.000000 |
| P1b, random 48 or more, mean | 0.191980 | 0.190874 | -0.001106 |
| P1b, random 48 or more, lo95 | 0.186209 | 0.185793 | -0.000416 |
| P1b, random 48 or more, hi95 | 0.197851 | 0.196027 | -0.001824 |
| P1b, random 48 or more, median_age_h | 58.277000 | 59.594000 | +1.317000 |
| P1b, stale 0 to 6, n | 310 | 310 | +0.000000 |
| P1b, stale 0 to 6, days | 19 | 19 | +0.000000 |
| P1b, stale 0 to 6, mean | 0.005765 | 0.005765 | +0.000000 |
| P1b, stale 0 to 6, lo95 | 0.000551 | 0.000558 | +0.000007 |
| P1b, stale 0 to 6, hi95 | 0.016907 | 0.016850 | -0.000057 |
| P1b, stale 0 to 6, median_age_h | 3.897000 | 3.897000 | +0.000000 |
| P1b, stale 6 to 12, n | 680 | 680 | +0.000000 |
| P1b, stale 6 to 12, days | 20 | 20 | +0.000000 |
| P1b, stale 6 to 12, mean | 0.012983 | 0.012983 | +0.000000 |
| P1b, stale 6 to 12, lo95 | 0.006725 | 0.006723 | -0.000002 |
| P1b, stale 6 to 12, hi95 | 0.021441 | 0.021459 | +0.000018 |
| P1b, stale 6 to 12, median_age_h | 8.957000 | 8.957000 | +0.000000 |
| P1b, stale 12 to 18, n | 820 | 825 | +5.000000 |
| P1b, stale 12 to 18, days | 20 | 21 | +1.000000 |
| P1b, stale 12 to 18, mean | 0.023495 | 0.023352 | -0.000143 |
| P1b, stale 12 to 18, lo95 | 0.015414 | 0.015268 | -0.000146 |
| P1b, stale 12 to 18, hi95 | 0.031218 | 0.031411 | +0.000193 |
| P1b, stale 12 to 18, median_age_h | 15.266000 | 15.276000 | +0.010000 |
| P1b, stale 18 to 24, n | 764 | 779 | +15.000000 |
| P1b, stale 18 to 24, days | 21 | 21 | +0.000000 |
| P1b, stale 18 to 24, mean | 0.016102 | 0.015792 | -0.000310 |
| P1b, stale 18 to 24, lo95 | 0.010009 | 0.009889 | -0.000120 |
| P1b, stale 18 to 24, hi95 | 0.023726 | 0.023520 | -0.000206 |
| P1b, stale 18 to 24, median_age_h | 20.931000 | 20.960000 | +0.029000 |
| P1b, stale 24 to 36, n | 1250 | 1330 | +80.000000 |
| P1b, stale 24 to 36, days | 22 | 22 | +0.000000 |
| P1b, stale 24 to 36, mean | 0.017026 | 0.016618 | -0.000408 |
| P1b, stale 24 to 36, lo95 | 0.013095 | 0.012792 | -0.000303 |
| P1b, stale 24 to 36, hi95 | 0.021088 | 0.020688 | -0.000400 |
| P1b, stale 24 to 36, median_age_h | 27.963000 | 28.098000 | +0.135000 |
| P1b, stale 36 to 48, n | 495 | 580 | +85.000000 |
| P1b, stale 36 to 48, days | 21 | 21 | +0.000000 |
| P1b, stale 36 to 48, mean | 0.030487 | 0.026762 | -0.003725 |
| P1b, stale 36 to 48, lo95 | 0.017124 | 0.014475 | -0.002649 |
| P1b, stale 36 to 48, hi95 | 0.049601 | 0.044909 | -0.004692 |
| P1b, stale 36 to 48, median_age_h | 39.664000 | 40.674000 | +1.010000 |
| P1b, stale 48 or more, n | 939 | 1114 | +175.000000 |
| P1b, stale 48 or more, days | 21 | 21 | +0.000000 |
| P1b, stale 48 or more, mean | 0.038608 | 0.036742 | -0.001866 |
| P1b, stale 48 or more, lo95 | 0.024485 | 0.024450 | -0.000035 |
| P1b, stale 48 or more, hi95 | 0.059408 | 0.054015 | -0.005393 |
| P1b, stale 48 or more, median_age_h | 58.277000 | 59.594000 | +1.317000 |
| P1b, window_mean 0 to 6, n | 310 | 310 | +0.000000 |
| P1b, window_mean 0 to 6, days | 19 | 19 | +0.000000 |
| P1b, window_mean 0 to 6, mean | 0.011015 | 0.011015 | +0.000000 |
| P1b, window_mean 0 to 6, lo95 | 0.007642 | 0.007505 | -0.000137 |
| P1b, window_mean 0 to 6, hi95 | 0.014714 | 0.014793 | +0.000079 |
| P1b, window_mean 0 to 6, median_age_h | 3.897000 | 3.897000 | +0.000000 |
| P1b, window_mean 6 to 12, n | 680 | 680 | +0.000000 |
| P1b, window_mean 6 to 12, days | 20 | 20 | +0.000000 |
| P1b, window_mean 6 to 12, mean | 0.014319 | 0.014319 | +0.000000 |
| P1b, window_mean 6 to 12, lo95 | 0.008989 | 0.009019 | +0.000030 |
| P1b, window_mean 6 to 12, hi95 | 0.020955 | 0.020907 | -0.000048 |
| P1b, window_mean 6 to 12, median_age_h | 8.957000 | 8.957000 | +0.000000 |
| P1b, window_mean 12 to 18, n | 820 | 825 | +5.000000 |
| P1b, window_mean 12 to 18, days | 20 | 21 | +1.000000 |
| P1b, window_mean 12 to 18, mean | 0.014128 | 0.014089 | -0.000039 |
| P1b, window_mean 12 to 18, lo95 | 0.010738 | 0.010780 | +0.000042 |
| P1b, window_mean 12 to 18, hi95 | 0.017601 | 0.017373 | -0.000228 |
| P1b, window_mean 12 to 18, median_age_h | 15.266000 | 15.276000 | +0.010000 |
| P1b, window_mean 18 to 24, n | 764 | 779 | +15.000000 |
| P1b, window_mean 18 to 24, days | 21 | 21 | +0.000000 |
| P1b, window_mean 18 to 24, mean | 0.015125 | 0.014967 | -0.000158 |
| P1b, window_mean 18 to 24, lo95 | 0.009083 | 0.008984 | -0.000099 |
| P1b, window_mean 18 to 24, hi95 | 0.025263 | 0.024555 | -0.000708 |
| P1b, window_mean 18 to 24, median_age_h | 20.931000 | 20.960000 | +0.029000 |
| P1b, window_mean 24 to 36, n | 1250 | 1330 | +80.000000 |
| P1b, window_mean 24 to 36, days | 22 | 22 | +0.000000 |
| P1b, window_mean 24 to 36, mean | 0.013310 | 0.013533 | +0.000223 |
| P1b, window_mean 24 to 36, lo95 | 0.010214 | 0.010581 | +0.000367 |
| P1b, window_mean 24 to 36, hi95 | 0.016566 | 0.016764 | +0.000198 |
| P1b, window_mean 24 to 36, median_age_h | 27.963000 | 28.098000 | +0.135000 |
| P1b, window_mean 36 to 48, n | 495 | 580 | +85.000000 |
| P1b, window_mean 36 to 48, days | 21 | 21 | +0.000000 |
| P1b, window_mean 36 to 48, mean | 0.018398 | 0.019440 | +0.001042 |
| P1b, window_mean 36 to 48, lo95 | 0.013221 | 0.014591 | +0.001370 |
| P1b, window_mean 36 to 48, hi95 | 0.024280 | 0.024734 | +0.000454 |
| P1b, window_mean 36 to 48, median_age_h | 39.664000 | 40.674000 | +1.010000 |
| P1b, window_mean 48 or more, n | 939 | 1114 | +175.000000 |
| P1b, window_mean 48 or more, days | 21 | 21 | +0.000000 |
| P1b, window_mean 48 or more, mean | 0.022575 | 0.021382 | -0.001193 |
| P1b, window_mean 48 or more, lo95 | 0.016941 | 0.016578 | -0.000363 |
| P1b, window_mean 48 or more, hi95 | 0.030009 | 0.027912 | -0.002097 |
| P1b, window_mean 48 or more, median_age_h | 58.277000 | 59.594000 | +1.317000 |
| P1b, std_adjusted 0 to 6, n | 310 | 310 | +0.000000 |
| P1b, std_adjusted 0 to 6, days | 19 | 19 | +0.000000 |
| P1b, std_adjusted 0 to 6, mean | 0.011070 | 0.011070 | +0.000000 |
| P1b, std_adjusted 0 to 6, lo95 | 0.006568 | 0.006623 | +0.000055 |
| P1b, std_adjusted 0 to 6, hi95 | 0.015184 | 0.015152 | -0.000032 |
| P1b, std_adjusted 0 to 6, median_age_h | 3.897000 | 3.897000 | +0.000000 |
| P1b, std_adjusted 6 to 12, n | 680 | 680 | +0.000000 |
| P1b, std_adjusted 6 to 12, days | 20 | 20 | +0.000000 |
| P1b, std_adjusted 6 to 12, mean | 0.014845 | 0.014845 | +0.000000 |
| P1b, std_adjusted 6 to 12, lo95 | 0.009949 | 0.009960 | +0.000011 |
| P1b, std_adjusted 6 to 12, hi95 | 0.020804 | 0.020682 | -0.000122 |
| P1b, std_adjusted 6 to 12, median_age_h | 8.957000 | 8.957000 | +0.000000 |
| P1b, std_adjusted 12 to 18, n | 820 | 825 | +5.000000 |
| P1b, std_adjusted 12 to 18, days | 20 | 21 | +1.000000 |
| P1b, std_adjusted 12 to 18, mean | 0.015657 | 0.015587 | -0.000070 |
| P1b, std_adjusted 12 to 18, lo95 | 0.012449 | 0.012384 | -0.000065 |
| P1b, std_adjusted 12 to 18, hi95 | 0.019004 | 0.018921 | -0.000083 |
| P1b, std_adjusted 12 to 18, median_age_h | 15.266000 | 15.276000 | +0.010000 |
| P1b, std_adjusted 18 to 24, n | 764 | 779 | +15.000000 |
| P1b, std_adjusted 18 to 24, days | 21 | 21 | +0.000000 |
| P1b, std_adjusted 18 to 24, mean | 0.017396 | 0.017147 | -0.000249 |
| P1b, std_adjusted 18 to 24, lo95 | 0.012207 | 0.012119 | -0.000088 |
| P1b, std_adjusted 18 to 24, hi95 | 0.024190 | 0.024181 | -0.000009 |
| P1b, std_adjusted 18 to 24, median_age_h | 20.931000 | 20.960000 | +0.029000 |
| P1b, std_adjusted 24 to 36, n | 1250 | 1330 | +80.000000 |
| P1b, std_adjusted 24 to 36, days | 22 | 22 | +0.000000 |
| P1b, std_adjusted 24 to 36, mean | 0.017563 | 0.017583 | +0.000020 |
| P1b, std_adjusted 24 to 36, lo95 | 0.013658 | 0.013955 | +0.000297 |
| P1b, std_adjusted 24 to 36, hi95 | 0.021746 | 0.021560 | -0.000186 |
| P1b, std_adjusted 24 to 36, median_age_h | 27.963000 | 28.098000 | +0.135000 |
| P1b, std_adjusted 36 to 48, n | 495 | 580 | +85.000000 |
| P1b, std_adjusted 36 to 48, days | 21 | 21 | +0.000000 |
| P1b, std_adjusted 36 to 48, mean | 0.020953 | 0.021821 | +0.000868 |
| P1b, std_adjusted 36 to 48, lo95 | 0.016407 | 0.017528 | +0.001121 |
| P1b, std_adjusted 36 to 48, hi95 | 0.026259 | 0.026413 | +0.000154 |
| P1b, std_adjusted 36 to 48, median_age_h | 39.664000 | 40.674000 | +1.010000 |
| P1b, std_adjusted 48 or more, n | 939 | 1114 | +175.000000 |
| P1b, std_adjusted 48 or more, days | 21 | 21 | +0.000000 |
| P1b, std_adjusted 48 or more, mean | 0.030817 | 0.028312 | -0.002505 |
| P1b, std_adjusted 48 or more, lo95 | 0.021045 | 0.020316 | -0.000729 |
| P1b, std_adjusted 48 or more, hi95 | 0.045244 | 0.041116 | -0.004128 |
| P1b, std_adjusted 48 or more, median_age_h | 58.277000 | 59.594000 | +1.317000 |
| P1b, shrinkage 0 to 6, n | 310 | 310 | +0.000000 |
| P1b, shrinkage 0 to 6, days | 19 | 19 | +0.000000 |
| P1b, shrinkage 0 to 6, mean | 0.005724 | 0.005724 | +0.000000 |
| P1b, shrinkage 0 to 6, lo95 | 0.002291 | 0.002356 | +0.000065 |
| P1b, shrinkage 0 to 6, hi95 | 0.011101 | 0.011198 | +0.000097 |
| P1b, shrinkage 0 to 6, median_age_h | 3.897000 | 3.897000 | +0.000000 |
| P1b, shrinkage 6 to 12, n | 680 | 680 | +0.000000 |
| P1b, shrinkage 6 to 12, days | 20 | 20 | +0.000000 |
| P1b, shrinkage 6 to 12, mean | 0.012083 | 0.012083 | +0.000000 |
| P1b, shrinkage 6 to 12, lo95 | 0.007494 | 0.007451 | -0.000043 |
| P1b, shrinkage 6 to 12, hi95 | 0.017669 | 0.017689 | +0.000020 |
| P1b, shrinkage 6 to 12, median_age_h | 8.957000 | 8.957000 | +0.000000 |
| P1b, shrinkage 12 to 18, n | 820 | 825 | +5.000000 |
| P1b, shrinkage 12 to 18, days | 20 | 21 | +1.000000 |
| P1b, shrinkage 12 to 18, mean | 0.019062 | 0.018971 | -0.000091 |
| P1b, shrinkage 12 to 18, lo95 | 0.014490 | 0.014535 | +0.000045 |
| P1b, shrinkage 12 to 18, hi95 | 0.023405 | 0.023129 | -0.000276 |
| P1b, shrinkage 12 to 18, median_age_h | 15.266000 | 15.276000 | +0.010000 |
| P1b, shrinkage 18 to 24, n | 764 | 779 | +15.000000 |
| P1b, shrinkage 18 to 24, days | 21 | 21 | +0.000000 |
| P1b, shrinkage 18 to 24, mean | 0.015445 | 0.015213 | -0.000232 |
| P1b, shrinkage 18 to 24, lo95 | 0.010163 | 0.010178 | +0.000015 |
| P1b, shrinkage 18 to 24, hi95 | 0.022073 | 0.021795 | -0.000278 |
| P1b, shrinkage 18 to 24, median_age_h | 20.931000 | 20.960000 | +0.029000 |
| P1b, shrinkage 24 to 36, n | 1250 | 1330 | +80.000000 |
| P1b, shrinkage 24 to 36, days | 22 | 22 | +0.000000 |
| P1b, shrinkage 24 to 36, mean | 0.015905 | 0.015562 | -0.000343 |
| P1b, shrinkage 24 to 36, lo95 | 0.012147 | 0.011938 | -0.000209 |
| P1b, shrinkage 24 to 36, hi95 | 0.019822 | 0.019525 | -0.000297 |
| P1b, shrinkage 24 to 36, median_age_h | 27.963000 | 28.098000 | +0.135000 |
| P1b, shrinkage 36 to 48, n | 495 | 580 | +85.000000 |
| P1b, shrinkage 36 to 48, days | 21 | 21 | +0.000000 |
| P1b, shrinkage 36 to 48, mean | 0.027548 | 0.024622 | -0.002926 |
| P1b, shrinkage 36 to 48, lo95 | 0.016954 | 0.014966 | -0.001988 |
| P1b, shrinkage 36 to 48, hi95 | 0.042064 | 0.038536 | -0.003528 |
| P1b, shrinkage 36 to 48, median_age_h | 39.664000 | 40.674000 | +1.010000 |
| P1b, shrinkage 48 or more, n | 939 | 1114 | +175.000000 |
| P1b, shrinkage 48 or more, days | 21 | 21 | +0.000000 |
| P1b, shrinkage 48 or more, mean | 0.034293 | 0.031998 | -0.002295 |
| P1b, shrinkage 48 or more, lo95 | 0.023125 | 0.022954 | -0.000171 |
| P1b, shrinkage 48 or more, hi95 | 0.048745 | 0.043585 | -0.005160 |
| P1b, shrinkage 48 or more, median_age_h | 58.277000 | 59.594000 | +1.317000 |
| P2, 0 to 6, n | 950 | 960 | +10.000000 |
| P2, 0 to 6, days | 22 | 22 | +0.000000 |
| P2, 0 to 6, mean | 0.009058 | 0.008964 | -0.000094 |
| P2, 0 to 6, lo95 | 0.005215 | 0.005179 | -0.000036 |
| P2, 0 to 6, hi95 | 0.013765 | 0.013773 | +0.000008 |
| P2, 0 to 6, median_age_h | 4.173000 | 4.154000 | -0.019000 |
| P2, 6 to 12, n | 1404 | 1414 | +10.000000 |
| P2, 6 to 12, days | 22 | 22 | +0.000000 |
| P2, 6 to 12, mean | 0.019091 | 0.019004 | -0.000087 |
| P2, 6 to 12, lo95 | 0.011811 | 0.011586 | -0.000225 |
| P2, 6 to 12, hi95 | 0.027672 | 0.027655 | -0.000017 |
| P2, 6 to 12, median_age_h | 8.383000 | 8.383000 | +0.000000 |
| P2, 12 to 18, n | 920 | 945 | +25.000000 |
| P2, 12 to 18, days | 21 | 21 | +0.000000 |
| P2, 12 to 18, mean | 0.024094 | 0.023751 | -0.000343 |
| P2, 12 to 18, lo95 | 0.017847 | 0.017646 | -0.000201 |
| P2, 12 to 18, hi95 | 0.031250 | 0.030828 | -0.000422 |
| P2, 12 to 18, median_age_h | 14.042000 | 14.079000 | +0.037000 |
| P2, 18 to 24, n | 280 | 315 | +35.000000 |
| P2, 18 to 24, days | 20 | 20 | +0.000000 |
| P2, 18 to 24, mean | 0.024125 | 0.021654 | -0.002471 |
| P2, 18 to 24, lo95 | 0.014662 | 0.012584 | -0.002078 |
| P2, 18 to 24, hi95 | 0.035824 | 0.033098 | -0.002726 |
| P2, 18 to 24, median_age_h | 19.791000 | 19.840000 | +0.049000 |
| P2, 24 to 36, n | 895 | 1025 | +130.000000 |
| P2, 24 to 36, days | 21 | 21 | +0.000000 |
| P2, 24 to 36, mean | 0.022879 | 0.020791 | -0.002088 |
| P2, 24 to 36, lo95 | 0.016720 | 0.014628 | -0.002092 |
| P2, 24 to 36, hi95 | 0.029944 | 0.028296 | -0.001648 |
| P2, 24 to 36, median_age_h | 27.582000 | 27.638000 | +0.056000 |
| P2, 36 to 48, n | 40 | 75 | +35.000000 |
| P2, 36 to 48, days | 4 | 5 | +1.000000 |
| P2, 36 to 48, mean | 0.024415 | 0.020495 | -0.003920 |
| P2, 36 to 48, lo95 | 0.010830 | 0.013859 | +0.003029 |
| P2, 36 to 48, hi95 | 0.047057 | 0.031270 | -0.015787 |
| P2, 36 to 48, median_age_h | 42.579000 | 40.163000 | -2.416000 |
| P2, 48 or more, n | 799 | 914 | +115.000000 |
| P2, 48 or more, days | 19 | 20 | +1.000000 |
| P2, 48 or more, mean | 0.036540 | 0.036452 | -0.000088 |
| P2, 48 or more, lo95 | 0.025178 | 0.026113 | +0.000935 |
| P2, 48 or more, hi95 | 0.050004 | 0.048887 | -0.001117 |
| P2, 48 or more, median_age_h | 51.941000 | 51.941000 | +0.000000 |
| P4, ibm_fez 1, n | 315 | 325 | +10.000000 |
| P4, ibm_fez 1, days | 22 | 22 | +0.000000 |
| P4, ibm_fez 1, lo95 | 0.000458 | 0.000428 | -0.000030 |
| P4, ibm_fez 1, hi95 | 0.001884 | 0.001906 | +0.000022 |
| P4, ibm_fez 1, mean_regret | 0.001142 | 0.001106 | -0.000036 |
| P4, ibm_fez 3, n | 315 | 325 | +10.000000 |
| P4, ibm_fez 3, days | 22 | 22 | +0.000000 |
| P4, ibm_fez 3, lo95 | 0.001814 | 0.001748 | -0.000066 |
| P4, ibm_fez 3, hi95 | 0.005568 | 0.005216 | -0.000352 |
| P4, ibm_fez 3, mean_regret | 0.003416 | 0.003311 | -0.000105 |
| P4, ibm_fez 6, n | 310 | 325 | +15.000000 |
| P4, ibm_fez 6, days | 22 | 22 | +0.000000 |
| P4, ibm_fez 6, lo95 | 0.005298 | 0.005711 | +0.000413 |
| P4, ibm_fez 6, hi95 | 0.014086 | 0.013891 | -0.000195 |
| P4, ibm_fez 6, mean_regret | 0.009359 | 0.009512 | +0.000153 |
| P4, ibm_fez 12, n | 290 | 315 | +25.000000 |
| P4, ibm_fez 12, days | 20 | 21 | +1.000000 |
| P4, ibm_fez 12, lo95 | 0.009849 | 0.009931 | +0.000082 |
| P4, ibm_fez 12, hi95 | 0.019517 | 0.018847 | -0.000670 |
| P4, ibm_fez 12, mean_regret | 0.014319 | 0.014124 | -0.000195 |
| P4, ibm_fez 24, n | 280 | 310 | +30.000000 |
| P4, ibm_fez 24, days | 20 | 21 | +1.000000 |
| P4, ibm_fez 24, lo95 | 0.007813 | 0.007932 | +0.000119 |
| P4, ibm_fez 24, hi95 | 0.019266 | 0.017901 | -0.001365 |
| P4, ibm_fez 24, mean_regret | 0.012437 | 0.012037 | -0.000400 |
| P4, ibm_fez 48, n | 250 | 290 | +40.000000 |
| P4, ibm_fez 48, days | 18 | 20 | +2.000000 |
| P4, ibm_fez 48, lo95 | 0.008474 | 0.007897 | -0.000577 |
| P4, ibm_fez 48, hi95 | 0.021356 | 0.019792 | -0.001564 |
| P4, ibm_fez 48, mean_regret | 0.014230 | 0.013208 | -0.001022 |
| P4, ibm_kingston 1, n | 300 | 315 | +15.000000 |
| P4, ibm_kingston 1, days | 21 | 21 | +0.000000 |
| P4, ibm_kingston 1, lo95 | 0.000220 | 0.000217 | -0.000003 |
| P4, ibm_kingston 1, hi95 | 0.002810 | 0.002603 | -0.000207 |
| P4, ibm_kingston 1, mean_regret | 0.001295 | 0.001233 | -0.000062 |
| P4, ibm_kingston 3, n | 300 | 315 | +15.000000 |
| P4, ibm_kingston 3, days | 21 | 21 | +0.000000 |
| P4, ibm_kingston 3, lo95 | 0.003596 | 0.003389 | -0.000207 |
| P4, ibm_kingston 3, hi95 | 0.029709 | 0.027931 | -0.001778 |
| P4, ibm_kingston 3, mean_regret | 0.013280 | 0.012648 | -0.000632 |
| P4, ibm_kingston 6, n | 300 | 315 | +15.000000 |
| P4, ibm_kingston 6, days | 21 | 21 | +0.000000 |
| P4, ibm_kingston 6, lo95 | 0.009582 | 0.009270 | -0.000312 |
| P4, ibm_kingston 6, hi95 | 0.036926 | 0.035601 | -0.001325 |
| P4, ibm_kingston 6, mean_regret | 0.020453 | 0.019592 | -0.000861 |
| P4, ibm_kingston 12, n | 290 | 315 | +25.000000 |
| P4, ibm_kingston 12, days | 20 | 21 | +1.000000 |
| P4, ibm_kingston 12, lo95 | 0.013619 | 0.013515 | -0.000104 |
| P4, ibm_kingston 12, hi95 | 0.042959 | 0.040510 | -0.002449 |
| P4, ibm_kingston 12, mean_regret | 0.024998 | 0.024133 | -0.000865 |
| P4, ibm_kingston 24, n | 275 | 305 | +30.000000 |
| P4, ibm_kingston 24, days | 20 | 21 | +1.000000 |
| P4, ibm_kingston 24, lo95 | 0.012492 | 0.013406 | +0.000914 |
| P4, ibm_kingston 24, hi95 | 0.042126 | 0.039437 | -0.002689 |
| P4, ibm_kingston 24, mean_regret | 0.023687 | 0.023471 | -0.000216 |
| P4, ibm_kingston 48, n | 260 | 300 | +40.000000 |
| P4, ibm_kingston 48, days | 18 | 20 | +2.000000 |
| P4, ibm_kingston 48, lo95 | 0.011898 | 0.013785 | +0.001887 |
| P4, ibm_kingston 48, hi95 | 0.071027 | 0.064269 | -0.006758 |
| P4, ibm_kingston 48, mean_regret | 0.036025 | 0.034853 | -0.001172 |
| P4, ibm_marrakesh 1, n | 315 | 330 | +15.000000 |
| P4, ibm_marrakesh 1, days | 21 | 22 | +1.000000 |
| P4, ibm_marrakesh 1, lo95 | 0.003333 | 0.003301 | -0.000032 |
| P4, ibm_marrakesh 1, hi95 | 0.029944 | 0.029110 | -0.000834 |
| P4, ibm_marrakesh 1, mean_regret | 0.015153 | 0.014464 | -0.000689 |
| P4, ibm_marrakesh 3, n | 305 | 320 | +15.000000 |
| P4, ibm_marrakesh 3, days | 21 | 22 | +1.000000 |
| P4, ibm_marrakesh 3, lo95 | 0.020166 | 0.019266 | -0.000900 |
| P4, ibm_marrakesh 3, hi95 | 0.051355 | 0.049405 | -0.001950 |
| P4, ibm_marrakesh 3, mean_regret | 0.035035 | 0.033393 | -0.001642 |
| P4, ibm_marrakesh 6, n | 299 | 314 | +15.000000 |
| P4, ibm_marrakesh 6, days | 20 | 21 | +1.000000 |
| P4, ibm_marrakesh 6, lo95 | 0.025653 | 0.023733 | -0.001920 |
| P4, ibm_marrakesh 6, hi95 | 0.055539 | 0.053511 | -0.002028 |
| P4, ibm_marrakesh 6, mean_regret | 0.039584 | 0.037693 | -0.001891 |
| P4, ibm_marrakesh 12, n | 300 | 315 | +15.000000 |
| P4, ibm_marrakesh 12, days | 20 | 21 | +1.000000 |
| P4, ibm_marrakesh 12, lo95 | 0.026638 | 0.025662 | -0.000976 |
| P4, ibm_marrakesh 12, hi95 | 0.051650 | 0.050583 | -0.001067 |
| P4, ibm_marrakesh 12, mean_regret | 0.037928 | 0.036911 | -0.001017 |
| P4, ibm_marrakesh 24, n | 300 | 315 | +15.000000 |
| P4, ibm_marrakesh 24, days | 20 | 21 | +1.000000 |
| P4, ibm_marrakesh 24, lo95 | 0.026035 | 0.026195 | +0.000160 |
| P4, ibm_marrakesh 24, hi95 | 0.049104 | 0.048330 | -0.000774 |
| P4, ibm_marrakesh 24, mean_regret | 0.036536 | 0.035919 | -0.000617 |
| P4, ibm_marrakesh 48, n | 284 | 299 | +15.000000 |
| P4, ibm_marrakesh 48, days | 19 | 20 | +1.000000 |
| P4, ibm_marrakesh 48, lo95 | 0.040152 | 0.042917 | +0.002765 |
| P4, ibm_marrakesh 48, hi95 | 0.075943 | 0.081316 | +0.005373 |
| P4, ibm_marrakesh 48, mean_regret | 0.056967 | 0.061453 | +0.004486 |
| P5 gap jobs, 1, n | 40 | 40 | +0.000000 |
| P5 gap jobs, 1, days | 3 | 3 | +0.000000 |
| P5 gap jobs, 1, lo95 | 0.000000 | 0.000000 | +0.000000 |
| P5 gap jobs, 1, hi95 | 0.000000 | 0.000000 | +0.000000 |
| P5 gap jobs, 1, mean_regret | 0.000000 | 0.000000 | +0.000000 |
| P5 gap jobs, 1, no_change_share | 0.875000 | 0.875000 | +0.000000 |
| P5 gap jobs, 3, n | 40 | 40 | +0.000000 |
| P5 gap jobs, 3, days | 3 | 3 | +0.000000 |
| P5 gap jobs, 3, lo95 | 0.000000 | 0.000000 | +0.000000 |
| P5 gap jobs, 3, hi95 | 0.000000 | 0.000000 | +0.000000 |
| P5 gap jobs, 3, mean_regret | 0.000000 | 0.000000 | +0.000000 |
| P5 gap jobs, 3, no_change_share | 0.875000 | 0.875000 | +0.000000 |
| P5 gap jobs, 6, n | 45 | 45 | +0.000000 |
| P5 gap jobs, 6, days | 3 | 3 | +0.000000 |
| P5 gap jobs, 6, lo95 | 0.000000 | 0.000000 | +0.000000 |
| P5 gap jobs, 6, hi95 | 0.007901 | 0.007901 | +0.000000 |
| P5 gap jobs, 6, mean_regret | 0.005013 | 0.005013 | +0.000000 |
| P5 gap jobs, 6, no_change_share | 0.555600 | 0.555600 | +0.000000 |
| P5 gap jobs, 12, n | 65 | 65 | +0.000000 |
| P5 gap jobs, 12, days | 3 | 3 | +0.000000 |
| P5 gap jobs, 12, lo95 | 0.011474 | 0.011474 | +0.000000 |
| P5 gap jobs, 12, hi95 | 0.016582 | 0.016582 | +0.000000 |
| P5 gap jobs, 12, mean_regret | 0.013810 | 0.013810 | +0.000000 |
| P5 gap jobs, 12, no_change_share | 0.076900 | 0.076900 | +0.000000 |
| P5 gap jobs, 24, n | 75 | 75 | +0.000000 |
| P5 gap jobs, 24, days | 3 | 3 | +0.000000 |
| P5 gap jobs, 24, lo95 | 0.011427 | 0.011427 | +0.000000 |
| P5 gap jobs, 24, hi95 | 0.021208 | 0.021208 | +0.000000 |
| P5 gap jobs, 24, mean_regret | 0.016630 | 0.016630 | +0.000000 |
| P5 gap jobs, 24, no_change_share | 0.000000 | 0.000000 | +0.000000 |
| P5 gap jobs, 48, n | 95 | 95 | +0.000000 |
| P5 gap jobs, 48, days | 3 | 3 | +0.000000 |
| P5 gap jobs, 48, lo95 | 0.013024 | 0.013024 | +0.000000 |
| P5 gap jobs, 48, hi95 | 0.059345 | 0.059345 | +0.000000 |
| P5 gap jobs, 48, mean_regret | 0.037452 | 0.037452 | +0.000000 |
| P5 gap jobs, 48, no_change_share | 0.000000 | 0.000000 | +0.000000 |
| P5b, ibm_fez 1, n | 10 | 10 | +0.000000 |
| P5b, ibm_fez 1, mean_regret | 0.000000 | 0.000000 | +0.000000 |
| P5b, ibm_fez 3, n | 10 | 10 | +0.000000 |
| P5b, ibm_fez 3, mean_regret | 0.000000 | 0.000000 | +0.000000 |
| P5b, ibm_fez 6, n | 15 | 15 | +0.000000 |
| P5b, ibm_fez 6, mean_regret | 0.012673 | 0.012673 | +0.000000 |
| P5b, ibm_fez 12, n | 25 | 25 | +0.000000 |
| P5b, ibm_fez 12, mean_regret | 0.011860 | 0.011860 | +0.000000 |
| P5b, ibm_fez 24, n | 30 | 30 | +0.000000 |
| P5b, ibm_fez 24, mean_regret | 0.008302 | 0.008302 | +0.000000 |
| P5b, ibm_fez 48, n | 40 | 40 | +0.000000 |
| P5b, ibm_fez 48, mean_regret | 0.006820 | 0.006820 | +0.000000 |
| P5b, ibm_kingston 1, n | 15 | 15 | +0.000000 |
| P5b, ibm_kingston 1, mean_regret | 0.000000 | 0.000000 | +0.000000 |
| P5b, ibm_kingston 3, n | 15 | 15 | +0.000000 |
| P5b, ibm_kingston 3, mean_regret | 0.000000 | 0.000000 | +0.000000 |
| P5b, ibm_kingston 6, n | 15 | 15 | +0.000000 |
| P5b, ibm_kingston 6, mean_regret | 0.002366 | 0.002366 | +0.000000 |
| P5b, ibm_kingston 12, n | 25 | 25 | +0.000000 |
| P5b, ibm_kingston 12, mean_regret | 0.014096 | 0.014096 | +0.000000 |
| P5b, ibm_kingston 24, n | 30 | 30 | +0.000000 |
| P5b, ibm_kingston 24, mean_regret | 0.021489 | 0.021489 | +0.000000 |
| P5b, ibm_kingston 48, n | 40 | 40 | +0.000000 |
| P5b, ibm_kingston 48, mean_regret | 0.027236 | 0.027236 | +0.000000 |
| P5b, ibm_marrakesh 1, n | 15 | 15 | +0.000000 |
| P5b, ibm_marrakesh 1, mean_regret | 0.000000 | 0.000000 | +0.000000 |
| P5b, ibm_marrakesh 3, n | 15 | 15 | +0.000000 |
| P5b, ibm_marrakesh 3, mean_regret | 0.000000 | 0.000000 | +0.000000 |
| P5b, ibm_marrakesh 6, n | 15 | 15 | +0.000000 |
| P5b, ibm_marrakesh 6, mean_regret | 0.000000 | 0.000000 | +0.000000 |
| P5b, ibm_marrakesh 12, n | 15 | 15 | +0.000000 |
| P5b, ibm_marrakesh 12, mean_regret | 0.016582 | 0.016582 | +0.000000 |
| P5b, ibm_marrakesh 24, n | 15 | 15 | +0.000000 |
| P5b, ibm_marrakesh 24, mean_regret | 0.023570 | 0.023570 | +0.000000 |
| P5b, ibm_marrakesh 48, n | 15 | 15 | +0.000000 |
| P5b, ibm_marrakesh 48, mean_regret | 0.146382 | 0.146382 | +0.000000 |
| P8, bv10 1, n | 186 | 194 | +8.000000 |
| P8, bv10 1, days | 22 | 22 | +0.000000 |
| P8, bv10 1, lo95 | 0.002552 | 0.002353 | -0.000199 |
| P8, bv10 1, hi95 | 0.015096 | 0.014549 | -0.000547 |
| P8, bv10 1, mean_regret | 0.008043 | 0.007711 | -0.000332 |
| P8, bv10 3, n | 184 | 192 | +8.000000 |
| P8, bv10 3, days | 22 | 22 | +0.000000 |
| P8, bv10 3, lo95 | 0.014218 | 0.013113 | -0.001105 |
| P8, bv10 3, hi95 | 0.039658 | 0.038466 | -0.001192 |
| P8, bv10 3, mean_regret | 0.025493 | 0.024431 | -0.001062 |
| P8, bv10 6, n | 181 | 190 | +9.000000 |
| P8, bv10 6, days | 22 | 22 | +0.000000 |
| P8, bv10 6, lo95 | 0.021200 | 0.020964 | -0.000236 |
| P8, bv10 6, hi95 | 0.043883 | 0.042422 | -0.001461 |
| P8, bv10 6, mean_regret | 0.031859 | 0.031014 | -0.000845 |
| P8, bv10 12, n | 176 | 189 | +13.000000 |
| P8, bv10 12, days | 21 | 21 | +0.000000 |
| P8, bv10 12, lo95 | 0.027774 | 0.026615 | -0.001159 |
| P8, bv10 12, hi95 | 0.046881 | 0.045258 | -0.001623 |
| P8, bv10 12, mean_regret | 0.036479 | 0.035134 | -0.001345 |
| P8, bv10 24, n | 171 | 186 | +15.000000 |
| P8, bv10 24, days | 21 | 21 | +0.000000 |
| P8, bv10 24, lo95 | 0.028018 | 0.027034 | -0.000984 |
| P8, bv10 24, hi95 | 0.054150 | 0.051543 | -0.002607 |
| P8, bv10 24, mean_regret | 0.039167 | 0.037472 | -0.001695 |
| P8, bv10 48, n | 158 | 177 | +19.000000 |
| P8, bv10 48, days | 19 | 20 | +1.000000 |
| P8, bv10 48, lo95 | 0.028594 | 0.030065 | +0.001471 |
| P8, bv10 48, hi95 | 0.060536 | 0.060054 | -0.000482 |
| P8, bv10 48, mean_regret | 0.043381 | 0.043782 | +0.000401 |
| P8, bv8 1, n | 186 | 194 | +8.000000 |
| P8, bv8 1, days | 22 | 22 | +0.000000 |
| P8, bv8 1, lo95 | 0.001641 | 0.001620 | -0.000021 |
| P8, bv8 1, hi95 | 0.011257 | 0.010563 | -0.000694 |
| P8, bv8 1, mean_regret | 0.005485 | 0.005259 | -0.000226 |
| P8, bv8 3, n | 184 | 192 | +8.000000 |
| P8, bv8 3, days | 22 | 22 | +0.000000 |
| P8, bv8 3, lo95 | 0.009628 | 0.009144 | -0.000484 |
| P8, bv8 3, hi95 | 0.023523 | 0.023029 | -0.000494 |
| P8, bv8 3, mean_regret | 0.015936 | 0.015272 | -0.000664 |
| P8, bv8 6, n | 182 | 191 | +9.000000 |
| P8, bv8 6, days | 22 | 22 | +0.000000 |
| P8, bv8 6, lo95 | 0.014934 | 0.014197 | -0.000737 |
| P8, bv8 6, hi95 | 0.024926 | 0.024271 | -0.000655 |
| P8, bv8 6, mean_regret | 0.019974 | 0.019262 | -0.000712 |
| P8, bv8 12, n | 176 | 189 | +13.000000 |
| P8, bv8 12, days | 21 | 21 | +0.000000 |
| P8, bv8 12, lo95 | 0.015154 | 0.014731 | -0.000423 |
| P8, bv8 12, hi95 | 0.024293 | 0.023743 | -0.000550 |
| P8, bv8 12, mean_regret | 0.019666 | 0.019066 | -0.000600 |
| P8, bv8 24, n | 171 | 186 | +15.000000 |
| P8, bv8 24, days | 21 | 21 | +0.000000 |
| P8, bv8 24, lo95 | 0.016352 | 0.015669 | -0.000683 |
| P8, bv8 24, hi95 | 0.027722 | 0.026764 | -0.000958 |
| P8, bv8 24, mean_regret | 0.021719 | 0.020931 | -0.000788 |
| P8, bv8 48, n | 159 | 178 | +19.000000 |
| P8, bv8 48, days | 19 | 20 | +1.000000 |
| P8, bv8 48, lo95 | 0.020244 | 0.020849 | +0.000605 |
| P8, bv8 48, hi95 | 0.042749 | 0.041335 | -0.001414 |
| P8, bv8 48, mean_regret | 0.030538 | 0.030396 | -0.000142 |
| P8, ghz10 1, n | 186 | 194 | +8.000000 |
| P8, ghz10 1, days | 22 | 22 | +0.000000 |
| P8, ghz10 1, lo95 | 0.002342 | 0.002096 | -0.000246 |
| P8, ghz10 1, hi95 | 0.014481 | 0.013670 | -0.000811 |
| P8, ghz10 1, mean_regret | 0.007576 | 0.007264 | -0.000312 |
| P8, ghz10 3, n | 184 | 192 | +8.000000 |
| P8, ghz10 3, days | 22 | 22 | +0.000000 |
| P8, ghz10 3, lo95 | 0.007821 | 0.007716 | -0.000105 |
| P8, ghz10 3, hi95 | 0.027805 | 0.027462 | -0.000343 |
| P8, ghz10 3, mean_regret | 0.017223 | 0.016505 | -0.000718 |
| P8, ghz10 6, n | 182 | 191 | +9.000000 |
| P8, ghz10 6, days | 22 | 22 | +0.000000 |
| P8, ghz10 6, lo95 | 0.016540 | 0.015312 | -0.001228 |
| P8, ghz10 6, hi95 | 0.035979 | 0.034999 | -0.000980 |
| P8, ghz10 6, mean_regret | 0.025490 | 0.024392 | -0.001098 |
| P8, ghz10 12, n | 176 | 189 | +13.000000 |
| P8, ghz10 12, days | 21 | 21 | +0.000000 |
| P8, ghz10 12, lo95 | 0.019204 | 0.019073 | -0.000131 |
| P8, ghz10 12, hi95 | 0.040822 | 0.039917 | -0.000905 |
| P8, ghz10 12, mean_regret | 0.028976 | 0.028304 | -0.000672 |
| P8, ghz10 24, n | 171 | 186 | +15.000000 |
| P8, ghz10 24, days | 21 | 21 | +0.000000 |
| P8, ghz10 24, lo95 | 0.017409 | 0.018165 | +0.000756 |
| P8, ghz10 24, hi95 | 0.035322 | 0.034743 | -0.000579 |
| P8, ghz10 24, mean_regret | 0.025363 | 0.025433 | +0.000070 |
| P8, ghz10 48, n | 159 | 178 | +19.000000 |
| P8, ghz10 48, days | 19 | 20 | +1.000000 |
| P8, ghz10 48, lo95 | 0.027760 | 0.029674 | +0.001914 |
| P8, ghz10 48, hi95 | 0.077188 | 0.074294 | -0.002894 |
| P8, ghz10 48, mean_regret | 0.050205 | 0.049523 | -0.000682 |
| P8, ghz5 1, n | 186 | 194 | +8.000000 |
| P8, ghz5 1, days | 22 | 22 | +0.000000 |
| P8, ghz5 1, lo95 | 0.000336 | 0.000326 | -0.000010 |
| P8, ghz5 1, hi95 | 0.001031 | 0.000986 | -0.000045 |
| P8, ghz5 1, mean_regret | 0.000660 | 0.000633 | -0.000027 |
| P8, ghz5 3, n | 184 | 192 | +8.000000 |
| P8, ghz5 3, days | 22 | 22 | +0.000000 |
| P8, ghz5 3, lo95 | 0.002615 | 0.002471 | -0.000144 |
| P8, ghz5 3, hi95 | 0.006752 | 0.006588 | -0.000164 |
| P8, ghz5 3, mean_regret | 0.004562 | 0.004372 | -0.000190 |
| P8, ghz5 6, n | 182 | 191 | +9.000000 |
| P8, ghz5 6, days | 22 | 22 | +0.000000 |
| P8, ghz5 6, lo95 | 0.004136 | 0.004063 | -0.000073 |
| P8, ghz5 6, hi95 | 0.009544 | 0.009327 | -0.000217 |
| P8, ghz5 6, mean_regret | 0.006635 | 0.006461 | -0.000174 |
| P8, ghz5 12, n | 176 | 189 | +13.000000 |
| P8, ghz5 12, days | 21 | 21 | +0.000000 |
| P8, ghz5 12, lo95 | 0.008885 | 0.008947 | +0.000062 |
| P8, ghz5 12, hi95 | 0.019923 | 0.019132 | -0.000791 |
| P8, ghz5 12, mean_regret | 0.013887 | 0.013494 | -0.000393 |
| P8, ghz5 24, n | 171 | 186 | +15.000000 |
| P8, ghz5 24, days | 21 | 21 | +0.000000 |
| P8, ghz5 24, lo95 | 0.008517 | 0.008319 | -0.000198 |
| P8, ghz5 24, hi95 | 0.017977 | 0.017409 | -0.000568 |
| P8, ghz5 24, mean_regret | 0.012648 | 0.012299 | -0.000349 |
| P8, ghz5 48, n | 159 | 178 | +19.000000 |
| P8, ghz5 48, days | 19 | 20 | +1.000000 |
| P8, ghz5 48, lo95 | 0.010551 | 0.011454 | +0.000903 |
| P8, ghz5 48, hi95 | 0.028568 | 0.029300 | +0.000732 |
| P8, ghz5 48, mean_regret | 0.017966 | 0.019060 | +0.001094 |
| P8, ghz8 1, n | 186 | 194 | +8.000000 |
| P8, ghz8 1, days | 22 | 22 | +0.000000 |
| P8, ghz8 1, lo95 | 0.001197 | 0.001181 | -0.000016 |
| P8, ghz8 1, hi95 | 0.015474 | 0.015264 | -0.000210 |
| P8, ghz8 1, mean_regret | 0.007919 | 0.007592 | -0.000327 |
| P8, ghz8 3, n | 184 | 192 | +8.000000 |
| P8, ghz8 3, days | 22 | 22 | +0.000000 |
| P8, ghz8 3, lo95 | 0.011437 | 0.011010 | -0.000427 |
| P8, ghz8 3, hi95 | 0.034387 | 0.033221 | -0.001166 |
| P8, ghz8 3, mean_regret | 0.022362 | 0.021430 | -0.000932 |
| P8, ghz8 6, n | 182 | 191 | +9.000000 |
| P8, ghz8 6, days | 22 | 22 | +0.000000 |
| P8, ghz8 6, lo95 | 0.018396 | 0.017391 | -0.001005 |
| P8, ghz8 6, hi95 | 0.045382 | 0.043738 | -0.001644 |
| P8, ghz8 6, mean_regret | 0.030902 | 0.029496 | -0.001406 |
| P8, ghz8 12, n | 176 | 189 | +13.000000 |
| P8, ghz8 12, days | 21 | 21 | +0.000000 |
| P8, ghz8 12, lo95 | 0.019743 | 0.019261 | -0.000482 |
| P8, ghz8 12, hi95 | 0.042541 | 0.040843 | -0.001698 |
| P8, ghz8 12, mean_regret | 0.030426 | 0.029283 | -0.001143 |
| P8, ghz8 24, n | 171 | 186 | +15.000000 |
| P8, ghz8 24, days | 21 | 21 | +0.000000 |
| P8, ghz8 24, lo95 | 0.015305 | 0.015410 | +0.000105 |
| P8, ghz8 24, hi95 | 0.034259 | 0.033460 | -0.000799 |
| P8, ghz8 24, mean_regret | 0.023658 | 0.023243 | -0.000415 |
| P8, ghz8 48, n | 159 | 178 | +19.000000 |
| P8, ghz8 48, days | 19 | 20 | +1.000000 |
| P8, ghz8 48, lo95 | 0.026669 | 0.027643 | +0.000974 |
| P8, ghz8 48, hi95 | 0.058616 | 0.056095 | -0.002521 |
| P8, ghz8 48, mean_regret | 0.041218 | 0.040970 | -0.000248 |
| P2b, count, cz_age_at_run_h | 5258.000000 | 5618.000000 | +360.000000 |
| P2b, count, readout_age_at_run_h | 5288.000000 | 5648.000000 | +360.000000 |
| P2b, mean, cz_age_at_run_h | 28.180000 | 29.570000 | +1.390000 |
| P2b, mean, readout_age_at_run_h | 19.626000 | 20.667000 | +1.041000 |
| P2b, std, cz_age_at_run_h | 18.363000 | 19.152000 | +0.789000 |
| P2b, std, readout_age_at_run_h | 16.446000 | 16.978000 | +0.532000 |
| P2b, min, cz_age_at_run_h | 1.070000 | 1.070000 | +0.000000 |
| P2b, min, readout_age_at_run_h | 1.005000 | 1.005000 | +0.000000 |
| P2b, 25%, cz_age_at_run_h | 14.664000 | 15.276000 | +0.612000 |
| P2b, 25%, readout_age_at_run_h | 7.298000 | 7.482000 | +0.184000 |
| P2b, 50%, cz_age_at_run_h | 24.295000 | 25.317000 | +1.022000 |
| P2b, 50%, readout_age_at_run_h | 13.396000 | 13.983000 | +0.587000 |
| P2b, 75%, cz_age_at_run_h | 38.221000 | 40.498000 | +2.277000 |
| P2b, 75%, readout_age_at_run_h | 27.189000 | 28.377000 | +1.188000 |
| P2b, max, cz_age_at_run_h | 99.731000 | 99.731000 | +0.000000 |
| P2b, max, readout_age_at_run_h | 76.481000 | 76.481000 | +0.000000 |
| P3, D=1 h, ceiling_esp | 0.916245 | 0.916694 | +0.000449 |
| P3, D=1 h, random_esp | 0.725920 | 0.726554 | +0.000634 |
| P3, D=1 h, shrinkage_esp | 0.910718 | 0.911320 | +0.000602 |
| P3, D=1 h, stale_esp | 0.910398 | 0.911089 | +0.000691 |
| P3, D=1 h, std_adjusted_esp | 0.906110 | 0.906109 | -0.000001 |
| P3, D=1 h, window_mean_esp | 0.905547 | 0.905556 | +0.000009 |
| P3, D=1 h, random_fidelity | 0.735555 | 0.736305 | +0.000750 |
| P3, D=1 h, stale_fidelity | 0.911774 | 0.912432 | +0.000658 |
| P3, D=1 h, window_mean_fidelity | 0.907005 | 0.907006 | +0.000001 |
| P3, D=1 h, std_adjusted_fidelity | 0.907616 | 0.907606 | -0.000010 |
| P3, D=1 h, shrinkage_fidelity | 0.912005 | 0.912581 | +0.000576 |
| P3, D=1 h, ceiling_fidelity | 0.917711 | 0.918124 | +0.000413 |
| P3, D=3 h, ceiling_esp | 0.921815 | 0.922036 | +0.000221 |
| P3, D=3 h, random_esp | 0.720754 | 0.721973 | +0.001219 |
| P3, D=3 h, shrinkage_esp | 0.907763 | 0.908494 | +0.000731 |
| P3, D=3 h, stale_esp | 0.904430 | 0.905376 | +0.000946 |
| P3, D=3 h, std_adjusted_esp | 0.907472 | 0.907414 | -0.000058 |
| P3, D=3 h, window_mean_esp | 0.909371 | 0.909221 | -0.000150 |
| P3, D=3 h, random_fidelity | 0.731715 | 0.732843 | +0.001128 |
| P3, D=3 h, stale_fidelity | 0.906117 | 0.907031 | +0.000914 |
| P3, D=3 h, window_mean_fidelity | 0.910914 | 0.910743 | -0.000171 |
| P3, D=3 h, std_adjusted_fidelity | 0.909022 | 0.908949 | -0.000073 |
| P3, D=3 h, shrinkage_fidelity | 0.909322 | 0.910028 | +0.000706 |
| P3, D=3 h, ceiling_fidelity | 0.923232 | 0.923433 | +0.000201 |
| P3, D=6 h, ceiling_esp | 0.927443 | 0.927425 | -0.000018 |
| P3, D=6 h, random_esp | 0.726768 | 0.726318 | -0.000450 |
| P3, D=6 h, shrinkage_esp | 0.907499 | 0.908190 | +0.000691 |
| P3, D=6 h, stale_esp | 0.904015 | 0.904858 | +0.000843 |
| P3, D=6 h, std_adjusted_esp | 0.909226 | 0.909137 | -0.000089 |
| P3, D=6 h, window_mean_esp | 0.913974 | 0.913674 | -0.000300 |
| P3, D=6 h, random_fidelity | 0.737799 | 0.737433 | -0.000366 |
| P3, D=6 h, stale_fidelity | 0.905697 | 0.906529 | +0.000832 |
| P3, D=6 h, window_mean_fidelity | 0.915482 | 0.915162 | -0.000320 |
| P3, D=6 h, std_adjusted_fidelity | 0.910691 | 0.910579 | -0.000112 |
| P3, D=6 h, shrinkage_fidelity | 0.909144 | 0.909826 | +0.000682 |
| P3, D=6 h, ceiling_fidelity | 0.928660 | 0.928644 | -0.000016 |
| P3, D=12 h, ceiling_esp | 0.922217 | 0.922621 | +0.000404 |
| P3, D=12 h, random_esp | 0.721882 | 0.721483 | -0.000399 |
| P3, D=12 h, shrinkage_esp | 0.898581 | 0.899753 | +0.001172 |
| P3, D=12 h, stale_esp | 0.895655 | 0.896935 | +0.001280 |
| P3, D=12 h, std_adjusted_esp | 0.901014 | 0.901735 | +0.000721 |
| P3, D=12 h, window_mean_esp | 0.902359 | 0.903073 | +0.000714 |
| P3, D=12 h, random_fidelity | 0.731965 | 0.732024 | +0.000059 |
| P3, D=12 h, stale_fidelity | 0.897501 | 0.898809 | +0.001308 |
| P3, D=12 h, window_mean_fidelity | 0.903919 | 0.904622 | +0.000703 |
| P3, D=12 h, std_adjusted_fidelity | 0.902326 | 0.903062 | +0.000736 |
| P3, D=12 h, shrinkage_fidelity | 0.900215 | 0.901407 | +0.001192 |
| P3, D=12 h, ceiling_fidelity | 0.923388 | 0.923866 | +0.000478 |
| P3, D=24 h, ceiling_esp | 0.926578 | 0.926663 | +0.000085 |
| P3, D=24 h, random_esp | 0.720419 | 0.720790 | +0.000371 |
| P3, D=24 h, shrinkage_esp | 0.901613 | 0.902368 | +0.000755 |
| P3, D=24 h, stale_esp | 0.901372 | 0.902145 | +0.000773 |
| P3, D=24 h, std_adjusted_esp | 0.904072 | 0.904649 | +0.000577 |
| P3, D=24 h, window_mean_esp | 0.908432 | 0.908676 | +0.000244 |
| P3, D=24 h, random_fidelity | 0.731442 | 0.731875 | +0.000433 |
| P3, D=24 h, stale_fidelity | 0.903351 | 0.904078 | +0.000727 |
| P3, D=24 h, window_mean_fidelity | 0.909893 | 0.910115 | +0.000222 |
| P3, D=24 h, std_adjusted_fidelity | 0.905408 | 0.905976 | +0.000568 |
| P3, D=24 h, shrinkage_fidelity | 0.903321 | 0.904037 | +0.000716 |
| P3, D=24 h, ceiling_fidelity | 0.927862 | 0.927954 | +0.000092 |
| P3, D=48 h, ceiling_esp | 0.920833 | 0.921851 | +0.001018 |
| P3, D=48 h, random_esp | 0.717893 | 0.718102 | +0.000209 |
| P3, D=48 h, shrinkage_esp | 0.886049 | 0.887854 | +0.001805 |
| P3, D=48 h, stale_esp | 0.882027 | 0.883119 | +0.001092 |
| P3, D=48 h, std_adjusted_esp | 0.887397 | 0.890281 | +0.002884 |
| P3, D=48 h, window_mean_esp | 0.897306 | 0.899183 | +0.001877 |
| P3, D=48 h, random_fidelity | 0.728635 | 0.729393 | +0.000758 |
| P3, D=48 h, stale_fidelity | 0.885147 | 0.886103 | +0.000956 |
| P3, D=48 h, window_mean_fidelity | 0.899646 | 0.901420 | +0.001774 |
| P3, D=48 h, std_adjusted_fidelity | 0.890824 | 0.893496 | +0.002672 |
| P3, D=48 h, shrinkage_fidelity | 0.888859 | 0.890577 | +0.001718 |
| P3, D=48 h, ceiling_fidelity | 0.921800 | 0.922842 | +0.001042 |
| P9, D=1 h, n | 930 | 970 | +40.000000 |
| P9, D=1 h, fid_random | 0.735555 | 0.736305 | +0.000750 |
| P9, D=1 h, fid_random_lo95 | 0.714176 | 0.716554 | +0.002378 |
| P9, D=1 h, fid_random_hi95 | 0.750009 | 0.750094 | +0.000085 |
| P9, D=1 h, fid_stale | 0.911774 | 0.912432 | +0.000658 |
| P9, D=1 h, fid_stale_lo95 | 0.889826 | 0.890889 | +0.001063 |
| P9, D=1 h, fid_stale_hi95 | 0.924739 | 0.925037 | +0.000298 |
| P9, D=1 h, fid_window_mean | 0.907005 | 0.907006 | +0.000001 |
| P9, D=1 h, fid_window_mean_lo95 | 0.885858 | 0.886249 | +0.000391 |
| P9, D=1 h, fid_window_mean_hi95 | 0.919528 | 0.919030 | -0.000498 |
| P9, D=1 h, fid_std_adjusted | 0.907616 | 0.907606 | -0.000010 |
| P9, D=1 h, fid_std_adjusted_lo95 | 0.887022 | 0.888535 | +0.001513 |
| P9, D=1 h, fid_std_adjusted_hi95 | 0.919315 | 0.918709 | -0.000606 |
| P9, D=1 h, fid_shrinkage | 0.912005 | 0.912581 | +0.000576 |
| P9, D=1 h, fid_shrinkage_lo95 | 0.891734 | 0.892899 | +0.001165 |
| P9, D=1 h, fid_shrinkage_hi95 | 0.924322 | 0.924207 | -0.000115 |
| P9, D=1 h, fid_ceiling | 0.917711 | 0.918124 | +0.000413 |
| P9, D=1 h, fid_ceiling_lo95 | 0.897200 | 0.898149 | +0.000949 |
| P9, D=1 h, fid_ceiling_hi95 | 0.928998 | 0.928901 | -0.000097 |
| P9, D=1 h, regret_random | 0.182156 | 0.181819 | -0.000337 |
| P9, D=1 h, regret_random_lo95 | 0.174174 | 0.174042 | -0.000132 |
| P9, D=1 h, regret_random_hi95 | 0.190041 | 0.189306 | -0.000735 |
| P9, D=1 h, regret_stale | 0.005937 | 0.005692 | -0.000245 |
| P9, D=1 h, regret_stale_lo95 | 0.002018 | 0.001873 | -0.000145 |
| P9, D=1 h, regret_stale_hi95 | 0.010722 | 0.010356 | -0.000366 |
| P9, D=1 h, regret_window_mean | 0.010706 | 0.011119 | +0.000413 |
| P9, D=1 h, regret_window_mean_lo95 | 0.008021 | 0.008525 | +0.000504 |
| P9, D=1 h, regret_window_mean_hi95 | 0.014062 | 0.014255 | +0.000193 |
| P9, D=1 h, regret_std_adjusted | 0.010095 | 0.010518 | +0.000423 |
| P9, D=1 h, regret_std_adjusted_lo95 | 0.008290 | 0.008768 | +0.000478 |
| P9, D=1 h, regret_std_adjusted_hi95 | 0.012148 | 0.012403 | +0.000255 |
| P9, D=1 h, regret_shrinkage | 0.005706 | 0.005543 | -0.000163 |
| P9, D=1 h, regret_shrinkage_lo95 | 0.003508 | 0.003442 | -0.000066 |
| P9, D=1 h, regret_shrinkage_hi95 | 0.008294 | 0.008054 | -0.000240 |
| P9, D=3 h, n | 920 | 960 | +40.000000 |
| P9, D=3 h, fid_random | 0.731715 | 0.732843 | +0.001128 |
| P9, D=3 h, fid_random_lo95 | 0.720641 | 0.722212 | +0.001571 |
| P9, D=3 h, fid_random_hi95 | 0.741932 | 0.742378 | +0.000446 |
| P9, D=3 h, fid_stale | 0.906117 | 0.907031 | +0.000914 |
| P9, D=3 h, fid_stale_lo95 | 0.894284 | 0.895759 | +0.001475 |
| P9, D=3 h, fid_stale_hi95 | 0.915869 | 0.916803 | +0.000934 |
| P9, D=3 h, fid_window_mean | 0.910914 | 0.910743 | -0.000171 |
| P9, D=3 h, fid_window_mean_lo95 | 0.900049 | 0.900281 | +0.000232 |
| P9, D=3 h, fid_window_mean_hi95 | 0.918806 | 0.918288 | -0.000518 |
| P9, D=3 h, fid_std_adjusted | 0.909022 | 0.908949 | -0.000073 |
| P9, D=3 h, fid_std_adjusted_lo95 | 0.898287 | 0.898454 | +0.000167 |
| P9, D=3 h, fid_std_adjusted_hi95 | 0.916519 | 0.915902 | -0.000617 |
| P9, D=3 h, fid_shrinkage | 0.909322 | 0.910028 | +0.000706 |
| P9, D=3 h, fid_shrinkage_lo95 | 0.897832 | 0.899028 | +0.001196 |
| P9, D=3 h, fid_shrinkage_hi95 | 0.918653 | 0.918699 | +0.000046 |
| P9, D=3 h, fid_ceiling | 0.923232 | 0.923433 | +0.000201 |
| P9, D=3 h, fid_ceiling_lo95 | 0.912659 | 0.912772 | +0.000113 |
| P9, D=3 h, fid_ceiling_hi95 | 0.929755 | 0.929577 | -0.000178 |
| P9, D=3 h, regret_random | 0.191517 | 0.190590 | -0.000927 |
| P9, D=3 h, regret_random_lo95 | 0.183502 | 0.183298 | -0.000204 |
| P9, D=3 h, regret_random_hi95 | 0.199245 | 0.197897 | -0.001348 |
| P9, D=3 h, regret_stale | 0.017115 | 0.016402 | -0.000713 |
| P9, D=3 h, regret_stale_lo95 | 0.010387 | 0.009487 | -0.000900 |
| P9, D=3 h, regret_stale_hi95 | 0.025235 | 0.024316 | -0.000919 |
| P9, D=3 h, regret_window_mean | 0.012318 | 0.012690 | +0.000372 |
| P9, D=3 h, regret_window_mean_lo95 | 0.009512 | 0.009952 | +0.000440 |
| P9, D=3 h, regret_window_mean_hi95 | 0.015746 | 0.015847 | +0.000101 |
| P9, D=3 h, regret_std_adjusted | 0.014210 | 0.014484 | +0.000274 |
| P9, D=3 h, regret_std_adjusted_lo95 | 0.011786 | 0.012349 | +0.000563 |
| P9, D=3 h, regret_std_adjusted_hi95 | 0.016644 | 0.016827 | +0.000183 |
| P9, D=3 h, regret_shrinkage | 0.013910 | 0.013405 | -0.000505 |
| P9, D=3 h, regret_shrinkage_lo95 | 0.008792 | 0.008601 | -0.000191 |
| P9, D=3 h, regret_shrinkage_hi95 | 0.019978 | 0.019259 | -0.000719 |
| P9, D=6 h, n | 909 | 954 | +45.000000 |
| P9, D=6 h, fid_random | 0.737799 | 0.737433 | -0.000366 |
| P9, D=6 h, fid_random_lo95 | 0.732012 | 0.731934 | -0.000078 |
| P9, D=6 h, fid_random_hi95 | 0.743332 | 0.742897 | -0.000435 |
| P9, D=6 h, fid_stale | 0.905697 | 0.906529 | +0.000832 |
| P9, D=6 h, fid_stale_lo95 | 0.898915 | 0.899919 | +0.001004 |
| P9, D=6 h, fid_stale_hi95 | 0.912457 | 0.913053 | +0.000596 |
| P9, D=6 h, fid_window_mean | 0.915482 | 0.915162 | -0.000320 |
| P9, D=6 h, fid_window_mean_lo95 | 0.912157 | 0.911985 | -0.000172 |
| P9, D=6 h, fid_window_mean_hi95 | 0.918798 | 0.918117 | -0.000681 |
| P9, D=6 h, fid_std_adjusted | 0.910691 | 0.910579 | -0.000112 |
| P9, D=6 h, fid_std_adjusted_lo95 | 0.905281 | 0.905709 | +0.000428 |
| P9, D=6 h, fid_std_adjusted_hi95 | 0.915572 | 0.915169 | -0.000403 |
| P9, D=6 h, fid_shrinkage | 0.909144 | 0.909826 | +0.000682 |
| P9, D=6 h, fid_shrinkage_lo95 | 0.904427 | 0.904850 | +0.000423 |
| P9, D=6 h, fid_shrinkage_hi95 | 0.913954 | 0.914454 | +0.000500 |
| P9, D=6 h, fid_ceiling | 0.928660 | 0.928644 | -0.000016 |
| P9, D=6 h, fid_ceiling_lo95 | 0.926836 | 0.926971 | +0.000135 |
| P9, D=6 h, fid_ceiling_hi95 | 0.930386 | 0.930307 | -0.000079 |
| P9, D=6 h, regret_random | 0.190860 | 0.191211 | +0.000351 |
| P9, D=6 h, regret_random_lo95 | 0.185225 | 0.185437 | +0.000212 |
| P9, D=6 h, regret_random_hi95 | 0.196642 | 0.196873 | +0.000231 |
| P9, D=6 h, regret_stale | 0.022962 | 0.022116 | -0.000846 |
| P9, D=6 h, regret_stale_lo95 | 0.016909 | 0.016015 | -0.000894 |
| P9, D=6 h, regret_stale_hi95 | 0.029007 | 0.028611 | -0.000396 |
| P9, D=6 h, regret_window_mean | 0.013177 | 0.013482 | +0.000305 |
| P9, D=6 h, regret_window_mean_lo95 | 0.010776 | 0.011311 | +0.000535 |
| P9, D=6 h, regret_window_mean_hi95 | 0.015432 | 0.015606 | +0.000174 |
| P9, D=6 h, regret_std_adjusted | 0.017969 | 0.018065 | +0.000096 |
| P9, D=6 h, regret_std_adjusted_lo95 | 0.013759 | 0.014043 | +0.000284 |
| P9, D=6 h, regret_std_adjusted_hi95 | 0.022541 | 0.022403 | -0.000138 |
| P9, D=6 h, regret_shrinkage | 0.019515 | 0.018819 | -0.000696 |
| P9, D=6 h, regret_shrinkage_lo95 | 0.015641 | 0.014909 | -0.000732 |
| P9, D=6 h, regret_shrinkage_hi95 | 0.023262 | 0.022663 | -0.000599 |
| P9, D=12 h, n | 880 | 945 | +65.000000 |
| P9, D=12 h, fid_random | 0.731965 | 0.732024 | +0.000059 |
| P9, D=12 h, fid_random_lo95 | 0.720487 | 0.720493 | +0.000006 |
| P9, D=12 h, fid_random_hi95 | 0.742414 | 0.741827 | -0.000587 |
| P9, D=12 h, fid_stale | 0.897501 | 0.898809 | +0.001308 |
| P9, D=12 h, fid_stale_lo95 | 0.885025 | 0.887201 | +0.002176 |
| P9, D=12 h, fid_stale_hi95 | 0.907868 | 0.908412 | +0.000544 |
| P9, D=12 h, fid_window_mean | 0.903919 | 0.904622 | +0.000703 |
| P9, D=12 h, fid_window_mean_lo95 | 0.890340 | 0.891736 | +0.001396 |
| P9, D=12 h, fid_window_mean_hi95 | 0.914849 | 0.914644 | -0.000205 |
| P9, D=12 h, fid_std_adjusted | 0.902326 | 0.903062 | +0.000736 |
| P9, D=12 h, fid_std_adjusted_lo95 | 0.890338 | 0.891494 | +0.001156 |
| P9, D=12 h, fid_std_adjusted_hi95 | 0.911780 | 0.911802 | +0.000022 |
| P9, D=12 h, fid_shrinkage | 0.900215 | 0.901407 | +0.001192 |
| P9, D=12 h, fid_shrinkage_lo95 | 0.887646 | 0.889405 | +0.001759 |
| P9, D=12 h, fid_shrinkage_hi95 | 0.910108 | 0.910662 | +0.000554 |
| P9, D=12 h, fid_ceiling | 0.923388 | 0.923866 | +0.000478 |
| P9, D=12 h, fid_ceiling_lo95 | 0.911990 | 0.913222 | +0.001232 |
| P9, D=12 h, fid_ceiling_hi95 | 0.929785 | 0.929911 | +0.000126 |
| P9, D=12 h, regret_random | 0.191423 | 0.191842 | +0.000419 |
| P9, D=12 h, regret_random_lo95 | 0.183820 | 0.183943 | +0.000123 |
| P9, D=12 h, regret_random_hi95 | 0.198728 | 0.198744 | +0.000016 |
| P9, D=12 h, regret_stale | 0.025887 | 0.025056 | -0.000831 |
| P9, D=12 h, regret_stale_lo95 | 0.019768 | 0.019348 | -0.000420 |
| P9, D=12 h, regret_stale_hi95 | 0.032649 | 0.031935 | -0.000714 |
| P9, D=12 h, regret_window_mean | 0.019469 | 0.019243 | -0.000226 |
| P9, D=12 h, regret_window_mean_lo95 | 0.013534 | 0.013753 | +0.000219 |
| P9, D=12 h, regret_window_mean_hi95 | 0.027468 | 0.026661 | -0.000807 |
| P9, D=12 h, regret_std_adjusted | 0.021062 | 0.020804 | -0.000258 |
| P9, D=12 h, regret_std_adjusted_lo95 | 0.016213 | 0.016314 | +0.000101 |
| P9, D=12 h, regret_std_adjusted_hi95 | 0.026840 | 0.026753 | -0.000087 |
| P9, D=12 h, regret_shrinkage | 0.023173 | 0.022459 | -0.000714 |
| P9, D=12 h, regret_shrinkage_lo95 | 0.017794 | 0.017538 | -0.000256 |
| P9, D=12 h, regret_shrinkage_hi95 | 0.029491 | 0.028139 | -0.001352 |
| P9, D=24 h, n | 855 | 930 | +75.000000 |
| P9, D=24 h, fid_random | 0.731442 | 0.731875 | +0.000433 |
| P9, D=24 h, fid_random_lo95 | 0.722724 | 0.723849 | +0.001125 |
| P9, D=24 h, fid_random_hi95 | 0.739518 | 0.739314 | -0.000204 |
| P9, D=24 h, fid_stale | 0.903351 | 0.904078 | +0.000727 |
| P9, D=24 h, fid_stale_lo95 | 0.895853 | 0.897282 | +0.001429 |
| P9, D=24 h, fid_stale_hi95 | 0.909959 | 0.910297 | +0.000338 |
| P9, D=24 h, fid_window_mean | 0.909893 | 0.910115 | +0.000222 |
| P9, D=24 h, fid_window_mean_lo95 | 0.904405 | 0.904971 | +0.000566 |
| P9, D=24 h, fid_window_mean_hi95 | 0.915063 | 0.915042 | -0.000021 |
| P9, D=24 h, fid_std_adjusted | 0.905408 | 0.905976 | +0.000568 |
| P9, D=24 h, fid_std_adjusted_lo95 | 0.898831 | 0.899643 | +0.000812 |
| P9, D=24 h, fid_std_adjusted_hi95 | 0.911092 | 0.911236 | +0.000144 |
| P9, D=24 h, fid_shrinkage | 0.903321 | 0.904037 | +0.000716 |
| P9, D=24 h, fid_shrinkage_lo95 | 0.896413 | 0.897244 | +0.000831 |
| P9, D=24 h, fid_shrinkage_hi95 | 0.910102 | 0.910150 | +0.000048 |
| P9, D=24 h, fid_ceiling | 0.927862 | 0.927954 | +0.000092 |
| P9, D=24 h, fid_ceiling_lo95 | 0.925697 | 0.925911 | +0.000214 |
| P9, D=24 h, fid_ceiling_hi95 | 0.929812 | 0.929650 | -0.000162 |
| P9, D=24 h, regret_random | 0.196420 | 0.196079 | -0.000341 |
| P9, D=24 h, regret_random_lo95 | 0.188004 | 0.188092 | +0.000088 |
| P9, D=24 h, regret_random_hi95 | 0.205131 | 0.204087 | -0.001044 |
| P9, D=24 h, regret_stale | 0.024511 | 0.023876 | -0.000635 |
| P9, D=24 h, regret_stale_lo95 | 0.018489 | 0.018219 | -0.000270 |
| P9, D=24 h, regret_stale_hi95 | 0.031591 | 0.030625 | -0.000966 |
| P9, D=24 h, regret_window_mean | 0.017969 | 0.017839 | -0.000130 |
| P9, D=24 h, regret_window_mean_lo95 | 0.013781 | 0.013849 | +0.000068 |
| P9, D=24 h, regret_window_mean_hi95 | 0.022496 | 0.022105 | -0.000391 |
| P9, D=24 h, regret_std_adjusted | 0.022454 | 0.021979 | -0.000475 |
| P9, D=24 h, regret_std_adjusted_lo95 | 0.017626 | 0.017665 | +0.000039 |
| P9, D=24 h, regret_std_adjusted_hi95 | 0.027826 | 0.026979 | -0.000847 |
| P9, D=24 h, regret_shrinkage | 0.024541 | 0.023917 | -0.000624 |
| P9, D=24 h, regret_shrinkage_lo95 | 0.018571 | 0.018344 | -0.000227 |
| P9, D=24 h, regret_shrinkage_hi95 | 0.031044 | 0.030297 | -0.000747 |
| P9, D=48 h, n | 794 | 889 | +95.000000 |
| P9, D=48 h, fid_random | 0.728635 | 0.729393 | +0.000758 |
| P9, D=48 h, fid_random_lo95 | 0.715366 | 0.718031 | +0.002665 |
| P9, D=48 h, fid_random_hi95 | 0.739220 | 0.739061 | -0.000159 |
| P9, D=48 h, fid_stale | 0.885147 | 0.886103 | +0.000956 |
| P9, D=48 h, fid_stale_lo95 | 0.864776 | 0.868315 | +0.003539 |
| P9, D=48 h, fid_stale_hi95 | 0.901691 | 0.901025 | -0.000666 |
| P9, D=48 h, fid_window_mean | 0.899646 | 0.901420 | +0.001774 |
| P9, D=48 h, fid_window_mean_lo95 | 0.885204 | 0.888313 | +0.003109 |
| P9, D=48 h, fid_window_mean_hi95 | 0.910875 | 0.911755 | +0.000880 |
| P9, D=48 h, fid_std_adjusted | 0.890824 | 0.893496 | +0.002672 |
| P9, D=48 h, fid_std_adjusted_lo95 | 0.869209 | 0.874195 | +0.004986 |
| P9, D=48 h, fid_std_adjusted_hi95 | 0.907084 | 0.908328 | +0.001244 |
| P9, D=48 h, fid_shrinkage | 0.888859 | 0.890577 | +0.001718 |
| P9, D=48 h, fid_shrinkage_lo95 | 0.869994 | 0.873731 | +0.003737 |
| P9, D=48 h, fid_shrinkage_hi95 | 0.904019 | 0.903369 | -0.000650 |
| P9, D=48 h, fid_ceiling | 0.921800 | 0.922842 | +0.001042 |
| P9, D=48 h, fid_ceiling_lo95 | 0.908501 | 0.911713 | +0.003212 |
| P9, D=48 h, fid_ceiling_hi95 | 0.928991 | 0.929319 | +0.000328 |
| P9, D=48 h, regret_random | 0.193165 | 0.193449 | +0.000284 |
| P9, D=48 h, regret_random_lo95 | 0.186381 | 0.186874 | +0.000493 |
| P9, D=48 h, regret_random_hi95 | 0.199863 | 0.199526 | -0.000337 |
| P9, D=48 h, regret_stale | 0.036653 | 0.036739 | +0.000086 |
| P9, D=48 h, regret_stale_lo95 | 0.024948 | 0.026065 | +0.001117 |
| P9, D=48 h, regret_stale_hi95 | 0.050606 | 0.049532 | -0.001074 |
| P9, D=48 h, regret_window_mean | 0.022154 | 0.021422 | -0.000732 |
| P9, D=48 h, regret_window_mean_lo95 | 0.015916 | 0.015667 | -0.000249 |
| P9, D=48 h, regret_window_mean_hi95 | 0.031052 | 0.029347 | -0.001705 |
| P9, D=48 h, regret_std_adjusted | 0.030976 | 0.029346 | -0.001630 |
| P9, D=48 h, regret_std_adjusted_lo95 | 0.020243 | 0.020130 | -0.000113 |
| P9, D=48 h, regret_std_adjusted_hi95 | 0.047271 | 0.044070 | -0.003201 |
| P9, D=48 h, regret_shrinkage | 0.032940 | 0.032265 | -0.000675 |
| P9, D=48 h, regret_shrinkage_lo95 | 0.023340 | 0.023465 | +0.000125 |
| P9, D=48 h, regret_shrinkage_hi95 | 0.045479 | 0.042536 | -0.002943 |
| P9c, ibm_fez D=1 h, n | 315 | 325 | +10.000000 |
| P9c, ibm_fez D=1 h, fid_random | 0.706561 | 0.707751 | +0.001190 |
| P9c, ibm_fez D=1 h, fid_random_lo95 | 0.694031 | 0.695132 | +0.001101 |
| P9c, ibm_fez D=1 h, fid_random_hi95 | 0.718337 | 0.719808 | +0.001471 |
| P9c, ibm_fez D=1 h, regret_random | 0.222389 | 0.221077 | -0.001312 |
| P9c, ibm_fez D=1 h, regret_random_lo95 | 0.209864 | 0.208816 | -0.001048 |
| P9c, ibm_fez D=1 h, regret_random_hi95 | 0.235150 | 0.234223 | -0.000927 |
| P9c, ibm_fez D=1 h, fid_stale | 0.927808 | 0.927722 | -0.000086 |
| P9c, ibm_fez D=1 h, fid_stale_lo95 | 0.925677 | 0.925517 | -0.000160 |
| P9c, ibm_fez D=1 h, fid_stale_hi95 | 0.930077 | 0.930001 | -0.000076 |
| P9c, ibm_fez D=1 h, regret_stale | 0.001142 | 0.001106 | -0.000036 |
| P9c, ibm_fez D=1 h, regret_stale_lo95 | 0.000450 | 0.000457 | +0.000007 |
| P9c, ibm_fez D=1 h, regret_stale_hi95 | 0.001917 | 0.001857 | -0.000060 |
| P9c, ibm_fez D=1 h, fid_window_mean | 0.924528 | 0.924326 | -0.000202 |
| P9c, ibm_fez D=1 h, fid_window_mean_lo95 | 0.921011 | 0.920945 | -0.000066 |
| P9c, ibm_fez D=1 h, fid_window_mean_hi95 | 0.927653 | 0.927316 | -0.000337 |
| P9c, ibm_fez D=1 h, regret_window_mean | 0.004421 | 0.004503 | +0.000082 |
| P9c, ibm_fez D=1 h, regret_window_mean_lo95 | 0.002981 | 0.003101 | +0.000120 |
| P9c, ibm_fez D=1 h, regret_window_mean_hi95 | 0.006302 | 0.006320 | +0.000018 |
| P9c, ibm_fez D=1 h, fid_std_adjusted | 0.922676 | 0.922608 | -0.000068 |
| P9c, ibm_fez D=1 h, fid_std_adjusted_lo95 | 0.918344 | 0.918424 | +0.000080 |
| P9c, ibm_fez D=1 h, fid_std_adjusted_hi95 | 0.926378 | 0.926111 | -0.000267 |
| P9c, ibm_fez D=1 h, regret_std_adjusted | 0.006273 | 0.006220 | -0.000053 |
| P9c, ibm_fez D=1 h, regret_std_adjusted_lo95 | 0.003654 | 0.003614 | -0.000040 |
| P9c, ibm_fez D=1 h, regret_std_adjusted_hi95 | 0.010021 | 0.010071 | +0.000050 |
| P9c, ibm_fez D=1 h, fid_shrinkage | 0.926777 | 0.926593 | -0.000184 |
| P9c, ibm_fez D=1 h, fid_shrinkage_lo95 | 0.924392 | 0.924207 | -0.000185 |
| P9c, ibm_fez D=1 h, fid_shrinkage_hi95 | 0.929129 | 0.928820 | -0.000309 |
| P9c, ibm_fez D=1 h, regret_shrinkage | 0.002173 | 0.002235 | +0.000062 |
| P9c, ibm_fez D=1 h, regret_shrinkage_lo95 | 0.001471 | 0.001555 | +0.000084 |
| P9c, ibm_fez D=1 h, regret_shrinkage_hi95 | 0.002900 | 0.002903 | +0.000003 |
| P9c, ibm_fez D=1 h, fid_ceiling | 0.928949 | 0.928828 | -0.000121 |
| P9c, ibm_fez D=1 h, fid_ceiling_lo95 | 0.926801 | 0.926695 | -0.000106 |
| P9c, ibm_fez D=1 h, fid_ceiling_hi95 | 0.931038 | 0.930919 | -0.000119 |
| P9c, ibm_fez D=3 h, n | 315 | 325 | +10.000000 |
| P9c, ibm_fez D=3 h, fid_random | 0.697775 | 0.699047 | +0.001272 |
| P9c, ibm_fez D=3 h, fid_random_lo95 | 0.685401 | 0.687431 | +0.002030 |
| P9c, ibm_fez D=3 h, fid_random_hi95 | 0.709744 | 0.711155 | +0.001411 |
| P9c, ibm_fez D=3 h, regret_random | 0.230922 | 0.229527 | -0.001395 |
| P9c, ibm_fez D=3 h, regret_random_lo95 | 0.218100 | 0.217031 | -0.001069 |
| P9c, ibm_fez D=3 h, regret_random_hi95 | 0.243115 | 0.241025 | -0.002090 |
| P9c, ibm_fez D=3 h, fid_stale | 0.925282 | 0.925263 | -0.000019 |
| P9c, ibm_fez D=3 h, fid_stale_lo95 | 0.921851 | 0.921813 | -0.000038 |
| P9c, ibm_fez D=3 h, fid_stale_hi95 | 0.928441 | 0.928315 | -0.000126 |
| P9c, ibm_fez D=3 h, regret_stale | 0.003416 | 0.003311 | -0.000105 |
| P9c, ibm_fez D=3 h, regret_stale_lo95 | 0.001810 | 0.001734 | -0.000076 |
| P9c, ibm_fez D=3 h, regret_stale_hi95 | 0.005436 | 0.005240 | -0.000196 |
| P9c, ibm_fez D=3 h, fid_window_mean | 0.923664 | 0.923498 | -0.000166 |
| P9c, ibm_fez D=3 h, fid_window_mean_lo95 | 0.920063 | 0.919906 | -0.000157 |
| P9c, ibm_fez D=3 h, fid_window_mean_hi95 | 0.927152 | 0.926896 | -0.000256 |
| P9c, ibm_fez D=3 h, regret_window_mean | 0.005034 | 0.005076 | +0.000042 |
| P9c, ibm_fez D=3 h, regret_window_mean_lo95 | 0.003268 | 0.003320 | +0.000052 |
| P9c, ibm_fez D=3 h, regret_window_mean_hi95 | 0.007029 | 0.007021 | -0.000008 |
| P9c, ibm_fez D=3 h, fid_std_adjusted | 0.921101 | 0.921088 | -0.000013 |
| P9c, ibm_fez D=3 h, fid_std_adjusted_lo95 | 0.916993 | 0.917037 | +0.000044 |
| P9c, ibm_fez D=3 h, fid_std_adjusted_hi95 | 0.924779 | 0.924651 | -0.000128 |
| P9c, ibm_fez D=3 h, regret_std_adjusted | 0.007597 | 0.007486 | -0.000111 |
| P9c, ibm_fez D=3 h, regret_std_adjusted_lo95 | 0.004917 | 0.004862 | -0.000055 |
| P9c, ibm_fez D=3 h, regret_std_adjusted_hi95 | 0.011372 | 0.011134 | -0.000238 |
| P9c, ibm_fez D=3 h, fid_shrinkage | 0.925202 | 0.925107 | -0.000095 |
| P9c, ibm_fez D=3 h, fid_shrinkage_lo95 | 0.922339 | 0.922350 | +0.000011 |
| P9c, ibm_fez D=3 h, fid_shrinkage_hi95 | 0.928023 | 0.927740 | -0.000283 |
| P9c, ibm_fez D=3 h, regret_shrinkage | 0.003495 | 0.003467 | -0.000028 |
| P9c, ibm_fez D=3 h, regret_shrinkage_lo95 | 0.002289 | 0.002305 | +0.000016 |
| P9c, ibm_fez D=3 h, regret_shrinkage_hi95 | 0.004819 | 0.004763 | -0.000056 |
| P9c, ibm_fez D=3 h, fid_ceiling | 0.928698 | 0.928574 | -0.000124 |
| P9c, ibm_fez D=3 h, fid_ceiling_lo95 | 0.926673 | 0.926618 | -0.000055 |
| P9c, ibm_fez D=3 h, fid_ceiling_hi95 | 0.930651 | 0.930452 | -0.000199 |
| P9c, ibm_fez D=6 h, n | 310 | 325 | +15.000000 |
| P9c, ibm_fez D=6 h, fid_random | 0.698503 | 0.698797 | +0.000294 |
| P9c, ibm_fez D=6 h, fid_random_lo95 | 0.688372 | 0.689012 | +0.000640 |
| P9c, ibm_fez D=6 h, fid_random_hi95 | 0.709498 | 0.709694 | +0.000196 |
| P9c, ibm_fez D=6 h, regret_random | 0.229988 | 0.229640 | -0.000348 |
| P9c, ibm_fez D=6 h, regret_random_lo95 | 0.219956 | 0.219969 | +0.000013 |
| P9c, ibm_fez D=6 h, regret_random_hi95 | 0.239227 | 0.238927 | -0.000300 |
| P9c, ibm_fez D=6 h, fid_stale | 0.919132 | 0.918925 | -0.000207 |
| P9c, ibm_fez D=6 h, fid_stale_lo95 | 0.913627 | 0.913441 | -0.000186 |
| P9c, ibm_fez D=6 h, fid_stale_hi95 | 0.924231 | 0.923833 | -0.000398 |
| P9c, ibm_fez D=6 h, regret_stale | 0.009359 | 0.009512 | +0.000153 |
| P9c, ibm_fez D=6 h, regret_stale_lo95 | 0.005274 | 0.005645 | +0.000371 |
| P9c, ibm_fez D=6 h, regret_stale_hi95 | 0.014087 | 0.013956 | -0.000131 |
| P9c, ibm_fez D=6 h, fid_window_mean | 0.920630 | 0.920509 | -0.000121 |
| P9c, ibm_fez D=6 h, fid_window_mean_lo95 | 0.916415 | 0.916588 | +0.000173 |
| P9c, ibm_fez D=6 h, fid_window_mean_hi95 | 0.924797 | 0.924361 | -0.000436 |
| P9c, ibm_fez D=6 h, regret_window_mean | 0.007862 | 0.007928 | +0.000066 |
| P9c, ibm_fez D=6 h, regret_window_mean_lo95 | 0.005186 | 0.005408 | +0.000222 |
| P9c, ibm_fez D=6 h, regret_window_mean_hi95 | 0.010695 | 0.010615 | -0.000080 |
| P9c, ibm_fez D=6 h, fid_std_adjusted | 0.915742 | 0.915822 | +0.000080 |
| P9c, ibm_fez D=6 h, fid_std_adjusted_lo95 | 0.908033 | 0.908090 | +0.000057 |
| P9c, ibm_fez D=6 h, fid_std_adjusted_hi95 | 0.921815 | 0.921630 | -0.000185 |
| P9c, ibm_fez D=6 h, regret_std_adjusted | 0.012750 | 0.012615 | -0.000135 |
| P9c, ibm_fez D=6 h, regret_std_adjusted_lo95 | 0.007672 | 0.007763 | +0.000091 |
| P9c, ibm_fez D=6 h, regret_std_adjusted_hi95 | 0.019940 | 0.019488 | -0.000452 |
| P9c, ibm_fez D=6 h, fid_shrinkage | 0.920013 | 0.919905 | -0.000108 |
| P9c, ibm_fez D=6 h, fid_shrinkage_lo95 | 0.915009 | 0.915414 | +0.000405 |
| P9c, ibm_fez D=6 h, fid_shrinkage_hi95 | 0.924601 | 0.924363 | -0.000238 |
| P9c, ibm_fez D=6 h, regret_shrinkage | 0.008478 | 0.008533 | +0.000055 |
| P9c, ibm_fez D=6 h, regret_shrinkage_lo95 | 0.005214 | 0.005366 | +0.000152 |
| P9c, ibm_fez D=6 h, regret_shrinkage_hi95 | 0.012199 | 0.012138 | -0.000061 |
| P9c, ibm_fez D=6 h, fid_ceiling | 0.928491 | 0.928437 | -0.000054 |
| P9c, ibm_fez D=6 h, fid_ceiling_lo95 | 0.926606 | 0.926566 | -0.000040 |
| P9c, ibm_fez D=6 h, fid_ceiling_hi95 | 0.930339 | 0.930224 | -0.000115 |
| P9c, ibm_fez D=12 h, n | 290 | 315 | +25.000000 |
| P9c, ibm_fez D=12 h, fid_random | 0.701075 | 0.699722 | -0.001353 |
| P9c, ibm_fez D=12 h, fid_random_lo95 | 0.688523 | 0.687635 | -0.000888 |
| P9c, ibm_fez D=12 h, fid_random_hi95 | 0.713955 | 0.712483 | -0.001472 |
| P9c, ibm_fez D=12 h, regret_random | 0.228660 | 0.229926 | +0.001266 |
| P9c, ibm_fez D=12 h, regret_random_lo95 | 0.215634 | 0.217318 | +0.001684 |
| P9c, ibm_fez D=12 h, regret_random_hi95 | 0.240993 | 0.241746 | +0.000753 |
| P9c, ibm_fez D=12 h, fid_stale | 0.915416 | 0.915523 | +0.000107 |
| P9c, ibm_fez D=12 h, fid_stale_lo95 | 0.909789 | 0.910152 | +0.000363 |
| P9c, ibm_fez D=12 h, fid_stale_hi95 | 0.921054 | 0.920689 | -0.000365 |
| P9c, ibm_fez D=12 h, regret_stale | 0.014319 | 0.014124 | -0.000195 |
| P9c, ibm_fez D=12 h, regret_stale_lo95 | 0.009908 | 0.009903 | -0.000005 |
| P9c, ibm_fez D=12 h, regret_stale_hi95 | 0.019363 | 0.018556 | -0.000807 |
| P9c, ibm_fez D=12 h, fid_window_mean | 0.919563 | 0.919471 | -0.000092 |
| P9c, ibm_fez D=12 h, fid_window_mean_lo95 | 0.915400 | 0.915370 | -0.000030 |
| P9c, ibm_fez D=12 h, fid_window_mean_hi95 | 0.923521 | 0.923271 | -0.000250 |
| P9c, ibm_fez D=12 h, regret_window_mean | 0.010172 | 0.010176 | +0.000004 |
| P9c, ibm_fez D=12 h, regret_window_mean_lo95 | 0.007406 | 0.007516 | +0.000110 |
| P9c, ibm_fez D=12 h, regret_window_mean_hi95 | 0.013092 | 0.012922 | -0.000170 |
| P9c, ibm_fez D=12 h, fid_std_adjusted | 0.918013 | 0.917933 | -0.000080 |
| P9c, ibm_fez D=12 h, fid_std_adjusted_lo95 | 0.913589 | 0.914139 | +0.000550 |
| P9c, ibm_fez D=12 h, fid_std_adjusted_hi95 | 0.922086 | 0.921679 | -0.000407 |
| P9c, ibm_fez D=12 h, regret_std_adjusted | 0.011723 | 0.011715 | -0.000008 |
| P9c, ibm_fez D=12 h, regret_std_adjusted_lo95 | 0.009031 | 0.009240 | +0.000209 |
| P9c, ibm_fez D=12 h, regret_std_adjusted_hi95 | 0.014803 | 0.014502 | -0.000301 |
| P9c, ibm_fez D=12 h, fid_shrinkage | 0.918870 | 0.918806 | -0.000064 |
| P9c, ibm_fez D=12 h, fid_shrinkage_lo95 | 0.914263 | 0.914532 | +0.000269 |
| P9c, ibm_fez D=12 h, fid_shrinkage_hi95 | 0.923141 | 0.922774 | -0.000367 |
| P9c, ibm_fez D=12 h, regret_shrinkage | 0.010866 | 0.010842 | -0.000024 |
| P9c, ibm_fez D=12 h, regret_shrinkage_lo95 | 0.007846 | 0.008001 | +0.000155 |
| P9c, ibm_fez D=12 h, regret_shrinkage_hi95 | 0.014173 | 0.013876 | -0.000297 |
| P9c, ibm_fez D=12 h, fid_ceiling | 0.929736 | 0.929648 | -0.000088 |
| P9c, ibm_fez D=12 h, fid_ceiling_lo95 | 0.927971 | 0.927903 | -0.000068 |
| P9c, ibm_fez D=12 h, fid_ceiling_hi95 | 0.931480 | 0.931342 | -0.000138 |
| P9c, ibm_fez D=24 h, n | 280 | 310 | +30.000000 |
| P9c, ibm_fez D=24 h, fid_random | 0.693137 | 0.693191 | +0.000054 |
| P9c, ibm_fez D=24 h, fid_random_lo95 | 0.676527 | 0.677869 | +0.001342 |
| P9c, ibm_fez D=24 h, fid_random_hi95 | 0.708002 | 0.707340 | -0.000662 |
| P9c, ibm_fez D=24 h, regret_random | 0.235221 | 0.234945 | -0.000276 |
| P9c, ibm_fez D=24 h, regret_random_lo95 | 0.219483 | 0.220818 | +0.001335 |
| P9c, ibm_fez D=24 h, regret_random_hi95 | 0.251964 | 0.250159 | -0.001805 |
| P9c, ibm_fez D=24 h, fid_stale | 0.915922 | 0.916100 | +0.000178 |
| P9c, ibm_fez D=24 h, fid_stale_lo95 | 0.908215 | 0.908999 | +0.000784 |
| P9c, ibm_fez D=24 h, fid_stale_hi95 | 0.921218 | 0.920866 | -0.000352 |
| P9c, ibm_fez D=24 h, regret_stale | 0.012437 | 0.012037 | -0.000400 |
| P9c, ibm_fez D=24 h, regret_stale_lo95 | 0.007811 | 0.007790 | -0.000021 |
| P9c, ibm_fez D=24 h, regret_stale_hi95 | 0.019406 | 0.017808 | -0.001598 |
| P9c, ibm_fez D=24 h, fid_window_mean | 0.920533 | 0.920051 | -0.000482 |
| P9c, ibm_fez D=24 h, fid_window_mean_lo95 | 0.915222 | 0.915215 | -0.000007 |
| P9c, ibm_fez D=24 h, fid_window_mean_hi95 | 0.924429 | 0.923777 | -0.000652 |
| P9c, ibm_fez D=24 h, regret_window_mean | 0.007826 | 0.008086 | +0.000260 |
| P9c, ibm_fez D=24 h, regret_window_mean_lo95 | 0.004555 | 0.005068 | +0.000513 |
| P9c, ibm_fez D=24 h, regret_window_mean_hi95 | 0.012176 | 0.012142 | -0.000034 |
| P9c, ibm_fez D=24 h, fid_std_adjusted | 0.916319 | 0.916134 | -0.000185 |
| P9c, ibm_fez D=24 h, fid_std_adjusted_lo95 | 0.908013 | 0.909067 | +0.001054 |
| P9c, ibm_fez D=24 h, fid_std_adjusted_hi95 | 0.921818 | 0.921134 | -0.000684 |
| P9c, ibm_fez D=24 h, regret_std_adjusted | 0.012039 | 0.012003 | -0.000036 |
| P9c, ibm_fez D=24 h, regret_std_adjusted_lo95 | 0.007376 | 0.007634 | +0.000258 |
| P9c, ibm_fez D=24 h, regret_std_adjusted_hi95 | 0.019528 | 0.018390 | -0.001138 |
| P9c, ibm_fez D=24 h, fid_shrinkage | 0.918264 | 0.918035 | -0.000229 |
| P9c, ibm_fez D=24 h, fid_shrinkage_lo95 | 0.911048 | 0.911404 | +0.000356 |
| P9c, ibm_fez D=24 h, fid_shrinkage_hi95 | 0.923177 | 0.922513 | -0.000664 |
| P9c, ibm_fez D=24 h, regret_shrinkage | 0.010095 | 0.010102 | +0.000007 |
| P9c, ibm_fez D=24 h, regret_shrinkage_lo95 | 0.005820 | 0.006128 | +0.000308 |
| P9c, ibm_fez D=24 h, regret_shrinkage_hi95 | 0.016931 | 0.016127 | -0.000804 |
| P9c, ibm_fez D=24 h, fid_ceiling | 0.928359 | 0.928137 | -0.000222 |
| P9c, ibm_fez D=24 h, fid_ceiling_lo95 | 0.926679 | 0.926653 | -0.000026 |
| P9c, ibm_fez D=24 h, fid_ceiling_hi95 | 0.929978 | 0.929650 | -0.000328 |
| P9c, ibm_fez D=48 h, n | 250 | 290 | +40.000000 |
| P9c, ibm_fez D=48 h, fid_random | 0.692532 | 0.693287 | +0.000755 |
| P9c, ibm_fez D=48 h, fid_random_lo95 | 0.678359 | 0.681130 | +0.002771 |
| P9c, ibm_fez D=48 h, fid_random_hi95 | 0.704926 | 0.703874 | -0.001052 |
| P9c, ibm_fez D=48 h, regret_random | 0.235813 | 0.234972 | -0.000841 |
| P9c, ibm_fez D=48 h, regret_random_lo95 | 0.223029 | 0.223582 | +0.000553 |
| P9c, ibm_fez D=48 h, regret_random_hi95 | 0.249634 | 0.247159 | -0.002475 |
| P9c, ibm_fez D=48 h, fid_stale | 0.914115 | 0.915051 | +0.000936 |
| P9c, ibm_fez D=48 h, fid_stale_lo95 | 0.905020 | 0.907036 | +0.002016 |
| P9c, ibm_fez D=48 h, fid_stale_hi95 | 0.921639 | 0.921779 | +0.000140 |
| P9c, ibm_fez D=48 h, regret_stale | 0.014230 | 0.013208 | -0.001022 |
| P9c, ibm_fez D=48 h, regret_stale_lo95 | 0.008381 | 0.007985 | -0.000396 |
| P9c, ibm_fez D=48 h, regret_stale_hi95 | 0.021645 | 0.019826 | -0.001819 |
| P9c, ibm_fez D=48 h, fid_window_mean | 0.914770 | 0.915856 | +0.001086 |
| P9c, ibm_fez D=48 h, fid_window_mean_lo95 | 0.905274 | 0.907610 | +0.002336 |
| P9c, ibm_fez D=48 h, fid_window_mean_hi95 | 0.923054 | 0.922984 | -0.000070 |
| P9c, ibm_fez D=48 h, regret_window_mean | 0.013575 | 0.012403 | -0.001172 |
| P9c, ibm_fez D=48 h, regret_window_mean_lo95 | 0.006950 | 0.006706 | -0.000244 |
| P9c, ibm_fez D=48 h, regret_window_mean_hi95 | 0.021194 | 0.019197 | -0.001997 |
| P9c, ibm_fez D=48 h, fid_std_adjusted | 0.912056 | 0.913260 | +0.001204 |
| P9c, ibm_fez D=48 h, fid_std_adjusted_lo95 | 0.903489 | 0.905312 | +0.001823 |
| P9c, ibm_fez D=48 h, fid_std_adjusted_hi95 | 0.919656 | 0.919919 | +0.000263 |
| P9c, ibm_fez D=48 h, regret_std_adjusted | 0.016289 | 0.014999 | -0.001290 |
| P9c, ibm_fez D=48 h, regret_std_adjusted_lo95 | 0.010187 | 0.009689 | -0.000498 |
| P9c, ibm_fez D=48 h, regret_std_adjusted_hi95 | 0.023562 | 0.021256 | -0.002306 |
| P9c, ibm_fez D=48 h, fid_shrinkage | 0.914602 | 0.915509 | +0.000907 |
| P9c, ibm_fez D=48 h, fid_shrinkage_lo95 | 0.905247 | 0.907758 | +0.002511 |
| P9c, ibm_fez D=48 h, fid_shrinkage_hi95 | 0.922599 | 0.922465 | -0.000134 |
| P9c, ibm_fez D=48 h, regret_shrinkage | 0.013742 | 0.012750 | -0.000992 |
| P9c, ibm_fez D=48 h, regret_shrinkage_lo95 | 0.007701 | 0.007207 | -0.000494 |
| P9c, ibm_fez D=48 h, regret_shrinkage_hi95 | 0.020722 | 0.019027 | -0.001695 |
| P9c, ibm_fez D=48 h, fid_ceiling | 0.928344 | 0.928259 | -0.000085 |
| P9c, ibm_fez D=48 h, fid_ceiling_lo95 | 0.926076 | 0.926289 | +0.000213 |
| P9c, ibm_fez D=48 h, fid_ceiling_hi95 | 0.930569 | 0.930210 | -0.000359 |
| P9c, ibm_kingston D=1 h, n | 300 | 315 | +15.000000 |
| P9c, ibm_kingston D=1 h, fid_random | 0.773211 | 0.773031 | -0.000180 |
| P9c, ibm_kingston D=1 h, fid_random_lo95 | 0.715801 | 0.718601 | +0.002800 |
| P9c, ibm_kingston D=1 h, fid_random_hi95 | 0.809712 | 0.808017 | -0.001695 |
| P9c, ibm_kingston D=1 h, regret_random | 0.133487 | 0.134955 | +0.001468 |
| P9c, ibm_kingston D=1 h, regret_random_lo95 | 0.117646 | 0.120270 | +0.002624 |
| P9c, ibm_kingston D=1 h, regret_random_hi95 | 0.148810 | 0.149816 | +0.001006 |
| P9c, ibm_kingston D=1 h, fid_stale | 0.905403 | 0.906753 | +0.001350 |
| P9c, ibm_kingston D=1 h, fid_stale_lo95 | 0.841100 | 0.847652 | +0.006552 |
| P9c, ibm_kingston D=1 h, fid_stale_hi95 | 0.937535 | 0.937498 | -0.000037 |
| P9c, ibm_kingston D=1 h, regret_stale | 0.001295 | 0.001233 | -0.000062 |
| P9c, ibm_kingston D=1 h, regret_stale_lo95 | 0.000215 | 0.000226 | +0.000011 |
| P9c, ibm_kingston D=1 h, regret_stale_hi95 | 0.002742 | 0.002624 | -0.000118 |
| P9c, ibm_kingston D=1 h, fid_window_mean | 0.902108 | 0.902888 | +0.000780 |
| P9c, ibm_kingston D=1 h, fid_window_mean_lo95 | 0.838620 | 0.843546 | +0.004926 |
| P9c, ibm_kingston D=1 h, fid_window_mean_hi95 | 0.934588 | 0.933980 | -0.000608 |
| P9c, ibm_kingston D=1 h, regret_window_mean | 0.004589 | 0.005098 | +0.000509 |
| P9c, ibm_kingston D=1 h, regret_window_mean_lo95 | 0.003112 | 0.003485 | +0.000373 |
| P9c, ibm_kingston D=1 h, regret_window_mean_hi95 | 0.006143 | 0.006807 | +0.000664 |
| P9c, ibm_kingston D=1 h, fid_std_adjusted | 0.899758 | 0.900669 | +0.000911 |
| P9c, ibm_kingston D=1 h, fid_std_adjusted_lo95 | 0.835845 | 0.842097 | +0.006252 |
| P9c, ibm_kingston D=1 h, fid_std_adjusted_hi95 | 0.931438 | 0.931122 | -0.000316 |
| P9c, ibm_kingston D=1 h, regret_std_adjusted | 0.006939 | 0.007317 | +0.000378 |
| P9c, ibm_kingston D=1 h, regret_std_adjusted_lo95 | 0.005214 | 0.005432 | +0.000218 |
| P9c, ibm_kingston D=1 h, regret_std_adjusted_hi95 | 0.009013 | 0.009510 | +0.000497 |
| P9c, ibm_kingston D=1 h, fid_shrinkage | 0.904853 | 0.906275 | +0.001422 |
| P9c, ibm_kingston D=1 h, fid_shrinkage_lo95 | 0.840270 | 0.846721 | +0.006451 |
| P9c, ibm_kingston D=1 h, fid_shrinkage_hi95 | 0.937238 | 0.936950 | -0.000288 |
| P9c, ibm_kingston D=1 h, regret_shrinkage | 0.001844 | 0.001711 | -0.000133 |
| P9c, ibm_kingston D=1 h, regret_shrinkage_lo95 | 0.000926 | 0.000833 | -0.000093 |
| P9c, ibm_kingston D=1 h, regret_shrinkage_hi95 | 0.002832 | 0.002571 | -0.000261 |
| P9c, ibm_kingston D=1 h, fid_ceiling | 0.906698 | 0.907986 | +0.001288 |
| P9c, ibm_kingston D=1 h, fid_ceiling_lo95 | 0.843247 | 0.849102 | +0.005855 |
| P9c, ibm_kingston D=1 h, fid_ceiling_hi95 | 0.938794 | 0.938679 | -0.000115 |
| P9c, ibm_kingston D=3 h, n | 300 | 315 | +15.000000 |
| P9c, ibm_kingston D=3 h, fid_random | 0.782673 | 0.783274 | +0.000601 |
| P9c, ibm_kingston D=3 h, fid_random_lo95 | 0.751556 | 0.752881 | +0.001325 |
| P9c, ibm_kingston D=3 h, fid_random_hi95 | 0.804837 | 0.804911 | +0.000074 |
| P9c, ibm_kingston D=3 h, regret_random | 0.139461 | 0.139456 | -0.000005 |
| P9c, ibm_kingston D=3 h, regret_random_lo95 | 0.126323 | 0.127001 | +0.000678 |
| P9c, ibm_kingston D=3 h, regret_random_hi95 | 0.152352 | 0.151248 | -0.001104 |
| P9c, ibm_kingston D=3 h, fid_stale | 0.908854 | 0.910082 | +0.001228 |
| P9c, ibm_kingston D=3 h, fid_stale_lo95 | 0.873187 | 0.875020 | +0.001833 |
| P9c, ibm_kingston D=3 h, fid_stale_hi95 | 0.932627 | 0.932682 | +0.000055 |
| P9c, ibm_kingston D=3 h, regret_stale | 0.013280 | 0.012648 | -0.000632 |
| P9c, ibm_kingston D=3 h, regret_stale_lo95 | 0.003583 | 0.003391 | -0.000192 |
| P9c, ibm_kingston D=3 h, regret_stale_hi95 | 0.029963 | 0.028178 | -0.001785 |
| P9c, ibm_kingston D=3 h, fid_window_mean | 0.915385 | 0.915552 | +0.000167 |
| P9c, ibm_kingston D=3 h, fid_window_mean_lo95 | 0.883674 | 0.885389 | +0.001715 |
| P9c, ibm_kingston D=3 h, fid_window_mean_hi95 | 0.932428 | 0.931800 | -0.000628 |
| P9c, ibm_kingston D=3 h, regret_window_mean | 0.006749 | 0.007178 | +0.000429 |
| P9c, ibm_kingston D=3 h, regret_window_mean_lo95 | 0.004815 | 0.005264 | +0.000449 |
| P9c, ibm_kingston D=3 h, regret_window_mean_hi95 | 0.008689 | 0.009037 | +0.000348 |
| P9c, ibm_kingston D=3 h, fid_std_adjusted | 0.912792 | 0.913105 | +0.000313 |
| P9c, ibm_kingston D=3 h, fid_std_adjusted_lo95 | 0.880756 | 0.882845 | +0.002089 |
| P9c, ibm_kingston D=3 h, fid_std_adjusted_hi95 | 0.929791 | 0.929318 | -0.000473 |
| P9c, ibm_kingston D=3 h, regret_std_adjusted | 0.009342 | 0.009626 | +0.000284 |
| P9c, ibm_kingston D=3 h, regret_std_adjusted_lo95 | 0.006880 | 0.007161 | +0.000281 |
| P9c, ibm_kingston D=3 h, regret_std_adjusted_hi95 | 0.012058 | 0.012383 | +0.000325 |
| P9c, ibm_kingston D=3 h, fid_shrinkage | 0.911940 | 0.913035 | +0.001095 |
| P9c, ibm_kingston D=3 h, fid_shrinkage_lo95 | 0.877511 | 0.880049 | +0.002538 |
| P9c, ibm_kingston D=3 h, fid_shrinkage_hi95 | 0.933015 | 0.933075 | +0.000060 |
| P9c, ibm_kingston D=3 h, regret_shrinkage | 0.010194 | 0.009695 | -0.000499 |
| P9c, ibm_kingston D=3 h, regret_shrinkage_lo95 | 0.003805 | 0.003642 | -0.000163 |
| P9c, ibm_kingston D=3 h, regret_shrinkage_hi95 | 0.020838 | 0.019809 | -0.001029 |
| P9c, ibm_kingston D=3 h, fid_ceiling | 0.922135 | 0.922730 | +0.000595 |
| P9c, ibm_kingston D=3 h, fid_ceiling_lo95 | 0.890364 | 0.892775 | +0.002411 |
| P9c, ibm_kingston D=3 h, fid_ceiling_hi95 | 0.938823 | 0.938668 | -0.000155 |
| P9c, ibm_kingston D=6 h, n | 300 | 315 | +15.000000 |
| P9c, ibm_kingston D=6 h, fid_random | 0.789599 | 0.788272 | -0.001327 |
| P9c, ibm_kingston D=6 h, fid_random_lo95 | 0.775637 | 0.774187 | -0.001450 |
| P9c, ibm_kingston D=6 h, fid_random_hi95 | 0.803594 | 0.802114 | -0.001480 |
| P9c, ibm_kingston D=6 h, regret_random | 0.147582 | 0.148745 | +0.001163 |
| P9c, ibm_kingston D=6 h, regret_random_lo95 | 0.132858 | 0.134541 | +0.001683 |
| P9c, ibm_kingston D=6 h, regret_random_hi95 | 0.163049 | 0.163458 | +0.000409 |
| P9c, ibm_kingston D=6 h, fid_stale | 0.916728 | 0.917425 | +0.000697 |
| P9c, ibm_kingston D=6 h, fid_stale_lo95 | 0.900224 | 0.900785 | +0.000561 |
| P9c, ibm_kingston D=6 h, fid_stale_hi95 | 0.927588 | 0.927716 | +0.000128 |
| P9c, ibm_kingston D=6 h, regret_stale | 0.020453 | 0.019592 | -0.000861 |
| P9c, ibm_kingston D=6 h, regret_stale_lo95 | 0.009523 | 0.009172 | -0.000351 |
| P9c, ibm_kingston D=6 h, regret_stale_hi95 | 0.037166 | 0.037021 | -0.000145 |
| P9c, ibm_kingston D=6 h, fid_window_mean | 0.928579 | 0.928223 | -0.000356 |
| P9c, ibm_kingston D=6 h, fid_window_mean_lo95 | 0.925907 | 0.925704 | -0.000203 |
| P9c, ibm_kingston D=6 h, fid_window_mean_hi95 | 0.931088 | 0.930448 | -0.000640 |
| P9c, ibm_kingston D=6 h, regret_window_mean | 0.008601 | 0.008794 | +0.000193 |
| P9c, ibm_kingston D=6 h, regret_window_mean_lo95 | 0.006275 | 0.006578 | +0.000303 |
| P9c, ibm_kingston D=6 h, regret_window_mean_hi95 | 0.011149 | 0.011298 | +0.000149 |
| P9c, ibm_kingston D=6 h, fid_std_adjusted | 0.925672 | 0.925480 | -0.000192 |
| P9c, ibm_kingston D=6 h, fid_std_adjusted_lo95 | 0.923186 | 0.923139 | -0.000047 |
| P9c, ibm_kingston D=6 h, fid_std_adjusted_hi95 | 0.928020 | 0.927814 | -0.000206 |
| P9c, ibm_kingston D=6 h, regret_std_adjusted | 0.011508 | 0.011536 | +0.000028 |
| P9c, ibm_kingston D=6 h, regret_std_adjusted_lo95 | 0.008975 | 0.009076 | +0.000101 |
| P9c, ibm_kingston D=6 h, regret_std_adjusted_hi95 | 0.014346 | 0.014190 | -0.000156 |
| P9c, ibm_kingston D=6 h, fid_shrinkage | 0.921445 | 0.921955 | +0.000510 |
| P9c, ibm_kingston D=6 h, fid_shrinkage_lo95 | 0.910463 | 0.911947 | +0.001484 |
| P9c, ibm_kingston D=6 h, fid_shrinkage_hi95 | 0.929100 | 0.929178 | +0.000078 |
| P9c, ibm_kingston D=6 h, regret_shrinkage | 0.015736 | 0.015061 | -0.000675 |
| P9c, ibm_kingston D=6 h, regret_shrinkage_lo95 | 0.008403 | 0.007991 | -0.000412 |
| P9c, ibm_kingston D=6 h, regret_shrinkage_hi95 | 0.026703 | 0.025760 | -0.000943 |
| P9c, ibm_kingston D=6 h, fid_ceiling | 0.937181 | 0.937016 | -0.000165 |
| P9c, ibm_kingston D=6 h, fid_ceiling_lo95 | 0.935442 | 0.935385 | -0.000057 |
| P9c, ibm_kingston D=6 h, fid_ceiling_hi95 | 0.938896 | 0.938555 | -0.000341 |
| P9c, ibm_kingston D=12 h, n | 290 | 315 | +25.000000 |
| P9c, ibm_kingston D=12 h, fid_random | 0.781118 | 0.780880 | -0.000238 |
| P9c, ibm_kingston D=12 h, fid_random_lo95 | 0.745684 | 0.748072 | +0.002388 |
| P9c, ibm_kingston D=12 h, fid_random_hi95 | 0.807170 | 0.804489 | -0.002681 |
| P9c, ibm_kingston D=12 h, regret_random | 0.140283 | 0.141791 | +0.001508 |
| P9c, ibm_kingston D=12 h, regret_random_lo95 | 0.124633 | 0.126551 | +0.001918 |
| P9c, ibm_kingston D=12 h, regret_random_hi95 | 0.157801 | 0.157902 | +0.000101 |
| P9c, ibm_kingston D=12 h, fid_stale | 0.896403 | 0.898538 | +0.002135 |
| P9c, ibm_kingston D=12 h, fid_stale_lo95 | 0.858702 | 0.865628 | +0.006926 |
| P9c, ibm_kingston D=12 h, fid_stale_hi95 | 0.921443 | 0.921928 | +0.000485 |
| P9c, ibm_kingston D=12 h, regret_stale | 0.024998 | 0.024133 | -0.000865 |
| P9c, ibm_kingston D=12 h, regret_stale_lo95 | 0.013588 | 0.013465 | -0.000123 |
| P9c, ibm_kingston D=12 h, regret_stale_hi95 | 0.042922 | 0.040540 | -0.002382 |
| P9c, ibm_kingston D=12 h, fid_window_mean | 0.910571 | 0.910974 | +0.000403 |
| P9c, ibm_kingston D=12 h, fid_window_mean_lo95 | 0.878077 | 0.880718 | +0.002641 |
| P9c, ibm_kingston D=12 h, fid_window_mean_hi95 | 0.928088 | 0.927432 | -0.000656 |
| P9c, ibm_kingston D=12 h, regret_window_mean | 0.010830 | 0.011697 | +0.000867 |
| P9c, ibm_kingston D=12 h, regret_window_mean_lo95 | 0.008285 | 0.008947 | +0.000662 |
| P9c, ibm_kingston D=12 h, regret_window_mean_hi95 | 0.013438 | 0.014579 | +0.001141 |
| P9c, ibm_kingston D=12 h, fid_std_adjusted | 0.905787 | 0.906511 | +0.000724 |
| P9c, ibm_kingston D=12 h, fid_std_adjusted_lo95 | 0.872425 | 0.875782 | +0.003357 |
| P9c, ibm_kingston D=12 h, fid_std_adjusted_hi95 | 0.924807 | 0.924153 | -0.000654 |
| P9c, ibm_kingston D=12 h, regret_std_adjusted | 0.015614 | 0.016160 | +0.000546 |
| P9c, ibm_kingston D=12 h, regret_std_adjusted_lo95 | 0.011502 | 0.011956 | +0.000454 |
| P9c, ibm_kingston D=12 h, regret_std_adjusted_hi95 | 0.021418 | 0.021351 | -0.000067 |
| P9c, ibm_kingston D=12 h, fid_shrinkage | 0.901848 | 0.903601 | +0.001753 |
| P9c, ibm_kingston D=12 h, fid_shrinkage_lo95 | 0.866202 | 0.871394 | +0.005192 |
| P9c, ibm_kingston D=12 h, fid_shrinkage_hi95 | 0.924168 | 0.924174 | +0.000006 |
| P9c, ibm_kingston D=12 h, regret_shrinkage | 0.019553 | 0.019070 | -0.000483 |
| P9c, ibm_kingston D=12 h, regret_shrinkage_lo95 | 0.011472 | 0.011600 | +0.000128 |
| P9c, ibm_kingston D=12 h, regret_shrinkage_hi95 | 0.031176 | 0.029845 | -0.001331 |
| P9c, ibm_kingston D=12 h, fid_ceiling | 0.921401 | 0.922671 | +0.001270 |
| P9c, ibm_kingston D=12 h, fid_ceiling_lo95 | 0.888805 | 0.892728 | +0.003923 |
| P9c, ibm_kingston D=12 h, fid_ceiling_hi95 | 0.938515 | 0.938559 | +0.000044 |
| P9c, ibm_kingston D=24 h, n | 275 | 305 | +30.000000 |
| P9c, ibm_kingston D=24 h, fid_random | 0.793620 | 0.792765 | -0.000855 |
| P9c, ibm_kingston D=24 h, fid_random_lo95 | 0.779300 | 0.779401 | +0.000101 |
| P9c, ibm_kingston D=24 h, fid_random_hi95 | 0.808848 | 0.806626 | -0.002222 |
| P9c, ibm_kingston D=24 h, regret_random | 0.143948 | 0.144770 | +0.000822 |
| P9c, ibm_kingston D=24 h, regret_random_lo95 | 0.128564 | 0.130925 | +0.002361 |
| P9c, ibm_kingston D=24 h, regret_random_hi95 | 0.158390 | 0.158317 | -0.000073 |
| P9c, ibm_kingston D=24 h, fid_stale | 0.913881 | 0.914064 | +0.000183 |
| P9c, ibm_kingston D=24 h, fid_stale_lo95 | 0.896392 | 0.897480 | +0.001088 |
| P9c, ibm_kingston D=24 h, fid_stale_hi95 | 0.925103 | 0.924066 | -0.001037 |
| P9c, ibm_kingston D=24 h, regret_stale | 0.023687 | 0.023471 | -0.000216 |
| P9c, ibm_kingston D=24 h, regret_stale_lo95 | 0.012470 | 0.013372 | +0.000902 |
| P9c, ibm_kingston D=24 h, regret_stale_hi95 | 0.041035 | 0.038913 | -0.002122 |
| P9c, ibm_kingston D=24 h, fid_window_mean | 0.926605 | 0.924984 | -0.001621 |
| P9c, ibm_kingston D=24 h, fid_window_mean_lo95 | 0.923550 | 0.921721 | -0.001829 |
| P9c, ibm_kingston D=24 h, fid_window_mean_hi95 | 0.929622 | 0.928282 | -0.001340 |
| P9c, ibm_kingston D=24 h, regret_window_mean | 0.010962 | 0.012550 | +0.001588 |
| P9c, ibm_kingston D=24 h, regret_window_mean_lo95 | 0.008621 | 0.009845 | +0.001224 |
| P9c, ibm_kingston D=24 h, regret_window_mean_hi95 | 0.013392 | 0.015415 | +0.002023 |
| P9c, ibm_kingston D=24 h, fid_std_adjusted | 0.922211 | 0.921165 | -0.001046 |
| P9c, ibm_kingston D=24 h, fid_std_adjusted_lo95 | 0.914543 | 0.914140 | -0.000403 |
| P9c, ibm_kingston D=24 h, fid_std_adjusted_hi95 | 0.927395 | 0.926296 | -0.001099 |
| P9c, ibm_kingston D=24 h, regret_std_adjusted | 0.015356 | 0.016369 | +0.001013 |
| P9c, ibm_kingston D=24 h, regret_std_adjusted_lo95 | 0.011038 | 0.011978 | +0.000940 |
| P9c, ibm_kingston D=24 h, regret_std_adjusted_hi95 | 0.022054 | 0.022736 | +0.000682 |
| P9c, ibm_kingston D=24 h, fid_shrinkage | 0.918875 | 0.918434 | -0.000441 |
| P9c, ibm_kingston D=24 h, fid_shrinkage_lo95 | 0.907889 | 0.908615 | +0.000726 |
| P9c, ibm_kingston D=24 h, fid_shrinkage_hi95 | 0.926412 | 0.925383 | -0.001029 |
| P9c, ibm_kingston D=24 h, regret_shrinkage | 0.018692 | 0.019100 | +0.000408 |
| P9c, ibm_kingston D=24 h, regret_shrinkage_lo95 | 0.011225 | 0.012233 | +0.001008 |
| P9c, ibm_kingston D=24 h, regret_shrinkage_hi95 | 0.030042 | 0.029499 | -0.000543 |
| P9c, ibm_kingston D=24 h, fid_ceiling | 0.937568 | 0.937534 | -0.000034 |
| P9c, ibm_kingston D=24 h, fid_ceiling_lo95 | 0.935684 | 0.935741 | +0.000057 |
| P9c, ibm_kingston D=24 h, fid_ceiling_hi95 | 0.939357 | 0.939240 | -0.000117 |
| P9c, ibm_kingston D=48 h, n | 260 | 300 | +40.000000 |
| P9c, ibm_kingston D=48 h, fid_random | 0.780187 | 0.779412 | -0.000775 |
| P9c, ibm_kingston D=48 h, fid_random_lo95 | 0.742361 | 0.747637 | +0.005276 |
| P9c, ibm_kingston D=48 h, fid_random_hi95 | 0.807635 | 0.803821 | -0.003814 |
| P9c, ibm_kingston D=48 h, regret_random | 0.139721 | 0.142907 | +0.003186 |
| P9c, ibm_kingston D=48 h, regret_random_lo95 | 0.122304 | 0.127371 | +0.005067 |
| P9c, ibm_kingston D=48 h, regret_random_hi95 | 0.158582 | 0.159527 | +0.000945 |
| P9c, ibm_kingston D=48 h, fid_stale | 0.883884 | 0.887466 | +0.003582 |
| P9c, ibm_kingston D=48 h, fid_stale_lo95 | 0.837950 | 0.845989 | +0.008039 |
| P9c, ibm_kingston D=48 h, fid_stale_hi95 | 0.922700 | 0.920525 | -0.002175 |
| P9c, ibm_kingston D=48 h, regret_stale | 0.036025 | 0.034853 | -0.001172 |
| P9c, ibm_kingston D=48 h, regret_stale_lo95 | 0.012062 | 0.013714 | +0.001652 |
| P9c, ibm_kingston D=48 h, regret_stale_hi95 | 0.069355 | 0.064679 | -0.004676 |
| P9c, ibm_kingston D=48 h, fid_window_mean | 0.899097 | 0.900672 | +0.001575 |
| P9c, ibm_kingston D=48 h, fid_window_mean_lo95 | 0.856342 | 0.863535 | +0.007193 |
| P9c, ibm_kingston D=48 h, fid_window_mean_hi95 | 0.928283 | 0.926480 | -0.001803 |
| P9c, ibm_kingston D=48 h, regret_window_mean | 0.020811 | 0.021647 | +0.000836 |
| P9c, ibm_kingston D=48 h, regret_window_mean_lo95 | 0.007344 | 0.009326 | +0.001982 |
| P9c, ibm_kingston D=48 h, regret_window_mean_hi95 | 0.044867 | 0.042937 | -0.001930 |
| P9c, ibm_kingston D=48 h, fid_std_adjusted | 0.887117 | 0.890548 | +0.003431 |
| P9c, ibm_kingston D=48 h, fid_std_adjusted_lo95 | 0.831162 | 0.841722 | +0.010560 |
| P9c, ibm_kingston D=48 h, fid_std_adjusted_hi95 | 0.926239 | 0.924842 | -0.001397 |
| P9c, ibm_kingston D=48 h, regret_std_adjusted | 0.032791 | 0.031771 | -0.001020 |
| P9c, ibm_kingston D=48 h, regret_std_adjusted_lo95 | 0.009499 | 0.011042 | +0.001543 |
| P9c, ibm_kingston D=48 h, regret_std_adjusted_hi95 | 0.077311 | 0.070395 | -0.006916 |
| P9c, ibm_kingston D=48 h, fid_shrinkage | 0.889397 | 0.891712 | +0.002315 |
| P9c, ibm_kingston D=48 h, fid_shrinkage_lo95 | 0.843548 | 0.849858 | +0.006310 |
| P9c, ibm_kingston D=48 h, fid_shrinkage_hi95 | 0.924463 | 0.921856 | -0.002607 |
| P9c, ibm_kingston D=48 h, regret_shrinkage | 0.030511 | 0.030608 | +0.000097 |
| P9c, ibm_kingston D=48 h, regret_shrinkage_lo95 | 0.009640 | 0.011860 | +0.002220 |
| P9c, ibm_kingston D=48 h, regret_shrinkage_hi95 | 0.063526 | 0.058418 | -0.005108 |
| P9c, ibm_kingston D=48 h, fid_ceiling | 0.919909 | 0.922319 | +0.002410 |
| P9c, ibm_kingston D=48 h, fid_ceiling_lo95 | 0.882558 | 0.890828 | +0.008270 |
| P9c, ibm_kingston D=48 h, fid_ceiling_hi95 | 0.939022 | 0.939060 | +0.000038 |
| P9c, ibm_marrakesh D=1 h, n | 315 | 330 | +15.000000 |
| P9c, ibm_marrakesh D=1 h, fid_random | 0.728687 | 0.729371 | +0.000684 |
| P9c, ibm_marrakesh D=1 h, fid_random_lo95 | 0.719506 | 0.720146 | +0.000640 |
| P9c, ibm_marrakesh D=1 h, fid_random_hi95 | 0.737693 | 0.737927 | +0.000234 |
| P9c, ibm_marrakesh D=1 h, regret_random | 0.188275 | 0.187889 | -0.000386 |
| P9c, ibm_marrakesh D=1 h, regret_random_lo95 | 0.180448 | 0.180302 | -0.000146 |
| P9c, ibm_marrakesh D=1 h, regret_random_hi95 | 0.196387 | 0.195348 | -0.001039 |
| P9c, ibm_marrakesh D=1 h, fid_stale | 0.901809 | 0.902796 | +0.000987 |
| P9c, ibm_marrakesh D=1 h, fid_stale_lo95 | 0.884462 | 0.886820 | +0.002358 |
| P9c, ibm_marrakesh D=1 h, fid_stale_hi95 | 0.915249 | 0.915601 | +0.000352 |
| P9c, ibm_marrakesh D=1 h, regret_stale | 0.015153 | 0.014464 | -0.000689 |
| P9c, ibm_marrakesh D=1 h, regret_stale_lo95 | 0.003513 | 0.003300 | -0.000213 |
| P9c, ibm_marrakesh D=1 h, regret_stale_hi95 | 0.030528 | 0.028933 | -0.001595 |
| P9c, ibm_marrakesh D=1 h, fid_window_mean | 0.894146 | 0.893878 | -0.000268 |
| P9c, ibm_marrakesh D=1 h, fid_window_mean_lo95 | 0.881959 | 0.882715 | +0.000756 |
| P9c, ibm_marrakesh D=1 h, fid_window_mean_hi95 | 0.904141 | 0.903510 | -0.000631 |
| P9c, ibm_marrakesh D=1 h, regret_window_mean | 0.022816 | 0.023382 | +0.000566 |
| P9c, ibm_marrakesh D=1 h, regret_window_mean_lo95 | 0.015222 | 0.016005 | +0.000783 |
| P9c, ibm_marrakesh D=1 h, regret_window_mean_hi95 | 0.031981 | 0.032450 | +0.000469 |
| P9c, ibm_marrakesh D=1 h, fid_std_adjusted | 0.900039 | 0.899453 | -0.000586 |
| P9c, ibm_marrakesh D=1 h, fid_std_adjusted_lo95 | 0.892834 | 0.892143 | -0.000691 |
| P9c, ibm_marrakesh D=1 h, fid_std_adjusted_hi95 | 0.906917 | 0.906358 | -0.000559 |
| P9c, ibm_marrakesh D=1 h, regret_std_adjusted | 0.016922 | 0.017806 | +0.000884 |
| P9c, ibm_marrakesh D=1 h, regret_std_adjusted_lo95 | 0.012476 | 0.013322 | +0.000846 |
| P9c, ibm_marrakesh D=1 h, regret_std_adjusted_hi95 | 0.021405 | 0.022525 | +0.001120 |
| P9c, ibm_marrakesh D=1 h, fid_shrinkage | 0.904046 | 0.904801 | +0.000755 |
| P9c, ibm_marrakesh D=1 h, fid_shrinkage_lo95 | 0.893601 | 0.893921 | +0.000320 |
| P9c, ibm_marrakesh D=1 h, fid_shrinkage_hi95 | 0.912690 | 0.913283 | +0.000593 |
| P9c, ibm_marrakesh D=1 h, regret_shrinkage | 0.012916 | 0.012458 | -0.000458 |
| P9c, ibm_marrakesh D=1 h, regret_shrinkage_lo95 | 0.006488 | 0.006309 | -0.000179 |
| P9c, ibm_marrakesh D=1 h, regret_shrinkage_hi95 | 0.020990 | 0.020174 | -0.000816 |
| P9c, ibm_marrakesh D=1 h, fid_ceiling | 0.916962 | 0.917259 | +0.000297 |
| P9c, ibm_marrakesh D=1 h, fid_ceiling_lo95 | 0.912823 | 0.913095 | +0.000272 |
| P9c, ibm_marrakesh D=1 h, fid_ceiling_hi95 | 0.921151 | 0.921110 | -0.000041 |
| P9c, ibm_marrakesh D=3 h, n | 305 | 320 | +15.000000 |
| P9c, ibm_marrakesh D=3 h, fid_random | 0.716644 | 0.717524 | +0.000880 |
| P9c, ibm_marrakesh D=3 h, fid_random_lo95 | 0.705043 | 0.705891 | +0.000848 |
| P9c, ibm_marrakesh D=3 h, fid_random_hi95 | 0.728914 | 0.729312 | +0.000398 |
| P9c, ibm_marrakesh D=3 h, regret_random | 0.202022 | 0.201379 | -0.000643 |
| P9c, ibm_marrakesh D=3 h, regret_random_lo95 | 0.191841 | 0.191885 | +0.000044 |
| P9c, ibm_marrakesh D=3 h, regret_random_hi95 | 0.211437 | 0.210073 | -0.001364 |
| P9c, ibm_marrakesh D=3 h, fid_stale | 0.883630 | 0.885510 | +0.001880 |
| P9c, ibm_marrakesh D=3 h, fid_stale_lo95 | 0.864314 | 0.866959 | +0.002645 |
| P9c, ibm_marrakesh D=3 h, fid_stale_hi95 | 0.899996 | 0.901341 | +0.001345 |
| P9c, ibm_marrakesh D=3 h, regret_stale | 0.035035 | 0.033393 | -0.001642 |
| P9c, ibm_marrakesh D=3 h, regret_stale_lo95 | 0.020495 | 0.019555 | -0.000940 |
| P9c, ibm_marrakesh D=3 h, regret_stale_hi95 | 0.051580 | 0.050500 | -0.001080 |
| P9c, ibm_marrakesh D=3 h, fid_window_mean | 0.893348 | 0.893055 | -0.000293 |
| P9c, ibm_marrakesh D=3 h, fid_window_mean_lo95 | 0.880041 | 0.880194 | +0.000153 |
| P9c, ibm_marrakesh D=3 h, fid_window_mean_hi95 | 0.904406 | 0.903498 | -0.000908 |
| P9c, ibm_marrakesh D=3 h, regret_window_mean | 0.025318 | 0.025848 | +0.000530 |
| P9c, ibm_marrakesh D=3 h, regret_window_mean_lo95 | 0.017371 | 0.017940 | +0.000569 |
| P9c, ibm_marrakesh D=3 h, regret_window_mean_hi95 | 0.034883 | 0.035401 | +0.000518 |
| P9c, ibm_marrakesh D=3 h, fid_std_adjusted | 0.892838 | 0.892530 | -0.000308 |
| P9c, ibm_marrakesh D=3 h, fid_std_adjusted_lo95 | 0.881769 | 0.882395 | +0.000626 |
| P9c, ibm_marrakesh D=3 h, fid_std_adjusted_hi95 | 0.902988 | 0.902620 | -0.000368 |
| P9c, ibm_marrakesh D=3 h, regret_std_adjusted | 0.025827 | 0.026373 | +0.000546 |
| P9c, ibm_marrakesh D=3 h, regret_std_adjusted_lo95 | 0.019057 | 0.019731 | +0.000674 |
| P9c, ibm_marrakesh D=3 h, regret_std_adjusted_hi95 | 0.032746 | 0.033292 | +0.000546 |
| P9c, ibm_marrakesh D=3 h, fid_shrinkage | 0.890345 | 0.891753 | +0.001408 |
| P9c, ibm_marrakesh D=3 h, fid_shrinkage_lo95 | 0.875957 | 0.877657 | +0.001700 |
| P9c, ibm_marrakesh D=3 h, fid_shrinkage_hi95 | 0.903544 | 0.904426 | +0.000882 |
| P9c, ibm_marrakesh D=3 h, regret_shrinkage | 0.028321 | 0.027150 | -0.001171 |
| P9c, ibm_marrakesh D=3 h, regret_shrinkage_lo95 | 0.018081 | 0.016744 | -0.001337 |
| P9c, ibm_marrakesh D=3 h, regret_shrinkage_hi95 | 0.039627 | 0.037847 | -0.001780 |
| P9c, ibm_marrakesh D=3 h, fid_ceiling | 0.918666 | 0.918903 | +0.000237 |
| P9c, ibm_marrakesh D=3 h, fid_ceiling_lo95 | 0.913756 | 0.914319 | +0.000563 |
| P9c, ibm_marrakesh D=3 h, fid_ceiling_hi95 | 0.923220 | 0.923433 | +0.000213 |
| P9c, ibm_marrakesh D=6 h, n | 299 | 314 | +15.000000 |
| P9c, ibm_marrakesh D=6 h, fid_random | 0.726569 | 0.726422 | -0.000147 |
| P9c, ibm_marrakesh D=6 h, fid_random_lo95 | 0.717918 | 0.717993 | +0.000075 |
| P9c, ibm_marrakesh D=6 h, fid_random_hi95 | 0.735035 | 0.734794 | -0.000241 |
| P9c, ibm_marrakesh D=6 h, regret_random | 0.193716 | 0.194038 | +0.000322 |
| P9c, ibm_marrakesh D=6 h, regret_random_lo95 | 0.185790 | 0.186023 | +0.000233 |
| P9c, ibm_marrakesh D=6 h, regret_random_hi95 | 0.201268 | 0.201446 | +0.000178 |
| P9c, ibm_marrakesh D=6 h, fid_stale | 0.880701 | 0.882767 | +0.002066 |
| P9c, ibm_marrakesh D=6 h, fid_stale_lo95 | 0.865377 | 0.867788 | +0.002411 |
| P9c, ibm_marrakesh D=6 h, fid_stale_hi95 | 0.894701 | 0.897298 | +0.002597 |
| P9c, ibm_marrakesh D=6 h, regret_stale | 0.039584 | 0.037693 | -0.001891 |
| P9c, ibm_marrakesh D=6 h, regret_stale_lo95 | 0.025309 | 0.023541 | -0.001768 |
| P9c, ibm_marrakesh D=6 h, regret_stale_hi95 | 0.055504 | 0.052791 | -0.002713 |
| P9c, ibm_marrakesh D=6 h, fid_window_mean | 0.897005 | 0.896526 | -0.000479 |
| P9c, ibm_marrakesh D=6 h, fid_window_mean_lo95 | 0.889458 | 0.888986 | -0.000472 |
| P9c, ibm_marrakesh D=6 h, fid_window_mean_hi95 | 0.903951 | 0.903290 | -0.000661 |
| P9c, ibm_marrakesh D=6 h, regret_window_mean | 0.023280 | 0.023934 | +0.000654 |
| P9c, ibm_marrakesh D=6 h, regret_window_mean_lo95 | 0.017657 | 0.018244 | +0.000587 |
| P9c, ibm_marrakesh D=6 h, regret_window_mean_hi95 | 0.029154 | 0.029506 | +0.000352 |
| P9c, ibm_marrakesh D=6 h, fid_std_adjusted | 0.890422 | 0.890203 | -0.000219 |
| P9c, ibm_marrakesh D=6 h, fid_std_adjusted_lo95 | 0.879457 | 0.879608 | +0.000151 |
| P9c, ibm_marrakesh D=6 h, fid_std_adjusted_hi95 | 0.900717 | 0.900048 | -0.000669 |
| P9c, ibm_marrakesh D=6 h, regret_std_adjusted | 0.029863 | 0.030257 | +0.000394 |
| P9c, ibm_marrakesh D=6 h, regret_std_adjusted_lo95 | 0.020853 | 0.022153 | +0.001300 |
| P9c, ibm_marrakesh D=6 h, regret_std_adjusted_hi95 | 0.039073 | 0.038375 | -0.000698 |
| P9c, ibm_marrakesh D=6 h, fid_shrinkage | 0.885534 | 0.887226 | +0.001692 |
| P9c, ibm_marrakesh D=6 h, fid_shrinkage_lo95 | 0.874256 | 0.875732 | +0.001476 |
| P9c, ibm_marrakesh D=6 h, fid_shrinkage_hi95 | 0.896300 | 0.897645 | +0.001345 |
| P9c, ibm_marrakesh D=6 h, regret_shrinkage | 0.034750 | 0.033235 | -0.001515 |
| P9c, ibm_marrakesh D=6 h, regret_shrinkage_lo95 | 0.024709 | 0.023281 | -0.001428 |
| P9c, ibm_marrakesh D=6 h, regret_shrinkage_hi95 | 0.044756 | 0.043259 | -0.001497 |
| P9c, ibm_marrakesh D=6 h, fid_ceiling | 0.920285 | 0.920460 | +0.000175 |
| P9c, ibm_marrakesh D=6 h, fid_ceiling_lo95 | 0.916645 | 0.916817 | +0.000172 |
| P9c, ibm_marrakesh D=6 h, fid_ceiling_hi95 | 0.923845 | 0.923788 | -0.000057 |
| P9c, ibm_marrakesh D=12 h, n | 300 | 315 | +15.000000 |
| P9c, ibm_marrakesh D=12 h, fid_random | 0.714311 | 0.715468 | +0.001157 |
| P9c, ibm_marrakesh D=12 h, fid_random_lo95 | 0.703838 | 0.705196 | +0.001358 |
| P9c, ibm_marrakesh D=12 h, fid_random_hi95 | 0.724258 | 0.725202 | +0.000944 |
| P9c, ibm_marrakesh D=12 h, regret_random | 0.204862 | 0.203810 | -0.001052 |
| P9c, ibm_marrakesh D=12 h, regret_random_lo95 | 0.196419 | 0.195646 | -0.000773 |
| P9c, ibm_marrakesh D=12 h, regret_random_hi95 | 0.213270 | 0.212170 | -0.001100 |
| P9c, ibm_marrakesh D=12 h, fid_stale | 0.881245 | 0.882367 | +0.001122 |
| P9c, ibm_marrakesh D=12 h, fid_stale_lo95 | 0.864364 | 0.867047 | +0.002683 |
| P9c, ibm_marrakesh D=12 h, fid_stale_hi95 | 0.895145 | 0.895911 | +0.000766 |
| P9c, ibm_marrakesh D=12 h, regret_stale | 0.037928 | 0.036911 | -0.001017 |
| P9c, ibm_marrakesh D=12 h, regret_stale_lo95 | 0.026425 | 0.026067 | -0.000358 |
| P9c, ibm_marrakesh D=12 h, regret_stale_hi95 | 0.051391 | 0.050286 | -0.001105 |
| P9c, ibm_marrakesh D=12 h, fid_window_mean | 0.882365 | 0.883422 | +0.001057 |
| P9c, ibm_marrakesh D=12 h, fid_window_mean_lo95 | 0.855684 | 0.857011 | +0.001327 |
| P9c, ibm_marrakesh D=12 h, fid_window_mean_hi95 | 0.901256 | 0.901431 | +0.000175 |
| P9c, ibm_marrakesh D=12 h, regret_window_mean | 0.036807 | 0.035856 | -0.000951 |
| P9c, ibm_marrakesh D=12 h, regret_window_mean_lo95 | 0.020004 | 0.019871 | -0.000133 |
| P9c, ibm_marrakesh D=12 h, regret_window_mean_hi95 | 0.059917 | 0.058391 | -0.001526 |
| P9c, ibm_marrakesh D=12 h, fid_std_adjusted | 0.883817 | 0.884741 | +0.000924 |
| P9c, ibm_marrakesh D=12 h, fid_std_adjusted_lo95 | 0.862017 | 0.864265 | +0.002248 |
| P9c, ibm_marrakesh D=12 h, fid_std_adjusted_hi95 | 0.900322 | 0.900170 | -0.000152 |
| P9c, ibm_marrakesh D=12 h, regret_std_adjusted | 0.035355 | 0.034537 | -0.000818 |
| P9c, ibm_marrakesh D=12 h, regret_std_adjusted_lo95 | 0.021536 | 0.021216 | -0.000320 |
| P9c, ibm_marrakesh D=12 h, regret_std_adjusted_hi95 | 0.053751 | 0.052300 | -0.001451 |
| P9c, ibm_marrakesh D=12 h, fid_shrinkage | 0.880604 | 0.881812 | +0.001208 |
| P9c, ibm_marrakesh D=12 h, fid_shrinkage_lo95 | 0.860957 | 0.862810 | +0.001853 |
| P9c, ibm_marrakesh D=12 h, fid_shrinkage_hi95 | 0.896360 | 0.897217 | +0.000857 |
| P9c, ibm_marrakesh D=12 h, regret_shrinkage | 0.038569 | 0.037466 | -0.001103 |
| P9c, ibm_marrakesh D=12 h, regret_shrinkage_lo95 | 0.025526 | 0.024406 | -0.001120 |
| P9c, ibm_marrakesh D=12 h, regret_shrinkage_hi95 | 0.054211 | 0.053620 | -0.000591 |
| P9c, ibm_marrakesh D=12 h, fid_ceiling | 0.919173 | 0.919278 | +0.000105 |
| P9c, ibm_marrakesh D=12 h, fid_ceiling_lo95 | 0.915498 | 0.915666 | +0.000168 |
| P9c, ibm_marrakesh D=12 h, fid_ceiling_hi95 | 0.922518 | 0.922410 | -0.000108 |
| P9c, ibm_marrakesh D=24 h, n | 300 | 315 | +15.000000 |
| P9c, ibm_marrakesh D=24 h, fid_random | 0.710197 | 0.710989 | +0.000792 |
| P9c, ibm_marrakesh D=24 h, fid_random_lo95 | 0.694492 | 0.696525 | +0.002033 |
| P9c, ibm_marrakesh D=24 h, fid_random_hi95 | 0.724147 | 0.723967 | -0.000180 |
| P9c, ibm_marrakesh D=24 h, regret_random | 0.208304 | 0.207509 | -0.000795 |
| P9c, ibm_marrakesh D=24 h, regret_random_lo95 | 0.196170 | 0.196101 | -0.000069 |
| P9c, ibm_marrakesh D=24 h, regret_random_hi95 | 0.221320 | 0.220107 | -0.001213 |
| P9c, ibm_marrakesh D=24 h, fid_stale | 0.881965 | 0.882580 | +0.000615 |
| P9c, ibm_marrakesh D=24 h, fid_stale_lo95 | 0.867797 | 0.869290 | +0.001493 |
| P9c, ibm_marrakesh D=24 h, fid_stale_hi95 | 0.893250 | 0.893730 | +0.000480 |
| P9c, ibm_marrakesh D=24 h, regret_stale | 0.036536 | 0.035919 | -0.000617 |
| P9c, ibm_marrakesh D=24 h, regret_stale_lo95 | 0.026425 | 0.026174 | -0.000251 |
| P9c, ibm_marrakesh D=24 h, regret_stale_hi95 | 0.048697 | 0.047859 | -0.000838 |
| P9c, ibm_marrakesh D=24 h, fid_window_mean | 0.884644 | 0.885941 | +0.001297 |
| P9c, ibm_marrakesh D=24 h, fid_window_mean_lo95 | 0.870343 | 0.871792 | +0.001449 |
| P9c, ibm_marrakesh D=24 h, fid_window_mean_hi95 | 0.899088 | 0.899650 | +0.000562 |
| P9c, ibm_marrakesh D=24 h, regret_window_mean | 0.033858 | 0.032558 | -0.001300 |
| P9c, ibm_marrakesh D=24 h, regret_window_mean_lo95 | 0.022724 | 0.021842 | -0.000882 |
| P9c, ibm_marrakesh D=24 h, regret_window_mean_hi95 | 0.046684 | 0.044990 | -0.001694 |
| P9c, ibm_marrakesh D=24 h, fid_std_adjusted | 0.879821 | 0.881271 | +0.001450 |
| P9c, ibm_marrakesh D=24 h, fid_std_adjusted_lo95 | 0.862592 | 0.864745 | +0.002153 |
| P9c, ibm_marrakesh D=24 h, fid_std_adjusted_hi95 | 0.893685 | 0.894597 | +0.000912 |
| P9c, ibm_marrakesh D=24 h, regret_std_adjusted | 0.038680 | 0.037227 | -0.001453 |
| P9c, ibm_marrakesh D=24 h, regret_std_adjusted_lo95 | 0.025926 | 0.024799 | -0.001127 |
| P9c, ibm_marrakesh D=24 h, regret_std_adjusted_hi95 | 0.053539 | 0.051511 | -0.002028 |
| P9c, ibm_marrakesh D=24 h, fid_shrinkage | 0.875116 | 0.876322 | +0.001206 |
| P9c, ibm_marrakesh D=24 h, fid_shrinkage_lo95 | 0.859487 | 0.861624 | +0.002137 |
| P9c, ibm_marrakesh D=24 h, fid_shrinkage_hi95 | 0.889729 | 0.890516 | +0.000787 |
| P9c, ibm_marrakesh D=24 h, regret_shrinkage | 0.043385 | 0.042177 | -0.001208 |
| P9c, ibm_marrakesh D=24 h, regret_shrinkage_lo95 | 0.031051 | 0.030285 | -0.000766 |
| P9c, ibm_marrakesh D=24 h, regret_shrinkage_hi95 | 0.056705 | 0.055377 | -0.001328 |
| P9c, ibm_marrakesh D=24 h, fid_ceiling | 0.918501 | 0.918498 | -0.000003 |
| P9c, ibm_marrakesh D=24 h, fid_ceiling_lo95 | 0.914159 | 0.914410 | +0.000251 |
| P9c, ibm_marrakesh D=24 h, fid_ceiling_hi95 | 0.922299 | 0.922164 | -0.000135 |
| P9c, ibm_marrakesh D=48 h, n | 284 | 299 | +15.000000 |
| P9c, ibm_marrakesh D=48 h, fid_random | 0.713220 | 0.714226 | +0.001006 |
| P9c, ibm_marrakesh D=48 h, fid_random_lo95 | 0.700726 | 0.702008 | +0.001282 |
| P9c, ibm_marrakesh D=48 h, fid_random_hi95 | 0.724217 | 0.724864 | +0.000647 |
| P9c, ibm_marrakesh D=48 h, regret_random | 0.204550 | 0.203886 | -0.000664 |
| P9c, ibm_marrakesh D=48 h, regret_random_lo95 | 0.195538 | 0.195233 | -0.000305 |
| P9c, ibm_marrakesh D=48 h, regret_random_hi95 | 0.214348 | 0.213277 | -0.001071 |
| P9c, ibm_marrakesh D=48 h, fid_stale | 0.860803 | 0.856659 | -0.004144 |
| P9c, ibm_marrakesh D=48 h, fid_stale_lo95 | 0.839010 | 0.834842 | -0.004168 |
| P9c, ibm_marrakesh D=48 h, fid_stale_hi95 | 0.879550 | 0.877211 | -0.002339 |
| P9c, ibm_marrakesh D=48 h, regret_stale | 0.056967 | 0.061453 | +0.004486 |
| P9c, ibm_marrakesh D=48 h, regret_stale_lo95 | 0.039927 | 0.043129 | +0.003202 |
| P9c, ibm_marrakesh D=48 h, regret_stale_hi95 | 0.076690 | 0.081321 | +0.004631 |
| P9c, ibm_marrakesh D=48 h, fid_window_mean | 0.886834 | 0.888168 | +0.001334 |
| P9c, ibm_marrakesh D=48 h, fid_window_mean_lo95 | 0.876646 | 0.877915 | +0.001269 |
| P9c, ibm_marrakesh D=48 h, fid_window_mean_hi95 | 0.896669 | 0.897895 | +0.001226 |
| P9c, ibm_marrakesh D=48 h, regret_window_mean | 0.030936 | 0.029944 | -0.000992 |
| P9c, ibm_marrakesh D=48 h, regret_window_mean_lo95 | 0.022353 | 0.021786 | -0.000567 |
| P9c, ibm_marrakesh D=48 h, regret_window_mean_hi95 | 0.040078 | 0.038984 | -0.001094 |
| P9c, ibm_marrakesh D=48 h, fid_std_adjusted | 0.875528 | 0.877284 | +0.001756 |
| P9c, ibm_marrakesh D=48 h, fid_std_adjusted_lo95 | 0.857969 | 0.861127 | +0.003158 |
| P9c, ibm_marrakesh D=48 h, fid_std_adjusted_hi95 | 0.890005 | 0.891102 | +0.001097 |
| P9c, ibm_marrakesh D=48 h, regret_std_adjusted | 0.042242 | 0.040828 | -0.001414 |
| P9c, ibm_marrakesh D=48 h, regret_std_adjusted_lo95 | 0.029096 | 0.028429 | -0.000667 |
| P9c, ibm_marrakesh D=48 h, regret_std_adjusted_hi95 | 0.056740 | 0.055069 | -0.001671 |
| P9c, ibm_marrakesh D=48 h, fid_shrinkage | 0.865706 | 0.865256 | -0.000450 |
| P9c, ibm_marrakesh D=48 h, fid_shrinkage_lo95 | 0.848956 | 0.849049 | +0.000093 |
| P9c, ibm_marrakesh D=48 h, fid_shrinkage_hi95 | 0.880953 | 0.879890 | -0.001063 |
| P9c, ibm_marrakesh D=48 h, regret_shrinkage | 0.052064 | 0.052856 | +0.000792 |
| P9c, ibm_marrakesh D=48 h, regret_shrinkage_lo95 | 0.037945 | 0.039302 | +0.001357 |
| P9c, ibm_marrakesh D=48 h, regret_shrinkage_hi95 | 0.066748 | 0.067319 | +0.000571 |
| P9c, ibm_marrakesh D=48 h, fid_ceiling | 0.917770 | 0.918112 | +0.000342 |
| P9c, ibm_marrakesh D=48 h, fid_ceiling_lo95 | 0.913537 | 0.914078 | +0.000541 |
| P9c, ibm_marrakesh D=48 h, fid_ceiling_hi95 | 0.921846 | 0.922022 | +0.000176 |
