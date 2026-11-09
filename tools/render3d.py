"""render3d.py - tiny signed-distance-field renderer (numpy) used to pre-render the GBA
characters and illustration figures: orthographic camera, key/fill/rim lighting, soft AO,
procedural cloth textures (herringbone tweed, knitted balaclava). Rendered supersampled,
then downsampled for smooth, non-pixel-art results."""
import math
import numpy as np


def V(*a):
    return np.array(a, dtype=np.float64)


def norm(v):
    return v / (np.linalg.norm(v, axis=-1, keepdims=True) + 1e-9)


# ------------------------------------------------------------------ primitives (vectorised)
def sd_sphere(p, c, r):
    return np.linalg.norm(p - c, axis=-1) - r


def sd_ellipsoid(p, c, r):
    q = (p - c) / r
    k0 = np.linalg.norm(q, axis=-1)
    k1 = np.linalg.norm(q / r, axis=-1)
    return k0 * (k0 - 1.0) / (k1 + 1e-9)


def sd_capsule(p, a, b, ra, rb=None):
    rb = ra if rb is None else rb
    pa, ba = p - a, b - a
    h = np.clip((pa @ ba) / (ba @ ba), 0, 1)
    d = np.linalg.norm(pa - h[..., None] * ba, axis=-1)
    return d - (ra + (rb - ra) * h)


def sd_rbox(p, c, half, r):
    q = np.abs(p - c) - half
    return np.linalg.norm(np.maximum(q, 0), axis=-1) + np.minimum(np.max(q, axis=-1), 0) - r


def smin(a, b, k):
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1)
    return b + (a - b) * h - k * h * (1 - h)


class Prim:
    def __init__(self, kind, mat, *args, blend=0.0):
        self.kind, self.mat, self.args, self.blend = kind, mat, args, blend

    def d(self, p):
        return {'sphere': sd_sphere, 'ell': sd_ellipsoid, 'cap': sd_capsule, 'box': sd_rbox}[self.kind](p, *self.args)


def scene_eval(prims, p):
    d = np.full(p.shape[:-1], 1e9)
    m = np.zeros(p.shape[:-1], dtype=np.int32)
    for pr in prims:
        dd = pr.d(p)
        if pr.blend > 0:
            nd = smin(d, dd, pr.blend)
            take = dd < d
            d = nd
        else:
            take = dd < d
            d = np.where(take, dd, d)
        m = np.where(take, pr.mat, m)
    return d, m


