"""GBA CITY tileset - Gloam exteriors, redrawn for the GBA overhaul (16x16 metatiles,
light from top-left, consistent tiling).  Same legend characters as the GBC set."""
import random
from gba_art import Canvas, R, dither_mix, hx

T = {}


def tile(ch):
    def deco(fn):
        T[ch] = fn
        return fn
    return deco


def asphalt(seed, wet=True):
    c = Canvas().fill(R['asphalt'][2])
    rnd = random.Random(seed)
    for y in range(16):
        for x in range(16):
            r = rnd.random()
            if r < 0.18:
                c.set(x, y, R['asphalt'][1])
            elif r < 0.26:
                c.set(x, y, R['asphalt'][3])
    if wet:
        for _ in range(3):
            x, y = rnd.randrange(14), rnd.randrange(15)
            c.set(x, y, R['asphalt'][4]); c.set(x + 1, y, R['metal'][3])
    return c


def pavers(seed, rp=R['walk']):
    c = Canvas().fill(rp[2])
    rnd = random.Random(seed)
    for y in range(16):
        for x in range(16):
            if rnd.random() < 0.12:
                c.set(x, y, rp[1] if rnd.random() < .6 else rp[3])
    for y in (7, 15):
        c.hline(0, 15, y, rp[0])
        c.hline(0, 15, (y + 1) % 16, rp[3])
    for x in (7, 15):
        c.vline(x, 0, 6, rp[0]); c.vline(x, 8, 14, rp[0])
    for x in (3, 11):
        c.vline(x, 8, 14, rp[1])
    return c


def bricks(seed, rp=R['brick'], mp=R['mortar']):
    c = Canvas().fill(rp[2])
    rnd = random.Random(seed)
    for row in range(4):
        y = row * 4
        c.hline(0, 15, y + 3, mp[0])
        off = 0 if row % 2 == 0 else 4
        for x in range(off, 16 + off, 8):
            xx = x % 16
            c.vline(xx, y, y + 2, mp[0])
            # each brick: highlight top-left, shade bottom
            for bx in range(1, 7):
                c.set((xx + bx) % 16, y, rp[3])
            for bx in range(1, 8):
                c.set((xx + bx) % 16, y + 2, rp[1])
            if rnd.random() < 0.35:
                tone = rp[4] if rnd.random() < .4 else rp[1]
                c.set((xx + rnd.randint(2, 6)) % 16, y + 1, tone)
    return c


def shingles(seed):
    rp = R['roof']
    c = Canvas().fill(rp[2])
    for row in range(4):
        y = row * 4
        off = 0 if row % 2 else 3
        c.hline(0, 15, y, rp[3])
        c.hline(0, 15, y + 3, rp[0])
        for x in range(off, 16, 6):
            c.vline(x, y + 1, y + 2, rp[1])
    c.noise([rp[1], rp[3]], .06, seed)
    return c


@tile('.')
def _():
    return asphalt(11)


@tile(',')
def _():
    c = asphalt(12)
    w = R['water']
    for y in range(4, 12):
        for x in range(2, 14):
            if ((x - 7.5) / 6) ** 2 + ((y - 7.5) / 4) ** 2 < 1:
                c.set(x, y, w[2] if y < 8 else w[1])
    c.hline(5, 9, 6, R['light'][2]); c.hline(6, 8, 7, R['light'][1])   # streetlight reflection
    c.set(10, 9, w[4]); c.set(4, 9, w[3])
    return c


@tile('=')
def _():
    c = asphalt(13)
    for y in list(range(1, 6)) + list(range(10, 15)):
        c.set(7, y, R['light'][1]); c.set(8, y, R['light'][2])
    return c


@tile('-')
def _():
    c = asphalt(14)
    for x in list(range(1, 6)) + list(range(10, 15)):
        c.set(x, 7, R['light'][2]); c.set(x, 8, R['light'][1])
    return c


@tile('_')
def _():
    return pavers(15)


@tile(':')
def _():
    c = pavers(16)
    c.vline(0, 0, 15, R['walk'][3]); c.vline(15, 0, 15, R['walk'][1])
    return c


