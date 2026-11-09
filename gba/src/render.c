/* render.c (GBA) - camera and OAM composition (shadow OAM flushed in VBlank) */
#include "hm.h"
#include "gba_dirs.h"

int16_t cam_x, cam_y;
uint8_t shake_t;
uint8_t shadow_mode;
uint8_t big_shadow_on;
int16_t big_shadow_x, big_shadow_y;
static uint16_t oam[128 * 4] __attribute__((aligned(4)));
static uint8_t oam_n;
static uint8_t image_view;
extern uint8_t image_mode;

#define TRAIL 32
static int16_t trail_x[TRAIL], trail_y[TRAIL];
static uint8_t trail_i;

#define SHAPE_SQ 0
#define SHAPE_TALL 2
#define FX_TILE(i) (32 + (i) * 4)

/* streamed character frames: VRAM slot k (0 = player) receives the current 1 KB frame */
static const uint8_t *slot_src[13];
static const uint8_t *up_src[13];
static uint8_t up_k[13], n_up;
extern const uint8_t spr_player[];

void oam_flush(void) {
    uint8_t i;
    for (i = 0; i < n_up; i++)
        dma3_copy32(CHARBLOCK(4) + (up_k[i] ? 128 + (up_k[i] - 1) * 32 : 0) * 16, up_src[i], 256);
    n_up = 0;
    dma3_copy32(MEM_OAM, oam, 256);
}

void hide_all_sprites(void) {
    int i;
    for (i = 0; i < 128; i++) { oam[i * 4] = 0x0200; oam[i * 4 + 1] = 0; oam[i * 4 + 2] = 0; }
}

void camera_update(void) {
    int16_t mw = (int16_t)mh.w * 16, mhh = (int16_t)mh.h * 16;
    cam_x = (pl_x >> 4) + 8 - 120;
    cam_y = (pl_y >> 4) + 8 - 80;
    if (mw <= 240) cam_x = -(240 - mw) / 2;
    else { if (cam_x > mw - 240) cam_x = mw - 240; if (cam_x < 0) cam_x = 0; }
    if (mhh <= 160) cam_y = -(160 - mhh) / 2;
    else { if (cam_y > mhh - 160) cam_y = mhh - 160; if (cam_y < 0) cam_y = 0; }
}

void apply_scroll(void) {
    int8_t sx = 0, sy = 0;
    if (shake_t) { shake_t--; sx = (rand8() & 3) - 1; sy = (rand8() & 3) - 1; }
    scroll_x = cam_x + sx;
    scroll_y = cam_y + sy;
}

static void spr(int16_t x, int16_t y, uint8_t shape, uint8_t size, uint16_t tile, uint8_t pal, uint16_t flip) {
    uint16_t *o;
    if (oam_n >= 128) return;
    if (x < -64 || x > 240 || y < -64 || y > 160) return;
    o = &oam[oam_n * 4];
    o[0] = (y & 0xFF) | (shape << 14);
    o[1] = (x & 0x1FF) | (size << 14) | flip;
    o[2] = tile | (2 << 10) | (pal << 12);
    oam_n++;
}

/* character: pre-rendered 32x64 frame, feet on the actor's 16x16 body box */
static uint8_t char_k;
static void draw_char_frames(int16_t wx, int16_t wy, const uint8_t *frames, uint8_t frame, uint8_t pal,
                             uint8_t flip, int16_t yoff) {
    uint8_t k = char_k++;
    const uint8_t *src = frames + (uint32_t)frame * 1024;
    if (k > 12) return;
    if (slot_src[k] != src && n_up < 13) { slot_src[k] = src; up_src[n_up] = src; up_k[n_up++] = k; }
    spr(wx - cam_x - 8, wy - cam_y - 44 + yoff, SHAPE_TALL, 3, k ? 128 + (k - 1) * 32 : 0, pal, flip ? 0x1000 : 0);
}

static void draw_fx(int16_t wx, int16_t wy, uint8_t idx, uint16_t flip) {
    spr(wx - cam_x, wy - cam_y, SHAPE_SQ, 1, FX_TILE(idx), 1, flip);
}

static uint8_t walk_frame(uint8_t dir, uint8_t anim, uint8_t *flip) {
    uint8_t ph = (anim >> 3) & 3;
    *flip = 0;
    if (dir == DIR_DOWN) return ph;
    if (dir == DIR_UP) return 4 + ph;
    *flip = dir == DIR_LEFT;
    return 8 + ph;
}

