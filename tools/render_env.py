"""render_env.py - bakes every map into one unique, lit picture (pre-rendered look):
point lights from lamps/windows/neon/candles/screens with glow, soft cast shadows from a
height field, ambient occlusion where walls meet floors, wet-street reflections, fog and a
mood grade.  The picture is then split into 8x8 4bpp tiles with 13 palettes chosen per map."""
import numpy as np
from PIL import Image, ImageFilter

# metatile heights (in metatile units) - anything SOLID and not listed is 0.9
HEIGHTS = {
    'city': {'B': 1.6, 'Z': 1.6, 'W': 1.6, 'w': 1.6, 'x': 1.6, 'R': 2.0, 'r': 1.8, 'D': 1.2, 'S': 1.6, 'N': 1.6,
             'Q': 1.6, 'q': 1.5, 'A': 1.6, 'a': 1.6, 'U': 0.6, 'T': 1.4, 'F': 0.7, 'f': 0.5, 'C': 0.9, 'G': 0.9,
             'I': 0.8, 'X': 0.5, 'L': 1.8, 'b': 0.5, 'h': 0.4, 'E': 0.9, 'c': 0.6, 'v': 0.6, 'M': 1.0, 'O': 1.0,
             'P': 0.4, 'Y': 0.8, '+': 0.5, '#': 0.0, '~': -0.15},
    'interior': {'B': 1.5, 'Z': 1.5, 'W': 1.5, 'o': 1.5, 'M': 1.5, 'E': 1.5, 'L': 1.2, 'D': 1.2, 'S': 1.0,
                 's': 0.9, 'T': 0.45, 't': 0.4, 'C': 0.55, 'c': 0.6, 'b': 0.35, 'X': 0.6, 'x': 0.6, 'P': 0.4,
                 'A': 0.6, 'a': 0.5, 'O': 0.8, 'R': 0.3, 'V': 1.0, 'm': 0.5, 'G': 0.5, 'F': 1.5, 'Q': 1.5, 'I': 1.0,
                 'p': 0.5, 'k': 0.6, 'n': 0.5, 'v': 0.6, '#': 0.0, '\x00': 1.5},
    'under': {'B': 1.5, 'Z': 1.5, 'b': 1.5, 'P': 1.5, 'F': 1.5, '#': 0.0, '~': -0.2, 'w': -0.3, 'V': 0.6,
              'G': 1.2, 'S': 1.4, 'X': 0.6, 'x': 0.6, 'M': 1.0, 'E': 1.0, 'O': 0.6, 'C': 0.4, 'c': 1.5, 'Q': 1.5,
              'D': 1.2, 'l': 1.2, 'h': 0.9, 'T': 0.45, 'A': 0.6, '\x00': 1.5},
}

# light sources: char -> (rgb 0..1, intensity, radius in px, y offset of the light in the tile)
LIGHTS = {
    'city': {'L': ((1.0, 0.82, 0.55), 1.5, 52, -6), 'l': ((1.0, 0.82, 0.55), 0.5, 26, 8),
             'W': ((1.0, 0.78, 0.45), 0.75, 30, 18), 'N': ((1.0, 0.25, 0.3), 1.0, 44, 16),
             'S': ((1.0, 0.85, 0.6), 0.35, 20, 16), 'E': ((0.5, 0.9, 0.7), 0.35, 18, 8),
             'a': ((0.9, 0.4, 0.5), 0.5, 28, 16), 'c': ((1.0, 0.95, 0.8), 0.45, 26, 4)},
    'interior': {'W': ((0.55, 0.65, 0.9), 0.55, 34, 20), 'a': ((1.0, 0.75, 0.4), 1.2, 44, 4),
                 'v': ((0.55, 0.7, 1.0), 0.8, 34, 8), 'k': ((0.4, 1.0, 0.6), 0.6, 28, 6),
                 'c': ((1.0, 0.9, 0.6), 0.4, 26, 6), 'M': ((0.6, 0.65, 0.8), 0.35, 24, 16),
                 'A': ((1.0, 0.75, 0.45), 0.6, 36, 6), 'F': ((1.0, 0.85, 0.5), 0.35, 20, 8)},
    'under': {'E': ((1.0, 0.3, 0.25), 0.8, 36, 8), 'A': ((1.0, 0.2, 0.25), 1.2, 48, 6),
              'M': ((0.5, 1.0, 0.6), 0.55, 30, 6), 'S': ((1.0, 0.7, 0.3), 0.4, 26, 2),
              'U': ((0.8, 0.85, 1.0), 0.5, 30, -4), 'e': ((0.4, 0.6, 0.55), 0.25, 20, 8)},
}
WET = {'.', ',', '=', '-', 'K', 'g'}          # city: asphalt surfaces reflect lights in the rain

