"""Read-only: follower counts of approved pages and their most-liked videos (last ~50 posts)."""
import json
import pathlib
import graph

ROOT = pathlib.Path(__file__).resolve().parent.parent
a = json.loads((ROOT / "accounts.json").read_text())
caps = json.loads((ROOT / "state" / "captures.json").read_text())["clips"]
users = sorted(set(a["accounts"]) | {c["user"] for c in caps.values()})
rows = []
for u in users:
    try:
        r = graph.call("GET", graph.ig_id(), fields=f"business_discovery.username({u}){{followers_count,media_count,"
                       f"media.limit(50){{media_type,like_count,comments_count,timestamp,permalink,media_url,caption}}}}")
        bd = r["business_discovery"]
        vids = [m for m in bd.get("media", {}).get("data", []) if m.get("media_type") == "VIDEO"]
        vids.sort(key=lambda m: -(m.get("like_count") or 0))
        rows.append((bd.get("followers_count", 0), u, vids[:5]))
    except RuntimeError as e:
        rows.append((0, u, []))
        print(f"{u}: {str(e)[:120]}")
for f, u, vids in sorted(rows, reverse=True):
    print(f"FOLLOWERS {f:>8} @{u}")
    for m in vids:
        code = m["permalink"].rstrip("/").split("/")[-1]
        lib = "LIB" if f"{u}_{code}" in caps else ("url" if m.get("media_url") else "music")
        print(f"   {m.get('like_count',0):>6} likes {m['timestamp'][:10]} {code} [{lib}] {(m.get('caption') or '')[:70]!r}")
