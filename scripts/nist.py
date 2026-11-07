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
import textwrap
import urllib.request

import ig
import media_host

ROOT = pathlib.Path(__file__).resolve().parent.parent
VIDEOS = json.loads((ROOT / "content/nist_videos.json").read_text())["videos"]
STATE_FILE = ROOT / "state/nist.json"
state = json.loads(STATE_FILE.read_text()) if STATE_FILE.exists() else {"posted": []}
DRY = bool(os.environ.get("DRY_RUN"))
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


SRC_WINDOW = 80  # seconds of source footage, played at 2x -> 40 s clip


def best_window(path, total):
    """80 s of source leading up to (and just past) the brightest moment, usually flashover."""
    if total <= SRC_WINDOW:
        return 0.0, total
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-vf",
                        "fps=1,scale=160:-1,signalstats,metadata=print:key=lavfi.signalstats.YAVG:file=-",
                        "-f", "null", "-"], capture_output=True, text=True)
    ys = [float(l.split("=")[1]) for l in r.stdout.splitlines() if "YAVG=" in l]
    if len(ys) < 10:
        return 0.0, SRC_WINDOW
    sm = [sum(ys[max(0, i - 2):i + 3]) / len(ys[max(0, i - 2):i + 3]) for i in range(len(ys))]
    skip = min(30, len(sm) // 10)  # ignore title cards at the start
    peak = max(range(skip, len(sm)), key=lambda i: sm[i])
    pre = sm[skip:max(skip + 5, peak - 60)]
    base = sorted(pre)[len(pre) // 2]
    thresh = base + 0.25 * (sm[peak] - base)
    # walk back from the peak to where the final rise began = fire taking off
    rise = peak
    while rise > skip and sm[rise] >= thresh:
        rise -= 1
    start = max(0.0, min(rise - 20.0, total - SRC_WINDOW))
    print(f"brightness: base {base:.0f}, peak {sm[peak]:.0f} at {peak}s, takeoff at {rise}s")
    return start, SRC_WINDOW


def build(v):
    work = pathlib.Path(tempfile.mkdtemp())
    raw, out = work / "raw.mp4", work / f"nist_{v['id']}.mp4"
    download(v["id"], raw)
    total = duration(raw)
    start, length = best_window(raw, total)
    print(f"{v['title']}: source {total:.0f}s, using {start:.0f}s-{start + length:.0f}s at 2x")
    out_len = length / 2
    # Wrap the title so every line fits inside the 1080 px frame with margins.
    # DejaVu Sans Bold averages ~0.62 em per character; keep lines under ~900 px.
    size = 58
    lines = textwrap.wrap(v["title"], width=max(8, int(900 / (size * 0.62))))
    while len(lines) > 3 and size > 36:
        size -= 4
        lines = textwrap.wrap(v["title"], width=max(8, int(900 / (size * 0.62))))
    line_h = int(size * 1.25)
    box_y, pad = 170, 36
    box_h = pad * 2 + line_h * len(lines)
    titles = "".join(
        f"drawtext=fontfile={FONT}:text='{ln.replace(':', chr(92) + ':').replace(chr(39), '’')}':"
        f"x=(w-text_w)/2:y={box_y + pad + i * line_h}:fontsize={size}:fontcolor=white,"
        for i, ln in enumerate(lines))
    # NIST footage is 16:9 and often a side-by-side comparison with its own labels near the
    # edges, so show the full frame (no side crop) centered on the blurred background.
    vf = (f"[0:v]setpts=0.5*PTS,split=2[a][b];"
          f"[a]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=24:2,"
          f"eq=brightness=-0.12[bg];"
          f"[b]scale=1080:-2[fg];"
          f"[bg][fg]overlay=0:(H-h)/2,"
          f"drawbox=x=0:y={box_y}:w=iw:h={box_h}:color=black@0.55:t=fill,"
          f"{titles}"
          f"drawtext=fontfile={FONT}:text='Video\\: NIST':x=(w-text_w)/2:y=h-260:fontsize=40:"
          f"fontcolor=white@0.9:box=1:boxcolor=black@0.5:boxborderw=18,fps=30[v]")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{start:.2f}", "-t", f"{length:.2f}",
           "-i", str(raw), "-f", "lavfi", "-t", f"{out_len:.2f}", "-i", "anullsrc=r=44100:cl=stereo",
           "-filter_complex", vf, "-map", "[v]", "-map", "1:a",
           "-c:v", "libx264", "-preset", "veryfast", "-b:v", "4M", "-maxrate", "4.5M", "-bufsize", "9M",
           "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-shortest",
           "-movflags", "+faststart", str(out)]
    subprocess.run(cmd, check=True)
    return out, work


TODAY = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=5)).date().isoformat()
if os.environ.get("GITHUB_EVENT_NAME") == "schedule" and state.get("last") == TODAY:
    print("NIST video already posted today; skipping.")
    raise SystemExit(0)

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

ig.publish("REELS", url, v["caption"], first_comment=ig.first_comment("nist", v.get("id", "")))
print(f"Posted NIST video: {v['title']}")
state["posted"].append(v["id"])
state["last"] = TODAY
STATE_FILE.parent.mkdir(exist_ok=True)
STATE_FILE.write_text(json.dumps(state, indent=2))
