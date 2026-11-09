/* map.c (GBA) - metatile maps on BG0 (4bpp, charblock 0, screenblock 28), sprite-sheet slots */
#include "hm.h"
#include "gba_dirs.h"

maphdr_t mh;
uint8_t cur_map = 0xFF;
uint8_t map_grid[256];
warp_t warps[MAX_WARPS];
obj_t objs[MAX_OBJS];
uint8_t mt_flags[64];
static uint16_t mt_ent[64 * 4];
uint8_t cur_tileset = 0xFF;
static const uint8_t *patch_ptr;
#define MAPSB ((uint16_t *)SCREENBLOCK(28))

uint8_t mt_at(uint8_t tx, uint8_t ty) {
    if (tx >= mh.w || ty >= mh.h) return 0xFF;
    return map_grid[(ty << 4) | tx];
}

uint8_t mflags_at(uint8_t tx, uint8_t ty) {
    if (tx >= mh.w || ty >= mh.h) return MF_SOLID;
    return mt_flags[map_grid[(ty << 4) | tx] & 63];
}

static uint8_t wall_mt = 0xFF, top_mt = 0xFF;

static void draw_mt(uint8_t tx, uint8_t ty) {
    uint8_t m = map_grid[(ty << 4) | tx] & 63;
    uint16_t *e;
    /* auto wall-tops: a wall with another wall (or the map edge) below shows its top */
    if (m == wall_mt && (ty + 1 >= mh.h || (mt_flags[map_grid[((ty + 1) << 4) | tx] & 63] & MF_SOLID) ||
                         (map_grid[((ty + 1) << 4) | tx] & 63) == wall_mt))
        m = top_mt;
    e = &mt_ent[m << 2];
    uint16_t *d = &MAPSB[(ty * 2) * 32 + tx * 2];
    d[0] = e[0] + 1; d[1] = e[1] + 1; d[32] = e[2] + 1; d[33] = e[3] + 1;
}

void map_set(uint8_t tx, uint8_t ty, uint8_t mt) {
    if (tx >= mh.w || ty >= mh.h) return;
    map_grid[(ty << 4) | tx] = mt;
    draw_mt(tx, ty);
    if (ty) draw_mt(tx, ty - 1);
}

void map_draw_all(void) {
    uint8_t x, y;
    dma3_fill32(MAPSB, 0, 512);
    for (y = 0; y < mh.h; y++)
        for (x = 0; x < mh.w; x++) draw_mt(x, y);
}

static void load_tileset(uint8_t ts) {
    const tileset_t *t = &tilesets[ts];
    dma3_fill32(CHARBLOCK(0), 0, 8);                       /* tile 0 = empty void */
    memcpy(CHARBLOCK(0) + 16, t->tiles, t->ntiles * 32);
    memcpy(mt_ent, t->mt, t->nmt * 8);
    memcpy(mt_flags, t->flags, t->nmt);
    wall_mt = t->wall_mt; top_mt = t->top_mt;
    cur_tileset = ts;
}

void map_reload_tileset(void) { load_tileset(mh.tileset); }

void map_apply_patches(void) {
    uint8_t i;
    const uint8_t *p = patch_ptr;
    for (i = 0; i < mh.npatches; i++, p += 5) {
        if (cond_ok(p[3] | (p[4] << 8)) && p[0] < 16 && p[1] < 16)
            map_grid[(p[1] << 4) | p[0]] = p[2];
    }
}

void map_load(uint8_t id) {
    const uint8_t *p = map_dir[id].ptr;
    uint8_t y;
    cur_map = id;
    memcpy(&mh, p, 16);
    mh.enter_script = p[11] | (p[12] << 8);
    mh.nwarps = p[13]; mh.nobjs = p[14]; mh.npatches = p[15];
    p += 16;
    memset(map_grid, 0, 256);
    for (y = 0; y < mh.h; y++) { memcpy(&map_grid[y << 4], p, mh.w); p += mh.w; }
    for (y = 0; y < mh.nwarps; y++, p += 10) {
        warp_t *w = &warps[y];
        w->x = p[0]; w->y = p[1]; w->dmap = p[2]; w->dx = p[3]; w->dy = p[4]; w->ddir = p[5];
        w->cond = p[6] | (p[7] << 8); w->lockscript = p[8] | (p[9] << 8);
    }
    for (y = 0; y < mh.nobjs; y++, p += 10) {
        obj_t *o = &objs[y];
        o->type = p[0]; o->x = p[1]; o->y = p[2]; o->a = p[3]; o->b = p[4]; o->c = p[5];
        o->cond = p[6] | (p[7] << 8); o->script = p[8] | (p[9] << 8);
    }
    patch_ptr = p;
    map_apply_patches();
    if (mh.tileset != cur_tileset) load_tileset(mh.tileset);
    load_bg_palset(mh.palset);
    map_draw_all();
}

void map_anim_tick(void) {
    if ((mh.flags & MAPF_RAIN) && rand8() == 7 && (frame_ctr & 1)) {
        flash_white(2);
        sfx_play(16);
    }
}

far_t script_dir_get(uint16_t id) { return script_dir[id]; }

/* ---------------------------------------------------------------- sprite sheet slots
 * 10 slots of 72 OBJ tiles (9 frames of 16x32) from tile 256; palette bank 3 + slot.
 * A big sheet (3 frames of 32x64 = 96 tiles) takes two adjacent slots. */
uint8_t slot_sheet[NUM_SLOTS];

uint16_t slot_tile(uint8_t slot) { return 256 + slot * 72; }
uint8_t slot_attr(uint8_t slot, uint8_t pal) { (void)pal; return 3 + slot; }

uint8_t sheet_load(uint8_t sheet) {
    uint8_t i;
    const sheet_t *s = &sheet_dir[sheet];
    for (i = 0; i < NUM_SLOTS; i++) if (slot_sheet[i] == sheet) return i;
    for (i = 0; i < NUM_SLOTS - (s->big ? 1 : 0); i++) {
        if (slot_sheet[i] == 0xFF && (!s->big || slot_sheet[i + 1] == 0xFF)) {
            slot_sheet[i] = sheet;
            if (s->big) slot_sheet[i + 1] = 0xFE;
            memcpy(CHARBLOCK(4) + slot_tile(i) * 16, s->tiles, s->big ? 96 * 32 : 72 * 32);
            memcpy(&obj_pal[(3 + i) * 16], s->pal, 32);
            dma3_copy32(MEM_PAL_OBJ + (3 + i) * 16, &obj_pal[(3 + i) * 16], 8);
            return i;
        }
    }
    return 0;
}
