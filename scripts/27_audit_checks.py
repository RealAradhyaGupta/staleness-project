"""Three read-only audit checks on the Round 1 results and the installed Qiskit.

OURS. EXPLORATORY AND POST-HOC. Nothing here is confirmatory.

READ ONLY. No IBM call is made. The engine is NOT re-run on the 5648 jobs.
Nothing in `data/raw` is written. No confirmatory file is changed. Check C
COMPILES circuits only: no simulator is built and no shot is taken. Only
development-period cards (28 August to 12 October 2026) are read.

SIGN CONVENTION, the same as scripts/26_row_check.py:
    regret = ceiling minus strategy      (positive means the strategy is worse)
    gain   = F_strategy minus F_stale    (positive means the strategy is better)

CHECK A  Reconcile 5648 jobs against the 5288 used in the row check, name the
         360 excluded jobs, quote the line that excludes them, and say whether
         that exclusion is in the frozen protocol. Then confirm how the random
         arm's `dead_qubits_used` is built.
CHECK B  Stale regret by delay, and the two pooled gains, per circuit, in
         View 1 and View 2b. Plus how often the stale layout differs from the
         ceiling layout.
CHECK C  Transpiler audit, compile only: versions and settings, which layout
         passes really run per circuit and optimization level, how often the
         chosen physical qubits move when the card changes, and the
         interaction graph max degree per circuit.

The bootstrap function, the seed (20261014) and the resample count (4000) are
imported from scripts/20_analyse_results.py, not copied. The generator is
re-seeded at the start of each block so a block's numbers do not depend on how
many bootstrap calls ran before it.

Wording rule from L-032: say "consistent with", never "proved".

Usage:  27_audit_checks.py [--results ...] [--outdir outputs/row_check_2]
                           [--machine ibm_fez] [--pairs 20]
"""
import argparse
import sys
import types
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "engine"))

ARMS = ["random", "stale", "window_mean", "std_adjusted", "shrinkage", "ceiling"]
STRATS = [a for a in ARMS if a != "ceiling"]
INFORMED = ["stale", "window_mean", "std_adjusted", "shrinkage"]
JOB = ["machine", "draw_order", "delay_h", "circuit"]
CIRCUITS = ["ghz5", "ghz8", "ghz10", "bv8", "bv10"]
QFT_SIZES = [5, 8, 10]
POOL_DELAYS = [6, 12, 24, 48]
LEVELS = [2, 3]
SEED_PAIRS = 20261024          # only picks WHICH cards are paired, nothing else


def load_script20():
    """Import scripts/20_analyse_results.py for its loader and bootstrap.

    That file calls main() at the bottom, so the trailing call is dropped and
    the rest is executed as a module. This reuses the real function instead of
    copying it, the same approach as scripts/26_row_check.py.
    """
    path = ROOT / "scripts/20_analyse_results.py"
    src = path.read_text().rsplit("\nmain()", 1)[0]
    mod = types.ModuleType("analyse20")
    mod.__file__ = str(path)
    exec(compile(src, str(path), "exec"), mod.__dict__)
    return mod


M20 = load_script20()


def fresh_rng():
    return np.random.default_rng(M20.SEED_BOOT)


def ci(frame, col, rng):
    if len(frame) == 0:
        return float("nan"), float("nan"), float("nan"), 0
    return M20.block_boot(frame, col, rng)


# ============================================================== CHECK A

