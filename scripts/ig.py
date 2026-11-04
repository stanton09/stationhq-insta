"""Instagram posting through Make.com webhooks (no Meta developer account needed).

Make scenario 1 "StationHQ publish"  (secret MAKE_PUBLISH_URL)
  Custom webhook receives JSON: {"kind": "IMAGE" | "REELS", "url": "<public media url>", "caption": "..."}
  -> Router -> Instagram for Business: Create a photo post / Create a reel post

Make scenario 2 "StationHQ lookup"   (secret MAKE_LOOKUP_URL)
  Custom webhook receives JSON: {"username": "<handle>"}
  -> Instagram for Business: List public user media (limit 8)
  -> Text aggregator, one row per post:  {{id}}<TAB>{{media_type}}<TAB>{{media_url}}<TAB>{{permalink}}
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
    return _send(PUBLISH_URL, {"kind": kind, "url": url, "caption": caption})


def recent_media(username):
    """Newest-first list of {id, media_type, media_url, permalink} for a Business/Creator account."""
    text = _send(LOOKUP_URL, {"username": username})
    posts = []
    for line in text.splitlines():
        parts = line.strip().split("\t")
        if len(parts) >= 4 and parts[0]:
            posts.append(dict(zip(("id", "media_type", "media_url", "permalink"), parts[:4])))
    return posts
