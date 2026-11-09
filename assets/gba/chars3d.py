"""Pre-rendered 3D characters for the GBA version (rendered with tools/render3d.py).
Each character is a parametric model: head style, body style, colours. Frames are 32x64:
dir down/up/side x 4-frame walk cycle (+ 3 attack poses for Hollow Man)."""
import math
import numpy as np
import render3d as R3
from render3d import V, Prim

SKIN = (198, 150, 118)
SKIN_D = (138, 92, 66)

CHARS = {
    'hollow': dict(head='mask', body='suit', skin=SKIN, suit=(112, 74, 46), tweed=True, shirt=(232, 222, 196),
                   tie=(92, 22, 26), pants=(92, 62, 38), shoes=(22, 20, 24), mask=(30, 30, 36), mask_hi=(92, 92, 108)),
    'bell': dict(head='long', body='coat', skin=SKIN, hair=(112, 46, 26), suit=(168, 124, 76), shirt=(230, 220, 196),
                 pants=(60, 50, 50), shoes=(44, 28, 20)),
    'thug': dict(head='short', body='jacket', skin=SKIN, hair=(28, 24, 22), suit=(62, 64, 70), shirt=(140, 134, 120),
                 pants=(38, 42, 56), shoes=(16, 16, 18)),
    'runner': dict(head='bald', body='jacket', skin=SKIN_D, suit=(92, 58, 92), shirt=(196, 182, 154),
                   pants=(34, 34, 42), shoes=(210, 210, 210)),
    'gunman': dict(head='cap', body='suit', skin=SKIN, hat=(40, 40, 48), suit=(44, 44, 52), shirt=(168, 164, 154),
                   tie=(26, 26, 32), pants=(34, 34, 42), shoes=(14, 14, 16)),
    'police': dict(head='cap', body='uniform', skin=SKIN, hat=(28, 36, 66), suit=(38, 48, 78), shirt=(168, 176, 192),
                   tie=(20, 26, 46), pants=(28, 36, 56), shoes=(12, 12, 16), accent=(216, 184, 80)),
    'oldwoman': dict(head='long', body='coat', skin=SKIN, hair=(160, 156, 148), suit=(90, 74, 94), shirt=(200, 188, 160),
                     pants=(58, 48, 48), shoes=(42, 28, 20)),
    'oldman': dict(head='bald', body='coat', skin=SKIN, suit=(94, 90, 70), shirt=(192, 180, 154), pants=(58, 52, 40),
                   shoes=(42, 28, 20)),
    'citizen': dict(head='short', body='coat', skin=SKIN, hair=(74, 48, 32), suit=(62, 90, 90), shirt=(208, 200, 176),
                    pants=(46, 42, 40), shoes=(26, 18, 16)),
    'vagrant': dict(head='long', body='jacket', skin=SKIN_D, hair=(90, 80, 64), suit=(74, 74, 46), shirt=(122, 112, 96),
                    pants=(58, 52, 40), shoes=(30, 22, 18)),
    'clerk': dict(head='glasses', body='jacket', skin=SKIN, hair=(46, 32, 24), suit=(106, 106, 90), shirt=(224, 216, 196),
                  pants=(52, 48, 42), shoes=(26, 20, 16)),
    'priest': dict(head='bald', body='robe', skin=SKIN_D, suit=(30, 30, 36), shirt=(232, 228, 220), shoes=(14, 14, 16)),
    'eddie': dict(head='bald', body='fat', skin=SKIN, suit=(106, 90, 58), shirt=(216, 204, 176), pants=(58, 50, 38),
                  shoes=(30, 22, 18)),
    'hector': dict(head='bald', body='apron', skin=SKIN, suit=(74, 74, 82), shirt=(216, 208, 192), pants=(42, 42, 48),
                   shoes=(20, 20, 22), accent=(220, 212, 196), blood=(138, 26, 30)),
    'nolan': dict(head='short', body='jacket', skin=SKIN, hair=(138, 106, 58), suit=(110, 42, 42), shirt=(216, 208, 192),
                  pants=(42, 46, 58), shoes=(224, 224, 224)),
    'dacre': dict(head='cap', body='uniform', skin=SKIN, hat=(30, 30, 56), suit=(42, 42, 68), shirt=(168, 176, 192),
                  tie=(20, 26, 46), pants=(28, 28, 48), shoes=(12, 12, 16), accent=(216, 184, 80)),
    'mott': dict(head='hardhat', body='jacket', skin=SKIN, hair=(42, 32, 24), hat=(224, 176, 48), suit=(58, 90, 58),
                 shirt=(224, 144, 64), pants=(46, 58, 74), shoes=(42, 26, 16)),
    'crewe': dict(head='glasses', body='suit', skin=SKIN, hair=(154, 154, 154), suit=(58, 58, 68), shirt=(232, 228, 220),
                  tie=(106, 26, 26), pants=(44, 44, 52), shoes=(14, 14, 16)),
    'rusk': dict(head='short', body='robe', skin=SKIN, hair=(232, 232, 232), suit=(216, 216, 208), shirt=(255, 255, 255),
                 shoes=(58, 58, 58)),
    'wraith': dict(head='hood', body='robe', skin=(10, 8, 12), suit=(42, 34, 50), shirt=(42, 34, 50), shoes=(10, 8, 12),
                   glow=(255, 48, 48)),
    'nurse': dict(head='short', body='robe', skin=SKIN, hair=(58, 42, 32), suit=(200, 204, 192), shirt=(255, 255, 255),
                  shoes=(216, 216, 216)),
}
ORDER = ['bell', 'thug', 'runner', 'gunman', 'police', 'oldwoman', 'oldman', 'citizen', 'vagrant', 'clerk', 'priest',
         'eddie', 'hector', 'nolan', 'dacre', 'mott', 'crewe', 'rusk', 'wraith', 'nurse', 'hollow']

