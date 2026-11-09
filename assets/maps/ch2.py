"""CHAPTER 2 - COLD STORAGE.  Target: Hector Vale.  Puzzle: fuse + breaker order restores power."""
from content import *
import gloam

gloam.indust.on_enter(iff('ch1_done', iff('ch2_started', [], [setf('ch2_started'), chapter(2),
                      say("Vale Cold Storage.\nHector Vale cuts\nmeat for the whole\nsouth side.",
                          "Eleven years ago\nhe cut something\nelse.")])))

dock = Map('cs_dock', 'under', 'und_cold', 'indust', """
BBBBBBBSSBBBBBBB
BXX...........OB
BXX..O.....OO..B
B......mmmm....B
D......mmmm..XXB
B..KK.......KK.B
BOO.KK......KK.B
B..........O...B
BXX....hh....XXB
B.....K....K...B
B..............B
BBBBBBBDBBBBBBBB
""", district=3, flags=RESTRICTED, title='Loading Dock')
dock.door(7, 11, 'indust', 12, 3, 'down')
dock.door(0, 4, 'cs_freezer', 14, 4, 'left')
for x in (7, 8):
    dock.patch(x, 0, 'D', 'power_on')
    dock.door(x, 0, 'cs_floor', 6, 10, 'up', cond='power_on')
    dock.sign(x, 0, say("The loading bay\nshutter. No power.\nIt won't budge."), cond=('not', 'power_on'))
dock.enemy('gunman', 3, 3, 'v', 4, 'down', cond=('not', 'ch2_done'))
dock.enemy('thug', 10, 9, 'h', 4, 'left', cond=('not', 'ch2_done'))
dock.enemy('gunman', 12, 5, 'guard', 0, 'left', cond=('not', 'ch2_done'))
dock.search(14, 1, [say("A drum of rags.\nSomeone stashed\nrevolver rounds."), ammo(3)])
dock.search(5, 2, [say("Empty bottles\nfrom the night\nshift."), bottle(2)])
dock.sign(1, 1, say("NOTICE: Bay shutter\nruns off the main\ncircuit. Power room\nis past the freezer."))
dock.on_enter(iff('dock_seen', [], [setf('dock_seen'),
                                    say("Armed men on the\ndock. Use the dark\nfloor. A thrown\nbottle draws eyes.",
                                        "SELECT to equip a\nbottle. A throws it.")]))

freezer = Map('cs_freezer', 'under', 'und_cold', 'indust', """
FFFFFFFFFFFFFFFF
Ff.ff.ff.ff.fffF
FhfhfhfhfhfhfhfF
FfffffffffffffKF
FfffffffffffffKD
FFFFFFFfFFFFFFFF
FmmmmmmmmmmmmmmF
FffffffffffffffF
FfFFFFFfFFFFFfKF
FfF..TFfF.O.FfKF
FfF...FfF...FfKF
FfFFfFFfFFfFFffF
FfffffffffffffKF
FKKfffffffffffKF
DKKffffffffffffF
FFFFFFFFFFFFFFFF
""", district=3, flags=RESTRICTED, title='Freezer Corridors')
freezer.door(15, 4, 'cs_dock', 1, 4, 'right')
freezer.door(0, 14, 'cs_power', 8, 7, 'up')
freezer.hazard('saw', 1, 7, 'h', 12)
freezer.hazard('saw', 13, 12, 'h', 11)
freezer.hazard('saw', 1, 3, 'h', 11)
freezer.enemy('gunman', 2, 12, 'h', 9, 'right', cond=('not', 'ch2_done'))
freezer.enemy('thug', 7, 9, 'v', 3, 'down', cond=('not', 'ch2_done'))
freezer.search(5, 9, [say("A fire axe behind\nfrosted glass. You\nbreak the glass."),
                      give('axe'), special('equip_axe'),
                      say("Got the FIRE AXE.\nSlower, but it\nhits twice as hard.\nSwap in INVENTORY.")])
freezer.search(10, 9, [say("A locker. Inside,\nwrapped in a work\nglove: a heavy\ncartridge fuse."),
                       give('fuse'), say("Got a HEAVY FUSE.")])
