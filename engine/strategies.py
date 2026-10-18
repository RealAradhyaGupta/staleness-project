"""The six arms of PROTOCOL.md section 6, as amended by A1.2, A1.4 and A1.7.

OURS. This replaces the teammates' predictors.py for real data. Their file is
kept untouched in engine/predictors.py and is still used by their synthetic
fixture.

What changed from their predictors.py, and why:

  * WINDOWS ARE PER FIELD (Amendment A1.2). "The last N" means the last N
    DISTINCT VALUES OF THAT FIELD, not the last N states. A state is new if ANY
    field changed, and L-017 showed readout error moves far more often than the
    rest, so five consecutive states can carry five identical cz values. Under
    the old per state window the cz standard deviation would be exactly zero
    and the std-adjusted arm would silently collapse into the window mean arm.

  * THE TREND ARM IS DROPPED. PROTOCOL.md section 6 lists six arms and trend is
    not one of them. It is their straight line forecast and it is not part of
    this protocol. Their code for it stays in engine/predictors.py, unused.

  * "ORACLE" IS CALLED "CEILING" (Amendment A1.4), defined as best available
    reported numbers, because L-017 measured a state's own sx and cz values as
    already 13 to 16 hours old when it is first published. It is not perfect
    knowledge.

  * PER FIELD SHRINKAGE is ours and is NOT TUNED yet. The placeholder is N = 5
    and w = 0.5 for all three field groups. Every output carries NOT TUNED.

All averaging is on the log of each value, as in their predictors.py, because
error rates span orders of magnitude.
"""
import warnings

import numpy as np

import engine_config as cfg

ARMS = ["random", "stale", "window_mean", "std_adjusted", "shrinkage", "ceiling"]
ERROR_FIELDS = ("err_1q", "err_ro")
TIME_FIELDS = ("t1", "t2")
# Amendment A1.3 groups the five fields into three for the tuning grid.
FIELD_GROUP = {"err_ro": "readout", "err_1q": "gate", "err_2q": "gate",
               "t1": "times", "t2": "times"}


def _vector(snap, field):
    if field == "err_2q":
        return np.array([snap["err_2q"][k] for k in sorted(snap["err_2q"])])
    return np.asarray(snap[field], dtype=float)


def distinct_history(store, upto_index, field, n):
    """The last `n` DISTINCT values of ONE field, newest first.

    Walks back through states and keeps a state only when that field's numbers
    actually differ from the newest one kept. This is Amendment A1.2.
    """
    out = []
    last = None
    i = upto_index
    while i >= 0 and len(out) < n:
        snap = store.snapshot(i)
        try:
            v = _vector(snap, field)
        except KeyError:
            i -= 1
            continue
        if v.size == 0:
            i -= 1
            continue
        # equal_nan=True is essential. Without it, a field with a missing
        # value on ANY qubit compares unequal to itself (NaN != NaN), so
        # every state looks like a new distinct value. That silently turned
        # the per field window of Amendment A1.2 back into a per state
        # window for T1 and T2. See PROGRESS_LOG.md L-027.
        if last is None or v.shape != last.shape or not np.array_equal(
                v, last, equal_nan=True):
            out.append((i, v))
            last = v
        i -= 1
    return out


def _safe_log(v):
    return np.log(np.clip(v, 1e-12, None))


def _combine(store, upto_index, field, how, n, w_by_group=None):
    """Build one field's predicted vector from its own last n distinct values."""
    hist = distinct_history(store, upto_index, field, n)
    if how == "stale":
        # RAW values, no log round trip. exp(log(x)) is not exactly x, and
        # PROTOCOL.md section 12 check 1 requires stale regret to be EXACTLY
        # zero when stale and ceiling see the same state.
        return hist[0][1], len(hist)
    arr = np.array([_safe_log(v) for _, v in hist])     # newest first
    # A qubit missing this field in EVERY one of the last n distinct values
    # gives an all-NaN column. numpy warns; the value is never used, because
    # such a qubit is dead by the L-016 rule and is removed from the target.
    warnings.filterwarnings("ignore", r"(Mean|All-NaN).*", RuntimeWarning)
    warnings.filterwarnings("ignore", r"Degrees of freedom.*", RuntimeWarning)
    if how == "mean":
        out = np.nanmean(arr, axis=0)
    elif how == "std":
        mean = np.nanmean(arr, axis=0)
        std = np.nanstd(arr, axis=0) if arr.shape[0] > 1 else np.zeros_like(mean)
        out = mean + std if field in ERROR_FIELDS or field == "err_2q" else mean - std
    elif how == "shrink":
        # Amendment A1.3: w is set per FIELD GROUP, not per field.
        w = (cfg.SHRINK_W if w_by_group is None
             else w_by_group[FIELD_GROUP[field]])
        med = np.nanmedian(arr, axis=0)
        out = (1.0 - w) * arr[0] + w * med
    else:
        raise ValueError(how)
    return np.exp(out), len(hist)


def predict(store, upto_index, how, n=None, w_by_group=None):
    """Return a snapshot dict built field by field. `upto_index` is the newest
    state the strategy is allowed to see, which is the state at t_s."""
    n = n or cfg.WINDOW_N
    latest = store.snapshot(upto_index)
    out = dict(latest)
    out["err_2q"] = dict(latest["err_2q"])
    depth = {}
    for field in ("t1", "t2", "err_1q", "err_ro"):
        vals, d = _combine(store, upto_index, field, how, n, w_by_group)
        out[field] = vals
        depth[field] = d
    keys = sorted(latest["err_2q"])
    if keys:
        vals, d = _combine(store, upto_index, "err_2q", how, n, w_by_group)
        out["err_2q"] = {k: float(v) for k, v in zip(keys, vals)}
        depth["err_2q"] = d
    out["window_depth"] = depth
    return out


def arm_snapshot(arm, store, info_index, truth_index):
    """The numbers each arm is allowed to hand to the compiler."""
    if arm in ("stale", "random"):
        return predict(store, info_index, "stale")
    if arm == "window_mean":
        return predict(store, info_index, "mean")
    if arm == "std_adjusted":
        return predict(store, info_index, "std")
    if arm == "shrinkage":
        return predict(store, info_index, "shrink", n=cfg.SHRINK_N)
    if arm == "ceiling":
        return store.snapshot(truth_index)
    raise ValueError(arm)
