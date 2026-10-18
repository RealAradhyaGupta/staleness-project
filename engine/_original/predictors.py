"""M4 - Predictors. Each one looks ONLY at snapshots up to the submission cycle k
(decision F5: no peeking at the future) and returns a predicted snapshot for the
cycle the job will actually run in.

All math is done on the log of each number, because error rates span orders of
magnitude (0.0002 vs 0.02). "Errors" (gate, readout) are bad when high;
"times" (T1, T2) are bad when low.
"""
import copy

import numpy as np

import config
import snapshot

ERROR_FIELDS = ("err_1q", "err_ro")
TIME_FIELDS = ("t1", "t2")


def _stack(history):
    """Turn a list of snapshots into arrays of shape (cycles, items) per field."""
    hist = [snapshot.clean(s) for s in history]
    edges = list(hist[-1]["err_2q"].keys())
    arrays = {f: np.log(np.array([h[f] for h in hist])) for f in ERROR_FIELDS + TIME_FIELDS}
    arrays["err_2q"] = np.log(np.array([[h["err_2q"][k] for k in edges] for h in hist]))
    return hist[-1], edges, arrays


def _build(template, edges, values):
    out = copy.deepcopy(template)
    for f in ERROR_FIELDS:
        out[f] = np.clip(np.exp(values[f]), 1e-6, config.ERR_CAP)
    for f in TIME_FIELDS:
        out[f] = np.clip(np.exp(values[f]), 1e-6, 1e-2)
    e2 = np.clip(np.exp(values["err_2q"]), 1e-6, config.ERR_CAP)
    out["err_2q"] = {k: float(v) for k, v in zip(edges, e2)}
    return out


def persistence(history, delay):
    """'Next cycle = this cycle.' This is exactly the Stale strategy."""
    return copy.deepcopy(history[-1])


def stability(history, delay, window=config.WINDOW, penalty=config.PENALTY):
    """MAIN METHOD. Predicted value = average over the last `window` cycles,
    pushed toward 'bad' by `penalty` x how much it swung.
    A qubit that is good on average but unreliable gets marked as risky."""
    last, edges, a = _stack(history[-window:])
    vals = {}
    for f in ERROR_FIELDS + ("err_2q",):
        vals[f] = a[f].mean(0) + penalty * a[f].std(0)        # higher error = worse
    for f in TIME_FIELDS:
        vals[f] = a[f].mean(0) - penalty * a[f].std(0)        # lower T1/T2 = worse
    return _build(last, edges, vals)


def rolling_mean(history, delay, window=config.WINDOW):
    """Stability method with no penalty: just the recent average."""
    return stability(history, delay, window, penalty=0.0)


def trend(history, delay, window=config.WINDOW):
    """The email's 'forecasting' idea taken literally: fit a straight line to each
    qubit's last `window` cycles and extend it `delay` cycles into the future."""
    last, edges, a = _stack(history[-window:])
    w = a["t1"].shape[0]
    if w < 2:
        return copy.deepcopy(last)
    x = np.arange(w)
    x_future = (w - 1) + delay
    vals = {}
    for f, arr in a.items():
        slope, intercept = np.polyfit(x, arr, 1)              # one line per qubit/connection
        vals[f] = intercept + slope * x_future
    return _build(last, edges, vals)


PREDICTORS = {"stale": persistence, "stability": stability, "trend": trend, "rolling_mean": rolling_mean}
