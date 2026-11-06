"""Turn a reposted fire clip into a StationHQ "Size-up" post.

Instagram (2026) stops recommending accounts that mostly re-upload other people's videos
"without material changes", but counts clips you meaningfully edit with your own context
text or informational graphics as original. So every repost gets:

  - a size-up question burned into the top of the video (the hook, visible with sound off),
  - a context line (incident / place, taken from the creator's caption),
  - a credit bar at the bottom ("Video: @creator | StationHQ"),
  - a tighter cut (best 30 s of fire; 15-30 s Reels get the widest reach),
  - a caption that leads with the question, asks for comments and sends, and uses 5 hashtags.
"""
import hashlib
import pathlib
import re
import subprocess

MAX_SECONDS = 30
TITLE_SECONDS = 3  # the size-up question fades out after this

QUESTIONS = [
    "What's your size-up?",
    "First due: what's your first move?",
    "Offensive or defensive?",
    "Where's this fire going next?",
    "What's the smoke telling you?",
    "Where does the first line go?",
    "What's your report on arrival?",
    "Where do you put the truck?",
    "Search or fire attack first?",
    "What would you call for?",
]
VEHICLE_QUESTIONS = ["How do you attack this one?", "What's your first move?", "Where do you position?"]
RESPONSE_QUESTIONS = ["Where are they headed?", "Rate this response 1-10", "Who's first due here?"]

FONT_PATHS = [
    str(pathlib.Path(__file__).resolve().parent.parent / "brand" / "fonts" / "DejaVuSans-Bold.ttf"),
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
]


def _font():
    for p in FONT_PATHS:
        if pathlib.Path(p).exists():
            return p
    r = subprocess.run(["fc-match", "-f", "%{file}", "sans:bold"], capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 and r.stdout.strip() else None


def _clean(text):
    text = re.sub(r"[#@][\w.]+", "", text or "")
    text = re.sub(r"https?://\S+", "", text)
    text = "".join(ch for ch in text if ord(ch) < 0x2000)  # drop emoji (the font can't draw them)
    return re.sub(r"\s+", " ", text).strip(" -|·.,")


def context_line(caption, limit=34):
    """Short incident/place line from the creator's caption, or '' if there's nothing useful."""
    first = re.split(r"(?<=[.!?])\s|\n", _clean(caption), maxsplit=1)[0]
    if len(first) < 4:
        return ""
    if len(first) > limit:
        first = first[:limit].rsplit(" ", 1)[0] + "..."
    return first


def question_for(code, caption):
    c = (caption or "").lower()
    pool = QUESTIONS
    if re.search(r"car fire|vehicle fire|mva|crash", c):
        pool = VEHICLE_QUESTIONS
    elif re.search(r"respond|arriving|en route|going on|pulling up", c) and not re.search(r"fire showing|working", c):
        pool = RESPONSE_QUESTIONS
    return pool[int(hashlib.md5(code.encode()).hexdigest(), 16) % len(pool)]


BRAND = pathlib.Path(__file__).resolve().parent.parent / "brand"
HEAVY = BRAND / "fonts" / "barlow-condensed-latin-800-normal.woff"
SEMI = BRAND / "fonts" / "barlow-condensed-latin-600-normal.woff"
RED = (198, 40, 40, 240)


def _dims(src):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "stream=width,height", "-of", "csv=p=0", str(src)], capture_output=True, text=True).stdout
    iw, ih = (int(x) for x in out.strip().split(",")[:2])
    w = min(1080, iw)
    h = int(round(ih * w / iw / 2)) * 2
    return w - w % 2, h


def _fit(draw, text, font_path, max_w, size, min_size):
    """Largest font (down to min_size) that fits text on <=2 lines within max_w. Returns (font, lines)."""
    from PIL import ImageFont
    words = text.split()
    while size >= min_size:
        f = ImageFont.truetype(str(font_path), size)
        if draw.textlength(text, font=f) <= max_w:
            return f, [text]
        for i in range(1, len(words)):  # best 2-line split
            l1, l2 = " ".join(words[:i]), " ".join(words[i:])
            if max(draw.textlength(l1, font=f), draw.textlength(l2, font=f)) <= max_w:
                return f, [l1, l2]
        size -= 4
    return ImageFont.truetype(str(font_path), min_size), [text]


