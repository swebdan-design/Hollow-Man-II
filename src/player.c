#pragma bank 255
/* player.c - Hollow Man: movement, collision, melee, tools, interaction */
#include "hm.h"

int16_t pl_x, pl_y;
uint8_t pl_dir, pl_anim, pl_atk, pl_hurt, pl_charge, pl_busy;
static uint8_t atk_heavy, step_t, push_t;
uint8_t shadow_cast;

static const int8_t dxs[4] = {0, 0, -1, 1};
static const int8_t dys[4] = {1, -1, 0, 0};

void player_place(uint8_t tx, uint8_t ty, uint8_t dir) BANKED {
    pl_x = ((int16_t)tx * 16) << 4;
    pl_y = (((int16_t)ty * 16) - 4) << 4;
    pl_dir = dir;
    pl_atk = 0; pl_hurt = 0; pl_charge = 0; pl_anim = 0;
    trail_reset();
}

/* feet hitbox: x+3..x+12, y+9..y+15 (pixels) */
static uint8_t blocked_at(int16_t px, int16_t py) {
    int16_t x0 = px + 3, x1 = px + 12, y0 = py + 9, y1 = py + 15;
    /* walking off an edge is only possible where the map has an exit */
    if (x0 < 0) return mh.exits[2] == 0xFF;
    if (y0 < 0) return mh.exits[0] == 0xFF;
    if (x1 >= (int16_t)mh.w * 16) return mh.exits[3] == 0xFF;
    if (y1 >= (int16_t)mh.h * 16) return mh.exits[1] == 0xFF;
    if (mflags_at(x0 >> 4, y0 >> 4) & MF_SOLID) return 1;
    if (mflags_at(x1 >> 4, y0 >> 4) & MF_SOLID) return 1;
    if (mflags_at(x0 >> 4, y1 >> 4) & MF_SOLID) return 1;
    if (mflags_at(x1 >> 4, y1 >> 4) & MF_SOLID) return 1;
    if (actor_blocks(px, py, 0xFF)) return 1;
    return 0;
}

/* sokoban-style crate push: crate tile moves one metatile if the far side is free floor */
static void try_push(void) {
    int16_t cx = (pl_x >> 4) + 8 + dxs[pl_dir] * 10, cy = (pl_y >> 4) + 12 + dys[pl_dir] * 8;
    uint8_t tx, ty, nx, ny, m, dst;
    if (cx < 0 || cy < 0) return;
    tx = cx >> 4; ty = cy >> 4;
    if (!(mflags_at(tx, ty) & MF_PUSH)) { push_t = 0; return; }
    if (++push_t < 16) return;
    push_t = 0;
    nx = tx + dxs[pl_dir]; ny = ty + dys[pl_dir];
    dst = mt_at(nx, ny);
    if (dst == 0xFF || (mt_flags[dst & 63] & (MF_SOLID | MF_WATER))) { sfx_play(15); return; }
    m = mt_at(tx, ty);
    map_set(nx, ny, m);
    map_set(tx, ty, 0);   /* metatile 0 is the base floor of every tileset */
    sfx_play(13);
    shake_t = 4;
}

static void start_attack(uint8_t heavy) {
    pl_atk = heavy ? 20 : 14;
    atk_heavy = heavy;
    sfx_play(heavy ? 17 : 3);
}

static void do_attack_hit(void) {
    int16_t px = pl_x >> 4, py = pl_y >> 4;
    int16_t x0, y0;
    uint8_t dmg = (gs.weapon ? 2 : 1) * (atk_heavy ? 2 : 1);
    switch (pl_dir) {
    case DIR_DOWN: x0 = px; y0 = py + 12; break;
    case DIR_UP: x0 = px; y0 = py - 12; break;
    case DIR_LEFT: x0 = px - 14; y0 = py + 2; break;
    default: x0 = px + 14; y0 = py + 2; break;
    }
    if (x0 < 0) x0 = 0;
    if (y0 < 0) y0 = 0;
    actors_hit_box((uint8_t)x0, (uint8_t)y0, (uint8_t)(x0 + 15), (uint8_t)(y0 + 15), dmg, atk_heavy);
}

