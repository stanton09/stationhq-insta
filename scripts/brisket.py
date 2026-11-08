"""Animated short: Captain Roy Brisket sends a drill change to the station group chat and it gets buried.
Loose black-ink cartoon, red only on his helmet (and StationHQ at the end). Writes brisket_groupchat.mp4."""
import math
import pathlib
import random
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = pathlib.Path(__file__).resolve().parent.parent
W, H, FPS = 1080, 1920, 30
INK, PAPER, RED, GRAY = (22, 22, 22), (250, 248, 243), (214, 38, 32), (150, 150, 150)
FD = pathlib.Path("/usr/share/fonts/opentype/inter")
F_LOCAL = ROOT / "brand" / "fonts"


def font(name, size):
    for p in (F_LOCAL / name, FD / name):
        if p.exists():
            return ImageFont.truetype(str(p), size)
    return ImageFont.truetype(str(F_LOCAL / "DejaVuSans-Bold.ttf"), size)


HEAVY = ImageFont.truetype(str(F_LOCAL / "barlow-condensed-latin-800-normal.woff"), 96)
CAP = font("Inter-Italic.otf", 40)
CHAT = font("Inter-Regular.otf", 46)
NAME = font("Inter-SemiBold.otf", 26)
HOOK = ImageFont.truetype(str(F_LOCAL / "barlow-condensed-latin-800-normal.woff"), 70)


class Pen:
    """Wobbly hand-drawn lines; the wobble re-rolls every few frames ("line boil")."""

    def __init__(self, d, seed):
        self.d, self.r = d, random.Random(seed)

    def j(self, v, a=2.2):
        return v + self.r.uniform(-a, a)

    def line(self, pts, w=5, fill=INK, closed=False):
        pts = list(pts) + ([pts[0]] if closed else [])
        out = []
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            n = max(2, int(math.hypot(x1 - x0, y1 - y0) / 28))
            for k in range(n):
                t = k / n
                out.append((self.j(x0 + (x1 - x0) * t), self.j(y0 + (y1 - y0) * t)))
        out.append((self.j(pts[-1][0]), self.j(pts[-1][1])))
        self.d.line(out, fill=fill, width=w, joint="curve")

    def rect(self, x0, y0, x1, y1, w=5, fill=None):
        if fill:
            self.d.rectangle((x0, y0, x1, y1), fill=fill)
        self.line([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], w, closed=True)

    def arc(self, cx, cy, rx, ry, a0, a1, w=5, fill=INK):
        pts = [(cx + rx * math.cos(math.radians(a)), cy + ry * math.sin(math.radians(a)))
               for a in range(int(a0), int(a1) + 1, 12)]
        self.line(pts, w, fill)



EPISODES = {
    "groupchat": dict(
        hook=("WHEN THE CAPTAIN CHANGES", "DRILL TIME IN THE GROUP CHAT\u2026"),
        msgs=[("Capt. Brisket", "Attention all personnel. Drill relocated to 1900 hours. Acknowledge receipt.", True),
              ("Kevin (probie)", "YES CAP!!!", False), ("Marco", "who took the good spatula", False),
              ("Donna", "costco run anyone?", False), ("Pete", "can someone cover my sunday", False),
              ("Marco", "SPATULA. NOW.", False), ("Donna", "lol", False),
              ("Kevin (probie)", "wait is drill tonight??", False)],
        mad="\u201cMessage status: buried. Cause: group text.\u201d",
        alert=("DRILL CHANGE", "Drill moved to 1900 hours.", "Tap to confirm."),
        rows=[(c, "Received") for c in ["Kevin", "Marco", "Donna", "Pete", "Sully", "Big Mike", "Rosa", "T.J."]], unit="received",
        verdict="\u201cReceipt rate: acceptable.\u201d",
        end=("ALERTS THAT DON'T", "GET BURIED."), music_start=0),
    "roster": dict(
        hook=("WHEN CAP POSTS THE SCHEDULE", "AS A PHOTO OF THE WHITEBOARD\u2026"),
        msgs=[("Capt. Brisket", "December schedule attached. IMG_4471.jpg. Know your shifts.", True),
              ("Kevin (probie)", "YES CAP!!!", False), ("Marco", "is that a 3 or an 8", False),
              ("Donna", "its sideways on my phone", False), ("Pete", "who's on christmas", False),
              ("Sully", "why is there a ketchup stain on it", False), ("Donna", "lol", False),
              ("Kevin (probie)", "wait am I working tonight??", False)],
        mad="\u201cSchedule status: unreadable. Cause: whiteboard photo.\u201d",
        alert=("SCHEDULE POSTED", "December shifts are live.", "Tap to see your shifts."),
        rows=[("Kevin", "Tonight"), ("Marco", "Fri 12/4"), ("Donna", "Sat 12/5"), ("Pete", "Thu 12/24"),
              ("Sully", "Fri 12/25"), ("Big Mike", "Mon 12/7"), ("Rosa", "Tue 12/8"), ("T.J.", "Wed 12/9")],
        unit="viewed",
        verdict="\u201cQuestions received: zero.\u201d",
        end=("SHIFTS THE WHOLE", "CREW CAN READ."), music_start=34),
    "dues": dict(
        hook=("WHEN THE CAPTAIN TRIES TO", "COLLECT DUES OVER TEXT\u2026"),
        msgs=[("Capt. Brisket", "Reminder: $20 dues due Friday. No exceptions.", True),
              ("Kevin (probie)", "YES CAP!!! sent", False), ("Marco", "whats your venmo again", False),
              ("Pete", "I paid in march", False), ("Sully", "can I pay in wings", False),
              ("Marco", "is it cash or", False), ("Donna", "lol", False),
              ("Kevin (probie)", "wait who did I send it to??", False)],
        mad="\u201cDues collected: $0. Excuses collected: 6.\u201d",
        alert=("DUES REMINDER", "$20 station dues due Friday.", "Tap to view."),
        rows=[(c, "Paid") for c in ["Kevin", "Marco", "Donna", "Pete", "Sully", "Big Mike", "Rosa", "T.J."]],
        unit="paid",
        verdict="\u201cCollection rate: acceptable.\u201d",
        end=("DUES TRACKING", "WITHOUT THE CHASE."), music_start=68),
    "rigcheck": dict(
        hook=("WHEN THE RIG CHECK", "CLIPBOARD GOES MISSING AGAIN\u2026"),
        msgs=[("Capt. Brisket", "Who has the rig check clipboard. Engine 1 is not signed off.", True),
              ("Kevin (probie)", "YES CAP!!!", False), ("Marco", "check the bathroom", False),
              ("Donna", "it had coffee on it last time", False), ("Pete", "I signed it yesterday I think", False),
              ("Sully", "is it the yellow one", False), ("Donna", "lol", False),
              ("Kevin (probie)", "wait whats a rig check??", False)],
        mad="\u201cRig check: unsigned. Clipboard: missing.\u201d",
        alert=("RIG CHECK DUE", "Engine 1 daily check.", "Tap to start."),
        rows=[(x, "Checked") for x in ["SCBA", "Irons", "Hose load", "Pump", "Lights", "Fuel", "Medical bag", "Radios"]],
        unit="checked",
        verdict="\u201cRig status: in service.\u201d",
        end=("RIG CHECKS THAT", "ACTUALLY GET DONE."), music_start=100),
}
EP = EPISODES.get(sys.argv[2] if len(sys.argv) > 2 else "groupchat", EPISODES["groupchat"])
MSGS = EP["msgs"]


