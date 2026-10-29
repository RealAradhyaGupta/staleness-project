# Four scripts that no longer match their freeze checksums

Investigation only, 29 October 2026. No file was edited, moved or deleted, and
nothing was committed. Every rerun was done in a scratch folder outside the
project, with the scripts' own write paths redirected, so no output file, no
data folder and no frozen file was touched. The four scripts themselves were
read only: where a script had to be run with different output paths it was
loaded and its module level path constants were overridden in memory, never
edited on disk.

## The short version

**All four mismatches are real edits made after the freeze, all four are
deliberate bug fixes, and three of the four are logged with both checksums.
None of them touched the rule, and every saved output they produced is
reproduced byte for byte by the versions now on disk.**

The one genuine gap in the record is script 35: the log records its first new
checksum but then says "and then to a third value after the fault below"
without ever writing that third value down. The current checksum appears
nowhere in PROGRESS_LOG.md or NOTES.md.

## 1. Is there a copy of any frozen version anywhere? No.

| where I looked | result |
| --- | --- |
| the git clone `~/staleness-repo-export` working tree | tracks only scripts 01 to 26 plus two helpers; none of the four |
| every blob in that clone's git history, 107 objects, content hashed | no match |
| `scripts/__pycache__/` | holds only 30, 41 and 42; none of the four |
| `report_pack.zip` (18 Oct) and `drift_pipeline.zip` (12 Oct) | neither contains any of the four, and both predate Round 2 |
| `~/.Trash` | empty |
| VS Code local history, 667 files | no entry for any of the four |
| JetBrains caches, 4616 files | no match |
| every `.py`, `.py.*`, `.bak`, `*~`, `.orig`, `.save`, `.swp`, `.tmp` under the home folder, content hashed against all five frozen and intermediate checksums | no match |
| the project tree by filename | exactly one copy of each, the current one |

**No copy of any frozen version exists on this machine.** So no diff against a
frozen original can be produced for any of the four. That is stated as a
limit, not worked around. What the freeze files preserve is the checksum only.

### What the mtimes and sizes say instead

FREEZE.txt was written 2026-10-25 00:11:15 IST. FREEZE_HARDWARE.txt was
written 2026-10-25 22:02:09 IST. Against those:

| time (IST) | event |
| --- | --- |
| 00:11:15 | FREEZE.txt written |
| 01:18:59 | `35_build_round2_tables.py` last modified |
| 01:20:09 to 01:20:14 | script 35 run: `data/clean_r2`, `data/cache_r2`, `stage3_build_tables.txt` |
| 01:21:23 | `34_run_round2.py` last modified |
| 04:24:46 | script 34 run finished: `all_rows.csv`, `stage4_run.txt` |
| 04:34:11 | `31_analyse_round2.py` last modified, and `stage5_console_FIRST_RUN_gap_bug.txt` written |
| 04:34:16 | script 31 rerun: `r2_results.csv`, `stage5_console.txt` |
| 22:02:09 | FREEZE_HARDWARE.txt written |
| 22:03:36 to 22:03:47 | script 44 run, parts J and N: `J1`, `N1`, `N2` |
| 22:05:10 | `44_stage6_explore.py` last modified |
| 22:06:10 to 22:06:28 | script 44 run, parts K and M: `K1` to `K3`, `M_fresh/` |

Two things follow. Every edit is immediately followed by a run, which is the
signature of finding a fault and fixing it rather than of drift. And in every
case except one the saved output was produced by the version now on disk, so
reproducing it proves self-consistency and not that the frozen version agreed.

**The one exception is the most useful fact in this file.** Script 44's parts J
and N were written at 22:03, before the 22:05 edit, so those three files were
produced by the FROZEN version. They are reproduced byte for byte by the
current version. That is direct evidence that the edit changed nothing numeric
in those parts.

Sizes tell us little on their own and are recorded only for completeness:
31 is 18,005 bytes, 34 is 12,833, 35 is 10,208, 44 is 34,570.

## 2. Script by script

### scripts/31_analyse_round2.py (FREEZE.txt)

    frozen   6f79cbcd43f1d68d54995a7504d4ed537f5f0de99b0064a4a28908c34ecf5c9b
    current  74ecc570e67efab06eae51317a64afd4d17f2255e4d7d100feb933f623baea0f

