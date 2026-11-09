"""GBA emulator tests: the real GBA ROM in headless mGBA (libmgba) via build/gba_harness."""
import os
import sys
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'tools'))
import worldlib  # noqa
import savefmt  # noqa
import gbafix  # noqa
from gba_emu import ROM, HARNESS  # noqa
from gba_play import GBot  # noqa

c, world, L = worldlib.load()
F, IT, EV = c.FLAGS, c.ITEM_ID, c.EV_ID
M = {m.name: i for i, m in enumerate(c.MAPS)}
SHOTS = os.path.join(HERE, '..', 'build', 'gba', 'shots')
os.makedirs(SHOTS, exist_ok=True)
TXT_SB = 0x0600F000   # BG1 text screenblock 30

pytestmark = pytest.mark.skipif(not (os.path.exists(ROM) and os.path.exists(HARNESS)),
                                reason='GBA ROM or harness not built')


def sram_img(*states):
    return savefmt.make_sram(*states) + bytes([0xFF]) * (32768 - 8192)


def boot_with(map_name, x, y, flags=(), items=(), evs=(), **kw):
    st = savefmt.make_state(M[map_name], x, y, flags=[F[f] for f in flags],
                            items=[IT['pipe']] + [IT[i] for i in items], evidence=[EV[e] for e in evs], **kw)
    e = GBot(sav=sram_img(st))
    e.continue_game()
    assert e.r8('cur_map') == M[map_name]
    return e


def text_row(e, row, x0=0, n=30):
    raw = e.peek(TXT_SB + row * 64, 64)
    out = ''
    for x in range(x0, x0 + n):
        t = (raw[x * 2] | (raw[x * 2 + 1] << 8)) & 0x3FF
        out += chr(t + 32) if t < 96 else ' '
    return out


def test_gba_header():
    assert gbafix.check(ROM) == []


def test_gba_title_and_menu():
    e = GBot()
    e.tick(240)
    assert e.r8('image_mode') == 1          # title illustration (title + credit drawn in it)
    e.shot(os.path.join(SHOTS, 'title.png'))
    e.press('start'); e.tick(40)
    assert 'NEW GAME' in text_row(e, 12)
    assert 'CONTINUE' in text_row(e, 13)
    e.stop()


def test_gba_new_game():
    e = GBot()
    e.new_game()
    assert e.r8('cur_map') == M['strip'] and e.gs('chapter') == 1 and e.pos() == (4, 5)
    e.walk('left', 2)
    assert e.pos() == (2, 5)
    e.stop()


def test_gba_save_load_roundtrip():
    e = boot_with('diner', 6, 6, flags=['ch1_done'], items=['eddie_keys'], chapter=1, influence=12, ammo=5)
    e.press('start'); e.tick(20)
    for _ in range(4):
        e.press('down', 2, 4)
    e.press('a'); e.tick(90)
    e.press('b'); e.tick(20)
    s = e.sram()
    okA, a = savefmt.parse(s, 'A')
    okB, b = savefmt.parse(s, 'B')
    assert okA and okB and b[savefmt.OFF['seq']] == 2 and b[savefmt.OFF['map']] == M['diner']
    e.stop()
    e2 = GBot(sav=s)
    e2.continue_game()
    assert e2.r8('cur_map') == M['diner'] and e2.gs('influence') == 12
    e2.stop()


def test_gba_corrupt_save_ignored():
    st = bytearray(savefmt.make_state(M['diner'], 6, 6))
    st[50] ^= 0xFF
    e = GBot(sav=sram_img(bytes(st)))
    e.tick(180); e.press('start'); e.tick(30); e.press('a'); e.tick(300)
    assert e.r8('cur_map') != M['diner']
    e.stop()


def test_gba_power_puzzle():
    e = boot_with('cs_power', 8, 7, flags=['ch1_done', 'indust_open'], items=['fuse'], chapter=2)
    e.interact((8, 1))
    e.interact((2, 1))
    assert not e.flag(F['power_on'])
    for x in (4, 6, 2):
        e.interact((x, 1))
    assert e.flag(F['power_on'])
    e.stop()


def test_gba_water_puzzle():
    e = boot_with('drain2', 1, 7, flags=['ch4_done'], items=['valve_wheel', 'sluice_key'], chapter=5)
    e.interact((1, 1))
    assert e.flag(F['west_low'])
    e.tick(60)
    assert e.goto((8, 2))
    e.interact((8, 1)); e.interact((8, 1))
    assert e.flag(F['east_low'])
    e.tick(60)
    assert e.goto((14, 12))
    e.shot(os.path.join(SHOTS, 'water.png'))
    e.stop()


def test_gba_church_sequence():
    e = boot_with('ag_tower', 5, 7, flags=['ch3_done', 'dacre_fled', 'old_open'], items=['church_key'], chapter=4)
    e.interact((4, 1))
    e.goto((5, 7)); e.walk('down', 1); e.tick(60); e.skip_text()
    assert e.r8('cur_map') == M['ag_nave']
    e.interact((5, 1)); e.interact((11, 2))
    assert e.flag(F['agnes_open'])
    e.stop()


