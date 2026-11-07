"""Seasonal fire-safety posts (photo posts, plus animated explainer Reels from design/explainer.js) that look like a real department's post, not a template:
a real public-domain photo (DVIDS) full-bleed, one short headline, a small StationHQ mark.

  python safety.py build   -> make content/safety/<day>_<slug>.jpg + .txt for topics without an image
  python safety.py post    -> post the oldest due one (day <= today) not yet posted
"""
import datetime as dt
import io
import json
import os
import pathlib
import sys
import urllib.parse
import urllib.request

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = pathlib.Path(__file__).resolve().parent.parent
DIR = ROOT / "content" / "safety"
STATE = ROOT / "state" / "safety.json"
BRAND = ROOT / "brand"
HEAVY = BRAND / "fonts" / "barlow-condensed-latin-800-normal.woff"
SEMI = BRAND / "fonts" / "barlow-condensed-latin-600-normal.woff"
W, H = 1080, 1350
TAGS = "#firesafety #fireprevention #firedepartment #firefighter #stationhq"
API = "https://api.dvidshub.net"


def api(path, **params):
    params["api_key"] = os.environ["DVIDS_API_KEY"]
    url = f"{API}/{path}?{urllib.parse.urlencode(params, doseq=True)}"
    req = urllib.request.Request(url, headers={"User-Agent": "stationhq-bot", "Origin": "https://stationhq.app"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def find_photo(queries, used):
    for q in queries:
        res = api("search", q=q, type="image", sort="score", max_results=25).get("results", [])
        for r in res:
            if r["id"] in used:
                continue
            a = api("asset", id=r["id"]).get("results") or {}
            if isinstance(a, list):
                a = a[0] if a else {}
            url = a.get("image")
            w, h = int(a.get("dimensions", {}).get("width") or 0), int(a.get("dimensions", {}).get("height") or 0)
            if url and (w == 0 or w >= 1000):
                return r["id"], url, a
    return None, None, None


def wrap(d, text, font, max_w):
    words, lines, cur = text.split(), [], ""
    for w_ in words:
        t = (cur + " " + w_).strip()
        if d.textlength(t, font=font) <= max_w:
            cur = t
        else:
            lines.append(cur)
            cur = w_
    lines.append(cur)
    return lines


def render(photo_bytes, headline, credit):
    img = Image.open(io.BytesIO(photo_bytes)).convert("RGB")
    s = max(W / img.width, H / img.height)
    img = img.resize((int(img.width * s) + 1, int(img.height * s) + 1), Image.LANCZOS)
    x, y = (img.width - W) // 2, (img.height - H) // 2
    img = img.crop((x, y, x + W, y + H))
    # soft dark fade at the bottom for the text
    fade = Image.new("L", (1, H), 0)
    for i in range(H):
        t = min(1.0, max(0.0, (i - H * 0.38) / (H * 0.42)))
        fade.putpixel((0, i), int(240 * t ** 0.9))
    fade = fade.resize((W, H))
    black = Image.new("RGB", (W, H), (8, 8, 10))
    img = Image.composite(black, img, fade)
    d = ImageDraw.Draw(img)
    size = 104
    while size > 64:
        f = ImageFont.truetype(str(HEAVY), size)
        lines = wrap(d, headline, f, W - 150)
        if len(lines) <= 3:
            break
        size -= 6
    asc, desc = f.getmetrics()
    lh = int((asc + desc) * 0.92)
    y = H - 150 - lh * len(lines)
    d.rectangle([75, y - 34, 75 + 90, y - 26], fill=(198, 40, 40))
    for l in lines:
        d.text((75, y), l, font=f, fill=(255, 255, 255))
        y += lh
    small = ImageFont.truetype(str(SEMI), 30)
    logo = Image.open(BRAND / "logo_badge.png").convert("RGBA").resize((52, 53))
    img.paste(logo, (75, H - 92), logo)
    d.text((140, H - 84), "STATIONHQ", font=small, fill=(255, 255, 255))
    cf = ImageFont.truetype(str(SEMI), 22)
    d.text((W - 75 - d.textlength(credit, font=cf), H - 80), credit, font=cf, fill=(190, 190, 190))
    out = io.BytesIO()
    img.save(out, "JPEG", quality=90)
    return out.getvalue()


def candidates():
    """List photo options (id | title) for topics marked "pick": true, to choose photo_id by hand."""
    for t in json.loads((DIR / "topics.json").read_text()):
        if not t.get("pick"):
            continue
        seen = set()
        for q in t["q"]:
            for r in api("search", q=q, type="image", sort="score", max_results=15).get("results", []):
                if r["id"] not in seen:
                    seen.add(r["id"])
                    print(f"{t['slug']} | {r['id']} | {(r.get('title') or '')[:70]} | {(r.get('description') or '')[:90]}")


def build():
    topics = json.loads((DIR / "topics.json").read_text())
    used = set()
    for t in topics:
        name = f"{t['day']}_{t['slug']}"
        if (DIR / f"{name}.mp4").exists():
            continue  # this day is an animated explainer Reel (design/explainer.js), not a photo post
        if (DIR / f"{name}.jpg").exists() and not t.get("rebuild"):
            continue
        if t.get("photo_id"):
            pid = t["photo_id"]
            a = api("asset", id=pid).get("results") or {}
            a = a[0] if isinstance(a, list) and a else a
            url = a.get("image")
        else:
            pid, url, a = find_photo(t["q"], used)
        if not pid:
            print(f"{name}: no photo found")
            continue
        used.add(pid)
        req = urllib.request.Request(url, headers={"User-Agent": "stationhq-bot"})
        photo = urllib.request.urlopen(req, timeout=120).read()
        branch = a.get("branch") or "U.S. military"
        credit = f"Photo: {branch} / DVIDS"
        (DIR / f"{name}.jpg").write_bytes(render(photo, t["head"], credit))
        cap = (f"{t['cap']}\n\nShare this with your community.\n\n"
               f"Photo: {branch} via DVIDS (public domain). The appearance of U.S. Department of War (DoW) "
               f"visual information does not imply or constitute DoW endorsement.\n\n{TAGS}")
        (DIR / f"{name}.txt").write_text(cap)
        print(f"{name}: built from {pid} ({(a.get('title') or '')[:60]})")


def post():
    import ig
    state = json.loads(STATE.read_text()) if STATE.exists() else {"posted": []}
    today = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=5)).date().isoformat()
    if state.get("last") == today and not os.environ.get("FORCE"):
        print("Safety post already went out today")
        return
    due = sorted(p for p in DIR.iterdir() if p.suffix in (".jpg", ".mp4")
                 and p.stem[:10] <= today and p.stem not in state["posted"])
    if not due:
        print("No safety post due")
        return
    p = due[0]
    import media_host
    import shutil
    import tempfile
    work = pathlib.Path(tempfile.mkdtemp())
    shutil.copy(p, work / p.name)
    url = media_host.host_file(work / p.name, work)
    if os.environ.get("DRY_RUN"):
        print(f"[dry run] would post {p.name}: {url}")
        return
    if p.suffix == ".mp4":  # explainer Reel (also shared to the Story by ig.publish)
        ig.publish("REELS", url, p.with_suffix(".txt").read_text(), music="under",
                   first_comment=ig.first_comment("safety", p.stem))
    else:
        ig.publish("IMAGE", url, p.with_suffix(".txt").read_text(), first_comment=ig.first_comment("safety", p.stem))
    state["posted"].append(p.stem)
    state["last"] = today
    STATE.write_text(json.dumps(state, indent=2))
    print(f"Posted safety post {p.name}")


if __name__ == "__main__":
    {"build": build, "post": post, "candidates": candidates}[sys.argv[1]]()
