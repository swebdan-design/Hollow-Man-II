/* state.c - bank 0: persistent game state helpers (flags, items, evidence, influence, alert) */
#include "hm.h"

gstate_t gs;
gstate_t checkpoint;

uint8_t flag_get(uint16_t f) {
    if (f >= 1024) return 0;
    return (gs.flags[f >> 3] >> (f & 7)) & 1;
}
void flag_set(uint16_t f) { if (f < 1024) gs.flags[f >> 3] |= 1 << (f & 7); }
void flag_clr(uint16_t f) { if (f < 1024) gs.flags[f >> 3] &= ~(1 << (f & 7)); }

/* object / patch condition: 0xFFFF none; bit15 negate; 0x7Fxx pseudo flags */
uint8_t cond_ok(uint16_t c) {
    uint8_t neg, r;
    uint16_t f;
    if (c == 0xFFFF) return 1;
    neg = (c & 0x8000) ? 1 : 0;
    f = c & 0x7FFF;
    if (f >= 0x7F00) {
        uint8_t n = f & 0x0F;
        switch (f & 0xFFF0) {
        case 0x7F00: r = alert_level() >= n; break;
        case 0x7F10: r = infl_stage() >= n; break;
        case 0x7F20: r = gs.chapter >= n; break;
        case 0x7F40: r = item_has(f & 0x3F); break;
        default: r = 0;
        }
        if ((f & 0xFFF0) == 0x7F40 || (f & 0xFFF0) == 0x7F50) r = item_has(f - 0x7F40);
    } else {
        r = flag_get(f);
    }
    return neg ? !r : r;
}

uint8_t item_has(uint8_t i) { return (gs.items[i >> 3] >> (i & 7)) & 1; }
void item_give(uint8_t i) { gs.items[i >> 3] |= 1 << (i & 7); hud_dirty = 1; }
void item_take(uint8_t i) { gs.items[i >> 3] &= ~(1 << (i & 7)); hud_dirty = 1; }

uint8_t ev_has(uint8_t e) { return (gs.evidence[e >> 3] >> (e & 7)) & 1; }
void ev_give(uint8_t e) { gs.evidence[e >> 3] |= 1 << (e & 7); }
uint8_t ev_count(void) {
    uint8_t i, n = 0;
    for (i = 0; i < NUM_EVIDENCE; i++) n += ev_has(i);
    return n;
}

uint8_t infl_stage(void) {
    if (gs.influence >= 75) return 3;
    if (gs.influence >= 50) return 2;
    if (gs.influence >= 25) return 1;
    return 0;
}

void infl_add(int8_t d) {
    int16_t v = (int16_t)gs.influence + d;
    if (v < 0) v = 0;
    if (v > 100) v = 100;
    gs.influence = (uint8_t)v;
    music_disturb = gs.influence >= 75 ? 2 : (gs.influence >= 50 ? 1 : 0);
    hud_dirty = 1;
}

uint8_t alert_level(void) {
    if (gs.alert >= 75) return 3;
    if (gs.alert >= 50) return 2;
    if (gs.alert >= 25) return 1;
    return 0;
}

void alert_add(int8_t d) {
    int16_t v = (int16_t)gs.alert + d;
    if (v < 0) v = 0;
    if (v > 99) v = 99;
    gs.alert = (uint8_t)v;
    hud_dirty = 1;
}
