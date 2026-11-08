"""Story-only repost: one saved library clip (with its own sound) to the Story, not the feed.
Picks a page at random (equal chance per page, never the page just used), then a random clip."""
import json
import os
import pathlib
import random
import sys
import tempfile
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import graph  # noqa: E402
import media_host  # noqa: E402
import sizeup  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
CAPS = ROOT / "state" / "captures.json"
caps = json.loads(CAPS.read_text())
st = caps.setdefault("story", {})
today = __import__("datetime").datetime.now(__import__("datetime").timezone.utc)
day = (today - __import__("datetime").timedelta(hours=5)).date().isoformat()
if st.get("date") != day:
    st["date"], st["count"] = day, 0
if st["count"] >= 4 and not os.environ.get("FORCE"):
    print("Four Story reposts already today")
    raise SystemExit(0)
holds = caps.get("hold_until", {})
ready = [c for c in caps["clips"].values()
         if not c["posted"] and not c["music"] and day >= holds.get(c["user"], "") and c.get("asset") and c.get("seconds", 60) >= 20]
if not ready:
    print("No clips with sound left for Stories")
    raise SystemExit(0)
pages = sorted({c["user"] for c in ready if c["user"] != st.get("last_page")}) or sorted({c["user"] for c in ready})
page = random.choice(pages)
c = random.choice([x for x in ready if x["user"] == page])
print(f"Story pick: @{page} {c['permalink']}")
work = pathlib.Path(tempfile.mkdtemp())
f = work / c["asset"]
url = f"https://github.com/stanton09/stationhq-insta/releases/download/captures/{c['asset']}"
with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "stationhq-bot"}), timeout=180) as r:
    f.write_bytes(r.read())
out = work / f"story_{c['asset']}"
sizeup.make_sizeup(f, out, work, c["user"], c["code"], c.get("caption", ""), has_audio=True, max_seconds=60)
hosted = media_host.host_file(out, work)
if os.environ.get("DRY_RUN"):
    print(f"[dry run] would post Story {hosted}")
    raise SystemExit(0)
sid = graph.publish("STORIES", hosted, "")
print(f"Story posted: {sid} (@{page})")
c["posted"] = True
c["story_only"] = True
st["count"] += 1
st["last_page"] = page
CAPS.write_text(json.dumps(caps, indent=2))
