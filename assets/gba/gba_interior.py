"""GBA INTERIOR tileset - shops, motel, church, records, hospital."""
import random
from gba_art import Canvas, R, dither_mix, hx
from gba_city import bricks

T = {}


def tile(ch):
    def deco(fn):
        T[ch] = fn
        return fn
    return deco


def planks(seed, rp=R['floor']):
    c = Canvas().fill(rp[2])
    rnd = random.Random(seed)
    for row in range(4):
        y = row * 4
        c.hline(0, 15, y + 3, rp[0])
        c.hline(0, 15, y, rp[3])
        j = rnd.randrange(16)
        c.vline(j, y, y + 2, rp[0])
        for _ in range(4):
            c.set(rnd.randrange(16), y + rnd.randint(1, 2), rp[1] if rnd.random() < .6 else rp[4])
    return c


def wall_face(seed=1, rp=R['wall']):
    """interior wall seen from the front: wallpaper with stripes, wainscot, skirting"""
    c = Canvas().fill(rp[2])
    for x in range(0, 16, 4):
        c.vline(x, 0, 9, rp[1]); c.vline(x + 2, 0, 9, rp[3])
    c.hline(0, 15, 0, rp[4])
    c.rect(0, 10, 16, 5, R['wood'][2]); c.hline(0, 15, 10, R['wood'][4]); c.hline(0, 15, 11, R['wood'][3])
    for x in range(1, 16, 5):
        c.rect(x, 12, 3, 2, R['wood'][1])
    c.hline(0, 15, 15, R['black'][0])
    rnd = random.Random(seed)
    c.noise([rp[1]], .04, seed, 0, 0, 16, 9)
    return c


def furniture_floor(seed=60):
    return planks(seed)


@tile('.')
def _():
    return planks(60)


