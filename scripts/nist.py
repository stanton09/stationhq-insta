"""Weekly NIST fire-science Reel: download a public-domain NIST fire video, cut the 30-45 s with the
most fire growth, format it vertically with a title and 'Video: NIST' credit, and post it.

DRY_RUN=1: build and host the clip (prints its URL) but don't post.  NIST_ID=<entry> forces a video.
"""
import datetime as dt
import json
import os
import pathlib
import subprocess
import tempfile
import urllib.request

import ig
import media_host

ROOT = pathlib.Path(__file__).resolve().parent.parent
VIDEOS = json.loads((ROOT / "content/nist_videos.json").read_text())["videos"]
STATE_FILE = ROOT / "state/nist.json"
state = json.loads(STATE_FILE.read_text()) if STATE_FILE.exists() else {"posted": []}
DRY = bool(os.environ.get("DRY_RUN"))
CLIP = 40  # seconds
PARTNER = "684682"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def pick():
    forced = os.environ.get("NIST_ID")
    if forced:
        return next(v for v in VIDEOS if v["id"] == forced)
    month = dt.datetime.now().strftime("%m").lstrip("0")
    pool = [v for v in VIDEOS if v["id"] not in state["posted"]]
    seasonal = [v for v in pool if v.get("season") == month]
    regular = [v for v in pool if not v.get("season")]
    if seasonal:
        return seasonal[0]
    if regular:
        return regular[0]
    return None


def download(entry, dest):
    base = f"https://cdnapisec.kaltura.com/p/{PARTNER}/sp/{PARTNER}00/playManifest/entryId/{entry}"
    for url in (f"{base}/format/download/protocol/https/flavorParamIds/0",
                f"{base}/format/url/protocol/https/a.mp4"):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=300) as r:
                data = r.read()
            if len(data) > 100_000:
                dest.write_bytes(data)
                return
        except Exception as e:
            print(f"download try failed: {e}")
    raise RuntimeError(f"couldn't download NIST video {entry}")


def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
                          "csv=p=0", str(path)], capture_output=True, text=True).stdout
    return float(out.strip() or 0)


def best_window(path, total):
    """Window with the biggest brightness rise (ignition -> fully involved)."""
    if total <= CLIP + 5:
        return 0.0, total
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-vf",
                        "fps=2,scale=160:-1,signalstats,metadata=print:key=lavfi.signalstats.YAVG:file=-",
                        "-f", "null", "-"], capture_output=True, text=True)
    ys = [float(l.split("=")[1]) for l in r.stdout.splitlines() if "YAVG=" in l]
    if len(ys) < 10:
        return 0.0, CLIP
    w = CLIP * 2
    best, start = -1, 0
    for i in range(0, max(1, len(ys) - w)):
        seg = ys[i:i + w]
        score = (max(seg) - min(seg)) + 0.2 * (sum(seg) / len(seg))
        if score > best:
            best, start = score, i
    s = max(0.0, start / 2 - 2)  # a little lead-in
    return s, min(CLIP, total - s)


def build(v):
    work = pathlib.Path(tempfile.mkdtemp())
    raw, out = work / "raw.mp4", work / f"nist_{v['id']}.mp4"
    download(v["id"], raw)
    total = duration(raw)
    start, length = best_window(raw, total)
    print(f"{v['title']}: source {total:.0f}s, using {start:.0f}s-{start + length:.0f}s")
    title = v["title"].replace(":", r"\:").replace("'", "’")
    vf = (f"[0:v]split=2[a][b];"
          f"[a]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=24:2,"
          f"eq=brightness=-0.12[bg];"
          f"[b]scale=1080:-2[fg];"
          f"[bg][fg]overlay=0:(H-h)/2,"
          f"drawbox=x=0:y=170:w=iw:h=150:color=black@0.55:t=fill,"
          f"drawtext=fontfile={FONT}:text='{title}':x=(w-text_w)/2:y=218:fontsize=58:fontcolor=white,"
          f"drawtext=fontfile={FONT}:text='Video\\: NIST':x=(w-text_w)/2:y=h-260:fontsize=40:"
          f"fontcolor=white@0.9:box=1:boxcolor=black@0.5:boxborderw=18,fps=30[v]")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{start:.2f}", "-t", f"{length:.2f}",
           "-i", str(raw), "-f", "lavfi", "-t", f"{length:.2f}", "-i", "anullsrc=r=44100:cl=stereo",
           "-filter_complex", vf, "-map", "[v]", "-map", "1:a" if v.get("mute", True) else "0:a?",
           "-c:v", "libx264", "-preset", "veryfast", "-b:v", "4M", "-maxrate", "4.5M", "-bufsize", "9M",
           "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-shortest",
           "-movflags", "+faststart", str(out)]
    subprocess.run(cmd, check=True)
    return out, work


v = pick()
if not v:
    print("All NIST videos have been posted. Add more to content/nist_videos.json.")
    raise SystemExit(0)

clip, work = build(v)
url = media_host.host_file(clip, work)
print(f"Clip ready: {url}")

if DRY:
    print("[dry run] not posting")
    raise SystemExit(0)

ig.publish("REELS", url, v["caption"])
print(f"Posted NIST video: {v['title']}")
state["posted"].append(v["id"])
STATE_FILE.parent.mkdir(exist_ok=True)
STATE_FILE.write_text(json.dumps(state, indent=2))
