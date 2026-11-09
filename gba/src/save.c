/* save.c (GBA) - battery-backed SRAM saves (32 KB SRAM, byte access only).
 * Layout (MBC5, 8 KB RAM bank 0):
 *   0xA000  options block: 'O','P','T', music, sfx, text speed, checksum
 *   0xA100  save slot A    (gstate_t with magic/version/seq/checksum)
 *   0xA400  save slot B
 * Saves alternate between slots; the slot with the newest valid sequence number is
 * loaded. A valid save is never overwritten in place - the other slot is written and
 * verified first, so power loss mid-write cannot destroy the previous save. */
#include <string.h>
#include "hm.h"

#define SLOT_A (SRAM + 0x100)
#define SLOT_B (SRAM + 0x400)
#define OPT (SRAM)

/* SRAM is on an 8-bit bus: copy byte by byte */
static void sram_put(volatile uint8_t *dst, const void *src, uint16_t n) {
    const uint8_t *s = src;
    while (n--) *dst++ = *s++;
}
static void sram_get(void *dst, volatile const uint8_t *src, uint16_t n) {
    uint8_t *d = dst;
    while (n--) *d++ = *src++;
}

static gstate_t tmp;

static uint16_t calc_sum(const gstate_t *s) {
    const uint8_t *p = (const uint8_t *)s;
    uint16_t a = 0x1234, i;
    for (i = 0; i < sizeof(gstate_t) - 2; i++) {
        a = (a << 1 | a >> 15) ^ p[i];
    }
    return a;
}

static uint8_t slot_ok(volatile const uint8_t *slot, gstate_t *out) {
    sram_get(out, slot, sizeof(gstate_t));
    if (out->magic[0] != 'H' || out->magic[1] != 'M' || out->magic[2] != '2' || out->magic[3] != 'S') return 0;
    if (out->version != 1) return 0;
    if (out->checksum != calc_sum(out)) return 0;
    if (out->map >= NUM_MAPS || out->hp == 0 || out->hp > 20) return 0;
    return 1;
}

/* returns 0 none, 1 slot A, 2 slot B (newest valid) */
static uint8_t newest(uint8_t *seq_out) {
    uint8_t a, b, sa = 0, sb = 0;
    a = slot_ok(SLOT_A, &tmp); sa = tmp.seq;
    b = slot_ok(SLOT_B, &tmp); sb = tmp.seq;
    if (a && b) {
        if ((uint8_t)(sb - sa) < 128 && sb != sa) { *seq_out = sb; return 2; }
        *seq_out = sa; return 1;
    }
    if (a) { *seq_out = sa; return 1; }
    if (b) { *seq_out = sb; return 2; }
    return 0;
}

uint8_t save_valid(void) BANKED {
    uint8_t s;
    return newest(&s) != 0;
}

uint8_t save_write(void) BANKED {
    uint8_t seq = 0, cur = newest(&seq), ok;
    volatile uint8_t *dst = (cur == 1) ? SLOT_B : SLOT_A;
    gs.map = cur_map;
    gs.px = (uint8_t)(((pl_x >> 4) + 8) >> 4);
    gs.py = (uint8_t)(((pl_y >> 4) + 12) >> 4);
    gs.pdir = pl_dir;
    gs.seq = cur ? seq + 1 : 1;
    gs.checksum = calc_sum(&gs);
    sram_put(dst, &gs, sizeof(gstate_t));
    ok = slot_ok(dst, &tmp) && memcmp(&tmp, &gs, sizeof(gstate_t)) == 0;
    if (ok) memcpy(&checkpoint, &gs, sizeof(gs));
    return ok;
}

uint8_t save_load(void) BANKED {
    uint8_t seq, s = newest(&seq);
    if (!s) return 0;
    slot_ok(s == 1 ? SLOT_A : SLOT_B, &gs);
    infl_add(0);
    memcpy(&checkpoint, &gs, sizeof(gs));
    return 1;
}

void options_load(void) BANKED {
    if (OPT[0] == 'O' && OPT[1] == 'P' && OPT[2] == 'T' &&
        OPT[6] == (uint8_t)(OPT[3] + OPT[4] * 3 + OPT[5] * 7 + 0x5A) && OPT[3] < 2 && OPT[4] < 2 && OPT[5] < 4) {
        music_on = OPT[3];
        sfx_on = OPT[4];
        text_speed = OPT[5];
    }
}

void options_save(void) BANKED {
    OPT[0] = 'O'; OPT[1] = 'P'; OPT[2] = 'T';
    OPT[3] = music_on; OPT[4] = sfx_on; OPT[5] = text_speed;
    OPT[6] = (uint8_t)(music_on + sfx_on * 3 + text_speed * 7 + 0x5A);
}
