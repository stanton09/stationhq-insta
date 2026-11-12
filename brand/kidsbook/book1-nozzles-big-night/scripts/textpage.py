"""Right-hand story pages: cream paper inside a turnout-coat frame (red, yellow + silver reflective stripe)."""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import random, sys
sys.path.insert(0, '/home/claude/kb')

W, H = 2588, 2625
FONT = '/home/claude/kb/fonts/Fredoka.ttf'
SFX = '/home/claude/kb/fonts/Bangers.ttf'
INK = (40, 28, 26)
RED = (186, 26, 32)
DRED = (130, 14, 20)
YEL = (255, 206, 38)
SILVER = (205, 210, 214)
CREAM = (255, 245, 222)
GOLD = (232, 170, 40)


def font(size, weight='SemiBold'):
    f = ImageFont.truetype(FONT, size)
    f.set_variation_by_name(weight)
    return f


def paw(d, cx, cy, s, fill):
    d.ellipse((cx - s, cy - s * 0.7, cx + s, cy + s * 0.9), fill=fill)
    for dx, dy in ((-1.15, -1.25), (-0.4, -1.75), (0.4, -1.75), (1.15, -1.25)):
        r = s * 0.38
        x, y = cx + dx * s, cy + dy * s
        d.ellipse((x - r, y - r * 1.15, x + r, y + r * 1.15), fill=fill)


def diamond_plate(w, h, base=(178, 24, 30)):
    tile = Image.new('RGB', (90, 90), base)
    t = ImageDraw.Draw(tile)
    hi, sh = (222, 70, 72), (120, 10, 16)
    def tread(cx, cy, flip):
        if flip:
            pts = [(cx - 26, cy - 10), (cx - 18, cy - 16), (cx + 26, cy + 10), (cx + 18, cy + 16)]
        else:
            pts = [(cx - 26, cy + 10), (cx - 18, cy + 16), (cx + 26, cy - 10), (cx + 18, cy - 16)]
        t.polygon([(x + 3, y + 3) for x, y in pts], fill=sh)
        t.polygon(pts, fill=hi)
    tread(22, 22, False); tread(67, 67, False); tread(67, 22, True); tread(22, 67, True)
    im = Image.new('RGB', (w, h))
    for x in range(0, w, 90):
        for y in range(0, h, 90):
            im.paste(tile, (x, y))
    return im


def maltese(d, cx, cy, r, fill):
    import math
    for k in range(4):
        a = math.radians(90 * k)
        def P(rr, ang):
            return (cx + rr * math.cos(a + ang), cy + rr * math.sin(a + ang))
        d.polygon([P(r * 0.18, math.radians(-30)), P(r, math.radians(-26)), P(r * 0.8, 0), P(r, math.radians(26)), P(r * 0.18, math.radians(30))], fill=fill)
    d.ellipse((cx - r * 0.3, cy - r * 0.3, cx + r * 0.3, cy + r * 0.3), fill=fill)


