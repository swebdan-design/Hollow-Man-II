"""Full-colour 240x160 illustrations (title + cutscenes) for GBA mode 4.
Drawn procedurally: gradient skies, layered silhouettes, fog, rain, light cones.
The figure of Hollow Man is always placed against lit fog so the black balaclava reads."""
import math
import random
from PIL import Image, ImageDraw, ImageFilter
import gba_chars as chars

W, H = 240, 160


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def hx(h):
    h = h.lstrip('#')
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def gradient(im, top, bot, y0=0, y1=H):
    d = ImageDraw.Draw(im)
    for y in range(y0, y1):
        d.line([(0, y), (W, y)], fill=lerp(hx(top), hx(bot), (y - y0) / max(1, y1 - y0 - 1)))


def glow(im, cx, cy, r, col, strength=0.8):
    px = im.load()
    c = hx(col)
    for y in range(max(0, cy - r), min(im.size[1], cy + r)):
        for x in range(max(0, cx - r), min(im.size[0], cx + r)):
            d = math.hypot(x - cx, y - cy) / r
            if d < 1:
                t = (1 - d) ** 2 * strength
                px[x, y] = lerp(px[x, y], c, t)


def fog(im, y0, y1, col, strength, seed):
    px = im.load()
    c = hx(col)
    rnd = random.Random(seed)
    phase = [rnd.random() * 6 for _ in range(4)]
    for y in range(y0, y1):
        for x in range(W):
            n = (math.sin(x * 0.045 + phase[0] + y * 0.02) + math.sin(x * 0.11 + phase[1]) * 0.5 +
                 math.sin(y * 0.15 + phase[2] + x * 0.01)) / 2.5
            t = max(0, min(1, (0.5 + n * 0.5))) * strength * (1 - abs((y - (y0 + y1) / 2) / ((y1 - y0) / 2 + 1)))
            px[x, y] = lerp(px[x, y], c, t)