**Logged, with both checksums, in PROGRESS_LOG.md entry L-057.** The script
imported `real_data` without setting the two store environment variables, so
its publishing-gap scan fell back to the Round 1 default `data/clean` and
scanned the development window instead of the fresh one. The engine was always
reading the right store; only the analysis script's gap scan was not. The fix
was to set the two variables at the top of the file with a comment saying why.

The evidence is preserved in the outputs. `stage5_console_FIRST_RUN_gap_bug.txt`
(04:34:11) against `stage5_console.txt` (04:34:16):

- first run: "jobs that straddle a publishing gap: 0", and no ibm_marrakesh gap
  listed at all;
- corrected run: 192 straddling jobs, 96 of them in the D = 6 to 48 h pool, and
  the ibm_marrakesh gap of 2026-10-22T20:25:11 to 2026-10-23T19:17:54, 22.88 h.

**Rerun on the frozen input, in a scratch folder.** Running the current script
with `--rows outputs/round2_run/all_rows.csv` reproduces all five saved files
byte for byte: `r2_results.csv`, `r2_jobs_wide.csv`, `r2_design_effects.csv`,
`r2_publishing_gaps.csv` and `r2_analysis_console.txt`. No differences at all.
(Running it with the default absolute input path reproduces the four data files
byte for byte and differs from the saved console in one line, the recorded
input path. That is my invocation, not the code.)

### scripts/34_run_round2.py (FREEZE.txt)

    frozen   467f82315089364ce18ae9bada56426abc062efe56888db96cc9ffee28896526
    current  a949b6bcceac9879490562d8ece0730839f860d77492868788b29dcae0cb1de5

**Logged, with both checksums, in PROGRESS_LOG.md entry L-056, as "Fault 2".**
On macOS multiprocessing uses "spawn", so every worker re-imports the module.
The file had `sys.exit(main())` at module level with no `if __name__ ==
"__main__":` guard, so each child tried to start its own workers and the first
pilot died in one second with all six workers failing. The fix was to add the
guard, with a comment. That comment and guard are at lines 294 to 301 of the
current file and match the logged description.

**Not fully rerun.** A full rerun is 4392 jobs, 26352 rows, about 2.88 hours on
6 workers. The task did not ask for it and I did not do it. What I did instead
was a 96-row spot check: `--pilot 2 --workers 2`, written to a scratch folder.
All 16 jobs matched a saved row on job identity, and of the 16 columns:

- 14 identical exactly, including `fidelity`, `esp`, `qubits_used`,
  `info_state`, `truth_state`, `new_states`, `job_seed`, `n_forbidden`,
  `hybrid_w_readout` and `guard_removed`;
- `label` differs because I passed `--label verify34`;
- `dead_qubits_used` is missing in both on all 96 rows, so it is identical once
  missing is compared as missing.

That slice is ibm_fez only, at D = 1 and 3 h, and exercises no dead qubit. It
is a spot check and not a verification of the whole file. I can run the full
2.88 hours on request.

### scripts/35_build_round2_tables.py (FREEZE.txt)

    frozen            c034342a878905bdb87cb7ab67b002ecbd26097ae04f153b64c37d11f5c0ec2d
    logged next value be900b19c90588d8c3e6185cb899e9dbfd2fcb61fc370c3d36c8cc7566f5c188
    current           094233a4bf441fe7d561141cf2a254b726b26c3ad008a9896a71983368740cdf

**This is the incomplete record.** PROGRESS_LOG.md entry L-056 describes two
successive edits and records the first new checksum, then says the hash went
"to a third value after the fault below" without writing that value. The
current checksum `094233a4...` appears nowhere in PROGRESS_LOG.md or NOTES.md.
The intermediate value `be900b19...` does not match any file on this machine
either, so that version is also gone.

Both edits are described in the log and both are to the VERIFICATION step, not
to the table building:

1. the strict check failed on `states.csv` for `last_card_utc` and `n_cards` on
   2 of 921 rows, both the last development state of their machine, because
   that state kept being republished into the fresh window. The check was
   narrowed so those two columns may grow on the boundary state only;
