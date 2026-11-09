"""PyBoy-based harness for automated emulator tests and genuine screenshots."""
import os
import sys
import warnings

warnings.filterwarnings('ignore')
os.environ.setdefault('PYSDL2_DLL_PATH', '')
from pyboy import PyBoy  # noqa

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROM = os.path.join(ROOT, 'build', 'HOLLOW_MAN_II_THE_SECOND_SHADOW.gbc')


class Emu:
    def __init__(self, rom=ROM, ram_file=None, sound=False):
        kw = dict(window='null', cgb=True, log_level='ERROR')
        if not sound:
            kw['sound_emulated'] = False
        self.pb = PyBoy(rom, **kw)
        self.pb.set_emulation_speed(0)
        if ram_file and os.path.exists(ram_file):
            with open(ram_file, 'rb') as f:
                self.pb.load_state(f)

    def tick(self, n=1):
        for _ in range(n):
            self.pb.tick(1, False)
        self.pb.tick(1, True)

    def press(self, btn, frames=4, after=6):
        self.pb.button_press(btn)
        self.tick(frames)
        self.pb.button_release(btn)
        self.tick(after)

    def hold(self, btn, frames):
        self.pb.button_press(btn)
        self.tick(frames)
        self.pb.button_release(btn)
        self.tick(2)

    def shot(self, path, scale=2):
        im = self.pb.screen.image.convert('RGB')
        if scale != 1:
            im = im.resize((160 * scale, 144 * scale), 0)
        im.save(path)
        return im

    def mem(self, addr):
        return self.pb.memory[addr]

    def symbol(self, name):
        return self.pb.symbol_lookup(name)

    def stop(self):
        self.pb.stop(save=False)


def load_symbols(noi_path):
    syms = {}
    if not os.path.exists(noi_path):
        return syms
    for line in open(noi_path):
        p = line.split()
        if len(p) == 3 and p[0] == 'DEF':
            syms[p[1]] = int(p[2], 16)
    return syms
