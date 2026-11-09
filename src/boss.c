#pragma bank 255
/* boss.c - the seven targets. Each boss has a distinct pattern:
 *  0 EDDIE  shotgun spread, reload windows, crates give cover
 *  1 HECTOR huge butcher: aligned charges, stuns himself on walls/machinery
 *  2 NOLAN  flees; must be cornered, then fights with a knife
 *  3 DACRE  pistol duellist, calls a crooked patrolman at half health
 *  4 MOTT   vanishes into the water and ambushes
 *  5 CREWE  retreats, fires, triggers the alarm (summons guards)
 *  6 RUSK   occult bolts, summons wraiths; second phase teleports
 */
#include "hm.h"
#include "gen_dirs.h"

uint8_t boss_hp_show;

void spawn_obj_actor(uint8_t oi) BANKED;

static const uint8_t boss_maxhp[7] = {8, 14, 6, 10, 10, 8, 16};
static const uint8_t boss_sheet[7] = {SHEET_EDDIE, SHEET_BIG_HECTOR, SHEET_NOLAN, SHEET_DACRE,
                                      SHEET_MOTT, SHEET_CREWE, SHEET_RUSK};
static const int8_t dxs[4] = {0, 0, -1, 1};
static const int8_t dys[4] = {1, -1, 0, 0};

enum { B_IDLE, B_MOVE, B_AIM, B_FIRE, B_RELOAD, B_CHARGE, B_STUN, B_HIDE, B_AMBUSH, B_FLEE, B_CORNER, B_SWIPE };

void boss_init(actor_t *a) BANKED {
    uint8_t sh = boss_sheet[a->kind];
    uint8_t sl = sheet_load(sh);
    a->tile = slot_tile(sl);
    a->attr = slot_attr(sl, sheet_dir[sh].pal);
    a->size = sheet_dir[sh].big ? 2 : 0;
    a->hp = boss_maxhp[a->kind];
    a->state = B_IDLE;
    a->timer = 60;
    a->dir = DIR_DOWN;
    boss_hp_show = a->hp;
    hud_dirty = 1;
}

static uint8_t dir_to(actor_t *a, int16_t tx, int16_t ty) {
    int16_t dx = tx - (a->x >> 4), dy = ty - (a->y >> 4);
    if (ABS(dx) > ABS(dy)) return dx < 0 ? DIR_LEFT : DIR_RIGHT;
    return dy < 0 ? DIR_UP : DIR_DOWN;
}

static void shoot_at(actor_t *a, uint8_t dir, int8_t off) {
    int8_t i = actor_new(ACT_PROJ, 0, a->x + ((4 + (dir < 2 ? off : 0)) << 4),
                         a->y + ((2 + (dir >= 2 ? off : 0)) << 4));
    if (i >= 0) {
        actors[i].dir = dir;
        actors[i].tile = SPR_BULLET;
        actors[i].attr = 5;
        actors[i].size = 1;
        actors[i].timer = 70;
    }
}

static uint8_t count_kind(uint8_t type, uint8_t kind) {
    uint8_t i, n = 0;
    for (i = 0; i < MAX_ACTORS; i++) if (actors[i].type == type && actors[i].kind == kind) n++;
    return n;
}

static void summon(uint8_t kind, int16_t x, int16_t y) {
    static const uint8_t sheets[5] = {SHEET_THUG, SHEET_RUNNER, SHEET_GUNMAN, SHEET_POLICE, SHEET_WRAITH};
    int8_t i = actor_new(ACT_ENEMY, kind, x, y);
    if (i >= 0) {
        actor_t *e = &actors[i];
        uint8_t sl = sheet_load(sheets[kind]);
        e->tile = slot_tile(sl);
        e->attr = slot_attr(sl, sheet_dir[sheets[kind]].pal);
        e->hp = kind == 4 ? 3 : 2;
        e->state = 2;  /* chase */
        e->hx = (uint8_t)((x >> 4) >> 4);
        e->hy = (uint8_t)((y >> 4) >> 4);
        sfx_play(kind == 4 ? 10 : 14);
    }
}

