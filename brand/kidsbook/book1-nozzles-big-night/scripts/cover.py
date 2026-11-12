"""KDP paperback cover: 8.5x8.5 trim, premium color, 46 pages.
Spine = 46 x 0.002347 in = 0.108 in. Full cover = 0.125 + 8.5 + 0.108 + 8.5 + 0.125 = 17.358 x 8.75 in."""
import sys
sys.path.insert(0, '/home/claude/kb')
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import textpage as T
from textpage import RED, DRED, YEL, SILVER, CREAM, INK, font, wrap, maltese

DPI = 300
PAGES = 46
SPINE_IN = PAGES * 0.002347
W = round((0.125 + 8.5 + SPINE_IN + 8.5 + 0.125) * DPI)
H = round(8.75 * DPI)
B = round(0.125 * DPI)
TRIM = round(8.5 * DPI)
SP = W - 2 * B - 2 * TRIM
FX = B + TRIM + SP          # front cover trim-left x
OUT = '/home/claude/kb/out/'


def outlined(d, xy, text, f, fill, stroke, sw, shadow=None):
    if shadow:
        d.text((xy[0] + 16, xy[1] + 16), text, font=f, fill=shadow, stroke_width=sw, stroke_fill=shadow)
    d.text(xy, text, font=f, fill=fill, stroke_width=sw, stroke_fill=stroke)


def build():
    c = Image.new('RGB', (W, H), RED)
    # ---- front: art fills trim + bleed (right, top, bottom)
    art = Image.open('/mnt/user-data/uploads/Kids Book/cover_front_KDP.png').convert('RGB')
    fw = W - FX  # trim + right bleed
    art = art.resize((max(fw, H), max(fw, H)), Image.LANCZOS)
    art = art.crop(((art.width - fw) // 2, (art.height - H) // 2, (art.width - fw) // 2 + fw, (art.height - H) // 2 + H))
    c.paste(art, (FX, 0))
    d = ImageDraw.Draw(c)
    cx = FX + TRIM // 2
    # title in the open sky to the right of Brisket's helmet
    tf = ImageFont.truetype(T.SFX, 250)
    right = FX + TRIM - 170
    y = B + 120
    for line in ["NOZZLE'S", 'BIG NIGHT']:
        tw = d.textlength(line, font=tf)
        outlined(d, (right - tw, y), line, tf, YEL, DRED, 14, shadow=(60, 10, 10))
        y += 245
    sf = font(56, 'Bold')
    for k, sub in enumerate(['A Captain Brisket & Nozzle', 'Fire Safety Story']):
        sw = d.textlength(sub, font=sf)
        yy = y + 20 + k * 84
        if k == 0:
            boxw = max(d.textlength('A Captain Brisket & Nozzle', font=sf), d.textlength('Fire Safety Story', font=sf)) + 90
            d.rounded_rectangle((right - boxw, yy - 14, right, yy + 168 + 14), 50, fill=RED, outline=YEL, width=8)
            bcx = right - boxw / 2
        d.text((bcx - sw / 2, yy + 10), sub, font=sf, fill=CREAM)
    # "by a real firefighter" ribbon bottom-left of the front
    rf = font(60, 'Bold')
    rt = 'Written by a real firefighter'
    rw = d.textlength(rt, font=rf) + 90
    rx, ry = FX + 160, H - B - 250
    d.rounded_rectangle((rx, ry, rx + rw, ry + 110), 55, fill=YEL, outline=DRED, width=8)
    d.text((rx + 45, ry + 18), rt, font=rf, fill=DRED)

    # ---- back: diamond plate + cream panel
    back = T.diamond_plate(B + TRIM + SP, H)
    c.paste(back, (0, 0))
    d = ImageDraw.Draw(c)
    m = 190
    L, R = B + m, B + TRIM - m
    top, bot = B + m, H - B - m
    for off, col in ((0, YEL), (26, SILVER), (52, YEL)):
        d.rounded_rectangle((L + off, top + off, R - off, bot - off), 110 - off, fill=col)
    d.rounded_rectangle((L + 78, top + 78, R - 78, bot - 78), 80, fill=CREAM)
    bx = (L + R) / 2
    hf = ImageFont.truetype(T.SFX, 150)
    head = 'NOZZLE WANTS A BADGE.'
    d.text((bx - d.textlength(head, font=hf) / 2, top + 150), head, font=hf, fill=RED)
    body = [
        "But first, Captain Brisket says, he has to learn the rules: smoke alarms, getting low, two ways out and a meeting spot.",
        "Then one night, the smoke alarm goes off at home. Can Nozzle and Mia remember every rule?",
        "Written by a real firefighter, this story teaches kids ages 3 to 7 the 8 Station 12 Rules, with a checklist for grown-ups and a badge certificate to earn.",
    ]
    bf = font(66, 'Medium')
    y = top + 360
    for p in body:
        for ln in wrap(d, p, bf, R - L - 360):
            d.text((bx - d.textlength(ln, font=bf) / 2, y), ln, font=bf, fill=INK)
            y += 88
        y += 44
    # three page thumbnails
    thumbs = ['/home/claude/kb/art/a03.png', '/home/claude/kb/out/t05.png', '/home/claude/kb/art/a12.png']
    tw_, th_ = 470, 477
    gap = 40
    tx = bx - (3 * tw_ + 2 * gap) / 2
    ty = y + 10
    for i, f in enumerate(thumbs):
        im = Image.open(f).convert('RGB').resize((tw_, th_), Image.LANCZOS)
        x = int(tx + i * (tw_ + gap))
        d.rounded_rectangle((x - 10, ty - 10, x + tw_ + 10, ty + th_ + 10), 20, fill=RED)
        c.paste(im, (x, int(ty)))
    # barcode area (KDP prints the barcode here): keep it clear and white
    bw_, bh_ = 600, 360
    bxr, byb = B + TRIM - 250, H - B - 250
    pass  # KDP adds its own white barcode box; no placeholder needed
    # StationHQ line at bottom left of back
    lf = font(52, 'Bold')
    d.text((L + 140, bot - 190), 'stationhq.app', font=lf, fill=DRED)
    return c


if __name__ == '__main__':
    c = build()
    print('cover px', c.size, 'spine px', SP, 'spine in', round(SPINE_IN, 4))
    c.save(OUT + 'cover_full.png', dpi=(DPI, DPI))
    import img2pdf
    c.save(OUT + 'cover_full.jpg', quality=95, dpi=(DPI, DPI), subsampling=0)
    with open(OUT + 'Nozzles_Big_Night_cover_KDP.pdf', 'wb') as fh:
        fh.write(img2pdf.convert([OUT + 'cover_full.jpg'],
                                 layout_fun=img2pdf.get_layout_fun((img2pdf.in_to_pt(W / DPI), img2pdf.in_to_pt(H / DPI)))))
    c.resize((c.width // 4, c.height // 4)).save(OUT + 'cover_preview.jpg', quality=88)
