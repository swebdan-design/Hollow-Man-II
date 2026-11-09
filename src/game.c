#pragma bank 255
/* game.c - main gameplay loop, map transitions, HUD, death/retry, chapter cards, illustrations */
#include <string.h>
#include "hm.h"
#include "gen_dirs.h"

uint8_t game_state;
uint8_t hud_dirty;
uint8_t pending_warp, pw_map, pw_x, pw_y, pw_dir;
uint8_t image_mode;
static uint8_t last_tx = 0xFF, last_ty = 0xFF;
static uint8_t trig_latch = 0xFF;
static uint16_t possess_t;

extern uint8_t slot_sheet[NUM_SLOTS];

/* ------------------------------------------------------------------ HUD */
static const char *const weapon_names[2] = {"PIPE", "AXE "};
static const char *const tool_names[NUM_TOOLS] = {"---", "GUN", "BTL", "SHD", "BND"};

void hud_draw(void) BANKED {
    uint8_t i, h, ot = txt_target, n = 0;
    if (dlg_is_open || image_mode) return;
    hud_dirty = 0;
    txt_target = TXT_WIN;
    h = gs.hp;
    for (i = 0; i < 7; i++) {
        uint8_t t;
        if (i * 2 >= gs.maxhp) t = 0;
        else if (h >= i * 2 + 2) t = UI_HEART;
        else if (h == i * 2 + 1) t = UI_HEART_H;
        else t = UI_HEART_E;
        put_tile(i, 0, t);
    }
    put_tile(7, 0, 0);
    print_at(8, 0, weapon_names[gs.weapon & 1]);
    put_tile(12, 0, 0);
    if (lockdown_timer_on) {
        uint16_t s = lockdown_frames / 60;
        print_at(13, 0, "T");
        print_num(14, 0, s, 3);
    } else {
        print_at(13, 0, tool_names[gs.tool]);
        switch (gs.tool) {
        case TOOL_PISTOL: n = gs.ammo; break;
        case TOOL_BOTTLE: n = gs.bottles; break;
        case TOOL_BANDAGE: n = gs.bandages; break;
        case TOOL_SHADOW: n = gs.influence; break;
        }
        if (gs.tool == TOOL_NONE) print_at(16, 0, "  ");
        else if (gs.tool == TOOL_SHADOW) print_num(16, 0, n > 99 ? 99 : n, 2);
        else print_num(16, 0, n, 2);
    }
    put_tile(18, 0, UI_EYE0 + infl_stage());
    i = alert_level();
    put_tile(19, 0, i ? UI_BADGE : UI_BADGE_OFF);
    txt_target = ot;
}

void hud_show(void) BANKED {
    uint8_t ot = txt_target;
    txt_target = TXT_WIN;
    attr_area(0, 0, 20, 6, PAL_HUD | 0x80);
    fill_area(0, 1, 20, 5, 0);
    txt_target = ot;
    move_win(7, 136);
    SHOW_WIN;
    hud_draw();
}

/* ------------------------------------------------------------------ transitions */
void restore_map_view(void) BANKED {
    DISPLAY_OFF;
    image_mode = 0;
    map_reload_tileset();
    load_bg_palset(mh.palset);
    clear_bg();
    map_draw_all();
    camera_update();
    apply_scroll();
    render_sprites();
    hud_show();
    DISPLAY_ON;
}

void warp_to(uint8_t map, uint8_t x, uint8_t y, uint8_t dir) BANKED {
    uint8_t i;
    if (!fade_level) fade_out();
    DISPLAY_OFF;
    hide_all_sprites();
    big_shadow_on = 0;
    actors_clear();
    for (i = 0; i < NUM_SLOTS; i++) slot_sheet[i] = 0xFF;
    map_load(map);
    if (x == 0xFE) x = mh.w - 1;
    if (y == 0xFE) y = mh.h - 1;
    player_place(x, y, dir);
    actors_spawn_map();
    if (mh.music != 0xFF) {
        music_play(mh.music);
        gs.music_unlock[mh.music >> 3] |= 1 << (mh.music & 7);
    }
    gs.map = map;
    gs.px = x; gs.py = y; gs.pdir = dir;
    if (mh.district) gs.visited |= 1 << (mh.district - 1);
    gs.revive_used = gs.revive_used;   /* unchanged */
    memcpy(&checkpoint, &gs, sizeof(gs));
    last_tx = x; last_ty = y;
    trig_latch = 0xFF;
    image_mode = 0;
    clear_bg();
    map_draw_all();
    camera_update();
    apply_scroll();
    render_sprites();
    hud_show();
    DISPLAY_ON;
    fade_in();
    if (mh.enter_script != 0xFFFF) script_run(mh.enter_script);
}

