"""Builds sprite sheets + OBJ palettes."""
import os
import sys
from gfx import Grid, tile_2bpp, rgb15, hexcol, save_preview

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'assets', 'sprites'))
import chars  # noqa
import fx  # noqa


def P(*hs):
    return [(255, 0, 255)] + [hexcol(h) for h in hs]


# OBJ palettes: index 0 transparent
OBJ_PALS = [
    P('d8c8a8', '7a5236', '141010'),   # 0 Hollow Man: cream shirt/skin, brown tweed, black mask
    P('d0a888', '6c6858', '201814'),   # 1 civilians: skin, grey-olive coat, dark
    P('d0a888', '6a5a3a', '181410'),   # 2 people B: skin, olive-brown, dark
    P('c89c80', '50504c', '101010'),   # 3 thugs: skin, charcoal, black
    P('c89c80', '384058', '0c0c18'),   # 4 police: skin, navy, black
    P('e8d8b0', 'a02020', '140808'),   # 5 crimson fx / butcher
    P('d8b090', 'a0784c', '5a2418'),   # 6 Bell: skin, camel coat, auburn
    P('b01818', '2a2026', '060406'),   # 7 shadow: glowing crimson, charcoal, black
]


def doll_frames(name):
    head, body, cm, pal = chars.CHARS[name]
    H = chars.HEADS[head]
    B = chars.BODIES[body]
    frames = []
    for d in ('down', 'up', 'side'):
        for step in (0, 1):
            rows = H[d] + B[d][step]
            assert len(rows) == 16, (name, d, len(rows))
            g = Grid(16, 16)
            for y, r in enumerate(rows):
                assert len(r) == 16, (name, d, y, r)
                for x, ch in enumerate(r):
                    g.p[y][x] = cm[ch]
            frames.append(g)
    return frames, pal


def attack_frames(name):
    head, body, cm, pal = chars.CHARS[name]
    H = chars.HEADS[head]
    out = []
    for d in ('down', 'up', 'side'):
        rows = H[d] + chars.ATTACK[d]
        g = Grid(16, 16)
        for y, r in enumerate(rows):
            for x, ch in enumerate(r):
                g.p[y][x] = cm[ch]
        out.append(g)
    return out


def frame16_tiles(g, ox=0, oy=0):
    """16x16 -> 4 tiles in 8x16 sprite order: TL, BL, TR, BR"""
    return (tile_2bpp(g, ox, oy) + tile_2bpp(g, ox, oy + 8) +
            tile_2bpp(g, ox + 8, oy) + tile_2bpp(g, ox + 8, oy + 8))


def g_from(rows):
    return Grid.from_ascii(rows)


def scale2(g):
    o = Grid(g.w * 2, g.h * 2)
    for y in range(g.h):
        for x in range(g.w):
            v = g.p[y][x]
            for dy in (0, 1):
                for dx in (0, 1):
                    o.p[y * 2 + dy][x * 2 + dx] = v
    return o


def big_tiles(g):
    """32x32 -> 16 tiles: 4 columns x 2 rows of 8x16 sprites (col-major per row)"""
    out = b''
    for row in range(2):
        for col in range(4):
            out += tile_2bpp(g, col * 8, row * 16) + tile_2bpp(g, col * 8, row * 16 + 8)
    return out


NPC_SHEETS = ['bell', 'thug', 'runner', 'gunman', 'police', 'oldwoman', 'oldman',
              'citizen', 'vagrant', 'clerk', 'priest', 'eddie', 'hector', 'nolan',
              'dacre', 'mott', 'crewe', 'rusk', 'wraith', 'nurse', 'hollow']
BIG_SHEETS = ['hector', 'shadowman']

FX16_ORDER = ['pipe_v', 'pipe_h', 'axe_v', 'axe_h', 'spark', 'shadow_blob',
              'shadow_horned', 'saw', 'rat_side', 'rat_down', 'bell']
FX8_ORDER = ['bullet', 'alert', 'question', 'heart', 'ammo', 'bottle', 'stars', 'ember', 'smoke']


