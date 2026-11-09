"""Host-side model of the SRAM save format (mirrors src/save.c and gstate_t in include/hm.h)."""
import struct

GS_SIZE = 188
SLOT_A, SLOT_B, OPT = 0x100, 0x400, 0x000
OFF = dict(magic=0, version=4, seq=5, map=6, px=7, py=8, pdir=9, hp=10, maxhp=11, chapter=12,
           influence=13, alert=14, weapon=15, tool=16, ammo=17, bandages=18, bottles=19, items=20,
           evidence=24, flags=29, vars=157, music_unlock=173, revive_used=175, kills=176,
           cops_killed=177, play_min=178, play_sec=180, play_frm=181, visited=182, checksum=186)


def checksum(b):
    a = 0x1234
    for x in b[:GS_SIZE - 2]:
        a = (((a << 1) | (a >> 15)) & 0xFFFF) ^ x
    return a


def make_state(map_id, x, y, flags=(), items=(), evidence=(), **kw):
    g = bytearray(GS_SIZE)
    g[0:4] = b'HM2S'
    g[OFF['version']] = 1
    g[OFF['seq']] = kw.get('seq', 1)
    g[OFF['map']], g[OFF['px']], g[OFF['py']], g[OFF['pdir']] = map_id, x, y, kw.get('pdir', 0)
    g[OFF['hp']] = kw.get('hp', 10)
    g[OFF['maxhp']] = kw.get('maxhp', 10)
    for k in ('chapter', 'influence', 'alert', 'weapon', 'tool', 'ammo', 'bandages', 'bottles'):
        g[OFF[k]] = kw.get(k, 0)
    for i in items:
        g[OFF['items'] + (i >> 3)] |= 1 << (i & 7)
    for e in evidence:
        g[OFF['evidence'] + (e >> 3)] |= 1 << (e & 7)
    for f in flags:
        g[OFF['flags'] + (f >> 3)] |= 1 << (f & 7)
    g[OFF['music_unlock']] = kw.get('music', 0xFF)
    g[OFF['music_unlock'] + 1] = kw.get('music2', 0xFF)
    g[OFF['visited']] = kw.get('visited', 0x7F)
    struct.pack_into('<H', g, OFF['checksum'], checksum(g))
    return bytes(g)


def make_sram(state_a=None, state_b=None, options=None):
    s = bytearray([0xFF]) * 8192
    if state_a:
        s[SLOT_A:SLOT_A + GS_SIZE] = state_a
    if state_b:
        s[SLOT_B:SLOT_B + GS_SIZE] = state_b
    if options:
        m, fx, sp = options
        s[0:7] = bytes([ord('O'), ord('P'), ord('T'), m, fx, sp, (m + fx * 3 + sp * 7 + 0x5A) & 0xFF])
    return bytes(s)


def parse(sram, slot):
    off = SLOT_A if slot == 'A' else SLOT_B
    g = sram[off:off + GS_SIZE]
    ok = g[0:4] == b'HM2S' and g[4] == 1 and struct.unpack_from('<H', g, OFF['checksum'])[0] == checksum(g)
    return ok, g
