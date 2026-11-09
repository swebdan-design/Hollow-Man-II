"""Capture genuine emulator screenshots for the release (PyBoy, CGB mode)."""
import os
import sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', 'tests'))
import worldlib
import savefmt
from play import Bot

c, w, L = worldlib.load()
F, IT, EV = c.FLAGS, c.ITEM_ID, c.EV_ID
M = {m.name: i for i, m in enumerate(c.MAPS)}
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, '..', 'release', 'screenshots')
os.makedirs(OUT, exist_ok=True)


def shot(e, name):
    e.shot(os.path.join(OUT, name + '.png'), scale=2)
    print('saved', name)


def boot(map_name, x, y, flags=(), items=(), evs=(), **kw):
    st = savefmt.make_state(M[map_name], x, y, flags=[F[f] for f in flags],
                            items=[IT['pipe']] + [IT[i] for i in items], evidence=[EV[e] for e in evs], **kw)
    e = Bot(ram=savefmt.make_sram(st))
    e.continue_game()
    return e


# 1 title
e = Bot(); e.tick(260); shot(e, '01_title')
e.press('start'); e.tick(40); shot(e, '02_main_menu'); e.stop()

# 3 intro cutscene
e = Bot(); e.tick(180); e.press('start'); e.tick(30); e.press('a'); e.tick(200)
for i in range(9):
    e.press('a', 3, 50)
shot(e, '03_intro_photograph'); e.stop()

# 4 overworld
e = Bot(); e.new_game(); e.walk('right', 3); e.walk('down', 2); e.tick(10); shot(e, '04_gloam_commercial_strip'); e.stop()

# 5 combat
e = boot('pawn_front', 5, 8, chapter=1)
e.goto((6, 6)); e.tick(20)
for i in range(8):
    e.hold('up', 1); e.press('b', 2, 4)
    if i == 3:
        shot(e, '05_combat_pawnshop')
e.stop()

# 6 interior + stealth in the dock
e = boot('cs_dock', 7, 10, flags=['ch1_done', 'indust_open', 'dock_seen'], chapter=2)
e.walk('up', 2); e.tick(40); shot(e, '06_cold_storage_dock'); e.stop()

# 7 pause menu, casebook, shadow status, city map
e = boot('diner', 6, 7, flags=['ch1_done', 'ch2_done', 'shadow_power'], items=['eddie_keys', 'cutters', 'pistol'],
         evs=['photo', 'pawn_ledger', 'manifest', 'bell_notes'], chapter=3, influence=38, ammo=6, visited=0x0F)
e.press('start'); e.tick(30); shot(e, '07_pause_menu')
e.press('down', 2, 4); e.press('a'); e.tick(20); shot(e, '08_casebook_names')
e.press('a'); e.tick(20); e.press('a'); e.tick(20); shot(e, '09_casebook_entry')
e.press('b'); e.tick(10); e.press('b'); e.tick(20)
e.press('down', 2, 4); e.press('a'); e.tick(20); shot(e, '10_city_map')
e.press('b'); e.tick(20)
e.press('down', 2, 4); e.press('a'); e.tick(20); shot(e, '11_shadow_status')
e.press('b'); e.tick(20)
e.press('up', 2, 4); e.press('up', 2, 4); e.press('up', 2, 4); e.press('a'); e.tick(20); shot(e, '12_inventory')
e.stop()

# 13 second shadow sequence (mirror event)
e = boot('motel_hall', 13, 8, flags=['ch2_done', 'lantern_open', 'r6_open'], items=['room_key'], chapter=3, influence=10)
e.goto((12, 11)); e.hold('up', 1); e.press('a', 3, 10)
for i in range(4):
    e.press('a', 3, 40)
shot(e, '13_second_shadow_mirror'); e.stop()

# 14 final chapter
e = boot('ward_halls', 7, 10, flags=['ch6_done', 'ward_open', 'ward_seen'], chapter=7, influence=40, maxhp=14, hp=14)
e.walk('up', 5); e.tick(30); shot(e, '14_last_ward'); e.stop()

# 15 final boss
e = boot('ward_chapel', 5, 10, flags=['ch6_done', 'theatre_done', 'chapel_open'], chapter=7, influence=40, maxhp=14, hp=14)
e.walk('up', 3); e.tick(90); shot(e, '15_victor_rusk'); e.stop()

# 16 music player
e = Bot(); e.tick(180); e.press('start'); e.tick(30); e.press('down', 2, 4); e.press('a'); e.tick(60)
e.press('a'); e.tick(40); shot(e, '16_music_player'); e.stop()
