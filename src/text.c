/* text.c - bank 0: font printing, boxes, dialogue window */
#include "hm.h"

uint8_t txt_target = TXT_BG, txt_pal = PAL_DLG;
uint8_t text_speed = 1;
uint8_t dlg_is_open;

#define T_SPACE 0
#define DLG_ROWS 6
#define DLG_WY 96

void put_tile(uint8_t x, uint8_t y, uint8_t t) {
    if (txt_target == TXT_WIN) set_win_tile_xy(x, y, t);
    else set_bkg_tile_xy(x, y, t);
}

static uint8_t ch2tile(uint8_t c) {
    if (c < 32 || c > 127) return 0;
    return c - 32;
}

void print_at(uint8_t x, uint8_t y, const char *s) {
    while (*s) {
        put_tile(x++, y, ch2tile((uint8_t)*s));
        s++;
    }
}

void print_far(uint8_t x, uint8_t y, uint8_t bank, const uint8_t *s) {
    uint8_t c;
    while ((c = far_byte(bank, s++)) != 0) {
        if (c == '\n') { y++; continue; }
        put_tile(x++, y, ch2tile(c));
    }
}

void print_num(uint8_t x, uint8_t y, uint16_t n, uint8_t digits) {
    uint8_t i;
    x += digits - 1;
    for (i = 0; i < digits; i++) {
        put_tile(x--, y, (n % 10) + ('0' - 32));
        n /= 10;
    }
}

void fill_area(uint8_t x, uint8_t y, uint8_t w, uint8_t h, uint8_t t) {
    if (txt_target == TXT_WIN) fill_win_rect(x, y, w, h, t);
    else fill_bkg_rect(x, y, w, h, t);
}

void attr_area(uint8_t x, uint8_t y, uint8_t w, uint8_t h, uint8_t a) {
    VBK_REG = 1;
    fill_area(x, y, w, h, a);
    VBK_REG = 0;
}

void draw_box(uint8_t x, uint8_t y, uint8_t w, uint8_t h) {
    uint8_t i;
    put_tile(x, y, UI_BOX_TL);
    put_tile(x + w - 1, y, UI_BOX_TR);
    put_tile(x, y + h - 1, UI_BOX_BL);
    put_tile(x + w - 1, y + h - 1, UI_BOX_BR);
    for (i = 1; i < w - 1; i++) {
        put_tile(x + i, y, UI_BOX_T);
        put_tile(x + i, y + h - 1, UI_BOX_B);
    }
    for (i = 1; i < h - 1; i++) {
        put_tile(x, y + i, UI_BOX_L);
        put_tile(x + w - 1, y + i, UI_BOX_R);
    }
    fill_area(x + 1, y + 1, w - 2, h - 2, T_SPACE);
}

void dlg_open(void) {
    uint8_t ot = txt_target;
    if (dlg_is_open) return;
    txt_target = TXT_WIN;
    attr_area(0, 0, 20, DLG_ROWS, PAL_DLG | 0x80);
    draw_box(0, 0, 20, DLG_ROWS);
    txt_target = ot;
    move_win(7, DLG_WY);
    SHOW_WIN;
    dlg_is_open = 1;
}

void dlg_close(void) {
    if (!dlg_is_open) return;
    dlg_is_open = 0;
    hud_show();
}

static void dlg_clear(void) {
    uint8_t ot = txt_target;
    txt_target = TXT_WIN;
    fill_area(1, 1, 18, 4, T_SPACE);
    txt_target = ot;
}

static void wait_ack(void) {
    uint8_t blink = 0;
    for (;;) {
        wait_frame();
        blink++;
        set_win_tile_xy(18, 5, (blink & 16) ? UI_MORE : UI_BOX_B);
        if (joy_new & (J_A | J_B)) break;
    }
    set_win_tile_xy(18, 5, UI_BOX_B);
    sfx_play(1);
}

/* Typewriter output. Codes: \n newline, \f page break (wait), \v end-without-wait, 0 end */
static uint8_t say_bank;
static uint8_t say_near;

static uint8_t say_get(const uint8_t *p) {
    return say_near ? *p : far_byte(say_bank, p);
}

static const uint8_t *say_core(const uint8_t *t) {
    uint8_t x = 1, y = 1, c, fast = 0, d;
    dlg_open();
    dlg_clear();
    for (;;) {
        c = say_get(t++);
        if (c == 0) { wait_ack(); break; }
        if (c == '\v') break;
        if (c == '\n') { x = 1; y++; continue; }
        if (c == '\f') { wait_ack(); dlg_clear(); x = 1; y = 1; fast = 0; continue; }
        set_win_tile_xy(x++, y, ch2tile(c));
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

const uint8_t *dlg_say_far(uint8_t bank, const uint8_t *txt) {
    say_bank = bank; say_near = 0;
    return say_core(txt);
}

void dlg_say(const char *txt) {
    say_near = 1;
    say_core((const uint8_t *)txt);
}

uint8_t dlg_choice2(const char *a, const char *b) {
    uint8_t sel = 0, ot = txt_target;
    dlg_open();
    txt_target = TXT_WIN;
    fill_area(1, 3, 18, 2, T_SPACE);
    print_at(3, 3, a);
    print_at(3, 4, b);
    for (;;) {
        set_win_tile_xy(2, 3, sel == 0 ? UI_CURSOR : 0);
        set_win_tile_xy(2, 4, sel == 1 ? UI_CURSOR : 0);
        wait_frame();
        if (joy_new & (J_UP | J_DOWN)) { sel ^= 1; sfx_play(2); }
        if (joy_new & J_A) { sfx_play(1); break; }
    }
    txt_target = ot;
    return sel;
}
