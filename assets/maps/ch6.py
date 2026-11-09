"""CHAPTER 6 - THE RECORDS ROOM.  Target: Silas Crewe.  Document search + timed lockdown."""
from content import *
import gloam

gloam.old.on_enter([
    iff('ch3_done', iff('ch4_started', [], [setf('ch4_started'), chapter(4),
        say("Old Gloam. The\nchurch, the\ncemetery, the\npolice records.",
            "Sergeant Dacre\nprays at St. Agnes\nevery night. He has\na lot to pray for.")])),
    iff('ch6_done', iff('bell6', [], [
        setf('bell6'), music('shadow'),
        say("DETECTIVE BELL is\nwaiting in the rain\noutside the annex.\nGun drawn. Low.",
            "BELL: Six bodies.\nSix men from one\nphotograph. And you\nhave the casefile.",
            "BELL: I read the\nmemo. Crewe buried\nit. Rusk paid for\nthe shovel.",
            "BELL: Give me a\ncopy. Let me end\nthis in a court-\nroom. Not a chapel."),
        choice("Give Bell a copy\nof the casefile?", "GIVE IT", "WALK AWAY",
               [setf('bell_trust'), infl(-10),
                say("You hand her the\ncopy. She doesn't\nthank you.",
                    "BELL: Rusk is at\nthe Last Ward. The\ngate code is in\nthe file. Go.",
                    "BELL: And if that\nthing behind you\nwins... I'll be\nthe one waiting.")],
               [infl(5),
                say("You walk past her.\nShe doesn't shoot.",
                    "BELL: Then I'll\nfollow the bodies.\nI always do.")]),
        music_resume()])),
])

lobby = Map('rec_lobby', 'interior', 'int_records', 'records', """
BBBBBDBBBBBB
B,,,,,,,,,,B
B,s,,,,,,,sB
B,,CCcCC,,,B
B,,,,,,,,,,B
B,T,,,,,,T,B
BK,,,,,,,,KB
BK,,,,,,,,,B
B,,,,,,,,,,B
BBBBBDBBBBBB
""", district=5, flags=RESTRICTED, title='Records Annex')
lobby.door(5, 9, 'old', 2, 14, 'down', cond=('not', 'lockdown_on'),
           lock=say("Steel shutters cover\nthe front doors.\nLOCKDOWN. Find\nanother way out."))
lobby.door(5, 0, 'rec_stacks', 12, 14, 'up')
lobby.enemy('gunman', 2, 4, 'h', 7, 'right', cond=('not', 'ch6_done'))
lobby.sign(5, 3, say("The front desk\nterminal. ANNEX\nLAYOUT: STACKS BY\nYEAR AND QUARTER.",
                     "EVIDENCE CAGE D-7:\nKEY HOLDERS ONLY."))
lobby.search(10, 2, [say("A filing cabinet.\nA visitor's pass\nand some bandages."), bandage(1)])
lobby.on_enter(iff('ch6_started', [], [setf('ch6_started'), chapter(6),
    say("The Records Annex.\nSomewhere in here\nis the casefile\nthat never closed.",
        "Case 11-0413. The\nnight of April\n13th, 2011.")]))

stacks = Map('rec_stacks', 'interior', 'int_records', 'records', """
BBBBBBBBBBBBBBDB
B,,,,,,,,,,,,,,B
B,SSSS,,SSSS,,,B
B,,,,,,,,,,,,,,B
B,SSSS,,SSSS,,,B
B,,,,,,,,,,,,,,B
B,SSSS,,SSSS,,,B
B,,,,,,,,,,,,,,B
B,SSSS,,SSSS,,,B
B,,,,,,,,,,,,,,B
BIIIILIII,,,,,,B
B,,,,,,,I,,KK,,B
B,ss,,s,I,,KK,,B
B,,,,,,,I,,,,,,B
BIIIIIIII,,,,,,B
BBBBBBBBBBBBDBBB
""", district=5, flags=RESTRICTED, title='The Stacks')
stacks.door(12, 15, 'rec_lobby', 5, 1, 'down')
stacks.door(14, 0, 'rec_office', 5, 7, 'up', cond='lockdown_on',
            lock=say("SUPERVISOR S. CREWE.\nLocked. A light is\non inside."))
