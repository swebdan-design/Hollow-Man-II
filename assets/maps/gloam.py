"""Gloam City overworld: seven districts connected edge to edge.

        [OLD GLOAM]  [RED LANTERN]  [WARD ROAD]
        [MERCY ST ]  [COMMERCIAL ]  [INDUSTRIAL]
                     [THE CANAL  ]  -> The Drain (underground)
Main roads: horizontal rows 7-8, vertical columns 7-8 on every district map.
"""
from content import *

CITY = OUTDOOR | RAIN


def gate_pair(m, cells, flagname, item, locked_text, open_text, open_tile='.'):
    """Chained gate tiles that open permanently with an item."""
    for (x, y) in cells:
        m.patch(x, y, open_tile, flagname)
    script = iff(flagname, [],
                 iff(('item', item),
                     [say(open_text), sfx('key'), setf(flagname)] +
                     [settile(x, y, open_tile) for (x, y) in cells] + [sfx('door')],
                     [sfx('deny'), say(locked_text)]))
    for (x, y) in cells:
        m.sign(x, y, script, cond=('not', flagname))


def police(m, spots):
    """Police patrols appear when the alert level rises."""
    for (x, y, lvl, mode) in spots:
        m.enemy('police', x, y, patrol=mode, rng=3, d='left', cond=('alert', lvl))


# ======================================================================= COMMERCIAL STRIP
strip = Map('strip', 'city', 'city_strip', 'gloam', """
RRRRRR_GG_RRRRRR
rrrrrr_.._rrrrrr
BSBWBB_.._BWBSBB
BWDBwB_.._BBwDBB
______:..:______
_L____:..:____L_
__b___:..:_h____
...............G
-------..------G
______:..:______
_E____:..:__M___
BBWBBB:..:QQQQQQ
BDBBwB:..:QqQQQQ
;;;KKK:..:KKK;;;
;T;KKK:..:KKK;T;
UUUUUU_.._UUUUUU
""", district=2, flags=CITY, title='Commercial Strip')
strip.exit(n='lantern', s='canal', w='mercy', e='indust')
strip.door(2, 3, 'pawn_front', 5, 8, 'up')
strip.door(13, 3, 'diner', 5, 7, 'up')
strip.door(1, 12, 'apartment', 5, 7, 'up')
gate_pair(strip, [(15, 7), (15, 8)], 'indust_open', 'eddie_keys',
          "A chained gate.\nA tag on the chain:\nVALE COLD STORAGE.",
          "Eddie's keyring.\nThe third key\nturns the padlock.")
gate_pair(strip, [(7, 0), (8, 0)], 'lantern_open', 'cutters',
          "The underpass to\nthe Red Lantern is\nchained shut.\nThick links.",
          "The bolt cutters\nbite. The chain\nfalls into the\nrain.")
strip.sign(1, 2, say("PAWN & PRAY.\nWE BUY GOLD.\nNO QUESTIONS."))
strip.sign(13, 2, say("NITE OWL DINER.\nOPEN ALL NIGHT.\nPIE."))
strip.noisemaker(1, 10, "A payphone. It\nrings once when\nyou touch it, too\nloud in the rain.")
strip.search(2, 6, [bottle(1), say("An empty bottle\nin the bin. It\nwould make a fine\ndistraction.")])
strip.sign(11, 12, say("A loading shutter.\nPadlocked from\nthe inside."))
strip.sign(12, 10, iff('ch1_done', say("BUS TIMETABLE.\nLast bus: 11:52.\nSomeone has drawn\nhorns on the map."),
                       say("BUS TIMETABLE.\nNo buses after\nmidnight.")))
strip.npc('vagrant', 5, 10, 'vagrant',
          iff('ch1_done',
              iff(('stage', 1),
                  say("VAGRANT: Don't\nturn around. It\nlikes it when you\nturn around."),
                  say("VAGRANT: Eddie's\ngone quiet. Good.\nHe sold my coat\nonce.")),
              say("VAGRANT: Eddie\nkeeps a man on the\nshop floor. Big\nguy. Bad eyes.",
                  "Stay in the dark\nby the walls. He\nonly sees what's\nin front of him.",
                  "And if you come at\na man from behind,\nhe never knows.")),
          move='static', d='right')
