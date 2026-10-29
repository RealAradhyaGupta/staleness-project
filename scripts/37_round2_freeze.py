"""Round 2, Stage 2: the conformance table and FREEZE.txt.

The conformance table puts every item of protocol_round2.md next to the line
of code that carries it out, with both quoted from the files rather than
retyped, so a reader can check each pair without trusting this script.

FREEZE.txt holds the SHA-256 of the protocol, the rule, the analysis, the
engine files and the w(D) table. After this the rule cannot change: any edit
changes a checksum.
"""
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "engine"))
sys.path.insert(0, str(ROOT / "scripts"))

OUT = ROOT / "outputs" / "round2"
PROTOCOL = ROOT / "protocol_round2.md"

FREEZE_FILES = [
    "protocol_round2.md",
    "scripts/30_hybrid_rule.py",
    "scripts/31_analyse_round2.py",
    "scripts/33_round2_fit.py",
    "scripts/34_run_round2.py",
    "scripts/35_build_round2_tables.py",
    "scripts/36_freeze_tests.py",
    "scripts/37_round2_freeze.py",
    "engine/run_engine.py",
    "engine/real_data.py",
    "engine/strategies.py",
    "engine/jobs.py",
    "engine/circuits.py",
    "engine/engine_config.py",
    "engine/snapshot.py",
    "scripts/20_analyse_results.py",
]


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def quote_md(needle, n_lines=1):
    """Quote the protocol by finding a line, so the quote is the real text."""
    lines = PROTOCOL.read_text().splitlines()
    for i, line in enumerate(lines):
        if needle in line:
            txt = " ".join(x.strip() for x in lines[i:i + n_lines] if x.strip())
            return f"protocol_round2.md:{i+1}: {txt}"
    return f"NOT FOUND IN PROTOCOL: {needle!r}"


def quote_code(relpath, needle, n_lines=1):
    """Quote the code by finding a line, so the quote is the real source."""
    path = ROOT / relpath
    lines = path.read_text().splitlines()
    for i, line in enumerate(lines):
        if needle in line:
            txt = " ".join(x.strip() for x in lines[i:i + n_lines] if x.strip())
            return f"{relpath}:{i+1}: {txt}"
    return f"NOT FOUND IN CODE: {relpath} {needle!r}"