# mood grade per palette-set name: ambient light colour, fog colour/amount, saturation
MOOD = {
    'city_night': ((0.42, 0.45, 0.58), (0.22, 0.24, 0.32), 0.12, 0.85),
    'city_mercy': ((0.55, 0.47, 0.40), (0.35, 0.28, 0.22), 0.16, 0.7),
    'city_strip': ((0.45, 0.48, 0.60), (0.22, 0.24, 0.32), 0.12, 0.85),
    'city_indust': ((0.45, 0.47, 0.38), (0.28, 0.28, 0.20), 0.15, 0.75),
    'city_neon': ((0.48, 0.36, 0.45), (0.30, 0.12, 0.18), 0.14, 0.95),
    'city_old': ((0.38, 0.44, 0.58), (0.22, 0.26, 0.34), 0.18, 0.75),
    'city_ward': ((0.38, 0.47, 0.40), (0.22, 0.30, 0.26), 0.22, 0.7),
    'city_canal': ((0.36, 0.46, 0.48), (0.20, 0.28, 0.30), 0.18, 0.75),
    'int_warm': ((0.62, 0.55, 0.48), (0.2, 0.15, 0.1), 0.0, 0.95),
    'int_motel': ((0.58, 0.42, 0.45), (0.25, 0.08, 0.12), 0.05, 0.95),
    'int_church': ((0.42, 0.45, 0.58), (0.15, 0.15, 0.22), 0.06, 0.8),
    'int_records': ((0.66, 0.66, 0.56), (0.2, 0.2, 0.15), 0.0, 0.8),
    'int_ward': ((0.50, 0.60, 0.52), (0.2, 0.26, 0.22), 0.06, 0.7),
    'int_dark': ((0.30, 0.28, 0.34), (0.08, 0.06, 0.1), 0.1, 0.8),
    'und_sewer': ((0.36, 0.44, 0.40), (0.12, 0.18, 0.15), 0.12, 0.8),
    'und_cold': ((0.58, 0.66, 0.76), (0.4, 0.48, 0.58), 0.14, 0.75),
    'und_crypt': ((0.40, 0.38, 0.52), (0.12, 0.10, 0.18), 0.1, 0.8),
    'und_basement': ((0.42, 0.36, 0.30), (0.14, 0.10, 0.06), 0.1, 0.8),
    'und_ward': ((0.38, 0.46, 0.38), (0.1, 0.16, 0.12), 0.12, 0.75),
}


def blur(a, r):
    """separable gaussian blur (edge-clamped), works on 2D or HxWxC float arrays"""
    if r <= 0:
        return a
    k = int(r * 3) + 1
    x = np.arange(-k, k + 1)
    g = np.exp(-x ** 2 / (2 * r * r))
    g /= g.sum()
    out = a.astype(np.float64)
    for axis in (0, 1):
        pad = [(0, 0)] * out.ndim
        pad[axis] = (k, k)
        p = np.pad(out, pad, mode='edge')
        acc = np.zeros_like(out)
        for i, gv in enumerate(g):
            sl = [slice(None)] * out.ndim
            sl[axis] = slice(i, i + out.shape[axis])
            acc += p[tuple(sl)] * gv
        out = acc
    return out


def shift(a, dx, dy, fill=0.0):
    out = np.full_like(a, fill)
    h, w = a.shape[:2]
    ys, yd = (slice(0, h - dy), slice(dy, h)) if dy >= 0 else (slice(-dy, h), slice(0, h + dy))
    xs, xd = (slice(0, w - dx), slice(dx, w)) if dx >= 0 else (slice(-dx, w), slice(0, w + dx))
    out[yd, xd] = a[ys, xs]
    return out


