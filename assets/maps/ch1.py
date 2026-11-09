"""CHAPTER 1 - THE PAWNSHOP.  Target: Eddie Voss.  Tutorial: stealth, combat, push puzzle."""
from content import *

front = Map('pawn_front', 'interior', 'int_warm', 'pawn', """
BBBBBDBBBLBB
BS........SB
B..........B
BCCcC...XX.B
B.......X..B
BKK........B
BKK..TT..S.B
B..........B
B..........B
BBBBBDBBBBBB
""", district=2, flags=RESTRICTED, title="Pawn & Pray")
front.door(5, 9, 'strip', 2, 4, 'down')
front.door(5, 0, 'pawn_store', 7, 10, 'up')
front.patch(9, 0, 'D', 'office_open')
front.door(9, 0, 'pawn_office', 5, 8, 'up', cond='office_open')
front.sign(9, 0, iff(('item', 'office_key'),
                     [say("The brass key\nturns. OFFICE."), sfx('key'), setf('office_open'), settile(9, 0, 'D')],
                     [sfx('deny'), say("A door marked\nOFFICE. Locked.\nThe key must be\nsomewhere back.")]),
           cond=('not', 'office_open'))
front.enemy('thug', 6, 4, 'h', 3, 'right', cond=('not', 'ch1_done'))
front.search(3, 3, [say("The register.\nEleven years of\nreceipts. One page\nis different."), ev('pawn_ledger')])
front.sign(1, 1, say("Shelves of stolen\nwatches. Each one\nstopped at the same\ntime: 3:13."))
front.sign(10, 1, say("Wedding rings by\nthe pound."))
front.search(9, 6, [say("Behind the shelf:\nan empty bottle."), bottle(1)])
front.on_enter(iff('pf_seen', [], [setf('pf_seen'),
                                   say("A big man walks\nthe shop floor.\nKeep to the dark\ncorner by the wall.",
                                       "Hit him from\nbehind and he\nwon't get up.\nFace to face, he\nwill fight.")]))

store = Map('pawn_store', 'interior', 'int_dark', 'pawn', """
BBBBBBBBBBBBBBBB
BX......X......B
B.......XXXXXX.B
B..XX...X..x...B
B..XX...X.X.XX.B
B.......X..X...B
B.......x......B
BKK.....X..XX..B
BKK.....X..XX..B
B.......X......B
BX......X.....XB
BBBBBBBDBBBBBBBB
""", district=2, flags=RESTRICTED | DARKMAP, title='Storeroom')
store.door(7, 11, 'pawn_front', 5, 1, 'down')
store.search(11, 4, [say("Wedged under the\ncrates: a brass\nkey tagged OFFICE."), give('office_key'),
                     say("Got the OFFICE KEY.")], empty="Just dust now.")
store.sign(1, 1, say("Crates stamped\nVALE COLD STORAGE.\nThey smell of\nfrost and meat."))
store.enemy('rat', 4, 8, 'wander')
store.enemy('rat', 12, 9, 'wander')
store.pickup(2, 9, 'bandage')
store.pickup(14, 1, 'bottle')
store.on_enter(iff('ps_seen', [], [setf('ps_seen'),
                                   say("Crates everywhere.\nSome are loose -\nwalk into one to\npush it.",
                                       "If you get stuck,\nstep out and back\nin. The crates go\nback where they\nwere.")]))

office = Map('pawn_office', 'interior', 'int_warm', 'pawn', """
BBBBBBBBBBBB
Bo..n...S..B
B...t......B
B..X....X..B
B..........B
B.X..XX..X.B
B..........B
B..X....X..B
B..........B
BBBBBDBBBBBB
""", district=2, flags=RESTRICTED, title="Eddie's Office")
office.door(5, 9, 'pawn_front', 9, 1, 'down')
office.boss('eddie', 5, 2, ('not', 'ch1_done'), [
    music(None),
    say("EDDIE: Wait. Wait.\nIt wasn't me who\nlit it. I swear to\nGod.",
        "Rusk paid us. To\ndig. Under the\nhouse. That's all.",
        "There was somebody\nelse in there with\nus. Tall. Wrong.",
        "It's standing\nbehind you right\nnow."),
    sfx('kill'), flash(),
    say("Eddie Voss stops\nbreathing. His hand\nopens. A keyring\nand a photograph."),
    give('eddie_keys'),
    ev('photo'),
    wait(30),
    music('shadow'),
    shadow(64, 8), shake(20),
    say("Something tall\nstands in the\ncorner of the\noffice.",
        "It has always\nbeen there. It has\nnever needed the\nlight."),
    choice("It offers a hand\nmade of smoke.", "TAKE IT", "REFUSE",
           [infl(10), setf('shadow_power'), special('tool_shadow'),
            say("Cold pours into\nyour arm. You can\nlet it out again.",
                "SHADOW tool: press\nSELECT to equip,\nA to use. It\nstuns your foes.",
                "It also opens the\nwalls that breathe.\nIt costs you\nsomething each use.")],
           [say("It lowers its\nhand. It is\npatient. It has\nwaited eleven\nyears.")]),
    shadow_hide(),
    setf('ch1_done'), setf('bell_at_strip'),
    music('jingle'),
    say("CHAPTER 1\nCOMPLETE.\nOne name crossed\noff the list."),
    music('pawn'),
    savepoint(),
])
office.on_enter(iff('ch1_done', [], iff('eddie_seen', [special('pursuit')],
                                       [setf('eddie_seen'),
                                        say("EDDIE: Who the\nhell... you. The\nsuit. The mask.",
                                            "EDDIE: I heard\nyou were dead. I\nheard you were a\nghost story.",
                                            "Crates! Get behind\nthe crates when he\nfires. He has to\nreload."),
                                        special('pursuit')])))
office.search(4, 1, [say("Eddie's desk. A\nrevolver in the\ndrawer, and a box\nof rounds."), give('pistol'), ammo(6),
                     say("Got the REVOLVER.\nSELECT to equip.\nEvery shot raises\nthe police alert.")],
              cond='ch1_done')
office.sign(8, 1, say("A safe, open and\nempty. Eddie\nalready ran once\ntonight."))
office.sign(1, 1, say("A framed photo of\nEddie shaking hands\nwith a thin man in\na white coat."))
