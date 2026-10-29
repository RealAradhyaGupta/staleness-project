# NOTES

Facts and numbers only.

## CORRECTION (L-049), 19 October 2026

The Comparison B number in the headline below has the WRONG SIGN. See
PROGRESS_LOG.md entry L-049. The headline text below this block is left exactly
as it was first written and is superseded on this one point only.

`scripts/20_analyse_results.py` computed the paired value as stale minus
shrinkage on fidelity while calling it the gain of shrinkage over stale. Higher
fidelity is better, so that sign is the wrong way round. The corrected numbers,
same data, same bootstrap seed 20261014:

    n = 1764 jobs over 22 days                 (unchanged)
    mean paired gain of shrinkage over stale   +0.00176
    95 percent interval                        [-0.00147, +0.00482]
      at  6 h   +0.00345   [-0.00030, +0.00725]
      at 24 h   -0.00003   [-0.00307, +0.00265]

Flipping the sign negates the whole bootstrap distribution, so each interval
bound becomes minus the other bound.

THE VERDICT DOES NOT CHANGE. Comparison B is still NULL: every interval still
includes zero. What changes is the direction of the point estimate. Shrinkage
was slightly better than stale on average, by about 0.0018 of fidelity pooled
and about 0.0034 at 6 h, but the interval includes zero, so no claim that
shrinkage beats using the newest card is made. The sentence below, "the point
estimate is negative, the method under test did not beat using the newest
card", is wrong in direction and is superseded by this block.

`scripts/23_independent_check.py` had the same inverted line, so the agreement
reported in L-042 was an agreement on a sign-flipped number. Both scripts are
fixed. Table A, the stale regret numbers and every other number in these notes
are unaffected, because they use ceiling minus stale, where a larger number
correctly means worse.

## HEADLINE, test period 21 Sep to 12 Oct 2026

### 1. The pre-registered fix did NOT work. Comparison B is null.

Per-field shrinkage (N=3, w_readout=0.5, w_gate=0.0, w_times=0.0) against
stale, D = 6 and 24 h pooled, paired by job, block bootstrap over whole days,
gap jobs excluded.

    n = 1764 jobs over 22 days
    mean paired gain of shrinkage over stale   -0.00176
    95 percent interval                        [-0.00482, +0.00147]
      at  6 h   -0.00345   [-0.00725, +0.00030]
      at 24 h   +0.00003   [-0.00265, +0.00307]

The interval includes zero and the point estimate is negative. The method
under test did not beat using the newest card. PROTOCOL.md prediction 5
expected this possibility.

Not promoted to a finding: the window_mean arm had lower mean regret than both
stale and shrinkage at every delay from 3 h on (0.0222 against 0.0367 for
stale at 48 h). It was not pre-registered as the fix and is labelled
EXPLORATORY everywhere.

### 2. What DID hold: staleness has a real cost. Comparison A.

Stale regret against the ceiling, gap jobs excluded.

    D (h)    n    no-change   mean regret   95 pct interval
        1   930      72.6%        +0.0059   [+0.0020, +0.0109]
        3   920      39.7%        +0.0171   [+0.0102, +0.0250]
        6   909      14.9%        +0.0230   [+0.0169, +0.0292]
       12   880       3.4%        +0.0259   [+0.0199, +0.0330]
       24   855       0.0%        +0.0245   [+0.0184, +0.0315]
       48   794       0.0%        +0.0367   [+0.0250, +0.0510]

Every interval is above zero.

### 3. Both numbers reproduce from a second, independent code path.

scripts/23_independent_check.py, written from scratch, sharing no code with
scripts/20_analyse_results.py, bootstrap seed 20261015 instead of 20261014.
42 numbers compared against L-039 at a tolerance of 0.0005: 0 over tolerance.
Largest difference on a point estimate 0.00005; largest on an interval bound
0.00036, which is bootstrap seed noise. Confirmed again at seed 777 with 20000
resamples.


## 2026-10-12: account and machines

Real backends visible: 3. All 156 qubits. Two-qubit basis gate: cz.

| machine | qubits | queue at 13:21 UTC |
|---|---|---|
| ibm_fez | 156 | 2 |
| ibm_kingston | 156 | 2 |
| ibm_marrakesh | 156 | 0 |

## 2026-10-12: saved calibration snapshots

Saved with scripts/04_save_snapshots.py. Files are read-only (a-w).
Filename is the snapshot last_update_date in UTC.

| file | last_update_date (UTC) | size |
|---|---|---|
| data/raw/ibm_fez/2026-10-12T12-34-33Z.json | 2026-10-12 12:34:33 | 1382.5 KB |
| data/raw/ibm_kingston/2026-10-12T13-09-02Z.json | 2026-10-12 13:09:02 | 1382.3 KB |
| data/raw/ibm_marrakesh/2026-10-12T12-20-38Z.json | 2026-10-12 12:20:38 | 1384.6 KB |

## 2026-10-12: ibm_kingston first 10 qubits, snapshot 13:09:02 UTC

| qubit | T1 us | T2 us | readout err | sx err |
|---|---|---|---|---|
| 0 | 277.782 | 309.523 | 0.0115967 | 0.000243905 |
| 1 | 361.682 | 551.333 | 0.00732422 | 0.000155728 |
| 2 | 161.489 | 97.5195 | 0.0057373 | 0.0000970114 |
| 3 | 142.419 | 171.637 | 0.00500488 | 0.000507097 |
| 4 | 258.944 | 59.8179 | 0.00744629 | 0.00030453 |
| 5 | 107.826 | 51.4881 | 0.00549316 | 0.000413124 |
| 6 | 274.719 | 102.93 | 0.0168457 | 0.000280011 |
| 7 | 294.194 | 77.2413 | 0.0115967 | 0.000243315 |
| 8 | 292.78 | 91.4153 | 0.015625 | 0.000301733 |
| 9 | 156.114 | 42.42 | 0.00622559 | 0.00023305 |

Example cz errors, same snapshot: cz(72,73) 0.00177422, cz(7,17) 0.00624437,
cz(67,68) 0.00178909. Pair errors are symmetric.

## 2026-10-12: can we get OLD calibration snapshots?

Tested on ibm_kingston. Today's snapshot for comparison: 2026-10-12 13:09:02 UTC.

Method that works: `backend.properties(datetime=<past datetime>)`.
Library maps it to the REST query param `updated_before`. It returns the
snapshot closest to but older than the date asked. Result is not cached.

| asked | returned last_update_date (UTC) | gap from today | really older |
|---|---|---|---|
| 1 day ago | 2026-10-11 12:47:15 | 24.36 h | yes |
| 3 days ago | 2026-10-09 12:54:09 | 72.25 h | yes |
| 7 days ago | 2026-10-05 12:28:13 | 168.68 h | yes |
| 30 days ago | 2026-09-12 13:14:23 | 719.91 h | yes |
| 60 days ago | 2026-08-13 | 60.1 d | yes |
| 90 days ago | 2026-07-14 | 90.0 d | yes |
| 180 days ago | 2026-04-15 | 180.0 d | yes |
| 365 days ago | 2025-10-12 | 365.0 d | yes |

Depth limit, found by binary search:
- deepest working request: 576 days back, asked 2025-03-15, returned 2025-03-15
- 577 days back and more: RequestsApiError 404, error code 1216
  "Backend ibm_kingston not found." So history starts about 2025-03-15.

One snapshot per day is published, around 12:00 to 13:00 UTC.

Method that does not work for history: `calibration_id`.
- `backend.calibration_id` is None on a normal backend object.
- The properties payload has no id field. Keys are backend_name,
  backend_version, last_update_date, qubits, gates, general, general_qlists.
- The package has no endpoint that lists calibration ids.
- `service.backend("ibm_kingston", calibration_id="latest")` and
  `calibration_id="2026-10-12"` both raise QiskitBackendNotFoundError.

