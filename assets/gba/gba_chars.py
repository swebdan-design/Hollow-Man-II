"""GBA character sprites: 16x32, light from top-left, automatic 1px outline.
Templates are drawn WITHOUT outline using material letters; build() maps letters to
colours, applies patterns (tweed herringbone) and adds the outline.

Letters: M/m/n mask (base/shade/knit highlight)  S/s skin  E eye white  e pupil  L mouth
         H/h/j hair  C/c/d clothes (mid/shade/light)  W/w shirt  T tie  P/p trousers
         F/f shoes  A/a accent  G glove/hand(skin)  O glow (eyes of the supernatural)
Frames: 0 down, 1 down-walkA, 2 down-walkB, 3 up, 4 up-walkA, 5 up-walkB,
        6 side(right), 7 side-walkA, 8 side-walkB, [player: 9 atk-down, 10 atk-up, 11 atk-side]
"""
from gba_art import Canvas, hx

# ------------------------------------------------------------------ heads (rows 3..15)
HEAD = {}
HEAD['mask'] = {
    'down': ["......mMMm......",
             ".....mMnMnMm....",
             "....mMnMMnMMm...",
             "....MnMMMMnMM...",
             "...mMMMnMMMMMm..",
             "...MMsEeMMeEsM..",
             "...mMssMMMMssMm.",
             "...MMMMMnMMMMM..",
             "...mMMMLLMMMMm..",
             "....MMnMMMnMM...",
             ".....mMMMMMm....",
             "......mMMMm.....",
             "......wWWWw....."],
    'up': ["......mMMm......",
           ".....mMnMnMm....",
           "....mMnMMnMMm...",
           "....MnMMnMMnM...",
           "...mMMnMMMnMMm..",
           "...MnMMMnMMMnM..",
           "...mMMnMMMnMMm..",
           "...MMnMMnMMnMM..",
           "...mMMMnMMMMMm..",
           "....MMnMMnMMM...",
           ".....mMMMMMm....",
           "......mMMMm.....",
           "......CCCCC....."],
    'side': [".....mMMMm......",
             "....mMnMnMMm....",
             "...mMnMMnMMMm...",
             "...MnMMMMnMMM...",
             "...mMMnMMMMMMm..",
             "...MMMMMMMsEeM..",
             "...mMnMMMMssMM..",
             "...MMMMnMMMMMMm.",
             "...mMMMMMMMMLM..",
             "....MMnMMMMMM...",
             ".....mMMMMMm....",
             "......mMMMm.....",
             "......CwWW......"],
}
HEAD['short'] = {
    'down': ["......hHHh......",
             ".....hHjjHh.....",
             "....hHjHHjHHh...",
             "....HHHHHHHHH...",
             "...hHSSSSSSSHh..",
             "...HSSEeSeESSH..",
             "...sSSSSSSSSSs..",
             "...sSSSSsSSSSs..",
             "....SSSLLSSSS...",
             ".....sSSSSSs....",
             "......sSSSs.....",
             "......sSSSs.....",
             "......wWWWw....."],
    'up': ["......hHHh......",
           ".....hHjjHh.....",
           "....hHjHHjHHh...",
           "....HHHHHHHHH...",
           "...hHHjHHHjHHh..",
           "...HHHHHHHHHHH..",
           "...hHHHHHHHHHh..",
           "...sHHHHHHHHHs..",
           "....SHHHHHHHS...",
           ".....sSSSSSs....",
           "......sSSSs.....",
           "......sSSSs.....",
           "......CCCCC....."],
    'side': [".....hHHHh......",
             "....hHjjHHh.....",
             "...hHjHHHHHh....",
             "...HHHHHHHHHH...",
             "...hHHHSSSSSSs..",
             "...HHHSSSSEeS...",
             "...hHHSSSSSSSs..",
             "...HHSSSSSSSSSS.",
             "...sHSSSSSSLSs..",
             "....sSSSSSSSS...",
             ".....sSSSSSs....",
             "......sSSSs.....",
             "......CwWW......"],
}


def _sub(rows, a, b):
    return [r.replace(a, b) for r in rows]


