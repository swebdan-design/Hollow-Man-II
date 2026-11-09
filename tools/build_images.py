"""Title screen + cutscene illustrations, drawn procedurally (original art) and
converted to CGB tiles: each 8x8 tile picks the best of up to 6 palettes."""
import os
import sys
import random
from PIL import Image, ImageDraw
from gfx import Grid, tile_2bpp, TileBank, rgb15, hexcol

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'assets', 'sprites'))
sys.path.insert(0, os.path.join(ROOT, 'assets', 'art'))
import fx  # noqa
import chars  # noqa
import font  # noqa

C = {k: hexcol(v) for k, v in dict(
    black='0c0a0a', char='241e1e', slate='3c3a40', grey='5c5650',
    dbrown='3a2418', brown='7a5236', tan='b08c60', cream='e8dcc0',
    dcrim='4a1010', crim='8c1c1c', red='b02424',
    olive='5e6038', yellow='d8c070', amber='a08030',
    sep0='2e2218', sep1='5c4430', sep2='9c7c58', sep3='d8c098',
    navy='1c2030', blue='38445c',
).items()}

PALS_NIGHT = [
    ['black', 'char', 'slate', 'grey'],
    ['black', 'dbrown', 'brown', 'cream'],
    ['black', 'dcrim', 'crim', 'cream'],
    ['black', 'char', 'amber', 'yellow'],
    ['black', 'char', 'dcrim', 'red'],
    ['black', 'navy', 'blue', 'grey'],
]
PALS_SEPIA = [
    ['sep0', 'sep1', 'sep2', 'sep3'],
    ['black', 'sep0', 'sep1', 'sep2'],
    ['black', 'dcrim', 'crim', 'sep3'],
    ['black', 'sep1', 'sep2', 'cream'],
    ['black', 'char', 'dcrim', 'red'],
    ['black', 'dbrown', 'brown', 'cream'],
]


def pal_rgb(p):
    return [C[n] for n in p]