Docstring note not triggered on this account: properties() documents
`NotImplementedError: If datetime is specified when IBM Quantum Compute is
used`. On this ibm_quantum_platform channel the datetime argument worked.

No quantum jobs were run. Read-only API calls only.

## 2026-10-12: correction to an earlier note

Earlier I wrote "one snapshot per day, published around 12:00 to 13:00 UTC".
That was wrong. It came from asking for past dates at the current clock time
(about 13:20 UTC), so I only ever saw snapshots published before that hour.
Asking at 23:59 UTC returns later snapshots. Hour of day of the 341 collected
snapshots (UTC): 23 h -> 214, 22 h -> 64, 21 h -> 11, 20 h -> 9, 18 h -> 7,
12 h -> 6, 16 h -> 5, 19 h -> 5, 14 h -> 4, 3 h -> 3, 9 h -> 3, 13 h -> 3,
1 h -> 2, 0 h -> 1, 2 h -> 1, 8 h -> 1, 15 h -> 1, 17 h -> 1.
Machines are recalibrated more than once a day. Asking at 23:59 UTC gives the
last snapshot of that day.

## 2026-10-12: 120 day history download

Window asked: 2026-06-15 to 2026-10-12 (120 days).
Method: backend.properties(datetime=<day at 23:59:00 UTC>) per machine per day.
Requests attempted: 357 (3 days already had a file). Pause 0.7 s between
requests, up to 3 retries. Failures: 0. Unavailable: 0.

| machine | saved | already had | duplicate | files on disk | distinct days | missing days | size |
|---|---|---|---|---|---|---|---|
| ibm_fez | 112 | 1 | 7 | 113 | 113 | 7 | 129 MB |
| ibm_kingston | 114 | 1 | 5 | 115 | 115 | 5 | 136 MB |
| ibm_marrakesh | 112 | 1 | 7 | 113 | 113 | 7 | 130 MB |

Total: 341 files, 395 MB. No day has more than one snapshot stored.
A "duplicate" means that day returned a snapshot already on disk, so no new
snapshot was published that day.

Missing days (no snapshot of their own):
- ibm_fez: 2026-06-28, 2026-07-06, 2026-08-08, 2026-08-09, 2026-08-11,
  2026-08-15, 2026-08-16
- ibm_kingston: 2026-06-28, 2026-07-06, 2026-08-14, 2026-08-15, 2026-08-16
- ibm_marrakesh: 2026-06-28, 2026-07-06, 2026-08-08, 2026-08-09, 2026-08-10,
  2026-08-15, 2026-08-16

2026-06-28, 2026-07-06, 2026-08-15 and 2026-08-16 are missing on all three
machines.

## 2026-10-12: clean tables

Built by scripts/09_build_tables.py from local JSON only, no API calls.

| file | rows | size | rows per snapshot |
|---|---|---|---|
| data/clean/qubits.csv | 53196 | 5.9 MB | 156 qubits |
| data/clean/pairs.csv | 59840 | 3.8 MB | 176 pairs |

qubits.csv columns: machine, snapshot_utc, qubit, t1_us, t2_us,
readout_error, sx_error. T1 and T2 are in microseconds as published.
pairs.csv columns: machine, snapshot_utc, qubit_a, qubit_b, cz_error,
with qubit_a < qubit_b.

Data quality facts:
- cz is published twice per pair, once per direction. The two directions
  disagreed in 0 cases out of all snapshots, so storing one row per unordered
  pair loses nothing.
- Missing values in qubits.csv: t1_us 191 rows, t2_us 333 rows, spread over
  263 snapshots. Both are left empty, not filled in. These sit on dead or bad
  qubits. Example: ibm_fez qubit 72 on 2026-06-15 has T1 8.64 us,
  readout_error 0.3385 and sx_error 1.0, with no T2 value.
- pairs.csv has 340 machine-and-snapshot groups while qubits.csv has 341. The
  snapshot ibm_kingston 2026-10-05T22:26:34Z contains no two-qubit gates at
  all, neither cz nor rzz, only the 12 single-qubit gate kinds. So that
  snapshot has 156 qubit rows and 0 pair rows.
- No missing values in pairs.csv.

No quantum jobs were run. Read-only API calls only.

## 2026-10-12: Part A, real publishing cadence (ibm_kingston)

Probed 5 days at 00:00, 04:00, 08:00, 12:00, 16:00, 20:00, 23:59 UTC.
"Distinct returned" counts the 00:00 answer, which always comes from the day
before.

| day | days ago | distinct returned | published that day | times published (UTC) |
|---|---|---|---|---|
| 2026-08-13 | 60 | 4 | 3 | 03:30:21, 07:25:03, 09:46:07 |
| 2026-08-28 | 45 | 7 | 6 | 03:35:20, 07:49:58, 11:25:53, 12:45:30, 18:59:43, 23:12:18 |
| 2026-09-12 | 30 | 7 | 6 | 03:30:03, 07:18:50, 10:43:26, 15:33:21, 18:32:34, 23:26:44 |
| 2026-09-27 | 15 | 7 | 6 | 01:59:11, 07:12:54, 11:26:18, 13:55:36, 19:29:13, 23:34:34 |
| 2026-10-10 | 2 | 7 | 6 | 03:25:33, 07:47:17, 11:27:34, 15:36:01, 19:19:27, 22:34:50 |

Result: 6 snapshots per day on 4 of the 5 days, roughly one every 4 hours.
2026-08-13 is the exception: 3 snapshots, and the 09:46:07 one was still the
newest at 23:59, a gap of about 14 hours.
Lower bound only: with 7 probes per day I cannot see more than 7 per day.
22 new snapshot files saved. ibm_kingston now has 137 files.

## 2026-10-12: Part B, dead qubits

Rule: sx_error > 0.1, or readout_error > 0.2, or T1 missing, or T2 missing.
Normal values are about 1e-4 for sx_error and 1e-2 for readout_error, so the
cuts sit far above normal and catch broken qubits, not merely poor ones.

| machine | mean dead of 156 | min | max | snapshots |
|---|---|---|---|---|
| ibm_fez | 1.65 | 1 | 4 | 113 |
| ibm_kingston | 4.61 | 3 | 8 | 137 |
| ibm_marrakesh | 5.59 | 3 | 13 | 113 |

Reason counts over all dead rows (one qubit can trip more than one):
sx_error > 0.1 -> 1022, readout_error > 0.2 -> 1195, T1 missing -> 213,
T2 missing -> 355.

## 2026-10-12: Part B, overlap of best choices against staleness gap

Score = readout_error + sx_error, lower is better. Top 10 live qubits per
snapshot. Top 20 cz pairs per snapshot where both qubits are live.
Gap computed from last_update_date inside the files, rounded to whole days,
kept between 1 and 30.
Snapshot comparisons used: 9579 for qubits, 9527 for pairs.
Mean live qubits per snapshot 152.0, so chance overlap = 10/152 = 0.066.
Mean eligible pairs per snapshot 167.1, so chance overlap = 20/167 = 0.120.

Shared best qubits out of 10:

| machine | 1 d | 2 d | 3 d | 7 d | 14 d | 30 d |
|---|---|---|---|---|---|---|
| ibm_fez | 0.253 | 0.254 | 0.250 | 0.275 | 0.249 | 0.235 |
| ibm_kingston | 0.266 | 0.257 | 0.266 | 0.258 | 0.237 | 0.232 |
| ibm_marrakesh | 0.283 | 0.278 | 0.261 | 0.255 | 0.248 | 0.226 |

Shared best cz pairs out of 20:

| machine | 1 d | 2 d | 3 d | 7 d | 14 d | 30 d |
|---|---|---|---|---|---|---|
| ibm_fez | 0.546 | 0.476 | 0.477 | 0.467 | 0.466 | 0.465 |
| ibm_kingston | 0.622 | 0.535 | 0.507 | 0.485 | 0.436 | 0.431 |
| ibm_marrakesh | 0.553 | 0.464 | 0.483 | 0.448 | 0.432 | 0.431 |

