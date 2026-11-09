/* audio.c (GBA) - four-channel music driver + sound effects on the GBA's DMG-compatible channels.
 * Runs from the VBlank interrupt (60 Hz).  Song data lives in data banks;
 * the ISR switches to the song bank and restores the interrupted bank.
 *
 * Stream format (per channel):
 *   0x00-0x53 note (C2 + n)       0x60 rest      0x61 hold
 *   0x80 n  length (rows)         0x81 i instrument
 *   0x82    loop point            0x83 jump to loop point / stop if none
 *   0x84    stop channel
 */
#include "hm.h"
#include "gba_dirs.h"

static uint8_t s1l, s1e, s2l, s2e;   /* shadow copies: GBA packs NRx1/NRx2 into one register */

uint8_t music_cur = 0xFF, music_on = 1, sfx_on = 1, music_disturb;

typedef struct {
    const uint8_t *p, *loop;
    uint8_t wait, len, ins, note, active, phase;
} chan_t;

static chan_t ch[4];
uint8_t vis_level[4];
static uint8_t song_bank, song_speed, playing;
static uint8_t sfx_mask;   /* bit0: ch1 owned by sfx, bit3: noise */
static uint8_t cur_wave = 0xFF;

/* instruments: pulse {duty, env, fx}; fx: 0 none 1 vibrato 2 arp minor 3 arp oct 4 drop 5 slow vib */
static const uint8_t ins_tab[][3] = {
    {2, 0xA3, 0},   /* 0 lead soft decay */
    {1, 0x82, 0},   /* 1 pluck */
    {0, 0x61, 2},   /* 2 minor arp thin */
    {2, 0x77, 1},   /* 3 sustained vibrato */
    {1, 0x5F, 5},   /* 4 swell (env up) slow vib */
    {3, 0xC1, 4},   /* 5 stab with pitch drop */
    {2, 0x50, 0},   /* 6 sustained quiet */
    {0, 0x93, 3},   /* 7 octave arp */
    {1, 0x40, 1},   /* 8 ghost quiet vibrato */
    {2, 0xF2, 0},   /* 9 loud short */
};
/* wave instruments: {wave, vol(NR32)} */
static const uint8_t wins_tab[][2] = {
    {0, 0x20}, {1, 0x20}, {2, 0x40}, {0, 0x40}, {3, 0x20},
};
static const uint8_t waves[4][16] = {
    {0x01,0x23,0x45,0x67,0x89,0xAB,0xCD,0xEF,0xFE,0xDC,0xBA,0x98,0x76,0x54,0x32,0x10}, /* triangle bass */
    {0xFF,0xEE,0xDD,0xCC,0xBB,0xAA,0x99,0x88,0x77,0x66,0x55,0x44,0x33,0x22,0x11,0x00}, /* saw */
    {0x8B,0xDE,0xEF,0xFF,0xFE,0xED,0xB8,0x52,0x21,0x10,0x00,0x01,0x12,0x25,0x7A,0xBC}, /* sine-ish */
    {0xFF,0xFF,0xFF,0xFF,0xF0,0x00,0x00,0x00,0xFF,0xF0,0x00,0x0F,0xFF,0x00,0x00,0x00}, /* growl */
};
/* drums: {NR41 len, NR42 env, NR43 poly} */
static const uint8_t drum_tab[][3] = {
    {0x00, 0xC1, 0x71},   /* 0 kick (low thump) */
    {0x00, 0xA2, 0x52},   /* 1 snare */
    {0x30, 0x51, 0x10},   /* 2 closed hat */
    {0x00, 0x63, 0x13},   /* 3 open hat */
    {0x00, 0x82, 0x60},   /* 4 dusty snare */
    {0x00, 0x37, 0x6D},   /* 5 rumble swell */
    {0x00, 0xF3, 0x80},   /* 6 crash/thunder */
    {0x00, 0x41, 0x37},   /* 7 rim/click */
};

static void set_wave(uint8_t w) {
    uint8_t i;
    if (w == cur_wave) return;
    cur_wave = w;
    REG_SND3SEL = 0x40;      /* play bank 1, so writes go to bank 0 */
    for (i = 0; i < 4; i++)
        REG_WAVE_RAM[i] = waves[w][i * 4] | (waves[w][i * 4 + 1] << 8) | (waves[w][i * 4 + 2] << 16) | ((uint32_t)waves[w][i * 4 + 3] << 24);
    REG_SND3SEL = 0x80;      /* enable, play bank 0 */
}

static uint16_t note_freq(uint8_t n) {
    if (n > 83) n = 83;
    return note_table[n];
}