def rot_y(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def render(prims, materials, w, h, scale, center, yaw=0.0, pitch=0.55, steps=56,
           key=V(-0.6, 0.8, 0.7), rim=V(0.4, 0.5, -1.0), rim_col=V(1.0, 0.85, 0.6),
           ambient=0.32, key_col=V(1.0, 0.95, 0.88), fill_col=V(0.35, 0.40, 0.55)):
    """Orthographic render. Returns RGBA float image (h, w, 4). `scale` = world units per pixel.
    yaw rotates the model (0 = facing the camera/down the screen)."""
    R = rot_y(yaw)
    cp, sp = math.cos(pitch), math.sin(pitch)
    fwd = V(0, -sp, -cp)               # camera looks down and into the scene
    up = V(0, cp, -sp)
    right = V(1, 0, 0)
    ys, xs = np.mgrid[0:h, 0:w]
    u = (xs - w / 2 + 0.5) * scale
    v = (h / 2 - ys - 0.5) * scale
    ro = center + u[..., None] * right + v[..., None] * up - fwd * 4.0
    # transform rays into model space (rotate scene by -yaw)
    Ri = R.T
    ro_m = ro @ Ri.T
    rd_m = (fwd @ Ri.T) * np.ones_like(ro)
    t = np.zeros((h, w))
    hit = np.zeros((h, w), dtype=bool)
    for _ in range(steps):
        p = ro_m + rd_m * t[..., None]
        d, _ = scene_eval(prims, p)
        hit |= d < 0.002
        t = np.where(hit, t, t + np.maximum(d, 0.004))
    p = ro_m + rd_m * t[..., None]
    d, mat = scene_eval(prims, p)
    hit &= t < 8.0
    e = 0.004
    n = np.stack([scene_eval(prims, p + V(*o))[0] - scene_eval(prims, p - V(*o))[0]
                  for o in ((e, 0, 0), (0, e, 0), (0, 0, e))], axis=-1)
    n = norm(n)
    # AO
    ao = np.ones((h, w))
    for i in range(1, 5):
        dist = 0.03 * i
        ao -= (dist - scene_eval(prims, p + n * dist)[0]) * (0.6 / i)
    ao = np.clip(ao, 0.35, 1.0)
    km = norm(key @ Ri.T)
    rm = norm(rim @ Ri.T)
    ndl = np.clip(n @ km, 0, 1)
    fill = np.clip(n @ norm(V(0.6, 0.2, 0.6) @ Ri.T), 0, 1)
    view = -rd_m[0, 0]
    rimt = np.clip(1 - np.abs(n @ view), 0, 1) ** 2.2 * np.clip(n @ rm + 0.5, 0, 1)
    spec = np.clip((n @ norm(km + view)), 0, 1) ** 24
    col = np.zeros((h, w, 3))
    specm = np.zeros((h, w))
    for mid, mfn in materials.items():
        sel = (mat == mid) & hit
        if not sel.any():
            continue
        c, sp_amt = mfn(p[sel], n[sel])
        col[sel] = c
        specm[sel] = sp_amt
    light = (ambient * ao)[..., None] + ndl[..., None] * key_col * (0.95 * (0.6 + 0.4 * ao))[..., None] \
        + fill[..., None] * fill_col * 0.25
    out = col * light + rimt[..., None] * rim_col * 0.65 + (spec * specm)[..., None] * 0.6
    rgba = np.zeros((h, w, 4))
    rgba[..., :3] = np.clip(out, 0, 1)
    rgba[..., 3] = hit
    return rgba


def downsample(rgba, f):
    h, w = rgba.shape[0] // f, rgba.shape[1] // f
    a = rgba[:h * f, :w * f].reshape(h, f, w, f, 4)
    alpha = a[..., 3].mean(axis=(1, 3))
    colsum = (a[..., :3] * a[..., 3:4]).sum(axis=(1, 3))
    cnt = a[..., 3].sum(axis=(1, 3))[..., None]
    col = colsum / np.maximum(cnt, 1e-9)
    out = np.zeros((h, w, 4))
    out[..., :3] = col
    out[..., 3] = alpha
    return out


# ------------------------------------------------------------------ materials
def flat(rgb, spec=0.0, vary=0.04, seed=0):
    c = np.array(rgb, dtype=np.float64) / 255

    def f(p, n):
        k = (np.sin(p[:, 0] * 91 + p[:, 1] * 57 + p[:, 2] * 33 + seed) * 0.5 + 0.5) * vary
        return np.clip(c * (1 - vary / 2 + k)[:, None], 0, 1), np.full(len(p), spec)
    return f


def tweed(base, dark, light):
    b, d, l = (np.array(x, dtype=np.float64) / 255 for x in (base, dark, light))

    def f(p, n):
        # herringbone: diagonal stripes whose direction flips every band
        band = np.floor(p[:, 0] * 22)
        diag = (p[:, 1] * 44 + np.where(band % 2 == 0, 1, -1) * (p[:, 0] * 44)) % 2.0
        c = np.where((diag < 0.8)[:, None], d, b)
        speck = (np.sin(p[:, 0] * 313 + p[:, 1] * 197 + p[:, 2] * 151) > 0.92)[:, None]
        c = np.where(speck, l, c)
        return c, np.full(len(p), 0.05)
    return f


def knit(base, hi):
    b, h = (np.array(x, dtype=np.float64) / 255 for x in (base, hi))

    def f(p, n):
        ang = np.arctan2(p[:, 0], p[:, 2])
        rib = (np.sin(ang * 26) * 0.5 + 0.5) ** 3
        row = (np.sin(p[:, 1] * 160) * 0.5 + 0.5) * 0.35
        t = np.clip(rib * 0.8 + row * 0.4, 0, 1)[:, None]
        return b * (1 - t) + h * t, np.full(len(p), 0.02)
    return f


def leather(rgb):
    return flat(rgb, spec=0.9, vary=0.02)
