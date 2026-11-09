
/* actors.c - NPCs, enemies (patrol / stealth / chase / search), projectiles, pickups, hazards */
#include "hm.h"
#include "gba_dirs.h"

actor_t actors[MAX_ACTORS];
uint8_t noise_x, noise_y, noise_t;

enum { ST_PATROL, ST_ALERT, ST_CHASE, ST_ATTACK, ST_SEARCH, ST_RETURN, ST_STUN, ST_COOL };

#define K_THUG 0
#define K_RUNNER 1
#define K_GUNMAN 2
#define K_POLICE 3
#define K_WRAITH 4
#define K_RAT 5
#define K_HEART 10
#define K_AMMO 11

static const uint8_t kind_hp[6] = {3, 2, 3, 3, 4, 1};
static const uint8_t kind_patrol_spd[6] = {8, 10, 8, 8, 6, 12};
static const uint8_t kind_chase_spd[6] = {17, 26, 12, 15, 9, 20};
static const uint8_t kind_sheet[6] = {SHEET_THUG, SHEET_RUNNER, SHEET_GUNMAN, SHEET_POLICE, SHEET_WRAITH, 0};

static const int8_t dxs[4] = {0, 0, -1, 1};
static const int8_t dys[4] = {1, -1, 0, 0};

void actors_clear(void) {
    uint8_t i;
    for (i = 0; i < MAX_ACTORS; i++) actors[i].type = ACT_NONE;
}

int8_t actor_new(uint8_t type, uint8_t kind, int16_t x, int16_t y) {
    uint8_t i;
    for (i = 0; i < MAX_ACTORS; i++) {
        actor_t *a = &actors[i];
        if (a->type == ACT_NONE) {
            uint8_t *p = (uint8_t *)a, k;
            for (k = 0; k < sizeof(actor_t); k++) p[k] = 0;
            a->type = type;
            a->kind = kind;
            a->x = x;
            a->y = y;
            a->obj = 0xFF;
            return i;
        }
    }
    return -1;
}

static void set_sheet(actor_t *a, uint8_t sheet) {
    uint8_t sl = sheet_load(sheet);
    a->tile = slot_tile(sl);
    a->attr = slot_attr(sl, 0);
    a->size = sheet_dir[sheet].big ? 2 : 0;
}

void spawn_obj_actor(uint8_t oi) {
    obj_t *o = &objs[oi];
    int8_t ai;
    actor_t *a;
    int16_t x = ((int16_t)o->x * 16) << 4, y = (((int16_t)o->y * 16) - 4) << 4;
    switch (o->type) {
    case OBJ_NPC:
        ai = actor_new(ACT_NPC, o->b, x, y);
        if (ai < 0) return;
        a = &actors[ai];
        set_sheet(a, o->a);
        a->dir = o->c;
        break;
    case OBJ_ENEMY:
        ai = actor_new(ACT_ENEMY, o->a, x, y);
        if (ai < 0) return;
        a = &actors[ai];
        if (o->a == K_RAT) { a->tile = SPR_RAT_SIDE; a->attr = 2; a->size = 3; }
        else set_sheet(a, kind_sheet[o->a]);
        a->hp = kind_hp[o->a];
        a->dir = o->c;
        a->aux = o->b;     /* patrol mode<<4 | range */
        a->hx = o->x; a->hy = o->y;
        break;
    case OBJ_BOSS:
        ai = actor_new(ACT_BOSS, o->a, x, y);
        if (ai < 0) return;
        a = &actors[ai];
        a->aux2 = o->b;
        boss_init(a);
        break;
    case OBJ_HAZARD:
        ai = actor_new(ACT_HAZARD, o->a, x, y + (4 << 4));
        if (ai < 0) return;
        a = &actors[ai];
        a->tile = o->a == 0 ? SPR_SAW : SPR_BELL;
        if (o->a == 1) a->tile = SPR_SHADOW_BLOB;
        a->attr = o->a == 0 ? 5 : 3;
        a->size = 3;
        a->hx = o->x; a->hy = o->y;
        a->aux = o->b; a->aux2 = o->c;
        a->dir = o->b ? DIR_DOWN : DIR_RIGHT;
        if (o->a == 1) { a->tile = SPR_SAW; a->attr = 3; }
        break;
    case OBJ_PICKUP:
        ai = actor_new(ACT_PICKUP, o->a, x + (4 << 4), y + (4 << 4));
        if (ai < 0) return;
        a = &actors[ai];
        a->tile = o->a == 0 ? SPR_HEART : (o->a == 1 ? SPR_AMMO : SPR_BOTTLE);
        a->attr = o->a == 0 ? 5 : 0;
        a->size = 1;
        break;
    default:
        return;
    }
    a->obj = oi;
}

