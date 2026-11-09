"""gba_art.py - pixel-art drawing helpers for the GBA overhaul (RGB canvases, ramps,
shaded primitives) plus 4bpp tile / palette conversion with automatic palette packing."""
import random
from PIL import Image


def hx(h):
    h = h.lstrip('#')
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def ramp(*hs):
    return [hx(h) for h in hs]


# ------------------------------------------------------------------ master ramps (dark -> light)
R = dict(
    asphalt=ramp('16161b', '22222a', '2e2d35', '3b3a42', '4b4951'),
    walk=ramp('3e3a36', '524c46', '665e56', '7d7469', '978c7f'),
    brick=ramp('2e1814', '47231b', '5f3024', '7a4130', '955640'),
    mortar=ramp('3b3632', '524b45', '6a625a'),
    wood=ramp('24170f', '3a2618', '553a25', '725034', '936b47'),
    roof=ramp('18181e', '24242c', '32323c', '42424e', '55556a'),
    grass=ramp('1d2014', '2b301c', '3c4226', '4f5531', '686d3f'),
    metal=ramp('1a1e23', '2a3037', '3d454e', '566069', '7a858d'),
    light=ramp('8a5a22', 'b8823a', 'dcae5c', 'f2d488', 'fff2c4'),
    neon=ramp('3d0a10', '6e1520', 'a8222e', 'e04048', 'ff8a8a'),
    water=ramp('0b1216', '13202a', '1d3039', '2a4650', '3f6672'),
    glass=ramp('131a22', '1d2833', '2b3b4a', '41566a'),
    stone=ramp('25262b', '35363c', '48494f', '5f6066', '7b7c82'),
    concrete=ramp('26251f', '35332b', '46433a', '59554a', '6f6a5d'),
    floor=ramp('2a1c12', '3f2a1b', '573b26', '6f4d33', '8a6443'),
    tile_w=ramp('5a5650', '77726a', '958f85', 'b2aba0'),
    carpet=ramp('2c0c10', '45131a', '611c24', '7c2a30'),
    wall=ramp('2f2a25', '423a33', '564c42', '6b5f52', '84756a'),
    frost=ramp('4e5c68', '6f808c', '93a5b0', 'bccbd2', 'e2ecef'),
    rust=ramp('2a170e', '442616', '603820', '7d4c2b', '9a6438'),
    bone=ramp('5e5546', '7f7560', 'a2977e', 'c4b99d'),
    crimson=ramp('2a0507', '4a0a0e', '6f1217', '961d22'),
    black=ramp('08080a', '101014', '1a1a20'),
    cream=ramp('a69a80', 'c9bc9c', 'e6dcc0', 'f6efdc'),
    fabric=ramp('20181c', '33262c', '4a3840', '624a54'),
    green_w=ramp('1a2420', '26342e', '35473f', '4a5e54'),
)


class Canvas:
    def __init__(self, w=16, h=16, fill=(0, 0, 0)):
        self.w, self.h = w, h
        self.im = Image.new('RGB', (w, h), fill)
        self.px = self.im.load()

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.px[x, y] = c

    def get(self, x, y):
        return self.px[x, y]

    def fill(self, c):
        self.rect(0, 0, self.w, self.h, c)
        return self

    def rect(self, x, y, w, h, c):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.set(xx, yy, c)

    def hline(self, x0, x1, y, c):
        for x in range(x0, x1 + 1):
            self.set(x, y, c)

    def vline(self, x, y0, y1, c):
        for y in range(y0, y1 + 1):
            self.set(x, y, c)

    def noise(self, colors, density, seed, x=0, y=0, w=None, h=None):
        rnd = random.Random(seed)
        w = self.w if w is None else w
        h = self.h if h is None else h
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                if rnd.random() < density:
                    self.set(xx, yy, rnd.choice(colors))

    def box(self, x, y, w, h, rp, hi=3, mid=2, lo=1, edge=0):
        """bevelled box: lit top/left, shadowed bottom/right, dark edge"""
        self.rect(x, y, w, h, rp[mid])
        self.hline(x, x + w - 1, y, rp[hi])
        self.vline(x, y, y + h - 1, rp[hi])
        self.hline(x, x + w - 1, y + h - 1, rp[lo])
        self.vline(x + w - 1, y, y + h - 1, rp[lo])
        if edge is not None:
            self.hline(x, x + w - 1, y + h, rp[edge])

    def blit(self, other, ox, oy, key=None):
        for y in range(other.h):
            for x in range(other.w):
                c = other.get(x, y)
                if key is not None and c == key:
                    continue
                self.set(ox + x, oy + y, c)

    def ascii(self, rows, cmap, ox=0, oy=0):
        for y, r in enumerate(rows):
            for x, ch in enumerate(r):
                if ch in cmap and cmap[ch] is not None:
                    self.set(ox + x, oy + y, cmap[ch])
        return self

    def copy(self):
        c = Canvas(self.w, self.h)
        c.im = self.im.copy()
        c.px = c.im.load()
        return c


