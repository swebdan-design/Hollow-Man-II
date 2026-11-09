#pragma bank 255
/* menu.c - pause menu: inventory, casebook, city map, shadow status, save, options */
#include "hm.h"
#include "gen_dirs.h"

static void win_full(void) {
    txt_target = TXT_WIN;
    attr_area(0, 0, 20, 18, PAL_DLG | 0x80);
    fill_area(0, 0, 20, 18, 0);
    move_win(7, 0);
    SHOW_WIN;
    hide_all_sprites();
}

static void title_bar(const char *t) {
    draw_box(0, 0, 20, 18);
    print_at(2, 1, t);
    fill_area(1, 2, 18, 1, UI_BOX_B);
}

static uint8_t menu_select(uint8_t x, uint8_t y, uint8_t n, uint8_t sel) {
    for (;;) {
        uint8_t i;
        for (i = 0; i < n; i++) put_tile(x, y + i, i == sel ? UI_CURSOR : 0);
        wait_frame();
        if (joy_new & J_UP) { sel = sel ? sel - 1 : n - 1; sfx_play(2); }
        if (joy_new & J_DOWN) { sel = (sel + 1) % n; sfx_play(2); }
        if (joy_new & J_A) { sfx_play(1); return sel; }
        if (joy_new & (J_B | J_START)) { sfx_play(2); return 0xFF; }
    }
}

/* far text reader with paging inside a region of the window */
static void page_far(uint8_t x, uint8_t y, uint8_t bank, const uint8_t *p) {
    uint8_t c, cx = x, cy = y;
    fill_area(x, y, 18, 4, 0);
    for (;;) {
        c = far_byte(bank, p++);
        if (c == 0 || c == '\v') break;
        if (c == '\n') { cx = x; cy++; continue; }
        if (c == '\f') {
            put_tile(18, y + 4, UI_MORE);
            do wait_frame(); while (!(joy_new & (J_A | J_B)));
            put_tile(18, y + 4, 0);
            fill_area(x, y, 18, 4, 0);
            cx = x; cy = y;
            continue;
        }
        put_tile(cx++, cy, c - 32);
    }
    put_tile(18, y + 4, UI_MORE);
    do wait_frame(); while (!(joy_new & (J_A | J_B)));
    put_tile(18, y + 4, 0);
}

static const uint8_t *menu_entry(uint8_t idx) {
    uint16_t off = far_word(menu_text_offs_BANK, menu_text_offs + idx * 2);
    return menu_text + off;
}

static void print_name(uint8_t x, uint8_t y, uint8_t idx) {
    print_far(x, y, menu_text_BANK, menu_entry(idx));
}

static const uint8_t *desc_of(uint8_t idx) {
    const uint8_t *p = menu_entry(idx);
    while (far_byte(menu_text_BANK, p)) p++;
    return p + 1;
}

/* ------------------------------------------------------------------ inventory */
static uint8_t use_request;

static void inventory(void) {
    static uint8_t list[NUM_ITEMS + 4];
    uint8_t n, i, sel = 0, top = 0;
    for (;;) {
        win_full();
        title_bar("INVENTORY");
        n = 0;
        for (i = 0; i < NUM_ITEMS; i++) if (item_has(i)) list[n++] = i;
        list[n++] = 200;   /* bandages */
        list[n++] = 201;   /* bottles */
        list[n++] = 202;   /* ammo */
        if (sel >= n) sel = n - 1;
        if (sel < top) top = sel;
        if (sel >= top + 9) top = sel - 8;
        for (i = 0; i < 9 && top + i < n; i++) {
            uint8_t it = list[top + i], y = 3 + i;
            if (it == 200) { print_at(2, y, "Bandages"); print_num(15, y, gs.bandages, 2); }
            else if (it == 201) { print_at(2, y, "Empty Bottles"); print_num(15, y, gs.bottles, 2); }
            else if (it == 202) { print_at(2, y, "Revolver Rounds"); print_num(17, y, gs.ammo, 2); }
            else {
                print_name(2, y, it);
                if ((it == IT_PIPE && gs.weapon == 0) || (it == IT_AXE && gs.weapon == 1)) put_tile(18, y, UI_CHECK_ON);
            }
        }
        print_at(1, 13, "A:USE/EQUIP B:BACK");
        fill_area(1, 14, 18, 1, UI_BOX_B);
        for (;;) {
            uint8_t it;
            for (i = 0; i < 9; i++) put_tile(1, 3 + i, (top + i) == sel ? UI_CURSOR : 0);
            fill_area(1, 15, 18, 2, 0);
            it = list[sel];
            if (it < NUM_ITEMS) {
                /* first line of description */
                const uint8_t *d = desc_of(it);
                uint8_t c, x = 1, y = 15;
                while ((c = far_byte(menu_text_BANK, d++)) && c != '\f' && y < 17) {
                    if (c == '\n') { x = 1; y++; continue; }
                    put_tile(x++, y, c - 32);
                }
            } else if (it == 200) print_at(1, 15, "Restores 2 hearts");
            else if (it == 201) print_at(1, 15, "Throw to distract");
            else print_at(1, 15, "For the revolver.");
            wait_frame();
            if (joy_new & J_UP && sel) { sel--; sfx_play(2); if (sel < top) break; }
            if (joy_new & J_DOWN && sel + 1 < n) { sel++; sfx_play(2); if (sel >= top + 9) break; }
            if (joy_new & (J_B | J_START)) { sfx_play(2); return; }
            if (joy_new & J_A) {
                sfx_play(1);
                if (it == IT_PIPE) { gs.weapon = 0; break; }
                if (it == IT_AXE) { gs.weapon = 1; break; }
                if (it == 200) {
                    if (gs.bandages && gs.hp < gs.maxhp) {
                        gs.bandages--;
                        gs.hp = gs.hp + 4 > gs.maxhp ? gs.maxhp : gs.hp + 4;
                        sfx_play(9);
                    } else sfx_play(15);
                    break;
                }
                if (it == 201) { if (gs.bottles) gs.tool = TOOL_BOTTLE; else sfx_play(15); return; }
                if (it == 202 || it == IT_PISTOL) { if (item_has(IT_PISTOL)) gs.tool = TOOL_PISTOL; return; }
                /* key item: use on whatever is in front of you */
                use_request = 1;
                return;
            }
        }
    }
}

