"""content.py - DSL + compiler for maps, objects and event scripts.

Content files in assets/maps/*.py import this module and declare maps and
scripts.  build() compiles everything to bytecode blobs and C directories.
"""
import textwrap

# ---------------------------------------------------------------- registries
FLAGS = {}
VARS = {}
MAPS = []
MAP_BY_NAME = {}
SCRIPTS = []          # list of (name, ops)
SCRIPT_ID = {}
WARNINGS = []

DIRS = {'down': 0, 'up': 1, 'left': 2, 'right': 3}

ITEMS = [
    # id, name (<=14), description (casebook/inventory)
    ('pipe', 'Lead Pipe', 'A length of rusted lead pipe. It has done this before.'),
    ('axe', 'Fire Axe', 'Taken from a cold storage wall. Hold B to charge a crushing swing.'),
    ('pistol', 'Revolver', 'Six chambers. Loud. Every shot raises the police alert.'),
    ('office_key', 'Office Key', "A brass key tagged OFFICE. From Eddie's storeroom."),
    ('eddie_keys', "Eddie's Keys", 'A heavy keyring. One tag reads VALE COLD STORAGE - GATE.'),
    ('fuse', 'Heavy Fuse', 'A 60-amp cartridge fuse. Still good.'),
    ('cutters', 'Bolt Cutters', 'Hector kept them by the loading bay. They bite through chain.'),
    ('room_key', 'Room 6 Key', 'Red Lantern Motel. Room 6. The tag is sticky.'),
    ('church_key', 'Sacristy Key', 'An iron key wrapped in a rosary. St. Agnes sacristy.'),
    ('sluice_key', 'Sluice Key', 'A city works key for the storm drain gates.'),
    ('evidence_key', 'Evidence Key', 'Gloam P.D. evidence locker key. Stamped D-7.'),
    ('basement_map', 'Basement Map', 'A hand-drawn map of the cellar under 13 Mercy Street.'),
    ('keycard', 'Ward Keycard', 'A magnetic keycard. LAST WARD - STAFF ONLY.'),
    ('house_key', 'House Key', 'A key to 13 Mercy Street. It still turns.'),
    ('valve_wheel', 'Valve Wheel', 'A loose iron valve wheel from the Drain works.'),
    ('chapel_key', 'Chapel Key', 'A tarnished key. LAST WARD - CHAPEL.'),
]
ITEM_ID = {it[0]: i for i, it in enumerate(ITEMS)}

EVIDENCE = []          # (id, title, text)
EV_ID = {}


def evidence(eid, title, text):
    assert eid not in EV_ID, eid
    assert len(title) <= 17, title
    EV_ID[eid] = len(EVIDENCE)
    EVIDENCE.append((eid, title, text))


SHEETS = {}            # filled by build from sprite builder
TILE_LEGENDS = {}      # tileset -> {char: (idx, mt)}
PALSETS = {}
MUSIC = {}
TILESET_ID = {}

ENEMY_KINDS = {'thug': 0, 'runner': 1, 'gunman': 2, 'police': 3, 'wraith': 4, 'rat': 5}
ENEMY_SHEET = {'thug': 'thug', 'runner': 'runner', 'gunman': 'gunman', 'police': 'police',
               'wraith': 'wraith', 'rat': None}
BOSSES = {'eddie': 0, 'hector': 1, 'nolan': 2, 'dacre': 3, 'mott': 4, 'crewe': 5, 'rusk': 6}
BOSS_SHEET = {'eddie': 'eddie', 'hector': 'big_hector', 'nolan': 'nolan', 'dacre': 'dacre',
              'mott': 'mott', 'crewe': 'crewe', 'rusk': 'rusk'}
SPECIALS = {}


def special_id(name):
    if name not in SPECIALS:
        SPECIALS[name] = len(SPECIALS)
    return SPECIALS[name]