strip.npc('citizen', 12, 5, 'citizen',
          iff('ch2_done',
              say("They found Hector\nVale in his own\nfreezer. I'm\nmoving to Ohio."),
              say("Lady, I mean,\nmister, the whole\nstrip is wrong\ntonight.",
                  "There were seven\nnames in the\nreport. Everybody\nknows that.")),
          move='wander')
strip.npc('bell1', 10, 4, 'bell',
          [say("DETECTIVE BELL:\nMara Bell. Gloam\nHomicide.",
               "Eddie Voss is\ndead and the door\nwas locked from\nthe inside.",
               "Funny. You look\nlike a man who\nhas keys."),
           say("...", "BELL: I don't\nbelieve in ghosts.\nI believe in\nfingerprints.",
               "Leave town. Or\nleave me a trail.\nI'll find the end\nof it."),
           setf('bell_met1'), ev('bell_notes')],
          cond='bell_at_strip', d='left')
strip.on_enter(iff('ch1_done', iff('bell_met1', [], say("Blue lights on\nwet brick. Someone\nis waiting by the\ndiner."))))
police(strip, [(3, 7, 1, 'h'), (12, 8, 2, 'h'), (7, 11, 3, 'v')])
strip.pickup(14, 14, 'bandage')

# ======================================================================= DINER (safe)
diner = Map('diner', 'interior', 'int_warm', 'gloam', """
BBWBBBBBWBBB
B,,,,,,,,,,B
BC c CCCC,,B
B,,,,,,,,,,B
BT,T,,T,T,,B
Bt,t,,t,t,,B
B,,,,,,,,,,B
B,,,,,,,,,,B
B,,,,,D,,,,B
""".replace(' ', 'C'), district=2, flags=SAFE, title='Nite Owl Diner')
diner.door(6, 8, 'strip', 13, 4, 'down')
diner.npc('waitress', 4, 1, 'oldwoman',
          [say("DOT: Coffee's\nburnt. Pie's\nworse. Sit down\nanyway, hon."),
           iff(('stage', 2),
               say("DOT: Your shadow\njust moved, hon.\nI'm gonna pretend\nit didn't."),
               say("DOT: The phone\nin the back works.\nUse it if you need\nto rest a while.")),
           heal(10), say("You drink the\ncoffee. It helps.")])
diner.sign(10, 1, [say("The diner's back\nphone. A quiet\ncorner. Nobody\nwatches here."), savepoint()])
diner.npc('trucker', 8, 4, 'citizen',
          iff('ch3_done',
              say("TRUCKER: Old Gloam\ncordon's down.\nCops are crawling\nall over St. Agnes."),
              say("TRUCKER: Red\nLantern's chained\noff since the\nfire. Need cutters.")),
          d='left')
diner.search(1, 4, [say("Under the table:\na cassette tape.\nTRACK: MERCY ST."), unlock('mercy'),
                    say("(New music in the\nMusic Player.)")])
diner.sign(9, 2, say("A jukebox. Every\nsong is about\nleaving town."))

# ======================================================================= APARTMENT (lore)
apt = Map('apartment', 'interior', 'int_dark', None, """
BBBBWBBBBB
B....b...B
B..r.....B
B....T.p.B
B....t...B
BK.......B
BKK......B
BKKK.v...B
BBBBBDBBBB
""", district=2, flags=DARKMAP, title='Apartment 3B')
apt.door(5, 8, 'strip', 1, 13, 'down')
apt.sign(5, 7, say("The TV hisses.\nBetween the static,\na face with horns\nflickers once."))
apt.search(7, 3, [say("Behind the dead\nplant: a rosary\nand a note: FOR\nWHEN IT COMES."), special('maxhp_up'),
                  say("Your heart beats\nharder.\nMAX HEALTH UP.")])
apt.search(5, 1, [say("A child's bed.\nUnder the pillow:\nbandages."), bandage(2)])
apt.on_enter(say("Apartment 3B.\nThe family left in\na hurry. The door\nwasn't locked."))

