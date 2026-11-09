/* HOLLOW MAN: THE SECOND SHADOW - shared engine header
 * by Synth Centric
 *
 * Memory/bank layout:
 *   bank 0      : core engine (far access, VRAM, audio driver, text, map, sprites)
 *   banks 1-15  : gameplay code (auto-banked by GBDK bankpack, BANKED calls)
 *   banks 16+   : generated data (tiles, maps, scripts, music) - accessed only
 *                 through the bank-0 far_* helpers.
 */
#ifndef HM_H
#define HM_H

#include <gb/gb.h>
#include <gb/cgb.h>
#include <stdint.h>

/* ------------------------------------------------------------ far data */
typedef struct { uint8_t bank; const uint8_t *ptr; } far_t;
typedef struct { uint8_t bank; const uint8_t *ptr; uint8_t pal; uint8_t big; } sheet_t;
#include "gen_data.h"

void far_read(uint8_t bank, const void *src, void *dst, uint16_t len);
uint8_t far_byte(uint8_t bank, const uint8_t *p);
uint16_t far_word(uint8_t bank, const uint8_t *p);

/* ------------------------------------------------------------ metatile flags */
#define MF_SOLID   0x01
#define MF_DARK    0x02
#define MF_WATER   0x04
#define MF_HAZARD  0x08
#define MF_SHADOW  0x10
#define MF_PUSH    0x20
#define MF_ANIM    0x40
#define MF_SLOW    0x80

/* ------------------------------------------------------------ input */
extern uint8_t joy, joy_prev, joy_new;
extern uint8_t frame_ctr;
void input_update(void);
void wait_frame(void);
void wait_frames(uint8_t n);
uint8_t rand8(void);

/* ------------------------------------------------------------ palettes / fades */
extern uint16_t bg_pal[32];
extern uint16_t obj_pal[32];
extern uint8_t fade_level;      /* 0 = normal, 4 = black */
void pal_apply(void);
void fade_out(void);
void fade_in(void);
void flash_white(uint8_t frames);
void flash_red(uint8_t frames);
void load_bg_palset(uint8_t id);
void load_obj_pals(void);

/* ------------------------------------------------------------ VRAM helpers */
void vram_bg_tiles(uint8_t vbank, uint8_t first, uint16_t n, uint8_t bank, const uint8_t *src);
void vram_spr_tiles(uint8_t vbank, uint8_t first, uint16_t n, uint8_t bank, const uint8_t *src);
void screen_init(void);
void hide_all_sprites(void);
void clear_bg(void);

/* ------------------------------------------------------------ text */
#define TXT_BG  0
#define TXT_WIN 1
#define PAL_HUD 6
#define PAL_DLG 7
extern uint8_t txt_target, txt_pal;
extern uint8_t text_speed;      /* frames per char 0..3 */
void put_tile(uint8_t x, uint8_t y, uint8_t t);
void print_at(uint8_t x, uint8_t y, const char *s);
void print_far(uint8_t x, uint8_t y, uint8_t bank, const uint8_t *s);
void print_num(uint8_t x, uint8_t y, uint16_t n, uint8_t digits);
void fill_area(uint8_t x, uint8_t y, uint8_t w, uint8_t h, uint8_t t);
void attr_area(uint8_t x, uint8_t y, uint8_t w, uint8_t h, uint8_t a);
void draw_box(uint8_t x, uint8_t y, uint8_t w, uint8_t h);
/* dialogue box on window. returns pointer just past text */
void dlg_open(void);
void dlg_close(void);
const uint8_t *dlg_say_far(uint8_t bank, const uint8_t *txt);
void dlg_say(const char *txt);  /* near string (caller's bank) */
uint8_t dlg_choice2(const char *a, const char *b);
extern uint8_t dlg_is_open;

/* ------------------------------------------------------------ audio */
void audio_init(void);
void audio_tick(void);
void music_play(uint8_t id);
void music_stop(void);
void sfx_play(uint8_t id);
extern uint8_t music_cur, music_on, sfx_on, music_disturb;

/* ------------------------------------------------------------ map */
typedef struct {
    uint8_t w, h, tileset, palset, music, district, flags;
    uint8_t exits[4];
    uint16_t enter_script;
    uint8_t nwarps, nobjs, npatches;
} maphdr_t;

typedef struct {
    uint8_t x, y, dmap, dx, dy, ddir;
    uint16_t cond;
    uint16_t lockscript;
} warp_t;