def flag(name):
    if name not in FLAGS:
        FLAGS[name] = len(FLAGS)
        assert len(FLAGS) < 1000
    return FLAGS[name]


def var(name):
    if name not in VARS:
        VARS[name] = len(VARS)
        assert len(VARS) <= 16, 'too many vars'
    return VARS[name]


# ---------------------------------------------------------------- conditions
# cond objects: 'FLAG' | ('not', c) | ('item', x) | ('ev', x) | ('infl', n) |
#               ('var', name, val) | ('varge', name, val) | ('alert', n) | ('evcount', n)
#               ('stage', n) | ('chapter', n) | ('ammo', n)
C_FLAG, C_ITEM, C_EV, C_INFL, C_VAREQ, C_VARGE, C_ALERT, C_EVCOUNT, C_STAGE, C_CHAPTER, C_AMMO, C_NOT, C_MERCY = range(13)


def enc_cond(c):
    if isinstance(c, str):
        f = flag(c)
        return [C_FLAG, f & 0xFF, f >> 8]
    k = c[0]
    if k == 'not':
        return [C_NOT] + enc_cond(c[1])
    if k == 'item':
        return [C_ITEM, ITEM_ID[c[1]]]
    if k == 'ev':
        return [C_EV, EV_ID[c[1]]]
    if k == 'infl':
        return [C_INFL, c[1]]
    if k == 'var':
        return [C_VAREQ, var(c[1]), c[2]]
    if k == 'varge':
        return [C_VARGE, var(c[1]), c[2]]
    if k == 'alert':
        return [C_ALERT, c[1]]
    if k == 'evcount':
        return [C_EVCOUNT, c[1]]
    if k == 'stage':
        return [C_STAGE, c[1]]
    if k == 'chapter':
        return [C_CHAPTER, c[1]]
    if k == 'ammo':
        return [C_AMMO, c[1]]
    if k == 'mercycount':
        return [C_MERCY, c[1]]
    raise ValueError(c)


def obj_cond(c):
    """16-bit object/patch condition: flag, bit15 = negate. special pseudo flags."""
    if c is None:
        return 0xFFFF
    neg = 0
    if isinstance(c, tuple) and c[0] == 'not':
        neg = 0x8000
        c = c[1]
    if isinstance(c, str):
        return flag(c) | neg
    if c[0] == 'alert':
        return (0x7F00 + c[1]) | neg
    if c[0] == 'stage':
        return (0x7F10 + c[1]) | neg
    if c[0] == 'chapter':
        return (0x7F20 + c[1]) | neg
    if c[0] == 'item':
        return (0x7F40 + ITEM_ID[c[1]]) | neg
    raise ValueError(c)


# ---------------------------------------------------------------- script ops
OP = dict(END=0, SAY=1, JMP=2, IF=3, SETF=4, CLRF=5, GIVE=6, TAKE=7, EV=8, INFL=9, ALERT=10,
          CHOICE=11, WARP=12, MUSIC=13, SFX=14, WAIT=15, FADEOUT=16, FADEIN=17, SHAKE=18,
          IMAGE=19, IMAGE_END=20, AMOVE=21, PMOVE=22, PFACE=23, SETTILE=24, CHAPTER=25,
          HEAL=26, SAVE=27, ENDING=28, SPECIAL=29, SETVAR=30, ADDVAR=31, AHIDE=32, ASHOW=33,
          NOISE=34, SHADOW=35, AMMO=36, BANDAGE=37, BOTTLE=38, UNLOCK=39, AFACE=40,
          FLASH=41, CALL=42, DAMAGE=43, REDRAW=44, WEAPON=45, CLOSE=46, PHIDE=47, PSHOW=48,
          AWARP=49, CREDITS=50, REDFLASH=51, CHECKPOINT=52, ALERTSET=53, MUSICRESUME=54)

