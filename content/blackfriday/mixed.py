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
    sh = Image.new('RGBA', (x1 - x0 + 60, y1 - y0 + 60), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([30, 36, x1 - x0 + 30, y1 - y0 + 36], 26, fill=(0, 0, 0, 70))
    sh = sh.filter(ImageFilter.GaussianBlur(12))
    b.alpha_composite(sh, (x0 - 30, y0 - 30))
    l = Image.new('RGBA', (x1 - x0, y1 - y0), (0, 0, 0, 0))
    ImageDraw.Draw(l).rounded_rectangle([0, 0, x1 - x0 - 1, y1 - y0 - 1], 26, fill=(252, 249, 243, 246), outline=(222, 206, 184, 255), width=2)
    b.alpha_composite(l, (x0, y0))

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