2. rewriting that check replaced a pandas `.equals` comparison with a numpy one
   and broke missing-value handling, flagging 918 identical rows of
   `short_section` as different. That was fixed.

**Structural reason this cannot change the store.** The tables are written at
steps 2 and 3 by `scripts/15_build_tables_all.py` and
`scripts/17_build_states.py`, invoked through script 35's own `run_script`
helper with only `RAW` and `CLEAN` overridden. Those two scripts are not pinned
by FREEZE.txt and are unmodified since 12 and 13 October, before Round 2 began.
The edited `compare()` function runs at step 4, after the tables are already
written, and only validates them.

**Rerun with LINKS, CLEAN_R2 and CACHE_R2 redirected to scratch.** This mattered
because `build_links()` and `main()` call `shutil.rmtree` on
`data/round2_cards`, `data/clean_r2` and `data/cache_r2`; redirecting kept all
three untouched, which I confirmed by entry count and mtime before and after.
Results:

- `qubits.csv` identical, 93,758,263 bytes, 628,836 rows;
- `pairs.csv` identical, 60,543,708 bytes, 708,576 rows;
- `states.csv` identical, 360,699 bytes, 921 development rows;
- all three `.npz` caches identical array for array, once missing values are
  compared as equal. The raw byte compare fails only because `np.array_equal`
  treats NaN as unequal to itself and `t1`, `t2` and `err_2q` legitimately
  contain missing values.

The builder's own development-window check passed on the rerun, reporting the
same two boundary-state growths the log describes: fez `n_cards` 3 to 5,
kingston 6 to 7.

### scripts/44_stage6_explore.py (FREEZE_HARDWARE.txt)

    frozen   59cd5d1faef78bc164084b321c60e3b428eaa327621a18a23723075e7a003fc7
    current  c044da565fc9fbcbd92cdf60e18eee7ece0c3d1678b9b469b1b5b84ce3b3dd91

**Logged, with both checksums, in PROGRESS_LOG.md entry L-058.** Part J printed
a circular standard deviation of the clock hour and compared it against a
claimed maximum of 6.93 h. That ceiling is wrong, because the circular SD is
not bounded. The printed column was replaced with the resultant length R, which
runs from 0 to 1, plus the share of changes in the busiest 6 hour block. The
log states the unbounded number stays in the CSV.

**Rerun, both groups, into scratch.** All 12 outputs are byte identical:

- parts J and N, written at 22:03 BEFORE the 22:05 edit: `J1_change_intervals.csv`,
  `N1_hybrid_vs_window.csv`, `N2_dead_qubit_share.csv` all identical;
- parts K and M, written at 22:06 after it: `K1`, `K2`, `K3` and all six
  `M_fresh/` files all identical;
- the printed console text reproduces `KM_console.txt` exactly, the only
  difference being the final "files written to" path line.

`J1_change_intervals.csv` carries `clock_R`, `clock_sd_h` and
`busiest_6h_share` together, and that file, produced by the frozen version, is
reproduced unchanged. So the edit added nothing to and removed nothing from the
CSV: it changed which column is displayed in the console and in
`REPORT_EXPLORATORY.md`. `KM_console.txt` is not written by the script; it was
a shell redirect.

## 3. Could any edit have changed a reported number?

| script | comment, formatting or logic | could it change a number? |
| --- | --- | --- |
| 31 | logic, two environment variable assignments plus a comment | **Yes, and it did. The reported numbers are the fixed ones.** |
| 34 | logic, a control flow guard plus a comment | No |
| 35 | logic, but only inside the verification check | No |
| 44 | logic, but only in what is printed | Presentation only, no CSV number |

**Script 31 is the only one that changed a reported number, and it changed it
by fixing a fault.** Before the fix the report would have said zero fresh jobs
straddle a publishing gap and would have missed the ibm_marrakesh gap entirely.
The whole gap section of `REPORT.md`, the 192 straddling jobs, the 96 in the
pool and the -0.027813 figure, exists only because of this fix. Beyond that:

