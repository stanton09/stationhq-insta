"""Download a Reel, re-encode it to Instagram's publishing spec, and host it at a public raw GitHub URL.

Instagram often refuses to publish video straight from its own CDN links, so we:
  1. download the original video,
  2. re-encode with ffmpeg (H.264 + AAC, faststart, <=5 Mbps, <=1080 wide, 30 fps),
  3. force-push it as the only file on the orphan branch `media`
     (so the repo never grows), and return its raw.githubusercontent.com URL.
"""
import os
import pathlib
import subprocess
import tempfile
import time
import urllib.request

REPO = os.environ.get("GITHUB_REPOSITORY", "stanton09/stationhq-insta")


class NoAudio(Exception):
    """The source video has no sound track."""


def _has_audio(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries",
                        "stream=codec_type", "-of", "csv=p=0", str(path)],
                       capture_output=True, text=True)
    return "audio" in r.stdout


def _run(*cmd, cwd=None):
    subprocess.run(cmd, cwd=cwd, check=True)


def prepare_video(source_url, media_id):
    work = pathlib.Path(tempfile.mkdtemp())
    raw_in, out = work / "in.mp4", work / f"{media_id}.mp4"
    req = urllib.request.Request(source_url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=120) as r:
        raw_in.write_bytes(r.read())
    if not _has_audio(raw_in):
        raise NoAudio(f"{media_id} has no sound")
    _run("ffmpeg", "-y", "-loglevel", "error", "-i", str(raw_in), "-map", "0:v:0", "-map", "0:a:0",
         "-vf", "scale='min(1080,iw)':-2,fps=30", "-c:v", "libx264", "-profile:v", "high",
         "-pix_fmt", "yuv420p", "-preset", "veryfast", "-b:v", "4M", "-maxrate", "4.5M",
         "-bufsize", "9M", "-g", "60", "-c:a", "aac", "-b:a", "128k", "-ar", "44100", "-ac", "2",
         "-movflags", "+faststart", str(out))

    url = host_file(out, work)
    if not _has_audio(out):
        raise NoAudio(f"{media_id} lost its sound while converting")
    print(f"Hosted video at {url} ({out.stat().st_size // 1024} KB, with sound)")
    return url


def host_file(out, work=None):
    """Force-push a finished file as the only file on the orphan `media` branch; return raw URL."""
    work = pathlib.Path(work or tempfile.mkdtemp())
    out = pathlib.Path(out)
    branch_dir = work / "media"
    branch_dir.mkdir()
    remote = subprocess.run(["git", "remote", "get-url", "origin"], capture_output=True,
                            text=True, check=True).stdout.strip()
    _run("git", "init", "-q", "-b", "media", cwd=branch_dir)
    _run("git", "config", "user.name", "stationhq-bot", cwd=branch_dir)
    _run("git", "config", "user.email", "actions@users.noreply.github.com", cwd=branch_dir)
    # Reuse the checkout's auth header so the push is allowed.
    extra = subprocess.run(["git", "config", "--get-regexp", r"http\..*\.extraheader"],
                           capture_output=True, text=True).stdout.split(None, 1)
    if len(extra) == 2:
        _run("git", "config", extra[0], extra[1].strip(), cwd=branch_dir)
    (branch_dir / out.name).write_bytes(out.read_bytes())
    _run("git", "add", out.name, cwd=branch_dir)
    _run("git", "commit", "-q", "-m", f"media {out.stem}", cwd=branch_dir)
    _run("git", "push", "-q", "-f", remote, "media", cwd=branch_dir)

    url = f"https://raw.githubusercontent.com/{REPO}/media/{out.name}"
    for _ in range(12):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, method="HEAD"), timeout=20) as r:
                if r.status == 200:
                    break
        except Exception:
            pass
        time.sleep(5)
    return url
