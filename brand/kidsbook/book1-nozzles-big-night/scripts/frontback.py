"""Front/back matter pages + full interior assembly for Nozzle's Big Night."""
import sys
sys.path.insert(0, '/home/claude/kb')
from PIL import Image, ImageDraw, ImageFont
import textpage as T
from textpage import W, H, RED, DRED, YEL, SILVER, CREAM, INK, font, maltese, wrap
from portraits import P

SFX = T.SFX
OUT = '/home/claude/kb/out/'


def center(d, y, text, f, fill):
    d.text(((W - d.textlength(text, font=f)) / 2, y), text, font=f, fill=fill)


def round_portrait(im, art, cx, cy, r, D, px, py):
    d = ImageDraw.Draw(im)
    src = Image.open(f'/home/claude/kb/art/{art}.png').convert('RGB').crop((cx - r, cy - r, cx + r, cy + r)).resize((D, D), Image.LANCZOS)
    m = Image.new('L', (D, D), 0)
    ImageDraw.Draw(m).ellipse((0, 0, D, D), fill=255)
    for g, col in ((60, RED), (38, YEL), (18, SILVER)):
        d.ellipse((px - g, py - g, px + D + g, py + D + g), fill=col)
    im.paste(src, (px, py), m)


def title_page():
    im, d = T.base()
    center(d, 380, 'A Captain Brisket & Nozzle Fire Safety Story', font(70, 'Bold'), DRED)
    tf = ImageFont.truetype(SFX, 330)
    for i, line in enumerate(["NOZZLE'S", 'BIG NIGHT']):
        tw = d.textlength(line, font=tf)
        x, y = (W - tw) / 2, 500 + i * 330
        d.text((x + 14, y + 14), line, font=tf, fill=DRED)
        d.text((x, y), line, font=tf, fill=RED, stroke_width=10, stroke_fill=DRED)
    D = 920
    round_portrait(im, 'a14', 1640, 1300, 470, D, (W - D) // 2, 1220)
    center(d, 2240, 'Book 1', font(72, 'Bold'), RED)
    return im


def copyright_page():
    im, d = T.base()
    f = font(56, 'Medium')
    fb = font(60, 'Bold')
    y = 520
    blocks = [
        (fb, "Nozzle's Big Night: A Captain Brisket & Nozzle Fire Safety Story"),
        (f, 'Copyright © 2026 JDX Group LLC. All rights reserved.'),
        (f, 'Captain Brisket, Nozzle and Station 12 are characters of StationHQ, a brand of JDX Group LLC.'),
        (f, 'No part of this book may be copied or shared in any form without written permission, except short quotes in reviews.'),
        (f, 'A note for grown-ups: the lessons in this book follow common fire department advice for families. Every home is different. Your local fire department can help you make your family’s escape plan. In an emergency, get out and call 9-1-1.'),
        (f, 'First edition, 2026'),
        (f, 'stationhq.app  ·  shop.stationhq.app'),
    ]
    for fnt, txt in blocks:
        for ln in wrap(d, txt, fnt, 1560):
            center(d, y, ln, fnt, INK)
            y += int(fnt.size * 1.35)
        y += 60
    return im


def belongs_page():
    im, d = T.base()
    D = 900
    a, cx, cy, r, _ = P[20]
    round_portrait(im, a, cx, cy, r, D, (W - D) // 2, 430)
    center(d, 1500, 'This book belongs to', font(120, 'Bold'), RED)
    d.line((560, 1880, W - 560, 1880), fill=INK, width=8)
    center(d, 1960, 'Junior Firefighter, Station 12', font(70, 'Medium'), DRED)
    return im


def checklist_page():
    im, d = T.base()
    D = 420
    a, cx, cy, r, _ = P[8]
    round_portrait(im, a, cx, cy, r, D, (W - D) // 2, 330)
    center(d, 830, "Captain Brisket's", font(110, 'Bold'), RED)
    center(d, 960, 'Checklist for Grown-Ups', font(110, 'Bold'), RED)
    items = ['Test smoke alarms once a month.',
             'Make an escape plan with two ways out of every room.',
             'Pick a meeting spot outside.',
             'Practice a fire drill twice a year, once at night.',
             'Teach kids: get low and go, never hide, never go back in.',
             'Make sure kids know their address and how to call 9-1-1.']
    f = font(74, 'Medium')
    y = 1170
    for it in items:
        d.rounded_rectangle((450, y + 8, 530, y + 88), 14, outline=RED, width=10, fill='white')
        lines = wrap(d, it, f, 1480)
        for ln in lines:
            d.text((580, y), ln, font=f, fill=INK)
            y += 92
        y += 40
    return im


def certificate_page():
    im, d = T.base()
    center(d, 380, 'OFFICIAL STATION 12', font(90, 'Bold'), DRED)
    tf = ImageFont.truetype(SFX, 230)
    t = 'ESCAPE BADGE'
    x = (W - d.textlength(t, font=tf)) / 2
    d.text((x + 10, 500 + 10), t, font=tf, fill=DRED)
    d.text((x, 500), t, font=tf, fill=RED, stroke_width=8, stroke_fill=DRED)
    cx, cy = W // 2, 1150
    maltese(d, cx, cy, 330, RED)
    d.ellipse((cx - 160, cy - 160, cx + 160, cy + 160), fill=YEL, outline=DRED, width=12)
    nf = ImageFont.truetype(SFX, 230)
    d.text((cx - d.textlength('12', font=nf) / 2, cy - 125), '12', font=nf, fill=RED)
    f = font(78, 'Medium')
    center(d, 1560, 'This certifies that', f, INK)
    d.line((480, 1800, W - 480, 1800), fill=INK, width=8)
    for i, ln in enumerate(['knows all 8 Station 12 Rules and', 'has earned the Escape Badge!']):
        center(d, 1850 + i * 100, ln, f, INK)
    sf = font(62, 'Bold')
    d.line((470, 2210, 1180, 2210), fill=INK, width=5)
    d.line((1410, 2210, 2120, 2210), fill=INK, width=5)
    d.text((825 - d.textlength('Capt. Brisket', font=sf) / 2, 2230), 'Capt. Brisket', font=sf, fill=DRED)
    d.text((1765 - d.textlength('Nozzle', font=sf) / 2, 2230), 'Nozzle', font=sf, fill=DRED)
    T.paw(d, 1765, 2140, 34, (90, 60, 50))
    return im


def series_page():
    im, d = T.base()
    tf = ImageFont.truetype(SFX, 170)
    for i, line in enumerate(['COLLECT ALL OF', "NOZZLE'S BADGES!"]):
        x = (W - d.textlength(line, font=tf)) / 2
        d.text((x + 8, 400 + i * 180 + 8), line, font=tf, fill=DRED)
        d.text((x, 400 + i * 180), line, font=tf, fill=RED)
    books = [('Escape Badge', "Nozzle's Big Night", True)] + [('Badge #%d' % k, 'Coming soon', False) for k in range(2, 7)]
    for i, (badge, sub, done) in enumerate(books):
        col, row = i % 2, i // 2
        cx, cy = 900 + col * 790, 1090 + row * 470
        maltese(d, cx, cy, 160, RED if done else (214, 196, 160))
        d.ellipse((cx - 72, cy - 72, cx + 72, cy + 72), fill=YEL if done else CREAM, outline=DRED if done else (200, 180, 140), width=8)
        nf = ImageFont.truetype(SFX, 110)
        mark = str(i + 1) if done else '?'
        d.text((cx - d.textlength(mark, font=nf) / 2, cy - 60), mark, font=nf, fill=RED if done else (190, 170, 130))
        bf, sf2 = font(64, 'Bold'), font(54, 'Medium')
        d.text((cx - d.textlength(badge, font=bf) / 2, cy + 190), badge, font=bf, fill=INK if done else (150, 130, 100))
        d.text((cx - d.textlength(sub, font=sf2) / 2, cy + 265), sub, font=sf2, fill=DRED if done else (150, 130, 100))
    return im


STORY_ORDER = [('a01', 1), ('a16', 2), ('a02', 3), ('a15', 4), ('a03', 5), ('a04', 6), ('a17', 7), ('a05', 8),
               ('a06', 9), ('a07', 10), ('a08', 11), ('a09', 12), ('a10', 13), ('a18', 14), ('a11', 15),
               ('a12', 16), ('a19', 17), ('a13', 18), ('a14', 19), ('a20', 20)]


def build():
    import img2pdf, os
    pages = [title_page(), copyright_page(), belongs_page()]
    for art, n in STORY_ORDER:
        pages.append(Image.open(f'/home/claude/kb/art/{art}.png').convert('RGB'))
        pages.append(Image.open(f'{OUT}t{n:02d}.png').convert('RGB'))
    pages += [checklist_page(), certificate_page(), series_page()]
    assert len(pages) == 46, len(pages)
    os.makedirs(OUT + 'pages', exist_ok=True)
    files = []
    for i, p in enumerate(pages, 1):
        assert p.size == (W, H)
        fn = f'{OUT}pages/p{i:02d}.jpg'
        p.save(fn, quality=95, dpi=(300, 300), subsampling=0)
        files.append(fn)
    layout = img2pdf.get_layout_fun((img2pdf.in_to_pt(8.625), img2pdf.in_to_pt(8.75)))
    with open(OUT + 'Nozzles_Big_Night_interior_KDP.pdf', 'wb') as fh:
        fh.write(img2pdf.convert(files, layout_fun=layout))
    # contact sheet as spreads (page 1 alone on the right)
    tw, th = 300, 304
    sheet = Image.new('RGB', (tw * 8 + 70, th * 12 + 120), (230, 230, 230))
    order = [None] + list(range(46)) + [None]
    for k in range(0, len(order), 2):
        sp = k // 2
        x0, y0 = (sp % 4) * (tw * 2 + 18) + 10, (sp // 4) * (th + 10) + 10
        for j in (0, 1):
            idx = order[k + j]
            if idx is not None:
                sheet.paste(pages[idx].resize((tw, th)), (x0 + j * tw, y0))
    sheet.save(OUT + 'interior_spreads.jpg', quality=80)


if __name__ == '__main__':
    build()
    print('done')
