"""Black Friday ads: Jesse's holiday backgrounds + real product photos (cut out) + sale tags."""
import os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from scipy import ndimage

DISC = int(sys.argv[1]) if len(sys.argv) > 1 else 25
W, H = 1080, 1350
U = '/mnt/user-data/uploads'
P = '/home/claude/remote/brand/products'
F = '/home/claude/fit/fonts'
OUT = '/home/claude/tt/out/bf'; os.makedirs(OUT, exist_ok=True)
BGS = {'wood': '0eadadcc-image.png', 'kraft': '4c4f8de2-image.png', 'paper': '59e70172-image.png',
       'snow': '26ee2211-image.png', 'stripe': '7343822a-image.png', 'dark': '093c17e1-image.png'}
RED = (190, 26, 30)

def font(n, s): return ImageFont.truetype(os.path.join(F, n), s)
BIG = lambda s: font('Anton-Regular.ttf', s)
SM = lambda s: font('Oswald.ttf', s)

_cache = {}
def cutout(name):
    if name in _cache: return _cache[name]
    im = Image.open(f'{P}/{name}.jpg').convert('RGB')
    a = np.asarray(im).astype(int)
    light = a.min(2) > 226
    lab, n = ndimage.label(light)
    edge = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    bg = np.isin(lab, list(edge))
    # enclosed pure-white holes (inside mug handles) are background too
    bright = a.min(2) > 243
    lab2, n2 = ndimage.label(bright)
    sizes = ndimage.sum(bright, lab2, range(1, n2 + 1))
    holes = np.isin(lab2, [i + 1 for i, sz in enumerate(sizes) if sz > 4000])
    fg = ~(bg | holes)
    alpha = Image.fromarray((fg * 255).astype('uint8')).filter(ImageFilter.GaussianBlur(1.2))
    rgba = im.convert('RGBA'); rgba.putalpha(alpha)
    rgba = rgba.crop(alpha.getbbox())
    _cache[name] = rgba
    return rgba

def place(base, name, cx, cy, box):
    p = cutout(name)
    s = min(box[0] / p.width, box[1] / p.height)
    p = p.resize((int(p.width * s), int(p.height * s)), Image.LANCZOS)
    x, y = int(cx - p.width / 2), int(cy - p.height / 2)
    # soft contact shadow
    sh = Image.new('RGBA', (p.width + 80, p.height + 80), (0, 0, 0, 0))
    a = p.split()[3].point(lambda v: int(v * 0.42))
    blk = Image.new('RGBA', p.size, (0, 0, 0, 255)); blk.putalpha(a)
    sh.paste(blk, (40, 40), blk)
    sh = sh.filter(ImageFilter.GaussianBlur(14))
    base.alpha_composite(sh, (x - 40 + 8, y - 40 + 18))
    base.alpha_composite(p, (x, y))
    return x, y, p.width, p.height

def sale_tag(base, cx, cy, price, dark=False):
    """Name-free price line: old price struck, new price bold."""
    d = ImageDraw.Draw(base)
    new = price * (100 - DISC) / 100
    old_s, new_s = f'${price:.0f}', f'${new:.2f}'.replace('.00', '')
    fo, fn = SM(34), BIG(46)
    wo, wn = d.textlength(old_s, font=fo), d.textlength(new_s, font=fn)
    gap = 14; tw = wo + gap + wn
    x0 = cx - tw / 2
    oc = (200, 190, 175) if dark else (120, 110, 100)
    d.text((x0, cy), old_s, font=fo, fill=oc, anchor='lm')
    d.line([(x0 - 3, cy + 2), (x0 + wo + 3, cy + 2)], fill=oc, width=3)
    d.text((x0 + wo + gap + wn / 2, cy), new_s, font=fn, fill=(255, 90, 80) if dark else RED, anchor='mm')

def badge(base, cx, cy, r=84):
    """Round '% OFF' sticker."""
    l = Image.new('RGBA', (r * 6, r * 6), (0, 0, 0, 0)); d = ImageDraw.Draw(l)
    c = r * 3
    d.ellipse([c - r * 3 + 6, c - r * 3 + 6, c + r * 3 - 6, c + r * 3 - 6], fill=RED)
    d.ellipse([c - r * 3 + 22, c - r * 3 + 22, c + r * 3 - 22, c + r * 3 - 22], outline=(255, 236, 200), width=5)
    d.text((c, c - r * .35), f'{DISC}%', font=BIG(int(r * 1.45)), fill='white', anchor='mm')
    d.text((c, c + r * 1.45), 'OFF', font=BIG(int(r * .9)), fill='white', anchor='mm')
    l = l.resize((r * 2, r * 2), Image.LANCZOS).rotate(-12, resample=Image.BICUBIC, expand=True)
    base.alpha_composite(l, (int(cx - l.width / 2), int(cy - l.height / 2)))