/* A button: interact with what's in front; otherwise use the equipped tool */
static uint8_t try_interact(void) {
    int16_t fx = (pl_x >> 4) + 8 + dxs[pl_dir] * 14, fy = (pl_y >> 4) + 11 + dys[pl_dir] * 14;
    uint8_t tx, ty, i;
    if (fx < 0 || fy < 0) return 0;
    tx = fx >> 4; ty = fy >> 4;
    /* NPCs */
    for (i = 0; i < MAX_ACTORS; i++) {
        actor_t *a = &actors[i];
        int16_t ax, ay;
        if (a->type != ACT_NPC) continue;
        ax = (a->x >> 4) + 8; ay = (a->y >> 4) + 10;
        if (ABS(ax - fx) < 12 && ABS(ay - fy) < 12) {
            if (a->obj != 0xFF && objs[a->obj].script != 0xFFFF) {
                a->dir = pl_dir ^ 1;
                if (pl_dir >= 2) a->dir = pl_dir == DIR_LEFT ? DIR_RIGHT : DIR_LEFT;
                render_sprites();
                script_queue(objs[a->obj].script);
                return 1;
            }
        }
    }
    /* signs / searchable objects */
    for (i = 0; i < mh.nobjs; i++) {
        obj_t *o = &objs[i];
        if (o->type == OBJ_SIGN && o->x == tx && o->y == ty && cond_ok(o->cond)) {
            script_queue(o->script);
            return 1;
        }
    }
    if (mflags_at(tx, ty) & MF_SHADOW) {
        dlg_say("The bricks are\ncold to the touch.\nSomething behind\nthem breathes.");
        dlg_close();
        return 1;
    }
    return 0;
}

static void use_tool(void) {
    int16_t px = pl_x >> 4, py = pl_y >> 4;
    int8_t a;
    switch (gs.tool) {
    case TOOL_PISTOL:
        if (!gs.ammo) { sfx_play(15); return; }
        gs.ammo--;
        a = actor_new(ACT_PPROJ, 0, (px + 4) << 4, (py + 2) << 4);
        if (a >= 0) {
            actors[a].dir = pl_dir;
            actors[a].tile = SPR_BULLET;
            actors[a].attr = 5;
            actors[a].size = 1;
            actors[a].timer = 50;
        }
        sfx_play(5);
        shake_t = 3;
        alert_add((mh.flags & MAPF_OUTDOOR) ? 25 : 15);
        actors_noise(px + 8, py + 8, 140);
        hud_dirty = 1;
        break;
    case TOOL_BOTTLE:
        if (!gs.bottles) { sfx_play(15); return; }
        gs.bottles--;
        a = actor_new(ACT_BOTTLE, 0, (px + 4) << 4, (py + 2) << 4);
        if (a >= 0) {
            actors[a].dir = pl_dir;
            actors[a].tile = SPR_BOTTLE;
            actors[a].attr = 0;
            actors[a].size = 1;
            actors[a].timer = 28;
        }
        sfx_play(3);
        if (!gs.bottles) gs.tool = TOOL_NONE;
        hud_dirty = 1;
        break;
    case TOOL_SHADOW: {
        int16_t fx = px + 8 + dxs[pl_dir] * 14, fy = py + 11 + dys[pl_dir] * 14;
        uint8_t i;
        flash_red(4);
        sfx_play(10);
        shake_t = 10;
        infl_add(3);
        actors_stun_near(px + 8, py + 8, 64, infl_stage() >= 2 ? 2 : 0);
        /* opens shadow walls: run the wall's script with shadow_cast set */
        if (fx >= 0 && fy >= 0 && (mflags_at(fx >> 4, fy >> 4) & MF_SHADOW)) {
            for (i = 0; i < mh.nobjs; i++) {
                obj_t *o = &objs[i];
                if (o->type == OBJ_SIGN && o->x == (fx >> 4) && o->y == (fy >> 4)) {
                    flag_set(F_SHADOWCAST);
                    script_run(o->script);
                    flag_clr(F_SHADOWCAST);
                }
            }
        }
        break;
    }
    case TOOL_BANDAGE:
        if (!gs.bandages || gs.hp >= gs.maxhp) { sfx_play(15); return; }
        gs.bandages--;
        gs.hp = gs.hp + 4 > gs.maxhp ? gs.maxhp : gs.hp + 4;
        sfx_play(9);
        if (!gs.bandages) gs.tool = TOOL_NONE;
        hud_dirty = 1;
        break;
    default:
        break;
    }
}