nothing = "Nothing filed\nunder 11-0413 on\nthis shelf."
shelves = [(2, 2, '2008 - 2009'), (8, 2, '2010 JAN - JUN'), (2, 4, '2010 JUL - DEC'),
           (8, 4, '2011 JAN - MAR'), (2, 6, '2011 APR - JUN'), (8, 6, '2011 JUL - SEP'),
           (2, 8, '2011 OCT - DEC'), (8, 8, '2012 - 2013')]
for (x, y, label) in shelves:
    if label == '2011 APR - JUN':
        body = [say("SHELF: " + label),
                iff('found_card', say("The index card\nsays: CAGE D-7."),
                    [setf('found_card'), sfx('solved'),
                     say("A gap where a box\nshould be. Taped\nto the shelf, an\nindex card:",
                         "11-0413 MERCY ST.\nBOX MOVED TO CAGE\nD-7 BY ORDER OF\nS. CREWE.")])]
    else:
        body = [say("SHELF: " + label + "\n" + nothing)]
    for xx in range(x, x + 4):
        stacks.sign(xx, y, body)
stacks.patch(5, 10, 'd', 'cage_open')
stacks.sign(5, 10, iff(('item', 'evidence_key'),
                       iff('found_card',
                           [say("EVIDENCE CAGE D-7.\nDacre's key turns."), sfx('key'),
                            setf('cage_open'), settile(5, 10, 'd')],
                           say("The evidence cage.\nDozens of boxes.\nYou need to know\nwhich case first.")),
                       [sfx('deny'), say("EVIDENCE CAGE. D-7.\nLocked. A police\nkey is needed.")]),
            cond=('not', 'cage_open'))
stacks.sign(6, 12, iff(('ev', 'casefile'), say("The empty box.\nNothing left but\nthe smell of dust."), [
    say("Box 11-0413.\nInside: the\ncasefile. Heavier\nthan paper should\nbe."),
    ev('casefile'),
    sfx('alert'), shake(20), flash(),
    say("A siren whoops.\nRED LIGHTS. A voice\non the speakers:",
        "SECURITY LOCKDOWN\nIN 100 SECONDS.\nALL EXITS SEALING."),
    setf('lockdown_on'), alert(20), special('lockdown_start'), special('pursuit'),
    say("The lobby will be\nsealed. Crewe's\noffice has a side\ndoor. GO.")]))
stacks.search(2, 12, [say("A box of seized\nammunition."), ammo(5)])
stacks.enemy('gunman', 12, 3, 'v', 5, 'down', cond=('not', 'ch6_done'))
stacks.enemy('thug', 7, 1, 'h', 6, 'right', cond=('not', 'ch6_done'))
stacks.enemy('gunman', 10, 9, 'h', 4, 'right', cond='lockdown_on')
stacks.enemy('police', 13, 12, 'guard', 0, 'left', cond='lockdown_on')
stacks.noisemaker(13, 1, "A fire alarm\nbox. You smash it.\nBells ring in the\nwrong aisle.")

office = Map('rec_office', 'interior', 'int_records', 'records', """
BBBBBWBBBB
B..n..s..B
B..t.....B
B.S....S.B
B........B
B..T..T..B
B........B
B........B
BBBBBDBBBB
""", district=5, flags=RESTRICTED, title="Crewe's Office")
office.door(5, 8, 'old', 2, 14, 'down', cond='ch6_done',
            lock=say("The side door is\nbolted. Crewe has\nthe key."))
office.boss('crewe', 4, 3, ('not', 'ch6_done'), [
    music(None), special('lockdown_stop'), clrf('lockdown_on'),
    say("CREWE: I only\nmoved paper. Paper\nnever hurt anybody.",
        "Rusk said the boy\nwould come back.\nHe said the boy\nwould be the door.",
        "He's at the Last\nWard. He's waiting\nfor you. He's been\nwaiting for you."),
    sfx('kill'), flash(),
    say("Silas Crewe falls\nacross his own\ndesk. The lockdown\nsirens die."),
    ev('rusk_letter'),
    setf('ch6_done'), alertset(10), music('jingle'),
    say("CHAPTER 6\nCOMPLETE.\nSix names. One\nleft."),
    music('records'), special('reset_revive'), savepoint(),
])
office.on_enter(iff('ch6_done', [], say("CREWE: The file was\nsafe in the cage.\nNow you've made it\neveryone's problem.")))