def label(base, cx, cy, text, dark=False):
    d = ImageDraw.Draw(base)
    d.text((cx, cy), text, font=BIG(40), fill='white' if dark else (24, 22, 20), anchor='mm',
           stroke_width=0)

def headline(base, text, y, dark=False):
    d = ImageDraw.Draw(base)
    d.text((W // 2, y), text, font=BIG(76), fill='white' if dark else (24, 22, 20), anchor='mm')

def footer(base, line, dark=False):
    d = ImageDraw.Draw(base)
    logo = Image.open('/home/claude/tt/bf/xmas_logo.png').convert('RGBA')
    logo = logo.crop((0, 18, logo.width, logo.height))
    s = 128 / logo.height; logo = logo.resize((int(logo.width * s), 128), Image.LANCZOS)
    base.alpha_composite(logo, (66, H - 168))
    tc = (235, 228, 215) if dark else (70, 62, 54)
    d.text((222, H - 120), line, font=SM(30), fill=tc, anchor='lm')
    d.text((W - 70, H - 104), 'shop.stationhq.app', font=BIG(44), fill=(255, 90, 80) if dark else RED, anchor='rm')

def bg(key):
    return Image.open(f'{U}/{BGS[key]}').convert('RGBA').resize((W, H), Image.LANCZOS)

def grid(key, head, items, cols, box, row_h, top, line, dark=False):
    b = bg(key)
    headline(b, head, 395, dark)
    rows = (len(items) + cols - 1) // cols
    colw = (W - 120) / cols
    for i, (name, lab, price) in enumerate(items):
        cx = 60 + colw * (i % cols + .5); cy = top + row_h * (i // cols)
        place(b, name, cx, cy, box)
        label(b, cx, cy + box[1] / 2 + 34, lab, dark)
        sale_tag(b, cx, cy + box[1] / 2 + 82, price, dark)
    badge(b, W - 110, 395)
    footer(b, line, dark)
    return b.convert('RGB')

MUGS = [('probie-mug_1', 'PROBIE', 24), ('firefighter-mug_1', 'FIREFIGHTER', 24), ('engineer-mug_1', 'ENGINEER', 24),
        ('lieutenant-mug_1', 'LIEUTENANT', 24), ('captain-mug_1', 'CAPTAIN', 24), ('chief-mug_1', 'CHIEF', 24)]
HATS = [('engine-company-trucker_1', 'ENGINE', 32), ('ladder-company-trucker_1', 'LADDER', 32),
        ('rescue-company-trucker_1', 'RESCUE', 32), ('shq-firehouse-badge-beanie_1', 'FIREHOUSE BEANIE', 28)]

grid('wood', 'A MUG FOR EVERY RANK', MUGS, 3, (290, 210), 355, 545, 'Order by Dec 10 for Christmas').save(f'{OUT}/bf_mugs_wood.jpg', quality=94)
grid('paper', 'PICK YOUR COMPANY', HATS, 2, (360, 260), 380, 590, 'Order by Dec 10 for Christmas').save(f'{OUT}/bf_hats_paper.jpg', quality=94)
grid('snow', 'PICK YOUR COMPANY', HATS, 2, (360, 260), 380, 590, 'Order by Dec 10 for Christmas').save(f'{OUT}/bf_hats_snow.jpg', quality=94)
grid('stripe', 'A MUG FOR EVERY RANK', MUGS, 3, (280, 205), 355, 545, 'Order by Dec 10 for Christmas').save(f'{OUT}/bf_mugs_stripe.jpg', quality=94)

# Gift layouts: hoodie hero + mug + hat
def gifts(key, dark=False):
    b = bg(key)
    headline(b, 'GIFTS FOR YOUR FIREFIGHTER', 400, dark)
    place(b, 'firehouse-hoodie_2', 360, 760, (560, 640))
    label(b, 360, 1110, 'FIREHOUSE HOODIE', dark); sale_tag(b, 360, 1158, 60, dark)
    place(b, 'captain-mug_1', 820, 610, (300, 240))
    label(b, 820, 765, 'CAPTAIN MUG', dark); sale_tag(b, 820, 812, 24, dark)
    place(b, 'engine-company-trucker_1', 820, 950, (300, 230))
    label(b, 820, 1100, 'ENGINE TRUCKER', dark); sale_tag(b, 820, 1148, 32, dark)
    badge(b, 110, 530)
    footer(b, 'Order by Dec 10 for Christmas', dark)
    return b.convert('RGB')

gifts('dark', True).save(f'{OUT}/bf_gifts_dark.jpg', quality=94)
gifts('kraft').save(f'{OUT}/bf_gifts_kraft.jpg', quality=94)
print('done', DISC)