# ======================================================================= MERCY STREET
mercy = Map('mercy', 'city', 'city_mercy', 'mercy', """
;;;;;;;XX;;;;;;;
;T;\"\"\"_.._\"\"\";T;
RRRR\"\"_.._\"\"RRRR
rrrr\"\"_.._\"\"rrrr
BwBD\"\"_.._\"\"DBxB
F_FF__:..:__FF_F
\"_\"___:..:___\"_\"
##..............
##-------..-----
\"\"____:..:______
\"PPPP\":..:\"YY\"y\"
\"PppP\":..:\"\"\"\"\"\"
\"PppP\":..:\"\"\"T\"\"
\"PPPP\":..:\"\"\"\"\"\"
;;;;;;:..:;;;;;;
;;;;;;;;;;;;;;;;
""", district=1, flags=CITY, title='Mercy Street')
mercy.exit(n='old', e='strip')
mercy.door(3, 4, 'hale', 5, 7, 'up')
mercy.door(12, 4, 'oldhouse', 5, 7, 'up')
for x in (7, 8):
    mercy.patch(x, 0, '.', 'old_open')
mercy.sign(7, 0, say("POLICE LINE.\nDO NOT CROSS.\nOld Gloam is\nclosed tonight."), cond=('not', 'old_open'))
mercy.sign(8, 0, say("POLICE LINE.\nDO NOT CROSS."), cond=('not', 'old_open'))
mercy.patch(3, 12, 'H', 'cellar_open')
mercy.door(3, 12, 'cellar', 5, 2, 'down', cond='cellar_open')
mercy.search(2, 11, [say("Ash and glass.\nA scrap of paper\nthe fire didn't\nwant."), ev('mercy1')],
             empty="Only ash now.")
mercy.sign(3, 12,
           iff('cellar_open', [],
               iff(('item', 'basement_map'),
                   iff(('item', 'house_key'),
                       [say("The map shows a\ncellar door under\nthe kitchen. The\nhouse key fits."),
                        sfx('key'), setf('cellar_open'), settile(3, 12, 'H'), sfx('solved')],
                       say("Mott's map marks a\ncellar door here.\nIt's locked. You\nneed a house key.")),
                   say("Burnt boards. The\nfloor sounds\nhollow when you\nstep here."))))
mercy.sign(4, 10, say("13 MERCY STREET.\nThe number is\nstill on the\nmailbox."))
mercy.sign(11, 10, say("A swing moves.\nThere is no wind."))
mercy.npc('kid', 13, 11, 'citizen',
          [say("KID: My brother\nsays that house\neats people.",
               "KID: I saw a man\nthere last night.\nHe was really tall.\nHe had horns.")],
          move='wander')
police(mercy, [(9, 7, 2, 'h')])
mercy.pickup(14, 13, 'bottle')

hale = Map('hale', 'interior', 'int_warm', 'mercy', """
BBWBBBBWBB
B..r.....B
B..r..T..B
B.....t..B
Bb....S.pB
B........B
B..o.....B
B........B
BBBBBDBBBB
""", district=1, flags=SAFE, title="Mrs. Hale's House")
hale.door(5, 8, 'mercy', 3, 5, 'down')
hale.npc('mrs_hale', 3, 2, 'oldwoman', [
    iff(('ev', 'mercy6'),
        say("MRS. HALE: Go\ndown there. End it.\nOr let it end you.\nEither is mercy."),
        iff(('item', 'basement_map'),
            [say("MRS. HALE: That\nmap... so it's\ntrue. There is a\ncellar.",
                 "I never told the\npolice. I counted\neight men going\ninto that house.",
                 "Seven came out.\nThe eighth walked\naway... wearing the\nboy's shadow."),
             ev('mercy6')],
            iff('ch3_done',
                iff(('item', 'house_key'),
                    say("MRS. HALE: The\nkey is yours now.\nI don't want it\nin my house."),
                    [say("MRS. HALE: You.\nI know that suit.\nI know who you\nwere. The boy.",
                         "Take this. The\nfamily left me a\nkey before... that\nnight."),
                     give('house_key'),
                     say("Got the HOUSE KEY.")]),
                iff('ch2_done',
                    iff(('ev', 'mercy2'), say("MRS. HALE: Some\nnights I still hear\nthe scratching."),
                        [say("MRS. HALE: The\ngirl's diary. I\nfound one page in\nmy garden."),
                         ev('mercy2')]),
                    say("MRS. HALE: Nobody\nlives in that\nhouse. Nobody has\nfor eleven years.",
                        "Come back when\nyou've done what\nyou came to do."))))),
], d='down')
hale.sign(6, 4, [say("Mrs. Hale's sewing\nchair. A blanket.\nA moment's rest."), savepoint()])
hale.sign(3, 6, say("Photographs of\nMercy Street before\nthe fire. Children\nplaying."))

