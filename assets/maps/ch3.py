"""CHAPTER 3 - THE RED LANTERN.  Target: Nolan Pike.  Room-key puzzle, mirror event, pursuit."""
from content import *
import gloam

gloam.lantern.on_enter([
    iff('ch2_done', iff('ch3_started', [], [setf('ch3_started'), chapter(3),
        say("The Red Lantern.\nNolan Pike rents\nrooms by the hour\nand takes photos.",
            "He was the one who\nheld the camera\nthat night.")])),
    iff('ch3_done', iff('old_open', [], [setf('old_open'), settile(0, 7, '.'), settile(0, 8, '.')])),
])

office = Map('motel_office', 'interior', 'int_motel', 'motel', """
BBBBBBBBDB
B-S--o---B
B--------B
BCCcC----B
B--------B
B-t-T----B
B--------B
B--------B
BBBBDBBBBB
""", district=4, flags=0, title='Motel Office')
office.door(4, 8, 'lantern', 2, 4, 'down')
office.door(8, 0, 'motel_hall', 1, 7, 'right')
office.npc('clerk', 2, 2, 'clerk',
           iff('ch3_done', say("CLERK: Room six is\nyours if you want\nit. Nobody else\nwill sleep there."),
               say("CLERK: I didn't\nsee anything. I\nnever see anything.\nThat's the job.",
                   "The register's on\nthe counter. The\nkeys are on the\nboard. I'm on break.")),
           d='down')
office.search(3, 3, [say("GUEST REGISTER.\nRoom 6: N. LANE.\nPaid cash. Three\nmonths in advance.",
                         "N. LANE. Nolan.\nHe always did\nsign his work."), setf('read_register')],
              empty="ROOM 6: N. LANE.")
office.sign(5, 1, iff(('item', 'room_key'), say("The key board. The\nhook for 6 is\nempty now."),
                      iff('read_register',
                          [say("Six hooks. You\ntake the key for\nROOM 6."), give('room_key'),
                           say("Got the ROOM 6\nKEY.")],
                          say("Six hooks, six\nkeys. Which room\nis he in? The\nregister knows."))))
office.sign(2, 1, [say("A rack of motel\npostcards. A quiet\ncorner to rest."), savepoint()])

hall = Map('motel_hall', 'interior', 'int_motel', 'motel', """
BBBBBBBBBBBBBBBB
B-b-B-b--BB-b--B
B---B----BB----B
B-t-B-T--BB-T-pB
B---B----BB----B
BBLBBBBLBBBBBLBB
B--------------B
D--------------D
B--------------B
BBLBBBBLBBBBBLBB
B---B----BB-M--B
B-b-B-b--BB-b--B
B---B----BB----B
BK--B--T-BB--KKB
BK--B----BB--K-B
BBBBBBBBBBBBBBBB
""", district=4, flags=RESTRICTED, title='Motel Corridor')
hall.door(0, 7, 'motel_office', 8, 1, 'down')
hall.door(15, 7, 'motel_court', 1, 8, 'right', cond='motel_scene',
          lock=say("A fire door to the\ncourtyard. Chained\nfrom outside."))
hall.patch(13, 9, 'd', 'r6_open')
hall.patch(13, 5, 'd', 'nolan_fled')
hall.patch(2, 5, 'd', 'r1_open')
locked_room = say("A locked door. A\nTV murmurs behind\nit. Not his room.")
for x, y in ((7, 5), (2, 9), (7, 9)):
    hall.sign(x, y, locked_room)
hall.sign(2, 5, [say("Room 1. The lock is\ncheap. You lean on\nit until it gives."), sfx('door'),
                 setf('r1_open'), settile(2, 5, 'd')], cond=('not', 'r1_open'))
hall.sign(13, 9, iff(('item', 'room_key'),
                     [say("ROOM 6. The key\nturns."), sfx('key'), setf('r6_open'), settile(13, 9, 'd')],
                     [sfx('deny'), say("ROOM 6. DO NOT\nDISTURB. Locked.")]), cond=('not', 'r6_open'))
