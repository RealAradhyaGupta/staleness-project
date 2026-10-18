"""Append one PROGRESS_LOG.md entry with a timestamp taken from the clock.

OURS. Written after L-030 and L-031, where I typed the time by hand three
times and got it wrong three times. The timestamp is never typed now: it is
read here and substituted into both the entry header and the Timeline index
row, which are written in the same call so they cannot disagree.

Usage:  add_log_entry.py <TAG> <title> <body file>
"""
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOG = ROOT / "PROGRESS_LOG.md"
TAGS = {"DONE", "FOUND", "RESULT", "FAULT", "DECISION", "CHANGE", "FEEDBACK",
        "REVIEW"}


def now():
    """Read the clock once, use it everywhere."""
    out = subprocess.run(["date", "+%s"], capture_output=True, text=True,
                         check=True).stdout.strip()
    utc = datetime.fromtimestamp(int(out), tz=timezone.utc)
    ist = utc.astimezone(timezone(timedelta(hours=5, minutes=30)))
    return ist.strftime("%Y-%m-%d %H:%M"), utc.strftime("%Y-%m-%d %H:%M")


def next_id(text):
    ids = [int(line[5:8]) for line in text.splitlines()
           if line.startswith("## L-")]
    return f"L-{max(ids) + 1:03d}"


def main():
    tag, title, body_file = sys.argv[1], sys.argv[2], sys.argv[3]
    assert tag in TAGS, f"bad tag {tag}, must be one of {sorted(TAGS)}"
    body = Path(body_file).read_text().rstrip()
    assert "—" not in body, "em dash found; CLAUDE.md forbids them"
    for secret in ("IBM_API_KEY=", "crn:", "apikey"):
        assert secret.lower() not in body.lower(), f"possible secret: {secret}"

    text = LOG.read_text()
    eid = next_id(text)
    ist, utc = now()
    header = f"## {eid} | {ist} IST ({utc} UTC) | {tag} | {title}"
    row = f"| {eid} | {ist} | {tag} | {title} |\n"

    lines = text.splitlines(keepends=True)
    last_row = max(i for i, l in enumerate(lines) if l.startswith("| L-"))
    lines.insert(last_row + 1, row)
    text = "".join(lines).rstrip() + f"\n\n---\n\n{header}\n\n{body}\n"
    LOG.write_text(text)
    print(f"appended {eid} at {ist} IST ({utc} UTC)")
    print(f"  {header}")


main()