/* ------------------------------------------------------------------ casebook */
static const char *const target_names[7] = {
    "Eddie Voss", "Hector Vale", "Nolan Pike", "Sgt. Dacre", "Alec Mott", "Silas Crewe", "Victor Rusk"
};

static void casebook(void) {
    static uint8_t list[NUM_EVIDENCE];
    uint8_t n = 0, i, sel = 0, top = 0, page = 0;
    for (i = 0; i < NUM_EVIDENCE; i++) if (ev_has(i)) list[n++] = i;
    for (;;) {
        win_full();
        title_bar("CASEBOOK");
        if (page == 0) {
            print_at(2, 3, "THE SEVEN NAMES");
            for (i = 0; i < 7; i++) {
                uint8_t done = gs.chapter > i + 1 || flag_get(F_CH1_DONE + i);
                print_at(3, 5 + i, done || gs.chapter >= i + 1 ? target_names[i] : "? ? ? ? ?");
                put_tile(16, 5 + i, done ? UI_CHECK_ON : UI_CHECK_OFF);
            }
            print_at(2, 13, "EVIDENCE");
            print_num(11, 13, n, 2);
            print_at(13, 13, "/");
            print_num(14, 13, NUM_EVIDENCE, 2);
            print_at(2, 15, "A:FILES  B:BACK");
            for (;;) {
                wait_frame();
                if (joy_new & (J_B | J_START)) { sfx_play(2); return; }
                if (joy_new & (J_A | J_RIGHT)) { sfx_play(1); page = 1; break; }
            }
            continue;
        }
        if (n == 0) {
            print_at(2, 4, "No evidence yet.");
            do wait_frame(); while (!(joy_new & (J_A | J_B)));
            page = 0;
            continue;
        }
        if (sel < top) top = sel;
        if (sel >= top + 10) top = sel - 9;
        for (i = 0; i < 10 && top + i < n; i++) print_name(2, 3 + i, NUM_ITEMS + list[top + i]);
        print_at(1, 14, "A:READ  B:BACK");
        for (;;) {
            for (i = 0; i < 10; i++) put_tile(1, 3 + i, (top + i) == sel ? UI_CURSOR : 0);
            wait_frame();
            if (joy_new & J_UP && sel) { sel--; sfx_play(2); if (sel < top) break; }
            if (joy_new & J_DOWN && sel + 1 < n) { sel++; sfx_play(2); if (sel >= top + 10) break; }
            if (joy_new & (J_B | J_START)) { sfx_play(2); page = 0; break; }
            if (joy_new & J_A) {
                sfx_play(1);
                fill_area(1, 3, 18, 14, 0);
                print_name(1, 4, NUM_ITEMS + list[sel]);
                fill_area(1, 5, 18, 1, UI_BOX_B);
                page_far(1, 7, menu_text_BANK, desc_of(NUM_ITEMS + list[sel]));
                break;
            }
        }
    }
}

/* ------------------------------------------------------------------ city map */
static const char *const dist_names[7] = {
    "MERCY ST", "COMMERCE", "INDUSTRY", "RED LANT", "OLD GLOAM", "THE DRAIN", "LAST WARD"
};
static const uint8_t dist_x[7] = {1, 7, 13, 7, 1, 7, 13};
static const uint8_t dist_y[7] = {8, 8, 8, 4, 4, 12, 4};

