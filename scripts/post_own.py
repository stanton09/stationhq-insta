"""Publish the next StationHQ post from content/queue, then move it to content/posted."""
import os
import pathlib
import shutil
import sys

import ig

ROOT = pathlib.Path(__file__).resolve().parent.parent
QUEUE, POSTED = ROOT / "content/queue", ROOT / "content/posted"
# Public URL base for files in this repo (repo must be public for Instagram to fetch them).
RAW = os.environ.get("RAW_BASE") or (
    f"https://raw.githubusercontent.com/{os.environ['GITHUB_REPOSITORY']}/"
    f"{os.environ.get('GITHUB_REF_NAME', 'main')}")

media = sorted(p for p in QUEUE.iterdir() if p.suffix.lower() in (".jpg", ".jpeg", ".mp4"))
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

ig.publish("REELS" if kind == "VIDEO" else "IMAGE", url, caption)
print(f"Posted {item.name}")

POSTED.mkdir(exist_ok=True)
shutil.move(str(item), POSTED / item.name)
if cap_file.exists():
    shutil.move(str(cap_file), POSTED / cap_file.name)
