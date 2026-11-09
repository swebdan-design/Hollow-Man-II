# Building HOLLOW MAN: THE SECOND SHADOW

The ROM is built entirely from the sources in this repository. All graphics, maps, scripts
and music are stored as Python/ASCII source assets and converted at build time.

## Tested toolchain

| Tool | Version used for the release build |
|---|---|
| GBDK-2020 | 4.3.0 (`lcc` 2024/06/08, SDCC 4.4.1 #14650) |
| Python | 3.13 (3.9+ should work) |
| Pillow | 12.3.0 (asset conversion) |
| GNU Make | 4.x |
| PyBoy | 2.9.0 (tests and screenshots only, optional) |
| pytest | 9.x (tests only, optional) |
| OS | Linux x86-64 |

## Step by step (Linux)

```sh
# 1. Python dependencies
python3 -m pip install pillow            # required
python3 -m pip install pyboy pytest      # optional: emulator tests / screenshots

# 2. GBDK-2020 (downloads 4.3.0 into ./toolchain/gbdk)
sh tools/setup_gbdk.sh

# 3. Build
make GBDK_HOME=toolchain/gbdk
#    -> build/HOLLOW_MAN_THE_SECOND_SHADOW.gbc
#    The build ends by validating the cartridge header ("HEADER OK").

# 4. (optional) run the test suite
make test GBDK_HOME=toolchain/gbdk

# 5. (optional) produce the release folder and zips
make release GBDK_HOME=toolchain/gbdk
```

If GBDK-2020 is installed elsewhere, point `GBDK_HOME` at the folder that contains `bin/lcc`
(default: `/opt/gbdk`). On macOS/Windows use the matching GBDK-2020 4.3.0 release archive from
<https://github.com/gbdk-2020/gbdk-2020/releases/tag/4.3.0>; the Makefile needs a POSIX shell
(on Windows use MSYS2 or WSL).

## What the build does

1. `tools/build_assets.py` runs the asset pipeline into `build/gen/`:
   - `build_tiles.py` — font, UI tiles, three metatile tilesets, background palette sets
   - `build_sprites.py` — character sprite sheets (paper-doll generator), effects, OBJ palettes
   - `build_images.py` — title screen and cutscene illustrations (CGB tile + palette conversion)
   - `build_music.py` — compiles `assets/music/songs.py` into driver streams
   - `content.py` — compiles maps, NPCs, enemies, puzzles and event scripts from
     `assets/maps/*.py` into bytecode, validating text-box fit, warp targets and limits
   - `packer.py` — packs all generated data into explicit ROM banks 16+
   Preview PNGs of tilesets, sprites and illustrations are written to `build/preview/`.
2. Every `src/*.c` is compiled with `lcc`. Gameplay modules use `#pragma bank 255` and are
   auto-banked by bankpack into banks 1–15; the core engine lives in bank 0.
3. Linking: `-Wm-yC` (CGB only), `-Wl-yt0x1B` (MBC5+RAM+BATTERY), `-Wl-ya1` (one 8 KB RAM
   bank), `-Wm-yoA` (automatic ROM size, currently 512 KB / 32 banks).
4. `tools/romcheck.py` validates logo, CGB flag, cartridge type, ROM/RAM size codes and both
   checksums.

## Reproducibility

The source archive `release/HOLLOW_MAN_SOURCE.zip` contains everything needed. The release
script rebuilds the ROM from a fresh extraction of that archive and checks that the result is
byte-identical to the released ROM (see `docs/TESTING.md`).

## Project layout

```
src/        C engine and gameplay (bank 0 core + banked modules)
include/    hm.h shared engine header
assets/     art/ (font, UI), tilesets/, sprites/, music/, maps/ (world + story scripts)
tools/      asset pipeline, ROM checker, emulator harness, release script
tests/      host-side world/progression tests + PyBoy emulator tests
docs/       manual, build, controls, soundtrack, testing, design/status
release/    final ROM, zips, release notes, genuine emulator screenshots
```
