"""Scripted-input helpers for emulator playtests."""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emu import Emu, load_symbols, ROOT  # noqa

SYM = load_symbols(os.path.join(ROOT, 'build', 'HOLLOW_MAN_II_THE_SECOND_SHADOW.noi'))
GS_OFF = dict(map=6, px=7, py=8, pdir=9, hp=10, maxhp=11, chapter=12, influence=13, alert=14,
              weapon=15, tool=16, ammo=17, bandages=18, bottles=19, items=20, evidence=24, flags=29)


class Play(Emu):
    def r8(self, name, off=0):
        return self.pb.memory[SYM['_' + name] + off]

    def w8(self, name, val, off=0):
        self.pb.memory[SYM['_' + name] + off] = val

    def gs(self, field):
        return self.r8('gs', GS_OFF[field])

    def pos(self):
        x = self.r8('pl_x') | (self.r8('pl_x', 1) << 8)
        y = self.r8('pl_y') | (self.r8('pl_y', 1) << 8)
        if x >= 0x8000:
            x -= 0x10000
        if y >= 0x8000:
            y -= 0x10000
        return ((x >> 4) + 8) >> 4, ((y >> 4) + 12) >> 4

    def dlg_open(self):
        return self.r8('dlg_is_open')

    def skip_text(self, max_presses=80):
        """press A until no dialogue is open for a while"""
        for _ in range(max_presses):
            self.tick(20)
            if not self.dlg_open():
                self.tick(20)
                if not self.dlg_open():
                    return
            self.press('a', 3, 3)

    def new_game(self):
        self.tick(180)
        self.press('start'); self.tick(30)
        self.press('a'); self.tick(30)
        for _ in range(60):
            self.press('a', 3, 40)
            if self.r8('cur_map') == 0 and self.r8('game_state') == 0 and not self.dlg_open() and self.r8('fade_level') == 0 and self.r8('image_mode') == 0:
                self.tick(40)
                if not self.dlg_open():
                    break
        self.skip_text()

    def continue_game(self):
        self.tick(180)
        self.press('start'); self.tick(30)
        self.press('a'); self.tick(200)
        self.skip_text()

    def walk(self, d, tiles):
        self.hold(d, int(tiles * 16 / 1.25) + 1)

    def flag_set(self, fid):
        a = SYM['_gs'] + GS_OFF['flags'] + (fid >> 3)
        self.pb.memory[a] |= 1 << (fid & 7)

    def flag(self, fid):
        a = SYM['_gs'] + GS_OFF['flags'] + (fid >> 3)
        return (self.pb.memory[a] >> (fid & 7)) & 1


DIRS = {(0, 1): 'down', (0, -1): 'up', (-1, 0): 'left', (1, 0): 'right'}
ACTOR_SIZE = 26


