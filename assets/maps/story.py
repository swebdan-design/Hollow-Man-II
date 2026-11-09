"""Story registry: ordered flags, evidence, specials, intro and endings."""
from content import *

# chapter completion flags MUST be consecutive (menu.c relies on F_CH1_DONE + i)
for i in range(1, 8):
    flag('ch%d_done' % i)
for f in ['shadow_power', 'shadowcast', 'killed_cop', 'mercy_done', 'game_clear', 'power_on',
          'bell_trust', 'indust_open', 'lantern_open', 'old_open', 'ward_open']:
    flag(f)

for sp in ['lockdown_start', 'lockdown_stop', 'fullheal', 'maxhp_up', 'clear_enemies',
           'spawn_enemies', 'reset_revive', 'pursuit', 'equip_axe', 'tool_shadow']:
    special_id(sp)

# ------------------------------------------------------------------ evidence (Casebook)
evidence('photo', 'The Photograph',
         "Seven men outside 13 Mercy Street the night it burned. Eddie, Hector, Nolan, Dacre, "
         "Mott, Crewe... and a seventh face torn away.|Behind them stands an eighth shape. "
         "Taller. Horned. Nobody remembers it being there.")
evidence('pawn_ledger', 'Pawn Ledger Page',
         "Eddie's books. A payment every month for eleven years, marked only V.R.|"
         "Someone has been paying for silence.")
evidence('manifest', 'Freezer Manifest',
         "A cold storage manifest. Crate 13 shipped to the Red Lantern Motel, Room 6. "
         "Signed N. PIKE.")
evidence('motel_ledger', 'Motel Ledger',
         "Nolan Pike kept accounts. Cash from V. RUSK to every name in the photograph.|"
         "One line reads: SGT. R. DACRE - KEEP THE FILE CLOSED. ST. AGNES.")
evidence('confession', 'Confession Tape',
         "A tape from the confessional recorder. Dacre's voice: 'We were told to dig. "
         "Under the house. Rusk wanted what was buried. Not the family.'")
evidence('police_memo', 'Police Memo',
         "Gloam P.D. internal memo. Mercy Street case reassigned to Sgt. Dacre. Evidence "
         "transferred to the Records Annex, cage D-7. Signed S. CREWE.")
evidence('sewer_survey', 'Sewer Survey',
         "Alec Mott's survey of the old storm drains. A tunnel marked in red runs from the "
         "Drain to the cellar of 13 Mercy Street.")
evidence('casefile', 'Casefile 11-0413',
         "The original casefile. Seven suspects. Physical evidence of an eighth person was "
         "removed by Crewe.|Final page: V. RUSK, director of the Last Ward hospital, paid "
         "for everything. Gate code: 0413.")
evidence('rusk_letter', "Rusk's Letter",
         "'The vessel must be emptied before it can be filled. The boy survived. The thing "
         "beneath Mercy Street has chosen him.'")
evidence('bell_notes', "Bell's Notes",
         "Detective Mara Bell's notebook. 'Every victim had the same photograph. "
         "In every copy, the eighth shape is closer to the camera.'")
# Mercy Street secret investigation (EV_MERCY1..EV_MERCY7 must be consecutive)
evidence('mercy1', "Child's Drawing",
         "A crayon drawing found in the ruins. A family of three. Behind the house, a tall "
         "black figure with horns. It is smiling.")
evidence('mercy2', 'Burnt Diary Page',
         "'The scratching under the floor is worse. Dad says it is the pipes. It is not the "
         "pipes. It counts.'")
evidence('mercy3', 'Survey Plat 1958',
         "Before the house was built, the lot was listed as CHURCH LAND - DO NOT EXCAVATE.")
evidence('mercy4', 'Parish Register',
         "St. Agnes, 1958: a priest records burying 'a thing that was not a man' under the "
         "Mercy lot. Eight candles. Eight names. Never speak the eighth.")
evidence('mercy5', "Workman's Tape",
         "A cassette left in the Drain. A workman whispers: 'There is a door down here that "
         "goes up into a house. Something knocks from the other side.'")
