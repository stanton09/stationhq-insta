"""Every page (feed and Story combined) is reposted at most once per cooldown_days (accounts.json, 7).

Repost the best recent action video from the next firehouse account in a shuffled rotation, with credit.

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
LIBRARY_PER_DAY = 1  # one repost a day from the saved clip library, the other is a fresh post from an approved page
state = json.loads(STATE_FILE.read_text()) if STATE_FILE.exists() else {}
state.setdefault("shared", [])
state.setdefault("order", [])
state.setdefault("last", {})  # handle -> ISO time of last repost


def on_cooldown(user, days=None):
    t = state["last"].get(user)
    if not t:
        return False
    age = dt.datetime.now(dt.timezone.utc) - dt.datetime.fromisoformat(t)
    return age.total_seconds() < (COOLDOWN_DAYS if days is None else days) * 86400


_CAPS_FILE = ROOT / "state" / "captures.json"
_LIB = json.loads(_CAPS_FILE.read_text())["clips"] if _CAPS_FILE.exists() else {}


def _mark_library(user, permalink):
    """A fresh repost that's also in the clip library: mark the library copy posted too."""
    if not _CAPS_FILE.exists():
        return
    caps = json.loads(_CAPS_FILE.read_text())
    k = f"{user}_{permalink.rstrip('/').split('/')[-1]}"
    if k in caps["clips"] and not caps["clips"][k]["posted"]:
        caps["clips"][k]["posted"] = True
        _CAPS_FILE.write_text(json.dumps(caps, indent=2))


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
        code = m.get("permalink", "").rstrip("/").split("/")[-1]
        lib = _LIB.get(f"{user}_{code}")
        if lib and lib.get("posted"):
            continue  # already posted from the clip library
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

def last_page():
    """The page we reposted most recently (never repeat it back to back)."""
    return max(state["last"], key=lambda u: state["last"][u]) if state["last"] else None


def post_captured(force=False):
    """Up to LIBRARY_PER_DAY times a day, post a clip captured in the browser from an approved page (stored on the
    `captures` release). Only clips with their own sound; muted ones wait for Instagram music."""
    cap_file = ROOT / "state" / "captures.json"
    if os.environ.get("TEST_ACCOUNT") or not cap_file.exists():
        return False
    caps = json.loads(cap_file.read_text())
    today = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=5)).date().isoformat()
    if caps.get("last_day") != today:
        caps["last_day"], caps["today_count"] = today, 0
    if caps.get("today_count", 0) >= LIBRARY_PER_DAY and not force:
        return False
    import graph
    music_ok = graph.available()  # muted clips can post once Instagram music is available
    holds = caps.get("hold_until", {})  # page -> date: no library clips from that page before then
    ready = [c for c in caps["clips"].values() if not c["posted"] and (music_ok or not c["music"])
             and not on_cooldown(c["user"]) and today >= holds.get(c["user"], "")]
    if not ready and not (caps.get("next") and today >= caps.get("next_after", "")):
        return False
    if not ready and caps.get("next") in caps["clips"] and on_cooldown(caps["clips"][caps["next"]]["user"]):
        return False
    nxt = caps.get("next")  # a clip hand-picked for the next repost (skips the cooldown)
    if nxt and caps.get("next_after") and today < caps["next_after"]:
        nxt = None  # hand-pick is held until that date
    if nxt and nxt in caps["clips"] and on_cooldown(caps["clips"][nxt]["user"]):
        print(f"Hand-picked clip {nxt} waits: that page was reposted in the last {COOLDOWN_DAYS:g} days")
        nxt = None  # stays queued for a later run
    if nxt and nxt in caps["clips"] and not caps["clips"][nxt]["posted"]:
        c = caps["clips"][nxt]
        print(f"Hand-picked clip: {nxt}")
    else:
        # variety: pick a page at random (every page equally likely, not weighted by how many clips it has),
        # never the page we just reposted, then a random clip from that page
        pages = sorted({x["user"] for x in ready if x["user"] != last_page()}) or sorted({x["user"] for x in ready})
        page = random.choice(pages)
        c = random.choice([x for x in ready if x["user"] == page])
        print(f"Library pick: @{page} (from {len(pages)} pages)")
    if DRY:
        print(f"[dry run] would post captured clip {c['permalink']} from @{c['user']}")
        return True
    import tempfile, urllib.request
    work = pathlib.Path(tempfile.mkdtemp())
    f = work / c["asset"]
    url = f"https://github.com/stanton09/stationhq-insta/releases/download/captures/{c['asset']}"
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "stationhq-bot"}), timeout=180) as r:
        f.write_bytes(r.read())
    import sizeup
    out = work / f"sizeup_{c['asset']}"
    q, ctx, _ = sizeup.make_sizeup(f, out, work, c["user"], c["code"], c.get("caption", ""), has_audio=not c["music"])
    ig.publish("REELS", media_host.host_file(out, work), sizeup.caption_for(c["user"], q, ctx, c["permalink"]),
               optional=True, collaborators=[c["user"]], music=True if c["music"] else "under",
               first_comment=ig.first_comment("repost", c["code"]))
    print(f"Posted captured clip {c['permalink']} from @{c['user']}")
    c["posted"] = True
    if caps.get("next") == c.get("user", "") + "_" + c.get("code", ""):
        caps.pop("next", None)
        caps.pop("next_after", None)
    caps["today_count"] = caps.get("today_count", 0) + 1
    cap_file.write_text(json.dumps(caps, indent=2))
    state["last"][c["user"]] = dt.datetime.now(dt.timezone.utc).isoformat()
    return True


