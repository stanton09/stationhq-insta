"""Keep a queue of TikTok-ready videos for @stationhq (no posting).

Videos live on the orphan branch `tiktok` (force-pushed each run, so main never grows):
  queue.json + *.mp4. Fire-safety explainer Reels already on main are referenced by path instead.
Sources: DVIDS live-burn clips (public domain), NIST fire-science clips (public domain),
StationHQ fire-safety explainers. Silent clips get a credited Kevin MacLeod track (CC BY 4.0).

The TikTok scheduler (a Claude scheduled task) schedules items in TikTok Studio and records each
scheduled id in state/tiktok.json on main; this script drops those from the queue and refills it.

Env: QUEUE_DIR = checkout of the `tiktok` branch (may be empty), DVIDS_API_KEY, TARGET (default 16).
"""
import datetime as dt
import json
import os
import pathlib
import re
import shutil
import subprocess

ROOT = pathlib.Path(__file__).resolve().parent.parent
Q = pathlib.Path(os.environ.get("QUEUE_DIR", ROOT / "tq"))
Q.mkdir(parents=True, exist_ok=True)
STATE = ROOT / "state/tiktok.json"
state = json.loads(STATE.read_text()) if STATE.exists() else {"scheduled": []}
DONE = {s["id"] for s in state["scheduled"]} | set(state.get("used_before", []))
TODAY = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=5)).date()
TARGET = int(os.environ.get("TARGET", "16"))
MUSIC = ROOT / "brand/brisket/music"
TRACKS = {  # file -> display title
    "music_ready_aim_fire.mp3": "Ready Aim Fire", "music_hustle.mp3": "Hustle",
    "music_investigations.mp3": "Investigations", "music_guts_and_bourbon.mp3": "Guts and Bourbon",
    "music_fearless_first.mp3": "Fearless First", "music_montauk_point.mp3": "Montauk Point",
}
MUSIC_CREDIT = "🎵 \"{}\" Kevin MacLeod (incompetech.com), CC BY 4.0"

mf = Q / "queue.json"
queue = json.loads(mf.read_text()) if mf.exists() else []
queue = [q for q in queue if q["id"] not in DONE and (q.get("path") or (Q / q["file"]).exists())]
keep = {q.get("file") for q in queue}
for f in Q.glob("*.mp4"):
    if f.name not in keep:
        f.unlink()
have = {q["id"] for q in queue}
print(f"{len(queue)} unscheduled items kept; target {TARGET}")


def kind_count(k):
    return sum(q["kind"] == k for q in queue)


def duration(p):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                         capture_output=True, text=True).stdout
    return float(out.strip() or 0)


def add_music(src, dst, track):
    d = duration(src)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(src), "-i", str(MUSIC / track),
                    "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                    "-af", f"volume=0.8,afade=t=in:d=0.5,afade=t=out:st={max(d - 1.5, 0):.2f}:d=1.5",
                    "-c:a", "aac", "-b:a", "160k", "-t", f"{d:.2f}", "-movflags", "+faststart", str(dst)],
                   check=True)


def next_track():
    names = list(TRACKS)
    return names[(len(DONE) + len(queue)) % len(names)]


def load_lib(script, cut):
    src = (ROOT / "scripts" / script).read_text().split(cut)[0]
    src = src.replace("import ig\n", "").replace("import media_host\n", "")
    ns = {"__file__": str(ROOT / "scripts" / script)}
    exec(compile(src, script, "exec"), ns)
    return ns


