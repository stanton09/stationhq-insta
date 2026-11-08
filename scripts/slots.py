"""Print how many collab/DVIDS/safety feed posts went out today (ET), so a slot only posts when it's behind.
Daily plan: 12:07 PM DVIDS live burn (repost if none found), 4:07 PM collab repost,
6:07 PM fire-safety post if due (Mon/Wed/Fri), otherwise another collab repost."""
import datetime as dt
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
day = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=5)).date().isoformat()


def load(name):
    p = ROOT / "state" / name
    return json.loads(p.read_text()) if p.exists() else {}


n = (load("dvids.json").get("last") == day) + (load("safety.json").get("last") == day)
t = load("reposts.json").get("today", {})
n += t.get("count", 0) if t.get("date") == day else 0
print(n)
