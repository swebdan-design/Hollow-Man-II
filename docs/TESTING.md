# HOLLOW MAN: THE SECOND SHADOW — Testing Report

All results below were produced in this development environment. Nothing here was tested on
real Game Boy Color hardware or a flash cartridge.

## Environment

| | |
|---|---|
| OS | Linux x86-64 (cloud container) |
| Compiler | GBDK-2020 4.3.0 — `lcc` 2024/06/08, SDCC 4.4.1 #14650 |
| Python / Pillow | 3.13 / 12.3.0 |
| Emulator | **PyBoy 2.9.0**, forced CGB mode, headless (`window='null'`), scripted inputs |
| Test runner | pytest 9.x — `make test` |

## ROM / header (tools/romcheck.py, run at the end of every build)

| Field | Value | Check |
|---|---|---|
| File | `HOLLOW_MAN_THE_SECOND_SHADOW.gbc`, 524,288 bytes (512 KB, 32 banks) | ROM size code 0x04 matches file size ✔ |
| Title | `HOLLOWMAN` | ✔ |
| CGB flag (0x143) | 0xC0 — Game Boy Color only | ✔ |
| Cartridge type (0x147) | 0x1B — MBC5 + RAM + BATTERY | ✔ |
| RAM size (0x149) | 0x02 — 8 KB | ✔ |
| Nintendo logo | matches | ✔ |
| Header checksum | valid | ✔ |
| Global checksum | valid | ✔ |
| Linker | no unresolved symbols, no bank overflow (bank 0 77% used; code banks 1–3; data banks 16–21) | ✔ |
| Clean rebuild | `make clean && make` produces a byte-identical ROM (SHA-1 compared) | ✔ |
| Rebuild from source zip | `tools/make_release.py` extracts `HOLLOW_MAN_SOURCE.zip` into a temp dir, builds it, and requires a byte-identical ROM | ✔ IDENTICAL — SHA-1 94bec7e5e061979471da03944fdcc7057d76ec4f |