void actors_spawn_map(void) {
    uint8_t i;
    for (i = 0; i < mh.nobjs; i++) {
        obj_t *o = &objs[i];
        if (o->type == OBJ_SIGN || o->type == OBJ_TRIGGER || o->type == OBJ_NOISE) continue;
        if (!cond_ok(o->cond)) continue;
        spawn_obj_actor(i);
    }
}

/* body box of actor for blocking */
uint8_t actor_blocks(int16_t x, int16_t y, uint8_t self) {
    uint8_t i;
    for (i = 0; i < MAX_ACTORS; i++) {
        actor_t *a = &actors[i];
        int16_t ax, ay, w;
        if (i == self) continue;
        if (a->type != ACT_NPC && a->type != ACT_ENEMY && a->type != ACT_BOSS) continue;
        if (a->kind == K_RAT && a->type == ACT_ENEMY) continue;
        ax = a->x >> 4; ay = a->y >> 4;
        w = a->size == 2 ? 28 : 12;
        if (x + 12 > ax + 2 && x + 3 < ax + w + 2 && y + 15 > ay + 8 && y + 9 < ay + (a->size == 2 ? 30 : 15))
            return 1;
    }
    return 0;
}

static uint8_t solid_box(int16_t px, int16_t py) {
    int16_t x0 = px + 3, x1 = px + 12, y0 = py + 9, y1 = py + 15;
    if (x0 < 0 || y0 < 0 || x1 >= (int16_t)mh.w * 16 || y1 >= (int16_t)mh.h * 16) return 1;
    if (mflags_at(x0 >> 4, y0 >> 4) & MF_SOLID) return 1;
    if (mflags_at(x1 >> 4, y0 >> 4) & MF_SOLID) return 1;
    if (mflags_at(x0 >> 4, y1 >> 4) & MF_SOLID) return 1;
    if (mflags_at(x1 >> 4, y1 >> 4) & MF_SOLID) return 1;
    return 0;
}

/* move with collision; returns 1 if moved */
uint8_t actor_step(actor_t *a, uint8_t dir, uint8_t spd, uint8_t walls) {
    int16_t nx = a->x + dxs[dir] * spd, ny = a->y + dys[dir] * spd;
    a->dir = dir;
    if (walls && solid_box(nx >> 4, ny >> 4)) return 0;
    {
        int16_t px = pl_x >> 4, py = pl_y >> 4, ax = nx >> 4, ay = ny >> 4;
        if (a->type != ACT_PROJ && ABS(ax - px) < 11 && ABS(ay - py) < 9) return 0;
    }
    a->x = nx; a->y = ny;
    a->anim++;
    return 1;
}

/* move toward point (pixels), axis-aligned with fallback */
uint8_t actor_toward(actor_t *a, int16_t tx, int16_t ty, uint8_t spd, uint8_t walls) {
    int16_t dx = tx - (a->x >> 4), dy = ty - (a->y >> 4);
    uint8_t d1, d2;
    if (ABS(dx) < 2 && ABS(dy) < 2) return 2;
    if (ABS(dx) > ABS(dy)) {
        d1 = dx < 0 ? DIR_LEFT : DIR_RIGHT;
        d2 = dy < 0 ? DIR_UP : DIR_DOWN;
    } else {
        d1 = dy < 0 ? DIR_UP : DIR_DOWN;
        d2 = dx < 0 ? DIR_LEFT : DIR_RIGHT;
    }
    if (actor_step(a, d1, spd, walls)) return 1;
    if ((d2 >= 2 ? ABS(dx) : ABS(dy)) > 1 && actor_step(a, d2, spd, walls)) { a->dir = d1; return 1; }
    return 0;
}

