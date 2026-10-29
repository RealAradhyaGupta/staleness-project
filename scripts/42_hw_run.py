"""Stage 6, Part A: the hardware run. Standalone, restartable, capped.

Everything this script does is fixed in protocol_hardware.md, which was
written and frozen before it ran. It does not change the rule, the Round 2
protocol, any frozen Round 2 file or any Round 2 result. The frozen rule in
scripts/30_hybrid_rule.py is imported and used exactly as it stands.

What it does, in order:
  1. confirms the instance name and plan, and reads the account usage
  2. picks the device by the protocol rule (kingston, else fez, never
     marrakesh, never anything else)
  3. runs ONE pilot: a 2 qubit Bell circuit at 100 shots, reads its usage,
     stops if it used more than 10 s
  4. projects the usage of all 12 jobs by the model fixed in the protocol and
     stops if the projection is above 150 s
  5. three compile times two hours apart. At each: fetches the live cards,
     rebuilds the combined store, and transpiles each of 4 circuits under
     each of 3 arms. The compiled circuits are written to disk as QPY, which
     is what "held locally" means here.
  6. holds each compiled job for D = 6 h, then submits it as ONE Sampler job
     with one PUB per DISTINCT transpiled circuit, 1000 shots each, strictly
     one job at a time, reading the usage after each one before considering
     the next.
  7. retrieves every result by job id and writes it to disk as it arrives.

The cap is 180 s of QPU usage. Nothing is submitted when
usage_so_far + 1.5 * largest_job_so_far would pass 150 s, when less than
480 s remain on the account, or when the usage cannot be read at all. The
last of those is the important one: it fails CLOSED, so an unreadable usage
total never leads to a submission.

The API key and the CRN are read from .env and are never printed. Every line
of output goes through hide() first.

Usage:
  caffeinate -dimsu nohup team_code/.venv/bin/python scripts/42_hw_run.py \
      > outputs/hardware/hw_console.txt 2>&1 &
"""
import json
import os
import sys
import time
import traceback
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs/hardware"
STATE_FILE = OUT / "hw_state.json"
STATUS_FILE = OUT / "STATUS.txt"
COMPILED = OUT / "compiled"
RESULTS = OUT / "results"
HW_CARDS = ROOT / "data/hardware_cards"

# the combined store this stage reads. Set BEFORE real_data is imported.
os.environ["STALENESS_CLEAN_DIR"] = str(ROOT / "data/clean_hw")
os.environ["STALENESS_CACHE_DIR"] = str(ROOT / "data/cache_hw")

sys.path.insert(0, str(ROOT / "engine"))
sys.path.insert(0, str(ROOT / "scripts"))

# ------------------------------------------------------- protocol constants

ALLOWED_DEVICES = ["ibm_kingston", "ibm_fez"]   # in the protocol's order
FORBIDDEN_DEVICE = "ibm_marrakesh"              # paused, never used
CIRCUITS = ["ghz5", "ghz8", "bv8", "qft5"]
ARMS = ["stale", "window_mean", "hybrid"]
HW_SHOTS = 1000                  # per PUB, protocol section 8
PILOT_SHOTS = 100                # protocol section 4
N_SLOTS = 3
COMPILE_GAP_H = 2
HOLD_H = 6
OPT_LEVEL = 2                    # protocol section 12
SEED_TRANSPILE = 11

CAP_TOTAL_S = 180.0              # the hard ceiling for the whole stage
CAP_SUBMIT_S = 150.0             # the sequential guard
PILOT_MAX_S = 10.0               # stop if the pilot costs more than this
MIN_ACCOUNT_REMAIN_S = 480.0     # 8 minutes
CAP_HEADROOM = 1.5               # usage_so_far + 1.5 * largest job so far

RETRY_WAIT_S = 60
RETRY_MINUTES = 45
CARD_WINDOW_START = datetime(2026, 10, 24, 0, 0, 0, tzinfo=timezone.utc)

SECRETS = []


# -------------------------------------------------------------- plumbing

def utcnow():
    return datetime.now(timezone.utc)


def read_env():
    env = {}
    for line in (ROOT / ".env").read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def hide(text):
    safe = str(text)
    for s in SECRETS:
        if s and len(s) > 6:
            safe = safe.replace(s, "<hidden>")
            safe = safe.replace(s.replace(":", "%3A"), "<hidden>")
    return safe


def say(*parts):
    msg = hide(" ".join(str(p) for p in parts))
    print(f"[{utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')}] {msg}", flush=True)


class StepFailed(Exception):
    """A step that kept failing past the 45 minute limit."""


# ------------------------------------------------------------------ state

