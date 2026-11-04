"""Repost the newest not-yet-shared post from the next firehouse account in rotation, with credit."""
import json
import os
import pathlib
import sys

import ig

ROOT = pathlib.Path(__file__).resolve().parent.parent
ACCOUNTS = ([os.environ["TEST_ACCOUNT"]] if os.environ.get("TEST_ACCOUNT")
            else json.loads((ROOT / "accounts.json").read_text())["accounts"])
STATE_FILE = ROOT / "state/reposts.json"
state = json.loads(STATE_FILE.read_text()) if STATE_FILE.exists() else {"next": 0, "shared": []}
DRY = bool(os.environ.get("DRY_RUN"))

if not ACCOUNTS:
    print("No accounts in accounts.json yet.")
    sys.exit(0)


def caption_for(username, permalink):
    return (f"📸 @{username}\n\n"
            f"Great work from our brothers and sisters at @{username}. Give them a follow!\n\n"
            f"Original post: {permalink}\n\n"
            "Tag us to be featured. #fireservice #firefighter #firehouse #firedepartment #stationhq")


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
        if m["id"] in state["shared"] or not m["media_url"].startswith("http"):
            continue  # already shared, or video withheld (licensed audio)
        # Carousels: Instagram returns the first slide's URL, so we share that slide.
        kind = "REELS" if m["media_type"] == "VIDEO" else "IMAGE"
        if DRY:
            print(f"[dry run] would repost {m['permalink']} from @{user} as {kind}")
        else:
            ig.publish(kind, m["media_url"], caption_for(user, m["permalink"]))
            print(f"Reposted {m['permalink']} from @{user}")
            state["shared"] = (state["shared"] + [m["id"]])[-500:]
        posted = True
        break
    if posted:
        state["next"] = (idx + 1) % len(ACCOUNTS)
        break

if not posted:
    print("Nothing new to repost right now.")

if not DRY:
    STATE_FILE.parent.mkdir(exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))
