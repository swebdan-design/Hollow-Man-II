
/* title.c - title screen, main menu, options, music player, credits, endings */
#include <string.h>
#include "hm.h"
#include "gba_dirs.h"

extern uint8_t vis_level[4];

static void bg_text_screen(void) {
    fade_out();
    DISPLAY_OFF;
    hide_all_sprites();
    image_mode = 1;
    set_mode_tiles();
    ui_clear();
    clear_bg();
    load_bg_palset(0);
    txt_target = TXT_BG;
    ui_ox = 5; ui_oy = 1;
}

static void center(uint8_t y, const char *s) {
    uint8_t l = 0;
    while (s[l]) l++;
    print_at((20 - l) >> 1, y, s);
}

/* ------------------------------------------------------------------ title */
static uint8_t smoke_x[4], smoke_y[4];

static void title_draw(void) {
    fade_out();
    DISPLAY_OFF;
    hide_all_sprites();
    image_show(IMG_TITLE);   /* title, subtitle and credit are part of the illustration */
}

extern void oam_set(uint8_t i, int16_t x, int16_t y, uint16_t tile, uint8_t pal);
static void smoke_tick(void) {
    /* the painted title already carries fog and rain: park the four title OBJ slots off-screen */
    uint8_t i;
    for (i = 0; i < 4; i++) { oam_set(i, 0, 160, 0, 0); }   /* y=160: off-screen */
}

void title_run(void) {
    uint8_t i, blink = 0;
    music_play(MUS_TITLE);
    title_draw();
    for (i = 0; i < 4; i++) { smoke_x[i] = 20 + i * 36; smoke_y[i] = 80 + i * 16; }
    fade_in();
    for (;;) {
        wait_frame();
        smoke_tick();
        blink++;
        if (blink == 1) center(16, "PRESS START");
        if (blink == 40) fill_area(0, 16, 20, 1, 0);
        if (blink >= 70) blink = 0;
        if (joy_new & (J_START | J_A)) { sfx_play(1); break; }
    }
    fill_area(0, 16, 20, 1, 0);
}

/* ------------------------------------------------------------------ main menu */
static const char *const mm_items[5] = {"NEW GAME", "CONTINUE", "MUSIC PLAYER", "OPTIONS", "CREDITS"};

uint8_t main_menu(void) {
    uint8_t sel, i, has = save_valid();
    sel = has ? 1 : 0;
    txt_target = TXT_WIN;
    ui_ox = 0; ui_oy = 0;
    draw_box(7, 11, 16, 7);
    for (i = 0; i < 5; i++) print_at(10, 12 + i, mm_items[i]);
    if (!has) {
        attr_area(10, 13, 9, 1, 5);
        put_tile(20, 13, UI_LOCK);
    }
    for (;;) {
        for (i = 0; i < 5; i++) put_tile(9, 12 + i, i == sel ? UI_CURSOR : 0);
        wait_frame();
        smoke_tick();
        if (joy_new & J_UP) { do sel = sel ? sel - 1 : 4; while (sel == 1 && !has); sfx_play(2); }
        if (joy_new & J_DOWN) { do sel = (sel + 1) % 5; while (sel == 1 && !has); sfx_play(2); }
        if (joy_new & (J_A | J_START)) { sfx_play(1); break; }
    }
    ui_clear();
    ui_ox = 5; ui_oy = 1;
    hide_all_sprites();
    return sel;
}

/* ------------------------------------------------------------------ options */
static const char *const speed_names[4] = {"FAST  ", "NORMAL", "SLOW  ", "SLOWER"};

