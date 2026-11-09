# Project status & engine design

## Status: release 1.2 — Game Boy Advance + Game Boy Color

The GBA version (`gba/`) is a port of the GBC engine: the gameplay modules (player, actors,
bosses, script VM, menus, saves) are shared code paths adapted to GBA hardware; the hardware
layer (core, text, map, render, audio, save, runtime) is GBA-specific; the art is all new
(`assets/gba`). World, scripts and music data come from the same sources as the GBC version.

GBA display (1.2): BG0 is the map, pre-rendered and lit per map (up to 1000 4bpp tiles,
13 baked palettes, plus pre-lit pieces for tiles that change in-game), or an 8bpp
illustration. BG1 holds text (anti-aliased font) and BG2 the panels. Characters are OBJ 32x64
frames rendered from 3D models; the current frame of each actor is DMA'd into VRAM during
VBlank. The 64x64 Second Shadow is also an OBJ. Music uses the DMG sound channels, plus Direct
Sound for recorded tracks. Release 1.0 (GBC only) notes follow.

Everything in the brief is implemented and the ROM builds, validates and passes 30 automated
tests (see TESTING.md). Remaining gaps are verification gaps, not missing systems:
real-hardware testing, a full human playthrough of chapters 2–7, and balance tuning with people.

### If development resumes, the next actions are
1. Play chapters 2–7 by hand on SameBoy/Emulicious and on a flash cart; note balance issues.
2. Lengthen music loops (most cues loop after 20–30 s) and add more optional side content to
   move playtime toward the 4–6 h target.
3. Consider sprite multiplexing / flicker for rooms with many enemies on one row.

## Architecture

| Bank | Contents |
|---|---|
| 0 | `core.c` (far data access, input, palettes/fades, VRAM loaders), `audio.c` (VBlank music + SFX driver), `text.c` (font, boxes, dialogue), `map.c` (metatile maps, tileset loading, sprite-sheet slots), `render.c` (camera, OAM), `state.c` (flags/items/influence/alert), `main.c`, generated directories |
| 1–15 (auto) | `game.c` (loop, warps, HUD, death/retry, chapter cards, illustrations), `player.c`, `actors.c` (NPC + enemy AI, stealth), `boss.c` (7 bosses), `script.c` (event VM), `menu.c` (pause menu), `title.c` (title, menu, options, music player, credits, endings), `save.c`, `special.c` |
| 16+ | Generated data: tiles, palettes, sprites, illustrations, maps, script bytecode, music |

- **Graphics:** BG tiles use signed addressing. VRAM bank 0 holds the font/UI (tiles 0–127) and
  all sprite tiles (player, effects, NPC sheet slots); VRAM bank 1 holds the current
  environment tileset (up to 256 tiles) or a cutscene illustration, plus extra sprite slots
  and the 32×48 Second Shadow figure. Maps are up to 16×16 metatiles (256×256 px) so the whole
  map fits the 32×32 BG map and scrolls with SCX/SCY only. The window layer shows the HUD,
  dialogue box and full-screen menus.
- **Sprites:** 8×16 mode. Characters are 16×16 (two OAM entries) with 6 frames; Hector is a
  32×32 big actor; effects/bullets are 8×16.
- **Data-driven content:** maps, NPCs, enemies, bosses, pickups, puzzles, cutscenes and endings
  are written in a Python DSL (`assets/maps/*.py`) and compiled to bytecode for the event VM
  (`src/script.c`): text, branching on flags/items/evidence/influence/vars, choices, warps,
  tile changes, actor movement, music, illustrations, chapter cards, saves, endings.
- **World state:** 1024 flags, 16 byte variables, items, evidence, influence, alert, unlocked
  music. Doors/gates/walls persist through flag-conditional map patches.
- **Saves:** two SRAM slots with magic, version, sequence number and checksum; written to the
  older slot and read back for verification before the save is reported successful.
- **CPU:** CGB double-speed mode for headroom; game logic runs at 60 Hz.
