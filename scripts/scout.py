"""Scout for repost sources: read @mentions in captions of seed fire pages, test each mentioned
page, and report which ones have downloadable videos (original audio = automation-ready).

Run: Actions -> Instagram autopost -> Run workflow -> job "scout", test_account = seed handles.
Posts nothing. Prints a ranked list.
"""
import os
import re
import subprocess
import tempfile
import urllib.request

import ig
from filters import FIRE_WORDS

SEEDS = [s.strip().lstrip("@") for s in os.environ.get("TEST_ACCOUNT", "").split(",") if s.strip()]
MAX_TEST = int(os.environ.get("SCOUT_MAX", "20"))
MENTION = re.compile(r"@([A-Za-z0-9_.]{2,30}[A-Za-z0-9_])")

mentions = {}
for seed in SEEDS:
    try:
        media = ig.recent_media(seed)
        print(f"seed @{seed}: {len(media)} posts; sample captions: " + " || ".join(repr(m.get('caption','')[:80]) for m in media[:3]))
        for m in media:
            for h in MENTION.findall(m.get("caption", "")):
                h = h.lower()
                if h not in SEEDS and h != "stationhqofficial":
                    mentions[h] = mentions.get(h, 0) + 1
    except RuntimeError as e:
        print(f"seed @{seed}: {e}")

ranked = sorted(mentions, key=lambda h: -mentions[h])[:MAX_TEST]
print(f"Found {len(mentions)} tagged pages; testing top {len(ranked)}")

results = []
for h in ranked:
    try:
        media = ig.recent_media(h)
    except RuntimeError:
        print(f"SCOUT @{h}: not usable (personal/private/Creator-restricted)")
        continue
    vids = [m for m in media if m["media_type"] == "VIDEO"]
    ok = [m for m in vids if m["media_url"].startswith("http")]
    fire = [m for m in ok if FIRE_WORDS.search(m.get("caption", ""))]
    sound = 0
    for m in ok[:2]:
        f = tempfile.mktemp(suffix=".mp4")
        try:
            urllib.request.urlretrieve(m["media_url"], f)
            r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries",
                                "stream=codec_type", "-of", "csv=p=0", f], capture_output=True, text=True)
            sound += "audio" in r.stdout
        except Exception:
            pass
    verdict = "READY" if ok and sound else ("NO-FILES" if vids else "NO-VIDEOS")
    results.append((verdict, h, len(vids), len(ok), len(fire), sound))
    print(f"SCOUT @{h}: {verdict} videos={len(vids)} downloadable={len(ok)} fire={len(fire)} sound={sound}/{min(2, len(ok))}")

print("\nREADY TO DM (automation will work):")
for v, h, *_ in sorted(results, key=lambda r: (r[0] != "READY", -r[4])):
    if v == "READY":
        print(f"  https://instagram.com/{h}")