SFX = dict(none=0, confirm=1, cursor=2, swing=3, hit=4, gun=5, hurt=6, door=7, key=8,
           pickup=9, shadow=10, solved=11, blip=12, step=13, alert=14, deny=15, thunder=16,
           heavy=17, save=18, smash=19, kill=20)

IMAGES = {}


class Op:
    def __init__(self, kind, *args):
        self.kind = kind
        self.args = args


def _text(s, nowait=False, page_lines=4, width=18):
    """Wrap text: '|' forces a page break. Returns bytes with \\n \\f codes."""
    out = []
    pages = s.split('|')
    first = True
    for pg in pages:
        pg = pg.strip()
        paras = pg.split('\n')
        lines = []
        for para in paras:
            ws = textwrap.wrap(para.strip(), width, break_long_words=False, break_on_hyphens=False)
            for w in ws:
                if len(w) > width:
                    raise ValueError('word too long for text box: %r' % w)
            lines += ws if ws else ['']
        for i in range(0, len(lines), page_lines):
            chunk = lines[i:i + page_lines]
            if not first:
                out.append('\f')
            first = False
            out.append('\n'.join(chunk))
    txt = ''.join(out)
    for ch in txt:
        if ch not in '\n\f' and not (32 <= ord(ch) < 127):
            raise ValueError('bad char %r in %r' % (ch, s))
    b = txt.encode('ascii')
    if nowait:
        lines_last = txt.split('\f')[-1].count('\n') + 1
        if lines_last > 2:
            raise ValueError('choice question must fit in 2 lines on its page: %r' % s)
        return b + b'\v'
    return b + b'\x00'


def say(*texts):
    return [Op('SAY', _text(t)) for t in texts]


def iff(cond, then, els=None):
    return [Op('IF', cond, flatten(then), flatten(els or []))]


def choice(question, a, b, on_a, on_b):
    return [Op('SAY', _text(question, nowait=True)), Op('CHOICE', a, b, flatten(on_a), flatten(on_b))]


def setf(f): return [Op('SETF', flag(f))]
def clrf(f): return [Op('CLRF', flag(f))]
def give(i): return [Op('GIVE', ITEM_ID[i])]
def take(i): return [Op('TAKE', ITEM_ID[i])]
def ev(e): return [Op('EV', EV_ID[e])]
def infl(n): return [Op('INFL', n & 0xFF)]
def alert(n): return [Op('ALERT', n & 0xFF)]
def alertset(n): return [Op('ALERTSET', n)]
def warp(m, x, y, d='down'): return [Op('WARP', m, x, y, DIRS[d])]
def music(m): return [Op('MUSIC', m)]
def music_resume(): return [Op('MUSICRESUME')]
def sfx(s): return [Op('SFX', SFX[s])]
def wait(n): return [Op('WAIT', n)]
def fade_out(): return [Op('FADEOUT')]
def fade_in(): return [Op('FADEIN')]
def shake(n): return [Op('SHAKE', n)]
def image(i): return [Op('IMAGE', i)]
def image_end(): return [Op('IMAGE_END')]
def amove(who, d, tiles): return [Op('AMOVE', who, DIRS[d], tiles)]
def pmove(d, tiles): return [Op('PMOVE', DIRS[d], tiles)]
def pface(d): return [Op('PFACE', DIRS[d])]
def settile(x, y, ch): return [Op('SETTILE', x, y, ch)]
def chapter(n): return [Op('CHAPTER', n)]
def heal(n): return [Op('HEAL', n)]
def savepoint(): return [Op('SAVE')]
def ending(): return [Op('ENDING')]
def special(name): return [Op('SPECIAL', special_id(name))]
def setvar(v, n): return [Op('SETVAR', var(v), n)]
def addvar(v, n): return [Op('ADDVAR', var(v), n & 0xFF)]
def ahide(who): return [Op('AHIDE', who)]
def ashow(who): return [Op('ASHOW', who)]
def noise(x, y): return [Op('NOISE', x, y)]
def shadow(x, y): return [Op('SHADOW', x, y)]
def shadow_hide(): return [Op('SHADOW', 0xFF, 0xFF)]
def ammo(n): return [Op('AMMO', n)]
def bandage(n): return [Op('BANDAGE', n)]
def bottle(n): return [Op('BOTTLE', n)]
def unlock(m): return [Op('UNLOCK', m)]
def aface(who, d): return [Op('AFACE', who, DIRS[d])]
def flash(): return [Op('FLASH')]
def redflash(): return [Op('REDFLASH')]
def call(name): return [Op('CALL', name)]
def damage(n): return [Op('DAMAGE', n)]
def redraw(): return [Op('REDRAW')]
def weapon(n): return [Op('WEAPON', n)]
def close(): return [Op('CLOSE')]
def phide(): return [Op('PHIDE')]
def pshow(): return [Op('PSHOW')]
def awarp(who, x, y): return [Op('AWARP', who, x, y)]
def credits(): return [Op('CREDITS')]
def checkpoint(): return [Op('CHECKPOINT')]


