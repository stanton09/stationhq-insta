"""StationHQ merch: print-ready artwork (transparent PNG, 300 dpi sizes) + flat mockups.
Run: python3 scripts/merch.py  ->  brand/merch/print/*.png and brand/merch/mockups/*.png"""
import math
import pathlib

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "brand" / "merch"
PRINT, MOCK = OUT / "print", OUT / "mockups"
PRINT.mkdir(parents=True, exist_ok=True)
MOCK.mkdir(parents=True, exist_ok=True)

RED, DRED, INK, WHITE, GOLD = (214, 38, 32), (150, 20, 16), (20, 20, 22), (250, 248, 243), (214, 170, 70)
BARLOW = str(ROOT / "brand/fonts/barlow-condensed-latin-800-normal.woff")
BARLOW6 = str(ROOT / "brand/fonts/barlow-condensed-latin-600-normal.woff")
INTERB = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"


def F(path, size):
    return ImageFont.truetype(path, size)


def ctext(d, cx, y, s, f, fill, spacing=0):
    if spacing:
        w = sum(d.textlength(c, font=f) for c in s) + spacing * (len(s) - 1)
        x = cx - w / 2
        for c in s:
            d.text((x, y), c, font=f, fill=fill)
            x += d.textlength(c, font=f) + spacing
    else:
        d.text((cx - d.textlength(s, font=f) / 2, y), s, font=f, fill=fill)


def arc_text(img, cx, cy, r, s, f, fill, center_deg=-90, bottom=False, spacing=1.0):
    """Text along a circle. Top arcs read clockwise; bottom arcs read left-to-right too."""
    d = ImageDraw.Draw(img)
    widths = [d.textlength(c, font=f) * spacing for c in s]
    total = sum(widths) / r  # radians
    a = math.radians(center_deg) + (total / 2 if bottom else -total / 2)
    asc = f.getbbox("H")[3]
    for c, w in zip(s, widths):
        step = w / r
        mid = a + (-step / 2 if bottom else step / 2)
        tile = Image.new("RGBA", (int(w * 2 + 40), int(asc * 2 + 40)), (0, 0, 0, 0))
        ImageDraw.Draw(tile).text((tile.width / 2 - d.textlength(c, font=f) / 2, tile.height / 2 - asc / 2 - f.getbbox("H")[1] / 2),
                                  c, font=f, fill=fill)
        rot = -math.degrees(mid) - 90 if not bottom else -math.degrees(mid) + 90
        tile = tile.rotate(rot, resample=Image.BICUBIC, expand=True)
        x, y = cx + r * math.cos(mid), cy + r * math.sin(mid)
        img.alpha_composite(tile, (int(x - tile.width / 2), int(y - tile.height / 2)))
        a += -step if bottom else step


def maltese(size, fill, outline=None, ow=0):
    """Maltese cross polygon set, centered in a size x size RGBA tile."""
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c, R = size / 2, size / 2 - ow - 4

    def arms(R, grow=0):
        polys = []
        for k in range(4):
            th = math.radians(90 * k)
            pts = [(-0.10 * R - grow, -0.10 * R), (-0.46 * R - grow, -R - grow), (0, -0.80 * R - grow),
                   (0.46 * R + grow, -R - grow), (0.10 * R + grow, -0.10 * R)]
            polys.append([(c + x * math.cos(th) - y * math.sin(th), c + x * math.sin(th) + y * math.cos(th)) for x, y in pts])
        return polys
    if outline:
        for p in arms(R, ow):
            d.polygon(p, fill=outline)
        d.ellipse((c - 0.30 * R - ow, c - 0.30 * R - ow, c + 0.30 * R + ow, c + 0.30 * R + ow), fill=outline)
    for p in arms(R):
        d.polygon(p, fill=fill)
    return im


