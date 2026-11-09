#!/usr/bin/env python3
"""GBA asset build: new overhauled art + the shared world/story/music compilers.
Writes gba_data.c / gba_data.h / gba_dirs.h into the output directory."""
import os
import sys
import importlib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for p in (HERE, os.path.join(ROOT, 'assets', 'gba'), os.path.join(ROOT, 'assets', 'tilesets'),
          os.path.join(ROOT, 'assets', 'art'), os.path.join(ROOT, 'assets', 'maps'),
          os.path.join(ROOT, 'assets', 'sprites'), os.path.join(ROOT, 'assets', 'music')):
    sys.path.insert(0, p)

from PIL import Image, ImageDraw, ImageFont
import gba_art
from gba_art import Canvas, hx, rgb15, tile4, convert_metatiles, pal_bytes, nearest
import build_tiles          # GBC legends (metatile order / flags shared with the maps)
import build_music
import content
import font
import gba_chars
import gba_illus

TILESET_NAMES = [n for n, _ in build_tiles.TILESETS]

# per-map palette moods (same names/ids as the GBC palette sets): tint, amount, brightness
MOODS = {
    'city_night': (None, 0, 1.0), 'city_mercy': ('806848', .30, .95), 'city_strip': ('5a6070', .12, 1.0),
    'city_indust': ('6a6a40', .22, .95), 'city_neon': ('a02838', .22, .95), 'city_old': ('485870', .25, .92),
    'city_ward': ('5c7058', .30, .9), 'city_canal': ('3c5850', .25, .9), 'int_warm': (None, 0, 1.0),
    'int_motel': ('903040', .18, .95), 'int_church': ('485068', .28, .92), 'int_records': ('c0c090', .15, 1.05),
    'int_ward': ('88a088', .28, .95), 'int_dark': ('201820', .30, .8), 'und_sewer': (None, 0, 1.0),
    'und_cold': ('8098b0', .25, 1.05), 'und_crypt': ('504860', .22, 1.0), 'und_basement': ('705038', .25, .9),
    'und_ward': ('506850', .25, .9),
}


class FlatPacker:
    """Collects blobs; everything lives in flat GBA ROM (no banks)."""

    def __init__(self):
        self.items = []

    def blob(self, name, data, group=None):
        self.items.append((name, 'blob', bytes(data)))

    def ccode(self, name, code, size, group=None):
        self.items.append((name, 'code', code))


def c_array(name, data, typ='uint8_t', align=4):
    s = 'const %s %s[%d] __attribute__((aligned(%d))) = {\n' % (typ, name, len(data), align)
    for i in range(0, len(data), 32):
        s += '  ' + ','.join(str(b) for b in data[i:i + 32]) + ',\n'
    return s + '};\n'


def c_u16(name, vals):
    s = 'const uint16_t %s[%d] __attribute__((aligned(4))) = {\n' % (name, len(vals))
    for i in range(0, len(vals), 16):
        s += '  ' + ','.join('0x%04X' % v for v in vals[i:i + 16]) + ',\n'
    return s + '};\n'


# ------------------------------------------------------------------ UI: font + icons + panel
UI_PAL = ['000000', 'efe6cf', '17121a', '241a1c', 'b8a07a', '6a5440', 'd23a3a', '6a1418',
          'e0b050', '7a7480', 'c02a2a', '4a4a58', 'f6efdc', '8a1a1e', '3a3040', '9aa6b0']
DIM_PAL = ['000000', '6a6470', '17121a', '241a1c', 'b8a07a', '6a5440', 'd23a3a', '6a1418',
           'e0b050', '453f4a', 'c02a2a', '4a4a58', '8a8490', '8a1a1e', '3a3040', '9aa6b0']


FONT_TTF = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets', 'fonts', 'DejaVuSans-Bold.ttf')
_ttf = []


def glyph_tile(ch):
    """anti-aliased 8x8 glyph from DejaVu Sans Bold: 1 = ink, 9 = edge (half-tone), 2 = drop shadow"""
    from PIL import ImageFont
    if not _ttf:
        _ttf.append(ImageFont.truetype(FONT_TTF, 8))
    f = _ttf[0]
    g = Image.new('L', (8, 8), 0)
    d = ImageDraw.Draw(g)
    d.text(((8 - d.textlength(ch, font=f)) / 2, -2), ch, font=f, fill=255)
    a = list(g.tobytes())
    lv = [2 if v > 158 else 1 if v > 64 else 0 for v in a]
    px = [0] * 64
    for y in range(8):
        for x in range(8):
            v = lv[y * 8 + x]
            if v == 2:
                px[y * 8 + x] = 1
            elif v == 1:
                px[y * 8 + x] = 9
            elif x > 0 and y > 0 and lv[(y - 1) * 8 + x - 1]:
                px[y * 8 + x] = 2      # drop shadow so text reads on any background
    return tile4(px)


