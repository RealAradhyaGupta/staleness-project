"""Job generation, exactly as PROTOCOL.md section 4 and section 3 define it.

OURS. Not part of the teammates' pipeline.

Section 4, word for word, is implemented below and the order of visits is part
of the definition, because changing the order changes the draws:

    one numpy.random.default_rng(20260828) is created once. Machines are
    visited in sorted name order. Within a machine, days are visited in
    ascending date order. For each day, 3 values are drawn uniformly from
    [0, 86400) seconds, sorted ascending, and added to that day's 00:00:00 UTC.

Section 3 validity rule, also implemented here. Invalid jobs are DROPPED AND
COUNTED, never silently skipped.
"""
from datetime import datetime, timedelta, timezone

import numpy as np

import engine_config as cfg

MACHINES = ["ibm_fez", "ibm_kingston", "ibm_marrakesh"]   # sorted name order


def all_submission_times(window_start=None, window_end=None):
    """Every submission time for every machine, in the protocol's draw order.

    Returns a list of (machine, t_s, draw_order) with draw_order counting from
    0 across the whole sequence, so "the first 30 for ibm_kingston" is
    well defined.

    ROUND 2, additive: the two arguments move the window. Called with no
    arguments, which is how Round 1 calls it, the window comes from
    engine_config exactly as before and the draws are identical.
    """
    rng = np.random.default_rng(cfg.SEED_SUBMIT)
    start = datetime.fromisoformat(
        window_start or cfg.WINDOW_START).replace(tzinfo=timezone.utc)
    end = datetime.fromisoformat(
        window_end or cfg.WINDOW_END).replace(tzinfo=timezone.utc)
    days = []
    d = start
    while d <= end:
        days.append(d)
        d += timedelta(days=1)

    out = []
    order = 0
    for machine in sorted(MACHINES):
        for day in days:
            secs = sorted(rng.uniform(0.0, 86400.0, size=cfg.SUBMITS_PER_DAY))
            for s in secs:
                out.append((machine, day + timedelta(seconds=float(s)), order))
                order += 1
    return out


def in_training(t):
    return (datetime.fromisoformat(cfg.WINDOW_START).replace(tzinfo=timezone.utc)
            <= t <
            datetime.fromisoformat(cfg.TEST_START).replace(tzinfo=timezone.utc))


def build_jobs(store, submissions, delays_h, circuits, min_history=5):
    """Apply the section 3 validity rule. Returns (jobs, dropped counts)."""
    jobs = []
    dropped = {}
    last_state_time = store.times[-1]
    for machine, t_s, order in submissions:
        info = store.index_at_or_before(t_s)
        for D in delays_h:
            key = f"D={D}"
            dropped.setdefault(key, {"no_history": 0, "no_truth": 0,
                                     "past_end": 0, "kept": 0})
            if info < min_history - 1:
                dropped[key]["no_history"] += 1
                continue
            t_r = t_s + timedelta(hours=D)
            if t_r > last_state_time:
                dropped[key]["past_end"] += 1
                continue
            truth = store.index_at_or_before(t_r)
            if truth < 0:
                dropped[key]["no_truth"] += 1
                continue
            dropped[key]["kept"] += 1
            for circuit in circuits:
                jobs.append({
                    "machine": machine, "draw_order": order,
                    "t_s": t_s, "t_r": t_r, "delay_h": D, "circuit": circuit,
                    "info_state": info, "truth_state": truth,
                    "new_states": truth - info,
                })
    return jobs, dropped