# Keep a shuffled rotation; refill and reshuffle when it runs out or accounts change.
order = [a for a in state["order"] if a in ACCOUNTS]
if not order:
    order = ACCOUNTS[:]
    random.shuffle(order)

try:
    posted = post_captured()
except ig.OverBudget as e:
    print(f"Skipping captured clip: {e}")
    posted = True  # nothing else to try this run
for _ in range(0 if posted else len(ACCOUNTS)):  # each account at most once per run
    if not order:
        order = ACCOUNTS[:]
        random.shuffle(order)
    user = order.pop(0)
    if user == last_page() and not os.environ.get("TEST_ACCOUNT"):
        print(f"@{user}: just reposted, picking a different page")
        continue
    if on_cooldown(user) and not os.environ.get("TEST_ACCOUNT"):
        print(f"@{user}: reposted in the last {COOLDOWN_DAYS:g} days, skipping")
        continue
    try:
        want = os.environ.get("PAYLOAD", "").strip()
        if want and os.environ.get("TEST_ACCOUNT"):
            # owner-requested: payload "newest" or a post's shortcode (skips the ranking and caption filters)
            ok = [m for m in ig.recent_media(user) if m["media_url"].startswith("http")
                  and m["media_type"] in ("VIDEO", "IMAGE")]
            vids = ok[:1] if want == "newest" else [m for m in ok if f"/{want}/" in m["permalink"] + "/"][:1]
            if not vids:
                print(f"@{user}: requested post {want} not found in their recent posts")
        else:
            vids = candidates(ig.recent_media(user), user)
    except ig.OverBudget as e:
        print(f"Stopping reposts: {e}")
        break
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
        if os.environ.get("PAYLOAD") and m["media_type"] == "VIDEO":  # requested post: build a preview too
            print("Preview: " + media_host.prepare_video(m["media_url"], m["id"], sizeup_info=(
                user, m["permalink"].rstrip("/").split("/")[-1], m.get("caption", ""))))
        posted = True
        break
    for m in vids[:4]:  # best first; skip any without sound
        try:
            if m["media_type"] != "VIDEO":
                ig.publish("IMAGE", media_host.prepare_image(m["media_url"], m["id"]),
                           caption_for(user, m["permalink"]).replace("🎥", "📸", 1).replace("Video by", "Photo by", 1),
                           optional=True, collaborators=[user])
                print(f"Reposted photo {m['permalink']} from @{user}")
                state["shared"] = (state["shared"] + [m["id"]])[-1000:]
                state["last"][user] = dt.datetime.now(dt.timezone.utc).isoformat()
                posted = True
                break
            hosted_url = media_host.prepare_video(m["media_url"], m["id"],
                                                  sizeup_info=(user, m["permalink"].rstrip("/").split("/")[-1],
                                                               m.get("caption", "")))
        except media_host.NoAudio as e:
            print(f"Skipping {m['permalink']}: {e}")
            state["shared"] = (state["shared"] + [m["id"]])[-1000:]  # don't retry silent videos
            continue
        import sizeup
        code = m["permalink"].rstrip("/").split("/")[-1]
        ig.publish("REELS", hosted_url, sizeup.caption_for(user, sizeup.question_for(code, m.get("caption", "")),
                                                           sizeup.context_line(m.get("caption", "")), m["permalink"]),
                   optional=True, collaborators=[user], music="under",
                   first_comment=ig.first_comment("repost", code))
        print(f"Reposted {m['permalink']} from @{user}")
        _mark_library(user, m["permalink"])
        state["shared"] = (state["shared"] + [m["id"]])[-1000:]
        state["last"][user] = dt.datetime.now(dt.timezone.utc).isoformat()
        posted = True
        break
    if posted:
        break
    print(f"@{user}: no live-fire videos with sound, trying the next account")

if not posted and not DRY:
    print("No fresh post from approved pages; using the clip library instead.")
    posted = post_captured(force=True)
if not posted:
    print("Nothing new to repost right now.")

if not DRY:
    if posted:  # how many reposts went out today (ET), for the backup scheduler
        day = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=5)).date().isoformat()
        tc = state.get("today", {})
        state["today"] = {"date": day, "count": (tc.get("count", 0) if tc.get("date") == day else 0) + 1}
    state["order"] = order
    STATE_FILE.parent.mkdir(exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))