@tile('K')
def _():
    c = Canvas().fill(R['asphalt'][0])
    c.noise([R['asphalt'][1], R['black'][2]], .25, 17)
    c.noise([R['water'][1]], .04, 18)
    return c


@tile('l')
def _():
    c = pavers(19)
    lt = R['light']
    for y in range(16):
        for x in range(16):
            d = ((x - 7.5) ** 2 + (y - 7.5) ** 2) ** .5
            if d < 8:
                base = c.get(x, y)
                t = max(0, 1 - d / 8)
                if t > .55:
                    c.set(x, y, dither_mix(None, lt[2], lt[3], (t - .55) * 2, x, y) if base != R['walk'][0] else lt[1])
                elif t > .2:
                    c.set(x, y, dither_mix(None, base, lt[1], (t - .2) * 2.5, x, y))
    return c


@tile('p')
def _():
    c = Canvas().fill(R['wood'][1])
    rnd = random.Random(20)
    for y in range(0, 16, 4):
        c.hline(0, 15, y + 3, R['black'][1])
    for y in range(16):
        for x in range(16):
            r = rnd.random()
            if r < .3:
                c.set(x, y, R['black'][1])
            elif r < .38:
                c.set(x, y, R['wood'][2])
            elif r < .40:
                c.set(x, y, R['neon'][2])
    return c


@tile('H')
def _():
    c = asphalt(21, wet=False)
    m = R['metal']
    for y in range(16):
        for x in range(16):
            d = ((x - 7.5) ** 2 + (y - 7.5) ** 2) ** .5
            if d < 7.5:
                c.set(x, y, m[1] if d > 6.5 else m[2])
    for y in range(4, 12, 2):
        c.hline(4, 11, y, m[0])
    c.set(5, 3, m[4]); c.set(4, 4, m[3])
    return c


@tile('^')
def _():
    c = Canvas()
    w = R['walk']
    for i in range(4):
        y = i * 4
        c.rect(0, y, 16, 4, w[2 + (i % 2)])
        c.hline(0, 15, y, w[4])
        c.hline(0, 15, y + 3, w[0])
    return c


@tile('"')
def _():
    g = R['grass']
    c = Canvas().fill(g[2])
    rnd = random.Random(22)
    for y in range(16):
        for x in range(16):
            r = rnd.random()
            if r < .25:
                c.set(x, y, g[1])
            elif r < .40:
                c.set(x, y, g[3])
    for _ in range(6):
        x, y = rnd.randrange(16), rnd.randrange(4, 16)
        c.set(x, y, g[4]); c.set(x, y - 1, g[3]); c.set(x + 1, y - 2, g[4])
    return c


@tile(';')
def _():
    g = R['grass']
    c = Canvas().fill(g[0])
    c.noise([g[1], R['black'][1]], .35, 23)
    return c


@tile('T')
def _():
    c = T['"']()
    w, k = R['wood'], R['black']
    # trunk
    c.rect(6, 6, 4, 9, w[1]); c.vline(6, 6, 14, w[2]); c.vline(9, 6, 14, k[2])
    c.hline(5, 10, 15, k[1])
    # bare branches
    for (x0, y0, dx, dy, n) in ((7, 6, -1, -1, 6), (8, 6, 1, -1, 6), (7, 4, -1, 0, 4), (8, 3, 1, 0, 4), (7, 2, 0, -1, 2)):
        x, y = x0, y0
        for i in range(n):
            c.set(x, y, w[0] if i % 2 else k[2])
            x += dx; y += dy
            if dy == 0 and i % 2:
                y -= 1
    c.set(2, 1, k[2]); c.set(13, 1, k[2]); c.set(1, 2, w[0]); c.set(14, 2, w[0])
    return c


@tile('U')
def _():
    g = R['grass']
    c = Canvas().fill(g[1])
    rnd = random.Random(24)
    for y in range(16):
        for x in range(16):
            v = rnd.random()
            sh = 3 if (x + y) % 5 == 0 else (2 if v < .5 else 1)
            if y > 12:
                sh = max(0, sh - 2)
            c.set(x, y, g[sh])
    c.hline(0, 15, 0, g[3]); c.hline(0, 15, 15, R['black'][1])
    return c


@tile('B')
def _():
    return bricks(30)


