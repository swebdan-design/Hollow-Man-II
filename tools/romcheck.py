#!/usr/bin/env python3
"""Validate the Game Boy Color cartridge header of the built ROM."""
import sys

NINTENDO_LOGO = bytes.fromhex(
    'CEED6666CC0D000B03730083000C000D0008111F8889000EDCCC6EE6DDDDD999BBBB67636E0EECCCDDDC999FBBB9333E')


def check(path, quiet=False):
    d = open(path, 'rb').read()
    res = {}
    errors = []
    res['size'] = len(d)
    res['title'] = d[0x134:0x13F].rstrip(b'\0').decode('ascii', 'replace')
    res['cgb_flag'] = d[0x143]
    res['cart_type'] = d[0x147]
    res['rom_size_code'] = d[0x148]
    res['ram_size_code'] = d[0x149]
    if d[0x104:0x134] != NINTENDO_LOGO:
        errors.append('boot logo mismatch')
    if d[0x143] != 0xC0:
        errors.append('CGB flag is not 0xC0 (CGB only)')
    if d[0x147] != 0x1B:
        errors.append('cartridge type is not 0x1B (MBC5+RAM+BATTERY)')
    if (32768 << d[0x148]) != len(d):
        errors.append('ROM size code %d does not match file size %d' % (d[0x148], len(d)))
    if d[0x149] != 0x02:
        errors.append('RAM size code is not 0x02 (8 KB)')
    x = 0
    for i in range(0x134, 0x14D):
        x = (x - d[i] - 1) & 0xFF
    res['header_checksum'] = d[0x14D]
    if x != d[0x14D]:
        errors.append('header checksum bad (%02X != %02X)' % (x, d[0x14D]))
    g = (sum(d) - d[0x14E] - d[0x14F]) & 0xFFFF
    res['global_checksum'] = (d[0x14E] << 8) | d[0x14F]
    if g != res['global_checksum']:
        errors.append('global checksum bad')
    if not quiet:
        print('ROM %s: %d bytes, title=%r, CGB=0x%02X, type=0x%02X, rom=%d, ram=%d, hdr=0x%02X, global=0x%04X' % (
            path, len(d), res['title'], res['cgb_flag'], res['cart_type'], res['rom_size_code'],
            res['ram_size_code'], res['header_checksum'], res['global_checksum']))
        print('HEADER OK' if not errors else 'HEADER ERRORS: ' + '; '.join(errors))
    return res, errors


if __name__ == '__main__':
    r, e = check(sys.argv[1])
    sys.exit(1 if e else 0)