/* line of sight between pixel points, sampling every 8 px */
uint8_t los(int16_t x0, int16_t y0, int16_t x1, int16_t y1) {
    int16_t dx = x1 - x0, dy = y1 - y0;
    uint8_t i, n = (uint8_t)((ABS(dx) > ABS(dy) ? ABS(dx) : ABS(dy)) >> 3);
    for (i = 1; i < n; i++) {
        int16_t x = x0 + (dx * i) / n, y = y0 + (dy * i) / n;
        if (x < 0 || y < 0) return 0;
        if (mflags_at(x >> 4, y >> 4) & MF_SOLID) {
            if (!(mflags_at(x >> 4, y >> 4) & MF_WATER)) return 0;
        }
    }
    return 1;
}

static uint8_t sees_player(actor_t *a) {
    int16_t ax = (a->x >> 4) + 8, ay = (a->y >> 4) + 8;
    int16_t px = (pl_x >> 4) + 8, py = (pl_y >> 4) + 10;
    int16_t dx = px - ax, dy = py - ay, fwd, side;
    uint8_t range = 72;
    if (mflags_at(px >> 4, (py + 2) >> 4) & MF_DARK) range = 28;
    if (mh.flags & MAPF_DARK) range = range > 40 ? 40 : range;
    if (ABS(dx) < 14 && ABS(dy) < 14) return 1;     /* too close: felt */
    switch (a->dir) {
    case DIR_DOWN: fwd = dy; side = dx; break;
    case DIR_UP: fwd = -dy; side = dx; break;
    case DIR_LEFT: fwd = -dx; side = dy; break;
    default: fwd = dx; side = dy; break;
    }
    if (fwd <= 0 || fwd > range) return 0;
    if (ABS(side) > (fwd >> 1) + 10) return 0;
    return los(ax, ay, px, py);
}

static void enemy_alert(actor_t *a) {
    a->state = ST_ALERT;
    a->timer = 24;
    a->icon = 1;
    sfx_play(14);
    if (mh.flags & MAPF_RESTRICTED) alert_add(8);
    if (music_cur != MUS_PURSUIT && !(mh.flags & MAPF_OUTDOOR) && mh.music != 0xFF) {
        /* keep area music; pursuit theme reserved for scripted chases */
    }
}

static void spawn_fx(int16_t x, int16_t y, uint8_t tile, uint8_t t) {
    int8_t i = actor_new(ACT_FX, 0, x, y);
    if (i >= 0) {
        actors[i].tile = tile;
        actors[i].attr = 5;
        actors[i].size = 3;
        actors[i].timer = t;
    }
}

static void enemy_kill(actor_t *a) {
    uint8_t r = rand8();
    int16_t x = a->x, y = a->y;
    uint8_t oi = a->obj;
    sfx_play(20);
    gs.kills++;
    if (a->kind == K_POLICE) {
        gs.cops_killed++;
        flag_set(F_KILLED_COP);
        alert_add(35);
    }
    a->type = ACT_NONE;
    spawn_fx(x, y, SPR_SPARK, 12);
    if (r < 70) {
        int8_t i = actor_new(ACT_PICKUP, (r < 40 || !item_has(IT_PISTOL)) ? K_HEART : K_AMMO, x + (4 << 4), y + (4 << 4));
        if (i >= 0) {
            actors[i].tile = actors[i].kind == K_HEART ? SPR_HEART : SPR_AMMO;
            actors[i].attr = actors[i].kind == K_HEART ? 5 : 0;
            actors[i].size = 1;
            actors[i].timer = 255;
        }
    }
    if (oi != 0xFF && objs[oi].script != 0xFFFF) script_queue(objs[oi].script);
}

void actor_damage(actor_t *a, uint8_t dmg, uint8_t fromdir, uint8_t heavy) {
    if (a->hurt) return;
    if (a->type == ACT_BOSS) {
        boss_hit_hook(a, dmg, fromdir, heavy);
        return;
    }
    /* takedown: unaware enemy struck from behind dies instantly */
    if ((a->state == ST_PATROL || a->state == ST_SEARCH || a->state == ST_RETURN) && fromdir == a->dir && a->kind != K_WRAITH) {
        dlg_is_open = 0;
        flash_white(1);
        enemy_kill(a);
        return;
    }
    if (a->state == ST_STUN) dmg *= 2;
    a->hp -= dmg;
    a->hurt = 16;
    sfx_play(heavy ? 17 : 4);
    if (fromdir < 4) {
        a->kx = dxs[fromdir] * (heavy ? 4 : 2);
        a->ky = dys[fromdir] * (heavy ? 4 : 2);
    }
    if (a->hp <= 0) { enemy_kill(a); return; }
    if (a->state != ST_STUN) { a->state = ST_CHASE; a->timer = 0; a->icon = 0; }
}