def _head_variant(base, fn):
    return {d: fn(d, list(base[d])) for d in base}


def _long(d, rows):
    out = []
    for i, r in enumerate(rows):
        r = list(r)
        if 3 <= i <= 12:
            if d == 'down':
                for x in (2, 3):
                    r[x] = 'H' if x == 3 else 'h'
                for x in (12, 13):
                    r[x] = 'H' if x == 12 else 'h'
            elif d == 'up':
                r = list("..hH" + "".join(r[4:12]).replace('S', 'H').replace('s', 'h') + "Hh..")
            else:
                r[2] = 'h'; r[3] = 'H'; r[4] = 'H'
        out.append(''.join(r))
    return out


HEAD['long'] = _head_variant(HEAD['short'], _long)
HEAD['bald'] = {d: _sub(_sub(_sub(HEAD['short'][d], 'H', 'S'), 'h', 's'), 'j', 'S') for d in HEAD['short']}
for d in ('down', 'side'):
    HEAD['bald'][d] = [r.replace('S', 'S') for r in HEAD['bald'][d]]


def _cap(d, rows):
    rows = list(rows)
    rows[0] = rows[0].replace('h', 'y').replace('H', 'Y')
    rows[1] = rows[1].replace('h', 'y').replace('H', 'Y').replace('j', 'Y')
    rows[2] = rows[2].replace('h', 'y').replace('H', 'Y').replace('j', 'Y')
    if d == 'side':
        rows[3] = "...yyyyyyyyyyyy."
    else:
        rows[3] = "...yyyyyyyyyyy.."
    return rows


HEAD['cap'] = _head_variant(HEAD['short'], _cap)


def _hardhat(d, rows):
    rows = list(rows)
    rows[0] = rows[0].replace('h', 'Y').replace('H', 'Y')
    rows[1] = rows[1].replace('h', 'Y').replace('H', 'Y').replace('j', 'Y')
    rows[2] = rows[2].replace('h', 'Y').replace('H', 'Y').replace('j', 'Y')
    rows[3] = "..yYYYYYYYYYYy.." if d != 'side' else "..yYYYYYYYYYYYy."
    return rows


HEAD['hardhat'] = _head_variant(HEAD['short'], _hardhat)


def _glasses(d, rows):
    rows = list(rows)
    if d == 'down':
        rows[5] = "...HSaEaaaEaSH.."
    elif d == 'side':
        rows[5] = "...HHHSSSaEaS..."
    return rows


HEAD['glasses'] = _head_variant(HEAD['short'], _glasses)


def _hood(d, rows):
    out = []
    for i, r in enumerate(rows):
        r = r.replace('H', 'C').replace('h', 'c').replace('j', 'd')
        r = r.replace('S', 'm').replace('s', 'm').replace('L', 'm')
        r = r.replace('E', 'O').replace('e', 'O')
        out.append(r)
    return out


HEAD['hood'] = _head_variant(HEAD['short'], _hood)

# ------------------------------------------------------------------ bodies (rows 16..31)
BODY = {}
BODY['suit'] = {
    'down': ["....dCWTWCc.....",
             "...dCCWTWCCc....",
             "..ddCCdTWCCcc...",
             "..dCdCCTCCCcc...",
             "..dCdCCTCCCcc...",
             "..dCdCCCCCCcc...",
             "..dCdCCCCCCcc...",
             "..GGdCCCCCCcGG..",
             "....PPPPPPPP....",
             "....PPPpPPPp....",
             "....PPPpPPPp....",
             "....PPPpPPPp....",
             "....PPPpPPPp....",
             "...FFFfp.FFFf...",
             "................",
             "................"],
    'up': ["....dCCCCCc.....",
           "...dCCCCCCCc....",
           "..ddCCCCCCCcc...",
           "..dCdCCCCCCcc...",
           "..dCdCCcCCCcc...",
           "..dCdCCcCCCcc...",
           "..dCdCCcCCCcc...",
           "..GGdCCCCCCcGG..",
           "....PPPPPPPP....",
           "....PPPpPPPp....",
           "....PPPpPPPp....",
           "....PPPpPPPp....",
           "....PPPpPPPp....",
           "...FFFf..FFFf...",
           "................",
           "................"],
    'side': [".....dCWWT......",
             ".....dCCWT......",
             ".....dCCCTc.....",
             ".....dCdCCc.....",
             ".....dCdCCc.....",
             ".....dCdCCc.....",
             ".....dCdCCc.....",
             ".....dCGCCc.....",
             ".....PPPPPp.....",
             ".....PPPPPp.....",
             ".....PPPPPp.....",
             ".....PPPPPp.....",
             ".....PPPPPp.....",
             ".....FFFFFFf....",
             "................",
             "................"],
}