oldhouse = Map('oldhouse', 'interior', 'int_dark', 'mercy', """
BBBBBWBBBB
BKK...p..B
BK.......B
B..T..XX.B
B..t..X..B
B......K.B
BZ.....KKB
B.......KB
BBBBBDBBBB
""", district=1, flags=DARKMAP, title='Abandoned House')
oldhouse.door(5, 8, 'mercy', 12, 5, 'down')
oldhouse.patch(1, 6, '.', 'oh_wall')
oldhouse.sign(1, 6, iff('shadowcast', [say("The wall softens\nlike wet paper and\ncollapses inward."),
                                       setf('oh_wall'), settile(1, 6, '.'), sfx('solved')],
                        say("A cold patch of\nwallpaper. It\nbreathes when you\nstand close.")))
oldhouse.search(1, 7, [say("Behind the wall: a\nsmall shrine. A\ncassette labelled\nTHE EIGHTH MAN."), unlock('shadow'),
                       ammo(3), say("(New music in the\nMusic Player.)")], cond='oh_wall')
oldhouse.enemy('rat', 3, 6, 'wander')
oldhouse.enemy('rat', 7, 2, 'wander')
oldhouse.pickup(8, 1, 'bandage')

# ======================================================================= INDUSTRIAL QUARTER
indust = Map('indust', 'city', 'city_indust', 'indust', """
QQQQQQQQQQQQQQQQ
QQQQQQQQQQQQQQQQ
QqQQQQQQQQQQDQQQ
_____________b__
_OO_C____C______
_OO_C_OO_C_OO_h_
____C_OO_C_OO___
................
----------------
______._________
_OO_OO._OOO__OO_
_OO_OO._OOO__OO_
______._____KKKK
QQQQQQ._QQQQKKKK
QQqQQQ._QQqQKKKK
QQQQQQQQQQQQQQQQ
""", district=3, flags=CITY, title='Industrial Quarter')
indust.exit(w='strip')
indust.door(12, 2, 'cs_dock', 7, 10, 'up')
indust.sign(12, 3, say("VALE COLD STORAGE\nMEAT - PRODUCE\nDELIVERIES REAR"), cond=None)
indust.enemy('thug', 2, 3, 'h', 6, 'right')
indust.enemy('thug', 13, 12, 'guard', 0, 'left')
indust.enemy('runner', 10, 9, 'h', 4, 'left')
indust.search(14, 13, [say("A dropped toolbox.\nRevolver rounds\nwrapped in a rag."), ammo(4)])
indust.sign(2, 14, say("Rusted shutter.\nSomeone scratched\n'8' into the\npaint, many times."))
indust.npc('worker', 6, 3, 'citizen',
           iff('ch2_done', say("WORKER: Power's\nback on at Vale's.\nNobody's going in."),
               say("WORKER: Vale's men\nwork nights. They\ncarry guns now.\nSince the fire.",
                   "Loading bay's dead.\nPower room's in\nthe back. Fuse\nkeeps blowing.")),
           move='paceh', d='right')
police(indust, [(1, 8, 2, 'h')])

# ======================================================================= THE CANAL
canal = Map('canal', 'city', 'city_canal', 'drain', """
______:..:______
_L____:..:____L_
__E___:..:___b__
CCCCCC_.._CCCCCC
______.....____\"
~~~~~~~..~~~~~~~
~~~~~~~..~~~~~~~
______....______
_H____;..;___\"\"\"
;;;;;;;..;;;;;;;
UU;;;;;..;;;;;UU
\"\";;;;;..;;;;;T\"
\"T;;;;;..;;;;;;\"
\"\";;;;KKKK;;;\"\"\"
UUUUUUKKKKUUUUUU
UUUUUUUUUUUUUUUU
""", district=6, flags=CITY, title='The Canal')
canal.exit(n='strip')
canal.door(1, 8, 'drain1', 2, 2, 'down', cond=('item', 'sluice_key'),
           lock=say("A storm drain hatch.\nCITY WORKS. A\nsluice key is\nneeded."))
