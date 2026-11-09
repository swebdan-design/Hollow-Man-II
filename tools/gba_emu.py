"""Python driver for build/gba_harness (headless libmgba): scripted input, screenshots,
memory access via ELF symbols, SRAM extraction."""
import os
import subprocess
import tempfile
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROM = os.path.join(ROOT, 'build', 'gba', 'HOLLOW_MAN_THE_SECOND_SHADOW.gba')
ELF = os.path.join(ROOT, 'build', 'gba', 'hm.elf')
HARNESS = os.path.join(ROOT, 'build', 'gba_harness')
KEYS = dict(a=1, b=2, select=4, start=8, right=16, left=32, up=64, down=128, r=256, l=512)


def symbols():
    out = subprocess.check_output(['arm-none-eabi-nm', ELF]).decode()
    s = {}
    for line in out.splitlines():
        p = line.split()
        if len(p) == 3:
            s[p[2]] = int(p[0], 16)
    return s


class GBA:
    def __init__(self, sav=None):
        self.tmp = tempfile.mkdtemp()
        self.savpath = os.path.join(self.tmp, 'game.sav')
        if sav is not None:
            open(self.savpath, 'wb').write(sav)
        self.p = subprocess.Popen([HARNESS, ROM, self.savpath], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  text=True, bufsize=1)
        self.sym = symbols()
        self.held = 0

    def cmd(self, c):
        self.p.stdin.write(c + '\n')
        self.p.stdin.flush()
        return self.p.stdout.readline().strip()

    def keys(self, mask):
        self.held = mask
        self.cmd('keys %d' % mask)

    def tick(self, n=1):
        self.cmd('run %d' % n)

    def press(self, btn, frames=4, after=6):
        self.keys(KEYS[btn]); self.tick(frames); self.keys(0); self.tick(after)

    def hold(self, btn, frames):
        self.keys(KEYS[btn]); self.tick(frames); self.keys(0); self.tick(2)

    def shot(self, path, scale=2):
        ppm = os.path.join(self.tmp, 's.ppm')
        self.cmd('shot ' + ppm)
        im = Image.open(ppm).convert('RGB')
        if scale != 1:
            im = im.resize((240 * scale, 160 * scale), Image.NEAREST)
        im.save(path)
        return im

    def peek(self, addr, n=1):
        r = self.cmd('peek %x %d' % (addr, n)).split()[1:]
        return bytes(int(x, 16) for x in r)

    def poke(self, addr, v):
        self.cmd('poke %x %x' % (addr, v))

    def r8(self, name, off=0):
        return self.peek(self.sym[name] + off)[0]

    def r16(self, name, off=0):
        b = self.peek(self.sym[name] + off, 2)
        v = b[0] | (b[1] << 8)
        return v - 0x10000 if v >= 0x8000 else v

    def sram(self):
        """read the 32 KB battery SRAM through the bus (byte-wide, like the cartridge)"""
        out = b''
        for off in range(0, 32768, 4096):
            out += self.peek(0x0E000000 + off, 4096)
        return out

    def stop(self):
        try:
            self.cmd('quit')
        except Exception:
            pass
        self.p.wait(timeout=5)