freezer.sign(0, 7, say("NIGHT SHIFT: after\na blackout, start\ncompressor TWO,\nthen THREE, then\nONE. Or it trips."))
freezer.sign(15, 12, say("The cold here has\na smell. Copper.\nOld pennies."))
freezer.pickup(13, 1, 'bandage')
freezer.on_enter(iff('frz_seen', [], [setf('frz_seen'),
                                      say("Blades ride the\nrails between the\nhooks. Time your\nsteps.",
                                          "The conveyor belts\nslow you down.")]))


def breaker(k, step):
    return iff('power_on', say("Breaker %d: ON." % k),
               iff(('not', 'fuse_in'), say("Breaker %d.\nDead. No current\nto the board." % k),
                   iff(('var', 'breaker', step),
                       [addvar('breaker', 1), sfx('door'), say("Breaker %d: CLUNK.\nA compressor wakes." % k),
                        iff(('var', 'breaker', 3),
                            [setf('power_on'), sfx('solved'), shake(30), flash(),
                             say("The whole building\nshudders. Lights.\nCompressors roar.",
                                 "Far off, the\nloading bay\nshutter grinds\nopen.")])],
                       [setvar('breaker', 0), sfx('hurt'), shake(10), damage(1),
                        say("SPARKS! The board\ntrips. Every\nbreaker snaps back\nto OFF.")])))


power = Map('cs_power', 'under', 'und_cold', 'indust', """
BBBBBBBBBB
BBEBEBEBMB
B........B
B.O....O.B
B........B
B..T.....B
B........B
B.......KB
BBBBBBBBDB
""", district=3, flags=RESTRICTED, title='Power Room')
power.door(8, 8, 'cs_freezer', 1, 13, 'down')
power.sign(2, 1, breaker(1, 2))
power.sign(4, 1, breaker(2, 0))
power.sign(6, 1, breaker(3, 1))
power.sign(8, 1, iff('power_on', say("The main panel\nhums."),
                     iff('fuse_in', say("The fuse is seated.\nNow the breakers."),
                         iff(('item', 'fuse'),
                             [take('fuse'), setf('fuse_in'), sfx('key'), setvar('breaker', 0),
                              say("You seat the heavy\nfuse. The panel\nticks, waiting.")],
                             say("MAIN PANEL. The\n60A fuse socket\nis empty.")))))
power.sign(3, 5, say("A clipboard. Every\nnight shift since\nthe fire has signed\nout early."))
power.pickup(2, 6, 'ammo', 2)

floor = Map('cs_floor', 'under', 'und_cold', 'indust', """
BBBBBBBBBBBBBB
Bffffffffffff B
Bff M......Mf B
Bffffffffffff B
Bf....hh....f B
Bf..........f B
Bf.M......M.f B
Bf..........f B
Bf....mm....f B
Bf..........f B
Bf..........f B
BBBBBBDBBBBBBB
""".replace(' B', 'B').replace('ff M', 'ffM.'), district=3, flags=RESTRICTED, title='Processing Floor')
floor.door(6, 11, 'cs_dock', 7, 1, 'down')
floor.boss('hector', 6, 1, ('not', 'ch2_done'), [
    music(None),
    say("HECTOR: Mercy\nStreet. You think I\nremember every\nhouse I break?",
        "I remember that\none. The floor was\nwarm. Like\nsomething breathing\nunder it.",
        "Rusk's money is\nstill in my\nfreezer. Take it.\nTake all of it."),
    sfx('kill'), flash(),
    say("Hector Vale goes\nstill against the\nmachine he fed for\ntwenty years."),
    ev('manifest'),
    give('cutters'),
    say("Got the BOLT\nCUTTERS. The chain\non the Red Lantern\nunderpass..."),
    iff(('stage', 1),
        [shadow(64, 8), sfx('shadow'),
         say("YOU HESITATED.\nI DID NOT.|The voice comes\nfrom your own\nshadow."), shadow_hide()]),
    setf('ch2_done'), clrf('bell_at_strip'),
    music('jingle'),
    say("CHAPTER 2\nCOMPLETE.\nTwo names."),
    music('indust'),
    special('reset_revive'),
    savepoint(),
])
floor.on_enter(iff('ch2_done', [], [
    say("HECTOR: Thought I\nheard a fly in my\nfreezer.",
        "He is too heavy\nto stagger. Make\nhim charge into the\nmachines,",
        "or hold B and hit\nhim with every-\nthing you have."),
    special('pursuit')]))
