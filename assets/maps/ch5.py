"""CHAPTER 5 - THE DRAIN.  Target: Alec Mott.  Water-level puzzle with two valves."""
from content import *
import gloam

gloam.canal.on_enter(iff('ch4_done', iff('ch5_started', [], [setf('ch5_started'), chapter(5),
    say("The Drain runs\nunder all of Gloam.\nAlec Mott mapped\nevery inch of it.",
        "He mapped one\ntunnel in red.")])))

d1 = Map('drain1', 'under', 'und_sewer', 'drain', """
BBUBBBBBBBBBBBBB
B.......PPP....B
B..,.......K...B
B~~~~~=~~~~~~~~B
B~~~~~=~~~~~~~~B
B.....,....O...B
B.X.......BBBBBB
B.X.....,.B...eB
B.............KB
BBBBB..BBBB...KB
B......,.....B.B
B~~~~~~~~~=~~B.B
B~~~~~~~~~=~~B.B
B.........,....B
B.......K......D
BBBBBBBBBBBBBBBB
""", district=6, flags=DARKMAP, title='The Drain')
d1.door(2, 0, 'canal', 1, 9, 'down')
d1.door(15, 14, 'drain2', 1, 7, 'right')
d1.search(14, 7, [say("A maintenance\ncrate. Inside: a\nloose iron VALVE\nWHEEL."), give('valve_wheel'),
                  say("Got the VALVE\nWHEEL.")])
d1.search(14, 9, [say("A cassette in a\nplastic bag, taped\nto the pipe. A\nworkman's voice..."), ev('mercy5')])
d1.enemy('rat', 4, 5, 'wander')
d1.enemy('rat', 8, 13, 'wander')
d1.enemy('rat', 12, 1, 'wander')
d1.enemy('thug', 3, 8, 'h', 5, 'right', cond=('not', 'ch5_done'))
d1.pickup(1, 13, 'bandage')
d1.search(11, 5, [say("An oil drum.\nSomeone left a\nbox of rounds."), ammo(3)])
d1.on_enter(iff('d1_seen', [], [setf('d1_seen'), say("Water roars in the\nchannels. Too deep\nand too fast to\nswim.")]))

d2 = Map('drain2', 'under', 'und_sewer', 'drain', """
BBBBBBBBBBBBBBBB
BV.BBBBPVPBBBB.B
B..~~~...~~~...B
B..~~~...~~~...B
B..~~~...~~~...B
B..~~~...~~~...B
B..~~~.,.~~~...B
D..~~~...~~~...B
B..~~~...~~~...B
B..~~~...~~~...B
B..~~~...~~~...B
B..~~~...~~~...B
B..~~~...~~~...D
B..~~~..K~~~...B
BBBBBBBBBBBBBBBB
""", district=6, flags=DARKMAP, title='Sluice Works')
d2.door(0, 7, 'drain1', 14, 14, 'left')
d2.door(15, 12, 'drain3', 1, 5, 'right')
for y in range(2, 14):
    for x in (3, 4, 5):
        d2.patch(x, y, '=', 'west_low')
    for x in (9, 10, 11):
        d2.patch(x, y, '=', 'east_low')
d2.sign(1, 1, [say("SLUICE VALVE A.\nWEST BASIN."),
               iff('west_low', say("It's already open.\nThe west basin is\ndrained."),
                   [sfx('door'), shake(30), setf('west_low'), clrf('east_low'),
                    say("You heave the wheel.\nThe west basin\ngurgles and drops."
                        "|...and the east\nbasin rises."), redraw()])])
d2.sign(8, 1, iff(('not', 'v2_fitted'),
                  iff(('item', 'valve_wheel'),
                      [take('valve_wheel'), setf('v2_fitted'), sfx('key'),
                       say("You fit the loose\nvalve wheel onto\nthe shaft.")],
                      say("SLUICE VALVE B.\nEAST BASIN.\nThe wheel is\nmissing.")),
                  iff('east_low', say("Valve B is open."),
                      [sfx('door'), shake(30), setf('east_low'), clrf('west_low'),
                       say("Valve B turns. The\neast basin drains\nwith a roar.",
                           "Behind you, the\nwest basin floods\nback to the brim."), redraw()])))
d2.sign(14, 1, say("A painted sign:\nOPEN A TO REACH B.\nOPEN B TO REACH\nTHE OUTFALL."))
d2.enemy('rat', 7, 4, 'wander')
d2.enemy('rat', 13, 9, 'wander')
d2.pickup(7, 12, 'ammo', 2)
d2.on_enter(iff('d2_seen', [], [setf('d2_seen'),
                                say("Two basins, two\nvalves. The far\nside is out of\nreach. For now.")]))

d3 = Map('drain3', 'under', 'und_sewer', 'pursuit', """
BBBBBBBBBBBBUB
B.....,......B
B.~~~....~~~.B
B.~~~....~~~.B
B............B
D....OO......B
B............B
B.~~~....~~~.B
B.~~~....~~~.B
B......T.....B
B............B
BBBBBBBBBBBBBB
""", district=6, flags=DARKMAP, title="Mott's Outfall")
d3.door(0, 5, 'drain2', 14, 12, 'left')
d3.door(12, 0, 'canal', 13, 8, 'down', cond='ch5_done',
        lock=say("A ladder to the\ncanal. Mott has\nchained the hatch\nabove."))
d3.boss('mott', 6, 7, ('not', 'ch5_done'), [
    music(None),
    say("MOTT: Every pipe\nin this city leads\nback to that house.\nDid you know?",
        "Rusk had me find\nthe old tunnel. We\ncame up through the\ncellar floor.",
        "Crewe buried the\nfile. Records Annex.\nHe still has the\nkey to the cage."),
    sfx('kill'), flash(),
    say("Alec Mott sinks\ninto the black\nwater he knew so\nwell."),
    ev('sewer_survey'), give('basement_map'),
    say("Got the BASEMENT\nMAP. A cellar under\n13 Mercy Street.\nA red tunnel."),
    setf('ch5_done'), music('jingle'),
    say("CHAPTER 5\nCOMPLETE.\nFive names."),
    music('drain'), special('reset_revive'), savepoint(),
])
d3.on_enter(iff('ch5_done', [], say("MOTT: You followed\nthe water. Clever.\nThe water always\nfollows me back.",
                                    "He slips beneath\nthe surface. Watch\nthe ripples.")))
