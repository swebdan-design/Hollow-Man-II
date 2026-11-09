/* main.c (GBA) - HOLLOW MAN: THE SECOND SHADOW by Synth Centric
 * Entry point: hardware init, then title -> menu -> game state machine. */
#include "hm.h"

extern const char save_type_marker[];
int main(void) {
    uint8_t sel;
    if (save_type_marker[0] != 'S') return 0;   /* keep the marker linked */
    screen_init();
    audio_init();
    options_load();
    fade_level = 4;
    pal_apply();
    DISPLAY_ON;
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

/* tells emulators / flash carts that this cartridge uses 32 KB battery SRAM */
const char save_type_marker[] __attribute__((used, aligned(4), section(".marker"))) = "SRAM_V113";
