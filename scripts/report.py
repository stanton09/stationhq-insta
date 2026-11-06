"""Weekly growth report: followers this week vs last, best posts by views, collab pages ranked.
Prints a short plain-text summary (the scheduled task forwards it to the user's phone)."""
import datetime as dt
import json
import pathlib
import re

import graph

ROOT = pathlib.Path(__file__).resolve().parent.parent
STATE = ROOT / "state" / "report.json"
now = dt.datetime.now(dt.timezone.utc)
since = now - dt.timedelta(days=7)

acct = graph.call("GET", graph.ig_id(), fields="followers_count,media_count")
prev = json.loads(STATE.read_text()) if STATE.exists() else {}
followers = acct["followers_count"]
delta = followers - prev["followers"] if "followers" in prev else None

posts, after = [], None
while True:
    params = {"fields": "id,caption,media_type,media_product_type,timestamp,permalink,like_count,comments_count",
              "limit": 50}
    if after:
        params["after"] = after
    r = graph.call("GET", f"{graph.ig_id()}/media", **params)
    batch = r.get("data", [])
    posts += [p for p in batch if dt.datetime.fromisoformat(p["timestamp"].replace("+0000", "+00:00")) >= since]
    after = r.get("paging", {}).get("cursors", {}).get("after")
    if not batch or dt.datetime.fromisoformat(batch[-1]["timestamp"].replace("+0000", "+00:00")) < since or not after:
        break


def insights(p):
    out = {}
    for m in ("views", "reach", "shares", "saved", "total_interactions", "follows"):
        try:
            d = graph.call("GET", f"{p['id']}/insights", metric=m).get("data", [])
            if d:
                out[m] = d[0].get("values", [{}])[0].get("value", d[0].get("total_value", {}).get("value", 0))
        except RuntimeError:
            pass
    return out


def kind(p):
    c = p.get("caption") or ""
    if "via DVIDS" in c and "Photo:" in c:
        return "safety"
    if "DVIDS" in c:
        return "military video"
    if "NIST" in c:
        return "NIST"
    m = re.search(r"🎥 @([\w.]+)", c) or re.search(r"Video by @([\w.]+)", c) or re.search(r"Photo by @([\w.]+)", c)
    if m:
        return f"repost @{m.group(1)}"
    return "StationHQ post"


rows = []
for p in posts:
    i = insights(p)
    rows.append({"kind": kind(p), "views": i.get("views", 0) or 0, "reach": i.get("reach", 0) or 0,
                 "shares": i.get("shares", 0) or 0, "follows": i.get("follows", 0) or 0,
                 "likes": p.get("like_count", 0), "comments": p.get("comments_count", 0),
                 "link": p["permalink"], "first": (p.get("caption") or "").split("\n")[0][:60]})
rows.sort(key=lambda r: -r["views"])

lines = [f"📈 StationHQ weekly report ({since:%b %d} – {now:%b %d})", ""]
lines.append(f"Followers: {followers:,}" + (f" ({'+' if delta >= 0 else ''}{delta} this week)" if delta is not None else " (first report, change shows next week)"))
lines.append(f"Posts this week: {len(rows)} · total views {sum(r['views'] for r in rows):,} · shares {sum(r['shares'] for r in rows):,}")
lines.append("")
lines.append("Top posts by views:")
for r in rows[:5]:
    lines.append(f"• {r['views']:,} views, {r['likes']} likes, {r['shares']} shares, {r['follows']} follows: {r['kind']}, \"{r['first']}\"")
by = {}
for r in rows:
    k = r["kind"].split(" @")[0] if not r["kind"].startswith("repost") else "reposts"
    by.setdefault(k, []).append(r["views"])
lines.append("")
lines.append("Average views by type:")
for k, v in sorted(by.items(), key=lambda kv: -sum(kv[1]) / len(kv[1])):
    lines.append(f"• {k}: {sum(v) // len(v):,} ({len(v)} posts)")
pages = {}
for r in rows:
    if r["kind"].startswith("repost @"):
        pages.setdefault(r["kind"][7:], []).append(r["views"])
if pages:
    lines.append("")
    lines.append("Best collab pages:")
    for u, v in sorted(pages.items(), key=lambda kv: -sum(kv[1]) / len(kv[1]))[:5]:
        lines.append(f"• {u}: {sum(v) // len(v):,} avg views ({len(v)} posts)")
caps_file = ROOT / "state" / "captures.json"
if caps_file.exists():
    clips = json.loads(caps_file.read_text())["clips"].values()
    sound = sum(1 for c in clips if not c["posted"] and not c["music"])
    muted = sum(1 for c in clips if not c["posted"] and c["music"])
    days = (sound + muted) // 3
    lines.append("")
    lines.append(f"Clip library: {sound + muted} left ({sound} with sound, {muted} get music), about {days} days"
                 + (". ⚠️ Running low: say \"grab videos\" on your laptop to refill." if days < 14 else "."))
import datetime as _dt
_today = _dt.date.today().isoformat()
warn = []
own = len(list((ROOT / "content" / "queue").glob("*.jpg"))) + len(list((ROOT / "content" / "queue").glob("*.mp4")))
if own < 7:
    warn.append(f"⚠️ Only {own} StationHQ posts left in the queue. Send me app screenshots for more.")
_n = json.loads((ROOT / "content" / "nist_videos.json").read_text())["videos"]
_np = set(json.loads((ROOT / "state" / "nist.json").read_text()).get("posted", [])) if (ROOT / "state" / "nist.json").exists() else set()
_nl = sum(1 for v in _n if v["id"] not in _np)
if _nl < 4:
    warn.append(f"⚠️ {_nl} NIST videos left. The monthly refill adds more.")
_sl = sum(1 for t in json.loads((ROOT / "content" / "safety" / "topics.json").read_text()) if t["day"] >= _today)
if _sl < 4:
    warn.append(f"⚠️ {_sl} fire-safety posts left. The monthly refill adds more.")
if warn:
    lines += [""] + warn
print("REPORT-START")
print("\n".join(lines))
print("REPORT-END")
STATE.write_text(json.dumps({"followers": followers, "date": now.date().isoformat()}, indent=2))
