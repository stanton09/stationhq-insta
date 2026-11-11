"""Veterans Day 2026 vertical video for StationHQ. Public-domain DoD photos + US Army Band 'Taps'."""
import os, math, glob, subprocess, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

SRC = '/home/claude/remote/content/vets/src'
FONTS = '/home/claude/fit/fonts'
W, H, FPS = 1080, 1920, 30
GOLD = (226, 178, 72)
CREAM = (246, 238, 222)
OUT = '/home/claude/tt/out/veterans_day_2026_v4.mp4'
TMP = '/tmp/vets_frames'


def F(name, size):
    return ImageFont.truetype(os.path.join(FONTS, name), size)


ANTON = lambda s: F('Anton-Regular.ttf', s)
OSW = lambda s: F('Oswald.ttf', s)


def ease(t):
    t = max(0, min(1, t))
    return 1 - (1 - t) ** 3


def smooth(t):
    t = max(0, min(1, t))
    return t * t * (3 - 2 * t)


# ---------- grading / overlays ----------
rng = np.random.default_rng(3)
GRAIN = [rng.normal(0, 5, (H // 2, W // 2)).astype(np.float32) for _ in range(6)]
yy, xx = np.mgrid[0:H, 0:W]
VIG = (1 - 0.55 * (((xx - W / 2) / (W * 0.75)) ** 2 + ((yy - H / 2) / (H * 0.62)) ** 2)).clip(0.25, 1).astype(np.float32)[..., None]
GRAD = np.ones((H, W, 1), np.float32)
g0 = 1100
GRAD[g0:] = (1 - 0.82 * ((np.arange(H - g0) / (H - g0)) ** 0.9))[:, None, None]
GRAD[:260] *= (0.45 + 0.55 * (np.arange(260) / 260))[:, None, None]


def finish(im, fr, grad=True):
    a = np.asarray(im, np.float32)
    a = a * VIG
    if grad:
        a = a * GRAD
    g = GRAIN[fr % 6]
    g = np.repeat(np.repeat(g, 2, 0), 2, 1)[..., None]
    a = (a + g).clip(0, 255).astype(np.uint8)
    return Image.fromarray(a)


def grade(img):
    img = ImageEnhance.Color(img).enhance(0.72)
    img = ImageEnhance.Contrast(img).enhance(1.12)
    a = np.asarray(img, np.float32)
    a[..., 0] *= 1.04
    a[..., 2] *= 0.94
    return Image.fromarray(a.clip(0, 255).astype(np.uint8))


PHOTO_CACHE = {}


def photo(name):
    if name not in PHOTO_CACHE:
        im = Image.open(f'{SRC}/{name}').convert('RGB')
        s = (H * 1.16) / im.height
        im = im.resize((int(im.width * s), int(H * 1.16)), Image.LANCZOS)
        PHOTO_CACHE[name] = grade(im)
    return PHOTO_CACHE[name]


def kenburns(name, t, fx0, fx1, z0=1.0, z1=1.1):
    """t in 0..1, focus x fraction moves fx0->fx1, zoom z0->z1."""
    im = photo(name)
    z = z0 + (z1 - z0) * t
    ch = im.height / 1.12 / z
    cw = ch * W / H
    fx = fx0 + (fx1 - fx0) * t
    cx = fx * im.width
    cy = im.height / 2
    x0 = min(max(cx - cw / 2, 0), im.width - cw)
    y0 = min(max(cy - ch / 2, 0), im.height - ch)
    return im.transform((W, H), Image.EXTENT, (x0, y0, x0 + cw, y0 + ch), Image.BICUBIC)


def ctext(d, y, s, f, fill, track=0, alpha=255, shadow=True):
    chars = list(s)
    widths = [d.textlength(c, font=f) for c in chars]
    total = sum(widths) + track * (len(chars) - 1)
    x = (W - total) / 2
    for c, w in zip(chars, widths):
        if shadow:
            d.text((x + 3, y + 4), c, font=f, fill=(0, 0, 0, int(alpha * 0.8)))
        d.text((x, y), c, font=f, fill=fill + (alpha,))
        x += w + track
    return total


def text_layer(draw_fn):
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    draw_fn(ImageDraw.Draw(lay))
    return lay


def header(d, a):
    ctext(d, 120, 'VETERANS DAY  ·  11.11.2026', OSW(34), CREAM, track=6, alpha=int(170 * a), shadow=False)


def slam(lay, t):
    """title slams in: big->normal in 0.2s, then shake + RGB split decays"""
    if t < 0 or t > 0.6:
        return lay
    k = ease(t / 0.2)
    sc = 1.5 - 0.5 * k
    if sc != 1:
        w2, h2 = int(W * sc), int(H * sc)
        big = lay.resize((w2, h2), Image.BILINEAR)
        cx, cy = w2 / 2, 1520 * sc
        lay = big.crop((int(cx - W / 2), int(cy - 1520), int(cx - W / 2) + W, int(cy - 1520) + H))
    amp = 14 * max(0, 1 - t / 0.6)
    a = np.asarray(lay).copy()
    if amp > 1:
        sh = int(amp)
        r = np.roll(a, sh, axis=1); b = np.roll(a, -sh, axis=1)
        a[..., 0] = np.maximum(a[..., 0], r[..., 0] * (r[..., 3] > 0))
        a[..., 2] = np.maximum(a[..., 2], b[..., 2] * (b[..., 3] > 0))
        a[..., 3] = np.maximum(a[..., 3], np.maximum(r[..., 3], b[..., 3]) // 2)
        a = np.roll(a, (int(amp * math.sin(t * 90)), int(amp * math.cos(t * 70))), axis=(0, 1))
    return Image.fromarray(a)


# ---------- transitions ----------
LEAK = None


def leak():
    global LEAK
    if LEAK is None:
        g = np.zeros((H, W, 3), np.float32)
        a = np.exp(-(((xx - W * 0.85) / 500.0) ** 2 + ((yy - H * 0.3) / 900.0) ** 2))
        b = np.exp(-(((xx - W * 0.1) / 400.0) ** 2 + ((yy - H * 0.75) / 600.0) ** 2))
        g += a[..., None] * np.array([255, 140, 40]) + b[..., None] * np.array([255, 60, 30]) * 0.8
        LEAK = g
    return LEAK


def zoom_blur(img, amount, n=6):
    """radial blur by averaging progressively zoomed copies"""
    if amount < 0.01:
        return img
    acc = np.zeros((H, W, 3), np.float32)
    for i in range(n):
        z = 1 + amount * i / (n - 1)
        w2, h2 = int(W * z), int(H * z)
        c = img.resize((w2, h2), Image.BILINEAR).crop(((w2 - W) // 2, (h2 - H) // 2, (w2 - W) // 2 + W, (h2 - H) // 2 + H))
        acc += np.asarray(c, np.float32)
    return Image.fromarray((acc / n).astype(np.uint8))


def whip(img, amount, direction=1):
    """horizontal motion-blur whip pan"""
    a = np.asarray(img, np.float32)
    off = int(amount * W * 0.9) * direction
    a = np.roll(a, off, axis=1)
    acc = np.zeros_like(a)
    n = 8
    step = max(1, int(amount * 140))
    for i in range(n):
        acc += np.roll(a, i * step * direction, axis=1)
    return Image.fromarray((acc / n).astype(np.uint8))


def transition(img, p, kind, side):
    """p: 0 at window edge -> 1 at the cut. side -1 outgoing, +1 incoming"""
    e = p ** 2
    if kind == 'zoom':
        z = 0.55 * e
        if side < 0:
            w2, h2 = int(W * (1 + z)), int(H * (1 + z))
            img = img.resize((w2, h2), Image.BILINEAR).crop(((w2 - W) // 2, (h2 - H) // 2, (w2 - W) // 2 + W, (h2 - H) // 2 + H))
        else:
            # incoming settles from slightly zoomed in
            w2, h2 = int(W * (1 + z * 0.6)), int(H * (1 + z * 0.6))
            img = img.resize((w2, h2), Image.BILINEAR).crop(((w2 - W) // 2, (h2 - H) // 2, (w2 - W) // 2 + W, (h2 - H) // 2 + H))
        img = zoom_blur(img, 0.25 * e)
    elif kind == 'whip':
        img = whip(img, 0.45 * e, side * -1)
    # flash + light leak peak at the cut
    a = np.asarray(img, np.float32)
    lk = leak() * (0.9 * e)
    a = 255 - (255 - a) * (255 - lk) / 255   # screen
    a = a + (255 - a) * (0.55 * e ** 3)       # white flash
    return Image.fromarray(a.clip(0, 255).astype(np.uint8))


# ---------- scenes ----------
def scene_intro(t, dur, fr):
    """black -> stars + title"""
    im = Image.new('RGB', (W, H), (6, 7, 10))
    d = ImageDraw.Draw(im)
    r = random.Random(11)
    for _ in range(260):
        x, y = r.random() * W, r.random() * H
        tw = 0.5 + 0.5 * math.sin(t * 2 + r.random() * 6.28)
        c = int(60 + 120 * tw * r.random())
        y = (y - t * 30) % H
        d.point((x, y), fill=(c, c, c + 10))
    glow = Image.new('RGB', (W, H), 0)
    ImageDraw.Draw(glow).ellipse((W / 2 - 500, 760 - 300, W / 2 + 500, 760 + 300), fill=(90, 60, 25))
    glow = glow.filter(ImageFilter.GaussianBlur(160))
    im = Image.fromarray(np.minimum(255, np.asarray(im, np.int16) + np.asarray(glow, np.int16) * smooth(t / 1)).astype(np.uint8))
    a1, a2, a3 = ease((t - 0.1) / 0.45), ease((t - 0.45) / 0.5), ease((t - 0.9) / 0.5)

    def dr(d):
        ctext(d, 640, 'NOVEMBER 11', OSW(56), GOLD, track=int(30 - 16 * a1), alpha=int(255 * a1))
        ctext(d, 730 + 30 * (1 - a2), 'TO ALL', ANTON(190), CREAM, track=4, alpha=int(255 * a2))
        ctext(d, 930 + 30 * (1 - a3), 'WHO SERVED', ANTON(190), CREAM, track=4, alpha=int(255 * a3))
        if a3 > 0:
            w = 520 * ease((t - 1.2) / 0.5)
            d.rectangle((W / 2 - w / 2, 1180, W / 2 + w / 2, 1186), fill=GOLD + (255,))
    im = im.convert('RGBA')
    im.alpha_composite(text_layer(dr))
    return finish(im.convert('RGB'), fr, grad=False)


def make_photo_scene(name, fx0, fx1, title, sub, z0=1.0, z1=1.1, small=None, ty=1440):
    def sc(t, dur, fr):
        u = t / dur
        im = kenburns(name, u, fx0, fx1, z0, z1)
        im = finish(im, fr).convert('RGBA')
        a = ease((t - 0.35) / 0.7)
        b = ease((t - 0.75) / 0.7)
        out = ease((t - (dur - 0.5)) / 0.5)

        def dr(d):
            header(d, 1)
            fs = 150 if len(title) <= 12 else 118
            a2 = 1.0 if t > 0.35 else 0.0
            ctext(d, ty, title, ANTON(fs), CREAM, track=3, alpha=int(255 * a2 * (1 - out)))
            w = 380 * b * (1 - out)
            yy = ty + fs * 1.42
            d.rectangle((W / 2 - w / 2, yy, W / 2 + w / 2, yy + 5), fill=GOLD + (int(255 * (1 - out)),))
            ctext(d, yy + 28, sub, OSW(50), GOLD, track=10, alpha=int(255 * b * (1 - out)))
            if small:
                ctext(d, yy + 110, small, OSW(40), CREAM, track=2, alpha=int(220 * ease((t - 1.3) / 0.8) * (1 - out)))
        lay = text_layer(dr)
        im.alpha_composite(slam(lay, t - 0.35))
        return im.convert('RGB')
    return sc


def two_line_scene(name, fx0, fx1, l1, l2, l3=None, z0=1.0, z1=1.12):
    def sc(t, dur, fr):
        im = kenburns(name, t / dur, fx0, fx1, z0, z1)
        im = finish(im, fr).convert('RGBA')
        a = ease((t - 0.4) / 0.9)
        b = ease((t - 1.6) / 0.9)
        c = ease((t - 3.0) / 0.9)

        def dr(d):
            header(d, 1)
            ctext(d, 1300 + 30 * (1 - a), l1, OSW(64), GOLD, track=8, alpha=int(255 * a))
            ctext(d, 1400 + 30 * (1 - b), l2, ANTON(116), CREAM, track=3, alpha=int(255 * b))
            if l3:
                ctext(d, 1580 + 30 * (1 - c), l3, ANTON(116), CREAM, track=3, alpha=int(255 * c))
        im.alpha_composite(text_layer(dr))
        return im.convert('RGB')
    return sc


def fit(text, fontfn, size, maxw=990):
    d = ImageDraw.Draw(Image.new('L', (1, 1)))
    while size > 40 and d.textlength(text, font=fontfn(size)) > maxw:
        size -= 4
    return fontfn(size)


def words_line(d, y, text, f, fill, t0, t, alpha_mul=1.0, step=0.16):
    """reveal a centered line word by word starting at t0"""
    words = text.split(' ')
    sp = d.textlength(' ', font=f)
    ws = [d.textlength(w, font=f) for w in words]
    x = (W - (sum(ws) + sp * (len(words) - 1))) / 2
    for i, (w, wl) in enumerate(zip(words, ws)):
        a = ease((t - t0 - i * step) / 0.45) * alpha_mul
        if a > 0:
            dy = 18 * (1 - a)
            d.text((x + 3, y + 4 + dy), w, font=f, fill=(0, 0, 0, int(200 * a)))
            d.text((x, y + dy), w, font=f, fill=fill + (int(255 * a),))
        x += wl + sp
    return t0 + len(words) * step


def heart_scene(name, fx0, fx1, small, big, tail=None, z0=0.92, z1=1.04, desat=False, y0=1230):
    def sc(t, dur, fr):
        im = kenburns(name, t / dur, fx0, fx1, z0, z1)
        if desat:
            im = ImageEnhance.Color(im).enhance(0.15)
        im = finish(im, fr).convert('RGBA')
        out = smooth((t - (dur - 0.6)) / 0.6)

        def dr(d):
            header(d, 1)
            k = 1 - out * 0.0
            nt = words_line(d, y0, small, OSW(58), GOLD, 0.25, t, k, step=0.1)
            y = y0 + 100
            for line in big:
                f = fit(line, ANTON, 124)
                nt = words_line(d, y, line, f, CREAM, nt + 0.1, t, k, step=0.14)
                y += f.size * 1.18
            if tail:
                words_line(d, y + 20, tail, fit(tail, OSW, 46), CREAM, nt + 0.15, t, k, step=0.08)
        im.alpha_composite(text_layer(dr))
        return im.convert('RGB')
    return sc


# ---------- waving flag ----------
def flag_image(fw=2280, fh=1200):
    im = Image.new('RGB', (fw, fh), (255, 255, 255))
    d = ImageDraw.Draw(im)
    sh = fh / 13
    red, blue, white = (178, 34, 52), (60, 59, 110), (245, 245, 240)
    for i in range(13):
        d.rectangle((0, i * sh, fw, (i + 1) * sh), fill=red if i % 2 == 0 else white)
    cw, ch = fw * 0.4, sh * 7
    d.rectangle((0, 0, cw, ch), fill=blue)
    R = sh * 0.616 / 2 * 0.9

    def star(cx, cy):
        pts = []
        for k in range(10):
            rr = R if k % 2 == 0 else R * 0.382
            ang = -math.pi / 2 + k * math.pi / 5
            pts.append((cx + rr * math.cos(ang), cy + rr * math.sin(ang)))
        d.polygon(pts, fill=white)
    gx, gy = cw / 12, ch / 10
    for row in range(9):
        for col in range(11):
            if (row + col) % 2 == 0:
                star(gx * (col + 1), gy * (row + 1))
    return np.asarray(im, np.float32)


FLAG = flag_image()


def wave_flag(t, out_w, out_h):
    fh, fw = FLAG.shape[:2]
    y, x = np.mgrid[0:out_h, 0:out_w].astype(np.float32)
    u = x / out_w
    v = y / out_h
    ph1 = 2 * math.pi * 1.35 * u - t * 3.0 + 0.6 * v
    ph2 = 2 * math.pi * 2.9 * u - t * 4.7 + 1.8 * v
    ph3 = 2 * math.pi * 5.5 * u - t * 6.8 - 2.2 * v
    env = u ** 0.8
    amp = out_h * (0.12 * np.sin(ph1) + 0.045 * np.sin(ph2) + 0.014 * np.sin(ph3)) * env
    droop = out_h * 0.05 * u ** 2
    dx = out_w * 0.02 * env * np.cos(ph1)
    sx = ((x - dx) / out_w * fw).clip(0, fw - 1)
    sy = (y - amp - droop - out_h * 0.1) / (out_h * 0.8) * fh
    valid = (sy >= 0) & (sy < fh) & (x - dx < out_w)
    sy = sy.clip(0, fh - 1)
    img = FLAG[sy.astype(np.int32), sx.astype(np.int32)]
    # slope-based lighting: folds facing the light are brighter, creases darker
    slope = (0.12 * 1.35 * np.cos(ph1) + 0.045 * 2.9 * np.cos(ph2) + 0.014 * 5.5 * np.cos(ph3)) * env
    light = 1 + 2.4 * slope
    spec = np.clip(slope * 9 - 0.25, 0, 1) ** 2 * 70
    weave = (np.sin(x * 2.1) * np.sin(y * 2.3)) * 4
    img = img * light[..., None] + spec[..., None] + weave[..., None]
    alpha = valid.astype(np.float32)[..., None]
    # soft edges
    return img.clip(0, 255), alpha


SKY = None


def sky():
    global SKY
    if SKY is None:
        t = (yy / H).astype(np.float32)[..., None]
        top = np.array([10, 14, 32], np.float32)
        mid = np.array([70, 42, 48], np.float32)
        low = np.array([235, 130, 50], np.float32)
        a = np.where(t < 0.55, top + (mid - top) * (t / 0.55), mid + (low - mid) * ((t - 0.55) / 0.45))
        sun = np.exp(-(((xx - W * 0.72) / 330.0) ** 2 + ((yy - 1150) / 330.0) ** 2))[..., None]
        a = a + sun * np.array([255, 190, 110]) * 0.9
        # god rays
        ang = np.arctan2(yy - 1150, xx - W * 0.72)
        rays = ((0.5 + 0.5 * np.sin(ang * 7 + 0.5)) * (0.6 + 0.4 * np.sin(ang * 13))) ** 2 * np.exp(-np.hypot(yy - 1150, xx - W * 0.72) / 650)
        a = a + rays[..., None] * np.array([255, 190, 120]) * 0.22
        a = np.asarray(Image.fromarray(a.clip(0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(18)), np.float32)
        # dark ground silhouette at bottom
        ground = np.clip((yy - 1700) / 40, 0, 1)[..., None]
        a = a * (1 - ground) + ground * np.array([12, 10, 10])
        SKY = a.astype(np.float32)
    return SKY


EMBERS = [(random.Random(i).random() * W, random.Random(i + 99).random() * H, random.Random(i + 7).random()) for i in range(70)]


def scene_flag(t, dur, fr):
    bg = sky().copy()
    z = 1.0 + 0.07 * (t / dur)
    # pole
    px = int(150 * z) - 30
    top = int(250 - 60 * z)
    pole_w = 26
    for i in range(pole_w):
        sh = 0.45 + 0.55 * math.sin(math.pi * i / pole_w)
        bg[top:1720, px + i] = np.array([205, 190, 160]) * sh
    # finial
    fy = top - 26
    fin = np.hypot(xx - (px + pole_w / 2), yy - fy) < 30
    hl = np.exp(-np.hypot(xx - (px + pole_w / 2 - 9), yy - (fy - 9)) / 10)
    bg[fin] = (np.array([210, 160, 50]) * (0.7 + 0.6 * hl[fin][:, None]))
    fw, fh = int(1060 * z), int(640 * z)
    img, al = wave_flag(t, fw, fh)
    x0, y0 = px + pole_w - 2, top + 10
    xs1, ys1 = min(fw, W - x0), min(fh, H - y0)
    a_in = smooth(t / 0.4)
    reg = bg[y0:y0 + ys1, x0:x0 + xs1]
    al_r = al[:ys1, :xs1] * a_in
    # backlit glow: fabric closer to the sun picks up warmth
    glowmap = sky()[y0:y0 + ys1, x0:x0 + xs1] / 255.0
    fab = img[:ys1, :xs1] * (0.78 + 0.35 * glowmap)
    reg[:] = reg * (1 - al_r) + fab * al_r
    # embers
    for ex, ey, r in EMBERS:
        yv = (ey - t * (40 + 80 * r)) % H
        xv = (ex + 20 * math.sin(t * 1.5 + r * 6)) % W
        rad = 2 + 3 * r
        x1, x2, y1, y2 = int(xv - 6), int(xv + 7), int(yv - 6), int(yv + 7)
        if 0 <= x1 and x2 < W and 0 <= y1 and y2 < H:
            g = np.exp(-((xx[y1:y2, x1:x2] - xv) ** 2 + (yy[y1:y2, x1:x2] - yv) ** 2) / (rad ** 2))[..., None]
            bg[y1:y2, x1:x2] += g * np.array([255, 170, 70]) * (0.5 + 0.5 * r)
    im = Image.fromarray(bg.clip(0, 255).astype(np.uint8))
    im = finish(im, fr).convert('RGBA')
    a = ease((t - 0.5) / 0.6)
    b = ease((t - 1.1) / 0.6)
    c = ease((t - 1.8) / 0.7)

    def dr(d):
        ctext(d, 1200 + 30 * (1 - a), 'THANK YOU', ANTON(200), CREAM, track=6, alpha=int(255 * a))
        w = 560 * b
        d.rectangle((W / 2 - w / 2, 1478, W / 2 + w / 2, 1484), fill=GOLD + (255,))
        ctext(d, 1510 + 20 * (1 - b), 'FOR YOUR SERVICE', OSW(72), GOLD, track=12, alpha=int(255 * b))
        ctext(d, 1640, 'Every branch. Every era. Every one of you.', OSW(42), CREAM, alpha=int(230 * c))
    im.alpha_composite(text_layer(dr))
    return im.convert('RGB')


LOGO = Image.open('/home/claude/remote/brand/logo_badge.png').convert('RGBA')
LOGO.thumbnail((660, 660))


def scene_outro(t, dur, fr):
    im = Image.new('RGB', (W, H), (8, 8, 10))
    im = finish(im, fr, grad=False).convert('RGBA')
    a = ease(t / 0.5)
    lg = LOGO.copy()
    lg.putalpha(Image.fromarray((np.asarray(lg.getchannel('A'), np.float32) * a).astype(np.uint8)))
    im.alpha_composite(lg, ((W - lg.width) // 2, 480 + int(30 * (1 - a))))
    b = ease((t - 0.35) / 0.5)

    def dr(d):
        ctext(d, 1190, 'FROM ALL OF US AT', OSW(48), GOLD, track=10, alpha=int(255 * b))
        ctext(d, 1260, 'STATIONHQ', ANTON(140), CREAM, track=6, alpha=int(255 * b))
        ctext(d, 1460, 'Built by an active firefighter', OSW(42), CREAM, alpha=int(200 * ease((t - 0.8) / 0.5)))
    im.alpha_composite(text_layer(dr))
    # fade to black at end
    fo = smooth((t - (dur - 0.5)) / 0.5)
    out = Image.blend(im.convert('RGB'), Image.new('RGB', (W, H), 0), fo)
    return out


# timeline (seconds) aligned to Taps phrase breaks: 14.9, 29.7, 45.6, 58.3
SCENES = [
    (scene_intro, 2.6),
    (make_photo_scene('army_2.jpg', 0.47, 0.53, 'U.S. ARMY', 'EST. 1775'), 2.3),
    (make_photo_scene('marines_2.jpg', 0.44, 0.47, 'U.S. MARINE CORPS', 'EST. 1775', z0=0.9, z1=1.0), 2.3),
    (make_photo_scene('navy_0.jpg', 0.36, 0.28, 'U.S. NAVY', 'EST. 1775'), 2.3),
    (make_photo_scene('airforce_1.jpg', 0.5, 0.5, 'U.S. AIR FORCE', 'EST. 1947', z0=0.95, z1=1.1), 2.3),
    (make_photo_scene('spaceforce_1.jpg', 0.55, 0.52, 'U.S. SPACE FORCE', 'EST. 2019'), 2.3),
    (make_photo_scene('coastguard_0.jpg', 0.30, 0.36, 'U.S. COAST GUARD', 'EST. 1790'), 2.3),
    (make_photo_scene('army_0.jpg', 0.42, 0.5, 'GUARD & RESERVE', 'ALWAYS READY', small='Citizen soldiers, sailors, airmen & Marines', z0=0.95, z1=1.08), 2.3),
    (heart_scene('salute_2.jpg', 0.55, 0.5, 'EVERY VETERAN', ['WROTE A BLANK CHECK'], 'payable to the United States of America', z0=0.9, z1=1.02), 4.2),
    (heart_scene('marines_0.jpg', 0.35, 0.33, 'FOR AN AMOUNT', ['UP TO AND INCLUDING', 'THEIR LIFE.'], z0=0.9, z1=1.0, desat=True), 4.2),
    (heart_scene('firefighter_1.jpg', 0.55, 0.5, 'SO MANY CAME HOME', ['AND KEPT', 'ANSWERING THE CALL.']), 3.7),
    (heart_scene('salute_0.jpg', 0.45, 0.5, 'IF YOU KNOW A VETERAN', ['TELL THEM', 'THANK YOU TODAY.']), 3.5),
    (scene_flag, 5.0),
    (scene_outro, 2.8),
]
XF = 0.6
KINDS = ['zoom', 'whip']
SOFT = {8, 9, 10, 11}   # veteran + flag scenes dissolve in


def build():
    os.makedirs(TMP, exist_ok=True)
    for f in glob.glob(f'{TMP}/*.jpg'):
        os.remove(f)
    starts, s = [], 0.0
    for fn, dur in SCENES:
        starts.append(s)
        s += dur
    total = s
    n = int(total * FPS)
    for fr in range(n):
        T = fr / FPS
        idx = max(i for i, st in enumerate(starts) if st <= T)
        fn, dur = SCENES[idx]
        lt = T - starts[idx]
        img = fn(lt, dur, fr)
        HW = 0.28
        kind = KINDS[idx % len(KINDS)]
        if idx + 1 < len(SCENES) and lt > dur - HW and idx + 1 not in SOFT:
            img = transition(img, (lt - (dur - HW)) / HW, kind, -1)
        if idx > 0 and lt < HW and idx not in SOFT:
            img = transition(img, 1 - lt / HW, KINDS[(idx - 1) % len(KINDS)], 1)
        if idx in SOFT and lt < 0.5:   # slow dissolve from previous for emotional beats
            pfn, pdur = SCENES[idx - 1]
            img = Image.blend(pfn(pdur, pdur, fr), img, smooth(lt / 0.5))
        img.save(f'{TMP}/{fr:05d}.jpg', quality=90)
        if fr % 150 == 0:
            print(fr, '/', n, flush=True)
    if os.environ.get('NOMUSIC'):
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(FPS), '-i', f'{TMP}/%05d.jpg',
                        '-f', 'lavfi', '-i', 'anullsrc=r=44100:cl=stereo', '-t', f'{total:.2f}',
                        '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '24', '-maxrate', '7M', '-bufsize', '14M', '-pix_fmt', 'yuv420p',
                        '-c:a', 'aac', '-b:a', '96k', '-shortest', '-movflags', '+faststart', OUT.replace('.mp4', '_nomusic.mp4')], check=True)
        print('done', total); return
    hs = starts[8]; fe = starts[12]; outro = starts[13]
    mstart = 210.6 - outro
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-ss', f'{mstart:.2f}', '-i', f'{SRC}/med_1.mp3', '-t', f'{total:.2f}',
                    '-ac', '2', '-ar', '44100', '-f', 'f32le', '/tmp/m.raw'], check=True)
    a = np.fromfile('/tmp/m.raw', np.float32).reshape(-1, 2)
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'f32le', '-ac', '2', '-ar', '44100', '-i', '/tmp/m.raw',
                    '-af', 'lowpass=f=700,lowpass=f=700,aecho=0.8:0.7:60:0.3', '-f', 'f32le', '/tmp/ml.raw'], check=True)
    lp = np.fromfile('/tmp/ml.raw', np.float32).reshape(-1, 2)[:len(a)]
    tt = np.arange(len(a)) / 44100.0
    m = np.clip((tt - (hs - 0.6)) / 1.2, 0, 1) * np.clip((fe - tt) / 0.35, 0, 1)   # 1 = muffled
    m = m * m * (3 - 2 * m)
    vol = 1.15 * (1 - m) + 0.55 * m
    vol *= np.clip(tt / 0.6, 0, 1)
    vol *= np.clip((total - tt) / 1.5, 0, 1) * 0 + 1
    mix = (a * (1 - m)[:, None] + lp * m[:, None]) * vol[:, None]
    mix.clip(-1, 1).astype(np.float32).tofile('/tmp/mix.raw')
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(FPS), '-i', f'{TMP}/%05d.jpg',
                    '-f', 'f32le', '-ac', '2', '-ar', '44100', '-i', '/tmp/mix.raw', '-t', f'{total:.2f}',
                    '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '24', '-maxrate', '7M', '-bufsize', '14M', '-pix_fmt', 'yuv420p',
                    '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', OUT], check=True)
    print(OUT, total)


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'stills':
        # preview stills at chosen times
        starts, s = [], 0.0
        for fn, dur in SCENES:
            starts.append(s); s += dur
        for i, (fn, dur) in enumerate(SCENES):
            fn(dur * 0.7, dur, 0).save(f'/tmp/vs_{i:02d}.jpg', quality=85)
    else:
        build()