Both stay well above chance at every gap. Files:
outputs/overlap_qubits.png, outputs/overlap_pairs.png,
outputs/overlap_table.csv, outputs/overlap_curve_qubits.csv,
outputs/overlap_curve_pairs.csv.

Table rebuild after Part A: qubits.csv 56628 rows 6.2 MB, pairs.csv 63712 rows
4.0 MB, from 363 snapshot files. Missing values: t1_us 213, t2_us 355.

No quantum jobs were run. Read-only API calls only.

## 2026-10-12: true snapshot cadence (corrects the earlier "6 per day")

Measured by walking back along the real chain of snapshots: ask for the newest
snapshot at or before time T, read the returned last_update_date, then ask
again for one second before it. Writes nothing. Script: scripts/12_walkback_pilot.py
and a one-off density probe.

The earlier figure of "about 6 snapshots a day" was wrong. It came from probing
7 fixed clock times per day, so it could never return more than 7 distinct
snapshots. The real number is about 4 times higher.

| machine | UTC day | snapshots in that day | gap hours min / median / max |
|---|---|---|---|
| ibm_kingston | 2026-09-20 | 27 | 0.27 / 0.79 / 1.82 |
| ibm_kingston | 2026-08-29 | 26 | 0.36 / 0.77 / 1.74 |
| ibm_fez | 2026-09-20 | 29 | 0.33 / 0.81 / 1.69 |
| ibm_marrakesh | 2026-09-20 | 31 | 0.33 / 0.82 / 1.66 |

So all three machines publish roughly 26 to 31 snapshots per day, about one
every 45 to 50 minutes. This also contradicts IBM's documented 24 hour cadence.

Request speed measured on 8 consecutive walk-back requests, ibm_kingston:
min 1.27 s, median 1.53 s, max 2.46 s. Payload about 1050 KB each.
Connect plus backend lookup: 7.84 s once per run.

Compression measured on data/raw/ibm_kingston/2026-10-12T13-09-02Z.json:
plain as stored (indent=2) 1.35 MB, gzip 0.07 MB, 20.3x smaller.

## 2026-10-12: Part A estimate before running

Window 2026-08-28 00:00 UTC to now, 45.7 days.
- snapshots per machine per day: 26 to 31, used 28 for the estimate
- expected snapshots all 3 machines: about 3840
- already on disk inside the window: 158 files
- expected API requests: about 3845 (the walk-back must request every step even
  where the file is already held, because only the reply reveals where the
  previous snapshot sits)
- expected time: about 2 h 20 min at 2.2 s per request
- expected size: about 4.9 GB plain, about 260 MB gzipped
Chosen storage: gzip (.json.gz). Existing 363 plain .json files left untouched.

## 2026-10-12 20:24 UTC: stall and integrity check of what was on disk

Stall: last log line in logs/download_all_45d.log at 18:40:32 UTC, no process
alive at 20:24:35 UTC. About 1 h 44 min with no progress. Cause: one request
with no time limit never returned.

State at the stall (logs/walkback_state.json):
- ibm_fez: 1380 requests, done, covered 2026-08-28T01:04:26Z to
  2026-10-12T16:22:41Z
- ibm_kingston: 671 requests, not done, frontier 2026-09-17T13:32:11Z
- ibm_marrakesh: not started

Integrity of files on disk, all passed:
- gzip -t on 1971 .json.gz files: 0 broken
- JSON parse plus presence of the keys qubits and last_update_date on all 2334
  files (1971 .json.gz plus 363 .json): 0 bad
- leftover .part or .tmp files: 0
Files written are safe against a kill because the script writes a .part file
and renames only after the write completes.

File counts before the restart: ibm_fez 1449, ibm_kingston 772,
ibm_marrakesh 113.

## Download time limit added to scripts/13_download_all_snapshots.py

TIMEOUT_S = 60, TIMEOUT_TRIES = 3, SKIP_BACK = 30 min, MAX_SKIPS_IN_A_ROW = 5.
Worst case cost of one unanswerable point: about 184 s (3 x 60 s plus 2 x 2 s
pauses) instead of unlimited. Points given up on are appended to
logs/skipped_requests.log as timestamp, machine, requested time, note.
Alarm tested with a fake 600 s call and the limit set to 2 s: cancelled at
2.0 s, 4.0 s, 6.0 s then gave up; a normal call still worked afterwards.

## 2026-10-12 21:31 UTC: Part A download finished

Restart run (started 20:26:47 UTC, finished 21:31:53 UTC, 1 h 5 min):
- ibm_fez: skipped, already marked done in an earlier run (1380 requests)
- ibm_kingston: 489 requests, 458 new files, 30 already on disk, 0 skipped
  covered 2026-08-28T00:35:09Z to 2026-09-17T12:35:08Z this run
- ibm_marrakesh: 1283 requests, 1239 new files, 43 already on disk, 0 skipped
  covered 2026-08-28T01:11:22Z to 2026-10-12T19:53:05Z

The 60 second time limit fired once for real, at 20:35:50 UTC on
ibm_kingston: "no answer within 60s, timeout try 1 of 3". Try 2 answered, so
the walk continued. Cost 60 s. Total timeouts in the whole run: 1. Points
given up on: 0, so logs/skipped_requests.log was never created.

Files on disk now: ibm_fez 1449, ibm_kingston 1230, ibm_marrakesh 1352,
total 4031 files, 624 MB.
Final integrity check: gzip -t on 3668 .json.gz files 0 broken; JSON parse
plus qubits and last_update_date keys on all 4031 files 0 bad; 0 .part or
.tmp files.

Measured against the estimate: about 3840 snapshots expected, 4031 files held
(the extra includes 363 older plain .json files from Checkpoint 2 inside and
outside the window). Expected 4.9 GB plain, actual 624 MB because gzip was
used.

## 2026-10-12 to 13: clean tables over the full 45 day window

Built by scripts/15_build_tables_all.py from all 4031 files.
- data/clean/qubits.csv: 628836 rows, 69.1 MB
- data/clean/pairs.csv: 708576 rows, 44.6 MB
- rows with a missing value: qubits 7107, pairs 0
- cz pairs where the two directions disagreed: 0
- files skipped as a repeated timestamp: 0
- old tables kept as qubits_pre_all.csv.bak and pairs_pre_all.csv.bak
- data/raw 619.0 MB, data/clean 123.9 MB including the backups

### Item 1: cards per machine per day, inside 2026-08-28 onwards

                 cards in window   per day min / median / max
ibm_fez               1382              11 / 32 / 39
ibm_kingston          1159               9 / 26 / 35
ibm_marrakesh         1285               3 / 32 / 47

Gap between neighbouring cards, hours, inside the window:
ibm_fez       min 0.15, median 0.67, max 26.74
ibm_kingston  min 0.14, median 0.77, max 27.23
ibm_marrakesh min 0.08, median 0.66, max 27.77

Biggest in-window gaps with dates:
ibm_fez       26.74 h  2026-09-22 14:00 -> 2026-09-23 16:44 UTC
              12.77 h  2026-09-01 12:51 -> 2026-09-02 01:37
               8.76 h  2026-09-05 19:28 -> 2026-09-06 04:14
              gaps of 6 h or more: 3
ibm_kingston  27.23 h  2026-09-22 14:13 -> 2026-09-23 17:27 UTC
               9.29 h  2026-08-30 03:45 -> 2026-08-30 13:03
               6.73 h  2026-09-06 18:22 -> 2026-09-07 01:06
              gaps of 6 h or more: 5
ibm_marrakesh 27.77 h  2026-09-21 01:28 -> 2026-09-22 05:14 UTC
              24.71 h  2026-08-28 08:33 -> 2026-08-29 09:16
              24.26 h  2026-09-22 12:31 -> 2026-09-23 12:46
              gaps of 6 h or more: 8