static void edge_exit(uint8_t e) {
    uint8_t m = mh.exits[e];
    uint8_t tx = (uint8_t)((pl_x >> 4) + 8) >> 4, ty = (uint8_t)((pl_y >> 4) + 8) >> 4;
    if (m == 0xFF) return;
    switch (e) {
    case 0: warp_to(m, tx, 0xFE, DIR_UP); break;
    case 1: warp_to(m, tx, 0, DIR_DOWN); break;
    case 2: warp_to(m, 0xFE, ty, DIR_LEFT); break;
    default: warp_to(m, 0, ty, DIR_RIGHT); break;
    }
}

static void check_player_tile(void) {
    int16_t cx = (pl_x >> 4) + 8, cy = (pl_y >> 4) + 12;
    uint8_t tx, ty, i;
    /* edge exits */
    if ((pl_x >> 4) < -2 && pl_dir == DIR_LEFT) { edge_exit(2); return; }
    if ((pl_y >> 4) < -4 && pl_dir == DIR_UP) { edge_exit(0); return; }
    if ((pl_x >> 4) > (int16_t)mh.w * 16 - 14 && pl_dir == DIR_RIGHT) { edge_exit(3); return; }
    if ((pl_y >> 4) > (int16_t)mh.h * 16 - 14 && pl_dir == DIR_DOWN) { edge_exit(1); return; }
    if (cx < 0 || cy < 0) return;
    tx = (uint8_t)(cx >> 4);
    ty = (uint8_t)(cy >> 4);
    if (tx != last_tx || ty != last_ty) {
        last_tx = tx; last_ty = ty;
        for (i = 0; i < mh.nwarps; i++) {
            warp_t *w = &warps[i];
            if (w->x == tx && w->y == ty) {
                if (cond_ok(w->cond)) {
                    sfx_play(7);
                    warp_to(w->dmap, w->dx, w->dy, w->ddir);
                    return;
                } else if (w->lockscript != 0xFFFF) {
                    /* locked: step back and explain */
                    static const int8_t bx[4] = {0, 0, 1, -1};
                    static const int8_t by[4] = {-1, 1, 0, 0};
                    pl_x += bx[pl_dir] * 6 * 16;
                    pl_y += by[pl_dir] * 6 * 16;
                    sfx_play(15);
                    last_tx = 0xFF;
                    script_run(w->lockscript);
                    return;
                }
            }
        }
    }
    /* triggers */
    for (i = 0; i < mh.nobjs; i++) {
        obj_t *o = &objs[i];
        if (o->type != OBJ_TRIGGER) continue;
        if (tx >= o->x && tx < o->x + o->a && ty >= o->y && ty < o->y + o->b && cond_ok(o->cond)) {
            if (trig_latch != i) {
                trig_latch = i;
                script_run(o->script);
            }
            return;
        }
    }
    trig_latch = 0xFF;
}

/* ------------------------------------------------------------------ death */
void game_over(void) BANKED {
    uint8_t sel = 0;
    music_play(MUS_GAMEOVER);
    fade_out();
    DISPLAY_OFF;
    hide_all_sprites();
    HIDE_WIN;
    image_mode = 1;
    load_bg_palset(mh.palset);
    clear_bg();
    SCX_REG = 0; SCY_REG = 0;
    txt_target = TXT_BG;
    attr_area(0, 0, 20, 18, PAL_HUD);
    fill_area(0, 0, 20, 18, 0);
    print_at(5, 6, "THE SHADOW");
    print_at(7, 7, "WAITS.");
    print_at(6, 11, "RETRY");
    print_at(6, 12, "QUIT TO TITLE");
    DISPLAY_ON;
    fade_in();
    for (;;) {
        put_tile(4, 11, sel == 0 ? UI_CURSOR : 0);
        put_tile(4, 12, sel == 1 ? UI_CURSOR : 0);
        wait_frame();
        if (joy_new & (J_UP | J_DOWN)) { sel ^= 1; sfx_play(2); }
        if (joy_new & (J_A | J_START)) { sfx_play(1); break; }
    }
    fade_out();
    if (sel == 1) {
        game_state = GS_TITLE;
        return;
    }
    memcpy(&gs, &checkpoint, sizeof(gs));
    if (gs.hp < 6) gs.hp = gs.maxhp < 6 ? gs.maxhp : 6;
    lockdown_timer_on = 0;
    music_cur = 0xFE;
    warp_to(gs.map, gs.px, gs.py, gs.pdir);
}