def overlay_png(work, src, user, question):
    """Transparent PNG the size of the output video: StationHQ size-up banner up top, credit lower down,
    both kept inside Instagram's safe area (clear of the top bar and the caption/buttons)."""
    from PIL import Image, ImageDraw
    if not HEAVY.exists():
        return None
    w, h = _dims(src)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    pad = int(w * 0.022)
    # --- top: small black tab + red question banner ---
    tab_font, _ = _fit(d, "STATIONHQ SIZE-UP", SEMI, w, int(w * 0.03), 14)
    qf, lines = _fit(d, question.upper(), HEAVY, w * 0.88, int(w * 0.058), int(w * 0.04))
    asc, desc = qf.getmetrics()
    line_h = int((asc + desc) * 0.95)
    box_w = int(max(d.textlength(l, font=qf) for l in lines) + pad * 2)
    box_h = line_h * len(lines) + pad
    top = int(h * 0.12) if h > w else int(h * 0.07)
    x0 = (w - box_w) // 2
    tab_w = int(d.textlength("STATIONHQ SIZE-UP", font=tab_font) + pad * 1.2)
    ta, tdsc = tab_font.getmetrics()
    tab_h = int((ta + tdsc) * 1.15)
    d.rounded_rectangle([x0, top - tab_h + 6, x0 + tab_w, top + 6], radius=8, fill=(12, 12, 12, 235))
    d.text((x0 + pad * 0.6, top - tab_h + 6 + (tab_h - ta - tdsc) / 2), "STATIONHQ SIZE-UP",
           font=tab_font, fill=(255, 255, 255, 255))
    d.rounded_rectangle([x0, top, x0 + box_w, top + box_h], radius=10, fill=RED)
    y = top + pad // 2
    for l in lines:
        d.text(((w - d.textlength(l, font=qf)) / 2, y), l, font=qf, fill=(255, 255, 255, 255))
        y += line_h
    title = pathlib.Path(work) / "title.png"
    img.save(title)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # --- credit: logo + "VIDEO: @user" in a dark pill ---
    cf, _ = _fit(d, f"VIDEO: @{user}", SEMI, w * 0.6, int(w * 0.036), 14)
    ca, cd = cf.getmetrics()
    ch = int((ca + cd) * 1.35)
    logo = Image.open(BRAND / "logo_badge.png").convert("RGBA")
    logo = logo.resize((int(ch * 0.95 * logo.width / logo.height), int(ch * 0.95)))
    text = f"VIDEO: @{user}"
    cw = int(logo.width + pad * 0.5 + d.textlength(text, font=cf) + pad * 1.2)
    cy = int(h * 0.70) if h > w else int(h * 0.80)
    cx = (w - cw) // 2
    d.rounded_rectangle([cx, cy, cx + cw, cy + ch], radius=ch // 2, fill=(0, 0, 0, 170))
    img.alpha_composite(logo, (cx + int(pad * 0.35), cy + (ch - logo.height) // 2))
    d.text((cx + int(pad * 0.35) + logo.width + int(pad * 0.4), cy + (ch - ca - cd) / 2), text,
           font=cf, fill=(255, 255, 255, 255))
    credit = pathlib.Path(work) / "credit.png"
    img.save(credit)
    return (title, credit), (w, h)


def caption_for(user, question, context, permalink):
    lines = [f"🔥 {question}"]
    lines += [
        f"🎥 @{user} (give them a follow)",
        "Drop your size-up in the comments 👇 and send this to someone on your crew.",
        f"Original: {permalink}",
        "#firefighter #fireground #structurefire #firedepartment #stationhq",
    ]
    return "\n\n".join(lines)


def make_sizeup(src, out, work, user, code, caption, has_audio=True):
    """Re-encode src -> out: best 30 s, size-up graphics on. Returns (question, context, transformed)."""
    import firecut
    question, context = question_for(code, caption), ""
    total = firecut.duration(src)
    start = firecut.best_window(src, MAX_SECONDS) if total > MAX_SECONDS + 1 else 0
    length = min(MAX_SECONDS, total - start)
    audio = ["-map", "0:a:0?", "-c:a", "aac", "-b:a", "128k", "-ar", "44100", "-ac", "2"] if has_audio else ["-an"]
    enc = ["-c:v", "libx264", "-profile:v", "high", "-pix_fmt", "yuv420p", "-preset", "veryfast", "-b:v", "4M",
           "-maxrate", "4.5M", "-bufsize", "9M", "-g", "60", *audio, "-movflags", "+faststart", str(out)]
    ov = None
    try:
        ov = overlay_png(work, src, user, question)
    except Exception as e:
        print(f"Size-up graphics failed ({e}); posting the plain cut")
    base = ["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{start:.2f}", "-t", f"{length:.2f}", "-i", str(src)]
    if ov:
        (title, credit), (w, h) = ov
        # the question shows for the first TITLE_SECONDS, then fades out; the credit stays on
        cmd = base + ["-loop", "1", "-t", f"{length:.2f}", "-i", str(title), "-i", str(credit), "-filter_complex",
                      f"[0:v]scale={w}:{h},fps=30[v];"
                      f"[1:v]format=rgba,fade=t=out:st={TITLE_SECONDS}:d=0.8:alpha=1[t];"
                      f"[v][t]overlay=0:0:shortest=1[vt];[vt][2:v]overlay=0:0[o]", "-map", "[o]", *enc]
    else:
        cmd = base + ["-map", "0:v:0", "-vf", "scale='min(1080,iw)':-2,fps=30", *enc]
    subprocess.run(cmd, check=True)
    print(f"Size-up: '{question}' | {length:.0f}s from {start:.0f}s | graphics {'on' if ov else 'OFF'}")
    return question, context, bool(ov)