All three machines have a gap of about 27 h ending 2026-09-22 or 2026-09-23,
so that looks platform wide and not per machine.

### Item 2: full vs partial updates, all neighbouring pairs

Built by scripts/16_card_quality.py. "Changed" means the float is not exactly
equal. Share = changed qubits / qubits present in both cards.

Median share changed is 0.000 for every field on every machine. Share of
neighbouring pairs with nothing changed, and with 95 percent or more changed:

ibm_fez        none changed    >=95% changed
  T1              96.7%            2.1%
  T2              96.7%            3.3%
  readout_error   86.8%           12.2%
  sx_error        96.8%            3.0%
  cz_error        96.7%            2.8%
ibm_kingston
  T1              96.1%            3.0%
  T2              96.1%            3.9%
  readout_error   87.2%           11.4%
  sx_error        96.1%            1.4%
  cz_error        96.4%            3.4%
ibm_marrakesh
  T1              96.6%            0.2%
  T2              96.6%            3.4%
  readout_error   83.2%           15.8%
  sx_error        96.4%            0.3%
  cz_error        96.2%            0.0%

On the pairs where the field did move (count, median share, share of those at
90 percent or more):
ibm_fez        T1 45 0.955 97.8% | T2 45 0.994 100% | readout 182 0.981 92.3%
               sx 44 0.974 100% | cz 45 0.960 100%
ibm_kingston   T1 45 0.961 100% | T2 45 0.987 100% | readout 148 0.984 89.9%
               sx 45 0.949 91.1% | cz 41 0.966 100%
ibm_marrakesh  T1 44 0.922 84.1% | T2 44 0.974 100% | readout 216 0.994 94.4%
               sx 46 0.929 89.1% | cz 49 0.920 77.6%

Neighbouring pairs where not one of the 5 fields moved:
ibm_fez 1069 of 1381 (77.4%), ibm_kingston 885 of 1158 (76.4%),
ibm_marrakesh 955 of 1284 (74.4%).

Hand check on 59 consecutive ibm_kingston pairs (2026-09-17 to 2026-09-20),
scratchpad script: 49 of 59 changed nothing in the 5 fields, and every pair
that did change moved one field type at a time across almost all qubits, for
example "readout_error:155", "cz_error:171", "T1:147,T2:154,sx_error:142".
Those same no-change cards still carried about 23 value-date strings that were
new to the card, so the card is republished with fresh dates on fields outside
the 5 I track.

### Item 3: age of each value inside its own card, hours

last_update_date of the card minus the date printed on the value itself.

ibm_fez        values   median    p90      max
  T1           215592   12.92    23.87   645.39
  T2           214210   12.45    23.19   178.16
  readout_error 215592   2.87     7.37    25.19
  sx_error     215592   12.88    23.70   178.26
  cz_error     486464   12.06    22.79   306.77
ibm_kingston
  T1           179645   12.58    24.18   132.85
  T2           179645   12.31    23.71  2662.32
  readout_error 180804   3.79     9.83    23.41
  sx_error     180804   12.65    24.73   335.93
  cz_error     406208   12.76    24.63   335.34
ibm_marrakesh
  T1           198064   13.55    24.40  5523.70
  T2           197135   12.81    23.25  5709.49
  readout_error 200460   2.23     7.01    16.73
  sx_error     200460   13.57    24.98   335.86
  cz_error     452320   12.94    23.95   335.95

2662 h is about 111 days. 5709 h is about 238 days.

### Item 4: unusable qubits per card, and cards with a missing section

Per card counts, window only. Rules used, stated plainly: a value is missing
if the key is absent; T1 or T2 not positive; readout_error at or above 0.5 is
a coin flip and carries no information; sx_error at or above 0.5, and the
separate count of sx_error exactly 1.0 which is how a dead gate is published.

ibm_fez, 1382 cards
  missing a value: min 1, median 1, max 1; cards with at least one 1382 (100%)
  T1 or T2 not positive: 0 cards
  readout_error >= 0.5: median 0, max 1; cards with at least one 49 (3.5%)
  sx_error >= 0.5: 0 cards
  cz pairs present: min 176, median 176, max 176
ibm_kingston, 1159 cards
  missing a value: min 1, median 1, max 1; cards with at least one 1159 (100%)
  T1 or T2 not positive: 0 cards
  readout_error >= 0.5: 0 cards
  sx_error >= 0.5: min 2, median 2, max 4; all 1159 cards (100%)
  sx_error exactly 1.0: min 2, median 2, max 4; all 1159 cards (100%)
  cz pairs present: min 0, median 176, max 176
ibm_marrakesh, 1285 cards
  missing a value: min 0, median 4, max 4; cards with at least one 1107 (86.1%)
  T1 or T2 not positive: 0 cards
  readout_error >= 0.5: median 0, max 2; cards with at least one 158 (12.3%)
  sx_error >= 0.5 and exactly 1.0: median 0, max 4; 178 cards (13.9%)
  cz pairs present: min 176, median 176, max 176

Cards with a missing or short section, counted by the exact problem text:
  1382  T2 only on 155/156 qubits                     (ibm_fez, every card)
  1154  T1 only on 155/156; T2 only on 155/156        (ibm_kingston)
   921  T1 only on 154/156; T2 only on 153/156        (ibm_marrakesh)
   182  T1 only on 153/156; T2 only on 153/156        (ibm_marrakesh)
   178  no problem found                              (ibm_marrakesh)
     5  no cz gates; T1 155/156; T2 155/156           (ibm_kingston)
     4  T1 only on 154/156; T2 only on 152/156        (ibm_marrakesh)

The 5 cards with no cz gates at all, all ibm_kingston, 1872 gates instead of
2576: 2026-10-05T20:35:03Z, 2026-10-05T21:17:39Z, 2026-10-05T22:13:15Z,
2026-10-05T22:26:34Z, 2026-10-06T00:42:52Z.

Per card table written to data/clean/card_quality.csv, 3826 rows.
Cards older than the window and skipped: ibm_fez 67, ibm_kingston 71,
ibm_marrakesh 67, total 205. 4031 files minus 205 is 3826.

### data/raw locked again

After the download finished, the three machine folders were set to mode 555
(dr-xr-xr-x): data/raw/ibm_fez, data/raw/ibm_kingston, data/raw/ibm_marrakesh.
Files were already 444. Verified with touch: "Permission denied".

## 2026-10-13: distinct calibration states (data/clean/states.csv)

Built by scripts/17_build_states.py. A state is a run of neighbouring cards
whose five fields (T1, T2, readout_error, sx_error, cz_error) are all exactly
equal. The state keeps the last_update_date of its first card. Window
2026-08-28 onwards, same as card_quality.csv. Full run log: logs/build_states.log.

states.csv: 921 rows, 28 columns, 264179 bytes.

### States per machine

| machine | cards in window | states | cards per state | states/day min, median, p90, max |
|---|---|---|---|---|
| ibm_fez | 1382 | 313 | 4.42 | 4, 7, 8, 12 |
| ibm_kingston | 1159 | 276 | 4.20 | 2, 6, 8, 10 |
| ibm_marrakesh | 1285 | 332 | 3.87 | 2, 8, 9, 11 |

Totals: 3826 cards collapse to 921 states, a factor of 4.15.
Cards per state: median 3 on all three machines, max 18 (ibm_fez), 14
(ibm_kingston), 12 (ibm_marrakesh).

Hours between consecutive states: ibm_fez min 0.22, median 2.60, p90 6.73,
max 26.74. ibm_kingston min 0.22, median 2.42, p90 8.45, max 27.23.
ibm_marrakesh min 0.29, median 2.41, p90 6.29, max 30.36.

States whose first card has a short or missing section: ibm_fez 0,
ibm_marrakesh 0, ibm_kingston 3 (state 226 2026-10-05T20:35:03Z, state 227
2026-10-05T22:13:15Z, state 228 2026-10-06T00:42:52Z, all "no cz_error").
cz_error is therefore present in 273 of 276 ibm_kingston states.