void actors_hit_box(uint8_t x0, uint8_t y0, uint8_t x1, uint8_t y1, uint8_t dmg, uint8_t heavy) {
    uint8_t i;
    for (i = 0; i < MAX_ACTORS; i++) {
        actor_t *a = &actors[i];
        int16_t ax, ay, w;
        if (a->type != ACT_ENEMY && a->type != ACT_BOSS) continue;
        ax = a->x >> 4; ay = a->y >> 4;
        w = a->size == 2 ? 30 : 14;
        if (x1 >= ax + 1 && x0 <= ax + w && y1 >= ay + 1 && y0 <= ay + w + 1)
            actor_damage(a, dmg, pl_dir, heavy);
    }
}

void actors_noise(uint8_t x, uint8_t y, uint8_t radius) {
    uint8_t i;
    for (i = 0; i < MAX_ACTORS; i++) {
        actor_t *a = &actors[i];
        int16_t dx, dy;
        if (a->type != ACT_ENEMY || a->state == ST_CHASE || a->state == ST_STUN || a->state == ST_ATTACK) continue;
        dx = ((a->x >> 4) + 8) - x; dy = ((a->y >> 4) + 8) - y;
        if (ABS(dx) + ABS(dy) < radius) {
            a->state = ST_SEARCH;
            a->timer = 200;
            a->px0 = x; a->px1 = y;  /* search target (pixels) */
            a->icon = 2;
        }
    }
}

void actors_stun_near(uint8_t x, uint8_t y, uint8_t radius, uint8_t dmg) {
    uint8_t i;
    for (i = 0; i < MAX_ACTORS; i++) {
        actor_t *a = &actors[i];
        int16_t dx, dy;
        if (a->type != ACT_ENEMY && a->type != ACT_BOSS) continue;
        dx = ((a->x >> 4) + 8) - x; dy = ((a->y >> 4) + 8) - y;
        if (ABS(dx) + ABS(dy) < radius) {
            if (a->type == ACT_BOSS) { boss_stun_hook(a); continue; }
            a->state = ST_STUN;
            a->timer = 180;
            a->icon = 3;
            if (dmg) { a->hp -= dmg; if (a->hp <= 0) enemy_kill(a); }
        }
    }
}

static uint8_t touch_player(actor_t *a, uint8_t r) {
    int16_t dx = ((a->x >> 4) + 4) - ((pl_x >> 4) + 8);
    int16_t dy = ((a->y >> 4) + 8) - ((pl_y >> 4) + 10);
    if (a->size != 1) { dx -= 4; }
    return ABS(dx) < r && ABS(dy) < r;
}

static uint8_t dir_to_player(actor_t *a) {
    int16_t dx = (pl_x - a->x) >> 4, dy = (pl_y - a->y) >> 4;
    if (ABS(dx) > ABS(dy)) return dx < 0 ? DIR_LEFT : DIR_RIGHT;
    return dy < 0 ? DIR_UP : DIR_DOWN;
}

void enemy_shoot(actor_t *a, uint8_t dir) {
    int8_t i = actor_new(ACT_PROJ, 0, a->x + (4 << 4), a->y + (2 << 4));
    if (i >= 0) {
        actors[i].dir = dir;
        actors[i].tile = SPR_BULLET;
        actors[i].attr = 5;
        actors[i].size = 1;
        actors[i].timer = 70;
    }
    sfx_play(5);
}

