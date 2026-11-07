"""Instagram posting through Make.com webhooks (no Meta developer account needed).

Make scenario 1 "StationHQ publish"  (secret MAKE_PUBLISH_URL)
  Custom webhook receives JSON: {"kind": "IMAGE" | "REELS", "url": "<public media url>", "caption": "..."}
  -> Router -> Instagram for Business: Create a photo post / Create a reel post

Make scenario 2 "StationHQ lookup"   (secret MAKE_LOOKUP_URL)
  Custom webhook receives JSON: {"username": "<handle>"}
  -> Instagram for Business: List public user media (limit 8)
  -> Text aggregator, one row per post:  {{id}} {{media_type}} {{media_url}} {{permalink}} {{like_count}} {{view_count}} {{timestamp}} {{caption}} (tab-separated, caption flattened)
  -> Webhook response with the aggregated text as the body
"""
import datetime as dt
import json
import os
import pathlib
import urllib.request

PUBLISH_URL = os.environ.get("MAKE_PUBLISH_URL", "")
LOOKUP_URL = os.environ.get("MAKE_LOOKUP_URL", "")

# ---- Make free-plan credit guard -------------------------------------------------------------
# Make's free plan has 1,000 credits a month (resets on the 4th). A lookup costs ~4 credits and a
# post ~3. We keep an estimate in state/make_budget.json and always hold back enough credits for
# the StationHQ, DVIDS and NIST posts until the next reset. Reposts and lookups ("optional" work)
# only run with what's left over, and lookups are capped per day so a quiet page can't drain it.
ROOT = pathlib.Path(__file__).resolve().parent.parent
BUDGET_FILE = ROOT / "state" / "make_budget.json"
MONTHLY_CREDITS = 1000
RESET_DAY = 4
LOOKUP_COST = 4
PUBLISH_COST = 3
OWN_POSTS_PER_DAY_COST = 6   # StationHQ post + DVIDS reel + weekly NIST, rounded up
SAFETY = 15
LOOKUPS_PER_DAY = 3  # 2 reposts a day, plus one spare if a page has nothing new


class OverBudget(RuntimeError):
    pass


def _cycle_start(now):
    d = now.date()
    start = d.replace(day=RESET_DAY) if d.day >= RESET_DAY else \
        (d.replace(day=1) - dt.timedelta(days=1)).replace(day=RESET_DAY)
    return start


def _next_reset(start):
    nxt = (start.replace(day=1) + dt.timedelta(days=32)).replace(day=RESET_DAY)
    return nxt


def _budget():
    now = dt.datetime.now(dt.timezone.utc)
    start = _cycle_start(now).isoformat()
    b = json.loads(BUDGET_FILE.read_text()) if BUDGET_FILE.exists() else {}
    if b.get("cycle") != start:
        b = {"cycle": start, "used": 0, "lookups_by_day": {}}
    return b, now


def _save(b):
    if os.environ.get("DRY_RUN"):
        return
    BUDGET_FILE.parent.mkdir(exist_ok=True)
    BUDGET_FILE.write_text(json.dumps(b, indent=2) + "\n")


def _spare(b, now):
    days_left = (_next_reset(dt.date.fromisoformat(b["cycle"])) - now.date()).days
    reserve = max(days_left, 0) * OWN_POSTS_PER_DAY_COST + SAFETY
    return MONTHLY_CREDITS - b["used"] - reserve


def _charge(cost, optional, lookup=False):
    b, now = _budget()
    if optional:
        spare = _spare(b, now)
        if spare < cost:
            raise OverBudget(f"saving Make credits for your own posts ({b['used']} of {MONTHLY_CREDITS} used, "
                             f"next reset {_next_reset(dt.date.fromisoformat(b['cycle']))})")
        if lookup:
            day = (now - dt.timedelta(hours=5)).date().isoformat()
            if b["lookups_by_day"].get(day, 0) >= LOOKUPS_PER_DAY:
                raise OverBudget(f"daily lookup limit ({LOOKUPS_PER_DAY}) reached")
            b["lookups_by_day"] = {day: b["lookups_by_day"].get(day, 0) + 1}
    b["used"] += cost
    _save(b)


def _send(url, payload, timeout=120):
    if not url:
        raise RuntimeError("Make webhook URL secret is not set")
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read().decode()
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Make webhook failed: {e.code} {e.read().decode()}") from None


MUSIC_SEARCHES = ["rock", "metal", "hard rock", "intense", "epic", "action"]


def _pick_track():
    """A royalty-free Instagram Sound Collection track that fits fire footage (at least 30 s long)."""
    import random
    import graph
    for q in random.sample(MUSIC_SEARCHES, len(MUSIC_SEARCHES)):
        tracks = [t for t in graph.search_audio(q, limit=20) if int(t.get("duration_in_ms") or 0) >= 30000]
        if tracks:
            t = random.choice(tracks)
            print(f"Music: '{t.get('title')}' by {t.get('display_artist')} (search '{q}')")
            return t["audio_id"]
    raise RuntimeError("No Instagram music found")