@tile('Z')
def _():
    c = bricks(30)
    return c


def window(lit, broken=False, seed=31):
    c = bricks(seed)
    w, gl, lt = R['wood'], R['glass'], R['light']
    c.rect(3, 2, 10, 11, w[0])              # frame shadow
    c.rect(4, 3, 8, 9, lt[2] if lit else gl[1])
    if lit:
        for y in range(3, 12):
            for x in range(4, 12):
                t = 1 - (y - 3) / 9
                c.set(x, y, dither_mix(None, lt[2], lt[3], t, x, y))
        c.rect(5, 9, 3, 3, lt[1])          # silhouette of a lamp/plant
    else:
        c.set(5, 4, gl[3]); c.set(6, 4, gl[2]); c.set(5, 5, gl[2])
    if broken:
        for (x, y) in ((8, 5), (9, 6), (7, 7), (10, 4), (6, 9), (9, 9)):
            c.set(x, y, R['black'][0])
    c.vline(7, 3, 11, w[1]); c.vline(8, 3, 11, w[2])
    c.hline(4, 11, 7, w[2])
    c.hline(3, 12, 2, w[3]); c.vline(3, 2, 12, w[3])
    c.hline(2, 13, 13, R['walk'][4]); c.hline(2, 13, 14, R['walk'][1])   # sill
    return c


@tile('W')
def _():
    return window(True)


@tile('w')
def _():
    return window(False, seed=33)


@tile('x')
def _():
    return window(False, True, seed=34)


@tile('R')
def _():
    return shingles(35)


@tile('r')
def _():
    c = shingles(36)
    rp, m = R['roof'], R['metal']
    c.rect(0, 9, 16, 3, m[2]); c.hline(0, 15, 9, m[4]); c.hline(0, 15, 11, m[1])   # gutter
    c.rect(0, 12, 16, 4, R['brick'][0])
    c.hline(0, 15, 12, R['black'][0])
    for x in range(0, 16, 4):
        c.vline(x, 13, 15, R['brick'][1])
    return c


@tile('D')
def _():
    c = bricks(37)
    w = R['wood']
    c.rect(2, 1, 12, 15, R['black'][1])            # door recess
    c.rect(3, 2, 10, 13, w[2])
    c.vline(3, 2, 14, w[3]); c.hline(3, 12, 2, w[3]); c.vline(12, 2, 14, w[1])
    c.rect(5, 4, 6, 4, w[1]); c.hline(5, 10, 4, w[0]); c.vline(5, 4, 7, w[0])
    c.rect(5, 9, 6, 4, w[1]); c.hline(5, 10, 9, w[0]); c.vline(5, 9, 12, w[0])
    c.set(11, 9, R['light'][3]); c.set(11, 10, R['light'][1])   # brass handle
    c.hline(1, 14, 15, R['walk'][4])                            # step
    return c


@tile('S')
def _():
    c = bricks(38)
    m, lt, w = R['metal'], R['light'], R['wood']
    c.hline(1, 14, 2, m[1]); c.set(2, 1, m[2]); c.set(13, 1, m[2])     # bracket
    c.vline(3, 3, 4, m[2]); c.vline(12, 3, 4, m[2])
    c.rect(1, 5, 14, 8, w[0]); c.rect(2, 6, 12, 6, w[2]); c.hline(2, 13, 6, w[3])
    # three gold balls - the pawnbroker's sign
    for cx in (5, 8, 11):
        c.set(cx, 8, lt[3]); c.set(cx - 1, 9, lt[2]); c.set(cx, 9, lt[2]); c.set(cx, 10, lt[1])
    return c


@tile('N')
def _():
    c = Canvas().fill(R['brick'][0])
    n = R['neon']
    c.rect(1, 2, 14, 10, R['black'][1])
    for (x, y) in [(3, 4), (3, 5), (3, 6), (3, 7), (3, 8), (4, 4), (5, 4), (4, 8), (5, 8),
                   (8, 4), (8, 5), (8, 6), (8, 7), (8, 8), (9, 6), (10, 4), (10, 5), (10, 6), (10, 7), (10, 8),
                   (12, 4), (12, 5), (12, 6), (12, 7), (12, 8), (13, 8)]:
        c.set(x, y, n[4])
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if c.get(x + dx, y + dy) == R['black'][1]:
                c.set(x + dx, y + dy, n[1])
    c.hline(0, 15, 13, R['brick'][1]); c.rect(0, 14, 16, 2, n[0])
    return c


