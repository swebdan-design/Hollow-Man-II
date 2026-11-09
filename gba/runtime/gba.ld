OUTPUT_FORMAT("elf32-littlearm")
OUTPUT_ARCH(arm)
ENTRY(_start)
MEMORY {
    rom   : ORIGIN = 0x08000000, LENGTH = 32M
    iwram : ORIGIN = 0x03000000, LENGTH = 0x7E00
    ewram : ORIGIN = 0x02000000, LENGTH = 256K
}
SECTIONS {
    .text : {
        KEEP(*(.crt0))
        KEEP(*(.marker))
        *(.text .text.*)
        *(.rodata .rodata.*)
        *(.glue_7 .glue_7t)
        . = ALIGN(4);
    } > rom
    .ARM.exidx : { *(.ARM.exidx*) } > rom
    __data_lma = .;
    .data : {
        __data_start = .;
        *(.iwram .iwram.*)
        *(.data .data.*)
        . = ALIGN(4);
        __data_end = .;
    } > iwram AT > rom
    __ewram_lma = __data_lma + SIZEOF(.data);
    .ewram_data : {
        __ewram_start = .;
        *(.ewram .ewram.*)
        . = ALIGN(4);
        __ewram_end = .;
    } > ewram AT > rom
    .bss (NOLOAD) : {
        __bss_start = .;
        *(.bss .bss.* COMMON)
        . = ALIGN(4);
        __bss_end = .;
    } > iwram
    .sbss (NOLOAD) : {
        __sbss_start = .;
        *(.sbss .sbss.*)
        . = ALIGN(4);
        __sbss_end = .;
    } > ewram
    /DISCARD/ : { *(.comment) *(.note*) }
}
