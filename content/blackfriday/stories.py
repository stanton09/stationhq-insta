"""9:16 Instagram Story versions of the Black Friday ads, dated for the story queue."""
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

SRC = '/home/claude/tt/out/bf'
OUT = '/home/claude/remote/content/stories'; os.makedirs(OUT, exist_ok=True)
F = '/home/claude/fit/fonts'
BIG = lambda s: ImageFont.truetype(f'{F}/Anton-Regular.ttf', s)
SM = lambda s: ImageFont.truetype(f'{F}/Oswald.ttf', s)
GOLD = (255, 214, 120)

PLAN = [  # date, ad, top line
    ('2026-11-17', 'bf_gifts_kraft', 'EARLY BLACK FRIDAY IS LIVE'),
    ('2026-11-18', 'bf_family_wood', '20% OFF EVERYTHING'),
    ('2026-11-19', 'bf_mugs_wood', '20% OFF EVERYTHING'),
    ('2026-11-20', 'bf_gym_snow', '20% OFF THE GYM LINE'),
    ('2026-11-21', 'bf_hats_paper', '20% OFF EVERYTHING'),
    ('2026-11-22', 'bf_kids_paper', 'FOR THE JUNIOR FIREFIGHTER'),
    ('2026-11-23', 'bf_everything_kraft', '20% OFF EVERYTHING'),
    ('2026-11-24', 'bf_stockings_stripe', 'STOCKING STUFFERS'),
    ('2026-11-25', 'bf_gifts_dark', '20% OFF EVERYTHING'),
    ('2026-11-26', 'bf_mugs_stripe', 'A MUG FOR EVERY RANK'),
    ('2026-11-27', 'bf_family_wood', 'HAPPY THANKSGIVING'),
    ('2026-11-28', 'bf_hats_snow', 'BLACK FRIDAY IS HERE'),
    ('2026-11-29', 'bf_everything_kraft', 'SALE ENDS MONDAY'),
    ('2026-11-30', 'bf_gifts_kraft', '2 DAYS LEFT'),
    ('2026-12-01', 'bf_mugs_wood', 'LAST DAY · ENDS TONIGHT'),
]

for date, name, top in PLAN:
    ad = Image.open(f'{SRC}/{name}.jpg').convert('RGB')
    W, H = 1080, 1920
    bg = ad.resize((int(H * ad.width / ad.height), H), Image.LANCZOS)
    bg = bg.crop(((bg.width - W) // 2, 0, (bg.width - W) // 2 + W, H)).filter(ImageFilter.GaussianBlur(28))
    bg = ImageEnhance.Brightness(bg).enhance(0.45)
    aw = 980; ah = int(aw * ad.height / ad.width)
    a = ad.resize((aw, ah), Image.LANCZOS)
    x, y = (W - aw) // 2, 330
    sh = Image.new('RGBA', (aw + 80, ah + 80), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([40, 48, aw + 40, ah + 48], 28, fill=(0, 0, 0, 150))
    bg = bg.convert('RGBA'); bg.alpha_composite(sh.filter(ImageFilter.GaussianBlur(18)), (x - 40, y - 40))
    m = Image.new('L', (aw, ah), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, aw - 1, ah - 1], 28, fill=255)
    bg.paste(a, (x, y), m)
    d = ImageDraw.Draw(bg)
    d.text((W // 2, 255), top, font=BIG(70), fill=GOLD, anchor='mm', stroke_width=3, stroke_fill=(60, 10, 10))
    yb = y + ah + 95
    d.text((W // 2, yb), 'SHOP.STATIONHQ.APP', font=BIG(66), fill='white', anchor='mm', stroke_width=3, stroke_fill=(60, 10, 10))
    d.text((W // 2, yb + 70), 'Link in bio  ·  20% off through Dec 1', font=SM(38), fill=(235, 225, 210), anchor='mm')
    bg.convert('RGB').save(f'{OUT}/d{date}_{name}.jpg', quality=92)
print('ok')
