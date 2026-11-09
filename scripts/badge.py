"""StationHQ badge logo (the 'Recommended' ChatGPT concept), redrawn flat at print resolution.
Maltese-cross badge, signal tower on top, STATIONHQ banner, firehouse with two bay doors below."""
import math
import pathlib
import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "brand/merch/print"
RED, DRED, INK, WHITE, SILVER = (220, 30, 36), (150, 14, 20), (16, 16, 18), (250, 250, 250), (205, 208, 214)
BARLOW = str(ROOT / "brand/fonts/barlow-condensed-latin-800-normal.woff")


def cross_arms(c, R, k=1.0):
    """Maltese/fire cross as 4 flared arms with V-notched ends, scaled by k about the center."""
    cx, cy = c
    arm = [(-0.20, -0.05), (-0.58, -1.0), (0.0, -0.80), (0.58, -1.0), (0.20, -0.05)]
    polys = []
    for q in range(4):
        th = math.radians(90 * q)
        polys.append([(cx + k * R * (x * math.cos(th) - y * math.sin(th)), cy + k * R * (x * math.sin(th) + y * math.cos(th)))
                      for x, y in arm])
    return polys


def draw_cross(d, c, R, k, fill):
    for p in cross_arms(c, R, k):
        d.polygon(p, fill=fill)
    d.ellipse((c[0] - 0.3 * R * k, c[1] - 0.3 * R * k, c[0] + 0.3 * R * k, c[1] + 0.3 * R * k), fill=fill)


