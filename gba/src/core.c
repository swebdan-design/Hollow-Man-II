/* core.c (GBA) - input, timing, palettes, fades, display modes */
#include "hm.h"
#include "gba_dirs.h"

uint16_t joy, joy_prev, joy_new;
uint8_t frame_ctr;
uint16_t bg_pal[256];
uint16_t obj_pal[256];
uint8_t fade_level;
int16_t scroll_x, scroll_y;
static uint32_t rng = 0x2545F491;
static uint16_t dispcnt_saved = DCNT_MODE0 | DCNT_BG0 | DCNT_BG1 | DCNT_BG2 | DCNT_OBJ | DCNT_OBJ_1D;
extern void oam_flush(void);
extern void audio_tick(void);

/* the "far" helpers of the GBC engine: on the GBA ROM is flat */
void far_read(uint8_t bank, const void *src, void *dst, uint16_t len) { (void)bank; memcpy(dst, src, len); }
uint8_t far_byte(uint8_t bank, const uint8_t *p) { (void)bank; return *p; }
uint16_t far_word(uint8_t bank, const uint8_t *p) { (void)bank; return p[0] | (p[1] << 8); }

void irq_vblank(void) {
    oam_flush();
    REG_BGHOFS(0) = (uint16_t)scroll_x;
    REG_BGVOFS(0) = (uint16_t)scroll_y;
    audio_tick();
}

void input_update(void) {
    joy_prev = joy;
    joy = (~REG_KEYINPUT) & 0x03FF;
    joy_new = joy & ~joy_prev;
}

void wait_frame(void) {
    vblank_intr_wait();
    frame_ctr++;
    input_update();
}

void wait_frames(uint8_t n) { while (n--) wait_frame(); }

uint8_t rand8(void) {
    rng ^= rng << 13; rng ^= rng >> 17; rng ^= rng << 5;
    return (uint8_t)(rng >> 8) ^ frame_ctr;
}

void pal_apply(void) {
    dma3_copy32(MEM_PAL, bg_pal, 128);
    dma3_copy32(MEM_PAL_OBJ, obj_pal, 128);
    REG_BLDCNT = fade_level ? (0x3F | (3 << 6)) : 0;
    REG_BLDY = fade_level * 4;
}

void fade_out(void) {
    while (fade_level < 4) { fade_level++; wait_frames(3); pal_apply(); }
}

void fade_in(void) {
    while (fade_level) { fade_level--; wait_frames(3); pal_apply(); }
}

void flash_white(uint8_t frames) {
    REG_BLDCNT = 0x3F | (2 << 6);
    REG_BLDY = 12;
    wait_frames(frames);
    pal_apply();
}

void flash_red(uint8_t frames) {
    static uint16_t tmp[256];
    int i;
    for (i = 0; i < 208; i++) tmp[i] = (bg_pal[i] & 0x1F) | ((bg_pal[i] >> 2) & 0x3E0 & 0x0E0);
    dma3_copy32(MEM_PAL, tmp, 104);
    wait_frames(frames);
    pal_apply();
}

/* map palettes are baked per map (lighting and mood are part of the picture) */
extern const uint16_t *map_pals(void);
void load_bg_palset(uint8_t id) {
    const uint16_t *p = map_pals();
    (void)id;
    if (p) memcpy(bg_pal, p, 13 * 32);
    bg_pal[0] = RGB15(1, 1, 2);
    memcpy(&bg_pal[14 * 16], ui_pal + 16, 32);   /* dim UI palette */
    memcpy(&bg_pal[15 * 16], ui_pal, 32);        /* UI palette */
}

void load_obj_pals(void) {
    memcpy(&obj_pal[0], pal_player, 32);
    memcpy(&obj_pal[16], pal_fx, 32);
    memcpy(&obj_pal[32], pal_shadowbig, 32);
}

void display_off(void) { REG_DISPCNT |= DCNT_BLANK; }
void display_on(void) { REG_DISPCNT &= ~DCNT_BLANK; }

void set_mode_tiles(void) {
    REG_BGCNT(0) = BG_PRIO(3) | BG_CBB(0) | BG_SBB(28);
    REG_DISPCNT = (REG_DISPCNT & DCNT_BLANK) | dispcnt_saved;
}

/* full-screen 256-colour illustration on BG0 (8bpp tiles 0..599, sequential map) */
void set_mode_bitmap(void) {
    int i;
    REG_BGCNT(0) = BG_PRIO(3) | BG_CBB(0) | BG_SBB(28) | BG_8BPP;
    for (i = 0; i < 32 * 32; i++) {
        int x = i & 31, y = i >> 5;
        SCREENBLOCK(28)[i] = (x < 30 && y < 20) ? (y * 30 + x) : 0;
    }
    scroll_x = 0; scroll_y = 0;
    REG_DISPCNT = (REG_DISPCNT & DCNT_BLANK) | dispcnt_saved;
}

void hide_all_sprites(void);

void screen_init(void) {
    REG_DISPCNT = DCNT_BLANK;
    REG_WAITCNT = 0x4317;   /* faster ROM wait states */
    REG_BGCNT(0) = BG_PRIO(3) | BG_CBB(0) | BG_SBB(28);
    REG_BGCNT(1) = BG_PRIO(0) | BG_CBB(3) | BG_SBB(30);
    REG_BGCNT(2) = BG_PRIO(1) | BG_CBB(3) | BG_SBB(29);
    /* UI tiles in charblock 3 (below the screenblocks at 0xE000+) */
    memcpy(CHARBLOCK(3), ui_tiles, UI_TILE_COUNT * 32);
    /* OBJ VRAM: 0..31 player frame (streamed), 32.. effects, 128..511 actor frames (streamed),
     * 512..575 the Second Shadow figure */
    memcpy(CHARBLOCK(4) + 32 * 16, spr_fx, SPR_FX_COUNT * 128);
    memcpy(CHARBLOCK(4) + 512 * 16, spr_shadowbig, 64 * 32);
    load_obj_pals();
    memcpy(&bg_pal[15 * 16], ui_pal, 32);
    memcpy(&bg_pal[14 * 16], ui_pal + 16, 32);
    hide_all_sprites();
    clear_bg();
    ui_clear();
    set_mode_tiles();
    REG_DISPCNT |= DCNT_BLANK;
    REG_DISPSTAT = 0x0008;
    REG_IE = IRQ_VBLANK;
    REG_IME = 1;
}

void clear_bg(void) {
    dma3_fill32(CHARBLOCK(0), 0, 8);          /* tile 0 must be empty (an illustration may have used it) */
    dma3_fill32(SCREENBLOCK(28), 0, 512);
    scroll_x = 0; scroll_y = 0;
}