static void boss_die(actor_t *a) {
    uint8_t oi = a->obj;
    a->type = ACT_NONE;
    boss_hp_show = 0;
    hud_dirty = 1;
    sfx_play(20);
    shake_t = 20;
    flash_white(3);
    /* clear remaining hostiles */
    {
        uint8_t i;
        for (i = 0; i < MAX_ACTORS; i++)
            if (actors[i].type == ACT_PROJ || actors[i].type == ACT_ENEMY) actors[i].type = ACT_NONE;
    }
    if (oi != 0xFF) script_queue(objs[oi].script);
}

void boss_hit_hook(actor_t *a, uint8_t dmg, uint8_t fromdir, uint8_t heavy) BANKED {
    if (a->state == B_HIDE) return;
    /* Hector shrugs off light blows unless stunned */
    if (a->kind == 1 && a->state != B_STUN && !heavy) { sfx_play(15); a->hurt = 8; return; }
    if (a->kind == 0 && a->state == B_RELOAD) dmg++;
    if (a->kind == 1 && a->state == B_STUN) dmg++;
    a->hp -= dmg;
    a->hurt = 30;
    sfx_play(heavy ? 17 : 4);
    if (fromdir < 4 && a->size != 2) {
        a->kx = dxs[fromdir] * 2;
        a->ky = dys[fromdir] * 2;
    }
    boss_hp_show = a->hp > 0 ? a->hp : 0;
    hud_dirty = 1;
    if (a->hp <= 0) boss_die(a);
}

void boss_stun_hook(actor_t *a) BANKED {
    if (a->kind == 6 || a->state == B_HIDE) return;   /* Rusk is immune to the shadow */
    a->state = B_STUN;
    a->timer = 120;
    a->icon = 3;
}

static uint8_t solid_ahead(actor_t *a, uint8_t dir, uint8_t dist) {
    int16_t w = a->size == 2 ? 32 : 16;
    int16_t cx = (a->x >> 4) + w / 2 + dxs[dir] * (w / 2 + dist);
    int16_t cy = (a->y >> 4) + w / 2 + 4 + dys[dir] * (w / 2 + dist - 4);
    if (cx < 0 || cy < 0) return 1;
    return mflags_at(cx >> 4, cy >> 4) & MF_SOLID;
}

static void contact_damage(actor_t *a, uint8_t dmg) {
    int16_t w = a->size == 2 ? 32 : 16;
    int16_t dx = ((a->x >> 4) + w / 2) - ((pl_x >> 4) + 8);
    int16_t dy = ((a->y >> 4) + w / 2) - ((pl_y >> 4) + 10);
    if (ABS(dx) < w / 2 + 6 && ABS(dy) < w / 2 + 6) player_damage(dmg, a->dir);
}

