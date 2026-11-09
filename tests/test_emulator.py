"""Emulator tests: run the real ROM in PyBoy (CGB mode) with scripted inputs and
crafted battery saves.  Requires the ROM to be built (make)."""
import os
import sys
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'tools'))
import worldlib  # noqa
import savefmt  # noqa
from play import Bot, SYM  # noqa
import romcheck  # noqa

c, world, L = worldlib.load()
F = c.FLAGS
IT = c.ITEM_ID
EV = c.EV_ID
M = {m.name: i for i, m in enumerate(c.MAPS)}
ROM = os.path.join(HERE, '..', 'build', 'HOLLOW_MAN_II_THE_SECOND_SHADOW.gbc')
SHOTS = os.path.join(HERE, '..', 'build', 'shots')
os.makedirs(SHOTS, exist_ok=True)

pytestmark = pytest.mark.skipif(not os.path.exists(ROM), reason='ROM not built')


def bg_text(e, row, vram_base=0x9800, width=20):
    out = ''
    for x in range(width):
        t = e.pb.memory[vram_base + row * 32 + x]
        out += chr(t + 32) if t < 96 else '?'
    return out


def boot_with(map_name, x, y, flags=(), items=(), **kw):
    fl = [F[f] for f in flags]
    it = [IT['pipe']] + [IT[i] for i in items]
    st = savefmt.make_state(M[map_name], x, y, flags=fl, items=it, **kw)
    e = Bot(ram=savefmt.make_sram(st))
    e.continue_game()
    assert e.r8('cur_map') == M[map_name]
    return e


def test_rom_header():
    res, errors = romcheck.check(ROM, quiet=True)
    assert errors == []
    assert res['cgb_flag'] == 0xC0 and res['cart_type'] == 0x1B and res['ram_size_code'] == 2


def test_title_screen_text():
    e = Bot()
    e.tick(240)
    e.shot(os.path.join(SHOTS, 'test_title.png'))
    assert bg_text(e, 4).strip() == 'THE SECOND SHADOW'
    assert bg_text(e, 5).strip() == 'by Synth Centric'
    e.stop()


def test_new_game_reaches_chapter1():
    e = Bot()
    e.new_game()
    assert e.r8('cur_map') == M['strip']
    assert e.gs('chapter') == 1
    assert e.pos() == (4, 5)
    e.walk('left', 2)
    assert e.pos() == (2, 5)
    e.stop()


def test_continue_unavailable_without_save():
    e = Bot()
    e.tick(180)
    e.press('start'); e.tick(30)
    # cursor starts on NEW GAME; moving down must skip the locked CONTINUE
    e.press('down'); e.tick(5)
    e.press('a'); e.tick(60)
    # selected item 2 = MUSIC PLAYER (not continue): game_state stays at title(0 before play)
    assert e.r8('cur_map') in (0xFF, 0)
    e.stop()


def test_save_and_load_roundtrip():
    e = boot_with('diner', 6, 6, flags=['ch1_done'], items=['eddie_keys'], chapter=1, influence=12, ammo=5)
    assert e.gs('influence') == 12 and e.gs('ammo') == 5
    # save from the pause menu (START, down x4 to SAVE, A)
    e.press('start'); e.tick(20)
    for _ in range(4):
        e.press('down', 2, 4)
    e.press('a'); e.tick(90)
    e.press('b'); e.tick(20)
    sram = e.sram()
    okA, a = savefmt.parse(sram, 'A')
    okB, b = savefmt.parse(sram, 'B')
    assert okA and okB, 'both slots valid (old save preserved, new save verified)'
    assert b[savefmt.OFF['seq']] == 2
    assert b[savefmt.OFF['map']] == M['diner']
    assert b[savefmt.OFF['influence']] == 12
    e.stop()
    # reload the written SRAM and continue: must resume in the diner
    e2 = Bot(ram=sram)
    e2.continue_game()
    assert e2.r8('cur_map') == M['diner']
    assert e2.gs('influence') == 12
    e2.stop()


