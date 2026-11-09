"""Story-only repost: one saved library clip (with its own sound) to the Story, not the feed.
Picks a page at random (equal chance per page) among pages not reposted in the last 7 days
(feed or Story), then a random clip."""
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
if st["count"] >= 6 and not os.environ.get("FORCE"):
    print("Six Story reposts already today")
    raise SystemExit(0)
holds = caps.get("hold_until", {})
# One weekly limit per page, shared with feed reposts (state/reposts.json "last")
REPOSTS = ROOT / "state" / "reposts.json"
rstate = json.loads(REPOSTS.read_text()) if REPOSTS.exists() else {}
rstate.setdefault("last", {})
COOLDOWN_DAYS = float(json.loads((ROOT / "accounts.json").read_text()).get("cooldown_days", 7))
_dt = __import__("datetime")


def on_cooldown(user):
    t = rstate["last"].get(user)
    return bool(t) and (today - _dt.datetime.fromisoformat(t)).total_seconds() < COOLDOWN_DAYS * 86400


ready = [c for c in caps["clips"].values()
         if not c["posted"] and not c["music"] and day >= holds.get(c["user"], "") and c.get("asset")
         and c.get("seconds", 60) >= 20 and not on_cooldown(c["user"])]
if not ready:
    print(f"No Story clip: every page with saved clips was reposted in the last {COOLDOWN_DAYS:g} days")
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
rstate["last"][page] = today.isoformat()
REPOSTS.write_text(json.dumps(rstate, indent=2))