static void enemy_update(actor_t *a) {
    int16_t ax = a->x >> 4, ay = a->y >> 4, px = pl_x >> 4, py = pl_y >> 4;
    int16_t dx = px - ax, dy = py - ay;
    uint8_t k = a->kind, mode = a->aux >> 4, rng = a->aux & 15;
    uint8_t ranged = (k == K_GUNMAN || k == K_POLICE);

    if (a->hurt) a->hurt--;
    if (a->kx || a->ky) {
        int16_t nx = a->x + a->kx * 16, ny = a->y + a->ky * 16;
        if (!solid_box(nx >> 4, ny >> 4)) { a->x = nx; a->y = ny; }
        if (a->kx) a->kx += a->kx > 0 ? -1 : 1;
        if (a->ky) a->ky += a->ky > 0 ? -1 : 1;
        return;
    }
    if (k == K_RAT) {
        a->tile = a->dir >= 2 ? SPR_RAT_SIDE : SPR_RAT_DOWN;
    }
    switch (a->state) {
    case ST_PATROL:
        a->icon = 0;
        if (k == K_WRAITH) {
            if (ABS(dx) + ABS(dy) < 90) { a->state = ST_CHASE; sfx_play(10); }
            break;
        }
        if (k == K_RAT) {
            if (ABS(dx) + ABS(dy) < 48) { a->state = ST_CHASE; break; }
            if (!a->timer) { a->timer = 30 + (rand8() & 63); a->dir = rand8() & 3; }
            a->timer--;
            actor_step(a, a->dir, kind_patrol_spd[k], 1);
            break;
        }
        if (mode == 1 || mode == 2) {
            /* pace between home and home+range */
            uint8_t tx = ((ax + 8) >> 4), ty = ((ay + 8) >> 4);
            uint8_t d = a->dir;
            if (mode == 1) {
                if (d != DIR_LEFT && d != DIR_RIGHT) d = DIR_RIGHT;
                if (d == DIR_RIGHT && tx >= a->hx + rng) d = DIR_LEFT;
                if (d == DIR_LEFT && tx <= a->hx && (ax & 15) == 0) d = DIR_RIGHT;
            } else {
                if (d != DIR_UP && d != DIR_DOWN) d = DIR_DOWN;
                if (d == DIR_DOWN && ty >= a->hy + rng) d = DIR_UP;
                if (d == DIR_UP && ty <= a->hy && ((ay + 4) & 15) == 0) d = DIR_DOWN;
            }
            if (!actor_step(a, d, kind_patrol_spd[k], 1)) {
                if (++a->timer > 30) { a->timer = 0; a->dir = d ^ 1; if (mode == 1) a->dir = d == DIR_LEFT ? DIR_RIGHT : DIR_LEFT; }
            }
        } else if (mode == 4 || mode == 0) {
            /* guard: turn around periodically */
            if (++a->timer > (mode == 4 ? 90 : 160)) {
                a->timer = 0;
                if (mode == 4) a->dir = (a->dir + 1 + (rand8() & 1)) & 3;
            }
        } else {
            if (!a->timer) { a->timer = 40 + (rand8() & 63); a->dir = rand8() & 3; }
            a->timer--;
            if (a->timer > 20) actor_step(a, a->dir, kind_patrol_spd[k], 1);
        }
        if ((frame_ctr & 3) == (a->hx & 3) && sees_player(a)) enemy_alert(a);
        break;
    case ST_ALERT:
        a->dir = dir_to_player(a);
        if (--a->timer == 0) { a->state = ST_CHASE; a->timer = 0; a->icon = 0; }
        break;
    case ST_CHASE:
        a->icon = 0;
        if ((frame_ctr & 7) == 0) {
            if (k == K_WRAITH || sees_player(a) || (ABS(dx) + ABS(dy) < 40)) {
                a->timer = 0;
                a->px0 = (uint8_t)(px + 8); a->px1 = (uint8_t)(py + 8);
            } else if (++a->timer > 14) {
                a->state = ST_SEARCH; a->timer = 160; a->icon = 2;
                break;
            }
        }
        if (ranged) {
            uint8_t aligned = ABS(dx) < 6 || ABS(dy) < 6;
            if (a->aux2) a->aux2--;
            if (aligned && !a->aux2 && ABS(dx) + ABS(dy) < 110 && los(ax + 8, ay + 8, px + 8, py + 10)) {
                a->dir = dir_to_player(a);
                a->state = ST_ATTACK;
                a->timer = 20;
                break;
            }
            if (ABS(dx) + ABS(dy) > 40) actor_toward(a, px, py, kind_chase_spd[k], 1);
            else if (ABS(dx) + ABS(dy) < 28) {
                uint8_t d = dir_to_player(a);
                actor_step(a, d < 2 ? d ^ 1 : (d == DIR_LEFT ? DIR_RIGHT : DIR_LEFT), kind_chase_spd[k], 1);
                a->dir = d;
            } else {
                /* strafe to line up */
                if (ABS(dx) < ABS(dy)) actor_step(a, dx < 0 ? DIR_LEFT : DIR_RIGHT, kind_chase_spd[k], 1);
                else actor_step(a, dy < 0 ? DIR_UP : DIR_DOWN, kind_chase_spd[k], 1);
                a->dir = dir_to_player(a);
            }
        } else {
            if (ABS(dx) < 16 && ABS(dy) < 14) {
                a->dir = dir_to_player(a);
                a->state = ST_ATTACK;
                a->timer = k == K_RUNNER ? 10 : (k == K_RAT ? 8 : 18);
                break;
            }
            if (!actor_toward(a, px, py, kind_chase_spd[k], k != K_WRAITH)) {
                if (k == K_RUNNER) actor_step(a, rand8() & 3, kind_chase_spd[k], 1);
            }
        }
        break;
    case ST_ATTACK:
        if (--a->timer == 0) {
            if (ranged) {
                enemy_shoot(a, a->dir);
                a->aux2 = k == K_POLICE ? 70 : 55;
                a->state = ST_CHASE;
            } else {
                if (touch_player(a, 16)) player_damage(k == K_RAT ? 1 : 2, a->dir);
                a->state = ST_COOL;
                a->timer = k == K_RUNNER ? 36 : 24;
                if (k == K_RUNNER) {
                    /* evasive: dart away after striking */
                    a->kx = -dxs[a->dir] * 3;
                    a->ky = -dys[a->dir] * 3;
                }
            }
        } else if (a->timer & 2) {
            /* wind-up shimmy */
            a->anim += 4;
        }
        break;
    case ST_COOL:
        if (--a->timer == 0) a->state = ST_CHASE;
        break;
    case ST_SEARCH:
        if (actor_toward(a, (int16_t)a->px0 - 8, (int16_t)a->px1 - 8, kind_patrol_spd[k] + 4, 1) != 1) {
            if ((a->timer & 31) == 0) a->dir = (a->dir + 1) & 3;
        }
        if ((frame_ctr & 3) == 1 && sees_player(a)) { enemy_alert(a); break; }
        if (--a->timer == 0) { a->state = ST_RETURN; a->icon = 0; }
        break;
    case ST_RETURN: {
        uint8_t r = actor_toward(a, (int16_t)a->hx * 16, (int16_t)a->hy * 16 - 4, kind_patrol_spd[k], 1);
        if (r == 2 || (r == 0 && ++a->timer > 60)) { a->state = ST_PATROL; a->timer = 0; }
        if ((frame_ctr & 3) == 2 && sees_player(a)) enemy_alert(a);
        break;
    }
    case ST_STUN:
        if (--a->timer == 0) { a->state = ST_CHASE; a->icon = 0; }
        break;
    }
}

