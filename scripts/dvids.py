"""Daily public-domain fire video from DVIDS (U.S. military public media).

Searches DVIDS for live-fire training videos, picks the newest one not yet posted (raw B-Roll first,
since it has real fire sound), cuts the 40 s with the most fire, formats it vertically with credit,
and posts it as a Reel.

DVIDS content is public domain; DVIDS API data is free for commercial use. Every post credits the
branch/unit and carries the DoD non-endorsement line.

Needs secret DVIDS_API_KEY.  DRY_RUN=1: build + host the clip but don't post.  DVIDS_ID=<n> forces one.
"""
import datetime as dt
import json
import os
import pathlib
import re
import subprocess
import tempfile
import urllib.parse
import urllib.request

import ig
import media_host

ROOT = pathlib.Path(__file__).resolve().parent.parent
STATE_FILE = ROOT / "state/dvids.json"
state = json.loads(STATE_FILE.read_text()) if STATE_FILE.exists() else {"posted": []}
DRY = bool(os.environ.get("DRY_RUN"))
KEY = os.environ.get("DVIDS_API_KEY", "")
API = "https://api.dvidshub.net"
CLIP = 40
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
QUERIES = ["firefighters live burn", "firefighter live fire training", "structural fire training firefighters",
           "aircraft rescue firefighting", "ARFF live fire", "fire department training burn", "firefighters fire"]
# must be about firefighting, not weapons ranges ("live fire" means shooting in the military)
FIREFIGHT = re.compile(r"firefight|fire fight|fire department|fire dept|fire and emergency|fire & emergency|"
                       r"fire station|fire rescue|\barff\b|crash rescue|fire protection|fire academy|live burn|"
                       r"burn (building|tower|pit)|structural fire|aircraft fire|fire truck|fire engine", re.I)
WEAPONS = re.compile(r"squad|platoon|rifle|weapon|range|marksman|gunner|artillery|mortar|howitzer|tank|"
                     r"machine gun|grenade|missile|rocket|munition|small arms|qualification|assault|attack training|"
                     r"maneuver|infantry|sniper|\bhimars\b|strike|bomb|ordnance|\beod\b|airstrike", re.I)
MUSIC = re.compile(r"music|licensed|envato|soundtrack|artlist|audio jungle|epidemic sound", re.I)
TODAY = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=5)).date().isoformat()


def api(path, **params):
    params["api_key"] = KEY
    url = f"{API}/{path}?{urllib.parse.urlencode(params, doseq=True)}"
    req = urllib.request.Request(url, headers={"User-Agent": "stationhq-bot", "Origin": "https://stationhq.app"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def candidates():
    seen, out = set(), []
    for q in QUERIES:
        res = api("search", q=q, type="video", sort="date", sortdir="desc", max_results=50,
                  from_duration=20, to_duration=900)
        for r in res.get("results", []):
            if r["id"] in seen or r["id"] in state["posted"]:
                continue
            seen.add(r["id"])
            text = f"{r.get('title', '')} {r.get('short_description', '')}".lower()
            if not FIREFIGHT.search(text) or WEAPONS.search(text):
                continue
            out.append(r)
    # raw B-Roll first (natural sound), then newest
    out.sort(key=lambda r: r.get("date_published", ""), reverse=True)
    out.sort(key=lambda r: r.get("category") != "B-Roll")  # stable: B-Roll first, newest within
    return out


def best_file(asset):
    files = [f for f in asset.get("files", []) if f.get("type") == "video/mp4" and f.get("src")]
    files = [f for f in files if int(f.get("width") or 0) <= 1920] or files
    return max(files, key=lambda f: int(f.get("bitrate") or 0))["src"] if files else None


def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                          str(path)], capture_output=True, text=True).stdout
    return float(out.strip() or 0)


def has_audio(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=codec_type",
                        "-of", "csv=p=0", str(path)], capture_output=True, text=True)
    return "audio" in r.stdout


MIN_FIRE = 0.004   # at least ~0.4% flame-colored pixels on average across the clip, or the video is skipped
W, H = 96, 54


def flame_scores(path):
    """Fraction of flame-colored pixels (bright orange/yellow, R>G>B) in each frame, sampled 2x a second."""
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-vf", f"fps=2,scale={W}:{H}",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    size, out = W * H * 3, []
    for i in range(0, len(raw) - size + 1, size):
        f, hits = raw[i:i + size], 0
        for j in range(0, size, 3):
            r, g, b = f[j], f[j + 1], f[j + 2]
            # flames: hot orange/yellow. Excludes red trucks/mats (low green), hi-vis yellow (R≈G), sky/gray (low sat)
            if r > 190 and g > 70 and r - g > 35 and g - b > 35 and b < 150:
                hits += 1
        out.append(hits / (W * H))
    return out


def fire_window(path, total):
    """(start, length, fire) for the 40 s with the most visible flame."""
    sc = flame_scores(path)
    win = CLIP * 2
    if len(sc) <= win:
        return 0.0, min(CLIP, total), (sum(sc) / len(sc) if sc else 0.0)
    best, start = -1.0, 0
    for i in range(0, len(sc) - win + 1):
        v = sum(sc[i:i + win])
        if v > best:
            best, start = v, i
    return start / 2, float(CLIP), best / win


