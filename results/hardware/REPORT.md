# Stage 6 Part A: results from real quantum hardware

Device: **ibm_kingston**. Protocol: `protocol_hardware.md`, hashed into
`FREEZE_HARDWARE.txt` at 2026-10-25T16:32:09Z, which is before the pilot job
and before every other job. Nothing in the analysis was decided after seeing a
number.

This stage did not touch Round 2. No frozen file, no rule, no protocol and no
Round 2 result was changed.

## 1. What was run

Three strategies choose which physical qubits to use, from the same
calibration card:

- **stale**: use the newest card, which is what a normal user does.
- **window_mean**: the Round 1 window mean, parameters unchanged.
- **hybrid**: the frozen rule in `scripts/30_hybrid_rule.py`, unchanged, with
  the weights for a 6 hour hold.

Four circuits: ghz5, ghz8, bv8, qft5. Three compile times two hours apart.
Each compiled job was held on this laptop for 6 hours and then submitted, so
the calibration card the choice was made from was 6 hours out of date by the
time the circuit actually ran. That gives 12 jobs. All three arms of a job sit
in the same Sampler job as separate PUBs at 1,000 shots each, so the three arms
share one queue position and one device state.

The comparison order was fixed in writing before any job was sent:
**primary is window_mean minus stale, secondary is hybrid minus stale.**

## 2. QPU usage against the cap

The cap for the whole stage was 180 seconds, which I set myself and which is
well inside the account's 10 minute allocation.

| job | usage (s) |
| --- | --- |
| pilot (Bell, 100 shots) | 2.000 |
| s1_bv8 | 3.000 |
| s1_ghz5 | 3.000 |
| s1_ghz8 | 2.000 |
| s1_qft5 | 3.000 |
| s2_bv8 | 3.000 |
| s2_ghz5 | 3.000 |
| s2_ghz8 | 3.000 |
| s2_qft5 | 3.000 |
| s3_bv8 | 3.000 |
| s3_ghz5 | 3.000 |
| s3_ghz8 | 3.000 |
| s3_qft5 | 3.000 |
| **TOTAL** | **37.000 s of the 180 s cap (20.6 percent)** |

The cap was never approached. IBM's own account counter moved from 0.0 s to
34.0 s, a change of 34.000 s. The guard deliberately uses whichever of the two
figures is larger, so it treated the total as 37.000 s. The cap was respected.

Before the run I projected 32.825 s for all 12 jobs from the pilot. The real
total for those 12 jobs was 35.000 s, so the projection was accurate to about
7 percent. s1_ghz8 cost 2.000 s instead of 3.000 s because all three arms gave
the same transpiled circuit there, so only one PUB was submitted.

Jobs were submitted strictly one at a time. Before each submission the script
read the usage so far from IBM, added 1.5 times the largest full job measured
so far, and refused to submit if that came out above 150 s. It also read the
account's remaining time and would have refused below 8 minutes remaining. If
the usage could not be read it would have refused to submit. None of those
guards ever had to fire.

## 3. The main result

Hellinger fidelity of the measured counts against the ideal noiseless
distribution. Bootstrap is 4,000 resamples of the 12 jobs, seed 20261025.
Jobs are the resampling unit because the three arms of a job share a queue
position.

| comparison | role | n | mean | SD | 95 percent interval |
| --- | --- | --- | --- | --- | --- |
| window_mean minus stale | PRIMARY | 12 | -0.01256 | 0.04382 | -0.03906 to +0.00710 |
| hybrid minus stale | secondary | 12 | +0.00018 | 0.02246 | -0.01253 to +0.01151 |
| hybrid minus window_mean | extra | 12 | +0.01274 | 0.04408 | -0.00276 to +0.03903 |

Mean fidelity: stale 0.8845, window_mean 0.8720, hybrid 0.8847.

In plain words: **on 12 real jobs neither corrected rule beat the plain stale
choice.** Every interval contains zero. The primary comparison, the window
mean, is negative on average on hardware, which is the opposite sign to the
+0.005346 it showed on Round 2's 2,824 simulated jobs. The hybrid came out at
essentially exactly zero.

I am not entitled to call that a contradiction of Round 2. Twelve jobs cannot
separate -0.013 from +0.005 when the paired SD is 0.044. All I can say is that
the hardware run did not reproduce the window mean's simulated advantage, and
that it is consistent with the hybrid being close to neutral at a 6 hour delay,
which is also what Round 2 found at that delay (-0.002282).

## 4. One job carries the primary number (post hoc, not pre-stated)

This was not in the protocol. I looked only after the result existed and I
label it as such.

