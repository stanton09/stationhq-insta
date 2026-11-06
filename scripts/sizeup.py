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


def _write(work, name, text):
    p = pathlib.Path(work) / name
    p.write_text(text)
    return str(p).replace("\\", "/").replace(":", r"\:")


def overlay_filter(work, user, question, context):
    """ffmpeg -vf fragment that draws the size-up graphics, or None if no font is available."""
    font = _font()
    if not font:
        return None
    f = font.replace(":", r"\:")
    q = _write(work, "q.txt", question.upper())
    parts = [
        f"drawtext=fontfile='{f}':textfile='{q}':fontcolor=white:fontsize=w/17:"
        f"box=1:boxcolor=0xB71C1C@0.92:boxborderw=w/45:x=(w-text_w)/2:y=h*0.07",
    ]
    if context:
        c = _write(work, "c.txt", f"SIZE-UP  |  {context}")
        parts.append(
            f"drawtext=fontfile='{f}':textfile='{c}':fontcolor=white:fontsize=w/32:"
            f"box=1:boxcolor=black@0.6:boxborderw=w/80:x=(w-text_w)/2:y=h*0.07+w/17+w/14")
    cr = _write(work, "cr.txt", f"Video: @{user}  |  StationHQ")
    parts.append(
        f"drawtext=fontfile='{f}':textfile='{cr}':fontcolor=white:fontsize=w/30:"
        f"box=1:boxcolor=black@0.6:boxborderw=w/80:x=(w-text_w)/2:y=h*0.90")
    return ",".join(parts)


def caption_for(user, question, context, permalink):
    lines = [f"🔥 {question}"]
    if context:
        lines.append(context)
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
    question, context = question_for(code, caption), context_line(caption)
    total = firecut.duration(src)
    start = firecut.best_window(src, MAX_SECONDS) if total > MAX_SECONDS + 1 else 0
    length = min(MAX_SECONDS, total - start)
    vf = "scale='min(1080,iw)':-2,fps=30"
    ov = overlay_filter(work, user, question, context)
    if ov:
        vf += "," + ov
    audio = ["-map", "0:a:0?", "-c:a", "aac", "-b:a", "128k", "-ar", "44100", "-ac", "2"] if has_audio else ["-an"]
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{start:.2f}", "-t", f"{length:.2f}", "-i", str(src),
           "-map", "0:v:0", "-vf", vf, "-c:v", "libx264", "-profile:v", "high", "-pix_fmt", "yuv420p",
           "-preset", "veryfast", "-b:v", "4M", "-maxrate", "4.5M", "-bufsize", "9M", "-g", "60",
           *audio, "-movflags", "+faststart", str(out)]
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError:
        if not ov:
            raise
        print("Size-up graphics failed; posting the plain cut")
        cmd[cmd.index("-vf") + 1] = "scale='min(1080,iw)':-2,fps=30"
        subprocess.run(cmd, check=True)
        ov = None
    print(f"Size-up: '{question}' | '{context}' | {length:.0f}s from {start:.0f}s | graphics {'on' if ov else 'OFF'}")
    return question, context, bool(ov)
