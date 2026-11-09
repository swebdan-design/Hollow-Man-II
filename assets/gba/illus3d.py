"""3D pieces and the cinematic finish for the GBA illustrations (title + cutscenes).
Figures are raymarched with tools/render3d.py: Hollow Man is the same model as his in-game
sprite, rendered large from a low camera; the Second Shadow is a horned SDF figure that
dissolves into smoke. Renders are cached in build/gba/cache3d (keyed on the source)."""
import hashlib
import math
import os
import numpy as np
import render3d as R3
from render3d import V, Prim
import chars3d

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, '..', '..', 'build', 'gba', 'cache3d')
W, H = 240, 160


def _src_hash():
    h = hashlib.sha1()
    for f in (os.path.join(HERE, 'illus3d.py'), os.path.join(HERE, 'chars3d.py'),
              os.path.join(HERE, '..', '..', 'tools', 'render3d.py')):
        h.update(open(f, 'rb').read())
    return h.hexdigest()[:12]


def _cached(key, fn):
    os.makedirs(CACHE, exist_ok=True)
    p = os.path.join(CACHE, 'illus_%s_%s.npy' % (key, _src_hash()))
    if os.path.exists(p):
        return np.load(p)
    a = fn()
    np.save(p, a)
    return a


# ------------------------------------------------------------------ figures
def figure(key, name, w, h, height_px, center_y=0.92, pitch=0.16, yaw=0.0, ss=2,
           key_dir=V(-0.7, 0.5, 0.6), rim=V(0.6, 0.4, -1.0), rim_col=V(1.0, 0.82, 0.5), ambient=0.30,
           key_col=V(1.0, 0.9, 0.78), phase=0, attack=False):
    """render a chars3d character into a w x h RGBA float image; the whole 1.85-unit figure
    would be `height_px` pixels tall"""
    def go():
        P, mats = chars3d.build(chars3d.CHARS[name], phase, attack)
        scale = 1.85 / height_px / ss
        rgba = R3.render(P, mats, w * ss, h * ss, scale, center=V(0, center_y, 0), yaw=yaw, pitch=pitch,
                         steps=64, key=key_dir, rim=rim, rim_col=rim_col, ambient=ambient, key_col=key_col)
        return R3.downsample(rgba, ss)
    return _cached(key, go)


M_BODY, M_EYE, M_HORN = 1, 2, 3


def beast_prims():
    """the Second Shadow: tall, horned, long-armed; the lower body is smoke (alpha added later)"""
    P = []
    P.append(Prim('ell', M_BODY, V(0, 1.15, 0), V(0.42, 0.55, 0.26)))           # chest
    P.append(Prim('ell', M_BODY, V(0, 0.55, 0), V(0.34, 0.6, 0.22), blend=0.12))  # trailing body
    P.append(Prim('cap', M_BODY, V(0, 1.55, 0.0), V(0, 1.78, 0.03), 0.11, blend=0.08))  # neck
    P.append(Prim('ell', M_BODY, V(0, 1.92, 0.05), V(0.2, 0.25, 0.21), blend=0.06))   # skull
    P.append(Prim('ell', M_BODY, V(0, 1.82, 0.14), V(0.13, 0.12, 0.12), blend=0.05))  # jaw / snout
    for s in (-1, 1):
        # horns: tapered chain curving up and out
        pts = [V(s * 0.12, 2.06, 0.02), V(s * 0.26, 2.22, -0.02), V(s * 0.36, 2.42, -0.06), V(s * 0.38, 2.62, -0.1)]
        rads = [0.07, 0.05, 0.032, 0.012]
        for a, b, ra, rb in zip(pts, pts[1:], rads, rads[1:]):
            P.append(Prim('cap', M_HORN, a, b, ra, rb))
        # shoulders, long arms, long fingers
        sh = V(s * 0.42, 1.42, 0)
        el = V(s * 0.6, 0.95, 0.08)
        wr = V(s * 0.62, 0.42, 0.16)
        P.append(Prim('cap', M_BODY, sh, el, 0.11, 0.075, blend=0.08))
        P.append(Prim('cap', M_BODY, el, wr, 0.075, 0.05, blend=0.04))
        for k in range(4):
            a = (k - 1.5) * 0.18
            tip = wr + V(s * (0.04 + 0.05 * math.sin(a)), -0.32 + 0.04 * abs(k - 1.5), 0.06 + 0.06 * math.cos(a) * k * 0.3)
            P.append(Prim('cap', M_BODY, wr, tip, 0.024, 0.008))
        P.append(Prim('sphere', M_EYE, V(s * 0.075, 1.95, 0.22), 0.028))
    return P