def base():
    im = diamond_plate(W, H)
    d = ImageDraw.Draw(im)
    m = 190
    for off, col in ((-10, (90, 8, 12)), (0, YEL), (26, SILVER), (52, YEL)):
        d.rounded_rectangle((m + off, m + off, W - m - off, H - m - off), 110 - max(off, 0), fill=col)
    d.rounded_rectangle((m + 78, m + 78, W - m - 78, H - m - 78), 80, fill=CREAM)
    # faint Maltese cross watermark
    wm = Image.new('L', (W, H), 0)
    maltese(ImageDraw.Draw(wm), W // 2, H // 2 - 40, 760, 255)
    im.paste(Image.new('RGB', (W, H), (247, 233, 205)), (0, 0), wm)
    d = ImageDraw.Draw(im)
    # rivets in the panel corners
    for x, y in ((m + 150, m + 150), (W - m - 150, m + 150), (m + 150, H - m - 150), (W - m - 150, H - m - 150)):
        d.ellipse((x - 26, y - 26, x + 26, y + 26), fill=(170, 172, 176))
        d.ellipse((x - 18, y - 22, x + 14, y + 10), fill=(225, 228, 230))
    return im, d


def wrap(d, text, f, maxw):
    lines = _wrap(d, text, f, maxw)
    w = maxw
    while len(lines) > 1 and len(lines[-1].split()) < 2 and w > maxw * 0.7:
        w -= 40
        lines = _wrap(d, text, f, w)
    return lines


def _wrap(d, text, f, maxw):
    out, cur = [], ''
    for w in text.split():
        t = (cur + ' ' + w).strip()
        if d.textlength(t.replace('~', ' '), font=f) <= maxw:
            cur = t
        else:
            out.append(cur)
            cur = w
    out.append(cur)
    return [l.replace('~', ' ') for l in out]


def story_page(paras, rule=None, size=128, portrait=None):
    """paras: list of strings; a string starting with '!' is a sound word."""
    im, d = base()
    maxw = 1640
    top0 = 430
    if portrait:
        a, pcx, pcy, pr, name = portrait
        D = 470
        src = Image.open(f'/home/claude/kb/art/{a}.png').convert('RGB').crop((pcx - pr, pcy - pr, pcx + pr, pcy + pr)).resize((D, D), Image.LANCZOS)
        mask = Image.new('L', (D, D), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, D, D), fill=255)
        px, py = (W - D) // 2, 320
        d.ellipse((px - 44, py - 44 + 14, px + D + 44, py + D + 44 + 14), fill=(214, 196, 160))
        d.ellipse((px - 44, py - 44, px + D + 44, py + D + 44), fill=RED)
        d.ellipse((px - 26, py - 26, px + D + 26, py + D + 26), fill=YEL)
        d.ellipse((px - 12, py - 12, px + D + 12, py + D + 12), fill=SILVER)
        im.paste(src, (px, py), mask)
        nf = font(64, 'Bold')
        nw = d.textlength(name, font=nf) + 110
        ry = py + D + 10
        d.rounded_rectangle(((W - nw) / 2, ry, (W + nw) / 2, ry + 104), 52, fill=RED, outline=DRED, width=6)
        d.text(((W - d.textlength(name, font=nf)) / 2, ry + 14), name, font=nf, fill=(255, 246, 225))
        top0 = ry + 140
    blocks = []
    for p in paras:
        if p.startswith('!'):
            f = ImageFont.truetype(SFX, int(size * 1.6))
            blocks.append(('sfx', [p[1:]], f, int(size * 1.6 * 1.1)))
        else:
            f = font(size, 'Medium')
            blocks.append(('txt', wrap(d, p, f, maxw), f, int(size * 1.32)))
    gap = int(size * 0.75)
    rule_h = 0
    if rule:
        rf1, rf2 = font(70, 'Bold'), font(96, 'Bold')
        rlines = wrap(d, rule[1], rf2, 1160)
        rule_h = 120 + 60 + len(rlines) * 112 + 50
    total = sum(len(b[1]) * b[3] for b in blocks) + gap * (len(blocks) - 1)
    top, bottom = top0, H - 420 - (rule_h + 70 if rule else 0)
    y = top + max(0, (bottom - top - total) // 2)
    if total > bottom - top and size > 100:
        return story_page(paras, rule, size - 8, portrait)
    for kind, lines, f, lh in blocks:
        for ln in lines:
            tw = d.textlength(ln, font=f)
            x = (W - tw) / 2
            if kind == 'sfx':
                d.text((x + 8, y + 8), ln, font=f, fill=DRED)
                d.text((x, y), ln, font=f, fill=RED, stroke_width=4, stroke_fill=DRED)
            else:
                d.text((x, y), ln, font=f, fill=INK)
            y += lh
        y += gap
    if rule:
        bw = 1640
        bx, by = (W - bw) // 2, H - 440 - rule_h
        d.rounded_rectangle((bx + 14, by + 16, bx + bw + 14, by + rule_h + 16), 60, fill=(220, 200, 165))
        d.rounded_rectangle((bx, by, bx + bw, by + rule_h), 60, fill=YEL, outline=RED, width=14)
        d.rounded_rectangle((bx + 22, by + 22, bx + bw - 22, by + rule_h - 22), 44, outline=(255, 238, 160), width=6)
        ex, ey = bx + 190, by + rule_h // 2
        maltese(d, ex, ey, 165, RED)
        d.ellipse((ex - 72, ey - 72, ex + 72, ey + 72), fill=YEL, outline=DRED, width=8)
        nf = ImageFont.truetype(SFX, 120)
        num = str(rule[0])
        d.text((ex - d.textlength(num, font=nf) / 2, ey - 66), num, font=nf, fill=RED)
        tx0 = bx + 360
        tw_ = bw - 400
        cx_ = tx0 + tw_ / 2
        t1 = 'STATION 12 RULE'
        d.text((cx_ - d.textlength(t1, font=rf1) / 2, by + 50), t1, font=rf1, fill=RED)
        yy = by + 150
        for ln in rlines:
            d.text((cx_ - d.textlength(ln, font=rf2) / 2, yy), ln, font=rf2, fill=INK)
            yy += 116
    return im


STORY = {
    1: (["Meet Captain~Brisket. He has been a firefighter for thirty-four years. He doesn't talk much.",
         "And this is Nozzle. Every day, Nozzle visits Station~12. Nozzle talks a LOT."], None),
    2: (["!BRRRING!", "When the bell rings, Station~12 rolls out.", '"Can I come?" asked Nozzle.',
         '"Not yet," said Captain~Brisket.'], None),
    3: (['"Captain! Captain! When do I get a real badge?"', 'Captain~Brisket sipped his coffee.',
         '"When you know the rules."'], None),
    4: (["Nozzle tried on the captain's boots.", '"When will they fit?"', '"About thirty years."'], None),
    5: (["!BEEP! BEEP! BEEP!", '"That sound means GET~OUT!"', '"And stay out."'],
        (1, 'When the smoke alarm beeps, get out and stay out.')),
    6: (['"Smoke goes up," said Captain~Brisket. "So get low and go!"', '"I\'m already low!" said Nozzle.'],
        (2, 'Get low and go.')),
    7: (['Nozzle got low. Very low.', 'Then he crawled under the couch!',
         '"Not under there," said Captain~Brisket. "Never hide. Get low and get OUT."'], None),
    8: (['"Every room has two ways out," said Captain~Brisket.', '"A door... and a window."'],
        (3, 'Know two ways out of every room.')),
    9: (['"Pick a meeting spot outside," said Captain~Brisket.',
         'Nozzle picked the fire hydrant. Of course.'], (4, 'Pick a meeting spot outside.')),
    10: (['"Never hide. And never go back in."', '"Not even for toys?" asked Nozzle.', '"Not even for toys."'],
         (5, 'Never hide. Never go back in.')),
    11: (['!STOP! DROP! ROLL!', 'Nozzle stopped. He dropped. He covered his face and rolled.',
          '"Perfect," said Captain~Brisket.'], (6, 'If your clothes catch fire: stop, drop and roll.')),
    12: (['"If a firefighter looks like this, don\'t hide. Come to us!"',
          '"Still smells like coffee," said Nozzle.'], (7, 'Firefighters are your friends.')),
    13: (['"Once you\'re outside, call 9-1-1," said Captain~Brisket.', 'Nozzle saluted. "Got it, Captain!"'],
         (8, 'Get outside, then call 9-1-1.')),
    14: (["Nozzle went home and taught his family every rule.", "Then the Riveras drew their escape plan. Two ways out of every room.",
          '"Our meeting spot is the big oak tree!" said Mia.'], None),
    15: (["Nozzle is Mia's dog, and Mia is his favorite person in the whole world.",
          "That night, Captain~Brisket had a plan: a fire drill, so the Riveras could practice."], None),
    16: (['!BEEP! BEEP! BEEP!', '"Get low and go!" said Mia.', '"Leave the teddy," said Nozzle. "GO!"'], None),
    17: (['Dad scooped up baby Leo.', 'Grown-ups help the little ones get out.'], None),
    18: (['Everybody got out and met at the oak tree.',
          'Then Engine~12 pulled up. Out stepped Captain~Brisket, holding a stopwatch.',
          'It was a practice drill!',
          '"Two minutes, ten seconds," he said. "...Good."'], None),
    19: (['A real badge for Nozzle!', 'Under the mustache, Captain~Brisket smiled.', 'Probably.'], None),
    20: (['After all that excitement, Nozzle took a nap at the station, wearing his new badge.',
          '"Good work, Firefighter Nozzle."'], None),
}

if __name__ == '__main__':
    import sys
    for n in [int(a) for a in sys.argv[1:]] or STORY:
        paras, rule = STORY[n]
        from portraits import P
        im = story_page(paras, rule, portrait=P[n])
        im.save(f'/home/claude/kb/out/t{n:02d}.png', dpi=(300, 300))
        im.resize((862, 875)).save(f'/home/claude/kb/out/prev_t{n:02d}.jpg', quality=85)
        print('text', n)
