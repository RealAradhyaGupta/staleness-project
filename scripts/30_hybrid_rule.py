"""The Round 2 hybrid rule, frozen.

Fitted on development cards only (28 Aug to 12 Oct 2026) by
scripts/33_round2_fit.py. The numbers below are written out here by hand so
that this file, and its SHA-256 in FREEZE.txt, IS the rule. The fitted JSON is
read at import time only to check the two agree; if they ever disagree this
module refuses to load.

What the rule does, in plain words. At submission time the newest calibration
card is the obvious thing to trust, but it is one noisy measurement and it
ages. So for each field we predict the run-time value as a blend: part the
newest number, part the median of the last N distinct numbers of that same
field. The weight on the median rises with the delay, because the older the
newest card is, the less it is worth. On top of that a guard removes any qubit
that looked dead in the last M distinct states, so a qubit that just failed is
never chosen.

  predicted log value = (1 - w(D)) * newest + w(D) * median of last N distinct

All averaging is on the log of each value, as everywhere else in this project,
because error rates span orders of magnitude.

Sign conventions, as in every file here:
  regret = ceiling minus strategy (positive means the strategy is worse)
  gain   = F_strategy minus F_stale (positive means the strategy is better)
"""
import json
import sys
import warnings
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT / "engine") not in sys.path:
    sys.path.insert(0, str(ROOT / "engine"))

import real_data as rd          # noqa: E402
import strategies as strat      # noqa: E402

# Expected, and explained the same way in engine/strategies.py: a qubit that is
# missing a field in EVERY one of the last N distinct values gives an all-NaN
# column, and numpy warns on the median of it. The value is never used, because
# such a qubit is dead by the PROTOCOL.md section 7 rule and is removed from
# the target before the compiler sees it. This hides no failure: the forbidden
# count goes into every output row as n_forbidden.
warnings.filterwarnings("ignore", r"(Mean|All-NaN).*", RuntimeWarning)

# ---------------------------------------------------------------- the rule

RULE_NAME = "hybrid_round2"
RULE_FITTED_ON = ("2026-08-28", "2026-10-12")

# how many distinct values of that field the median is taken over
N_BY_GROUP = {"readout": 12, "sx": 5, "cz": 12, "times": 12}

# the weight on the median, by field group and delay in hours
W_BY_GROUP_AND_DELAY = {
    "readout": {1: 0.15, 3: 0.40, 6: 0.65, 12: 0.85, 24: 0.90, 48: 0.90},
    "sx":      {1: 0.05, 3: 0.05, 6: 0.15, 12: 0.30, 24: 0.55, 48: 0.70},
    "cz":      {1: 0.00, 3: 0.05, 6: 0.10, 12: 0.25, 24: 0.45, 48: 0.55},
    "times":   {1: 0.00, 3: 0.10, 6: 0.15, 12: 0.35, 24: 0.80, 48: 0.90},
}

# the dead qubit guard: dead in ANY of the last M distinct states
GUARD_M = 1

# which snapshot field belongs to which group. Round 2 splits the Round 1
# "gate" group into sx and cz, because Stage 1 fitted them separately.
FIELD_GROUP = {"err_ro": "readout", "err_1q": "sx", "err_2q": "cz",
               "t1": "times", "t2": "times"}
FIELDS = ("t1", "t2", "err_1q", "err_ro", "err_2q")
DELAYS = (1, 3, 6, 12, 24, 48)

# Permanent defects, computed from DEVELOPMENT cards only and frozen here, so
# no fresh card can change which qubits are removed for every arm. This is the
# Round 2 reading of Amendment A1.5, which took them from training days only.
PERMANENT_DEFECTS = {
    "ibm_fez": [72],
    "ibm_kingston": [113, 121, 146],
    "ibm_marrakesh": [82, 94, 113, 130],
}


def _check_against_fit():
    """Refuse to load if the hand written table and the fit disagree."""
    path = ROOT / "outputs" / "round2" / "stage1_fitted_rule.json"
    if not path.exists():
        return "fit file absent, table not cross checked"
    fit = json.loads(path.read_text())
    bad = []
    if int(fit["guard_M"]) != GUARD_M:
        bad.append(f"guard M: fit {fit['guard_M']} vs rule {GUARD_M}")
    for g, info in fit["groups"].items():
        if int(info["N"]) != N_BY_GROUP[g]:
            bad.append(f"{g} N: fit {info['N']} vs rule {N_BY_GROUP[g]}")
        for d, w in info["w_by_delay"].items():
            mine = W_BY_GROUP_AND_DELAY[g][int(d)]
            if abs(float(w) - mine) > 1e-12:
                bad.append(f"{g} w(D={d}): fit {w} vs rule {mine}")
    if bad:
        raise AssertionError("frozen rule does not match the fit: "
                             + "; ".join(bad))
    return "table matches outputs/round2/stage1_fitted_rule.json"


CHECK_NOTE = _check_against_fit()


def weight(group, delay_h):
    return W_BY_GROUP_AND_DELAY[group][int(delay_h)]


