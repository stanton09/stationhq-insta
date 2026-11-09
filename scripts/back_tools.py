"""Firefighter back print: crossed axe + Halligan over the distressed thin red line flag, SMOKE EATER banner."""
import math
import pathlib

from PIL import Image, ImageDraw, ImageFont

from badge import distressed_flag, cross_arms

ROOT = pathlib.Path(__file__).resolve().parent.parent
BARLOW = str(ROOT / "brand/fonts/barlow-condensed-latin-800-normal.woff")
RED, INK, WHITE, STEEL, WOOD = (220, 30, 36), (16, 16, 18), (245, 245, 245), (200, 204, 210), (176, 112, 60)
OL = 26  # outline width


def tool_layer(S):
    """Draw one tool pointing up, centered, on an S x S canvas. Returns (axe, halligan)."""
    def canvas():
        return Image.new("RGBA", (S, S), (0, 0, 0, 0))

    # --- axe (pick-head flat axe) ---
    axe = canvas()
    d = ImageDraw.Draw(axe)
    cx = S / 2
    hw = S * 0.028
    top, bot = S * 0.14, S * 0.95
    d.rounded_rectangle((cx - hw - OL, top - OL, cx + hw + OL, bot + OL), int(hw), fill=INK)
    d.rounded_rectangle((cx - hw, top, cx + hw, bot), int(hw * 0.8), fill=WOOD)
    for k in range(5):  # grip wraps
        y = bot - S * 0.03 - k * S * 0.03
        d.rectangle((cx - hw, y, cx + hw, y + S * 0.012), fill=INK)
    # head: blade on the left, pick on the right
    hy0, hy1 = S * 0.10, S * 0.24
    blade = [(cx - hw, hy0 + S * 0.02), (cx - S * 0.20, hy0 - S * 0.03), (cx - S * 0.23, (hy0 + hy1) / 2),
             (cx - S * 0.20, hy1 + S * 0.05), (cx - hw, hy1 - S * 0.01)]
    pick = [(cx + hw, hy0 + S * 0.03), (cx + S * 0.21, (hy0 + hy1) / 2 + S * 0.01), (cx + hw, hy1 - S * 0.02)]
    for poly, fill in ((blade, STEEL), (pick, STEEL)):
        d.polygon(poly, fill=INK)
    sh = lambda poly, f: [(x + (cx - x) * f, y + ((hy0 + hy1) / 2 - y) * f) for x, y in poly]
    d.polygon(sh(blade, 0.10), fill=STEEL)
    d.polygon(sh(pick, 0.12), fill=STEEL)
    d.rectangle((cx - hw - OL, hy0, cx + hw + OL, hy1), fill=INK)
    d.rectangle((cx - hw, hy0 + OL, cx + hw, hy1 - OL), fill=RED)
    # blade edge highlight
    d.line([(cx - S * 0.20, hy0 - S * 0.02), (cx - S * 0.22, (hy0 + hy1) / 2), (cx - S * 0.19, hy1 + S * 0.04)], fill=WHITE, width=OL)

    # --- Halligan bar ---
    hal = canvas()
    d = ImageDraw.Draw(hal)
    bw = S * 0.022
    top, bot = S * 0.16, S * 0.86
    d.rectangle((cx - bw - OL, top, cx + bw + OL, bot), fill=INK)
    d.rectangle((cx - bw, top, cx + bw, bot), fill=STEEL)
    for k in range(9):  # knurled grip
        y = S * 0.42 + k * S * 0.03
        d.line([(cx - bw, y), (cx + bw, y + S * 0.012)], fill=(150, 154, 160), width=10)
    # top: adz (flat blade to the left) + pick (to the right)
    t = top
    adz = [(cx - bw, t + S * 0.01), (cx - S * 0.15, t + S * 0.05), (cx - S * 0.16, t + S * 0.09), (cx - bw, t + S * 0.07)]
    pk = [(cx + bw, t), (cx + S * 0.16, t + S * 0.06), (cx + bw, t + S * 0.07)]
    for poly in (adz, pk):
        g = [(x + (x - cx) * 0.06, y) for x, y in poly]
        d.polygon(g, fill=INK)
    d.polygon(adz, fill=STEEL)
    d.polygon(pk, fill=STEEL)
    d.rectangle((cx - bw - OL, t - S * 0.02, cx + bw + OL, t + S * 0.09), fill=INK)
    d.rectangle((cx - bw, t - S * 0.02 + OL, cx + bw, t + S * 0.09 - OL), fill=STEEL)
    # bottom: fork (two tines)
    fy = bot
    for side in (-1, 1):
        tine = [(cx + side * bw * 0.2, fy - S * 0.01), (cx + side * (bw + S * 0.025), fy + S * 0.07),
                (cx + side * (bw + S * 0.01), fy + S * 0.075), (cx + side * bw * 0.1, fy + S * 0.02)]
        d.polygon([(x + side * 10, y + 10) for x, y in tine], fill=INK)
        d.polygon(tine, fill=STEEL)
    return axe, hal


def italic(text, size, fill, stroke, skew=0.18):
    f = ImageFont.truetype(BARLOW, size)
    tmp = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    w = int(tmp.textlength(text, font=f) + stroke * 2 + 200)
    a, dsc = f.getmetrics()
    im = Image.new("RGBA", (w, a + dsc + stroke * 2 + 40), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((100, stroke + 20), text, font=f, fill=fill, stroke_width=stroke, stroke_fill=INK)
    im = im.transform(im.size, Image.AFFINE, (1, skew, -skew * im.height / 2, 0, 1, 0), resample=Image.BICUBIC)
    return im.crop(im.getbbox())


def back_print():
    W, H = 4500, 5400
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    fl = distressed_flag(5200, 3300).rotate(-90, expand=True)
    out.alpha_composite(fl, ((W - fl.width) // 2, 100))
    # Maltese cross behind the tools
    cr = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    d = ImageDraw.Draw(cr)
    c, R = (W / 2, W / 2), W * 0.40
    for k, col in ((1.0, WHITE), (0.955, RED), (0.86, INK)):
        for p in cross_arms(c, R, k):
            d.polygon(p, fill=col)
        d.ellipse((c[0] - 0.3 * R * k, c[1] - 0.3 * R * k, c[0] + 0.3 * R * k, c[1] + 0.3 * R * k), fill=col)
    out.alpha_composite(cr, (0, 450))
    S = 3600
    axe, hal = tool_layer(S)
    a = axe.rotate(38, resample=Image.BICUBIC, expand=True)
    h = hal.rotate(-38, resample=Image.BICUBIC, expand=True)
    cy = 450 + W // 2
    out.alpha_composite(h, (W // 2 - h.width // 2, cy - h.height // 2))
    out.alpha_composite(a, (W // 2 - a.width // 2, cy - a.height // 2))
    # banner text
    t1 = italic("SMOKE EATER", 760, WHITE, 40)
    out.alpha_composite(t1, (W // 2 - t1.width // 2, 4720 - t1.height // 2 - 120))
    return out


if __name__ == "__main__":
    im = back_print()
    p = ROOT / "brand/merch/print/43_tools_flag_back.png"
    im.save(p, dpi=(300, 300))
    prev = Image.new("RGB", im.size, (22, 22, 24))
    prev.paste(im, (0, 0), im)
    prev.resize((600, 720)).save("/tmp/tools_back.jpg")
    print("ok")