def wrap(d, text, f, maxw):
    words, lines, cur = text.split(), [], ""
    for w_ in words:
        t = (cur + " " + w_).strip()
        if d.textlength(t, font=f) <= maxw:
            cur = t
        else:
            lines.append(cur)
            cur = w_
    return lines + [cur]


def chat(d, pen, x0, y0, x1, y1, shown, pop, typing):
    """The group chat on a big hand-drawn phone. Newest at the bottom; older ones scroll off the top."""
    pen.rect(x0, y0, x1, y1, 7, fill=(255, 255, 255))
    d.rectangle((x0 + 4, y0 + 4, x1 - 4, y0 + 92), fill=(244, 244, 244))
    t = "STATION 12 CREW  (14)"
    d.text(((x0 + x1) / 2 - d.textlength(t, font=NAME) / 2, y0 + 32), t, font=NAME, fill=INK)
    pen.line([(x0, y0 + 96), (x1, y0 + 96)], 4)
    inner_top, y = y0 + 110, y1 - 30
    items = list(range(shown))[::-1]
    if typing:  # Roy typing: dots bubble on his side of the chat
        d.rounded_rectangle((x1 - 170, y - 70, x1 - 30, y), 30, fill=(250, 210, 210))
        for k in range(3):
            a = 0.5 + 0.5 * math.sin(typing * 0.5 + k)
            r_ = 5 + 4 * a
            d.ellipse((x1 - 138 + k * 30 - r_, y - 35 - r_, x1 - 138 + k * 30 + r_, y - 35 + r_), fill=RED)
        y -= 90
    for idx in items:
        name, text, capt = MSGS[idx]
        lines = wrap(d, text, CHAT, (x1 - x0) * 0.62)
        bh = 44 + 58 * len(lines)
        bw = max(d.textlength(ln, font=CHAT) for ln in lines) + 60
        sc = pop if idx == shown - 1 else 1.0
        top = y - bh
        if top - 36 < inner_top:
            break
        bx = x1 - 30 - bw if capt else x0 + 30
        fill = RED if capt else (232, 232, 232)
        col = (255, 255, 255) if capt else INK
        if sc < 1:
            cxm, cym = bx + bw / 2, top + bh / 2
            d.rounded_rectangle((cxm - bw * sc / 2, cym - bh * sc / 2, cxm + bw * sc / 2, cym + bh * sc / 2), 34, fill=fill)
        else:
            d.rounded_rectangle((bx, top, bx + bw, top + bh), 34, fill=fill)
            for k, ln in enumerate(lines):
                d.text((bx + 30, top + 18 + k * 58), ln, font=CHAT, fill=col)
        d.text((bx + (bw - d.textlength(name, font=NAME) - 10 if capt else 10), top - 34), name, font=NAME, fill=GRAY)
        y = top - 52
    # clip anything above the header
    d.rectangle((x0 + 4, y0 + 4, x1 - 4, y0 + 92), fill=(244, 244, 244))
    t = "STATION 12 CREW  (14)"
    d.text(((x0 + x1) / 2 - d.textlength(t, font=NAME) / 2, y0 + 32), t, font=NAME, fill=INK)
    pen.line([(x0, y0 + 96), (x1, y0 + 96)], 4)


def caption(d, text, y=150):
    for k, ln in enumerate(wrap(d, text, CAP, W - 160)):
        d.text((W / 2 - d.textlength(ln, font=CAP) / 2, y + k * 54), ln, font=CAP, fill=INK)



CREW = ["Kevin", "Marco", "Donna", "Pete", "Sully", "Big Mike", "Rosa", "T.J."]
BOLD = font("Inter-Bold.otf", 44)
SMALL = font("Inter-Regular.otf", 32)