def load_state():
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception as e:
            say(f"  state file unreadable ({type(e).__name__}), starting fresh")
    return {"device": None, "t0_utc": None, "pilot": None,
            "per_job_usage_s": {}, "account_usage_start_s": None,
            "jobs": {}, "events": []}


STATE = {}


def save_state():
    OUT.mkdir(parents=True, exist_ok=True)
    tmp = STATE_FILE.with_suffix(".json.part")
    tmp.write_text(hide(json.dumps(STATE, indent=2, default=str)))
    tmp.rename(STATE_FILE)


def event(kind, note):
    """Append a truthful event. Retries, delays, late compiles and MISSED
    jobs all land here and all reach REPORT.md."""
    STATE.setdefault("events", []).append(
        {"utc": utcnow().isoformat(), "kind": kind, "note": hide(str(note))})
    save_state()


def write_status(step, next_due=None, extra=""):
    OUT.mkdir(parents=True, exist_ok=True)
    total, n_done = usage_total(), len(STATE.get("per_job_usage_s", {}))
    lines = [
        "Stage 6 Part A, hardware run. No secret is written in this file.",
        f"written           {utcnow().isoformat()}",
        f"device            {STATE.get('device')}",
        f"last step done    {step}",
        f"next step due     {next_due.isoformat() if next_due else 'now'}",
        f"jobs finished     {n_done} of {N_SLOTS * len(CIRCUITS)}",
        f"QPU usage so far  {total:.3f} s of a {CAP_TOTAL_S:.0f} s cap",
        f"note              {extra}",
    ]
    STATUS_FILE.write_text(hide("\n".join(lines) + "\n"))


def retry(label, fn, minutes=RETRY_MINUTES):
    """Every IBM call goes through here: on failure wait 60 s and try again,
    for up to 45 minutes. Then give up and let the caller mark the job."""
    deadline = time.time() + minutes * 60
    attempt = 0
    while True:
        attempt += 1
        try:
            return fn()
        except Exception as e:
            note = f"{label}: attempt {attempt} failed: {type(e).__name__}: {e}"
            say("  " + note)
            event("retry", note)
            if time.time() + RETRY_WAIT_S > deadline:
                raise StepFailed(f"{label} still failing after {minutes} "
                                 f"minutes: {type(e).__name__}: {e}")
            time.sleep(RETRY_WAIT_S)


def wait_until(when, label):
    if when is None:
        return
    first = True
    while True:
        left = (when - utcnow()).total_seconds()
        if left <= 0:
            if not first:
                say(f"  due now: {label}")
            return
        if first:
            say(f"  waiting {left / 3600:.2f} h until {when.isoformat()} "
                f"for {label}")
            first = False
        write_status(f"waiting for {label}", when,
                     f"{left / 3600:.2f} h left")
        time.sleep(min(left, 60.0))


# ------------------------------------------------------------------ usage

def usage_total():
    """The running QPU total used against the cap.

    The sum of the per job usages IBM reported, and the account's own counter
    since this stage began, whichever is LARGER. Taking the larger of the two
    means a lagging or disagreeing counter can only make the guard stricter,
    never looser."""
    per_job = sum(float(v) for v in STATE.get("per_job_usage_s", {}).values())
    acct = STATE.get("account_usage_latest_s")
    start = STATE.get("account_usage_start_s")
    if acct is not None and start is not None:
        return max(per_job, float(acct) - float(start))
    return per_job


def read_account_usage(service):
    """(consumed_s, remaining_s) from IBM. Raises if it cannot be read."""
    u = service.usage()
    consumed = u.get("usage_consumed_seconds")
    remaining = u.get("usage_remaining_seconds")
    if consumed is None:
        raise RuntimeError("IBM did not report usage_consumed_seconds")
    if remaining is None:
        limit = u.get("usage_limit_seconds")
        if limit is None:
            raise RuntimeError("IBM reported neither remaining nor limit")
        remaining = float(limit) - float(consumed)
    return float(consumed), float(remaining)


def refresh_account_usage(service):
    consumed, remaining = retry("read account usage",
                                lambda: read_account_usage(service))
    STATE["account_usage_latest_s"] = consumed
    if STATE.get("account_usage_start_s") is None:
        STATE["account_usage_start_s"] = consumed
    save_state()
    return consumed, remaining


def job_usage_seconds(job):
    """The QPU seconds IBM charged for one job."""
    m = job.metrics() or {}
    u = m.get("usage") or {}
    for key in ("quantum_seconds", "seconds", "quantum_nanoseconds"):
        if key in u and u[key] is not None:
            v = float(u[key])
            return v / 1e9 if key.endswith("nanoseconds") else v
    try:
        v = job.usage()
        if v is not None:
            return float(v)
    except Exception:
        pass
    raise RuntimeError("IBM did not report this job's usage")