Compiler output contains only SDCC informational warning 110 ("conditional flow changed by
optimizer") in `actors.c`/`boss.c`, caused by constant table lookups; it is harmless.

## Automated tests (`make test` → 46 tests, all passing: 30 GBC/host + 16 GBA)

### Host-side world validation — `tests/test_world.py` (11 tests)

| Test | What it proves |
|---|---|
| no stub maps | every referenced map is authored (39 maps) |
| map dimensions / tiles | every map is 10–16 × 9–16 metatiles and uses only valid tiles |
| warp arrivals walkable | every door/warp lands on a walkable tile |
| every door has a way back | no one-way interiors |
| edge exits mutual | district connections are symmetric |
| **all chapters completable** | a progression simulator (interprets every event script, both branches of choices, flags, items, conditional doors, patches, edge exits restricted to the road lanes exactly as the engine does) reaches `ch1_done` … `ch7_done` from a new game |
| all maps visited | every map is reachable in normal progression |
| all evidence obtainable | all 17 Casebook entries |
| secret ending reachable | `mercy_done` attainable |
| all items obtainable | all 16 key items |
| text fits text box | every page ≤ 4 lines × 18 characters (the compiler also enforces this at build time) |

### Emulator tests — `tests/test_emulator.py` (19 tests, real ROM in PyBoy)

| Test | Result |
|---|---|
| ROM header | pass |
| Title screen shows `THE SECOND SHADOW` / `by Synth Centric` (read back from VRAM) | pass |
| New Game → intro cutscene → Chapter 1 card → player on the Commercial Strip, movement works | pass |
| CONTINUE locked without a save (cursor skips it) | pass |
| **Save → SRAM → reload → Continue** round trip (pause-menu save; both slots valid; new seq; position/influence restored) | pass |
| Corrupt save (checksum mismatch) is ignored | pass |
| Newest of two valid slots wins | pass |
| Cold Storage power puzzle: fuse, wrong breaker resets, 2-3-1 restores power | pass |
| The Drain water-level puzzle: valve A, wheel fitted, valve B; platform and outfall become reachable | pass |
| Records Annex: casefile starts the timed lockdown | pass |
| St. Agnes: bell → flame → hymn opens the crypt | pass |
| Death → Game Over screen → RETRY restores the checkpoint | pass |
| Music Player: lists tracks, credits Synth Centric, plays/stops via the real driver | pass |
| **Chapter 1 full playthrough with scripted inputs** (combat, crate-push puzzle, key, locked door, Eddie Voss boss, shadow choice, photograph evidence) | pass |
| Ending A — NOT TONIGHT (final boss fought by the test bot, refuse) | pass |
| Ending B — THE EMPTY VESSEL (high influence) | pass |
| Secret ending — THE EIGHTH MAN (all Mercy evidence, low influence) | pass |
| Tools: revolver uses ammo and raises alert; bottle consumed; shadow tool raises influence | pass |
| Police patrols appear only at raised alert | pass |

The tests for later chapters start from crafted battery saves (the save format is modelled in
`tests/savefmt.py`, which mirrors `src/save.c`).

### Other emulator verification

- `tools/map_tour.py` boots every one of the 39 maps from a save and screenshots it: all load
  and render (contact sheet in `build/tour/contact.png`).
- Audio: with sound emulation enabled the APU produces non-silent output on the title screen
  (peak sample checked), NR52 = 0xFF.
- `release/screenshots/` — 16 genuine PyBoy captures produced by `tools/screenshots.py`.

## Game Boy Advance version

| | |
|---|---|
| Compiler | arm-none-eabi-gcc 13.2.1 + newlib, own crt0/linker script |
| Emulator | **mGBA 0.10.2 (libmgba)**, headless, driven by `build/gba_harness` (`tools/gba_harness.c`) with scripted inputs |
| ROM | `HOLLOW_MAN_THE_SECOND_SHADOW.gba`, 571,904 bytes; header logo + complement check valid; `SRAM_V113` save type; 32 KB SRAM |

`tests/test_gba.py` — **16 tests, all passing**, running the real GBA ROM:

| Test | Result |
|---|---|
| Cartridge header (logo, fixed byte, complement, save-type marker) | pass |
| Title illustration + main menu (NEW GAME, dimmed CONTINUE) | pass |
| New Game → intro → Chapter 1, movement | pass |
| Save via pause menu → SRAM (read back through the cartridge bus) → Continue | pass |
| Corrupt save ignored | pass |
| Power puzzle, water-level puzzle, church sequence, records lockdown | pass |
| Death → Game Over → Retry | pass |
| Music Player (plays/stops via the real driver; credits Synth Centric) | pass |
| **Chapter 1 full playthrough** with scripted inputs (crate puzzle, keys, Eddie Voss) | pass |
| Endings A / B / secret (Rusk's health is lowered by the test so the simple bot wins quickly; the test checks the ending logic) | pass |
| Revolver ammo/alert; police patrols at high alert | pass |

Also: `tools/gba_map_tour.py` boots all 39 maps on the GBA build (all load and render),
`tools/gba_screenshots.py` produced the 15 captures in `release/screenshots_gba/`.

## Not tested / limitations

- **Real hardware:** not tested for either version (no GBC, GBA or flash cart available). No flash cart or physical GBC was available. Timing-sensitive
  code (VBlank music driver, VRAM writes via GBDK's STAT-safe routines, double-speed mode) has
  only been verified in PyBoy.
- **Other emulators** (SameBoy, Emulicious, mGBA, BGB): not run here; PyBoy only.
- **A complete human playthrough of chapters 2–7** was not performed. Each chapter's puzzle and
  final boss/ending were exercised with scripted bots and crafted saves, and progression is
  verified by the simulator, but bosses 2–6 were not individually fought by the bot end-to-end
  (Eddie Voss and Victor Rusk were).
- Balance (enemy damage, boss health, ammo economy) has only been tuned against the test bot.
- **Playtime:** not measured with real players. Content estimate: roughly 1.5–3 hours for a
  first playthrough (39 maps, 7 chapters, optional secrets), short of the 4–6 hour aspiration.
- Sprite flicker/drop with more than 10 sprites on one scanline is possible in busy rooms
  (hardware limit; no sprite multiplexing is implemented).
- **GBA pre-rendered graphics (1.2)** were checked in mGBA only: the 15 release screenshots,
  the 39-map tour contact sheet and the full test suite. Each VBlank, every changed 1 KB character frame is
  DMA'd into VRAM, at most 13 KB. By cycle count that fits easily in VBlank, but it has not
  been timed on real hardware.