def check(d, x, y, sz, col):
    d.line([(x, y + sz * 0.5), (x + sz * 0.38, y + sz * 0.85), (x + sz, y + sz * 0.1)], fill=col, width=max(4, sz // 6))


def solution(im, d, t, roy_head, logo):
    """StationHQ: the drill change goes out as a push alert and the crew acknowledges it."""
    # banner
    d.rectangle((0, 120, W, 230), fill=RED)
    b = "NOW WITH STATIONHQ"
    d.text((W / 2 - d.textlength(b, font=HEAVY) / 2, 118), b, font=HEAVY, fill="white")
    # phone
    sh = int(14 * max(0, 1 - t / 0.9) * abs(math.sin(t * 60)))
    px0, py0, px1, py1 = 170 + sh, 290, W - 170 + sh, 1420
    d.rounded_rectangle((px0, py0, px1, py1), 70, fill=(24, 24, 28))
    d.rounded_rectangle((px0 + 22, py0 + 22, px1 - 22, py1 - 22), 52, fill=(238, 238, 242))
    d.rounded_rectangle((W / 2 - 80, py0 + 40, W / 2 + 80, py0 + 78), 19, fill=(24, 24, 28))
    # push notification slides down
    slide = min(1.0, t / 0.4)
    ny = py0 + 120 - int((1 - slide) ** 2 * 260)
    nx0, nx1 = px0 + 50, px1 - 50
    d.rounded_rectangle((nx0, ny, nx1, ny + 230), 36, fill="white", outline=(210, 210, 215), width=2)
    lg = logo.resize((80, 80))
    im.paste(lg, (nx0 + 28, ny + 26), lg)
    d.text((nx0 + 128, ny + 30), "STATIONHQ  \u00b7  now", font=NAME, fill=GRAY)
    d.text((nx0 + 128, ny + 66), EP["alert"][0], font=BOLD, fill=RED)
    d.text((nx0 + 30, ny + 130), EP["alert"][1], font=CHAT, fill=INK)
    d.text((nx0 + 30, ny + 178), EP["alert"][2], font=SMALL, fill=GRAY)
    # acknowledgments tick in, one every 0.45 s from t=1.2
    ROWS = EP["rows"]
    n = max(0, min(len(ROWS), int((t - 1.2) / 0.45) + 1)) if t >= 1.2 else 0
    total = 14
    count = min(total, n + (6 if n == len(ROWS) and t > 1.2 + 0.45 * len(CREW) else 0))
    ly = ny + 270
    head = f"{count} of {total} {EP['unit']}"
    d.text((nx0 + 10, ly), head, font=BOLD, fill=(30, 140, 70) if count == total else INK)
    d.rounded_rectangle((nx0 + 10, ly + 66, nx1 - 10, ly + 82), 8, fill=(215, 215, 220))
    if count:
        d.rounded_rectangle((nx0 + 10, ly + 66, nx0 + 10 + (nx1 - nx0 - 20) * count / total, ly + 82), 8,
                            fill=(30, 140, 70))
    for i in range(n):
        y = ly + 110 + i * 62
        check(d, nx0 + 18, y + 8, 34, (30, 140, 70))
        d.text((nx0 + 74, y), ROWS[i][0], font=CHAT, fill=INK)
        d.text((nx1 - 20 - d.textlength(ROWS[i][1], font=SMALL), y + 6), ROWS[i][1], font=SMALL, fill=GRAY)
    # Roy's verdict
    paste_c(im, roy_head, W / 2, 1590)
    if t > 5.0:
        caption(d, EP["verdict"], y=1470)


ROY = ROOT / "brand" / "roy"


def load(name, h):
    im = Image.open(ROY / f"{name}.png").convert("RGBA")
    return im.resize((int(im.width * h / im.height), h), Image.LANCZOS)


def paste_c(im, sprite, cx, top, sc=1.0):
    if sc != 1.0:
        sprite = sprite.resize((int(sprite.width * sc), int(sprite.height * sc)), Image.BICUBIC)
    im.paste(sprite, (int(cx - sprite.width / 2), int(top + (1 - sc) * sprite.height)), sprite)


SR = 44100


def sfx(total_s, events):
    """Synthesize the sound track: (time, kind) events -> 16-bit stereo wav bytes path."""
    import numpy as np
    import wave
    n = int(total_s * SR)
    mix = np.zeros(n)
    rng = np.random.default_rng(3)

    def put(t0, sig):
        i = int(t0 * SR)
        sig = sig[: max(0, n - i)]
        mix[i:i + len(sig)] += sig

    def sample(name, start, dur, vol):
        raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(start), "-t", str(dur), "-i", str(ROY / "sfx" / name),
                              "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"], capture_output=True).stdout
        a = np.frombuffer(raw, "<i2").astype(float) / 32768
        fl = min(len(a), int(0.04 * SR)); a[-fl:] *= np.linspace(1, 0, fl)
        return a * vol

    def tone(f0, f1, dur, wave_="sine", vol=0.5):
        tt = np.arange(int(dur * SR)) / SR
        f = np.linspace(f0, f1, len(tt))
        ph = 2 * np.pi * np.cumsum(f) / SR
        if wave_ == "saw":
            sig = sum(np.sin(k * ph) / k for k in range(1, 14))
        else:
            sig = np.sin(ph)
        return sig * vol

    for t, kind in events:
        if kind == "type":      # soft key click
            put(t, rng.normal(0, 1, int(0.012 * SR)) * np.linspace(0.25, 0, int(0.012 * SR)))
        elif kind == "send":    # whoosh
            d = int(0.35 * SR)
            noise = rng.normal(0, 1, d)
            env = np.sin(np.linspace(0, np.pi, d)) ** 2
            k = np.exp(-np.linspace(0, 6, 64)); k /= k.sum()
            put(t, np.convolve(noise, k, "same") * env * 0.6)
            put(t + 0.05, tone(700, 1400, 0.12, vol=0.15) * np.linspace(1, 0, int(0.12 * SR)))
        elif kind == "pop":     # incoming bubble
            d = 0.09
            env = np.exp(-np.linspace(0, 7, int(d * SR)))
            put(t, tone(1250, 820, d, vol=0.45) * env)
            put(t + 0.06, tone(1650, 1500, 0.07, vol=0.18) * np.exp(-np.linspace(0, 8, int(0.07 * SR))))
        elif kind == "thud":    # deadpan hit
            d = 0.6
            put(t, tone(90, 45, d, vol=0.9) * np.exp(-np.linspace(0, 5, int(d * SR))))
        elif kind == "scratch":  # cartoon record scratch: "wait... WHAT?"
            from scipy.signal import butter, lfilter
            for k, (d, f0, f1) in enumerate(((0.12, 900, 2600), (0.16, 2600, 700))):
                m = int(d * SR); nz = rng.normal(0, 1, m)
                fc = np.linspace(f0, f1, m); out = np.zeros(m)
                for j in range(0, m, 256):  # sweep a band-pass through the noise
                    seg = slice(j, min(m, j + 256)); c = fc[j]
                    bb, aa = butter(2, [c * 0.8 / (SR / 2), min(0.99, c * 1.25 / (SR / 2))], "band")
                    out[seg] = lfilter(bb, aa, nz[seg])
                env = np.minimum(1, np.linspace(0, 12, m)) * np.linspace(1, 0.3, m)
                put(t + k * 0.13, out / (np.abs(out).max() + 1e-9) * env * 0.5)
        elif kind == "steam":    # boiling over: cartoon kettle whistle + hiss, building up
            from scipy.signal import butter, lfilter
            d = 1.9; m = int(d * SR); tt = np.arange(m) / SR
            f = 1500 + 700 * (tt / d) ** 1.5 + 25 * np.sin(2 * np.pi * 9 * tt)
            whistle = np.sin(2 * np.pi * np.cumsum(f) / SR)
            bb, aa = butter(2, [3000 / (SR / 2), 9000 / (SR / 2)], "band")
            hiss = lfilter(bb, aa, rng.normal(0, 1, m)); hiss /= np.abs(hiss).max()
            env = (tt / d) ** 1.2 * np.minimum(1, (d - tt) / 0.08)
            put(t, (whistle * 0.16 + hiss * 0.22) * env)
        elif kind == "tada":    # happy ending: real "ta-da" fanfare (Pixabay, free license)
            put(t, sample("tada.mp3", 0, 2.4, 0.6))
        elif kind == "horn":    # app alert: real fire-truck air horn, "honk HONK" (Pixabay, free license)
            put(t, sample("horn2.mp3", 0, 1.3, 0.55))
        elif kind == "grrr1":   # Roy grumbles (real recording, Pixabay)
            put(t, sample("grrr.mp3", 0.15, 0.85, 0.9))
        elif kind == "grrr2":
            put(t, sample("grrr.mp3", 2.15, 0.7, 0.9))
        elif kind == "mic":     # voice-to-text start blip
            for k, f in enumerate((880, 1320)):
                put(t + k * 0.08, tone(f, f, 0.1, vol=0.2) * np.exp(-np.linspace(0, 6, int(0.1 * SR))))
        elif kind == "ring":    # US phone ring (440 + 480 Hz), one 1.0 s burst
            m = int(1.0 * SR); tt = np.arange(m) / SR
            sig = (np.sin(2 * np.pi * 440 * tt) + np.sin(2 * np.pi * 480 * tt)) * 0.5
            env = np.minimum(1, tt / 0.02) * np.minimum(1, (1.0 - tt) / 0.03)
            put(t, sig * env * 0.16)
        elif kind == "vmbeep":  # voicemail beep
            m = int(0.45 * SR); tt = np.arange(m) / SR
            put(t, np.sin(2 * np.pi * 1000 * tt) * np.minimum(1, tt / 0.01) * np.minimum(1, (0.45 - tt) / 0.02) * 0.22)
        elif kind == "shutter": # phone camera shutter: two quick clicks
            for k in range(2):
                m = int(0.05 * SR)
                put(t + k * 0.07, rng.normal(0, 1, m) * np.exp(-np.linspace(0, 9, m)) * 0.35)
        elif kind == "stamp":   # rubber stamp: thump + slap
            m = int(0.25 * SR); tt = np.arange(m) / SR
            put(t, np.sin(2 * np.pi * (110 - 200 * tt) * tt) * np.exp(-tt * 18) * 0.7)
            put(t, rng.normal(0, 1, int(0.06 * SR)) * np.exp(-np.linspace(0, 8, int(0.06 * SR))) * 0.3)
        elif kind == "whoosh":  # quick swipe between rooms
            from scipy.signal import butter, lfilter
            m = int(0.35 * SR); tt = np.arange(m) / SR
            bb, aa = butter(2, [400 / (SR / 2), 3000 / (SR / 2)], "band")
            put(t, lfilter(bb, aa, rng.normal(0, 1, m)) * np.sin(np.pi * tt / 0.35) ** 2 * 0.5)
        elif kind == "nope":    # wrong-answer buzz (soft, cartoon)
            m = int(0.3 * SR); tt = np.arange(m) / SR
            sig = np.sign(np.sin(2 * np.pi * 150 * tt)) * 0.5 + np.sin(2 * np.pi * 150 * tt) * 0.5
            put(t, sig * np.minimum(1, (0.3 - tt) / 0.03) * 0.09)
        elif kind == "k":       # tiny "k" reply pop, pitched randomly
            f = rng.uniform(900, 1600); d = 0.06
            put(t, tone(f, f * 0.7, d, vol=0.22) * np.exp(-np.linspace(0, 7, int(d * SR))))
        elif kind == "rewind":  # VHS rewind: fast warbling squeal + tape hiss
            m = int(0.7 * SR); tt = np.arange(m) / SR
            f = 2200 - 1400 * tt / 0.7 + 300 * np.sin(2 * np.pi * 23 * tt)
            sq = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.12
            hiss = rng.normal(0, 1, m) * 0.05
            put(t, (sq + hiss) * np.minimum(1, tt / 0.03) * np.minimum(1, (0.7 - tt) / 0.05))
        elif kind == "erase":   # marker eraser rubbing back and forth
            from scipy.signal import butter, lfilter
            bb, aa = butter(2, [700 / (SR / 2), 4000 / (SR / 2)], "band")
            for k in range(6):
                m = int(0.16 * SR); tt = np.arange(m) / SR
                put(t + k * 0.17, lfilter(bb, aa, rng.normal(0, 1, m)) * np.sin(np.pi * tt / 0.16) * 0.35)
        elif kind == "coin":    # junk dropping in a glass jar
            for k, f in enumerate((2400, 3100)):
                d = 0.25
                put(t + k * 0.05, tone(f, f, d, vol=0.18) * np.exp(-np.linspace(0, 9, int(d * SR))))
        elif kind == "tick":    # a received: short two-note notification ding
            for k, (f, v) in enumerate(((1568, 0.24), (2093, 0.2))):
                d_ = 0.32
                env = np.exp(-np.linspace(0, 7, int(d_ * SR)))
                put(t + k * 0.075, (tone(f, f, d_, vol=v) + tone(f * 2, f * 2, d_, vol=v * 0.25)) * env)
        elif kind == "ding":    # all acknowledged
            for k, f in enumerate((1047, 1319, 1568)):
                put(t + k * 0.09, tone(f, f, 0.5, vol=0.22) * np.exp(-np.linspace(0, 5, int(0.5 * SR))))
    # quiet upbeat music bed under the effects (synthesized, royalty-free)
    bpm = 104.0; beat = 60 / bpm
    prog = [(261.63, 329.63, 392.0), (196.0, 246.94, 293.66), (220.0, 261.63, 329.63), (174.61, 220.0, 261.63)]
    music = np.zeros(n)
    def addm(t0, sig):
        i = int(t0 * SR); sig = sig[: max(0, n - i)]; music[i:i + len(sig)] += sig
    nb = int(total_s / beat)
    for b in range(nb):
        t0 = b * beat; ch = prog[(b // 4) % 4]
        dd = beat * 0.9; tt = np.arange(int(dd * SR)) / SR
        if b % 2 == 0:  # plucky chord on the beat
            sig = sum(np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(4 * np.pi * f * tt) for f in ch) / 3
            addm(t0, sig * np.exp(-tt * 7) * 0.5)
        bf = ch[0] / 2  # bass
        addm(t0, np.sin(2 * np.pi * bf * tt) * np.exp(-tt * 4) * 0.55)
        h = rng.normal(0, 1, int(0.04 * SR)) * np.exp(-np.linspace(0, 8, int(0.04 * SR)))
        addm(t0 + beat / 2, np.diff(h, prepend=0) * 0.12)  # offbeat hat
    fade = np.ones(n); fl_ = int(1.5 * SR); fade[-fl_:] = np.linspace(1, 0, fl_); fade[:int(0.3 * SR)] = np.linspace(0, 1, int(0.3 * SR))
    mix = np.clip(mix, -1, 1)
    pcm = (mix * 32000).astype("<i2")
    path = pathlib.Path("/tmp") / f"brisket_sfx_{__import__('os').getpid()}.wav"
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(np.repeat(pcm, 2).tobytes())
    return path


def events():
    ev = [(0.8 + i * 0.11, "type") for i in range(9)] + [(1.8, "send")]
    ev += [(3.4 + k * 0.95, "pop") for k in range(len(MSGS) - 1)]
    ev += [(3.4 + 6 * 0.95 + 0.25, "scratch"), (3.4 + 6 * 0.95 + 0.6, "grrr1"), (10.4, "thud"), (10.5, "grrr2"), (10.55, "steam"), (13.05, "horn")]
    ev += [(13.0 + 1.2 + i * 0.45, "tick") for i in range(len(CREW))]
    ev += [(13.0 + 1.2 + 0.45 * len(CREW), "ding"), (20.0, "send"), (20.35, "tada")]
    return ev


REACT = ["neutral", "neutral", "sideeye", "bored", "bored", "sideeye", "closed", "furious"]  # by messages shown


def steam(im, x0, y0, w, h, t):
    """Cartoon steam puffs blowing out of both ears (mad close-up), synced with the kettle sound."""
    from PIL import ImageDraw
    if t < 0.15 or t > 2.15:
        return
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ld = ImageDraw.Draw(lay)
    ears = ((x0 + 0.17 * w, y0 + 0.50 * h, -1), (x0 + 0.83 * w, y0 + 0.50 * h, 1))
    k = 0
    while 0.15 + k * 0.07 < t:
        born = 0.15 + k * 0.07
        age = (t - born) / 0.75
        if 0 <= age < 1 and born < 1.95:
            ex, ey, side = ears[k % 2]
            wob = math.sin(k * 1.7) * 18
            x = ex + side * (8 + 240 * age)
            y = ey - 10 - 260 * age + wob * age
            r = 18 + 80 * age
            a = int(255 * min(1, (1 - age) * 1.6))
            circ = [(x + dx * r, y + dy * r, r * rr) for dx, dy, rr in ((0, 0, 1.0), (-0.55, 0.25, 0.7), (0.55, 0.3, 0.65))]
            for cx, cy, R in circ:  # outline pass, then fill pass, so the puff reads as one cloud
                ld.ellipse((cx - R - 5, cy - R - 5, cx + R + 5, cy + R + 5), fill=(120, 120, 128, a))
            for cx, cy, R in circ:
                ld.ellipse((cx - R, cy - R, cx + R, cy + R), fill=(246, 247, 250, a))
        k += 1
        if born > 2.2:
            break
    im.alpha_composite(lay) if im.mode == "RGBA" else im.paste(lay, (0, 0), lay)


def wiggle(sprite, t, box, amp=1.0):
    """Mustache wiggle: bend the mustache in place with a smooth warp centred on it (no copy on top)."""
    import numpy as np
    import cv2
    w, h = sprite.size
    cx, cy = (box[0] + box[2]) / 2 * w, (box[1] + box[3]) / 2 * h
    rx, ry = (box[2] - box[0]) / 2 * w, (box[3] - box[1]) / 2 * h
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    nx, ny = (xx - cx) / rx, (yy - cy) / ry
    win = np.exp(-(nx ** 2 + ny ** 2) * 1.6).astype(np.float32)
    lift = np.clip(ny + 0.6, 0, None)                      # the ends and bottom move most
    beat = t * 2 * math.pi * 2.2                            # ~132 bpm
    seesaw = math.sin(beat) * nx                            # one end up while the other goes down
    bounce = abs(math.sin(beat)) - 0.5                      # both ends hop on the beat
    dy = win * ry * amp * (0.16 * seesaw + 0.08 * bounce) * (0.35 + np.abs(nx)) * lift
    dx = win * rx * 0.05 * amp * math.sin(beat * 2) * nx
    arr = np.array(sprite)
    out = cv2.remap(arr, xx - dx, yy - dy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    return Image.fromarray(out)


MUSTACHE_HEAD = (0.10, 0.54, 0.90, 0.78)   # in the expression heads
MUSTACHE_BODY = (0.26, 0.17, 0.78, 0.29)   # in the texting pose


def bubble(head, dia):
    """Round video-call style bubble: head and shoulders inside a circle with a white ring."""
    sc = dia * 1.0 / head.height
    hs = head.resize((int(head.width * sc), int(head.height * sc)), Image.LANCZOS)
    inner = Image.new("RGBA", (dia, dia), (226, 222, 214, 255))
    inner.alpha_composite(hs, ((dia - hs.width) // 2, dia - hs.height + int(dia * 0.06)))
    mask = Image.new("L", (dia, dia), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, dia - 1, dia - 1), fill=255)
    out = Image.new("RGBA", (dia + 24, dia + 24))
    ImageDraw.Draw(out).ellipse((0, 0, dia + 23, dia + 23), fill=(255, 255, 255, 255), outline=INK, width=5)
    out.paste(inner, (12, 12), mask)
    return out


def fade_bottom(h):
    a = h.getchannel("A")
    fade = Image.linear_gradient("L").resize(h.size).point(lambda v: 255 if v < 205 else int(255 * (255 - v) / 50))
    h.putalpha(Image.composite(a, Image.new("L", h.size, 0), fade))
    return h


def head_of(m):
    """Head-and-shoulders crop of the master art, fading out at the bottom."""
    h = m.crop((int(m.width * 0.22), 0, int(m.width * 0.80), int(m.height * 0.30)))
    a = h.getchannel("A")
    fade = Image.linear_gradient("L").resize(h.size).point(lambda v: 255 if v < 200 else int(255 * (255 - v) / 55))
    h.putalpha(Image.composite(a, Image.new("L", h.size, 0), fade))
    return h


def sway(sprite, ang, sy=1.0):
    """Rotate about the feet and squash/stretch vertically."""
    w, h = sprite.size
    sp = sprite.resize((w, int(h * sy)), Image.BICUBIC) if sy != 1.0 else sprite
    pad = Image.new("RGBA", (sp.width * 2, sp.height * 2))
    pad.paste(sp, (sp.width // 2, 0), sp)
    pad = pad.rotate(ang, resample=Image.BICUBIC, center=(sp.width, sp.height))
    return pad.crop((0, 0, pad.width, sp.height)), sp.width


def anger(d, x, y, sc, t):
    """Comic anger mark: four red curved ticks that pulse."""
    p = 1 + 0.18 * abs(math.sin(t * 14))
    r = 34 * sc * p
    for ang in (45, 135, 225, 315):
        cx = x + math.cos(math.radians(ang)) * r
        cy = y + math.sin(math.radians(ang)) * r
        d.arc((cx - r * 0.8, cy - r * 0.8, cx + r * 0.8, cy + r * 0.8), ang + 135, ang + 225, fill=RED, width=int(10 * sc))


def camera(im, z=1.0, dx=0.0, dy=0.0, cx=W / 2, cy=H / 2):
    """Zoom about (cx, cy) and shift: used for handheld drift and documentary snap zooms."""
    if z <= 1.0005 and abs(dx) < 0.5 and abs(dy) < 0.5:
        return im
    zz = max(z, 1.0 + (abs(dx) + abs(dy)) * 2.4 / W)
    w, h = W / zz, H / zz
    x0 = min(max(cx - w / 2 - dx / zz, 0), W - w)
    y0 = min(max(cy - h / 2 - dy / zz, 0), H - h)
    return im.crop((int(x0), int(y0), int(x0 + w), int(y0 + h))).resize((W, H), Image.BILINEAR)


CO = 1.3       # cold open length (s)
FRZ = 1.0      # freeze frame: "Yep. That's me."
RW = 0.5       # VHS rewind
TTL = 0.0      # no title card up front (pros: no logo/title before the hook); show name rides as a chyron
PRE = CO + FRZ + RW + TTL
LOOK0 = 3.4 + 3 * 0.95 + 0.35   # after "costco run anyone?"
CRASH0 = 3.4 + 6 * 0.95 + 0.05  # "wait is drill tonight??" lands
COLD_HOOK = ("WHEN THE CAPTAIN", "CHANGES DRILL TIME", "IN THE GROUP CHAT\u2026")


def render(out):
    enc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                            "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", str(sfx(24.0 + PRE, [(0.0, "thud"), (0.05, "grrr2"), (0.1, "steam"), (CO, "scratch"), (CO + FRZ, "rewind"), (CO + FRZ + RW, "whoosh")] + [(t + PRE, k) for t, k in events()])),
                            "-ss", str(EP["music_start"]), "-i", str(ROY / "music_sneaky_snitch.mp3"),
                            "-filter_complex", ("[2:a]atrim=0:%.1f,volume=0.85,volume=enable='between(t,%.2f,%.2f)':volume=0.12,"
                                               "afade=t=out:st=%.1f:d=1.7[m];[1:a][m]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.95[a]")
                            % (24.0 + PRE, PRE + 10.4, PRE + 11.3, 22.3 + PRE),
                            "-map", "0:v", "-map", "[a]",
                            "-shortest", "-c:v", "libx264", "-preset", "veryfast",
                            "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart",
                            str(out)], stdin=subprocess.PIPE)
    total = int(FPS * (24.0 + PRE))
    freeze = None
    office = Image.open(ROY / "v2" / "bg_office.png").convert("RGB")
    office = office.resize((int(office.width * H / office.height), H), Image.LANCZOS)
    office = office.crop(((office.width - W) // 2, 0, (office.width - W) // 2 + W, H)).filter(ImageFilter.GaussianBlur(5))
    from PIL import ImageEnhance
    office = ImageEnhance.Brightness(office).enhance(0.75)
    logo = Image.open(ROOT / "brand" / "logo_badge.png").convert("RGBA").resize((260, 260))
    tap = []
    for i in range(9):
        fr = Image.open(ROY / "text_anim" / f"f{i}.png").convert("RGBA")
        tap.append(fr.resize((980, int(fr.height * 980 / fr.width)), Image.LANCZOS))
    office_im = office.copy()
    lf = Image.open(ROY / "x_sideeye.png").convert("RGBA")
    look_face = lf.resize((int(lf.width * 1180 / lf.height), 1180), Image.LANCZOS)
    xp = {k: Image.open(ROY / f"x_{k}.png").convert("RGBA")
          for k in ("neutral", "sideeye", "bored", "closed", "furious", "mad")}
    sm = {k: bubble(v, 360) for k, v in xp.items()}
    xs = {k: v.resize((int(v.width * 420 / v.height), 420), Image.LANCZOS) for k, v in xp.items()}
    small = sm["neutral"]
    end_head = xp["neutral"].resize((int(xp["neutral"].width * 1220 / xp["neutral"].height), 1220), Image.LANCZOS)
    hp = Image.open(ROY / "x_neutral.png").convert("RGBA")
    end_happy = hp.resize((int(hp.width * 1220 / hp.height), 1220), Image.LANCZOS)
    arm = Image.open(ROY / "arm_point.png").convert("RGBA")
    arm = arm.resize((int(arm.width * 1.95), int(arm.height * 1.95)), Image.LANCZOS)
    face_big = xp["mad"].resize((int(xp["mad"].width * 1180 / xp["mad"].height), 1180), Image.LANCZOS)
    for f in range(total):
        s = f / FPS
        im = Image.new("RGB", (W, H), PAPER)
        d = ImageDraw.Draw(im)
        pen = Pen(d, f // 3)
        if s < CO:
            # Cold open: the payoff first. Furious Roy, steam, big hook text, screen shake.
            t = s
            z = 1.08 + 0.05 * t
            fb = face_big.resize((int(face_big.width * z), int(face_big.height * z)), Image.BICUBIC)
            sh = int(16 * max(0, 1 - t * 2))
            im.paste(fb, (int(W / 2 - fb.width / 2) + random.randint(-sh, sh), H - fb.height + 10 + random.randint(-sh, sh)), fb)
            anger(d, W / 2 + 330, H - fb.height + 230, 3.2, t)
            steam(im, W / 2 - fb.width / 2, H - fb.height + 10, fb.width, fb.height, t + 0.3)
            for k, ln in enumerate(COLD_HOOK):
                sc = 1 + 0.25 * max(0, 1 - t / 0.15)
                fnt = HEAVY
                tw = d.textlength(ln, font=fnt)
                for dx in (-5, 0, 5):
                    for dy in (-5, 0, 5):
                        d.text((W / 2 - tw / 2 + dx, 90 + k * 108 + dy), ln, font=fnt, fill="white")
                d.text((W / 2 - tw / 2, 90 + k * 108), ln, font=fnt, fill=RED if k == len(COLD_HOOK) - 1 else INK)
            freeze = im.copy()
            enc.stdin.write(im.tobytes())
            continue
        if s < CO + FRZ:
            # Freeze frame, mockumentary style
            t = s - CO
            from PIL import ImageOps
            g = ImageOps.grayscale(freeze).convert("RGB")
            im = Image.blend(freeze, g, min(1, t / 0.15) * 0.85)
            d = ImageDraw.Draw(im)
            line = "Yep. That\u2019s me."
            tw = d.textlength(line, font=BOLD)
            d.rounded_rectangle((W / 2 - tw / 2 - 30, 1560, W / 2 + tw / 2 + 30, 1650), 20, fill=(0, 0, 0))
            d.text((W / 2 - tw / 2, 1578), line, font=BOLD, fill="white")
            enc.stdin.write(im.tobytes())
            continue
        if s < CO + FRZ + RW:
            # VHS rewind: band tearing, scanlines, "<< 6 HOURS EARLIER"
            t = s - CO - FRZ
            from PIL import ImageOps
            src = ImageOps.grayscale(freeze).convert("RGB")
            im = Image.new("RGB", (W, H), (10, 10, 10))
            rr = random.Random(f)
            for y in range(0, H, 40):
                off = int(rr.uniform(-60, 60) * (0.4 + t))
                im.paste(src.crop((0, y, W, y + 40)), (off, y))
            d = ImageDraw.Draw(im)
            for y in range(0, H, 6):
                d.line((0, y, W, y), fill=(0, 0, 0), width=2)
            by = int((t * 3 % 1) * H)
            d.rectangle((0, by, W, by + 70), fill=(200, 200, 200))
            d.rectangle((0, 880, W, 1060), fill=(0, 0, 0))
            d.polygon([(220, 930), (220, 1010), (160, 970)], fill="white")
            d.polygon([(280, 930), (280, 1010), (220, 970)], fill="white")
            d.text((310, 922), "6 HOURS EARLIER", font=HEAVY, fill="white")
            enc.stdin.write(im.tobytes())
            continue
        if s < PRE:
            # Show title card: STATION 12
            t = s - CO - FRZ - RW
            im = Image.new("RGB", (W, H), INK)
            d = ImageDraw.Draw(im)
            sc = min(1, t / 0.2)
            big = "STATION 12"
            from PIL import ImageFont as _IF
            ft = _IF.truetype(str(F_LOCAL / "barlow-condensed-latin-800-normal.woff"), int(190 * (0.8 + 0.2 * sc)))
            tw = d.textlength(big, font=ft)
            d.text((W / 2 - tw / 2, 700), big, font=ft, fill="white")
            d.rectangle((W / 2 - tw / 2, 920, W / 2 - tw / 2 + tw * sc, 940), fill=RED)
            ep = "EPISODE 1  \u00b7  THE GROUP CHAT"
            d.text((W / 2 - d.textlength(ep, font=BOLD) / 2, 990), ep, font=BOLD, fill=(220, 220, 220))
            lg = logo.resize((140, 140))
            im.paste(lg, (W // 2 - 70, 1120), lg)
            enc.stdin.write(im.tobytes())
            continue
        s -= PRE
        if s < 3.4:
            # Scene 1: Roy, full body, sends the message
            spr = tap[int(s / 0.16) % len(tap)]  # Roy tapping away at his phone
            im.paste(spr, (W // 2 - spr.width // 2, H - spr.height + 14), spr)
            shown, typing, pop = 0, 0, 1.0
            if 0.8 <= s < 1.8:
                typing = f
            if s >= 1.8:
                shown, pop = 1, min(1.0, (s - 1.8) * 6)
            chat(d, pen, 90, 250, W - 90, 900, shown, pop, typing)
            caption(d, "Captain Roy Brisket. 34 years on the job.", y=130)
        elif s < 10.4:
            # Scene 2: the crew floods the chat; Roy watches from the corner
            k = int((s - 3.4) / 0.95)
            shown = min(len(MSGS), 2 + k)
            pop = min(1.0, ((s - 3.4) - k * 0.95) * 7) if 2 + k <= len(MSGS) else 1.0
            chat(d, pen, 70, 230, W - 70, 1500, shown, pop, 0)
            k2 = int((s - 3.4) / 0.95)
            bump = max(0.0, 1 - ((s - 3.4) - k2 * 0.95) * 5)  # little jolt each time a message lands
            face_k = REACT[min(shown, len(REACT)) - 1]
            hd = sm[face_k]
            if face_k == "furious":
                hd = hd.rotate(random.uniform(-3, 3), resample=Image.BICUBIC, expand=True)
                bump = max(bump, 0.35)
            else:
                hd = hd.rotate(4 * bump * (1 if k2 % 2 else -1), resample=Image.BICUBIC, expand=True)
            paste_c(im, hd, W - 240, 1540 - 18 * bump, 1 + 0.05 * bump)
            if face_k == "furious":
                anger(d, W - 75, 1560, 1.6, s)
            zb = 1 + 0.035 * bump
            if zb > 1.001:
                big = im.resize((int(W * zb), int(H * zb)), Image.BILINEAR)
                im = big.crop(((big.width - W) // 2, (big.height - H) // 2, (big.width - W) // 2 + W, (big.height - H) // 2 + H))
        elif s < 13.0:
            # Scene 3: close-up, deadpan verdict
            t = s - 10.4
            z = 1.0 + 0.10 * min(1, t / 0.25) + 0.03 * t  # snap zoom on the deadpan, then a slow push
            sh = int(10 * max(0, 1 - t * 6))
            fb = face_big.resize((int(face_big.width * z), int(face_big.height * z)), Image.BICUBIC)
            im.paste(office, (0, 0))  # reality-TV confessional: Roy alone in his office
            d = ImageDraw.Draw(im)
            im.paste(fb, (int(W / 2 - fb.width / 2) + random.randint(-sh, sh), H - fb.height + 10), fb)
            if t > 0.3:
                anger(d, W / 2 + 330, H - fb.height + 230, 3.0, t)
            steam(im, W / 2 - fb.width / 2, H - fb.height + 10, fb.width, fb.height, t)
            d = ImageDraw.Draw(im)
            lt = min(1, t / 0.25)
            lx = int(-700 * (1 - lt) ** 2)
            n1, n2 = "CAPT. ROY BRISKET", "34 YEARS ON THE JOB"
            d.rectangle((lx + 60, 1560, lx + 120 + d.textlength(n1, font=BOLD), 1640), fill=RED)
            d.text((lx + 90, 1572), n1, font=BOLD, fill="white")
            d.rectangle((lx + 60, 1640, lx + 100 + d.textlength(n2, font=NAME), 1696), fill=INK)
            d.text((lx + 80, 1652), n2, font=NAME, fill="white")
            d.rounded_rectangle((40, 120, W - 40, 230), 30, fill=PAPER)
            caption(d, EP["mad"], y=150)
        elif s < 20.0:
            solution(im, d, s - 13.0, small, logo)
        else:
            t = s - 20.0
            lg = logo.resize((200, 200))
            im.paste(lg, (W // 2 - 100, 110), lg)
            l1, l2 = EP["end"]
            d.text((W / 2 - d.textlength(l1, font=HEAVY) / 2, 340), l1, font=HEAVY, fill=INK)
            d.text((W / 2 - d.textlength(l2, font=HEAVY) / 2, 440), l2, font=HEAVY, fill=RED)
            sub = "Keep your station updates simple."
            d.text((W / 2 - d.textlength(sub, font=BOLD) / 2, 562), sub, font=BOLD, fill=INK)
            fl = "FOLLOW FOR MORE CAPTAIN BRISKET"
            d.rounded_rectangle((W / 2 - d.textlength(fl, font=BOLD) / 2 - 30, 635, W / 2 + d.textlength(fl, font=BOLD) / 2 + 30, 715), 40, fill=RED)
            d.text((W / 2 - d.textlength(fl, font=BOLD) / 2, 648), fl, font=BOLD, fill=(255, 255, 255))
            # Roy's head under the title, mustache dancing
            pop = min(1.0, t / 0.25)
            hy = H - end_head.height + 80 + int((1 - pop) * 400)
            dancing = t > 0.45
            src = end_happy if dancing else end_head
            eh = wiggle(src, t, MUSTACHE_HEAD, 1.6) if dancing else src
            if dancing:  # head bobs and tilts with the beat
                b = math.sin((t - 0.45) * 2 * math.pi * 2.2)
                eh = eh.rotate(3 * b, resample=Image.BICUBIC, center=(eh.width / 2, eh.height))
                hy += int(-14 * abs(b))
            im.paste(eh, (W // 2 - eh.width // 2, hy), eh)
            if t < 0.2:
                im = Image.blend(Image.new("RGB", (W, H), PAPER), im, t / 0.2)
        if s < 10.4 and not (LOOK0 <= s < LOOK0 + 0.9):
            dd = ImageDraw.Draw(im)
            bug = "STATION 12  \u00b7  EP. 1  \u00b7  THE GROUP CHAT"
            bw = dd.textlength(bug, font=NAME) + 36
            dd.rectangle((W - bw - 40, H - 330, W - 40, H - 286), fill=INK)
            dd.text((W - bw - 22, H - 322), bug, font=NAME, fill="white")
        if LOOK0 <= s < LOOK0 + 0.9:
            # The "Jim look": cut to Roy staring dead into the camera mid-chaos, snap zoom in
            t = s - LOOK0
            im = office_im.copy()
            fl = look_face
            im.paste(fl, (W // 2 - fl.width // 2, H - fl.height + 10), fl)
            im = camera(im, 1.0 + 0.14 * min(1, t / 0.1), cy=H * 0.62)
        elif CRASH0 <= s < CRASH0 + 0.9:
            # Documentary crash zoom onto "wait is drill tonight??"
            t = s - CRASH0
            im = camera(im, 1.0 + 0.55 * min(1, t / 0.12), cx=W * 0.33, cy=1330)
        elif s < 20.0:
            # handheld documentary drift on every story shot
            im = camera(im, 1.03, dx=9 * math.sin(s * 0.9) + 4 * math.sin(s * 2.3), dy=6 * math.sin(s * 1.3 + 1))
        enc.stdin.write(im.tobytes())
    enc.stdin.close()
    enc.wait()


if __name__ == "__main__":
    render(pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "brisket_groupchat.mp4"))