def cap_allows_submission(service, label):
    """The protocol section 3 guard. Returns (ok, reason). FAILS CLOSED: any
    usage that cannot be read returns False."""
    try:
        consumed, remaining = refresh_account_usage(service)
    except StepFailed as e:
        return False, f"usage unreadable, failing closed: {e}"
    if remaining < MIN_ACCOUNT_REMAIN_S:
        return False, (f"only {remaining:.0f} s remain on the account, "
                       f"below the {MIN_ACCOUNT_REMAIN_S:.0f} s floor")
    total = usage_total()
    # the pilot is 100 shots of a 2 qubit circuit, so it is NOT a measurement
    # of what a full 3 PUB 1000 shot job costs. It is excluded from "largest
    # job measured so far" on purpose: counting it would make this guard
    # looser than the protocol says, not stricter.
    real = {k: float(v) for k, v in STATE.get("per_job_usage_s", {}).items()
            if k != "pilot"}
    est = float(STATE["pilot"]["per_job_estimate_s"])
    if real:
        largest = max(max(real.values()), est)
        basis = "largest full job measured so far, floored at the estimate"
    else:
        largest = est
        basis = "pilot based estimate, no full job yet"
    projected = total + CAP_HEADROOM * largest
    say(f"  cap check for {label}: used {total:.3f} s, {basis} "
        f"{largest:.3f} s, {total:.3f} + {CAP_HEADROOM} x {largest:.3f} "
        f"= {projected:.3f} s against the {CAP_SUBMIT_S:.0f} s guard")
    if projected > CAP_SUBMIT_S:
        return False, (f"{total:.3f} + {CAP_HEADROOM} x {largest:.3f} = "
                       f"{projected:.3f} s would pass the "
                       f"{CAP_SUBMIT_S:.0f} s guard")
    return True, f"projected {projected:.3f} s"


# ------------------------------------------------------------------ device

def pick_device(service):
    """The protocol section 2 rule. Returns the name or None."""
    for name in ALLOWED_DEVICES:
        try:
            st = service.backend(name).status()
        except Exception as e:
            say(f"  {name}: status unreadable: {type(e).__name__}: {e}")
            continue
        online = str(st.status_msg).lower() == "active" and st.operational
        say(f"  {name}: status={st.status_msg} operational={st.operational} "
            f"pending_jobs={st.pending_jobs} -> {'Online' if online else 'not Online'}")
        if online:
            return name
    return None


def device_is_online(service, name):
    try:
        st = service.backend(name).status()
        return str(st.status_msg).lower() == "active" and st.operational
    except Exception:
        return None            # unknown, not the same as offline


# ------------------------------------------------------------------- cards

def fetch_cards(service, machine):
    """Live cards from 24 Oct 2026 00:00 UTC up to now, into
    data/hardware_cards. Round 1's collector with its folders and window
    moved; data/raw and data/fresh are not touched."""
    import types
    path = ROOT / "scripts/13_download_all_snapshots.py"
    src = path.read_text()
    marker = "\ntry:\n    main()"
    assert marker in src, "the collector no longer ends with try: main()"
    src = src.split(marker, 1)[0]
    stub = types.ModuleType("dotenv")
    stub.load_dotenv = lambda *a, **k: None
    sys.modules.setdefault("dotenv", stub)
    mod = types.ModuleType("collector13_hw")
    mod.__file__ = str(path)
    exec(compile(src, str(path), "exec"), mod.__dict__)
    env = read_env()
    mod.API_KEY = env["IBM_API_KEY"]
    mod.INSTANCE = env["IBM_INSTANCE"]
    mod.RAW = HW_CARDS
    mod.START_DATE = CARD_WINDOW_START
    mod.STATE_FILE = ROOT / "logs/walkback_state_hardware.json"
    mod.USE_GZIP = True
    mod.MACHINES = [machine]
    HW_CARDS.mkdir(parents=True, exist_ok=True)
    backend = retry("backend for the card fetch",
                    lambda: service.backend(machine))
    # a fresh walk each time: start at now and step back to 24 Oct. Cards
    # already on disk are counted, not refetched or overwritten.
    state = {}
    totals = retry("card walk", lambda: mod.walk_machine(backend, machine, state))
    say(f"  cards: {totals}")
    return totals


def newest_card_utc(machine):
    d = HW_CARDS / machine
    if not d.exists():
        return None
    names = sorted(f.name.split(".json")[0] for f in d.iterdir()
                   if ".json" in f.name)
    if not names:
        return None
    return datetime.strptime(names[-1], "%Y-%m-%dT%H-%M-%SZ").replace(
        tzinfo=timezone.utc)


