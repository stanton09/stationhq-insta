"""Repost the best recent action video from the next firehouse account in a shuffled rotation, with credit.

Each run looks at ONE account (keeps Make credit use low), takes its last ~12 posts and picks the
best unshared action video: Reels only, posted in the last 30 days, no fundraiser/birthday-type
captions, ranked by views and likes. The account order is reshuffled every full cycle for variety.
"""
import datetime as dt
import json
import os
import pathlib
import random
import re
import sys

import ig
import media_host

ROOT = pathlib.Path(__file__).resolve().parent.parent
STATE_FILE = ROOT / "state/reposts.json"
DRY = bool(os.environ.get("DRY_RUN"))
MAX_AGE_DAYS = 45
SKIP_WORDS = re.compile(
    r"fundrais|birthday|bday|pancake|breakfast|open house|ribbon|ceremony|graduat|promotion|"
    r"retire|condolence|rest in peace|\brip\b|funeral|line of duty death|lodd|in memory|memorial|"
    r"raffle|donat|sponsor|ticket|golf outing|toy drive|blood drive|vote|election|hiring|job posting|"
    r"apply now|merch|t-shirt|giveaway|congrat|welcome our|swearing|sworn in|holiday party"
    r"|training|drill|academy|recruit|class|demo|simulat|exercise|wildfire|brush fire|acres|vegetation|"
    r"prescribed|controlled burn|red flag",
    re.I)
# Only repost videos whose caption says it's a real working fire.
FIRE_WORDS = re.compile(
    r"working fire|structure fire|house fire|apartment fire|commercial fire|garage fire|building fire|"
    r"dwelling|\d+(st|nd|rd|th)?[- ]alarm|all[- ]hands|fully involved|heavy fire|fire showing|"
    r"smoke showing|flames|blaze|fire attack|knock(ed)? ?down|interior attack|2-alarm|3-alarm|"
    r"multiple alarm|fire on the|fire in a|fire at a|fire broke out|vehicle fire|car fire",
    re.I)

if os.environ.get("TEST_ACCOUNT"):
    ACCOUNTS = [a.strip().lstrip("@") for a in os.environ["TEST_ACCOUNT"].split(",") if a.strip()]
else:
    ACCOUNTS = json.loads((ROOT / "accounts.json").read_text())["accounts"]
if not ACCOUNTS:
    print("No accounts in accounts.json yet.")
    sys.exit(0)

state = json.loads(STATE_FILE.read_text()) if STATE_FILE.exists() else {}
state.setdefault("shared", [])
state.setdefault("order", [])


def candidates(media):
    now = dt.datetime.now(dt.timezone.utc)
    out = []
    for m in media:
        if m["media_type"] != "VIDEO" or not m["media_url"].startswith("http"):
            continue  # Reels only; skips videos whose file Instagram withholds (licensed music)
        cap = m.get("caption", "")
        if m["id"] in state["shared"] or SKIP_WORDS.search(cap) or not FIRE_WORDS.search(cap):
            continue
        try:
            age = now - dt.datetime.fromisoformat(m["timestamp"].replace("Z", "+00:00"))
            if age.days > MAX_AGE_DAYS:
                continue
        except ValueError:
            pass
        score = float(m.get("view_count") or 0) / 20 + float(m.get("like_count") or 0)
        out.append((score, m))
    return [m for _, m in sorted(out, key=lambda x: -x[0])]


def caption_for(username, permalink):
    return (f"🎥 @{username}\n\n"
            f"Great work from our brothers and sisters at @{username}. Give them a follow!\n\n"
            f"Original post: {permalink}\n\n"
            "Tag us to be featured. #fireservice #firefighter #firehouse #firedepartment #fireground #stationhq")


# Check mode: test several handles at once without posting.
if DRY and len(ACCOUNTS) > 1 and os.environ.get("TEST_ACCOUNT"):
    for user in ACCOUNTS:
        try:
            media = ig.recent_media(user)
            vids = candidates(media)
            print(f"CHECK @{user}: OK {len(media)} posts, {len(vids)} usable action videos | " + " ".join(f"{m['media_type'][:5]}:{m['timestamp'][:10]}:{'url' if m['media_url'].startswith('http') else 'nourl'}" for m in media[:6]))
        except RuntimeError as e:
            print(f"CHECK @{user}: FAIL {str(e)[:120]}")
    sys.exit(0)

# Keep a shuffled rotation; refill and reshuffle when it runs out or accounts change.
order = [a for a in state["order"] if a in ACCOUNTS]
if not order:
    order = ACCOUNTS[:]
    random.shuffle(order)

posted = False
for _ in range(min(3, len(ACCOUNTS))):  # try at most 3 accounts per run
    if not order:
        order = ACCOUNTS[:]
        random.shuffle(order)
    user = order.pop(0)
    try:
        vids = candidates(ig.recent_media(user))
    except RuntimeError as e:
        print(f"Skipping @{user}: {e}")
        continue
    if not vids:
        print(f"@{user}: no fresh action videos, trying the next account")
        continue
    m = vids[0]
    if DRY:
        print(f"[dry run] would repost {m['permalink']} from @{user} "
              f"(views {m.get('view_count') or '?'}, likes {m.get('like_count') or '?'})")
    else:
        hosted_url = media_host.prepare_video(m["media_url"], m["id"])
        ig.publish("REELS", hosted_url, caption_for(user, m["permalink"]))
        print(f"Reposted {m['permalink']} from @{user}")
        state["shared"] = (state["shared"] + [m["id"]])[-1000:]
    posted = True
    break

if not posted:
    print("Nothing new to repost right now.")

if not DRY:
    state["order"] = order
    STATE_FILE.parent.mkdir(exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))
