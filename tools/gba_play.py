"""Test bot for the GBA build: reuses the GBC bot logic (tools/play.py) on the mGBA harness."""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gba_emu import GBA
from play import Bot, GS_OFF

ACTOR_SIZE = 28


class GBot(GBA, Bot):
    auto_fight = True

    def __init__(self, sav=None):
        GBA.__init__(self, sav)

    def r8(self, name, off=0):
        return GBA.r8(self, name, off)

    def actors(self):
        out = []
        base = self.sym['actors']
        raw = self.peek(base, ACTOR_SIZE * 12)
        for i in range(12):
            a = raw[i * ACTOR_SIZE:(i + 1) * ACTOR_SIZE]
            if not a[0]:
                continue
            x = a[2] | (a[3] << 8)
            y = a[4] | (a[5] << 8)
            if x >= 0x8000: x -= 0x10000
            if y >= 0x8000: y -= 0x10000
            out.append(dict(i=i, type=a[0], kind=a[1], px=x >> 4, py=y >> 4,
                            tx=((x >> 4) + 8) >> 4, ty=((y >> 4) + 12) >> 4, hp=a[10], state=a[7]))
        return out

    def flag(self, fid):
        return (self.r8('gs', GS_OFF['flags'] + (fid >> 3)) >> (fid & 7)) & 1

    def flag_set(self, fid):
        a = self.sym['gs'] + GS_OFF['flags'] + (fid >> 3)
        self.poke(a, self.peek(a)[0] | (1 << (fid & 7)))