# ----------------------------------------------------------------- compile

def build_store(machine):
    """Rebuild data/clean_hw and data/cache_hw from all three card folders."""
    import importlib
    for mod in ("real_data", "prepare_cache"):
        sys.modules.pop(mod, None)
    builder = importlib.import_module("41_build_hw_tables")
    n = builder.build(machine)
    for mod in ("real_data", "prepare_cache", "snapshot"):
        sys.modules.pop(mod, None)
    import real_data as rd
    assert str(rd.CLEAN) == str(ROOT / "data/clean_hw"), rd.CLEAN
    return rd, n


def compile_slot(slot, machine, rd, rule, circ_mod, run_engine):
    """Build the three arm snapshots at this moment and transpile each one.

    Nothing newer than the compile time is read: the index handed to every arm
    is index_at_or_before(compile time), the same mechanism Round 2's freeze
    test (iii) checked.
    """
    from qiskit import qpy
    from qiskit.transpiler import generate_preset_pass_manager

    COMPILED.mkdir(parents=True, exist_ok=True)
    actual_compile = utcnow()
    store = rd.open_store(machine)
    base = rd.load_base_target(machine)[0]
    permanent = rule.permanent(machine)
    info = store.index_at_or_before(actual_compile)
    if info < 0:
        raise StepFailed("no calibration state at or before the compile time")
    card_utc = store.times[info]
    age_h = (actual_compile - card_utc).total_seconds() / 3600.0
    say(f"  slot {slot}: compiled at {actual_compile.isoformat()} from the "
        f"state of {card_utc.isoformat()} (state index {info} of "
        f"{len(store)}, {age_h:.2f} h old)")

    out = {}
    for circuit in CIRCUITS:
        qc = circ_mod.build(circuit)
        key = f"s{slot}_{circuit}"
        job = STATE["jobs"].setdefault(key, {})
        if job.get("job_id") or job.get("compiled"):
            say(f"    {key}: already compiled, left alone")
            continue
        arms, keys_seen, pubs = {}, {}, []
        for arm in ARMS:
            snap = rule.arm_snapshot(arm, store, info, info, HOLD_H)
            extra = rule.arm_extra_forbid(arm, store, info)
            s_target, forbid, _ = rd.strategy_target(snap, base,
                                                     permanent | extra)
            pm = generate_preset_pass_manager(
                optimization_level=OPT_LEVEL, target=s_target,
                seed_transpiler=SEED_TRANSPILE)
            isa = pm.run(qc)
            ikey = run_engine.isa_key(isa)
            layout = [int(q) for q in isa.layout.final_index_layout()]
            if ikey in keys_seen:
                # protocol 8.1: an identical transpiled circuit is submitted
                # ONCE and both arms are given that one result.
                pub = keys_seen[ikey]
            else:
                pub = len(pubs)
                keys_seen[ikey] = pub
                pubs.append(isa)
            arms[arm] = {"pub": pub, "layout": layout,
                         "n_forbidden": len(forbid),
                         "guard_extra": sorted(int(q) for q in extra)}
        with open(COMPILED / f"{key}.qpy", "wb") as fh:
            qpy.dump(pubs, fh)
        job.update({
            "slot": slot, "circuit": circuit, "machine": machine,
            "compiled": True,
            "actual_compile_utc": actual_compile.isoformat(),
            "card_utc": card_utc.isoformat(),
            "card_age_at_compile_h": round(age_h, 4),
            "info_state_index": int(info),
            "n_states_in_store": len(store),
            "arms": arms, "n_pubs": len(pubs),
            "planned_submit_utc": (actual_compile
                                   + timedelta(hours=HOLD_H)).isoformat(),
            "status": "HELD",
        })
        same = {}
        for a in ARMS:
            same.setdefault(arms[a]["pub"], []).append(a)
        groups = [v for v in same.values() if len(v) > 1]
        say(f"    {key}: {len(pubs)} distinct circuit(s) from 3 arms"
            + (f", identical: {groups}" if groups else ", all three differ"))
        out[key] = job
    save_state()
    return actual_compile


# ------------------------------------------------------------------ submit

