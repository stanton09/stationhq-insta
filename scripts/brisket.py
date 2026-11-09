"""Animated short: Captain Roy Brisket sends a drill change to the station group chat and it gets buried.
Loose black-ink cartoon, red only on his helmet (and StationHQ at the end). Writes brisket_groupchat.mp4."""
import math
import os
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
        verdict="\u201cMessage status: delivered. All 14.\u201d",
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


def chat(d, pen, x0, y0, x1, y1, shown, pop, typing, hl=0.0):
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
            if hl > 0 and idx == len(MSGS) - 1:
                # the trigger message itself pulses bigger with a red outline
                g = 1 + 0.18 * hl
                cxm, cym = bx + bw / 2, top + bh / 2
                gx0, gy0, gx1, gy1 = cxm - bw * g / 2, cym - bh * g / 2, cxm + bw * g / 2, cym + bh * g / 2
                d.rounded_rectangle((gx0, gy0, gx1, gy1), 40, fill=(255, 236, 234), outline=RED, width=8)
                hf = font("Inter-Bold.otf", int(46 * g))
                for k, ln in enumerate(lines):
                    d.text((gx0 + 30 * g, gy0 + 18 * g + k * 58 * g), ln, font=hf, fill=RED)
                d.text((bx + 10, top - 34), name, font=NAME, fill=GRAY)
                y = top - 52
                continue
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


_PH = {}


def _phone_assets(logo):
    """Built once: wallpaper (blurred station bay), fonts, avatar colors."""
    if _PH:
        return _PH
    from PIL import ImageEnhance
    pw, ph = 620, 1300
    wp = Image.open(ROOT / "brand" / "roy" / "v2" / "bg_bay.png").convert("RGB")
    wp = wp.resize((int(wp.width * ph / wp.height), ph), Image.LANCZOS)
    wp = wp.crop(((wp.width - pw) // 2, 0, (wp.width - pw) // 2 + pw, ph)).filter(ImageFilter.GaussianBlur(14))
    wp = ImageEnhance.Brightness(wp).enhance(0.55)
    _PH.update(pw=pw, ph=ph, wp=wp, clock=font("InterDisplay-SemiBold.otf", 150), date=font("Inter-Medium.otf", 30),
               t1=font("Inter-SemiBold.otf", 28), t2=font("Inter-Regular.otf", 26), t3=font("Inter-Bold.otf", 34),
               t4=font("Inter-SemiBold.otf", 24), logo=logo.resize((64, 64), Image.LANCZOS))
    return _PH


def _rr_mask(size, r):
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, size[0] - 1, size[1] - 1), r, fill=255)
    return m


