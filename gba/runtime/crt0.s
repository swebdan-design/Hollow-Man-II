@ HOLLOW MAN: THE SECOND SHADOW (GBA) - startup code
    .section .crt0, "ax"
    .arm
    .global _start
_start:
    b       rom_start
    .fill   188, 1, 0               @ cartridge header (patched by tools/gbafix.py)
rom_start:
    mov     r0, #0x12               @ IRQ mode
    msr     cpsr_c, r0
    ldr     sp, =0x03007FA0
    mov     r0, #0x1F               @ System mode
    msr     cpsr_c, r0
    ldr     sp, =0x03007F00
    @ copy .data/.iwram from ROM to IWRAM
    ldr     r0, =__data_lma
    ldr     r1, =__data_start
    ldr     r2, =__data_end
1:  cmp     r1, r2
    ldrlt   r3, [r0], #4
    strlt   r3, [r1], #4
    blt     1b
    @ copy .ewram_data
    ldr     r0, =__ewram_lma
    ldr     r1, =__ewram_start
    ldr     r2, =__ewram_end
2:  cmp     r1, r2
    ldrlt   r3, [r0], #4
    strlt   r3, [r1], #4
    blt     2b
    @ clear .bss and .sbss (EWRAM)
    mov     r3, #0
    ldr     r1, =__bss_start
    ldr     r2, =__bss_end
3:  cmp     r1, r2
    strlt   r3, [r1], #4
    blt     3b
    ldr     r1, =__sbss_start
    ldr     r2, =__sbss_end
4:  cmp     r1, r2
    strlt   r3, [r1], #4
    blt     4b
    @ install IRQ handler
    ldr     r0, =isr_master
    ldr     r1, =0x03007FFC
    str     r0, [r1]
    ldr     r0, =main
    mov     lr, pc
    bx      r0
    b       .

    .section .iwram, "ax"
    .arm
    .align 2
    .global isr_master
isr_master:
    mov     r3, #0x04000000
    add     r3, r3, #0x200
    ldr     r2, [r3]                @ IE | IF << 16
    and     r2, r2, r2, lsr #16     @ IE & IF
    strh    r2, [r3, #2]            @ acknowledge
    ldr     r1, =0x03007FF8
    ldrh    r0, [r1]
    orr     r0, r0, r2
    strh    r0, [r1]                @ BIOS IntrWait flags
    tst     r2, #1
    bxeq    lr
    stmfd   sp!, {lr}
    ldr     r0, =irq_vblank
    mov     lr, pc
    bx      r0
    ldmfd   sp!, {lr}
    bx      lr
    .pool
