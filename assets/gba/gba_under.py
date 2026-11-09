"""GBA UNDER tileset - sewers, crypt, cold storage, basements."""
import random
from gba_art import Canvas, R, dither_mix, hx
from gba_city import bricks
from gba_interior import crate

T = {}


def tile(ch):
    def deco(fn):
        T[ch] = fn
        return fn
    return deco


def concrete(seed, rp=R['concrete']):
    c = Canvas().fill(rp[2])
    rnd = random.Random(seed)
    for y in range(16):
        for x in range(16):
            r = rnd.random()
            if r < .14:
                c.set(x, y, rp[1])
            elif r < .2:
                c.set(x, y, rp[3])
    c.hline(0, 15, 15, rp[1]); c.vline(15, 0, 15, rp[1]); c.hline(0, 15, 0, rp[3])
    return c


def cwall(seed, rp=R['concrete']):
    c = Canvas().fill(rp[1])
    for y in (3, 7):
        c.hline(0, 15, y, rp[0]); c.hline(0, 15, y + 1, rp[2])
    c.noise([rp[0], rp[2]], .08, seed, 0, 0, 16, 11)
    c.hline(0, 15, 0, rp[3])
    c.rect(0, 11, 16, 4, rp[0]); c.hline(0, 15, 11, rp[2])
    c.hline(0, 15, 15, R['black'][0])
    c.set(4, 9, R['green_w'][2]); c.set(4, 10, R['green_w'][1]); c.set(11, 6, R['rust'][2])
    return c


def on_floor(fn, seed=90):
    def w():
        c = concrete(seed)
        fn(c)
        return c
    return w


@tile('.')
def _():
    return concrete(91)


@tile(',')
def _():
    c = concrete(92)
    w = R['water']
    for (x, y) in ((3, 4), (4, 4), (9, 9), (10, 9), (11, 10), (5, 12), (12, 3)):
        c.set(x, y, w[3])
    c.noise([w[2]], .08, 93)
    return c


@tile('K')
def _():
    c = Canvas().fill(R['black'][1])
    c.noise([R['concrete'][0], R['black'][0]], .4, 94)
    return c


@tile('g')
def _():
    m = R['metal']
    c = Canvas().fill(R['black'][0])
    for y in range(16):
        for x in range(16):
            if x % 4 == 0 or y % 4 == 0:
                c.set(x, y, m[2] if (x % 4 == 0 and y % 4 == 0) else m[1])
    c.hline(0, 15, 0, m[3])
    return c


@tile('=')
def _():
    m = R['rust']
    c = Canvas().fill(m[2])
    for y in range(0, 16, 3):
        c.hline(0, 15, y, m[4]); c.hline(0, 15, y + 1, m[1])
    c.vline(0, 0, 15, R['black'][1]); c.vline(15, 0, 15, R['black'][1])
    return c


@tile('f')
def _():
    f = R['frost']
    c = Canvas().fill(f[2])
    c.noise([f[1], f[3], f[4]], .3, 95)
    return c


@tile('B')
def _():
    return cwall(96)


@tile('Z')
def _():
    return cwall(96)


@tile('b')
def _():
    return bricks(97, R['stone'], R['mortar'])


@tile('P')
def _():
    c = cwall(98)
    m = R['rust']
    for y0 in (1, 7):
        c.rect(0, y0, 16, 4, m[2]); c.hline(0, 15, y0, m[4]); c.hline(0, 15, y0 + 1, m[3]); c.hline(0, 15, y0 + 3, m[0])
    c.rect(5, 0, 2, 12, m[1]); c.vline(5, 0, 11, m[3])
    return c


@tile('F')
def _():
    f = R['frost']
    c = Canvas().fill(f[2])
    for x in range(0, 16, 4):
        c.vline(x, 0, 12, f[1]); c.vline(x + 1, 0, 12, f[4])
    c.noise([f[3], f[4]], .15, 99, 0, 0, 16, 12)
    c.rect(0, 12, 16, 4, f[0]); c.hline(0, 15, 12, f[3]); c.hline(0, 15, 15, R['black'][0])
    return c


@tile('#')
def _():
    return Canvas().fill(R['black'][0])


@tile('~')
def _():
    w = R['water']
    c = Canvas().fill(w[2])
    for y in range(16):
        for x in range(16):
            v = (x * 3 + y * 5) % 17
            if v == 0:
                c.set(x, y, w[4])
            elif v < 3:
                c.set(x, y, w[3])
            elif v > 14:
                c.set(x, y, w[1])
    return c


@tile('w')
def _():
    w = R['water']
    c = Canvas().fill(w[1])
    for y in range(16):
        for x in range(16):
            if (x * 5 + y * 3) % 19 == 0:
                c.set(x, y, w[3])
            elif (x + y) % 9 == 0:
                c.set(x, y, w[0])
    return c


