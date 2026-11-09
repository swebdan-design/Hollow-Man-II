/* map.c - bank 0: map loading, metatile rendering, collision lookup, sheet slots */
#include <string.h>
#include "hm.h"
#include "gen_dirs.h"

maphdr_t mh;
uint8_t cur_map = 0xFF;
uint8_t map_grid[256];
warp_t warps[MAX_WARPS];
obj_t objs[MAX_OBJS];
uint8_t mt_flags[64];
static uint8_t mt_tiles[256];
static uint8_t mt_attr[256];
uint8_t cur_tileset = 0xFF;
static uint8_t patch_bank;
static const uint8_t *patch_ptr;

uint8_t mt_at(uint8_t tx, uint8_t ty) {
    if (tx >= mh.w || ty >= mh.h) return 0xFF;
    return map_grid[(ty << 4) | tx];
}

uint8_t mflags_at(uint8_t tx, uint8_t ty) {
    uint8_t m;
    if (tx >= mh.w || ty >= mh.h) return MF_SOLID;
    m = map_grid[(ty << 4) | tx];
    return mt_flags[m & 63];
}

static void draw_mt(uint8_t tx, uint8_t ty) {
    uint8_t m = map_grid[(ty << 4) | tx] & 63;
    uint8_t *t = &mt_tiles[m << 2];
    uint8_t *a = &mt_attr[m << 2];
    VBK_REG = 1;
    set_bkg_tiles(tx << 1, ty << 1, 2, 2, a);
    VBK_REG = 0;
    set_bkg_tiles(tx << 1, ty << 1, 2, 2, t);
}

void map_set(uint8_t tx, uint8_t ty, uint8_t mt) {
    if (tx >= mh.w || ty >= mh.h) return;
    map_grid[(ty << 4) | tx] = mt;
    draw_mt(tx, ty);
}

void map_draw_all(void) {
    uint8_t x, y;
    for (y = 0; y < mh.h; y++)
        for (x = 0; x < mh.w; x++)
            draw_mt(x, y);
}

static void load_tileset(uint8_t ts) {
    far_t f;
    uint8_t n, nmt;
    const uint8_t *p;
    f = tileset_dir[ts];
    n = far_byte(f.bank, f.ptr);
    nmt = far_byte(f.bank, f.ptr + 1);
    p = f.ptr + 2;
    vram_bg_tiles(1, 0, n ? n : 256, f.bank, p);
    p += (uint16_t)(n ? n : 256) * 16;
    far_read(f.bank, p, mt_tiles, (uint16_t)nmt * 4);
    p += (uint16_t)nmt * 4;
    far_read(f.bank, p, mt_attr, (uint16_t)nmt * 4);
    p += (uint16_t)nmt * 4;
    far_read(f.bank, p, mt_flags, nmt);
    cur_tileset = ts;
}

void map_reload_tileset(void) {
    load_tileset(mh.tileset);
}

void map_apply_patches(void) {
    uint8_t i, b[5];
    const uint8_t *p = patch_ptr;
    for (i = 0; i < mh.npatches; i++) {
        far_read(patch_bank, p, b, 5);
        p += 5;
        if (cond_ok(b[3] | ((uint16_t)b[4] << 8))) {
            if (b[0] < 16 && b[1] < 16) map_grid[(b[1] << 4) | b[0]] = b[2];
        }
    }
}

void map_load(uint8_t id) {
    far_t f;
    const uint8_t *p;
    uint8_t y;
    f = map_dir[id];
    p = f.ptr;
    cur_map = id;
    far_read(f.bank, p, &mh, sizeof(maphdr_t));
    p += sizeof(maphdr_t);
    memset(map_grid, 0, 256);
    for (y = 0; y < mh.h; y++) {
        far_read(f.bank, p, &map_grid[y << 4], mh.w);
        p += mh.w;
    }
    far_read(f.bank, p, warps, (uint16_t)mh.nwarps * sizeof(warp_t));
    p += (uint16_t)mh.nwarps * sizeof(warp_t);
    far_read(f.bank, p, objs, (uint16_t)mh.nobjs * sizeof(obj_t));
    p += (uint16_t)mh.nobjs * sizeof(obj_t);
    patch_bank = f.bank;
    patch_ptr = p;
    map_apply_patches();
    if (mh.tileset != cur_tileset) load_tileset(mh.tileset);
    load_bg_palset(mh.palset);
    map_draw_all();
}

/* lightning on rainy outdoor maps */
void map_anim_tick(void) {
    if ((mh.flags & MAPF_RAIN) && rand8() == 7 && (frame_ctr & 1)) {
        flash_white(2);
        sfx_play(16);
    }
}

/* ---------------------------------------------------------- sprite sheet slots */
uint8_t slot_sheet[NUM_SLOTS];

uint8_t slot_tile(uint8_t slot) {
    return slot < 6 ? 100 + slot * 24 : 24 + (slot - 6) * 24;
}

uint8_t slot_attr(uint8_t slot, uint8_t pal) {
    return pal | (slot < 6 ? 0 : 0x08);
}

uint8_t sheet_load(uint8_t sheet) {
    uint8_t i;
    sheet_t s;
    s = sheet_dir[sheet];
    for (i = 0; i < NUM_SLOTS; i++)
        if (slot_sheet[i] == sheet) return i;
    if (s.big) {
        static const uint8_t pairs[4] = {0, 2, 6, 8};
        for (i = 0; i < 4; i++) {
            uint8_t sl = pairs[i];
            if (slot_sheet[sl] == 0xFF && slot_sheet[sl + 1] == 0xFF) {
                slot_sheet[sl] = sheet;
                slot_sheet[sl + 1] = 0xFE;
                vram_spr_tiles(sl < 6 ? 0 : 1, slot_tile(sl), 48, s.bank, s.ptr);
                return sl;
            }
        }
        return 0;
    }
    for (i = 0; i < NUM_SLOTS; i++) {
        if (slot_sheet[i] == 0xFF) {
            slot_sheet[i] = sheet;
            vram_spr_tiles(i < 6 ? 0 : 1, slot_tile(i), 24, s.bank, s.ptr);
            return i;
        }
    }
    return 0;  /* out of slots: reuse slot 0 (content checker prevents this) */
}

far_t script_dir_get(uint16_t id) {
    far_t f;
    far_read(script_dir_BANK, &script_dir[id], &f, sizeof(far_t));
    return f;
}