hall.sign(13, 5, iff('mirror_done',
                     [sfx('heavy'), shake(20),
                      say("Room 3 bursts open.\nNOLAN PIKE runs\npast you, camera\nbag flapping!",
                          "NOLAN: Not me! Not\nme! Go haunt\nsomebody else!",
                          "He crashes through\nthe fire door to\nthe courtyard."),
                      setf('nolan_fled'), setf('motel_scene'), settile(13, 5, 'd'), special('pursuit')],
                     say("Room 3. Locked.\nSomeone inside is\nbreathing very\nquietly.")),
          cond=('not', 'nolan_fled'))
hall.sign(12, 10, iff('mirror_done', say("The mirror is just\na mirror now. You\ndon't believe it."), [
    setf('mirror_done'), music('shadow'),
    say("A mirror. Your\nreflection wears\nthe suit and the\nmask.",
        "It does not move\nwhen you move."),
    shadow(64, 4), shake(10),
    say("BEHIND THE GLASS:\nYOU CAME BACK FOR\nTHEM. FOR ME.|I NEVER LEFT YOU."),
    iff('shadow_power',
        choice("Its hand presses\nthe glass.", "PRESS BACK", "LOOK AWAY",
               [infl(8), say("Cold. Familiar.\nIt grows stronger.")],
               [infl(-5), say("You look away.\nIt laughs like\nwater in a drain.")]),
        choice("Its hand presses\nthe glass.", "PRESS BACK", "BREAK GLASS",
               [infl(10), setf('shadow_power'), special('tool_shadow'),
                say("Cold pours into\nyour arm. SHADOW\ntool gained. SELECT\nto equip it.")],
               [infl(3), sfx('smash'), setf('shadow_power'),
                say("The glass breaks.\nThe cold is in\nyour hand anyway.",
                    "SHADOW tool gained.\nIt did not need\nyour permission.")])),
    shadow_hide(), music_resume(),
    say("Somewhere down the\nhall, a door\nrattles. Room 3.")]))
hall.search(1, 3, [say("Room 1. Bandages in\nthe bathroom."), bandage(1)])
hall.search(12, 11, [say("Nolan's bed. Under\nthe mattress: rounds\nfor a revolver."), ammo(4)])
hall.search(14, 3, [say("Room 3. Photos\npinned everywhere.\nThe same house.\nThe same eight."), ev('bell_notes')],
            cond='nolan_fled')
hall.enemy('thug', 1, 7, 'h', 12, 'right', cond=('not', 'ch3_done'))
hall.enemy('gunman', 8, 13, 'guard', 0, 'up', cond=('not', 'ch3_done'))
hall.noisemaker(7, 13, "A TV left on. You\nturn the volume all\nthe way up.")

court = Map('motel_court', 'city', 'city_neon', 'motel', """
RRRRRRRRRRRRRRRR
rrrrrrrrrrrrrrrr
BWBwBWBwBWBwBWBw
________________
_cv___~~~~___cv_
______~~~~______
_L____~~~~____L_
______~~~~______
__b___________h_
__U__U____U__U__
________________
_cv__________E__
________________
UUUUUUUDUUUUUUUU
""", district=4, flags=CITY, title='Motel Courtyard')
court.door(7, 13, 'lantern', 3, 14, 'down')
court.door(0, 8, 'motel_hall', 14, 7, 'left')
court.noisemaker(13, 11, "A payphone. It\nrings and rings.")
court.boss('nolan', 12, 6, ('not', 'ch3_done'), [
    music(None),
    say("NOLAN: Okay! Okay.\nI took the picture.\nThat's all I ever\ndid.",
        "Rusk wanted a\nrecord. Seven men\nat the door. He\nsaid count them.",
        "I counted eight.\nI've been counting\neight for eleven\nyears."),
    sfx('kill'), flash(),
    say("Nolan Pike's camera\nhits the pool and\nsinks without a\nsound."),
    ev('motel_ledger'),
    give('church_key'),
    say("In his coat: a\nledger and an iron\nkey wrapped in a\nrosary.", "Got the SACRISTY\nKEY. St. Agnes,\nOld Gloam."),
    setf('ch3_done'), music('jingle'),
    say("CHAPTER 3\nCOMPLETE.\nThree names."),
    music('motel'), special('reset_revive'), savepoint(),
])
court.on_enter(iff('ch3_done', [], say("Nolan scrambles\naround the pool.\nCorner him. He\ncan't run forever.")))