### Median age of a state's values at first publication, hours

Median over qubits or pairs of (first publication time minus the date printed
on the value itself).

| field | ibm_fez median / p90 / max | ibm_kingston | ibm_marrakesh |
|---|---|---|---|
| T1 | 7.44 / 23.54 / 32.60 | 7.27 / 23.59 / 30.35 | 10.08 / 22.75 / 29.07 |
| T2 | 7.44 / 23.54 / 32.60 | 7.26 / 23.58 / 30.33 | 10.08 / 22.75 / 29.06 |
| readout_error | 0.56 / 4.36 / 25.19 | 1.09 / 4.81 / 23.41 | 0.51 / 4.55 / 12.16 |
| sx_error | 13.08 / 23.94 / 48.13 | 13.99 / 24.62 / 57.24 | 14.18 / 23.53 / 51.15 |
| cz_error | 15.00 / 23.32 / 29.86 | 15.55 / 24.40 / 41.77 | 15.50 / 23.02 / 51.10 |

### Dead qubits per state, Checkpoint 3 rule

Rule: sx_error > 0.1, or readout_error > 0.2, or T1 missing, or T2 missing.
Same thresholds as scripts/11_overlap_analysis.py lines 25 to 26.
The three reason counts overlap, because one qubit can break several rules at
once, so they do not add up to dead_qubits.

| machine | dead per state min, median, p90, max | permanent (dead in every state) | dead in some states only |
|---|---|---|---|
| ibm_fez | 1, 1, 3, 5 | 1 qubit: 72 | 28 qubits |
| ibm_kingston | 3, 4, 5, 6 | 3 qubits: 113, 121, 146 | 14 qubits |
| ibm_marrakesh | 4, 6, 9, 13 | 4 qubits: 82, 94, 113, 130 | 87 qubits |

Most common dead sets: ibm_fez [72] in 181 of 313 states; ibm_kingston
[113 121 146] in 101 of 276; ibm_marrakesh [82 94 113 130] in 63 of 332.
Union of permanent defects across machines: 72, 82, 94, 113, 121, 130, 146.
Permanent defects are machine specific; only 113 is permanent on two machines
(ibm_kingston and ibm_marrakesh).

### Collapse check, done independently

Biggest state, ibm_fez state_id 143, 18 cards from 2026-09-17T03:32:48Z to
2026-09-18T01:07:35Z (21.58 hours). A separate script re-read the raw JSON and
compared 975 numbers per card with a plain nested loop: 0 differing and 0
extra across all 18 cards. All 18 last_update_date stamps are distinct.

### data/raw after this step

Unchanged. Folders still mode 555. File counts still ibm_fez 1449,
ibm_kingston 1230, ibm_marrakesh 1352. Files modified today after 09:40 IST: 0.

## 2026-10-13: teammates' drift_pipeline demo, run check

SYNTHETIC DATA. Not findings. 20 curated cycles made by the teammates'
synth_drift.py from assumptions in their config.py (SYNTH_SEED 7,
PERSISTENCE 0.6, VOL_MEDIAN 0.15, JUMP_RATE 0.05, JUMP 3x to 10x).
Code author: teammates, not me. See PROGRESS_LOG.md L-018.

drift_pipeline.zip sha256 80519dcecfec55b033377f0c9fe1ee16e1af46b742817afedb76ba5db916a77f
507935 bytes, mtime 2026-10-12 21:37. Unchanged before and after this step.

Environment: team_code/.venv on Python 3.12.4 (their README asks for 3.11 or
3.12; main project .venv is 3.13.7 and qiskit-aer has no 3.13 build).
Installed unchanged: qiskit 2.5.2, qiskit-aer 0.17.2, qiskit-ibm-runtime
0.50.0, pandas 3.0.6, scipy 1.18.1, matplotlib 3.11.2.
Main .venv untouched: still 3.13.7, qiskit_aer not importable there.

### Their summary table (synthetic), from analysis.py synthetic

| delay | n_pairs | blind | stale | trend | stability | oracle | staleness_cost | wilcoxon_p stability vs stale |
|---|---|---|---|---|---|---|---|---|
| 1 | 27 | 0.350 | 0.833 | 0.837 | 0.837 | 0.863 | 0.030 | 0.768 |
| 2 | 27 | 0.343 | 0.816 | 0.826 | 0.814 | 0.860 | 0.044 | 0.409 |
| 3 | 27 | 0.342 | 0.812 | 0.789 | 0.823 | 0.854 | 0.042 | 0.374 |
| 7 | 27 | 0.320 | 0.793 | 0.789 | 0.795 | 0.853 | 0.059 | 0.290 |

stability_beats_stale_share: 0.519, 0.407, 0.296, 0.333.
Drift: steadiest qubit swings 0.01, swingiest 0.80 (log10 units).
Matches their README section 6 digit for digit.

### Reproduction check

experiment.py synthetic re-run in team_code/rerun/: 20 snapshots, starting
cycles 4 to 12, delays [1,2,3,7], circuits ghz5/ghz8/bv8, 540 circuit versions
compiled, 540 rows written, 49 seconds.

sha256 results_synthetic.csv, zip and re-run both:
afd161059ecad53ec35c87450832d920880ecd04504a7d17a830ebc611716f69
summary_synthetic.csv and volatility_synthetic.csv also byte identical.

PNGs differ in bytes only: 96288/172806/82587 (zip) vs 80326/127235/62356
(re-run). Opened fidelity_vs_delay_synthetic.png from both and compared by
eye: same curves, same points, same captions, only text rendering differs.
Likely a different matplotlib version (their pin is matplotlib>=3.7). Not
confirmed which version they used.

### Safety

.env never opened. ingest_ibm.py (the only file with network or credential
code) never run. No quantum hardware; all runs were local Aer simulation.
data/raw folders still mode 555, 0 files modified today after 09:40 IST.

## 2026-10-14: what N and w mean, in plain words

Settings frozen for the test run (Amendments A2 and A3):

    N         = 3
    w_readout = 0.5
    w_gate    = 0.0     (sx error and cz error)
    w_times   = 0.0     (T1 and T2)

### What N is

N is how far back the rule looks, counted in DISTINCT VALUES OF ONE FIELD, not
in cards and not in states. IBM republishes a card about every 45 minutes but
only remeasures a given field about once a day (L-028), so most cards carry a
copy of the number before. N = 3 means "the last 3 times this field actually
changed".

Each field keeps its own window, so the windows cover different stretches of
time. Real example, ibm_kingston, state 100, first seen 2026-09-14 08:42:14Z:

    readout error, last 3 distinct values: states 100, 96, 95
        2026-09-14 08:42:14Z, 2026-09-13 23:29:30Z, 2026-09-13 17:02:52Z
        -> spans about 16 hours
    cz error, last 3 distinct values:      states 100, 99, 93
        2026-09-14 08:42:14Z, 2026-09-14 07:44:48Z, 2026-09-13 07:05:46Z
        -> spans about 26 hours

Same N, different amount of history, because the fields move at different
rates. That is the whole point of Amendment A1.2.

### What w is

w is how far to pull a value away from the newest reading and toward the median
of the window. All the arithmetic is in logs, because error rates span orders
of magnitude.

    predicted = exp( (1 - w) * ln(newest) + w * ln(median of last N) )

w = 0 means trust the newest reading completely, which is exactly the stale
rule. w = 1 means ignore the newest reading and use the median. w = 0.5 is
halfway, in log space, which is the geometric mean of the two.

### Worked example, ibm_kingston state 100, qubit 140, readout error

    newest distinct value (state 100)  0.224365
    one before            (state 96)   0.006226
    two before            (state 95)   0.005371
    median of the three                0.006226
    blend with w = 0.5                 0.037374