- every point estimate is unchanged between the two runs, because H1, H2 and
  the arm comparisons come from the rows file and not from the store scan. The
  means are identical to all printed digits: 0.000151, 0.005346, 0.000843,
  0.001897, 0.044053 and so on;
- the bootstrap interval bounds moved in the fourth decimal. For example H2
  went from [-0.008722, 0.007241] to [-0.008739, 0.007228]. The reason is the
  shared random stream: with 0 gap jobs the gap test returned early without
  drawing, and with 192 it draws 4000 resamples, which shifts every later
  test's position in the one stream. This is the same mechanism documented in
  `outputs/round2/NOTE_three_intervals.md`, and the log records it.

**Script 34's guard cannot change arithmetic.** It only stops child processes
re-entering `main()`. Each job's simulator seed is computed from the job's own
identity in `job_seed_of`, `SEED_SIM + draw_order * 1000 + delay_h * 10 +
circuit index`, so a result does not depend on which worker ran it or in what
order. And without the guard the run died in one second, so the frozen version
could not have produced `all_rows.csv` at all.

**Script 35's edits were to the check, not the build**, and the rerun
reproduces the entire store exactly.

**Script 44 is Part B, which is exploratory and post hoc throughout**, and no
Part A file and no hardware number depends on it.

## 4. The rule itself is intact

This is the thing worth being sure of, and it is verifiable rather than
assumed:

- the w(D) table embedded in FREEZE.txt still hashes to its own recorded
  `fe3e3dee...`, so the freeze record is internally consistent;
- that table cross-checks against `outputs/round2/stage1_fitted_rule.json`
  exactly: guard M = 1, and N and the full w(D) curve match for all four field
  groups, cz, readout, sx and times;
- `scripts/30_hybrid_rule.py`, which holds the rule and the permanent defect
  list, still matches its frozen checksum, as does `scripts/33_round2_fit.py`,
  which produced the fit;
- the whole engine still matches: `run_engine.py`, `real_data.py`,
  `strategies.py`, `jobs.py`, `circuits.py`, `engine_config.py`,
  `snapshot.py`;
- `scripts/20_analyse_results.py`, `36_freeze_tests.py`, `37_round2_freeze.py`
  and `protocol_round2.md` all match;
- in FREEZE_HARDWARE.txt everything matches except script 44, including
  `scripts/43_hw_analyse.py`, which is what produced the reported hardware
  numbers.

None of the four changed scripts is the rule. They are the store builder, the
run harness, the analysis script and an exploratory script.

## 5. What I could not determine

1. **What the frozen versions actually contained.** No copy survives, so no
   diff is possible for any of the four. Everything above rests on the logged
   descriptions, the mtimes, and reproducing the saved outputs.
2. **Whether the frozen version of 31, 34 or 35 would have produced the same
   numbers.** For those three the saved outputs were produced after the edit,
   so reproducing them shows self-consistency only. Script 44 is the single
   case with real before-and-after evidence, and there the answer is yes.
3. **Script 35's missing checksum.** The log never recorded the third hash, so
   the record does not account for the file now on disk even though it
   describes the change that produced it.
4. **Whether `all_rows.csv` as a whole is what the frozen 34 would have
   produced.** My check covers 96 of 26,352 rows, one machine, two delays, and
   no dead-qubit case. The structural argument that a `__main__` guard cannot
   change arithmetic is strong, but it is an argument and not a measurement.
5. **Whether anything else was changed in the same edits** beyond what the log
   describes. With no frozen copy I can only say the outputs are reproduced and
   the logged descriptions match what is in the files now.

## 6. What this means for the freeze record

The freeze did its job: it detected four real changes. What it did not do is
preserve the frozen bytes, so the only way to check a mismatch now is to rerun
and compare outputs, which cannot distinguish "the edit was harmless" from "the
edit changed something and the saved output was regenerated afterwards".

Two things would fix that for a future round, and neither is a change to any
existing number: keep a copy of each frozen file alongside its checksum, for
example in a read-only `frozen/` folder or a git tag, and record the new
checksum in the log every time a pinned file changes, which was done for three
of these four and left incomplete for the fourth.

Nothing in this file changes any Round 1, Round 2 or hardware number.
