"""Round 2 freeze tests. Stage 2 stops the whole run if any of these fails.

  (i)   any field whose weight is 0 gives EXACTLY the stale numbers
  (ii)  with every weight set to 0 and the guard off, hybrid equals stale
  (iii) the rule never reads a card newer than the submission time
  (iv)  at M = 1 the guard removes exactly what stale already removes, so the
        pre-stated guard_only ablation is identical to stale and need not be
        simulated

Test (i) matters because exp(log(x)) is not exactly x. If the rule took a log
round trip even at w = 0, a field the fit told us to leave alone would still
be nudged, and PROTOCOL.md section 12 check 1 would stop being exactly zero.

These run on the development store, which is enough: they test the rule's
mechanics, not the fresh data.
"""
import importlib
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "engine"))
sys.path.insert(0, str(ROOT / "scripts"))

import real_data as rd          # noqa: E402
import strategies as strat      # noqa: E402

rule = importlib.import_module("30_hybrid_rule")

MACHINE = "ibm_fez"
PROBE_INDEX = 300               # a state well inside the development window
RESULTS = []


def check(name, ok, note=""):
    RESULTS.append((name, bool(ok), note))
    print(f"  {'PASS' if ok else 'FAIL'}  {name}")
    if note:
        print(f"        {note}")
    return ok


def same_field(a, b):
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    return a.shape == b.shape and np.array_equal(a, b, equal_nan=True)


def same_dict(a, b):
    if set(a) != set(b):
        return False
    return all(a[k] == b[k] for k in a)


class Recorder:
    """Wraps a store and records every state index that is read."""

    def __init__(self, store):
        self._s = store
        self.read = []
        self.times = store.times
        self.machine = store.machine
        self.n_qubits = store.n_qubits

    def __len__(self):
        return len(self._s)

    def snapshot(self, i):
        self.read.append(i)
        return self._s.snapshot(i)

    def index_at_or_before(self, when):
        return self._s.index_at_or_before(when)


