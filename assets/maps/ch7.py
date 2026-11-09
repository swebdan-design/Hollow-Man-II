"""CHAPTER 7 - THE LAST WARD.  Target: Victor Rusk.  The Second Shadow intervenes. Final choice.
Also: the Mercy Street cellar (secret investigation)."""
from content import *

recep = Map('ward_recep', 'interior', 'int_ward', 'ward', """
BBBBBBDBBBBBBB
B,,,,,,,,,,,,B
B,CCcCC,,,s,,B
B,,,,,,,,,,,,B
B,T,,G,,G,,T,B
B,,,,,,,,,,,,B
BE,,,,,,,,,,KB
B,,,,,,,,,,,KB
B,,,,,,,,,,,,B
BBBBBBDBBBBBBB
""", district=7, flags=RESTRICTED, title='Reception')
recep.door(6, 9, 'wardroad', 7, 5, 'down')
recep.door(6, 0, 'ward_halls', 7, 10, 'up')
recep.enemy('gunman', 2, 5, 'h', 8, 'right', cond=('not', 'ch7_done'))
recep.enemy('gunman', 11, 1, 'guard', 0, 'left', cond=('not', 'ch7_done'))
recep.sign(4, 2, say("The reception desk.\nA visitors' book.\nThe last entry is\nyour own name."))
recep.search(10, 2, [say("A drug cabinet,\nforced open long\nago. Bandages\nremain."), bandage(2)])
recep.sign(1, 6, say("A service elevator.\nThe cables were cut\nfrom the inside."))
recep.sign(12, 6, [say("A nurses' alcove.\nA cot. Dust.\nRest while you\ncan."), savepoint()])

halls = Map('ward_halls', 'interior', 'int_ward', 'ward', """
BBBBBBBBBBBBBBBB
Bb,,B,b,,B,b,,,B
B,,,B,,,,B,,,,,B
BBdBBBBdBBBBdBBB
B,,,,,,,,,,,,,,B
B,,,,,,,,,,,,,,L
BBdBBBBdBBBBdBBB
Bb,,B,b,,B,b,,,B
B,,,B,,,,B,,G,,B
B,,,,,,,,,,,,,,B
BH,,,,,,,,,,,KKB
BBBBBBBDBBBBBBBB
""", district=7, flags=RESTRICTED | DARKMAP, title='Patient Wards')
halls.door(7, 11, 'ward_recep', 6, 1, 'down')
halls.door(1, 10, 'ward_basement', 1, 1, 'down', cond='theatre_done',
           lock=say("Stairs down. A gate\nof chain across\nthem. The chapel\nkey... later."))
halls.patch(15, 5, 'D', 'keycard_used')
halls.door(15, 5, 'ward_theatre', 1, 5, 'right', cond='keycard_used')
halls.sign(15, 5, iff(('item', 'keycard'),
                      [say("The keycard reader\nblinks green."), sfx('key'), setf('keycard_used'),
                       settile(15, 5, 'D')],
                      [sfx('deny'), say("SURGICAL THEATRE.\nSTAFF ONLY. A\nkeycard reader.")]),
           cond=('not', 'keycard_used'))
halls.search(12, 8, [say("A gurney. Under the\nsheet: a dead\norderly's keycard."), give('keycard'),
                     say("Got the WARD\nKEYCARD.")])
halls.npc('nurse', 2, 2, 'nurse',
          [say("NURSE: Visiting\nhours are over.\nThey've been over\nfor twenty years.",
               "NURSE: Dr. Rusk\nkept the children\nin the chapel. He\ncalled them doors."),
           iff(('stage', 2), say("NURSE: Oh. It's\nwith you. Then\nyou're expected.")),
           ahide('nurse')])
halls.enemy('wraith', 6, 4, 'static', 0)
halls.enemy('wraith', 11, 9, 'static', 0)
halls.enemy('gunman', 1, 9, 'h', 10, 'right', cond=('not', 'ch7_done'))
halls.search(6, 1, [say("Patient 13's bed.\nScratched into the\nframe: 8 8 8 8 8."), ammo(3)])
halls.search(11, 1, [say("A child's room. A\nbottle and gauze."), bottle(1), bandage(1)])
halls.sign(6, 7, say("A bed with leather\nstraps. The straps\nare torn from the\ninside."))

