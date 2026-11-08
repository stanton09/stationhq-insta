"""Captain Roy Brisket episodes, each with its own format (the group-chat one lives in brisket.py).

    python3 brisket_eps.py OUT.mp4 dues|roster|rigcheck|replyall
"""
import math
import random
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFilter

import brisket as B
from brisket import (W, H, FPS, INK, PAPER, RED, GRAY, HEAVY, HOOK, CAP, CHAT, NAME, BOLD, SMALL,
                     Pen, caption, wrap, bubble, steam, wiggle, anger, paste_c, MUSTACHE_HEAD, ROY, ROOT, sfx)

GREEN = (30, 140, 70)
random.seed(7)


# ---------- shared pieces ----------

class Kit:
    def __init__(self):
        self.logo = Image.open(ROOT / "brand" / "logo_badge.png").convert("RGBA").resize((260, 260))
        self.xp = {k: Image.open(ROY / f"x_{k}.png").convert("RGBA")
                   for k in ("neutral", "sideeye", "bored", "closed", "furious", "mad", "doubt")}
        self.sm = {k: bubble(v, 300) for k, v in self.xp.items()}
        self.big = {k: v.resize((int(v.width * 1180 / v.height), 1180), Image.LANCZOS) for k, v in self.xp.items()}
        self.end = self.xp["neutral"].resize((int(self.xp["neutral"].width * 1220 / self.xp["neutral"].height), 1220),
                                             Image.LANCZOS)
        self.tap = []
        for i in range(9):
            fr = Image.open(ROY / "text_anim" / f"f{i}.png").convert("RGBA")
            self.tap.append(fr.resize((980, int(fr.height * 980 / fr.width)), Image.LANCZOS))
        pc = Image.open(ROY / "pose_call.png").convert("RGBA")
        self.call = pc.resize((int(pc.width * 1150 / pc.height), 1150), Image.LANCZOS)


def hook(d, lines):
    for k, ln in enumerate(lines):
        d.text((W / 2 - d.textlength(ln, font=HOOK) / 2, 62 + k * 74), ln, font=HOOK, fill=INK if k == 0 else RED)


def banner(d, text="NOW WITH STATIONHQ"):
    d.rectangle((0, 120, W, 230), fill=RED)
    d.text((W / 2 - d.textlength(text, font=HEAVY) / 2, 118), text, font=HEAVY, fill="white")


def mad_closeup(im, d, kit, t, cap):
    z = 1.0 + 0.10 * min(1, t / 0.25) + 0.03 * t
    sh = int(10 * max(0, 1 - t * 6))
    fb = kit.big["mad"].resize((int(kit.big["mad"].width * z), int(kit.big["mad"].height * z)), Image.BICUBIC)
    im.paste(fb, (int(W / 2 - fb.width / 2) + random.randint(-sh, sh), H - fb.height + 10), fb)
    if t > 0.3:
        anger(d, W / 2 + 330, H - fb.height + 230, 3.0, t)
    steam(im, W / 2 - fb.width / 2, H - fb.height + 10, fb.width, fb.height, t)
    caption(d, cap, y=150)


