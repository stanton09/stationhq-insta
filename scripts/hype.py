"""Beat-cut "hype edit" of a StationHQ post: fast cuts of real live-fire photos (DVIDS, public domain) with
punch zooms, white flashes, split screens, a picture-in-picture inset, glitch and blur transitions. The post's
lines slam on screen one at a time and it ends on the post's own end card. Music is added by Instagram at publish.

    python hype.py <slug>        e.g. 05_grouptexts  (reads content/hype/<slug>.json)
Writes content/hype/<slug>.mp4 and prints a preview URL."""
import io
import json
import os
import pathlib
import random
import re
import subprocess
import sys
import tempfile
import urllib.request

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import media_host  # noqa: E402
from safety import api  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
HEAVY = ROOT / "brand" / "fonts" / "barlow-condensed-latin-800-normal.woff"
SEMI = ROOT / "brand" / "fonts" / "barlow-condensed-latin-600-normal.woff"
W, H, FPS = 1080, 1920, 30
BEAT = 12  # frames per beat (0.4 s, ~150 bpm)
RED = (230, 40, 35)
QUERIES = ["firefighters structure fire", "live fire training firefighters", "firefighters battle fire",
           "aircraft rescue firefighting live fire", "firefighter hose flames", "firefighters extinguish fire",
           "fire truck ladder firefighters", "firefighter turnout gear helmet"]
BAD = re.compile(r"weapon|rifle|pistol|grenade|explosive|ordnance|range|wildland|wildfire|prescribed|"
                 r"controlled burn|forest fire|brush fire|memorial|funeral|casualt|injur|killed", re.I)
random.seed(int(os.environ.get("SEED", "7")))


def fetch_photos(n=12):
    out, seen = [], set()
    for q in QUERIES:
        for r in api("search", q=q, type="image", sort="score", max_results=25).get("results", []):
            if r["id"] in seen or BAD.search((r.get("title") or "") + " " + (r.get("description") or "")):
                continue
            seen.add(r["id"])
            a = api("asset", id=r["id"]).get("results") or {}
            a = (a[0] if a else {}) if isinstance(a, list) else a
            url = a.get("image")
            if not url or BAD.search(a.get("description") or ""):
                continue
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "stationhq-bot"})
                im = Image.open(io.BytesIO(urllib.request.urlopen(req, timeout=60).read())).convert("RGB")
            except Exception:  # noqa: BLE001
                continue
            if min(im.size) < 900:
                continue
            print(f"photo {r['id']}: {(a.get('title') or '')[:70]}")
            out.append(im)
            break  # one per query keeps variety
        if len(out) >= n:
            break
    return out


def cover(im, w, h, zoom=1.0, dx=0.0, dy=0.0):
    s = max(w / im.width, h / im.height) * zoom
    rw, rh = int(im.width * s), int(im.height * s)
    im = im.resize((rw, rh), Image.BILINEAR)
    x = int((rw - w) / 2 + dx * (rw - w) / 2)
    y = int((rh - h) / 2 + dy * (rh - h) / 2)
    return im.crop((max(0, x), max(0, y), max(0, x) + w, max(0, y) + h))


def grade(im):
    """Punchy, warm, a little crushed: makes the fire pop."""
    r, g, b = im.split()
    r = r.point(lambda v: min(255, int(v * 1.12)))
    b = b.point(lambda v: int(v * 0.9))
    im = Image.merge("RGB", (r, g, b))
    return im.point(lambda v: max(0, min(255, int((v - 128) * 1.18 + 128))))


def rgb_split(im, px):
    r, g, b = im.split()
    return Image.merge("RGB", (ImageChops.offset(r, px, 0), g, ImageChops.offset(b, -px, 0)))