M_SKIN, M_SUIT, M_SHIRT, M_TIE, M_PANTS, M_SHOES, M_HEAD, M_ACC, M_DARK, M_WHITE, M_HAT, M_GLOW, M_BLOOD = range(1, 14)


def leg_point(hip, ang, length):
    return hip + V(0, -math.cos(ang), math.sin(ang)) * length


def build(c, phase=0, attack=False):
    """returns (prims, materials) for character dict c at walk phase 0..3 (stylised proportions)"""
    swing = [0, 0.38, 0, -0.38][phase]
    bob = [0, 0.02, 0, 0.02][phase]
    fat = c['body'] in ('fat', 'apron')
    tw = 0.25 if fat else 0.19
    td = 0.15 if fat else 0.09
    P = []
    y0 = bob
    for side, s in ((-1, swing), (1, -swing)):
        hip = V(side * (0.1 if not fat else 0.12), 0.7 + y0, 0)
        knee = leg_point(hip, s, 0.33)
        ankle = leg_point(knee, s * 0.5 - (0.2 if s < 0 else 0), 0.31)
        if c['body'] != 'robe':
            P.append(Prim('cap', M_PANTS, hip, knee, 0.08, 0.068))
            P.append(Prim('cap', M_PANTS, knee, ankle, 0.068, 0.058))
        P.append(Prim('ell', M_SHOES, ankle + V(0, -0.02, 0.06), V(0.065, 0.05, 0.12)))
    ty = 0.95 + y0
    P.append(Prim('box', M_SUIT, V(0, ty, 0), V(tw - 0.06, 0.2, td), 0.06))
    if c['body'] in ('coat', 'robe'):
        hem = 0.1 if c['body'] == 'robe' else 0.38
        P.append(Prim('cap', M_SUIT, V(0, ty - 0.1, 0), V(0, hem + y0, 0.0), tw - 0.03, tw + 0.06))
    fz = td + 0.06
    if c['body'] in ('suit', 'uniform'):
        P.append(Prim('box', M_SHIRT, V(0, ty + 0.1, fz - 0.005), V(0.065, 0.11, 0.012), 0.01))
        P.append(Prim('cap', M_TIE, V(0, ty + 0.19, fz + 0.012), V(0, ty - 0.12, fz + 0.016), 0.026, 0.034))
        for sx in (-1, 1):   # lapels
            P.append(Prim('cap', M_SUIT, V(sx * 0.07, ty + 0.2, fz + 0.002), V(sx * 0.02, ty - 0.04, fz + 0.01), 0.022))
    elif c['body'] == 'jacket':
        P.append(Prim('box', M_SHIRT, V(0, ty + 0.02, fz - 0.005), V(0.075, 0.18, 0.012), 0.01))
    else:
        P.append(Prim('box', M_SHIRT, V(0, ty + 0.15, fz - 0.005), V(0.06, 0.06, 0.012), 0.01))
    if c['body'] == 'apron':
        P.append(Prim('box', M_ACC, V(0, ty - 0.08, fz), V(0.17, 0.3, 0.012), 0.02))
        P.append(Prim('sphere', M_BLOOD, V(0.06, ty - 0.02, fz + 0.01), 0.045))
        P.append(Prim('sphere', M_BLOOD, V(-0.07, ty - 0.2, fz + 0.01), 0.035))
    if c['body'] == 'uniform':
        P.append(Prim('sphere', M_ACC, V(-0.11, ty + 0.1, fz), 0.03))
        P.append(Prim('box', M_ACC, V(0, ty - 0.2, 0.0), V(tw - 0.04, 0.025, td + 0.02), 0.01))
    for side, s in ((-1, -swing), (1, swing)):
        sh = V(side * (tw + 0.03), ty + 0.16, 0)
        if attack:
            el = sh + V(-side * 0.03, -0.06, 0.2)
            ha = el + V(-side * 0.06, 0.02, 0.18)
        else:
            el = leg_point(sh, s * 0.8, 0.24) + V(side * 0.02, 0, 0)
            ha = leg_point(el, s * 0.9 + 0.1, 0.22)
        P.append(Prim('cap', M_SUIT, sh, el, 0.068, 0.058))
        P.append(Prim('cap', M_SUIT, el, ha, 0.058, 0.05))
        P.append(Prim('sphere', M_SKIN if c['head'] != 'mask' else M_DARK, ha + V(0, -0.03, 0), 0.052))
    hy = 1.4 + y0
    hr = V(0.19, 0.21, 0.19)
    head = c['head']
    P.append(Prim('cap', M_SKIN if head != 'mask' else M_HEAD, V(0, ty + 0.18, 0), V(0, hy - 0.1, 0), 0.07))
    fzh = hr[2] - 0.012
    if head == 'mask':
        P.append(Prim('ell', M_HEAD, V(0, hy, 0), hr))
        for sx in (-1, 1):
            P.append(Prim('ell', M_SKIN, V(sx * 0.075, hy + 0.015, fzh - 0.02), V(0.058, 0.036, 0.03)))
            P.append(Prim('sphere', M_WHITE, V(sx * 0.072, hy + 0.017, fzh - 0.005), 0.024))
            P.append(Prim('sphere', M_DARK, V(sx * 0.068, hy + 0.017, fzh + 0.014), 0.012))
        P.append(Prim('ell', M_SKIN, V(0, hy - 0.11, fzh - 0.025), V(0.05, 0.026, 0.03)))
    else:
        P.append(Prim('ell', M_SKIN, V(0, hy, 0), hr * 0.97))
        for sx in (-1, 1):
            P.append(Prim('sphere', M_WHITE, V(sx * 0.07, hy + 0.012, fzh - 0.01), 0.026))
            P.append(Prim('sphere', M_DARK, V(sx * 0.068, hy + 0.012, fzh + 0.008), 0.014))
        P.append(Prim('ell', M_SKIN, V(0, hy - 0.035, fzh + 0.01), V(0.026, 0.04, 0.03)))
        if head in ('short', 'long', 'glasses'):
            P.append(Prim('ell', M_HEAD, V(0, hy + 0.07, -0.03), V(0.2, 0.17, 0.2)))
        if head == 'long':
            P.append(Prim('cap', M_HEAD, V(0, hy, -0.08), V(0, hy - 0.36, -0.09), 0.18, 0.15))
        if head == 'glasses':
            for sx in (-1, 1):
                P.append(Prim('box', M_ACC, V(sx * 0.07, hy + 0.012, fzh + 0.012), V(0.045, 0.026, 0.004), 0.004))
        if head == 'cap':
            P.append(Prim('ell', M_HAT, V(0, hy + 0.11, -0.01), V(0.21, 0.11, 0.21)))
            P.append(Prim('box', M_HAT, V(0, hy + 0.08, 0.17), V(0.14, 0.01, 0.08), 0.01))
            if 'accent' in c:
                P.append(Prim('sphere', M_ACC, V(0, hy + 0.15, 0.19), 0.03))
        if head == 'hardhat':
            P.append(Prim('ell', M_HAT, V(0, hy + 0.11, 0), V(0.22, 0.14, 0.23)))
            P.append(Prim('ell', M_HAT, V(0, hy + 0.05, 0.02), V(0.27, 0.025, 0.28)))
        if head == 'hood':
            P.append(Prim('ell', M_SUIT, V(0, hy + 0.03, -0.02), V(0.24, 0.26, 0.24)))
            P.append(Prim('ell', M_DARK, V(0, hy - 0.01, 0.1), V(0.15, 0.18, 0.14)))
            for sx in (-1, 1):
                P.append(Prim('sphere', M_GLOW, V(sx * 0.06, hy + 0.01, 0.22), 0.026))
    mats = {
        M_SKIN: R3.flat(c['skin'], 0.1), M_SHIRT: R3.flat(c['shirt']), M_TIE: R3.flat(c.get('tie', (40, 40, 40)), 0.3),
        M_PANTS: R3.flat(c.get('pants', c['suit'])), M_SHOES: R3.leather(c['shoes']),
        M_DARK: R3.flat((14, 12, 14)), M_WHITE: R3.flat((236, 230, 220), 0.6),
        M_HAT: R3.flat(c.get('hat', (40, 40, 40)), 0.3), M_ACC: R3.flat(c.get('accent', (200, 200, 200)), 0.7),
        M_GLOW: R3.flat(c.get('glow', (255, 60, 60))), M_BLOOD: R3.flat(c.get('blood', (120, 20, 20)), 0.4),
    }
    mats[M_SUIT] = R3.tweed(c['suit'], tuple(int(x * .62) for x in c['suit']),
                            tuple(min(255, int(x * 1.35)) for x in c['suit'])) if c.get('tweed') else R3.flat(c['suit'], 0.05, 0.08)
    mats[M_HEAD] = R3.knit(c['mask'], c['mask_hi']) if head == 'mask' else R3.flat(c.get('hair', (40, 30, 24)), 0.15, 0.1)
    return P, mats


YAWS = {'down': 0.0, 'up': math.pi, 'side': math.pi / 2}
SS = 3                      # supersampling factor
FW, FH = 32, 64             # final frame size
SCALE = 1.0 / 28 / SS       # world units per hi-res pixel (1 unit ~ 28 px)


def render_frame(name, d, phase=0, attack=False, big=1.0):
    c = CHARS[name]
    P, mats = build(c, phase, attack)
    w, h = FW * SS, FH * SS
    rgba = R3.render(P, mats, w, h, SCALE / big, center=V(0, 0.92, 0), yaw=YAWS[d], steps=40, ambient=0.42)
    return R3.downsample(rgba, SS)


def frames(name, big=1.0):
    out = []
    for d in ('down', 'up', 'side'):
        for ph in range(4):
            out.append(render_frame(name, d, ph, big=big))
    if name == 'hollow':
        for d in ('down', 'up', 'side'):
            out.append(render_frame(name, d, 0, True))
    return out
