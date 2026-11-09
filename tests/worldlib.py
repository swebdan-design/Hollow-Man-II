"""Loads the compiled world description (host side) for validation tests."""
import os
import sys
import functools

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
sys.path.insert(0, os.path.join(ROOT, 'assets', 'maps'))


@functools.lru_cache()
def load():
    import build_tiles
    import content
    legends = {name: build_tiles.legend(name) for name, _ in build_tiles.TILESETS}
    content.TILE_LEGENDS.update(legends)
    import world
    return content, world, legends


def solid(legends, m, x, y):
    if not (0 <= x < m.w and 0 <= y < m.h):
        return True
    ch = m.rows[y][x]
    return bool(legends[m.ts][ch][1].flags & 0x01)


def tile_at(m, x, y, flags):
    """tile char after applying patches whose flag condition is in `flags`"""
    ch = m.rows[y][x]
    for (px, py, pch, cond) in m.patches:
        if px == x and py == y and cond_true(cond, flags):
            ch = pch
    return ch


def cond_true(cond, flags):
    if cond is None:
        return True
    if isinstance(cond, str):
        return cond in flags
    if cond[0] == 'not':
        return not cond_true(cond[1], flags)
    if cond[0] == 'item':
        return ('item:' + cond[1]) in flags
    return True   # alert/stage etc.: treat as satisfiable


def reachable(legends, m, start, flags):
    """BFS over walkable tiles with patches applied (crate pushes ignored: crates are solid)."""
    seen = {start}
    st = [start]
    while st:
        x, y = st.pop()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if (nx, ny) in seen or not (0 <= nx < m.w and 0 <= ny < m.h):
                continue
            ch = tile_at(m, nx, ny, flags)
            if legends[m.ts][ch][1].flags & 0x01:
                # warp tiles on solid gates still count as reachable targets
                continue
            seen.add((nx, ny))
            st.append((nx, ny))
    return seen