def end_card(im, d, kit, t, l1, l2):
    lg = kit.logo.resize((200, 200))
    im.paste(lg, (W // 2 - 100, 110), lg)
    d.text((W / 2 - d.textlength(l1, font=HEAVY) / 2, 340), l1, font=HEAVY, fill=INK)
    d.text((W / 2 - d.textlength(l2, font=HEAVY) / 2, 440), l2, font=HEAVY, fill=RED)
    sub = "Keep your station updates simple."
    d.text((W / 2 - d.textlength(sub, font=BOLD) / 2, 562), sub, font=BOLD, fill=INK)
    fl = "FOLLOW FOR MORE CAPTAIN BRISKET"
    fw = d.textlength(fl, font=BOLD)
    d.rounded_rectangle((W / 2 - fw / 2 - 30, 635, W / 2 + fw / 2 + 30, 715), 40, fill=RED)
    d.text((W / 2 - fw / 2, 648), fl, font=BOLD, fill=(255, 255, 255))
    pop = min(1.0, t / 0.25)
    hy = H - kit.end.height + 80 + int((1 - pop) * 400)
    eh = kit.end
    if t > 0.45:
        eh = wiggle(eh, t, MUSTACHE_HEAD, 1.6)
        b = math.sin((t - 0.45) * 2 * math.pi * 2.2)
        eh = eh.rotate(3 * b, resample=Image.BICUBIC, center=(eh.width / 2, eh.height))
        hy += int(-14 * abs(b))
    im.paste(eh, (W // 2 - eh.width // 2, hy), eh)


def sticker(im, x, y, name, text, pop, ang=0.0, w=620):
    """A white speech-bubble sticker with the sender's name, popped in with a little overshoot."""
    layer = Image.new("RGBA", (w + 40, 260), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    lines = wrap(d, text, CHAT, w - 60)
    hgt = 70 + 50 * len(lines)
    d.rounded_rectangle((14, 14, w + 14, hgt + 14), 30, fill=(0, 0, 0, 60))
    d.rounded_rectangle((6, 6, w + 6, hgt + 6), 30, fill="white", outline=INK, width=4)
    d.text((34, 20), name, font=NAME, fill=RED)
    for k, ln in enumerate(lines):
        d.text((34, 58 + k * 50), ln, font=CHAT, fill=INK)
    layer = layer.crop((0, 0, w + 20, hgt + 20))
    sc = 0.3 + 0.7 * min(1, pop) + 0.12 * math.sin(min(1, pop) * math.pi)
    layer = layer.resize((max(1, int(layer.width * sc)), max(1, int(layer.height * sc))), Image.BICUBIC)
    layer = layer.rotate(ang, resample=Image.BICUBIC, expand=True)
    im.paste(layer, (int(x - layer.width / 2), int(y - layer.height / 2)), layer)


def stamp(im, x, y, text, t, col=GREEN, ang=-12, size=110):
    """Rubber stamp that slams down (big -> normal) at t=0."""
    if t < 0:
        return
    from PIL import ImageFont
    f = ImageFont.truetype(str(B.F_LOCAL / "barlow-condensed-latin-800-normal.woff"), size)
    tmp = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    tw = int(tmp.textlength(text, font=f))
    lay = Image.new("RGBA", (tw + 60, size + 50), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    d.rounded_rectangle((6, 6, tw + 54, size + 44), 16, outline=col + (235,), width=9)
    d.text((30, 4), text, font=f, fill=col + (235,))
    sc = 1 + 1.4 * max(0, 1 - t / 0.12)
    lay = lay.resize((int(lay.width * sc), int(lay.height * sc)), Image.BICUBIC).rotate(ang, expand=True,
                                                                                         resample=Image.BICUBIC)
    if t < 0.12:
        lay.putalpha(lay.getchannel("A").point(lambda v: int(v * t / 0.12)))
    im.paste(lay, (int(x - lay.width / 2), int(y - lay.height / 2)), lay)


def encode(out, total_s, events, music_start, frames):
    wav = sfx(total_s, events)
    fade = total_s - 1.7
    enc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                            "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", str(wav),
                            "-ss", str(music_start), "-i", str(ROY / "music_sneaky_snitch.mp3"),
                            "-filter_complex", f"[2:a]atrim=0:{total_s},volume=0.85,afade=t=out:st={fade}:d=1.7[m];"
                            "[1:a][m]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.95[a]",
                            "-map", "0:v", "-map", "[a]", "-shortest", "-c:v", "libx264", "-preset", "veryfast",
                            "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
                            "-movflags", "+faststart", str(out)], stdin=subprocess.PIPE)
    for f in range(int(FPS * total_s)):
        im = frames(f / FPS, f)
        enc.stdin.write(im.convert("RGB").tobytes())
    enc.stdin.close()
    enc.wait()


def blank():
    im = Image.new("RGBA", (W, H), PAPER + (255,))
    return im, ImageDraw.Draw(im)


# ---------- DUES: voicemail montage ----------

CALLS = [  # name, what happens, Roy's face after
    ("Marco", "“Hey it's Marco, leave a message… unless it's about money.”", "sideeye"),
    ("Pete", "“Pete here. If this is about dues, I paid in March.”", "bored"),
    ("Sully", "“Yo it's Sully. Can I pay in wings?”", "doubt"),
    ("Kevin (probie)", "“YES CAP!!! …wait who is this?”", "closed"),
    ("Donna", "The mailbox is full and cannot accept new messages.", "furious"),
]
CALL_T0, CALL_LEN = 2.0, 2.3


def dues(out):
    kit = Kit()
    T = 24.5
    mad0, sol0, end0 = CALL_T0 + CALL_LEN * len(CALLS), 0, 0
    sol0 = mad0 + 2.6
    end0 = sol0 + 5.4
    T = end0 + 4.0
    ev = [(0.4, "ring"), (1.4, "ring")]
    for i, (name, _, _) in enumerate(CALLS):
        t0 = CALL_T0 + i * CALL_LEN
        ev += [(t0, "whoosh"), (t0 + 0.15, "ring")]
        ev += [(t0 + 0.95, "vmbeep" if name != "Kevin (probie)" else "pop")]
        ev += [(t0 + 1.25, "nope")]
    ev += [(mad0, "thud"), (mad0 + 0.1, "grrr2"), (mad0 + 0.15, "steam")]
    ev += [(sol0 + 1.0 + i * 0.5, "stamp") for i in range(6)] + [(sol0 + 4.2, "ding")]
    ev += [(end0, "send"), (end0 + 0.35, "tada")]
    paid = ["Kevin", "Marco", "Pete", "Sully", "Donna", "Big Mike"]

    def frame(s, f):
        im, d = blank()
        pen = Pen(d, f // 3)
        if s < CALL_T0:
            body = kit.call
            im.paste(body, (W // 2 - body.width // 2, H - body.height + 40), body)
            hook(d, ("WHEN THE CAPTAIN HAS TO CALL", "EVERYONE ABOUT DUES…"))
        elif s < mad0:
            i = int((s - CALL_T0) / CALL_LEN)
            t = s - CALL_T0 - i * CALL_LEN
            name, line, face = CALLS[i]
            # tally at top
            d.rounded_rectangle((60, 70, W - 60, 230), 30, fill=INK)
            d.text((100, 92), "DUES COLLECTED", font=NAME, fill=(200, 200, 200))
            d.text((100, 128), "$0", font=HEAVY, fill=RED)
            d.text((W / 2 + 40, 92), "EXCUSES", font=NAME, fill=(200, 200, 200))
            exc = i + (1 if t > 1.25 else 0)
            d.text((W / 2 + 40, 128), str(exc), font=HEAVY, fill="white")
            # call card slides in
            sl = min(1, t / 0.25)
            cx = int(W / 2 + (1 - sl) ** 2 * W)
            pen.rect(cx - 400, 300, cx + 400, 760, 6, fill="white")
            d.ellipse((cx - 70, 340, cx + 70, 480), fill=(225, 225, 230), outline=INK, width=5)
            d.text((cx - d.textlength(name[0], font=HEAVY) / 2, 352), name[0], font=HEAVY, fill=INK)
            d.text((cx - d.textlength(name, font=BOLD) / 2, 500), name, font=BOLD, fill=INK)
            status = "calling…" if t < 0.95 else ("answered" if name.startswith("Kevin") else "voicemail")
            d.text((cx - d.textlength(status, font=SMALL) / 2, 565), status, font=SMALL, fill=GRAY)
            secs = f"0:0{min(9, int(t * 3))}"
            d.text((cx - d.textlength(secs, font=SMALL) / 2, 610), secs, font=SMALL, fill=GRAY)
            d.ellipse((cx - 45, 670, cx + 45, 740), fill=RED)  # hang-up button
            d.rounded_rectangle((cx - 24, 698, cx + 24, 712), 6, fill="white")
            if t > 1.0:
                sticker(im, W / 2, 900, name if not line.startswith("The mailbox") else "Voicemail",
                        line, (t - 1.0) / 0.25, ang=random.Random(i).uniform(-4, 4), w=820)
            # Roy on the phone, getting angrier each call
            body = kit.call
            im.paste(body, (40, H - body.height + 260), body)
            fc = kit.sm[face if t > 1.3 else (CALLS[i - 1][2] if i else "neutral")]
            paste_c(im, fc, W - 240, 1380)
            if face == "furious" and t > 1.3:
                anger(d, W - 90, 1400, 1.6, s)
        elif s < sol0:
            mad_closeup(im, d, kit, s - mad0, "“Calls made: 5. Dues collected: $0.”")
        elif s < end0:
            t = s - sol0
            banner(d)
            pen.rect(110, 300, W - 110, 1420, 6, fill="white")
            d.text((160, 340), "STATION DUES  ·  $20", font=BOLD, fill=INK)
            d.text((160, 400), "Due Friday", font=SMALL, fill=GRAY)
            for k, nm in enumerate(paid):
                y = 500 + k * 140
                d.line((160, y + 110, W - 160, y + 110), fill=(220, 220, 225), width=3)
                d.text((170, y + 30), nm, font=CHAT, fill=INK)
                stamp(im, W - 330, y + 50, "PAID", t - 1.0 - k * 0.5, size=80)
            if t > 4.2:
                caption(d, "“Collection rate: acceptable.”", y=1480)
            paste_c(im, kit.sm["neutral"], W / 2, 1580)
        else:
            end_card(im, d, kit, s - end0, "DUES TRACKING", "WITHOUT THE CHASE.")
        return im

    encode(out, T, ev, 68, frame)


# ---------- ROSTER: whiteboard photo zoom ----------

def whiteboard(seed=3):
    """A messy hand-written schedule on a whiteboard, as a phone photo (sideways-ish, glare, stain, thumb)."""
    bw, bh = 1500, 1050
    wb = Image.new("RGBA", (bw, bh), (246, 247, 244, 255))
    d = ImageDraw.Draw(wb)
    pen = Pen(d, seed)
    r = random.Random(seed)
    from PIL import ImageFont
    hand = ImageFont.truetype(str(B.F_LOCAL / "barlow-condensed-latin-800-normal.woff"), 46)
    d.rectangle((0, 0, bw - 1, bh - 1), outline=(150, 150, 155), width=26)
    d.text((70, 50), "DEC  SCHED", font=hand, fill=(30, 60, 160))
    days = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
    names = ["KEV", "MARCO", "DONNA", "PETE", "SULLY", "MIKE", "ROSA", "TJ", "MARCO?", "SEE CAP", "8 or 3", "KEV"]
    for i, dy in enumerate(days):
        x = 70 + i * 200
        d.text((x + 20, 140), dy, font=hand, fill=(30, 60, 160))
        pen.line([(x, 130), (x, 980)], 4, fill=(60, 60, 70))
        for j in range(4):
            nm = names[(i * 4 + j) % len(names)]
            col = (200, 30, 30) if r.random() < 0.25 else (20, 20, 25)
            d.text((x + 14 + r.randint(-8, 8), 240 + j * 180 + r.randint(-10, 10)), nm, font=hand, fill=col)
            if r.random() < 0.3:
                pen.line([(x + 10, 270 + j * 180), (x + 180, 250 + j * 180)], 6, fill=(20, 20, 25))
    pen.line([(400, 600), (900, 380), (880, 420)], 6, fill=(200, 30, 30))  # mystery arrow
    d.ellipse((980, 640, 1180, 790), fill=(170, 30, 25, 230))  # ketchup stain
    d.ellipse((1150, 700, 1210, 750), fill=(170, 30, 25, 230))
    glare = Image.new("L", (bw, bh), 0)
    ImageDraw.Draw(glare).ellipse((250, 120, 900, 520), fill=200)
    glare = glare.filter(ImageFilter.GaussianBlur(70))
    wb = Image.composite(Image.new("RGBA", (bw, bh), (255, 255, 255, 255)), wb, glare)
    photo = Image.new("RGBA", (bw + 120, bh + 120), (70, 66, 60, 255))
    photo.paste(wb, (60, 60))
    pd = ImageDraw.Draw(photo)
    pd.ellipse((-120, bh - 160, 260, bh + 260), fill=(226, 170, 135, 255))  # thumb over the lens
    photo = photo.filter(ImageFilter.GaussianBlur(1.6)).rotate(-9, expand=True, resample=Image.BICUBIC,
                                                                 fillcolor=(40, 38, 36, 255))
    return photo


ROSTER_Q = [("Marco", "is that a 3 or an 8"), ("Donna", "its sideways on my phone"),
            ("Pete", "who's on christmas??"), ("Sully", "why is there ketchup on it"),
            ("Kevin (probie)", "wait am I working tonight??")]


def roster(out):
    kit = Kit()
    photo = whiteboard()
    Q0, QL = 2.6, 1.5
    mad0 = Q0 + QL * len(ROSTER_Q) + 0.6
    sol0 = mad0 + 2.6
    end0 = sol0 + 5.6
    T = end0 + 4.0
    ev = [(1.75, "shutter"), (2.1, "send")]
    ev += [(Q0 + i * QL + 0.2, "pop") for i in range(len(ROSTER_Q))]
    ev += [(Q0 + (len(ROSTER_Q) - 1) * QL + 0.4, "scratch"), (Q0 + (len(ROSTER_Q) - 1) * QL + 0.75, "grrr1")]
    ev += [(mad0, "thud"), (mad0 + 0.1, "grrr2"), (mad0 + 0.15, "steam")]
    ev += [(sol0 + 0.9 + i * 0.28, "tick") for i in range(8)] + [(sol0 + 3.6, "stamp"), (sol0 + 4.0, "ding")]
    ev += [(end0, "send"), (end0 + 0.35, "tada")]
    # zoom targets on the photo (fractions): roam around the mess
    spots = [(0.5, 0.5, 1.0), (0.25, 0.35, 1.8), (0.62, 0.28, 2.0), (0.75, 0.68, 1.9), (0.4, 0.75, 1.7),
             (0.18, 0.2, 2.2)]
    cal_days = ["M", "T", "W", "T", "F", "S", "S"]
    shifts = [(0, 0, "Kevin"), (1, 4, "Marco"), (1, 5, "Donna"), (3, 3, "Pete"), (3, 4, "Sully"),
              (1, 0, "Mike"), (1, 1, "Rosa"), (1, 2, "T.J.")]

    def frame(s, f):
        im, d = blank()
        pen = Pen(d, f // 3)
        if s < 1.9:
            spr = kit.tap[int(s / 0.16) % len(kit.tap)]
            im.paste(spr, (W // 2 - spr.width // 2, H - spr.height + 14), spr)
            hook(d, ("WHEN CAP POSTS THE SCHEDULE", "AS A PHOTO OF THE WHITEBOARD…"))
            if s > 1.75:
                im.alpha_composite(Image.new("RGBA", (W, H), (255, 255, 255, int(255 * (1 - (s - 1.75) / 0.15)))))
        elif s < mad0:
            t = s - 1.9
            seg = min(len(spots) - 2, int(t / 1.6))
            u = min(1, (t - seg * 1.6) / 1.6)
            u = u * u * (3 - 2 * u)
            (ax, ay, az), (bx, by, bz) = spots[seg], spots[seg + 1]
            fx, fy, z = ax + (bx - ax) * u, ay + (by - ay) * u, az + (bz - az) * u
            sc = W * 1.0 / photo.width * z * 1.25
            pw, ph = int(photo.width * sc), int(photo.height * sc)
            ph_img = photo.resize((pw, ph), Image.BILINEAR)
            px, py = int(W / 2 - fx * pw), int(H * 0.46 - fy * ph)
            im.paste(ph_img, (px, py))
            d.rectangle((0, 0, W, 60), fill=INK)
            d.text((40, 12), "IMG_4471.jpg  ·  from Capt. Brisket", font=NAME, fill="white")
            for i, (nm, q) in enumerate(ROSTER_Q):
                qt = s - (Q0 + i * QL)
                if qt > 0:
                    rr = random.Random(i)
                    sticker(im, W / 2 + rr.uniform(-140, 140), 300 + i * 230, nm, q, qt / 0.25,
                            ang=rr.uniform(-6, 6), w=640)
            last = s - (Q0 + (len(ROSTER_Q) - 1) * QL)
            face = "furious" if last > 0.4 else ("sideeye" if s > Q0 + QL * 2 else "neutral")
            paste_c(im, kit.sm[face], W - 220, 1560)
            if face == "furious":
                anger(d, W - 75, 1580, 1.6, s)
        elif s < sol0:
            mad_closeup(im, d, kit, s - mad0, "“Schedule status: unreadable.”")
        elif s < end0:
            t = s - sol0
            banner(d)
            x0, y0, cw, chh = 100, 330, (W - 200) / 7, 190
            pen.rect(x0, y0, W - 100, y0 + 70 + chh * 4, 6, fill="white")
            d.text((x0 + 30, y0 + 14), "DECEMBER  ·  STATION 12", font=NAME, fill=GRAY)
            for k, dl in enumerate(cal_days):
                d.text((x0 + k * cw + cw / 2 - 10, y0 + 40), dl, font=NAME, fill=INK)
            for r_ in range(4):
                for c in range(7):
                    d.rectangle((x0 + c * cw, y0 + 70 + r_ * chh, x0 + (c + 1) * cw, y0 + 70 + (r_ + 1) * chh),
                                outline=(225, 225, 230), width=2)
                    d.text((x0 + c * cw + 10, y0 + 76 + r_ * chh), str(r_ * 7 + c + 1), font=SMALL, fill=GRAY)
            for k, (r_, c, nm) in enumerate(shifts):
                if t > 0.9 + k * 0.28:
                    a = min(1, (t - 0.9 - k * 0.28) / 0.15)
                    cxl, cyl = x0 + c * cw + 6, y0 + 70 + r_ * chh + 110
                    col = RED if nm == "Kevin" else (40, 90, 200)
                    d.rounded_rectangle((cxl, cyl - 30 * (1 - a), cxl + cw - 12, cyl + 56), 12, fill=col)
                    d.text((cxl + 8, cyl + 8), nm, font=SMALL, fill="white")
            if t > 3.6:
                stamp(im, W / 2, y0 + 70 + chh * 4 + 120, "KEVIN: TONIGHT", t - 3.6, col=RED, ang=-6, size=90)
            if t > 4.0:
                caption(d, "“Questions received: zero.”", y=1500)
            paste_c(im, kit.sm["neutral"], W / 2, 1600)
        else:
            end_card(im, d, kit, s - end0, "SHIFTS THE WHOLE", "CREW CAN READ.")
        return im

    encode(out, T, ev, 34, frame)


# ---------- RIG CHECK: clipboard hunt ----------

def room(kind, seed):
    """Line-art firehouse room on a tinted wall."""
    im = Image.new("RGBA", (W, 1300), (236, 230, 218, 255))
    d = ImageDraw.Draw(im)
    pen = Pen(d, seed)
    d.rectangle((0, 1000, W, 1300), fill=(200, 192, 178))
    pen.line([(0, 1000), (W, 1000)], 6)
    if kind == "bay":
        d.rectangle((60, 120, W - 60, 1000), fill=(210, 205, 196))
        for k in range(6):
            pen.line([(60, 120 + k * 150), (W - 60, 120 + k * 150)], 3, fill=(170, 165, 158))
        d.rounded_rectangle((120, 520, 960, 960), 30, fill=RED)  # engine side
        pen.rect(120, 520, 960, 960, 7)
        pen.rect(160, 560, 420, 760, 5, fill=(180, 210, 230))
        for x in (260, 800):
            d.ellipse((x - 85, 880, x + 85, 1050), fill=INK)
            d.ellipse((x - 40, 925, x + 40, 1005), fill=(180, 180, 180))
        d.text((480, 640), "ENGINE 1", font=BOLD, fill="white")
    elif kind == "kitchen":
        pen.rect(640, 260, 960, 1000, 7, fill=(240, 240, 240))  # fridge
        pen.line([(640, 520), (960, 520)], 6)
        pen.line([(920, 330), (920, 450)], 8)
        pen.line([(920, 590), (920, 760)], 8)
        pen.rect(80, 700, 560, 760, 6, fill=(170, 120, 80))  # table
        pen.line([(130, 760), (130, 1000)], 8)
        pen.line([(510, 760), (510, 1000)], 8)
        pen.line([(200, 690), (330, 640)], 8, fill=(80, 80, 85))  # the good spatula
        d.ellipse((320, 620, 380, 670), fill=(80, 80, 85))
    elif kind == "bathroom":
        pen.rect(330, 220, 750, 1000, 8, fill=(170, 130, 95))  # door
        d.ellipse((680, 600, 712, 632), fill=(200, 170, 60))
        d.rectangle((430, 330, 650, 420), fill="white")
        d.text((448, 350), "OCCUPIED", font=BOLD, fill=RED)
    elif kind == "bunks":
        for y in (380, 700):
            pen.rect(120, y, 960, y + 120, 6, fill=(120, 140, 170))
            d.rectangle((140, y - 40, 300, y), fill="white")
        pen.line([(120, 300), (120, 1000)], 8)
        pen.line([(960, 300), (960, 1000)], 8)
        d.text((560, 410), "zzz", font=BOLD, fill=GRAY)
    return im


ROOMS = [("APPARATUS BAY", "bay", "sideeye"), ("BUNK ROOM", "bunks", "bored"),
         ("BATHROOM", "bathroom", "doubt"), ("KITCHEN", "kitchen", "closed")]


def rigcheck(out):
    kit = Kit()
    rooms = [room(k, i) for i, (_, k, _) in enumerate(ROOMS)]
    R0, RL = 2.0, 2.0
    fr0 = R0 + RL * len(ROOMS)        # freezer reveal
    mad0 = fr0 + 2.2
    sol0 = mad0 + 2.6
    end0 = sol0 + 5.4
    T = end0 + 4.0
    ev = [(R0 + i * RL, "whoosh") for i in range(len(ROOMS))] + [(R0 + i * RL + 1.1, "nope") for i in range(3)]
    ev += [(fr0, "whoosh"), (fr0 + 0.5, "scratch"), (fr0 + 0.85, "grrr1")]
    ev += [(mad0, "thud"), (mad0 + 0.1, "grrr2"), (mad0 + 0.15, "steam")]
    items = ["SCBA", "Irons", "Hose load", "Pump", "Lights", "Fuel", "Medical bag", "Radios"]
    ev += [(sol0 + 0.7 + i * 0.3, "tick") for i in range(len(items))] + [(sol0 + 3.4, "stamp"), (sol0 + 3.8, "ding")]
    ev += [(end0, "send"), (end0 + 0.35, "tada")]

    def frame(s, f):
        im, d = blank()
        pen = Pen(d, f // 3)
        if s < R0:
            # the empty nail where the clipboard should hang
            pen.rect(240, 420, 840, 1260, 6, fill=(236, 230, 218))
            d.ellipse((525, 470, 555, 500), fill=INK)
            pen.rect(390, 560, 690, 980, 4)  # faint outline of where it used to hang
            d.text((W / 2 - d.textlength("RIG CHECK", font=BOLD) / 2, 1020), "RIG CHECK", font=BOLD, fill=GRAY)
            paste_c(im, kit.sm["sideeye"], W / 2, 1380)
            hook(d, ("WHEN THE RIG CHECK", "CLIPBOARD GOES MISSING AGAIN…"))
        elif s < fr0:
            i = int((s - R0) / RL)
            t = s - R0 - i * RL
            label, _, face = ROOMS[i]
            off = int((1 - min(1, t / 0.25)) ** 2 * W)
            im.paste(rooms[i], (off, 300), rooms[i])
            d.rectangle((0, 120, W, 260), fill=INK)
            d.text((W / 2 - d.textlength(label, font=HEAVY) / 2, 130), label, font=HEAVY, fill="white")
            # Roy peeks in from the right edge
            peek = min(1, max(0, (t - 0.35) / 0.3))
            hd = kit.sm[face]
            paste_c(im, hd.rotate(12, expand=True, resample=Image.BICUBIC), W + 60 - 300 * peek, 1250)
            if t > 1.1 and i < 3:
                stamp(im, W / 2, 800, "NOPE", t - 1.1, col=RED, ang=-10, size=150)
            if i == 3 and t > 1.0:
                caption(d, "…the freezer?", y=1720)
        elif s < mad0:
            t = s - fr0
            im.paste(rooms[3], (0, 300), rooms[3])
            d.rectangle((0, 120, W, 260), fill=INK)
            d.text((W / 2 - d.textlength("FOUND IT.", font=HEAVY) / 2, 130), "FOUND IT.", font=HEAVY, fill="white")
            # freezer door swings open, frozen clipboard inside
            op = min(1, t / 0.3)
            d.rectangle((650, 570, 950, 990), fill=(200, 230, 245))
            pen.rect(690, 610, 900, 950, 6, fill=(160, 120, 80))
            pen.rect(720, 660, 870, 930, 3, fill=(245, 250, 255))
            for k in range(5):
                pen.line([(735, 690 + k * 45), (850, 690 + k * 45)], 3, fill=(170, 190, 210))
            d.rectangle((770, 600, 820, 640), fill=(150, 150, 155))
            for x in range(700, 900, 40):
                d.polygon([(x, 610), (x + 20, 610), (x + 10, 650 + (x % 3) * 12)], fill=(220, 240, 255))
            if op < 1:
                d.rectangle((640, 560, 640 + int(320 * (1 - op)), 1000), fill=(240, 240, 240), outline=INK, width=6)
            caption(d, "“Location: freezer. Status: unsigned.”", y=1800)
            paste_c(im, kit.sm["furious" if t > 0.5 else "closed"], W / 2, 1460)
            if t > 0.5:
                anger(d, W / 2 + 150, 1480, 1.6, s)
        elif s < sol0:
            mad_closeup(im, d, kit, s - mad0, "“Rig check: unsigned. Clipboard: frozen.”")
        elif s < end0:
            t = s - sol0
            banner(d)
            pen.rect(130, 300, W - 130, 1380, 6, fill="white")
            d.text((180, 330), "ENGINE 1  ·  DAILY CHECK", font=BOLD, fill=INK)
            for k, it in enumerate(items):
                y = 430 + k * 110
                d.rounded_rectangle((180, y, 240, y + 60), 10, outline=INK, width=4)
                if t > 0.7 + k * 0.3:
                    B.check(d, 186, y + 8, 46, GREEN)
                d.text((270, y + 6), it, font=CHAT, fill=INK)
            stamp(im, W / 2, 1300, "IN SERVICE", t - 3.4, col=GREEN, ang=-5, size=110)
            if t > 3.8:
                caption(d, "“Rig status: in service.”", y=1450)
            paste_c(im, kit.sm["neutral"], W / 2, 1560)
        else:
            end_card(im, d, kit, s - end0, "RIG CHECKS THAT", "ACTUALLY GET DONE.")
        return im

    encode(out, T, ev, 100, frame)


# ---------- REPLY-ALL: Kevin floods the inbox ----------

def replyall(out):
    kit = Kit()
    F0 = 3.2                      # flood starts
    FL = 6.0                      # flood length
    tw0 = F0 + FL                 # eye twitch close-up
    mad0 = tw0 + 1.6
    sol0 = mad0 + 2.6
    end0 = sol0 + 5.0
    T = end0 + 4.0
    times = []
    t, gap = F0, 0.42
    while t < F0 + FL:
        times.append(t)
        t += gap
        gap = max(0.05, gap * 0.86)
    ev = [(0.8 + i * 0.11, "type") for i in range(8)] + [(1.9, "send")]
    ev += [(x, "k") for x in times]
    ev += [(tw0, "scratch"), (tw0 + 0.4, "grrr1"), (mad0, "thud"), (mad0 + 0.1, "grrr2"), (mad0 + 0.15, "steam")]
    ev += [(sol0 + 0.2, "horn"), (sol0 + 1.6, "ding"), (end0, "send"), (end0 + 0.35, "tada")]
    rnd = random.Random(5)
    ks = [(rnd.uniform(80, W - 80), rnd.uniform(260, 1700), rnd.uniform(-25, 25), rnd.uniform(60, 170)) for _ in times]
    subj = ["RE: Station meeting Thu 1900", "RE: RE: Station meeting", "RE: RE: RE: Station meeting",
            "RE: RE: RE: RE: Station mtg", "RE: [no subject]"]

    def frame(s, f):
        im, d = blank()
        pen = Pen(d, f // 3)
        if s < F0:
            # inbox view: Roy's email goes out to ALL STATION 12
            if s >= 2.2:
                d.rectangle((0, 0, W, 240), fill=(40, 70, 140))
                d.text((60, 140), "Inbox", font=HEAVY, fill="white")
            pen.rect(60, 300, W - 60, 760, 5, fill="white")
            d.text((100, 330), "To: ALL STATION 12 (14)", font=NAME, fill=GRAY)
            d.text((100, 380), "Subject: Station meeting Thu 1900", font=BOLD, fill=INK)
            body = "Mandatory station meeting Thursday at 1900. Do not reply."
            n = len(body) if s > 1.9 else int(len(body) * max(0, s - 0.8) / 1.1)
            for k, ln in enumerate(wrap(d, body[:n], CHAT, W - 220)):
                d.text((100, 460 + k * 52), ln, font=CHAT, fill=INK)
            spr = kit.tap[int(s / 0.16) % len(kit.tap)]
            im.paste(spr, (W // 2 - spr.width // 2, H - spr.height + 14), spr)
            if s < 2.2:
                hook(d, ("WHEN THE PROBIE DISCOVERS", "REPLY-ALL…"))
                d.rectangle((0, 40, W, 230), fill=PAPER)
                hook(d, ("WHEN THE PROBIE DISCOVERS", "REPLY-ALL…"))
        elif s < tw0:
            n = sum(1 for x in times if x <= s)
            d.rectangle((0, 0, W, 240), fill=(40, 70, 140))
            d.text((60, 140), "Inbox", font=HEAVY, fill="white")
            cnt = f"{n} new"
            d.rounded_rectangle((W - 120 - d.textlength(cnt, font=BOLD), 150, W - 60, 220), 30, fill=RED)
            d.text((W - 90 - d.textlength(cnt, font=BOLD), 158), cnt, font=BOLD, fill="white")
            for k in range(min(n, 12)):  # newest rows on top
                y = 270 + k * 120
                d.rectangle((0, y, W, y + 116), fill="white")
                d.line((0, y + 116, W, y + 116), fill=(225, 225, 230), width=2)
                d.text((60, y + 14), "Kevin (probie)", font=BOLD, fill=INK)
                d.text((60, y + 66), subj[min(4, (n - k) // 4)] + "  —  k", font=SMALL, fill=GRAY)
            for k in range(n):  # flying "k"s pile up over everything
                x, y, a, sz = ks[k]
                age = s - times[k]
                from PIL import ImageFont
                fk = ImageFont.truetype(str(B.F_LOCAL / "barlow-condensed-latin-800-normal.woff"), int(sz))
                lay = Image.new("RGBA", (int(sz * 1.6), int(sz * 1.6)), (0, 0, 0, 0))
                ld = ImageDraw.Draw(lay)
                sc = min(1, age / 0.12)
                ld.rounded_rectangle((4, 4, lay.width - 4, lay.height - 4), int(sz * 0.4), fill=(225, 232, 255, 255),
                                     outline=(40, 70, 140, 255), width=5)
                ld.text((lay.width / 2 - ld.textlength("k", font=fk) / 2, lay.height * 0.12), "k", font=fk,
                        fill=(40, 70, 140))
                lay = lay.resize((max(1, int(lay.width * sc)), max(1, int(lay.height * sc)))).rotate(a, expand=True)
                im.paste(lay, (int(x - lay.width / 2), int(y - lay.height / 2)), lay)
            face = "sideeye" if n < 6 else ("bored" if n < 14 else "closed")
            paste_c(im, kit.sm[face], W - 220, 1620)
        elif s < mad0:
            # eye twitch: tight close-up on the eyes, jittering
            t = s - tw0
            src = kit.big["furious"]
            z = 1.9
            fb = src.resize((int(src.width * z), int(src.height * z)), Image.BICUBIC)
            jx = random.randint(-14, 14) if int(t * 20) % 3 == 0 else 0
            jy = random.randint(-8, 8) if int(t * 20) % 3 == 0 else 0
            im.paste(fb, (int(W / 2 - fb.width / 2) + jx, int(H * 0.5 - fb.height * 0.42) + jy), fb)
            caption(d, "*eye twitch*", y=150)
            anger(d, W / 2 + 300, 520, 2.6, s)
        elif s < sol0:
            mad_closeup(im, d, kit, s - mad0, "“Replies received: 47. Information gained: zero.”")
        elif s < end0:
            t = s - sol0
            banner(d)
            sl = min(1, t / 0.35)
            y0 = 360 - int((1 - sl) ** 2 * 300)
            pen.rect(110, y0, W - 110, y0 + 520, 6, fill="white")
            lg = kit.logo.resize((90, 90))
            im.paste(lg, (150, y0 + 30), lg)
            d.text((260, y0 + 36), "OFFICER UPDATE", font=BOLD, fill=RED)
            d.text((260, y0 + 92), "from Capt. Brisket", font=SMALL, fill=GRAY)
            for k, ln in enumerate(wrap(d, "Mandatory station meeting Thursday at 1900.", CHAT, W - 320)):
                d.text((150, y0 + 170 + k * 52), ln, font=CHAT, fill=INK)
            seen = min(14, max(0, int((t - 0.6) / 0.08)))
            d.text((150, y0 + 330), f"Seen by {seen} of 14", font=BOLD, fill=GREEN if seen == 14 else INK)
            d.text((150, y0 + 400), "Inbox: quiet.", font=SMALL, fill=GRAY)
            if t > 1.8:
                caption(d, "“Replies needed: zero. Peace restored.”", y=1000)
            paste_c(im, kit.sm["neutral"], W / 2, 1250)
        else:
            end_card(im, d, kit, s - end0, "OFFICER UPDATES,", "NO REPLY-ALL.")
        return im

    encode(out, T, ev, 15, frame)


if __name__ == "__main__":
    {"dues": dues, "roster": roster, "rigcheck": rigcheck, "replyall": replyall}[sys.argv[2]](sys.argv[1])