static void handle_death(void) {
    if (infl_stage() >= 2 && !gs.revive_used) {
        /* the Second Shadow refuses to let him die */
        gs.revive_used = 1;
        flash_red(10);
        shake_t = 30;
        sfx_play(10);
        dlg_say("A cold weight\nlifts you off the\nfloor.|NOT YET.\nYOU ARE STILL\nUSEFUL TO ME.");
        dlg_close();
        gs.hp = 4;
        infl_add(8);
        pl_hurt = 90;
        hud_dirty = 1;
        return;
    }
    game_over();
}

/* ------------------------------------------------------------------ chapter card & images */
static const char *const ch_titles[8] = {
    "PROLOGUE", "THE PAWNSHOP", "COLD STORAGE", "THE RED LANTERN",
    "ST. AGNES", "THE DRAIN", "THE RECORDS ROOM", "THE LAST WARD"
};
static const char *const ch_targets[8] = {
    "", "Eddie Voss", "Hector Vale", "Nolan Pike", "Sgt. Dacre", "Alec Mott", "Silas Crewe", "Victor Rusk"
};

void chapter_card(uint8_t n) BANKED {
    uint8_t i, l;
    dlg_close();
    fade_out();
    DISPLAY_OFF;
    hide_all_sprites();
    HIDE_WIN;
    image_mode = 1;
    SCX_REG = 0; SCY_REG = 0;
    txt_target = TXT_BG;
    clear_bg();
    attr_area(0, 0, 20, 18, PAL_HUD);
    gs.chapter = n;
    if (n) {
        print_at(6, 5, "CHAPTER");
        put_tile(14, 5, n + ('0' - 32));
    }
    l = 0;
    while (ch_titles[n][l]) l++;
    print_at((20 - l) >> 1, 8, ch_titles[n]);
    if (n) {
        print_at(4, 12, "TARGET:");
        print_at(4, 13, ch_targets[n]);
    }
    DISPLAY_ON;
    fade_in();
    for (i = 0; i < 150; i++) {
        wait_frame();
        if (joy_new & (J_A | J_START)) break;
    }
    fade_out();
    restore_map_view();
    fade_in();
}

/* illustration: id 0xFF = restore map */
void image_show(uint8_t id) BANKED {
    far_t f;
    uint8_t n, tw, th, y;
    const uint8_t *p;
    static uint8_t row[20];
    if (id == 0xFF) {
        if (!image_mode) return;
        dlg_close();
        fade_out();
        restore_map_view();
        fade_in();
        return;
    }
    cur_tileset = 0xFF;   /* VRAM bank 1 tiles get overwritten */
    dlg_close();
    fade_out();
    DISPLAY_OFF;
    image_mode = 1;
    hide_all_sprites();
    f = image_dir[id];
    n = far_byte(f.bank, f.ptr);
    tw = far_byte(f.bank, f.ptr + 1);
    th = far_byte(f.bank, f.ptr + 2);
    p = f.ptr + 3;
    far_read(f.bank, p, bg_pal, 48);
    p += 48;
    vram_bg_tiles(1, 0, n ? n : 256, f.bank, p);
    p += (uint16_t)(n ? n : 256) * 16;
    clear_bg();
    VBK_REG = 0;
    for (y = 0; y < th; y++) {
        far_read(f.bank, p + (uint16_t)y * tw, row, tw);
        set_bkg_tiles(0, y, tw, 1, row);
    }
    p += (uint16_t)tw * th;
    VBK_REG = 1;
    for (y = 0; y < th; y++) {
        far_read(f.bank, p + (uint16_t)y * tw, row, tw);
        set_bkg_tiles(0, y, tw, 1, row);
    }
    VBK_REG = 0;
    txt_target = TXT_BG;
    if (th < 18) attr_area(0, th, 20, 18 - th, PAL_HUD);
    SCX_REG = 0; SCY_REG = 0;
    HIDE_WIN;
    DISPLAY_ON;
    fade_in();
}