void boss_update(actor_t *a) BANKED {
    int16_t px = pl_x >> 4, py = pl_y >> 4, ax = a->x >> 4, ay = a->y >> 4;
    int16_t dx = px - ax, dy = py - ay;
    uint8_t pd = dir_to(a, px, py);

    if (a->hurt) a->hurt--;
    if (a->kx || a->ky) {
        actor_step(a, a->kx ? (a->kx < 0 ? DIR_LEFT : DIR_RIGHT) : (a->ky < 0 ? DIR_UP : DIR_DOWN), 24, 1);
        if (a->kx) a->kx += a->kx > 0 ? -1 : 1;
        if (a->ky) a->ky += a->ky > 0 ? -1 : 1;
        a->dir = pd;
        return;
    }
    if (a->state == B_STUN) {
        if (--a->timer == 0) { a->state = B_MOVE; a->timer = 60; a->icon = 0; }
        return;
    }

    switch (a->kind) {
    case 0: /* EDDIE VOSS - shotgun */
        switch (a->state) {
        case B_IDLE: case B_MOVE:
            a->icon = 0;
            if (ABS(dx) + ABS(dy) > 36) actor_toward(a, px, py, 10, 1);
            else a->dir = pd;
            if (--a->timer == 0) { a->state = B_AIM; a->timer = 26; a->dir = pd; a->icon = 1; }
            break;
        case B_AIM:
            if (--a->timer == 0) {
                a->icon = 0;
                shoot_at(a, a->dir, 0);
                shoot_at(a, a->dir, -10);
                shoot_at(a, a->dir, 10);
                sfx_play(5); shake_t = 6;
                a->state = B_RELOAD; a->timer = 70;
            }
            break;
        case B_RELOAD:
            a->icon = 2;
            if (--a->timer == 0) { a->state = B_MOVE; a->timer = 70 + (rand8() & 31); a->icon = 0; }
            break;
        }
        break;

    case 1: /* HECTOR VALE - charging butcher (32x32) */
        switch (a->state) {
        case B_IDLE: case B_MOVE:
            a->icon = 0;
            actor_toward(a, px - 8, py - 8, 8, 1);
            contact_damage(a, 3);
            if (a->timer) a->timer--;
            if (!a->timer && (ABS(dx + 8) < 12 || ABS(dy + 8) < 12)) {
                a->state = B_AIM; a->timer = 30; a->dir = dir_to(a, px - 8, py - 8); a->icon = 1;
                sfx_play(14);
            }
            break;
        case B_AIM:
            if (--a->timer == 0) { a->state = B_CHARGE; a->timer = 90; a->icon = 0; }
            break;
        case B_CHARGE:
            if (solid_ahead(a, a->dir, 2) || !actor_step(a, a->dir, 44, 1)) {
                if (solid_ahead(a, a->dir, 3)) {
                    /* slammed into the machinery: stunned */
                    a->state = B_STUN; a->timer = 110; a->icon = 3;
                    shake_t = 16; sfx_play(17);
                } else {
                    a->state = B_MOVE; a->timer = 50;
                }
                break;
            }
            contact_damage(a, 3);
            if (--a->timer == 0) { a->state = B_MOVE; a->timer = 60; }
            break;
        }
        break;

    case 2: /* NOLAN PIKE - runs */
        if (a->state == B_IDLE) { a->state = B_FLEE; a->timer = 0; }
        if (a->state == B_FLEE) {
            uint8_t best = 0xFF, d;
            int16_t bestd = -1;
            if (ABS(dx) + ABS(dy) > 90) { a->anim = 0; break; }   /* hides, catches breath */
            for (d = 0; d < 4; d++) {
                int16_t nx = ax + dxs[d] * 8, ny = ay + dys[d] * 8, dd;
                if (solid_ahead(a, d, 2)) continue;
                dd = ABS(px - nx) + ABS(py - ny);
                if (dd > bestd) { bestd = dd; best = d; }
            }
            if (best == 0xFF || !actor_step(a, best, 17, 1) || bestd < ABS(dx) + ABS(dy)) {
                if (++a->timer > 40 && ABS(dx) + ABS(dy) < 40) {
                    a->state = B_CORNER; a->timer = 0; a->icon = 1;
                    sfx_play(14);
                }
            } else a->timer = 0;
        } else if (a->state == B_CORNER) {
            a->icon = 0;
            actor_toward(a, px, py, 14, 1);
            if (ABS(dx) < 16 && ABS(dy) < 14) {
                if (++a->timer > 14) { contact_damage(a, 2); a->timer = 0; }
            }
            if (rand8() < 2 && a->hp > 2) { a->state = B_FLEE; a->timer = 0; }
        }
        break;

    case 3: /* SGT. DACRE - pistol duel */
        if (a->hp <= 5 && !a->aux) {
            a->aux = 1;
            summon(3, a->x, a->y + (24 << 4));
            dlg_is_open = 0;
        }
        if (a->aux2) a->aux2--;
        if ((ABS(dx) < 8 || ABS(dy) < 8) && !a->aux2 && los(ax + 8, ay + 8, px + 8, py + 10)) {
            a->dir = pd;
            shoot_at(a, pd, 0);
            sfx_play(5);
            a->aux2 = a->hp <= 5 ? 34 : 50;
        } else if (ABS(dx) + ABS(dy) < 40) {
            actor_step(a, pd < 2 ? pd ^ 1 : (pd == DIR_LEFT ? DIR_RIGHT : DIR_LEFT), 16, 1);
            a->dir = pd;
        } else {
            if (ABS(dx) < ABS(dy)) actor_step(a, dx < 0 ? DIR_LEFT : DIR_RIGHT, 14, 1);
            else actor_step(a, dy < 0 ? DIR_UP : DIR_DOWN, 14, 1);
            a->dir = pd;
        }
        break;

    case 4: /* ALEC MOTT - ambusher */
        switch (a->state) {
        case B_IDLE: case B_MOVE:
            a->icon = 0;
            actor_toward(a, px, py, 13, 1);
            if (ABS(dx) < 16 && ABS(dy) < 14 && (frame_ctr & 15) == 0) contact_damage(a, 2);
            if (++a->timer > 200) {
                a->state = B_HIDE; a->timer = 80;
                a->hurt = 0;
                sfx_play(19);
            }
            break;
        case B_HIDE:
            a->hurt = 2;   /* invisible (render skips when hurt&2) */
            if (--a->timer == 0) {
                /* resurface beside the player */
                int16_t nx = px + ((rand8() & 1) ? 28 : -28), ny = py;
                if (nx < 8) nx = px + 28;
                if (nx > (int16_t)mh.w * 16 - 24) nx = px - 28;
                a->x = nx << 4; a->y = ny << 4;
                a->hurt = 0;
                a->state = B_AMBUSH; a->timer = 24; a->icon = 1; a->dir = dir_to(a, px, py);
                sfx_play(14);
            }
            break;
        case B_AMBUSH:
            if (--a->timer == 0) {
                a->icon = 0;
                contact_damage(a, 3);
                a->state = B_MOVE; a->timer = 0;
            }
            break;
        }
        break;

    case 5: /* SILAS CREWE - retreats, fires, summons guards */
        if (a->aux2) a->aux2--;
        if (!a->aux && a->hp <= 6) { a->aux = 1; summon(2, 2 << 8, 3 << 8); }
        if (a->aux == 1 && a->hp <= 3) { a->aux = 2; summon(0, 10 << 8, 3 << 8); }
        if (ABS(dx) + ABS(dy) < 48) {
            uint8_t d, moved = 0;
            for (d = 0; d < 4 && !moved; d++) {
                uint8_t dd = (pd < 2 ? pd ^ 1 : (pd == DIR_LEFT ? DIR_RIGHT : DIR_LEFT));
                moved = actor_step(a, d == 0 ? dd : d, 15, 1);
            }
            a->dir = pd;
        }
        if ((ABS(dx) < 8 || ABS(dy) < 8) && !a->aux2) {
            a->dir = pd;
            shoot_at(a, pd, 0);
            sfx_play(5);
            a->aux2 = 70;
        }
        break;

    case 6: /* VICTOR RUSK - occult */
        if (a->timer) a->timer--;
        if (!a->timer) {
            if (a->hp > 8) {
                /* phase 1: bolts in four directions, summon wraiths */
                uint8_t d;
                for (d = 0; d < 4; d++) shoot_at(a, d, 0);
                sfx_play(10);
                if (count_kind(ACT_ENEMY, 4) < 2 && (rand8() & 1)) summon(4, a->x + (((rand8() & 1) ? 40 : -40) << 4), a->y);
                a->timer = 90;
            } else {
                /* phase 2: blink beside the player, then fire */
                int16_t nx = px + ((rand8() & 1) ? 36 : -36), ny = py + ((rand8() & 1) ? 20 : -20);
                if (nx < 16) nx = 16;
                if (ny < 16) ny = 16;
                if (nx > (int16_t)mh.w * 16 - 32) nx = (int16_t)mh.w * 16 - 32;
                if (ny > (int16_t)mh.h * 16 - 40) ny = (int16_t)mh.h * 16 - 40;
                if (!(mflags_at((nx + 8) >> 4, (ny + 12) >> 4) & MF_SOLID)) {
                    a->x = nx << 4; a->y = ny << 4;
                    flash_red(2);
                }
                a->dir = dir_to(a, px, py);
                shoot_at(a, a->dir, 0);
                shoot_at(a, a->dir, -10);
                shoot_at(a, a->dir, 10);
                sfx_play(10);
                a->timer = 70;
            }
        }
        a->dir = pd;
        break;
    }
}