BAYER4 = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def dither_mix(c, a, b, t, x, y):
    """ordered dither between colours a and b with ratio t (0..1)"""
    return b if BAYER4[y & 3][x & 3] < t * 16 else a


# ------------------------------------------------------------------ 4bpp conversion
def tile4(pixels):
    """pixels: 64 palette indices (0..15) row-major -> 32 bytes"""
    out = bytearray()
    for y in range(8):
        for x in range(0, 8, 2):
            out.append(pixels[y * 8 + x] | (pixels[y * 8 + x + 1] << 4))
    return bytes(out)


def rgb15(c):
    r, g, b = c
    return (r >> 3) | ((g >> 3) << 5) | ((b >> 3) << 10)


def tiles_of(im, x0, y0):
    px = im.load()
    return [px[x0 + x, y0 + y] for y in range(8) for x in range(8)]


def _err(a, b):
    return sum((a[i] - b[i]) ** 2 for i in range(3))


def pack_palettes(colorsets, max_pals, fixed=None):
    """Greedy bin-pack tile colour sets into <= max_pals palettes of 15 colours.
    Tiles that cannot fit exactly are assigned the palette with the smallest colour
    error and later remapped to its nearest colours (remap list returned in assign)."""
    pals = [list(p) for p in (fixed or [])]
    order = sorted(range(len(colorsets)), key=lambda i: -len(colorsets[i]))
    assign = [None] * len(colorsets)
    overflow = []
    for i in order:
        cs = colorsets[i]
        best, bestadd = None, 99
        for pi, p in enumerate(pals):
            add = len(cs - set(p))
            if len(p) + add <= 15 and (add < bestadd or (add == bestadd and len(p) > len(pals[best]))):
                best, bestadd = pi, add
        if best is None:
            if len(pals) < max_pals:
                pals.append([])
                best = len(pals) - 1
            else:
                overflow.append(i)
                continue
        for c in sorted(cs):
            if c not in pals[best]:
                pals[best].append(c)
        assign[i] = best
    for i, cs in enumerate(colorsets):
        if assign[i] is None:
            continue
        for pi, p in enumerate(pals):
            if cs <= set(p):
                assign[i] = pi
                break
    for i in overflow:
        cs = colorsets[i]
        assign[i] = min(range(len(pals)), key=lambda pi: sum(min(_err(c, q) for q in pals[pi]) for c in cs))
    return pals, assign


def nearest(pal, c):
    if c in pal:
        return pal.index(c)
    return min(range(len(pal)), key=lambda k: _err(pal[k], c))


class TileStore:
    """dedup 4bpp tiles with h/v flip detection"""

    def __init__(self, limit=1024):
        self.tiles = []
        self.index = {}
        self.limit = limit

    @staticmethod
    def _flip(idx, hf, vf):
        rows = [idx[y * 8:(y + 1) * 8] for y in range(8)]
        if hf:
            rows = [r[::-1] for r in rows]
        if vf:
            rows = rows[::-1]
        return tuple(v for r in rows for v in r)

    def add(self, idx):
        idx = tuple(idx)
        for hf in (0, 1):
            for vf in (0, 1):
                k = self._flip(idx, hf, vf)
                if k in self.index:
                    return self.index[k], hf, vf
        n = len(self.tiles)
        if n >= self.limit:
            raise RuntimeError('tile store full')
        self.tiles.append(idx)
        self.index[idx] = n
        return n, 0, 0

    def data(self):
        return b''.join(tile4(list(t)) for t in self.tiles)


def convert_metatiles(images, max_pals=12, first_pal=0):
    """images: list of 16x16 PIL RGB images.  Returns (tile_bytes, palettes, mt_entries)
    where mt_entries is 4 screen-entry u16 per metatile (TL, TR, BL, BR)."""
    quads = []
    for im in images:
        for (qx, qy) in ((0, 0), (8, 0), (0, 8), (8, 8)):
            quads.append(tiles_of(im, qx, qy))
    sets = [frozenset(q) for q in quads]
    pals, assign = pack_palettes(sets, max_pals)
    store = TileStore()
    entries = []
    for q, pi in zip(quads, assign):
        pal = pals[pi]
        idx = [nearest(pal, c) + 1 for c in q]
        t, hf, vf = store.add(idx)
        entries.append(t | (hf << 10) | (vf << 11) | ((pi + first_pal) << 12))
    return store, pals, entries


def pal_bytes(pals, pad_to=None):
    out = bytearray()
    for p in pals:
        cols = [(0, 0, 0)] + list(p)
        cols += [(0, 0, 0)] * (16 - len(cols))
        for c in cols:
            v = rgb15(c)
            out += bytes([v & 0xFF, v >> 8])
    return bytes(out)


def scale_up(im, s):
    return im.resize((im.size[0] * s, im.size[1] * s), Image.NEAREST)
