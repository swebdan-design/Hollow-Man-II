#!/usr/bin/env python3
"""Master asset build: graphics, music, illustrations, world content -> build/gen/*.c/h"""
import os
import sys
import glob
import importlib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, 'assets', 'maps'))

import packer
import build_tiles
import build_sprites
import build_music
import build_images
import content


def main(outdir, preview_dir):
    os.makedirs(outdir, exist_ok=True)
    os.makedirs(preview_dir, exist_ok=True)
    pk = packer.Packer()
    hdr = []
    dirs_c = []
    report = []
    report += build_tiles.generate(pk, hdr, preview_dir)
    dirlines, sheet_code = build_sprites.generate(pk, hdr, preview_dir)
    songs = build_music.generate(pk, hdr, dirs_c)
    img_ids = build_images.generate(pk, hdr, dirs_c, preview_dir)

    # world content
    legends = {name: build_tiles.legend(name) for name, _ in build_tiles.TILESETS}
    palsets = {n: i for i, n in enumerate(build_tiles.palettes.SETS)}
    music_ids = {s['id']: i for i, s in enumerate(songs)}
    sheets = {n: i for i, (n, pal, big) in enumerate(dirlines)}
    content.TILE_LEGENDS.update(legends)
    content.MUSIC.update(music_ids)
    content.IMAGES.update(img_ids)
    import world  # noqa  (assets/maps/world.py imports all chapter files)
    report += content.build(pk, hdr, dirs_c, legends, palsets, music_ids, sheets, img_ids,
                            build_tiles.TILESET_ID)

    # tileset directory (bank 0)
    dirs_c.append('const far_t tileset_dir[%d] = {' % len(build_tiles.TILESETS))
    for n, _ in build_tiles.TILESETS:
        dirs_c.append('  { ts_%s_BANK, ts_%s },' % (n, n))
    dirs_c.append('};')

    files, phdr = pk.pack(outdir)
    with open(os.path.join(outdir, 'gen_data.h'), 'w') as f:
        f.write('\n'.join(phdr + [''] + hdr + ['', '#endif', '']))
    with open(os.path.join(outdir, 'gen_dirs.c'), 'w') as f:
        f.write('/* generated - bank 0 directories */\n#include "hm.h"\n#include "gen_dirs.h"\n\n')
        f.write(sheet_code + '\n')
        f.write('\n'.join(dirs_c) + '\n')
    with open(os.path.join(outdir, 'gen_dirs.h'), 'w') as f:
        f.write('#ifndef GEN_DIRS_H\n#define GEN_DIRS_H\n#include "hm.h"\n')
        f.write('extern const sheet_t sheet_dir[];\nextern const far_t song_dir[];\n')
        f.write('extern const uint16_t note_table[84];\nextern const char * const song_title[];\n')
        f.write('extern const far_t image_dir[];\nextern const far_t map_dir[];\n')
        f.write('extern const far_t tileset_dir[];\n#endif\n')
    with open(os.path.join(outdir, 'data_files.txt'), 'w') as f:
        f.write(' '.join(os.path.basename(x) for x in files))
    report.append('data banks %d..%d' % (packer.DATA_FIRST_BANK, pk.last_bank))
    with open(os.path.join(outdir, 'asset_report.txt'), 'w') as f:
        f.write('\n'.join(report) + '\n')
    print('\n'.join(report))


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'build', 'gen'),
         sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, 'build', 'preview'))