def _jacket(d, rows):
    rows = [r.replace('T', 'W') for r in rows]
    return rows


def _coat(d, rows):
    rows = list(rows)
    for i in range(8, 12):
        rows[i] = rows[i].replace('P', 'C').replace('p', 'c')
    return rows


def _uniform(d, rows):
    rows = list(rows)
    if d == 'down':
        rows[2] = "..ddCAdTWCCcc..."
        rows[7] = "..GGaaaaaaaaGG.."
    elif d == 'side':
        rows[2] = ".....dCACTc....."
        rows[7] = ".....aaGaaa....."
    return rows


BODY['jacket'] = {d: _jacket(d, BODY['suit'][d]) for d in BODY['suit']}
BODY['coat'] = {d: _coat(d, BODY['jacket'][d]) for d in BODY['suit']}
BODY['uniform'] = {d: _uniform(d, BODY['suit'][d]) for d in BODY['suit']}
BODY['fat'] = {
    'down': ["...dCCWWCCc.....",
             "..dCCCWWWCCcc...",
             ".ddCCCCWWCCCcc..",
             ".dCdCCCCCCCCcc..",
             ".dCdCCCCCCCCcc..",
             ".dCdCCCCCCCCcc..",
             ".dCdCCCCCCCCcc..",
             ".GGdCCCCCCCCcGG.",
             "...PPPPPPPPPP...",
             "...PPPPpPPPPp...",
             "...PPPPpPPPPp...",
             "...PPPPpPPPPp...",
             "....PPPpPPPp....",
             "...FFFFf.FFFFf..",
             "................",
             "................"],
    'up': ["...dCCCCCCc.....",
           "..dCCCCCCCCcc...",
           ".ddCCCCCCCCCcc..",
           ".dCdCCCCCCCCcc..",
           ".dCdCCCCCCCCcc..",
           ".dCdCCCCCCCCcc..",
           ".dCdCCCCCCCCcc..",
           ".GGdCCCCCCCCcGG.",
           "...PPPPPPPPPP...",
           "...PPPPpPPPPp...",
           "...PPPPpPPPPp...",
           "...PPPPpPPPPp...",
           "....PPPpPPPp....",
           "...FFFFf.FFFFf..",
           "................",
           "................"],
    'side': ["....dCCCWW......",
             "...dCCCCWWW.....",
             "...dCCCCCWWc....",
             "...dCdCCCCCc....",
             "...dCdCCCCCCc...",
             "...dCdCCCCCCc...",
             "...dCdCCCCCc....",
             "...dCCGCCCCc....",
             "....PPPPPPPp....",
             "....PPPPPPPp....",
             "....PPPPPPPp....",
             "....PPPPPPPp....",
             ".....PPPPPp.....",
             ".....FFFFFFFf...",
             "................",
             "................"],
}


def _apron(d, rows):
    rows = list(rows)
    if d != 'up':
        for i in range(1, 12):
            r = list(rows[i])
            lo, hi = (5, 10) if d == 'down' else (8, 11)
            for x in range(lo, hi + 1):
                if r[x] in 'CcdWwP':
                    r[x] = 'A' if (x + i) % 5 else 'a'
            rows[i] = ''.join(r)
    return rows


BODY['apron'] = {d: _apron(d, BODY['fat'][d]) for d in BODY['fat']}


