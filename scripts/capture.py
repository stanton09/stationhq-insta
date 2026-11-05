"""Download clips captured from approved pages (content/captures_in.json, collected in the browser),
cut each to its best 60 s of fire, and store them as assets on the GitHub release `captures`.

Clips with an Instagram song are stored muted (music=true) and wait for Instagram's own music
(Audio API) before they post. state/captures.json tracks every stored clip.
"""
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import firecut  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
IN_FILE = ROOT / "content" / "captures_in.json"
STATE_FILE = ROOT / "state" / "captures.json"
TAG = "captures"
MAX_SECONDS = 60

state = json.loads(STATE_FILE.read_text()) if STATE_FILE.exists() else {"clips": {}}
items = json.loads(IN_FILE.read_text()) if IN_FILE.exists() else []
if not items:
    print("Nothing to capture.")
    raise SystemExit(0)

env = dict(os.environ, GH_TOKEN=os.environ.get("GH_TOKEN", ""))
if subprocess.run(["gh", "release", "view", TAG], env=env, capture_output=True).returncode != 0:
    subprocess.run(["gh", "release", "create", TAG, "--title", "Captured clips",
                    "--notes", "Clips from approved pages, cut and ready to post."], env=env, check=True)

for it in items:
    key = f"{it['user']}_{it['code']}"
    if key in state["clips"]:
        print(f"{key}: already stored")
        continue
    work = pathlib.Path(tempfile.mkdtemp())
    raw, out = work / "raw.mp4", work / f"{key}.mp4"
    try:
        req = urllib.request.Request(it["url"], headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=180) as r:
            raw.write_bytes(r.read())
    except Exception as e:
        print(f"{key}: download failed ({e})")
        continue
    total = firecut.duration(raw)
    start = firecut.best_window(raw, MAX_SECONDS)
    length = min(MAX_SECONDS, total - start)
    audio = ["-an"] if it["music"] else ["-map", "0:a:0?", "-c:a", "aac", "-b:a", "128k", "-ar", "44100", "-ac", "2"]
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{start:.2f}", "-t", f"{length:.2f}", "-i", str(raw),
           "-map", "0:v:0", "-vf", "scale='min(1080,iw)':-2,fps=30", "-c:v", "libx264", "-profile:v", "high",
           "-pix_fmt", "yuv420p", "-preset", "veryfast", "-b:v", "4M", "-maxrate", "4.5M", "-bufsize", "9M",
           "-g", "60", *audio, "-movflags", "+faststart", str(out)]
    subprocess.run(cmd, check=True)
    subprocess.run(["gh", "release", "upload", TAG, str(out), "--clobber"], env=env, check=True)
    state["clips"][key] = {
        "user": it["user"], "code": it["code"], "caption": it.get("cap", "")[:300],
        "permalink": f"https://www.instagram.com/reel/{it['code']}/",
        "music": bool(it["music"]), "seconds": round(length), "source_seconds": round(total),
        "start": round(start), "asset": out.name, "posted": False,
    }
    print(f"{key}: stored {length:.0f}s (from {start:.0f}s of {total:.0f}s), "
          f"{'muted (had Instagram music)' if it['music'] else 'with sound'}, "
          f"{out.stat().st_size // 1024} KB")
    STATE_FILE.parent.mkdir(exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))

# the Instagram file links expire within a day or two; don't keep them around
IN_FILE.unlink()
print(f"{sum(1 for c in state['clips'].values() if not c['posted'])} clips waiting to post")