def flatten(ops):
    out = []
    if ops is None:
        return out
    if isinstance(ops, Op):
        return [ops]
    for o in ops:
        if isinstance(o, Op):
            out.append(o)
        else:
            out += flatten(o)
    return out


def S(name, *ops):
    """Register a named script."""
    assert name not in SCRIPT_ID, name
    SCRIPT_ID[name] = len(SCRIPTS)
    SCRIPTS.append((name, flatten(list(ops)), None))
    return name


_anon = [0]


def anon(ops, mapname=None):
    if ops is None:
        return 0xFFFF
    if isinstance(ops, str):
        return ops   # named reference (resolved later)
    _anon[0] += 1
    name = '_s%d' % _anon[0]
    SCRIPT_ID[name] = len(SCRIPTS)
    SCRIPTS.append((name, flatten(ops), mapname))
    return name


# ---------------------------------------------------------------- maps
OUTDOOR, RESTRICTED, RAIN, SAFE, DARKMAP = 1, 2, 4, 8, 16
CITY = OUTDOOR | RAIN


class Map:
    def __init__(self, name, ts, pal, music, grid, district=0, flags=0, title=''):
        assert name not in MAP_BY_NAME, name
        self.name, self.ts, self.pal, self.music = name, ts, pal, music
        self.district, self.flags, self.title = district, flags, title
        rows = [r.rstrip() for r in grid.strip('\n').split('\n')]
        rows = [r.strip() for r in rows]
        self.rows = rows
        self.h = len(rows)
        self.w = len(rows[0])
        for r in rows:
            assert len(r) == self.w, (name, r)
        assert 10 <= self.w <= 16 and 9 <= self.h <= 16, (name, self.w, self.h)
        self.exits = [None] * 4
        self.warps = []
        self.objs = []
        self.patches = []
        self.enter = None
        self.names = {}
        MAPS.append(self)
        MAP_BY_NAME[name] = self

    def exit(self, n=None, s=None, w=None, e=None):
        self.exits = [n, s, w, e]
        return self

    def warp(self, x, y, dest, dx, dy, ddir='down', cond=None, lock=None):
        self.warps.append((x, y, dest, dx, dy, DIRS[ddir], cond, anon(lock, self.name) if lock else 0xFFFF))
        return self

    def door(self, x, y, dest, dx, dy, ddir='down', cond=None, lock=None):
        return self.warp(x, y, dest, dx, dy, ddir, cond, lock)

    def _obj(self, typ, x, y, a, b, c, cond, script, name=None):
        idx = len(self.objs)
        self.objs.append([typ, x, y, a, b, c, cond, script])
        if name:
            assert name not in self.names, name
            self.names[name] = idx
        return idx

    def npc(self, name, x, y, sheet, talk, move='static', d='down', cond=None):
        mv = {'static': 0, 'wander': 1, 'paceh': 2, 'pacev': 3, 'none': 4}[move]
        return self._obj(1, x, y, sheet, mv, DIRS[d], cond, anon(talk, self.name), name)

    def enemy(self, kind, x, y, patrol='static', rng=0, d='down', cond=None, name=None, on_death=None):
        mode = {'static': 0, 'h': 1, 'v': 2, 'wander': 3, 'guard': 4}[patrol]
        return self._obj(2, x, y, ENEMY_KINDS[kind], (mode << 4) | rng, DIRS[d], cond,
                         anon(on_death, self.name) if on_death else 0xFFFF, name)

    def boss(self, bid, x, y, cond, on_defeat, name=None, param=0):
        return self._obj(3, x, y, BOSSES[bid], param, 0, cond, anon(on_defeat, self.name), name)

    def sign(self, x, y, script, cond=None):
        return self._obj(4, x, y, 0, 0, 0, cond, anon(script, self.name))

    def trigger(self, x, y, w, h, script, cond=None):
        return self._obj(5, x, y, w, h, 0, cond, anon(script, self.name))

    def hazard(self, kind, x, y, axis, rng, cond=None):
        k = {'saw': 0, 'hook': 1}[kind]
        return self._obj(6, x, y, k, {'h': 0, 'v': 1}[axis], rng, cond, 0xFFFF)

    def pickup(self, x, y, kind, n=1):
        k = {'bandage': 0, 'ammo': 1, 'bottle': 2}[kind]
        f = '_pk_%s_%d_%d' % (self.name, x, y)
        act = {'bandage': bandage(n), 'ammo': ammo(n), 'bottle': bottle(n)}[kind]
        return self._obj(7, x, y, k, n, 0, ('not', f), anon([setf(f), act], self.name))

    def search(self, x, y, found, empty="Nothing else here.", cond=None):
        f = '_srch_%s_%d_%d' % (self.name, x, y)
        return self.sign(x, y, iff(f, say(empty), [setf(f)] + flatten(found)), cond)

    def noisemaker(self, x, y, text):
        return self.sign(x, y, [say(text), sfx('alert'), noise(x, y)])

    def patch(self, x, y, ch, cond):
        self.patches.append((x, y, ch, cond))
        return self

    def on_enter(self, script):
        self.enter = anon(script, self.name)
        return self