canal.noisemaker(2, 2, "A payphone. The\nreceiver hangs by\nits cord, humming.")
canal.npc('fisher', 12, 7, 'oldman',
          iff('ch5_done', say("OLD MAN: The water\nwent down by a\nfoot last night.\nSomething drained."),
              say("OLD MAN: Don't go\ndown the Drain.\nMott's down there.\nHe rigs the gates.",
                  "He used to work for\nthe city. Now the\ncity works for\nhim.")),
          d='left')
canal.search(13, 2, [say("In the bin: a\nbottle and a\nbandage."), bottle(1), bandage(1)])
canal.sign(8, 13, say("A drainage grate.\nWarm air breathes\nout of it, in and\nout, in and out."))
police(canal, [(3, 7, 1, 'h')])
canal.enemy('runner', 11, 10, 'wander', 0)

# ======================================================================= RED LANTERN
lantern = Map('lantern', 'city', 'city_neon', 'motel', """
RRRRRRRRRRRRRRRR
rrrrrrrrrrrrrrrr
BNBWBBBBBBWBBNBB
BBDBBWBBBWBBBDBB
________________
_L____:..:____L_
______:..:_b____
X..............I
X------..------I
______:..:______
RRRRRR:..:RRRRRR
rrrrrr:..:rrrrrr
BWBWBB:..:BBWBNB
BBBDBB:..:BDBBBB
KKKKKK:..:KKKKKK
______:..:______
""", district=4, flags=CITY, title='Red Lantern District')
lantern.exit(s='strip', w='old', e='wardroad')
lantern.door(2, 3, 'motel_office', 5, 7, 'up')
lantern.door(13, 3, 'bar', 5, 7, 'up')
lantern.door(3, 13, 'motel_court', 7, 13, 'up', cond='motel_scene',
             lock=say("RED LANTERN MOTEL\nCOURTYARD.\nThe gate is shut.\nTry the office."))
lantern.door(11, 13, 'apartment2', 5, 7, 'up')
for y in (7, 8):
    lantern.patch(0, y, '.', 'old_open')
    lantern.patch(15, y, '.', 'ward_open')
lantern.sign(0, 7, say("POLICE LINE.\nOld Gloam is\nclosed."), cond=('not', 'old_open'))
lantern.sign(0, 8, say("POLICE LINE."), cond=('not', 'old_open'))
ward_gate = iff('ward_open', [],
                iff(('ev', 'casefile'),
                    [say("A keypad on the\nhospital gate.\nYou enter the code\nfrom the casefile."),
                     say("0 - 4 - 1 - 3."), sfx('solved'), setf('ward_open'),
                     settile(15, 7, '.'), settile(15, 8, '.')],
                    say("An iron gate. A\nrusted keypad:\nLAST WARD - STAFF.\nFour digits.")))
lantern.sign(15, 7, ward_gate, cond=('not', 'ward_open'))
lantern.sign(15, 8, ward_gate, cond=('not', 'ward_open'))
lantern.sign(1, 2, say("RED LANTERN MOTEL\nVACANCY\n(the V is dead)"))
lantern.sign(13, 2, say("THE LOW NOTE.\nLIVE MUSIC NEVER."))
lantern.npc('girl', 5, 4, 'citizen',
            iff('ch3_done', say("Nolan's gone. Good.\nHe took photos of\nall of us. Said a\nman paid him."),
                say("Looking for Nolan?\nRoom six. Always\nroom six. Ask at\nthe desk, honey.")),
            move='wander')
