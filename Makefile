# HOLLOW MAN II: THE SECOND SHADOW - by Synth Centric
# Build: make            (ROM -> build/HOLLOW_MAN_II_THE_SECOND_SHADOW.gbc)
#        make test       (host-side tests + emulator smoke tests)
#        make release    (release/ ROM, zips)
# Requires GBDK-2020 (set GBDK_HOME) and Python 3 with Pillow.

GBDK_HOME ?= /opt/gbdk
LCC       := $(GBDK_HOME)/bin/lcc
PYTHON    ?= python3

BUILD := build
GEN   := $(BUILD)/gen
OBJ   := $(BUILD)/obj
ROMNAME := HOLLOW_MAN_II_THE_SECOND_SHADOW
ROM   := $(BUILD)/$(ROMNAME).gbc

CFLAGS  := -Iinclude -I$(GEN) -Wf--opt-code-speed
LDFLAGS := -Wm-yC -Wl-yt0x1B -Wl-ya1 -autobank -Wb-max=15 -Wm-yoA \
           -Wm-yn"HOLLOWMAN2" -Wm-ys -Wm-yk"SC" -Wm-yl0x33

SRC      := $(wildcard src/*.c)
ASSET_PY := $(wildcard tools/*.py assets/*/*.py)
STAMP    := $(GEN)/.stamp

.PHONY: all clean test release

all: $(ROM)

$(STAMP): $(ASSET_PY)
	@mkdir -p $(GEN) $(BUILD)/preview
	$(PYTHON) tools/build_assets.py $(GEN) $(BUILD)/preview
	@touch $@

GEN_C = $(GEN)/gen_dirs.c $(wildcard $(GEN)/data_bank*.c)

$(OBJ)/%.o: src/%.c include/hm.h $(STAMP)
	@mkdir -p $(OBJ)
	$(LCC) $(CFLAGS) -c -o $@ $<

$(ROM): $(STAMP) $(patsubst src/%.c,$(OBJ)/%.o,$(SRC))
	@mkdir -p $(OBJ)/gen
	@for f in $(GEN)/gen_dirs.c $(GEN)/data_bank*.c; do \
	  b=$$(basename $$f .c); \
	  if [ ! -f $(OBJ)/gen/$$b.o ] || [ $$f -nt $(OBJ)/gen/$$b.o ]; then \
	    echo "CC $$f"; $(LCC) $(CFLAGS) -c -o $(OBJ)/gen/$$b.o $$f || exit 1; fi; done
	$(LCC) $(LDFLAGS) -o $@ $(patsubst src/%.c,$(OBJ)/%.o,$(SRC)) \
	  $(patsubst $(GEN)/%.c,$(OBJ)/gen/%.o,$(GEN)/gen_dirs.c $(wildcard $(GEN)/data_bank*.c))
	$(PYTHON) tools/romcheck.py $@

test: $(ROM)
	$(PYTHON) -m pytest -q tests

release: $(ROM)
	$(PYTHON) tools/make_release.py

clean:
	rm -rf $(BUILD)
