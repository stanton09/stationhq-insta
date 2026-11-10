import re
s = open('/home/claude/shqcanvas/project/Main.dc.html').read()
css = s[s.index('<style>') + 7:s.index('</style>')]
body = s[s.index('<x-dc>'):s.index('</x-dc>')]
CDN = 'https://cdn.jsdelivr.net/gh/stanton09/stationhq-insta@7ac23d7/brand/shop/web/'
blobs = {'3de4f50805f1fd51cb47678c8aaed3cb': 'vintage', '5d7e6f5b2c31e4fdd5abcb80a0fd6d53': 'firehouse',
         '16eca46e96e7d10675c3a74786b254b8': 'engineco', '22527e3fea15c36bbb24e02b894d3690': 'irons',
         'f6bc5d79924f70f2f2648a2d5a2032f7': 'filo', 'eb498c02aae9a8c3ec7b886d544e29f9': 'answer',
         '6d2baa6bf21e89bfec14fea352f60f15': 'nozzle', '3363cb15d86a0708fa5e0c6cad211162': 'engine',
         'ff0ed6584a560714f5a62145c5cf4ae7': 'truck', 'cc5e64c7ffd8408b3790e149ecff030c': 'ladder',
         '2b03c84ee8f09564344ac6ba5e28e9b7': 'rescue', 'e4d97e6409d9b6de478c5a8979fbd705': 'squad',
         '13a7ec3cd86cf6396319dcad33616066': 'tower'}


def conv(h):
    h = h.replace('{{gold}}', '#E2A93B').replace('{{red}}', '#A3201A')
    for k, v in blobs.items():
        h = h.replace('/_blob/' + k, CDN + v + '.webp')
    return h.replace('<img ', '<img loading="lazy" ')


rules = [('alt="Engine patch"', '/products/engine-company-trucker'), ('alt="Truck patch"', '/products/truck-company-trucker'),
         ('alt="Ladder patch"', '/products/ladder-company-trucker'), ('alt="Rescue patch"', '/products/rescue-company-trucker'),
         ('alt="Squad patch"', '/products/squad-company-trucker'), ('alt="Tower patch"', '/products/tower-company-trucker'),
         ('Shop all apparel', '/collections/apparel'), ('alt="Engine Company design"', '/products/engine-company-tee'),
         ('alt="The Irons design"', '/products/the-irons-tee'), ('alt="First In Last Out design"', '/products/first-in-last-out-tee'),
         ('alt="Firehouse design"', '/products/firehouse-tee'), ('alt="Answer the Call design"', '/products/answer-the-call-tee'),
         ('Under $15', '/collections/stickers'), ('Under $35', '/collections/hats'), ('The big one', '/collections/apparel'),
         ('>Probie<', '/products/probie-mug'), ('>Firefighter<', '/products/firefighter-mug'), ('>Engineer<', '/products/engineer-mug'),
         ('>Lieutenant<', '/products/lieutenant-mug'), ('>Captain<', '/products/captain-mug'), ('>Ex-Chief<', '/products/ex-chief-mug'),
         ('>Chief<', '/products/chief-mug'),
         ('Get the StationHQ app', 'https://stationhq.app'), ('@stationhqofficial', 'https://www.instagram.com/stationhqofficial/'),
         ('Nozzle Kids Tee', '/products/nozzle-the-firehouse-dog-kids-tee'), ('Dog Collars', '/collections/dog-gear'),
         ('Toolbox Stickers', '/collections/stickers'), ('Start a station order', '/contact'), ('Shop the gear', '/collections/all')]


def links(h):
    out = []
    pos = 0
    for m in re.finditer(r'<a href="#"', h):
        end = h.index('</a>', m.start()) + 4
        chunk = h[m.start():end]
        url = next((u for k, u in rules if k in chunk), None)
        assert url, chunk[:300]
        ext = url.startswith('http')
        out.append(h[pos:m.start()] + '<a href="' + url + '"' + (' target="_blank" rel="noopener"' if ext else ''))
        pos = m.end()
    out.append(h[pos:])
    return ''.join(out)


def scope(c):
    out = []
    i = 0
    while i < len(c):
        if c[i].isspace():
            i += 1
            continue
        if c.startswith('@keyframes', i) or c.startswith('@media', i):
            j = c.index('{', i)
            depth = 0
            k = j
            while True:
                if c[k] == '{':
                    depth += 1
                elif c[k] == '}':
                    depth -= 1
                    if depth == 0:
                        break
                k += 1
            if c.startswith('@keyframes', i):
                out.append(c[i:k + 1])
            else:
                out.append(c[i:j + 1] + scope(c[j + 1:k]) + '}')
            i = k + 1
            continue
        j = c.find('{', i)
        if j < 0:
            break
        k = c.index('}', j)
        sel = c[i:j].strip()
        if sel and not sel.startswith('body'):
            sel = ','.join('.shq ' + x.strip() for x in sel.split(','))
            out.append(sel + '{' + c[j + 1:k] + '}')
        i = k + 1
    return ''.join(out)


topbar = body[body.index('<div style="background: {{red}}; color: #FFF6E6'):]
topbar = topbar[:topbar.index('</div>') + 6]
li = body.index('<div class="lights"')
lights = body[li:body.index('</div>', li) + 6]
hero_i = body.index('<section style="padding: 64px 0 72px')
rigs_end = body.index('</section>', body.index('id="rigs"')) + 10
mugs_end = body.index('</section>', body.index('From probie to chief')) + 10
trust_end = body.index('</section>', body.index('Heavyweight tees')) + 10
blocks = [('A_topbar_lights', topbar + '\n' + lights), ('B_hero_rigs', body[hero_i:rigs_end]),
          ('C_prints_gifts_mugs', body[rigs_end:mugs_end]), ('D_story_family_orders', body[mugs_end:trust_end])]
fonts = '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Alfa+Slab+One&family=Kaushan+Script&family=Oswald:wght@500;600;700&family=Inter:wght@400;500;600&display=swap">'
base = '.shq{background:#141210;color:#F3E7CF;font-family:Inter,sans-serif;font-size:16px;line-height:1.5}.shq *{box-sizing:border-box}.shq img{max-width:100%}'
scss = scope(css)
for name, blk in blocks:
    html = fonts + '<style>' + base + scss + '</style><div class="shq">' + links(conv(blk)) + '</div>'
    html = re.sub(r'\n\s*', '\n', html)
    open('/home/claude/shqlive/' + name + '.html', 'w').write(html)
    print(name, len(html))