static void pulse_write(uint8_t c, uint16_t f, uint8_t trig) {
    if (c == 0) {
        if (sfx_mask & 1) return;
        REG_SND1FREQ = (f & 0x7FF) | (trig ? 0x8000 : 0);
    } else {
        REG_SND2FREQ = (f & 0x7FF) | (trig ? 0x8000 : 0);
    }
}

static void note_on(uint8_t c) {
    chan_t *h = &ch[c];
    uint8_t n = h->note;
    if (!music_on) return;
    vis_level[c] = 15;
    if (c < 2) {
        const uint8_t *in = ins_tab[h->ins];
        if (c == 0) {
            if (sfx_mask & 1) return;
            REG_SND1SWEEP = 0x08;
            s1l = in[0] << 6; s1e = in[1];
            REG_SND1CNT = s1l | (s1e << 8);
        } else {
            s2l = in[0] << 6; s2e = in[1];
            REG_SND2CNT = s2l | (s2e << 8);
        }
        pulse_write(c, note_freq(n), 1);
    } else if (c == 2) {
        uint16_t f;
        set_wave(wins_tab[h->ins][0]);
        f = note_freq(n + 12 > 83 ? 83 : n + 12);
        REG_SND3CNT = (uint16_t)wins_tab[h->ins][1] << 8;
        REG_SND3FREQ = (f & 0x7FF) | 0x8000;
    } else {
        const uint8_t *d;
        if (sfx_mask & 8) return;
        d = drum_tab[n & 7];
        REG_SND4CNT = d[0] | (d[1] << 8);
        REG_SND4FREQ = d[2] | 0x8000;
    }
}

static void note_off(uint8_t c) {
    if (c == 0) { if (!(sfx_mask & 1)) { REG_SND1CNT = 0x0800; REG_SND1FREQ = 0x8000; } }
    else if (c == 1) { REG_SND2CNT = 0x0800; REG_SND2FREQ = 0x8000; }
    else if (c == 2) { REG_SND3CNT = 0; }
}

static void chan_step(uint8_t c) {
    chan_t *h = &ch[c];
    uint8_t b;
    for (;;) {
        b = *h->p++;
        if (b < 0x60) {
            h->note = b;
            h->phase = 0;
            note_on(c);
            break;
        } else if (b == 0x60) {
            note_off(c);
            h->note = 0xFF;
            break;
        } else if (b == 0x61) {
            break;
        } else if (b == 0x80) {
            h->len = *h->p++;
        } else if (b == 0x81) {
            h->ins = *h->p++;
        } else if (b == 0x82) {
            h->loop = h->p;
        } else if (b == 0x83) {
            if (h->loop) h->p = h->loop;
            else { h->active = 0; note_off(c); return; }
        } else {
            h->active = 0;
            note_off(c);
            return;
        }
    }
    h->wait = h->len * song_speed;
}

static const int8_t vib[8] = {0, 1, 2, 1, 0, -1, -2, -1};

static void chan_fx(uint8_t c) {
    chan_t *h = &ch[c];
    uint8_t fx, n;
    uint16_t f;
    if (c > 1 || h->note == 0xFF || !music_on) return;
    fx = ins_tab[h->ins][2];
    if (music_disturb && fx == 0) fx = music_disturb == 2 ? 1 : 5;
    if (!fx) return;
    h->phase++;
    n = h->note;
    if (fx == 2) {
        static const uint8_t arp[3] = {0, 3, 7};
        n += arp[h->phase % 3];
        pulse_write(c, note_freq(n), 0);
    } else if (fx == 3) {
        if (h->phase & 2) n += 12;
        pulse_write(c, note_freq(n), 0);
    } else if (fx == 4) {
        f = note_freq(n);
        if (h->phase < 40) f -= h->phase * 2;
        pulse_write(c, f, 0);
    } else {
        int8_t d = vib[(fx == 5 ? (h->phase >> 2) : (h->phase >> 1)) & 7];
        if (music_disturb == 2 && (h->phase & 63) > 54) d *= 4;
        f = note_freq(n) + d;
        pulse_write(c, f, 0);
    }
}

/* ------------------------------------------------------------------ sfx */
/* each sfx: channel(0 pulse1 / 3 noise), then steps {frames, a, b, c} terminated by frames=0
 * pulse: a = duty/env byte pair packed: a=NR11 duty, b=NR12 env, c=freq index (note)
 * noise: a = NR42 env, b = NR43 poly, c unused */