# ---------------------------------------------------------------- compile
def compile_script(name, ops, mapname):
    code = []
    fixups = []

    def emit(o):
        k = o.kind
        if k == 'SAY':
            code.append(OP['SAY'])
            code.extend(o.args[0])
        elif k == 'IF':
            cond, then, els = o.args
            code.append(OP['IF'])
            code.extend(enc_cond(cond))
            pos = len(code)
            code.extend([0, 0])
            for t in then:
                emit(t)
            if els:
                code.append(OP['JMP'])
                pos2 = len(code)
                code.extend([0, 0])
                tgt = len(code)
                code[pos] = tgt & 0xFF
                code[pos + 1] = tgt >> 8
                for e in els:
                    emit(e)
                tgt2 = len(code)
                code[pos2] = tgt2 & 0xFF
                code[pos2 + 1] = tgt2 >> 8
            else:
                tgt = len(code)
                code[pos] = tgt & 0xFF
                code[pos + 1] = tgt >> 8
        elif k == 'CHOICE':
            a, b, on_a, on_b = o.args
            assert len(a) <= 15 and len(b) <= 15
            code.append(OP['CHOICE'])
            code.extend(a.encode() + b'\0' + b.encode() + b'\0')
            pos = len(code)
            code.extend([0, 0])
            for t in on_a:
                emit(t)
            code.append(OP['JMP'])
            pos2 = len(code)
            code.extend([0, 0])
            tgt = len(code)
            code[pos] = tgt & 0xFF
            code[pos + 1] = tgt >> 8
            for t in on_b:
                emit(t)
            tgt2 = len(code)
            code[pos2] = tgt2 & 0xFF
            code[pos2 + 1] = tgt2 >> 8
        elif k in ('SETF', 'CLRF'):
            code.append(OP[k])
            code.extend([o.args[0] & 0xFF, o.args[0] >> 8])
        elif k == 'WARP':
            m, x, y, d = o.args
            if m not in MAP_BY_NAME:
                raise ValueError('script %s warps to unknown map %s' % (name, m))
            code.extend([OP['WARP'], MAPS.index(MAP_BY_NAME[m]), x, y, d])
        elif k == 'MUSIC':
            m = o.args[0]
            code.extend([OP['MUSIC'], 0xFF if m is None else MUSIC[m]])
        elif k == 'UNLOCK':
            code.extend([OP['UNLOCK'], MUSIC[o.args[0]]])
        elif k == 'IMAGE':
            code.extend([OP['IMAGE'], IMAGES[o.args[0]]])
        elif k in ('AMOVE', 'AHIDE', 'ASHOW', 'AFACE', 'AWARP'):
            who = o.args[0]
            m = MAP_BY_NAME[mapname] if mapname else None
            if m is None or who not in m.names:
                raise ValueError('script %s: unknown actor %s (map %s)' % (name, who, mapname))
            code.extend([OP[k], m.names[who]] + list(o.args[1:]))
        elif k == 'SETTILE':
            x, y, ch = o.args
            m = MAP_BY_NAME[mapname]
            code.extend([OP['SETTILE'], x, y, TILE_LEGENDS[m.ts][ch][0]])
        elif k == 'CALL':
            fixups.append((len(code) + 1, o.args[0]))
            code.extend([OP['CALL'], 0, 0])
        else:
            code.append(OP[k])
            for a in o.args:
                code.append(a & 0xFF)
    for o in ops:
        emit(o)
    code.append(OP['END'])
    return code, fixups


