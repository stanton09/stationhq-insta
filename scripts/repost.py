"""Repost the newest not-yet-shared post from the next firehouse account in rotation, with credit."""
import json
import os
import pathlib
import sys

import ig

ROOT = pathlib.Path(__file__).resolve().parent.parent
ACCOUNTS = json.loads((ROOT / "accounts.json").read_text())["accounts"]
STATE_FILE = ROOT / "state/reposts.json"
state = json.loads(STATE_FILE.read_text()) if STATE_FILE.exists() else {"next": 0, "shared": []}

if not ACCOUNTS:
    print("No accounts in accounts.json yet.")
    sys.exit(0)

MAX_CAPTION = 2200


def build_caption(username, original):
    credit = f"📸 @{username}\n\n"
    tail = "\n\nShared with credit. Tag us to be featured. #fireservice #firefighter #firehouse #stationhq"
    body = (original or "").strip()
    room = MAX_CAPTION - len(credit) - len(tail)
    if len(body) > room:
        body = body[: room - 1] + "…"
    return credit + body + tail


def items_for(m):
    if m["media_type"] == "CAROUSEL_ALBUM":
        kids = m.get("children", {}).get("data", [])
        return [(k["media_type"], k["media_url"]) for k in kids if k.get("media_url")]
    if m.get("media_url"):
        return [(m["media_type"], m["media_url"])]
    return []  # e.g. video with licensed audio: API withholds the file


posted = False
for attempt in range(len(ACCOUNTS)):
    idx = (state["next"] + attempt) % len(ACCOUNTS)
    user = ACCOUNTS[idx]
    try:
        media = ig.recent_media(user)
    except RuntimeError as e:
        print(f"Skipping @{user}: {e}")
        continue
    for m in media:  # newest first
        if m["id"] in state["shared"]:
            continue
        items = items_for(m)
        if not items:
            continue
        if os.environ.get("DRY_RUN"):
            print(f"[dry run] would repost {m['permalink']} from @{user}")
        else:
            new_id = ig.publish(items, build_caption(user, m.get("caption")))
            print(f"Reposted {m['permalink']} from @{user} -> {new_id}")
            state["shared"] = (state["shared"] + [m["id"]])[-500:]
        posted = True
        break
    if posted:
        state["next"] = (idx + 1) % len(ACCOUNTS)
        break

if not posted:
    print("Nothing new to repost right now.")

if not os.environ.get("DRY_RUN"):
    STATE_FILE.parent.mkdir(exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))
