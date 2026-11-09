"""CHAPTER 4 - ST. AGNES.  Target: Sgt. Dacre.  Puzzle: bell, flame, hymn - in order."""
from content import *


def mech(step, name, done_text, ok_text):
    return iff('agnes_open', say(done_text),
               iff(('var', 'agnes', step),
                   [addvar('agnes', 1), sfx('door'), say(ok_text),
                    iff(('var', 'agnes', 3),
                        [setf('agnes_open'), sfx('solved'), shake(30),
                         say("Stone grinds on\nstone. Before the\naltar, the floor\nfolds into stairs."),
                         settile(7, 2, 'H')])],
                   [setvar('agnes', 0), sfx('deny'),
                    say("Nothing. Somewhere\nin the walls a\nmechanism clicks\nback to the start."),
                    iff(('var', 'agnes', 0), [])]))


nave = Map('ag_nave', 'interior', 'int_church', 'church', """
BDBBBWBBWBBBBB
B____a_A_a___B
B__________O_B
B_PPP____PPP_B
B____________B
B_PPP____PPP_B
BV___________B
B_PPP____PPP_B
B____________B
B_PPP____PPP_B
B____________B
BK__________KB
BKK________KKB
B____________B
B____________B
BBBBBBDBBBBBBB
""", district=5, flags=RESTRICTED, title='St. Agnes')
nave.door(6, 15, 'old', 10, 4, 'down')
nave.door(1, 0, 'ag_tower', 5, 7, 'up')
nave.patch(7, 2, 'H', 'agnes_open')
nave.door(7, 2, 'ag_crypt', 7, 1, 'down', cond='agnes_open')
nave.sign(5, 0, say("Stained glass. The\nletters run around\nthe saint's halo:",
                    "FIRST THE BELL\nCALLS. THEN THE\nFLAME IS LIT.\nLAST, THE HYMN."))
nave.sign(8, 0, say("A window of a saint\nholding a key over\na hole in the\nground."))
nave.sign(5, 1, mech(1, 'flame', "The candles burn\nsteadily.",
                     "You light the\ncandles. Eight\nwicks. One will\nnot take the flame."))
nave.sign(11, 2, mech(2, 'hymn', "The organ is\nsilent.",
                      "You press the\nkeys. A hymn, in a\nkey that hurts."))
nave.sign(9, 1, say("Candles, burnt down\nto stubs long ago."))
nave.sign(7, 1, iff('agnes_open', say("The altar has\nslid aside."),
                    say("The altar. Fresh\nscratches on the\nfloor in front of\nit. It moved.")))
nave.sign(1, 6, iff('confessed', say("The confessional\nis silent now."), [
    setf('confessed'),
    say("Inside the\nconfessional: a\ntape recorder,\nstill running."),
    ev('confession'),
    music('shadow'),
    say("Then a voice from\nthe empty booth.\nYour voice. Older."),
    choice("CONFESS. I WILL\nTELL YOU MY NAME.", "LISTEN", "LEAVE",
           [infl(6), say("IT WAS NEVER THEM\nYOU WANTED. IT WAS\nME. YOU WANTED\nME TO BE REAL.",
                         "The booth goes\ncold and quiet.")],
           [infl(-4), say("You leave the\nbooth. Behind you,\nsomething sighs.")]),
    music_resume()]))
nave.npc('dacre_npc', 7, 3, 'dacre',
         say("DACRE: ..."), cond=('not', 'dacre_fled'), d='down')
nave.enemy('police', 3, 10, 'h', 7, 'right', cond=('not', 'ch4_done'))
nave.search(12, 12, [say("Behind a pew:\na box of rounds\nand a bandage."), ammo(3), bandage(1)])
nave.on_enter(iff('dacre_fled', [], [
    setf('dacre_fled'),
    say("SGT. DACRE: Eleven\nyears I kept that\nfile closed. You\nopened it anyway.",
        "You want me? Learn\nto pray. The church\nonly opens for\nthe faithful."),
    sfx('heavy'), shake(20), ahide('dacre_npc'),
    say("Dacre vanishes\nbehind the altar.\nStone grinds shut\nbehind him."),
]))

tower = Map('ag_tower', 'interior', 'int_church', 'church', """
BBBBBBBBBB
B___R____B
B________B
B_S____S_B
B________B
BK______KB
B________B
B________B
BBBBBDBBBB
""", district=5, flags=RESTRICTED, title='Bell Tower')
tower.door(5, 8, 'ag_nave', 1, 1, 'down')
tower.sign(4, 1, mech(0, 'bell', "The bell rope hangs\nstill.",
                      "You haul the rope.\nThe bell calls\nonce over Old\nGloam."))
tower.search(2, 3, [say("A parish register.\n1958. A page is\nmarked with a\nblack ribbon."), ev('mercy4')])
tower.search(7, 3, [say("Spare candles and a\nbandage roll."), bandage(1)])
tower.enemy('wraith', 7, 6, 'static', 0, cond=('stage', 1))

crypt = Map('ag_crypt', 'under', 'und_crypt', 'church', """
bbbbbbbUbbbbbbbb
b......,.......b
b.C.C.C...C.C.Cb
b..............b
bcbbbbb.bbbbbbcb
b.....b.b......b
b.k...b.b..O...b
b.....b.b......b
bbb.bbb.bbbb.bbb
b..............b
b.Q..Q..K..Q..Qb
b..............b
b......KK......b
b..C..A..A..C..b
b..............b
bbbbbbbbbbbbbbbb
""", district=5, flags=RESTRICTED | DARKMAP, title='The Crypt')
crypt.door(7, 0, 'ag_nave', 7, 3, 'down')
crypt.enemy('police', 3, 9, 'h', 9, 'right', cond=('not', 'ch4_done'))
crypt.enemy('rat', 2, 6, 'wander')
crypt.enemy('rat', 12, 6, 'wander')
crypt.enemy('wraith', 13, 1, 'static', 0, cond=('not', 'ch4_done'))
crypt.search(1, 4, [say("A burial niche.\nSomeone hid revolver\nrounds with the\nbones."), ammo(4)])
crypt.search(14, 4, [say("A niche. A bottle\nof altar wine,\nempty."), bottle(1)])
crypt.pickup(4, 5, 'bandage')
crypt.boss('dacre', 7, 11, ('not', 'ch4_done'), [
    music(None),
    say("DACRE: I was a good\ncop once. Then Rusk\npaid better than\nthe city.",
        "We were sent to dig.\nUnder that house\nwas a door. Rusk\nwanted it opened.",
        "The family heard us.\nThe rest... the\nrest was the thing\nbehind the door."),
    sfx('kill'), flash(),
    say("Sergeant Dacre\nslumps against the\ncoffin he was\nhiding behind."),
    ev('police_memo'),
    give('evidence_key'), give('sluice_key'),
    say("On his belt: an\nEVIDENCE KEY and a\nCITY WORKS SLUICE\nKEY.",
        "Mott. The Drain.\nThe canal hatch."),
    setf('ch4_done'), music('jingle'),
    say("CHAPTER 4\nCOMPLETE.\nFour names."),
    music('church'), special('reset_revive'), savepoint(),
])
crypt.on_enter(iff('ch4_done', [], say("Somewhere below,\na pistol cocks.")))
