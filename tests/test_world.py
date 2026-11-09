"""Host-side validation of the compiled world: map connectivity, warp targets,
script references and full story progression (no unreachable mandatory objectives)."""
import worldlib
from worldlib import reachable, cond_true

c, world, L = worldlib.load()
MAPS = c.MAPS
BY = c.MAP_BY_NAME


def test_no_stub_maps():
    assert world.STUBS == [], world.STUBS


def test_map_dimensions_and_tiles():
    for m in MAPS:
        assert 10 <= m.w <= 16 and 9 <= m.h <= 16, m.name
        for r in m.rows:
            for ch in r:
                assert ch in L[m.ts], (m.name, ch)


def test_warp_arrivals_walkable():
    for m in MAPS:
        for (x, y, dest, dx, dy, dd, cond, lock) in m.warps:
            dm = BY[dest]
            assert not worldlib.solid(L, dm, dx, dy), (m.name, dest, dx, dy)


def test_every_door_has_a_way_back():
    """Every interior reached by a warp has some warp leading out again."""
    for m in MAPS:
        for w in m.warps:
            dm = BY[w[2]]
            assert dm.warps or any(dm.exits), dm.name


def test_edge_exits_are_mutual():
    opp = {0: 1, 1: 0, 2: 3, 3: 2}
    for m in MAPS:
        for i, e in enumerate(m.exits):
            if e:
                assert BY[e].exits[opp[i]] == m.name, (m.name, i, e)


# ------------------------------------------------------------------ progression simulation
class Sim:
    def __init__(self):
        self.flags = set()
        self.evs = set()
        self.done_objs = set()

    def has(self, cond):
        if isinstance(cond, str):
            return cond in self.flags
        k = cond[0]
        if k == 'not':
            return not self.has(cond[1])
        if k == 'item':
            return ('item:' + cond[1]) in self.flags
        if k == 'ev':
            return cond[1] in self.evs
        if k == 'mercycount':
            return len([e for e in self.evs if e.startswith('mercy')]) >= cond[1]
        if k == 'evcount':
            return len(self.evs) >= cond[1]
        return None   # var / infl / stage / alert: unknown -> explore both

    def run(self, ops, mapname, depth=0):
        for o in ops:
            k = o.kind
            if k == 'SETF':
                name = [n for n, i in c.FLAGS.items() if i == o.args[0]][0]
                self.flags.add(name)
            elif k == 'GIVE':
                self.flags.add('item:' + c.ITEMS[o.args[0]][0])
            elif k == 'EV':
                self.evs.add(c.EVIDENCE[o.args[0]][0])
            elif k == 'IF':
                cond, then, els = o.args
                h = self.has(cond)
                if h is None or h:
                    self.run(then, mapname, depth)
                if h is None or not h:
                    self.run(els, mapname, depth)
            elif k == 'CHOICE':
                self.run(o.args[2], mapname, depth)
                self.run(o.args[3], mapname, depth)
            elif k == 'CALL' and depth < 4:
                self.run(script_ops(o.args[0]), mapname, depth + 1)


def script_ops(ref):
    if ref == 0xFFFF or ref is None:
        return []
    return c.SCRIPTS[c.SCRIPT_ID[ref]][1]


