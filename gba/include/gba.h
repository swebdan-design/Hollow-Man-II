/* gba.h - minimal Game Boy Advance hardware definitions (HOLLOW MAN GBA engine) */
#ifndef GBA_H
#define GBA_H
#include <stdint.h>

typedef volatile uint16_t vu16;
typedef volatile uint32_t vu32;

#define IWRAM_CODE __attribute__((section(".iwram"), long_call, target("arm")))
#define EWRAM_BSS __attribute__((section(".sbss")))

/* display */
#define REG_DISPCNT   (*(vu16 *)0x04000000)
#define REG_DISPSTAT  (*(vu16 *)0x04000004)
#define REG_VCOUNT    (*(vu16 *)0x04000006)
#define REG_BGCNT(n)  (*(vu16 *)(0x04000008 + (n) * 2))
#define REG_BGHOFS(n) (*(vu16 *)(0x04000010 + (n) * 4))
#define REG_BGVOFS(n) (*(vu16 *)(0x04000012 + (n) * 4))
#define REG_WIN0H     (*(vu16 *)0x04000040)
#define REG_WIN0V     (*(vu16 *)0x04000044)
#define REG_WININ     (*(vu16 *)0x04000048)
#define REG_WINOUT    (*(vu16 *)0x0400004A)
#define REG_MOSAIC    (*(vu16 *)0x0400004C)
#define REG_BLDCNT    (*(vu16 *)0x04000050)
#define REG_BLDALPHA  (*(vu16 *)0x04000052)
#define REG_BLDY      (*(vu16 *)0x04000054)

#define DCNT_MODE0 0x0000
#define DCNT_MODE3 0x0003
#define DCNT_MODE4 0x0004
#define DCNT_OBJ_1D 0x0040
#define DCNT_BLANK 0x0080
#define DCNT_BG0 0x0100
#define DCNT_BG1 0x0200
#define DCNT_BG2 0x0400
#define DCNT_BG3 0x0800
#define DCNT_OBJ 0x1000
#define DCNT_WIN0 0x2000

#define BG_PRIO(n) (n)
#define BG_CBB(n) ((n) << 2)
#define BG_SBB(n) ((n) << 8)
#define BG_8BPP 0x0080
#define BG_SIZE0 0x0000   /* 256x256 */

/* memory */
#define MEM_PAL     ((uint16_t *)0x05000000)
#define MEM_PAL_OBJ ((uint16_t *)0x05000200)
#define MEM_VRAM    ((uint16_t *)0x06000000)
#define MEM_OAM     ((uint16_t *)0x07000000)
#define SRAM        ((volatile uint8_t *)0x0E000000)
#define CHARBLOCK(n) ((uint16_t *)(0x06000000 + (n) * 0x4000))
#define SCREENBLOCK(n) ((uint16_t *)(0x06000000 + (n) * 0x800))

/* input */
#define REG_KEYINPUT (*(vu16 *)0x04000130)
#define KEY_A      0x0001
#define KEY_B      0x0002
#define KEY_SELECT 0x0004
#define KEY_START  0x0008
#define KEY_RIGHT  0x0010
#define KEY_LEFT   0x0020
#define KEY_UP     0x0040
#define KEY_DOWN   0x0080
#define KEY_R      0x0100
#define KEY_L      0x0200

/* interrupts */
#define REG_IE   (*(vu16 *)0x04000200)
#define REG_IF   (*(vu16 *)0x04000202)
#define REG_WAITCNT (*(vu16 *)0x04000204)
#define REG_IME  (*(vu16 *)0x04000208)
#define IRQ_VBLANK 0x0001

/* DMA 3 */
#define REG_DMA3SAD (*(vu32 *)0x040000D4)
#define REG_DMA3DAD (*(vu32 *)0x040000D8)
#define REG_DMA3CNT (*(vu32 *)0x040000DC)
#define DMA_ENABLE 0x80000000
#define DMA_32 0x04000000
#define DMA_16 0x00000000
#define DMA_SRC_FIXED 0x01000000

/* sound (DMG-compatible channels) */
#define REG_SND1SWEEP (*(vu16 *)0x04000060)
#define REG_SND1CNT   (*(vu16 *)0x04000062)
#define REG_SND1FREQ  (*(vu16 *)0x04000064)
#define REG_SND2CNT   (*(vu16 *)0x04000068)
#define REG_SND2FREQ  (*(vu16 *)0x0400006C)
#define REG_SND3SEL   (*(vu16 *)0x04000070)
#define REG_SND3CNT   (*(vu16 *)0x04000072)
#define REG_SND3FREQ  (*(vu16 *)0x04000074)
#define REG_SND4CNT   (*(vu16 *)0x04000078)
#define REG_SND4FREQ  (*(vu16 *)0x0400007C)
#define REG_SNDDMGCNT (*(vu16 *)0x04000080)
#define REG_SNDDSCNT  (*(vu16 *)0x04000082)
#define REG_SNDSTAT   (*(vu16 *)0x04000084)
#define REG_SNDBIAS   (*(vu16 *)0x04000088)
#define REG_WAVE_RAM  ((vu32 *)0x04000090)

static inline void dma3_copy32(void *dst, const void *src, uint32_t words) {
    REG_DMA3SAD = (uint32_t)src;
    REG_DMA3DAD = (uint32_t)dst;
    REG_DMA3CNT = words | DMA_ENABLE | DMA_32;
}
static inline void dma3_copy16(void *dst, const void *src, uint32_t halfwords) {
    REG_DMA3SAD = (uint32_t)src;
    REG_DMA3DAD = (uint32_t)dst;
    REG_DMA3CNT = halfwords | DMA_ENABLE | DMA_16;
}
static inline void dma3_fill32(void *dst, uint32_t value, uint32_t words) {
    static volatile uint32_t v;
    v = value;
    REG_DMA3SAD = (uint32_t)&v;
    REG_DMA3DAD = (uint32_t)dst;
    REG_DMA3CNT = words | DMA_ENABLE | DMA_32 | DMA_SRC_FIXED;
}
static inline void vblank_intr_wait(void) {
    __asm__ volatile("swi 0x05" ::: "r0", "r1", "r2", "r3", "memory");
}
#define RGB15(r, g, b) ((r) | ((g) << 5) | ((b) << 10))

#endif