/* ------------------------------------------------------------------ game start */
static void state_reset(void) {
    memset(&gs, 0, sizeof(gs));
    gs.magic[0] = 'H'; gs.magic[1] = 'M'; gs.magic[2] = '2'; gs.magic[3] = 'S';
    gs.version = 1;
    gs.hp = 10; gs.maxhp = 10;
    gs.weapon = 0;
    gs.tool = TOOL_NONE;
    gs.bandages = 1;
    gs.music_unlock[0] = 0x03;  /* title + gloam */
}

void game_new(void) BANKED {
    state_reset();
    item_give(IT_PIPE);
    game_state = GS_PLAY;
    fade_level = 4;
    music_cur = 0xFE;
    script_run(SCR_INTRO);
    if (game_state != GS_PLAY) return;
    game_loop();
}

void game_continue(void) BANKED {
    if (!save_load()) return;
    game_state = GS_PLAY;
    music_cur = 0xFE;
    fade_level = 4;
    warp_to(gs.map, gs.px, gs.py, gs.pdir);
    game_loop();
}

static void cycle_tool(void) {
    uint8_t t = gs.tool, k;
    for (k = 0; k < NUM_TOOLS; k++) {
        t = (t + 1) % NUM_TOOLS;
        if (t == TOOL_NONE) break;
        if (t == TOOL_PISTOL && item_has(IT_PISTOL)) break;
        if (t == TOOL_BOTTLE && gs.bottles) break;
        if (t == TOOL_SHADOW && flag_get(F_SHADOW_POWER)) break;
        if (t == TOOL_BANDAGE && gs.bandages) break;
    }
    gs.tool = t;
    sfx_play(2);
    hud_dirty = 1;
}

void game_loop(void) BANKED {
    uint8_t decay = 0;
    while (game_state == GS_PLAY) {
        wait_frame();
        apply_scroll();
        if (++gs.play_frm >= 60) {
            gs.play_frm = 0;
            if (++gs.play_sec >= 60) { gs.play_sec = 0; gs.play_min++; }
        }
        if (joy_new & J_START) {
            pause_menu();
            if (game_state != GS_PLAY) break;
            continue;
        }
        if (joy_new & J_SELECT) cycle_tool();
        player_update();
        actors_update();
        special_tick();
        map_anim_tick();
        check_player_tile();
        if (game_state != GS_PLAY) break;
        camera_update();
        render_sprites();
        if (script_pending != 0xFFFF) {
            uint16_t s = script_pending;
            script_pending = 0xFFFF;
            script_run(s);
        }
        if (hud_dirty) hud_draw();
        if (gs.hp == 0) handle_death();
        /* police alert decays over time; faster in safe places */
        if (gs.alert && ++decay >= ((mh.flags & MAPF_SAFE) ? 8 : 90)) {
            decay = 0;
            alert_add(-1);
        }
        /* Possession stage: brief, signalled loss of control */
        if (infl_stage() == 3 && !lockdown_timer_on) {
            if (++possess_t > 2400 && rand8() < 4) {
                uint8_t i, d = rand8() & 3;
                possess_t = 0;
                flash_red(4);
                sfx_play(10);
                dlg_say("Your body moves\nwithout you.");
                dlg_close();
                for (i = 0; i < 24; i++) {
                    static const int8_t dx[4] = {0, 0, -1, 1};
                    static const int8_t dy[4] = {1, -1, 0, 0};
                    int16_t nx = pl_x + dx[d] * 16, ny = pl_y + dy[d] * 16;
                    uint8_t tx = (uint8_t)(((nx >> 4) + 8) >> 4), ty = (uint8_t)(((ny >> 4) + 12) >> 4);
                    if (mflags_at(tx, ty) & MF_SOLID) break;
                    pl_x = nx; pl_y = ny;
                    pl_dir = d;
                    pl_anim++;
                    camera_update();
                    wait_frame();
                    apply_scroll();
                    render_sprites();
                }
            }
        }
    }
}