theatre = Map('ward_theatre', 'interior', 'int_ward', 'ward', """
BBBBBBBBBBBB
B,,,,,,,,,,B
B,,,GGG,,,,B
B,,,,,,,,,,B
B,s,,,,,,s,B
D,,,,,,,,,,B
B,,,,,,,,,,B
B,,,,,,,,,,B
B,,,,,,,,,,B
BBBBBBBBBBBB
""", district=7, flags=RESTRICTED, title='Surgical Theatre')
theatre.door(0, 5, 'ward_halls', 14, 5, 'left')
theatre.npc('g1', 4, 7, 'gunman', None, cond=('not', 'theatre_done'), d='up')
theatre.npc('g2', 8, 7, 'gunman', None, cond=('not', 'theatre_done'), d='up')
theatre.npc('g3', 6, 1, 'gunman', None, cond=('not', 'theatre_done'), d='down')
theatre.search(9, 4, [say("A steel cabinet.\nInside: a chapel\nkey and a letter."), give('chapel_key'),
                      say("Got the CHAPEL KEY.")], cond='theatre_done')
theatre.search(1, 4, [say("Surgical tools.\nAnd a medical kit."), bandage(2), ammo(3)], cond='theatre_done')
theatre.on_enter(iff('theatre_done', [], [
    say("Lights snap on. Men\nwith rifles in\nevery corner.",
        "GUARD: Dr. Rusk\nsays hello."),
    sfx('gun'), shake(10), redflash(), sfx('gun'), redflash(), sfx('hurt'), shake(20),
    say("Hollow Man drops to\none knee. Then to\nthe floor.",
        "The light is very\nfar away.", "..."),
    music('shadow'), fade_out(), wait(60), fade_in(),
    shadow(64, 20), shake(40), sfx('shadow'),
    say("The floor goes\nblack. The black\nstands up.",
        "It has horns. It\nhas your shoulders.\nIt does not hurry."),
    flash(), ahide('g1'), sfx('kill'), wait(20),
    flash(), ahide('g2'), sfx('kill'), wait(20),
    flash(), ahide('g3'), sfx('kill'), wait(30),
    say("Three screams. Then\nthree silences."),
    say("GET UP. WE ARE\nNOT FINISHED. I\nWILL NOT LET YOU\nFINISH WITHOUT ME."),
    shadow_hide(), infl(10), special('fullheal'),
    setf('theatre_done'), music_resume(),
    say("You are standing.\nYou don't remember\nstanding up.",
        "Your suit is wet.\nIt isn't your\nblood."),
    checkpoint(),
]))

base = Map('ward_basement', 'under', 'und_ward', 'ward', """
BUBBBBBBBBBBBBBB
B..,....PP.....B
B.O....,.......B
B.....BBBBB..O.B
B..K..B...B....B
B..K..B.k.B....B
B.....B...B..K.B
B.....BB.BB....B
B..............B
B.O..,.....O...B
B..............B
BBBBBBBBBBBBBlBB
""", district=7, flags=RESTRICTED | DARKMAP, title='Basement Tunnels')
base.door(1, 0, 'ward_halls', 1, 9, 'down')
base.patch(13, 11, 'D', 'chapel_open')
base.door(13, 11, 'ward_chapel', 5, 10, 'up', cond='chapel_open')
base.sign(13, 11, iff(('item', 'chapel_key'),
                      [say("The chapel key\nturns. The door\nis warm."), sfx('key'), setf('chapel_open'),
                       settile(13, 11, 'D')],
                      [sfx('deny'), say("CHAPEL. Locked.\nSomething on the\nother side is\nsinging.")]),
          cond=('not', 'chapel_open'))
base.enemy('rat', 4, 2, 'wander')
base.enemy('rat', 12, 9, 'wander')
base.enemy('wraith', 8, 5, 'static', 0)
base.enemy('thug', 2, 8, 'h', 10, 'right', cond=('not', 'ch7_done'))
base.search(13, 3, [say("A drum of old\nsupplies. Rounds\nand gauze."), ammo(4), bandage(1)])
base.search(2, 9, [say("A bottle of\nsurgical spirit,\nempty."), bottle(1)])
base.on_enter(iff('ch7_done', [], iff('base_seen', [], [setf('base_seen'),
    say("Below the hospital.\nThe walls sweat.\nThe chapel is at\nthe far end.")])))