typedef struct {
    uint8_t type, x, y, a, b, c;
    uint16_t cond;
    uint16_t script;
} obj_t;

#define MAPF_OUTDOOR    0x01
#define MAPF_RESTRICTED 0x02
#define MAPF_RAIN       0x04
#define MAPF_SAFE       0x08
#define MAPF_DARK       0x10

#define OBJ_NPC     1
#define OBJ_ENEMY   2
#define OBJ_BOSS    3
#define OBJ_SIGN    4
#define OBJ_TRIGGER 5
#define OBJ_HAZARD  6
#define OBJ_PICKUP  7
#define OBJ_NOISE   8

#define MAX_WARPS 16
#define MAX_OBJS  48
extern maphdr_t mh;
extern uint8_t cur_map;
extern uint8_t map_grid[256];
extern warp_t warps[MAX_WARPS];
extern obj_t objs[MAX_OBJS];
extern uint8_t mt_flags[64];
extern uint8_t cur_tileset;
void map_load(uint8_t id);
void map_draw_all(void);
uint8_t mt_at(uint8_t tx, uint8_t ty);
uint8_t mflags_at(uint8_t tx, uint8_t ty);
void map_set(uint8_t tx, uint8_t ty, uint8_t mt);
void map_apply_patches(void);
void map_anim_tick(void);
void map_reload_tileset(void);
far_t script_dir_get(uint16_t id);
extern uint8_t shake_t;
void trail_reset(void);
extern uint8_t image_mode;
void restore_map_view(void) BANKED;

/* ------------------------------------------------------------ actors */
#define MAX_ACTORS 12
#define ACT_NONE   0
#define ACT_NPC    1
#define ACT_ENEMY  2
#define ACT_BOSS   3
#define ACT_PROJ   4    /* enemy bullet */
#define ACT_PPROJ  5    /* player bullet */
#define ACT_FX     6
#define ACT_PICKUP 7
#define ACT_HAZARD 8
#define ACT_BOTTLE 9

#define DIR_DOWN  0
#define DIR_UP    1
#define DIR_LEFT  2
#define DIR_RIGHT 3

typedef struct {
    uint8_t type, kind;
    int16_t x, y;          /* 1/16 pixel */
    uint8_t dir, state, timer, anim;
    int8_t hp;
    uint8_t tile, attr, size;  /* size 0=16x16 1=8x16 2=32x32 */
    uint8_t obj;           /* source obj index or 0xFF */
    uint8_t hurt;          /* invuln / flash timer */
    int8_t kx, ky;         /* knockback */
    uint8_t hx, hy;        /* home / target tile */
    uint8_t px0, px1;      /* patrol bounds (tile) */
    uint8_t aux, aux2;
    uint8_t icon;          /* 0 none, 1 '!' 2 '?' 3 stars */
    uint8_t stun;
} actor_t;
extern actor_t actors[MAX_ACTORS];

/* sprite-sheet VRAM slots */
#define NUM_SLOTS 10
extern uint8_t slot_sheet[NUM_SLOTS];
uint8_t sheet_load(uint8_t sheet);   /* returns slot index */
uint8_t slot_tile(uint8_t slot);
uint8_t slot_attr(uint8_t slot, uint8_t pal);

/* ------------------------------------------------------------ player / game state */
typedef struct {
    uint8_t magic[4];
    uint8_t version, seq;
    uint8_t map, px, py, pdir;
    uint8_t hp, maxhp;
    uint8_t chapter;
    uint8_t influence, alert;
    uint8_t weapon, tool;
    uint8_t ammo, bandages, bottles;
    uint8_t items[4];
    uint8_t evidence[5];
    uint8_t flags[128];
    uint8_t vars[16];
    uint8_t music_unlock[2];
    uint8_t revive_used;
    uint8_t kills, cops_killed;
    uint16_t play_min;
    uint8_t play_sec, play_frm;
    uint8_t visited;       /* district bits */
    uint8_t pad[3];
    uint16_t checksum;
} gstate_t;
extern gstate_t gs;
extern gstate_t checkpoint;

/* player runtime */
extern int16_t pl_x, pl_y;
extern uint8_t pl_dir, pl_anim, pl_atk, pl_hurt, pl_charge, pl_busy;
extern int16_t cam_x, cam_y;
extern uint8_t hud_dirty;