def valve(c):
    m, n = R['metal'], R['neon']
    for y in range(16):
        for x in range(16):
            d = ((x - 7.5) ** 2 + (y - 6.5) ** 2) ** .5
            if 4.5 < d < 6.3:
                c.set(x, y, n[2] if y < 6 else n[1])
    c.hline(2, 13, 6, n[1]); c.vline(7, 1, 12, n[1]); c.vline(8, 1, 12, n[2])
    c.rect(6, 5, 4, 3, m[3])
    c.rect(6, 12, 4, 4, m[1])


T['V'] = on_floor(valve, 100)


@tile('G')
def _():
    m = R['rust']
    c = Canvas().fill(m[1])
    for y in range(0, 16, 2):
        c.hline(0, 15, y, m[3]); c.hline(0, 15, y + 1, m[1])
    c.vline(0, 0, 15, m[0]); c.vline(15, 0, 15, m[0]); c.hline(0, 15, 15, R['black'][0])
    for x in (3, 12):
        c.vline(x, 0, 15, m[4])
    return c


@tile('S')
def _():
    m = R['metal']
    c = Canvas().fill(m[1])
    c.rect(0, 0, 16, 2, R['neon'][1])
    for x in range(0, 16, 2):
        c.set(x, 0, R['light'][3])
    for y in range(2, 16, 2):
        c.hline(0, 15, y, m[3]); c.hline(0, 15, y + 1, m[1])
    c.hline(0, 15, 15, R['black'][0])
    return c


T['X'] = on_floor(crate, 101)
T['x'] = on_floor(lambda c: crate(c, True), 102)


def machine(c):
    m = R['metal']
    c.rect(0, 0, 16, 15, m[1]); c.rect(1, 1, 14, 6, m[2]); c.hline(1, 14, 1, m[4])
    c.rect(3, 2, 4, 4, R['black'][1]); c.set(4, 3, R['neon'][3]); c.set(5, 4, R['light'][3])
    c.rect(9, 2, 5, 4, R['green_w'][1]); c.hline(10, 12, 3, hx('6fdc8c'))
    for x in range(1, 15, 2):
        c.vline(x, 8, 13, m[3]); c.vline(x + 1, 8, 13, m[0])
    c.hline(0, 15, 15, R['black'][0])


T['M'] = on_floor(machine, 103)


@tile('m')
def _():
    m = R['metal']
    c = Canvas().fill(R['black'][1])
    c.rect(0, 2, 16, 12, m[1])
    for x in range(0, 16, 3):
        c.vline(x, 3, 12, m[3]); c.vline(x + 1, 3, 12, m[2])
    c.hline(0, 15, 2, m[4]); c.hline(0, 15, 13, m[0])
    return c


def breaker(c):
    m, lt = R['metal'], R['light']
    c.rect(1, 0, 14, 11, m[1]); c.rect(2, 1, 12, 9, m[0]); c.hline(1, 14, 0, m[3])
    for x in (3, 7, 11):
        c.rect(x, 3, 2, 5, m[2]); c.rect(x, 3, 2, 2, R['neon'][3])
    c.hline(1, 14, 10, R['black'][0])
    c.rect(7, 11, 2, 4, m[1])


T['E'] = on_floor(breaker, 104)


def drum(c):
    r = R['rust']
    c.rect(3, 2, 10, 12, r[2]); c.vline(3, 2, 13, r[3]); c.vline(12, 2, 13, r[0])
    c.rect(3, 1, 10, 2, r[4]); c.hline(4, 11, 1, R['bone'][2])
    c.hline(3, 12, 6, r[1]); c.hline(3, 12, 10, r[1])
    c.hline(3, 12, 14, R['black'][0])


T['O'] = on_floor(drum, 105)


def coffin(c):
    w = R['wood']
    pts = [(5, 0), (10, 0), (13, 4), (12, 15), (3, 15), (2, 4)]
    for y in range(16):
        for x in range(16):
            l = 5 - 3 * min(y, 4) / 4 if y < 4 else 2 + (y - 4) / 11
            r = 10 + 3 * min(y, 4) / 4 if y < 4 else 13 - (y - 4) / 11
            if l <= x <= r:
                c.set(x, y, w[2] if x > (l + r) / 2 else w[3])
    c.vline(7, 3, 10, R['cream'][1]); c.hline(5, 9, 5, R['cream'][1])


T['C'] = on_floor(coffin, 106)


@tile('c')
def _():
    c = bricks(107, R['stone'], R['mortar'])
    c.rect(2, 2, 12, 9, R['black'][0])
    b = R['bone']
    c.rect(5, 5, 5, 4, b[2]); c.set(6, 6, R['black'][0]); c.set(8, 6, R['black'][0]); c.hline(6, 8, 8, b[0])
    c.hline(2, 13, 11, R['stone'][4])
    return c


