# HOLLOW MAN: THE SECOND SHADOW - Game Boy Advance build (by Synth Centric)
# make -C gba   ->  build/gba/HOLLOW_MAN_THE_SECOND_SHADOW.gba
# Requires: arm-none-eabi-gcc + newlib (e.g. Ubuntu gcc-arm-none-eabi, libnewlib-arm-none-eabi),
#           Python 3 + Pillow.
PREFIX  ?= arm-none-eabi-
CC      := $(PREFIX)gcc
OBJCOPY := $(PREFIX)objcopy
PYTHON  ?= python3

ROOT  := ..
BUILD := $(ROOT)/build/gba
GEN   := $(BUILD)/gen
ROM   := $(BUILD)/HOLLOW_MAN_THE_SECOND_SHADOW.gba

ARCH    := -mthumb -mcpu=arm7tdmi -mthumb-interwork
CFLAGS  := $(ARCH) -O2 -ffreestanding -fno-strict-aliasing -fno-common -Wall -Wno-unused-variable \
           -Wno-unused-function -Wno-char-subscripts -Wno-misleading-indentation -Iinclude -I$(GEN)
LDFLAGS := $(ARCH) -nostartfiles -T runtime/gba.ld -Wl,--gc-sections -Wl,-Map,$(BUILD)/hm.map

SRC  := $(wildcard src/*.c)
OBJS := $(patsubst src/%.c,$(BUILD)/obj/%.o,$(SRC)) $(BUILD)/obj/gba_data.o $(BUILD)/obj/crt0.o
ASSET_PY := $(wildcard $(ROOT)/tools/*.py $(ROOT)/assets/*/*.py $(ROOT)/assets/music/audio/*)

.PHONY: all clean
all: $(ROM)

$(GEN)/gba_data.c: $(ASSET_PY)
	@mkdir -p $(GEN) $(BUILD)/preview
	$(PYTHON) $(ROOT)/tools/build_gba_assets.py $(GEN) $(BUILD)/preview

$(BUILD)/obj/%.o: src/%.c include/hm.h include/gba.h $(GEN)/gba_data.c
	@mkdir -p $(BUILD)/obj
	$(CC) $(CFLAGS) -c $< -o $@

$(BUILD)/obj/gba_data.o: $(GEN)/gba_data.c
	@mkdir -p $(BUILD)/obj
	$(CC) $(CFLAGS) -O1 -c $< -o $@

$(BUILD)/obj/crt0.o: runtime/crt0.s
	@mkdir -p $(BUILD)/obj
	$(CC) $(ARCH) -c $< -o $@

$(ROM): $(OBJS)
	$(CC) $(LDFLAGS) $(OBJS) -lc -lgcc -o $(BUILD)/hm.elf
	$(OBJCOPY) -O binary $(BUILD)/hm.elf $@
	$(PYTHON) $(ROOT)/tools/gbafix.py $@

clean:
	rm -rf $(BUILD)