def _robe(d, rows):
    rows = list(rows)
    for i in range(8, 13):
        rows[i] = rows[i].replace('P', 'C').replace('p', 'c')
    if d == 'down' or d == 'up':
        rows[12] = "...cCCCCCCCCc..."
        rows[13] = "...cccccccccc..."
    else:
        rows[12] = "....cCCCCCCc...."
        rows[13] = "....ccccccccc..."
    return rows


BODY['robe'] = {d: _robe(d, BODY['jacket'][d]) for d in BODY['suit']}

# side walking legs (rows 24..29 replaced)
SIDE_WALK = [
    [".....PPPPPp.....",
     ".....PPpPPp.....",
     "....PPp..PPp....",
     "...PPp....PPp...",
     "..FFFf....FFFFf.",
     "................"],
    [".....PPPPPp.....",
     ".....PPPPPp.....",
     ".....PPPPp......",
     "......PPPp......",
     "......FFFFf.....",
     "................"],
]

# ------------------------------------------------------------------ characters
def P(**kw):
    return {k: hx(v) if isinstance(v, str) else v for k, v in kw.items()}


SKIN = dict(S='c69a78', s='9a6e52', L='6e3a32', E='e8e2d6', e='1a1214', G='c69a78')
SKIN_D = dict(S='8a5e44', s='5e3c2a', L='4a2420', E='e8e2d6', e='1a1214', G='8a5e44')


def style(base, **over):
    d = dict(base)
    d.update(over)
    return P(**d)