# 1. Fire-safety explainers already on main (seasonal: up to 10 days ahead of their Instagram date).
for mp4 in sorted((ROOT / "content/safety").glob("*.mp4")):
    if kind_count("safety") >= 4:
        break
    day, slug = mp4.stem.split("_", 1)
    sid = f"safety:{slug}"
    if sid in DONE or sid in have or dt.date.fromisoformat(day) > TODAY + dt.timedelta(days=10):
        continue
    if dt.date.fromisoformat(day) < TODAY - dt.timedelta(days=21):
        continue
    txt = mp4.with_suffix(".txt").read_text().strip() if mp4.with_suffix(".txt").exists() else ""
    txt = re.sub(r"\s*Departments, feel free to repost to your story\.", "", txt)
    queue.append({"id": sid, "kind": "safety", "path": str(mp4.relative_to(ROOT)), "caption": txt,
                  "title": slug.replace("_", " ")})
    have.add(sid)
    print("added", sid)

# 2. NIST fire-science clips.
if kind_count("nist") < 3:
    nist = load_lib("nist.py", "\nTODAY =")
    for v in nist["VIDEOS"]:
        if kind_count("nist") >= 3 or len(queue) >= TARGET:
            break
        nid = f"nist:{v['id']}"
        if nid in DONE or nid in have:
            continue
        try:
            clip, work = nist["build"](v)
        except Exception as e:  # noqa: BLE001
            print("skip", nid, e)
            continue
        track = next_track()
        name = f"nist_{v['id']}.mp4"
        add_music(clip, Q / name, track)
        shutil.rmtree(work, ignore_errors=True)
        cap = v["caption"].replace("\n\n#", f"\n{MUSIC_CREDIT.format(TRACKS[track])}\n\n#", 1)
        queue.append({"id": nid, "kind": "nist", "file": name, "caption": cap, "title": v["title"]})
        have.add(nid)
        print("added", nid)

# 3. DVIDS live-burn clips fill the rest.
if len(queue) < TARGET and os.environ.get("DVIDS_API_KEY"):
    dv = load_lib("dvids.py", '\nif os.environ.get("GITHUB_EVENT_NAME")')
    dv["state"]["posted"] = []  # Instagram history doesn't matter on TikTok
    tries = 0
    for r in dv["candidates"]():
        if len(queue) >= TARGET or tries >= 14:
            break
        did = f"dvids:{r['id'].split(':')[1]}"
        if did in DONE or did in have:
            continue
        tries += 1
        try:
            asset = dv["api"]("asset", id=r["id"]).get("results") or {}
            if isinstance(asset, list):
                asset = asset[0] if asset else {}
            src = dv["best_file"](asset)
            if not src:
                continue
            clip, work, branch = dv["build"](asset, src)
        except Exception as e:  # noqa: BLE001
            print("skip", did, e)
            continue
        if not clip:
            shutil.rmtree(work, ignore_errors=True)
            continue
        name = f"dvids_{did.split(':')[1]}.mp4"
        credit = ""
        if dv["KEPT_AUDIO"]:
            shutil.move(str(clip), Q / name)
        else:
            track = next_track()
            add_music(clip, Q / name, track)
            credit = MUSIC_CREDIT.format(TRACKS[track]) + "\n"
        shutil.rmtree(work, ignore_errors=True)
        loc = asset.get("location") or {}
        place = ", ".join(x for x in (loc.get("city"), loc.get("state") or loc.get("country")) if x)
        cap = (f"{asset['title'].strip()} 🔥\n\n"
               "Military firefighters run live burns like this year-round. "
               "What does your department's live-fire training look like? 👇\n\n"
               f"{'📍 ' + place + chr(10) if place else ''}"
               f"🎥 Video: {branch} via DVIDS (public domain). The appearance of U.S. Department of War (DoW) "
               "visual information does not imply or constitute DoW endorsement.\n"
               f"{credit}\n"
               "#firefighter #livefire #firetraining #firehouse #fireservice #stationhq")
        queue.append({"id": did, "kind": "dvids", "file": name, "caption": cap, "title": asset["title"].strip()})
        have.add(did)
        print("added", did, asset["title"])

mf.write_text(json.dumps(queue, indent=1, ensure_ascii=False))
print(f"queue now {len(queue)}: " + ", ".join(f"{k}={kind_count(k)}" for k in ("dvids", "nist", "safety")))