def submit_and_collect(service, key, machine):
    """Submit one job, wait for it, read its usage, save its result."""
    from qiskit import qpy
    from qiskit_ibm_runtime import SamplerV2

    job_rec = STATE["jobs"][key]
    RESULTS.mkdir(parents=True, exist_ok=True)
    res_path = RESULTS / f"{key}.json"
    if res_path.exists() and job_rec.get("status") == "DONE":
        say(f"  {key}: already done, left alone")
        return True

    if not job_rec.get("job_id"):
        ok, reason = cap_allows_submission(service, key)
        if not ok:
            say(f"  {key}: NOT SUBMITTED. {reason}")
            job_rec["status"] = "SKIPPED_FOR_CAP"
            job_rec["skip_reason"] = reason
            event("skipped_for_cap", f"{key}: {reason}")
            save_state()
            return False
        online = device_is_online(service, machine)
        if online is False:
            job_rec["status"] = "DEVICE_OFFLINE"
            event("device_offline", f"{key}: {machine} is not Online")
            save_state()
            return False

        with open(COMPILED / f"{key}.qpy", "rb") as fh:
            pubs = qpy.load(fh)
        submit_t = utcnow()
        compile_t = datetime.fromisoformat(job_rec["actual_compile_utc"])
        d_actual = (submit_t - compile_t).total_seconds() / 3600.0

        def do_submit():
            backend = service.backend(machine)
            sampler = SamplerV2(mode=backend)
            return sampler.run(list(pubs), shots=HW_SHOTS)

        try:
            job = retry(f"submit {key}", do_submit)
        except StepFailed as e:
            job_rec["status"] = "MISSED"
            job_rec["missed_reason"] = str(e)
            event("missed", f"{key}: submit failed for 45 minutes: {e}")
            save_state()
            return False
        job_rec.update({
            "job_id": job.job_id(),
            "actual_submit_utc": submit_t.isoformat(),
            "D_actual_h": round(d_actual, 4),
            "shots_per_pub": HW_SHOTS,
            "status": "SUBMITTED",
        })
        save_state()
        say(f"  {key}: submitted, job id {job.job_id()}, {job_rec['n_pubs']} "
            f"PUB(s) x {HW_SHOTS} shots, actual hold D = {d_actual:.3f} h")
        if abs(d_actual - HOLD_H) > 0.05:
            event("late", f"{key}: actual hold {d_actual:.3f} h, "
                          f"planned {HOLD_H} h")
    else:
        say(f"  {key}: already has job id {job_rec['job_id']}, retrieving "
            "instead of resubmitting")
        job = retry(f"look up {key}",
                    lambda: service.job(job_rec["job_id"]))

    # wait for a final state, then read the usage BEFORE anything else
    def wait():
        job.wait_for_final_state(timeout=3600)
        return str(job.status())

    try:
        status = retry(f"wait for {key}", wait, minutes=180)
    except StepFailed as e:
        job_rec["status"] = "MISSED"
        job_rec["missed_reason"] = f"never reached a final state: {e}"
        event("missed", f"{key}: {job_rec['missed_reason']}")
        save_state()
        return False

    # the usage is read even when the job failed: a failed job can still cost
    # time, and the protocol forbids submitting again before it is read.
    try:
        used = retry(f"usage for {key}", lambda: job_usage_seconds(job))
    except StepFailed as e:
        job_rec["status"] = "USAGE_UNREADABLE"
        event("usage_unreadable",
              f"{key}: {e}. Nothing more will be submitted (fail closed).")
        save_state()
        return False
    STATE["per_job_usage_s"][key] = used
    job_rec["usage_s"] = used

    m = {}
    try:
        m = retry(f"metrics for {key}", lambda: job.metrics()) or {}
    except StepFailed:
        pass
    ts = (m.get("timestamps") or {})
    job_rec["created_utc"] = ts.get("created")
    job_rec["running_utc"] = ts.get("running")
    job_rec["finished_utc"] = ts.get("finished")
    try:
        c = ts.get("created")
        r = ts.get("running")
        if c and r:
            job_rec["queue_wait_s"] = (
                datetime.fromisoformat(r.replace("Z", "+00:00"))
                - datetime.fromisoformat(c.replace("Z", "+00:00"))
            ).total_seconds()
    except Exception as e:
        event("note", f"{key}: could not compute the queue wait: {e}")
    save_state()
    say(f"  {key}: {status}, usage {used:.3f} s, running total "
        f"{usage_total():.3f} s of {CAP_TOTAL_S:.0f} s")

    if "ERROR" in status.upper() or "CANCEL" in status.upper():
        job_rec["status"] = "FAILED_ON_DEVICE"
        job_rec["device_error"] = hide(str(job.error_message()))
        event("job_failed", f"{key}: {status}. Its usage was still counted. "
                            "It is NOT retried.")
        save_state()
        return False

    try:
        result = retry(f"result for {key}", lambda: job.result())
    except StepFailed as e:
        job_rec["status"] = "RESULT_PENDING"
        event("result_pending", f"{key}: {e}. Will be retried at the end.")
        save_state()
        return False

    counts = []
    for i in range(len(result)):
        data = result[i].data
        reg = next(iter(data.keys())) if hasattr(data, "keys") else "meas"
        counts.append({str(k): int(v)
                       for k, v in getattr(data, reg).get_counts().items()})
    res_path.write_text(json.dumps({
        "key": key, "job_id": job_rec["job_id"], "circuit": job_rec["circuit"],
        "slot": job_rec["slot"], "machine": machine,
        "shots_per_pub": HW_SHOTS, "usage_s": used,
        "counts_per_pub": counts,
    }, indent=2))
    job_rec["status"] = "DONE"
    save_state()
    say(f"  {key}: result saved, {len(counts)} PUB(s)")
    return True