def convert(im, pals, max_tiles=256):
    """im: PIL RGB image (w,h multiples of 8). Returns tiles, map, attrs."""
    W, H = im.size
    px = im.load()
    prgb = [pal_rgb(p) for p in pals]
    bank = TileBank(allow_flip=True, limit=max_tiles)
    tmap, amap = [], []
    for ty in range(H // 8):
        for tx in range(W // 8):
            best = None
            for pi, pr in enumerate(prgb):
                err = 0
                idxs = []
                for y in range(8):
                    for x in range(8):
                        c = px[tx * 8 + x, ty * 8 + y]
                        bi, be = 0, 1e18
                        for ci, pc in enumerate(pr):
                            e = sum((c[k] - pc[k]) ** 2 for k in range(3))
                            if e < be:
                                bi, be = ci, e
                        err += be
                        idxs.append(bi)
                if best is None or err < best[0]:
                    best = (err, pi, idxs)
            _, pi, idxs = best
            # palette colour order is light..dark? we store index directly (0..3 = pal order)
            g = Grid(8, 8)
            for i, v in enumerate(idxs):
                g.p[i // 8][i % 8] = v
            t = tile_2bpp(g)
            ti, hf, vf = bank.add(t)
            tmap.append(ti)
            amap.append(pi | 0x08 | (0x20 if hf else 0) | (0x40 if vf else 0))
    return bank, tmap, amap


def preview(im, pals, bank, tmap, amap, path):
    W, H = im.size
    out = Image.new('RGB', (W, H))
    o = out.load()
    prgb = [pal_rgb(p) for p in pals]
    i = 0
    for ty in range(H // 8):
        for tx in range(W // 8):
            t = bank.tiles[tmap[i]]
            a = amap[i]
            for y in range(8):
                lo, hi = t[y * 2], t[y * 2 + 1]
                for x in range(8):
                    v = ((lo >> (7 - x)) & 1) | (((hi >> (7 - x)) & 1) << 1)
                    xx = 7 - x if a & 0x20 else x
                    yy = 7 - y if a & 0x40 else y
                    o[tx * 8 + xx, ty * 8 + yy] = prgb[a & 7][v]
            i += 1
    out.resize((W * 3, H * 3), Image.NEAREST).save(path)


# ---------------------------------------------------------------- drawing helpers
def draw_grid(im, rows, ox, oy, colmap, scale=1):
    px = im.load()
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            c = colmap.get(ch)
            if c is None:
                continue
            for dy in range(scale):
                for dx in range(scale):
                    X, Y = ox + x * scale + dx, oy + y * scale + dy
                    if 0 <= X < im.size[0] and 0 <= Y < im.size[1]:
                        px[X, Y] = C[c]


def doll_rows(name, d='down', step=0):
    head, body, cm, pal = chars.CHARS[name]
    rows = chars.HEADS[head][d] + chars.BODIES[body][d][step]
    out = []
    for r in rows:
        out.append(''.join(str(cm[ch]) for ch in r))
    return out


def big_text(im, text, x, y, fill='cream', shadow='crim', scale=2):
    d = 0
    for ch in text:
        rows = font.G.get(ch, font.G[' '])
        rr = [r.replace('#', 'X') for r in rows[:7]]
        draw_grid(im, rr, x + d + 1, y + 1, {'X': shadow}, scale)
        draw_grid(im, rr, x + d, y, {'X': fill}, scale)
        d += 6 * scale
    return d


BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def dither_sky(im, top, bot, y0, y1, seed=1):
    """ordered (Bayer) dither so tiles repeat"""
    px = im.load()
    for y in range(y0, y1):
        t = (y - y0) / max(1, (y1 - y0))
        lvl = int(t * 0.85 * 16 + 0.5)
        for x in range(im.size[0]):
            px[x, y] = C[bot] if BAYER[y & 3][x & 3] < lvl else C[top]


def skyline(im, y_base, seed, col='black', win='yellow', density=0.12, heights=(30, 70)):
    dr = ImageDraw.Draw(im)
    rnd = random.Random(seed)
    x = -4
    while x < im.size[0]:
        w = rnd.randint(14, 30)
        h = rnd.randint(*heights)
        top = y_base - h
        dr.rectangle([x, top, x + w, y_base], fill=C[col])
        if rnd.random() < 0.4:
            dr.rectangle([x + w // 2 - 1, top - 6, x + w // 2 + 1, top], fill=C[col])
        for wy in range(top + 4, y_base - 4, 6):
            for wx in range(x + 3, x + w - 3, 5):
                if rnd.random() < density:
                    dr.rectangle([wx, wy, wx + 1, wy + 2], fill=C[win])
        x += w + rnd.randint(0, 3)


def rain(im, n, seed, col='slate', y0=0, y1=None):
    dr = ImageDraw.Draw(im)
    rnd = random.Random(seed)
    y1 = y1 or im.size[1]
    for _ in range(n):
        x = rnd.randint(0, im.size[0])
        y = rnd.randint(y0, y1)
        dr.line([x, y, x - 2, y + 5], fill=C[col])


def shadow_figure(im, ox, oy, scale, body='char', eye='red', edge='black'):
    rows = fx.SHADOW_BIG
    cm = {'3': body, '2': edge, '1': eye}
    draw_grid(im, rows, ox, oy, cm, scale)


# ---------------------------------------------------------------- images
def img_title():
    im = Image.new('RGB', (160, 144), C['black'])
    dither_sky(im, 'black', 'char', 0, 100, 3)
    dr = ImageDraw.Draw(im)
    # horned shadow behind (scaled x2 = 64x96)
    shadow_figure(im, 48, 40, 2, body='char', eye='red', edge='black')
    # skyline
    skyline(im, 128, 7, col='black', win='amber', density=0.10, heights=(16, 44))
    dr.rectangle([0, 128, 159, 143], fill=C['black'])
    # street lamp (left) - lamp head flickers via palette in-game
    dr.rectangle([18, 74, 19, 128], fill=C['slate'])
    dr.rectangle([14, 72, 23, 74], fill=C['slate'])
    dr.rectangle([15, 75, 22, 77], fill=C['yellow'])
    for i in range(6):
        dr.line([16 - i, 78 + i * 6, 21 + i, 78 + i * 6], fill=C['amber'])
    # warm fog halo behind him (colours from his own palette) so the black balaclava reads
    px = im.load()
    for y in range(70, 136):
        for x in range(40, 120):
            d = ((x - 80) / 40.0) ** 2 + ((y - 102) / 34.0) ** 2
            if d < 1 and BAYER[y & 3][x & 3] < (1 - d) * 22:
                px[x, y] = C['dbrown'] if d > .35 or BAYER[y & 3][x & 3] > 9 else C['brown']
    # Hollow Man x3 (48x48), standing centre
    rows = doll_rows('hollow', 'down', 0)
    draw_grid(im, rows, 56, 82, {'1': 'cream', '2': 'brown', '3': 'black'}, 3)
    # tweed texture flecks
    px = im.load()
    rnd = random.Random(9)
    for y in range(82 + 27, 82 + 45):
        for x in range(56, 104):
            if px[x, y] == C['brown'] and rnd.random() < 0.18:
                px[x, y] = C['dbrown']
    # big title "HOLLOW MAN"
    w = len('HOLLOW MAN') * 12
    big_text(im, 'HOLLOW MAN', (160 - w) // 2 + 1, 12, 'cream', 'crim', 2)
    # leave rows 4-5 (y 32..47) dark for subtitle + credit text (font tiles)
    dr.rectangle([0, 32, 159, 47], fill=C['black'])
    dr.rectangle([0, 0, 159, 9], fill=C['black'])
    return im, PALS_NIGHT


def img_gloam():
    im = Image.new('RGB', (160, 96), C['black'])
    dither_sky(im, 'black', 'navy', 0, 70, 4)
    skyline(im, 80, 21, 'char', 'amber', 0.08, (30, 60))
    skyline(im, 96, 22, 'black', 'yellow', 0.06, (20, 50))
    rain(im, 160, 5, 'slate')
    return im, PALS_NIGHT


def house(dr, x, y, s, wall, roof, win, door):
    dr.rectangle([x, y, x + 60 * s // 2, y + 30 * s // 2], fill=C[wall])
    dr.polygon([(x - 4, y), (x + 15 * s, y - 16 * s // 2), (x + 30 * s + 4, y)], fill=C[roof])
    for wx in (x + 6, x + 22 * s // 2 + 6, x + 40 * s // 2 + 2):
        dr.rectangle([wx, y + 6, wx + 7, y + 14], fill=C[win])
    dr.rectangle([x + 26 * s // 2, y + 16, x + 26 * s // 2 + 8, y + 30 * s // 2], fill=C[door])


def img_house():
    im = Image.new('RGB', (160, 96), C['sep1'])
    dither_sky(im, 'sep1', 'sep2', 0, 60, 6)
    dr = ImageDraw.Draw(im)
    dr.rectangle([0, 70, 159, 95], fill=C['sep0'])
    house(dr, 40, 34, 2, 'sep0', 'black', 'black', 'black')
    # one window burning crimson
    dr.rectangle([62, 40, 69, 48], fill=C['crim'])
    dr.rectangle([64, 42, 67, 46], fill=C['red'])
    # fence
    for fx_ in range(0, 160, 6):
        dr.rectangle([fx_, 74, fx_ + 2, 84], fill=C['sep2'])
    dr.rectangle([0, 77, 159, 78], fill=C['sep2'])
    dr.rectangle([0, 82, 159, 83], fill=C['sep2'])
    # bare tree
    dr.line([140, 70, 140, 30], fill=C['black'], width=3)
    dr.line([140, 45, 128, 32], fill=C['black'], width=2)
    dr.line([140, 40, 152, 26], fill=C['black'], width=2)
    return im, PALS_SEPIA


def img_photo():
    im = Image.new('RGB', (160, 96), C['black'])
    dr = ImageDraw.Draw(im)
    dr.rectangle([16, 4, 143, 91], fill=C['sep3'])
    dr.rectangle([22, 10, 137, 76], fill=C['sep2'])
    dither_sky(im, 'sep2', 'sep1', 10, 50, 8)
    dr.rectangle([0, 0, 21, 95], fill=C['black'])
    dr.rectangle([138, 0, 159, 95], fill=C['black'])
    dr.rectangle([16, 4, 21, 91], fill=C['sep3'])
    dr.rectangle([138, 4, 143, 91], fill=C['sep3'])
    dr.rectangle([22, 4, 137, 9], fill=C['sep3'])
    dr.rectangle([22, 77, 137, 91], fill=C['sep3'])
    house(dr, 50, 30, 2, 'sep1', 'sep0', 'sep0', 'sep0')
    dr.rectangle([22, 60, 137, 76], fill=C['sep1'])
    # seven men
    for i in range(7):
        x = 30 + i * 13
        dr.ellipse([x, 50, x + 5, 56], fill=C['sep0'])
        dr.rectangle([x - 1, 56, x + 6, 72], fill=C['sep0'])
    # an eighth figure - taller, horned, at the end of the line
    x = 121
    dr.rectangle([x - 1, 50, x + 7, 74], fill=C['black'])
    dr.ellipse([x - 1, 44, x + 7, 52], fill=C['black'])
    dr.line([x, 46, x - 3, 39], fill=C['black'])
    dr.line([x + 6, 46, x + 9, 39], fill=C['black'])
    im.load()[x + 1, 47] = C['red']
    im.load()[x + 5, 47] = C['red']
    # caption scratched under photo
    return im, PALS_SEPIA


def img_shadow():
    im = Image.new('RGB', (160, 96), C['black'])
    dither_sky(im, 'black', 'dcrim', 40, 96, 11)
    shadow_figure(im, 32, -8, 3, body='char', eye='red', edge='black')
    rain(im, 60, 12, 'char')
    return im, PALS_NIGHT


def img_hollow():
    im = Image.new('RGB', (160, 96), C['black'])
    dither_sky(im, 'black', 'char', 0, 96, 13)
    rows = doll_rows('hollow', 'down', 0)
    draw_grid(im, rows, 48, -8, {'1': 'cream', '2': 'brown', '3': 'black'}, 4)
    px = im.load()
    rnd = random.Random(2)
    for y in range(28, 96):
        for x in range(40, 120):
            if px[x, y] == C['brown'] and rnd.random() < 0.22:
                px[x, y] = C['dbrown']
    return im, PALS_NIGHT


def img_ward():
    im = Image.new('RGB', (160, 96), C['black'])
    dither_sky(im, 'char', 'slate', 0, 60, 14)
    dr = ImageDraw.Draw(im)
    dr.rectangle([20, 22, 140, 80], fill=C['black'])
    dr.polygon([(16, 22), (80, 6), (144, 22)], fill=C['black'])
    rnd = random.Random(15)
    for wy in range(28, 74, 10):
        for wx in range(26, 136, 10):
            col = 'char'
            if rnd.random() < 0.08:
                col = 'yellow'
            dr.rectangle([wx, wy, wx + 4, wy + 5], fill=C[col])
    dr.rectangle([72, 60, 87, 80], fill=C['char'])
    for x in range(0, 160, 5):
        dr.rectangle([x, 76, x + 1, 95], fill=C['slate'])
    dr.rectangle([0, 78, 159, 79], fill=C['slate'])
    rain(im, 40, 16, 'char')
    return im, PALS_NIGHT


def img_dawn():
    im = Image.new('RGB', (160, 96), C['char'])
    dither_sky(im, 'slate', 'tan', 0, 64, 17)
    skyline(im, 72, 18, 'black', 'amber', 0.03, (20, 40))
    dr = ImageDraw.Draw(im)
    dr.rectangle([0, 72, 159, 95], fill=C['char'])
    dr.polygon([(60, 95), (78, 72), (82, 72), (100, 95)], fill=C['slate'])
    rows = doll_rows('hollow', 'up', 0)
    draw_grid(im, rows, 72, 66, {'1': 'cream', '2': 'brown', '3': 'black'}, 1)
    # long shadow behind him... with horns
    dr.polygon([(78, 82), (74, 95), (86, 95), (82, 82)], fill=C['black'])
    dr.line([75, 93, 72, 89], fill=C['black'])
    dr.line([85, 93, 88, 89], fill=C['black'])
    return im, PALS_NIGHT


def img_vessel():
    im = Image.new('RGB', (160, 96), C['black'])
    dither_sky(im, 'black', 'dcrim', 0, 96, 19)
    shadow_figure(im, 48, 0, 2, body='black', eye='red', edge='char')
    skyline(im, 96, 20, 'black', 'amber', 0.12, (20, 46))
    return im, PALS_NIGHT


def img_eighth():
    im = Image.new('RGB', (160, 96), C['black'])
    dither_sky(im, 'black', 'dbrown', 0, 96, 21)
    dr = ImageDraw.Draw(im)
    dr.rectangle([50, 56, 110, 80], fill=C['dbrown'])
    dr.rectangle([52, 58, 108, 60], fill=C['brown'])
    dr.rectangle([72, 36, 88, 56], fill=C['black'])
    dr.rectangle([74, 38, 86, 54], fill=C['char'])
    im.load()[78, 44] = C['red']
    im.load()[82, 44] = C['red']
    for i in range(8):
        x = 18 + i * 18
        dr.rectangle([x, 84, x + 2, 92], fill=C['cream'])
        dr.rectangle([x, 80, x + 2, 83], fill=C['yellow'])
    for i in range(8):
        x = 24 + i * 15
        dr.line([x, 12, x, 26], fill=C['crim'], width=2)
    return im, PALS_NIGHT


IMAGES = [
    ('title', img_title, 20, 18),
    ('gloam', img_gloam, 20, 12),
    ('house', img_house, 20, 12),
    ('photo', img_photo, 20, 12),
    ('shadow', img_shadow, 20, 12),
    ('hollow', img_hollow, 20, 12),
    ('ward', img_ward, 20, 12),
    ('dawn', img_dawn, 20, 12),
    ('vessel', img_vessel, 20, 12),
    ('eighth', img_eighth, 20, 12),
]


def pal_bytes(pals):
    b = b''
    for p in pals:
        for n in p:
            w = rgb15(*C[n])
            b += bytes([w & 0xFF, w >> 8])
    return b


def generate(pk, hdr, dirs_c, preview_dir):
    ids = {}
    dirs_c.append('const far_t image_dir[%d] = {' % len(IMAGES))
    for i, (name, fn, tw, th) in enumerate(IMAGES):
        im, pals = fn()
        assert im.size == (tw * 8, th * 8), name
        bank, tmap, amap = convert(im, pals)
        n = len(bank.tiles)
        blob = bytes([n & 0xFF, tw, th]) + pal_bytes(pals) + bank.data() + bytes(tmap) + bytes(amap)
        pk.blob('img_' + name, blob)
        preview(im, pals, bank, tmap, amap, os.path.join(preview_dir, 'img_%s.png' % name))
        ids[name] = i
        hdr.append('#define IMG_%s %d' % (name.upper(), i))
        dirs_c.append('  { img_%s_BANK, img_%s },' % (name, name))
    dirs_c.append('};')
    return ids
