"""Veterans Day 2026 vertical video for StationHQ. Public-domain DoD photos + US Army Band 'Taps'."""
import os, math, glob, subprocess, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

SRC = '/home/claude/remote/content/vets/src'
FONTS = '/home/claude/fit/fonts'
W, H, FPS = 1080, 1920, 30
GOLD = (226, 178, 72)
CREAM = (246, 238, 222)
OUT = '/home/claude/tt/out/veterans_day_2026.mp4'
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
    im = Image.fromarray(np.minimum(255, np.asarray(im, np.int16) + np.asarray(glow, np.int16) * smooth(t / 2)).astype(np.uint8))
    a1, a2, a3 = ease((t - 0.4) / 0.9), ease((t - 1.1) / 1.0), ease((t - 2.0) / 0.9)

    def dr(d):
        ctext(d, 640, 'NOVEMBER 11', OSW(56), GOLD, track=int(30 - 16 * a1), alpha=int(255 * a1))
        ctext(d, 730 + 30 * (1 - a2), 'TO ALL', ANTON(190), CREAM, track=4, alpha=int(255 * a2))
        ctext(d, 930 + 30 * (1 - a3), 'WHO SERVED', ANTON(190), CREAM, track=4, alpha=int(255 * a3))
        if a3 > 0:
            w = 520 * ease((t - 2.4) / 0.8)
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
    k1, k2 = 2 * math.pi * 1.6, 2 * math.pi * 2.7
    ph1 = k1 * u - t * 3.2
    ph2 = k2 * u - t * 4.6 + 1.3 * (y / out_h)
    amp = (0.03 + 0.06 * u) * out_h
    dy = amp * (np.sin(ph1) + 0.35 * np.sin(ph2))
    dx = 0.012 * out_w * u * np.cos(ph1)
    sx = ((x - dx) / out_w * fw).clip(0, fw - 1)
    sy = ((y - dy - out_h * 0.06) / (out_h * 0.88) * fh)
    valid = (sy >= 0) & (sy < fh)
    sy = sy.clip(0, fh - 1)
    img = FLAG[sy.astype(np.int32), sx.astype(np.int32)]
    shade = 1 + 0.32 * np.cos(ph1) * (0.4 + u) + 0.12 * np.cos(ph2)
    img = img * shade[..., None]
    alpha = valid.astype(np.float32)[..., None]
    return img.clip(0, 255), alpha


def scene_flag(t, dur, fr):
    bg = np.zeros((H, W, 3), np.float32)
    bg[:] = (8, 9, 12)
    # warm sky glow
    g = np.exp(-(((yy - 760) / 700.0) ** 2 + ((xx - W / 2) / 900.0) ** 2))[..., None]
    bg += g * np.array([70, 50, 28], np.float32)
    z = 1.0 + 0.08 * (t / dur)
    fw, fh = int(1240 * z), int(760 * z)
    img, al = wave_flag(t, fw, fh)
    x0, y0 = (W - fw) // 2, 300 - int(40 * z)
    # crop to frame
    xs0, ys0 = max(0, -x0), max(0, -y0)
    xs1, ys1 = min(fw, W - x0), min(fh, H - y0)
    a_in = smooth(t / 1.2)
    reg = bg[y0 + ys0:y0 + ys1, x0 + xs0:x0 + xs1]
    al_r = al[ys0:ys1, xs0:xs1] * a_in
    reg[:] = reg * (1 - al_r) + img[ys0:ys1, xs0:xs1] * al_r
    im = Image.fromarray(bg.clip(0, 255).astype(np.uint8))
    im = finish(im, fr).convert('RGBA')
    a = ease((t - 1.4) / 1.0)
    b = ease((t - 2.6) / 1.0)
    c = ease((t - 4.0) / 1.0)

    def dr(d):
        ctext(d, 1180 + 30 * (1 - a), 'THANK YOU', ANTON(200), CREAM, track=6, alpha=int(255 * a))
        w = 560 * b
        d.rectangle((W / 2 - w / 2, 1450, W / 2 + w / 2, 1456), fill=GOLD + (255,))
        ctext(d, 1490 + 20 * (1 - b), 'FOR YOUR SERVICE', OSW(72), GOLD, track=12, alpha=int(255 * b))
        ctext(d, 1620, 'Every branch. Every era. Every one of you.', OSW(42), CREAM, alpha=int(230 * c))
    im.alpha_composite(text_layer(dr))
    return im.convert('RGB')