def beast(key, w, h, height_px, center_y=1.3, pitch=0.1, ss=2):
    def go():
        mats = {M_BODY: R3.flat((14, 11, 16), 0.25, 0.1), M_HORN: R3.flat((34, 26, 30), 0.6, 0.15),
                M_EYE: R3.flat((255, 70, 60), 0.0, 0.0)}
        scale = 2.7 / height_px / ss
        rgba = R3.render(beast_prims(), mats, w * ss, h * ss, scale, center=V(0, center_y, 0), pitch=pitch,
                         steps=64, key=V(0.2, 0.3, 1.0), rim=V(0.0, 0.6, -1.0), rim_col=V(1.0, 0.25, 0.2),
                         ambient=0.18, key_col=V(0.5, 0.4, 0.45), fill_col=V(0.3, 0.1, 0.12))
        return R3.downsample(rgba, ss)
    a = _cached(key, go).copy()
    # dissolve the lower body into smoke
    hh, ww = a.shape[:2]
    ys, xs = np.mgrid[0:hh, 0:ww]
    n = (np.sin(xs * 0.21 + ys * 0.05) + np.sin(xs * 0.07 - ys * 0.13 + 1.7) + np.sin(ys * 0.31 + xs * 0.02)) / 3
    fade = np.clip((ys / hh - 0.55) / 0.4 + n * 0.25, 0, 1)
    a[..., 3] *= 1 - fade
    a[..., :3] *= (1 - fade * 0.5)[..., None]
    return a


# ------------------------------------------------------------------ compositing helpers
def eyes_of(b):
    """pixel centres of the beast's two eyes in a beast() render (for the glow pass)"""
    m = (b[..., 0] > 0.55) & (b[..., 1] < 0.35) & (b[..., 3] > 0.5)
    ys, xs = np.nonzero(m)
    if len(xs) == 0:
        return []
    mid = xs.mean()
    out = []
    for sel in (xs < mid, xs >= mid):
        if sel.any():
            out.append((xs[sel].mean(), ys[sel].mean()))
    return out


def beast_at(a, b, x, y, glow_r, strength=0.8):
    over(a, b, x, y)
    for ex, ey in eyes_of(b):
        glow_add(a, x + ex, y + ey, glow_r, (1.0, 0.18, 0.12), strength)


def to_arr(im):
    return np.asarray(im.convert('RGB'), dtype=np.float64) / 255


def to_img(a):
    from PIL import Image
    return Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8), 'RGB')


def over(dst, src, x, y):
    """alpha-composite RGBA float src at (x, y) onto RGB float dst (clipped)"""
    h, w = src.shape[:2]
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(dst.shape[1], x + w), min(dst.shape[0], y + h)
    if x1 <= x0 or y1 <= y0:
        return
    s = src[y0 - y:y1 - y, x0 - x:x1 - x]
    a = s[..., 3:4]
    dst[y0:y1, x0:x1] = dst[y0:y1, x0:x1] * (1 - a) + s[..., :3] * a


def blur(a, r):
    if r <= 0:
        return a
    k = np.exp(-0.5 * (np.arange(-3 * r, 3 * r + 1) / r) ** 2)
    k /= k.sum()
    out = a
    for ax in (0, 1):
        pad = [(0, 0)] * out.ndim
        pad[ax] = (3 * r, 3 * r)
        p = np.pad(out, pad, mode='edge')
        acc = np.zeros_like(out)
        for i, kv in enumerate(k):
            sl = [slice(None)] * out.ndim
            sl[ax] = slice(i, i + out.shape[ax])
            acc += p[tuple(sl)] * kv
        out = acc
    return out


def glow_add(a, cx, cy, r, col, strength):
    ys, xs = np.mgrid[0:a.shape[0], 0:a.shape[1]]
    d2 = ((xs - cx) ** 2 + (ys - cy) ** 2) / (r * r)
    a += np.exp(-d2 * 2.5)[..., None] * np.array(col) * strength


def light_shafts(a, cx, cy, strength=0.5, decay=0.965, samples=48):
    """screen-space god rays from the bright parts of the image toward (cx, cy)"""
    lum = a.mean(axis=2)
    src = np.clip(lum - 0.55, 0, None)[..., None] * a
    acc = np.zeros_like(a)
    ys, xs = np.mgrid[0:a.shape[0], 0:a.shape[1]]
    w = 1.0
    for i in range(samples):
        t = i / samples
        sx = np.clip((xs + (cx - xs) * t).astype(int), 0, a.shape[1] - 1)
        sy = np.clip((ys + (cy - ys) * t).astype(int), 0, a.shape[0] - 1)
        acc += src[sy, sx] * w
        w *= decay
    return a + acc / samples * strength * 4


def finish(a, seed, bloom=0.45, grain=0.025, vignette=0.45, warm=(1.0, 1.0, 1.0), contrast=1.08):
    """filmic finish: bloom, tone curve, colour grade, vignette and grain"""
    b = blur(np.clip(a - 0.6, 0, None), 6) + blur(np.clip(a - 0.45, 0, None), 14) * 0.6
    a = a + b * bloom
    a = 1 - np.exp(-a * 1.25)                         # soft shoulder
    a = np.clip((a - 0.5) * contrast + 0.5, 0, None) * np.array(warm)
    ys, xs = np.mgrid[0:a.shape[0], 0:a.shape[1]]
    r = np.hypot((xs - a.shape[1] / 2) / (a.shape[1] / 2), (ys - a.shape[0] / 2) / (a.shape[0] / 2))
    a = a * (1 - vignette * np.clip(r - 0.45, 0, None) ** 1.5)[..., None]
    rng = np.random.default_rng(seed)
    a = a + rng.normal(0, grain, a.shape[:2])[..., None]
    return np.clip(a, 0, 1)