void options_menu(uint8_t ingame) {
    uint8_t sel = 0, i;
    if (ingame) {
        txt_target = TXT_WIN;
        ui_ox = 5; ui_oy = 1;
    } else {
        bg_text_screen();
        DISPLAY_ON;
        fade_in();
    }
    fill_area(0, 0, 20, 18, 0);
    draw_box(0, 0, 20, 18);
    print_at(2, 1, "OPTIONS");
    print_at(3, 3, "MUSIC");
    print_at(3, 4, "SOUND FX");
    print_at(3, 5, "TEXT SPEED");
    print_at(3, 6, "DONE");
    print_at(2, 8, "CONTROLS");
    print_at(2, 9, "D-PAD  move");
    print_at(2, 10, "A  talk/search/use");
    print_at(2, 11, "B  attack");
    print_at(2, 12, "hold B  heavy blow");
    print_at(2, 13, "SELECT cycle tool");
    print_at(2, 14, "START  pause menu");
    print_at(2, 16, "A: interact first");
    for (;;) {
        print_at(14, 3, music_on ? "ON " : "OFF");
        print_at(14, 4, sfx_on ? "ON " : "OFF");
        print_at(12, 5, speed_names[text_speed & 3]);
        for (i = 0; i < 4; i++) put_tile(2, 3 + i, i == sel ? UI_CURSOR : 0);
        wait_frame();
        if (joy_new & J_UP) { sel = sel ? sel - 1 : 3; sfx_play(2); }
        if (joy_new & J_DOWN) { sel = (sel + 1) & 3; sfx_play(2); }
        if (joy_new & (J_A | J_LEFT | J_RIGHT)) {
            sfx_play(1);
            if (sel == 0) {
                music_on ^= 1;
                if (!music_on) { uint8_t m = music_cur; music_stop(); music_cur = m; }
                else { uint8_t m = music_cur; music_cur = 0xFE; music_play(m); }
            } else if (sel == 1) sfx_on ^= 1;
            else if (sel == 2) text_speed = (text_speed + 1) & 3;
            else break;
        }
        if (joy_new & J_B) break;
    }
    options_save();
}

/* ------------------------------------------------------------------ music player */
void music_player(void) {
    uint8_t sel = 0, top = 0, i, playing = 0xFF;
    /* unlocked tracks come from the save file (or the defaults) */
    if (!save_load()) gs.music_unlock[0] |= 0x03;
    bg_text_screen();
    print_at(1, 0, "MUSIC PLAYER");
    print_at(1, 1, "by Synth Centric");
    DISPLAY_ON;
    fade_in();
    music_stop();
    for (;;) {
        for (i = 0; i < 8; i++) {
            uint8_t s = top + i;
            fill_area(0, 3 + i, 20, 1, 0);
            if (s >= NUM_SONGS) continue;
            print_num(1, 3 + i, s + 1, 2);
            if (gs.music_unlock[s >> 3] & (1 << (s & 7))) print_at(4, 3 + i, song_title[s]);
            else { print_at(4, 3 + i, "- - - - -"); put_tile(18, 3 + i, UI_LOCK); }
            if (s == playing) put_tile(3, 3 + i, UI_NOTE);
        }
        print_at(1, 16, "A:PLAY B:STOP/BACK");
        for (;;) {
            uint8_t c, r;
            for (i = 0; i < 8; i++) put_tile(0, 3 + i, (top + i) == sel ? UI_CURSOR : 0);
            /* visualiser: four channel bars */
            for (c = 0; c < 4; c++) {
                uint8_t lv = vis_level[c] >> 1;
                for (r = 0; r < 4; r++) {
                    uint8_t t = lv > r * 2 + 1 ? UI_SOLID2 : (lv > r * 2 ? UI_SOLID1 : 0);
                    put_tile(5 + c * 3, 14 - r, t);
                    put_tile(6 + c * 3, 14 - r, t);
                }
            }
            wait_frame();
            if (joy_new & J_UP && sel) { sel--; sfx_play(2); if (sel < top) { top--; break; } }
            if (joy_new & J_DOWN && sel + 1 < NUM_SONGS) { sel++; sfx_play(2); if (sel >= top + 8) { top++; break; } }
            if (joy_new & J_A) {
                if (gs.music_unlock[sel >> 3] & (1 << (sel & 7))) {
                    music_cur = 0xFE;
                    music_play(sel);
                    playing = sel;
                } else sfx_play(15);
                break;
            }
            if (joy_new & J_B) {
                if (playing != 0xFF) { music_stop(); playing = 0xFF; break; }
                return;
            }
        }
    }
}