static const uint8_t sfx_data[] = {
    /* 0 none */ 0, 0,
    /* 1 confirm */ 0, 4, 0x80, 0xA1, 55, 6, 0x80, 0xA1, 62, 0,
    /* 2 cursor */ 0, 3, 0x40, 0x81, 60, 0,
    /* 3 swing */ 3, 3, 0x81, 0x22, 0, 3, 0x61, 0x12, 0, 0,
    /* 4 hit */ 3, 3, 0xC1, 0x50, 0, 5, 0xA2, 0x63, 0, 0,
    /* 5 gunshot */ 3, 2, 0xF1, 0x40, 0, 10, 0xD3, 0x55, 0, 0,
    /* 6 hurt */ 0, 4, 0x00, 0xC1, 30, 6, 0x00, 0xA1, 25, 0,
    /* 7 door */ 3, 4, 0x82, 0x6A, 0, 6, 0x62, 0x7B, 0, 0,
    /* 8 key */ 0, 3, 0x80, 0x91, 67, 3, 0x80, 0x91, 71, 6, 0x80, 0x93, 74, 0,
    /* 9 pickup */ 0, 3, 0x80, 0xA1, 60, 3, 0x80, 0xA1, 64, 3, 0x80, 0xA1, 67, 8, 0x80, 0xA3, 72, 0,
    /* 10 shadow */ 0, 10, 0xC0, 0xF7, 12, 10, 0xC0, 0xC7, 11, 20, 0xC0, 0x97, 10, 0,
    /* 11 solved */ 0, 5, 0x80, 0xA2, 55, 5, 0x80, 0xA2, 59, 5, 0x80, 0xA2, 62, 14, 0x80, 0xA4, 67, 0,
    /* 12 text blip */ 0, 1, 0x00, 0x31, 60, 0,
    /* 13 step */ 3, 2, 0x21, 0x22, 0, 0,
    /* 14 alert */ 0, 4, 0x80, 0xB1, 70, 4, 0x80, 0xB1, 75, 0,
    /* 15 deny */ 0, 5, 0x40, 0xA1, 30, 8, 0x40, 0xA1, 28, 0,
    /* 16 thunder */ 3, 30, 0xF5, 0x83, 0, 0,
    /* 17 heavy hit */ 3, 4, 0xF1, 0x71, 0, 12, 0xC3, 0x74, 0, 0,
    /* 18 save */ 0, 6, 0x80, 0x93, 48, 6, 0x80, 0x93, 55, 6, 0x80, 0x93, 60, 12, 0x80, 0x95, 67, 0,
    /* 19 bottle smash */ 3, 3, 0xD1, 0x21, 0, 8, 0x93, 0x10, 0, 0,
    /* 20 kill */ 3, 6, 0xF2, 0x61, 0, 14, 0xA4, 0x75, 0, 0,
};
static uint16_t sfx_off[24];
static const uint8_t *sfx_p;
static uint8_t sfx_ch, sfx_wait;

static void sfx_index(void) {
    uint8_t i = 0, k = 0;
    const uint8_t *p = sfx_data;
    while (k < 21) {
        sfx_off[k++] = i;
        i++;               /* channel byte */
        while (sfx_data[i]) i += 4;
        i++;
    }
    (void)p;
}

void sfx_play(uint8_t id) {
    if (!sfx_on || id == 0 || id > 20) return;
    /* low-priority sounds never interrupt others */
    if ((id == 12 || id == 13) && sfx_p) return;
    {
        sfx_p = &sfx_data[sfx_off[id]];
        sfx_ch = *sfx_p++;
        sfx_wait = 0;
        sfx_mask = sfx_ch == 0 ? 1 : 8;
    }
}

static void sfx_tick(void) {
    if (!sfx_p) return;
    if (sfx_wait) { sfx_wait--; return; }
    if (*sfx_p == 0) {
        sfx_p = 0;
        if (sfx_ch == 0) { REG_SND1CNT = 0x0800; REG_SND1FREQ = 0x8000; }
        sfx_mask = 0;
        return;
    }
    sfx_wait = sfx_p[0] - 1;
    if (sfx_ch == 0) {
        uint16_t f = note_freq(sfx_p[3]);
        REG_SND1SWEEP = 0x08;
        REG_SND1CNT = sfx_p[1] | (sfx_p[2] << 8);
        REG_SND1FREQ = (f & 0x7FF) | 0x8000;
    } else {
        REG_SND4CNT = sfx_p[1] << 8;
        REG_SND4FREQ = sfx_p[2] | 0x8000;
    }
    sfx_p += 4;
}