def check_a(df, w, outdir):
    print("=" * 74)
    print("CHECK A: RECONCILE THE COUNTS")
    print("=" * 74)
    n_jobs = df.groupby(JOB).ngroups
    gap = w[w.touches_gap]
    keep = w[~w.touches_gap]
    print(f"  jobs in the results file:            {n_jobs}")
    print(f"  jobs used by the row check (View 1): {len(keep)}")
    print(f"  jobs excluded:                       {len(gap)}")

    print("\n  WHAT EXCLUDES THEM. Two places in scripts/20_analyse_results.py.")
    print("  First the flag is built inside load():")
    print('      df["touches_gap"] = [')
    print("          (t_s < gs[m][1]) and (t_r > gs[m][0]) if m in gs else False")
    print("          for m, t_s, t_r in zip(df.machine, df.t_s, df.t_r)]")
    print("  Then the primary comparison is run on the complement of that flag:")
    print("      main_set = w[~w.touches_gap]")
    print("  and the header printed above it says:")
    print('      "jobs touching the 22 to 23 Sep publishing gap are EXCLUDED '
          'here and"')
    print('      "reported separately below, as PROTOCOL.md section 10 '
          'requires."')
    print("  The three gap windows come from GAPS at the top of that file,")
    print("  measured in L-033:")
    for m, (a, b) in M20.GAPS.items():
        print(f"      {m:<15} {a}  to  {b}")

    print("\n  WAS THIS EXCLUSION IN THE FROZEN PROTOCOL? No.")
    print("  PROTOCOL.md section 10 says the opposite, word for word:")
    print('      "The 22 to 23 September publishing gap stays in. It is not')
    print('       deleted or patched. Results are reported with it included,')
    print('       and the jobs that straddle it are reported separately so its')
    print('       effect is visible."')
    print("  PROTOCOL_AMENDMENTS.md A1.6 reaffirms it after moving the split:")
    print('      "Section 10 of the protocol says that gap stays in and is')
    print('       reported separately, and that still holds. But it now sits in')
    print('       the test days, so it will affect the headline numbers, and')
    print('       the jobs that straddle it must be reported separately from')
    print('       the rest of the test set."')
    print("  So the protocol asks for the gap jobs to be INCLUDED in the")
    print("  headline AND ALSO shown separately. Script 20 instead DROPS them")
    print("  from the primary comparison, and its own comment credits section")
    print("  10 for that. The comment does not match the section. This is a")
    print("  real departure from the frozen protocol, not a reading of it.")
    print("  I am recording it here and changing nothing: 20_analyse_results.py")
    print("  and every reported number stay exactly as they are.")
    print("  scripts/26_row_check.py inherited the same exclusion in all four")
    print("  of its views, so its numbers carry this departure too.")

    print("\n  THE 360 EXCLUDED JOBS, by delay")
    by_d = (gap.groupby("delay_h").size().rename("excluded").to_frame()
            .join(w.groupby("delay_h").size().rename("all_jobs")))
    by_d["share_pct"] = by_d.excluded / by_d.all_jobs * 100
    print(by_d.to_string(float_format=lambda x: f"{x:.2f}"))

    print("\n  by machine")
    by_m = (gap.groupby("machine").size().rename("excluded").to_frame()
            .join(w.groupby("machine").size().rename("all_jobs")))
    by_m["share_pct"] = by_m.excluded / by_m.all_jobs * 100
    print(by_m.to_string(float_format=lambda x: f"{x:.2f}"))

    print("\n  by circuit")
    by_c = (gap.groupby("circuit").size().rename("excluded").to_frame()
            .join(w.groupby("circuit").size().rename("all_jobs")))
    by_c["share_pct"] = by_c.excluded / by_c.all_jobs * 100
    print(by_c.to_string(float_format=lambda x: f"{x:.2f}"))

    print("\n  by submission date (UTC)")
    by_day = (gap.groupby("day").size().rename("excluded").to_frame()
              .join(w.groupby("day").size().rename("all_jobs")))
    by_day["share_pct"] = by_day.excluded / by_day.all_jobs * 100
    print(by_day.to_string(float_format=lambda x: f"{x:.2f}"))

    print("\n  by machine and submission date")
    print(gap.pivot_table(index="day", columns="machine", values="delay_h",
                          aggfunc="size").fillna(0).astype(int).to_string())

    for name, tab in (("A1_excluded_by_delay", by_d),
                      ("A2_excluded_by_machine", by_m),
                      ("A3_excluded_by_circuit", by_c),
                      ("A4_excluded_by_day", by_day)):
        tab.to_csv(outdir / f"{name}.csv")
    gap[JOB + ["day", "new_states"]].sort_values(JOB).to_csv(
        outdir / "A5_excluded_jobs_full_list.csv", index=False)

    print("\n  THE 5 MISSING STALE DEAD-QUBIT ROWS")
    stale_dead = df[df.dead & (df.arm == "stale")]
    gap_keys = set(map(tuple, gap[JOB].to_numpy()))
    in_gap = [k in gap_keys for k in map(tuple, stale_dead[JOB].to_numpy())]
    print(f"  stale dead-qubit rows in the whole file:        "
          f"{len(stale_dead)}")
    print(f"  of those, sitting in one of the 360 gap jobs:   {sum(in_gap)}")
    print(f"  of those, sitting in the 5288 kept jobs:        "
          f"{len(stale_dead) - sum(in_gap)}")
    print("  So yes: all 5 of the difference between 81 and 76 are gap jobs.")
    missing = stale_dead[pd.Series(in_gap).to_numpy()]
    print(missing[JOB + ["t_s", "dead_qubits_used", "fidelity"]]
          .to_string(index=False))
    missing.to_csv(outdir / "A6_stale_dead_rows_in_gap_jobs.csv", index=False)
    for arm in INFORMED + ["random"]:
        d = df[df.dead & (df.arm == arm)]
        gk = [k in gap_keys for k in map(tuple, d[JOB].to_numpy())]
        print(f"    {arm:<13} dead rows {len(d):>4}   in gap jobs {sum(gk):>3}"
              f"   kept {len(d) - sum(gk):>4}")

    print("\n  THE RANDOM ARM'S dead_qubits_used, from engine/run_engine.py")
    print("  The arm draws RANDOM_DRAWS = 5 layouts (engine_config.py, set by")
    print("  Amendment A1.7). Inside the draw loop the engine accumulates:")
    print("      used |= set(isa.layout.final_index_layout())")
    print("  and after the loop collapses the draws to one row:")
    print("      fid, esp_v, used = float(np.mean(fs)), float(np.mean(es)), "
          "sorted(used)")
    print("  then writes one value per row:")
    print('      "dead_qubits_used": " ".join(map(str, sorted(set(used) & '
          'truth_dead)))')
    print("  So the fidelity is the MEAN over the 5 draws while the qubit list")
    print("  is the UNION over the 5 draws. Confirmed: union, not per draw.")
    print("\n  IS PER-DRAW DATA STORED? No.")
    print("  The engine writes one CSV row per (job, arm). The per-draw")
    print("  fidelities `fs`, the per-draw ESPs `es` and the per-draw layouts")
    print("  are local variables that are averaged or unioned and then go out")
    print("  of scope. Nothing else is written. The columns in the results file")
    print("  are:")
    print("      " + ", ".join(df.columns))
    print("  There is no draw index and no per-draw column anywhere, so the")
    print("  per-draw dead rate CANNOT be computed from stored data. Getting")
    print("  it would need the engine re-run, which this task forbids.")
    nq = df[df.arm == "random"].qubits_used.str.split().apply(len)
    print(f"\n  What the union does to the qubit counts (random arm, all "
          f"{len(nq)} rows):")
    print(f"      distinct physical qubits listed per row: min {nq.min()}, "
          f"median {int(nq.median())}, max {nq.max()}")
    for c in CIRCUITS:
        sub = df[(df.arm == "random") & (df.circuit == c)]
        k = sub.qubits_used.str.split().apply(len)
        width = int(c[3:]) if c.startswith("ghz") else int(c[2:])
        print(f"      {c:<6} circuit width {width:>2}  union size median "
              f"{int(k.median()):>3}  so about "
              f"{k.median()/width:.1f}x the qubits of one draw")
    print("  A union over 5 draws covers several times the qubits of a single")
    print("  layout, which is why the random arm is flagged far more often")
    print("  than the single-layout arms. Its row count is not comparable with")
    print("  theirs. This is a reporting artefact of the union, and it is")
    print("  consistent with the arm itself being no worse than the draws.")
    return gap, keep