def compose(grid_chars, tsname, mt_images, w, h, top_image=None, wall='B'):
    """albedo + per-pixel height + list of lights for a grid of metatile characters"""
    alb = np.zeros((h * 16, w * 16, 3))
    hgt = np.zeros((h * 16, w * 16))
    emis = np.zeros((h * 16, w * 16, 3))
    lights = []
    H = HEIGHTS[tsname]
    for ty in range(h):
        for tx in range(w):
            ch = grid_chars[ty][tx]
            im = mt_images[ch]
            if top_image is not None and ch == wall:
                below = grid_chars[ty + 1][tx] if ty + 1 < h else None
                if below is None or below == wall or H.get(below, 0) >= 0.9:
                    im = top_image
            a = np.asarray(im, dtype=np.float64) / 255
            alb[ty * 16:ty * 16 + 16, tx * 16:tx * 16 + 16] = a
            hv = H.get(ch, 0.0)
            hgt[ty * 16:ty * 16 + 16, tx * 16:tx * 16 + 16] = hv
            if ch in LIGHTS.get(tsname, {}):
                col, inten, rad, yo = LIGHTS[tsname][ch]
                lights.append((tx * 16 + 8, ty * 16 + 8 + yo, np.array(col), inten, rad))
                lum = a.mean(-1)
                m = (lum > 0.62)[..., None]
                emis[ty * 16:ty * 16 + 16, tx * 16:tx * 16 + 16] = np.where(m, a, 0)
    return alb, hgt, emis, lights


def light_image(alb, hgt, emis, lights, mood, outdoor, rain, wet_mask):
    h, w = hgt.shape
    amb, fogc, fog_amt, sat = MOOD[mood]
    # painterly surfaces: soften the source texture, then add continuous fine-grain variation
    rng = np.random.default_rng(11)
    grain = blur(rng.standard_normal((h, w)), 0.8) * 0.05 + blur(rng.standard_normal((h, w)), 4.0) * 0.12
    alb = blur(alb, 0.75) * (1 + grain)[..., None]
    ys, xs = np.mgrid[0:h, 0:w]
    L = np.ones((h, w, 3)) * np.array(amb)
    # soft cast shadows from the moon / ceiling light direction (down-right)
    occ = np.maximum(shift(hgt, 4, 6) - hgt, 0) + np.maximum(shift(hgt, 2, 3) - hgt, 0)
    sh = np.clip(blur(occ, 3.0) * 0.45, 0, 0.6)
    # ambient occlusion: dark where something taller is nearby
    ao = np.clip((blur(hgt, 5.0) - hgt) * 0.5, 0, 0.45)
    L *= (1 - sh - ao)[..., None]
    # top faces of tall things catch more sky light
    L *= (1 + np.clip(hgt, 0, 2) * 0.06)[..., None]
    for (lx, ly, col, inten, rad) in lights:
        d2 = (xs - lx) ** 2 + (ys - ly) ** 2
        fall = np.exp(-d2 / (2 * (rad * 0.6) ** 2)) + 0.35 * np.exp(-d2 / (2 * (rad * 1.4) ** 2))
        L += (fall * inten * 1.25)[..., None] * col
    img = alb * L
    # bloom / glow of emissive parts
    glow = blur(emis, 2.0) * 0.9 + blur(emis, 6.0) * 0.7
    img = img + emis * 0.6 + glow * 0.5
    if rain and outdoor:
        # wet asphalt: streaky reflections of lights below their sources
        refl = np.zeros_like(img)
        for k in range(1, 14):
            refl += shift(glow + emis, 0, k * 2) * (0.07 * (1 - k / 14))
        img += refl * wet_mask[..., None]
    if fog_amt:
        img = img * (1 - fog_amt) + np.array(fogc) * fog_amt
    gray = img.mean(-1, keepdims=True)
    img = gray + (img - gray) * sat
    img = img / (1 + img * 0.25)          # soft tone curve
    return np.clip(img * 1.15, 0, 1)


