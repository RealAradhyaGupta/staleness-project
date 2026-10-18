"""Engine settings. Every seed and threshold lives here and is printed into
the run log, as PROTOCOL.md section 16 requires.

OURS. Not part of the teammates' pipeline.
"""

# --- seeds fixed by PROTOCOL.md and Amendment A1 ---
SEED_SUBMIT = 20260828      # PROTOCOL.md section 4, the submission time draw
SEED_RANDOM = 20261013      # Amendment A1.7, the random layout arm
SEED_TRANSPILE = 11         # same as the team's config.py
SEED_SIM = 3                # same as the team's config.py; one seed per job

SHOTS = 4000
OPT_LEVEL = 2               # the team's config.py

# --- window and split (Amendment A1.6) ---
WINDOW_START = "2026-08-28"
TRAIN_END = "2026-09-20"    # training days: 28 Aug to 20 Sep inclusive
TEST_START = "2026-09-21"   # test days:     21 Sep to 12 Oct inclusive
WINDOW_END = "2026-10-12"

SUBMITS_PER_DAY = 3         # PROTOCOL.md section 4
DELAYS_H = [1, 3, 6, 12, 24, 48]

# --- dead qubit rule (L-016 decision 2, PROTOCOL.md section 7) ---
SX_DEAD = 0.1
RO_DEAD = 0.2

# --- predictors (Amendment A1.2 and A1.3) ---
WINDOW_N = 5                # "last N DISTINCT VALUES OF THAT FIELD"
# TUNED on training days only, Amendment A2 of 14 October 2026.
# Chosen by the pre-registered rule: lowest mean ESP regret vs the ceiling,
# ties to smaller N, then to smaller total w.
SHRINK_N = 3
SHRINK_W_BY_GROUP = {"readout": 0.5, "gate": 0.0, "times": 0.0}
# NOTE: the analytic ESP is blind to T1 and T2, so "times" was settled by the
# tie-break and not by evidence. See Amendment A2.2.
SHRINK_W = 0.5              # legacy single weight, used only if no group map

# --- Aer's real ceilings, measured not assumed (see L-023) ---
# Aer silently clamps above these and gives no warning: sx error 0.75 and 1.0
# produce the identical channel, and cz 0.9375 and 1.0 likewise.
AER_MAX_1Q = 0.75
AER_MAX_2Q = 0.9375
RANDOM_DRAWS = 5            # Amendment A1.7