@tile(',')
def _():
    c = Canvas()
    a, b = R['tile_w'], R['stone']
    for y in range(16):
        for x in range(16):
            dark = ((x // 4) + (y // 4)) % 2
            c.set(x, y, b[1] if dark else a[1])
            if x % 4 == 0 or y % 4 == 0:
                c.set(x, y, b[0] if dark else a[0])
            if x % 4 == 1 and y % 4 == 1:
                c.set(x, y, b[2] if dark else a[3])
    return c


@tile('-')
def _():
    k = R['carpet']
    c = Canvas().fill(k[1])
    for y in range(16):
        for x in range(16):
            if (x + y) % 4 == 0:
                c.set(x, y, k[2])
            elif (x - y) % 8 == 0:
                c.set(x, y, k[0])
    return c


@tile('_')
def _():
    s = R['stone']
    c = Canvas().fill(s[2])
    for (x, y, w, h) in ((0, 0, 8, 8), (8, 0, 8, 8), (0, 8, 8, 8), (8, 8, 8, 8)):
        c.hline(x, x + w - 1, y, s[3]); c.vline(x, y, y + h - 1, s[3])
        c.hline(x, x + w - 1, y + h - 1, s[0]); c.vline(x + w - 1, y, y + h - 1, s[1])
    c.noise([s[1], s[3]], .07, 61)
    return c


@tile('K')
def _():
    c = planks(62, [R['black'][0], R['black'][1], R['floor'][0], R['floor'][1], R['floor'][1]])
    return c


@tile('g')
def _():
    c = planks(63)
    cr = R['crimson']
    rnd = random.Random(64)
    for y in range(3, 13):
        for x in range(2, 14):
            d = ((x - 7) / 5.5) ** 2 + ((y - 8) / 4.5) ** 2
            if d < 1 - rnd.random() * .3:
                c.set(x, y, cr[1] if d > .5 else cr[2])
    c.set(5, 6, cr[3]); c.set(13, 4, cr[1]); c.set(2, 13, cr[1])
    return c


@tile('~')
def _():
    c = planks(65)
    for (x, y) in ((3, 3), (9, 5), (12, 11), (5, 12), (10, 8), (2, 9)):
        c.set(x, y, R['glass'][3]); c.set(x + 1, y + 1, R['cream'][3])
    return c


@tile('r')
def _():
    c = planks(66)
    k, lt = R['carpet'], R['light']
    c.rect(1, 1, 14, 14, k[2])
    c.rect(2, 2, 12, 12, k[1]); c.rect(4, 4, 8, 8, k[2])
    for i in range(2, 14, 2):
        c.set(i, 2, lt[1]); c.set(i, 13, lt[1])
    return c


@tile('B')
def _():
    return wall_face(1)


@tile('Z')
def _():
    return wall_face(1)


@tile('W')
def _():
    c = wall_face(2)
    lt, w, gl = R['light'], R['wood'], R['glass']
    c.rect(3, 1, 10, 9, w[0])
    for y in range(2, 9):
        for x in range(4, 12):
            c.set(x, y, dither_mix(None, gl[2], gl[3], (y - 2) / 7, x, y))
    c.set(5, 3, R['cream'][2]); c.set(6, 3, gl[3])
    c.vline(7, 2, 8, w[2]); c.hline(4, 11, 5, w[2])
    return c


@tile('o')
def _():
    c = wall_face(3)
    w, cr = R['wood'], R['cream']
    c.rect(4, 1, 8, 8, w[1]); c.hline(4, 11, 1, w[4])
    c.rect(5, 2, 6, 6, cr[1]); c.rect(6, 4, 4, 3, R['fabric'][2]); c.set(7, 3, R['fabric'][1]); c.set(8, 3, R['fabric'][1])
    return c


@tile('M')
def _():
    c = wall_face(4)
    m, gl = R['metal'], R['glass']
    c.rect(2, 1, 12, 9, m[3])
    for y in range(2, 9):
        for x in range(3, 13):
            c.set(x, y, dither_mix(None, gl[1], gl[3], (x - y + 6) / 16, x, y))
    c.set(4, 3, R['cream'][3]); c.set(5, 3, gl[3]); c.set(4, 4, gl[3])
    return c


@tile('#')
def _():
    return Canvas().fill(R['black'][0])


def door(locked=False, open_=False):
    c = wall_face(5)
    w, k = R['wood'], R['black']
    c.rect(2, 0, 12, 16, w[0])
    if open_:
        c.rect(3, 1, 10, 15, k[1]); c.rect(3, 12, 10, 4, R['floor'][1])
        return c
    c.rect(3, 1, 10, 15, w[2]); c.vline(3, 1, 15, w[3]); c.hline(3, 12, 1, w[3]); c.vline(12, 1, 15, w[1])
    c.rect(5, 3, 6, 5, w[1]); c.rect(5, 9, 6, 5, w[1])
    c.hline(5, 10, 3, w[0]); c.hline(5, 10, 9, w[0])
    c.set(11, 9, R['light'][3])
    if locked:
        m = R['metal']
        c.rect(6, 7, 4, 4, m[2]); c.hline(6, 9, 7, m[4]); c.set(7, 9, k[0]); c.set(8, 9, k[0])
        c.vline(6, 5, 6, m[3]); c.vline(9, 5, 6, m[3]); c.hline(7, 8, 5, m[3])
    return c


@tile('D')
def _():
    return door()


@tile('d')
def _():
    c = planks(67)
    c.vline(0, 0, 15, R['wood'][1]); c.vline(15, 0, 15, R['wood'][1])
    c.vline(1, 0, 15, R['black'][1]); c.vline(14, 0, 15, R['black'][1])
    return c


@tile('L')
def _():
    return door(True)


@tile('U')
def _():
    s = R['stone']
    c = Canvas()
    for i in range(4):
        y = i * 4
        c.rect(0, y, 16, 4, s[1 + i % 2]); c.hline(0, 15, y, s[4]); c.hline(0, 15, y + 3, s[0])
    c.vline(0, 0, 15, R['wood'][1]); c.vline(15, 0, 15, R['wood'][1])
    return c


@tile('H')
def _():
    s = R['stone']
    c = Canvas().fill(R['black'][0])
    for i in range(4):
        y = i * 4
        c.rect(1 + i, y, 14 - 2 * i, 4, s[3 - min(i, 3)])
        c.hline(1 + i, 14 - i, y, s[4 - min(i, 3)])
    return c


@tile('E')
def _():
    c = wall_face(6)
    m = R['metal']
    c.rect(1, 0, 14, 16, m[1]); c.rect(2, 1, 12, 15, m[2])
    c.vline(7, 1, 15, m[0]); c.vline(8, 1, 15, m[3])
    c.rect(13, 6, 1, 3, R['neon'][3])
    return c


def floor_obj(fn, seed=70):
    def w():
        c = planks(seed)
        fn(c)
        return c
    return w


def shelf(c):
    w = R['wood']
    c.rect(1, 0, 14, 15, w[0]); c.rect(2, 1, 12, 13, w[1])
    cols = [R['neon'][1], hx('2a3a5a'), R['light'][1], R['green_w'][2], R['cream'][1], R['rust'][3]]
    for sy in (1, 5, 9):
        for x in range(2, 14):
            c.vline(x, sy, sy + 2, cols[(x * 7 + sy) % len(cols)])
        c.hline(1, 14, sy + 3, w[3])
    c.hline(1, 14, 15, R['black'][0])


T['S'] = floor_obj(shelf, 71)


def cabinet(c):
    m = R['metal']
    c.rect(2, 0, 12, 15, m[2]); c.vline(2, 0, 14, m[3]); c.vline(13, 0, 14, m[1])
    for y in (1, 6, 11):
        c.rect(3, y, 10, 4, m[3]); c.hline(3, 12, y + 3, m[0]); c.rect(6, y + 1, 4, 1, m[1])
    c.hline(2, 13, 15, R['black'][0])


T['s'] = floor_obj(cabinet, 72)


def table(c):
    w = R['wood']
    c.rect(1, 2, 14, 9, w[2]); c.hline(1, 14, 2, w[4]); c.hline(1, 14, 3, w[3]); c.hline(1, 14, 10, w[0])
    c.rect(2, 11, 2, 4, w[1]); c.rect(12, 11, 2, 4, w[1])
    c.rect(5, 5, 3, 2, R['cream'][2]); c.rect(9, 4, 2, 3, R['glass'][2])


T['T'] = floor_obj(table, 73)


def chair(c):
    w = R['wood']
    c.rect(4, 1, 8, 6, w[2]); c.hline(4, 11, 1, w[4]); c.vline(11, 1, 6, w[0])
    c.rect(4, 7, 8, 4, w[3]); c.hline(4, 11, 10, w[1])
    c.rect(4, 11, 2, 4, w[1]); c.rect(10, 11, 2, 4, w[1])


T['t'] = floor_obj(chair, 74)


def counter(c):
    w = R['wood']
    c.rect(0, 1, 16, 4, R['stone'][3]); c.hline(0, 15, 1, R['stone'][4])
    c.rect(0, 5, 16, 10, w[1])
    for x in range(0, 16, 4):
        c.vline(x, 6, 14, w[0]); c.vline(x + 1, 6, 14, w[2])
    c.hline(0, 15, 15, R['black'][0])


T['C'] = floor_obj(counter, 75)


def register(c):
    counter(c)
    m = R['metal']
    c.rect(3, 0, 10, 6, m[1]); c.rect(4, 1, 8, 2, R['green_w'][2]); c.hline(4, 11, 4, m[3])
    c.set(5, 4, R['light'][3]); c.set(8, 4, R['light'][3])


T['c'] = floor_obj(register, 76)


def bed(c):
    k, cr = R['carpet'], R['cream']
    c.rect(1, 0, 14, 15, R['wood'][1])
    c.rect(2, 1, 12, 4, cr[2]); c.hline(2, 13, 1, cr[3])
    c.rect(2, 5, 12, 9, k[2])
    for y in range(6, 14, 2):
        c.hline(2, 13, y, k[1])
    c.hline(1, 14, 15, R['black'][0])


T['b'] = floor_obj(bed, 77)


def crate(c, push=False):
    w = R['wood']
    c.rect(1, 1, 14, 13, w[2]); c.rect(1, 1, 14, 1, w[4]); c.vline(1, 1, 13, w[3])
    c.hline(1, 14, 13, w[0]); c.vline(14, 1, 13, w[1])
    if push:
        c.rect(3, 3, 10, 9, w[1]); c.rect(4, 4, 8, 7, w[3])
        c.set(7, 7, R['light'][3]); c.set(8, 7, R['light'][3])   # brass handles = movable
    else:
        for i in range(10):
            c.set(3 + i, 3 + i, w[0]); c.set(12 - i, 3 + i, w[0])
    c.hline(1, 14, 14, R['black'][0]); c.hline(2, 15, 15, R['black'][1])


T['X'] = floor_obj(crate, 78)
T['x'] = floor_obj(lambda c: crate(c, True), 79)


def pew(c):
    w = R['wood']
    c.rect(0, 1, 16, 4, w[2]); c.hline(0, 15, 1, w[4]); c.hline(0, 15, 4, w[0])
    c.rect(0, 7, 16, 6, w[1]); c.hline(0, 15, 7, w[3]); c.hline(0, 15, 12, w[0])
    c.hline(0, 15, 14, R['black'][0])


T['P'] = floor_obj(pew, 80)


def altar(c):
    s, lt = R['stone'], R['light']
    c.rect(1, 5, 14, 10, s[2]); c.hline(1, 14, 5, s[4]); c.hline(1, 14, 14, s[0])
    c.rect(3, 8, 10, 4, R['crimson'][2]); c.hline(3, 12, 8, R['crimson'][3])
    c.vline(7, 0, 4, lt[2]); c.vline(8, 0, 4, lt[1]); c.hline(5, 10, 1, lt[2])


T['A'] = lambda: (lambda c: (altar(c), c)[1])(T['_']())


def candles(c):
    lt, cr = R['light'], R['cream']
    c.rect(1, 9, 14, 2, R['metal'][1]); c.rect(6, 11, 4, 4, R['metal'][1])
    for x in (2, 5, 8, 11, 13):
        c.vline(x, 5, 8, cr[2]); c.set(x, 4, lt[4]); c.set(x, 3, lt[2])


T['a'] = lambda: (lambda c: (candles(c), c)[1])(T['_']())


def organ(c):
    w, m = R['wood'], R['metal']
    for x in range(1, 15, 2):
        h = 6 - abs(7 - x) // 2
        c.vline(x, 0, h, m[3]); c.set(x, 0, m[4])
    c.rect(0, 6, 16, 9, w[1]); c.hline(0, 15, 6, w[3])
    c.rect(1, 9, 14, 2, R['cream'][3])
    for x in range(2, 15, 2):
        c.set(x, 9, R['black'][0])


T['O'] = lambda: (lambda c: (organ(c), c)[1])(T['_']())


def rope(c):
    w = R['wood']
    for y in range(0, 12):
        c.set(7 + (y % 2), y, w[3]); c.set(8 - (y % 2), y, w[1])
    c.rect(5, 11, 6, 4, R['light'][1]); c.hline(5, 10, 11, R['light'][3])


T['R'] = lambda: (lambda c: (rope(c), c)[1])(T['_']())


def confessional(c):
    w = R['wood']
    c.rect(0, 0, 16, 15, w[1]); c.rect(1, 1, 14, 2, w[3])
    c.rect(3, 4, 10, 8, R['black'][1])
    for y in range(4, 12, 2):
        for x in range(3, 13, 2):
            c.set(x + (y // 2) % 2, y, w[2])
    c.hline(0, 15, 15, R['black'][0])


T['V'] = lambda: (lambda c: (confessional(c), c)[1])(T['_']())


def sink(c):
    m = R['frost']
    c.rect(2, 3, 12, 8, m[2]); c.hline(2, 13, 3, m[4]); c.rect(4, 5, 8, 4, m[1]); c.set(8, 6, R['black'][1])
    c.rect(7, 1, 2, 2, R['metal'][3]); c.rect(7, 11, 2, 4, m[1])


T['m'] = lambda: (lambda c: (sink(c), c)[1])(T[',']())


def gurney(c):
    m, cr = R['metal'], R['cream']
    c.rect(1, 2, 14, 9, m[3]); c.rect(2, 3, 12, 7, cr[1]); c.hline(2, 13, 3, cr[3])
    c.rect(3, 4, 4, 3, cr[2]); c.set(10, 7, R['crimson'][2]); c.set(11, 6, R['crimson'][1])
    c.vline(2, 11, 14, m[1]); c.vline(13, 11, 14, m[1])


T['G'] = lambda: (lambda c: (gurney(c), c)[1])(T[',']())


def fusebox(c):
    m = R['metal']
    c.rect(2, 0, 12, 12, m[1]); c.rect(3, 1, 10, 10, m[2]); c.hline(3, 12, 1, m[4])
    for x in (4, 7, 10):
        c.rect(x, 4, 2, 4, R['black'][1]); c.set(x, 4, R['light'][3])
    c.rect(7, 12, 2, 3, m[0])


T['F'] = lambda: (lambda c: (fusebox(c), c)[1])(wall_face(7))


def pillar(c):
    s = R['stone']
    c.rect(3, 0, 10, 16, s[2]); c.vline(3, 0, 15, s[4]); c.vline(4, 0, 15, s[3]); c.vline(12, 0, 15, s[0])
    c.rect(2, 0, 12, 2, s[3]); c.rect(2, 14, 12, 2, s[1])


T['Q'] = lambda: (lambda c: (pillar(c), c)[1])(T['_']())


def bars(c):
    m = R['metal']
    c.hline(0, 15, 0, m[3]); c.hline(0, 15, 8, m[2]); c.hline(0, 15, 15, m[1])
    for x in range(1, 16, 3):
        c.vline(x, 0, 15, m[2]); c.vline(x + 1, 0, 15, m[0])


T['I'] = lambda: (lambda c: (bars(c), c)[1])(T[',']())


def plant(c):
    g, w = R['grass'], R['rust']
    c.rect(5, 9, 6, 6, w[2]); c.hline(5, 10, 9, w[4]); c.vline(10, 9, 14, w[0])
    for (x, y) in ((7, 8), (6, 6), (5, 4), (8, 6), (9, 4), (10, 2), (7, 3), (4, 2)):
        c.set(x, y, g[1]); c.set(x, y - 1, g[3])


T['p'] = floor_obj(plant, 81)


def terminal(c):
    m = R['metal']
    c.rect(1, 6, 14, 9, R['wood'][1]); c.hline(1, 14, 6, R['wood'][3])
    c.rect(3, 0, 10, 8, m[1]); c.rect(4, 1, 8, 5, R['green_w'][1])
    for y in (2, 4):
        c.hline(5, 9, y, hx('6fdc8c'))


T['k'] = floor_obj(terminal, 82)


def desk(c):
    w = R['wood']
    c.rect(0, 2, 16, 8, w[2]); c.hline(0, 15, 2, w[4]); c.hline(0, 15, 9, w[0])
    c.rect(2, 4, 5, 3, R['cream'][2]); c.rect(10, 3, 3, 3, R['light'][2])
    c.rect(0, 10, 3, 5, w[1]); c.rect(13, 10, 3, 5, w[1])


T['n'] = floor_obj(desk, 83)


def tv(c):
    m = R['metal']
    c.rect(1, 3, 14, 10, m[1]); c.rect(2, 4, 10, 8, m[3])
    rnd = random.Random(84)
    for y in range(5, 11):
        for x in range(3, 11):
            c.set(x, y, R['cream'][rnd.randint(0, 3)] if rnd.random() < .6 else m[2])
    c.set(13, 6, R['neon'][3]); c.set(13, 8, m[3])
    c.set(5, 2, m[3]); c.set(4, 1, m[3]); c.set(10, 2, m[3]); c.set(11, 1, m[3])


T['v'] = floor_obj(tv, 85)


def wall_top():
    """top of a wall seen from above (used automatically where a wall has wall below it)"""
    rp = R['wall']
    c = Canvas().fill(R['black'][1])
    c.noise([R['black'][2], rp[0]], .25, 120)
    c.hline(0, 15, 0, rp[1]); c.vline(0, 0, 15, rp[0])
    return c
