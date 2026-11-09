
/* special.c - puzzle/system hooks callable from scripts (SPECIAL op) and per-frame ticks */
#include "hm.h"

uint8_t lockdown_timer_on;
uint16_t lockdown_frames;

uint8_t mercy_count(void) {
    uint8_t i, n = 0;
    for (i = EV_MERCY1; i <= EV_MERCY7; i++) n += ev_has(i);
    return n;
}

void special_call(uint8_t id) {
    uint8_t i;
    switch (id) {
    case SP_LOCKDOWN_START:
        lockdown_timer_on = 1;
        lockdown_frames = 100 * 60;
        hud_dirty = 1;
        break;
    case SP_LOCKDOWN_STOP:
        lockdown_timer_on = 0;
        hud_dirty = 1;
        break;
    case SP_FULLHEAL:
        gs.hp = gs.maxhp;
        hud_dirty = 1;
        break;
    case SP_MAXHP_UP:
        if (gs.maxhp < 14) gs.maxhp += 2;
        gs.hp = gs.maxhp;
        hud_dirty = 1;
        break;
    case SP_CLEAR_ENEMIES:
        for (i = 0; i < MAX_ACTORS; i++)
            if (actors[i].type == ACT_ENEMY || actors[i].type == ACT_PROJ) actors[i].type = ACT_NONE;
        break;
    case SP_SPAWN_ENEMIES:
        /* re-spawn this map's enemy objects (ambush) */
        for (i = 0; i < mh.nobjs; i++)
            if (objs[i].type == OBJ_ENEMY && cond_ok(objs[i].cond)) spawn_obj_actor(i);
        break;
    case SP_RESET_REVIVE:
        gs.revive_used = 0;
        break;
    case SP_PURSUIT:
        music_cur = 0xFE;
        music_play(MUS_PURSUIT);
        break;
    case SP_EQUIP_AXE:
        gs.weapon = 1;
        hud_dirty = 1;
        break;
    case SP_TOOL_SHADOW:
        gs.tool = TOOL_SHADOW;
        hud_dirty = 1;
        break;
    }
}

void special_tick(void) {
    if (lockdown_timer_on) {
        if (lockdown_frames) lockdown_frames--;
        if ((lockdown_frames % 60) == 0) {
            hud_dirty = 1;
            if (lockdown_frames <= 600) sfx_play(14);
        }
        if (lockdown_frames == 0) {
            lockdown_timer_on = 0;
            sfx_play(16);
            shake_t = 20;
            dlg_say("The steel doors\nslam shut. The\nlockdown is total.|Boots in every\naisle. There is\nnowhere left.");
            dlg_close();
            gs.hp = 0;
            hud_dirty = 1;
        }
    }
}
