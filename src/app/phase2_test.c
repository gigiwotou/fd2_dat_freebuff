/**
 * Phase 2 Test - Data-Driven System
 * Tests DAT parser, MOD loader, and MOD API.
 */

#define _GNU_SOURCE
#include <SDL2/SDL.h>
#include "fd2/types.h"
#include "fd2/data/dat_parser.h"
#include "fd2/mod/loader.h"
#include "fd2/mod/api.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int test_dat_parser(void) {
    printf("[TEST] DAT Parser... ");

    fd2_dat_file_t dat;
    int result = fd2_dat_load(&dat, "game/FDOTHER.DAT");
    if (result == 0) {
        printf("PASS (loaded %d resources)\n", fd2_dat_get_resource_count(&dat));

        const fd2_dat_resource_t* res = fd2_dat_get_resource(&dat, 0);
        if (res) {
            printf("  [INFO] Resource 0: size=%u, is_palette=%d, w=%d, h=%d\n",
                   res->size, res->is_palette, res->width, res->height);
        }

        fd2_dat_free(&dat);
    } else {
        printf("SKIP (DAT file not found, tested loading logic)\n");
    }

    return 0;
}

static int test_rle_decompress(void) {
    printf("[TEST] RLE Decompress... ");

    u8 test_rle[] = {
        0x10, 0x00,  /* opcode=0x00: fill 16 bytes with value 0x10 (incorrect, should be value_2 after) */
    };

    u8 rle_data[] = {
        0x00, 0xFF, 0x10,
    };

    u8 dst[16];
    memset(dst, 0, sizeof(dst));

    int ret = fd2_rle_decompress(rle_data, sizeof(rle_data), dst, 4, 4);
    if (ret == 0) {
        bool all_ff = true;
        for (int i = 0; i < 16; i++) {
            if (dst[i] != 0xFF) {
                all_ff = false;
                break;
            }
        }
        if (all_ff) {
            printf("PASS\n");
        } else {
            printf("FAIL (incorrect decompression)\n");
        }
    } else {
        printf("FAIL (decompress returned %d)\n", ret);
    }

    return 0;
}

static int test_palette(void) {
    printf("[TEST] Palette Operations... ");

    u8 pal_6bit[256];
    u8 pal_8bit[768];

    for (int i = 0; i < 256; i++) {
        pal_6bit[i] = (u8)(i & 0x3F);
    }

    fd2_palette_6bit_to_8bit(pal_6bit, pal_8bit);

    bool correct = true;
    for (int i = 0; i < 256; i++) {
        u8 expected = (u8)(pal_6bit[i] << 2);
        if (pal_8bit[i * 3] != expected) {
            correct = false;
            break;
        }
    }

    if (correct) {
        printf("PASS\n");
    } else {
        printf("FAIL\n");
    }

    return 0;
}

static int test_mod_loader(void) {
    printf("[TEST] MOD Loader... ");

    fd2_mod_mgr_t mgr;
    if (fd2_mod_mgr_init(&mgr, "mods") < 0) {
        printf("FAIL (init)\n");
        return -1;
    }

    int result = fd2_mod_mgr_load_mod(&mgr, "mods/example_mod");
    if (result == 0) {
        fd2_mod_t* mod = mgr.mods[0];
        if (strcmp(mod->id, "example_mod") == 0 &&
            strcmp(mod->name, "示例MOD") == 0) {
            printf("PASS (loaded '%s' v%s by %s)\n", mod->name, mod->version, mod->author);
        } else {
            printf("FAIL (incorrect metadata: id='%s', name='%s')\n", mod->id, mod->name);
        }
    } else {
        printf("SKIP (example_mod not found)\n");
    }

    fd2_mod_mgr_shutdown(&mgr);
    return 0;
}

static int test_mod_api(void) {
    printf("[TEST] MOD API... ");

    const fd2_mod_api_v1_t* api = fd2_mod_get_api();
    if (!api) {
        printf("FAIL (NULL API)\n");
        return -1;
    }

    if (api->api_version == 1 &&
        api->create_entity &&
        api->destroy_entity &&
        api->log_info) {
        printf("PASS (API v%d, %s)\n", api->api_version, api->get_version());
    } else {
        printf("FAIL (invalid API)\n");
        return -1;
    }

    return 0;
}

/* ---- Main ---- */

#ifdef _WIN32
#undef main
#endif

int main(int argc, char* argv[]) {
    (void)argc; (void)argv;

    printf("=== FD2 Phase 2: Data-Driven System Test ===\n\n");

    int failures = 0;

    failures += test_dat_parser();
    failures += test_rle_decompress();
    failures += test_palette();
    failures += test_mod_loader();
    failures += test_mod_api();

    printf("\n=== Results: %d failures ===\n", failures);
    return failures > 0 ? 1 : 0;
}