def bones(c):
    b = R['bone']
    for (x0, y0, dx) in ((2, 4, 1), (8, 10, 1), (5, 13, 1)):
        for i in range(6):
            c.set(x0 + i * dx, y0 - i // 3, b[2])
        c.set(x0, y0 - 1, b[3]); c.set(x0 + 5, y0 - 2, b[3])
    c.rect(10, 3, 4, 3, b[2]); c.set(11, 4, R['black'][0]); c.set(13, 4, R['black'][0])


T['k'] = on_floor(bones, 108)


def pillar(c):
    s = R['stone']
    c.rect(3, 0, 10, 16, s[2]); c.vline(3, 0, 15, s[4]); c.vline(12, 0, 15, s[0])
    c.rect(2, 0, 12, 2, s[3]); c.rect(2, 14, 12, 2, s[1])


T['Q'] = on_floor(pillar, 109)


def door(locked=False):
    def f():
        c = cwall(110)
        w = R['rust']
        c.rect(2, 0, 12, 16, R['black'][1]); c.rect(3, 1, 10, 15, w[2])
        c.vline(3, 1, 15, w[4]); c.vline(12, 1, 15, w[0])
        for y in (3, 8, 13):
            c.hline(3, 12, y, w[1])
        c.set(11, 8, R['light'][3])
        if locked:
            m = R['metal']
            c.rect(6, 6, 4, 4, m[2]); c.hline(6, 9, 6, m[4]); c.set(7, 8, R['black'][0])
            c.vline(6, 4, 5, m[3]); c.vline(9, 4, 5, m[3])
        return c
    return f


T['D'] = door()
T['l'] = door(True)


def ladder(c):
    m = R['metal']
    c.vline(3, 0, 15, m[3]); c.vline(12, 0, 15, m[3]); c.vline(4, 0, 15, m[1]); c.vline(13, 0, 15, m[1])
    for y in range(1, 16, 4):
        c.hline(4, 11, y, m[4]); c.hline(4, 11, y + 1, m[0])


T['U'] = on_floor(ladder, 111)


def hole(c):
    for y in range(16):
        for x in range(16):
            d = ((x - 7.5) / 7) ** 2 + ((y - 7.5) / 6) ** 2
            if d < 1:
                c.set(x, y, R['black'][0] if d < .7 else R['black'][2])
    c.hline(4, 11, 2, R['concrete'][4])


T['H'] = on_floor(hole, 112)


@tile('h')
def _():
    f = R['frost']
    c = Canvas().fill(f[2])
    c.noise([f[1], f[3]], .25, 113)
    m = R['metal']
    c.rect(0, 0, 16, 2, m[2]); c.hline(0, 15, 0, m[4])
    c.vline(7, 2, 5, m[3])
    for (x, y) in ((6, 6), (5, 7), (5, 8), (6, 9), (8, 9), (9, 8)):
        c.set(x, y, m[4])
    c.rect(4, 8, 8, 7, R['crimson'][2]); c.rect(5, 9, 6, 5, R['crimson'][3]); c.set(6, 10, R['neon'][4])
    c.hline(4, 11, 14, R['crimson'][0])
    return c


def drain(c):
    c.rect(3, 4, 10, 8, R['black'][0])
    for x in range(4, 12, 2):
        c.vline(x, 4, 11, R['metal'][2])
    c.hline(3, 12, 4, R['metal'][3])


T['e'] = on_floor(drain, 114)


def bench(c):
    w = R['wood']
    c.rect(0, 2, 16, 8, w[2]); c.hline(0, 15, 2, w[4]); c.hline(0, 15, 9, w[0])
    c.rect(2, 4, 4, 3, R['metal'][3]); c.rect(9, 3, 4, 2, R['rust'][3])
    c.rect(1, 10, 2, 5, w[1]); c.rect(13, 10, 2, 5, w[1])


T['T'] = on_floor(bench, 115)


def altar_stone(c):
    s, n = R['stone'], R['neon']
    c.rect(1, 7, 14, 8, s[2]); c.hline(1, 14, 7, s[4]); c.hline(1, 14, 14, s[0])
    for y in range(0, 7):
        for x in range(5, 11):
            if abs(x - 7.5) + abs(y - 3) < 3.5:
                c.set(x, y, n[1] if (x + y) % 2 else n[2])
    c.set(7, 3, n[4]); c.set(8, 3, n[4])


T['A'] = on_floor(altar_stone, 116)


def wall_top():
    """top of a wall seen from above (used automatically where a wall has wall below it)"""
    rp = R['concrete']
    c = Canvas().fill(R['black'][1])
    c.noise([R['black'][2], rp[0]], .25, 120)
    c.hline(0, 15, 0, rp[1]); c.vline(0, 0, 15, rp[0])
    return c