| job | stale | window_mean | hybrid | wm - stale | hyb - stale |
| --- | --- | --- | --- | --- | --- |
| s1_bv8 | 0.8290 | 0.6960 | 0.8470 | -0.1330 | +0.0180 |
| s1_ghz5 | 0.9252 | 0.9439 | 0.9332 | +0.0188 | +0.0081 |
| s1_ghz8 | 0.8602 | 0.8602 | 0.8602 | 0.0000 | 0.0000 |
| s1_qft5 | 0.8694 | 0.8820 | 0.8820 | +0.0126 | +0.0126 |
| s2_bv8 | 0.8320 | 0.8260 | 0.8380 | -0.0060 | +0.0060 |
| s2_ghz5 | 0.9270 | 0.9232 | 0.9260 | -0.0038 | -0.0010 |
| s2_ghz8 | 0.8439 | 0.8815 | 0.8815 | +0.0376 | +0.0376 |
| s2_qft5 | 0.9159 | 0.8870 | 0.8870 | -0.0289 | -0.0289 |
| s3_bv8 | 0.8680 | 0.8750 | 0.8850 | +0.0070 | +0.0170 |
| s3_ghz5 | 0.9313 | 0.9390 | 0.9267 | +0.0077 | -0.0046 |
| s3_ghz8 | 0.8909 | 0.8744 | 0.8744 | -0.0165 | -0.0165 |
| s3_qft5 | 0.9215 | 0.8753 | 0.8753 | -0.0462 | -0.0462 |

One job, s1_bv8, has a difference of -0.1330. The other 11 are all between
-0.046 and +0.038. Drop s1_bv8 and the primary mean moves from -0.01256 to
-0.00161. Leaving each job out in turn moves the primary mean between -0.01712
and -0.00161, so no single job flips its sign, but a single job sets most of
its size.

In s1_bv8 the window mean put the circuit on physical qubits
45 41 134 42 56 154 44 43, while stale and hybrid both stayed in the
108 to 129 region. So the window mean moved the layout to a different part of
the chip and that part ran worse. The hybrid's taper kept it near the stale
choice and it did not pay that cost. This is a single observation on one
circuit and I draw no rule from it.

Also worth stating plainly: the deliberate design of running all three arms in
one job means the hybrid's small positive numbers cannot come from a different
queue position or a different device state. They come from the layout only.

## 5. Identical transpiled circuits

The protocol says that when two arms produce the identical transpiled circuit,
the circuit is run once, both arms are given that one result, the paired
difference is exactly 0, and the job is **counted, not dropped**. Dropping
ties would throw away every case where the correction changed nothing, which
would inflate any apparent effect.

- 29 PUBs were submitted for 12 jobs, and 36 arm results came back. 7 arm
  results were served by a circuit another arm had already produced.
- window_mean and stale identical in 1 of 12 jobs (8.3 percent). Layouts differ
  in 11 of 12.
- hybrid and stale identical in 1 of 12 jobs (8.3 percent). Layouts differ in
  11 of 12.
- hybrid and window_mean identical in 6 of 12 jobs (50.0 percent).

So the arms really were choosing different qubits in 11 of 12 jobs. The result
above is not a tie artefact.

## 6. By circuit

| circuit | n | F stale | F window_mean | F hybrid | wm - stale | hyb - stale |
| --- | --- | --- | --- | --- | --- | --- |
| bv8 | 3 | 0.8430 | 0.7990 | 0.8567 | -0.04400 | +0.01367 |
| ghz5 | 3 | 0.9278 | 0.9353 | 0.9286 | +0.00753 | +0.00082 |
| ghz8 | 3 | 0.8650 | 0.8720 | 0.8720 | +0.00705 | +0.00705 |
| qft5 | 3 | 0.9023 | 0.8814 | 0.8814 | -0.02081 | -0.02081 |

Three jobs per circuit. These are four numbers from three observations each and
should be read as description only.

## 7. Queue wait

This is IBM's running time minus its created time, and it is **not** the
staleness delay.

- n 12, median 1.6 s, range 1.2 s to 354.6 s.
- share under 1 hour: 12 of 12, 100.0 percent.

The queue was essentially empty all night. That matters for the honesty of the
design: **the 6 hour delay in this stage is a deliberate local hold, not a
natural queue delay.** The compiled circuits were serialised to disk and sat on
this laptop for 6 hours before being sent. A real user waiting 6 hours in a
queue would be a different and larger experiment than this one.

## 8. The actual hold D, and every delay

The analysis uses the **actual** measured hold for each job, not the planned
6 hours.

