"""Music compiler: song definitions (assets/music/songs.py) -> driver byte streams.

Song channel text format: whitespace separated tokens
   NOTE:LEN   e.g. D4:8  F#3:2  Bb2:4      (LEN in rows)
   r:LEN      rest
   h:LEN      hold previous note (no retrigger)
   i:N        instrument change (0 rows)
Drum channel tokens: k s h o n w c r (kick snare hat open dusty rumble crash x=rim)
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'assets', 'music'))

SEMI = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}
DRUMS = {'k': 0, 's': 1, 'h': 2, 'o': 3, 'n': 4, 'w': 5, 'c': 6, 'x': 7}


def note_index(tok):
    name = tok[0].upper()
    i = 1
    acc = 0
    while i < len(tok) and tok[i] in '#b':
        acc += 1 if tok[i] == '#' else -1
        i += 1
    octv = int(tok[i:])
    n = (octv - 2) * 12 + SEMI[name] + acc
    if not (0 <= n < 84):
        raise ValueError('note out of range: ' + tok)
    return n


def parse(text, drums=False):
    ev = []   # (kind, value, rows)
    for tok in text.split():
        if tok == '|':
            continue
        k, _, v = tok.partition(':')
        if k == 'i':
            ev.append(('ins', int(v), 0))
            continue
        ln = int(v)
        if k == 'r':
            ev.append(('rest', 0, ln))
        elif k == 'h':
            ev.append(('hold', 0, ln))
        elif drums:
            ev.append(('note', DRUMS[k], ln))
        else:
            ev.append(('note', note_index(k), ln))
    return ev


def encode(ev, loop):
    out = []
    if loop:
        out.append(0x82)
    cur_len = None
    for kind, val, ln in ev:
        if kind == 'ins':
            out += [0x81, val]
            continue
        while ln > 0:
            chunk = min(ln, 255)
            if chunk != cur_len:
                out += [0x80, chunk]
                cur_len = chunk
            if kind == 'note':
                out.append(val)
                kind = 'hold'
            elif kind == 'rest':
                out.append(0x60)
                kind = 'hold_rest'
            else:
                out.append(0x61)
            ln -= chunk
    out.append(0x83 if loop else 0x84)
    return out


def total(ev):
    return sum(e[2] for e in ev)


def note_table():
    t = []
    for n in range(84):
        f = 65.406 * 2 ** (n / 12.0)
        x = int(round(2048 - 131072 / f))
        t.append(max(0, min(2047, x)))
    return t


def generate(pk, hdr, dirs_c):
    import songs
    names = []
    for idx, s in enumerate(songs.SONGS):
        chans = []
        lens = []
        for c in range(4):
            ev = parse(s['ch'][c], drums=(c == 3))
            lens.append(total(ev))
            chans.append(ev)
        L = max(lens)
        for c in range(4):
            if lens[c] == 0:
                chans[c] = [('rest', 0, L)]
            elif lens[c] != L:
                raise ValueError('song %s: channel %d length %d != %d' % (s['name'], c, lens[c], L))
        streams = [encode(chans[c], s.get('loop', True)) for c in range(4)]
        blob = [s['speed'], 1 if s.get('loop', True) else 0]
        off = 10
        offs = []
        for st in streams:
            offs.append(off)
            off += len(st)
        for o in offs:
            blob += [o & 0xFF, o >> 8]
        for st in streams:
            blob += st
        pk.blob('song_%d' % idx, bytes(blob), group='music%d' % (idx // 6))
        names.append(s)
        hdr.append('#define MUS_%s %d' % (s['id'].upper(), idx))
        secs = L * s['speed'] / 60.0
        s['_secs'] = secs
    hdr.append('#define NUM_SONGS %d' % len(names))
    dirs_c.append('const far_t song_dir[%d] = {' % len(names))
    for i in range(len(names)):
        dirs_c.append('  { song_%d_BANK, song_%d },' % (i, i))
    dirs_c.append('};')
    dirs_c.append('const uint16_t note_table[84] = {' + ','.join(str(x) for x in note_table()) + '};')
    # song titles for music player (bank 0 strings are small)
    dirs_c.append('const char * const song_title[%d] = {' % len(names))
    for s in names:
        assert len(s['title']) <= 16, s['title']
        dirs_c.append('  "%s",' % s['title'])
    dirs_c.append('};')
    return names
