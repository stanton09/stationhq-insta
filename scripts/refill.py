"""Keep the clip library stocked without the laptop: pull live-fire videos (ones Instagram lets us
download, i.e. no licensed song) from the approved pages' last ~100 posts into the library.

Runs weekly, and on any day the library has under 2 weeks of clips left (FORCE=1 runs it anyway)."""
import datetime as dt
import json
import os
import pathlib
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import graph  # noqa: E402
from filters import FIRE_WORDS, SKIP_WORDS  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
CAPS = ROOT / "state" / "captures.json"
caps = json.loads(CAPS.read_text()) if CAPS.exists() else {"clips": {}}
left = sum(1 for c in caps["clips"].values() if not c["posted"])
days = left // 3
weekly = dt.datetime.now(dt.timezone.utc).weekday() == 6  # Sunday
if days >= 14 and not weekly and not os.environ.get("FORCE"):
    print(f"Library has {left} clips (~{days} days); no refill needed today")
    raise SystemExit(0)

cfg = json.loads((ROOT / "accounts.json").read_text())
trusted = set(cfg.get("trusted_all_videos", []))
shared = set(json.loads((ROOT / "state" / "reposts.json").read_text()).get("shared", []))
PER_PAGE = 6
items = []
for u in cfg["accounts"]:
    after, media = "", []
    for _ in range(2):  # ~100 posts
        f = ("business_discovery.username(%s){media.limit(50)%s{id,media_type,media_url,permalink,caption,like_count}}"
             % (u, f".after({after})" if after else ""))
        try:
            r = graph.call("GET", graph.ig_id(), fields=f)["business_discovery"]["media"]
        except (RuntimeError, KeyError) as e:
            print(f"@{u}: skipped ({str(e)[:80]})")
            break
        media += r.get("data", [])
        after = r.get("paging", {}).get("cursors", {}).get("after")
        if not after:
            break
    picks = []
    for m in sorted(media, key=lambda m: -(m.get("like_count") or 0)):
        code = m["permalink"].rstrip("/").split("/")[-1]
        cap = m.get("caption") or ""
        if (m.get("media_type") != "VIDEO" or not m.get("media_url") or f"{u}_{code}" in caps["clips"]
                or m["id"] in shared or SKIP_WORDS.search(cap) or not (u in trusted or FIRE_WORDS.search(cap))):
            continue
        picks.append({"code": code, "user": u, "music": False, "cap": cap[:300], "url": m["media_url"]})
        if len(picks) >= PER_PAGE:
            break
    print(f"@{u}: {len(picks)} new clips")
    items += picks

if not items:
    print("No new clips found")
    raise SystemExit(0)
(ROOT / "content" / "captures_in.json").write_text(json.dumps(items))
subprocess.run([sys.executable, str(pathlib.Path(__file__).parent / "capture.py")], check=True)
