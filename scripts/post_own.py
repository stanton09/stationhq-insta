"""Publish the next StationHQ post from content/queue, then move it to content/posted."""
import os
import pathlib
import shutil
import sys

import datetime as dt
import json

import ig

ROOT = pathlib.Path(__file__).resolve().parent.parent
QUEUE, POSTED = ROOT / "content/queue", ROOT / "content/posted"
# Public URL base for files in this repo (repo must be public for Instagram to fetch them).
RAW = os.environ.get("RAW_BASE") or (
    f"https://raw.githubusercontent.com/{os.environ['GITHUB_REPOSITORY']}/"
    f"{os.environ.get('GITHUB_REF_NAME', 'main')}")

# Scheduled runs retry hourly; only the first successful one each (Eastern) day posts.
TODAY = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=5)).date().isoformat()
DAY_FILE = ROOT / "state/own.json"
day = json.loads(DAY_FILE.read_text()) if DAY_FILE.exists() else {}
if os.environ.get("GITHUB_EVENT_NAME") == "schedule" and day.get("last") == TODAY:
    print(f"Already posted today ({TODAY}); skipping.")
    sys.exit(0)

import re
# Files named dYYYY-MM-DD_*.mp4 are dated: held until that day, then they go first (e.g. weekly Captain Brisket).
media = sorted(p for p in QUEUE.iterdir() if p.suffix.lower() in (".jpg", ".jpeg", ".mp4"))
def _date(p):
    m = re.match(r"d(\d{4}-\d{2}-\d{2})_", p.name)
    return m.group(1) if m else None
due = [p for p in media if _date(p) and _date(p) <= TODAY]
media = due + [p for p in media if not _date(p)]
if not media:
    print("Queue is empty - nothing to post.")
    sys.exit(0)

item = media[0]
cap_file = item.with_suffix(".txt")
caption = cap_file.read_text().strip() if cap_file.exists() else ""
kind = "VIDEO" if item.suffix.lower() == ".mp4" else "IMAGE"
url = f"{RAW}/content/queue/{item.name}"

if os.environ.get("DRY_RUN"):
    print(f"[dry run] would post {item.name} from {url}")
    sys.exit(0)

# Captain Brisket reels carry their own music; other own Reels get a calm Instagram track under their sound
# (metal is only for live-fire footage).
own_music = "brisket" not in item.name
# Optional custom cover: content/covers/<same name>.jpg (kept out of the queue so it isn't posted on its own).
cover = ROOT / "content/covers" / f"{item.stem}.jpg"
cover_url = f"{RAW}/content/covers/{cover.name}" if (kind == "VIDEO" and cover.exists()) else None
# Brisket episodes: the owner shares them to the Story from the app so the Story taps through to the Reel.
ig.publish("REELS" if kind == "VIDEO" else "IMAGE", url, caption,
           music="under" if (kind == "VIDEO" and own_music) else False, music_style="calm",
           cover_url=cover_url, story=own_music)
print(f"Posted {item.name}")

POSTED.mkdir(exist_ok=True)
shutil.move(str(item), POSTED / item.name)
if cap_file.exists():
    shutil.move(str(cap_file), POSTED / cap_file.name)

DAY_FILE.parent.mkdir(exist_ok=True)
DAY_FILE.write_text(json.dumps({"last": TODAY}))