/* ------------------------------------------------------------------ public */
/* ---------------------------------------------------------------- recorded tracks
 * Signed 8-bit mono at 18157 Hz = exactly 304 samples per frame. DMA1 streams straight
 * from ROM into FIFO A; the VBlank tick counts samples and re-arms the DMA at the loop. */
#define ST_RATE_RELOAD (65536 - 924)
#define ST_PER_FRAME 304
static const int8_t *st_data;
static uint32_t st_len, st_loop, st_pos;
static uint8_t st_on;

static void stream_arm(uint32_t pos) {
    REG_DMA1CNT_H = 0;
    REG_DMA1SAD = (uint32_t)(st_data + pos);
    REG_DMA1DAD = REG_FIFO_A;
    REG_DMA1CNT_H = 0xB640;            /* enable, FIFO timing, repeat, 32-bit, fixed dest */
}

static void stream_stop(void) {
    st_on = 0;
    REG_TM0CNT_H = 0;
    REG_DMA1CNT_H = 0;
    REG_SNDDSCNT = 0x0002 | 0x0800;    /* DMG 100%, FIFO A reset, DS off */
}

static void stream_start(const stream_t *s) {
    stream_stop();
    st_data = s->data; st_len = s->len; st_loop = s->loop; st_pos = 0;
    REG_SNDDSCNT = 0x0002 | 0x0004 | 0x0300 | 0x0800;   /* DMG 100%, DS A 100% L+R, timer 0 */
    stream_arm(0);
    REG_TM0CNT_L = ST_RATE_RELOAD;
    REG_TM0CNT_H = 0x0080;
    st_on = 1;
}

static void stream_tick(void) {
    if (!st_on) return;
    st_pos += ST_PER_FRAME;
    if (st_pos >= st_len) {
        if (st_loop == 0xFFFFFFFF) { stream_stop(); return; }
        st_pos = st_loop + (st_pos - st_len);
        stream_arm(st_pos);
    }
    {   /* feed the Music Player visualiser from the waveform */
        uint8_t c;
        for (c = 0; c < 4; c++) {
            int8_t v = st_data[st_pos + c * 61];
            uint8_t l = (uint8_t)((v < 0 ? -v : v) >> 3);
            if (l > vis_level[c]) vis_level[c] = l;
        }
    }
}

void audio_tick(void) {
    uint8_t c, ob;
    stream_tick();
    for (c = 0; c < 4; c++) if (vis_level[c] && (frame_ctr & 3) == 0) vis_level[c]--;
    if (playing) {
        ob = 0;
        for (c = 0; c < 4; c++) {
            chan_t *h = &ch[c];
            if (!h->active) continue;
            if (--h->wait == 0) chan_step(c);
            else chan_fx(c);
        }
        (void)ob;
    }
    sfx_tick();
}

void audio_init(void) {
    REG_SNDSTAT = 0x80;
    REG_SNDDMGCNT = 0xFF77;
    REG_SNDDSCNT = 0x0002;   /* DMG channels at 100% */
    REG_SNDBIAS = 0x0200;
    sfx_index();
}

void music_stop(void) {
    stream_stop();
    {
        playing = 0;
        music_cur = 0xFF;
        note_off(0); note_off(1); note_off(2);
        REG_SND4CNT = 0x0800; REG_SND4FREQ = 0x8000;
    }
}

void music_play(uint8_t id) {
    far_t f;
    uint8_t hdr[10], c;
    if (id == music_cur) return;
    if (id < NUM_SONGS && stream_dir[id].data) {
        /* this cue is one of Synth Centric's recorded tracks */
        music_stop();
        gs.music_unlock[id >> 3] |= 1 << (id & 7);
        if (music_on) stream_start(&stream_dir[id]);
        music_cur = id;
        return;
    }
    music_stop();
    if (id == 0xFF || id >= NUM_SONGS) return;
    gs.music_unlock[id >> 3] |= 1 << (id & 7);   /* heard once = unlocked in the Music Player */
    f = song_dir[id];
    memcpy(hdr, f.ptr, 10);
    {
        song_bank = f.bank;
        song_speed = hdr[0];
        for (c = 0; c < 4; c++) {
            uint16_t off = hdr[2 + c * 2] | ((uint16_t)hdr[3 + c * 2] << 8);
            ch[c].p = f.ptr + off;
            ch[c].loop = 0;
            ch[c].wait = 1;
            ch[c].len = 1;
            ch[c].ins = 0;
            ch[c].note = 0xFF;
            ch[c].active = 1;
        }
        cur_wave = 0xFF;
        music_cur = id;
        playing = 1;
    }
}