| job | compiled (UTC) | submitted (UTC) | actual D (h) | card used | card age at compile |
| --- | --- | --- | --- | --- | --- |
| s1_ghz5 | 16:36:16 | 22:36:21 | 6.0016 | 2026-10-25T14:35:43Z | 2.0092 h |
| s1_ghz8 | 16:36:16 | 22:36:36 | 6.0058 | 2026-10-25T14:35:43Z | 2.0092 h |
| s1_bv8 | 16:36:16 | 22:36:50 | 6.0096 | 2026-10-25T14:35:43Z | 2.0092 h |
| s1_qft5 | 16:36:16 | 22:37:02 | 6.0130 | 2026-10-25T14:35:43Z | 2.0092 h |
| s2_ghz5 | 18:36:17 | 00:36:23 | 6.0016 | 2026-10-25T16:35:15Z | 2.0173 h |
| s2_ghz8 | 18:36:17 | 00:36:39 | 6.0061 | 2026-10-25T16:35:15Z | 2.0173 h |
| s2_bv8 | 18:36:17 | 00:36:55 | 6.0106 | 2026-10-25T16:35:15Z | 2.0173 h |
| s2_qft5 | 18:36:17 | 00:37:09 | 6.0144 | 2026-10-25T16:35:15Z | 2.0173 h |
| s3_ghz5 | 20:35:55 | 02:35:59 | 6.0011 | 2026-10-25T16:35:15Z | 4.0113 h |
| s3_ghz8 | 20:35:55 | 02:41:46 | 6.0976 | 2026-10-25T16:35:15Z | 4.0113 h |
| s3_bv8 | 20:35:55 | 02:42:01 | 6.1015 | 2026-10-25T16:35:15Z | 4.0113 h |
| s3_qft5 | 20:35:55 | 02:47:01 | 6.1850 | 2026-10-25T16:35:15Z | 4.0113 h |

### Retries, delays, late compiles and missed jobs

- **Retries on IBM calls: none.** No network error occurred, so the 60 second
  retry loop never ran.
- **Late compiles: none.** All three compile slots happened at their planned
  times, so no job had to fall back to an older card than planned.
- **MISSED jobs: none.** All 12 jobs reached DONE.
- **SKIPPED_FOR_CAP jobs: none.**
- **Three jobs submitted slightly late**, logged as `late` events:
  s3_ghz8 at 6.098 h, s3_bv8 at 6.102 h and s3_qft5 at 6.185 h instead of
  6 h. The cause is the no overrun rule itself: jobs go out strictly one at a
  time and each waits for the previous job to finish and for its usage to be
  read from IBM before the next is allowed. In slot 3 that queueing pushed the
  later jobs a few minutes past their nominal submit time. The analysis uses
  the actual D of 6.098, 6.102 and 6.185 h for those jobs, not 6 h.
- Slot 3 used the 16:35:15Z card, which was 4.0113 h old at compile time rather
  than about 2 h. That is not a fault: the device simply had not published a
  newer calibration card by 20:35Z. The actual card timestamp and its age are
  recorded for every job above, as the protocol requires.

### One known cosmetic defect

`outputs/hardware/STATUS.txt` reports "jobs finished 13 of 12". It counts the
entries in the per job usage record, which also holds the pilot. The number of
real jobs is 12 and the usage total of 37.000 s is correct. I chose not to edit
the runner while it was executing, because the script was in the freeze list
and changing it mid run would have broken its hash for a status line. Recording
it here instead.

## 9. What this stage cannot show

- **12 jobs is a sanity check, not a significance test.** Round 2 measured a
  design effect of 9.400 across 11 days, so jobs close together in time move
  together and the honest intervals here are wide on purpose.
- **The 6 hour delay is a deliberate local hold, not a natural queue delay.**
  The real queue was under 6 minutes on every job.
- There is no ceiling arm on hardware, because that would need a card from the
  future. So there is no regret figure and no absolute claim about how much
  fidelity staleness costs.
- One device, one night, four circuits, one delay. Nothing here speaks to other
  machines, other delays or other circuit families.
- Any agreement with Round 2 is **consistent with**, never proved. The same
  holds for disagreement.

## 10. Files

- `outputs/hardware/hw_jobs.csv`: one row per arm per job, 36 rows, with the
  layout, fidelity, job id, card timestamp, compile and submit times, actual D,
  usage and queue wait.
- `outputs/hardware/hw_summary.json`: the numbers in section 3.
- `outputs/hardware/results/`: the raw counts returned for each job.
- `outputs/hardware/hw_console.txt`: the full run log, 500 lines.
- `outputs/hardware/analysis_console.txt`: the analysis output in full.
- `outputs/hardware/hw_state.json`: the restart state file.
- `outputs/hardware/compiled/`: the held circuits, as QPY.

The live calibration cards are in `data/hardware_cards/` and the store built
from them is in `data/clean_hw/` and `data/cache_hw/`. All four are gitignored,
the same rule `data/raw` follows. No key and no CRN appears in any file here.
