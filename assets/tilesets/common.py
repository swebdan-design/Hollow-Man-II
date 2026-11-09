"""Shared helpers for metatile art (16x16, colour 0 = lightest, 3 = darkest)."""
import random
from gfx import Grid

# metatile flags (must match include/hm.h)
SOLID = 0x01
DARK = 0x02
WATER = 0x04
HAZARD = 0x08
SHADOWW = 0x10
PUSH = 0x20
ANIM = 0x40
SLOW = 0x80


class MT:
    def __init__(self, ch, name, role, flags, art, quad_roles=None):
        self.ch, self.name, self.role, self.flags = ch, name, role, flags
        self.art = art if isinstance(art, Grid) else Grid.from_ascii(art)
        assert self.art.w == 16 and self.art.h == 16, name
        self.quad_roles = quad_roles  # optional [tl,tr,bl,br]


def G16(fill=0):
    return Grid(16, 16, fill)


def asc(s):
    rows = [r.strip() for r in s.strip().splitlines()]
    return Grid.from_ascii(rows)


def bricks(base=1, mortar=0, dark=2, seed=1, rows=4, shade=True):
    g = G16(base)
    rnd = random.Random(seed)
    for r in range(4):
        y = r * 4
        g.hline(0, 15, y + 3, mortar)
        off = 0 if r % 2 == 0 else 4
        for x in range(off, 16, 8):
            g.vline(x, y, y + 2, mortar)
        if shade:
            for x in range(16):
                if rnd.random() < 0.18:
                    g.set(x, y + rnd.randint(0, 2), dark)
    return g


def planks(base=1, line=2, light=0, seed=2, vertical=False):
    g = G16(base)
    rnd = random.Random(seed)
    for i in range(4):
        y = i * 4 + 3
        g.hline(0, 15, y, line)
        jx = rnd.randint(0, 15)
        g.set(jx, y - 1, line)
        g.set(jx, y - 2, line)
        for x in range(16):
            if rnd.random() < 0.12:
                g.set(x, i * 4 + rnd.randint(0, 2), light)
    if vertical:
        g.p = [list(r) for r in zip(*g.p)]
    return g


def speckle(base, vals, density, seed):
    g = G16(base)
    g.noise(vals, density, seed)
    return g


def checker(a, b, size=4):
    g = G16(a)
    for y in range(16):
        for x in range(16):
            if ((x // size) + (y // size)) % 2:
                g.set(x, y, b)
    return g


def outline(g, v=3):
    g.frame(0, 0, 16, 16, v)
    return g
