/* gba_harness.c - headless mGBA (libmgba) driver for automated tests and screenshots.
 * usage: gba_harness ROM [SAVEFILE]
 * stdin commands (one per line):
 *   keys MASK        set held keys (GBA KEYINPUT bit order: A B SEL START R L U D RS LS)
 *   run N            run N frames
 *   shot PATH        write the current frame as binary PPM (240x160)
 *   peek ADDR N      print N bytes (hex) read from the bus
 *   poke ADDR VAL    write a byte
 *   save PATH        write the cartridge save data
 *   quit
 * Every command answers with one line starting with "ok". */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <mgba/core/core.h>
#include <mgba-util/vfs.h>
#include <mgba/core/log.h>
#include <stdarg.h>

static void nolog(struct mLogger *l, int cat, enum mLogLevel lvl, const char *fmt, va_list a) {
    (void)l; (void)cat; (void)lvl; (void)fmt; (void)a;
}
static struct mLogger quiet = { .log = nolog };

static color_t fb[256 * 160];

int main(int argc, char **argv) {
    char line[512];
    struct mCore *core;
    if (argc < 2) { fprintf(stderr, "usage\n"); return 1; }
    mLogSetDefaultLogger(&quiet);
    core = mCoreFind(argv[1]);
    if (!core || !core->init(core)) { fprintf(stderr, "no core\n"); return 1; }
    mCoreInitConfig(core, NULL);
    core->setVideoBuffer(core, fb, 256);
    if (!mCoreLoadFile(core, argv[1])) { fprintf(stderr, "load fail\n"); return 1; }
    if (argc > 2) {
        struct VFile *vf = VFileOpen(argv[2], O_RDWR | O_CREAT);
        if (vf) core->loadSave(core, vf);
    }
    core->reset(core);
    setvbuf(stdout, NULL, _IOLBF, 0);
    while (fgets(line, sizeof line, stdin)) {
        char cmd[32], arg[400];
        unsigned a = 0, b = 0;
        arg[0] = 0;
        if (sscanf(line, "%31s %399s", cmd, arg) < 1) continue;
        if (!strcmp(cmd, "keys")) {
            core->setKeys(core, strtoul(arg, 0, 0));
            printf("ok\n");
        } else if (!strcmp(cmd, "run")) {
            int n = atoi(arg), i;
            for (i = 0; i < n; i++) core->runFrame(core);
            printf("ok\n");
        } else if (!strcmp(cmd, "shot")) {
            FILE *f = fopen(arg, "wb");
            int x, y;
            fprintf(f, "P6\n240 160\n255\n");
            for (y = 0; y < 160; y++)
                for (x = 0; x < 240; x++) {
                    uint32_t c = fb[y * 256 + x];
                    unsigned char px[3] = {c & 0xFF, (c >> 8) & 0xFF, (c >> 16) & 0xFF};
                    fwrite(px, 1, 3, f);
                }
            fclose(f);
            printf("ok\n");
        } else if (!strcmp(cmd, "peek")) {
            unsigned i;
            sscanf(line, "%*s %x %u", &a, &b);
            printf("ok");
            for (i = 0; i < b; i++) printf(" %02x", core->busRead8(core, a + i));
            printf("\n");
        } else if (!strcmp(cmd, "poke")) {
            sscanf(line, "%*s %x %x", &a, &b);
            core->busWrite8(core, a, (uint8_t)b);
            printf("ok\n");
        } else if (!strcmp(cmd, "save")) {
            void *sram = 0;
            size_t n = core->savedataClone(core, &sram);
            FILE *f = fopen(arg, "wb");
            if (n) fwrite(sram, 1, n, f);
            fclose(f);
            free(sram);
            printf("ok %zu\n", n);
        } else if (!strcmp(cmd, "quit")) {
            printf("ok\n");
            break;
        } else printf("ok unknown\n");
    }
    core->deinit(core);
    return 0;
}