@tile('F')
def _():
    c = Canvas().fill(R['grass'][1])
    w = R['wood']
    for x in range(0, 16, 4):
        c.rect(x, 1, 3, 14, w[2]); c.vline(x, 1, 14, w[3]); c.vline(x + 2, 1, 14, w[1])
        c.set(x + 1, 0, w[3])
    c.rect(0, 4, 16, 2, w[1]); c.hline(0, 15, 4, w[3])
    c.rect(0, 10, 16, 2, w[1]); c.hline(0, 15, 10, w[3])
    c.hline(0, 15, 15, R['black'][1])
    return c


@tile('f')
def _():
    c = T['F']()
    g = R['grass']
    for y in range(2, 14):
        for x in range(5, 11):
            c.set(x, y, g[1] if (x + y) % 3 else g[2])
    c.set(6, 6, R['wood'][1]); c.set(7, 7, R['wood'][1]); c.set(9, 11, R['wood'][1])
    return c


def chainlink(base):
    c = base
    m = R['metal']
    for y in range(16):
        for x in range(16):
            if (x + y) % 4 == 0 or (x - y) % 4 == 0:
                c.set(x, y, m[3] if (x + y) % 8 == 0 else m[2])
    c.hline(0, 15, 0, m[4]); c.hline(0, 15, 1, m[1])
    c.vline(0, 0, 15, m[1]); c.vline(15, 0, 15, m[1])
    return c


@tile('C')
def _():
    return chainlink(asphalt(40, False))


@tile('G')
def _():
    c = chainlink(asphalt(41, False))
    m = R['metal']
    c.rect(2, 6, 12, 3, m[0])
    for x in range(2, 14, 3):
        c.rect(x, 6, 2, 3, m[3]); c.set(x, 6, m[4])
    c.rect(6, 8, 4, 5, R['rust'][2]); c.rect(7, 9, 2, 2, R['black'][0]); c.hline(6, 9, 8, R['rust'][4])
    return c


@tile('g')
def _():
    c = asphalt(42)
    m = R['metal']
    c.vline(0, 0, 15, m[2]); c.vline(15, 0, 15, m[2]); c.vline(1, 0, 15, m[0])
    return c


@tile('I')
def _():
    c = Canvas().fill(R['grass'][1])
    m = R['black']
    for x in range(1, 16, 3):
        c.vline(x, 2, 14, m[2]); c.set(x, 1, R['metal'][3]); c.set(x, 0, m[2])
    c.hline(0, 15, 4, m[2]); c.hline(0, 15, 12, m[2])
    c.hline(0, 15, 15, R['black'][0])
    return c


