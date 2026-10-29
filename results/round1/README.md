# Corrected Round 1 pack

Every test-period table of the Round 1 pack, rebuilt on **all 5,648 jobs**
with **no gap exclusion**, as PROTOCOL.md section 10 requires. Per-delay
numbers follow section 11.

Built by `scripts/45_round1_corrected_pack.py` from
`outputs/test_full/all_rows.csv`, read only. No IBM call, no hardware job,
no new modelling choice. Nothing in `engine/` and no frozen script was
edited: scripts 20, 24, 25 and 26 are loaded out of their own source so
the bootstrap and loader arithmetic is literally theirs.

Sign conventions, unchanged:

- regret = `F_ceiling` minus `F_strategy`
- gain = `F_strategy` minus `F_stale`

## What changed from the original pack

1. **No gap exclusion.** The original pack reported the 360 jobs that
   straddle the 22 to 23 September publishing gap separately but **also**
   dropped them from every headline. They are now inside every file here,
   and still reported on their own in `P5_gap_jobs.csv`.
2. **The `fig_d` sign is fixed.** The original computed `stale - shrinkage`
   under a label that said "positive = shrinkage better". It now reports
   `F_shrinkage minus F_stale`, with a new `sign` column spelling that out.
   This is the same correction `scripts/20_analyse_results.py` already
   carries from L-049. The verdict does not change: every interval still
   includes zero.
3. **Comparison B is reported at 6 h and at 24 h separately**, which is
   what PROTOCOL.md section 11 comparison B fixed in advance. The pooled
   figure is kept and labelled as an extra, not as the headline.

Each file keeps its original bootstrap seed, so a difference against the
old pack is the row set or the sign fix, never a different seed.

## Which original file each file replaces

| file here | replaces | changed? |
| --- | --- | --- |
| `numbers/figure_csv/fig_a_six_strategies_all_machines.csv` | `report_pack/numbers/figure_csv/` same name | yes, +360 jobs |
| `numbers/figure_csv/fig_a_six_strategies_ibm_fez.csv` | same name | yes, +360 jobs |
| `numbers/figure_csv/fig_a_six_strategies_ibm_kingston.csv` | same name | yes, +360 jobs |
| `numbers/figure_csv/fig_a_six_strategies_ibm_marrakesh.csv` | same name | yes, +360 jobs |
| `numbers/figure_csv/fig_b_regret_by_new_states.csv` | same name | yes, +360 jobs |
| `numbers/figure_csv/fig_c_stale_regret_per_machine.csv` | same name | yes, +360 jobs |
| `numbers/figure_csv/fig_d_shrinkage_minus_stale.csv` | same name | yes, +360 jobs **and the sign fix**, plus a new `sign` column |
| `numbers/prereg/P1_cz_age_at_run_stale_regret.csv` | `report_pack/numbers/prereg/` same name | yes, +360 jobs |
| `numbers/prereg/P1b_cz_age_at_run_all_arms.csv` | same name | yes, +360 jobs |
| `numbers/prereg/P2_readout_age_at_run_stale_regret.csv` | same name | yes, +360 jobs |
| `numbers/prereg/P2b_age_distributions.csv` | same name | yes, +360 jobs |
| `numbers/prereg/P3_esp_alongside_fidelity.csv` | same name | yes, +360 jobs |
| `numbers/prereg/P4_stale_regret_per_machine.csv` | same name | yes, +360 jobs |
| `numbers/prereg/P5_gap_jobs.csv` | same name | no change in content: it was always the gap jobs alone. Kept because section 10 asks for them separately as well as inside |
| `numbers/prereg/P5b_gap_jobs_per_machine.csv` | same name | no change, same reason |
| `numbers/prereg/P8_stale_regret_per_circuit_EXPLORATORY.csv` | same name | yes, +360 jobs |
| `numbers/prereg/P9_six_strategy_table_EXPLORATORY.csv` | same name | yes, +360 jobs |
| `numbers/prereg/P9c_six_strategy_table_per_machine_EXPLORATORY.csv` | same name | yes, +360 jobs |
| `numbers/prereg/D1_dead_qubit_rows_by_arm.csv` | same name | **no**, byte identical |
| `numbers/prereg/D2_dead_qubit_rows_by_delay.csv` | same name | **no**, byte identical |
| `numbers/prereg/D3_dead_qubit_rows_by_arm_and_delay.csv` | same name | **no**, byte identical |
| `numbers/prereg/D4_dead_qubit_rows_informed_arms.csv` | same name | **no**, byte identical |
| `numbers/prereg/D5_dead_qubit_rows_by_machine_and_arm.csv` | same name | **no**, byte identical |
| `numbers/prereg/D6_dead_qubit_rows_by_new_states.csv` | same name | **no**, byte identical |
| `sanity_checks_all_jobs.txt` | `report_pack/numbers/sanity_checks_and_independent_check.txt` | section 1 is now recomputed instead of quoted. Section 2 is not reproducible, see below |
| `comparison_A_stale_regret_all_jobs.csv` | no single original file; the old pack had Comparison A only inside the `fig_a` regret panel | new |
| `COMPARE.md` | new | old against new, one line per number |
| `READABLE_TABLES.txt` | new | every table above as readable text |
| `console_output.txt` | new | what the script printed |

The D1 to D6 files are byte identical because
`scripts/25_dead_qubit_rows.py` never applied a gap exclusion, so those
six were already on all 5,648 jobs. They are regenerated here and compared
byte for byte rather than assumed unchanged.

Files that do not depend on the test jobs are not in this pack, as the
addendum says they are not needed: the overlap tables, the drift study
panels (`fig_e1`, `fig_e2`, `fig_e3`), the tuning files, `P6` and `P6b`
(the permanent defect audit) and `P7` (dropped jobs per delay).

## What could not be done

**The Round 1 report itself is not in this project.** There is no document
anywhere in the tree with an abstract, a conclusions section, a Section
4.3.6, a Section 5.1, or tables and figures numbered 7 to 25: no `.md`,
`.txt`, `.pdf`, `.docx`, `.tex` or `.odt` file contains them. So:

- Mapping each file here to a report table number (Table 9, Table 7,
  Tables 10 to 17, Table 19, Figures 16 to 25) **could not be done**. I
  have not guessed a mapping.
- `COMPARE.md` could not be keyed to the abstract, the conclusions,
  Section 4.3.6, Section 5.1, Table 7 and Table 19. Instead it compares
  **every** number in the saved Round 1 CSV files, old against new, which
  covers whichever of them the report quotes. No old value is estimated.
- **Table 15** asked for ESP and fidelity for ceiling, stale and
  shrinkage. `P3_esp_alongside_fidelity.csv` carries ESP and fidelity for
  all six arms per delay, which contains those three, but I cannot confirm
  it is the file the report's Table 15 was built from.
- **Section 2 of the sanity file**, the independent check, is not
  reproduced on all jobs. `scripts/23_independent_check.py` was written
  for the gap-excluded set and was never run with `--json-out`, so no
  saved output exists for it on any row set. It is not rerun and not
  estimated.

Nothing in this pack was committed or pushed; the project is not a git
repository.