The newest reading is 36 times the one before it. The blend puts the qubit at
0.037374, which is 0.167 of the newest value.

Why this matters here: the dead qubit rule kills a qubit at readout error above
0.2. Under the stale rule qubit 140 reads 0.224365 and is DEAD, so the compiler
is not allowed to use it at all. Under the shrinkage rule it reads 0.037374 and
is alive. One noisy reading would have made the stale rule throw away a qubit
that the two previous readings say is fine.

Dead list for that state: stale [112, 113, 120, 121, 140, 146], shrinkage
[112, 113, 120, 121, 146].

Best 10 qubits by readout error for that state:

    stale      [10, 11, 38, 64, 93, 98, 109, 126, 147, 148]
    shrinkage  [10, 11, 21, 38, 42, 47, 98, 109, 110, 148]

They disagree on 8 of 10: 21, 42, 47, 64, 93, 110, 126, 147.

### Why N = 3 won on picking qubits, while N = 10 predicts values better

These are two different questions and they have different answers.

Predicting the value (Part B of step 8, logs/drift_study.log): the mean
absolute error in log space keeps FALLING as N grows, on nearly every field and
machine. ibm_fez cz error: 0.1960 at N=3, 0.1801 at N=5, 0.1785 at N=10.
ibm_fez T1: 0.2583, 0.2432, 0.2275. More history gives a better estimate of
where a qubit usually sits.

Picking qubits (Part C of step 8, outputs/tuning_training_only.json): the best
setting at each N by mean ESP regret was 0.014548 at N=3, 0.014640 at N=5 and
0.014581 at N=10. N = 3 won, and the whole spread across N is 0.000092, which
is about 13 percent of the 0.000695 gain the tuning achieved over stale.

Two reasons these disagree. First, the decision only needs the ORDER of qubits,
not accurate values; a rule can be worse at estimating every qubit and still
rank the top few correctly. Second, the prediction error is averaged over all
156 qubits, while the ESP regret only feels the 5 to 10 qubits a circuit
actually lands on.

A plausible mechanism, NOT established by anything measured here: a long window
keeps dragging in values from before a qubit genuinely changed, so when a real
change happens N = 10 is slower to follow it than N = 3. Our cards cannot
separate a remeasurement that moved from a qubit that moved, so this stays a
hypothesis.

The honest summary is that N barely matters for the decision. The knob that
mattered was w_readout: 0.0 gives 0.014981, 0.5 gives 0.014548 and 1.0 gives
0.015526, so half way beats both ends. w_gate preferred 0.0, meaning no
shrinkage at all on sx and cz error. And w_times could not be measured by ESP
and was then shown to be unable to affect any decision at all (Amendment A3).

## Test period results, 21 Sep to 12 Oct 2026

Run: 5648 of 5650 jobs, 33888 rows, 6 arms each, 0 duplicates.
2 jobs skipped (ibm_marrakesh bv10, truth states 233 and 237): qiskit-aer
0.17.2 cannot simulate them, see L-037. 0.035 percent of jobs.

Sanity checks (PROTOCOL.md section 12): all 4 pass.
  stale regret exactly 0 with no new state: 1305 jobs, max |regret| 0.0
  ceiling >= stale at every delay: yes
  random is the worst arm: 0.7334 vs stale 0.9027
  fixture checksum: afd161059ecad53ec35c87450832d920880ecd04504a7d17a830ebc611716f69

Primary A, stale regret vs ceiling, gap jobs excluded, block bootstrap by day:

  D (h)    n    no-change   mean regret   95 pct interval
      1   930      72.6%        +0.0059   [+0.0020, +0.0109]
      3   920      39.7%        +0.0171   [+0.0102, +0.0250]
      6   909      14.9%        +0.0230   [+0.0169, +0.0292]
     12   880       3.4%        +0.0259   [+0.0199, +0.0330]
     24   855       0.0%        +0.0245   [+0.0184, +0.0315]
     48   794       0.0%        +0.0367   [+0.0250, +0.0510]

Stale regret by new states crossed: 0 states 0.0000 (n=1205),
1 state 0.0289 (n=935), 2 or more 0.0280 (n=3148).

Primary B, shrinkage vs stale, D = 6 and 24 h pooled, paired, n = 1764:
  mean gain -0.00176, 95 pct [-0.00482, +0.00147]. Includes zero.
  at 6 h  -0.00345 [-0.00725, +0.00030]
  at 24 h +0.00003 [-0.00265, +0.00307]

Mean fidelity by arm and delay:

  D (h)  random  stale   window_mean  std_adjusted  shrinkage  ceiling
      1  0.7356  0.9118       0.9070        0.9076     0.9120   0.9177
      3  0.7317  0.9061       0.9109        0.9090     0.9093   0.9232
      6  0.7378  0.9057       0.9155        0.9107     0.9091   0.9287
     12  0.7320  0.8975       0.9039        0.9023     0.9002   0.9234
     24  0.7314  0.9034       0.9099        0.9054     0.9033   0.9279
     48  0.7286  0.8851       0.8996        0.8908     0.8889   0.9218

Mean regret by arm and delay (exploratory):

  D (h)  random  stale   window_mean  std_adjusted  shrinkage
      1  0.1822  0.0059       0.0107        0.0101     0.0057
      3  0.1915  0.0171       0.0123        0.0142     0.0139
      6  0.1909  0.0230       0.0132        0.0180     0.0195
     12  0.1914  0.0259       0.0195        0.0211     0.0232
     24  0.1964  0.0245       0.0180        0.0225     0.0245
     48  0.1932  0.0367       0.0222        0.0310     0.0329

Stale regret by machine and delay:

  D (h)  ibm_fez  ibm_kingston  ibm_marrakesh
      1   0.0011        0.0013         0.0152
      3   0.0034        0.0133         0.0350
      6   0.0094        0.0205         0.0396
     12   0.0143        0.0250         0.0379
     24   0.0124        0.0237         0.0365
     48   0.0142        0.0360         0.0570

22 to 23 Sep gap, separate: 360 of 5648 jobs overlap. Stale regret 0.0000
at 1 and 3 h, 0.0050 at 6 h, 0.0138 at 12 h, 0.0166 at 24 h, 0.0375 at 48 h.

Jobs where an arm used a qubit the truth device calls dead: random 786,
stale 81, shrinkage 66, std_adjusted 50, window_mean 42. No arm ever used a
qubit its own card called dead.

## 2026-10-14: the two counting questions answered

Sanity check 1 counts 1305 no-change jobs; table A's 0-states row has 1205.
Difference 100. Sanity check 1 runs on ALL 5648 jobs; table A excludes the 360
jobs touching the 22 to 23 Sep gap, and 100 of those crossed no new state.

n falls from 930 at D = 1 h to 794 at D = 48 h. Two causes, both in the
protocol:

    D (h)   jobs built   gap-excluded   kept in table A
        1          970             40               930
        3          960             40               920
        6          954             45               909
       12          945             65               880
       24          930             75               855
       48          889             95               794

930 - 794 = 136 = 81 fewer jobs built + 55 more jobs excluded as gap jobs.
The 81 come from PROTOCOL.md section 3 rule 3, which drops a job whose run
time falls after the last state on that machine; dropped (submission, delay)
slots by delay are 4, 6, 7, 9, 12, 20, each times 5 circuits. Of the 889 at
D = 48 h, one more is the Aer-skipped job. The 55 come from a longer
submission-to-run interval being more likely to overlap a fixed gap window.

## 2026-10-14: pre-registered outputs that the run never produced

Produced by scripts/24_prereg_outputs.py into outputs/prereg/, bootstrap seed
20261016. Full log in logs/prereg_outputs.log.

PRE-REGISTERED and previously missing: cz age at run time (PROTOCOL.md section
9 axis 2), readout age shown separately (section 9), mean ESP alongside mean
fidelity (section 8), permanent defect audit (section 7 and A1.5), dropped
jobs per delay with reason (section 3 and A1.7). Per machine (section 15
prediction 7) and the gap split (section 10) existed as bare means and now
carry intervals.