chapel = Map('ward_chapel', 'interior', 'int_dark', 'final', """
BBBBWBBWBBBB
B____aAa___B
B__________B
B_PP____PP_B
B__________B
B_PP____PP_B
B__________B
B_PP____PP_B
B__________B
BK________KB
B__________B
BBBBBDBBBBBB
""", district=7, flags=RESTRICTED, title='The Ruined Chapel')
chapel.door(5, 11, 'ward_basement', 13, 10, 'down')
chapel.boss('rusk', 6, 3, ('not', 'ch7_done'), [
    music('shadow'),
    say("VICTOR RUSK: So.\nThe door walks in\nby itself.",
        "RUSK: I did not\nwant the family. I\nwanted what was\nunder their floor.",
        "RUSK: Something old.\nBuried by the\nchurch. Eight names,\nnever say the last.",
        "RUSK: The men dug.\nIt woke. It needed\na vessel. A child\nwith no one left."),
    say("RUSK: It has been\nwearing you for\neleven years. And\nyou thanked it by\nkilling for it."),
    sfx('kill'), flash(), shake(30),
    say("Victor Rusk falls\nbefore the altar.\nThe candles all go\nout at once."),
    give('chapel_key'),
    setf('ch7_done'),
    shadow(64, 8), sfx('shadow'), shake(40),
    say("The Second Shadow\nrises behind the\naltar. It is taller\nthan the chapel."),
    iff(('infl', 75),
        [redflash(), say("You are already\nkneeling. Your hand\nis already raised.",
                         "There is no choice\nleft to make. There\nhas not been for a\nlong time."),
         infl(10)],
        [iff(('infl', 50),
             say("It is so close now.\nYour own hands\nfeel like gloves."),
             say("It looks smaller\nthan you remember.\nOr you are larger.")),
         choice("LET ME IN.\nALL THE WAY IN.", "ACCEPT", "REFUSE",
                [infl(25), redflash(),
                 say("Cold fills you to\nthe top like a\nglass. You stop\nbeing cold.")],
                [infl(-15), flash(),
                 say("NOT TONIGHT.|You say it out\nloud. The shadow\nflinches.")])]),
    shadow_hide(),
    ending(),
])
chapel.on_enter(iff('ch7_done', [], [
    say("A ruined chapel.\nEight candles on\nthe altar. An old\nman in white.",
        "VICTOR RUSK: Come\nin. Your other half\nalready did."),
    special('pursuit')]))

cellar = Map('cellar', 'under', 'und_basement', 'shadow', """
BBBBBUBBBBBB
B..........B
B.k.......kB
B....A.....B
B..........B
BZ.........B
B..c....c..B
B..........B
B..........B
BBBBBBBBBBBB
""", district=1, flags=DARKMAP, title='The Cellar')
cellar.door(5, 0, 'mercy', 2, 12, 'down')
cellar.sign(5, 3, iff('mercy_done', say("The altar is cold\nand quiet."),
                      iff(('mercycount', 6),
                          [say("You know enough now\nto read it. Eight\nnames carved into\nthe stone."),
                           ev('mercy7'), setf('mercy_done'), music('shadow'), shake(30),
                           shadow(64, 8),
                           say("THE EIGHTH NAME.\nYou do not say it.\nYou do not need to."),
                           shadow_hide(), infl(-10),
                           say("The Mercy Street\ninvestigation is\ncomplete.")],
                          say("A stone altar under\nthe house. Carvings\nyou can't read yet.",
                              "Other pieces of\nthe story are still\nout in Gloam."))))
cellar.patch(1, 5, '.', 'cel_wall')
cellar.sign(1, 5, iff('shadowcast', [say("The wall dissolves\ninto cold smoke."), setf('cel_wall'),
                                     settile(1, 5, '.'), sfx('solved')],
                      say("A brick wall that\nbreathes. Behind\nit, a draught.")))
cellar.search(1, 6, [say("A hidden alcove.\nA rosary and a\ncassette: VICTOR\nRUSK."), special('maxhp_up'),
                     unlock('final'), say("MAX HEALTH UP.\n(New music in the\nMusic Player.)")],
              cond='cel_wall')
cellar.enemy('wraith', 9, 7, 'static', 0, cond=('not', 'mercy_done'))
cellar.on_enter(iff('cel_seen', [], [setf('cel_seen'),
    say("The cellar of 13\nMercy Street. The\nfire never reached\ndown here.")]))