# -------------------------------------------------------------------- main

def main():
    global STATE
    OUT.mkdir(parents=True, exist_ok=True)
    env = read_env()
    SECRETS.extend([env.get("IBM_API_KEY"), env.get("IBM_INSTANCE")])
    if not env.get("IBM_API_KEY") or not env.get("IBM_INSTANCE"):
        say("STOP: .env is missing IBM_API_KEY or IBM_INSTANCE")
        return 2
    STATE = load_state()
    STATE.setdefault("jobs", {})
    STATE.setdefault("per_job_usage_s", {})
    STATE.setdefault("events", [])

    say("=" * 70)
    say("STAGE 6 PART A: HARDWARE RUN")
    say("=" * 70)
    say(f"  protocol: protocol_hardware.md, frozen in FREEZE_HARDWARE.txt")
    say(f"  cap: {CAP_TOTAL_S:.0f} s total, no submission past "
        f"{CAP_SUBMIT_S:.0f} s projected")

    from qiskit_ibm_runtime import QiskitRuntimeService
    service = retry("open the IBM service", lambda: QiskitRuntimeService(
        channel="ibm_quantum_platform", token=env["IBM_API_KEY"],
        instance=env["IBM_INSTANCE"]))

    # --- the instance: name and plan only, never the CRN ---
    try:
        for inst in service.instances():
            say(f"  instance name: {inst.get('name')}   "
                f"plan: {inst.get('plan')}")
    except Exception as e:
        say(f"  could not list the instance: {type(e).__name__}: {e}")

    consumed, remaining = refresh_account_usage(service)
    say(f"  account usage now {consumed:.1f} s, remaining {remaining:.1f} s")

    # --- device ---
    say("\n--- device choice (never " + FORBIDDEN_DEVICE + ") ---")
    machine = STATE.get("device") or pick_device(service)
    if machine is None:
        say(f"STOP: neither {' nor '.join(ALLOWED_DEVICES)} is Online. "
            "Nothing was submitted.")
        event("stop", "no allowed device Online")
        return 3
    if machine == FORBIDDEN_DEVICE:
        say("STOP: refusing the forbidden device")
        return 3
    STATE["device"] = machine
    save_state()
    say(f"  device for this stage: {machine}")

    import importlib
    import circuits as circ_mod
    import run_engine
    rule = importlib.import_module("30_hybrid_rule")
    say(f"  frozen rule loaded: {rule.RULE_NAME}, guard M = {rule.GUARD_M}, "
        f"w at D = {HOLD_H}: " + ", ".join(
            f"{g} {rule.weight(g, HOLD_H)}"
            for g in ("readout", "sx", "cz", "times")))

    # --- pilot and projection, before anything else ---
    if not STATE.get("pilot"):
        if not run_pilot(service, machine, circ_mod):
            return 4
    else:
        say(f"\n  pilot already run: usage "
            f"{STATE['pilot']['usage_s']:.3f} s, per job estimate "
            f"{STATE['pilot']['per_job_estimate_s']:.3f} s")
    if STATE["pilot"].get("stop"):
        say(f"STOP: {STATE['pilot']['stop']}")
        return 4

    # --- t0 ---
    if not STATE.get("t0_utc"):
        STATE["t0_utc"] = utcnow().isoformat()
        save_state()
    t0 = datetime.fromisoformat(STATE["t0_utc"])
    say(f"\n  t0 = {t0.isoformat()}")
    say(f"  planned compiles: " + ", ".join(
        (t0 + timedelta(hours=COMPILE_GAP_H * i)).strftime("%H:%M")
        for i in range(N_SLOTS)) + " UTC")
    say(f"  planned submissions: " + ", ".join(
        (t0 + timedelta(hours=COMPILE_GAP_H * i + HOLD_H)).strftime("%H:%M")
        for i in range(N_SLOTS)) + " UTC")

    # --- the three compiles ---
    for slot in range(1, N_SLOTS + 1):
        keys = [f"s{slot}_{c}" for c in CIRCUITS]
        if all(STATE["jobs"].get(k, {}).get("compiled") for k in keys):
            say(f"\n--- compile slot {slot}: already done ---")
            continue
        due = t0 + timedelta(hours=COMPILE_GAP_H * (slot - 1))
        say(f"\n--- compile slot {slot}, due {due.isoformat()} ---")
        wait_until(due, f"compile slot {slot}")
        late = (utcnow() - due).total_seconds() / 60.0
        if late > 5:
            event("late_compile",
                  f"slot {slot} compiled {late:.1f} min after it was due. "
                  "The newest card available at that moment was used and the "
                  "actual compile time was recorded.")
            say(f"  NOTE: this compile is {late:.1f} min late")
        try:
            fetch_cards(service, machine)
            rd, n_states = build_store(machine)
            compile_slot(slot, machine, rd, rule, circ_mod, run_engine)
        except StepFailed as e:
            for k in keys:
                j = STATE["jobs"].setdefault(k, {"slot": slot})
                if not j.get("compiled"):
                    j["status"] = "MISSED"
                    j["missed_reason"] = str(e)
            event("missed", f"compile slot {slot} failed: {e}")
            say(f"  slot {slot} MISSED: {e}")
            save_state()
        write_status(f"compiled slot {slot}")

    # --- the submissions, strictly one at a time ---
    stop_submitting = False
    for slot in range(1, N_SLOTS + 1):
        for circuit in CIRCUITS:
            key = f"s{slot}_{circuit}"
            job_rec = STATE["jobs"].get(key)
            if not job_rec or not job_rec.get("compiled"):
                say(f"\n  {key}: never compiled, nothing to submit")
                continue
            if job_rec.get("status") == "DONE":
                continue
            if stop_submitting and not job_rec.get("job_id"):
                job_rec["status"] = "SKIPPED_FOR_CAP"
                job_rec["skip_reason"] = "an earlier job stopped submissions"
                save_state()
                continue
            due = datetime.fromisoformat(job_rec["planned_submit_utc"])
            say(f"\n--- submit {key}, due {due.isoformat()} ---")
            wait_until(due, f"submit {key}")
            ok = submit_and_collect(service, key, machine)
            if not ok and job_rec.get("status") in (
                    "SKIPPED_FOR_CAP", "USAGE_UNREADABLE"):
                stop_submitting = True
                say("  no further job will be submitted")
            write_status(f"finished {key}")

    # --- a last sweep for results that were not ready earlier ---
    pending = [k for k, j in STATE["jobs"].items()
               if j.get("job_id") and j.get("status") != "DONE"]
    if pending:
        say(f"\n--- retrying {len(pending)} result retrieval(s) ---")
        for key in pending:
            try:
                submit_and_collect(service, key, machine)
            except Exception as e:
                event("note", f"{key}: final retrieval failed: {e}")

    say("\n" + "=" * 70)
    say("HARDWARE RUN FINISHED")
    say("=" * 70)
    done = [k for k, j in STATE["jobs"].items() if j.get("status") == "DONE"]
    say(f"  {len(done)} of {N_SLOTS * len(CIRCUITS)} jobs finished")
    for k in sorted(STATE["jobs"]):
        j = STATE["jobs"][k]
        say(f"    {k:<12} {j.get('status', 'NONE'):<18} "
            f"usage {j.get('usage_s', float('nan')):.3f} s  "
            f"D {j.get('D_actual_h', float('nan'))} h  "
            f"{j.get('n_pubs', '?')} PUB(s)")
    say(f"  QPU usage total {usage_total():.3f} s against the "
        f"{CAP_TOTAL_S:.0f} s cap")
    say(f"  pilot {STATE['pilot']['usage_s']:.3f} s is included in that total")
    write_status("run finished", None,
                 f"{len(done)} jobs done, {usage_total():.3f} s used")
    return 0