def generate(pk, hdr, preview_dir):
    prev = []
    # player sheet: 6 doll frames + 3 attack frames
    pf, _ = doll_frames('hollow')
    pf += attack_frames('hollow')
    data = b''.join(frame16_tiles(f) for f in pf)
    pk.blob('spr_player', data)
    for i, f in enumerate(pf):
        prev.append((f, i * 18, 0, OBJ_PALS[0]))

    # fx sheet
    data = b''
    for n in FX16_ORDER:
        data += frame16_tiles(g_from(fx.FX16[n]))
    for n in FX8_ORDER:
        g = g_from(fx.FX8[n])
        data += tile_2bpp(g, 0, 0) + tile_2bpp(g, 0, 8)
    pk.blob('spr_fx', data)
    base = 36
    for i, n in enumerate(FX16_ORDER):
        hdr.append('#define SPR_%s %d' % (n.upper(), base + i * 4))
        prev.append((g_from(fx.FX16[n]), i * 18, 20, OBJ_PALS[5]))
    base2 = base + len(FX16_ORDER) * 4
    for i, n in enumerate(FX8_ORDER):
        hdr.append('#define SPR_%s %d' % (n.upper(), base2 + i * 2))
    hdr.append('#define SPR_FX_TILES %d' % (len(data) // 16))
    hdr.append('#define SPR_FX_BASE %d' % base)
    assert base2 + len(FX8_ORDER) * 2 <= 100

    # npc sheets
    sheet_names = []
    dirlines = []
    for i, n in enumerate(NPC_SHEETS):
        fr, pal = doll_frames(n)
        data = b''.join(frame16_tiles(f) for f in fr)
        pk.blob('sheet_' + n, data, group='sheets')
        sheet_names.append(n)
        for j, f in enumerate(fr):
            prev.append((f, j * 18, 40 + i * 18, OBJ_PALS[pal]))
        hdr.append('#define SHEET_%s %d' % (n.upper(), i))
        dirlines.append((n, pal, 0))
    # big sheets (32x32, 3 frames down/up/side)
    for k, n in enumerate(BIG_SHEETS):
        idx = len(NPC_SHEETS) + k
        if n == 'shadowman':
            g = g_from(fx.SHADOW_BIG)
            # three frames: full upper 32 rows variants
            frames = [g.sub(0, 0, 32, 32), g.sub(0, 0, 32, 32), g.sub(0, 0, 32, 32)]
            pal = 7
        else:
            fr, pal = doll_frames(n)
            frames = [scale2(fr[0]), scale2(fr[2]), scale2(fr[4])]
        data = b''.join(big_tiles(f) for f in frames)
        pk.blob('sheet_big_' + n, data, group='sheets')
        hdr.append('#define SHEET_BIG_%s %d' % (n.upper(), idx))
        dirlines.append(('big_' + n, pal, 1))
        for j, f in enumerate(frames):
            prev.append((f, j * 34, 40 + len(NPC_SHEETS) * 18 + k * 34, OBJ_PALS[pal]))
    # the full shadow figure 32x48 = 4 cols x 3 rows of 8x16
    g = g_from(fx.SHADOW_BIG)
    data = b''
    for row in range(3):
        for col in range(4):
            data += tile_2bpp(g, col * 8, row * 16) + tile_2bpp(g, col * 8, row * 16 + 8)
    pk.blob('spr_shadowbig', data)
    prev.append((g, 200, 0, OBJ_PALS[7]))

    hdr.append('#define NUM_SHEETS %d' % len(dirlines))
    # directory: per sheet {bank, ptr(2), pal, big}
    code = 'const sheet_t sheet_dir[%d] = {\n' % len(dirlines)
    for n, pal, big in dirlines:
        code += '  { sheet_%s_BANK, sheet_%s, %d, %d },\n' % (n, n, pal, big)
    code += '};\n'
    pal = b''
    for p in OBJ_PALS:
        for c in p:
            w = rgb15(*c)
            pal += bytes([w & 0xFF, w >> 8])
    pk.blob('obj_pals', pal)
    save_preview(prev, os.path.join(preview_dir, 'sprites.png'), 3)
    return dirlines, code
