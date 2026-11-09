"""Boot a crafted save at every map on the GBA build and make a contact sheet."""
import os
import sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'tests'))
import worldlib, savefmt
from gba_play import GBot
from PIL import Image
c, w, L = worldlib.load()
M = {m.name: i for i, m in enumerate(c.MAPS)}
arrive = {}
for m in c.MAPS:
    for wp in m.warps:
        arrive.setdefault(wp[2], (wp[3], wp[4]))
arrive.setdefault('strip', (4, 5))
arrive['ward_basement'] = (5, 8)   # (1, 1) is the stairs tile: skipping the entry text there walks back up
fl = [c.FLAGS[f] for f in ('ch1_done', 'ch2_done', 'ch3_done', 'dacre_fled', 'theatre_done', 'eddie_seen', 'ward_seen',
                           'pf_seen', 'ps_seen', 'dock_seen', 'frz_seen', 'd1_seen', 'd2_seen', 'cel_seen', 'base_seen',
                           'ch2_started', 'ch3_started', 'ch4_started', 'ch5_started', 'ch6_started', 'bell6')]
out = os.path.join(HERE, '..', 'build', 'gba', 'tour')
os.makedirs(out, exist_ok=True)
tiles, bad = [], []
only = sys.argv[1:] or [m.name for m in c.MAPS]
for n in only:
    x, y = arrive[n]
    st = savefmt.make_state(M[n], x, y, flags=fl, chapter=4, influence=30)
    sav = bytearray(savefmt.make_sram(st)) + bytes([0xFF]) * (32768 - 8192)
    e = GBot(sav=bytes(sav))
    e.continue_game(); e.tick(30)
    if e.r8('cur_map') != M[n]:
        bad.append(n)
    p = os.path.join(out, n + '.png')
    e.shot(p, scale=1)
    tiles.append(p)
    e.stop()
cols = 5
sheet = Image.new('RGB', (cols * 240, ((len(tiles) + cols - 1) // cols) * 160))
for i, p in enumerate(tiles):
    sheet.paste(Image.open(p), ((i % cols) * 240, (i // cols) * 160))
sheet.save(os.path.join(out, 'contact.png'))
print('maps', len(tiles), 'failed', bad)