def simulate(max_rounds=60):
    s = Sim()
    s.flags.add('item:pipe')
    s.run(script_ops('intro'), None)
    for _ in range(max_rounds):
        before = (len(s.flags), len(s.evs))
        # maps reachable from the start map
        start = BY['strip']
        visited = {}
        todo = [(start, (4, 5))]
        while todo:
            m, pos = todo.pop()
            reach = visited.get(m.name, set())
            if pos in reach:
                continue
            # treat pushable crates as walkable for reachability (puzzle verified separately)
            r = reachable_push(m, pos, s)
            visited[m.name] = reach | r
            if m.enter:
                s.run(script_ops(m.enter), m.name)
            for (x, y, dest, dx, dy, dd, cond, lock) in m.warps:
                if (x, y) in r or adjacent(r, x, y):
                    if cond is None or s.has(cond) is not False:
                        todo.append((BY[dest], (dx, dy)))
            for i, e in enumerate(m.exits):
                if e and any(edge_ok(m, i, p) for p in r):
                    dm = BY[e]
                    for p in r:
                        if edge_ok(m, i, p):
                            q = enter_pos(dm, i, p)
                            if q:
                                todo.append((dm, q))
            for (typ, x, y, a, b, cc, cond, script) in m.objs:
                if cond is not None and s.has(cond) is False:
                    continue
                if not ((x, y) in r or adjacent(r, x, y)):
                    continue
                if typ in (3, 4, 5, 7) or (typ == 1 and script != 0xFFFF) or (typ == 2 and script != 0xFFFF):
                    s.run(script_ops(script), m.name)
                    if typ == 4 and script != 0xFFFF:
                        # shadow walls: also run with shadowcast set
                        s.flags.add('shadowcast')
                        s.run(script_ops(script), m.name)
                        s.flags.discard('shadowcast')
        if (len(s.flags), len(s.evs)) == before:
            break
    return s, visited


def adjacent(r, x, y):
    return any((x + dx, y + dy) in r for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))


def edge_ok(m, i, p):
    x, y = p
    if i < 2 and x not in (7, 8):
        return False
    if i >= 2 and y not in (7, 8):
        return False
    return (i == 0 and y == 0) or (i == 1 and y == m.h - 1) or (i == 2 and x == 0) or (i == 3 and x == m.w - 1)


def enter_pos(dm, i, p):
    x, y = p
    if i == 0:
        q = (x, dm.h - 1)
    elif i == 1:
        q = (x, 0)
    elif i == 2:
        q = (dm.w - 1, y)
    else:
        q = (0, y)
    if q[0] >= dm.w or q[1] >= dm.h:
        return None
    return q


def reachable_push(m, start, s):
    flags = set(s.flags)
    seen = {start}
    st = [start]
    while st:
        x, y = st.pop()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if (nx, ny) in seen or not (0 <= nx < m.w and 0 <= ny < m.h):
                continue
            ch = worldlib.tile_at(m, nx, ny, flags_with_items(flags))
            f = L[m.ts][ch][1].flags
            if f & 0x01 and not f & 0x20:
                continue
            seen.add((nx, ny))
            st.append((nx, ny))
    return seen


def flags_with_items(flags):
    return flags


SIM, VISITED = simulate()


def test_all_chapters_completable():
    for i in range(1, 8):
        assert 'ch%d_done' % i in SIM.flags, 'chapter %d cannot be completed' % i


def test_all_maps_visited():
    missing = [m.name for m in MAPS if m.name not in VISITED]
    assert missing == [], missing


def test_all_evidence_obtainable():
    missing = [e[0] for e in c.EVIDENCE if e[0] not in SIM.evs]
    assert missing == [], missing


def test_secret_ending_reachable():
    assert 'mercy_done' in SIM.flags


def test_all_items_obtainable():
    missing = [it[0] for it in c.ITEMS if 'item:' + it[0] not in SIM.flags]
    assert missing == [], missing


def test_text_fits_textbox():
    # _text() raises on overflow during build; double-check compiled SAY payloads
    for name, ops, mp in c.SCRIPTS:
        stack = list(ops)
        while stack:
            o = stack.pop()
            if o.kind == 'SAY':
                txt = o.args[0].rstrip(b'\0\v').decode()
                for page in txt.split('\f'):
                    lines = page.split('\n')
                    assert len(lines) <= 4, (name, page)
                    for ln in lines:
                        assert len(ln) <= 18, (name, ln)
            elif o.kind == 'IF':
                stack += o.args[1] + o.args[2]
            elif o.kind == 'CHOICE':
                stack += o.args[2] + o.args[3]
