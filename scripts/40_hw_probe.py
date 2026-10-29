"""Stage 6, Part A pre-flight probe. Read only. No job is submitted here.

Prints the instance NAME and the plan, the account usage so far, and the
status of the two allowed devices. The API key and the CRN live in .env and
are never printed: every line of output is passed through hide() first.
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ALLOWED = ["ibm_kingston", "ibm_fez"]      # in the order the task prefers
NEVER = "ibm_marrakesh"                    # paused, never used


def read_env():
    env = {}
    for line in (ROOT / ".env").read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def hide(text, secrets):
    safe = str(text)
    for s in secrets:
        if s and len(s) > 6:
            safe = safe.replace(s, "<hidden>")
            # a CRN also appears url-quoted in some error strings
            safe = safe.replace(s.replace(":", "%3A"), "<hidden>")
    return safe


def main():
    env = read_env()
    key, crn = env.get("IBM_API_KEY"), env.get("IBM_INSTANCE")
    secrets = [key, crn]
    if not key or not crn:
        print("STOP: .env is missing IBM_API_KEY or IBM_INSTANCE")
        return 2

    def say(*parts):
        print(hide(" ".join(str(p) for p in parts), secrets))

    from qiskit_ibm_runtime import QiskitRuntimeService

    service = QiskitRuntimeService(channel="ibm_quantum_platform",
                                   token=key, instance=crn)

    # --- the instance: name and plan only ---
    say("instance and plan")
    try:
        for inst in service.instances():
            name = inst.get("name") or inst.get("instance") or "?"
            plan = inst.get("plan") or inst.get("tier") or "?"
            say("   name:", name, "  plan:", plan)
    except Exception as e:
        say("   could not list instances:", type(e).__name__, e)

    # --- usage so far on the account ---
    say("")
    say("usage so far (this is the number the cap is checked against)")
    try:
        u = service.usage()
        import json
        say("   raw:", json.dumps(u)[:1200])
    except Exception as e:
        say("   could not read usage:", type(e).__name__, e)

    # --- device status ---
    say("")
    say("device status")
    chosen = None
    for name in ALLOWED:
        try:
            b = service.backend(name)
            st = b.status()
            say(f"   {name:15s} status={st.status_msg:12s} "
                f"operational={st.operational} pending_jobs={st.pending_jobs} "
                f"qubits={b.num_qubits}")
            online = str(st.status_msg).lower() == "active" and st.operational
            if online and chosen is None:
                chosen = name
        except Exception as e:
            say(f"   {name:15s} could not read status:", type(e).__name__, e)
    say(f"   {NEVER:15s} NOT QUERIED, NOT USED (paused, forbidden by the task)")

    say("")
    if chosen is None:
        say("STOP: neither ibm_kingston nor ibm_fez is Online. No job submitted.")
        return 3
    say("chosen device:", chosen)
    return 0


if __name__ == "__main__":
    sys.exit(main())