# ------------------------------------------------------------------ tile + palette conversion
def quantize_tiles(img, n_pals=13, max_tiles=1000, fixed_tiles=None):
    """img float (H, W, 3) -> (tiles list of 64 idx tuples, palettes[n][15 rgb], entries per 8x8 cell)"""
    from gba_art import TileStore
    H, W = img.shape[:2]
    rgb = (img * 255).round().astype(np.int32)
    rgb = (rgb // 8) * 8                      # GBA 15-bit colour
    cells = rgb.reshape(H // 8, 8, W // 8, 8, 3).transpose(0, 2, 1, 3, 4).reshape(-1, 64, 3)
    means = cells.mean(1)
    # k-means on tile mean colours (plus spread) to form palette groups
    feat = np.concatenate([means, cells.std(1) * 0.5], axis=1)
    rng = np.random.default_rng(7)
    k = min(n_pals, len(cells))
    cent = feat[rng.choice(len(feat), k, replace=False)]
    for _ in range(12):
        lab = ((feat[:, None] - cent[None]) ** 2).sum(-1).argmin(1)
        for i in range(k):
            if (lab == i).any():
                cent[i] = feat[lab == i].mean(0)
    pals = []
    for i in range(k):
        px = cells[lab == i].reshape(-1, 3)
        if len(px) == 0:
            px = cells[0]
        im = Image.fromarray(px.reshape(1, -1, 3).astype(np.uint8))
        q = im.quantize(colors=15, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
        pl = q.getpalette()[:45]
        cols = sorted(set(tuple(pl[j * 3:j * 3 + 3]) for j in range(len(pl) // 3)))
        while len(cols) < 15:
            cols.append(cols[-1])
        pals.append(np.array(cols[:15], dtype=np.int32))
    P = np.stack(pals)                                     # (k, 15, 3)
    # assign each cell to its best palette by reconstruction error
    d = ((cells[:, None, :, None, :] - P[None, :, None, :, :]) ** 2).sum(-1)   # (n, k, 64, 15)
    best = d.min(-1).sum(-1).argmin(1)
    idx = d[np.arange(len(cells)), best].argmin(-1) + 1     # (n, 64)
    store = TileStore(limit=4096)
    entries = []
    for ci in range(len(cells)):
        t, hf, vf = store.add(tuple(int(v) for v in idx[ci]))
        entries.append((t, hf, vf, int(best[ci])))
    return store, [[tuple(int(v) for v in c) for c in p] for p in P], entries, P, idx, best


def reconstruct(P, idx, best, W, H):
    cells = P[best][np.arange(len(best))[:, None], idx - 1]
    return cells.reshape(H // 8, W // 8, 8, 8, 3).transpose(0, 2, 1, 3, 4).reshape(H, W, 3).astype(np.uint8)


def merge_tiles(cells_idx, best, P, budget):
    """Reduce the number of unique tiles to `budget` by remapping the most similar ones."""
    rgb = P[best][np.arange(len(best))[:, None], cells_idx - 1].reshape(len(best), -1).astype(np.int32)
    keys = {}
    uniq = []
    owner = np.zeros(len(best), dtype=np.int32)
    for i in range(len(best)):
        k = rgb[i].tobytes()
        if k not in keys:
            keys[k] = len(uniq)
            uniq.append(i)
        owner[i] = keys[k]
    if len(uniq) <= budget:
        return cells_idx, best
    U = rgb[uniq].astype(np.float64)
    alive = np.ones(len(uniq), dtype=bool)
    target = np.arange(len(uniq))
    # repeatedly merge each tile into its nearest neighbour, cheapest first
    d = ((U[:, None] - U[None]) ** 2).mean(-1)
    np.fill_diagonal(d, 1e18)
    order = np.argsort(d.min(1))
    nearest = d.argmin(1)
    n = len(uniq)
    for t in order:
        if n <= budget:
            break
        j = nearest[t]
        while not alive[j]:
            j = target[j]
        if j == t or not alive[t]:
            continue
        alive[t] = False
        target[t] = j
        n -= 1
    def root(t):
        while not alive[t]:
            t = target[t]
        return t
    new_idx = cells_idx.copy()
    new_best = best.copy()
    for i in range(len(best)):
        r = uniq[root(owner[i])]
        new_idx[i] = cells_idx[r]
        new_best[i] = best[r]
    return new_idx, new_best
