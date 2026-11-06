"""Safe end-to-end test: prepare a muted library clip with size-up graphics, ask Instagram to build a Reel
container with Instagram music + a collab invite, wait until it's processed, and STOP (never publish).
Unpublished containers expire on their own after 24 h."""
import json
import pathlib
import tempfile
import time
import urllib.request

import graph
import ig
import media_host
import sizeup

caps = json.loads((graph.ROOT / "state" / "captures.json").read_text())
c = next(x for x in caps["clips"].values() if x["music"] and not x["posted"])
print(f"Test clip: {c['permalink']} from @{c['user']} (muted)")
work = pathlib.Path(tempfile.mkdtemp())
f = work / c["asset"]
url = f"https://github.com/stanton09/stationhq-insta/releases/download/captures/{c['asset']}"
with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "stationhq-bot"}), timeout=180) as r:
    f.write_bytes(r.read())
out = work / f"sizeup_{c['asset']}"
q, ctx, _ = sizeup.make_sizeup(f, out, work, c["user"], c["code"], c.get("caption", ""), has_audio=False)
hosted = media_host.host_file(out, work)
print("Hosted test video:", hosted)
audio = {"audio_id": ig._pick_track(), "audio_volume": 100, "video_volume": 0}
p = dict(media_type="REELS", video_url=hosted, caption="TEST - not published", share_to_feed="true",
         audio_configuration=json.dumps(audio), collaborators=json.dumps([c["user"]]))
cid = graph.call("POST", f"{graph.ig_id()}/media", **p)["id"]
print("Container created (not published):", cid)
for _ in range(40):
    st = graph.call("GET", cid, fields="status_code,status")
    if st.get("status_code") in ("FINISHED", "ERROR", "EXPIRED"):
        break
    time.sleep(10)
print("Container status:", st)
print("NOT PUBLISHED. Test only.")