@tile('X')
def _():
    c = asphalt(43)
    lt, k, w = R['light'], R['black'], R['wood']
    c.rect(0, 3, 16, 6, k[1])
    for x in range(16):
        for y in range(4, 8):
            c.set(x, y, lt[3] if ((x + y) // 3) % 2 else R['neon'][2])
    c.hline(0, 15, 3, lt[4]); c.hline(0, 15, 8, k[0])
    c.rect(2, 9, 2, 6, w[2]); c.rect(12, 9, 2, 6, w[2])
    c.hline(1, 4, 15, k[0]); c.hline(11, 14, 15, k[0])
    return c


@tile('L')
def _():
    c = pavers(44)
    m, lt, k = R['metal'], R['light'], R['black']
    c.rect(7, 4, 2, 11, m[1]); c.vline(7, 4, 14, m[2])
    c.rect(5, 13, 6, 3, m[0]); c.hline(5, 10, 13, m[2])
    c.rect(4, 0, 8, 3, m[1]); c.hline(4, 11, 0, m[3])
    c.hline(5, 10, 3, lt[4]); c.hline(6, 9, 4, lt[3]) if False else None
    c.set(5, 3, lt[3]); c.set(10, 3, lt[3])
    return c


@tile('b')
def _():
    c = pavers(45)
    m = R['metal']
    c.rect(3, 2, 10, 13, m[2])
    for x in range(4, 12, 2):
        c.vline(x, 4, 13, m[1])
    c.vline(3, 2, 14, m[3]); c.vline(12, 2, 14, m[0])
    c.rect(2, 1, 12, 3, m[3]); c.hline(2, 13, 1, m[4]); c.hline(2, 13, 3, m[1])
    c.hline(3, 12, 15, R['black'][1])
    return c


@tile('h')
def _():
    c = pavers(46)
    n = R['neon']
    c.rect(5, 3, 6, 11, n[2]); c.vline(5, 3, 13, n[3]); c.vline(10, 3, 13, n[1])
    c.rect(4, 2, 8, 2, n[2]); c.hline(4, 11, 2, n[4])
    c.rect(3, 7, 10, 2, n[1]); c.hline(3, 12, 7, n[3])
    c.rect(4, 13, 8, 2, n[0]); c.hline(4, 11, 15, R['black'][1])
    return c


@tile('E')
def _():
    c = pavers(47)
    m, k = R['metal'], R['black']
    c.rect(3, 0, 10, 12, m[1]); c.vline(3, 0, 11, m[3]); c.vline(12, 0, 11, m[0])
    c.rect(5, 2, 6, 4, k[1]); c.rect(6, 3, 4, 2, R['green_w'][2])
    for y in range(7, 11):
        c.hline(5, 10, y, m[2] if y % 2 else m[0])
    c.rect(11, 4, 2, 5, k[2])
    c.rect(6, 12, 4, 3, m[0]); c.hline(5, 10, 15, k[1])
    return c


@tile('c')
def _():
    c = asphalt(48)
    car(c, left=True)
    return c


@tile('v')
def _():
    c = asphalt(49)
    car(c, left=False)
    return c


def car(c, left):
    body = R['crimson'] if False else [hx('1e2228'), hx('2c323a'), hx('3c4450'), hx('566070'), hx('7a8494')]
    k, lt = R['black'], R['light']
    w = 16
    for y in range(2, 14):
        for x in range(16):
            xx = x if left else 15 - x
            if xx < 1 and y in (2, 13):
                continue
            c.set(x, y, body[2])
    for x in range(16):
        c.set(x, 2, body[4]); c.set(x, 13, k[1]); c.set(x, 12, body[1])
    # windscreen / cabin
    for y in range(4, 11):
        for x in range(16):
            xx = x if left else 15 - x
            if 7 <= xx <= 15:
                c.set(x, y, R['glass'][1] if xx > 8 else body[3])
    xs = (0,) if left else (15,)
    for x in xs:
        c.vline(x, 3, 12, body[1])
    if left:
        c.set(0, 4, lt[4]); c.set(0, 11, lt[4])      # headlights
    else:
        c.set(15, 4, R['neon'][3]); c.set(15, 11, R['neon'][3])
    for wx in ((3,) if left else (12,)):
        c.rect(wx, 13, 3, 2, k[0]); c.rect(wx, 1, 3, 2, k[0])


@tile('M')
def _():
    c = pavers(50)
    m, gl = R['metal'], R['glass']
    c.rect(0, 0, 16, 3, m[1]); c.hline(0, 15, 0, m[3])
    c.rect(1, 3, 14, 9, gl[1])
    for x in range(1, 15):
        c.set(x, 3 + (x % 3), gl[3])
    c.vline(1, 3, 13, m[2]); c.vline(14, 3, 13, m[2])
    c.rect(3, 9, 10, 2, R['wood'][2]); c.hline(3, 12, 9, R['wood'][3])
    c.hline(0, 15, 14, R['black'][1])
    return c


@tile('O')
def _():
    c = Canvas()
    rp = R['rust']
    c.fill(rp[2])
    for x in range(0, 16, 2):
        c.vline(x, 1, 13, rp[1])
    c.hline(0, 15, 0, rp[4]); c.hline(0, 15, 1, rp[3])
    c.hline(0, 15, 14, rp[0]); c.hline(0, 15, 15, R['black'][0])
    c.rect(11, 5, 3, 4, R['metal'][3])
    return c


@tile('Q')
def _():
    m = R['metal']
    c = Canvas().fill(m[2])
    for x in range(0, 16, 4):
        c.vline(x, 0, 15, m[1]); c.vline(x + 1, 0, 15, m[3])
    c.hline(0, 15, 15, m[0]); c.noise([R['rust'][2]], .05, 51)
    return c


@tile('q')
def _():
    m = R['metal']
    c = Canvas().fill(m[2])
    c.rect(1, 1, 14, 15, m[0])
    for y in range(2, 16, 2):
        c.hline(2, 13, y, m[3]); c.hline(2, 13, y + 1, m[1])
    c.rect(7, 13, 2, 2, R['light'][1])
    return c


@tile('~')
def _():
    w = R['water']
    c = Canvas().fill(w[1])
    for y in range(16):
        for x in range(16):
            if (x * 2 + y * 3) % 11 == 0:
                c.set(x, y, w[3])
            elif (x + y * 2) % 7 == 0:
                c.set(x, y, w[2])
            elif (x * 3 + y) % 13 == 0:
                c.set(x, y, w[0])
    return c


@tile('P')
def _():
    c = asphalt(52, False)
    rnd = random.Random(53)
    rp = R['brick']
    for _ in range(14):
        x, y, s = rnd.randrange(14), rnd.randrange(3, 14), rnd.randint(2, 4)
        c.rect(x, y, s, s - 1, rp[rnd.randint(1, 3)])
        c.hline(x, x + s - 1, y, rp[4])
        c.hline(x, x + s - 1, y + s - 1, R['black'][1])
    c.rect(2, 1, 3, 9, R['black'][1]); c.vline(2, 1, 9, R['wood'][1])
    return c


@tile('Y')
def _():
    c = T['"']()
    m, k = R['metal'], R['black']
    c.vline(1, 1, 15, m[2]); c.vline(14, 1, 15, m[2]); c.hline(1, 14, 1, m[3])
    for cx in (5, 10):
        c.vline(cx, 2, 9, k[2])
        c.rect(cx - 1, 10, 3, 1, R['wood'][3])
    return c


@tile('y')
def _():
    c = Canvas().fill(hx('8a7a5a'))
    c.noise([hx('6f6146'), hx('a8987a')], .3, 54)
    c.hline(0, 15, 0, R['wood'][3]); c.vline(0, 0, 15, R['wood'][3])
    c.hline(0, 15, 15, R['wood'][1]); c.vline(15, 0, 15, R['wood'][1])
    return c


@tile('A')
def _():
    s = R['stone']
    c = Canvas().fill(s[2])
    for row in range(3):
        y = row * 5 + (1 if row else 0)
        off = 0 if row % 2 == 0 else 5
        c.hline(0, 15, y, s[3])
        c.hline(0, 15, y + 4, s[0])
        for x in range(off, 16, 10):
            c.vline(x, y, y + 4, s[0]); c.vline((x + 1) % 16, y, y + 3, s[3])
    c.noise([s[1], s[4]], .06, 55)
    return c


@tile('a')
def _():
    c = T['A']()
    s = R['stone']
    c.rect(3, 1, 10, 14, s[0])
    pal = [R['neon'][2], hx('2a4a7a'), R['light'][2], hx('3d6a3a')]
    for y in range(2, 14):
        for x in range(4, 12):
            if y < 4 and (x < 5 + (4 - y) or x > 10 - (4 - y)):
                continue
            c.set(x, y, pal[((x // 2) + (y // 3)) % 4])
    c.vline(7, 2, 13, s[0]); c.hline(4, 11, 8, s[0])
    return c


@tile('+')
def _():
    c = T['"']()
    s = R['stone']
    c.rect(6, 1, 4, 13, s[2]); c.vline(6, 1, 13, s[4]); c.vline(9, 1, 13, s[1])
    c.rect(3, 4, 10, 3, s[2]); c.hline(3, 12, 4, s[4]); c.hline(3, 12, 6, s[1])
    c.rect(4, 13, 8, 2, s[1]); c.hline(3, 12, 15, R['black'][1])
    return c


@tile('#')
def _():
    return Canvas().fill(R['black'][0])