def test_corrupt_save_ignored():
    st = bytearray(savefmt.make_state(M['diner'], 6, 6))
    st[50] ^= 0xFF   # corrupt a byte -> checksum mismatch
    e = Bot(ram=savefmt.make_sram(bytes(st)))
    e.tick(180)
    e.press('start'); e.tick(30)
    e.press('a'); e.tick(300)
    # cursor defaulted to NEW GAME (no valid save): the intro starts, not the diner
    assert e.r8('cur_map') != M['diner']
    e.stop()


def test_newest_slot_wins():
    a = savefmt.make_state(M['diner'], 6, 6, seq=4)
    b = savefmt.make_state(M['hale'], 5, 6, seq=5)
    e = Bot(ram=savefmt.make_sram(a, b))
    e.continue_game()
    assert e.r8('cur_map') == M['hale']
    e.stop()


def test_power_puzzle_wrong_then_right():
    e = boot_with('cs_power', 8, 7, flags=['ch1_done', 'indust_open'], items=['fuse'], chapter=2)
    e.interact((8, 1))          # seat fuse
    assert e.flag(F['fuse_in'])
    e.interact((2, 1))          # breaker 1 first: wrong
    assert not e.flag(F['power_on'])
    for x in (4, 6, 2):         # 2, 3, 1
        e.interact((x, 1))
    assert e.flag(F['power_on'])
    e.shot(os.path.join(SHOTS, 'test_power.png'))
    e.stop()


def test_water_level_puzzle():
    e = boot_with('drain2', 1, 7, flags=['ch4_done'], items=['valve_wheel', 'sluice_key'], chapter=5)
    e.auto_fight = True
    e.interact((1, 1))
    assert e.flag(F['west_low'])
    e.tick(60)
    assert e.goto((8, 2)), 'platform reachable once the west basin drains'
    e.interact((8, 1))          # fit wheel
    e.interact((8, 1))          # open valve B
    assert e.flag(F['east_low']) and not e.flag(F['west_low'])
    e.tick(60)
    assert e.goto((14, 12)), 'outfall reachable once the east basin drains'
    e.shot(os.path.join(SHOTS, 'test_water.png'))
    e.stop()


def test_records_lockdown_starts():
    e = boot_with('rec_stacks', 12, 14, flags=['ch5_done', 'found_card', 'cage_open'],
                  items=['evidence_key'], chapter=6)
    e.auto_fight = True
    assert e.goto((5, 12))
    e.interact((6, 12))
    assert e.flag(F['lockdown_on'])
    assert e.r8('lockdown_timer_on') == 1
    e.stop()


def test_church_sequence():
    e = boot_with('ag_tower', 5, 7, flags=['ch3_done', 'dacre_fled', 'old_open'], items=['church_key'], chapter=4)
    e.interact((4, 1))      # bell
    e.goto((5, 7)); e.walk('down', 1); e.tick(60); e.skip_text()
    assert e.r8('cur_map') == M['ag_nave']
    e.interact((5, 1))      # flame
    e.interact((11, 2))     # hymn
    assert e.flag(F['agnes_open'])
    e.stop()


def test_game_over_and_retry():
    e = boot_with('pawn_front', 5, 8, hp=1, chapter=1)
    for _ in range(60):
        e.fight(max_steps=10)
        if e.r8('image_mode'):
            break
    e.tick(120)
    e.shot(os.path.join(SHOTS, 'test_gameover.png'))
    assert 'THE SHADOW' in bg_text(e, 6)
    e.press('a'); e.tick(200)
    assert e.r8('cur_map') == M['pawn_front'] and e.gs('hp') >= 1
    e.stop()


def test_music_player_plays():
    e = Bot()
    e.tick(180)
    e.press('start'); e.tick(30)
    e.press('down', 2, 4)    # skips locked CONTINUE -> MUSIC PLAYER
    e.press('a'); e.tick(90)
    assert 'MUSIC PLAYER' in bg_text(e, 0)
    assert 'Synth Centric' in bg_text(e, 1)
    e.press('a'); e.tick(60)
    assert e.r8('music_cur') == 0
    e.shot(os.path.join(SHOTS, 'test_musicplayer.png'))
    e.press('b'); e.tick(10)
    assert e.r8('music_cur') == 0xFF
    e.stop()
