/* render.c - bank 0: camera + OAM composition */
#include "hm.h"

int16_t cam_x, cam_y;
uint8_t shake_t;
uint8_t shadow_mode;
uint8_t big_shadow_on;
int16_t big_shadow_x, big_shadow_y;
static uint8_t oam_n;
static uint8_t clip_y;

/* trail of player positions for the Second Shadow follower */
#define TRAIL 32
static uint8_t trail_x[TRAIL], trail_y[TRAIL], trail_i;

void camera_update(void) {
    int16_t mx = (int16_t)mh.w * 16 - 160;
    int16_t my = (int16_t)mh.h * 16 - 136;
    cam_x = (pl_x >> 4) + 8 - 80;
    cam_y = (pl_y >> 4) + 8 - 68;
    if (cam_x > mx) cam_x = mx;
    if (cam_y > my) cam_y = my;
    if (cam_x < 0) cam_x = 0;
    if (cam_y < 0) cam_y = 0;
}

void apply_scroll(void) {
    int8_t sx = 0, sy = 0;
    if (shake_t) {
        shake_t--;
        sx = (rand8() & 3) - 1;
        sy = (rand8() & 3) - 1;
    }
    SCX_REG = (uint8_t)(cam_x + sx);
    SCY_REG = (uint8_t)(cam_y + sy);
}

static void spr(uint8_t x, uint8_t y, uint8_t tile, uint8_t attr) {
    if (oam_n >= 40) return;
    set_sprite_tile(oam_n, tile);
    set_sprite_prop(oam_n, attr);
    move_sprite(oam_n, x, y);
    oam_n++;
}

/* draw 16x16 at world pixel coords */
static void draw16(int16_t wx, int16_t wy, uint8_t tile, uint8_t attr, uint8_t flip) {
    int16_t sx = wx - cam_x + 8, sy = wy - cam_y + 16;
    if (sx < -8 || sx > 175 || sy < 0 || sy > 159) return;
    if (sy - 16 >= clip_y) return;
    if (flip) {
        spr((uint8_t)sx, (uint8_t)sy, tile + 2, attr | S_FLIPX);
        spr((uint8_t)(sx + 8), (uint8_t)sy, tile, attr | S_FLIPX);
    } else {
        spr((uint8_t)sx, (uint8_t)sy, tile, attr);
        spr((uint8_t)(sx + 8), (uint8_t)sy, tile + 2, attr);
    }
}

static void draw8(int16_t wx, int16_t wy, uint8_t tile, uint8_t attr) {
    int16_t sx = wx - cam_x + 8, sy = wy - cam_y + 16;
    if (sx < 0 || sx > 167 || sy < 0 || sy > 159) return;
    if (sy - 16 >= clip_y) return;
    spr((uint8_t)sx, (uint8_t)sy, tile, attr);
}

static void draw32(int16_t wx, int16_t wy, uint8_t tile, uint8_t attr, uint8_t flip) {
    uint8_t r, c;
    int16_t sx = wx - cam_x + 8, sy = wy - cam_y + 16;
    if (sx < -24 || sx > 175 || sy < 0 || sy > 175) return;
    for (r = 0; r < 2; r++) {
        int16_t yy = sy + r * 16;
        if (yy - 16 >= clip_y || yy < 0 || yy > 159) continue;
        for (c = 0; c < 4; c++) {
            int16_t xx = sx + (flip ? (3 - c) : c) * 8;
            if (xx < 0 || xx > 167) continue;
            spr((uint8_t)xx, (uint8_t)yy, tile + r * 8 + c * 2, attr | (flip ? S_FLIPX : 0));
        }
    }
}

static uint8_t walk_frame(uint8_t dir, uint8_t anim, uint8_t *flip) {
    uint8_t ph = (anim >> 3) & 3;
    *flip = 0;
    if (dir == DIR_DOWN || dir == DIR_UP) {
        uint8_t b = dir == DIR_DOWN ? 0 : 2;
        if (ph == 1) return b + 1;
        if (ph == 3) { *flip = 1; return b + 1; }
        return b;
    }
    *flip = dir == DIR_LEFT;
    return (ph & 1) ? 5 : 4;
}