static void npc_update(actor_t *a) {
    uint8_t mode = a->kind;
    if (mode == 1) {   /* wander near home */
        if (!a->timer) { a->timer = 60 + (rand8() & 127); a->aux = rand8() & 3; }
        a->timer--;
        if (a->timer < 16) {
            int16_t ox = a->x, oy = a->y;
            int16_t hx = (int16_t)objs[a->obj].x * 16, hy = (int16_t)objs[a->obj].y * 16;
            if (actor_step(a, a->aux, 8, 1)) {
                if (ABS((a->x >> 4) - hx) > 24 || ABS((a->y >> 4) - hy) > 24) { a->x = ox; a->y = oy; }
            }
        } else a->anim = 0;
    } else if (mode == 2 || mode == 3) {
        uint8_t d = a->dir;
        if (mode == 2 && d < 2) d = DIR_RIGHT;
        if (mode == 3 && d >= 2) d = DIR_DOWN;
        if (!actor_step(a, d, 6, 1) || ++a->timer > 64) {
            a->timer = 0;
            a->dir = mode == 2 ? (d == DIR_LEFT ? DIR_RIGHT : DIR_LEFT) : d ^ 1;
        }
    }
}

static void proj_update(actor_t *a, uint8_t player_owned) {
    uint8_t i, spd = player_owned ? 64 : 36;
    a->x += dxs[a->dir] * spd;
    a->y += dys[a->dir] * spd;
    if (--a->timer == 0) { a->type = ACT_NONE; return; }
    {
        int16_t x = (a->x >> 4) + 4, y = (a->y >> 4) + 8;
        if (x < 0 || y < 0 || x >= (int16_t)mh.w * 16 || y >= (int16_t)mh.h * 16) { a->type = ACT_NONE; return; }
        if ((mflags_at(x >> 4, y >> 4) & (MF_SOLID | MF_WATER)) == MF_SOLID) { a->type = ACT_NONE; return; }
        if (player_owned) {
            for (i = 0; i < MAX_ACTORS; i++) {
                actor_t *e = &actors[i];
                int16_t ex, ey, w;
                if (e->type != ACT_ENEMY && e->type != ACT_BOSS) continue;
                ex = e->x >> 4; ey = e->y >> 4;
                w = e->size == 2 ? 30 : 15;
                if (x >= ex && x <= ex + w && y >= ey && y <= ey + w + 1) {
                    actor_damage(e, 3, a->dir, 1);
                    a->type = ACT_NONE;
                    return;
                }
            }
        } else if (touch_player(a, 8)) {
            player_damage(2, a->dir);
            a->type = ACT_NONE;
        }
    }
}

