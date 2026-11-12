"""StationHQ x RecycledFirefighter giveaway carousel (1080x1350) + story (1080x1920)."""
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import numpy as np, os

W, H = 1080, 1350
SRC = '/home/claude/remote/brand/giveaway/Sergeant-Wallet-Hypalon-Edition-'
FONTS = '/home/claude/fit/fonts'
OUT = '/home/claude/tt/out/giveaway'
os.makedirs(OUT, exist_ok=True)
ORANGE = (255, 90, 20)
ORANGE2 = (255, 140, 40)
CREAM = (246, 238, 222)
GOLD = (255, 179, 71)
DARK = (14, 13, 12)

ANTON = lambda s: ImageFont.truetype(f'{FONTS}/Anton-Regular.ttf', s)
OSW = lambda s, w=600: _osw(s, w)


def _osw(s, w):
    f = ImageFont.truetype(f'{FONTS}/Oswald.ttf', s)
    try:
        f.set_variation_by_axes([w])
    except Exception:
        pass
    return f


LOGO = Image.open('/home/claude/remote/brand/logo_badge.png').convert('RGBA')


def photo(name, size, focus=(0.5, 0.5)):
    im = Image.open(SRC + name + '.webp').convert('RGB')
    tw, th = size
    s = max(tw / im.width, th / im.height)
    im = im.resize((int(im.width * s) + 1, int(im.height * s) + 1), Image.LANCZOS)
    x = int((im.width - tw) * focus[0]); y = int((im.height - th) * focus[1])
    im = im.crop((x, y, x + tw, y + th))
    im = ImageEnhance.Contrast(im).enhance(1.06)
    return im


def ctext(d, y, s, f, fill, track=0, shadow=True, x0=0, w=W):
    ws = [d.textlength(c, font=f) for c in s]
    total = sum(ws) + track * (len(s) - 1)
    x = x0 + (w - total) / 2
    for c, cw in zip(s, ws):
        if shadow:
            d.text((x + 3, y + 4), c, font=f, fill=(0, 0, 0, 170))
        d.text((x, y), c, font=f, fill=fill)
        x += cw + track
    return total


def grad(im, top=0, bottom=1, start=0.45, strength=0.92):
    a = np.asarray(im, np.float32)
    h = a.shape[0]
    t = np.clip((np.arange(h) / h - start) / (1 - start), 0, 1) ** 1.2
    m = 1 - strength * t
    a = a * m[:, None, None]
    return Image.fromarray(a.astype(np.uint8))