lantern.npc('bell3', 9, 9, 'bell',
            [say("BELL: Nolan Pike.\nThree. You're\nfaster than the\ncoroner.",
                 "I'm pulling the\ncordon off Old\nGloam. Not for you.\nFor me.",
                 "Something stands\nbehind you in\nevery photo I\ntake. Explain that."),
             iff(('stage', 1),
                 say("BELL: ...Don't.\nDon't let it look\nat me."),
                 say("BELL: Nothing?\nFine. Keep your\nsecrets. I keep\nscore.")),
             setf('bell_met3')],
            cond='ch3_done', d='up')
lantern.on_enter(iff('ch3_done', iff('old_open', [], [setf('old_open'),
                                                        settile(0, 7, '.'), settile(0, 8, '.')])))
police(lantern, [(4, 7, 1, 'h'), (11, 8, 2, 'h')])
lantern.enemy('thug', 2, 14, 'h', 4, 'right')

apt2 = Map('apartment2', 'interior', 'int_motel', 'motel', """
BBWBBBBWBB
B.b....p.B
B........B
B..T..S..B
B..t.....B
B......KKB
B.v....KKB
B.......KB
BBBBBDBBBB
""", district=4, flags=0, title='Walk-up')
apt2.door(5, 8, 'lantern', 11, 14, 'down')
apt2.npc('informant', 6, 4, 'runner',
         iff('ch4_done',
             say("SNITCH: Dacre's\ndead? Then Mott's\nnext. He's in the\nDrain. Bring light."),
             say("SNITCH: Information\ncosts. But you look\nlike you pay in\nother ways.",
                 "Free tip: Nolan\nkeeps a ledger.\nEvery name. Every\npayment.")),
         d='down')
apt2.search(6, 3, [say("Under the shelf:\na revolver rounds\nbox."), ammo(3)])
apt2.sign(2, 6, say("A TV plays a late\nmovie. A masked man\nin a suit. Someone\nturned it off."))

bar = Map('bar', 'interior', 'int_motel', 'motel', """
BBWBBBBBBWBB
B----------B
BCCCCcC----B
B----------B
B-T---T--T-B
B-t---t--t-B
B----------B
B-----d----B
BBBBBBDBBBBB
""".replace('d', '-'), district=4, flags=SAFE, title='The Low Note')
bar.door(6, 8, 'lantern', 13, 4, 'down')
bar.npc('barman', 4, 1, 'thug',
        [say("BARMAN: Whatever\nyou're drinking,\nit's on the house.\nJust don't stay."),
         heal(4),
         iff('ch3_done', say("BARMAN: The cops\nare finally talking\nabout St. Agnes.\nThe old sergeant."),
             say("BARMAN: Nolan runs\nthe motel. Scared\nrabbit. He'll bolt\nif he sees you."))])
bar.npc('drinker', 9, 5, 'oldman',
        [say("DRINKER: You know\nwhat's funny?\nThere were seven\nnames in the report.",
             "DRINKER: Then why\nare there eight\nshadows on the\nwall behind you?")], d='left')
bar.sign(10, 2, [say("A back booth.\nNobody looks here.\nRest a while?"), savepoint()])
bar.search(1, 4, [say("A cassette in the\nbooth. Labelled:\nRED LANTERN."), unlock('motel'),
                  say("(New music in the\nMusic Player.)")])

# ======================================================================= OLD GLOAM
old = Map('old', 'city', 'city_old', 'church', """
IIIIIIIIIIIIIIII
I+;+;+I\"AAAAAAA\"
I;;;;;I\"AaAaAaA\"
I+;+;+I\"AAADAAA\"
I;;;;;g\"\"\"^\"\"\"\"\"
I+;+;+I____..___
IIIIIII_:..:____
................
-------..-------
______:..:______
RRRRRR:..:RRRRRR
rrrrrr:..:rrrrrr
BWBWBW:..:BBWBBB
BBDBBB:..:BWBDBB
______:..:______
;;;;;;:..:;;;;;;
""", district=5, flags=CITY, title='Old Gloam')
old.exit(s='mercy', e='lantern')
old.door(10, 3, 'ag_nave', 6, 14, 'up', cond=('item', 'church_key'),
         lock=say("St. Agnes. The\ndoors are chained\nfrom inside. The\nsacristy key..."))
old.door(2, 13, 'rec_lobby', 5, 8, 'up', cond='ch5_done',
         lock=say("POLICE RECORDS\nANNEX. Locked. A\nguard inside.\nNot yet."))