def run_pilot(service, machine, circ_mod):
    """One Bell circuit at 100 shots. Then the projection fixed in the
    protocol. Returns False if a stop rule fired."""
    from qiskit import QuantumCircuit
    from qiskit.transpiler import generate_preset_pass_manager
    from qiskit_ibm_runtime import SamplerV2

    say("\n--- pilot: one 2 qubit Bell circuit, 100 shots ---")
    backend = retry("backend for the pilot", lambda: service.backend(machine))
    target = backend.target
    rep_delay = float(getattr(backend, "default_rep_delay", 0.00025) or 0.00025)

    bell = QuantumCircuit(2, name="bell")
    bell.h(0)
    bell.cx(0, 1)
    bell.measure_all()
    pm = generate_preset_pass_manager(optimization_level=OPT_LEVEL,
                                      backend=backend,
                                      seed_transpiler=SEED_TRANSPILE)
    isa_bell = pm.run(bell)
    try:
        bell_dur = float(isa_bell.estimate_duration(target, unit="s"))
    except Exception:
        bell_dur = 0.0

    _, remaining = refresh_account_usage(service)
    if remaining < MIN_ACCOUNT_REMAIN_S:
        say(f"STOP: only {remaining:.0f} s remain on the account")
        STATE["pilot"] = {"stop": f"only {remaining:.0f} s remain"}
        save_state()
        return False

    def do():
        return SamplerV2(mode=backend).run([isa_bell], shots=PILOT_SHOTS)

    try:
        job = retry("submit the pilot", do)
    except StepFailed as e:
        say(f"STOP: the pilot could not be submitted: {e}")
        STATE["pilot"] = {"stop": f"pilot could not be submitted: {e}"}
        save_state()
        return False
    say(f"  pilot job id {job.job_id()}")
    retry("wait for the pilot",
          lambda: job.wait_for_final_state(timeout=3600), minutes=180)
    used = retry("pilot usage", lambda: job_usage_seconds(job))
    STATE["per_job_usage_s"]["pilot"] = used
    refresh_account_usage(service)

    pilot_sampling = PILOT_SHOTS * (bell_dur + rep_delay)
    overhead = max(used - pilot_sampling, 0.0)

    # the per shot cost of each real circuit, from the device's own numbers
    per_circuit = {}
    for name in CIRCUITS:
        isa = pm.run(circ_mod.build(name))
        try:
            dur = float(isa.estimate_duration(target, unit="s"))
        except Exception:
            dur = 0.0
        per_circuit[name] = dur
    sampling_total = sum(
        3 * N_SLOTS * HW_SHOTS * (per_circuit[c] + rep_delay)
        for c in CIRCUITS)
    projection = N_SLOTS * len(CIRCUITS) * overhead + sampling_total

    STATE["pilot"] = {
        "job_id": job.job_id(), "shots": PILOT_SHOTS, "usage_s": used,
        "bell_isa_duration_s": bell_dur, "rep_delay_s": rep_delay,
        "predicted_sampling_s": pilot_sampling,
        "overhead_per_job_s": overhead,
        "isa_duration_s": per_circuit,
        "projected_sampling_all_jobs_s": sampling_total,
        "projected_total_12_jobs_s": projection,
        "per_job_estimate_s": overhead + sum(
            3 * HW_SHOTS * (per_circuit[c] + rep_delay) for c in CIRCUITS
        ) / len(CIRCUITS),
    }
    save_state()
    say(f"  pilot usage {used:.3f} s")
    say(f"  rep delay {rep_delay * 1e6:.0f} us, Bell ISA duration "
        f"{bell_dur * 1e6:.3f} us, so the pilot's own sampling time was "
        f"{pilot_sampling:.4f} s and the rest, {overhead:.3f} s, is per job "
        "overhead")
    say("  ISA durations at level 2: " + ", ".join(
        f"{c} {per_circuit[c] * 1e6:.3f} us" for c in CIRCUITS))
    say(f"  projection for 12 jobs = 12 x {overhead:.3f} s overhead + "
        f"{sampling_total:.3f} s sampling = {projection:.3f} s")

    if used > PILOT_MAX_S:
        say(f"STOP: the pilot used {used:.3f} s, above the "
            f"{PILOT_MAX_S:.0f} s limit. Nothing else is submitted.")
        STATE["pilot"]["stop"] = (f"pilot used {used:.3f} s, above "
                                  f"{PILOT_MAX_S:.0f} s")
        save_state()
        return False
    if projection > CAP_SUBMIT_S:
        say(f"STOP: the projection for 12 jobs is {projection:.3f} s, above "
            f"the {CAP_SUBMIT_S:.0f} s guard. Nothing else is submitted. "
            "The shots and the design are NOT changed; this is for the user "
            "to decide.")
        STATE["pilot"]["stop"] = (f"projection {projection:.3f} s above "
                                  f"{CAP_SUBMIT_S:.0f} s")
        save_state()
        return False
    say(f"  projection {projection:.3f} s is under the "
        f"{CAP_SUBMIT_S:.0f} s guard, so the run continues")
    return True


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        traceback.print_exc()
        try:
            event("crash", "the runner raised, see hw_console.txt")
            write_status("CRASHED, see hw_console.txt")
        except Exception:
            pass
        sys.exit(1)