void actors_update(void) {
    uint8_t i;
    for (i = 0; i < MAX_ACTORS; i++) {
        actor_t *a = &actors[i];
        switch (a->type) {
        case ACT_NPC: npc_update(a); break;
        case ACT_ENEMY:
            enemy_update(a);
            if (a->type && a->kind == K_WRAITH && touch_player(a, 10)) player_damage(2, a->dir);
            break;
        case ACT_BOSS: boss_update(a); break;
        case ACT_PROJ: proj_update(a, 0); break;
        case ACT_PPROJ: proj_update(a, 1); break;
        case ACT_FX:
            if (--a->timer == 0) a->type = ACT_NONE;
            break;
        case ACT_BOTTLE: {
            uint8_t smash = 0;
            int16_t x, y;
            a->x += dxs[a->dir] * 40;
            a->y += dys[a->dir] * 40;
            x = (a->x >> 4) + 4; y = (a->y >> 4) + 8;
            if (x < 0 || y < 0 || (mflags_at(x >> 4, y >> 4) & MF_SOLID)) smash = 1;
            if (--a->timer == 0) smash = 1;
            if (smash) {
                if (x < 0) x = 0;
                if (y < 0) y = 0;
                sfx_play(19);
                actors_noise((uint8_t)x, (uint8_t)y, 96);
                a->type = ACT_FX; a->tile = SPR_SPARK; a->size = 3; a->timer = 10;
                a->x -= 4 << 4;
            }
            break;
        }
        case ACT_PICKUP:
            if (touch_player(a, 10)) {
                if (a->obj != 0xFF) {
                    script_run(objs[a->obj].script);
                } else if (a->kind == K_HEART) {
                    gs.hp = gs.hp + 2 > gs.maxhp ? gs.maxhp : gs.hp + 2;
                    sfx_play(9);
                } else {
                    gs.ammo = gs.ammo + 2 > 24 ? 24 : gs.ammo + 2;
                    sfx_play(9);
                }
                hud_dirty = 1;
                a->type = ACT_NONE;
            } else if (a->obj == 0xFF && a->timer && --a->timer == 0) {
                a->type = ACT_NONE;
            }
            break;
        case ACT_HAZARD: {
            /* moving machinery along an axis between home and home+range tiles */
            int16_t ax = a->x >> 4, ay = a->y >> 4;
            int16_t lo = a->aux ? (int16_t)a->hy * 16 : (int16_t)a->hx * 16;
            int16_t hi = lo + (int16_t)a->aux2 * 16;
            int16_t pos = a->aux ? ay - 4 : ax;
            if (a->dir == DIR_RIGHT || a->dir == DIR_DOWN) { if (pos >= hi) a->dir = a->aux ? DIR_UP : DIR_LEFT; }
            else if (pos <= lo) a->dir = a->aux ? DIR_DOWN : DIR_RIGHT;
            a->x += dxs[a->dir] * 20;
            a->y += dys[a->dir] * 20;
            if (touch_player(a, 11)) player_damage(2, a->dir);
            break;
        }
        }
    }
}