UI_ICONS = {}


def icon(name, rows, cmap):
    px = []
    for r in rows:
        for ch in r:
            px.append(cmap.get(ch, 0))
    UI_ICONS[name] = tile4(px)


def build_ui():
    m = {'#': 2, 'r': 6, 'd': 7, 'w': 1, 'g': 8, 'k': 2, 'e': 10, 'x': 9, 'b': 4, 'o': 5}
    icon('heart', ['........', '.rr.rr..', 'rwrrrrd.', 'rrrrrrd.', '.rrrrd..', '..rrd...', '...d....', '........'], m)
    icon('heart_h', ['........', '.rr.xx..', 'rwrx..x.', 'rrrx..x.', '.rrx.x..', '..rxx...', '...x....', '........'], m)
    icon('heart_e', ['........', '.xx.xx..', 'x..x..x.', 'x.....x.', '.x...x..', '..x.x...', '...x....', '........'], m)
    icon('eye0', ['........', '........', '........', '.kkkkkk.', 'k.wwww.k', '.kkkkkk.', '........', '........'], m)
    icon('eye1', ['........', '........', '..kkkk..', '.kwwwwk.', 'kw.kk.wk', '.kkkkkk.', '........', '........'], m)
    icon('eye2', ['........', '..kkkk..', '.kwwwwk.', 'kwwkkwwk', 'kwwkkwwk', '.kwwwwk.', '..kkkk..', '........'], m)
    icon('eye3', ['k......k', '.kkkkkk.', 'kweeeewk', 'kwekkewk', 'kwekkewk', 'kweeeewk', '.kkkkkk.', '........'], m)
    icon('badge', ['...g....', '..ggg...', 'ggggggg.', '.ggwgg..', '..g.g...', '.g...g..', 'g.....g.', '........'], m)
    icon('badge_off', ['...x....', '..x.x...', 'xxx.xxx.', '.x...x..', '..x.x...', '.x...x..', 'x.....x.', '........'], m)
    icon('cursor', ['........', '.w......', '.ww.....', '.www....', '.wwww...', '.www....', '.ww.....', '.w......'], m)
    icon('more', ['........', '........', '.wwwww..', '..www...', '...w....', '........', '........', '........'], m)
    icon('lock', ['........', '..xxx...', '.x...x..', '.x...x..', 'xxxxxxx.', 'xxx.xxx.', 'xxxxxxx.', '........'], m)
    icon('note', ['...www..', '...w.ww.', '...w..w.', '...w....', '.www....', 'wwww....', '.ww.....', '........'], m)
    icon('marker', ['..rrr...', '.rrwrr..', 'rrwwwrr.', '.rrwrr..', '..rrr...', '...r....', '........', '........'], m)
    icon('check_on', ['........', '.wwwwww.', '.w....w.', '.w.gg.w.', '.w.gg.w.', '.w....w.', '.wwwwww.', '........'], m)
    icon('check_off', ['........', '.xxxxxx.', '.x....x.', '.x....x.', '.x....x.', '.x....x.', '.xxxxxx.', '........'], m)
    icon('bar_e', ['........', 'xxxxxxxx', '........', '........', '........', '........', 'xxxxxxxx', '........'], m)
    icon('bar_h', ['........', 'xxxxxxxx', 'rrrr....', 'rrrr....', 'dddd....', 'dddd....', 'xxxxxxxx', '........'], m)
    icon('bar_f', ['........', 'xxxxxxxx', 'rrrrrrrr', 'rrrrrrrr', 'dddddddd', 'dddddddd', 'xxxxxxxx', '........'], m)
    icon('solid1', ['bbbbbbbb'] * 8, m)
    icon('solid2', ['rrrrrrrr'] * 8, m)
    icon('solid3', ['kkkkkkkk'] * 8, m)
    icon('bullet', ['........', '..gg....', '.gwwg...', '.gwwg...', '.gggg...', '.gggg...', '.oooo...', '........'], m)
    icon('blade', ['.......x', '......xx', '.....xx.', '....xx..', 'o..xx...', '.ooo....', '.oo.....', 'o..o....'], m)
    # panel (box) tiles: fill 3, light border 4, dark border 5
    P = {'f': 3, 'L': 4, 'D': 5, '.': 0}
    icon('box_tl', ['........', '.LLLLLLL', '.LDDDDDD', '.LDfffff', '.LDfffff', '.LDfffff', '.LDfffff', '.LDfffff'], P)
    icon('box_t', ['........', 'LLLLLLLL', 'DDDDDDDD', 'ffffffff', 'ffffffff', 'ffffffff', 'ffffffff', 'ffffffff'], P)
    icon('box_tr', ['........', 'LLLLLLL.', 'DDDDDDL.', 'fffffDL.', 'fffffDL.', 'fffffDL.', 'fffffDL.', 'fffffDL.'], P)
    icon('box_l', ['.LDfffff'] * 8, P)
    icon('box_r', ['fffffDL.'] * 8, P)
    icon('box_bl', ['.LDfffff', '.LDfffff', '.LDfffff', '.LDfffff', '.LDfffff', '.LDDDDDD', '.LLLLLLL', '........'], P)
    icon('box_b', ['ffffffff', 'ffffffff', 'ffffffff', 'ffffffff', 'ffffffff', 'DDDDDDDD', 'LLLLLLLL', '........'], P)
    icon('box_br', ['fffffDL.', 'fffffDL.', 'fffffDL.', 'fffffDL.', 'fffffDL.', 'DDDDDDL.', 'LLLLLLL.', '........'], P)
    icon('box_f', ['ffffffff'] * 8, P)
    icon('rule', ['ffffffff', 'ffffffff', 'ffffffff', 'DDDDDDDD', 'LLLLLLLL', 'ffffffff', 'ffffffff', 'ffffffff'], P)
    data = b''.join(glyph_tile(chr(c)) for c in range(32, 128))
    names = list(UI_ICONS)
    data += b''.join(UI_ICONS[n] for n in names)
    return data, {n: 96 + i for i, n in enumerate(names)}