def main():
    print("=" * 72)
    print("ROUND 2 FREEZE TESTS")
    print("=" * 72)
    print(f"  rule cross check: {rule.CHECK_NOTE}")
    store = rd.open_store(MACHINE)
    base, _ = rd.load_base_target(MACHINE)
    perm = rule.permanent(MACHINE)
    i = min(PROBE_INDEX, len(store) - 1)
    print(f"  store: {MACHINE}, {len(store)} states, probing state {i} "
          f"({store.times[i].isoformat()})")

    stale = strat.predict(store, i, "stale")

    # ------------------------------------------------------------- test (i)
    print("\n(i) a field with weight 0 gives EXACTLY the stale numbers")
    zero_cases = []
    for group, by_d in rule.W_BY_GROUP_AND_DELAY.items():
        for D, w in by_d.items():
            if w == 0.0:
                zero_cases.append((group, D))
    print(f"    the frozen table has {len(zero_cases)} field-group and delay "
          f"pairs at w = 0: {zero_cases}")
    ok_i = True
    for group, D in zero_cases:
        hyb = rule.predict(store, i, D)
        fields = [f for f, g in rule.FIELD_GROUP.items() if g == group]
        for f in fields:
            if f == "err_2q":
                same = same_dict(hyb["err_2q"], stale["err_2q"])
            else:
                same = same_field(hyb[f], stale[f])
            ok_i &= same
            if not same:
                print(f"    MISMATCH in {f} for group {group} at D = {D}")
    check(f"(i) every w = 0 field is bit for bit the stale value", ok_i,
          f"{len(zero_cases)} pairs checked, exact float equality")

    # ------------------------------------------------------------ test (ii)
    print("\n(ii) with every weight 0 and the guard off, hybrid equals stale")
    saved = rule.W_BY_GROUP_AND_DELAY
    rule.W_BY_GROUP_AND_DELAY = {g: {d: 0.0 for d in by_d}
                                 for g, by_d in saved.items()}
    try:
        ok_ii = True
        detail = []
        for D in rule.DELAYS:
            hyb = rule.predict(store, i, D)
            for f in ("t1", "t2", "err_1q", "err_ro"):
                ok_ii &= same_field(hyb[f], stale[f])
            ok_ii &= same_dict(hyb["err_2q"], stale["err_2q"])
            # and the compiled device description, not just the numbers
            th, fh, _ = rd.strategy_target(hyb, base, perm)
            ts, fs, _ = rd.strategy_target(stale, base, perm)
            ok_ii &= (fh == fs)
            for name in ("sx", "measure"):
                eh = {k: v.error for k, v in th[name].items()}
                es = {k: v.error for k, v in ts[name].items()}
                ok_ii &= same_dict(eh, es)
            ech = {k: v.error for k, v in th["cz"].items()}
            ecs = {k: v.error for k, v in ts["cz"].items()}
            ok_ii &= same_dict(ech, ecs)
            detail.append(f"D={D} forbids {len(fh)}")
        check("(ii) hybrid with all weights 0 equals stale, numbers and target",
              ok_ii, "; ".join(detail))
    finally:
        rule.W_BY_GROUP_AND_DELAY = saved
    # make sure the restore worked
    check("(ii-restore) the frozen weight table is back as written",
          rule.W_BY_GROUP_AND_DELAY["readout"][24] == 0.90,
          f"readout w at D = 24 is {rule.W_BY_GROUP_AND_DELAY['readout'][24]}")

    # ----------------------------------------------------------- test (iii)
    print("\n(iii) the rule never reads a card newer than the submission time")
    ok_iii = True
    notes = []
    for D in rule.DELAYS:
        rec = Recorder(store)
        rule.predict(rec, i, D)
        rule.guard_dead(rec, i)
        newest = max(rec.read)
        ok_iii &= (newest <= i)
        notes.append(f"D={D}: read {len(rec.read)} states, newest index "
                     f"{newest} of an allowed {i}")
    check("(iii) no state newer than the submission time is ever read", ok_iii,
          "; ".join(notes))

    # a second, harder version: the truth state must be unreachable
    rec = Recorder(store)
    rule.predict(rec, i, 48)
    beyond = [x for x in rec.read if x > i]
    check("(iii-strict) not one read above the submission index",
          not beyond, f"reads above index {i}: {beyond}")

    # ------------------------------------------------------------ test (iv)
    print("\n(iv) at M = 1 the guard is what stale already removes")
    ok_iv = True
    notes = []
    for idx in (i, max(i - 50, 0), max(i - 120, 0), len(store) - 1):
        guard = rule.guard_dead(store, idx)
        stale_snap = strat.predict(store, idx, "stale")
        stale_forbid = rd.dead_qubits(stale_snap)
        same = (guard == stale_forbid)
        ok_iv &= same
        notes.append(f"state {idx}: guard {len(guard)}, stale {len(stale_forbid)}, "
                     f"{'equal' if same else 'DIFFERENT'}")
    check("(iv) guard_only would be identical to stale, so it is not run",
          ok_iv, "; ".join(notes))

    # ------------------------------------------------------- the guard bites
    print("\nextra, not a stop test: does the guard change anything for hybrid?")
    changed = 0
    for idx in range(max(len(store) - 200, 0), len(store)):
        for D in (24, 48):
            hyb = rule.predict(store, idx, D)
            own = rd.dead_qubits(hyb)
            g = rule.guard_dead(store, idx)
            if g - own:
                changed += 1
    print(f"  the guard adds at least one qubit that the hybrid's own blended")
    print(f"  numbers would NOT have called dead in {changed} of 400 checks.")
    print(f"  That is why the guard is kept for hybrid even though it is a")
    print(f"  no-op for stale: blending readout can pull a failed qubit back")
    print(f"  under the 0.2 threshold and make it look usable again.")

    print("\n" + "=" * 72)
    failed = [n for n, ok, _ in RESULTS if not ok]
    if failed:
        print(f"FREEZE TESTS FAILED: {failed}")
        print("STOP RULE FIRED. The rule is not frozen and nothing is fetched.")
        return 2
    print(f"ALL {len(RESULTS)} FREEZE TESTS PASSED")
    return 0


sys.exit(main())