def publish(kind, url, caption, optional=False, collaborators=None, music=False, first_comment=None):
    """kind: IMAGE or REELS. optional=True for reposts.
    With the direct API (state/ig_token.enc + META_APP_SECRET): collaborators=[usernames] sends collab
    invites, music=True adds an Instagram Sound Collection track (for clips whose own audio was removed).
    Otherwise posts through Make (no collabs or music)."""
    import graph
    if graph.available():
        audio = None
        if music and kind == "REELS":
            if music == "under":  # clip keeps its sirens/air horns; track sits underneath
                audio = {"audio_id": _pick_track(), "audio_volume": 35, "video_volume": 100}
            else:  # clip's own song was stripped: track carries the sound
                audio = {"audio_id": _pick_track(), "audio_volume": 100, "video_volume": 0}
        try:
            mid = graph.publish(kind, url, caption, collaborators=collaborators, audio=audio)
        except RuntimeError as e:
            if not collaborators:
                raise
            print(f"Collab invite failed ({e}); posting without it")
            mid = graph.publish(kind, url, caption, audio=audio)
        print(f"Instagram replied: POSTED {mid}" + (f" (collab invite: {', '.join(collaborators)})" if collaborators else ""))
        if first_comment:  # a question from us as the first comment gets the thread started
            try:
                graph.call("POST", f"{mid}/comments", message=first_comment)
                print(f"First comment: {first_comment}")
            except Exception as e:
                print(f"First comment skipped: {str(e)[:150]}")
        try:  # also share it to the Story (more reach); never fail the post over this
            sid = graph.publish("STORIES", url, "")
            print(f"Also posted to Story: {sid}")
        except Exception as e:
            print(f"Story share skipped: {str(e)[:150]}")
        return f"POSTED {mid}"
    if music:
        raise RuntimeError("Music needs the direct API (state/ig_token.enc); not posting a silent clip")
    _charge(PUBLISH_COST, optional)
    reply = _send(PUBLISH_URL, {"kind": kind, "url": url, "caption": caption}, timeout=300).strip()
    print(f"Make replied: {reply[:200]}")
    if not reply.startswith("POSTED") or reply == "POSTED":
        raise RuntimeError(f"Instagram did not confirm the post: {reply[:200]!r}")
    return reply


def _recent_media_direct(username):
    """Same as recent_media, through the free direct API (Business Discovery)."""
    import graph
    f = ("business_discovery.username(%s){media.limit(12){id,media_type,media_url,permalink,"
         "like_count,comments_count,timestamp,caption}}" % username)
    try:
        r = graph.call("GET", graph.ig_id(), fields=f)
    except RuntimeError as e:
        raise RuntimeError(f"not available (wrong handle, private, or not a Business/Creator account): {e}")
    posts = []
    for m in (r.get("business_discovery") or {}).get("media", {}).get("data", []):
        posts.append({"id": m.get("id", ""), "media_type": m.get("media_type", ""),
                      "media_url": m.get("media_url", ""), "permalink": m.get("permalink", ""),
                      "like_count": str(m.get("like_count", "")), "view_count": "",
                      "timestamp": m.get("timestamp", ""), "caption": m.get("caption", "")})
    return posts


def recent_media(username):
    """Newest-first list of {id, media_type, media_url, permalink} for a Business/Creator account."""
    import graph
    if graph.available():
        try:
            return _recent_media_direct(username)
        except RuntimeError as e:
            if "(#10)" not in str(e):  # (#10) = token lacks instagram_manage_insights; use Make for now
                raise
    _charge(LOOKUP_COST, optional=True, lookup=True)
    text = _send(LOOKUP_URL, {"username": username})
    if text.strip() == "NOT_AVAILABLE":
        raise RuntimeError("not available (wrong handle, private, or not a Business/Creator account)")
    posts = []
    fields = ("id", "media_type", "media_url", "permalink", "like_count", "view_count", "timestamp", "caption")
    for line in text.splitlines():
        parts = line.rstrip("\r").split("\t")
        if len(parts) >= 4 and parts[0].strip():
            posts.append(dict(zip(fields, [p.strip() for p in parts] + [""] * (len(fields) - len(parts)))))
    if not posts:
        print(f"Lookup for @{username} returned no posts. Make replied: {text[:300]!r}")
    return posts


FIRST_COMMENTS = {
    "repost": [
        "Rate this one 1-10 👇",
        "Tag your crew 👇",
        "Where's everyone watching from? Drop your department 👇",
        "What's the wildest job you've caught?",
        "Night jobs or day jobs?",
        "How long you been on the job?",
        "Send this to someone on your shift",
        "What's your rig? Engine, truck or rescue 👇",
        "Who's caught one like this?",
    ],
    "dvids": [
        "What's your go-to on a car fire: attack from the corner or straight on?",
        "How often does your department get live burn training?",
        "What's the best live fire training you've ever done?",
    ],
    "safety": [
        "What's the one you see most on calls this time of year?",
        "What would you add to this?",
        "Tag someone who needs this reminder.",
    ],
    "nist": [
        "Did that flashover time surprise you?",
        "What's your takeaway from this one?",
    ],
}


def first_comment(kind, seed):
    import hashlib
    opts = FIRST_COMMENTS[kind]
    return opts[int(hashlib.md5(str(seed).encode()).hexdigest(), 16) % len(opts)]