/* ------------------------------------------------------------------ credits */
static const char *const credit_lines[] = {
    "HOLLOW MAN",
    "THE SECOND SHADOW",
    "",
    "by Synth Centric",
    "",
    "",
    "- STORY -",
    "Synth Centric",
    "",
    "- MUSIC -",
    "Original soundtrack",
    "composed for the",
    "Game Boy Color",
    "by Synth Centric",
    "",
    "- CHARACTERS -",
    "HOLLOW MAN",
    "DET. MARA BELL",
    "EDDIE VOSS",
    "HECTOR VALE",
    "NOLAN PIKE",
    "SGT. DACRE",
    "ALEC MOTT",
    "SILAS CREWE",
    "VICTOR RUSK",
    "THE EIGHTH MAN",
    "",
    "- PROGRAMMING -",
    "- ART - DESIGN -",
    "Made for",
    "Synth Centric",
    "with GBDK-2020",
    "",
    "",
    "Thank you",
    "for playing.",
    "",
    "",
    "",
    "THE END",
    0
};

void credits_run(uint8_t ending) {
    uint8_t line = 0, row = 18, y, tail = 0;
    uint16_t scroll = 0;
    (void)ending;
    music_play(MUS_ENDING);
    bg_text_screen();
    ui_oy = 0;
    gs.music_unlock[MUS_ENDING >> 3] |= 1 << (MUS_ENDING & 7);
    /* prime first screen */
    DISPLAY_ON;
    fade_in();
    for (;;) {
        /* scroll 1 px every 3 frames; write a new line every 16 px */
        wait_frame();
        if ((frame_ctr % 3) == 0) {
            scroll++;
            REG_BGVOFS(1) = (uint16_t)scroll;
            if ((scroll & 15) == 0) {
                y = (uint8_t)((row) & 31);
                fill_area(0, y, 20, 1, 0);
                attr_area(0, y, 20, 1, PAL_HUD);
                if (credit_lines[line]) {
                    center(y, credit_lines[line]);
                    line++;
                } else {
                    if (tail == 0) {
                        /* clear every not-yet-visible ring row so old lines never reappear */
                        uint8_t k;
                        for (k = 1; k < 14; k++) fill_area(0, (uint8_t)(row + k) & 31, 20, 1, 0);
                    }
                    if (++tail > 5) break;
                }
                row += 2;
                y = (uint8_t)((row - 1) & 31);
                fill_area(0, y, 20, 1, 0);
            }
        }
        if (joy_new & J_START && line > 6) break;
    }
    for (y = 0; y < 120; y++) { wait_frame(); if (joy_new & (J_A | J_START)) break; }
    fade_out();
    REG_BGVOFS(1) = 0;
    ui_ox = 5; ui_oy = 1;
}

/* ------------------------------------------------------------------ endings */
uint8_t ending_id = 0xFF;   /* last ending shown (0 A, 1 B, 2 secret) */

void ending_run(void) {
    uint8_t e;
    if (flag_get(F_MERCY_DONE) && mercy_count() >= 7 && gs.influence < 50) e = 2;
    else if (gs.influence >= 75) e = 1;
    else e = 0;
    ending_id = e;
    flag_set(F_GAME_CLEAR);
    if (e == 0) script_run(SCR_END_A);
    else if (e == 1) script_run(SCR_END_B);
    else script_run(SCR_END_SECRET);
    credits_run(e);
    /* remember clearing in SRAM: keep the save at the final room */
    game_state = GS_ENDED;
}