CHARS = {
    # Hollow Man: brown herringbone tweed, cream shirt, oxblood tie, knitted black balaclava
    'hollow': ('mask', 'suit', style(SKIN, M='26262e', m='15151a', n='4a4a5a', C='6e4a2e', c='4a301d',
                                     d='94683f', x='3a2414', W='e6dcc0', w='a69a80', T='5a1418',
                                     P='5a3c24', p='3a2414', F='141418', f='3a3a44', K='0a0a0d'),
               True),
    'bell': ('long', 'coat', style(SKIN, H='6e2e1a', h='461a10', j='9a4a2a', C='a07848', c='705030',
                                   d='c8a070', W='e6dcc0', w='a69a80', P='3a3030', p='241e1e', F='2a1a14',
                                   f='5a4030', K='140e0c'), False),
    'thug': ('short', 'jacket', style(SKIN, H='1e1a18', h='0e0c0c', j='3a3430', C='3c3e44', c='26282c',
                                      d='5a5e66', W='8a8478', w='5a564e', P='262a36', p='16181e', F='101012',
                                      f='3a3a40', K='08080a'), False),
    'runner': ('bald', 'jacket', style(SKIN_D, C='5a3a5a', c='3a2440', d='7a5a7a', W='c0b49a', w='8a7e66',
                                       P='22222a', p='141418', F='d0d0d0', f='8a8a8a', K='0a080a'), False),
    'gunman': ('cap', 'suit', style(SKIN, y='1a1a20', Y='2a2a32', C='2c2c34', c='1a1a20', d='44444e',
                                    W='a8a49a', w='6a665e', T='1a1a20', P='22222a', p='141418', F='0e0e10',
                                    f='34343a', K='060608'), False),
    'police': ('cap', 'uniform', style(SKIN, y='0e1224', Y='1c2442', a='141a2e', A='d8b850', C='26304e', c='182036', d='3a4a72',
                                       W='a8b0c0', w='6a7080', T='141a2e', P='1c2438', p='10141e', F='0c0c10',
                                       f='3a3a44', K='06060a'), False),
    'oldwoman': ('long', 'coat', style(SKIN, H='9a968e', h='6a665e', j='c8c4ba', C='5a4a5e', c='3a2e3e',
                                       d='7a6a7e', W='c8bca0', w='8a8068', P='3a3030', p='241e1e', F='2a1a14',
                                       f='4a3a30', K='100c0e'), False),
    'oldman': ('bald', 'coat', style(SKIN, C='5e5a46', c='3e3a2c', d='7e7a5e', W='c0b49a', w='8a7e66',
                                     P='3a3428', p='26221a', F='2a1a14', f='4a3a30', K='0e0c0a'), False),
    'citizen': ('short', 'coat', style(SKIN, H='4a3020', h='2e1c12', j='6e4a30', C='3e5a5a', c='284040',
                                       d='5a7a7a', W='d0c8b0', w='8a8470', P='2e2a28', p='1e1a18', F='1a1210',
                                       f='3a2a20', K='0a0a0a'), False),
    'vagrant': ('long', 'jacket', style(SKIN_D, H='5a5040', h='3a3428', j='7a6e58', C='4a4a2e', c='30301c',
                                        d='6a6a44', W='7a7060', w='4e463a', P='3a3428', p='26221a', F='1e1612',
                                        f='3a2e24', K='0a0a08'), False),
    'clerk': ('glasses', 'jacket', style(SKIN, H='2e2018', h='1a120e', j='4a3426', a='101014', C='6a6a5a',
                                         c='48483c', d='8a8a78', W='e0d8c4', w='a09a88', P='34302a', p='221e1a',
                                         F='1a1410', f='3a2e24', K='0a0a08'), False),
    'priest': ('bald', 'robe', style(SKIN_D, C='1e1e24', c='121216', d='34343e', W='e8e4dc', w='a8a49a',
                                     F='0e0e10', f='2a2a30', K='050506'), False),
    'eddie': ('bald', 'fat', style(SKIN, C='6a5a3a', c='4a3e26', d='8a7a52', W='d8ccb0', w='9a9078',
                                   P='3a3226', p='26201a', F='1e1612', f='3a2e24', K='0a0806'), False),
    'hector': ('bald', 'apron', style(SKIN, C='4a4a52', c='303036', d='66666e', A='d8d0c0', a='8a1a1e',
                                      W='d8d0c0', w='9a9488', P='2a2a30', p='1a1a1e', F='141416', f='34343a',
                                      K='08080a'), False),
    'nolan': ('short', 'jacket', style(SKIN, H='8a6a3a', h='5e4626', j='b08a50', C='6e2a2a', c='4a1a1a',
                                       d='8e4040', W='d8d0c0', w='9a9488', P='2a2e3a', p='1a1e28', F='e0e0e0',
                                       f='9a9a9a', K='0a0606'), False),
    'dacre': ('cap', 'uniform', style(SKIN, y='0e1224', Y='1c2442', a='141a2e', A='d8b850', C='2a2a44', c='1a1a2e', d='40406a',
                                      W='a8b0c0', w='6a7080', T='141a2e', P='1c1c30', p='10101e', F='0c0c10',
                                      f='3a3a44', K='06060a'), False),
    'mott': ('hardhat', 'jacket', style(SKIN, y='8a6a10', Y='e0b030', H='2a2018', h='1a140e', j='4a3a2a',
                                        C='3a5a3a', c='243c24', d='5a7a5a', W='e09040', w='a06020', P='2e3a4a',
                                        p='1e2632', F='2a1a10', f='4a3424', K='080a08'), False),
    'crewe': ('glasses', 'suit', style(SKIN, H='9a9a9a', h='6a6a6a', j='c8c8c8', a='181818', C='3a3a44',
                                       c='26262e', d='54545e', W='e8e4dc', w='a8a49a', T='6a1a1a', P='2c2c34',
                                       p='1c1c22', F='0e0e10', f='34343a', K='060608'), False),
    'rusk': ('short', 'robe', style(SKIN, H='e8e8e8', h='b0b0b0', j='ffffff', C='d8d8d0', c='a0a098',
                                    d='f4f4ee', W='ffffff', w='c0c0b8', F='3a3a3a', f='6a6a6a', K='1a1a1a'), False),
    'wraith': ('hood', 'robe', style(SKIN, C='2a2232', c='181420', d='3e3448', M='050406', m='050406',
                                     O='ff3030', W='2a2232', w='181420', F='0a080c', f='181420', G='3e3448',
                                     K='020203'), False),
    'nurse': ('short', 'robe', style(SKIN, H='3a2a20', h='241a12', j='5a4030', C='c8ccc0', c='989c90',
                                     d='e8ece0', W='ffffff', w='c0c0b8', F='d8d8d8', f='9a9a9a', K='1a1a1a'), False),
}