def test_gba_lockdown():
    e = boot_with('rec_stacks', 12, 14, flags=['ch5_done', 'found_card', 'cage_open'], items=['evidence_key'], chapter=6)
    assert e.goto((5, 12))
    e.interact((6, 12))
    assert e.flag(F['lockdown_on']) and e.r8('lockdown_timer_on') == 1
    e.stop()


def test_gba_game_over_retry():
    e = boot_with('pawn_front', 5, 8, hp=1, chapter=1)
    e.poke(e.sym['gs'] + savefmt.OFF['hp'], 0)      # deterministic death
    e.tick(200)
    assert 'THE SHADOW' in text_row(e, 7)
    e.shot(os.path.join(SHOTS, 'gameover.png'))
    e.press('a'); e.tick(200)
    assert e.r8('cur_map') == M['pawn_front'] and e.gs('hp') >= 1
    e.stop()


def test_gba_music_player():
    e = GBot()
    e.tick(180); e.press('start'); e.tick(30)
    e.press('down', 2, 4); e.press('a'); e.tick(90)
    assert 'MUSIC PLAYER' in text_row(e, 1)
    assert 'Synth Centric' in text_row(e, 2)
    e.press('a'); e.tick(60)
    assert e.r8('music_cur') == 0
    e.press('b'); e.tick(10)
    assert e.r8('music_cur') == 0xFF
    e.stop()


def test_gba_chapter1_playthrough():
    e = GBot()
    e.new_game()
    e.goto((2, 4)); e.walk('up', 1); e.tick(60); e.skip_text()
    e.fight()
    e.goto((5, 1)); e.walk('up', 1); e.tick(60); e.skip_text()
    e.fight(kinds=(2,))
    e.goto((7, 6)); e.hold('right', 90); e.tick(10)
    e.goto((10, 3)); e.hold('right', 40); e.tick(10)
    e.interact((11, 4))
    e.goto((7, 10)); e.walk('down', 1); e.tick(60); e.skip_text()
    e.interact((9, 0))
    e.goto((9, 1)); e.walk('up', 1); e.tick(60); e.skip_text()
    assert e.r8('cur_map') == M['pawn_office']
    for _ in range(30):
        e.fight(max_steps=40)
        if not [a for a in e.actors() if a['type'] == 3] or e.gs('hp') == 0:
            break
    assert e.gs('hp') > 0
    e.skip_text(200)
    assert e.flag(F['ch1_done'])
    e.stop()


def _final(infl, secret=False):
    flags = ['ch%d_done' % i for i in range(1, 7)] + ['theatre_done', 'shadow_power', 'chapel_open']
    evs = []
    if secret:
        flags.append('mercy_done')
        evs = ['mercy%d' % i for i in range(1, 8)]
    e = boot_with('ward_chapel', 5, 10, flags=flags, items=['axe', 'pistol'], evs=evs, chapter=7,
                  influence=infl, ammo=12, bandages=3, weapon=1, maxhp=14, hp=14)
    # this test checks the ending logic: weaken Rusk so the simple bot always wins quickly
    for a in e.actors():
        if a['type'] == 3:
            e.poke(e.sym['actors'] + a['i'] * 28 + 10, 2)
    for _ in range(40):
        e.fight(max_steps=40)
        if not [a for a in e.actors() if a['type'] == 3] or e.gs('hp') == 0:
            break
    for _ in range(300):
        e.tick(20)
        if e.dlg_open():
            e.press('a', 3, 3)
        if e.r8('ending_id') != 0xFF and e.r8('game_state') == 1:
            break
    return e


@pytest.mark.parametrize('infl,secret,want', [(20, False, 0), (80, False, 1), (10, True, 2)])
def test_gba_endings(infl, secret, want):
    e = _final(infl, secret)
    assert e.r8('ending_id') == want
    e.stop()


def test_gba_tools_and_police():
    e = boot_with('indust', 1, 7, flags=['ch1_done', 'indust_open', 'shadow_power', 'ch2_started'],
                  items=['pistol'], chapter=2, ammo=4, bottles=2, influence=10)
    for want in (1,):
        for _ in range(6):
            if e.gs('tool') == want:
                break
            e.press('select', 2, 4)
    e.hold('right', 1); e.press('a', 2, 30)
    assert e.gs('ammo') == 3 and e.gs('alert') > 0
    e.stop()
    e = boot_with('strip', 4, 5, flags=['ch1_done'], chapter=1, alert=60)
    assert 3 in [a['kind'] for a in e.actors() if a['type'] == 2]
    e.stop()


def test_gba_recorded_title_track():
    """Synth Centric's recorded 'Intro' streams through Direct Sound on the title screen."""
    e = GBot()
    e.tick(150)
    assert e.r8('music_cur') == 0 and e.r8('st_on') == 1
    e.press('start'); e.tick(30)
    e.press('down', 2, 4); e.press('a'); e.tick(90)    # music player stops it
    assert e.r8('st_on') == 0
    e.press('a'); e.tick(30)                            # ...and plays it again (track 01)
    assert e.r8('st_on') == 1
    e.stop()