#define TOOL_NONE   0
#define TOOL_PISTOL 1
#define TOOL_BOTTLE 2
#define TOOL_SHADOW 3
#define TOOL_BANDAGE 4
#define NUM_TOOLS   5

uint8_t flag_get(uint16_t f);
void flag_set(uint16_t f);
void flag_clr(uint16_t f);
uint8_t cond_ok(uint16_t c);
uint8_t item_has(uint8_t i);
void item_give(uint8_t i);
void item_take(uint8_t i);
uint8_t ev_has(uint8_t e);
void ev_give(uint8_t e);
uint8_t ev_count(void);
uint8_t infl_stage(void);
void infl_add(int8_t d);
void alert_add(int8_t d);
uint8_t alert_level(void);

/* ------------------------------------------------------------ sprites render */
void render_sprites(void);
void camera_update(void);
void apply_scroll(void);
extern uint8_t shadow_mode;   /* override for cutscenes */
extern uint8_t big_shadow_on;
extern int16_t big_shadow_x, big_shadow_y;   /* screen pixels */

/* ------------------------------------------------------------ banked APIs */
void title_run(void) BANKED;
uint8_t main_menu(void) BANKED;
void game_new(void) BANKED;
void game_continue(void) BANKED;
void game_loop(void) BANKED;
void hud_draw(void) BANKED;
void hud_show(void) BANKED;
void player_update(void) BANKED;
void player_place(uint8_t tx, uint8_t ty, uint8_t dir) BANKED;
void player_damage(uint8_t dmg, uint8_t fromdir) BANKED;
void actors_clear(void) BANKED;
void actors_spawn_map(void) BANKED;
void actors_update(void) BANKED;
int8_t actor_new(uint8_t type, uint8_t kind, int16_t x, int16_t y) BANKED;
uint8_t actor_blocks(int16_t x, int16_t y, uint8_t self) BANKED;
void actors_hit_box(uint8_t x0, uint8_t y0, uint8_t x1, uint8_t y1, uint8_t dmg, uint8_t heavy) BANKED;
void actors_noise(uint8_t x, uint8_t y, uint8_t radius) BANKED;
void actors_stun_near(uint8_t x, uint8_t y, uint8_t radius, uint8_t dmg) BANKED;
void boss_update(actor_t *a) BANKED;
void boss_init(actor_t *a) BANKED;
void boss_hit_hook(actor_t *a, uint8_t dmg, uint8_t fromdir, uint8_t heavy) BANKED;
void boss_stun_hook(actor_t *a) BANKED;
uint8_t actor_step(actor_t *a, uint8_t dir, uint8_t spd, uint8_t walls) BANKED;
uint8_t actor_toward(actor_t *a, int16_t tx, int16_t ty, uint8_t spd, uint8_t walls) BANKED;
uint8_t los(int16_t x0, int16_t y0, int16_t x1, int16_t y1) BANKED;
void enemy_shoot(actor_t *a, uint8_t dir) BANKED;
void spawn_obj_actor(uint8_t oi) BANKED;
uint8_t mercy_count(void) BANKED;
extern uint8_t boss_hp_show;
extern uint8_t shadow_cast;
void script_run(uint16_t id) BANKED;
void script_queue(uint16_t id) BANKED;
extern uint16_t script_pending;
void pause_menu(void) BANKED;
uint8_t save_write(void) BANKED;
uint8_t save_valid(void) BANKED;
uint8_t save_load(void) BANKED;
void options_load(void) BANKED;
void options_save(void) BANKED;
void options_menu(uint8_t ingame) BANKED;
void music_player(void) BANKED;
void credits_run(uint8_t ending) BANKED;
void image_show(uint8_t id) BANKED;
void ending_run(void) BANKED;
void chapter_card(uint8_t n) BANKED;
void game_over(void) BANKED;
void warp_to(uint8_t map, uint8_t x, uint8_t y, uint8_t dir) BANKED;
void special_call(uint8_t id) BANKED;
void special_tick(void) BANKED;
extern uint8_t game_state;
#define GS_PLAY 0
#define GS_TITLE 1
#define GS_ENDED 2

extern uint8_t pending_warp, pw_map, pw_x, pw_y, pw_dir;
extern uint8_t lockdown_timer_on;
extern uint16_t lockdown_frames;
extern uint8_t noise_x, noise_y, noise_t;

#define ABS(x) ((x) < 0 ? -(x) : (x))

#endif