def solution(im, d, t, roy_head, logo):
    """StationHQ alert on a realistic phone: lock-screen push with buzz, tap, app opens, crew confirms."""
    A = _phone_assets(logo)
    pw, ph = A["pw"], A["ph"]
    GREEN_ = (40, 170, 90)
    # banner
    d.rectangle((0, 120, W, 230), fill=RED)
    b = "NOW WITH STATIONHQ"
    d.text((W / 2 - d.textlength(b, font=HEAVY) / 2, 118), b, font=HEAVY, fill="white")
    TAP = 1.1
    scr = Image.new("RGB", (pw, ph))
    sd = ImageDraw.Draw(scr)
    if t < TAP:
        # ---- lock screen ----
        scr.paste(A["wp"], (0, 0))
        sd = ImageDraw.Draw(scr)
        sd.text((pw / 2 - sd.textlength("Thursday, November 12", font=A["date"]) / 2, 120), "Thursday, November 12",
                font=A["date"], fill=(235, 235, 240))
        sd.text((pw / 2 - sd.textlength("6:58", font=A["clock"]) / 2, 150), "6:58", font=A["clock"], fill="white")
        # frosted notification slides down with overshoot
        u = min(1.0, max(0.0, t - 0.05) / 0.35)
        ease = 1 - (1 - u) ** 3 + 0.06 * math.sin(u * math.pi)
        ny = int(-260 + (400 + 260) * ease)
        nx0, nx1, nh = 26, pw - 26, 210
        if ny > -nh:
            box = (nx0, max(0, ny), nx1, min(ph, ny + nh))
            if box[3] > box[1]:
                region = scr.crop(box).filter(ImageFilter.GaussianBlur(18))
                glass = Image.blend(region, Image.new("RGB", region.size, (245, 245, 248)), 0.72)
                m = _rr_mask((nx1 - nx0, nh), 40).crop((0, box[1] - ny, nx1 - nx0, box[3] - ny))
                scr.paste(glass, (nx0, box[1]), m)
            sd = ImageDraw.Draw(scr)
            lg = A["logo"]
            lm = _rr_mask(lg.size, 15)
            scr.paste(lg.convert("RGB"), (nx0 + 22, ny + 24), lm)
            sd.text((nx0 + 104, ny + 26), "STATIONHQ", font=A["t4"], fill=(90, 90, 98))
            sd.text((nx1 - 22 - sd.textlength("now", font=A["t4"]), ny + 26), "now", font=A["t4"], fill=(120, 120, 128))
            sd.text((nx0 + 104, ny + 58), EP["alert"][0].title(), font=A["t3"], fill=(20, 20, 24))
            sd.text((nx0 + 22, ny + 112), EP["alert"][1], font=A["t2"], fill=(30, 30, 34))
            sd.text((nx0 + 22, ny + 150), EP["alert"][2], font=A["t2"], fill=(110, 110, 118))
        # flashlight / camera buttons
        for cx in (90, pw - 90):
            sd.ellipse((cx - 44, ph - 170, cx + 44, ph - 82), fill=(60, 60, 64))
        sd.rounded_rectangle((pw / 2 - 90, ph - 30, pw / 2 + 90, ph - 22), 4, fill="white")
        # tap ripple on the notification just before it opens
        if t > TAP - 0.35:
            r = int(20 + 140 * (t - (TAP - 0.35)) / 0.35)
            sd.ellipse((pw / 2 - r, 500 - r, pw / 2 + r, 500 + r), outline=(255, 255, 255), width=5)
    else:
        # ---- app open ----
        tt = t - TAP
        sd.rectangle((0, 0, pw, ph), fill=(246, 246, 249))
        sd.rectangle((0, 0, pw, 230), fill=RED)
        lg = A["logo"]
        scr.paste(lg.convert("RGB"), (30, 110), _rr_mask(lg.size, 15))
        sd.text((110, 112), "Station 12", font=A["t3"], fill="white")
        sd.text((110, 156), "Officer update", font=A["t2"], fill=(255, 220, 215))
        # alert card
        sd.rounded_rectangle((26, 260, pw - 26, 450), 30, fill="white")
        sd.text((54, 284), EP["alert"][0], font=A["t1"], fill=RED)
        sd.text((54, 326), EP["alert"][1], font=A["t3"], fill=(20, 20, 24))
        sd.text((54, 384), "Sent by Capt. Brisket  \u00b7  just now", font=A["t4"], fill=(130, 130, 138))
        # Matches the real app: only the total sent count is shown (no per-person names).
        total = 14
        k = min(1.0, max(0.0, (tt - 0.15) / 0.8))
        count = int(round(total * (1 - (1 - k) ** 2)))
        cx, cy, rr = pw / 2, 700, 150
        sd.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), outline=(222, 222, 228), width=26)
        if count:
            sd.arc((cx - rr, cy - rr, cx + rr, cy + rr), -90, -90 + 360 * count / total, fill=GREEN_, width=26)
        big = font("InterDisplay-SemiBold.otf", 110)
        lab = str(count)
        sd.text((cx - sd.textlength(lab, font=big) / 2, cy - 72), lab, font=big, fill=(20, 20, 24))
        sd.text((cx - sd.textlength("members", font=A["t2"]) / 2, cy + 46), "members", font=A["t2"], fill=(130, 130, 138))
        if count == total:
            line = "Sent to all 14 members"
            sd.rounded_rectangle((60, 920, pw - 60, 1000), 40, fill=(230, 246, 236))
            check(sd, 96, 944, 32, GREEN_)
            sd.text((148, 940), line, font=A["t1"], fill=GREEN_)
        sd.rounded_rectangle((pw / 2 - 90, ph - 30, pw / 2 + 90, ph - 22), 4, fill=(30, 30, 34))
    # status bar + dynamic island (always)
    sd = ImageDraw.Draw(scr)
    fg = "white" if t < TAP else "white"
    sd.text((48, 30), "6:58", font=A["t1"], fill=fg)
    for k in range(4):
        sd.rectangle((pw - 150 + k * 11, 52 - k * 6, pw - 143 + k * 11, 58), fill=fg)
    sd.rounded_rectangle((pw - 92, 36, pw - 46, 60), 7, outline=fg, width=3)
    sd.rectangle((pw - 88, 40, pw - 58, 56), fill=fg)
    sd.rounded_rectangle((pw / 2 - 95, 22, pw / 2 + 95, 74), 26, fill=(0, 0, 0))
    # app-open transition: screen zooms up from the notification
    if t >= TAP and t < TAP + 0.25:
        k = (t - TAP) / 0.25
        sc = 0.6 + 0.4 * (1 - (1 - k) ** 2)
        small = scr.resize((int(pw * sc), int(ph * sc)), Image.BILINEAR)
        base = A["wp"].copy()
        base.paste(small, ((pw - small.width) // 2, int(400 * (1 - sc))), _rr_mask(small.size, int(60 * sc)))
        scr = base
    # ---- device: frame, buttons, shadow ----
    fw = 22
    dev = Image.new("RGBA", (pw + 2 * fw + 20, ph + 2 * fw), (0, 0, 0, 0))
    dd = ImageDraw.Draw(dev)
    for xb, yb, hb in ((0, 300, 70), (0, 400, 120), (0, 540, 120), (pw + 2 * fw + 12, 420, 180)):
        dd.rounded_rectangle((xb + 4, yb, xb + 14, yb + hb), 4, fill=(70, 72, 78))
    dd.rounded_rectangle((10, 0, pw + 2 * fw + 10, ph + 2 * fw), 96, fill=(48, 50, 56))
    dd.rounded_rectangle((13, 3, pw + 2 * fw + 7, ph + 2 * fw - 3), 93, outline=(150, 152, 160), width=3)
    dd.rounded_rectangle((10 + fw - 6, fw - 6, 10 + fw + pw + 6, fw + ph + 6), 80, fill=(8, 8, 10))
    dev.paste(scr, (10 + fw, fw), _rr_mask((pw, ph), 74))
    # buzz: phone shakes and rotates slightly when the alert lands
    buzz = max(0.0, 1 - abs(t - 0.4) / 0.6) if t < 1.2 else 0.0
    ang = 2.2 * buzz * math.sin(t * 70)
    if abs(ang) > 0.01:
        dev = dev.rotate(ang, resample=Image.BICUBIC, expand=True)
    sc = 0.9
    dev = dev.resize((int(dev.width * sc), int(dev.height * sc)), Image.LANCZOS)
    shadow = Image.new("RGBA", (dev.width + 120, dev.height + 120), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle((60, 80, dev.width + 60, dev.height + 60), 90, fill=(0, 0, 0, 90))
    shadow = shadow.filter(ImageFilter.GaussianBlur(30))
    px, py = W // 2 - dev.width // 2, 262
    if im.mode != "RGBA":
        base = im.convert("RGBA")
    else:
        base = im
    base.alpha_composite(shadow, (px - 60, py - 60))
    base.alpha_composite(dev, (px, py))
    # vibration marks at the sides during the buzz
    if buzz > 0.05:
        bd = ImageDraw.Draw(base)
        for side in (-1, 1):
            xx = W / 2 + side * (dev.width / 2 + 30)
            for j in range(3):
                off = side * j * 22
                bd.arc((xx + off - 30, 700 - 60, xx + off + 30, 700 + 60), 300 if side > 0 else 120,
                       60 if side > 0 else 240, fill=RED, width=6)
    im.paste(base.convert("RGB"))
    d = ImageDraw.Draw(im)
    # Roy's verdict
    paste_c(im, roy_head, W - 230, 1520)
    if t > 2.6 and False:  # the line now lands on Roy's look-to-camera button instead
        d.rounded_rectangle((36, 1580, 640, 1720), 30, fill=PAPER)
        for k, ln in enumerate(wrap(d, EP["verdict"], CAP, 560)):
            d.text((60, 1600 + k * 54), ln, font=CAP, fill=INK)


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
        elif kind == "rscratch":  # real record scratch (Pixabay)
            put(t, sample("record_scratch.mp3", 0, 1.2, 0.9))
        elif kind == "needle":    # real needle rip: music stops (Pixabay)
            put(t, sample("needle_rip.mp3", 0, 1.4, 0.9))
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
    ev += [(3.4 + 6 * 0.95 + 0.1, "rscratch"), (3.4 + 6 * 0.95 + 0.6, "grrr1"), (10.4, "thud"), (10.5, "grrr2"), (10.55, "steam"), (13.05, "horn")]
    ev += [(14.3 + i * 0.2, "tick") for i in range(4)]
    ev += [(15.1, "ding"), (SOL_END + 0.05, "thud"), (END0, "send"), (END0 + 0.35, "tada")]
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


def soft_bust(img):
    """The face art ends in a hard straight cut at the shoulders. Fade the outer shoulder edges and the
    bottom so the bust melts into the background instead of showing a cut-off rectangle."""
    import numpy as np
    a = np.array(img).astype(float)
    h, w = a.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    side = np.minimum(xx, w - 1 - xx) / (0.10 * w)                 # 0 at the left/right edge
    low = np.clip((yy / h - 0.62) / 0.20, 0, 1)                    # only the shoulder rows
    fs = np.clip(side, 0, 1) * low + (1 - low)
    fb = np.clip((1.0 - yy / h) / 0.07, 0, 1)                      # bottom 7%
    a[..., 3] *= np.clip(fs * fb, 0, 1)
    return Image.fromarray(a.astype("uint8"), "RGBA")


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


CO = 1.8       # cold open length (s)
FRZ = 0.0      # freeze frame removed (owner: opening was confusing)
RW = 0.0       # rewind removed
TTL = 0.0      # no title card up front (pros: no logo/title before the hook); show name rides as a chyron
PRE = CO + FRZ + RW + TTL
LOOK0 = 3.4 + 3 * 0.95 + 0.35   # after "costco run anyone?"
SOL_END = 17.4                  # StationHQ sequence ends
END0 = SOL_END                   # (look-to-camera button removed: owner)
OUTRO = END0 + 2.6              # fade into the StationHQ logo on black smoke
TOTAL = OUTRO + 2.4
KEV_YES = -99.0                 # (Kevin bay cutaways removed: owner said they weren't needed)
KEV_HUH = -99.0
CRASH0 = 3.4 + 6 * 0.95 + 0.05  # crash zoom as "wait is drill tonight??" lands
COLD_HOOK = ("WHEN THE CAPTAIN", "CHANGES DRILL TIME", "IN THE GROUP CHAT\u2026")


def render(out):
    enc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                            "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", str(sfx(TOTAL + PRE, [(0.0, "thud"), (0.05, "grrr2"), (0.1, "steam"), (CO, "whoosh")] + [(t + PRE, k) for t, k in events()])),
                            "-ss", os.environ.get("MUSIC_START", str(EP["music_start"])), "-i", str(ROY / os.environ.get("MUSIC", "music_fearless_first.mp3")),
                            "-filter_complex", ("[2:a]atrim=0:%.1f,volume=" + os.environ.get("MUSIC_VOL", "0.45") + ",volume=enable='between(t,%.2f,%.2f)':volume=0.12,volume=enable='between(t,%.2f,%.2f)':volume=0,"
                                               "afade=t=out:st=%.1f:d=1.7[m];[1:a][m]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.95,"
                                               "afade=t=out:st=" + "%.2f" % (OUTRO + PRE) + ":d=" + "%.2f" % (TOTAL - OUTRO) + "[a]")
                            % (TOTAL + PRE, PRE + 10.4, PRE + 11.3, PRE + SOL_END, PRE + END0, TOTAL + PRE - 1.7),
                            "-map", "0:v", "-map", "[a]",
                            "-shortest", "-c:v", "libx264", "-preset", "veryfast",
                            "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart",
                            str(out)], stdin=subprocess.PIPE)
    total = int(FPS * (TOTAL + PRE))
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

    import numpy as _np
    _rng = _np.random.default_rng(12)
    def _noise(scale):
        n = _rng.random((H // scale + 4, W // scale + 4))
        return Image.fromarray((n * 255).astype("uint8")).resize((W + 4 * scale, H + 4 * scale), Image.BICUBIC)
    smoke_layers = [_noise(160).filter(ImageFilter.GaussianBlur(60)), _noise(60).filter(ImageFilter.GaussianBlur(24))]
    big_logo = Image.open(ROOT / "brand" / "logo_badge.png").convert("RGBA").resize((560, 568), Image.LANCZOS)

    def smoke_frame(t):
        """Black background with slow drifting gray smoke, plus a faint red ember glow at the bottom."""
        a = _np.zeros((H, W), float)
        for k, (lay, spd, amt) in enumerate(zip(smoke_layers, (18, 34), (0.55, 0.35))):
            ox = int(40 + 30 * math.sin(t * 0.5 + k))
            oy = int(200 - spd * t) % 200 + 20
            a += _np.asarray(lay.crop((ox, oy, ox + W, oy + H))).astype(float) / 255 * amt
        yy = _np.linspace(0, 1, H)[:, None]
        a = _np.clip((a - 0.35) * 1.6, 0, 1) * (0.25 + 0.75 * yy)          # thicker smoke low in frame
        g = (a * 120).astype("uint8")
        img = Image.merge("RGB", [Image.fromarray(g)] * 3)
        glow = Image.new("RGB", (W, H), (0, 0, 0))
        ImageDraw.Draw(glow).ellipse((-200, H - 300, W + 200, H + 400), fill=(70, 14, 6))
        glow = glow.filter(ImageFilter.GaussianBlur(120))
        from PIL import ImageChops
        return ImageChops.add(img, glow)

    def roombg(name, blur=6, bright=0.92):
        r = Image.open(ROY / "v2" / f"bg_{name}.png").convert("RGB")
        r = r.resize((int(r.width * H / r.height), H), Image.LANCZOS)
        r = r.crop(((r.width - W) // 2, 0, (r.width - W) // 2 + W, H)).filter(ImageFilter.GaussianBlur(blur))
        return ImageEnhance.Brightness(r).enhance(bright)
    bg_day, bg_bay = roombg("dayroom"), roombg("bay", 3, 0.95)

    def kevin(name, h=1480):
        k = Image.open(ROY / "v2" / f"kevin_{name}.png").convert("RGBA")
        return k.resize((int(k.width * h / k.height), h), Image.LANCZOS)
    kev = {k: kevin(k) for k in ("yes", "confused")}

    def panel(img, y0, y1):
        lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ImageDraw.Draw(lay).rounded_rectangle((30, y0, W - 30, y1), 34, fill=PAPER + (235,))
        out = img.convert("RGBA")
        out.alpha_composite(lay)
        return out.convert("RGB")
    lf = Image.open(ROY / "x_sideeye.png").convert("RGBA")
    look_face = soft_bust(lf.resize((int(lf.width * 1180 / lf.height), 1180), Image.LANCZOS))
    xp = {k: Image.open(ROY / f"x_{k}.png").convert("RGBA")
          for k in ("neutral", "sideeye", "bored", "closed", "furious", "mad")}
    sm = {k: bubble(v, 360) for k, v in xp.items()}
    xs = {k: v.resize((int(v.width * 420 / v.height), 420), Image.LANCZOS) for k, v in xp.items()}
    small = sm["neutral"]
    end_head = soft_bust(xp["neutral"].resize((int(xp["neutral"].width * 1220 / xp["neutral"].height), 1220), Image.LANCZOS))
    hp = Image.open(ROY / "x_neutral.png").convert("RGBA")
    end_happy = soft_bust(hp.resize((int(hp.width * 1220 / hp.height), 1220), Image.LANCZOS))
    arm = Image.open(ROY / "arm_point.png").convert("RGBA")
    arm = arm.resize((int(arm.width * 1.95), int(arm.height * 1.95)), Image.LANCZOS)
    face_big = soft_bust(xp["mad"].resize((int(xp["mad"].width * 1180 / xp["mad"].height), 1180), Image.LANCZOS))
    end_frame_last = None
    for f in range(total):
        s = f / FPS
        im = Image.new("RGB", (W, H), PAPER)
        d = ImageDraw.Draw(im)
        pen = Pen(d, f // 3)
        if s < CO:
            # Cold open: the payoff first. Furious Roy, steam, big hook text, screen shake.
            t = s
            im.paste(bg_day)
            z = 1.08 + 0.05 * t
            fb = face_big.resize((int(face_big.width * z), int(face_big.height * z)), Image.BICUBIC)
            sh = int(16 * max(0, 1 - t * 2))
            im.paste(fb, (int(W / 2 - fb.width / 2) + random.randint(-sh, sh), H - fb.height + 10 + random.randint(-sh, sh)), fb)
            d = ImageDraw.Draw(im)
            anger(d, W / 2 + 330, H - fb.height + 230, 3.2, t)
            steam(im, W / 2 - fb.width / 2, H - fb.height + 10, fb.width, fb.height, t + 0.3)
            # the group chat exploding around him: notifications burst in from every side
            d = ImageDraw.Draw(im)

            d.rounded_rectangle((30, 60, W - 30, 90 + len(COLD_HOOK) * 108 + 10), 34, fill=PAPER)
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
        if s < 10.4:
            im.paste(bg_day)
        elif 13.0 <= s < SOL_END:
            im.paste(bg_day)
        d = ImageDraw.Draw(im)
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
            im = panel(im, 110, 220)
            d = ImageDraw.Draw(im)
            caption(d, "6 hours earlier\u2026", y=140)
        elif s < 10.4:
            # Scene 2: the crew floods the chat; Roy watches from the corner
            k = int((s - 3.4) / 0.95)
            shown = min(len(MSGS), 2 + k)
            pop = min(1.0, ((s - 3.4) - k * 0.95) * 7) if 2 + k <= len(MSGS) else 1.0
            hl = 0.0
            if shown == len(MSGS):
                tl = s - (3.4 + (len(MSGS) - 2) * 0.95)
                if 0.1 < tl < 1.2:
                    hl = abs(math.sin((tl - 0.1) * math.pi / 0.3)) * min(1, (1.2 - tl) / 0.2)
            chat(d, pen, 70, 230, W - 70, 1500, shown, pop, 0, hl)
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
        elif s < SOL_END:
            solution(im, d, s - 13.0, small, logo)
        elif s < END0:
            # Button: Roy's deadpan look to camera, one word, silence
            t = s - SOL_END
            im = office_im.copy()
            fl = look_face
            im.paste(fl, (W // 2 - fl.width // 2, H - fl.height + 10), fl)
            im = camera(im, 1.0 + 0.12 * min(1, t / 0.1), cy=H * 0.62)
            d = ImageDraw.Draw(im)
            d.rounded_rectangle((40, 120, W - 40, 230), 30, fill=PAPER)
            caption(d, "\u201cDelivered. All 14.\u201d", y=150)
        elif s >= OUTRO:
            t = s - OUTRO
            sm = smoke_frame(t)
            sc = 0.92 + 0.08 * min(1, t / 2.0)
            lg = big_logo.resize((int(560 * sc), int(568 * sc)), Image.LANCZOS)
            la = min(1, max(0, (t - 0.25) / 0.6))
            if la < 1:
                lg.putalpha(lg.getchannel("A").point(lambda v: int(v * la)))
            sm.paste(lg, (W // 2 - lg.width // 2, 560 - lg.height // 2 + 140), lg)
            d2 = ImageDraw.Draw(sm)
            if t > 0.8:
                tl = "stationhq.app"
                c = int(230 * min(1, (t - 0.8) / 0.4))
                d2.text((W / 2 - d2.textlength(tl, font=BOLD) / 2, 1080), tl, font=BOLD, fill=(c, c, c))
            prev = end_frame_last if end_frame_last is not None else sm
            im = Image.blend(prev, sm, min(1, t / 0.6))
        else:
            t = s - END0
            lg = logo.resize((200, 200))
            im.paste(lg, (W // 2 - 100, 110), lg)
            l1, l2 = EP["end"]
            d.text((W / 2 - d.textlength(l1, font=HEAVY) / 2, 340), l1, font=HEAVY, fill=INK)
            d.text((W / 2 - d.textlength(l2, font=HEAVY) / 2, 440), l2, font=HEAVY, fill=RED)
            fl = "FOLLOW FOR MORE CAPTAIN BRISKET"
            d.rounded_rectangle((W / 2 - d.textlength(fl, font=BOLD) / 2 - 30, 580, W / 2 + d.textlength(fl, font=BOLD) / 2 + 30, 660), 40, fill=RED)
            d.text((W / 2 - d.textlength(fl, font=BOLD) / 2, 593), fl, font=BOLD, fill=(255, 255, 255))
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
            end_frame_last = im.copy()
        if s < 10.4 and not (LOOK0 <= s < LOOK0 + 0.9):
            dd = ImageDraw.Draw(im)
            bug = "STATION 12  \u00b7  EP. 1  \u00b7  THE GROUP CHAT"
            bw = dd.textlength(bug, font=NAME) + 36
            dd.rectangle((W - bw - 40, H - 330, W - 40, H - 286), fill=INK)
            dd.text((W - bw - 22, H - 322), bug, font=NAME, fill="white")
        if KEV_YES <= s < KEV_YES + 0.8:
            # Reaction cut: Kevin, way too excited, in the bay
            t = s - KEV_YES
            im = bg_bay.copy()
            kv = kev["yes"]
            im.paste(kv, (W // 2 - kv.width // 2, H - kv.height + 380 - int(14 * abs(math.sin(t * 14)))), kv)
            dd = ImageDraw.Draw(im)
            hf = ImageFont.truetype(str(F_LOCAL / "barlow-condensed-latin-800-normal.woff"), 130)
            tx = "YES CAP!!!"
            dd.text((W / 2 - dd.textlength(tx, font=hf) / 2 + 6, 186), tx, font=hf, fill=INK)
            dd.text((W / 2 - dd.textlength(tx, font=hf) / 2, 180), tx, font=hf, fill="white")
            n1 = "KEVIN  \u00b7  PROBIE, DAY 47"
            dd.rectangle((60, 1500, 100 + dd.textlength(n1, font=BOLD), 1580), fill=RED)
            dd.text((80, 1512), n1, font=BOLD, fill="white")
            im = camera(im, 1.0 + 0.06 * min(1, t / 0.3))
        elif KEV_HUH <= s < KEV_HUH + 0.6:
            # Reaction cut: Kevin realizing drill is tonight
            t = s - KEV_HUH
            im = bg_bay.copy()
            kv = kev["confused"]
            im.paste(kv, (W // 2 - kv.width // 2, H - kv.height + 380), kv)
            im = camera(im, 1.0 + 0.25 * min(1, t / 0.12), cy=H * 0.45)
        elif LOOK0 <= s < LOOK0 + 0.9:
            # The "Jim look": cut to Roy staring dead into the camera mid-chaos, snap zoom in
            t = s - LOOK0
            im = office_im.copy()
            fl = look_face
            im.paste(fl, (W // 2 - fl.width // 2, H - fl.height + 10), fl)
            im = camera(im, 1.0 + 0.14 * min(1, t / 0.1), cy=H * 0.62)
        elif CRASH0 <= s < CRASH0 + 1.0:
            # Documentary crash zoom onto "wait is drill tonight??"
            t = s - CRASH0
            im = camera(im, 1.0 + 0.55 * min(1, t / 0.12), cx=W * 0.33, cy=1330)

        elif s < SOL_END:
            # handheld documentary drift on every story shot
            im = camera(im, 1.03, dx=9 * math.sin(s * 0.9) + 4 * math.sin(s * 2.3), dy=6 * math.sin(s * 1.3 + 1))
        enc.stdin.write(im.tobytes())
    enc.stdin.close()
    enc.wait()


if __name__ == "__main__":
    render(pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "brisket_groupchat.mp4"))