def window_n(group):
    return N_BY_GROUP[group]


# ------------------------------------------------------------- the predictor

def predict(store, info_index, delay_h):
    """The snapshot the hybrid arm hands to the compiler.

    `info_index` is the newest state the rule is allowed to see, which is the
    state at or before the submission time. Nothing above that index is ever
    read, which is what freeze test (iii) checks.
    """
    latest = store.snapshot(info_index)
    out = dict(latest)
    out["err_2q"] = dict(latest["err_2q"])
    depth, used_w = {}, {}

    for field in FIELDS:
        group = FIELD_GROUP[field]
        n = window_n(group)
        w = weight(group, delay_h)
        hist = strat.distinct_history(store, info_index, field, n)
        if not hist:
            continue
        if w == 0.0:
            # RAW values, no log round trip. exp(log(x)) is not exactly x, and
            # freeze test (i) requires a field with w = 0 to give EXACTLY the
            # stale numbers.
            vals = hist[0][1]
        else:
            arr = np.array([strat._safe_log(v) for _, v in hist])
            med = np.nanmedian(arr, axis=0)
            vals = np.exp((1.0 - w) * arr[0] + w * med)
        if field == "err_2q":
            keys = sorted(latest["err_2q"])
            out["err_2q"] = {k: float(v) for k, v in zip(keys, vals)}
        else:
            out[field] = vals
        depth[field] = len(hist)
        used_w[field] = w

    out["window_depth"] = depth
    out["hybrid_w"] = used_w
    out["hybrid_delay_h"] = int(delay_h)
    return out


def guard_dead(store, info_index, m=None):
    """Qubits dead in ANY of the last M distinct states at or before t_s."""
    m = GUARD_M if m is None else m
    dead = set()
    for i in range(info_index, max(info_index - m, -1), -1):
        dead |= rd.dead_qubits(store.snapshot(i))
    return dead


def permanent(machine):
    return set(PERMANENT_DEFECTS[machine])


# ---------------------------------------------------------------- the arms

ARMS = ["stale", "window_mean", "shrinkage_r1", "hybrid", "hybrid_no_guard",
        "ceiling"]

# The pre-stated design named the second ablation "readout_only", meaning
# "hybrid without the guard". In Round 1 only readout carried weight, so the
# name fitted; Stage 1 gave all four groups weight, so the old name would now
# mislead. Same definition, clearer name. Logged as a naming change.
ARM_ALIASES = {"hybrid_no_guard": "readout_only"}

# The pre-stated design also asked for "guard_only", meaning stale plus the
# guard. Stage 1 chose M = 1, and at M = 1 the guard removes exactly the
# qubits dead in the state at t_s, which is exactly what the stale arm already
# removes. So guard_only would be identical to stale, value for value. It is
# NOT simulated; freeze test (iv) proves the two targets are identical instead.
DROPPED_ARMS = {"guard_only": "identical to stale at M = 1, proved by test iv"}


def arm_snapshot(arm, store, info_index, truth_index, delay_h):
    """The numbers each Round 2 arm is allowed to hand to the compiler."""
    if arm == "stale":
        return strat.predict(store, info_index, "stale")
    if arm == "window_mean":
        return strat.predict(store, info_index, "mean")
    if arm == "shrinkage_r1":
        import engine_config as cfg
        return strat.predict(store, info_index, "shrink", n=cfg.SHRINK_N,
                             w_by_group=cfg.SHRINK_W_BY_GROUP)
    if arm in ("hybrid", "hybrid_no_guard"):
        return predict(store, info_index, delay_h)
    if arm == "ceiling":
        return store.snapshot(truth_index)
    raise ValueError(arm)


def arm_extra_forbid(arm, store, info_index):
    """Qubits this arm removes on top of its own snapshot's dead qubits."""
    if arm == "hybrid":
        return guard_dead(store, info_index)
    return set()


def describe():
    lines = [f"rule: {RULE_NAME}",
             f"fitted on development cards {RULE_FITTED_ON[0]} to {RULE_FITTED_ON[1]}",
             f"cross check: {CHECK_NOTE}",
             f"guard: dead in any of the last M = {GUARD_M} distinct states",
             "N, the number of distinct values the median is taken over:"]
    for g in ("readout", "sx", "cz", "times"):
        lines.append(f"  {g:<8} N = {N_BY_GROUP[g]}")
    lines.append("w(D), the weight on the median:")
    lines.append("  " + f"{'group':<8}" + "".join(f"{'D=' + str(d):>8}"
                                                  for d in DELAYS))
    for g in ("readout", "sx", "cz", "times"):
        lines.append("  " + f"{g:<8}"
                     + "".join(f"{W_BY_GROUP_AND_DELAY[g][d]:>8.2f}"
                               for d in DELAYS))
    lines.append(f"arms: {ARMS}")
    lines.append(f"dropped arms: {DROPPED_ARMS}")
    lines.append("permanent defects, from development cards only: "
                 + str(PERMANENT_DEFECTS))
    return "\n".join(lines)


if __name__ == "__main__":
    print(describe())
