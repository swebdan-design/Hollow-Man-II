"""Builds font/UI tiles, environment tilesets and BG palettes."""
import os
import sys
from gfx import Grid, tile_2bpp, TileBank, rgb15, save_preview

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'assets', 'art'))
sys.path.insert(0, os.path.join(ROOT, 'assets', 'tilesets'))

import font  # noqa
import ui  # noqa
import palettes  # noqa
import city  # noqa
import interior  # noqa
import under  # noqa

TILESETS = [('city', city.TILESET), ('interior', interior.TILESET), ('under', under.TILESET)]
TILESET_ID = {n: i for i, (n, _) in enumerate(TILESETS)}


def legend(tsname):
    ts = dict(TILESETS)[tsname]
    return {mt.ch: (i, mt) for i, mt in enumerate(ts)}


def font_tiles():
    data = b''
    for c in range(32, 128):
        rows = font.glyph_rows(chr(c))
        g = Grid.from_ascii([r.replace('#', '3') for r in rows])
        data += tile_2bpp(g)
    for name, rows in ui.UI:
        g = Grid.from_ascii(rows)
        data += tile_2bpp(g)
    assert len(data) == 128 * 16
    return data


UI_INDEX = {name: 96 + i for i, (name, _) in enumerate(ui.UI)}


def build_tileset(name, mts, preview_dir=None, pal=None):
    bank = TileBank(allow_flip=True, limit=256)
    mt_tiles, mt_attr, mt_flags = [], [], []
    assert len(mts) <= 64, (name, len(mts))
    chars = set()
    for mt in mts:
        assert mt.ch not in chars, (name, mt.ch)
        chars.add(mt.ch)
        roles = mt.quad_roles or [mt.role] * 4
        for qi, (qx, qy) in enumerate(((0, 0), (8, 0), (0, 8), (8, 8))):
            t = tile_2bpp(mt.art, qx, qy)
            idx, hf, vf = bank.add(t)
            mt_tiles.append(idx)
            mt_attr.append((roles[qi] & 7) | 0x08 | (0x20 if hf else 0) | (0x40 if vf else 0))
        mt_flags.append(mt.flags)
    n = len(bank.tiles)
    blob = bytes([n & 0xFF, len(mts)]) + bank.data() + bytes(mt_tiles) + bytes(mt_attr) + bytes(mt_flags)
    if preview_dir and pal:
        items = []
        for i, mt in enumerate(mts):
            roles = mt.quad_roles or [mt.role] * 4
            for qi, (qx, qy) in enumerate(((0, 0), (8, 0), (0, 8), (8, 8))):
                items.append((mt.art.sub(qx, qy, 8, 8), (i % 8) * 18 + qx, (i // 8) * 18 + qy, pal[roles[qi]]))
        save_preview(items, os.path.join(preview_dir, 'tileset_%s.png' % name), 3)
    return blob, n


def pal_blob(pals):
    out = []
    for p in pals:
        assert len(p) == 4
        for c in p:
            w = rgb15(*c)
            out += [w & 0xFF, w >> 8]
    return bytes(out)


PALSET_ID = {n: i for i, n in enumerate(palettes.SETS)}


def generate(pk, hdr, preview_dir):
    pk.blob('font_tiles', font_tiles())
    stats = []
    for name, mts in TILESETS:
        # preview with first matching palette set
        pal = None
        for pn, (tsn, pals) in palettes.SETS.items():
            if tsn == name:
                pal = pals
                break
        blob, n = build_tileset(name, mts, preview_dir, pal)
        pk.blob('ts_' + name, blob)
        stats.append('tileset %s: %d metatiles, %d tiles' % (name, len(mts), n))
    pdata = b''
    for pn, (tsn, pals) in palettes.SETS.items():
        pdata += pal_blob(pals)
    pk.blob('bg_palsets', pdata)
    hdr.append('#define NUM_TILESETS %d' % len(TILESETS))
    for i, (n, _) in enumerate(TILESETS):
        hdr.append('#define TS_%s %d' % (n.upper(), i))
    for n, i in PALSET_ID.items():
        hdr.append('#define PS_%s %d' % (n.upper(), i))
    for n, i in UI_INDEX.items():
        hdr.append('#define UI_%s %d' % (n.upper(), i))
    return stats