def resolve_script(ref):
    if ref == 0xFFFF:
        return 0xFFFF
    return SCRIPT_ID[ref]


def build(pk, hdr, dirs_c, legends, palsets, music_ids, sheets, images, tileset_ids):
    TILE_LEGENDS.update(legends)
    PALSETS.update(palsets)
    MUSIC.update(music_ids)
    SHEETS.update(sheets)
    IMAGES.update(images)
    TILESET_ID.update(tileset_ids)
    report = []
    # --- scripts
    script_blobs = []
    for idx, (name, ops, mapname) in enumerate(SCRIPTS):
        code, fx = compile_script(name, ops, mapname)
        script_blobs.append((code, fx))
    for idx, (code, fx) in enumerate(script_blobs):
        for pos, ref in fx:
            sid = SCRIPT_ID[ref]
            code[pos] = sid & 0xFF
            code[pos + 1] = sid >> 8
        pk.blob('scr_%d' % idx, bytes(code), group=None)
    dirs = 'const far_t script_dir[%d] = {\n' % len(SCRIPTS)
    for idx in range(len(SCRIPTS)):
        dirs += '  { scr_%d_BANK, scr_%d },\n' % (idx, idx)
    dirs += '};\n'
    pk.ccode('script_dir', dirs, len(SCRIPTS) * 3, group='scriptdir')
    hdr.append('extern const far_t script_dir[%d];' % len(SCRIPTS))
    hdr.append('#define NUM_SCRIPTS %d' % len(SCRIPTS))

    # --- maps
    for mi, m in enumerate(MAPS):
        leg = legends[m.ts]
        grid = []
        for y, r in enumerate(m.rows):
            for x, ch in enumerate(r):
                if ch not in leg:
                    raise ValueError('map %s: unknown tile %r at %d,%d' % (m.name, ch, x, y))
                grid.append(leg[ch][0])
        ex = []
        for e in m.exits:
            if e is None:
                ex.append(0xFF)
            else:
                if e not in MAP_BY_NAME:
                    raise ValueError('map %s exit to unknown %s' % (m.name, e))
                ex.append(MAPS.index(MAP_BY_NAME[e]))
        es = resolve_script(m.enter) if m.enter else 0xFFFF
        assert len(m.warps) <= 16 and len(m.objs) <= 48 and len(m.patches) <= 120, m.name
        blob = [m.w, m.h, tileset_ids[m.ts], palsets[m.pal], 0xFF if m.music is None else music_ids[m.music],
                m.district, m.flags] + ex + [es & 0xFF, es >> 8, len(m.warps), len(m.objs), len(m.patches)]
        blob += grid
        for (x, y, dest, dx, dy, dd, cond, lock) in m.warps:
            if dest not in MAP_BY_NAME:
                raise ValueError('map %s warp to unknown %s' % (m.name, dest))
            dm = MAP_BY_NAME[dest]
            c = obj_cond(cond)
            ls = resolve_script(lock)
            blob += [x, y, MAPS.index(dm), dx, dy, dd, c & 0xFF, c >> 8, ls & 0xFF, ls >> 8]
        for (typ, x, y, a, b, c, cond, script) in m.objs:
            if typ == 1:
                a = sheets[a]
            cc = obj_cond(cond)
            sc = resolve_script(script)
            blob += [typ, x, y, a, b, c, cc & 0xFF, cc >> 8, sc & 0xFF, sc >> 8]
        for (x, y, ch, cond) in m.patches:
            cc = obj_cond(cond)
            blob += [x, y, leg[ch][0], cc & 0xFF, cc >> 8]
        pk.blob('map_%d' % mi, bytes(blob))
        hdr.append('#define MAP_%s %d' % (m.name.upper(), mi))
    dirs_c.append('const far_t map_dir[%d] = {' % len(MAPS))
    for mi in range(len(MAPS)):
        dirs_c.append('  { map_%d_BANK, map_%d },' % (mi, mi))
    dirs_c.append('};')
    # map names for the city map / debugging
    hdr.append('#define NUM_MAPS %d' % len(MAPS))
    hdr.append('#define NUM_FLAGS %d' % len(FLAGS))
    for n, i in FLAGS.items():
        if not n.startswith('_'):
            hdr.append('#define F_%s %d' % (n.upper(), i))
    for n, i in VARS.items():
        hdr.append('#define V_%s %d' % (n.upper(), i))
    for n, i in SPECIALS.items():
        hdr.append('#define SP_%s %d' % (n.upper(), i))
    for i, it in enumerate(ITEMS):
        hdr.append('#define IT_%s %d' % (it[0].upper(), i))
    for i, e in enumerate(EVIDENCE):
        hdr.append('#define EV_%s %d' % (e[0].upper(), i))
    hdr.append('#define NUM_ITEMS %d' % len(ITEMS))
    hdr.append('#define NUM_EVIDENCE %d' % len(EVIDENCE))
    for n in SCRIPT_ID:
        if not n.startswith('_'):
            hdr.append('#define SCR_%s %d' % (n.upper(), SCRIPT_ID[n]))
    # item & evidence texts (wrapped for menus: 18 cols x 4 rows pages)
    txt = b''
    offs = []
    for it in ITEMS:
        offs.append(len(txt))
        txt += it[1].encode() + b'\0' + _text(it[2])
    for e in EVIDENCE:
        offs.append(len(txt))
        txt += e[1].encode() + b'\0' + _text(e[2])
    pk.blob('menu_text', txt, group='menutext')
    ob = b''.join(bytes([o & 0xFF, o >> 8]) for o in offs)
    pk.blob('menu_text_offs', ob, group='menutext')
    report.append('%d maps, %d scripts, %d flags, %d vars, %d evidence' %
                  (len(MAPS), len(SCRIPTS), len(FLAGS), len(VARS), len(EVIDENCE)))
    return report