# ------------------------------------------------------------------ sprites
def sprite_tiles(im, w, h):
    """RGB image with magenta key -> palette list + 4bpp tiles in 1D order"""
    return im


def obj_convert(images, w, h, pal=None):
    """convert list of RGB images (w x h, magenta transparent) to 4bpp 1D tiles with one palette"""
    key = (255, 0, 255)
    cols = []
    for im in images:
        for c in im.getdata():
            if c != key and c not in cols:
                cols.append(c)
    if pal is None:
        pal = cols
    if len(pal) > 15:
        # reduce by merging nearest colours
        pal = gba_art_reduce(cols, 15)
    data = b''
    for im in images:
        px = im.load()
        for ty in range(h // 8):
            for tx in range(w // 8):
                idx = []
                for y in range(8):
                    for x in range(8):
                        c = px[tx * 8 + x, ty * 8 + y]
                        idx.append(0 if c == key else nearest(pal, c) + 1)
                data += tile4(idx)
    return data, pal


def gba_art_reduce(cols, n):
    from PIL import Image as I
    im = I.new('RGB', (len(cols), 1))
    im.putdata(cols)
    q = im.quantize(colors=n, method=I.Quantize.MEDIANCUT).convert('RGB')
    out = []
    for c in q.getdata():
        if c not in out:
            out.append(c)
    return out[:n]


def obj_pal_bytes(pal):
    cols = [(0, 0, 0)] + list(pal)
    cols += [(0, 0, 0)] * (16 - len(cols))
    out = bytearray()
    for c in cols:
        v = rgb15(c)
        out += bytes([v & 0xFF, v >> 8])
    return bytes(out)


def fx_images():
    """effect / item sprites, 16x16 (some 8x16 inside a 16x16 frame) - overhauled colours"""
    import fx as gfx   # GBC shapes (assets/sprites) recoloured with richer ramps
    shapes = {}
    cm = {
        'pipe_v': {'1': 'e6dcc0', '2': '6a6a74', '3': '2a2a30'}, 'pipe_h': {'1': 'e6dcc0', '2': '6a6a74', '3': '2a2a30'},
        'axe_v': {'1': 'd8dce0', '2': '8a1a1e', '3': '2a1810'}, 'axe_h': {'1': 'd8dce0', '2': '8a1a1e', '3': '2a1810'},
        'spark': {'1': 'fff2c4', '2': 'f2a040', '3': 'a03018'}, 'shadow_blob': {'3': '0c0a10'},
        'shadow_horned': {'1': 'ff3030', '2': '1a141e', '3': '0a080c'},
        'saw': {'1': 'd8dce0', '2': '8a9098', '3': '2a2e34'}, 'rat_side': {'1': 'e0a0a0', '2': '5a4a3e', '3': '1e1612'},
        'rat_down': {'1': 'e0a0a0', '2': '5a4a3e', '3': '1e1612'}, 'bell': {'1': 'fff2c4', '2': 'c09040', '3': '4a3018'},
    }
    imgs = []
    for n in ['pipe_v', 'pipe_h', 'axe_v', 'axe_h', 'spark', 'shadow_blob', 'shadow_horned', 'saw', 'rat_side',
              'rat_down', 'bell']:
        rows = gfx.FX16[n]
        im = Image.new('RGB', (16, 16), (255, 0, 255))
        for y, r in enumerate(rows):
            for x, ch in enumerate(r):
                if ch != '.' and ch in cm[n]:
                    im.putpixel((x, y), hx(cm[n][ch]))
        imgs.append((n, im))
    cm8 = {'bullet': {'1': 'fff2c4', '3': 'a07020'}, 'alert': {'2': 'ff4040', '3': '1a0a0a'},
           'question': {'1': 'fff2c4', '3': '1a1a2a'}, 'heart': {'2': 'd23a3a', '3': '4a0a0e'},
           'ammo': {'1': 'fff2c4', '2': 'c09040', '3': '3a2a18'}, 'bottle': {'1': 'c8e0c0', '2': '3a6a40', '3': '102018'},
           'stars': {'1': 'fff2c4', '2': 'f2c040'}, 'ember': {'1': 'fff2c4', '2': 'ff6020'},
           'smoke': {'1': '9a96a0', '2': '6a6670'}}
    for n in ['bullet', 'alert', 'question', 'heart', 'ammo', 'bottle', 'stars', 'ember', 'smoke']:
        rows = gfx.FX8[n]
        im = Image.new('RGB', (16, 16), (255, 0, 255))
        for y, r in enumerate(rows):
            for x, ch in enumerate(r):
                if ch != '.' and ch in cm8[n]:
                    im.putpixel((x + 4, y), hx(cm8[n][ch]))
        imgs.append((n, im))
    return imgs


def shadow_figure_64():
    beast = gba_illus.shadow_beast(64, 64, '0d0a10', 'ff3030', '2a1a2e', seed=3)
    im = Image.new('RGB', (64, 64), (255, 0, 255))
    im.paste(beast.convert('RGB'), (0, 0), beast)
    return im


# ------------------------------------------------------------------ illustrations
def bmp_text(im, x, y, text, col, scale=1, shadow=None):
    from PIL import ImageDraw
    d = ImageDraw.Draw(im)
    cx = x
    for ch in text:
        rows = font.G.get(ch, font.G[' '])
        for yy, r in enumerate(rows):
            for xx, p in enumerate(r):
                if p == '#':
                    if shadow:
                        d.rectangle([cx + xx * scale + 1, y + yy * scale + 1, cx + xx * scale + scale,
                                     y + yy * scale + scale], fill=hx(shadow))
                    d.rectangle([cx + xx * scale, y + yy * scale, cx + xx * scale + scale - 1,
                                 y + yy * scale + scale - 1], fill=hx(col))
        cx += 6 * scale
    return cx - x


def ttf_text(im, cx, y, text, path, size, col, shadow, glow=None, spacing=0):
    """anti-aliased centred text with a soft shadow (and optional glow) drawn into an RGB image"""
    f = ImageFont.truetype(os.path.join(os.path.dirname(FONT_TTF), path), size)
    d0 = ImageDraw.Draw(im)
    w = sum(d0.textlength(ch, font=f) + spacing for ch in text) - spacing
    mask = Image.new('L', im.size, 0)
    dm = ImageDraw.Draw(mask)
    x = cx - w / 2
    for ch in text:
        dm.text((x, y), ch, font=f, fill=255)
        x += dm.textlength(ch, font=f) + spacing
    from PIL import ImageFilter, ImageChops
    if glow:
        g = mask.filter(ImageFilter.GaussianBlur(5)).point(lambda v: min(255, v * 2))
        im.paste(Image.new('RGB', im.size, glow), (0, 0), g)
    sh = ImageChops.offset(mask, 1, 2).filter(ImageFilter.GaussianBlur(1))
    im.paste(Image.new('RGB', im.size, shadow), (0, 0), sh)
    im.paste(Image.new('RGB', im.size, col), (0, 0), mask)


def title_with_text(im):
    ttf_text(im, 120, 2, 'HOLLOW MAN', 'DejaVuSerif-Bold.ttf', 26, (239, 230, 207), (40, 6, 8),
             glow=(110, 20, 24), spacing=1)
    ttf_text(im, 120, 33, 'THE SECOND SHADOW', 'DejaVuSans-Bold.ttf', 9, (216, 200, 168), (20, 14, 16), spacing=2)
    ttf_text(im, 120, 45, 'by Synth Centric', 'DejaVuSans-Bold.ttf', 9, (224, 176, 80), (20, 14, 16))
    return im


def convert_illus(im):
    """224-colour quantised image -> 8bpp tiles (30x20, row-major tile order) + 256-entry palette
    (224..239 = dimmed UI palette, 240..255 = UI palette so text/boxes work on top)"""
    q0 = im.quantize(colors=224, method=Image.Quantize.MEDIANCUT, kmeans=2)
    q = im.quantize(palette=q0, dither=Image.Dither.FLOYDSTEINBERG)     # dithered: no gradient banding
    pal = q.getpalette()[:224 * 3]
    pal += [0] * (224 * 3 - len(pal))
    cols = [(pal[i * 3], pal[i * 3 + 1], pal[i * 3 + 2]) for i in range(224)]
    src = q.load()
    pixels = bytearray()
    for ty in range(20):
        for tx in range(30):
            for y in range(8):
                for x in range(8):
                    v = src[tx * 8 + x, ty * 8 + y]
                    pixels.append(v)
    pb = [rgb15(c) for c in cols]
    pb[0] = rgb15(cols[0])
    for h in DIM_PAL + UI_PAL:
        pb.append(rgb15(hx(h)))
    return bytes(pixels), pb


# ------------------------------------------------------------------ pre-rendered maps
def _settiles(ops, out):
    for o in ops:
        if o.kind == 'SETTILE':
            out.append(o.args)
        elif o.kind == 'IF':
            _settiles(o.args[1], out); _settiles(o.args[2], out)
        elif o.kind == 'CHOICE':
            _settiles(o.args[2], out); _settiles(o.args[3], out)


def bake_maps(code, hdr, preview_dir):
    import numpy as np
    import render_env as RE
    from gba_art import TileStore
    lines = []
    for mi, m in enumerate(content.MAPS):
        mod = importlib.import_module('gba_' + m.ts)
        leg = build_tiles.legend(m.ts)
        top = mod.wall_top().im if hasattr(mod, 'wall_top') and m.ts != 'city' else None
        cache = {}

        def img_of(ch):
            if ch not in cache:
                cache[ch] = mod.T[ch]().im
            return cache[ch]

        def render(rows):
            imgs = {ch: img_of(ch) for ch in set(''.join(rows))}
            alb, hgt, emis, lights = RE.compose(rows, m.ts, imgs, m.w, m.h, top)
            wet = np.zeros(hgt.shape)
            for ty, r in enumerate(rows):
                for tx, ch in enumerate(r):
                    if ch in RE.WET:
                        wet[ty * 16:ty * 16 + 16, tx * 16:tx * 16 + 16] = 1
            return RE.light_image(alb, hgt, emis, lights, m.pal, m.flags & 1, m.flags & 4, wet)

        base = render(m.rows)
        dyn = {}
        for (x, y, ch, cond) in m.patches:
            dyn.setdefault((x, y), []).append(ch)
        sts = []
        for (nm, ops, mp) in content.SCRIPTS:
            if mp == m.name:
                _settiles(ops, sts)
        for (x, y, ch) in sts:
            dyn.setdefault((x, y), []).append(ch)
        alt_rows = [list(r) for r in m.rows]
        for (x, y), chs in dyn.items():
            alt_rows[y][x] = chs[-1]
        alt = render([''.join(r) for r in alt_rows]) if dyn else base
        # generic (position-independent) pieces: pushable crates and the floor they leave behind
        generic = set()
        for (x, y), chs in dyn.items():
            generic.update(chs[:-1])
        if 'x' in ''.join(m.rows):
            generic.update(['x', '.'])
        pieces = []
        for (x, y), chs in sorted(dyn.items()):
            pieces.append(((x, y), chs[-1], alt[y * 16:y * 16 + 16, x * 16:x * 16 + 16]))
        floor = '.' if '.' in leg else list(leg)[0]
        for ch in sorted(generic):
            g = render_small(RE, m, mod, top, ch, floor, img_of)
            pieces.append(((0xFF, 0xFF), ch, g))
        W, H = m.w * 16, m.h * 16
        extra_rows = (len(pieces) + (m.w - 1)) // m.w
        pool = np.zeros((H + extra_rows * 16, W, 3))
        pool[:H] = base
        for k, (pos, ch, im) in enumerate(pieces):
            px, py = (k % m.w) * 16, H + (k // m.w) * 16
            pool[py:py + 16, px:px + 16] = im
        store, pals, entries, P, idx, best = RE.quantize_tiles(pool)
        idx, best = RE.merge_tiles(idx, best, P, 1000)
        store = TileStore(limit=4096)
        ent = []
        for ci in range(len(best)):
            t, hf, vf = store.add(tuple(int(v) for v in idx[ci]))
            ent.append((t + 1) | (hf << 10) | (vf << 11) | (int(best[ci]) << 12))
        assert len(store.tiles) <= 1023, (m.name, len(store.tiles))
        cw = m.w * 2
        base_ent = ent[:(H // 8) * cw]
        dyn_vals = []
        for k, (pos, ch, im) in enumerate(pieces):
            cx, cy = (k % m.w) * 2, (H // 8) + (k // m.w) * 2
            e4 = [ent[(cy + dy) * cw + cx + dx] for dy in (0, 1) for dx in (0, 1)]
            dyn_vals += [pos[0] | (pos[1] << 8), leg[ch][0]] + e4
        code.append(c_array('mapgfx%d_tiles' % mi, store.data()))
        palb = []
        for pal in pals:
            palb += [0] + [rgb15(tuple(c)) for c in pal]
        palb += [0] * (13 * 16 - len(palb))
        code.append(c_u16('mapgfx%d_pals' % mi, palb))
        code.append(c_u16('mapgfx%d_map' % mi, base_ent))
        code.append(c_u16('mapgfx%d_dyn' % mi, dyn_vals or [0]))
        lines.append('  { mapgfx%d_tiles, %d, mapgfx%d_pals, mapgfx%d_map, mapgfx%d_dyn, %d },' % (
            mi, len(store.tiles), mi, mi, mi, len(pieces)))
        Image.fromarray(RE.reconstruct(P, idx, best, W, H + extra_rows * 16)[:H]).save(
            os.path.join(preview_dir, 'map_%02d_%s.png' % (mi, m.name)))
        print('baked %-14s %4d tiles  %2d dynamic pieces' % (m.name, len(store.tiles), len(pieces)))
    code.append('const mapgfx_t mapgfx[%d] = {\n%s\n};' % (len(lines), '\n'.join(lines)))


def render_small(RE, m, mod, top, ch, floor, img_of):
    import numpy as np
    rows = [floor * 3, floor + ch + floor, floor * 3]
    imgs = {c: img_of(c) for c in set(''.join(rows))}
    alb, hgt, emis, lights = RE.compose(rows, m.ts, imgs, 3, 3, None)
    img = RE.light_image(alb, hgt, emis, lights, m.pal, m.flags & 1, False, np.zeros(hgt.shape))
    return img[16:32, 16:32]


# ------------------------------------------------------------------ main
def main(outdir, preview_dir):
    os.makedirs(outdir, exist_ok=True)
    os.makedirs(preview_dir, exist_ok=True)
    pk = FlatPacker()
    hdr = []
    dirs_c = []
    code = ['#include <stdint.h>', '#include "hm.h"', '#include "gba_dirs.h"', '']

    # UI
    ui, ui_index = build_ui()
    code.append(c_array('ui_tiles', ui))
    code.append(c_u16('ui_pal', [rgb15(hx(h)) for h in UI_PAL] + [rgb15(hx(h)) for h in DIM_PAL]))
    for n, i in ui_index.items():
        hdr.append('#define UI_%s %d' % (n.upper(), i))
    hdr.append('#define UI_TILE_COUNT %d' % (96 + len(ui_index)))

    # tilesets (metatile order = GBC legend order so map data is shared)
    ts_lines = []
    for ti, (name, mts) in enumerate(build_tiles.TILESETS):
        mod = importlib.import_module('gba_' + name)
        ims = [mod.T[mt.ch]().im for mt in mts]
        wall_mt = top_mt = 0xFF
        if hasattr(mod, 'wall_top') and name != 'city':
            wall_mt = [mt.ch for mt in mts].index('B')
            top_mt = len(mts)
            ims.append(mod.wall_top().im)
        store, pals, ent = convert_metatiles(ims, 12)
        flags = bytes([mt.flags for mt in mts] + ([1] if top_mt != 0xFF else []))
        code.append(c_array('ts%d_tiles' % ti, store.data()))
        code.append(c_array('ts%d_pals' % ti, pal_bytes(pals)))
        code.append(c_u16('ts%d_mt' % ti, ent))
        code.append(c_array('ts%d_flags' % ti, flags))
        ts_lines.append('  { ts%d_tiles, %d, ts%d_pals, %d, ts%d_mt, ts%d_flags, %d, %d, %d },' % (
            ti, len(store.tiles), ti, len(pals), ti, ti, len(ims), wall_mt, top_mt))
        # preview of the converted tileset
        sheet = Image.new('RGB', (10 * 16, ((len(mts) + 9) // 10) * 16))
        for i, im in enumerate(ims):
            sheet.paste(im, ((i % 10) * 16, (i // 10) * 16))
        sheet.resize((sheet.size[0] * 3, sheet.size[1] * 3), Image.NEAREST).save(
            os.path.join(preview_dir, 'gba_tileset_%s.png' % name))
    code.append('const tileset_t tilesets[%d] = {\n%s\n};' % (len(ts_lines), '\n'.join(ts_lines)))
    for i, n in enumerate(TILESET_NAMES):
        hdr.append('#define TS_%s %d' % (n.upper(), i))

    # palette moods
    import palettes
    moods = []
    for i, n in enumerate(palettes.SETS):
        tint, amt, bright = MOODS[n]
        t = hx(tint) if tint else (0, 0, 0)
        moods.append('  { %d, %d, %d, %d, %d },' % (t[0] >> 3, t[1] >> 3, t[2] >> 3, int(amt * 256), int(bright * 256)))
        hdr.append('#define PS_%s %d' % (n.upper(), i))
    code.append('const mood_t moods[%d] = {\n%s\n};' % (len(moods), '\n'.join(moods)))

    # sprites: pre-rendered 3D characters, 32x64 frames (cached between builds)
    import hashlib
    import numpy as np
    import chars3d
    src_hash = hashlib.sha1((open(os.path.join(HERE, 'render3d.py')).read() +
                             open(os.path.join(ROOT, 'assets', 'gba', 'chars3d.py')).read()).encode()).hexdigest()[:12]
    cache_dir = os.path.join(os.path.dirname(outdir.rstrip('/')), 'cache3d')
    os.makedirs(cache_dir, exist_ok=True)

    def char_frames(n, big=1.0):
        cp = os.path.join(cache_dir, '%s_%s_%s.npy' % (n, big, src_hash))
        if os.path.exists(cp):
            return list(np.load(cp))
        fr = chars3d.frames(n, big)
        np.save(cp, np.array(fr))
        return fr

    def frames_to_obj(fr):
        """RGBA float frames -> one shared 15-colour palette + 4bpp 32x64 tiles (1D order)"""
        opaque = []
        for f in fr:
            m = f[..., 3] >= 0.5
            opaque.append((f[..., :3][m] * 255).astype(np.uint8))
        allpx = np.concatenate(opaque)
        im = Image.fromarray(allpx.reshape(1, -1, 3))
        q = im.quantize(colors=15, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
        pl = q.getpalette()[:45]
        pal = [tuple(pl[k * 3:k * 3 + 3]) for k in range(15)]
        parr = np.array(pal, dtype=np.float64)
        data = bytearray()
        prev = Image.new('RGB', (len(fr) * 34, 64), (70, 66, 62))
        for fi, f in enumerate(fr):
            rgb = f[..., :3] * 255
            d = ((rgb[..., None, :] - parr[None, None]) ** 2).sum(-1)
            idx = d.argmin(-1) + 1
            idx[f[..., 3] < 0.5] = 0
            for ty in range(8):
                for tx in range(4):
                    data += tile4(list(idx[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8].reshape(-1)))
            vis = Image.fromarray(np.where((idx > 0)[..., None], parr[np.maximum(idx - 1, 0)], (70, 66, 62)).astype(np.uint8))
            prev.paste(vis, (fi * 34, 0))
        return bytes(data), pal, prev

    pf = char_frames('hollow')
    d, pal, pv = frames_to_obj(pf)
    code.append(c_array('spr_player', d))
    code.append(c_array('pal_player', obj_pal_bytes(pal)))
    previews = [pv]
    sheet_lines = []
    sheet_ids = {}
    for si, n in enumerate(chars3d.ORDER):
        d, pal, pv = frames_to_obj(char_frames(n)[:12])
        previews.append(pv)
        code.append(c_array('sheet_%s' % n, d))
        code.append(c_array('sheetpal_%s' % n, obj_pal_bytes(pal)))
        sheet_lines.append('  { sheet_%s, sheetpal_%s, 0 },' % (n, n))
        sheet_ids[n] = si
        hdr.append('#define SHEET_%s %d' % (n.upper(), si))
    d, pal, pv = frames_to_obj(char_frames('hector', 1.3)[:12])
    previews.append(pv)
    code.append(c_array('sheet_big_hector', d)); code.append(c_array('sheetpal_big_hector', obj_pal_bytes(pal)))
    sheet_lines.append('  { sheet_big_hector, sheetpal_big_hector, 1 },')
    hdr.append('#define SHEET_BIG_HECTOR %d' % len(chars3d.ORDER))
    sheet_ids['big_hector'] = len(chars3d.ORDER)
    sheet_lines.append('  { sheet_wraith, sheetpal_wraith, 0 },')
    hdr.append('#define SHEET_BIG_SHADOWMAN %d' % (len(chars3d.ORDER) + 1))
    sheet_ids['big_shadowman'] = len(chars3d.ORDER) + 1
    code.append('const sheet_t sheet_dir[%d] = {\n%s\n};' % (len(sheet_lines), '\n'.join(sheet_lines)))
    hdr.append('#define NUM_SHEETS %d' % len(sheet_lines))
    pw = max(p.size[0] for p in previews)
    sheet_img = Image.new('RGB', (pw, 66 * len(previews)))
    for k, p in enumerate(previews):
        sheet_img.paste(p, (0, k * 66))
    sheet_img.save(os.path.join(preview_dir, 'gba_sprites3d.png'))
    sf = shadow_figure_64()

    # fx
    fxs = fx_images()
    d, pal = obj_convert([im for n, im in fxs], 16, 16)
    code.append(c_array('spr_fx', d))
    code.append(c_array('pal_fx', obj_pal_bytes(pal)))
    for i, (n, im) in enumerate(fxs):
        hdr.append('#define SPR_%s %d' % (n.upper(), i))
    hdr.append('#define SPR_FX_COUNT %d' % len(fxs))
    d, pal = obj_convert([sf], 64, 64)
    code.append(c_array('spr_shadowbig', d))
    code.append(c_array('pal_shadowbig', obj_pal_bytes(pal)))

    # illustrations (mode 4)
    img_ids = {}
    img_lines = []
    for i, (n, fn) in enumerate(gba_illus.SCENES):
        im = fn()
        if n == 'title':
            im = title_with_text(im)
        px, pb = convert_illus(im)
        code.append(c_array('img_%s_px' % n, px))
        code.append(c_u16('img_%s_pal' % n, pb))
        img_lines.append('  { img_%s_px, img_%s_pal },' % (n, n))
        img_ids[n] = i
        hdr.append('#define IMG_%s %d' % (n.upper(), i))
        Image.frombytes('P', (240, 160), px).save(os.path.join(preview_dir, 'gba_img_%s.png' % n)) if False else \
            im.save(os.path.join(preview_dir, 'gba_img_%s.png' % n))
    code.append('const image_t image_dir[%d] = {\n%s\n};' % (len(img_lines), '\n'.join(img_lines)))

    # recorded tracks (Synth Centric) replace chip cues in the GBA version
    import songs as song_defs
    sys.path.insert(0, os.path.join(ROOT, 'assets', 'music', 'audio'))
    import tracks
    import audio_convert
    for sd in song_defs.SONGS:
        if sd['id'] in tracks.TRACKS:
            sd['title'] = tracks.TRACKS[sd['id']][1]
    stream_lines = []
    for sd in song_defs.SONGS:
        t = tracks.TRACKS.get(sd['id'])
        if not t:
            stream_lines.append('  { 0, 0, 0 },')
            continue
        fname, title, loop = t
        data, secs = audio_convert.convert(os.path.join(ROOT, 'assets', 'music', 'audio', fname))
        n = len(data) - len(data) % 4
        data = data[:n]
        # guard: DMA can run a little past the end before the VBlank tick re-arms it
        data += data[:4096] if loop else bytes(4096)
        code.append(c_array('stream_%s' % sd['id'], data).replace('const uint8_t', 'const int8_t', 1)
                    .replace('const int8_t stream', 'const int8_t stream'))
        stream_lines.append('  { (const int8_t *)stream_%s, %d, %s },' % (sd['id'], n, '0' if loop else '0xFFFFFFFF'))
        print('recorded track %s: %s, %.1f s, %d bytes' % (sd['id'], fname, secs, n))
    code.append('const stream_t stream_dir[%d] = {\n%s\n};' % (len(stream_lines), '\n'.join(stream_lines)))

    # music (shared driver format) + world content (text re-wrapped for the GBA box)
    songs = build_music.generate(pk, hdr, dirs_c)
    content.TEXT_W = 27
    content.REFLOW = True
    legends = {name: build_tiles.legend(name) for name, _ in build_tiles.TILESETS}
    palsets = {n: i for i, n in enumerate(palettes.SETS)}
    music_ids = {s['id']: i for i, s in enumerate(songs)}
    content.TILE_LEGENDS.update(legends)
    content.MUSIC.update(music_ids)
    content.IMAGES.update(img_ids)
    import world  # noqa
    rep = content.build(pk, hdr, dirs_c, legends, palsets, music_ids, sheet_ids, img_ids, build_tiles.TILESET_ID)
    bake_maps(code, hdr, preview_dir)
    for name, kind, payload in pk.items:
        if kind == 'blob':
            code.append(c_array(name, payload))
        else:
            code.append(payload)
            if name == 'script_dir':
                pass
    for name, kind, payload in pk.items:
        hdr.append('#define %s_BANK 0' % name)
        if kind == 'blob':
            hdr.append('extern const uint8_t %s[];' % name)
    code.append('\n'.join(dirs_c))
    with open(os.path.join(outdir, 'gba_data.c'), 'w') as f:
        f.write('\n'.join(code) + '\n')
    with open(os.path.join(outdir, 'gba_data.h'), 'w') as f:
        f.write('#ifndef GBA_DATA_H\n#define GBA_DATA_H\n#include <stdint.h>\n' + '\n'.join(hdr) + '\n#endif\n')
    print('\n'.join(rep))
    print('tilesets/sprites/illustrations OK')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
