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
from filters import FIRE_WORDS, SKIP_WORDS  # noqa: E402

if os.environ.get("TEST_ACCOUNT"):
    ACCOUNTS = [a.strip().lstrip("@") for a in os.environ["TEST_ACCOUNT"].split(",") if a.strip()]
else:
    ACCOUNTS = json.loads((ROOT / "accounts.json").read_text())["accounts"]
if not ACCOUNTS:
    print("No accounts in accounts.json yet.")
    sys.exit(0)

_cfg = json.loads((ROOT / "accounts.json").read_text())
TRUSTED = set(_cfg.get("trusted_all_videos", []))
COOLDOWN_DAYS = float(_cfg.get("cooldown_days", 7))
state = json.loads(STATE_FILE.read_text()) if STATE_FILE.exists() else {}
state.setdefault("shared", [])
state.setdefault("order", [])
state.setdefault("last", {})  # handle -> ISO time of last repost


def on_cooldown(user):
    t = state["last"].get(user)
    if not t:
        return False
    age = dt.datetime.now(dt.timezone.utc) - dt.datetime.fromisoformat(t)
    return age.total_seconds() < COOLDOWN_DAYS * 86400


def candidates(media, user=None):
    now = dt.datetime.now(dt.timezone.utc)
    out = []
    for m in media:
        is_photo = m["media_type"] in ("IMAGE", "CAROUSEL_ALBUM")
        if not m["media_url"].startswith("http"):
            continue  # Instagram withholds the file (licensed music)
        if m["media_type"] != "VIDEO" and not is_photo:  # untrusted pages: photo caption must mention fire (below)
            continue  # photos only from approved trusted fire pages
        cap = m.get("caption", "")
        trusted = user in TRUSTED
        if m["id"] in state["shared"] or SKIP_WORDS.search(cap) or not (trusted or FIRE_WORDS.search(cap)):
            continue
        try:
            age = now - dt.datetime.fromisoformat(m["timestamp"].replace("Z", "+00:00"))
            if age.days > MAX_AGE_DAYS:
                continue
        except ValueError:
            pass
        score = float(m.get("view_count") or 0) / 20 + float(m.get("like_count") or 0)
        if is_photo:
            score *= 0.5  # prefer videos when a page has both
        out.append((score, m))
    return [m for _, m in sorted(out, key=lambda x: -x[0])]


def caption_for(username, permalink):
    return (f"🎥 @{username}\n\n"
            f"Video by @{username}. Give them a follow!\n\n"
            f"Original post: {permalink}\n\n"
            "Tag us to be featured. #fireservice #firefighter #firehouse #firedepartment #fireground #stationhq")


# Check mode: test several handles at once without posting.
if DRY and len(ACCOUNTS) > 1 and os.environ.get("TEST_ACCOUNT"):
    for user in ACCOUNTS:
        try:
            media = ig.recent_media(user)
            vids = candidates(media, user)
            import subprocess, tempfile, urllib.request
            sound = []
            for v in [x for x in media if x["media_type"] == "VIDEO" and x["media_url"].startswith("http")][:3]:
                f = tempfile.mktemp(suffix=".mp4")
                try:
                    urllib.request.urlretrieve(v["media_url"], f)
                    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries",
                                        "stream=codec_type", "-of", "csv=p=0", f], capture_output=True, text=True)
                    sound.append("SOUND" if "audio" in r.stdout else "silent")
                except Exception as e:
                    sound.append(f"dlfail")
            print(f"AUDIO @{user}: {' '.join(sound) or 'no videos'}")
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
for _ in range(len(ACCOUNTS)):  # each account at most once per run
    if not order:
        order = ACCOUNTS[:]
        random.shuffle(order)
    user = order.pop(0)
    if on_cooldown(user) and not os.environ.get("TEST_ACCOUNT"):
        print(f"@{user}: reposted in the last {COOLDOWN_DAYS:g} days, skipping")
        continue
    try:
        vids = candidates(ig.recent_media(user), user)
    except RuntimeError as e:
        print(f"Skipping @{user}: {e}")
        continue
    if not vids:
        print(f"@{user}: no fresh action videos, trying the next account")
        continue
    if DRY:
        m = vids[0]
        print(f"[dry run] would repost {m['permalink']} from @{user} "
              f"(views {m.get('view_count') or '?'}, likes {m.get('like_count') or '?'})")
        posted = True
        break
    for m in vids[:4]:  # best first; skip any without sound
        try:
            if m["media_type"] != "VIDEO":
                ig.publish("IMAGE", media_host.prepare_image(m["media_url"], m["id"]),
                           caption_for(user, m["permalink"]).replace("🎥", "📸", 1).replace("Video by", "Photo by", 1))
                print(f"Reposted photo {m['permalink']} from @{user}")
                state["shared"] = (state["shared"] + [m["id"]])[-1000:]
                state["last"][user] = dt.datetime.now(dt.timezone.utc).isoformat()
                posted = True
                break
            hosted_url = media_host.prepare_video(m["media_url"], m["id"])
        except media_host.NoAudio as e:
            print(f"Skipping {m['permalink']}: {e}")
            state["shared"] = (state["shared"] + [m["id"]])[-1000:]  # don't retry silent videos
            continue
        ig.publish("REELS", hosted_url, caption_for(user, m["permalink"]))
        print(f"Reposted {m['permalink']} from @{user}")
        state["shared"] = (state["shared"] + [m["id"]])[-1000:]
        state["last"][user] = dt.datetime.now(dt.timezone.utc).isoformat()
        posted = True
        break
    if posted:
        break
    print(f"@{user}: no live-fire videos with sound, trying the next account")

if not posted:
    print("Nothing new to repost right now.")

if not DRY:
    state["order"] = order
    STATE_FILE.parent.mkdir(exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))
