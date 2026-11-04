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
import json
import os
import urllib.request

PUBLISH_URL = os.environ.get("MAKE_PUBLISH_URL", "")
LOOKUP_URL = os.environ.get("MAKE_LOOKUP_URL", "")


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


def publish(kind, url, caption):
    """kind: IMAGE or REELS. Returns Make's response text."""
    reply = _send(PUBLISH_URL, {"kind": kind, "url": url, "caption": caption}, timeout=300).strip()
    print(f"Make replied: {reply[:200]}")
    if not reply.startswith("POSTED") or reply == "POSTED":
        raise RuntimeError(f"Instagram did not confirm the post: {reply[:200]!r}")
    return reply


def recent_media(username):
    """Newest-first list of {id, media_type, media_url, permalink} for a Business/Creator account."""
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
