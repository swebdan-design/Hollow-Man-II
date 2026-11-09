/* core.c - bank 0: far data access, input, palettes, fades, VRAM helpers */
#include <string.h>
#include "hm.h"

uint8_t joy, joy_prev, joy_new;
uint8_t frame_ctr;
uint16_t bg_pal[32];
uint16_t obj_pal[32];
uint8_t fade_level;
static uint16_t rng = 0xACE1;

/* ---- far access: switch ROM bank, copy, restore the caller's bank ---- */
void far_read(uint8_t bank, const void *src, void *dst, uint16_t len) {
    uint8_t ob = _current_bank;
    SWITCH_ROM(bank);
    memcpy(dst, src, len);
    SWITCH_ROM(ob);
}

uint8_t far_byte(uint8_t bank, const uint8_t *p) {
    uint8_t ob = _current_bank, v;
    SWITCH_ROM(bank);
    v = *p;
    SWITCH_ROM(ob);
    return v;
}

uint16_t far_word(uint8_t bank, const uint8_t *p) {
    uint8_t ob = _current_bank;
    uint16_t v;
    SWITCH_ROM(bank);
    v = p[0] | ((uint16_t)p[1] << 8);
    SWITCH_ROM(ob);
    return v;
}

/* ---- input ---- */
void input_update(void) {
    joy_prev = joy;
    joy = joypad();
    joy_new = joy & ~joy_prev;
}

void wait_frame(void) {
    wait_vbl_done();
    frame_ctr++;
    input_update();
}

void wait_frames(uint8_t n) {
    while (n--) wait_frame();
}

uint8_t rand8(void) {
    /* 16-bit xorshift */
    rng ^= rng << 7;
    rng ^= rng >> 9;
    rng ^= rng << 8;
    return (uint8_t)(rng ^ frame_ctr);
}

/* ---- palettes ---- */
static uint16_t tmp_pal[32];

static void fade_calc(const uint16_t *src, uint8_t lvl, uint8_t white) {
    uint8_t i;
    for (i = 0; i < 32; i++) {
        uint16_t c = src[i];
        uint8_t r = c & 31, g = (c >> 5) & 31, b = (c >> 10) & 31;
        if (lvl) {
            if (white) {
                r = r + (((31 - r) * lvl) >> 2);
                g = g + (((31 - g) * lvl) >> 2);
                b = b + (((31 - b) * lvl) >> 2);
            } else {
                r = (r * (4 - lvl)) >> 2;
                g = (g * (4 - lvl)) >> 2;
                b = (b * (4 - lvl)) >> 2;
            }
        }
        tmp_pal[i] = r | (g << 5) | ((uint16_t)b << 10);
    }
}

static void pal_apply_ex(uint8_t lvl, uint8_t white) {
    fade_calc(bg_pal, lvl, white);
    set_bkg_palette(0, 8, tmp_pal);
    fade_calc(obj_pal, lvl, white);
    set_sprite_palette(0, 8, tmp_pal);
}

void pal_apply(void) { pal_apply_ex(fade_level, 0); }

void fade_out(void) {
    while (fade_level < 4) {
        fade_level++;
        wait_frames(3);
        pal_apply();
    }
}

void fade_in(void) {
    while (fade_level) {
        fade_level--;
        wait_frames(3);
        pal_apply();
    }
}

void flash_white(uint8_t frames) {
    pal_apply_ex(3, 1);
    wait_frames(frames);
    pal_apply();
}

void flash_red(uint8_t frames) {
    uint8_t i;
    for (i = 0; i < 32; i++) tmp_pal[i] = (bg_pal[i] & 0x1F) | 0x0008;
    set_bkg_palette(0, 6, tmp_pal);
    wait_frames(frames);
    pal_apply();
}

void load_bg_palset(uint8_t id) {
    far_read(bg_palsets_BANK, bg_palsets + (uint16_t)id * 64, bg_pal, 64);
}

void load_obj_pals(void) {
    far_read(obj_pals_BANK, obj_pals, obj_pal, 64);
}

/* ---- VRAM ----
 * BG tiles use signed addressing (LCDC.4 = 0): ids 0-127 at 0x9000, 128-255 at 0x8800.
 * Sprite tiles at 0x8000 (unsigned). Copies go through a small WRAM buffer
 * so the source bank can be switched away while writing VRAM. */
static uint8_t vbuf[128];

static void vram_copy_far(uint8_t *dst, uint8_t bank, const uint8_t *src, uint16_t len) {
    while (len) {
        uint8_t n = len > 128 ? 128 : (uint8_t)len;
        far_read(bank, src, vbuf, n);
        set_data(dst, vbuf, n);
        dst += n; src += n; len -= n;
    }
}

void vram_bg_tiles(uint8_t vbank, uint8_t first, uint16_t n, uint8_t bank, const uint8_t *src) {
    VBK_REG = vbank;
    while (n) {
        uint8_t *dst = (first < 128) ? (uint8_t *)(0x9000 + (uint16_t)first * 16)
                                     : (uint8_t *)(0x8800 + (uint16_t)(first - 128) * 16);
        uint16_t cnt = (first < 128) ? (128 - first) : (256 - first);
        if (cnt > n) cnt = n;
        vram_copy_far(dst, bank, src, cnt * 16);
        src += cnt * 16;
        n -= cnt;
        first += (uint8_t)cnt;
    }
    VBK_REG = 0;
}

void vram_spr_tiles(uint8_t vbank, uint8_t first, uint16_t n, uint8_t bank, const uint8_t *src) {
    VBK_REG = vbank;
    vram_copy_far((uint8_t *)(0x8000 + (uint16_t)first * 16), bank, src, n * 16);
    VBK_REG = 0;
}

void hide_all_sprites(void) {
    uint8_t i;
    for (i = 0; i < 40; i++) move_sprite(i, 0, 0);
}

void clear_bg(void) {
    VBK_REG = 1;
    fill_bkg_rect(0, 0, 32, 32, PAL_DLG);
    VBK_REG = 0;
    fill_bkg_rect(0, 0, 32, 32, 0);
}

void screen_init(void) {
    DISPLAY_OFF;
    /* BG map 0x9800, window map 0x9C00, signed BG tile data, 8x16 sprites */
    LCDC_REG = LCDCF_BG9800 | LCDCF_BG8800 | LCDCF_WIN9C00 | LCDCF_OBJ16 |
               LCDCF_OBJON | LCDCF_BGON;
    vram_bg_tiles(0, 0, 128, font_tiles_BANK, font_tiles);
    load_obj_pals();
    /* permanent sprite tiles: player (0..35), effects (36..), Second Shadow figure (VRAM1 0..23) */
    vram_spr_tiles(0, 0, 36, spr_player_BANK, spr_player);
    vram_spr_tiles(0, SPR_FX_BASE, SPR_FX_TILES, spr_fx_BANK, spr_fx);
    vram_spr_tiles(1, 0, 24, spr_shadowbig_BANK, spr_shadowbig);
    hide_all_sprites();
    clear_bg();
    VBK_REG = 1;
    fill_win_rect(0, 0, 32, 32, PAL_DLG | 0x80);
    VBK_REG = 0;
    fill_win_rect(0, 0, 32, 32, 0);
    HIDE_WIN;
    move_win(7, 144);
}