evidence('mercy6', "Hale's Testimony",
         "Mrs. Hale saw eight men go in. Seven came out. The eighth walked away with the "
         "boy's shadow.")
evidence('mercy7', 'The Eighth Name',
         "Carved beneath the altar in the cellar: a name that is no name. It is the shape of "
         "a horned head. Beneath it, freshly cut: the boy's name.")

# ------------------------------------------------------------------ intro
S('intro',
  music('shadow'),
  image('gloam'),
  say("GLOAM.\nEleven years after\nMercy Street.",
      "The rain never\nstops here.\nIt just changes\nits mind."),
  image('house'),
  say("13 Mercy Street.\nSeven men went in.\nA family did not\ncome out.",
      "No one was\npunished. Files\nwent missing.\nWitnesses went\nquiet."),
  image('photo'),
  say("Someone took a\nphotograph that\nnight. Seven men\noutside the fire.",
      "Count them again."),
  wait(40), sfx('shadow'), shake(10),
  say("Eight."),
  image('hollow'),
  say("Now a man in a\nbrown tweed suit\nis crossing names\noff a list.",
      "They call him\nHOLLOW MAN."),
  image('shadow'),
  say("He thinks he is\nalone.|He has never been\nalone."),
  warp('strip', 4, 5, 'up'),
  chapter(1),
  say("The pawnshop.\nEddie Voss buys\nand sells what\nother men steal.",
      "D-PAD: move\nA: talk, search,\nuse a tool\nB: strike",
      "Hold B to charge a\nheavy blow.\nSTART: pause menu\nSELECT: cycle tool"),
  checkpoint(),
)

# ------------------------------------------------------------------ endings
S('end_a',
  music('ending'),
  image('dawn'),
  say("The hospital burns\nbehind him.\nHe does not look\nback.",
      "The shadow pulls at\nhis heels like a\ndog on a chain.|He does not let\ngo of the chain."),
  iff('bell_trust',
      say("Three days later,\nDetective Bell\nopens Casefile\n11-0413 in court.",
          "Every name is\nread aloud.\nThe city listens\nfor once."),
      say("Detective Bell\nfinds the hospital\nempty. Ash and a\nbroken altar.",
          "She keeps the\nphotograph. She\ndoes not show it\nto anyone.")),
  iff('killed_cop',
      say("BELL: He killed\npolice. Whatever\nhe was hunting,\nhe is mine now.")),
  say("NOT TONIGHT.", "But the rain still\ncomes down on\nGloam. And under\nthe streetlights,"),
  image('shadow'),
  say("every shadow is\nslightly too tall."),
)

S('end_b',
  music('shadow'),
  image('vessel'),
  say("Hollow Man stands\nup in the chapel.\nHe is smiling\nunder the mask.",
      "It is not his\nsmile.|THE EMPTY VESSEL\nhas been filled.",
      "The Second Shadow\nwalks out of the\nLast Ward and down\ninto Gloam."),
  iff('bell_trust',
      say("Mara Bell is\nwaiting at the\ngate. She knows him\nby the suit.",
          "She raises her gun.\nIt looks at her\nwith his eyes.\nShe hesitates."),
      say("The rain stops for\nthe first time in\neleven years.",
          "Nobody in Gloam\nsleeps that night.")),
  say("THE EMPTY VESSEL."),
)

S('end_secret',
  music('shadow'),
  image('eighth'),
  say("The cellar under\nMercy Street.\nEight candles.\nEight names.",
      "Rusk did not want\nthe family dead.\nHe wanted the\nthing beneath them."),
  say("The seven men dug.\nThe thing woke.\nIt took the boy's\nshadow as a door.",
      "The boy survived.\nHe grew up.\nHe bought a\nbrown tweed suit."),
  image('hollow'),
  say("He was never\nhunting seven men.\nHe was hunting\nthe eighth.",
      "And now he knows\nits name."),
  iff('bell_trust',
      say("Bell reads the\nfull casefile. She\nburns the last\npage herself.")),
  image('photo'),
  say("THE EIGHTH MAN.", "...|Somewhere, a\nsecond copy of the\nphotograph exists.",
      "In it, there are\nnine."),
)