old.door(13, 13, 'oldhouse2', 5, 7, 'up')
old.sign(1, 4, say("ST. AGNES\nCEMETERY. Est.\n1888."))
old.search(3, 2, [say("A fresh grave. No\nname. Someone left\na bottle of whisky\nand bandages."), bandage(2), bottle(1)])
old.search(5, 4, [say("Under a headstone:\na rosary of black\nbeads. It warms\nin your hand."), special('maxhp_up'),
                  say("MAX HEALTH UP.")])
old.npc('priest', 12, 5, 'priest',
        iff('ch4_done',
            say("FATHER OYELARAN:\nThe bells rang by\nthemselves at three.\nNo one pulled them."),
            say("FATHER OYELARAN:\nSt. Agnes is closed.\nA policeman pays\nfor the privacy.",
                "Read the windows,\nif you get inside.\nThey tell you how\nto pray.")),
        d='left')
old.enemy('wraith', 3, 3, 'static', 0, cond=('stage', 2))
police(old, [(4, 7, 1, 'h'), (11, 14, 2, 'h')])

old2 = Map('oldhouse2', 'interior', 'int_records', 'church', """
BBBBWBBBBB
B..S.S.S.B
B........B
B.n...s..B
B.t......B
B........B
B..o.....B
B........B
BBBBBDBBBB
""", district=5, flags=SAFE, title='Archivist')
old2.door(5, 8, 'old', 13, 14, 'down')
old2.npc('archivist', 6, 4, 'clerk',
         iff('ch6_done',
             say("ARCHIVIST: So the\nfile surfaced. I\nhope it was worth\nwhat it cost."),
             say("ARCHIVIST: Case\nnumbers are year,\nthen month and day.\nEleven, oh-four,\nthirteen.",
                 "The annex shelves\nfiles by year and\nquarter. Spring is\nthe second quarter.")),
         d='down')
old2.sign(2, 3, [say("A reading desk.\nA lamp. Quiet."), savepoint()])
old2.search(6, 3, [say("A file cabinet.\nA survey plat from\n1958 falls out."), ev('mercy3')])

# ======================================================================= WARD ROAD
wardroad = Map('wardroad', 'city', 'city_ward', 'ward', """
IIIIIIIIIIIIIIII
IRRRRRRRRRRRRRRI
IrrrrrrrrrrrrrrI
IBwBxBwBBwBxBwBI
IBwBwBwDBwBwBxBI
I\"\"\"\"\"\"^\"\"\"\"\"\"\"I
I\"T\"\"\"\"..\"\"\"\"T\"I
.......;..;\"\"\"\"I
-------;..;\"\"\"\"I
I\"\"\"\";;;..;;\"\"\"I
I\"\"T\";;KKK;;\"T\"I
I\"\"\"\";;KKK;;\"\"\"I
I\"+\"\"\";;;;\"\"\"+\"I
I\"\"\"\"\"\"\"\"\"\"\"\"\"\"I
I\"T\"\"\"\"\"\"\"\"\"T\"\"I
IIIIIIIIIIIIIIII
""", district=7, flags=CITY, title='The Last Ward')
wardroad.exit(w='lantern')
wardroad.door(7, 4, 'ward_recep', 6, 8, 'up')
wardroad.sign(6, 5, say("THE LAST WARD\nGLOAM STATE\nHOSPITAL\nCLOSED 1999"))
wardroad.enemy('gunman', 4, 7, 'h', 2, 'right')
wardroad.enemy('gunman', 9, 10, 'guard', 0, 'up')
wardroad.enemy('wraith', 13, 12, 'static', 0)
wardroad.search(2, 12, [say("A gardener's shed\nbox. Revolver\nrounds and gauze."), ammo(4), bandage(1)])
wardroad.on_enter(iff('ward_seen', [], [setf('ward_seen'), music('shadow'), image('ward'),
                                         say("The Last Ward.\nWhere Gloam sent\nthe people it\nwanted to forget.",
                                             "Victor Rusk ran it\nfor thirty years.\nHe never left."),
                                         image_end(), music_resume(), chapter(7)]))