EXPLORATORY, not named in PROTOCOL.md: per circuit, and the full six strategy
per delay table.

### Stale regret against the age of the cz numbers it used (PRE-REGISTERED)

    cz age at run (h)     n   median age   mean regret   95 pct interval
    0 to 6              310        3.897        0.0058   [0.0005, 0.0164]
    6 to 12             680        8.957        0.0130   [0.0067, 0.0212]
    12 to 18            820       15.266        0.0235   [0.0156, 0.0317]
    18 to 24            764       20.931        0.0161   [0.0101, 0.0234]
    24 to 36           1250       27.963        0.0170   [0.0129, 0.0210]
    36 to 48            495       39.664        0.0305   [0.0170, 0.0506]
    48 or more          939       58.277        0.0386   [0.0242, 0.0580]

30 stale rows have no cz age and are left out: 5 ibm_kingston cards carry no
cz gates at all (L-008).

### Stale regret against readout error age at run time (PRE-REGISTERED)

    readout age (h)       n   median age   mean regret   95 pct interval
    0 to 6              950        4.173        0.0091   [0.0052, 0.0138]
    6 to 12            1404        8.383        0.0191   [0.0118, 0.0277]
    12 to 18            920       14.042        0.0241   [0.0178, 0.0313]
    18 to 24            280       19.791        0.0241   [0.0147, 0.0358]
    24 to 36            895       27.582        0.0229   [0.0167, 0.0299]
    36 to 48             40       42.579        0.0244   [0.0108, 0.0471]
    48 or more          799       51.941        0.0365   [0.0252, 0.0500]

The two clocks are not the same clock, over the same stale rows:

    cz age      mean 28.180 h, median 24.295, p25 14.664, p75 38.221, max 99.731
    readout age mean 19.626 h, median 13.396, p25  7.298, p75 27.189, max 76.481

### Mean ESP alongside mean fidelity (PRE-REGISTERED, section 8)

    D (h)   ceiling_esp  stale_esp  shrink_esp | ceiling_fid  stale_fid  shrink_fid
        1        0.9162     0.9104      0.9107 |      0.9177     0.9118      0.9120
        3        0.9218     0.9044      0.9078 |      0.9232     0.9061      0.9093
        6        0.9274     0.9040      0.9075 |      0.9287     0.9057      0.9091
       12        0.9222     0.8957      0.8986 |      0.9234     0.8975      0.9002
       24        0.9266     0.9014      0.9016 |      0.9279     0.9034      0.9033
       48        0.9208     0.8820      0.8860 |      0.9218     0.8851      0.8889

Full six-arm version in outputs/prereg/P3_esp_alongside_fidelity.csv.

### Permanent defect audit (PRE-REGISTERED, section 7 and A1.5)

Training-only lists: ibm_fez [72], ibm_kingston [113, 121, 146],
ibm_marrakesh [82, 94, 113, 130].

    machine         rows    n_forbidden min/median/max   permanent qubit ever used
    ibm_fez        11340              1 / 1 / 6          none
    ibm_kingston   11190              3 / 3 / 7          none
    ibm_marrakesh  11358              4 / 5 / 13         none

n_forbidden is that arm's own dead list UNION the permanent list, so it never
falls below n_permanent, and it never did.

### Jobs dropped per delay (PRE-REGISTERED, section 3 and A1.7)

Reason was `past_end` in every case: no_history 0 and no_truth 0 at every
delay, on all three machines. Dropped (submission, delay) slots, times 5
circuits, by delay: 4/20, 6/30, 7/35, 9/45, 12/60, 20/100.

## 2026-10-14: the 1025 rows where an arm used a truth-dead qubit

Descriptive only. 1025 of 33888 rows, 3.02 percent, over 842 distinct jobs.
Every one is a qubit the arm's OWN card called alive. No arm ever used a qubit
its own card called dead.

By arm:

    arm            rows   qubit instances   share of that arm's rows
    random          786              1036                    13.92%
    stale            81                81                     1.43%
    shrinkage        66                66                     1.17%
    std_adjusted     50                52                     0.89%
    window_mean      42                44                     0.74%
    ceiling           0                 0                     0.00%

By arm and delay, rows:

    D (h)   random  stale  window_mean  std_adjusted  shrinkage   all
        1       35      8            6             3          4    56
        3       82     12            4             3          8   109
        6      132     18            4            11         14   179
       12      183     12           15            14         16   240
       24      179      9            5             7         12   212
       48      175     22            8            12         12   229

By machine: ibm_fez 211, ibm_kingston 85, ibm_marrakesh 729.
ibm_kingston has 0 for every informed arm; all 85 are the random arm.

By new states crossed: 4 rows sit at 0 new states, all window_mean. That is
consistent by construction, because window_mean's predicted card is a mean and
not the latest card, so it can call a qubit alive that the latest card, which
is also the truth card when nothing changed, calls dead.

## 2026-10-14: report figures

scripts/26_report_figures.py, bootstrap seed 20261017, PNG at 300 dpi with a
CSV of the plotted numbers beside each one, in outputs/figures/.

    fig_a_six_strategies_all_machines    6 arms, fidelity + regret vs delay
    fig_a_six_strategies_ibm_fez         same, per machine
    fig_a_six_strategies_ibm_kingston
    fig_a_six_strategies_ibm_marrakesh
    fig_b_regret_by_new_states           regret by states crossed
    fig_c_stale_regret_per_machine       stale regret per machine vs delay
    fig_d_shrinkage_minus_stale          comparison B with intervals
    fig_e1_update_hour_per_machine       drift study, cz arrivals by UTC hour
    fig_e2_rank_persistence_by_lag       drift study, Spearman by lag
    fig_e3_winners_curse                 drift study, rank now / next / +3

Figure e panels are parsed from logs/drift_study.log, training days only, and
no training-day code was re-run.

## 2026-10-14: Aer "Kraus is empty", characterised

Draft issue and reproduction held privately in docs/aer_issue_draft/. Nothing
posted anywhere. Measured on qiskit-aer 0.17.2, qiskit 2.5.2, Python 3.12.4.

- Deterministic: 6 of 6 fresh processes fail on the same inputs and seed.
- Fails as the FIRST simulation in a clean process, which corrects part of
  L-037 for these 2 jobs.
- Sticky: once it fires, later simulations in the same process can fail too.
- Method independent: statevector and matrix_product_state both fail;
  density_matrix runs out of memory first.
- No empty Kraus on the Python side: 790 local quantum errors, 152 readout
  errors, 0 entries with zero terms.
- Depends on noise for qubits the circuit never touches. The circuit touches
  15 physical qubits; restricting the noise model to those 15 makes it run.
- Sharp measurement threshold: keeping 0 to 6 of the 9 measurements runs,
  keeping 7, 8 or 9 fails.
- The only non-Pauli entries are on 15 qubits with T2 > T1, which make
  thermal_relaxation_error return a Kraus channel. No single one of them
  reproduces the fault alone.
- NOT reproduced from invented numbers. The synthetic attempt builds 95 single
  term Kraus entries, more than the 18 in the real model, and runs clean.

<!-- Appended 2026-10-29 from outputs/protocol_headline/PREPARED_correction_NOTES.md.
     Appended at the end of the file, not inserted below the
     L-049 block, so no existing line is reworded. -->

## CORRECTION (L-053), 24 October 2026

The headline below was computed on 5288 jobs. The frozen protocol specifies
5648. See PROGRESS_LOG.md entries L-052 and L-053. The headline text below this
block is left exactly as it was first written and is superseded on this one
point only.

`scripts/20_analyse_results.py` runs both confirmatory comparisons on
`main_set = w[~w.touches_gap]`, dropping the 360 jobs that straddle a 22 to 23
September publishing gap. PROTOCOL.md section 10 says that gap "stays in",
results are "reported with it included", and the straddling jobs are "reported
separately so its effect is visible". Amendment A1.6 reaffirmed it. The
separate reporting was done; the inclusion was not.