def italic_text(text_parts, font, skew=0.22, stroke=0, stroke_fill=None):
    """Render colored text parts on one line, then shear for an italic look."""
    tmp = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    w = int(sum(tmp.textlength(t, font=font) for t, _ in text_parts) + stroke * 2 + 40)
    asc, desc = font.getmetrics()
    h = asc + desc + stroke * 2 + 20
    pad = int(h * skew) + 20
    im = Image.new("RGBA", (w + pad, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x = stroke + 20 + pad // 2
    for t, col in text_parts:
        d.text((x, stroke + 10), t, font=font, fill=col, stroke_width=stroke, stroke_fill=stroke_fill or col)
        x += d.textlength(t, font=font)
    im = im.transform(im.size, Image.AFFINE, (1, skew, -skew * h / 2, 0, 1, 0), resample=Image.BICUBIC)
    return im.crop(im.getbbox())


def badge(S=4000, on_dark=True):
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = (S / 2, S / 2 + S * 0.02)
    R = S * 0.48
    edge = WHITE if on_dark else INK
    draw_cross(d, c, R, 1.0, edge)        # outer white keyline
    draw_cross(d, c, R, 0.955, RED)       # red cross
    draw_cross(d, c, R, 0.86, INK)        # black inner field
    # signal tower + waves (top)
    tx, ty = c[0], c[1] - R * 0.50
    lw = int(S * 0.012)
    d.polygon([(tx - S * 0.018, ty + S * 0.075), (tx + S * 0.018, ty + S * 0.075), (tx + S * 0.007, ty), (tx - S * 0.007, ty)], fill=WHITE)
    d.ellipse((tx - S * 0.020, ty - S * 0.032, tx + S * 0.020, ty + S * 0.008), fill=WHITE)
    for i, r in enumerate((S * 0.055, S * 0.090, S * 0.125)):
        box = (tx - r, ty - S * 0.012 - r, tx + r, ty - S * 0.012 + r)
        d.arc(box, 205, 245, fill=WHITE, width=lw)
        d.arc(box, 295, 335, fill=WHITE, width=lw)
    # banner
    bw, bh = S * 0.86, S * 0.20
    by = c[1] - bh * 0.62
    sk = S * 0.035
    ban = [(c[0] - bw / 2 + sk, by), (c[0] + bw / 2 + sk, by), (c[0] + bw / 2 - sk, by + bh), (c[0] - bw / 2 - sk, by + bh)]
    grow = S * 0.014
    d.polygon([(ban[0][0] - grow, ban[0][1] - grow), (ban[1][0] + grow, ban[1][1] - grow),
               (ban[2][0] + grow, ban[2][1] + grow), (ban[3][0] - grow, ban[3][1] + grow)], fill=WHITE)
    d.polygon([(ban[0][0] - grow / 2, ban[0][1] - grow / 2), (ban[1][0] + grow / 2, ban[1][1] - grow / 2),
               (ban[2][0] + grow / 2, ban[2][1] + grow / 2), (ban[3][0] - grow / 2, ban[3][1] + grow / 2)], fill=RED)
    d.polygon(ban, fill=INK)
    f = ImageFont.truetype(BARLOW, int(bh * 1.02))
    txt = italic_text([("STATION", WHITE), ("HQ", RED)], f, stroke=int(S * 0.004), stroke_fill=None)
    s = min((bw * 0.88) / txt.width, (bh * 0.80) / txt.height)
    txt = txt.resize((int(txt.width * s), int(txt.height * s)), Image.LANCZOS)
    im.alpha_composite(txt, (int(c[0] - txt.width / 2), int(by + bh / 2 - txt.height / 2)))
    # firehouse with two bay doors (bottom)
    hw, hh = S * 0.30, S * 0.15
    hx, hy = c[0], c[1] + R * 0.40
    d.polygon([(hx - hw / 2 - S * 0.02, hy), (hx, hy - S * 0.055), (hx + hw / 2 + S * 0.02, hy)], fill=WHITE)
    d.rectangle((hx - hw / 2, hy, hx + hw / 2, hy + hh), fill=WHITE)
    dw = hw * 0.40
    for sx in (-1, 1):
        x0 = hx + sx * (hw * 0.06) + (0 if sx > 0 else -dw)
        d.rectangle((x0, hy + hh * 0.20, x0 + dw, hy + hh), fill=RED)
        for row in range(3):
            yy = hy + hh * 0.30 + row * hh * 0.22
            d.rectangle((x0 + dw * 0.10, yy, x0 + dw * 0.90, yy + hh * 0.12), fill=WHITE if row == 0 else DRED)
    return im


def distressed_flag(w, h, seed=7):
    """Black thin-red-line flag with worn texture (back prints / case)."""
    random.seed(seed)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    stripes = 13
    sh = h / stripes
    for i in range(stripes):
        col = (230, 230, 232) if i % 2 == 0 else (90, 92, 96)
        if i == 6:
            col = RED
        d.rectangle((0, i * sh, w, (i + 1) * sh - 1), fill=col)
    cw, ch = w * 0.40, sh * 7
    d.rectangle((0, 0, cw, ch), fill=(36, 36, 40))
    for r in range(9):
        for k in range(6 if r % 2 == 0 else 5):
            x = cw / 12 + k * cw / 6 + (cw / 12 if r % 2 else 0)
            y = ch / 18 + r * ch / 9
            rr = min(cw, ch) * 0.035
            pts = [(x + (rr if j % 2 == 0 else rr * 0.42) * math.cos(math.radians(-90 + 36 * j)),
                    y + (rr if j % 2 == 0 else rr * 0.42) * math.sin(math.radians(-90 + 36 * j))) for j in range(10)]
            d.polygon(pts, fill=(230, 230, 232))
    # wear: knock out random scratches so it reads distressed
    mask = Image.new("L", (w, h), 255)
    md = ImageDraw.Draw(mask)
    for _ in range(int(w * h / 900)):
        x, y = random.uniform(0, w), random.uniform(0, h)
        l = random.uniform(4, w * 0.03)
        md.line([(x, y), (x + l, y + random.uniform(-3, 3))], fill=0, width=random.randint(1, max(2, w // 900)))
    for _ in range(int(w * h / 5000)):
        x, y, r = random.uniform(0, w), random.uniform(0, h), random.uniform(1, w * 0.004)
        md.ellipse((x - r, y - r, x + r, y + r), fill=0)
    # fade edges
    fade = Image.new("L", (w, h), 0)
    ImageDraw.Draw(fade).rectangle((w * 0.04, h * 0.03, w * 0.96, h * 0.97), fill=255)
    fade = fade.filter(ImageFilter.GaussianBlur(w * 0.03))
    from PIL import ImageChops
    im.putalpha(ImageChops.multiply(ImageChops.multiply(im.getchannel("A"), mask), fade))
    return im


if __name__ == "__main__":
    b = badge(4000)
    b.save(OUT / "30_badge_logo.png", dpi=(300, 300))
    # hoodie/tee back print: vertical distressed flag behind the badge
    back = Image.new("RGBA", (4500, 5400), (0, 0, 0, 0))
    fl = distressed_flag(3300, 5200).rotate(90, expand=True).resize((3300, 5200)) if False else distressed_flag(5200, 3300).rotate(-90, expand=True)
    back.alpha_composite(fl, ((4500 - fl.width) // 2, 100))
    bb = b.resize((3900, 3900), Image.LANCZOS)
    back.alpha_composite(bb, (300, 750))
    back.save(OUT / "31_badge_flag_back.png", dpi=(300, 300))
    # chest hit
    b.resize((1500, 1500), Image.LANCZOS).save(OUT / "32_badge_chest.png", dpi=(300, 300))
    # phone case: black, flag strip, badge
    case = Image.new("RGBA", (1800, 3600), (16, 16, 18, 255))
    fl2 = distressed_flag(3600, 1500, seed=3).rotate(-90, expand=True)
    case.alpha_composite(fl2, (150, 0))
    bc = b.resize((1500, 1500), Image.LANCZOS)
    case.alpha_composite(bc, (150, 1500))
    case.save(OUT / "33_badge_case.png", dpi=(300, 300))
    print("ok")
