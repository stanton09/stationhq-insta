"""Build vertical store promo videos for TikTok from the shop design art.

usage: python3 promo.py <name>
"""
import sys, os, math, subprocess, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter

R = '/home/claude/remote'
FONTS = '/home/claude/fit/fonts'
W, H, FPS = 1080, 1920, 30
GOLD = (226, 169, 59)
CREAM = (243, 231, 207)
RED = (163, 32, 26)
BG = (20, 18, 16)


def font(name, size):
    return ImageFont.truetype(os.path.join(FONTS, name), size)


def background():
    bg = Image.new('RGB', (W, H), BG)
    d = ImageDraw.Draw(bg)
    rnd = random.Random(7)
    # subtle grain + vignette
    for _ in range(9000):
        x, y = rnd.randrange(W), rnd.randrange(H)
        c = rnd.randrange(24, 40)
        d.point((x, y), fill=(c, c - 2, c - 4))
    vig = Image.new('L', (W, H), 0)
    vd = ImageDraw.Draw(vig)
    vd.ellipse((-300, 200, W + 300, H - 200), fill=255)
    vig = vig.filter(ImageFilter.GaussianBlur(220))
    dark = Image.new('RGB', (W, H), (8, 7, 6))
    bg = Image.composite(bg, dark, vig)
    # light-string dots along top like the store header
    d = ImageDraw.Draw(bg)
    cols = [(226, 60, 40), (226, 169, 59), (90, 170, 90), (230, 230, 220)]
    for i, x in enumerate(range(30, W, 60)):
        d.ellipse((x - 9, 52, x + 9, 70), fill=cols[i % 4])
    d.line((0, 61, W, 61), fill=(60, 55, 50), width=2)
    return bg


def text_center(d, y, s, f, fill, shadow=True):
    w = d.textlength(s, font=f)
    if shadow:
        d.text(((W - w) / 2 + 4, y + 4), s, font=f, fill=(0, 0, 0))
    d.text(((W - w) / 2, y), s, font=f, fill=fill)


def ease(t):
    return 1 - (1 - t) ** 3


def render(slides, title, outro, music, out, seconds_per=1.4, music_start=0):
    base = background()
    tmp = f'/tmp/tt_{os.path.basename(out)}_frames'
    os.makedirs(tmp, exist_ok=True)
    for f in os.listdir(tmp):
        os.remove(os.path.join(tmp, f))
    fr = 0

    def emit(im):
        nonlocal fr
        im.save(f'{tmp}/{fr:05d}.jpg', quality=90)
        fr += 1

    big = font('Anton-Regular.ttf', 150)
    mid = font('Anton-Regular.ttf', 96)
    small = font('Oswald.ttf', 54)
    tiny = font('Oswald.ttf', 44)

    # intro title 1.6s
    for i in range(int(1.6 * FPS)):
        t = ease(min(1, i / 12))
        im = base.copy()
        d = ImageDraw.Draw(im)
        y0 = 700 + (1 - t) * 80
        for k, line in enumerate(title):
            text_center(d, y0 + k * 170, line, big, CREAM if k == 0 else GOLD)
        emit(im)

    for img_path, label, sub in slides:
        art = Image.open(img_path).convert('RGBA')
        art.thumbnail((860, 860))
        n = int(seconds_per * FPS)
        for i in range(n):
            t = ease(min(1, i / 9))
            sc = 0.82 + 0.18 * t + 0.03 * (i / n)
            a = art.resize((max(1, int(art.width * sc)), max(1, int(art.height * sc))), Image.LANCZOS)
            im = base.copy()
            # glow
            glow = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            gd = ImageDraw.Draw(glow)
            gd.ellipse((W / 2 - 430, 860 - 430, W / 2 + 430, 860 + 430), fill=(226, 120, 40, int(70 * t)))
            glow = glow.filter(ImageFilter.GaussianBlur(120))
            im.paste(glow, (0, 0), glow)
            im.paste(a, (int((W - a.width) / 2), int(860 - a.height / 2)), a)
            d = ImageDraw.Draw(im)
            text_center(d, 1380, label, mid, CREAM)
            if sub:
                text_center(d, 1500, sub, small, GOLD)
            emit(im)

    # outro 3s
    logo = Image.open(f'{R}/brand/shop/web/vintage.webp').convert('RGBA')
    logo.thumbnail((560, 640))
    for i in range(int(3.2 * FPS)):
        t = ease(min(1, i / 12))
        im = base.copy()
        im.paste(logo, (int((W - logo.width) / 2), 330), logo)
        d = ImageDraw.Draw(im)
        for k, line in enumerate(outro):
            f = mid if k == 0 else (small if k == 1 else tiny)
            col = CREAM if k == 0 else GOLD if k == 1 else (200, 190, 175)
            text_center(d, 1090 + k * 120 + (1 - t) * 40, line, f, col)
        emit(im)

    dur = fr / FPS
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(FPS), '-i', f'{tmp}/%05d.jpg',
                    '-ss', str(music_start), '-i', music, '-t', f'{dur:.2f}',
                    '-af', f'afade=t=in:d=0.4,afade=t=out:st={dur-1.2:.2f}:d=1.2',
                    '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-pix_fmt', 'yuv420p',
                    '-c:a', 'aac', '-b:a', '160k', '-shortest', '-movflags', '+faststart', out], check=True)
    print(out, f'{dur:.1f}s')


W_ = f'{R}/brand/shop/web'
M = f'{R}/brand/brisket/music'
OUT = '/home/claude/tt/out'
os.makedirs(OUT, exist_ok=True)
OUTRO = ['STATIONHQ SHOP', 'Built by an active firefighter', 'stationhq-shop.fourthwall.com']

if sys.argv[1] == 'company':
    render([(f'{W_}/engine.webp', 'ENGINE', 'Put the wet stuff on the red stuff'),
            (f'{W_}/truck.webp', 'TRUCK', 'Vent. Enter. Search.'),
            (f'{W_}/ladder.webp', 'LADDER', 'Up and over'),
            (f'{W_}/rescue.webp', 'RESCUE', 'When it all goes wrong'),
            (f'{W_}/squad.webp', 'SQUAD', 'Tools for every job'),
            (f'{W_}/tower.webp', 'TOWER', 'Reach for it')],
           ['WHICH COMPANY', 'ARE YOU?'], OUTRO, f'{M}/music_ready_aim_fire.mp3', f'{OUT}/company.mp4', 1.5, 2)
elif sys.argv[1] == 'classics':
    render([(f'{W_}/filo.webp', 'FIRST IN, LAST OUT', 'Tee'),
            (f'{W_}/answer.webp', 'ANSWER THE CALL', 'Tee'),
            (f'{W_}/irons.webp', 'THE IRONS', 'Forcible entry since day one'),
            (f'{W_}/firehouse.webp', 'FIREHOUSE', 'Always ready'),
            (f'{W_}/engineco.webp', 'ENGINE COMPANY', 'Wet stuff, red stuff'),
            (f'{W_}/nozzle.webp', 'NOZZLE THE FIREHOUSE DOG', 'Kids tee')],
           ['GEAR FROM THE', 'FIREHOUSE'], ['NOT THE COSTUME SHOP', 'Designed by an active firefighter', 'stationhq-shop.fourthwall.com'],
           f'{M}/music_guts_and_bourbon.mp3', f'{OUT}/classics.mp4', 1.5, 0)
