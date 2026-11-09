/* text.c (GBA) - font text on BG1, panels on BG2, dialogue box, HUD helpers.
 * Layouts written for the 20x18 GBC screen are drawn centred through ui_ox/ui_oy. */
#include "hm.h"

uint8_t txt_target = TXT_BG, txt_pal = PAL_DLG;
uint8_t text_speed = 1;
uint8_t dlg_is_open;
uint8_t ui_ox = 5, ui_oy = 1;
static uint8_t cur_bank = 15;   /* 15 = UI palette, 14 = dimmed */

#define TXT ((uint16_t *)SCREENBLOCK(30))
#define PANEL ((uint16_t *)SCREENBLOCK(29))
#define DLG_Y 14
#define DLG_H 6

static inline void txt_set(uint8_t x, uint8_t y, uint16_t t) {
    if (x < 32 && y < 32) TXT[y * 32 + x] = t | (cur_bank << 12);
}
static inline void pan_set(uint8_t x, uint8_t y, uint16_t t) {
    if (x < 32 && y < 32) PANEL[y * 32 + x] = t | (15 << 12);
}

void ui_clear(void) {
    dma3_fill32(TXT, 0, 512);
    dma3_fill32(PANEL, 0, 512);
}

void put_tile(uint8_t x, uint8_t y, uint8_t t) { txt_set(x + ui_ox, y + ui_oy, t); }

static uint8_t ch2tile(uint8_t c) { return (c < 32 || c > 127) ? 0 : c - 32; }

void print_at(uint8_t x, uint8_t y, const char *s) {
    while (*s) put_tile(x++, y, ch2tile((uint8_t)*s++));
}

void print_far(uint8_t x, uint8_t y, uint8_t bank, const uint8_t *s) {
    uint8_t c;
    (void)bank;
    while ((c = *s++) != 0) {
        if (c == '\n') { y++; continue; }
        put_tile(x++, y, ch2tile(c));
    }
}

void print_num(uint8_t x, uint8_t y, uint16_t n, uint8_t digits) {
    uint8_t i;
    x += digits - 1;
    for (i = 0; i < digits; i++) { put_tile(x--, y, (n % 10) + ('0' - 32)); n /= 10; }
}

void fill_area(uint8_t x, uint8_t y, uint8_t w, uint8_t h, uint8_t t) {
    uint8_t i, j;
    for (j = 0; j < h; j++) for (i = 0; i < w; i++) put_tile(x + i, y + j, t);
}

/* GBC attribute fills: palette 5 marks "dimmed" text; anything else is normal */
void attr_area(uint8_t x, uint8_t y, uint8_t w, uint8_t h, uint8_t a) {
    uint8_t i, j, bank = ((a & 7) == 5) ? 14 : 15;
    for (j = 0; j < h; j++)
        for (i = 0; i < w; i++) {
            uint16_t *e = &TXT[(y + j + ui_oy) * 32 + x + i + ui_ox];
            *e = (*e & 0x0FFF) | (bank << 12);
        }
}

void draw_box(uint8_t x, uint8_t y, uint8_t w, uint8_t h) {
    uint8_t i, j;
    x += ui_ox; y += ui_oy;
    for (j = 0; j < h; j++)
        for (i = 0; i < w; i++) {
            uint16_t t = UI_BOX_F;
            if (j == 0) t = i == 0 ? UI_BOX_TL : (i == w - 1 ? UI_BOX_TR : UI_BOX_T);
            else if (j == h - 1) t = i == 0 ? UI_BOX_BL : (i == w - 1 ? UI_BOX_BR : UI_BOX_B);
            else if (i == 0) t = UI_BOX_L;
            else if (i == w - 1) t = UI_BOX_R;
            pan_set(x + i, y + j, t);
            txt_set(x + i, y + j, 0);
        }
}

/* ---------------------------------------------------------------- dialogue */
static void dlg_clear(void) {
    uint8_t i, j;
    for (j = 1; j < DLG_H - 1; j++)
        for (i = 1; i < 29; i++) txt_set(i, DLG_Y + j, 0);
}

void dlg_open(void) {
    uint8_t ox = ui_ox, oy = ui_oy;
    if (dlg_is_open) return;
    ui_ox = 0; ui_oy = 0;
    hud_hide();
    draw_box(0, DLG_Y, 30, DLG_H);
    ui_ox = ox; ui_oy = oy;
    dlg_is_open = 1;
}

void dlg_close(void) {
    uint8_t i, j;
    if (!dlg_is_open) return;
    dlg_is_open = 0;
    for (j = DLG_Y; j < DLG_Y + DLG_H; j++)
        for (i = 0; i < 30; i++) { PANEL[j * 32 + i] = 0; TXT[j * 32 + i] = 0; }
    hud_show();
}

static void wait_ack(void) {
    uint8_t blink = 0;
    for (;;) {
        wait_frame();
        blink++;
        txt_set(28, DLG_Y + DLG_H - 2, (blink & 16) ? UI_MORE : 0);
        if (joy_new & (J_A | J_B)) break;
    }
    txt_set(28, DLG_Y + DLG_H - 2, 0);
    sfx_play(1);
}

static const uint8_t *say_core(const uint8_t *t) {
    uint8_t x = 1, y = 1, c, fast = 0, d;
    dlg_open();
    dlg_clear();
    for (;;) {
        c = *t++;
        if (c == 0) { wait_ack(); break; }
        if (c == '\v') break;
        if (c == '\n') { x = 1; y++; continue; }
        if (c == '\f') { wait_ack(); dlg_clear(); x = 1; y = 1; fast = 0; continue; }
        txt_set(x++, DLG_Y + y, ch2tile(c));
        if (!fast && text_speed) {
            for (d = 0; d < text_speed; d++) {
                wait_frame();
                if (joy_new & (J_A | J_B)) fast = 1;
            }
            if ((x & 3) == 0 && c != ' ') sfx_play(12);
        }
    }
    return t;
}

const uint8_t *dlg_say_far(uint8_t bank, const uint8_t *txt) { (void)bank; return say_core(txt); }
void dlg_say(const char *txt) { say_core((const uint8_t *)txt); }

uint8_t dlg_choice2(const char *a, const char *b) {
    uint8_t sel = 0, i;
    const char *s;
    dlg_open();
    for (i = 1; i < 29; i++) { txt_set(i, DLG_Y + 3, 0); txt_set(i, DLG_Y + 4, 0); }
    for (i = 0, s = a; *s; s++, i++) txt_set(4 + i, DLG_Y + 3, ch2tile(*s));
    for (i = 0, s = b; *s; s++, i++) txt_set(4 + i, DLG_Y + 4, ch2tile(*s));
    for (;;) {
        txt_set(3, DLG_Y + 3, sel == 0 ? UI_CURSOR : 0);
        txt_set(3, DLG_Y + 4, sel == 1 ? UI_CURSOR : 0);
        wait_frame();
        if (joy_new & (J_UP | J_DOWN)) { sel ^= 1; sfx_play(2); }
        if (joy_new & J_A) { sfx_play(1); break; }
    }
    return sel;
}

void hud_hide(void) {
    uint8_t i;
    for (i = 0; i < 30; i++) { TXT[i] = 0; PANEL[i] = 0; }
}
