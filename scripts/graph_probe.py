"""Read-only: find older garden_state_size_up videos (all pages of their feed), most-liked first."""
import graph
u = "garden_state_size_up"
f = "business_discovery.username(%s){media.limit(50)%s{media_type,like_count,timestamp,permalink,media_url,caption}}"
after, allm = "", []
for _ in range(8):
    r = graph.call("GET", graph.ig_id(), fields=f % (u, f".after({after})" if after else ""))
    m = r["business_discovery"]["media"]
    allm += m.get("data", [])
    after = m.get("paging", {}).get("cursors", {}).get("after")
    if not after:
        break
print("total posts scanned:", len(allm))
for m in allm:
    if "cornice" in (m.get("caption") or "").lower():
        print("CORNICE", m["permalink"], m["timestamp"][:10], m.get("like_count"), "url" if m.get("media_url") else "music")
vids = sorted([m for m in allm if m.get("media_type") == "VIDEO"], key=lambda m: -(m.get("like_count") or 0))
for m in vids[:15]:
    print(f"TOP {m.get('like_count'):>6} {m['timestamp'][:10]} {m['permalink'].rstrip('/').split('/')[-1]} "
          f"{'url' if m.get('media_url') else 'music'} {(m.get('caption') or '')[:70]!r}")