NOISE = [Image.effect_noise((W // 2, H // 2), 40).resize((W, H)).convert("RGB") for _ in range(4)]


def text_block(lines, size, red_idx=(), y=None, num=None, pop=1.0):
    """Big centered slam text with a dark shadow; lines in red_idx are red."""
    layer = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(layer)
    f = ImageFont.truetype(str(HEAVY), int(size * pop))
    lh = int(size * pop * 1.02)
    total = lh * len(lines) + (int(size * 0.55) if num else 0)
    y = (H - total) // 2 - 80 if y is None else y
    if num:
        nf = ImageFont.truetype(str(HEAVY), int(size * 0.5))
        tw = d.textlength(num, font=nf)
        d.rounded_rectangle(((W - tw) / 2 - 22, y - 6, (W + tw) / 2 + 22, y + int(size * 0.5) + 10), 10, fill=RED)
        d.text(((W - tw) / 2, y - 4), num, font=nf, fill="white")
        y += int(size * 0.55) + 24
    shadow = Image.new("RGBA", (W, H))
    sd = ImageDraw.Draw(shadow)
    for i, ln in enumerate(lines):
        tw = d.textlength(ln, font=f)
        x = (W - tw) / 2
        sd.text((x + 6, y + i * lh + 8), ln, font=f, fill=(0, 0, 0, 230))
        d.text((x, y + i * lh), ln, font=f, fill=RED if i in red_idx else "white")
    shadow = shadow.filter(ImageFilter.GaussianBlur(10))
    return Image.alpha_composite(shadow, layer)


def watermark():
    layer = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(layer)
    f = ImageFont.truetype(str(SEMI), 34)
    d.text((60, 120), "STATION", font=f, fill=(255, 255, 255, 220))
    d.text((60 + d.textlength("STATION ", font=f), 120), "HQ", font=f, fill=RED + (230,))
    cf = ImageFont.truetype(str(SEMI), 24)
    d.text((60, H - 330), "PHOTOS: DVIDS", font=cf, fill=(255, 255, 255, 150))
    return layer


def last_frame(slug, work):
    src = ROOT / "content" / "queue" / f"{slug}.mp4"
    if not src.exists():
        img = ROOT / "content" / "queue" / f"{slug}.jpg"
        return cover(Image.open(img).convert("RGB"), W, H)
    out = work / "end.png"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-sseof", "-0.2", "-i", str(src), "-frames:v", "1",
                    "-update", "1", str(out)], check=True)
    return cover(Image.open(out).convert("RGB"), W, H)


def build(slug):
    spec = json.loads((ROOT / "content" / "hype" / f"{slug}.json").read_text())
    work = pathlib.Path(tempfile.mkdtemp())
    photos = [grade(p) for p in fetch_photos()]
    if len(photos) < 6:
        raise SystemExit(f"Only {len(photos)} usable photos found")
    end = last_frame(slug, work)
    wm = watermark()
    frames = []  # list of callables -> one PIL frame each
    pi = iter(range(10_000))

    def nxt():
        return photos[next(pi) % len(photos)]

    def shot(n, kind, text=None, flash=True):
        a, b = nxt(), nxt()
        dx, dy = random.uniform(-0.6, 0.6), random.uniform(-0.4, 0.4)
        for i in range(n):
            t = i / max(1, n - 1)
            if kind == "punch":
                fr = cover(a, W, H, 1.28 - 0.18 * min(1, t * 3), dx, dy)
            elif kind == "drift":
                fr = cover(a, W, H, 1.08 + 0.10 * t, dx * (1 - t), dy)
            elif kind == "split":
                fr = Image.new("RGB", (W, H))
                fr.paste(cover(a, W, H // 2, 1.1 - 0.08 * t, dx, 0), (0, 0))
                fr.paste(cover(b, W, H // 2, 1.02 + 0.08 * t, -dx, 0), (0, H // 2))
                ImageDraw.Draw(fr).rectangle((0, H // 2 - 4, W, H // 2 + 4), fill="black")
            elif kind == "pip":
                fr = cover(a, W, H, 1.15 + 0.05 * t, dx, dy).filter(ImageFilter.GaussianBlur(14))
                iw, ih = 820, 1040
                inset = cover(b, iw, ih, 1.15 - 0.1 * t)
                mask = Image.new("L", (iw, ih))
                ImageDraw.Draw(mask).rounded_rectangle((0, 0, iw, ih), 28, fill=255)
                sc = 0.86 + 0.14 * min(1, t * 4)
                inset = inset.resize((int(iw * sc), int(ih * sc)))
                mask = mask.resize(inset.size)
                fr.paste(inset, ((W - inset.width) // 2, (H - inset.height) // 2 - 60), mask)
            else:  # "blur": whip in from a blur
                fr = cover(a, W, H, 1.2 - 0.1 * t, dx, dy)
                if i < 6:
                    fr = fr.filter(ImageFilter.GaussianBlur(28 * (1 - i / 6)))
            if i < 3:  # shake on the hit
                fr = ImageChops.offset(fr, random.randint(-18, 18), random.randint(-18, 18))
            if flash and i < 4:
                fr = Image.blend(fr, Image.new("RGB", (W, H), "white"), [0.85, 0.5, 0.25, 0.1][i])
            if kind in ("blur", "punch") and i in (1, 2):
                fr = rgb_split(fr, 14)
            frames.append((fr, text, i))

    title = spec["title"]
    shot(BEAT, "punch", (title[0], 0))
    shot(BEAT, "blur", (title[0], 1))
    shot(BEAT, "split", (title[1], 2))
    shot(BEAT, "punch", (title[1], 3))
    kinds = ["drift", "split", "pip", "punch"]
    for k, line in enumerate(spec["lines"]):
        shot(BEAT * 2, kinds[k % 4], ({"lines": line, "num": f"{k + 1:02d}"}, 0))
        shot(BEAT * 2, kinds[(k + 2) % 4], ({"lines": line, "num": f"{k + 1:02d}"}, 1), flash=False)
    for _ in range(4):  # quick-fire montage into the end card
        shot(BEAT // 2, random.choice(["punch", "blur"]))

    raw = work / "hype_raw.mp4"
    enc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                            "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-f", "lavfi", "-i",
                            "anullsrc=r=44100:cl=stereo", "-shortest", "-c:v", "libx264", "-preset", "veryfast",
                            "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-movflags", "+faststart",
                            str(raw)], stdin=subprocess.PIPE)
    for n, (fr, text, i) in enumerate(frames):
        fr = Image.blend(fr, NOISE[n % 4], 0.06).convert("RGBA")
        if text:
            spec_t, part = text
            pop = 1.18 - 0.18 * min(1, i / 4)
            if isinstance(spec_t, dict):
                lay = text_block(spec_t["lines"], 118, red_idx=(), num=spec_t["num"], pop=pop if part == 0 else 1.0)
            else:
                lay = text_block(spec_t, 150, red_idx=range(len(spec_t)) if part >= 2 else (), pop=pop)
            fr = Image.alpha_composite(fr, lay)
        fr = Image.alpha_composite(fr, wm).convert("RGB")
        enc.stdin.write(fr.tobytes())
    for i in range(int(FPS * 2.6)):  # end card: flash, then a slow push-in
        fr = cover(end, W, H, 1.0 + 0.04 * i / (FPS * 2.6))
        if i < 5:
            fr = Image.blend(fr, Image.new("RGB", (W, H), "white"), 0.8 - 0.16 * i)
        enc.stdin.write(fr.tobytes())
    enc.stdin.close()
    if enc.wait():
        raise SystemExit("ffmpeg failed")
    out = ROOT / "content" / "hype" / f"{slug}.mp4"
    out.write_bytes(raw.read_bytes())
    print(f"Built {out.name}: {(len(frames) + int(FPS * 2.6)) / FPS:.1f}s")
    print("Preview:", media_host.host_file(out, work))


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else "05_grouptexts")
