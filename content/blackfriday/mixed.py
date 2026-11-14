"""Mixed-item Black Friday ads (shop items 20% off + books on Amazon)."""
import sys
sys.argv = [sys.argv[0], '20']
from build import *  # noqa

def fit_headline(b, text, y, dark=False, maxw=760, size=78):
    d = ImageDraw.Draw(b)
    while d.textlength(text, font=BIG(size)) > maxw and size > 44: size -= 2
    d.text((W // 2 - 60, y), text, font=BIG(size), fill='white' if dark else (24, 22, 20), anchor='mm')

def item(b, it, cx, cy, box, dark=False):
    name, lab, price, note = it
    x, y, w, h = place(b, name, cx, cy, box, glow=dark)
    ly = y + h + 34
    label(b, cx, ly, lab, dark)
    if price is not None:
        sale_tag(b, cx, ly + 46, price, dark)
    else:
        d = ImageDraw.Draw(b)
        d.text((cx, ly + 44), note, font=BIG(36), fill=(255, 90, 80) if dark else RED, anchor='mm')

def ad(key, head, layout, items, out, dark=False):
    b = bg(key)
    fit_headline(b, head, 400, dark)
    badge(b, W - 115, 400, r=80)
    for it, (cx, cy, bw, bh) in zip(items, layout):
        item(b, it, cx, cy, (bw, bh), dark)
    footer(b, 'Order by Dec 10 for Christmas', dark)
    b.convert('RGB').save(f'{OUT}/{out}.jpg', quality=94)

# layouts: (cx, cy, box_w, box_h) — cy is product center
GRID4 = [(290, 595, 380, 230), (790, 595, 380, 230), (290, 960, 380, 230), (790, 960, 380, 230)]
HERO3 = [(360, 740, 540, 560), (820, 600, 290, 210), (820, 930, 290, 210)]
ROW32 = [(200, 600, 290, 220), (540, 600, 290, 220), (880, 600, 290, 220), (330, 930, 340, 240), (750, 930, 340, 240)]

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

gifts('dark', True).save(f'{OUT}/bf_gifts_dark.jpg', quality=94)
print('ok')