void player_damage(uint8_t dmg, uint8_t fromdir) BANKED {
    if (pl_hurt || gs.hp == 0) return;
    gs.hp = gs.hp > dmg ? gs.hp - dmg : 0;
    pl_hurt = 60;
    pl_atk = 0;
    pl_charge = 0;
    sfx_play(6);
    shake_t = 6;
    hud_dirty = 1;
    if (fromdir < 4) {
        /* knockback 12 px if free */
        uint8_t i;
        for (i = 0; i < 12; i++) {
            int16_t nx = pl_x + dxs[fromdir] * 16, ny = pl_y + dys[fromdir] * 16;
            if (blocked_at(nx >> 4, ny >> 4)) break;
            pl_x = nx; pl_y = ny;
        }
    }
}

void player_update(void) BANKED {
    uint8_t moving = 0, d = 0xFF, speed;
    int16_t px = pl_x >> 4, py = pl_y >> 4;

    if (pl_hurt) pl_hurt--;

    /* attacking: lock movement */
    if (pl_atk) {
        pl_atk--;
        if (pl_atk == 8 || (atk_heavy && pl_atk == 12)) do_attack_hit();
        return;
    }

    /* B: attack; hold to charge a heavy strike */
    if (joy & J_B) {
        if (pl_charge < 255) pl_charge++;
        if (pl_charge == 40) { sfx_play(14); flash_white(1); }
    } else if (pl_charge) {
        start_attack(pl_charge >= 40);
        pl_charge = 0;
        return;
    }

    if (joy_new & J_A) {
        if (!try_interact()) use_tool();
        return;
    }

    if (joy & J_LEFT) d = DIR_LEFT;
    else if (joy & J_RIGHT) d = DIR_RIGHT;
    else if (joy & J_UP) d = DIR_UP;
    else if (joy & J_DOWN) d = DIR_DOWN;

    if (d != 0xFF) {
        int16_t nx, ny;
        uint8_t i;
        pl_dir = d;
        speed = pl_charge ? 10 : 20;
        if (mflags_at((px + 8) >> 4, (py + 12) >> 4) & MF_SLOW) speed = 12;
        nx = pl_x + dxs[d] * speed;
        ny = pl_y + dys[d] * speed;
        if (!blocked_at(nx >> 4, ny >> 4)) {
            pl_x = nx; pl_y = ny;
            moving = 1;
            push_t = 0;
        } else {
            /* corner nudge: slide around corners up to 6 px */
            for (i = 1; i <= 6; i++) {
                if (d >= 2) {
                    if (!blocked_at(nx >> 4, (ny >> 4) - i)) { pl_y -= 16; moving = 1; break; }
                    if (!blocked_at(nx >> 4, (ny >> 4) + i)) { pl_y += 16; moving = 1; break; }
                } else {
                    if (!blocked_at((nx >> 4) - i, ny >> 4)) { pl_x -= 16; moving = 1; break; }
                    if (!blocked_at((nx >> 4) + i, ny >> 4)) { pl_x += 16; moving = 1; break; }
                }
            }
            try_push();
        }
    }
    if (moving) {
        pl_anim++;
        if (++step_t >= 18) {
            step_t = 0;
            if (!(mh.flags & MAPF_OUTDOOR)) sfx_play(13);
        }
        /* hazard tiles */
        if (mflags_at((px + 8) >> 4, (py + 12) >> 4) & MF_HAZARD) player_damage(1, 0xFF);
    } else {
        pl_anim = 0;
    }
}
