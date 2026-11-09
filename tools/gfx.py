"""
gfx.py - Graphics helpers for HOLLOW MAN asset pipeline.

All artwork in this project is authored as small indexed-colour pixel grids
(ASCII art or procedurally drawn with the helpers below) and converted here to
Game Boy 2bpp tile data.  No external image assets are required.
"""
import random


def rgb15(r, g, b):
    """8-bit RGB -> CGB 15-bit BGR555 word."""
    return ((b >> 3) << 10) | ((g >> 3) << 5) | (r >> 3)


def hexcol(h):
    h = h.lstrip('#')
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


class Grid:
    """Indexed pixel grid (values 0..3)."""

    def __init__(self, w, h, fill=0):
        self.w, self.h = w, h
        self.p = [[fill] * w for _ in range(h)]

    @staticmethod
    def from_ascii(rows, mapping=None):
        mapping = mapping or {'.': 0, ' ': 0, '0': 0, '1': 1, '2': 2, '3': 3,
                              'a': 1, 'b': 2, 'c': 3, '#': 3, '+': 2, '-': 1}
        rows = [r for r in rows]
        g = Grid(len(rows[0]), len(rows))
        for y, r in enumerate(rows):
            if len(r) != g.w:
                raise ValueError("ragged ascii row %d: %r" % (y, r))
            for x, ch in enumerate(r):
                g.p[y][x] = mapping[ch]
        return g

    def copy(self):
        g = Grid(self.w, self.h)
        g.p = [row[:] for row in self.p]
        return g

    def set(self, x, y, v):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.p[y][x] = v

    def get(self, x, y):
        return self.p[y][x]

    def rect(self, x0, y0, w, h, v):
        for y in range(y0, y0 + h):
            for x in range(x0, x0 + w):
                self.set(x, y, v)

    def hline(self, x0, x1, y, v):
        for x in range(x0, x1 + 1):
            self.set(x, y, v)

    def vline(self, x, y0, y1, v):
        for y in range(y0, y1 + 1):
            self.set(x, y, v)

    def frame(self, x0, y0, w, h, v):
        self.hline(x0, x0 + w - 1, y0, v)
        self.hline(x0, x0 + w - 1, y0 + h - 1, v)
        self.vline(x0, y0, y0 + h - 1, v)
        self.vline(x0 + w - 1, y0, y0 + h - 1, v)

    def blit(self, other, ox, oy, transparent=None):
        for y in range(other.h):
            for x in range(other.w):
                v = other.p[y][x]
                if transparent is not None and v == transparent:
                    continue
                self.set(ox + x, oy + y, v)

    def noise(self, vals, density, seed, x0=0, y0=0, w=None, h=None):
        rnd = random.Random(seed)
        w = self.w if w is None else w
        h = self.h if h is None else h
        for y in range(y0, y0 + h):
            for x in range(x0, x0 + w):
                if rnd.random() < density:
                    self.set(x, y, rnd.choice(vals))

    def flip_h(self):
        g = Grid(self.w, self.h)
        g.p = [row[::-1] for row in self.p]
        return g

    def flip_v(self):
        g = Grid(self.w, self.h)
        g.p = [row[:] for row in self.p[::-1]]
        return g

    def sub(self, x0, y0, w, h):
        g = Grid(w, h)
        g.p = [row[x0:x0 + w] for row in self.p[y0:y0 + h]]
        return g

    def remap(self, m):
        g = self.copy()
        for y in range(g.h):
            for x in range(g.w):
                g.p[y][x] = m.get(g.p[y][x], g.p[y][x])
        return g


def tile_2bpp(g, x0=0, y0=0):
    """Encode an 8x8 region of grid g to 16 bytes of GB 2bpp."""
    out = []
    for y in range(8):
        lo = hi = 0
        for x in range(8):
            v = g.p[y0 + y][x0 + x]
            lo |= (v & 1) << (7 - x)
            hi |= ((v >> 1) & 1) << (7 - x)
        out += [lo, hi]
    return bytes(out)


def flip_tile_h(t):
    def rev(b):
        return int('{:08b}'.format(b)[::-1], 2)
    return bytes(rev(b) for b in t)


def flip_tile_v(t):
    rows = [t[i:i + 2] for i in range(0, 16, 2)]
    return b''.join(rows[::-1])


class TileBank:
    """Deduplicating tile store with flip detection (CGB attribute flips)."""

    def __init__(self, allow_flip=True, limit=256):
        self.tiles = []
        self.index = {}
        self.allow_flip = allow_flip
        self.limit = limit

    def add(self, t):
        """Returns (tile_index, hflip, vflip)."""
        if t in self.index:
            return self.index[t], 0, 0
        if self.allow_flip:
            for hf in (0, 1):
                for vf in (0, 1):
                    if not hf and not vf:
                        continue
                    u = t
                    if hf:
                        u = flip_tile_h(u)
                    if vf:
                        u = flip_tile_v(u)
                    if u in self.index:
                        return self.index[u], hf, vf
        idx = len(self.tiles)
        if idx >= self.limit:
            raise RuntimeError("tile bank overflow (%d)" % self.limit)
        self.tiles.append(t)
        self.index[t] = idx
        return idx, 0, 0

    def data(self):
        return b''.join(self.tiles)


def c_bytes(name, data, per_line=16, const=True, static=False):
    s = ("static " if static else "") + ("const " if const else "") + \
        "unsigned char %s[%d] = {\n" % (name, len(data))
    for i in range(0, len(data), per_line):
        s += "  " + ",".join("0x%02X" % b for b in data[i:i + per_line]) + ",\n"
    s += "};\n"
    return s


def save_preview(grids_with_pals, path, scale=2):
    """Write a PNG preview. grids_with_pals: list of (grid, x, y, palette[4 rgb])"""
    from PIL import Image
    W = max(x + g.w for g, x, y, p in grids_with_pals)
    H = max(y + g.h for g, x, y, p in grids_with_pals)
    im = Image.new('RGB', (W, H), (255, 0, 255))
    px = im.load()
    for g, ox, oy, pal in grids_with_pals:
        for y in range(g.h):
            for x in range(g.w):
                px[ox + x, oy + y] = pal[g.p[y][x]]
    im = im.resize((W * scale, H * scale), Image.NEAREST)
    im.save(path)