Nothing was overwritten. Script 20 is unchanged and every reported number
stands. The protocol-faithful figures come from
`scripts/28_protocol_headline.py`, which imports the bootstrap, the seed
20261014 and the 4000 resamples from script 20, so only the job selection
differs, and which asserts that the 5288-job selection still reproduces every
reported number inside 0.0005.

Comparison A, mean stale regret against the ceiling:

    D       reported (5288)   protocol (5648)   protocol 95 pct interval
     1 h    +0.0059           +0.0057           [+0.0019, +0.0104]
     3 h    +0.0171           +0.0164           [+0.0096, +0.0242]
     6 h    +0.0230           +0.0221           [+0.0159, +0.0285]
    12 h    +0.0259           +0.0251           [+0.0192, +0.0319]
    24 h    +0.0245           +0.0239           [+0.0182, +0.0307]
    48 h    +0.0367           +0.0367           [+0.0263, +0.0494]

Comparison B on all 5648 jobs, gain = shrinkage minus stale, positive means
shrinkage is better:

      at  6 h   +0.00330   [-0.00037, +0.00694]
      at 24 h   -0.00004   [-0.00288, +0.00255]
      pooled    +0.00165   [-0.00126, +0.00458]

The 360 gap jobs on their own: Comparison A +0.0000, +0.0000, +0.0050, +0.0138,
+0.0166, +0.0375 by delay; Comparison B +0.00027 at 6 h, -0.00017 at 24 h.

NO VERDICT CHANGES. Comparison A is still positive at every delay with every
interval above zero and still grows with delay. Comparison B is still NULL at
6 h, at 24 h and pooled. The two sets of numbers are consistent with each
other, differing by at most 0.0008 of fidelity.

The headline moves slightly DOWN, not up, because during a publishing gap few
or no new states appear, so a stale card is often still correct. The no-change
share among the 360 gap jobs is 87.5 percent at 1 and 3 hours against 72.6 and
39.7 percent in the non-gap set, and their stale regret at those delays is
exactly 0.0000.

Second departure, recorded and not fixed: PROTOCOL.md section 11 defines
Comparison B "at D = 6 hours and D = 24 hours, pooled over machines and
circuits", which is two numbers, while script 20 headlines a third number that
also pools the two delays. Both are given above and the verdict is the same
either way.

The dead-qubit row share changes slightly because the stale arm now carries all
81 of its dead rows instead of 76: 20.99 percent of summed stale regret sits in
them, against the 20.41 percent recorded for the 5288-job set.

## Stage 6 Part A, real hardware, ibm_kingston, 25 to 26 Oct 2026

- Account: instance open-instance, open plan, 600 s allocated, 0 s used before.
- Freeze: FREEZE_HARDWARE.txt at 2026-10-25T16:32:09Z, before the pilot.
- t0 2026-10-25T16:32:39Z. 3 compile slots 2 h apart, 6 h hold, 12 jobs.
- Live cards fetched: 70, 2026-10-24T01:05:39Z to 2026-10-25T16:16:28Z.
- Store data/clean_hw: 376 distinct states, both reference checks IDENTICAL.
- Pilot Bell 100 shots: 2.000 s. Overhead 1.975 s per job.
- Projection for 12 jobs 32.825 s, actual 35.000 s. Guard was 150 s.
- Usage: 12 jobs DONE, 0 MISSED, 0 SKIPPED_FOR_CAP, 0 retries, 0 late compiles.
- TOTAL 37.000 s of the 180 s cap (20.6 percent). Account counter moved 34.0 s.
- Fidelity means: stale 0.8845, window_mean 0.8720, hybrid 0.8847.
- PRIMARY window_mean minus stale: -0.01256, SD 0.04382, 95 pct -0.03906 to +0.00710.
- secondary hybrid minus stale: +0.00018, SD 0.02246, 95 pct -0.01253 to +0.01151.
- extra hybrid minus window_mean: +0.01274, 95 pct -0.00276 to +0.03903.
- Bootstrap 4000 resamples of jobs, seed 20261025.
- Ties: 29 PUBs for 36 arm results. wm=stale 1/12, hyb=stale 1/12, hyb=wm 6/12.
- By circuit, wm minus stale: bv8 -0.04400, ghz5 +0.00753, ghz8 +0.00705, qft5 -0.02081.
- By circuit, hyb minus stale: bv8 +0.01367, ghz5 +0.00082, ghz8 +0.00705, qft5 -0.02081.
- Queue wait: median 1.6 s, range 1.2 to 354.6 s, 12/12 under 1 h.
- Actual hold D: 9 jobs 6.00 to 6.02 h, s3_ghz8 6.098, s3_bv8 6.102, s3_qft5 6.185.
- Slot 3 card 2026-10-25T16:35:15Z, 4.0113 h old at compile (no newer card existed).
- Post hoc: s1_bv8 alone is -0.1330. Drop it and PRIMARY moves to -0.00161.
  Leave one out range for PRIMARY: -0.01712 to -0.00161.

## Corrected Round 1 pack, all 5,648 jobs, no gap exclusion, 29 Oct 2026

- Source outputs/test_full/all_rows.csv, read only. 33,888 rows, 5,648 jobs, 22 days.
- Gap jobs: 360 of 5,648 overlap a gap window. Old pack headlined 5,288 only.
- Script scripts/45_round1_corrected_pack.py. Seeds unchanged: 20261017 figures,
  20261016 prereg, 20261014 Comparison A and sanity.
- Comparison A mean stale regret, old then new, by D:
  1 h 0.005937 -> 0.005692; 3 h 0.017115 -> 0.016402; 6 h 0.022962 -> 0.022116;
  12 h 0.025887 -> 0.025056; 24 h 0.024511 -> 0.023876; 48 h 0.036653 -> 0.036739.
- Comparison A n, old then new: 930->970, 920->960, 909->954, 880->945, 855->930,
  794->889.
- FAULT in old fig_d: it computed stale minus shrinkage under a label saying
  "positive = shrinkage better". Same fault L-049 fixed in script 20; the figure
  script never got the fix. Corrected to F_shrinkage minus F_stale.
- Comparison B, right sign, all jobs: 6 h n=954 +0.003297 [-0.000166, +0.006938];
  24 h n=930 -0.000041 [-0.002750, +0.002560];
  pooled n=1884 +0.001649 [-0.001391, +0.004533].
- All three intervals include zero. Verdict unchanged from L-039.
- Sanity checks on all jobs all PASS and reproduce the old numbers exactly:
  1,305 no-new-state jobs, largest absolute regret 0.0; ceiling minus stale
  +0.0057 at 1 h to +0.0367 at 48 h; random 0.7334 vs stale 0.9027; fixture sha ok.
- D1 to D6 byte identical to the originals: script 25 never excluded gap jobs.
- COMPARE.md holds 2,698 old vs new number lines. Median absolute difference 0.000685.
- Largest differences are counts, not estimates: P2b count +360, fig_b n +225.
- Secret scan over 31 new files: 0 leaks. 3 pattern hits, all the fixture sha256.
- No git repository exists, so nothing was committed or pushed.
- FREEZE.txt recheck: 13 of 16 match. scripts/31_analyse_round2.py,
  scripts/34_run_round2.py, scripts/35_build_round2_tables.py do NOT match.
  Their mtimes are 25 Oct 2026, so they changed during Round 2, not in this work.
- NOT DONE: the Round 1 report is not in the project, so report table and figure
  numbers could not be mapped and COMPARE.md could not be keyed to the abstract,
  conclusions, Section 4.3.6, Section 5.1, Table 7 or Table 19.
- NOT DONE: the independent check on all jobs. Script 23 has no saved output on
  any row set and was not rerun.