def skyline(im, base, seed, col, win, density, hmin, hmax, wmin=14, wmax=34):
    d = ImageDraw.Draw(im)
    rnd = random.Random(seed)
    x = -6
    while x < W:
        w = rnd.randint(wmin, wmax)
        h = rnd.randint(hmin, hmax)
        top = base - h
        d.rectangle([x, top, x + w, base], fill=hx(col))
        if rnd.random() < .35:
            d.rectangle([x + w // 2 - 1, top - rnd.randint(4, 12), x + w // 2 + 1, top], fill=hx(col))
        if rnd.random() < .3:
            d.polygon([(x, top), (x + w // 2, top - 8), (x + w, top)], fill=hx(col))
        for wy in range(top + 4, base - 4, 7):
            for wx in range(x + 3, x + w - 3, 6):
                if rnd.random() < density:
                    d.rectangle([wx, wy, wx + 2, wy + 3], fill=hx(rnd.choice(win)))
        x += w + rnd.randint(0, 4)


def rain(im, n, seed, col, alpha=.5):
    px = im.load()
    rnd = random.Random(seed)
    c = hx(col)
    for _ in range(n):
        x, y, l = rnd.randrange(W + 20), rnd.randrange(H), rnd.randint(4, 9)
        for i in range(l):
            xx, yy = x - i // 2, y + i
            if 0 <= xx < W and 0 <= yy < H:
                px[xx, yy] = lerp(px[xx, yy], c, alpha)


def sprite_figure(name, frame, scale):
    f = chars.frames(name)[frame].im
    f = f.resize((16 * scale, 32 * scale), Image.NEAREST)
    return f


def paste_key(im, spr, x, y, key=(255, 0, 255)):
    px, sp = im.load(), spr.load()
    for yy in range(spr.size[1]):
        for xx in range(spr.size[0]):
            c = sp[xx, yy]
            if c != key and 0 <= x + xx < W and 0 <= y + yy < im.size[1]:
                px[x + xx, y + yy] = c


def rim_light(im, spr, x, y, col, key=(255, 0, 255), side=-1):
    """add a 1-scaled-pixel rim of light on the silhouette edge facing the light"""
    px, sp = im.load(), spr.load()
    c = hx(col)
    w, h = spr.size
    for yy in range(h):
        for xx in range(w):
            if sp[xx, yy] == key:
                continue
            nx = xx + side * 3
            if 0 <= nx < w and sp[nx, yy] == key or nx < 0 or nx >= w:
                if 0 <= x + xx < W and 0 <= y + yy < H:
                    px[x + xx, y + yy] = lerp(px[x + xx, y + yy], c, .55)


def shadow_beast(w, h, body, eye, edge, seed=7):
    """the Second Shadow: horned silhouette dissolving into smoke"""
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx = w // 2
    # body / shoulders
    d.ellipse([cx - w * .36, h * .32, cx + w * .36, h * 1.1], fill=hx(body))
    d.ellipse([cx - w * .17, h * .12, cx + w * .17, h * .45], fill=hx(body))
    # horns
    for s in (-1, 1):
        pts = [(cx + s * w * .10, h * .18), (cx + s * w * .28, h * .02), (cx + s * w * .34, h * .0),
               (cx + s * w * .22, h * .12), (cx + s * w * .14, h * .26)]
        d.polygon(pts, fill=hx(body))
    # arms hanging, long fingers
    for s in (-1, 1):
        d.polygon([(cx + s * w * .30, h * .42), (cx + s * w * .46, h * .70), (cx + s * w * .44, h * .98),
                   (cx + s * w * .38, h * .98), (cx + s * w * .34, h * .72), (cx + s * w * .22, h * .5)],
                  fill=hx(body))
    # eyes
    for s in (-1, 1):
        ex, ey = cx + s * w * .065, h * .27
        d.ellipse([ex - w * .035, ey - h * .015, ex + w * .035, ey + h * .015], fill=hx(eye))
    # smoke edges
    rnd = random.Random(seed)
    px = im.load()
    for _ in range(w * h // 9):
        x, y = rnd.randrange(w), rnd.randrange(h // 3, h)
        if px[x, y][3] and rnd.random() < .5:
            for k in range(rnd.randint(1, 5)):
                yy = y + k
                if yy < h and not px[x, yy][3]:
                    px[x, yy] = hx(edge) + (255,)
    return im


def paste_rgba(im, top, x, y):
    im.paste(top.convert('RGB'), (x, y), top)


# ------------------------------------------------------------------ scenes
def title():
    im = Image.new('RGB', (W, H))
    gradient(im, '07070b', '2a1e22', 0, 110)
    gradient(im, '2a1e22', '120e10', 110, H)
    glow(im, 120, 92, 90, '6a4a3a', .55)                    # fog lit from below
    beast = shadow_beast(150, 150, '0d0a0f', 'e02828', '1c141c')
    paste_rgba(im, beast, 45, 2)
    glow(im, 110, 42, 7, 'ff4040', .5); glow(im, 130, 42, 7, 'ff4040', .5)
    skyline(im, 132, 7, '0b0a0e', ['8a6a2a', 'b8823a', '4a5a6a'], .07, 18, 52)
    fog(im, 96, 140, '8a7a6e', .55, 3)
    # streetlamp at left, its cone of light
    d = ImageDraw.Draw(im)
    d.rectangle([28, 50, 30, 136], fill=hx('15151a'))
    d.rectangle([22, 46, 37, 50], fill=hx('1c1c22'))
    glow(im, 29, 54, 46, 'f2c96b', .65)
    d.rectangle([24, 50, 35, 52], fill=hx('fff2c4'))
    # Hollow Man x3, standing in the light (rim-lit so the balaclava reads against the dark)
    fig = sprite_figure('hollow', 0, 3)
    glow(im, 120, 112, 44, 'c8a080', .45)                   # backlight behind the figure
    paste_key(im, fig, 96, 52)
    rim_light(im, fig, 96, 52, 'f2d488', side=-1)
    d.rectangle([0, 136, W, H], fill=hx('0a0809'))
    rain(im, 220, 5, '9aa0b0', .35)
    return im


def gloam():
    im = Image.new('RGB', (W, H))
    gradient(im, '06070c', '22283a', 0, 120)
    glow(im, 170, 30, 40, '3a4a6a', .4)
    skyline(im, 120, 21, '161a24', ['8a6a2a', 'b8823a'], .10, 40, 90)
    fog(im, 70, 120, '4a5468', .5, 2)
    skyline(im, 160, 22, '0a0b10', ['d8b860', 'b8823a', 'e04048'], .08, 30, 80)
    rain(im, 320, 5, 'a0a8c0', .4)
    return im


def house():
    im = Image.new('RGB', (W, H))
    gradient(im, '2e2218', '7a5e40', 0, 110)
    gradient(im, '3a2a1c', '1e140c', 110, H)
    d = ImageDraw.Draw(im)
    # the house on Mercy Street
    d.rectangle([60, 56, 180, 118], fill=hx('241a12'))
    d.polygon([(52, 58), (120, 20), (188, 58)], fill=hx('140e0a'))
    d.rectangle([150, 26, 160, 46], fill=hx('140e0a'))
    for wx in (74, 100, 146):
        d.rectangle([wx, 70, wx + 14, 88], fill=hx('0e0a08'))
    d.rectangle([120, 90, 136, 118], fill=hx('0e0a08'))
    d.rectangle([100, 70, 114, 88], fill=hx('8a1a14'))
    glow(im, 107, 79, 26, 'e04020', .6)
    d.rectangle([103, 73, 111, 85], fill=hx('ff9040'))
    for fx in range(0, W, 8):
        d.rectangle([fx, 116, fx + 3, 132], fill=hx('8a6a48'))
    d.rectangle([0, 120, W, 122], fill=hx('8a6a48'))
    d.line([(206, 120), (206, 50)], fill=hx('0e0a08'), width=4)
    d.line([(206, 70), (190, 52)], fill=hx('0e0a08'), width=2)
    d.line([(206, 64), (224, 40)], fill=hx('0e0a08'), width=2)
    fog(im, 100, 150, 'a08060', .35, 9)
    return im


def photo():
    im = Image.new('RGB', (W, H), hx('0c0a0a'))
    p = house().resize((180, 120))
    pe = Image.new('RGB', (196, 140), hx('d8c8a0'))
    # sepia
    px = p.load()
    for y in range(p.size[1]):
        for x in range(p.size[0]):
            r, g, b = px[x, y]
            l = (r * 30 + g * 59 + b * 11) // 100
            px[x, y] = (min(255, l + 40), min(255, l + 22), l)
    d = ImageDraw.Draw(p)
    for i in range(7):
        x = 22 + i * 18
        d.ellipse([x, 70, x + 7, 78], fill=(50, 36, 24))
        d.rectangle([x - 1, 78, x + 8, 102], fill=(50, 36, 24))
    x = 150
    d.rectangle([x - 2, 66, x + 10, 104], fill=(12, 8, 8))
    d.ellipse([x - 2, 58, x + 10, 70], fill=(12, 8, 8))
    d.line([(x, 61), (x - 5, 50)], fill=(12, 8, 8), width=2)
    d.line([(x + 8, 61), (x + 13, 50)], fill=(12, 8, 8), width=2)
    d.point([(x + 2, 64), (x + 6, 64)], fill=(220, 40, 40))
    pe.paste(p, (8, 8))
    im.paste(pe.rotate(-3, expand=False, fillcolor=hx('0c0a0a')), (22, 10))
    return im


def shadow_close():
    im = Image.new('RGB', (W, H))
    gradient(im, '050406', '3a0a10', 0, H)
    beast = shadow_beast(220, 230, '0a080c', 'ff3030', '24141c', seed=11)
    paste_rgba(im, beast, 10, -20)
    glow(im, 105, 42, 16, 'ff3030', .6); glow(im, 135, 42, 16, 'ff3030', .6)
    rain(im, 160, 12, '603040', .4)
    return im


def hollow_close():
    im = Image.new('RGB', (W, H))
    gradient(im, '1a1416', '4a3a32', 0, H)
    glow(im, 120, 40, 90, 'a08868', .55)
    fig = sprite_figure('hollow', 0, 6).crop((0, 6 * 3, 96, 6 * 27))
    paste_key(im, fig, 72, 16)
    rim_light(im, fig, 72, 16, 'f2d488', side=-1)
    rain(im, 120, 13, '9aa0b0', .3)
    return im


def ward():
    im = Image.new('RGB', (W, H))
    gradient(im, '1a1e22', '4a5450', 0, 100)
    gradient(im, '20241e', '0c0e0c', 100, H)
    d = ImageDraw.Draw(im)
    d.rectangle([30, 44, 210, 126], fill=hx('0e1010'))
    d.polygon([(24, 46), (120, 14), (216, 46)], fill=hx('0a0c0c'))
    rnd = random.Random(15)
    for wy in range(54, 116, 12):
        for wx in range(40, 202, 12):
            col = '1e2422' if rnd.random() > .07 else 'd8c070'
            d.rectangle([wx, wy, wx + 6, wy + 7], fill=hx(col))
    d.rectangle([108, 96, 132, 126], fill=hx('1e2422'))
    for x in range(0, W, 6):
        d.rectangle([x, 118, x + 1, H], fill=hx('2a302c'))
    d.rectangle([0, 122, W, 123], fill=hx('2a302c'))
    fog(im, 90, 150, '6a7a70', .45, 4)
    rain(im, 160, 16, '8a9a90', .3)
    return im


def dawn():
    im = Image.new('RGB', (W, H))
    gradient(im, '3a4258', 'd8a070', 0, 100)
    glow(im, 120, 100, 70, 'ffd8a0', .5)
    skyline(im, 108, 18, '1a1418', ['5a4030'], .02, 20, 60)
    gradient(im, '2a2226', '0e0a0c', 108, H)
    d = ImageDraw.Draw(im)
    d.polygon([(96, H), (118, 108), (122, 108), (144, H)], fill=hx('3a3236'))
    fig = sprite_figure('hollow', 3, 1)
    paste_key(im, fig, 112, 96)
    d.polygon([(118, 127), (110, H), (132, H), (122, 127)], fill=hx('0a0608'))
    d.line([(111, 157), (106, 150)], fill=hx('0a0608'), width=2)
    d.line([(131, 157), (136, 150)], fill=hx('0a0608'), width=2)
    return im


def vessel():
    im = Image.new('RGB', (W, H))
    gradient(im, '050405', '5a0a10', 0, H)
    beast = shadow_beast(150, 150, '060406', 'ff3030', '2a0a10', seed=21)
    paste_rgba(im, beast, 45, 0)
    glow(im, 110, 40, 10, 'ff4040', .6); glow(im, 130, 40, 10, 'ff4040', .6)
    skyline(im, H, 20, '050405', ['b8823a', 'd8b860'], .12, 20, 60)
    return im


def eighth():
    im = Image.new('RGB', (W, H))
    gradient(im, '0a0806', '2e2014', 0, H)
    d = ImageDraw.Draw(im)
    d.rectangle([70, 88, 170, 124], fill=hx('2a1e14'))
    d.rectangle([72, 88, 168, 92], fill=hx('5a4030'))
    d.rectangle([106, 52, 134, 88], fill=hx('0a0806'))
    d.rectangle([110, 56, 130, 86], fill=hx('1e1a1e'))
    d.point([(116, 66), (124, 66)], fill=hx('ff3030'))
    glow(im, 120, 66, 14, 'ff3030', .3)
    for i in range(8):
        x = 24 + i * 27
        d.rectangle([x, 128, x + 4, 142], fill=hx('e8dcc0'))
        glow(im, x + 2, 124, 12, 'f2c96b', .6)
        d.rectangle([x + 1, 122, x + 3, 127], fill=hx('fff2c4'))
    for i in range(8):
        x = 36 + i * 24
        d.line([(x, 14), (x, 36)], fill=hx('8a1a1e'), width=2)
    return im


SCENES = [('title', title), ('gloam', gloam), ('house', house), ('photo', photo),
          ('shadow', shadow_close), ('hollow', hollow_close), ('ward', ward), ('dawn', dawn),
          ('vessel', vessel), ('eighth', eighth)]