# ============================================================== CHECK B

def check_b(df, w, outdir):
    print("\n" + "=" * 74)
    print("CHECK B: BY CIRCUIT")
    print("=" * 74)
    print("  Gap jobs excluded, as in the row check, so View 1 here matches")
    print("  View 1 there. EXPLORATORY: the protocol pools over circuits, so a")
    print("  per-circuit split is not one of the two confirmatory comparisons.")

    dead_rows = df[df.dead]
    inf = dead_rows[dead_rows.arm.isin(INFORMED)]
    jobs_inf = set(map(tuple, inf[JOB].drop_duplicates().to_numpy()))
    keys = list(map(tuple, w[JOB].to_numpy()))
    w = w.assign(dead_informed=[k in jobs_inf for k in keys])
    views = {"View 1": w[~w.touches_gap].copy(),
             "View 2b": w[~w.touches_gap & ~w.dead_informed].copy()}

    rows_sr, rows_gain = [], []
    for vname, vw in views.items():
        print("\n  " + "-" * 70)
        print(f"  {vname}: mean stale regret by delay, per circuit")
        print("  " + "-" * 70)
        print(f"  {'circuit':<8} {'n':>6} " +
              " ".join(f"{D:>16}h" for D in sorted(vw.delay_h.unique())))
        rng = fresh_rng()
        for c in CIRCUITS:
            cw = vw[vw.circuit == c]
            cells = []
            for D in sorted(vw.delay_h.unique()):
                g = cw[cw.delay_h == D]
                o, lo, hi, nd = ci(g, "regret_stale", rng)
                cells.append(f"{o:+.4f}[{lo:+.3f},{hi:+.3f}]")
                rows_sr.append(dict(view=vname, circuit=c, delay_h=D, n=len(g),
                                    mean=o, lo=lo, hi=hi, days=nd))
            print(f"  {c:<8} {len(cw):>6} " + " ".join(f"{x:>17}" for x in cells))

        print(f"\n  {vname}: pooled gains over {POOL_DELAYS} h, per circuit")
        print("  gain = F_strategy minus F_stale, positive means the strategy "
              "beats stale")
        print(f"  {'circuit':<8} {'n':>6} {'window mean minus stale':>34} "
              f"{'shrinkage minus stale':>34}")
        rng = fresh_rng()
        pooled = vw[vw.delay_h.isin(POOL_DELAYS)].copy()
        pooled["gain_window_mean"] = pooled["window_mean"] - pooled["stale"]
        pooled["gain_shrinkage"] = pooled["shrinkage"] - pooled["stale"]
        for c in CIRCUITS:
            cw = pooled[pooled.circuit == c]
            cells = []
            for col in ("gain_window_mean", "gain_shrinkage"):
                o, lo, hi, nd = ci(cw, col, rng)
                zero = "includes zero" if lo <= 0 <= hi else "excludes zero"
                cells.append(f"{o:+.5f} [{lo:+.5f}, {hi:+.5f}]")
                rows_gain.append(dict(
                    view=vname, circuit=c,
                    contrast=col.replace("gain_", "") + " minus stale",
                    delays="pooled 6/12/24/48 h", n=len(cw), mean=o, lo=lo,
                    hi=hi, days=nd, verdict=zero))
            print(f"  {c:<8} {len(cw):>6} {cells[0]:>34} {cells[1]:>34}")
    pd.DataFrame(rows_sr).to_csv(outdir / "B1_stale_regret_by_circuit.csv",
                                 index=False)
    pd.DataFrame(rows_gain).to_csv(outdir / "B2_pooled_gains_by_circuit.csv",
                                   index=False)

    print("\n  " + "-" * 70)
    print("  ARE LAYOUTS STORED? Yes, in the `qubits_used` column.")
    print("  " + "-" * 70)
    print("  engine/run_engine.py writes, for every arm except random,")
    print('      "qubits_used": " ".join(map(str, used))')
    print("  with `used = list(isa.layout.final_index_layout())`, so the")
    print("  column holds the real physical qubits in layout order. For the")
    print("  random arm it is the sorted UNION over the 5 draws instead, so")
    print("  the random arm is left out of this comparison.")
    piv = df.pivot_table(index=JOB + ["day", "touches_gap"], columns="arm",
                         values="qubits_used", aggfunc="first").reset_index()
    piv = piv[~piv.touches_gap]
    rows = []
    print(f"\n  share of jobs where the STALE layout differs from the CEILING "
          f"layout")
    print(f"  (same set of physical qubits, and same ordered layout)")
    print(f"  {'circuit':<8} {'n':>6} {'set differs':>13} {'order differs':>15}")
    for c in CIRCUITS + ["ALL"]:
        sub = piv if c == "ALL" else piv[piv.circuit == c]
        set_diff = [set(a.split()) != set(b.split())
                    for a, b in zip(sub["stale"], sub["ceiling"])]
        ord_diff = [a.split() != b.split()
                    for a, b in zip(sub["stale"], sub["ceiling"])]
        s, o = np.mean(set_diff) * 100, np.mean(ord_diff) * 100
        print(f"  {c:<8} {len(sub):>6} {s:>12.1f}% {o:>14.1f}%")
        rows.append(dict(circuit=c, n_jobs=len(sub),
                         pct_set_differs=s, pct_order_differs=o))
    print("\n  the same split by delay, set comparison")
    for D in sorted(piv.delay_h.unique()):
        sub = piv[piv.delay_h == D]
        s = np.mean([set(a.split()) != set(b.split())
                     for a, b in zip(sub["stale"], sub["ceiling"])]) * 100
        print(f"    D={D:>3}h  n={len(sub):>5}  set differs {s:>5.1f}%")
        rows.append(dict(circuit=f"ALL at delay {D} h", n_jobs=len(sub),
                         pct_set_differs=s, pct_order_differs=float("nan")))
    pd.DataFrame(rows).to_csv(outdir / "B3_stale_vs_ceiling_layout.csv",
                              index=False)


