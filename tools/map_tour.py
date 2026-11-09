"""Boot a crafted save at the first warp-arrival point of every map and screenshot it."""
import os
import sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', 'tests'))
import worldlib
import savefmt
from play import Bot
from PIL import Image

c, w, L = worldlib.load()
M = {m.name: i for i, m in enumerate(c.MAPS)}
arrive = {}
for m in c.MAPS:
    for wp in m.warps:
        arrive.setdefault(wp[2], (wp[3], wp[4]))
arrive.setdefault('strip', (4, 5))
out = os.path.join(HERE, '..', 'build', 'tour')
os.makedirs(out, exist_ok=True)
names = [m.name for m in c.MAPS]
fl = [c.FLAGS[f] for f in ('ch1_done', 'ch2_done', 'ch3_done', 'dacre_fled', 'theatre_done', 'eddie_seen',
                           'ward_seen', 'pf_seen', 'ps_seen', 'dock_seen', 'frz_seen', 'd1_seen', 'd2_seen',
                           'cel_seen', 'base_seen', 'ch2_started', 'ch3_started', 'ch4_started', 'ch5_started',
                           'ch6_started', 'bell6')]
tiles = []
for n in names:
    x, y = arrive[n]
    st = savefmt.make_state(M[n], x, y, flags=fl, chapter=4, influence=30)
    e = Bot(ram=savefmt.make_sram(st))
    e.continue_game()
    e.tick(30)
    ok = e.r8('cur_map') == M[n]
    p = os.path.join(out, n + '.png')
    e.shot(p, scale=1)
    tiles.append((n, p, ok))
    e.stop()
cols = 6
sheet = Image.new('RGB', (cols * 160, ((len(tiles) + cols - 1) // cols) * 144))
for i, (n, p, ok) in enumerate(tiles):
    sheet.paste(Image.open(p), ((i % cols) * 160, (i // cols) * 144))
sheet.save(os.path.join(out, 'contact.png'))
print('maps', len(tiles), 'failed loads', [n for n, p, ok in tiles if not ok])
