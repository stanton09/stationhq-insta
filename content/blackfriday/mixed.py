"""Mixed-item Black Friday ads (shop items 20% off + books on Amazon)."""
import sys
sys.argv = [sys.argv[0], '20']
from build import *  # noqa

def fit_headline(b, text, y, dark=False, maxw=760, size=78):
    d = ImageDraw.Draw(b)
    while d.textlength(text, font=BIG(size)) > maxw and size > 44: size -= 2
    d.text((W // 2 - 60, y), text, font=BIG(size), fill='white' if dark else (24, 22, 20), anchor='mm')

CARDS = True
STYLE = 'festive'
TXT_LIGHT = False
def _shadow(b, x0, y0, w, h, r=24, alpha=80, ang=0):
    sh = Image.new('RGBA', (w + 80, h + 80), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([40, 46, w + 40, h + 46], r, fill=(0, 0, 0, alpha))
    sh = sh.filter(ImageFilter.GaussianBlur(13))
    if ang: sh = sh.rotate(ang, resample=Image.BICUBIC)
    b.alpha_composite(sh, (x0 - 40, y0 - 40))

def card(b, x0, y0, x1, y1, dark=False):
    w, h = x1 - x0, y1 - y0
    if STYLE == 'frost':
        _shadow(b, x0, y0, w, h, alpha=55)
        reg = b.crop((x0, y0, x1, y1)).filter(ImageFilter.GaussianBlur(14))
        white = Image.new('RGBA', (w, h), (255, 255, 255, 150))
        reg.alpha_composite(white)
        m = Image.new('L', (w, h), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, w - 1, h - 1], 26, fill=255)
        b.paste(reg, (x0, y0), m)
        ImageDraw.Draw(b).rounded_rectangle([x0, y0, x1 - 1, y1 - 1], 26, outline=(255, 255, 255, 220), width=3)
        return
    if STYLE == 'red':
        _shadow(b, x0, y0, w, h, alpha=90)
        l = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(l)
        top, bot = (196, 34, 36), (128, 14, 20)
        for yy in range(h):
            t = yy / (h - 1); d.line([(0, yy), (w, yy)], fill=tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3)) + (255,))
        g = Image.radial_gradient('L').resize((w, int(h * .85))).point(lambda v: max(0, 150 - v))
        gl = Image.new('RGBA', g.size, (255, 230, 210, 0)); gl.putalpha(g); l.alpha_composite(gl, (0, 0))
        m = Image.new('L', (w, h), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, w - 1, h - 1], 24, fill=255)
        out = Image.new('RGBA', (w, h), (0, 0, 0, 0)); out.paste(l, (0, 0), m)
        ImageDraw.Draw(out).rounded_rectangle([5, 5, w - 6, h - 6], 20, outline=(222, 182, 100, 255), width=2)
        b.alpha_composite(out, (x0, y0)); return
    if STYLE == 'kraft':
        _shadow(b, x0, y0, w, h, r=10, alpha=85)
        l = Image.new('RGBA', (w, h), (214, 184, 140, 255)); d = ImageDraw.Draw(l)
        import random as _r; rr = _r.Random(x0 * 7 + y0)
        for _ in range(w * h // 60):
            x, y = rr.randrange(w), rr.randrange(h); c = rr.randint(-14, 14)
            d.point((x, y), fill=(214 + c, 184 + c, 140 + c, 255))
        l = l.filter(ImageFilter.GaussianBlur(.6))
        d = ImageDraw.Draw(l)
        d.rectangle([0, 0, w - 1, h - 1], outline=(168, 132, 88, 255), width=2)
        d.line([(w // 2 - 1, 0), (w // 2 - 1, 22)], fill=(176, 28, 32, 255), width=6)
        d.ellipse([w // 2 - 10, 14, w // 2 + 8, 32], fill=(244, 236, 220, 255), outline=(150, 112, 70, 255), width=2)
        b.alpha_composite(l, (x0, y0)); return
    # festive (current)
    _shadow(b, x0, y0, w, h)
    top, bot = (252, 236, 226), (244, 230, 206)
    grad = Image.new('RGBA', (w, h)); gd = ImageDraw.Draw(grad)
    for yy in range(h):
        t = yy / max(1, h - 1)
        gd.line([(0, yy), (w, yy)], fill=tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3)) + (232,))
    mask = Image.new('L', (w, h), 0); ImageDraw.Draw(mask).rounded_rectangle([0, 0, w - 1, h - 1], 24, fill=255)
    ci = Image.new('RGBA', (w, h), (0, 0, 0, 0)); ci.paste(grad, (0, 0), mask)
    d = ImageDraw.Draw(ci)
    d.rectangle([0, 0, w, 11], fill=(176, 28, 32, 255))
    ci.putalpha(Image.composite(ci.split()[3], Image.new('L', (w, h), 0), mask))
    d = ImageDraw.Draw(ci)
    d.line([(14, 13), (w - 14, 13)], fill=(206, 168, 92, 255), width=2)
    d.rounded_rectangle([0, 0, w - 1, h - 1], 24, outline=(196, 160, 110, 255), width=2)
    b.alpha_composite(ci, (x0, y0))

def ribbon_tag(b, cx, cy, lab, price, note):
    d0 = ImageDraw.Draw(b)
    f1, f2, f3 = BIG(34), SM(28), BIG(40)
    if price is not None:
        new = price * 80 / 100; new_s = f'${new:.2f}'.replace('.00', ''); old_s = f'${price:.0f}'
    w1 = d0.textlength(lab, font=f1)
    line2 = (old_s + '  ' + new_s) if price is not None else note
    w2 = d0.textlength(line2, font=f3) + 10
    tw = int(max(w1, w2) + 70); th = 104
    S = 3
    l = Image.new('RGBA', ((tw + 60) * S, (th + 20) * S), (0, 0, 0, 0)); d = ImageDraw.Draw(l)
    x0, y0, x1, y1 = 30 * S, 4 * S, (30 + tw) * S, (4 + th) * S
    nz = 22 * S
    d.polygon([(x0 - nz, y0), (x1 + nz, y0), (x1, (y0 + y1) / 2), (x1 + nz, y1), (x0 - nz, y1), (x0, (y0 + y1) / 2)], fill=(168, 22, 28, 255))
    d.rectangle([x0, y0, x1, y1], fill=(196, 30, 36, 255))
    for yy in (y0 + 7 * S, y1 - 7 * S):
        xx = x0 + 8 * S
        while xx < x1 - 8 * S:
            d.line([(xx, yy), (xx + 8 * S, yy)], fill=(232, 196, 120, 255), width=2 * S); xx += 14 * S
    cxl = (x0 + x1) / 2
    d.text((cxl, y0 + 32 * S), lab, font=BIG(34 * S), fill=(255, 250, 240), anchor='mm')
    if price is not None:
        fo, fn = SM(30 * S), BIG(40 * S)
        wo, wn = d.textlength(old_s, font=fo), d.textlength(new_s, font=fn)
        sx = cxl - (wo + 16 * S + wn) / 2; yy = y0 + 74 * S
        d.text((sx, yy), old_s, font=fo, fill=(250, 210, 200), anchor='lm')
        d.line([(sx - 2 * S, yy + 2 * S), (sx + wo + 2 * S, yy + 2 * S)], fill=(250, 210, 200), width=3 * S)
        d.text((sx + wo + 16 * S, yy), new_s, font=fn, fill=(255, 222, 130), anchor='lm')
    else:
        d.text((cxl, y0 + 74 * S), note, font=BIG(34 * S), fill=(255, 222, 130), anchor='mm')
    l = l.resize((tw + 60, th + 20), Image.LANCZOS)
    sh = Image.new('RGBA', l.size, (0, 0, 0, 0)); sh.putalpha(l.split()[3].point(lambda v: v // 3))
    b.alpha_composite(sh.filter(ImageFilter.GaussianBlur(6)), (int(cx - l.width / 2) + 4, int(cy) + 6))
    b.alpha_composite(l, (int(cx - l.width / 2), int(cy)))

def item(b, it, cx, cy, box, dark=False, cw=None):
    name, lab, price, note = it
    if STYLE == 'tag':
        gw, gh = int(box[0] * 1.25), int(box[1] * 1.15)
        g = Image.radial_gradient('L').resize((gw, gh)).point(lambda v: max(0, int((255 - v) * .9) - 70))
        gl = Image.new('RGBA', (gw, gh), (255, 250, 240, 0)); gl.putalpha(g)
        b.alpha_composite(gl, (int(cx - gw / 2), int(cy - gh / 2)))
        place(b, name, cx, cy, box)
        ribbon_tag(b, cx, cy + box[1] / 2 + 10, lab, price, note)
        return
    if CARDS:
        cw = cw or box[0] + 40
        card(b, int(cx - cw / 2), int(cy - box[1] / 2 - 26), int(cx + cw / 2), int(cy + box[1] / 2 + 104))
        dark_txt = (STYLE == 'red')
    else:
        dark_txt = dark
    import build as _b; _b.NEWC = (255, 214, 120) if (CARDS and STYLE == 'red') else None
    x, y, w, h = place(b, name, cx, cy, box, glow=(dark and not CARDS))
    dark = dark_txt
    ly = cy + box[1] / 2 + 36
    label(b, cx, ly, lab, dark)
    if price is not None:
        sale_tag(b, cx, ly + 46, price, dark)
    else:
        d = ImageDraw.Draw(b)
        d.text((cx, ly + 44), note, font=BIG(36), fill=((255, 214, 120) if STYLE == 'red' else (255, 90, 80)) if dark else RED, anchor='mm')

def ad(key, head, layout, items, out, dark=False):
    b = bg(key)
    fit_headline(b, head, 398, dark, maxw=720)
    for it, (cx, cy, bw, bh) in zip(items, layout):
        item(b, it, cx, cy, (bw, bh), dark)
    badge(b, W - 105, 420, r=72)
    footer(b, 'Order by Dec 10 for Christmas', dark)
    b.convert('RGB').save(f'{OUT}/{out}.jpg', quality=94)

# layouts: (cx, cy, box_w, box_h) — cy is product center
GRID4 = [(295, 590, 400, 210), (785, 590, 400, 210), (295, 950, 400, 210), (785, 950, 400, 210)]
HERO3 = [(330, 735, 450, 470), (810, 590, 300, 210), (810, 950, 300, 210)]
ROW32 = [(205, 590, 280, 210), (540, 590, 280, 210), (875, 590, 280, 210), (330, 950, 380, 210), (750, 950, 380, 210)]

COLOR = ('book:book_coloring.webp', 'COLORING BOOK', None, '$9.99 ON AMAZON')
NOZZLE = ('book:book_nozzle.webp', "NOZZLE'S BIG NIGHT", None, 'ON AMAZON')

ROW33 = [(205, 585, 270, 200), (540, 585, 270, 200), (875, 585, 270, 200), (205, 950, 270, 200), (540, 950, 270, 200), (875, 950, 270, 200)]
MUG6 = [('probie-mug_1', 'PROBIE', 24, ''), ('firefighter-mug_1', 'FIREFIGHTER', 24, ''), ('engineer-mug_1', 'ENGINEER', 24, ''),
        ('lieutenant-mug_1', 'LIEUTENANT', 24, ''), ('captain-mug_1', 'CAPTAIN', 24, ''), ('chief-mug_1', 'CHIEF', 24, '')]
HAT4 = [('engine-company-trucker_1', 'ENGINE', 32, ''), ('ladder-company-trucker_1', 'LADDER', 32, ''),
        ('rescue-company-trucker_1', 'RESCUE', 32, ''), ('shq-firehouse-badge-beanie_1', 'FIREHOUSE BEANIE', 28, '')]
GIFT3 = [('firehouse-hoodie_2', 'FIREHOUSE HOODIE', 60, ''), ('captain-mug_1', 'CAPTAIN MUG', 24, ''), ('engine-company-trucker_1', 'ENGINE TRUCKER', 32, '')]

if __name__ == '__main__':
    STYLE = 'tag'
    import os, glob
    for f in glob.glob(f'{OUT}/*.jpg'): os.remove(f)
    ad('wood', 'A MUG FOR EVERY RANK', ROW33, MUG6, 'bf_mugs_wood')
    ad('stripe', 'A MUG FOR EVERY RANK', ROW33, MUG6, 'bf_mugs_stripe')
    ad('paper', 'PICK YOUR COMPANY', GRID4, HAT4, 'bf_hats_paper')
    ad('snow', 'PICK YOUR COMPANY', GRID4, HAT4, 'bf_hats_snow')
    ad('dark', 'GIFTS FOR YOUR FIREFIGHTER', HERO3, GIFT3, 'bf_gifts_dark', dark=True)
    ad('kraft', 'GIFTS FOR YOUR FIREFIGHTER', HERO3, GIFT3, 'bf_gifts_kraft')
    ad('snow', 'FOR THE FIREFIGHTER WHO TRAINS', GRID4, [
        ('shq-fit-stencil-tee_1', 'SHQ FIT STENCIL TEE', 28, ''), ('shq-fit-stencil-tee-light_1', 'STENCIL TEE · OLIVE', 28, ''),
        ('shq-fit-rope-cap_1', 'SHQ FIT ROPE CAP', 34, ''), ('shq-fit-tag-tee_1', 'SHQ FIT TAG TEE', 28, '')], 'bf_gym_snow')
    ad('wood', 'FOR THE WHOLE FIREHOUSE FAMILY', ROW32, [
        ('firehouse-hoodie_2', 'FIREHOUSE HOODIE', 60, ''), ('captain-mug_1', 'CAPTAIN MUG', 24, ''),
        ('engine-company-trucker_1', 'ENGINE TRUCKER', 32, ''), ('nozzle-kids-tee_1', 'NOZZLE KIDS TEE', 24, ''), NOZZLE], 'bf_family_wood')
    ad('stripe', 'STOCKING STUFFERS', GRID4, [
        ('sticker-pack-12_1', '12-STICKER PACK', 14, ''), ('probie-mug_1', 'PROBIE MUG', 24, ''), COLOR,
        ('shq-firehouse-badge-beanie_1', 'FIREHOUSE BEANIE', 28, '')], 'bf_stockings_stripe')
    ad('paper', 'FOR THE JUNIOR FIREFIGHTER', HERO3, [('nozzle-kids-tee_1', 'NOZZLE KIDS TEE', 24, ''), COLOR, NOZZLE], 'bf_kids_paper')
    ad('kraft', 'SOMETHING FOR EVERY FIREFIGHTER', ROW32, [
        ('shq-firehouse-badge-beanie_1', 'BEANIE', 28, ''), ('chief-mug_1', 'CHIEF MUG', 24, ''), ('shq-fit-stencil-tee_1', 'SHQ FIT TEE', 28, ''),
        ('firehouse-tee_1', 'FIREHOUSE TEE', 36, ''), ('sticker-pack-12_1', '12-STICKER PACK', 14, '')], 'bf_everything_kraft')
    print('ok')