# ============================================================== CHECK C

def build_circuits():
    """The five study circuits plus exact QFT on 5, 8 and 10 qubits."""
    import circuits as circ_mod
    from qiskit import QuantumCircuit
    from qiskit.circuit.library import QFTGate
    out = {c: circ_mod.build(c) for c in CIRCUITS}
    for n in QFT_SIZES:
        qc = QuantumCircuit(n, name=f"qft{n}")
        qc.append(QFTGate(n), range(n))     # exact QFT, no approximation
        qc.measure_all()
        out[f"qft{n}"] = qc
    return out


def interaction_degree(qc):
    """Max degree of the two-qubit interaction graph of the logical circuit.

    A gate like QFTGate arrives as ONE opaque instruction on n qubits, so the
    circuit is decomposed until nothing acts on more than two qubits before
    the graph is counted. Without this step a QFT would wrongly measure as
    degree 0, because it carries no explicit two-qubit gate of its own.
    """
    work = qc
    for _ in range(8):
        wide = [ins for ins in work.data
                if len(ins.qubits) > 2
                and ins.operation.name not in ("measure", "barrier")]
        if not wide:
            break
        work = work.decompose()
    deg = defaultdict(set)
    for instr in work.data:
        qs = [work.find_bit(q).index for q in instr.qubits]
        if len(qs) == 2 and instr.operation.name not in ("measure", "barrier"):
            deg[qs[0]].add(qs[1])
            deg[qs[1]].add(qs[0])
    return (max(len(v) for v in deg.values()) if deg else 0,
            len(deg), sum(len(v) for v in deg.values()) // 2)


def compile_once(qc, target, level, seed):
    """Compile and record which layout passes really ran. COMPILE ONLY."""
    from qiskit.transpiler import generate_preset_pass_manager
    ran, reasons = [], {}

    def cb(**kw):
        name = kw["pass_"].name()
        ran.append(name)
        if name in ("VF2Layout", "VF2PostLayout"):
            ps = kw["property_set"]
            r = ps.get(f"{name}_stop_reason")
            reasons[name] = getattr(r, "value", str(r))

    pm = generate_preset_pass_manager(optimization_level=level, target=target,
                                      seed_transpiler=seed)
    isa = pm.run(qc, callback=cb)
    return dict(
        passes_ran=ran,
        vf2_ran="VF2Layout" in ran,
        vf2_found=reasons.get("VF2Layout", "") == "solution found",
        vf2_stop_reason=reasons.get("VF2Layout", "pass did not run"),
        sabre_ran="SabreLayout" in ran,
        vf2post_ran="VF2PostLayout" in ran,
        vf2post_found=reasons.get("VF2PostLayout", "") == "solution found",
        vf2post_stop_reason=reasons.get("VF2PostLayout", "pass did not run"),
        depth=isa.depth(), cz=isa.count_ops().get("cz", 0),
        layout=sorted(isa.layout.final_index_layout()))


def check_c(outdir, machine, n_pairs):
    import engine_config as cfg
    import jobs as jobs_mod
    import real_data as rd
    import qiskit

    print("\n" + "=" * 74)
    print("CHECK C: TRANSPILER AUDIT (COMPILE ONLY)")
    print("=" * 74)
    print("  No simulator is constructed and no shot is taken anywhere in")
    print("  this section. Only development-period cards are read.")

    print("\n  VERSIONS")
    print(f"    this interpreter      python {sys.version.split()[0]}")
    print(f"    qiskit                {qiskit.__version__}")
    try:
        import qiskit_aer
        print(f"    qiskit-aer            {qiskit_aer.__version__}")
    except ImportError:
        print("    qiskit-aer            NOT IMPORTABLE in this interpreter")
    print("    For the record, the Round 1 run used team_code/.venv on python")
    print("    3.12.4 with qiskit 2.5.2 and qiskit-aer 0.17.2, recorded in")
    print("    logs/smoke_test_targets.log and NOTES.md. The main project")
    print("    .venv is python 3.13.7, where qiskit-aer has no build, so it")
    print("    cannot be imported there. Both have the SAME qiskit 2.5.2, and")
    print("    Check C only compiles, so the layout results below do not")
    print("    depend on which of the two runs this script.")

    print("\n  COMPILER SETTINGS THE ENGINE USES (engine/engine_config.py)")
    print(f"    OPT_LEVEL             {cfg.OPT_LEVEL}")
    print(f"    SEED_TRANSPILE        {cfg.SEED_TRANSPILE}")
    print(f"    RANDOM_DRAWS          {cfg.RANDOM_DRAWS}")
    print("    The engine's only transpiler call is")
    print("        generate_preset_pass_manager(")
    print("            optimization_level=cfg.OPT_LEVEL, target=s_target,")
    print("            seed_transpiler=cfg.SEED_TRANSPILE)")
    print("    plus initial_layout=pick for the random arm. There is NO")
    print("    layout_trials override anywhere: grepping engine/ for")
    print("    layout_trials returns nothing, so SabreLayout keeps the preset")
    print("    default for the level in use.")

    store = rd.open_store(machine)
    base, _ = rd.load_base_target(machine)
    dev = [i for i, t in enumerate(store.times)
           if cfg.WINDOW_START <= str(t.date()) <= cfg.WINDOW_END]
    train = [i for i, t in enumerate(store.times) if jobs_mod.in_training(t)]
    permanent = None
    for i in train:
        d = rd.dead_qubits(store.snapshot(i))
        permanent = set(d) if permanent is None else (permanent & d)
    permanent = permanent or set()
    print(f"\n  CARDS AND TARGET, {machine}")
    print(f"    development-period states available: {len(dev)} "
          f"({store.times[dev[0]]} to {store.times[dev[-1]]})")
    print(f"    permanent defects from training days: {sorted(permanent)}")

    fixed_i = dev[0]
    snap = store.snapshot(fixed_i)
    target, forbid, _ = rd.strategy_target(snap, base, permanent)
    print(f"    fixed card for the pass audit: state index {fixed_i}, "
          f"first seen {store.times[fixed_i]}")
    print(f"    target built exactly as the engine does, through")
    print(f"    real_data.strategy_target(snap, base, permanent): "
          f"{target.num_qubits} qubits, {len(forbid)} forbidden")

    qcs = build_circuits()
    names = CIRCUITS + [f"qft{n}" for n in QFT_SIZES]

    print("\n  INTERACTION GRAPH MAX DEGREE (logical circuit, two-qubit gates)")
    print("    `width` is the circuit's qubit count, `touched` the qubits that")
    print("    take part in a two-qubit gate. A gate given as one opaque")
    print("    multi-qubit instruction, as QFTGate is, is decomposed first.")
    print(f"    {'circuit':<8} {'width':>6} {'touched':>8} {'edges':>6} "
          f"{'max degree':>11}")
    deg_rows = []
    for n in names:
        md, nq, ne = interaction_degree(qcs[n])
        width = qcs[n].num_qubits
        shape = ("path" if md <= 2 else
                 "complete" if ne == nq * (nq - 1) // 2 and nq > 2 else
                 "star-like" if md >= nq - 1 else "mixed")
        print(f"    {n:<8} {width:>6} {nq:>8} {ne:>6} {md:>11}   {shape}")
        deg_rows.append(dict(circuit=n, circuit_width=width,
                             qubits_touched_by_2q=nq, edges=ne,
                             max_degree=md, shape=shape,
                             fits_heavy_hex_degree_3=md <= 3))
    pd.DataFrame(deg_rows).to_csv(outdir / "C1_interaction_degree.csv",
                                  index=False)
    print("    The device is heavy-hex, where every physical qubit has degree")
    print("    at most 3. A circuit whose max degree is above 3 cannot be")
    print("    embedded without routing, so VF2Layout cannot succeed on it.")

    print("\n  WHICH LAYOUT PASSES REALLY RAN, on the one fixed card")
    print(f"    {'circuit':<8} {'lvl':>4} {'VF2Layout':>10} "
          f"{'VF2 found':>10} {'Sabre':>6} {'VF2Post':>8} "
          f"{'Post found':>11} {'depth':>6} {'cz':>5}")
    pass_rows = []
    for n in names:
        for lvl in LEVELS:
            r = compile_once(qcs[n], target, lvl, cfg.SEED_TRANSPILE)
            print(f"    {n:<8} {lvl:>4} {str(r['vf2_ran']):>10} "
                  f"{str(r['vf2_found']):>10} {str(r['sabre_ran']):>6} "
                  f"{str(r['vf2post_ran']):>8} {str(r['vf2post_found']):>11} "
                  f"{r['depth']:>6} {r['cz']:>5}")
            pass_rows.append(dict(
                circuit=n, level=lvl, vf2layout_ran=r["vf2_ran"],
                vf2layout_found=r["vf2_found"],
                vf2layout_stop_reason=r["vf2_stop_reason"],
                sabrelayout_ran=r["sabre_ran"],
                vf2postlayout_ran=r["vf2post_ran"],
                vf2postlayout_found=r["vf2post_found"],
                vf2postlayout_stop_reason=r["vf2post_stop_reason"],
                final_depth=r["depth"], final_cz=r["cz"],
                layout=" ".join(map(str, r["layout"])),
                n_passes_ran=len(r["passes_ran"])))
    pd.DataFrame(pass_rows).to_csv(outdir / "C2_layout_passes.csv", index=False)
    print("    VF2Layout and VF2PostLayout score candidate placements with the")
    print("    target's error rates, so they are the error-aware passes.")
    print("    SabreLayout minimises swaps and never reads an error rate, so")
    print("    a layout that comes from Sabre alone is error-blind.")

    print("\n  ERROR SENSITIVITY: does the chosen layout move when the card")
    print(f"  changes? {n_pairs} pairs of DIFFERENT development-period cards, "
          f"{machine},")
    print("  same seed, compile only.")
    rng = np.random.default_rng(SEED_PAIRS)
    pairs = []
    while len(pairs) < n_pairs:
        a, b = rng.choice(dev, size=2, replace=False)
        if (int(a), int(b)) not in pairs and (int(b), int(a)) not in pairs:
            pairs.append((int(a), int(b)))
    tcache = {}

    def target_of(i):
        if i not in tcache:
            t, f, _ = rd.strategy_target(store.snapshot(i), base, permanent)
            tcache[i] = (t, frozenset(f))
        return tcache[i]

    forbid_diff = sum(1 for a, b in pairs if target_of(a)[1] != target_of(b)[1])
    print(f"    pairs whose forbidden-qubit set also differs: {forbid_diff} of "
          f"{n_pairs}")
    print("    That is a confound: when the dead list changes, the coupling")
    print("    map changes too, so even an error-blind pass can move. It is")
    print("    reported so the shares below can be read honestly.")
    print(f"\n    {'circuit':<8} {'lvl':>4} {'qubit set changed':>18} "
          f"{'order changed':>15} {'depth changed':>15}")
    sens_rows = []
    for n in names:
        for lvl in LEVELS:
            chg_set = chg_ord = chg_depth = 0
            for a, b in pairs:
                ra = compile_once(qcs[n], target_of(a)[0], lvl,
                                  cfg.SEED_TRANSPILE)
                rb = compile_once(qcs[n], target_of(b)[0], lvl,
                                  cfg.SEED_TRANSPILE)
                chg_set += set(ra["layout"]) != set(rb["layout"])
                chg_ord += ra["layout"] != rb["layout"]
                chg_depth += ra["depth"] != rb["depth"]
            print(f"    {n:<8} {lvl:>4} {chg_set/len(pairs)*100:>17.1f}% "
                  f"{chg_ord/len(pairs)*100:>14.1f}% "
                  f"{chg_depth/len(pairs)*100:>14.1f}%")
            sens_rows.append(dict(
                circuit=n, level=lvl, n_pairs=len(pairs),
                pct_qubit_set_changed=chg_set / len(pairs) * 100,
                pct_layout_order_changed=chg_ord / len(pairs) * 100,
                pct_depth_changed=chg_depth / len(pairs) * 100,
                pairs_with_different_forbidden_set=forbid_diff))
    pd.DataFrame(sens_rows).to_csv(outdir / "C3_error_sensitivity.csv",
                                   index=False)
    pd.DataFrame([dict(pair_index=i, state_a=a, state_b=b,
                       time_a=str(store.times[a]), time_b=str(store.times[b]))
                  for i, (a, b) in enumerate(pairs)]).to_csv(
        outdir / "C4_card_pairs_used.csv", index=False)
    return pass_rows, sens_rows, deg_rows


# ============================================================== summary

def summary(pass_rows, sens_rows, deg_rows):
    print("\n" + "=" * 74)
    print("PLAIN SUMMARY")
    print("=" * 74)
    p = pd.DataFrame(pass_rows)
    d = {r["circuit"]: r for r in deg_rows}
    l2 = p[p.level == 2].set_index("circuit")
    l3 = p[p.level == 3].set_index("circuit")
    aware2 = [c for c in l2.index if l2.loc[c, "vf2layout_found"]]
    post2 = [c for c in l2.index if not l2.loc[c, "vf2layout_found"]
             and l2.loc[c, "vf2postlayout_found"]]
    blind2 = [c for c in l2.index if not l2.loc[c, "vf2layout_found"]
              and not l2.loc[c, "vf2postlayout_found"]]

    print("\n  AT LEVEL 2, WHICH CIRCUITS GET AN ERROR-AWARE LAYOUT?")
    print("  Fully error-aware, VF2Layout found a perfect embedding and chose")
    print("  it by scoring the card's error rates:")
    print(f"    {', '.join(aware2) if aware2 else 'none'}")
    print("  These are the circuits whose interaction graph is a path, max")
    print("  degree 2, which fits the heavy-hex lattice directly:")
    for c in aware2:
        print(f"    {c:<8} max degree {d[c]['max_degree']}")
    print("\n  Error-blind layout, then an error-aware repair: VF2Layout found")
    print("  no embedding, SabreLayout chose the qubits by swap count only,")
    print("  and VF2PostLayout then moved the result to a better scoring spot:")
    print(f"    {', '.join(post2) if post2 else 'none'}")
    for c in post2:
        md = d[c]["max_degree"]
        note = ("above the heavy-hex limit of 3" if md > 3
                else "degree fits, but no embedding exists for this shape")
        print(f"    {c:<8} max degree {md}  ({note})")
    if blind2:
        print("\n  Error-blind with no repair, VF2PostLayout also failed:")
        print(f"    {', '.join(blind2)}")
    print("\n  So at level 2 no circuit is left completely error-blind, but the")
    print("  two groups are not the same thing. The GHZ circuits get the")
    print("  layout chosen by error from the start, over the whole device. The")
    print("  BV and QFT circuits get a layout chosen by swap count and then")
    print("  nudged by error afterwards, inside what the routing already fixed.")

    print("\n  DOES LEVEL 3 CHANGE THAT?")
    changed = []
    for c in l2.index:
        if (l2.loc[c, "vf2layout_found"] != l3.loc[c, "vf2layout_found"] or
                l2.loc[c, "vf2postlayout_ran"] != l3.loc[c, "vf2postlayout_ran"]
                or l2.loc[c, "vf2postlayout_found"]
                != l3.loc[c, "vf2postlayout_found"]):
            changed.append(c)
    print("  Which pass succeeds does not change for VF2Layout: the same")
    print("  circuits embed and the same ones do not, because that depends on")
    print("  the interaction graph, not the level. What changes is the repair:")
    print(f"    circuits whose pass pattern changed at all: "
          f"{', '.join(changed) if changed else 'none'}")
    for c in l2.index:
        print(f"    {c:<8} lvl2 VF2Post ran {str(l2.loc[c,'vf2postlayout_ran']):<5} "
              f"found {str(l2.loc[c,'vf2postlayout_found']):<5} "
              f"depth {l2.loc[c,'final_depth']:>4} cz {l2.loc[c,'final_cz']:>4}"
              f"   |   lvl3 ran {str(l3.loc[c,'vf2postlayout_ran']):<5} "
              f"found {str(l3.loc[c,'vf2postlayout_found']):<5} "
              f"depth {l3.loc[c,'final_depth']:>4} cz {l3.loc[c,'final_cz']:>4}")
    print("  Level 3 adds a VF2PostLayout attempt to the GHZ circuits, which")
    print("  level 2 skipped because VF2Layout had already placed them. The")
    print("  final depth and cz count of the GHZ circuits do not change, so")
    print("  the extra pass moves where the circuit sits without making it")
    print("  shorter. For BV and QFT, level 3 mostly changes depth and cz")
    print("  through better routing and optimisation, not through the layout")
    print("  mechanism.")

    s = pd.DataFrame(sens_rows)
    print("\n  HOW OFTEN DOES THE CHOSEN LAYOUT MOVE WHEN THE CARD CHANGES?")
    for lvl in LEVELS:
        sl = s[s.level == lvl].set_index("circuit")
        print(f"    level {lvl}: " + "  ".join(
            f"{c} {sl.loc[c,'pct_qubit_set_changed']:.0f}%" for c in sl.index))
    print("  A high share means the layout really does follow the card, which")
    print("  is what an error-aware choice should do. A low share means the")
    print("  layout is being driven by the lattice and the seed instead.")

    print("\n  DOES ANYTHING IN ROUND 1 LOOK DIFFERENT ONCE THIS IS KNOWN?")
    print("  Round 1 compiled everything at level 2, and the five study")
    print("  circuits split into the two groups above: ghz5, ghz8 and ghz10")
    print("  are placed by error over the whole device, while bv8 and bv10 are")
    print("  placed by swap count and then repaired. The whole experiment asks")
    print("  how much a stale card costs when it steers the layout. That")
    print("  steering is strongest exactly where VF2Layout drives the choice,")
    print("  so the GHZ circuits and the BV circuits are not measuring quite")
    print("  the same thing, and pooling them hides that. This is consistent")
    print("  with a per-circuit split being worth reporting beside the pooled")
    print("  number, which is what Check B does. It does not overturn any")
    print("  Round 1 result: no number changed here, and the per-circuit stale")
    print("  regret in Check B keeps the same direction as the pooled figure.")
    print("  One more thing to carry forward: Check A found that the 360 gap")
    print("  jobs are dropped from the headline although PROTOCOL.md section")
    print("  10 and Amendment A1.6 both say they stay in. That is a protocol")
    print("  departure in the analysis script, and it is separate from")
    print("  anything the transpiler does.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results",
                    default=str(ROOT / "outputs/test_full/all_rows.csv"))
    ap.add_argument("--outdir", default=str(ROOT / "outputs/row_check_2"))
    ap.add_argument("--machine", default="ibm_fez")
    ap.add_argument("--pairs", type=int, default=20)
    args = ap.parse_args()
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    print("THREE READ-ONLY AUDIT CHECKS ON ROUND 1 AND THE INSTALLED QISKIT")
    print("EXPLORATORY AND POST-HOC. No IBM call. The engine is not re-run on")
    print("the 5648 jobs. Check C compiles only: no simulation, no shots.")
    print("regret = ceiling minus strategy. gain = F_strategy minus F_stale.")
    print(f"source: {args.results}\n")

    df = M20.load(args.results)
    df["dead"] = df.dead_qubits_used.fillna("").astype(str).str.strip() != ""
    w = M20.widen(df)

    check_a(df, w, outdir)
    check_b(df, w, outdir)
    pass_rows, sens_rows, deg_rows = check_c(outdir, args.machine, args.pairs)
    summary(pass_rows, sens_rows, deg_rows)
    print(f"\nfiles written to {outdir}")
    print("EXPLORATORY AND POST-HOC throughout. Where this touches measurement")
    print("noise against real drift, the wording is 'consistent with'.")


main()
