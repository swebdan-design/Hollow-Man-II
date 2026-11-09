"""packer.py - assigns generated data blobs to explicit ROM banks.

Code is auto-banked by GBDK's bankpack into banks 1..CODE_MAX_BANK.
All generated data goes to banks DATA_FIRST_BANK.. and is accessed from
bank-0 helpers (far_read / far_byte) so no unsafe cross-bank reads occur.
"""
import os

DATA_FIRST_BANK = 16
BANK_SIZE = 0x4000
BANK_RESERVE = 64


class Packer:
    def __init__(self):
        self.items = []       # (name, kind, payload, size, group)
        self.names = set()

    def blob(self, name, data, group=None):
        assert name not in self.names, name
        self.names.add(name)
        self.items.append((name, 'blob', bytes(data), len(data), group))

    def ccode(self, name, code, size, group=None):
        """Raw C definition (e.g. pointer tables)."""
        assert name not in self.names, name
        self.names.add(name)
        self.items.append((name, 'code', code, size, group))

    def pack(self, outdir, first_bank=DATA_FIRST_BANK):
        # items in the same group must share a bank; pack groups first-fit
        groups = {}
        order = []
        for it in self.items:
            key = it[4] or ('__' + it[0])
            if key not in groups:
                groups[key] = []
                order.append(key)
            groups[key].append(it)
        banks = []   # list of [used, [items]]
        self.bank_of = {}
        for key in order:
            its = groups[key]
            sz = sum(i[3] for i in its)
            if sz > BANK_SIZE - BANK_RESERVE:
                raise RuntimeError("group %s too large (%d)" % (key, sz))
            for bi, b in enumerate(banks):
                if b[0] + sz <= BANK_SIZE - BANK_RESERVE:
                    break
            else:
                banks.append([0, []])
                bi = len(banks) - 1
            banks[bi][0] += sz
            banks[bi][1].extend(its)
            for i in its:
                self.bank_of[i[0]] = first_bank + bi
        files = []
        hdr = ['#ifndef GEN_DATA_H', '#define GEN_DATA_H', '#include <stdint.h>', '']
        for bi, (used, its) in enumerate(banks):
            bank = first_bank + bi
            fn = os.path.join(outdir, 'data_bank%02d.c' % bank)
            with open(fn, 'w') as f:
                f.write('#pragma bank %d\n#include "hm.h"\n\n' % bank)
                for name, kind, payload, size, group in its:
                    if kind == 'blob':
                        f.write('const uint8_t %s[%d] = {\n' % (name, size))
                        for i in range(0, size, 24):
                            f.write('  ' + ','.join(str(b) for b in payload[i:i + 24]) + ',\n')
                        f.write('};\n')
                    else:
                        f.write(payload + '\n')
            files.append(fn)
            hdr.append('/* bank %d: %d bytes used */' % (bank, used))
            for name, kind, payload, size, group in its:
                if kind == 'blob':
                    hdr.append('extern const uint8_t %s[%d];' % (name, size))
                hdr.append('#define %s_BANK %d' % (name, bank))
        self.banks = banks
        self.last_bank = first_bank + len(banks) - 1
        return files, hdr