static void draw_shadow_follower(int16_t px, int16_t py) {
    uint8_t st = infl_stage(), idx, lag;
    int16_t x, y;
    if (shadow_mode == 0xFF) return;
    if (st == 0) { draw_fx(px, py + 4, SPR_SHADOW_BLOB, 0); return; }
    lag = st == 1 ? 6 : (st == 2 ? 14 : 22);
    idx = (trail_i - lag) & (TRAIL - 1);
    x = trail_x[idx]; y = trail_y[idx];
    if (st == 1) {
        if ((frame_ctr & 0x7F) < 20) x += 6;
        draw_fx(x, y + 4, SPR_SHADOW_BLOB, 0);
        return;
    }
    if (st == 3 && (frame_ctr & 0x1F) == 0) return;
    draw_fx(x, y - 4, SPR_SHADOW_HORNED, pl_dir == DIR_LEFT ? 0x1000 : 0);
}

void render_sprites(void) {
    uint8_t i, f, flip;
    int16_t px = pl_x >> 4, py = pl_y >> 4;
    oam_n = 0;
    char_k = 1;
    if (!image_mode) {
        for (i = 0; i < MAX_ACTORS; i++) {
            actor_t *a = &actors[i];
            if (a->type && a->icon) {
                uint8_t t = a->icon == 1 ? SPR_ALERT : (a->icon == 2 ? SPR_QUESTION : SPR_STARS);
                draw_fx((a->x >> 4), (a->y >> 4) - 30, t, 0);
            }
        }
    }
    if (big_shadow_on) spr(big_shadow_x + 40, big_shadow_y, SHAPE_SQ, 3, 512, 2, 0);
    if (image_mode) goto done;

    if (shadow_mode != 0xFE && !(pl_hurt & 2)) {
        if (pl_atk) {
            uint8_t wt = gs.weapon ? SPR_AXE_V : SPR_PIPE_V;
            uint8_t wh = gs.weapon ? SPR_AXE_H : SPR_PIPE_H;
            f = pl_dir == DIR_DOWN ? 12 : (pl_dir == DIR_UP ? 13 : 14);
            if (pl_atk > 2) {
                switch (pl_dir) {
                case DIR_DOWN: draw_fx(px - 2, py + 10, wt, 0x2000); break;
                case DIR_UP: draw_fx(px + 2, py - 20, wt, 0); break;
                case DIR_LEFT: draw_fx(px - 13, py - 2, wh, 0x1000); break;
                default: draw_fx(px + 13, py - 2, wh, 0); break;
                }
            }
            { uint8_t k0 = char_k; char_k = 0; draw_char_frames(px, py, spr_player, f, 0, pl_dir == DIR_LEFT, 0); char_k = k0; }
        } else {
            f = walk_frame(pl_dir, pl_anim, &flip);
            { uint8_t k0 = char_k; char_k = 0; draw_char_frames(px, py, spr_player, f, 0, flip, 0); char_k = k0; }
        }
    }

    for (i = 0; i < MAX_ACTORS; i++) {
        actor_t *a = &actors[i];
        int16_t ax, ay;
        if (!a->type) continue;
        if ((a->hurt & 2) && a->type != ACT_FX) continue;
        ax = a->x >> 4; ay = a->y >> 4;
        if (a->size == 1 || a->size == 3) {
            draw_fx(ax + (a->size == 1 ? -4 : 0), ay, (uint8_t)a->tile, a->dir == DIR_LEFT ? 0x1000 : 0);
        } else {
            f = walk_frame(a->dir, a->anim, &flip);
            draw_char_frames(ax + (a->size == 2 ? 8 : 0), ay + (a->size == 2 ? 16 : 0),
                             sheet_dir[a->tile].frames, f, a->attr, flip, 0);
        }
    }
    if (shadow_mode != 0xFE) draw_shadow_follower(px, py);
    if (trail_x[trail_i] != px || trail_y[trail_i] != py) {
        trail_i = (trail_i + 1) & (TRAIL - 1);
        trail_x[trail_i] = px; trail_y[trail_i] = py;
    }
done:
    for (i = oam_n; i < 128; i++) oam[i * 4] = 0x0200;
    (void)image_view;
}

void trail_reset(void) {
    uint8_t i;
    for (i = 0; i < TRAIL; i++) { trail_x[i] = pl_x >> 4; trail_y[i] = pl_y >> 4; }
}

/* raw sprite for non-gameplay screens (title smoke) */
void oam_set(uint8_t i, int16_t x, int16_t y, uint16_t tile, uint8_t pal) {
    uint16_t *o = &oam[i * 4];
    o[0] = (y & 0xFF) | (SHAPE_SQ << 14);
    o[1] = (x & 0x1FF) | (1 << 14);
    o[2] = tile | (1 << 10) | (pal << 12);
}