def shq_mark(size=3000, on_dark=True):
    """New monogram: Maltese cross with SHQ across the center."""
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    cross = maltese(size, RED, outline=WHITE if on_dark else INK, ow=int(size * 0.025))
    im.alpha_composite(cross)
    d = ImageDraw.Draw(im)
    c = size / 2
    r = size * 0.205
    d.ellipse((c - r - size * 0.02, c - r - size * 0.02, c + r + size * 0.02, c + r + size * 0.02), fill=WHITE if on_dark else INK)
    d.ellipse((c - r, c - r, c + r, c + r), fill=INK)
    f = F(BARLOW, int(size * 0.20))
    bb = d.textbbox((0, 0), "SHQ", font=f)
    d.text((c - (bb[2] - bb[0]) / 2 - bb[0], c - (bb[3] - bb[1]) / 2 - bb[1]), "SHQ", font=f, fill=WHITE)
    return im


def fit(im, box):
    w, h = box
    s = min(w / im.width, h / im.height)
    return im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)


def canvas(w=4500, h=5400):
    return Image.new("RGBA", (w, h), (0, 0, 0, 0))


# ---------- designs ----------
def d_shq_tee():
    im = canvas()
    m = shq_mark(3400)
    im.alpha_composite(m, ((4500 - 3400) // 2, 300))
    d = ImageDraw.Draw(im)
    ctext(d, 2250, 3850, "STATIONHQ", F(BARLOW, 760), WHITE, spacing=40)
    ctext(d, 2250, 4700, "THE FIREHOUSE APP", F(BARLOW6, 300), RED, spacing=60)
    return im


def d_logo_tee():
    """Back print: the existing StationHQ badge, big, with a rocker."""
    im = canvas()
    lg = Image.open(ROOT / "brand/logo_badge.png").convert("RGBA")
    lg = fit(lg, (3600, 3600))
    im.alpha_composite(lg, ((4500 - lg.width) // 2, 500))
    d = ImageDraw.Draw(im)
    ctext(d, 2250, 4250, "BUILT BY A FIREFIGHTER", F(BARLOW, 420), WHITE, spacing=20)
    return im


def d_logo_pocket():
    im = canvas(1500, 1500)
    lg = fit(Image.open(ROOT / "brand/logo_badge.png").convert("RGBA"), (1400, 1400))
    im.alpha_composite(lg, ((1500 - lg.width) // 2, (1500 - lg.height) // 2))
    return im


def circle_crop(src, d_):
    src = src.copy()
    s = d_ / min(src.width, src.height * 0.82)
    src = src.resize((int(src.width * s), int(src.height * s)), Image.LANCZOS)
    tile = Image.new("RGBA", (d_, d_), (0, 0, 0, 0))
    tile.alpha_composite(src, ((d_ - src.width) // 2, int(d_ * 0.06)))
    m = Image.new("L", (d_, d_), 0)
    ImageDraw.Draw(m).ellipse((0, 0, d_ - 1, d_ - 1), fill=255)
    out = Image.new("RGBA", (d_, d_), (0, 0, 0, 0))
    out.paste(tile, (0, 0), Image.composite(tile.getchannel("A"), Image.new("L", (d_, d_), 0), m))
    return out


def brisket_badge(size=3800, face="x_sideeye"):
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = size / 2
    d.ellipse((0, 0, size - 1, size - 1), fill=INK)
    d.ellipse((size * 0.03, size * 0.03, size * 0.97, size * 0.97), fill=RED)
    inner = int(size * 0.70)
    d.ellipse((c - inner / 2 - size * 0.015, c - inner / 2 - size * 0.015, c + inner / 2 + size * 0.015, c + inner / 2 + size * 0.015), fill=INK)
    d.ellipse((c - inner / 2, c - inner / 2, c + inner / 2, c + inner / 2), fill=(236, 226, 205))
    fc = Image.open(ROOT / "brand/roy" / f"{face}.png").convert("RGBA")
    im.alpha_composite(circle_crop(fc, inner), (int(c - inner / 2), int(c - inner / 2)))
    f = F(BARLOW, int(size * 0.085))
    rr = size * 0.415
    arc_text(im, c, c, rr, "CAPTAIN BRISKET", f, WHITE, -90, spacing=1.12)
    arc_text(im, c, c, rr, "STATION 12", f, WHITE, 90, bottom=True, spacing=1.12)
    for ang in (180, 0):  # little stars
        x, y = c + rr * math.cos(math.radians(ang)), c + rr * math.sin(math.radians(ang))
        star(d, x, y, size * 0.03, WHITE)
    return im


def star(d, x, y, r, fill):
    pts = []
    for k in range(10):
        rr = r if k % 2 == 0 else r * 0.42
        a = math.radians(-90 + 36 * k)
        pts.append((x + rr * math.cos(a), y + rr * math.sin(a)))
    d.polygon(pts, fill=fill)


def d_brisket_tee():
    im = canvas()
    b = brisket_badge(3800)
    im.alpha_composite(b, (350, 300))
    d = ImageDraw.Draw(im)
    ctext(d, 2250, 4300, "STATIONHQ.APP", F(BARLOW6, 340), WHITE, spacing=50)
    return im


def d_rigcheck_tee():
    """App tee: a rig-check checklist, all checked."""
    im = canvas()
    d = ImageDraw.Draw(im)
    ctext(d, 2250, 200, "SHIFT CHECKLIST", F(BARLOW, 520), WHITE, spacing=20)
    items = ["RIG CHECK", "SCBA CHECK", "ROSTER SET", "ALERTS SENT", "COFFEE MADE"]
    fi = F(BARLOW, 470)
    y = 1000
    for it in items:
        x0 = 700
        d.rounded_rectangle((x0, y + 40, x0 + 460, y + 500), 60, outline=WHITE, width=55)
        d.line([(x0 + 80, y + 270), (x0 + 200, y + 400), (x0 + 520, y - 20)], fill=RED, width=110, joint="curve")
        d.text((x0 + 680, y), it, font=fi, fill=WHITE)
        y += 650
    m = shq_mark(700)
    im.alpha_composite(m, (2250 - 350 - 520, 4500))
    d.text((2250 - 350 + 260, 4640), "STATIONHQ", font=F(BARLOW, 380), fill=WHITE)
    return im


def d_shift_tee():
    """Firefighter tee: vintage shift-change badge."""
    im = canvas()
    d = ImageDraw.Draw(im)
    c = 2250
    d.rounded_rectangle((300, 600, 4200, 3900), 300, outline=WHITE, width=90)
    d.rounded_rectangle((470, 770, 4030, 3730), 220, outline=RED, width=40)
    ctext(d, c, 900, "SHIFT CHANGE", F(BARLOW, 560), WHITE, spacing=30)
    ctext(d, c, 1500, "0700", F(BARLOW, 1500), RED)
    ctext(d, c, 3050, "EVERYBODY GOES HOME", F(BARLOW6, 330), WHITE, spacing=30)
    m = shq_mark(900)
    im.alpha_composite(m, (c - 450, 4100))
    return im


def sticker(art, pad=60, border=WHITE):
    """Die-cut sticker: art with a white border following its shape."""
    a = art.getchannel("A")
    big = a.filter(ImageFilter.MaxFilter(pad * 2 + 1)) if pad < 120 else a
    w, h = art.width + pad * 2, art.height + pad * 2
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    m = Image.new("L", (w, h), 0)
    m.paste(a, (pad, pad))
    m = m.filter(ImageFilter.MaxFilter(pad // 2 * 2 + 1)).filter(ImageFilter.MaxFilter(pad // 2 * 2 + 1))
    out.paste(Image.new("RGBA", (w, h), border + (255,)), (0, 0), m)
    out.alpha_composite(art, (pad, pad))
    return out


def shield(size=1800, num="12"):
    """Helmet front-piece style decal: shield with SHQ and a company number."""
    im = Image.new("RGBA", (size, int(size * 1.2)), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    W_, H_ = im.size
    pts = [(W_ * 0.5, 0), (W_, H_ * 0.12), (W_ * 0.94, H_ * 0.62), (W_ * 0.5, H_), (W_ * 0.06, H_ * 0.62), (0, H_ * 0.12)]
    d.polygon(pts, fill=INK)
    inset = [(x * 0.92 + W_ * 0.04, y * 0.92 + H_ * 0.045) for x, y in pts]
    d.polygon(inset, fill=RED)
    ctext(d, W_ / 2, H_ * 0.10, "STATIONHQ", F(BARLOW, int(size * 0.13)), WHITE, spacing=6)
    ctext(d, W_ / 2, H_ * 0.25, num, F(BARLOW, int(size * 0.48)), WHITE)
    ctext(d, W_ / 2, H_ * 0.70, "ENGINE", F(BARLOW, int(size * 0.12)), INK, spacing=12)
    return im


def rocker(text="STATIONHQ", w=3000):
    im = Image.new("RGBA", (w, int(w * 0.38)), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx, cy, R = w / 2, w * 1.25, w * 1.2
    d.ellipse((cx - R, cy - R - 0, cx + R, cy + R), fill=INK)
    d.ellipse((cx - R + w * 0.18, cy - R + w * 0.18, cx + R - w * 0.18, cy + R - w * 0.18), fill=(0, 0, 0, 0))
    m = Image.new("L", im.size, 0)
    ImageDraw.Draw(m).rectangle((w * 0.04, 0, w * 0.96, im.height), fill=255)
    im.putalpha(Image.composite(im.getchannel("A"), Image.new("L", im.size, 0), m))
    arc_text(im, cx, cy, R - w * 0.09, text, F(BARLOW, int(w * 0.11)), WHITE, -90, spacing=1.1)
    return im


def d_case():
    """iPad / phone case: black, SHQ mark, small wordmark, subtle diamond plate."""
    w, h = 2400, 3200
    im = Image.new("RGBA", (w, h), INK + (255,))
    d = ImageDraw.Draw(im)
    for y in range(-100, h + 100, 120):  # diamond plate texture
        for x in range(-100, w + 100, 120):
            off = 60 if (y // 120) % 2 else 0
            d.line([(x + off - 22, y + 22), (x + off + 22, y - 22)], fill=(44, 44, 48), width=14)
    m = shq_mark(1300)
    im.alpha_composite(m, ((w - 1300) // 2, 900))
    ctext(d, w / 2, 2300, "STATIONHQ", F(BARLOW, 260), WHITE, spacing=24)
    ctext(d, w / 2, 2600, "BUILT BY A FIREFIGHTER", F(BARLOW6, 110), RED, spacing=20)
    return im


# ---------- mockups ----------
def tee(color, w=1000):
    h = int(w * 1.15)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    body = [(w * 0.30, h * 0.02), (w * 0.40, h * 0.06), (w * 0.60, h * 0.06), (w * 0.70, h * 0.02), (w * 0.97, h * 0.16),
            (w * 0.88, h * 0.36), (w * 0.79, h * 0.31), (w * 0.79, h * 0.98), (w * 0.21, h * 0.98), (w * 0.21, h * 0.31),
            (w * 0.12, h * 0.36), (w * 0.03, h * 0.16)]
    d.polygon(body, fill=color)
    d.chord((w * 0.38, -h * 0.03, w * 0.62, h * 0.12), 0, 180, fill=tuple(max(0, v - 25) for v in color))
    shade = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(shade).rectangle((w * 0.21, h * 0.31, w * 0.79, h * 0.98), fill=(0, 0, 0, 0))
    return im


def mock_tee(art, color, name, label, box=(0.44, 0.50), top=0.20, pocket=None):
    t = tee(color)
    a = fit(art, (int(t.width * box[0]), int(t.height * box[1])))
    t.alpha_composite(a, ((t.width - a.width) // 2, int(t.height * top)))
    if pocket is not None:
        p = fit(pocket, (int(t.width * 0.12), int(t.width * 0.12)))
        t.alpha_composite(p, (int(t.width * 0.58), int(t.height * 0.16)))
    card = Image.new("RGB", (1200, 1450), (238, 236, 232))
    card.paste(t, (100, 80), t)
    d = ImageDraw.Draw(card)
    ctext(d, 600, 1330, label, F(BARLOW, 70), INK)
    card.save(MOCK / f"{name}.png")
    return card


def mock_flat(art, name, label, bg=(238, 236, 232)):
    card = Image.new("RGB", (1200, 1450), bg)
    a = fit(art, (1000, 1150))
    card.paste(a, ((1200 - a.width) // 2, 80 + (1150 - a.height) // 2), a)
    ctext(ImageDraw.Draw(card), 600, 1330, label, F(BARLOW, 70), INK)
    card.save(MOCK / f"{name}.png")
    return card


def mock_case(art, name, label):
    card = Image.new("RGB", (1200, 1450), (238, 236, 232))
    a = fit(art, (820, 1100)).convert("RGBA")
    m = Image.new("L", a.size, 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, a.width - 1, a.height - 1), 70, fill=255)
    sh = Image.new("RGBA", (a.width + 80, a.height + 80), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((40, 50, a.width + 40, a.height + 40), 70, fill=(0, 0, 0, 90))
    sh = sh.filter(ImageFilter.GaussianBlur(18))
    x, y = (1200 - a.width) // 2, 90
    card.paste(sh, (x - 40, y - 40), sh)
    card.paste(a, (x, y), m)
    d = ImageDraw.Draw(card)
    d.rounded_rectangle((x + 50, y + 50, x + 230, y + 230), 50, fill=(30, 30, 34))  # camera bump
    for cx, cy in ((x + 105, y + 105), (x + 175, y + 175)):
        d.ellipse((cx - 32, cy - 32, cx + 32, cy + 32), fill=(10, 10, 12), outline=(70, 70, 76), width=6)
    ctext(d, 600, 1330, label, F(BARLOW, 70), INK)
    card.save(MOCK / f"{name}.png")
    return card


if __name__ == "__main__":
    BLACK, CHAR, NAVY, REDT = (24, 24, 26), (52, 54, 58), (28, 36, 58), (170, 30, 28)
    arts = {}
    arts["01_shq_monogram_tee"] = d_shq_tee()
    arts["02_logo_back_tee"] = d_logo_tee()
    arts["02_logo_pocket"] = d_logo_pocket()
    arts["03_brisket_badge_tee"] = d_brisket_tee()
    arts["04_shift_checklist_tee"] = d_rigcheck_tee()
    arts["05_shift_change_0700_tee"] = d_shift_tee()
    arts["06_sticker_shq"] = sticker(shq_mark(1800))
    arts["07_sticker_helmet_shield"] = sticker(shield(1600))
    arts["08_sticker_brisket"] = sticker(brisket_badge(1800))
    arts["09_sticker_rocker"] = sticker(rocker())
    arts["10_case_ipad_phone"] = d_case()
    arts["11_hat_patch_shq"] = shq_mark(1500)
    for k, v in arts.items():
        v.save(PRINT / f"{k}.png", dpi=(300, 300))

    mock_tee(arts["01_shq_monogram_tee"], BLACK, "m01", "SHQ CROSS TEE")
    mock_tee(arts["02_logo_back_tee"], CHAR, "m02", "LOGO TEE (BACK + POCKET)")
    mock_tee(arts["03_brisket_badge_tee"], NAVY, "m03", "CAPTAIN BRISKET TEE")
    mock_tee(arts["04_shift_checklist_tee"], BLACK, "m04", "SHIFT CHECKLIST TEE")
    mock_tee(arts["05_shift_change_0700_tee"], REDT, "m05", "SHIFT CHANGE 0700 TEE")
    sheet = Image.new("RGBA", (2400, 2400), (0, 0, 0, 0))
    for art, (x, y, s) in ((arts["06_sticker_shq"], (60, 60, 1050)), (arts["07_sticker_helmet_shield"], (1250, 40, 1100)),
                           (arts["08_sticker_brisket"], (80, 1200, 1050)), (arts["09_sticker_rocker"], (1150, 1450, 1200))):
        a = fit(art, (s, s))
        sheet.alpha_composite(a, (x, y))
    mock_flat(sheet, "m06", "HELMET + TOOLBOX STICKERS", bg=(70, 72, 76))
    mock_case(arts["10_case_ipad_phone"], "m07", "IPAD / PHONE CASE")
    hat = Image.new("RGBA", (1200, 900), (0, 0, 0, 0))
    hd = ImageDraw.Draw(hat)
    hd.chord((150, 80, 1050, 980), 180, 360, fill=(24, 24, 26))
    hd.rectangle((150, 520, 1050, 560), fill=(24, 24, 26))
    hd.ellipse((60, 500, 1140, 700), fill=(34, 34, 36))
    hd.chord((150, 80, 1050, 980), 180, 360, fill=(24, 24, 26))
    p = fit(arts["11_hat_patch_shq"], (380, 380))
    hat.alpha_composite(p, (600 - p.width // 2, 140))
    mock_flat(hat, "m08", "SHQ HAT")
    print("done", sorted(p.name for p in PRINT.iterdir()))