ORDER = ['bell', 'thug', 'runner', 'gunman', 'police', 'oldwoman', 'oldman', 'citizen', 'vagrant',
         'clerk', 'priest', 'eddie', 'hector', 'nolan', 'dacre', 'mott', 'crewe', 'rusk', 'wraith',
         'nurse', 'hollow']


def _grid(head, body, d):
    rows = ["................"] * 3 + HEAD[head][d] + BODY[body][d]
    assert len(rows) == 32, (head, body, d, len(rows))
    for r in rows:
        assert len(r) == 16, (head, body, d, r)
    return [list(r) for r in rows]


def _walk_down(g, phase):
    """phase 1: left leg lifted, 2: right leg lifted (shift leg+shoe columns up 1 row)"""
    g = [r[:] for r in g]
    cols = range(0, 8) if phase == 1 else range(8, 16)
    for x in cols:
        for y in range(25, 31):
            g[y - 1][x] = g[y][x] if g[y][x] != '.' or y > 25 else g[y - 1][x]
        g[30][x] = '.'
    # arm swing: opposite hand drops 1px
    hx_ = (12, 13) if phase == 1 else (2, 3)
    for x in hx_:
        if g[23][x] == 'G':
            g[24][x] = 'G'
            g[23][x] = 'c'
    return g


def _walk_side(g, phase, robe=False):
    g = [r[:] for r in g]
    legs = SIDE_WALK[phase - 1]
    if robe:
        legs = [r.replace('P', 'C').replace('p', 'c') for r in legs]
    for i, r in enumerate(legs):
        g[24 + i + 1] = list(r) if i else g[24 + i + 1]
    for i, r in enumerate(legs):
        g[25 + i] = list(r)
    return g


def _attack(g, d):
    g = [r[:] for r in g]
    if d == 'down':
        for x in (2, 3, 12, 13):
            g[23][x] = '.'
        for x in (6, 7, 8, 9):
            g[24][x] = 'G'
    elif d == 'up':
        for x in (2, 3, 12, 13):
            g[23][x] = '.'
        g[16][3] = 'G'; g[16][12] = 'G'; g[17][3] = 'G'; g[17][12] = 'G'
    else:
        g[23][7] = 'c'
        for x in (11, 12, 13, 14):
            g[20][x] = 'C' if x < 13 else 'G'
        g[21][11] = 'c'
    return g


def render(name, grid, cmap, tweed):
    K = cmap.get('K', hx('0a0a0a'))
    c = Canvas(16, 32, (255, 0, 255))
    for y, r in enumerate(grid):
        for x, ch in enumerate(r):
            if ch == '.':
                continue
            col = cmap.get(ch)
            if col is None:
                col = cmap.get(ch.upper(), K)
            if tweed and ch == 'C':
                # herringbone: chevron of darker threads
                k = (x + (y % 4 if (y // 4) % 2 == 0 else 3 - y % 4)) % 3
                if k == 0:
                    col = cmap['x']
                elif (x * 7 + y * 3) % 11 == 0:
                    col = cmap['d']
            c.set(x, y, col)
    # automatic outline
    key = (255, 0, 255)
    out = c.copy()
    for y in range(32):
        for x in range(16):
            if c.get(x, y) != key:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                xx, yy = x + dx, y + dy
                if 0 <= xx < 16 and 0 <= yy < 32 and c.get(xx, yy) != key:
                    out.set(x, y, K)
                    break
    return out


def frames(name):
    head, body, cmap, tweed = CHARS[name]
    out = []
    for d in ('down', 'up', 'side'):
        g = _grid(head, body, d)
        if d == 'side':
            seq = [g, _walk_side(g, 1, body == 'robe'), _walk_side(g, 2, body == 'robe')]
        else:
            seq = [g, _walk_down(g, 1), _walk_down(g, 2)]
        out += [render(name, s, cmap, tweed) for s in seq]
    if name == 'hollow':
        for d in ('down', 'up', 'side'):
            out.append(render(name, _attack(_grid(head, body, d), d), cmap, tweed))
    return out