class Bot(Play):
    def mapdims(self):
        return self.r8('mh', 0), self.r8('mh', 1)

    def solid(self, x, y):
        w, h = self.mapdims()
        if not (0 <= x < w and 0 <= y < h):
            return True
        m = self.r8('map_grid', (y << 4) | x)
        return self.r8('mt_flags', m & 63) & 1

    def actors(self):
        out = []
        base = SYM['_actors']
        for i in range(12):
            a = base + i * ACTOR_SIZE
            t = self.pb.memory[a]
            if t:
                x = self.pb.memory[a + 2] | (self.pb.memory[a + 3] << 8)
                y = self.pb.memory[a + 4] | (self.pb.memory[a + 5] << 8)
                if x >= 0x8000: x -= 0x10000
                if y >= 0x8000: y -= 0x10000
                out.append(dict(i=i, type=t, kind=self.pb.memory[a + 1], px=x >> 4, py=y >> 4,
                                tx=((x >> 4) + 8) >> 4, ty=((y >> 4) + 12) >> 4,
                                hp=self.pb.memory[a + 10], state=self.pb.memory[a + 7]))
        return out

    def path(self, goal, adjacent_ok=False):
        from collections import deque
        start = self.pos()
        blocked = {(a['tx'], a['ty']) for a in self.actors() if a['type'] in (1, 2, 3)}
        q = deque([start])
        prev = {start: None}
        while q:
            c = q.popleft()
            if c == goal or (adjacent_ok and abs(c[0] - goal[0]) + abs(c[1] - goal[1]) == 1):
                p = []
                while c != start:
                    p.append(c)
                    c = prev[c]
                return p[::-1]
            for d in DIRS:
                n = (c[0] + d[0], c[1] + d[1])
                if n in prev or self.solid(*n):
                    continue
                if n in blocked and n != goal:
                    continue
                prev[n] = c
                q.append(n)
        return None

    def step_to(self, n):
        for _ in range(40):
            c = self.pos()
            if c == n:
                return True
            d = (n[0] - c[0], n[1] - c[1])
            if d not in DIRS:
                if abs(d[0]) + abs(d[1]) > 2:
                    return False
                d = (d[0], 0) if d[0] else (0, d[1])
            # keep the feet centred on the tile row/column while walking
            if d[1] == 0:
                y = self.r8('pl_y') | (self.r8('pl_y', 1) << 8)
                fy = ((y >> 4) + 12) & 15
                if fy < 5:
                    self.hold('down', 2)
                elif fy > 12:
                    self.hold('up', 2)
            else:
                x = self.r8('pl_x') | (self.r8('pl_x', 1) << 8)
                fx = ((x >> 4) + 8) & 15
                if fx < 5:
                    self.hold('right', 2)
                elif fx > 11:
                    self.hold('left', 2)
            self.hold(DIRS[d], 3)
            if self.dlg_open():
                self.skip_text()
        return self.pos() == n

    def goto(self, goal, adjacent_ok=False, tries=6):
        for _ in range(tries):
            if self.pos() == goal or (adjacent_ok and abs(self.pos()[0] - goal[0]) + abs(self.pos()[1] - goal[1]) == 1):
                return True
            p = self.path(goal, adjacent_ok)
            if not p:
                return False
            m0 = self.r8('cur_map')
            me = self.pos()
            near = [a for a in self.actors() if a['type'] == 2 and abs(a['tx'] - me[0]) + abs(a['ty'] - me[1]) <= 2
                    and (abs(a['tx'] - me[0]) + abs(a['ty'] - me[1]) <= 1 or self.path((a['tx'], a['ty']), True))]
            if near and self.auto_fight:
                self.fight(max_steps=120, kinds=(2,), radius=3)
                continue
            for n in p[:6]:
                if not self.step_to(n) or self.r8('cur_map') != m0:
                    break
            if self.r8('cur_map') != m0:
                return True
        return self.pos() == goal

    def face(self, target):
        c = self.pos()
        d = (target[0] - c[0], target[1] - c[1])
        d = (max(-1, min(1, d[0])), max(-1, min(1, d[1])))
        if d in DIRS:
            self.hold(DIRS[d], 1)

    def interact(self, target):
        if not self.goto(target, adjacent_ok=True):
            return False
        c = self.pos()
        if abs(c[0] - target[0]) + abs(c[1] - target[1]) != 1:
            return False
        self.face(target)
        self.press('a', 3, 6)
        self.skip_text()
        return True

    auto_fight = True

    def fight(self, max_steps=400, kinds=(2, 3), radius=99):
        self._unr = 0
        for _ in range(max_steps):
            if self.gs('hp') == 0:
                return False
            if self.dlg_open():
                self.skip_text()
            me = self.pos()
            en = [a for a in self.actors() if a['type'] in kinds and
                  abs(a['tx'] - me[0]) + abs(a['ty'] - me[1]) <= radius]
            if not en:
                return True
            en.sort(key=lambda a: abs(a['tx'] - me[0]) + abs(a['ty'] - me[1]))
            t = en[0]
            if abs(t['tx'] - me[0]) + abs(t['ty'] - me[1]) <= 1:
                x = self.r8('pl_x') | (self.r8('pl_x', 1) << 8)
                y = self.r8('pl_y') | (self.r8('pl_y', 1) << 8)
                if x >= 0x8000: x -= 0x10000
                if y >= 0x8000: y -= 0x10000
                dx, dy = t['px'] - (x >> 4), t['py'] - (y >> 4)
                if abs(dx) + abs(dy) < 6:
                    self.hold('up' if self.pos()[1] > 1 else 'down', 6)
                    continue
                if abs(dx) > abs(dy):
                    self.hold('right' if dx > 0 else 'left', 1)
                else:
                    self.hold('down' if dy > 0 else 'up', 1)
                self.press('b', 2, 14)
            else:
                p = self.path((t['tx'], t['ty']), adjacent_ok=True)
                if p:
                    self.step_to(p[0])
                else:
                    unreachable = getattr(self, '_unr', 0) + 1
                    self._unr = unreachable
                    if unreachable > 20:
                        self._unr = 0
                        return True
                    self.tick(10)
        return False