ITEMS = [
    ("the blend formula",
     quote_md("predicted log value = (1 - w(D))"),
     quote_code("scripts/30_hybrid_rule.py",
                "vals = np.exp((1.0 - w) * arr[0] + w * med)")),
    ("N per field group",
     quote_md("| readout | `readout_error` | 12 |"),
     quote_code("scripts/30_hybrid_rule.py", "N_BY_GROUP = {")),
    ("w(D) table, readout",
     quote_md("| readout | 0.15 | 0.40 | 0.65 | 0.85 | 0.90 | 0.90 |"),
     quote_code("scripts/30_hybrid_rule.py", '"readout": {1: 0.15')),
    ("w(D) table, sx",
     quote_md("| sx | 0.05 | 0.05 | 0.15 | 0.30 | 0.55 | 0.70 |"),
     quote_code("scripts/30_hybrid_rule.py", '"sx":      {1: 0.05')),
    ("w(D) table, cz",
     quote_md("| cz | 0.00 | 0.05 | 0.10 | 0.25 | 0.45 | 0.55 |"),
     quote_code("scripts/30_hybrid_rule.py", '"cz":      {1: 0.00')),
    ("w(D) table, times",
     quote_md("| times | 0.00 | 0.10 | 0.15 | 0.35 | 0.80 | 0.90 |"),
     quote_code("scripts/30_hybrid_rule.py", '"times":   {1: 0.00')),
    ("last N DISTINCT values of that field",
     quote_md("The last N distinct values of that"),
     quote_code("scripts/30_hybrid_rule.py",
                "hist = strat.distinct_history(store, info_index, field, n)")),
    ("averaging on the log",
     quote_md("All averaging is on the log of each value"),
     quote_code("scripts/30_hybrid_rule.py",
                "arr = np.array([strat._safe_log(v) for _, v in hist])")),
    ("the dead qubit guard, M = 1",
     quote_md("`M = 1`, chosen as"),
     quote_code("scripts/30_hybrid_rule.py", "GUARD_M = 1")),
    ("the guard looks back M distinct states",
     quote_md("A qubit that is dead in any of the last `M` distinct"),
     quote_code("scripts/30_hybrid_rule.py",
                "for i in range(info_index, max(info_index - m, -1), -1):")),
    ("guard applies to hybrid, not to the others",
     quote_md("For the `stale` arm that is already what gets removed"),
     quote_code("scripts/30_hybrid_rule.py", 'if arm == "hybrid":')),
    ("guard_only is not run",
     quote_md("The pre-stated ablation `guard_only`, meaning stale plus the"),
     quote_code("scripts/30_hybrid_rule.py", "DROPPED_ARMS = {")),
    ("permanent defects from development cards only",
     quote_md("**Permanent defects.** Qubits dead in every development state"),
     quote_code("scripts/30_hybrid_rule.py", "PERMANENT_DEFECTS = {", 5)),
    ("optimization level 2 and seed 11",
     quote_md("**Compiler settings, unchanged from Round 1.**"),
     quote_code("scripts/34_run_round2.py",
                "optimization_level=cfg.OPT_LEVEL, target=s_target,")),
    ("shots 4000",
     quote_md("`shots = 4000`"),
     quote_code("engine/engine_config.py", "SHOTS = 4000")),
    ("one simulator seed per job",
     quote_md("one simulator seed per job"),
     quote_code("scripts/34_run_round2.py", "return (cfg.SEED_SIM")),
    ("the eight circuits",
     quote_md("| qft10 | 10 | approximate QFT"),
     quote_code("scripts/34_run_round2.py", 'CIRCUIT_ORDER = ["ghz5"', 2)),
    ("approximate QFT drops rotations below pi/2^3",
     quote_md("drops every controlled rotation smaller than"),
     quote_code("engine/circuits.py", "AQFT_MIN_ANGLE = math.pi / 2 ** 3")),
    ("the 4-peak input",
     quote_md("input is an even mixture of every integer", 2),
     quote_code("engine/circuits.py",
                "for q in range(2, n):            # even mixture")),
    ("the six arms",
     quote_md("| `hybrid_no_guard` | the frozen rule with the guard off |"),
     quote_code("scripts/30_hybrid_rule.py", 'ARMS = ["stale"', 2)),
    ("random and std_adjusted dropped",
     quote_md("`random` and `std_adjusted` are dropped"),
     quote_code("scripts/30_hybrid_rule.py", 'ARMS = ["stale"', 2)),
    ("the job generator, unchanged",
     quote_md("`numpy.random.default_rng(20260828)` is created once"),
     quote_code("engine/jobs.py", "rng = np.random.default_rng(cfg.SEED_SUBMIT)")),
    ("submission days 13 to 23 October",
     quote_md("Submission days: 13 October to 23 October 2026 inclusive"),
     quote_code("scripts/34_run_round2.py", 'FRESH_SUBMIT_START = "2026-10-13"', 2)),
    ("delays 1 to 48 hours",
     quote_md("Delays `D`: 1, 3, 6, 12, 24, 48 hours"),
     quote_code("engine/engine_config.py", "DELAYS_H = [1, 3, 6, 12, 24, 48]")),
    ("validity rule, 5 states of history and not past the end",
     quote_md("A job is valid only if at least 5 states of history"),
     quote_code("engine/jobs.py", "if info < min_history - 1:", 3)),
    ("invalid jobs dropped and counted per delay",
     quote_md("are dropped and counted per delay, never silently skipped"),
     quote_code("scripts/34_run_round2.py", "dropped {trimmed}")),
    ("job identity",
     quote_md("A job's identity is `(machine, draw_order, delay_h, circuit)`"),
     quote_code("scripts/31_analyse_round2.py",
                'JOB = ["machine", "draw_order", "delay_h", "circuit"]')),
    ("the store spans both windows",
     quote_md("The state store the engine reads spans BOTH windows"),
     quote_code("scripts/34_run_round2.py",
                'os.environ.setdefault("STALENESS_CLEAN_DIR"', 2)),
    ("the combined tables must reproduce data/clean",
     quote_md("stops unless the development part of the"),
     quote_code("scripts/35_build_round2_tables.py",
                "raise SystemExit(f\"STOP: the combined tables do not reproduce ")),
    ("H1, no harm, bound -0.002",
     quote_md("**H1, no harm.**"),
     quote_code("scripts/31_analyse_round2.py", "H1_BOUND = -0.002")),
    ("H1 pooled over D = 1 and 3",
     quote_md("pooled over `D = 1` and `D = 3` hours"),
     quote_code("scripts/31_analyse_round2.py", "H1_DELAYS = [1, 3]")),
    ("H2 pooled over D = 6 to 48",
     quote_md("**H2, primary.**"),
     quote_code("scripts/31_analyse_round2.py", "H2_DELAYS = [6, 12, 24, 48]")),
    ("H2 lower bound above 0",
     quote_md("has a lower 95 percent bound above 0"),
     quote_code("scripts/31_analyse_round2.py",
                'one_test(f"H2 hybrid minus stale, D = 6 to 48 h", h2, "gain_hybrid",')),
    ("6 h and 24 h also reported separately",
     quote_md("`D = 6` and `D = 24` are also"),
     quote_code("scripts/31_analyse_round2.py",
                'per_delay = [one_test(f"hybrid minus stale, D = {d} h",')),
    ("secondary list",
     quote_md("* by circuit family, GHZ, BV and QFT, and by individual circuit"),
     quote_code("scripts/31_analyse_round2.py",
                'FAMILY = {"ghz5": "GHZ"', 3)),
    ("block bootstrap on whole calendar days",
     quote_md("95 percent intervals from a block bootstrap that resamples"),
     quote_code("scripts/20_analyse_results.py",
                'days = frame.day.unique()')),
    ("the bootstrap is imported, not reimplemented",
     quote_md("`block_boot` from `scripts/20_analyse_results.py` rather than"),
     quote_code("scripts/31_analyse_round2.py",
                "return M20.block_boot(frame, col, rng)")),
    ("same seed and resample count as Round 1",
     quote_md("`SEED_BOOT = 20261014` and the same"),
     quote_code("scripts/31_analyse_round2.py",
                "rng = np.random.default_rng(M20.SEED_BOOT)")),
    ("design effect reported",
     quote_md("A design effect is also reported"),
     quote_code("scripts/31_analyse_round2.py",
                "de = (clustered / naive) ** 2 if naive")),
    ("nothing excluded but the validity rule",
     quote_md("**Nothing is excluded except what this section declares.**"),
     quote_code("scripts/31_analyse_round2.py",
                "# jobs that straddle a publishing gap stay IN and are flagged")),
    ("the publishing gap stays in, 18 hour threshold",
     quote_md("longer than 18 hours between neighbouring distinct states"),
     quote_code("scripts/31_analyse_round2.py", "GAP_MIN_H = 18.0")),
    ("gap jobs reported separately",
     quote_md("Jobs that straddle one are kept in the headline"),
     quote_code("scripts/31_analyse_round2.py",
                'one_test("hybrid minus stale, jobs across a gap",')),
    ("the three dead qubit views",
     quote_md("1. every row as it is"),
     quote_code("scripts/31_analyse_round2.py",
                'views["1 all rows as they are"] = w', 4)),
    ("dead row share of stale regret",
     quote_md("The share of total stale regret that"),
     quote_code("scripts/31_analyse_round2.py",
                "dead_share = (sub[sub.dead_stale].regret_stale.sum() / tot")),
    ("sanity check 1",
     quote_md("1. Stale regret is exactly 0 on jobs where no new state"),
     quote_code("scripts/31_analyse_round2.py",
                "worst = float(np.abs(nc.regret_stale).max())")),
    ("sanity check 2",
     quote_md("2. Ceiling regret is exactly 0 by construction"),
     quote_code("scripts/31_analyse_round2.py",
                "worst_c = float(np.abs(w.regret_ceiling).max())")),
    ("compute cut order",
     quote_md("1. drop the two ablations", 3),
     quote_code("scripts/34_run_round2.py",
                'ap.add_argument("--circuits"')),
    ("the run environment",
     quote_md("The run is on `team_code/.venv`"),
     quote_code("scripts/32_round2_stage0.py", 'print(f"  qiskit               ')),
    ("secrets stay in .env",
     quote_md("The API key and the instance CRN live only in `.env`"),
     quote_code("scripts/32_round2_stage0.py", "def hide(text, secrets):")),
    ("data/raw read only",
     quote_md("`data/raw` is read only"),
     quote_code("scripts/35_build_round2_tables.py", "os.symlink(f.resolve(), link)")),
    ("stop rule, freeze tests",
     quote_md("2. Stage 2: any freeze test fails"),
     quote_code("scripts/36_freeze_tests.py",
                "print(\"STOP RULE FIRED. The rule is not frozen and nothing is fetched.\")")),
]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    print("=" * 72)
    print("ROUND 2 STAGE 2: CONFORMANCE")
    print("=" * 72)
    rows = []
    bad = 0
    for topic, prot, code in ITEMS:
        ok = "NOT FOUND" not in prot and "NOT FOUND" not in code
        if not ok:
            bad += 1
            print(f"  UNRESOLVED  {topic}")
            if "NOT FOUND" in prot:
                print(f"      {prot}")
            if "NOT FOUND" in code:
                print(f"      {code}")
        rows.append({"topic": topic, "protocol_says": prot,
                     "code_does": code,
                     "resolved": "yes" if ok else "no"})
    conf = pd.DataFrame(rows)
    conf.to_csv(OUT / "r2_conformance.csv", index=False)
    print(f"  {len(rows)} protocol items checked, {bad} unresolved")
    print(f"  written to {OUT / 'r2_conformance.csv'}")
    if bad:
        print("  NOTE: an unresolved row means this script could not find the")
        print("  quoted text, which is a fault in this script, not proof that")
        print("  the code is wrong. It is reported and the run continues.")

    print()
    print("=" * 72)
    print("ROUND 2 FREEZE")
    print("=" * 72)
    import importlib
    rule = importlib.import_module("30_hybrid_rule")
    table = json.dumps({"N_BY_GROUP": rule.N_BY_GROUP,
                        "W_BY_GROUP_AND_DELAY": rule.W_BY_GROUP_AND_DELAY,
                        "GUARD_M": rule.GUARD_M,
                        "PERMANENT_DEFECTS": rule.PERMANENT_DEFECTS},
                       sort_keys=True)
    table_sha = hashlib.sha256(table.encode()).hexdigest()

    lines = ["ROUND 2 FREEZE",
             "",
             "After this point the rule cannot change. Any edit to a file",
             "below changes its checksum and is therefore visible.",
             "",
             f"frozen at (UTC): {pd.Timestamp.now(tz="UTC").isoformat()}",
             f"rule cross check: {rule.CHECK_NOTE}",
             "",
             "SHA-256:"]
    for rel in FREEZE_FILES:
        p = ROOT / rel
        if not p.exists():
            lines.append(f"  MISSING   {rel}")
            print(f"  MISSING   {rel}")
            continue
        d = sha(p)
        lines.append(f"  {d}  {rel}")
        print(f"  {d}  {rel}")
    lines += ["", "the w(D) table itself, as canonical JSON:",
              f"  {table_sha}  (sha256 of the table below)",
              f"  {table}", ""]
    print(f"\n  {table_sha}  the w(D) table as canonical JSON")
    print(f"  {table}")
    (ROOT / "FREEZE.txt").write_text("\n".join(lines) + "\n")
    print(f"\n  written to {ROOT / 'FREEZE.txt'}")
    return 0


sys.exit(main())
