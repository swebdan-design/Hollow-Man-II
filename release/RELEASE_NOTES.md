# HOLLOW MAN: THE SECOND SHADOW
### by Synth Centric — Release 1.0 (Game Boy Color)

A top-down survival-horror detective adventure for the Nintendo Game Boy Color. A masked man
in a brown tweed suit hunts the seven men behind the Mercy Street killings — while something
with horns walks in his shadow.

## Files
- `HOLLOW_MAN_THE_SECOND_SHADOW.gbc` — the game (512 KB, MBC5 + 8 KB battery RAM, CGB only)
- `HOLLOW_MAN_SOURCE.zip` — complete source; rebuilds this exact ROM (see docs/BUILD.md)
- `HOLLOW_MAN_COMPLETE.zip` — ROM, manual, docs, release notes, screenshots, source zip
- `screenshots/` — genuine emulator captures (PyBoy, CGB mode)

## Controls
D-Pad move · **A** talk/search/use (interaction first, then equipped tool) · **B** strike ·
hold **B** heavy strike · **SELECT** cycle tool · **START** pause menu.

## Features
- Seven interconnected districts of Gloam and 39 maps: streets, shops, a cold-storage plant,
  a motel, a church and crypt, storm drains, a records annex and an abandoned hospital.
- Seven playable chapters, each with its own location, puzzle, enemies, evidence and target:
  Eddie Voss, Hector Vale, Nolan Pike, Sgt. Dacre, Alec Mott, Silas Crewe, Victor Rusk.
- Real-time combat (pipe, fire axe, charged strikes, scarce revolver), six enemy types and
  seven distinct bosses.
- Stealth: vision cones, line of sight, dark floors, alert/search/return states, distractions,
  silent takedowns from behind.
- The Second Shadow: an influence meter (0–100) with four stages that change your shadow,
  the music, NPC dialogue, abilities (shadow stun, breathing walls, death refusal),
  loss-of-control moments and the ending.
- Police alert system, Detective Mara Bell's investigation and choices that change epilogues.
- Casebook with 17 readable evidence entries; inventory, city map, shadow status.
- Puzzles: crate pushing, power/breaker order, room-key deduction, church mechanism sequence,
  water-level valves, archive document search, timed lockdown, keycards.
- Three endings: NOT TONIGHT, THE EMPTY VESSEL, and the secret THE EIGHTH MAN.
- Original 16-track chiptune soundtrack by Synth Centric on the GBC sound hardware, with an
  unlockable Music Player and visualiser.
- Battery saves with two verified slots and checksums; options for music, SFX and text speed.

## Emulator guidance
Use any accurate Game Boy Color emulator in **GBC mode** (e.g. SameBoy, Emulicious, mGBA, BGB,
PyBoy). Saves are stored in the emulator's `.sav`/`.ram` file next to the ROM. The ROM is
CGB-only; it will not start on an original Game Boy.

## Known limitations
- Tested only in the PyBoy emulator; **not tested on real hardware** or other emulators.
- Chapters 2–7 were verified with automated bots, crafted saves and a progression simulator,
  not with a full human playthrough; balance has been tuned against bots.
- Estimated playtime is about 1.5–3 hours, not the 4–6 hours originally targeted.
- Busy rooms can exceed 10 sprites per scanline (hardware limit), causing brief sprite drop-out.
- Sound/music quality has been verified to produce output, but has not been reviewed by ear
  in this environment.

## Credits
Created by **Synth Centric**. Music by **Synth Centric**. Built with GBDK-2020.