def clean(s):
    return s.replace("\\", "").replace(":", r"\:").replace("'", "’").replace("%", r"\%")


def build(asset, src):
    work = pathlib.Path(tempfile.mkdtemp())
    raw, out = work / "raw.mp4", work / f"dvids_{asset['id'].split(':')[1]}.mp4"
    req = urllib.request.Request(src, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=300) as r:
        raw.write_bytes(r.read())
    total = duration(raw)
    start, length, fire = fire_window(raw, total)
    print(f"{asset.get('title')}: flame score {fire:.4f}")
    if fire < MIN_FIRE:
        return None, work, None
    music = bool(MUSIC.search(asset.get("description", "")))
    keep_audio = has_audio(raw) and not music and asset.get("category") == "B-Roll"
    branch = asset.get("branch") or "U.S. military"
    credit = f"Video\\: {clean(branch)} / DVIDS"
    print(f"{asset['title']}: {total:.0f}s, using {start:.0f}-{start + length:.0f}s, "
          f"category={asset.get('category')}, audio={'kept' if keep_audio else 'muted'}")
    vf = (f"[0:v]split=2[a][b];"
          f"[a]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=24:2,eq=brightness=-0.12[bg];"
          f"[b]crop='min(iw,ih*4/3)':ih,scale=1080:-2[fg];[bg][fg]overlay=0:(H-h)/2,"
          f"drawbox=x=0:y=170:w=iw:h=150:color=black@0.55:t=fill,"
          f"drawtext=fontfile={FONT}:text='LIVE FIRE TRAINING':x=(w-text_w)/2:y=218:fontsize=58:fontcolor=white,"
          f"drawtext=fontfile={FONT}:text='{credit}':x=(w-text_w)/2:y=h-260:fontsize=38:fontcolor=white@0.9:"
          f"box=1:boxcolor=black@0.5:boxborderw=18,fps=30[v]")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{start:.2f}", "-t", f"{length:.2f}", "-i", str(raw),
           "-f", "lavfi", "-t", f"{length:.2f}", "-i", "anullsrc=r=44100:cl=stereo", "-filter_complex", vf,
           "-map", "[v]", "-map", "0:a:0" if keep_audio else "1:a",
           "-c:v", "libx264", "-preset", "veryfast", "-b:v", "4M", "-maxrate", "4.5M", "-bufsize", "9M",
           "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-ar", "44100", "-ac", "2", "-shortest",
           "-movflags", "+faststart", str(out)]
    subprocess.run(cmd, check=True)
    return out, work, branch


def caption(asset, branch):
    loc = asset.get("location") or {}
    place = ", ".join(x for x in (loc.get("city"), loc.get("state") or loc.get("country")) if x)
    desc = re.sub(r"\s*\((U\.S\.|US) .*?\)\s*$", "", (asset.get("description") or "").strip())
    desc = re.split(r"(?<=[.!?])\s", desc)
    desc = " ".join(desc[:2])[:400]
    unit = asset.get("unit_name") or ""
    return (f"🔥 {asset['title']}\n\n{desc}\n\n"
            f"{'📍 ' + place + chr(10) if place else ''}"
            f"🎥 Video: {branch}{' / ' + unit if unit else ''} via DVIDS (public domain)\n"
            "The appearance of U.S. Department of War (DoW) visual information does not imply or constitute "
            "DoW endorsement.\n\n"
            "Military firefighters train like this year-round. What's your department's live-fire schedule? 👇\n\n"
            "#livefire #firetraining #firefighter #militaryfirefighter #fireservice #firehouse #stationhq")


if os.environ.get("GITHUB_EVENT_NAME") == "schedule" and state.get("last") == TODAY:
    print("DVIDS video already posted today; skipping.")
    raise SystemExit(0)
if not KEY:
    print("DVIDS_API_KEY secret not set yet; skipping.")
    raise SystemExit(0)

forced = os.environ.get("DVIDS_ID")
picks = [{"id": f"video:{forced}"}] if forced else candidates()
print(f"{len(picks)} candidate videos")
for r in picks[:12]:
    asset = api("asset", id=r["id"]).get("results") or {}
    if isinstance(asset, list):
        asset = asset[0] if asset else {}
    src = best_file(asset)
    if not src:
        print(f"skip {r['id']}: no downloadable mp4")
        continue
    clip, work, branch = build(asset, src)
    if not clip:
        print(f"skip {r['id']}: not enough visible fire")
        continue
    url = media_host.host_file(clip, work)
    print(f"Clip ready: {url}")
    cap = caption(asset, branch)
    if DRY:
        print("[dry run] caption:\n" + cap)
        break
    ig.publish("REELS", url, cap)
    print(f"Posted DVIDS {r['id']}: {asset.get('title')}")
    state["posted"].append(r["id"])
    state["last"] = TODAY
    STATE_FILE.parent.mkdir(exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))
    break
