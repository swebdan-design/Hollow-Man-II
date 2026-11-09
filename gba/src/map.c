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

static uint8_t base_grid[256];
static const mapgfx_t *gfx;

/* draw one metatile: the baked picture where the map is unchanged, otherwise a pre-lit piece */
static void draw_mt(uint8_t tx, uint8_t ty) {
    uint8_t m = map_grid[(ty << 4) | tx];
    uint16_t *d = &MAPSB[(ty * 2) * 32 + tx * 2];
    const uint16_t *e = 0;
    uint8_t i;
    if (m == base_grid[(ty << 4) | tx]) {
        const uint16_t *b = gfx->map + (ty * 2) * (mh.w * 2) + tx * 2;
        d[0] = b[0]; d[1] = b[1]; d[32] = b[mh.w * 2]; d[33] = b[mh.w * 2 + 1];
        return;
    }
    for (i = 0; i < gfx->ndyn; i++) {
        const uint16_t *q = gfx->dyn + i * 6;
        if (q[1] != m) continue;
        if (q[0] == (tx | (ty << 8))) { e = q + 2; break; }
        if (q[0] == 0xFFFF && !e) e = q + 2;
    }
    if (!e) return;
    d[0] = e[0]; d[1] = e[1]; d[32] = e[2]; d[33] = e[3];
}

void map_set(uint8_t tx, uint8_t ty, uint8_t mt) {
    if (tx >= mh.w || ty >= mh.h) return;
    map_grid[(ty << 4) | tx] = mt;
    draw_mt(tx, ty);
}

void map_draw_all(void) {
    uint8_t x, y;
    dma3_fill32(MAPSB, 0, 512);
    for (y = 0; y < mh.h; y++)
        for (x = 0; x < mh.w; x++) draw_mt(x, y);
}

/* collision flags come from the tileset; graphics come from the map's own baked picture */
static void load_tileset(uint8_t ts) {
    memcpy(mt_flags, tilesets[ts].flags, tilesets[ts].nmt);
    cur_tileset = ts;
}

static void load_map_gfx(void) {
    dma3_fill32(CHARBLOCK(0), 0, 8);                       /* tile 0 = empty void */
    memcpy(CHARBLOCK(0) + 16, gfx->tiles, gfx->ntiles * 32);
}

void map_reload_tileset(void) { load_tileset(mh.tileset); load_map_gfx(); }

const uint16_t *map_pals(void) { return gfx ? gfx->pals : 0; }

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
    memcpy(base_grid, map_grid, 256);
    map_apply_patches();
    gfx = &mapgfx[id];
    load_tileset(mh.tileset);
    load_map_gfx();
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

/* ---------------------------------------------------------------- sprite sheets
 * Characters are pre-rendered 32x64 frames streamed into VRAM as they animate (render.c).
 * A "slot" now only owns an OBJ palette bank (3 + slot) for one sheet on this map. */
uint8_t slot_sheet[NUM_SLOTS];

uint16_t slot_tile(uint8_t slot) { return slot_sheet[slot]; }
uint8_t slot_attr(uint8_t slot, uint8_t pal) { (void)pal; return 3 + slot; }

uint8_t sheet_load(uint8_t sheet) {
    uint8_t i;
    const sheet_t *s = &sheet_dir[sheet];
    for (i = 0; i < NUM_SLOTS; i++) if (slot_sheet[i] == sheet) return i;
    for (i = 0; i < NUM_SLOTS; i++) {
        if (slot_sheet[i] == 0xFF) {
            slot_sheet[i] = sheet;
            memcpy(&obj_pal[(3 + i) * 16], s->pal, 32);
            dma3_copy32(MEM_PAL_OBJ + (3 + i) * 16, &obj_pal[(3 + i) * 16], 8);
            return i;
        }
    }
    return 0;
}