static void draw_shadow_follower(int16_t px, int16_t py) {
    uint8_t st = infl_stage(), idx, lag;
    int16_t x, y;
    if (shadow_mode == 0xFF) return;
    if (st == 0) {
        draw16(px, py + 3, SPR_SHADOW_BLOB, 7, 0);
        return;
    }
    lag = st == 1 ? 6 : (st == 2 ? 14 : 22);
    idx = (trail_i - lag) & (TRAIL - 1);
    x = trail_x[idx];
    y = trail_y[idx];
    if (st == 1) {
        if ((frame_ctr & 0x7F) < 20) x += 6;   /* drifts on its own */
        draw16(x, y + 3, SPR_SHADOW_BLOB, 7, 0);
        return;
    }
    if (st == 3 && (frame_ctr & 0x1F) == 0) return;   /* flicker */
    draw16(x, y - 4, SPR_SHADOW_HORNED, 7, pl_dir == DIR_LEFT);
}

void render_sprites(void) {
    uint8_t i, f, flip;
    int16_t px = pl_x >> 4, py = pl_y >> 4;
    oam_n = 0;
    clip_y = dlg_is_open ? 96 - 4 : 136 - 4;

    /* icons above actors */
    for (i = 0; i < MAX_ACTORS; i++) {
        actor_t *a = &actors[i];
        if (a->type && a->icon) {
            uint8_t t = a->icon == 1 ? SPR_ALERT : (a->icon == 2 ? SPR_QUESTION : SPR_STARS);
            draw8((a->x >> 4) + 4, (a->y >> 4) - 14, t, 5);
        }
    }

    /* big Second Shadow figure (cutscenes): 32x48 from VRAM1 tiles 0..23 */
    if (big_shadow_on) {
        uint8_t r, c;
        for (r = 0; r < 3; r++)
            for (c = 0; c < 4; c++)
                spr((uint8_t)(big_shadow_x + 8 + c * 8), (uint8_t)(big_shadow_y + 16 + r * 16),
                    r * 8 + c * 2, 7 | 0x08);
    }

    /* player + weapon */
    if (shadow_mode != 0xFE && !(pl_hurt & 2)) {
        if (pl_atk) {
            uint8_t wt = gs.weapon ? SPR_AXE_V : SPR_PIPE_V;
            uint8_t wh = gs.weapon ? SPR_AXE_H : SPR_PIPE_H;
            f = pl_dir == DIR_DOWN ? 6 : (pl_dir == DIR_UP ? 7 : 8);
            if (pl_atk > 2) {
                switch (pl_dir) {
                case DIR_DOWN: draw16(px - 2, py + 12, wt, 0 | S_FLIPY, 0); break;
                case DIR_UP: draw16(px + 2, py - 12, wt, 0, 0); break;
                case DIR_LEFT: draw16(px - 13, py + 1, wh, 0, 1); break;
                default: draw16(px + 13, py + 1, wh, 0, 0); break;
                }
            }
            draw16(px, py, f * 4, 0, pl_dir == DIR_LEFT);
        } else {
            f = walk_frame(pl_dir, pl_anim, &flip);
            draw16(px, py, f * 4, 0, flip);
        }
    }

    /* actors */
    for (i = 0; i < MAX_ACTORS; i++) {
        actor_t *a = &actors[i];
        int16_t ax, ay;
        if (!a->type) continue;
        if ((a->hurt & 2) && a->type != ACT_FX) continue;
        ax = a->x >> 4;
        ay = a->y >> 4;
        if (a->size == 1) {
            draw8(ax, ay, a->tile, a->attr);
        } else if (a->size == 2) {
            f = a->dir == DIR_DOWN ? 0 : (a->dir == DIR_UP ? 1 : 2);
            draw32(ax, ay, a->tile + f * 16, a->attr, a->dir == DIR_LEFT);
        } else if (a->size == 3) {
            /* fixed 16x16 effect tile */
            draw16(ax, ay, a->tile, a->attr, a->dir == DIR_LEFT);
        } else {
            f = walk_frame(a->dir, a->anim, &flip);
            draw16(ax, ay, a->tile + f * 4, a->attr, flip);
        }
    }

    if (shadow_mode != 0xFE) draw_shadow_follower(px, py);

    /* trail update */
    if (trail_x[trail_i] != (uint8_t)px || trail_y[trail_i] != (uint8_t)py) {
        trail_i = (trail_i + 1) & (TRAIL - 1);
        trail_x[trail_i] = (uint8_t)px;
        trail_y[trail_i] = (uint8_t)py;
    }

    for (i = oam_n; i < 40; i++) move_sprite(i, 0, 0);
}

void trail_reset(void) {
    uint8_t i;
    for (i = 0; i < TRAIL; i++) {
        trail_x[i] = pl_x >> 4;
        trail_y[i] = pl_y >> 4;
    }
}
