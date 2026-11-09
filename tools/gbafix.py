#!/usr/bin/env python3
"""Fix up a GBA ROM header: boot logo, title, game code, maker, fixed byte, complement check.
Pads the ROM to a multiple of 256 bytes."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LOGO = bytes(int(x, 16) for x in open(os.path.join(HERE, 'gba_logo.txt')).read().split(','))


def fix(path, title=b'HOLLOWMAN', code=b'AHME', maker=b'SC'):
    d = bytearray(open(path, 'rb').read())
    d[0x04:0xA0] = LOGO
    d[0xA0:0xAC] = title.ljust(12, b'\0')[:12]
    d[0xAC:0xB0] = code
    d[0xB0:0xB2] = maker
    d[0xB2] = 0x96
    d[0xB3] = 0
    d[0xB4] = 0
    d[0xB5:0xBC] = bytes(7)
    d[0xBC] = 0
    chk = 0
    for b in d[0xA0:0xBD]:
        chk = (chk - b) & 0xFF
    d[0xBD] = (chk - 0x19) & 0xFF
    d[0xBE:0xC0] = bytes(2)
    while len(d) % 256:
        d.append(0xFF)
    open(path, 'wb').write(d)


def check(path):
    d = open(path, 'rb').read()
    errs = []
    if d[0x04:0xA0] != LOGO:
        errs.append('logo')
    if d[0xB2] != 0x96:
        errs.append('fixed byte')
    chk = 0
    for b in d[0xA0:0xBD]:
        chk = (chk - b) & 0xFF
    if d[0xBD] != (chk - 0x19) & 0xFF:
        errs.append('complement')
    if b'SRAM_V' not in d:
        errs.append('no SRAM save-type marker')
    return errs


if __name__ == '__main__':
    fix(sys.argv[1])
    e = check(sys.argv[1])
    print('GBA HEADER OK' if not e else 'GBA HEADER ERRORS: %s' % e, '(%d bytes)' % os.path.getsize(sys.argv[1]))
    sys.exit(1 if e else 0)