static void city_map(void) {
    uint8_t i;
    win_full();
    title_bar("GLOAM - CITY MAP");
    for (i = 0; i < 7; i++) {
        uint8_t x = dist_x[i], y = dist_y[i];
        draw_box(x, y, 6, 3);
        if (gs.visited & (1 << i)) {
            uint8_t l = 0;
            while (dist_names[i][l] && l < 4) {
                put_tile(x + 1 + l, y + 1, dist_names[i][l] - 32);
                l++;
            }
        } else print_at(x + 1, y + 1, "????");
        if (mh.district == i + 1) put_tile(x + 5, y + 1, UI_MARKER);
    }
    print_at(1, 15, "YOU ARE IN:");
    if (mh.district) print_at(1, 16, dist_names[mh.district - 1]);
    else print_at(1, 16, "UNKNOWN");
    do wait_frame(); while (!(joy_new & (J_A | J_B | J_START)));
    sfx_play(2);
}

/* ------------------------------------------------------------------ shadow status */
static const char *const stage_names[4] = {"DORMANT", "WATCHING", "AWAKENED", "POSSESSION"};
static const char *const stage_l1[4] = {"Your shadow is", "It moves when you", "It reaches for", "It wears you."};
static const char *const stage_l2[4] = {"only a shadow.", "do not.", "your enemies.", "Hold on."};

static void shadow_status(void) {
    uint8_t i, st = infl_stage();
    win_full();
    title_bar("THE SECOND SHADOW");
    print_at(2, 4, "INFLUENCE");
    print_num(14, 4, gs.influence, 3);
    for (i = 0; i < 10; i++) {
        uint8_t v = gs.influence >= (i + 1) * 10 ? UI_BAR_F : (gs.influence >= i * 10 + 5 ? UI_BAR_H : UI_BAR_E);
        put_tile(5 + i, 5, v);
    }
    put_tile(3, 5, UI_EYE0 + st);
    print_at(2, 7, "STAGE:");
    print_at(9, 7, stage_names[st]);
    print_at(2, 9, stage_l1[st]);
    print_at(2, 10, stage_l2[st]);
    if (flag_get(F_SHADOW_POWER)) {
        print_at(2, 12, "SHD tool: stuns");
        print_at(2, 13, "foes, opens walls");
    }
    print_at(2, 15, "POLICE ALERT");
    for (i = 0; i < 3; i++) put_tile(15 + i, 15, alert_level() > i ? UI_BADGE : UI_BADGE_OFF);
    do wait_frame(); while (!(joy_new & (J_A | J_B | J_START)));
    sfx_play(2);
}

/* ------------------------------------------------------------------ pause root */
static const char *const pause_items[7] = {
    "INVENTORY", "CASEBOOK", "CITY MAP", "SHADOW STATUS", "SAVE", "OPTIONS", "RETURN TO GAME"
};

void pause_menu(void) BANKED {
    uint8_t sel = 0, i, ot = txt_target;
    use_request = 0;
    sfx_play(1);
    for (;;) {
        win_full();
        title_bar("PAUSED");
        for (i = 0; i < 7; i++) print_at(3, 4 + i, pause_items[i]);
        print_at(2, 13, "CHAPTER");
        put_tile(10, 13, (gs.chapter < 8 ? gs.chapter : 7) + ('0' - 32));
        print_at(2, 14, "TIME");
        print_num(8, 14, gs.play_min / 60, 2);
        put_tile(10, 14, ':' - 32);
        print_num(11, 14, gs.play_min % 60, 2);
        print_at(2, 15, "EVIDENCE");
        print_num(11, 15, ev_count(), 2);
        sel = menu_select(2, 4, 7, sel);
        if (sel == 0xFF || sel == 6) break;
        if (sel == 0) { inventory(); if (use_request) break; }
        else if (sel == 1) casebook();
        else if (sel == 2) city_map();
        else if (sel == 3) shadow_status();
        else if (sel == 4) {
            fill_area(1, 12, 18, 5, 0);
            if (mh.flags & MAPF_SAFE || !lockdown_timer_on) {
                if (save_write()) { sfx_play(18); print_at(2, 13, "PROGRESS SAVED."); }
                else print_at(2, 13, "SAVE FAILED!");
            } else print_at(2, 13, "NOT NOW.");
            wait_frames(60);
        } else if (sel == 5) {
            options_menu(1);
        }
    }
    txt_target = ot;
    hud_show();
    hud_dirty = 1;
    render_sprites();
    if (use_request) {
        /* use key item on what is in front: identical to pressing A there */
        int16_t fx = (pl_x >> 4) + 8 + (pl_dir == DIR_LEFT ? -16 : (pl_dir == DIR_RIGHT ? 16 : 0));
        int16_t fy = (pl_y >> 4) + 12 + (pl_dir == DIR_UP ? -16 : (pl_dir == DIR_DOWN ? 16 : 0));
        uint8_t found = 0;
        if (fx >= 0 && fy >= 0) {
            for (i = 0; i < mh.nobjs; i++) {
                obj_t *o = &objs[i];
                if (o->type == OBJ_SIGN && o->x == (fx >> 4) && o->y == (fy >> 4) && cond_ok(o->cond)) {
                    script_run(o->script);
                    found = 1;
                    break;
                }
            }
        }
        if (!found) {
            sfx_play(15);
            dlg_say("There is nothing\nto use it on here.");
            dlg_close();
        }
    }
}
