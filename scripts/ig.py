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


def publish(kind, url, caption, optional=False):
    """kind: IMAGE or REELS. Returns Make's response text. optional=True for reposts."""
    _charge(PUBLISH_COST, optional)
    reply = _send(PUBLISH_URL, {"kind": kind, "url": url, "caption": caption}, timeout=300).strip()
    print(f"Make replied: {reply[:200]}")
    if not reply.startswith("POSTED") or reply == "POSTED":
        raise RuntimeError(f"Instagram did not confirm the post: {reply[:200]!r}")
    return reply


def recent_media(username):
    """Newest-first list of {id, media_type, media_url, permalink} for a Business/Creator account."""
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
