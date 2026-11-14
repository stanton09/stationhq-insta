"""Post today's dated own Story from content/stories (dYYYY-MM-DD_*.jpg), then move it to content/posted."""
import datetime as dt
import os
import pathlib
import re
import shutil
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import graph  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
Q, POSTED = ROOT / "content/stories", ROOT / "content/posted"
RAW = f"https://raw.githubusercontent.com/{os.environ['GITHUB_REPOSITORY']}/{os.environ.get('GITHUB_REF_NAME', 'main')}"
TODAY = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=5)).date().isoformat()

if not Q.exists():
    print("No story queue"); sys.exit(0)
due = sorted(p for p in Q.iterdir() if (m := re.match(r"d(\d{4}-\d{2}-\d{2})_", p.name)) and m.group(1) <= TODAY)
if not due:
    print(f"No own Story due for {TODAY}"); sys.exit(0)
item = due[0]
url = f"{RAW}/content/stories/{item.name}"
if os.environ.get("DRY_RUN"):
    print(f"[dry run] would post Story {item.name}"); sys.exit(0)
sid = graph.publish("STORIES", url, "")
print(f"Posted Story {item.name}: {sid}")
POSTED.mkdir(exist_ok=True)
shutil.move(str(item), POSTED / item.name)
# older missed ones are skipped (Stories are time-sensitive)
for p in due[1:]:
    shutil.move(str(p), POSTED / ("skipped_" + p.name))