def badge(d, cx, y, text, f, pad=(26, 12), fill=ORANGE, color=(255, 255, 255)):
    tw = d.textlength(text, font=f)
    bb = f.getbbox(text)
    h = bb[3] - bb[1]
    d.rounded_rectangle((cx - tw / 2 - pad[0], y, cx + tw / 2 + pad[0], y + h + pad[1] * 2), radius=(h + pad[1] * 2) // 2, fill=fill)
    d.text((cx - tw / 2, y + pad[1] - bb[1]), text, font=f, fill=color)


def frame(d):
    d.rectangle((0, 0, W - 1, 11), fill=ORANGE)


def logos_row(im, y, size=86):
    d = ImageDraw.Draw(im)
    lg = LOGO.copy(); lg.thumbnail((size, size))
    f = OSW(30, 600)
    t1, t2 = 'STATIONHQ', 'RECYCLEDFIREFIGHTER®'
    x_w = d.textlength(' × ', font=f)
    total = lg.width + 14 + d.textlength(t1, font=f) + x_w + d.textlength(t2, font=f)
    x = (W - total) / 2
    im.alpha_composite(lg, (int(x), int(y)))
    x += lg.width + 14
    ty = y + (lg.height - 30) / 2 - 6
    d.text((x, ty), t1, font=f, fill=CREAM); x += d.textlength(t1, font=f)
    d.text((x, ty), ' × ', font=f, fill=ORANGE2); x += x_w
    d.text((x, ty), t2, font=f, fill=CREAM)


# ---------- slide 1: hero ----------
def slide1():
    bg = photo('Coyote-and-Multicam-Arid-recycledfirefighter-2', (W, H), (0.5, 0.35))
    bg = grad(bg, start=0.38, strength=0.95)
    im = bg.convert('RGBA')
    top = Image.new('RGBA', (W, 260), (0, 0, 0, 0))
    a = np.zeros((260, W, 4), np.uint8); a[..., 3] = (np.linspace(170, 0, 260)[:, None]).astype(np.uint8)
    im.alpha_composite(Image.fromarray(a))
    d = ImageDraw.Draw(im)
    frame(d)
    badge(d, W / 2, 52, 'GIVEAWAY', OSW(40, 700))
    logos_row(im, 132, 78)
    d = ImageDraw.Draw(im)
    ctext(d, 790, 'WIN A', OSW(64, 700), GOLD, track=12)
    ctext(d, 860, 'SERGEANT', ANTON(190), CREAM, track=4)
    ctext(d, 1055, 'WALLET', ANTON(190), ORANGE2, track=4)
    ctext(d, 1262, 'WINNER PICKS THE COLOR  ·  ENDS DEC 17', OSW(34, 600), CREAM, track=3)
    return im.convert('RGB')


# ---------- slide 2: how to enter ----------
def slide2():
    bg = photo('Coyote-and-Multicam-recycledfirefighter-1', (W, H), (0.5, 0.5))
    bg = bg.filter(ImageFilter.GaussianBlur(14))
    bg = Image.fromarray((np.asarray(bg, np.float32) * 0.28).astype(np.uint8))
    im = bg.convert('RGBA')
    d = ImageDraw.Draw(im)
    frame(d)
    ctext(d, 70, 'HOW TO ENTER', ANTON(120), CREAM, track=4)
    d.rectangle((W / 2 - 120, 244, W / 2 + 120, 250), fill=ORANGE)
    steps = [
        ('FOLLOW', '@stationhqofficial + @recycledfirefighter'),
        ('LIKE', 'this post'),
        ('COMMENT', 'and tag a friend who’d want it'),
        ('SHARE', 'to your story & tag @stationhqofficial'),
        ('SIGN UP', 'at stationhq.app/giveaway'),
    ]
    y = 290
    for i, (a, b) in enumerate(steps):
        d.rounded_rectangle((70, y, W - 70, y + 150), radius=24, fill=(28, 25, 22, 235), outline=(255, 90, 20, 140), width=2)
        d.ellipse((100, y + 37, 176, y + 113), fill=ORANGE)
        n = str(i + 1); fn = ANTON(54)
        d.text((138 - d.textlength(n, font=fn) / 2, y + 36), n, font=fn, fill='white')
        d.text((208, y + 22), a, font=ANTON(58), fill=CREAM)
        d.text((208, y + 92), b, font=OSW(32, 500), fill=(205, 196, 180))
        y += 172
    ctext(d, 1170, 'LINK IN BIO TO ENTER', OSW(44, 700), GOLD, track=6)
    ctext(d, 1236, 'Ends Thu, Dec 17 · Winner announced Fri, Dec 18 · US 18+', OSW(28, 400), (190, 182, 168), shadow=False)
    return im.convert('RGB')


# ---------- slide 3: colors ----------
def slide3():
    im = Image.new('RGBA', (W, H), DARK + (255,))
    d = ImageDraw.Draw(im)
    frame(d)
    ctext(d, 66, 'WINNER PICKS', ANTON(110), CREAM, track=4)
    ctext(d, 196, 'THE COLOR', ANTON(110), ORANGE2, track=4)
    tiles = [('Coyote-and-Multicam-recycledfirefighter-1', (0.62, 0.55)), ('Coyote-and-Multicam-Arid-recycledfirefighter-1', (0.45, 0.5)),
             ('Black-and-Multicamblack-recycledfirefighter-5', (0.5, 0.5)), ('Black-and-Multicamblack-recycledfirefighter-2', (0.5, 0.45))]
    g, tw = 24, (W - 70 * 2 - 24) // 2
    th = 400
    for i, (n, fc) in enumerate(tiles):
        x = 70 + (i % 2) * (tw + g); y = 350 + (i // 2) * (th + g)
        p = photo(n, (tw, th), fc)
        m = Image.new('L', (tw, th), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, tw, th), radius=22, fill=255)
        im.paste(p, (x, y), m)
    ctext(d, 1205, 'Handmade in the USA from waterproof Hypalon', OSW(34, 500), (215, 206, 190), shadow=False)
    ctext(d, 1255, 'stationhq.app/giveaway', OSW(36, 700), GOLD, shadow=False)
    return im.convert('RGB')


# ---------- story ----------
def story():
    S = Image.new('RGB', (1080, 1920), DARK)
    s1 = slide1().resize((1080, 1350))
    S.paste(s1, (0, 150))
    d = ImageDraw.Draw(S)
    d.rectangle((0, 0, 1080, 11), fill=ORANGE)
    ctext(d, 40, 'NEW GIVEAWAY', OSW(54, 700), GOLD, track=8)
    d2 = ImageDraw.Draw(S)
    ctext(d2, 1560, 'Follow · Like · Comment & tag a friend', OSW(40, 600), CREAM)
    ctext(d2, 1620, 'Share · Sign up', OSW(40, 600), CREAM)
    badge(d2, 540, 1720, 'ENTER: STATIONHQ.APP/GIVEAWAY', OSW(40, 700))
    return S


if __name__ == '__main__':
    for i, fn in enumerate([slide1, slide2, slide3], 1):
        fn().save(f'{OUT}/giveaway_slide{i}.jpg', quality=93)
    story().save(f'{OUT}/giveaway_story.jpg', quality=93)
    print('ok')
