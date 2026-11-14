"""Mixed-item Black Friday ads (shop items 20% off + books on Amazon)."""
import sys
sys.argv = [sys.argv[0], '20']
from build import *  # noqa

def fit_headline(b, text, y, dark=False, maxw=760, size=78):
    d = ImageDraw.Draw(b)
    while d.textlength(text, font=BIG(size)) > maxw and size > 44: size -= 2
    d.text((W // 2 - 60, y), text, font=BIG(size), fill='white' if dark else (24, 22, 20), anchor='mm')

CARDS = True
def card(b, x0, y0, x1, y1, dark=False):
    w, h = x1 - x0, y1 - y0
    sh = Image.new('RGBA', (w + 60, h + 60), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([30, 36, w + 30, h + 36], 24, fill=(0, 0, 0, 80))
    b.alpha_composite(sh.filter(ImageFilter.GaussianBlur(12)), (x0 - 30, y0 - 30))
    # warm vertical gradient: soft blush top -> warm cream bottom, slightly see-through
    top, bot = (252, 236, 226), (244, 230, 206)
    grad = Image.new('RGBA', (w, h))
    gd = ImageDraw.Draw(grad)
    for yy in range(h):
        t = yy / max(1, h - 1)
        gd.line([(0, yy), (w, yy)], fill=tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3)) + (232,))
    # soft light behind the product
    glow = Image.radial_gradient('L').resize((int(w * 1.1), int(h * .9))).point(lambda v: max(0, 120 - v // 2))
    gl = Image.new('RGBA', glow.size, (255, 252, 246, 0)); gl.putalpha(glow)
    grad.alpha_composite(gl, (int(-w * .05), int(-h * .05)))
    mask = Image.new('L', (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, w - 1, h - 1], 24, fill=255)
    card_img = Image.new('RGBA', (w, h), (0, 0, 0, 0)); card_img.paste(grad, (0, 0), mask)
    d = ImageDraw.Draw(card_img)
    # red top band + gold rule
    band = Image.new('RGBA', (w, h), (0, 0, 0, 0)); bd = ImageDraw.Draw(band)
    bd.rounded_rectangle([0, 0, w - 1, 40], 24, fill=(176, 28, 32, 255))
    band_mask = Image.new('L', (w, h), 0); ImageDraw.Draw(band_mask).rectangle([0, 0, w, 11], fill=255)
    band_mask = Image.composite(band_mask, Image.new('L', (w, h), 0), mask)
    card_img.paste(band, (0, 0), band_mask)
    d.line([(14, 13), (w - 14, 13)], fill=(206, 168, 92, 255), width=2)
    d.rounded_rectangle([0, 0, w - 1, h - 1], 24, outline=(196, 160, 110, 255), width=2)
    b.alpha_composite(card_img, (x0, y0))

def item(b, it, cx, cy, box, dark=False, cw=None):
    name, lab, price, note = it
    if CARDS:
        cw = cw or box[0] + 40
        card(b, int(cx - cw / 2), int(cy - box[1] / 2 - 26), int(cx + cw / 2), int(cy + box[1] / 2 + 104))
        dark_txt = False
    else:
        dark_txt = dark
    x, y, w, h = place(b, name, cx, cy, box, glow=dark and not CARDS)
    dark = dark_txt
    ly = cy + box[1] / 2 + 36
    label(b, cx, ly, lab, dark)
    if price is not None:
        sale_tag(b, cx, ly + 46, price, dark)
    else:
        d = ImageDraw.Draw(b)
        d.text((cx, ly + 44), note, font=BIG(36), fill=(255, 90, 80) if dark else RED, anchor='mm')

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

ad('snow', 'FOR THE FIREFIGHTER WHO TRAINS', GRID4, [
    ('shq-fit-stencil-tee_1', 'SHQ FIT STENCIL TEE', 28, ''),
    ('shq-fit-stencil-tee-light_1', 'STENCIL TEE · OLIVE', 28, ''),
    ('shq-fit-rope-cap_1', 'SHQ FIT ROPE CAP', 34, ''),
    ('shq-fit-tag-tee_1', 'SHQ FIT TAG TEE', 28, ''),
], 'bf_gym_snow')

ad('wood', 'FOR THE WHOLE FIREHOUSE FAMILY', ROW32, [
    ('firehouse-hoodie_2', 'FIREHOUSE HOODIE', 60, ''),
    ('captain-mug_1', 'CAPTAIN MUG', 24, ''),
    ('engine-company-trucker_1', 'ENGINE TRUCKER', 32, ''),
    ('nozzle-kids-tee_1', 'NOZZLE KIDS TEE', 24, ''),
    NOZZLE,
], 'bf_family_wood')

ad('stripe', 'STOCKING STUFFERS', GRID4, [
    ('sticker-pack-12_1', '12-STICKER PACK', 14, ''),
    ('probie-mug_1', 'PROBIE MUG', 24, ''),
    COLOR,
    ('shq-firehouse-badge-beanie_1', 'FIREHOUSE BEANIE', 28, ''),
], 'bf_stockings_stripe')

ad('paper', 'FOR THE JUNIOR FIREFIGHTER', HERO3, [
    ('nozzle-kids-tee_1', 'NOZZLE KIDS TEE', 24, ''),
    COLOR, NOZZLE,
], 'bf_kids_paper')

ad('kraft', 'SOMETHING FOR EVERY FIREFIGHTER', ROW32, [
    ('shq-firehouse-badge-beanie_1', 'BEANIE', 28, ''),
    ('chief-mug_1', 'CHIEF MUG', 24, ''),
    ('shq-fit-stencil-tee_1', 'SHQ FIT TEE', 28, ''),
    ('firehouse-tee_1', 'FIREHOUSE TEE', 36, ''),
    ('sticker-pack-12_1', '12-STICKER PACK', 14, ''),
], 'bf_everything_kraft')

print('ok')
