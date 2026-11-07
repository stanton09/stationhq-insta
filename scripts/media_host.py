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


MAX_SECONDS = 60


def prepare_video(source_url, media_id, sizeup_info=None):
    """sizeup_info=(user, code, caption) adds StationHQ featured-crew graphics and a 30 s cut."""
    work = pathlib.Path(tempfile.mkdtemp())
    raw_in, out = work / "in.mp4", work / f"{media_id}.mp4"
    req = urllib.request.Request(source_url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=120) as r:
        raw_in.write_bytes(r.read())
    if not _has_audio(raw_in):
        raise NoAudio(f"{media_id} has no sound")
    if sizeup_info:
        import sizeup
        sizeup.make_sizeup(raw_in, out, work, *sizeup_info)
        url = host_file(out, work)
        if not _has_audio(out):
            raise NoAudio(f"{media_id} lost its sound while converting")
        print(f"Hosted featured-crew video at {url} ({out.stat().st_size // 1024} KB)")
        return url
    # Reposts use at most 60 s: the stretch with the most fire (keeps the file well under GitHub's 100 MB).
    import firecut
    start = firecut.best_window(raw_in, MAX_SECONDS)
    if firecut.duration(raw_in) > MAX_SECONDS + 1:
        print(f"Long video: using {start:.0f}-{start + MAX_SECONDS:.0f}s")
    _run("ffmpeg", "-y", "-loglevel", "error", "-ss", f"{start:.2f}", "-t", str(MAX_SECONDS),
         "-i", str(raw_in), "-map", "0:v:0", "-map", "0:a:0",
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
    for attempt in range(5):  # GitHub sometimes returns 500s; retry before giving up
        try:
            _run("git", "push", "-q", "-f", remote, "media", cwd=branch_dir)
            break
        except subprocess.CalledProcessError:
            if attempt == 4:
                raise
            time.sleep(20 * (attempt + 1))

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


def prepare_image(source_url, media_id):
    """Download a photo, fit it to Instagram's 4:5 portrait (blurred fill), save as JPEG and host it."""
    from PIL import Image, ImageFilter
    work = pathlib.Path(tempfile.mkdtemp())
    raw_in, out = work / "in.img", work / f"{media_id}.jpg"
    req = urllib.request.Request(source_url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=120) as r:
        raw_in.write_bytes(r.read())
    im = Image.open(raw_in).convert("RGB")
    W, H = 1080, 1350
    ratio = im.width / im.height
    if 0.8 <= ratio <= 1.91:  # already inside Instagram's allowed range
        fitted = im.resize((1080, round(1080 / ratio)))
        if fitted.height > 1350:
            fitted = im.resize((round(1350 * ratio), 1350))
        canvas = fitted
    else:  # too tall: put it on a blurred 4:5 background
        bg = im.resize((W, round(W / ratio))).crop((0, 0, W, H)).filter(ImageFilter.GaussianBlur(30))
        fg = im.resize((round(H * ratio), H))
        bg.paste(fg, ((W - fg.width) // 2, 0))
        canvas = bg
    canvas.save(out, "JPEG", quality=92)
    url = host_file(out, work)
    print(f"Hosted photo at {url}")
    return url
