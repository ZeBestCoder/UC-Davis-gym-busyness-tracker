"""Fetch UC Davis Rec facility occupancy once and append it to data/occupancy.csv.

Runs hourly from GitHub Actions (.github/workflows/collect.yml). Standard library only.
"""

import csv
import datetime as dt
import html
import os
import re
import sys
import urllib.request
from pathlib import Path
from zoneinfo import ZoneInfo

URL = "https://rec.ucdavis.edu/facilityoccupancy"
CSV_PATH = Path(__file__).parent / "data" / "occupancy.csv"
TZ = ZoneInfo("America/Los_Angeles")
FIELDS = [
    "timestamp_utc", "timestamp_local", "weekday", "hour",
    "facility_id", "facility", "current", "capacity", "pct_full",
]

repo = os.environ.get("GITHUB_REPOSITORY", "local")
# Open hours by weekday (Mon=0) as (first hour, last hour) in Davis local time.
# Mon-Fri 5am-midnight, Sat-Sun 8am-11pm.
OPEN_HOURS = {0: (5, 23), 1: (5, 23), 2: (5, 23), 3: (5, 23), 4: (5, 23), 5: (8, 22), 6: (8, 22)}

USER_AGENT = (
    "ucd-gym-occupancy-study/1.0 (student research; one request per hour; "
    f"+https://github.com/{repo})"
)


def warn(msg):
    # Shows up as a yellow annotation in the Actions run summary.
    print(f"::warning::{msg}")


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def parse(page):
    """Return [(facility_id, name, current, capacity), ...] from the page HTML."""
    rows = []
    # Each facility card starts with data-facilityid="<guid>"; split on it.
    parts = re.split(r'data-facilityid="([0-9a-fA-F-]{36})"', page)
    for fid, block in zip(parts[1::2], parts[2::2]):
        name = re.search(r"<h2>\s*<strong>(.*?)</strong>\s*</h2>", block, re.S)
        current = re.search(r'data-occupancy="(\d+)"', block)
        capacity = re.search(r"Max Occupancy:\s*<strong>\s*(\d+)", block)
        if not (name and current and capacity):
            warn(f"could not parse facility card {fid}")
            continue
        rows.append((fid, html.unescape(name.group(1)).strip(),
                     int(current.group(1)), int(capacity.group(1))))
    return rows


def main():
    now_utc = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
    now_local = now_utc.astimezone(TZ)

    until = os.environ.get("COLLECT_UNTIL")  # YYYY-MM-DD, inclusive
    if until and now_local.date() > dt.date.fromisoformat(until):
        print(f"Collection window ended on {until}; not fetching.")
        return 0

    first, last = OPEN_HOURS[now_local.weekday()]
    forced = os.environ.get("FORCE", "").lower() == "true"  # manual runs always fetch
    if not (first <= now_local.hour <= last) and not forced:
        print(f"Gym closed at {now_local:%a %H:%M}; not fetching.")
        return 0

    try:
        page = fetch(URL)
    except Exception as e:  # network error, 5xx, waiting room, etc. -> skip this hour
        warn(f"fetch failed: {e}")
        return 0

    rows = parse(page)
    if not rows:
        # e.g. a Queue-Fair waiting-room page instead of the real one. Record nothing
        # rather than zeros, so the gap shows up as missing data.
        warn("no facility data found on page; skipping this hour")
        return 0

    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    new_file = not CSV_PATH.exists()
    with CSV_PATH.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new_file:
            w.writerow(FIELDS)
        for fid, name, current, capacity in rows:
            pct = round(100 * current / capacity, 1) if capacity else ""
            w.writerow([
                now_utc.isoformat().replace("+00:00", "Z"),
                now_local.isoformat(),
                now_local.strftime("%a"),
                now_local.hour,
                fid, name, current, capacity, pct,
            ])
            print(f"{name}: {current}/{capacity} ({pct}%)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