LOGO = Image.open('/home/claude/remote/brand/logo_badge.png').convert('RGBA')
LOGO.thumbnail((660, 660))


def scene_outro(t, dur, fr):
    im = Image.new('RGB', (W, H), (8, 8, 10))
    im = finish(im, fr, grad=False).convert('RGBA')
    a = ease(t / 0.9)
    lg = LOGO.copy()
    lg.putalpha(Image.fromarray((np.asarray(lg.getchannel('A'), np.float32) * a).astype(np.uint8)))
    im.alpha_composite(lg, ((W - lg.width) // 2, 480 + int(30 * (1 - a))))
    b = ease((t - 0.7) / 0.9)

    def dr(d):
        ctext(d, 1190, 'FROM ALL OF US AT', OSW(48), GOLD, track=10, alpha=int(255 * b))
        ctext(d, 1260, 'STATIONHQ', ANTON(140), CREAM, track=6, alpha=int(255 * b))
        ctext(d, 1460, 'Built by an active firefighter', OSW(42), CREAM, alpha=int(200 * ease((t - 1.4) / 0.8)))
    im.alpha_composite(text_layer(dr))
    # fade to black at end
    fo = smooth((t - (dur - 1.2)) / 1.2)
    out = Image.blend(im.convert('RGB'), Image.new('RGB', (W, H), 0), fo)
    return out


# timeline (seconds) aligned to Taps phrase breaks: 14.9, 29.7, 45.6, 58.3
SCENES = [
    (scene_intro, 4.6),
    (make_photo_scene('army_2.jpg', 0.47, 0.53, 'U.S. ARMY', 'EST. 1775'), 3.8),
    (make_photo_scene('marines_2.jpg', 0.44, 0.47, 'U.S. MARINE CORPS', 'EST. 1775', z0=0.9, z1=1.0), 3.8),
    (make_photo_scene('navy_0.jpg', 0.36, 0.28, 'U.S. NAVY', 'EST. 1775'), 3.8),
    (make_photo_scene('airforce_1.jpg', 0.5, 0.5, 'U.S. AIR FORCE', 'EST. 1947', z0=0.95, z1=1.1), 3.8),
    (make_photo_scene('spaceforce_1.jpg', 0.55, 0.52, 'U.S. SPACE FORCE', 'EST. 2019'), 3.8),
    (make_photo_scene('coastguard_0.jpg', 0.30, 0.36, 'U.S. COAST GUARD', 'EST. 1790'), 3.6),
    (make_photo_scene('army_0.jpg', 0.42, 0.5, 'GUARD & RESERVE', 'ALWAYS READY', small='Citizen soldiers, sailors, airmen & Marines', z0=0.95, z1=1.08), 3.2),
    (two_line_scene('marines_0.jpg', 0.36, 0.33, z0=0.9, z1=0.99, l1= 'TO EVERY VETERAN', l2='WE OWE YOU', l3='MORE THAN WORDS.'), 7.9),
    (two_line_scene('firefighter_1.jpg', 0.55, 0.5, 'SO MANY OF YOU CAME HOME', 'AND KEPT', 'ANSWERING THE CALL.'), 8.0),
    (scene_flag, 11.0),
    (scene_outro, 5.0),
]
XF = 0.6
KINDS = ['zoom', 'whip']
SOFT = {8, 10}   # veteran + flag scenes dissolve in


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
        if idx in SOFT and lt < 0.8:   # slow dissolve from previous for emotional beats
            pfn, pdur = SCENES[idx - 1]
            img = Image.blend(pfn(pdur, pdur, fr), img, smooth(lt / 0.8))
        img.save(f'{TMP}/{fr:05d}.jpg', quality=90)
        if fr % 150 == 0:
            print(fr, '/', n, flush=True)
    taps = glob.glob(f'{SRC}/taps_4.*')[0]
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(FPS), '-i', f'{TMP}/%05d.jpg',
                    '-i', taps, '-t', f'{total:.2f}',
                    '-af', f'adelay=900|900,volume=1.15,afade=t=out:st={total-2.5:.2f}:d=2.5',
                    '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '23', '-maxrate', '9M', '-bufsize', '18M', '-pix_fmt', 'yuv420p',
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
