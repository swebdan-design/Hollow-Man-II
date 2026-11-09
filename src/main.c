/* main.c - HOLLOW MAN: THE SECOND SHADOW by Synth Centric
 * Entry point: hardware init, then title -> menu -> game state machine. */
#include "hm.h"

void main(void) {
    uint8_t sel;
    DISPLAY_OFF;
    if (_cpu == CGB_TYPE) cpu_fast();      /* double-speed CPU mode (CGB) */
    screen_init();
    audio_init();
    options_load();
    fade_level = 4;
    pal_apply();
    SHOW_BKG;
    SHOW_SPRITES;
    DISPLAY_ON;
    enable_interrupts();
    for (;;) {
        title_run();
        sel = main_menu();
        if (sel == 0) game_new();
        else if (sel == 1) game_continue();
        else if (sel == 2) music_player();
        else if (sel == 3) options_menu(0);
        else credits_run(0);
        game_state = GS_TITLE;
        dlg_is_open = 0;
    }
}
